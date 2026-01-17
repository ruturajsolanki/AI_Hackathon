"""
Escalation Agent

The Escalation Agent makes final decisions about whether an interaction
requires escalation beyond AI handling. It consumes reviewed decisions
from the Supervisor Agent and determines the appropriate escalation path.

This implementation uses deterministic placeholder logic for demonstration.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.agents.base import (
    AgentInput,
    AgentOutput,
    BaseAgent,
    ConfidenceReport,
)
from app.agents.supervisor import (
    ComplianceStatus,
    ReviewFlag,
    RiskLevel,
    SupervisorReview,
)
from app.core.models import (
    AgentType,
    ConfidenceLevel,
    DecisionType,
    EmotionalState,
    EscalationOutcome,
    EscalationReason,
    EscalationStatus,
    IntentCategory,
)


# -----------------------------------------------------------------------------
# Escalation-Specific Models
# -----------------------------------------------------------------------------

class EscalationType(str, Enum):
    """Types of escalation actions."""
    NONE = "none"
    HUMAN_IMMEDIATE = "human_immediate"
    HUMAN_QUEUE = "human_queue"
    TICKET_CREATE = "ticket_create"
    RETRY_PRIMARY = "retry_primary"
    SUPERVISOR_OVERRIDE = "supervisor_override"


class EscalationDecision(BaseModel):
    """
    Structured escalation decision output.
    
    Contains the escalation determination and full reasoning chain.
    """
    decision_id: UUID = Field(default_factory=uuid4)
    interaction_id: UUID = Field(description="Associated interaction")
    
    # Decision
    should_escalate: bool = Field(description="Whether escalation is required")
    escalation_type: EscalationType = Field(description="Type of escalation action")
    escalation_reason: Optional[EscalationReason] = Field(default=None)
    
    # Priority
    priority: int = Field(
        ge=1, le=5,
        description="Priority level 1 (highest) to 5 (lowest)"
    )
    
    # Target
    target_agent: Optional[AgentType] = Field(
        default=None,
        description="Target agent for escalation"
    )
    
    # Context for handoff
    context_summary: str = Field(description="Summary for receiving party")
    key_issues: List[str] = Field(default_factory=list)
    attempted_resolutions: List[str] = Field(default_factory=list)
    
    # Reasoning
    reasoning: List[str] = Field(
        default_factory=list,
        description="Step-by-step reasoning for the decision"
    )
    contributing_factors: List[str] = Field(default_factory=list)
    
    # Timing
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    recommended_response_time: Optional[str] = Field(
        default=None,
        description="Suggested response time (e.g., 'immediate', '1 hour')"
    )

    def to_escalation_outcome(self) -> Optional[EscalationOutcome]:
        """Convert to EscalationOutcome for persistence."""
        if not self.should_escalate:
            return None
        
        return EscalationOutcome(
            escalation_id=uuid4(),
            interaction_id=self.interaction_id,
            reason=self.escalation_reason or EscalationReason.COMPLEX_ISSUE,
            triggered_by=AgentType.ESCALATION,
            trigger_decision_id=self.decision_id,
            status=EscalationStatus.PENDING,
            escalated_to=self.target_agent or AgentType.HUMAN,
            context_summary=self.context_summary,
            priority_level=self.priority,
            escalated_at=self.decided_at,
            accepted_at=None,
            resolved_at=None,
            resolution_summary=None,
            returned_to_ai=False,
        )


# -----------------------------------------------------------------------------
# Escalation Rules Configuration
# -----------------------------------------------------------------------------

# Flags that mandate immediate escalation
IMMEDIATE_ESCALATION_FLAGS: Set[ReviewFlag] = {
    ReviewFlag.POLICY_CONCERN,
    ReviewFlag.SENSITIVE_TOPIC,
}

# Flags that suggest escalation
SUGGESTED_ESCALATION_FLAGS: Set[ReviewFlag] = {
    ReviewFlag.ESCALATION_RECOMMENDED,
    ReviewFlag.EMOTION_UNADDRESSED,
    ReviewFlag.CONFIDENCE_TOO_LOW,
}

# Intent categories that prefer human handling
HUMAN_PREFERRED_INTENTS: Set[IntentCategory] = {
    IntentCategory.COMPLAINT,
    IntentCategory.CANCELLATION,
}

# Emotional states requiring human empathy
HUMAN_EMPATHY_EMOTIONS: Set[EmotionalState] = {
    EmotionalState.ANGRY,
}

# Priority mappings
RISK_TO_PRIORITY = {
    RiskLevel.CRITICAL: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.MEDIUM: 3,
    RiskLevel.LOW: 4,
    RiskLevel.NONE: 5,
}


class EscalationAgent(BaseAgent):
    """
    Escalation Agent for routing decisions.
    
    Responsible for:
    - Evaluating reviewed decisions for escalation need
    - Determining appropriate escalation type
    - Assigning priority levels
    - Generating handoff context
    - Producing explainable escalation decisions
    
    Does NOT:
    - Interact with customers
    - Review decision quality (Supervisor's role)
    - Execute the actual escalation (handled by services)
    """

    @property
    def agent_type(self) -> AgentType:
        """Return ESCALATION agent type."""
        return AgentType.ESCALATION

    async def process(self, input_data: AgentInput) -> AgentOutput:
        """
        Process is not the primary interface for EscalationAgent.
        Use evaluate_for_escalation() instead.
        
        This implementation provides minimal compatibility with BaseAgent.
        """
        confidence = await self.assess_confidence(
            input_data,
            DecisionType.DEFER,
        )
        
        return AgentOutput(
            decision_id=uuid4(),
            interaction_id=input_data.interaction_id,
            agent_type=self.agent_type,
            decision_type=DecisionType.DEFER,
            decision_summary="Escalation agent - no direct customer interaction",
            response_content=None,
            detected_intent=input_data.suggested_intent,
            detected_emotion=input_data.suggested_emotion,
            confidence=confidence,
            reasoning=["Escalation agent does not process customer messages directly"],
            requires_followup=False,
            recommended_actions=["Use evaluate_for_escalation() method"],
            escalation_target=None,
            context_updates={},
            processed_at=datetime.now(timezone.utc),
            processing_duration_ms=0,
        )

    async def assess_confidence(
        self,
        input_data: AgentInput,
        preliminary_decision: DecisionType,
    ) -> ConfidenceReport:
        """Assess confidence for escalation operations."""
        return ConfidenceReport(
            overall_score=0.95,
            level=ConfidenceLevel.HIGH,
            intent_confidence=0.95,
            emotion_confidence=0.95,
            context_confidence=0.95,
            factors=["Escalation rules are deterministic"],
            concerns=[],
            meets_autonomous_threshold=True,
            requires_supervision=False,
            requires_escalation=False,
        )

    async def evaluate_for_escalation(
        self,
        primary_output: AgentOutput,
        supervisor_review: SupervisorReview,
        original_input: AgentInput,
        escalation_history: Optional[List[EscalationOutcome]] = None,
    ) -> EscalationDecision:
        """
        Evaluate whether an interaction requires escalation.
        
        Decision flow:
        1. Check for mandatory escalation triggers
        2. Evaluate risk-based escalation
        3. Assess confidence-based escalation
        4. Check emotional escalation needs
        5. Determine escalation type
        6. Assign priority
        7. Generate handoff context
        
        Args:
            primary_output: Output from Primary Agent.
            supervisor_review: Review from Supervisor Agent.
            original_input: Original customer input.
            escalation_history: Previous escalations in this interaction.
            
        Returns:
            EscalationDecision with determination and reasoning.
        """
        reasoning = ["Initiating escalation evaluation"]
        contributing_factors: List[str] = []
        escalation_history = escalation_history or []
        
        # Step 1: Check mandatory escalation triggers
        mandatory_escalation, mandatory_reason = self._check_mandatory_triggers(
            supervisor_review,
            reasoning,
        )
        
        if mandatory_escalation:
            contributing_factors.append(f"Mandatory trigger: {mandatory_reason}")
        
        # Step 2: Risk-based evaluation
        risk_escalation, risk_reason = self._evaluate_risk_escalation(
            supervisor_review,
            reasoning,
        )
        
        if risk_escalation:
            contributing_factors.append(f"Risk factor: {risk_reason}")
        
        # Step 3: Confidence-based evaluation
        confidence_escalation, confidence_reason = self._evaluate_confidence_escalation(
            primary_output,
            supervisor_review,
            reasoning,
        )
        
        if confidence_escalation:
            contributing_factors.append(f"Confidence factor: {confidence_reason}")
        
        # Step 4: Emotional escalation needs
        emotional_escalation, emotional_reason = self._evaluate_emotional_escalation(
            primary_output,
            supervisor_review,
            reasoning,
        )
        
        if emotional_escalation:
            contributing_factors.append(f"Emotional factor: {emotional_reason}")
        
        # Step 5: Check for repeated failures
        retry_exhausted = self._check_retry_exhaustion(
            escalation_history,
            reasoning,
        )
        
        if retry_exhausted:
            contributing_factors.append("Retry attempts exhausted")
        
        # Step 6: Make escalation decision
        should_escalate = (
            mandatory_escalation or
            risk_escalation or
            confidence_escalation or
            emotional_escalation or
            retry_exhausted or
            not supervisor_review.approved
        )
        
        reasoning.append(
            f"Escalation decision: {'required' if should_escalate else 'not required'}"
        )
        
        # Step 7: Determine escalation type and reason
        if should_escalate:
            escalation_type, escalation_reason = self._determine_escalation_type(
                mandatory_escalation,
                risk_escalation,
                confidence_escalation,
                emotional_escalation,
                retry_exhausted,
                supervisor_review,
                primary_output,
                reasoning,
            )
        else:
            escalation_type = EscalationType.NONE
            escalation_reason = None
        
        # Step 8: Assign priority
        priority = self._calculate_priority(
            supervisor_review.risk_level,
            primary_output.detected_emotion,
            mandatory_escalation,
            reasoning,
        )
        
        # Step 9: Determine target
        target_agent = self._determine_target_agent(
            escalation_type,
            reasoning,
        )
        
        # Step 10: Generate context summary
        context_summary = self._generate_context_summary(
            primary_output,
            supervisor_review,
            original_input,
            contributing_factors,
        )
        
        # Step 11: List attempted resolutions
        attempted_resolutions = self._list_attempted_resolutions(
            primary_output,
            escalation_history,
        )
        
        # Step 12: Determine response time recommendation
        response_time = self._recommend_response_time(priority, escalation_type)
        
        return EscalationDecision(
            interaction_id=primary_output.interaction_id,
            should_escalate=should_escalate,
            escalation_type=escalation_type,
            escalation_reason=escalation_reason,
            priority=priority,
            target_agent=target_agent,
            context_summary=context_summary,
            key_issues=contributing_factors,
            attempted_resolutions=attempted_resolutions,
            reasoning=reasoning,
            contributing_factors=contributing_factors,
            recommended_response_time=response_time,
        )

    def _check_mandatory_triggers(
        self,
        review: SupervisorReview,
        reasoning: List[str],
    ) -> tuple[bool, Optional[str]]:
        """Check for flags that mandate immediate escalation."""
        for flag in IMMEDIATE_ESCALATION_FLAGS:
            if flag in review.flags:
                reasoning.append(f"Mandatory escalation trigger: {flag.value}")
                return True, flag.value
        
        if review.compliance_status == ComplianceStatus.VIOLATION:
            reasoning.append("Compliance violation detected - mandatory escalation")
            return True, "compliance_violation"
        
        reasoning.append("No mandatory escalation triggers found")
        return False, None

    def _evaluate_risk_escalation(
        self,
        review: SupervisorReview,
        reasoning: List[str],
    ) -> tuple[bool, Optional[str]]:
        """Evaluate risk-based escalation need."""
        if review.risk_level == RiskLevel.CRITICAL:
            reasoning.append("Critical risk level requires escalation")
            return True, "critical_risk"
        
        if review.risk_level == RiskLevel.HIGH:
            reasoning.append("High risk level suggests escalation")
            return True, "high_risk"
        
        reasoning.append(f"Risk level ({review.risk_level.value}) does not require escalation")
        return False, None

    def _evaluate_confidence_escalation(
        self,
        output: AgentOutput,
        review: SupervisorReview,
        reasoning: List[str],
    ) -> tuple[bool, Optional[str]]:
        """Evaluate confidence-based escalation need."""
        adjusted_confidence = review.adjusted_confidence
        
        if adjusted_confidence < 0.4:
            reasoning.append(f"Very low confidence ({adjusted_confidence:.2f}) requires escalation")
            return True, "very_low_confidence"
        
        if adjusted_confidence < 0.5 and ReviewFlag.ESCALATION_RECOMMENDED in review.flags:
            reasoning.append("Low confidence with escalation recommendation")
            return True, "low_confidence_flagged"
        
        reasoning.append(f"Confidence level ({adjusted_confidence:.2f}) acceptable")
        return False, None

    def _evaluate_emotional_escalation(
        self,
        output: AgentOutput,
        review: SupervisorReview,
        reasoning: List[str],
    ) -> tuple[bool, Optional[str]]:
        """Evaluate emotional escalation need."""
        emotion = output.detected_emotion
        
        # Angry customers with unaddressed emotions need human
        if emotion == EmotionalState.ANGRY:
            if ReviewFlag.EMOTION_UNADDRESSED in review.flags:
                reasoning.append("Angry customer with unaddressed emotion - human needed")
                return True, "angry_unaddressed"
        
        # Anxious customers may need human reassurance
        if emotion == EmotionalState.ANXIOUS and review.risk_level != RiskLevel.NONE:
            reasoning.append("Anxious customer with risk factors")
            return True, "anxious_at_risk"
        
        reasoning.append("Emotional state does not require escalation")
        return False, None

    def _check_retry_exhaustion(
        self,
        history: List[EscalationOutcome],
        reasoning: List[str],
    ) -> bool:
        """Check if retry attempts are exhausted."""
        # Count how many times this was returned to AI
        return_count = sum(1 for e in history if e.returned_to_ai)
        
        if return_count >= 2:
            reasoning.append(f"Retry attempts exhausted ({return_count} returns)")
            return True
        
        return False

    def _determine_escalation_type(
        self,
        mandatory: bool,
        risk: bool,
        confidence: bool,
        emotional: bool,
        retry_exhausted: bool,
        review: SupervisorReview,
        output: AgentOutput,
        reasoning: List[str],
    ) -> tuple[EscalationType, EscalationReason]:
        """Determine the appropriate escalation type."""
        
        # Mandatory or critical risk = immediate human
        if mandatory or review.risk_level == RiskLevel.CRITICAL:
            reasoning.append("Immediate human escalation required")
            
            if ReviewFlag.POLICY_CONCERN in review.flags:
                return EscalationType.HUMAN_IMMEDIATE, EscalationReason.POLICY_VIOLATION
            if ReviewFlag.SENSITIVE_TOPIC in review.flags:
                return EscalationType.HUMAN_IMMEDIATE, EscalationReason.SAFETY_CONCERN
            
            return EscalationType.HUMAN_IMMEDIATE, EscalationReason.COMPLEX_ISSUE
        
        # Emotional escalation = human queue
        if emotional:
            reasoning.append("Human queue for emotional support")
            return EscalationType.HUMAN_QUEUE, EscalationReason.EMOTIONAL_DISTRESS
        
        # Low confidence without approval = supervisor override or retry
        if confidence and not review.approved:
            if retry_exhausted:
                reasoning.append("Creating ticket after failed retries")
                return EscalationType.TICKET_CREATE, EscalationReason.REPEATED_FAILURE
            else:
                reasoning.append("Retry with supervisor guidance")
                return EscalationType.RETRY_PRIMARY, EscalationReason.LOW_CONFIDENCE
        
        # High risk = human queue
        if risk:
            reasoning.append("Queued for human review due to risk")
            return EscalationType.HUMAN_QUEUE, EscalationReason.COMPLEX_ISSUE
        
        # Not approved but no specific reason = supervisor override
        if not review.approved:
            reasoning.append("Supervisor override for unapproved decision")
            return EscalationType.SUPERVISOR_OVERRIDE, EscalationReason.LOW_CONFIDENCE
        
        # Retry exhausted = ticket
        if retry_exhausted:
            reasoning.append("Creating ticket after exhausted retries")
            return EscalationType.TICKET_CREATE, EscalationReason.REPEATED_FAILURE
        
        # Default: human queue
        reasoning.append("Default escalation to human queue")
        return EscalationType.HUMAN_QUEUE, EscalationReason.COMPLEX_ISSUE

    def _calculate_priority(
        self,
        risk_level: RiskLevel,
        emotion: Optional[EmotionalState],
        mandatory: bool,
        reasoning: List[str],
    ) -> int:
        """Calculate priority level (1=highest, 5=lowest)."""
        base_priority = RISK_TO_PRIORITY.get(risk_level, 5)
        
        # Mandatory escalations are always high priority
        if mandatory:
            priority = 1
        # Angry customers get elevated priority
        elif emotion == EmotionalState.ANGRY:
            priority = min(base_priority, 2)
        # Anxious customers get slightly elevated priority
        elif emotion == EmotionalState.ANXIOUS:
            priority = min(base_priority, 3)
        else:
            priority = base_priority
        
        reasoning.append(f"Priority assigned: {priority}")
        return priority

    def _determine_target_agent(
        self,
        escalation_type: EscalationType,
        reasoning: List[str],
    ) -> Optional[AgentType]:
        """Determine target agent for escalation."""
        if escalation_type == EscalationType.NONE:
            return None
        
        if escalation_type in [EscalationType.HUMAN_IMMEDIATE, EscalationType.HUMAN_QUEUE]:
            reasoning.append("Target: Human agent")
            return AgentType.HUMAN
        
        if escalation_type == EscalationType.RETRY_PRIMARY:
            reasoning.append("Target: Primary agent (retry)")
            return AgentType.PRIMARY
        
        if escalation_type == EscalationType.SUPERVISOR_OVERRIDE:
            reasoning.append("Target: Supervisor agent (override)")
            return AgentType.SUPERVISOR
        
        if escalation_type == EscalationType.TICKET_CREATE:
            reasoning.append("Target: Ticket system (async)")
            return AgentType.HUMAN
        
        return None

    def _generate_context_summary(
        self,
        output: AgentOutput,
        review: SupervisorReview,
        input_data: AgentInput,
        factors: List[str],
    ) -> str:
        """Generate context summary for handoff."""
        parts = []
        
        # Customer state
        if output.detected_intent:
            parts.append(f"Customer intent: {output.detected_intent.value.replace('_', ' ')}")
        if output.detected_emotion:
            parts.append(f"Emotional state: {output.detected_emotion.value}")
        
        # Risk summary
        parts.append(f"Risk level: {review.risk_level.value}")
        
        # Key concerns
        if factors:
            parts.append(f"Key concerns: {'; '.join(factors[:3])}")
        
        # Original query summary
        query_preview = input_data.content[:100]
        if len(input_data.content) > 100:
            query_preview += "..."
        parts.append(f"Customer message: \"{query_preview}\"")
        
        return " | ".join(parts)

    def _list_attempted_resolutions(
        self,
        output: AgentOutput,
        history: List[EscalationOutcome],
    ) -> List[str]:
        """List resolutions that have been attempted."""
        resolutions = []
        
        if output.response_content:
            resolutions.append(f"AI response attempted: {output.decision_summary}")
        
        for escalation in history:
            if escalation.resolution_summary:
                resolutions.append(escalation.resolution_summary)
        
        return resolutions

    def _recommend_response_time(
        self,
        priority: int,
        escalation_type: EscalationType,
    ) -> Optional[str]:
        """Recommend response time based on priority."""
        if escalation_type == EscalationType.NONE:
            return None
        
        if escalation_type == EscalationType.HUMAN_IMMEDIATE or priority == 1:
            return "immediate"
        elif priority == 2:
            return "within 5 minutes"
        elif priority == 3:
            return "within 15 minutes"
        elif priority == 4:
            return "within 1 hour"
        else:
            return "within 24 hours"
