"""
Persistent Store

Lightweight SQLite-based persistence for call interactions,
messages, and agent decisions.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID
import threading

from pydantic import BaseModel


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class StoredInteraction(BaseModel):
    """Stored call interaction record."""
    interaction_id: str
    customer_id: Optional[str] = None
    channel: str
    status: str
    started_at: str
    ended_at: Optional[str] = None
    metadata: Dict[str, Any] = {}
    

class StoredMessage(BaseModel):
    """Stored message record."""
    message_id: str
    interaction_id: str
    role: str  # 'customer' | 'agent' | 'system'
    content: str
    timestamp: str
    metadata: Dict[str, Any] = {}


class StoredAgentDecision(BaseModel):
    """Stored agent decision record."""
    decision_id: str
    interaction_id: str
    message_id: Optional[str] = None
    agent_type: str  # 'primary' | 'supervisor' | 'escalation'
    decision_type: str
    confidence: float
    confidence_level: str
    processing_time_ms: int
    details: Dict[str, Any] = {}
    timestamp: str


class InteractionSummary(BaseModel):
    """Summary of a stored interaction."""
    interaction_id: str
    customer_id: Optional[str]
    channel: str
    status: str
    started_at: str
    ended_at: Optional[str]
    message_count: int
    decision_count: int
    final_outcome: Optional[str] = None


# -----------------------------------------------------------------------------
# Persistent Store
# -----------------------------------------------------------------------------

class PersistentStore:
    """
    SQLite-based persistent storage for call center data.
    
    Thread-safe implementation with connection pooling.
    """
    
    def __init__(self, db_path: str = "data/callcenter.db"):
        """
        Initialize the persistent store.
        
        Args:
            db_path: Path to SQLite database file.
        """
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_schema()
    
    @contextmanager
    def _get_connection(self):
        """Get a thread-local database connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                str(self._db_path),
                check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row
        
        try:
            yield self._local.connection
        except Exception:
            self._local.connection.rollback()
            raise
    
    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Interactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    interaction_id TEXT PRIMARY KEY,
                    customer_id TEXT,
                    channel TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    interaction_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (interaction_id) REFERENCES interactions(interaction_id)
                )
            """)
            
            # Agent decisions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_decisions (
                    decision_id TEXT PRIMARY KEY,
                    interaction_id TEXT NOT NULL,
                    message_id TEXT,
                    agent_type TEXT NOT NULL,
                    decision_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    confidence_level TEXT NOT NULL,
                    processing_time_ms INTEGER NOT NULL,
                    details TEXT DEFAULT '{}',
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (interaction_id) REFERENCES interactions(interaction_id),
                    FOREIGN KEY (message_id) REFERENCES messages(message_id)
                )
            """)
            
            # Indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_interaction 
                ON messages(interaction_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_decisions_interaction 
                ON agent_decisions(interaction_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_interactions_status 
                ON interactions(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_interactions_started 
                ON interactions(started_at)
            """)
            
            conn.commit()
    
    # -------------------------------------------------------------------------
    # Interaction Methods
    # -------------------------------------------------------------------------
    
    def save_interaction(
        self,
        interaction_id: UUID,
        channel: str,
        status: str,
        started_at: datetime,
        customer_id: Optional[str] = None,
        ended_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Save or update an interaction.
        
        Args:
            interaction_id: Unique interaction identifier.
            channel: Communication channel (voice/chat).
            status: Current status.
            started_at: Start timestamp.
            customer_id: Optional customer identifier.
            ended_at: Optional end timestamp.
            metadata: Optional metadata dictionary.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO interactions 
                (interaction_id, customer_id, channel, status, started_at, ended_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(interaction_id),
                customer_id,
                channel,
                status,
                started_at.isoformat(),
                ended_at.isoformat() if ended_at else None,
                json.dumps(metadata or {}),
            ))
            conn.commit()
    
    def get_interaction(self, interaction_id: UUID) -> Optional[StoredInteraction]:
        """
        Retrieve an interaction by ID.
        
        Args:
            interaction_id: The interaction to retrieve.
            
        Returns:
            StoredInteraction or None if not found.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM interactions WHERE interaction_id = ?
            """, (str(interaction_id),))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return StoredInteraction(
                interaction_id=row['interaction_id'],
                customer_id=row['customer_id'],
                channel=row['channel'],
                status=row['status'],
                started_at=row['started_at'],
                ended_at=row['ended_at'],
                metadata=json.loads(row['metadata'] or '{}'),
            )
    
    def update_interaction_status(
        self,
        interaction_id: UUID,
        status: str,
        ended_at: Optional[datetime] = None,
    ) -> bool:
        """
        Update interaction status.
        
        Args:
            interaction_id: The interaction to update.
            status: New status.
            ended_at: Optional end timestamp.
            
        Returns:
            True if updated, False if not found.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if ended_at:
                cursor.execute("""
                    UPDATE interactions 
                    SET status = ?, ended_at = ?
                    WHERE interaction_id = ?
                """, (status, ended_at.isoformat(), str(interaction_id)))
            else:
                cursor.execute("""
                    UPDATE interactions 
                    SET status = ?
                    WHERE interaction_id = ?
                """, (status, str(interaction_id)))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def list_interactions(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[InteractionSummary]:
        """
        List interactions with optional filtering.
        
        Args:
            status: Optional status filter.
            limit: Maximum results to return.
            offset: Results offset for pagination.
            
        Returns:
            List of interaction summaries.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    i.interaction_id,
                    i.customer_id,
                    i.channel,
                    i.status,
                    i.started_at,
                    i.ended_at,
                    COUNT(DISTINCT m.message_id) as message_count,
                    COUNT(DISTINCT d.decision_id) as decision_count
                FROM interactions i
                LEFT JOIN messages m ON i.interaction_id = m.interaction_id
                LEFT JOIN agent_decisions d ON i.interaction_id = d.interaction_id
            """
            params: List[Any] = []
            
            if status:
                query += " WHERE i.status = ?"
                params.append(status)
            
            query += """
                GROUP BY i.interaction_id
                ORDER BY i.started_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                InteractionSummary(
                    interaction_id=row['interaction_id'],
                    customer_id=row['customer_id'],
                    channel=row['channel'],
                    status=row['status'],
                    started_at=row['started_at'],
                    ended_at=row['ended_at'],
                    message_count=row['message_count'],
                    decision_count=row['decision_count'],
                )
                for row in rows
            ]
    
    # -------------------------------------------------------------------------
    # Message Methods
    # -------------------------------------------------------------------------
    
    def save_message(
        self,
        message_id: UUID,
        interaction_id: UUID,
        role: str,
        content: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Save a message.
        
        Args:
            message_id: Unique message identifier.
            interaction_id: Parent interaction ID.
            role: Message role (customer/agent/system).
            content: Message content.
            timestamp: Optional timestamp (defaults to now).
            metadata: Optional metadata.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO messages 
                (message_id, interaction_id, role, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(message_id),
                str(interaction_id),
                role,
                content,
                timestamp.isoformat(),
                json.dumps(metadata or {}),
            ))
            conn.commit()
    
    def get_messages(
        self,
        interaction_id: UUID,
        limit: Optional[int] = None,
    ) -> List[StoredMessage]:
        """
        Get messages for an interaction.
        
        Args:
            interaction_id: The interaction to get messages for.
            limit: Optional limit on results.
            
        Returns:
            List of stored messages, ordered by timestamp.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM messages 
                WHERE interaction_id = ?
                ORDER BY timestamp ASC
            """
            params: List[Any] = [str(interaction_id)]
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                StoredMessage(
                    message_id=row['message_id'],
                    interaction_id=row['interaction_id'],
                    role=row['role'],
                    content=row['content'],
                    timestamp=row['timestamp'],
                    metadata=json.loads(row['metadata'] or '{}'),
                )
                for row in rows
            ]
    
    # -------------------------------------------------------------------------
    # Agent Decision Methods
    # -------------------------------------------------------------------------
    
    def save_agent_decision(
        self,
        decision_id: UUID,
        interaction_id: UUID,
        agent_type: str,
        decision_type: str,
        confidence: float,
        confidence_level: str,
        processing_time_ms: int,
        message_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Save an agent decision.
        
        Args:
            decision_id: Unique decision identifier.
            interaction_id: Parent interaction ID.
            agent_type: Type of agent (primary/supervisor/escalation).
            decision_type: Type of decision made.
            confidence: Confidence score (0-1).
            confidence_level: Confidence level (high/medium/low).
            processing_time_ms: Processing time in milliseconds.
            message_id: Optional associated message ID.
            details: Optional decision details.
            timestamp: Optional timestamp.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO agent_decisions 
                (decision_id, interaction_id, message_id, agent_type, decision_type,
                 confidence, confidence_level, processing_time_ms, details, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(decision_id),
                str(interaction_id),
                str(message_id) if message_id else None,
                agent_type,
                decision_type,
                confidence,
                confidence_level,
                processing_time_ms,
                json.dumps(details or {}),
                timestamp.isoformat(),
            ))
            conn.commit()
    
    def get_agent_decisions(
        self,
        interaction_id: UUID,
        agent_type: Optional[str] = None,
    ) -> List[StoredAgentDecision]:
        """
        Get agent decisions for an interaction.
        
        Args:
            interaction_id: The interaction to get decisions for.
            agent_type: Optional filter by agent type.
            
        Returns:
            List of stored agent decisions.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM agent_decisions 
                WHERE interaction_id = ?
            """
            params: List[Any] = [str(interaction_id)]
            
            if agent_type:
                query += " AND agent_type = ?"
                params.append(agent_type)
            
            query += " ORDER BY timestamp ASC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                StoredAgentDecision(
                    decision_id=row['decision_id'],
                    interaction_id=row['interaction_id'],
                    message_id=row['message_id'],
                    agent_type=row['agent_type'],
                    decision_type=row['decision_type'],
                    confidence=row['confidence'],
                    confidence_level=row['confidence_level'],
                    processing_time_ms=row['processing_time_ms'],
                    details=json.loads(row['details'] or '{}'),
                    timestamp=row['timestamp'],
                )
                for row in rows
            ]
    
    # -------------------------------------------------------------------------
    # Analytics Methods
    # -------------------------------------------------------------------------
    
    def get_analytics(
        self,
        since: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get aggregated analytics.
        
        Args:
            since: Optional start date filter.
            
        Returns:
            Dictionary of analytics metrics.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Build where clause
            where_clause = ""
            params: List[Any] = []
            if since:
                where_clause = "WHERE started_at >= ?"
                params.append(since.isoformat())
            
            # Total interactions
            cursor.execute(f"""
                SELECT COUNT(*) as total FROM interactions {where_clause}
            """, params)
            total = cursor.fetchone()['total']
            
            # By status
            cursor.execute(f"""
                SELECT status, COUNT(*) as count 
                FROM interactions {where_clause}
                GROUP BY status
            """, params)
            by_status = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Average confidence
            cursor.execute(f"""
                SELECT AVG(confidence) as avg_confidence
                FROM agent_decisions d
                JOIN interactions i ON d.interaction_id = i.interaction_id
                {where_clause}
            """, params)
            avg_confidence = cursor.fetchone()['avg_confidence'] or 0
            
            # Resolution rate
            completed = by_status.get('completed', 0)
            escalated = by_status.get('escalated', 0)
            resolution_rate = completed / max(completed + escalated, 1)
            
            return {
                'total_interactions': total,
                'by_status': by_status,
                'resolution_rate': resolution_rate,
                'escalation_rate': 1 - resolution_rate,
                'average_confidence': avg_confidence,
            }
    
    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    
    def delete_interaction(self, interaction_id: UUID) -> bool:
        """
        Delete an interaction and all related data.
        
        Args:
            interaction_id: The interaction to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete in order due to foreign keys
            cursor.execute("""
                DELETE FROM agent_decisions WHERE interaction_id = ?
            """, (str(interaction_id),))
            cursor.execute("""
                DELETE FROM messages WHERE interaction_id = ?
            """, (str(interaction_id),))
            cursor.execute("""
                DELETE FROM interactions WHERE interaction_id = ?
            """, (str(interaction_id),))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def clear_all(self) -> None:
        """Clear all data from the store. Use with caution."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM agent_decisions")
            cursor.execute("DELETE FROM messages")
            cursor.execute("DELETE FROM interactions")
            conn.commit()
    
    def close(self) -> None:
        """Close the database connection."""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None


# -----------------------------------------------------------------------------
# Singleton Instance
# -----------------------------------------------------------------------------

_store_instance: Optional[PersistentStore] = None
_store_lock = threading.Lock()


def get_store(db_path: str = "data/callcenter.db") -> PersistentStore:
    """
    Get the singleton PersistentStore instance.
    
    Args:
        db_path: Path to database file.
        
    Returns:
        The PersistentStore instance.
    """
    global _store_instance
    
    if _store_instance is None:
        with _store_lock:
            if _store_instance is None:
                _store_instance = PersistentStore(db_path)
    
    return _store_instance
