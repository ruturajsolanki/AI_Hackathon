"""
AI Audit Logger

Provides transparency and compliance auditing for AI-assisted decisions.
Logs decision rationale, confidence levels, and escalation paths without
storing sensitive customer data.

Designed for:
- Regulatory compliance audits
- AI explainability requirements
- Decision review and analysis
- Quality assurance
"""

import asyncio
import hashlib
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Deque, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Audit Event Types
# -----------------------------------------------------------------------------

class AuditEventType(str, Enum):
    """Types of events captured in the audit log."""
    
    # Interaction lifecycle
    INTERACTION_STARTED = "interaction_started"
    INTERACTION_ENDED = "interaction_ended"
    
    # Agent decisions
    PRIMARY_DECISION = "primary_decision"
    SUPERVISOR_REVIEW = "supervisor_review"
    ESCALATION_DECISION = "escalation_decision"
    
    # Confidence events
    CONFIDENCE_ASSESSED = "confidence_assessed"
    CONFIDENCE_ADJUSTED = "confidence_adjusted"
    CONFIDENCE_THRESHOLD_CROSSED = "confidence_threshold_crossed"
    
    # Safety events
    SENSITIVE_TOPIC_DETECTED = "sensitive_topic_detected"
    COMPLIANCE_VIOLATION = "compliance_violation"
    PROHIBITED_CONTENT = "prohibited_content"
    
    # Escalation events
    ESCALATION_TRIGGERED = "escalation_triggered"
    HUMAN_HANDOFF = "human_handoff"
    ESCALATION_RETURNED = "escalation_returned"
    
    # Override events
    SUPERVISOR_OVERRIDE = "supervisor_override"
    HUMAN_OVERRIDE = "human_override"
    
    # System events
    LLM_CALL_MADE = "llm_call_made"
    LLM_FALLBACK_USED = "llm_fallback_used"
    SYSTEM_ERROR = "system_error"


class DecisionOutcome(str, Enum):
    """Outcome categories for decisions."""
    
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    DEFERRED = "deferred"
    ERROR = "error"


class ConfidenceCategory(str, Enum):
    """Confidence level categories."""
    
    HIGH = "high"          # >= 0.8
    MEDIUM = "medium"      # 0.6 - 0.8
    LOW = "low"            # 0.4 - 0.6
    UNCERTAIN = "uncertain"  # < 0.4


# -----------------------------------------------------------------------------
# Audit Record Models
# -----------------------------------------------------------------------------

class AuditRecord(BaseModel):
    """
    Individual audit record for an AI decision or event.
    
    Contains all information needed for compliance review
    WITHOUT storing sensitive customer data.
    """
    
    # Identifiers (anonymized)
    record_id: UUID = Field(default_factory=uuid4)
    interaction_id: UUID = Field(description="Interaction this record belongs to")
    customer_hash: Optional[str] = Field(
        None,
        description="One-way hash of customer ID for correlation without PII"
    )
    
    # Event details
    event_type: AuditEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Agent information
    agent_type: Optional[str] = Field(None, description="primary, supervisor, escalation, human")
    agent_id: Optional[str] = Field(None, description="Specific agent instance ID")
    
    # Decision details
    decision_outcome: Optional[DecisionOutcome] = None
    decision_summary: Optional[str] = Field(
        None,
        max_length=500,
        description="Brief, non-sensitive summary of the decision"
    )
    
    # Confidence tracking
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_category: Optional[ConfidenceCategory] = None
    confidence_factors: List[str] = Field(
        default_factory=list,
        description="Factors contributing to confidence"
    )
    confidence_concerns: List[str] = Field(
        default_factory=list,
        description="Factors reducing confidence"
    )
    
    # Escalation tracking
    escalation_triggered: bool = Field(default=False)
    escalation_reason: Optional[str] = Field(None, max_length=200)
    escalation_target: Optional[str] = Field(None, description="human, supervisor, retry")
    
    # Safety and compliance
    compliance_status: Optional[str] = Field(None, description="compliant, warning, violation")
    risk_level: Optional[str] = Field(None, description="none, low, medium, high, critical")
    safety_flags: List[str] = Field(
        default_factory=list,
        description="Safety-related flags raised"
    )
    
    # Reasoning chain (explainability)
    reasoning_steps: List[str] = Field(
        default_factory=list,
        description="Step-by-step reasoning for the decision"
    )
    
    # LLM usage tracking
    llm_used: bool = Field(default=False)
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_fallback_used: bool = Field(default=False)
    
    # Processing metadata
    processing_duration_ms: Optional[int] = None
    
    # Override tracking
    was_overridden: bool = Field(default=False)
    override_by: Optional[str] = None
    override_reason: Optional[str] = None
    
    # Additional context (non-sensitive)
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional non-sensitive context"
    )


class InteractionAuditSummary(BaseModel):
    """
    Summary of all audit events for a single interaction.
    
    Provides a complete view of the AI decision chain
    for compliance review.
    """
    
    interaction_id: UUID
    customer_hash: Optional[str]
    
    # Timing
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Decision summary
    total_decisions: int = 0
    decisions_approved: int = 0
    decisions_rejected: int = 0
    decisions_escalated: int = 0
    
    # Confidence summary
    initial_confidence: Optional[float] = None
    final_confidence: Optional[float] = None
    min_confidence: Optional[float] = None
    max_confidence: Optional[float] = None
    confidence_adjustments: int = 0
    
    # Escalation summary
    escalation_count: int = 0
    escalation_reasons: List[str] = Field(default_factory=list)
    human_intervention_required: bool = False
    
    # Safety summary
    compliance_violations: int = 0
    safety_flags_raised: List[str] = Field(default_factory=list)
    sensitive_topics_detected: bool = False
    
    # Agent involvement
    agents_involved: List[str] = Field(default_factory=list)
    
    # LLM usage
    llm_calls_made: int = 0
    llm_fallbacks_used: int = 0
    
    # Override summary
    overrides_applied: int = 0
    
    # Full event chain
    event_count: int = 0
    event_types: List[str] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Audit Logger Implementation
# -----------------------------------------------------------------------------

@dataclass
class InteractionAuditState:
    """Internal state for tracking an interaction's audit trail."""
    
    interaction_id: UUID
    customer_hash: Optional[str]
    started_at: datetime
    records: Deque[AuditRecord] = field(default_factory=lambda: deque(maxlen=100))
    confidence_history: List[float] = field(default_factory=list)
    ended: bool = False


class AuditLogger:
    """
    In-memory audit logger for AI decisions.
    
    Responsibilities:
    - Log all AI-assisted decisions with full context
    - Track confidence levels and adjustments
    - Record escalation rationale
    - Provide audit trail for compliance review
    - Support decision explainability queries
    
    Privacy guarantees:
    - Never stores raw customer messages
    - Customer IDs are one-way hashed
    - Only stores decision metadata, not content
    
    Designed for:
    - Regulatory compliance audits
    - AI fairness and bias analysis
    - Quality assurance reviews
    - Incident investigation
    """
    
    def __init__(
        self,
        max_interactions: int = 10000,
        max_records_per_interaction: int = 100,
    ):
        """
        Initialize the audit logger.
        
        Args:
            max_interactions: Maximum interactions to retain in memory.
            max_records_per_interaction: Maximum records per interaction.
        """
        self._max_interactions = max_interactions
        self._max_records = max_records_per_interaction
        self._interactions: Dict[UUID, InteractionAuditState] = {}
        self._completed_summaries: Deque[InteractionAuditSummary] = deque(
            maxlen=max_interactions
        )
        self._lock = asyncio.Lock()
    
    # =========================================================================
    # Core Logging Methods
    # =========================================================================
    
    async def log_interaction_start(
        self,
        interaction_id: UUID,
        customer_id: Optional[str] = None,
        channel: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditRecord:
        """Log the start of a customer interaction."""
        customer_hash = self._hash_customer_id(customer_id) if customer_id else None
        
        async with self._lock:
            # Create interaction state
            state = InteractionAuditState(
                interaction_id=interaction_id,
                customer_hash=customer_hash,
                started_at=datetime.now(timezone.utc),
            )
            self._interactions[interaction_id] = state
            
            # Limit total interactions
            if len(self._interactions) > self._max_interactions:
                oldest = min(
                    self._interactions.keys(),
                    key=lambda k: self._interactions[k].started_at
                )
                del self._interactions[oldest]
        
        record = AuditRecord(
            interaction_id=interaction_id,
            customer_hash=customer_hash,
            event_type=AuditEventType.INTERACTION_STARTED,
            metadata={
                "channel": channel,
                **(metadata or {}),
            },
        )
        
        await self._add_record(interaction_id, record)
        return record
    
    async def log_interaction_end(
        self,
        interaction_id: UUID,
        resolution: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[InteractionAuditSummary]:
        """Log the end of an interaction and generate summary."""
        record = AuditRecord(
            interaction_id=interaction_id,
            event_type=AuditEventType.INTERACTION_ENDED,
            decision_summary=resolution,
            metadata=metadata or {},
        )
        
        await self._add_record(interaction_id, record)
        
        # Generate and store summary
        summary = await self.get_interaction_summary(interaction_id)
        if summary:
            summary.ended_at = datetime.now(timezone.utc)
            summary.duration_seconds = (
                summary.ended_at - summary.started_at
            ).total_seconds()
            
            async with self._lock:
                self._completed_summaries.append(summary)
                
                # Mark as ended
                if interaction_id in self._interactions:
                    self._interactions[interaction_id].ended = True
        
        return summary
    
    async def log_primary_decision(
        self,
        interaction_id: UUID,
        agent_id: str,
        decision_outcome: DecisionOutcome,
        decision_summary: str,
        confidence_score: float,
        confidence_factors: List[str],
        confidence_concerns: List[str],
        reasoning_steps: List[str],
        detected_intent: Optional[str] = None,
        detected_emotion: Optional[str] = None,
        llm_used: bool = False,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        llm_fallback_used: bool = False,
        processing_duration_ms: Optional[int] = None,
    ) -> AuditRecord:
        """Log a decision from the Primary Agent."""
        record = AuditRecord(
            interaction_id=interaction_id,
            event_type=AuditEventType.PRIMARY_DECISION,
            agent_type="primary",
            agent_id=agent_id,
            decision_outcome=decision_outcome,
            decision_summary=self._sanitize_summary(decision_summary),
            confidence_score=confidence_score,
            confidence_category=self._categorize_confidence(confidence_score),
            confidence_factors=confidence_factors[:10],
            confidence_concerns=confidence_concerns[:10],
            reasoning_steps=reasoning_steps[:20],
            llm_used=llm_used,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_fallback_used=llm_fallback_used,
            processing_duration_ms=processing_duration_ms,
            metadata={
                "detected_intent": detected_intent,
                "detected_emotion": detected_emotion,
            },
        )
        
        await self._add_record(interaction_id, record)
        await self._track_confidence(interaction_id, confidence_score)
        
        return record
    
    async def log_supervisor_review(
        self,
        interaction_id: UUID,
        agent_id: str,
        approved: bool,
        quality_score: float,
        original_confidence: float,
        adjusted_confidence: float,
        compliance_status: str,
        risk_level: str,
        flags: List[str],
        recommendations: List[str],
        reasoning_steps: List[str],
        llm_used: bool = False,
        llm_fallback_used: bool = False,
    ) -> AuditRecord:
        """Log a review from the Supervisor Agent."""
        outcome = DecisionOutcome.APPROVED if approved else DecisionOutcome.REJECTED
        
        record = AuditRecord(
            interaction_id=interaction_id,
            event_type=AuditEventType.SUPERVISOR_REVIEW,
            agent_type="supervisor",
            agent_id=agent_id,
            decision_outcome=outcome,
            decision_summary=f"Review: {outcome.value}, quality={quality_score:.2f}",
            confidence_score=adjusted_confidence,
            confidence_category=self._categorize_confidence(adjusted_confidence),
            compliance_status=compliance_status,
            risk_level=risk_level,
            safety_flags=flags[:10],
            reasoning_steps=reasoning_steps[:20],
            llm_used=llm_used,
            llm_fallback_used=llm_fallback_used,
            metadata={
                "quality_score": quality_score,
                "original_confidence": original_confidence,
                "confidence_delta": adjusted_confidence - original_confidence,
                "recommendations": recommendations[:5],
            },
        )
        
        await self._add_record(interaction_id, record)
        
        # Log confidence adjustment if changed
        if abs(adjusted_confidence - original_confidence) > 0.01:
            await self.log_confidence_adjustment(
                interaction_id=interaction_id,
                original=original_confidence,
                adjusted=adjusted_confidence,
                reason=f"Supervisor review: {compliance_status}, risk={risk_level}",
            )
        
        return record
    
    async def log_escalation_decision(
        self,
        interaction_id: UUID,
        agent_id: str,
        should_escalate: bool,
        escalation_type: Optional[str],
        escalation_reason: Optional[str],
        priority: int,
        target: Optional[str],
        reasoning_steps: List[str],
    ) -> AuditRecord:
        """Log an escalation decision."""
        outcome = DecisionOutcome.ESCALATED if should_escalate else DecisionOutcome.APPROVED
        
        record = AuditRecord(
            interaction_id=interaction_id,
            event_type=AuditEventType.ESCALATION_DECISION,
            agent_type="escalation",
            agent_id=agent_id,
            decision_outcome=outcome,
            decision_summary=f"Escalation: {escalation_type or 'none'}",
            escalation_triggered=should_escalate,
            escalation_reason=escalation_reason,
            escalation_target=target,
            reasoning_steps=reasoning_steps[:20],
            metadata={
                "escalation_type": escalation_type,
                "priority": priority,
            },
        )
        
        await self._add_record(interaction_id, record)
        
        if should_escalate:
            await self._log_escalation_event(
                interaction_id=interaction_id,
                escalation_type=escalation_type,
                reason=escalation_reason,
                target=target,
            )
        
        return record
    
    async def log_confidence_adjustment(
        self,
        interaction_id: UUID,
        original: float,
        adjusted: float,
        reason: str,
        adjusted_by: str = "supervisor",
    ) -> AuditRecord:
        """Log a confidence score adjustment."""
        # Check if threshold crossed
        original_cat = self._categorize_confidence(original)
        adjusted_cat = self._categorize_confidence(adjusted)
        
        event_type = AuditEventType.CONFIDENCE_ADJUSTED
        if original_cat != adjusted_cat:
            event_type = AuditEventType.CONFIDENCE_THRESHOLD_CROSSED
        
        record = AuditRecord(
            interaction_id=interaction_id,
            event_type=event_type,
            confidence_score=adjusted,
            confidence_category=adjusted_cat,
            decision_summary=f"Confidence: {original:.2f} → {adjusted:.2f}",
            reasoning_steps=[reason],
            metadata={
                "original_confidence": original,
                "adjusted_by": adjusted_by,
                "threshold_crossed": original_cat != adjusted_cat,
            },
        )
        
        await self._add_record(interaction_id, record)
        await self._track_confidence(interaction_id, adjusted)
        
        return record
    
    async def log_safety_event(
        self,
        interaction_id: UUID,
        event_type: AuditEventType,
        description: str,
        flags: List[str],
        risk_level: str,
        action_taken: str,
    ) -> AuditRecord:
        """Log a safety-related event."""
        record = AuditRecord(
            interaction_id=interaction_id,
            event_type=event_type,
            decision_summary=self._sanitize_summary(description),
            risk_level=risk_level,
            safety_flags=flags[:10],
            reasoning_steps=[f"Safety event: {description}", f"Action: {action_taken}"],
            metadata={
                "action_taken": action_taken,
            },
        )
        
        await self._add_record(interaction_id, record)
        return record
    
    async def log_human_override(
        self,
        interaction_id: UUID,
        override_by: str,
        original_decision: str,
        new_decision: str,
        reason: str,
    ) -> AuditRecord:
        """Log a human override of an AI decision."""
        record = AuditRecord(
            interaction_id=interaction_id,
            event_type=AuditEventType.HUMAN_OVERRIDE,
            agent_type="human",
            agent_id=override_by,
            decision_summary=f"Override: {original_decision} → {new_decision}",
            was_overridden=True,
            override_by=override_by,
            override_reason=reason,
            reasoning_steps=[
                f"Original AI decision: {original_decision}",
                f"Human override applied",
                f"Reason: {reason}",
            ],
        )
        
        await self._add_record(interaction_id, record)
        return record
    
    async def log_llm_call(
        self,
        interaction_id: UUID,
        agent_type: str,
        provider: str,
        model: str,
        success: bool,
        fallback_used: bool = False,
        latency_ms: Optional[int] = None,
        error: Optional[str] = None,
    ) -> AuditRecord:
        """Log an LLM API call."""
        event_type = AuditEventType.LLM_FALLBACK_USED if fallback_used else AuditEventType.LLM_CALL_MADE
        
        record = AuditRecord(
            interaction_id=interaction_id,
            event_type=event_type,
            agent_type=agent_type,
            llm_used=True,
            llm_provider=provider,
            llm_model=model,
            llm_fallback_used=fallback_used,
            processing_duration_ms=latency_ms,
            decision_summary=f"LLM call: {'success' if success else 'failed'}",
            metadata={
                "success": success,
                "error": error[:200] if error else None,
            },
        )
        
        await self._add_record(interaction_id, record)
        return record
    
    async def log_system_error(
        self,
        interaction_id: UUID,
        error_type: str,
        error_message: str,
        component: str,
        recovery_action: Optional[str] = None,
    ) -> AuditRecord:
        """Log a system error."""
        record = AuditRecord(
            interaction_id=interaction_id,
            event_type=AuditEventType.SYSTEM_ERROR,
            decision_outcome=DecisionOutcome.ERROR,
            decision_summary=f"Error in {component}: {error_type}",
            reasoning_steps=[
                f"Component: {component}",
                f"Error: {error_type}",
                f"Recovery: {recovery_action or 'none'}",
            ],
            metadata={
                "error_type": error_type,
                "error_message": error_message[:500],
                "component": component,
                "recovery_action": recovery_action,
            },
        )
        
        await self._add_record(interaction_id, record)
        return record
    
    # =========================================================================
    # Query Methods
    # =========================================================================
    
    async def get_interaction_summary(
        self,
        interaction_id: UUID,
    ) -> Optional[InteractionAuditSummary]:
        """Generate a summary of all audit events for an interaction."""
        async with self._lock:
            state = self._interactions.get(interaction_id)
            if not state:
                return None
            
            records = list(state.records)
        
        if not records:
            return None
        
        # Build summary
        summary = InteractionAuditSummary(
            interaction_id=interaction_id,
            customer_hash=state.customer_hash,
            started_at=state.started_at,
            event_count=len(records),
        )
        
        agents = set()
        event_types = set()
        escalation_reasons = []
        safety_flags = set()
        
        for record in records:
            event_types.add(record.event_type.value)
            
            if record.agent_type:
                agents.add(record.agent_type)
            
            # Count decisions
            if record.decision_outcome:
                summary.total_decisions += 1
                if record.decision_outcome == DecisionOutcome.APPROVED:
                    summary.decisions_approved += 1
                elif record.decision_outcome == DecisionOutcome.REJECTED:
                    summary.decisions_rejected += 1
                elif record.decision_outcome == DecisionOutcome.ESCALATED:
                    summary.decisions_escalated += 1
            
            # Track escalations
            if record.escalation_triggered:
                summary.escalation_count += 1
                if record.escalation_reason:
                    escalation_reasons.append(record.escalation_reason)
                if record.escalation_target == "human":
                    summary.human_intervention_required = True
            
            # Track safety
            if record.compliance_status == "violation":
                summary.compliance_violations += 1
            
            safety_flags.update(record.safety_flags)
            
            if record.event_type == AuditEventType.SENSITIVE_TOPIC_DETECTED:
                summary.sensitive_topics_detected = True
            
            # Track LLM usage
            if record.llm_used:
                summary.llm_calls_made += 1
            if record.llm_fallback_used:
                summary.llm_fallbacks_used += 1
            
            # Track overrides
            if record.was_overridden:
                summary.overrides_applied += 1
        
        # Confidence summary
        if state.confidence_history:
            summary.initial_confidence = state.confidence_history[0]
            summary.final_confidence = state.confidence_history[-1]
            summary.min_confidence = min(state.confidence_history)
            summary.max_confidence = max(state.confidence_history)
            summary.confidence_adjustments = len(state.confidence_history) - 1
        
        summary.agents_involved = sorted(agents)
        summary.event_types = sorted(event_types)
        summary.escalation_reasons = escalation_reasons[:10]
        summary.safety_flags_raised = sorted(safety_flags)[:20]
        
        return summary
    
    async def get_interaction_records(
        self,
        interaction_id: UUID,
    ) -> List[AuditRecord]:
        """Get all audit records for an interaction."""
        async with self._lock:
            state = self._interactions.get(interaction_id)
            if not state:
                return []
            return list(state.records)
    
    async def get_records_by_type(
        self,
        interaction_id: UUID,
        event_type: AuditEventType,
    ) -> List[AuditRecord]:
        """Get audit records of a specific type."""
        records = await self.get_interaction_records(interaction_id)
        return [r for r in records if r.event_type == event_type]
    
    async def get_decision_chain(
        self,
        interaction_id: UUID,
    ) -> List[AuditRecord]:
        """Get the chain of decisions for an interaction."""
        decision_types = {
            AuditEventType.PRIMARY_DECISION,
            AuditEventType.SUPERVISOR_REVIEW,
            AuditEventType.ESCALATION_DECISION,
            AuditEventType.HUMAN_OVERRIDE,
        }
        records = await self.get_interaction_records(interaction_id)
        return [r for r in records if r.event_type in decision_types]
    
    async def get_confidence_history(
        self,
        interaction_id: UUID,
    ) -> List[float]:
        """Get the confidence score history for an interaction."""
        async with self._lock:
            state = self._interactions.get(interaction_id)
            if not state:
                return []
            return list(state.confidence_history)
    
    async def get_escalation_records(
        self,
        interaction_id: UUID,
    ) -> List[AuditRecord]:
        """Get all escalation-related records."""
        records = await self.get_interaction_records(interaction_id)
        return [r for r in records if r.escalation_triggered]
    
    async def get_safety_records(
        self,
        interaction_id: UUID,
    ) -> List[AuditRecord]:
        """Get all safety-related records."""
        safety_types = {
            AuditEventType.SENSITIVE_TOPIC_DETECTED,
            AuditEventType.COMPLIANCE_VIOLATION,
            AuditEventType.PROHIBITED_CONTENT,
        }
        records = await self.get_interaction_records(interaction_id)
        return [
            r for r in records
            if r.event_type in safety_types or r.safety_flags
        ]
    
    async def get_completed_summaries(
        self,
        limit: int = 100,
    ) -> List[InteractionAuditSummary]:
        """Get summaries of completed interactions."""
        async with self._lock:
            summaries = list(self._completed_summaries)
        return summaries[-limit:]
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get aggregate statistics from the audit log."""
        async with self._lock:
            active_count = len(self._interactions)
            completed_count = len(self._completed_summaries)
            summaries = list(self._completed_summaries)
        
        if not summaries:
            return {
                "active_interactions": active_count,
                "completed_interactions": 0,
                "total_decisions": 0,
                "approval_rate": 0.0,
                "escalation_rate": 0.0,
                "average_confidence": 0.0,
            }
        
        total_decisions = sum(s.total_decisions for s in summaries)
        total_approved = sum(s.decisions_approved for s in summaries)
        total_escalated = sum(s.decisions_escalated for s in summaries)
        
        confidences = [s.final_confidence for s in summaries if s.final_confidence]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            "active_interactions": active_count,
            "completed_interactions": completed_count,
            "total_decisions": total_decisions,
            "approval_rate": total_approved / total_decisions if total_decisions else 0.0,
            "escalation_rate": total_escalated / total_decisions if total_decisions else 0.0,
            "average_confidence": avg_confidence,
            "compliance_violations": sum(s.compliance_violations for s in summaries),
            "human_interventions": sum(1 for s in summaries if s.human_intervention_required),
            "llm_fallback_rate": (
                sum(s.llm_fallbacks_used for s in summaries) /
                sum(s.llm_calls_made for s in summaries)
                if sum(s.llm_calls_made for s in summaries) > 0 else 0.0
            ),
        }
    
    # =========================================================================
    # Internal Helpers
    # =========================================================================
    
    async def _add_record(
        self,
        interaction_id: UUID,
        record: AuditRecord,
    ) -> None:
        """Add a record to the interaction's audit trail."""
        async with self._lock:
            state = self._interactions.get(interaction_id)
            if state:
                state.records.append(record)
    
    async def _track_confidence(
        self,
        interaction_id: UUID,
        confidence: float,
    ) -> None:
        """Track confidence score in history."""
        async with self._lock:
            state = self._interactions.get(interaction_id)
            if state:
                state.confidence_history.append(confidence)
    
    async def _log_escalation_event(
        self,
        interaction_id: UUID,
        escalation_type: Optional[str],
        reason: Optional[str],
        target: Optional[str],
    ) -> None:
        """Log an escalation trigger event."""
        event_type = (
            AuditEventType.HUMAN_HANDOFF
            if target == "human"
            else AuditEventType.ESCALATION_TRIGGERED
        )
        
        record = AuditRecord(
            interaction_id=interaction_id,
            event_type=event_type,
            escalation_triggered=True,
            escalation_reason=reason,
            escalation_target=target,
            decision_summary=f"Escalation: {escalation_type} → {target}",
        )
        
        await self._add_record(interaction_id, record)
    
    def _hash_customer_id(self, customer_id: str) -> str:
        """Create one-way hash of customer ID for correlation without PII."""
        return hashlib.sha256(customer_id.encode()).hexdigest()[:16]
    
    def _sanitize_summary(self, text: str) -> str:
        """Sanitize decision summary to remove potential PII."""
        if not text:
            return ""
        # Truncate and basic sanitization
        sanitized = text[:500]
        # Could add more sophisticated PII detection here
        return sanitized
    
    def _categorize_confidence(self, score: float) -> ConfidenceCategory:
        """Categorize a confidence score."""
        if score >= 0.8:
            return ConfidenceCategory.HIGH
        elif score >= 0.6:
            return ConfidenceCategory.MEDIUM
        elif score >= 0.4:
            return ConfidenceCategory.LOW
        else:
            return ConfidenceCategory.UNCERTAIN
