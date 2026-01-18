"""
Supabase Persistence Layer

Production-grade Supabase/PostgreSQL integration for the AI Call Center.
Handles all data persistence including interactions, messages, 
agent decisions, and configurations.

Features:
- PostgreSQL database via Supabase
- Built-in authentication support
- Real-time subscriptions (future)
- Row Level Security ready
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Check if supabase is available
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase not installed. Run: pip install supabase")


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

class SupabaseConfig(BaseModel):
    """Supabase connection configuration."""
    
    url: str = Field(default="")
    anon_key: str = Field(default="")
    service_role_key: str = Field(default="")
    
    # Table names
    interactions_table: str = "interactions"
    messages_table: str = "messages"
    decisions_table: str = "agent_decisions"
    agent_configs_table: str = "agent_configs"
    audit_logs_table: str = "audit_logs"
    
    @classmethod
    def from_env(cls) -> "SupabaseConfig":
        """Load configuration from environment variables."""
        return cls(
            url=os.getenv("SUPABASE_URL", ""),
            anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
            service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
        )
    
    @property
    def is_configured(self) -> bool:
        """Check if Supabase is properly configured."""
        return bool(self.url and (self.anon_key or self.service_role_key))


# -----------------------------------------------------------------------------
# Supabase Client
# -----------------------------------------------------------------------------

class SupabaseStore:
    """
    Supabase persistence store.
    
    Provides CRUD operations for all application data using Supabase/PostgreSQL.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client: Optional[Client] = None
            cls._instance._config = SupabaseConfig.from_env()
            cls._instance._connected = False
        return cls._instance
    
    @property
    def is_available(self) -> bool:
        """Check if Supabase is available and connected."""
        return SUPABASE_AVAILABLE and self._connected
    
    def connect(self) -> bool:
        """
        Connect to Supabase.
        
        Returns True if connection successful, False otherwise.
        """
        if not SUPABASE_AVAILABLE:
            logger.warning("Supabase library not installed")
            return False
        
        if not self._config.is_configured:
            logger.warning("Supabase not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY")
            return False
        
        try:
            # Use service role key for backend operations (bypasses RLS)
            key = self._config.service_role_key or self._config.anon_key
            self._client = create_client(self._config.url, key)
            self._connected = True
            logger.info(f"Connected to Supabase: {self._config.url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from Supabase."""
        self._client = None
        self._connected = False
        logger.info("Disconnected from Supabase")
    
    # =========================================================================
    # Interactions
    # =========================================================================
    
    def save_interaction(
        self,
        interaction_id: str,
        channel: str,
        status: str,
        started_at: datetime,
        customer_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Save or update an interaction."""
        if not self.is_available:
            return False
        
        try:
            data = {
                "id": str(interaction_id),
                "customer_id": customer_id,
                "channel": channel,
                "status": status,
                "started_at": started_at.isoformat() if isinstance(started_at, datetime) else started_at,
                "metadata": metadata or {},
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            # Upsert (insert or update)
            self._client.table(self._config.interactions_table).upsert(data).execute()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save interaction: {e}")
            return False
    
    def update_interaction_status(
        self,
        interaction_id: str,
        status: str,
        ended_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update an interaction's status."""
        if not self.is_available:
            return False
        
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            if ended_at:
                update_data["ended_at"] = ended_at.isoformat() if isinstance(ended_at, datetime) else ended_at
            
            if metadata:
                update_data["metadata"] = metadata
            
            self._client.table(self._config.interactions_table).update(update_data).eq("id", str(interaction_id)).execute()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update interaction: {e}")
            return False
    
    def get_interaction(self, interaction_id: str) -> Optional[Dict[str, Any]]:
        """Get an interaction by ID."""
        if not self.is_available:
            return None
        
        try:
            result = self._client.table(self._config.interactions_table).select("*").eq("id", str(interaction_id)).single().execute()
            return result.data
        except Exception as e:
            logger.error(f"Failed to get interaction: {e}")
            return None
    
    def list_interactions(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List interactions with optional filtering."""
        if not self.is_available:
            return []
        
        try:
            query = self._client.table(self._config.interactions_table).select("*")
            
            if status:
                query = query.eq("status", status)
            
            query = query.order("started_at", desc=True).range(offset, offset + limit - 1)
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to list interactions: {e}")
            return []
    
    def count_interactions(self, status: Optional[str] = None) -> int:
        """Count interactions with optional filtering."""
        if not self.is_available:
            return 0
        
        try:
            query = self._client.table(self._config.interactions_table).select("id", count="exact")
            
            if status:
                query = query.eq("status", status)
            
            result = query.execute()
            return result.count or 0
            
        except Exception as e:
            logger.error(f"Failed to count interactions: {e}")
            return 0
    
    # =========================================================================
    # Messages
    # =========================================================================
    
    def save_message(
        self,
        message_id: str,
        interaction_id: str,
        role: str,
        content: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Save a message."""
        if not self.is_available:
            return False
        
        try:
            data = {
                "id": str(message_id),
                "interaction_id": str(interaction_id),
                "role": role,
                "content": content,
                "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat(),
                "metadata": metadata or {},
            }
            
            self._client.table(self._config.messages_table).insert(data).execute()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            return False
    
    def get_messages(self, interaction_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get messages for an interaction."""
        if not self.is_available:
            return []
        
        try:
            result = self._client.table(self._config.messages_table).select("*").eq("interaction_id", str(interaction_id)).order("timestamp").limit(limit).execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            return []
    
    # =========================================================================
    # Agent Decisions
    # =========================================================================
    
    def save_agent_decision(
        self,
        decision_id: str,
        interaction_id: str,
        agent_type: str,
        decision_summary: str,
        confidence: float,
        confidence_level: str,
        processing_time_ms: int,
        timestamp: Optional[datetime] = None,
        reasoning: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Save an agent decision."""
        if not self.is_available:
            return False
        
        try:
            data = {
                "id": str(decision_id),
                "interaction_id": str(interaction_id),
                "agent_type": agent_type,
                "decision_summary": decision_summary,
                "confidence": confidence,
                "confidence_level": confidence_level,
                "processing_time_ms": processing_time_ms,
                "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat(),
                "reasoning": reasoning or [],
                "metadata": metadata or {},
            }
            
            self._client.table(self._config.decisions_table).insert(data).execute()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save agent decision: {e}")
            return False
    
    def get_agent_decisions(self, interaction_id: str) -> List[Dict[str, Any]]:
        """Get agent decisions for an interaction."""
        if not self.is_available:
            return []
        
        try:
            result = self._client.table(self._config.decisions_table).select("*").eq("interaction_id", str(interaction_id)).order("timestamp").execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get agent decisions: {e}")
            return []
    
    # =========================================================================
    # Agent Configurations
    # =========================================================================
    
    def save_agent_config(self, agent_id: str, config: Dict[str, Any]) -> bool:
        """Save agent configuration."""
        if not self.is_available:
            return False
        
        try:
            config["id"] = agent_id
            config["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            self._client.table(self._config.agent_configs_table).upsert(config).execute()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save agent config: {e}")
            return False
    
    def get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent configuration."""
        if not self.is_available:
            return None
        
        try:
            result = self._client.table(self._config.agent_configs_table).select("*").eq("id", agent_id).single().execute()
            return result.data
        except Exception as e:
            logger.error(f"Failed to get agent config: {e}")
            return None
    
    def get_all_agent_configs(self) -> List[Dict[str, Any]]:
        """Get all agent configurations."""
        if not self.is_available:
            return []
        
        try:
            result = self._client.table(self._config.agent_configs_table).select("*").execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get agent configs: {e}")
            return []
    
    # =========================================================================
    # Audit Logs
    # =========================================================================
    
    def save_audit_log(
        self,
        record_id: str,
        interaction_id: str,
        event_type: str,
        agent_type: Optional[str] = None,
        decision_outcome: Optional[str] = None,
        confidence_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Save an audit log entry."""
        if not self.is_available:
            return False
        
        try:
            data = {
                "id": str(record_id),
                "interaction_id": str(interaction_id),
                "event_type": event_type,
                "agent_type": agent_type,
                "decision_outcome": decision_outcome,
                "confidence_score": confidence_score,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {},
            }
            
            self._client.table(self._config.audit_logs_table).insert(data).execute()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save audit log: {e}")
            return False
    
    def get_audit_logs(
        self,
        interaction_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get audit logs with optional filtering."""
        if not self.is_available:
            return []
        
        try:
            query = self._client.table(self._config.audit_logs_table).select("*")
            
            if interaction_id:
                query = query.eq("interaction_id", str(interaction_id))
            if event_type:
                query = query.eq("event_type", event_type)
            
            query = query.order("timestamp", desc=True).limit(limit)
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []
    
    # =========================================================================
    # Analytics
    # =========================================================================
    
    def get_analytics_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get analytics summary for the specified period."""
        if not self.is_available:
            return {}
        
        try:
            # Get counts by status
            total = self.count_interactions()
            completed = self.count_interactions(status="completed")
            escalated = self.count_interactions(status="escalated")
            active = self.count_interactions(status="active") + self.count_interactions(status="in_progress")
            
            return {
                "total_interactions": total,
                "completed_interactions": completed,
                "escalated_interactions": escalated,
                "active_interactions": active,
                "resolution_rate": completed / max(total, 1),
                "escalation_rate": escalated / max(total, 1),
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics summary: {e}")
            return {}


# Singleton accessor
def get_supabase_store() -> SupabaseStore:
    """Get the Supabase store singleton."""
    return SupabaseStore()
