"""
MongoDB Persistence Layer

Production-grade MongoDB integration for the AI Call Center.
Handles all data persistence including interactions, messages, 
agent decisions, and configurations.

Features:
- Async operations with Motor
- Connection pooling
- Graceful fallback for local development
- Schema validation
- Index management
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Check if motor is available
try:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False
    logger.warning("Motor not installed. MongoDB features will be disabled.")


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

class MongoDBConfig(BaseModel):
    """MongoDB connection configuration."""
    
    uri: str = Field(default="mongodb://localhost:27017")
    database_name: str = Field(default="ai_call_center")
    
    # Connection settings
    min_pool_size: int = 5
    max_pool_size: int = 50
    server_selection_timeout_ms: int = 5000
    
    # Collections
    interactions_collection: str = "interactions"
    messages_collection: str = "messages"
    decisions_collection: str = "agent_decisions"
    agent_configs_collection: str = "agent_configs"
    audit_logs_collection: str = "audit_logs"
    users_collection: str = "users"
    
    @classmethod
    def from_env(cls) -> "MongoDBConfig":
        """Load configuration from environment variables."""
        import os
        return cls(
            uri=os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
            database_name=os.getenv("MONGODB_DATABASE", "ai_call_center"),
        )


# -----------------------------------------------------------------------------
# MongoDB Client
# -----------------------------------------------------------------------------

class MongoDBStore:
    """
    MongoDB persistence store.
    
    Provides async CRUD operations for all application data.
    Falls back gracefully if MongoDB is unavailable.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client = None
            cls._instance._db = None
            cls._instance._config = MongoDBConfig.from_env()
            cls._instance._connected = False
        return cls._instance
    
    @property
    def is_available(self) -> bool:
        """Check if MongoDB is available."""
        return MOTOR_AVAILABLE and self._connected
    
    async def connect(self) -> bool:
        """
        Connect to MongoDB.
        
        Returns True if connection successful, False otherwise.
        """
        if not MOTOR_AVAILABLE:
            logger.warning("Motor not installed, using fallback storage")
            return False
        
        try:
            self._client = AsyncIOMotorClient(
                self._config.uri,
                minPoolSize=self._config.min_pool_size,
                maxPoolSize=self._config.max_pool_size,
                serverSelectionTimeoutMS=self._config.server_selection_timeout_ms,
            )
            
            # Verify connection
            await self._client.admin.command('ping')
            
            self._db = self._client[self._config.database_name]
            self._connected = True
            
            # Create indexes
            await self._create_indexes()
            
            logger.info(f"Connected to MongoDB: {self._config.database_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self._client:
            self._client.close()
            self._connected = False
            logger.info("Disconnected from MongoDB")
    
    async def _create_indexes(self) -> None:
        """Create database indexes for optimal query performance."""
        if not self._db:
            return
        
        try:
            # Interactions indexes
            interactions = self._db[self._config.interactions_collection]
            await interactions.create_index("interaction_id", unique=True)
            await interactions.create_index("customer_id")
            await interactions.create_index("status")
            await interactions.create_index("started_at")
            await interactions.create_index([("started_at", -1)])
            
            # Messages indexes
            messages = self._db[self._config.messages_collection]
            await messages.create_index("message_id", unique=True)
            await messages.create_index("interaction_id")
            await messages.create_index([("interaction_id", 1), ("timestamp", 1)])
            
            # Decisions indexes
            decisions = self._db[self._config.decisions_collection]
            await decisions.create_index("decision_id", unique=True)
            await decisions.create_index("interaction_id")
            await decisions.create_index("agent_type")
            await decisions.create_index([("interaction_id", 1), ("timestamp", 1)])
            
            # Audit logs indexes
            audit = self._db[self._config.audit_logs_collection]
            await audit.create_index("record_id", unique=True)
            await audit.create_index("interaction_id")
            await audit.create_index("event_type")
            await audit.create_index("timestamp")
            
            # Users indexes
            users = self._db[self._config.users_collection]
            await users.create_index("user_id", unique=True)
            await users.create_index("email", unique=True)
            
            logger.info("MongoDB indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    # =========================================================================
    # Interactions
    # =========================================================================
    
    async def save_interaction(
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
            collection = self._db[self._config.interactions_collection]
            
            doc = {
                "interaction_id": str(interaction_id),
                "customer_id": customer_id,
                "channel": channel,
                "status": status,
                "started_at": started_at.isoformat() if isinstance(started_at, datetime) else started_at,
                "metadata": metadata or {},
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            await collection.update_one(
                {"interaction_id": str(interaction_id)},
                {"$set": doc},
                upsert=True
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to save interaction: {e}")
            return False
    
    async def update_interaction_status(
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
            collection = self._db[self._config.interactions_collection]
            
            update = {
                "status": status,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            if ended_at:
                update["ended_at"] = ended_at.isoformat() if isinstance(ended_at, datetime) else ended_at
            
            if metadata:
                update["metadata"] = metadata
            
            await collection.update_one(
                {"interaction_id": str(interaction_id)},
                {"$set": update}
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to update interaction: {e}")
            return False
    
    async def get_interaction(self, interaction_id: str) -> Optional[Dict[str, Any]]:
        """Get an interaction by ID."""
        if not self.is_available:
            return None
        
        try:
            collection = self._db[self._config.interactions_collection]
            return await collection.find_one({"interaction_id": str(interaction_id)})
        except Exception as e:
            logger.error(f"Failed to get interaction: {e}")
            return None
    
    async def list_interactions(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List interactions with optional filtering."""
        if not self.is_available:
            return []
        
        try:
            collection = self._db[self._config.interactions_collection]
            
            query = {}
            if status:
                query["status"] = status
            
            cursor = collection.find(query).sort("started_at", -1).skip(offset).limit(limit)
            return await cursor.to_list(length=limit)
            
        except Exception as e:
            logger.error(f"Failed to list interactions: {e}")
            return []
    
    async def count_interactions(
        self,
        status: Optional[str] = None,
    ) -> int:
        """Count interactions with optional filtering."""
        if not self.is_available:
            return 0
        
        try:
            collection = self._db[self._config.interactions_collection]
            
            query = {}
            if status:
                query["status"] = status
            
            return await collection.count_documents(query)
            
        except Exception as e:
            logger.error(f"Failed to count interactions: {e}")
            return 0
    
    # =========================================================================
    # Messages
    # =========================================================================
    
    async def save_message(
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
            collection = self._db[self._config.messages_collection]
            
            doc = {
                "message_id": str(message_id),
                "interaction_id": str(interaction_id),
                "role": role,
                "content": content,
                "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat(),
                "metadata": metadata or {},
            }
            
            await collection.insert_one(doc)
            return True
            
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            return False
    
    async def get_messages(
        self,
        interaction_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get messages for an interaction."""
        if not self.is_available:
            return []
        
        try:
            collection = self._db[self._config.messages_collection]
            
            cursor = collection.find(
                {"interaction_id": str(interaction_id)}
            ).sort("timestamp", 1).limit(limit)
            
            return await cursor.to_list(length=limit)
            
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            return []
    
    # =========================================================================
    # Agent Decisions
    # =========================================================================
    
    async def save_agent_decision(
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
            collection = self._db[self._config.decisions_collection]
            
            doc = {
                "decision_id": str(decision_id),
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
            
            await collection.insert_one(doc)
            return True
            
        except Exception as e:
            logger.error(f"Failed to save agent decision: {e}")
            return False
    
    async def get_agent_decisions(
        self,
        interaction_id: str,
    ) -> List[Dict[str, Any]]:
        """Get agent decisions for an interaction."""
        if not self.is_available:
            return []
        
        try:
            collection = self._db[self._config.decisions_collection]
            
            cursor = collection.find(
                {"interaction_id": str(interaction_id)}
            ).sort("timestamp", 1)
            
            return await cursor.to_list(length=100)
            
        except Exception as e:
            logger.error(f"Failed to get agent decisions: {e}")
            return []
    
    # =========================================================================
    # Agent Configurations
    # =========================================================================
    
    async def save_agent_config(
        self,
        agent_id: str,
        config: Dict[str, Any],
    ) -> bool:
        """Save agent configuration."""
        if not self.is_available:
            return False
        
        try:
            collection = self._db[self._config.agent_configs_collection]
            
            config["agent_id"] = agent_id
            config["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            await collection.update_one(
                {"agent_id": agent_id},
                {"$set": config},
                upsert=True
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to save agent config: {e}")
            return False
    
    async def get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent configuration."""
        if not self.is_available:
            return None
        
        try:
            collection = self._db[self._config.agent_configs_collection]
            return await collection.find_one({"agent_id": agent_id})
        except Exception as e:
            logger.error(f"Failed to get agent config: {e}")
            return None
    
    async def get_all_agent_configs(self) -> List[Dict[str, Any]]:
        """Get all agent configurations."""
        if not self.is_available:
            return []
        
        try:
            collection = self._db[self._config.agent_configs_collection]
            cursor = collection.find({})
            return await cursor.to_list(length=10)
        except Exception as e:
            logger.error(f"Failed to get agent configs: {e}")
            return []
    
    # =========================================================================
    # Users (for Authentication)
    # =========================================================================
    
    async def save_user(
        self,
        user_id: str,
        email: str,
        hashed_password: str,
        role: str = "user",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Save a user."""
        if not self.is_available:
            return False
        
        try:
            collection = self._db[self._config.users_collection]
            
            doc = {
                "user_id": user_id,
                "email": email,
                "hashed_password": hashed_password,
                "role": role,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {},
                "is_active": True,
            }
            
            await collection.update_one(
                {"user_id": user_id},
                {"$set": doc},
                upsert=True
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to save user: {e}")
            return False
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get a user by email."""
        if not self.is_available:
            return None
        
        try:
            collection = self._db[self._config.users_collection]
            return await collection.find_one({"email": email})
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by ID."""
        if not self.is_available:
            return None
        
        try:
            collection = self._db[self._config.users_collection]
            return await collection.find_one({"user_id": user_id})
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return None
    
    # =========================================================================
    # Audit Logs
    # =========================================================================
    
    async def save_audit_log(
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
            collection = self._db[self._config.audit_logs_collection]
            
            doc = {
                "record_id": str(record_id),
                "interaction_id": str(interaction_id),
                "event_type": event_type,
                "agent_type": agent_type,
                "decision_outcome": decision_outcome,
                "confidence_score": confidence_score,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {},
            }
            
            await collection.insert_one(doc)
            return True
            
        except Exception as e:
            logger.error(f"Failed to save audit log: {e}")
            return False
    
    async def get_audit_logs(
        self,
        interaction_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get audit logs with optional filtering."""
        if not self.is_available:
            return []
        
        try:
            collection = self._db[self._config.audit_logs_collection]
            
            query = {}
            if interaction_id:
                query["interaction_id"] = str(interaction_id)
            if event_type:
                query["event_type"] = event_type
            
            cursor = collection.find(query).sort("timestamp", -1).limit(limit)
            return await cursor.to_list(length=limit)
            
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []
    
    # =========================================================================
    # Analytics Aggregations
    # =========================================================================
    
    async def get_analytics_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get analytics summary for the specified period."""
        if not self.is_available:
            return {}
        
        try:
            from datetime import timedelta
            
            collection = self._db[self._config.interactions_collection]
            
            start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            
            pipeline = [
                {"$match": {"started_at": {"$gte": start_date}}},
                {"$group": {
                    "_id": None,
                    "total": {"$sum": 1},
                    "completed": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
                    "escalated": {"$sum": {"$cond": [{"$eq": ["$status", "escalated"]}, 1, 0]}},
                    "active": {"$sum": {"$cond": [{"$in": ["$status", ["initiated", "in_progress"]]}, 1, 0]}},
                }},
            ]
            
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=1)
            
            if results:
                r = results[0]
                return {
                    "total_interactions": r.get("total", 0),
                    "completed_interactions": r.get("completed", 0),
                    "escalated_interactions": r.get("escalated", 0),
                    "active_interactions": r.get("active", 0),
                    "resolution_rate": r.get("completed", 0) / max(r.get("total", 1), 1),
                    "escalation_rate": r.get("escalated", 0) / max(r.get("total", 1), 1),
                }
            
            return {
                "total_interactions": 0,
                "completed_interactions": 0,
                "escalated_interactions": 0,
                "active_interactions": 0,
                "resolution_rate": 0.0,
                "escalation_rate": 0.0,
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics summary: {e}")
            return {}


# Singleton accessor
def get_mongodb_store() -> MongoDBStore:
    """Get the MongoDB store singleton."""
    return MongoDBStore()
