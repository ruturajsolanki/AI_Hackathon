"""
Core Domain Models

Shared domain models representing the fundamental entities of the
AI-powered call center. These models are persistence-agnostic and
contain no business logic.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Enumerations
# -----------------------------------------------------------------------------

class ChannelType(str, Enum):
    """Communication channel types."""
    VOICE = "voice"
    CHAT = "chat"
    EMAIL = "email"


class InteractionStatus(str, Enum):
    """Status of a customer interaction."""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    AWAITING_RESPONSE = "awaiting_response"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    ABANDONED = "abandoned"


class IntentCategory(str, Enum):
    """Categories of customer intent."""
    BILLING_INQUIRY = "billing_inquiry"
    TECHNICAL_SUPPORT = "technical_support"
    ACCOUNT_MANAGEMENT = "account_management"
    PRODUCT_INFORMATION = "product_information"
    COMPLAINT = "complaint"
    FEEDBACK = "feedback"
    ORDER_STATUS = "order_status"
    CANCELLATION = "cancellation"
    GENERAL_INQUIRY = "general_inquiry"
    UNKNOWN = "unknown"


class EmotionalState(str, Enum):
    """Detected emotional states."""
    NEUTRAL = "neutral"
    SATISFIED = "satisfied"
    FRUSTRATED = "frustrated"
    CONFUSED = "confused"
    URGENT = "urgent"
    ANGRY = "angry"
    ANXIOUS = "anxious"


class AgentType(str, Enum):
    """Types of agents in the system."""
    PRIMARY = "primary"
    SUPERVISOR = "supervisor"
    ESCALATION = "escalation"
    HUMAN = "human"


class DecisionType(str, Enum):
    """Types of decisions made by agents."""
    RESPOND = "respond"
    CLARIFY = "clarify"
    ESCALATE = "escalate"
    TRANSFER = "transfer"
    RESOLVE = "resolve"
    DEFER = "defer"


class ConfidenceLevel(str, Enum):
    """Confidence level classifications."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


class EscalationReason(str, Enum):
    """Reasons for escalation."""
    LOW_CONFIDENCE = "low_confidence"
    EMOTIONAL_DISTRESS = "emotional_distress"
    COMPLEX_ISSUE = "complex_issue"
    CUSTOMER_REQUEST = "customer_request"
    POLICY_VIOLATION = "policy_violation"
    SAFETY_CONCERN = "safety_concern"
    REPEATED_FAILURE = "repeated_failure"


class EscalationStatus(str, Enum):
    """Status of an escalation."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    RETURNED = "returned"


# -----------------------------------------------------------------------------
# Core Domain Models
# -----------------------------------------------------------------------------

class CustomerInteraction(BaseModel):
    """
    Represents a single customer interaction session.
    
    This is the primary entity tracking a customer's engagement
    from initiation through resolution.
    """
    interaction_id: UUID = Field(description="Unique identifier for this interaction")
    customer_id: Optional[str] = Field(default=None, description="Customer identifier if authenticated")
    channel: ChannelType = Field(description="Communication channel used")
    status: InteractionStatus = Field(default=InteractionStatus.INITIATED)
    
    # Timing
    started_at: datetime = Field(description="When the interaction began")
    ended_at: Optional[datetime] = Field(default=None, description="When the interaction concluded")
    
    # Classification
    detected_intent: Optional[IntentCategory] = Field(default=None)
    detected_emotion: Optional[EmotionalState] = Field(default=None)
    
    # Routing
    assigned_agent_type: AgentType = Field(default=AgentType.PRIMARY)
    escalation_count: int = Field(default=0, description="Number of times escalated")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "interaction_id": "550e8400-e29b-41d4-a716-446655440000",
                "customer_id": "CUST-12345",
                "channel": "chat",
                "status": "in_progress",
                "started_at": "2024-01-15T10:30:00Z",
                "detected_intent": "billing_inquiry",
                "detected_emotion": "neutral",
                "assigned_agent_type": "primary",
                "escalation_count": 0
            }
        }


class AgentDecision(BaseModel):
    """
    Represents a decision made by an AI agent.
    
    Captures the reasoning and confidence behind each decision
    to support explainability and audit requirements.
    """
    decision_id: UUID = Field(description="Unique identifier for this decision")
    interaction_id: UUID = Field(description="Associated interaction")
    agent_type: AgentType = Field(description="Agent that made this decision")
    
    # Decision details
    decision_type: DecisionType = Field(description="Type of decision made")
    decision_summary: str = Field(description="Human-readable summary of the decision")
    
    # Confidence and reasoning
    confidence_level: ConfidenceLevel = Field(description="Confidence classification")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Numeric confidence score")
    reasoning_factors: List[str] = Field(
        default_factory=list,
        description="Factors that contributed to this decision"
    )
    
    # Context at decision time
    detected_intent: Optional[IntentCategory] = Field(default=None)
    detected_emotion: Optional[EmotionalState] = Field(default=None)
    
    # Outcome
    action_taken: str = Field(description="Description of action executed")
    requires_followup: bool = Field(default=False)
    
    # Timing
    decided_at: datetime = Field(description="When the decision was made")
    
    # Audit
    reviewed_by_supervisor: bool = Field(default=False)
    supervisor_override: bool = Field(default=False)

    class Config:
        json_schema_extra = {
            "example": {
                "decision_id": "660e8400-e29b-41d4-a716-446655440001",
                "interaction_id": "550e8400-e29b-41d4-a716-446655440000",
                "agent_type": "primary",
                "decision_type": "respond",
                "decision_summary": "Provided billing statement explanation",
                "confidence_level": "high",
                "confidence_score": 0.92,
                "reasoning_factors": [
                    "Clear intent detected",
                    "Standard billing inquiry",
                    "Customer emotion neutral"
                ],
                "detected_intent": "billing_inquiry",
                "detected_emotion": "neutral",
                "action_taken": "Delivered billing breakdown response",
                "requires_followup": False,
                "decided_at": "2024-01-15T10:30:15Z",
                "reviewed_by_supervisor": False,
                "supervisor_override": False
            }
        }


class EscalationOutcome(BaseModel):
    """
    Represents the outcome of an escalation event.
    
    Tracks the full lifecycle of an escalation from trigger
    through resolution.
    """
    escalation_id: UUID = Field(description="Unique identifier for this escalation")
    interaction_id: UUID = Field(description="Associated interaction")
    
    # Escalation trigger
    reason: EscalationReason = Field(description="Why escalation was triggered")
    triggered_by: AgentType = Field(description="Agent that initiated escalation")
    trigger_decision_id: Optional[UUID] = Field(
        default=None,
        description="Decision that triggered this escalation"
    )
    
    # Status tracking
    status: EscalationStatus = Field(default=EscalationStatus.PENDING)
    escalated_to: AgentType = Field(description="Target agent for escalation")
    
    # Context passed
    context_summary: str = Field(description="Summary of context passed to receiving agent")
    priority_level: int = Field(ge=1, le=5, description="Priority 1 (highest) to 5 (lowest)")
    
    # Timing
    escalated_at: datetime = Field(description="When escalation was triggered")
    accepted_at: Optional[datetime] = Field(default=None)
    resolved_at: Optional[datetime] = Field(default=None)
    
    # Resolution
    resolution_summary: Optional[str] = Field(
        default=None,
        description="How the escalation was resolved"
    )
    returned_to_ai: bool = Field(
        default=False,
        description="Whether control was returned to AI agent"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "escalation_id": "770e8400-e29b-41d4-a716-446655440002",
                "interaction_id": "550e8400-e29b-41d4-a716-446655440000",
                "reason": "emotional_distress",
                "triggered_by": "supervisor",
                "status": "resolved",
                "escalated_to": "human",
                "context_summary": "Customer expressing frustration over repeated billing errors",
                "priority_level": 2,
                "escalated_at": "2024-01-15T10:35:00Z",
                "accepted_at": "2024-01-15T10:35:30Z",
                "resolved_at": "2024-01-15T10:45:00Z",
                "resolution_summary": "Human agent provided billing credit and apology",
                "returned_to_ai": False
            }
        }


class ConversationContext(BaseModel):
    """
    Represents the accumulated context of a conversation.
    
    Provides agents with the information needed to make
    informed, contextual decisions.
    """
    interaction_id: UUID = Field(description="Associated interaction")
    
    # Customer profile
    customer_id: Optional[str] = Field(default=None)
    customer_tier: Optional[str] = Field(default=None, description="Customer service tier")
    interaction_history_count: int = Field(
        default=0,
        description="Number of previous interactions"
    )
    
    # Current conversation state
    turn_count: int = Field(default=0, description="Number of conversation turns")
    current_intent: Optional[IntentCategory] = Field(default=None)
    current_emotion: Optional[EmotionalState] = Field(default=None)
    intent_history: List[IntentCategory] = Field(
        default_factory=list,
        description="Sequence of detected intents"
    )
    emotion_history: List[EmotionalState] = Field(
        default_factory=list,
        description="Sequence of detected emotions"
    )
    
    # Conversation summary
    key_topics: List[str] = Field(
        default_factory=list,
        description="Main topics discussed"
    )
    unresolved_issues: List[str] = Field(
        default_factory=list,
        description="Issues not yet addressed"
    )
    resolved_issues: List[str] = Field(
        default_factory=list,
        description="Issues successfully resolved"
    )
    
    # Agent coordination
    agents_involved: List[AgentType] = Field(default_factory=list)
    pending_actions: List[str] = Field(
        default_factory=list,
        description="Actions awaiting completion"
    )
    
    # Flags
    requires_human_review: bool = Field(default=False)
    sensitive_topic_detected: bool = Field(default=False)
    
    # Timing
    last_updated: datetime = Field(description="Last context update")

    class Config:
        json_schema_extra = {
            "example": {
                "interaction_id": "550e8400-e29b-41d4-a716-446655440000",
                "customer_id": "CUST-12345",
                "customer_tier": "premium",
                "interaction_history_count": 3,
                "turn_count": 5,
                "current_intent": "billing_inquiry",
                "current_emotion": "frustrated",
                "intent_history": ["general_inquiry", "billing_inquiry"],
                "emotion_history": ["neutral", "confused", "frustrated"],
                "key_topics": ["monthly statement", "unexpected charges"],
                "unresolved_issues": ["charge dispute"],
                "resolved_issues": ["statement access"],
                "agents_involved": ["primary", "supervisor"],
                "pending_actions": ["Review charge with billing team"],
                "requires_human_review": False,
                "sensitive_topic_detected": False,
                "last_updated": "2024-01-15T10:32:00Z"
            }
        }
