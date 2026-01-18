"""
Human Handoff Service

Generates comprehensive summaries and context for human agents
when AI escalates a call. Ensures smooth transition with all
relevant information.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field


class EscalationPriority(str, Enum):
    """Priority levels for escalated calls."""
    CRITICAL = "critical"   # Angry customer, high-value issue
    HIGH = "high"           # Frustrated, multiple AI attempts failed
    MEDIUM = "medium"       # Confused, needs human touch
    LOW = "low"             # Prefers human, no urgency


class SentimentPoint(BaseModel):
    """A point in the sentiment timeline."""
    timestamp: datetime
    emotion: str
    message_preview: str
    confidence: float


class HandoffSummary(BaseModel):
    """
    Comprehensive summary for human agent handoff.
    
    Contains everything a human agent needs to seamlessly
    take over from the AI.
    """
    # Identification
    interaction_id: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Priority
    priority: EscalationPriority
    priority_reason: str
    
    # Customer Context
    customer_intent: str
    current_emotion: str
    emotion_trajectory: str  # e.g., "neutral → frustrated → angry"
    
    # Conversation Summary
    total_messages: int
    ai_response_count: int
    conversation_duration_seconds: int
    
    # Issue Details
    issue_summary: str
    key_points: List[str]
    customer_requests: List[str]
    
    # AI Performance
    ai_attempts: int
    average_confidence: float
    escalation_reason: str
    what_ai_tried: List[str]
    
    # Recommendations
    suggested_actions: List[str]
    relevant_policies: List[str]
    similar_cases_resolved: Optional[str] = None
    
    # Full Transcript
    transcript: List[Dict[str, Any]]


class HandoffService:
    """
    Service for generating human handoff summaries.
    
    Analyzes the conversation history and AI decisions to create
    a comprehensive briefing for the human agent.
    """
    
    def generate_handoff_summary(
        self,
        interaction_id: UUID,
        messages: List[Dict[str, Any]],
        agent_decisions: List[Dict[str, Any]],
        escalation_reason: str,
        final_confidence: float,
    ) -> HandoffSummary:
        """
        Generate a comprehensive handoff summary for human agents.
        
        Args:
            interaction_id: The interaction being escalated
            messages: Full conversation history
            agent_decisions: All AI agent decisions made
            escalation_reason: Why the AI escalated
            final_confidence: Last confidence score
            
        Returns:
            HandoffSummary with all context for human agent
        """
        # Analyze conversation
        customer_messages = [m for m in messages if m.get("role") == "customer"]
        ai_messages = [m for m in messages if m.get("role") in ("agent", "assistant")]
        
        # Extract emotions from decisions
        emotions = self._extract_emotion_trajectory(agent_decisions)
        current_emotion = emotions[-1] if emotions else "unknown"
        emotion_trajectory = " → ".join(emotions) if emotions else "unknown"
        
        # Determine priority
        priority, priority_reason = self._calculate_priority(
            current_emotion, 
            escalation_reason, 
            final_confidence,
            len(ai_messages)
        )
        
        # Extract key information
        intent = self._extract_intent(agent_decisions)
        key_points = self._extract_key_points(customer_messages)
        customer_requests = self._extract_requests(customer_messages)
        
        # Analyze AI attempts
        what_ai_tried = self._analyze_ai_attempts(ai_messages, agent_decisions)
        avg_confidence = self._calculate_avg_confidence(agent_decisions)
        
        # Generate recommendations
        suggested_actions = self._generate_suggestions(
            intent, current_emotion, escalation_reason, key_points
        )
        relevant_policies = self._get_relevant_policies(intent)
        
        # Build summary
        issue_summary = self._generate_issue_summary(
            intent, customer_messages, escalation_reason
        )
        
        # Calculate duration
        if messages:
            first_time = messages[0].get("timestamp", datetime.now(timezone.utc))
            last_time = messages[-1].get("timestamp", datetime.now(timezone.utc))
            if isinstance(first_time, str):
                first_time = datetime.fromisoformat(first_time.replace("Z", "+00:00"))
            if isinstance(last_time, str):
                last_time = datetime.fromisoformat(last_time.replace("Z", "+00:00"))
            duration = int((last_time - first_time).total_seconds())
        else:
            duration = 0
        
        return HandoffSummary(
            interaction_id=interaction_id,
            priority=priority,
            priority_reason=priority_reason,
            customer_intent=intent,
            current_emotion=current_emotion,
            emotion_trajectory=emotion_trajectory,
            total_messages=len(messages),
            ai_response_count=len(ai_messages),
            conversation_duration_seconds=duration,
            issue_summary=issue_summary,
            key_points=key_points[:5],  # Top 5
            customer_requests=customer_requests[:3],  # Top 3
            ai_attempts=len(ai_messages),
            average_confidence=avg_confidence,
            escalation_reason=escalation_reason,
            what_ai_tried=what_ai_tried[:4],  # Last 4 attempts
            suggested_actions=suggested_actions[:4],
            relevant_policies=relevant_policies[:3],
            transcript=messages,
        )
    
    def _calculate_priority(
        self,
        emotion: str,
        reason: str,
        confidence: float,
        ai_attempts: int,
    ) -> tuple[EscalationPriority, str]:
        """Calculate escalation priority based on context."""
        
        # Critical: Angry or very low confidence
        if emotion in ("angry", "furious") or confidence < 0.2:
            return EscalationPriority.CRITICAL, f"Customer is {emotion}, immediate attention needed"
        
        # High: Frustrated or many failed attempts
        if emotion == "frustrated" or ai_attempts >= 4:
            return EscalationPriority.HIGH, f"Multiple AI attempts failed ({ai_attempts})"
        
        # Medium: Confused or moderate issues
        if emotion in ("confused", "anxious") or "confidence" in reason.lower():
            return EscalationPriority.MEDIUM, "Customer needs human explanation"
        
        # Low: Preference or simple handoff
        return EscalationPriority.LOW, "Routine escalation"
    
    def _extract_emotion_trajectory(self, decisions: List[Dict]) -> List[str]:
        """Extract emotion changes through the conversation."""
        emotions = []
        for d in decisions:
            emotion = d.get("detected_emotion") or d.get("emotion")
            if emotion and (not emotions or emotions[-1] != emotion):
                emotions.append(emotion)
        return emotions if emotions else ["neutral"]
    
    def _extract_intent(self, decisions: List[Dict]) -> str:
        """Get the primary detected intent."""
        for d in reversed(decisions):
            intent = d.get("detected_intent") or d.get("intent")
            if intent:
                return intent
        return "general_inquiry"
    
    def _extract_key_points(self, customer_messages: List[Dict]) -> List[str]:
        """Extract key points from customer messages."""
        key_points = []
        keywords = ["$", "charge", "refund", "cancel", "broken", "not working", "help", "urgent"]
        
        for msg in customer_messages:
            content = msg.get("content", "")
            for keyword in keywords:
                if keyword.lower() in content.lower():
                    # Extract sentence containing keyword
                    sentences = content.split(".")
                    for sentence in sentences:
                        if keyword.lower() in sentence.lower() and len(sentence) > 10:
                            key_points.append(sentence.strip()[:100])
                            break
        
        return list(set(key_points))[:5]
    
    def _extract_requests(self, customer_messages: List[Dict]) -> List[str]:
        """Extract what the customer is asking for."""
        requests = []
        request_indicators = ["want", "need", "can you", "please", "could you", "would like"]
        
        for msg in customer_messages:
            content = msg.get("content", "").lower()
            for indicator in request_indicators:
                if indicator in content:
                    requests.append(msg.get("content", "")[:80])
                    break
        
        return requests
    
    def _analyze_ai_attempts(
        self, 
        ai_messages: List[Dict], 
        decisions: List[Dict]
    ) -> List[str]:
        """Summarize what the AI tried."""
        attempts = []
        
        for msg in ai_messages[-4:]:  # Last 4 AI responses
            content = msg.get("content", "")[:100]
            if content:
                attempts.append(f"Responded: \"{content}...\"")
        
        return attempts
    
    def _calculate_avg_confidence(self, decisions: List[Dict]) -> float:
        """Calculate average confidence across decisions."""
        confidences = []
        for d in decisions:
            conf = d.get("confidence") or d.get("overall_confidence")
            if conf:
                confidences.append(float(conf))
        
        return sum(confidences) / len(confidences) if confidences else 0.5
    
    def _generate_suggestions(
        self,
        intent: str,
        emotion: str,
        reason: str,
        key_points: List[str],
    ) -> List[str]:
        """Generate suggested actions for human agent."""
        suggestions = []
        
        # Based on intent
        if "billing" in intent.lower():
            suggestions.append("Review customer's billing history")
            suggestions.append("Check for any pending refunds or credits")
        
        if "technical" in intent.lower():
            suggestions.append("Verify customer's service status")
            suggestions.append("Check known issues in the area")
        
        if "cancel" in intent.lower():
            suggestions.append("Review cancellation policy")
            suggestions.append("Offer retention incentives if applicable")
        
        # Based on emotion
        if emotion in ("angry", "frustrated"):
            suggestions.insert(0, "Acknowledge customer's frustration first")
            suggestions.append("Consider offering goodwill gesture")
        
        # Based on key points
        for point in key_points:
            if "$" in point:
                suggestions.append("Review the specific charge mentioned")
                break
        
        # Default suggestions
        if not suggestions:
            suggestions = [
                "Listen to customer's full concern",
                "Verify account information",
                "Provide clear resolution timeline"
            ]
        
        return suggestions[:4]
    
    def _get_relevant_policies(self, intent: str) -> List[str]:
        """Get relevant policies based on intent."""
        policies = {
            "billing": ["Refund Policy (30 days)", "Dispute Resolution Process"],
            "technical": ["Service Level Agreement", "Escalation to Tier 2"],
            "cancel": ["Cancellation Terms", "Early Termination Fees"],
            "complaint": ["Complaint Resolution SLA", "Compensation Guidelines"],
        }
        
        for key, values in policies.items():
            if key in intent.lower():
                return values
        
        return ["General Service Guidelines"]
    
    def _generate_issue_summary(
        self,
        intent: str,
        customer_messages: List[Dict],
        escalation_reason: str,
    ) -> str:
        """Generate a one-paragraph issue summary."""
        if not customer_messages:
            return "Customer interaction escalated to human agent."
        
        first_msg = customer_messages[0].get("content", "")[:100]
        last_msg = customer_messages[-1].get("content", "")[:100] if len(customer_messages) > 1 else ""
        
        summary = f"Customer contacted about {intent.replace('_', ' ')}. "
        summary += f"Initial query: \"{first_msg}\" "
        
        if last_msg and last_msg != first_msg:
            summary += f"Most recent: \"{last_msg}\" "
        
        summary += f"Escalated because: {escalation_reason}."
        
        return summary


# Singleton instance
_handoff_service: Optional[HandoffService] = None


def get_handoff_service() -> HandoffService:
    """Get the singleton HandoffService instance."""
    global _handoff_service
    if _handoff_service is None:
        _handoff_service = HandoffService()
    return _handoff_service
