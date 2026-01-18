"""
Context Store

In-memory storage for conversation context, history, and agent decisions.
Designed for concurrent access and easy replacement with persistent storage.

This implementation is in-memory only - no external persistence.
"""

import asyncio
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Deque, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.models import (
    AgentDecision,
    AgentType,
    ConversationContext,
    ConfidenceLevel,
    EmotionalState,
    IntentCategory,
)


# -----------------------------------------------------------------------------
# Memory Models
# -----------------------------------------------------------------------------

class MessageRole(str, Enum):
    """Role of a message in conversation."""
    CUSTOMER = "customer"
    AGENT = "agent"
    SYSTEM = "system"


class ConversationMessage(BaseModel):
    """A single message in conversation history."""
    message_id: UUID
    interaction_id: UUID
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Classification at time of message
    detected_intent: Optional[IntentCategory] = None
    detected_emotion: Optional[EmotionalState] = None
    
    # Metadata
    agent_type: Optional[AgentType] = None
    confidence_score: Optional[float] = None
    metadata: Dict = Field(default_factory=dict)


class DecisionRecord(BaseModel):
    """Record of an agent decision for audit trail."""
    decision_id: UUID
    interaction_id: UUID
    agent_type: AgentType
    decision_summary: str
    confidence_level: ConfidenceLevel
    confidence_score: float
    reasoning: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Review status
    supervisor_approved: Optional[bool] = None
    supervisor_adjusted_confidence: Optional[float] = None


class ShortTermContext(BaseModel):
    """
    Short-term context for immediate use by agents.
    
    Contains recent messages and decisions relevant to
    the current turn.
    """
    interaction_id: UUID
    
    # Recent history (configurable window)
    recent_messages: List[ConversationMessage] = Field(default_factory=list)
    recent_decisions: List[DecisionRecord] = Field(default_factory=list)
    
    # Current state
    turn_count: int = 0
    current_intent: Optional[IntentCategory] = None
    current_emotion: Optional[EmotionalState] = None
    
    # Aggregated signals
    intent_history: List[IntentCategory] = Field(default_factory=list)
    emotion_history: List[EmotionalState] = Field(default_factory=list)
    confidence_trend: List[float] = Field(default_factory=list)
    
    # Flags
    has_escalation_history: bool = False
    sensitive_topic_detected: bool = False
    
    # Summary
    key_topics: List[str] = Field(default_factory=list)
    unresolved_issues: List[str] = Field(default_factory=list)


@dataclass
class InteractionMemory:
    """
    Complete memory store for a single interaction.
    
    Contains full history and derived context.
    """
    interaction_id: UUID
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Full history (unbounded)
    messages: Deque[ConversationMessage] = field(default_factory=deque)
    decisions: Deque[DecisionRecord] = field(default_factory=deque)
    
    # Context (updated each turn)
    context: Optional[ConversationContext] = None
    
    # Lock for concurrent access
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    
    # Configuration
    max_short_term_messages: int = 10
    max_short_term_decisions: int = 5


# -----------------------------------------------------------------------------
# Context Store
# -----------------------------------------------------------------------------

class ContextStore:
    """
    In-memory context and conversation storage.
    
    Responsibilities:
    - Maintaining conversation history per interaction
    - Storing agent decisions with confidence levels
    - Providing short-term context for agents
    - Supporting concurrent access safely
    
    Does NOT:
    - Persist to external storage
    - Handle cross-session memory
    - Manage customer profiles
    
    Designed for easy replacement with persistent storage later.
    """

    def __init__(
        self,
        max_short_term_messages: int = 10,
        max_short_term_decisions: int = 5,
    ):
        """
        Initialize the context store.
        
        Args:
            max_short_term_messages: Max messages in short-term context.
            max_short_term_decisions: Max decisions in short-term context.
        """
        self._interactions: Dict[UUID, InteractionMemory] = {}
        self._global_lock = asyncio.Lock()
        self._max_short_term_messages = max_short_term_messages
        self._max_short_term_decisions = max_short_term_decisions

    async def create_interaction(
        self,
        interaction_id: UUID,
        initial_context: Optional[ConversationContext] = None,
    ) -> InteractionMemory:
        """
        Create memory store for a new interaction.
        
        Args:
            interaction_id: Unique interaction identifier.
            initial_context: Optional initial conversation context.
            
        Returns:
            New InteractionMemory instance.
        """
        async with self._global_lock:
            if interaction_id in self._interactions:
                return self._interactions[interaction_id]
            
            memory = InteractionMemory(
                interaction_id=interaction_id,
                context=initial_context,
                max_short_term_messages=self._max_short_term_messages,
                max_short_term_decisions=self._max_short_term_decisions,
            )
            self._interactions[interaction_id] = memory
            return memory

    async def get_interaction(
        self,
        interaction_id: UUID,
    ) -> Optional[InteractionMemory]:
        """
        Get memory store for an interaction.
        
        Args:
            interaction_id: Interaction to retrieve.
            
        Returns:
            InteractionMemory if exists, None otherwise.
        """
        return self._interactions.get(interaction_id)

    async def add_message(
        self,
        interaction_id: UUID,
        message: ConversationMessage,
    ) -> bool:
        """
        Add a message to conversation history.
        
        Args:
            interaction_id: Target interaction.
            message: Message to add.
            
        Returns:
            True if added successfully, False if interaction not found.
        """
        memory = self._interactions.get(interaction_id)
        if not memory:
            return False
        
        async with memory._lock:
            memory.messages.append(message)
            
            # Update context if available
            if memory.context:
                memory.context.turn_count = len(memory.messages)
                if message.detected_intent:
                    memory.context.current_intent = message.detected_intent
                    memory.context.intent_history.append(message.detected_intent)
                if message.detected_emotion:
                    memory.context.current_emotion = message.detected_emotion
                    memory.context.emotion_history.append(message.detected_emotion)
                memory.context.last_updated = datetime.now(timezone.utc)
        
        return True

    async def add_decision(
        self,
        interaction_id: UUID,
        decision: DecisionRecord,
    ) -> bool:
        """
        Add an agent decision to history.
        
        Args:
            interaction_id: Target interaction.
            decision: Decision record to add.
            
        Returns:
            True if added successfully, False if interaction not found.
        """
        memory = self._interactions.get(interaction_id)
        if not memory:
            return False
        
        async with memory._lock:
            memory.decisions.append(decision)
        
        return True

    async def get_short_term_context(
        self,
        interaction_id: UUID,
    ) -> Optional[ShortTermContext]:
        """
        Get short-term context for immediate agent use.
        
        Returns recent messages, decisions, and derived signals
        within the configured window.
        
        Args:
            interaction_id: Target interaction.
            
        Returns:
            ShortTermContext if interaction exists, None otherwise.
        """
        memory = self._interactions.get(interaction_id)
        if not memory:
            return None
        
        async with memory._lock:
            # Get recent messages
            recent_messages = list(memory.messages)[-memory.max_short_term_messages:]
            
            # Get recent decisions
            recent_decisions = list(memory.decisions)[-memory.max_short_term_decisions:]
            
            # Extract histories
            intent_history = [
                m.detected_intent for m in memory.messages
                if m.detected_intent is not None
            ]
            emotion_history = [
                m.detected_emotion for m in memory.messages
                if m.detected_emotion is not None
            ]
            confidence_trend = [
                d.confidence_score for d in memory.decisions
            ]
            
            # Determine current state
            current_intent = intent_history[-1] if intent_history else None
            current_emotion = emotion_history[-1] if emotion_history else None
            
            # Check for escalation history
            has_escalation = any(
                d.agent_type == AgentType.ESCALATION for d in memory.decisions
            )
            
            # Get topics and issues from context
            key_topics = []
            unresolved_issues = []
            sensitive_detected = False
            if memory.context:
                key_topics = memory.context.key_topics
                unresolved_issues = memory.context.unresolved_issues
                sensitive_detected = memory.context.sensitive_topic_detected
            
            return ShortTermContext(
                interaction_id=interaction_id,
                recent_messages=recent_messages,
                recent_decisions=recent_decisions,
                turn_count=len(memory.messages),
                current_intent=current_intent,
                current_emotion=current_emotion,
                intent_history=intent_history[-10:],  # Last 10
                emotion_history=emotion_history[-10:],
                confidence_trend=confidence_trend[-10:],
                has_escalation_history=has_escalation,
                sensitive_topic_detected=sensitive_detected,
                key_topics=key_topics,
                unresolved_issues=unresolved_issues,
            )

    async def get_full_history(
        self,
        interaction_id: UUID,
    ) -> Optional[List[ConversationMessage]]:
        """
        Get complete conversation history.
        
        Args:
            interaction_id: Target interaction.
            
        Returns:
            List of all messages if interaction exists.
        """
        memory = self._interactions.get(interaction_id)
        if not memory:
            return None
        
        async with memory._lock:
            return list(memory.messages)

    async def get_decision_history(
        self,
        interaction_id: UUID,
    ) -> Optional[List[DecisionRecord]]:
        """
        Get complete decision history.
        
        Args:
            interaction_id: Target interaction.
            
        Returns:
            List of all decisions if interaction exists.
        """
        memory = self._interactions.get(interaction_id)
        if not memory:
            return None
        
        async with memory._lock:
            return list(memory.decisions)

    async def update_context(
        self,
        interaction_id: UUID,
        context: ConversationContext,
    ) -> bool:
        """
        Update the conversation context.
        
        Args:
            interaction_id: Target interaction.
            context: New context to set.
            
        Returns:
            True if updated, False if interaction not found.
        """
        memory = self._interactions.get(interaction_id)
        if not memory:
            return False
        
        async with memory._lock:
            memory.context = context
        
        return True

    async def add_topic(
        self,
        interaction_id: UUID,
        topic: str,
    ) -> bool:
        """
        Add a topic to the conversation context.
        
        Args:
            interaction_id: Target interaction.
            topic: Topic to add.
            
        Returns:
            True if added, False if interaction not found.
        """
        memory = self._interactions.get(interaction_id)
        if not memory or not memory.context:
            return False
        
        async with memory._lock:
            if topic not in memory.context.key_topics:
                memory.context.key_topics.append(topic)
        
        return True

    async def add_unresolved_issue(
        self,
        interaction_id: UUID,
        issue: str,
    ) -> bool:
        """
        Add an unresolved issue.
        
        Args:
            interaction_id: Target interaction.
            issue: Issue description.
            
        Returns:
            True if added, False if interaction not found.
        """
        memory = self._interactions.get(interaction_id)
        if not memory or not memory.context:
            return False
        
        async with memory._lock:
            if issue not in memory.context.unresolved_issues:
                memory.context.unresolved_issues.append(issue)
        
        return True

    async def resolve_issue(
        self,
        interaction_id: UUID,
        issue: str,
    ) -> bool:
        """
        Mark an issue as resolved.
        
        Moves from unresolved to resolved list.
        
        Args:
            interaction_id: Target interaction.
            issue: Issue that was resolved.
            
        Returns:
            True if resolved, False if not found.
        """
        memory = self._interactions.get(interaction_id)
        if not memory or not memory.context:
            return False
        
        async with memory._lock:
            if issue in memory.context.unresolved_issues:
                memory.context.unresolved_issues.remove(issue)
                memory.context.resolved_issues.append(issue)
                return True
        
        return False

    async def mark_sensitive(
        self,
        interaction_id: UUID,
    ) -> bool:
        """
        Mark interaction as containing sensitive topics.
        
        Args:
            interaction_id: Target interaction.
            
        Returns:
            True if marked, False if not found.
        """
        memory = self._interactions.get(interaction_id)
        if not memory or not memory.context:
            return False
        
        async with memory._lock:
            memory.context.sensitive_topic_detected = True
        
        return True

    async def get_confidence_average(
        self,
        interaction_id: UUID,
    ) -> Optional[float]:
        """
        Get average confidence score for the interaction.
        
        Args:
            interaction_id: Target interaction.
            
        Returns:
            Average confidence or None if no decisions.
        """
        memory = self._interactions.get(interaction_id)
        if not memory or len(memory.decisions) == 0:
            return None
        
        async with memory._lock:
            scores = [d.confidence_score for d in memory.decisions]
            return sum(scores) / len(scores) if scores else None

    async def end_interaction(
        self,
        interaction_id: UUID,
    ) -> Optional[InteractionMemory]:
        """
        End interaction and remove from active storage.
        
        Returns the complete memory for persistence/logging.
        
        Args:
            interaction_id: Interaction to end.
            
        Returns:
            Final InteractionMemory if existed.
        """
        async with self._global_lock:
            return self._interactions.pop(interaction_id, None)

    async def get_active_count(self) -> int:
        """Get count of active interactions in memory."""
        return len(self._interactions)

    async def clear_all(self) -> int:
        """
        Clear all interactions from memory.
        
        Returns count of cleared interactions.
        Use with caution - primarily for testing.
        """
        async with self._global_lock:
            count = len(self._interactions)
            self._interactions.clear()
            return count

    async def get_conversation_for_llm(
        self,
        interaction_id: UUID,
        max_turns: int = 6,
    ) -> str:
        """
        Get formatted conversation history for LLM context.
        
        Returns recent messages in a format suitable for including
        in LLM prompts. This enables the AI to remember what was
        discussed earlier in the conversation.
        
        Args:
            interaction_id: Target interaction.
            max_turns: Maximum number of recent turns to include.
            
        Returns:
            Formatted string with conversation history, or empty string
            if no history exists.
        """
        memory = self._interactions.get(interaction_id)
        if not memory or len(memory.messages) == 0:
            return ""
        
        async with memory._lock:
            # Get recent messages
            recent = list(memory.messages)[-max_turns:]
            
            if not recent:
                return ""
            
            lines = ["=== Recent Conversation ==="]
            
            for msg in recent:
                role_display = "Customer" if msg.role == MessageRole.CUSTOMER else "Agent"
                timestamp = msg.timestamp.strftime("%H:%M:%S")
                lines.append(f"[{timestamp}] {role_display}: {msg.content}")
            
            lines.append("=== End Conversation ===")
            
            return "\n".join(lines)

    async def get_conversation_summary(
        self,
        interaction_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get a structured summary of the conversation for agent context.
        
        Returns:
            Dictionary with:
            - turn_count: Number of message exchanges
            - topics: Key topics discussed
            - issues: Unresolved issues
            - sentiment_trend: Is sentiment improving/declining
            - last_customer_message: Most recent customer input
            - last_agent_response: Most recent agent response
        """
        memory = self._interactions.get(interaction_id)
        if not memory:
            return {
                "turn_count": 0,
                "topics": [],
                "issues": [],
                "sentiment_trend": "neutral",
                "last_customer_message": None,
                "last_agent_response": None,
            }
        
        async with memory._lock:
            messages = list(memory.messages)
            
            # Find last customer and agent messages
            last_customer = None
            last_agent = None
            for msg in reversed(messages):
                if msg.role == MessageRole.CUSTOMER and last_customer is None:
                    last_customer = msg.content
                elif msg.role == MessageRole.AGENT and last_agent is None:
                    last_agent = msg.content
                if last_customer and last_agent:
                    break
            
            # Determine sentiment trend from emotion history
            emotion_history = [
                m.detected_emotion for m in messages 
                if m.detected_emotion is not None
            ]
            sentiment_trend = self._analyze_sentiment_trend(emotion_history)
            
            return {
                "turn_count": len(messages) // 2,  # Approximate exchanges
                "topics": memory.context.key_topics if memory.context else [],
                "issues": memory.context.unresolved_issues if memory.context else [],
                "sentiment_trend": sentiment_trend,
                "last_customer_message": last_customer,
                "last_agent_response": last_agent,
            }
    
    def _analyze_sentiment_trend(
        self,
        emotion_history: List[Optional[EmotionalState]],
    ) -> str:
        """
        Analyze sentiment trend from emotion history.
        
        Returns 'improving', 'declining', or 'stable'.
        """
        if len(emotion_history) < 2:
            return "stable"
        
        # Score emotions: positive = higher, negative = lower
        emotion_scores = {
            EmotionalState.SATISFIED: 5,
            EmotionalState.NEUTRAL: 3,
            EmotionalState.CONFUSED: 2,
            EmotionalState.ANXIOUS: 2,
            EmotionalState.FRUSTRATED: 1,
            EmotionalState.ANGRY: 0,
        }
        
        # Get scores for last few emotions
        recent = emotion_history[-3:]
        scores = [emotion_scores.get(e, 3) for e in recent if e is not None]
        
        if len(scores) < 2:
            return "stable"
        
        # Compare first vs last half
        first_avg = sum(scores[:len(scores)//2]) / max(1, len(scores)//2)
        second_avg = sum(scores[len(scores)//2:]) / max(1, len(scores) - len(scores)//2)
        
        diff = second_avg - first_avg
        if diff > 0.5:
            return "improving"
        elif diff < -0.5:
            return "declining"
        return "stable"
