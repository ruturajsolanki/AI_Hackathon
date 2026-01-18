"""
Call Orchestrator Service

Manages the lifecycle of customer interactions by coordinating
the flow between Primary, Supervisor, and Escalation agents.

Integrates with:
- ContextStore for conversation history
- MetricsEngine for analytics signals
- PersistentStore for durable storage
- AuditLogger for compliance auditing
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.agents.base import AgentInput, AgentOutput
from app.agents.escalation import EscalationAgent, EscalationDecision, EscalationType
from app.agents.primary import PrimaryAgent
from app.agents.supervisor import SupervisorAgent, SupervisorReview
from app.analytics.audit import AuditLogger, DecisionOutcome
from app.analytics.metrics import MetricsEngine, ResolutionType
from app.core.models import (
    AgentType,
    ConfidenceLevel,
    ConversationContext,
    CustomerInteraction,
    EmotionalState,
    EscalationOutcome,
    IntentCategory,
    InteractionStatus,
)
from app.memory.context_store import (
    ContextStore,
    ConversationMessage,
    DecisionRecord,
    MessageRole,
    ShortTermContext,
)
from app.persistence import PersistentStore, get_store

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Orchestration Models
# -----------------------------------------------------------------------------

class OrchestrationPhase(str, Enum):
    """Phases of the orchestration pipeline."""
    INITIALIZED = "initialized"
    PRIMARY_PROCESSING = "primary_processing"
    SUPERVISOR_REVIEW = "supervisor_review"
    ESCALATION_EVALUATION = "escalation_evaluation"
    RESPONSE_DELIVERY = "response_delivery"
    ESCALATION_HANDOFF = "escalation_handoff"
    COMPLETED = "completed"
    FAILED = "failed"


class OrchestrationResult(BaseModel):
    """
    Result of the orchestration pipeline.
    
    Contains all outputs from the agent chain and the final
    determination of how to proceed.
    """
    result_id: UUID = Field(default_factory=uuid4)
    interaction_id: UUID = Field(description="Associated interaction")
    
    # Phase tracking
    final_phase: OrchestrationPhase = Field(description="Final phase reached")
    phases_completed: List[OrchestrationPhase] = Field(default_factory=list)
    
    # Agent outputs
    primary_output: Optional[AgentOutput] = Field(default=None)
    supervisor_review: Optional[SupervisorReview] = Field(default=None)
    escalation_decision: Optional[EscalationDecision] = Field(default=None)
    
    # Final determination
    should_respond: bool = Field(
        default=False,
        description="Whether to deliver AI response to customer"
    )
    should_escalate: bool = Field(
        default=False,
        description="Whether to escalate to human/ticket"
    )
    response_content: Optional[str] = Field(
        default=None,
        description="Response to deliver (if should_respond)"
    )
    
    # Metadata
    total_duration_ms: int = Field(default=0)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = Field(default=None)
    
    # Error tracking
    error: Optional[str] = Field(default=None)
    error_phase: Optional[OrchestrationPhase] = Field(default=None)


class InteractionState(BaseModel):
    """
    Maintains state throughout the interaction lifecycle.
    
    Updated as the orchestrator progresses through phases.
    """
    interaction_id: UUID = Field(default_factory=uuid4)
    
    # Interaction details
    interaction: Optional[CustomerInteraction] = Field(default=None)
    
    # Current state
    current_phase: OrchestrationPhase = Field(default=OrchestrationPhase.INITIALIZED)
    turn_count: int = Field(default=0)
    
    # Agent outputs (accumulated)
    primary_outputs: List[AgentOutput] = Field(default_factory=list)
    supervisor_reviews: List[SupervisorReview] = Field(default_factory=list)
    escalation_decisions: List[EscalationDecision] = Field(default_factory=list)
    escalation_history: List[EscalationOutcome] = Field(default_factory=list)
    
    # Classification (latest)
    current_intent: Optional[IntentCategory] = Field(default=None)
    current_emotion: Optional[EmotionalState] = Field(default=None)
    
    # Flags
    is_escalated: bool = Field(default=False)
    is_completed: bool = Field(default=False)
    requires_human: bool = Field(default=False)
    
    # Timing
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def _score_to_confidence_level(score: float) -> ConfidenceLevel:
    """Convert numeric confidence score to confidence level."""
    if score >= 0.8:
        return ConfidenceLevel.HIGH
    elif score >= 0.6:
        return ConfidenceLevel.MEDIUM
    elif score >= 0.4:
        return ConfidenceLevel.LOW
    else:
        return ConfidenceLevel.UNCERTAIN


# -----------------------------------------------------------------------------
# Call Orchestrator
# -----------------------------------------------------------------------------

class CallOrchestrator:
    """
    Orchestrates the flow of customer interactions through the agent pipeline.
    
    Responsibilities:
    - Managing interaction lifecycle
    - Invoking agents in sequence: Primary → Supervisor → Escalation
    - Maintaining interaction state via ContextStore
    - Emitting analytics signals via MetricsEngine
    - Persisting interactions and decisions via PersistentStore
    - Determining final outcome
    
    Does NOT:
    - Handle API requests/responses
    - Implement AI logic
    - Manage WebSocket connections
    """

    def __init__(
        self,
        primary_agent: Optional[PrimaryAgent] = None,
        supervisor_agent: Optional[SupervisorAgent] = None,
        escalation_agent: Optional[EscalationAgent] = None,
        context_store: Optional[ContextStore] = None,
        metrics_engine: Optional[MetricsEngine] = None,
        persistent_store: Optional[PersistentStore] = None,
        audit_logger: Optional[AuditLogger] = None,
    ):
        """
        Initialize the orchestrator with agents, stores, and metrics.
        
        Args:
            primary_agent: Primary interaction agent (created if not provided).
            supervisor_agent: Supervisor review agent (created if not provided).
            escalation_agent: Escalation decision agent (created if not provided).
            context_store: Context memory store (created if not provided).
            metrics_engine: Analytics engine (created if not provided).
            persistent_store: Persistent storage (uses singleton if not provided).
            audit_logger: Audit logger for compliance (created if not provided).
        """
        # Create agents with LLM client if API key is available
        llm_client = self._create_llm_client()
        
        self._primary_agent = primary_agent or PrimaryAgent(llm_client=llm_client)
        self._supervisor_agent = supervisor_agent or SupervisorAgent(llm_client=llm_client)
        self._escalation_agent = escalation_agent or EscalationAgent()
        self._context_store = context_store or ContextStore()
        self._metrics_engine = metrics_engine or MetricsEngine()
        self._persistent_store = persistent_store or get_store()
        self._audit_logger = audit_logger or AuditLogger()
        self._active_states: dict[UUID, InteractionState] = {}
    
    def _create_llm_client(self):
        """
        Create an LLM client using runtime config or environment variables.
        
        Priority:
        1. Runtime-configured API key (from /api/config/llm)
        2. Environment variable (OPENAI_API_KEY or GEMINI_API_KEY)
        3. None (agents will use fallback logic)
        
        Returns:
            LLMClient (OpenAI or Gemini) if configured, None otherwise.
        """
        try:
            # Try runtime config first
            from app.api.config import get_runtime_config, LLMProvider
            runtime_config = get_runtime_config()
            
            if runtime_config.is_configured():
                api_key = runtime_config.get_api_key()
                provider = runtime_config.get_provider()
                
                if provider == LLMProvider.GEMINI:
                    from app.integrations.gemini_client import GeminiClient, GeminiConfig
                    config = GeminiConfig(api_key=api_key)
                    return GeminiClient(config)
                else:
                    from app.integrations.openai_client import OpenAIClient, OpenAIConfig
                    config = OpenAIConfig(api_key=api_key)
                    return OpenAIClient(config)
            
            # Fall back to environment variables
            import os
            
            # Check for Gemini first
            gemini_key = os.getenv("GEMINI_API_KEY")
            if gemini_key:
                from app.integrations.gemini_client import GeminiClient, GeminiConfig
                config = GeminiConfig(api_key=gemini_key)
                return GeminiClient(config)
            
            # Then try OpenAI
            from app.integrations.openai_client import OpenAIClient, OpenAIConfig
            env_config = OpenAIConfig.from_env()
            
            if env_config.api_key:
                return OpenAIClient(env_config)
            
            # No API key available - agents will use fallback logic
            return None
            
        except Exception:
            # If anything fails, return None - agents will use fallback
            return None

    @property
    def context_store(self) -> ContextStore:
        """Access the context store."""
        return self._context_store

    @property
    def metrics_engine(self) -> MetricsEngine:
        """Access the metrics engine."""
        return self._metrics_engine

    @property
    def persistent_store(self) -> PersistentStore:
        """Access the persistent store."""
        return self._persistent_store

    @property
    def audit_logger(self) -> AuditLogger:
        """Access the audit logger."""
        return self._audit_logger

    async def create_interaction(
        self,
        interaction: CustomerInteraction,
        initial_context: Optional[ConversationContext] = None,
    ) -> InteractionState:
        """
        Create a new interaction state with context, analytics, and persistence.
        
        Args:
            interaction: The customer interaction entity.
            initial_context: Optional initial conversation context.
            
        Returns:
            New InteractionState for tracking this interaction.
        """
        # Create context if not provided
        context = initial_context or self._create_initial_context(interaction)
        
        # Initialize in context store
        await self._context_store.create_interaction(
            interaction_id=interaction.interaction_id,
            initial_context=context,
        )
        
        # Start analytics tracking
        await self._metrics_engine.start_interaction(
            interaction_id=interaction.interaction_id,
            channel=interaction.channel,
            started_at=interaction.started_at,
        )
        
        # Persist interaction start
        self._persist_interaction_start(interaction)
        
        # Log to audit trail
        await self._audit_logger.log_interaction_start(
            interaction_id=interaction.interaction_id,
            customer_id=interaction.customer_id,
            channel=interaction.channel.value if interaction.channel else None,
            metadata={"source": "orchestrator"},
        )
        
        # Create orchestration state
        state = InteractionState(
            interaction_id=interaction.interaction_id,
            interaction=interaction,
        )
        self._active_states[interaction.interaction_id] = state
        
        return state

    def _persist_interaction_start(self, interaction: CustomerInteraction) -> None:
        """Persist interaction start to durable storage."""
        try:
            self._persistent_store.save_interaction(
                interaction_id=interaction.interaction_id,
                channel=interaction.channel,
                status=interaction.status.value if interaction.status else "initiated",
                started_at=interaction.started_at,
                customer_id=interaction.customer_id,
                metadata=interaction.metadata,
            )
        except Exception:
            # Log but don't fail - persistence is best-effort
            pass

    def get_state(self, interaction_id: UUID) -> Optional[InteractionState]:
        """Retrieve current state for an interaction."""
        return self._active_states.get(interaction_id)

    async def process_message(
        self,
        interaction_id: UUID,
        content: str,
        metadata: Optional[dict] = None,
    ) -> OrchestrationResult:
        """
        Process a customer message through the full agent pipeline.
        
        Flow:
        1. Store customer message in context
        2. Persist customer message
        3. Retrieve short-term context
        4. Invoke Primary Agent
        5. Persist primary decision
        6. Invoke Supervisor Agent for review
        7. Persist supervisor decision
        8. Invoke Escalation Agent for decision
        9. Persist escalation decision
        10. Determine final outcome
        11. Store agent response
        12. Persist agent response
        
        Args:
            interaction_id: ID of the active interaction.
            content: Customer message content.
            metadata: Optional additional metadata.
            
        Returns:
            OrchestrationResult with final determination.
        """
        start_time = datetime.now(timezone.utc)
        phases_completed: List[OrchestrationPhase] = []
        
        # Get or create state
        state = self._active_states.get(interaction_id)
        if not state:
            return self._create_error_result(
                interaction_id,
                "Interaction not found",
                OrchestrationPhase.INITIALIZED,
                start_time,
            )
        
        try:
            # Step 1: Store customer message
            customer_message = await self._store_customer_message(
                interaction_id,
                content,
                metadata or {},
            )
            
            # Step 2: Persist customer message
            self._persist_message(
                message_id=customer_message.message_id,
                interaction_id=interaction_id,
                role="customer",
                content=content,
                metadata=metadata,
            )
            
            # Step 3: Get short-term context
            short_term_context = await self._context_store.get_short_term_context(
                interaction_id
            )
            
            # Step 4: Prepare agent input with context
            agent_input = self._prepare_agent_input(
                state,
                content,
                metadata or {},
                short_term_context,
            )
            state.current_phase = OrchestrationPhase.PRIMARY_PROCESSING
            state.turn_count += 1
            
            # Step 5: Primary Agent processing
            primary_start = datetime.now(timezone.utc)
            primary_output = await self._invoke_primary_agent(agent_input)
            primary_duration = int((datetime.now(timezone.utc) - primary_start).total_seconds() * 1000)
            
            state.primary_outputs.append(primary_output)
            state.current_intent = primary_output.detected_intent
            state.current_emotion = primary_output.detected_emotion
            phases_completed.append(OrchestrationPhase.PRIMARY_PROCESSING)
            
            # Step 6: Emit analytics for primary decision
            await self._emit_turn_analytics(
                interaction_id,
                primary_output,
                AgentType.PRIMARY,
            )
            
            # Step 7: Store primary decision in context
            await self._store_decision(
                interaction_id,
                primary_output,
                supervisor_approved=None,
            )
            
            # Step 8: Persist primary decision
            self._persist_agent_decision(
                interaction_id=interaction_id,
                message_id=customer_message.message_id,
                agent_type="primary",
                decision_type=primary_output.decision_summary or "response",
                confidence=primary_output.confidence.overall_score,
                confidence_level=primary_output.confidence.level.value,
                processing_time_ms=primary_duration,
                details={
                    "intent": primary_output.detected_intent.value if primary_output.detected_intent else None,
                    "emotion": primary_output.detected_emotion.value if primary_output.detected_emotion else None,
                    "reasoning": primary_output.reasoning,
                },
            )
            
            # Step 9: Supervisor review
            state.current_phase = OrchestrationPhase.SUPERVISOR_REVIEW
            supervisor_start = datetime.now(timezone.utc)
            supervisor_review = await self._invoke_supervisor_agent(
                primary_output,
                agent_input,
            )
            supervisor_duration = int((datetime.now(timezone.utc) - supervisor_start).total_seconds() * 1000)
            
            state.supervisor_reviews.append(supervisor_review)
            phases_completed.append(OrchestrationPhase.SUPERVISOR_REVIEW)
            
            # Step 10: Update decision with supervisor review
            await self._update_decision_with_review(
                interaction_id,
                primary_output,
                supervisor_review,
            )
            
            # Step 11: Persist supervisor decision
            self._persist_agent_decision(
                interaction_id=interaction_id,
                message_id=customer_message.message_id,
                agent_type="supervisor",
                decision_type="approved" if supervisor_review.approved else "flagged",
                confidence=supervisor_review.adjusted_confidence,
                confidence_level=_score_to_confidence_level(supervisor_review.adjusted_confidence).value,
                processing_time_ms=supervisor_duration,
                details={
                    "approved": supervisor_review.approved,
                    "quality_score": supervisor_review.quality_score,
                    "risk_level": supervisor_review.risk_level.value if supervisor_review.risk_level else None,
                    "flags": supervisor_review.flags,
                },
            )
            
            # Step 12: Escalation evaluation
            state.current_phase = OrchestrationPhase.ESCALATION_EVALUATION
            escalation_start = datetime.now(timezone.utc)
            escalation_decision = await self._invoke_escalation_agent(
                primary_output,
                supervisor_review,
                agent_input,
                state.escalation_history,
            )
            escalation_duration = int((datetime.now(timezone.utc) - escalation_start).total_seconds() * 1000)
            
            state.escalation_decisions.append(escalation_decision)
            phases_completed.append(OrchestrationPhase.ESCALATION_EVALUATION)
            
            # Step 13: Persist escalation decision
            # Use supervisor's adjusted confidence for escalation decision
            escalation_confidence = supervisor_review.adjusted_confidence
            self._persist_agent_decision(
                interaction_id=interaction_id,
                message_id=customer_message.message_id,
                agent_type="escalation",
                decision_type=escalation_decision.escalation_type.value if escalation_decision.escalation_type else "none",
                confidence=escalation_confidence,
                confidence_level=_score_to_confidence_level(escalation_confidence).value,
                processing_time_ms=escalation_duration,
                details={
                    "should_escalate": escalation_decision.should_escalate,
                    "escalation_type": escalation_decision.escalation_type.value if escalation_decision.escalation_type else None,
                    "reason": escalation_decision.escalation_reason.value if escalation_decision.escalation_reason else None,
                    "priority": escalation_decision.priority,
                },
            )
            
            # Step 14: Emit escalation analytics if escalating
            if escalation_decision.should_escalate:
                await self._emit_escalation_analytics(interaction_id)
            
            # Step 15: Determine outcome
            result = self._determine_outcome(
                state,
                primary_output,
                supervisor_review,
                escalation_decision,
                phases_completed,
                start_time,
            )
            
            # Step 16: Store and persist agent response if responding
            if result.should_respond and result.response_content:
                agent_message = await self._store_agent_response(
                    interaction_id,
                    result.response_content,
                    primary_output,
                )
                
                self._persist_message(
                    message_id=agent_message.message_id,
                    interaction_id=interaction_id,
                    role="agent",
                    content=result.response_content,
                    metadata={
                        "intent": primary_output.detected_intent.value if primary_output.detected_intent else None,
                        "confidence": primary_output.confidence.overall_score,
                    },
                )
            
            # Step 17: Update context with topics/issues
            await self._update_context_from_output(interaction_id, primary_output)
            
            # Update state
            self._update_state_from_result(state, result)
            
            # Update persisted interaction status
            self._persist_interaction_status_update(
                interaction_id,
                "escalated" if result.should_escalate else "in_progress",
            )
            
            return result
            
        except Exception as e:
            return self._create_error_result(
                interaction_id,
                str(e),
                state.current_phase,
                start_time,
                phases_completed,
            )

    def _persist_message(
        self,
        message_id: UUID,
        interaction_id: UUID,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """Persist a message to durable storage."""
        try:
            self._persistent_store.save_message(
                message_id=message_id,
                interaction_id=interaction_id,
                role=role,
                content=content,
                metadata=metadata,
            )
        except Exception:
            # Log but don't fail
            pass

    def _persist_agent_decision(
        self,
        interaction_id: UUID,
        agent_type: str,
        decision_type: str,
        confidence: float,
        confidence_level: str,
        processing_time_ms: int,
        message_id: Optional[UUID] = None,
        details: Optional[dict] = None,
    ) -> None:
        """Persist an agent decision to durable storage."""
        try:
            self._persistent_store.save_agent_decision(
                decision_id=uuid4(),
                interaction_id=interaction_id,
                message_id=message_id,
                agent_type=agent_type,
                decision_type=decision_type,
                confidence=confidence,
                confidence_level=confidence_level,
                processing_time_ms=processing_time_ms,
                details=details,
            )
        except Exception:
            # Log but don't fail
            pass

    def _persist_interaction_status_update(
        self,
        interaction_id: UUID,
        status: str,
        ended_at: Optional[datetime] = None,
    ) -> None:
        """Update persisted interaction status."""
        try:
            self._persistent_store.update_interaction_status(
                interaction_id=interaction_id,
                status=status,
                ended_at=ended_at,
            )
        except Exception:
            # Log but don't fail
            pass

    async def _emit_turn_analytics(
        self,
        interaction_id: UUID,
        output: AgentOutput,
        agent_type: AgentType,
    ) -> None:
        """Emit analytics signal for a conversation turn."""
        await self._metrics_engine.record_turn(
            interaction_id=interaction_id,
            intent=output.detected_intent,
            emotion=output.detected_emotion,
            confidence=output.confidence.overall_score,
            agent_type=agent_type,
        )

    async def _emit_escalation_analytics(
        self,
        interaction_id: UUID,
    ) -> None:
        """Emit analytics signal for an escalation event."""
        await self._metrics_engine.record_escalation(interaction_id)

    async def _store_customer_message(
        self,
        interaction_id: UUID,
        content: str,
        metadata: dict,
    ) -> ConversationMessage:
        """Store customer message in context."""
        message = ConversationMessage(
            message_id=uuid4(),
            interaction_id=interaction_id,
            role=MessageRole.CUSTOMER,
            content=content,
            metadata=metadata,
        )
        await self._context_store.add_message(interaction_id, message)
        return message

    async def _store_agent_response(
        self,
        interaction_id: UUID,
        content: str,
        output: AgentOutput,
    ) -> ConversationMessage:
        """Store agent response in context."""
        message = ConversationMessage(
            message_id=uuid4(),
            interaction_id=interaction_id,
            role=MessageRole.AGENT,
            content=content,
            detected_intent=output.detected_intent,
            detected_emotion=output.detected_emotion,
            agent_type=output.agent_type,
            confidence_score=output.confidence.overall_score,
        )
        await self._context_store.add_message(interaction_id, message)
        return message

    async def _store_decision(
        self,
        interaction_id: UUID,
        output: AgentOutput,
        supervisor_approved: Optional[bool],
    ) -> DecisionRecord:
        """Store agent decision in context."""
        record = DecisionRecord(
            decision_id=output.decision_id,
            interaction_id=interaction_id,
            agent_type=output.agent_type,
            decision_summary=output.decision_summary,
            confidence_level=output.confidence.level,
            confidence_score=output.confidence.overall_score,
            reasoning=output.reasoning,
            supervisor_approved=supervisor_approved,
        )
        await self._context_store.add_decision(interaction_id, record)
        return record

    async def _update_decision_with_review(
        self,
        interaction_id: UUID,
        output: AgentOutput,
        review: SupervisorReview,
    ) -> None:
        """Update the stored decision with supervisor review results."""
        history = await self._context_store.get_decision_history(interaction_id)
        if history:
            for decision in reversed(history):
                if decision.decision_id == output.decision_id:
                    decision.supervisor_approved = review.approved
                    decision.supervisor_adjusted_confidence = review.adjusted_confidence
                    break

    async def _update_context_from_output(
        self,
        interaction_id: UUID,
        output: AgentOutput,
    ) -> None:
        """Update context with topics and issues from agent output."""
        if "topics" in output.context_updates:
            for topic in output.context_updates["topics"]:
                await self._context_store.add_topic(interaction_id, topic)
        
        if "unresolved_issues" in output.context_updates:
            for issue in output.context_updates["unresolved_issues"]:
                await self._context_store.add_unresolved_issue(interaction_id, issue)
        
        if "resolved_issues" in output.context_updates:
            for issue in output.context_updates["resolved_issues"]:
                await self._context_store.resolve_issue(interaction_id, issue)

    async def _invoke_primary_agent(
        self,
        agent_input: AgentInput,
    ) -> AgentOutput:
        """Invoke the Primary Agent for initial processing."""
        return await self._primary_agent.execute(agent_input)

    async def _invoke_supervisor_agent(
        self,
        primary_output: AgentOutput,
        original_input: AgentInput,
    ) -> SupervisorReview:
        """Invoke the Supervisor Agent for review."""
        return await self._supervisor_agent.review_decision(
            primary_output,
            original_input,
        )

    async def _invoke_escalation_agent(
        self,
        primary_output: AgentOutput,
        supervisor_review: SupervisorReview,
        original_input: AgentInput,
        escalation_history: List[EscalationOutcome],
    ) -> EscalationDecision:
        """Invoke the Escalation Agent for decision."""
        return await self._escalation_agent.evaluate_for_escalation(
            primary_output,
            supervisor_review,
            original_input,
            escalation_history,
        )

    def _prepare_agent_input(
        self,
        state: InteractionState,
        content: str,
        metadata: dict,
        short_term_context: Optional[ShortTermContext],
    ) -> AgentInput:
        """Prepare structured input for agents with context."""
        context = None
        if short_term_context:
            context = ConversationContext(
                interaction_id=state.interaction_id,
                customer_id=state.interaction.customer_id if state.interaction else None,
                turn_count=short_term_context.turn_count,
                current_intent=short_term_context.current_intent,
                current_emotion=short_term_context.current_emotion,
                intent_history=short_term_context.intent_history,
                emotion_history=short_term_context.emotion_history,
                key_topics=short_term_context.key_topics,
                unresolved_issues=short_term_context.unresolved_issues,
                resolved_issues=[],
                agents_involved=[AgentType.PRIMARY],
                pending_actions=[],
                requires_human_review=short_term_context.has_escalation_history,
                sensitive_topic_detected=short_term_context.sensitive_topic_detected,
                last_updated=datetime.now(timezone.utc),
            )
        
        return AgentInput(
            interaction_id=state.interaction_id,
            content=content,
            context=context,
            suggested_intent=short_term_context.current_intent if short_term_context else None,
            suggested_emotion=short_term_context.current_emotion if short_term_context else None,
            metadata=metadata,
        )

    def _determine_outcome(
        self,
        state: InteractionState,
        primary_output: AgentOutput,
        supervisor_review: SupervisorReview,
        escalation_decision: EscalationDecision,
        phases_completed: List[OrchestrationPhase],
        start_time: datetime,
    ) -> OrchestrationResult:
        """Determine final outcome based on agent outputs."""
        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        should_escalate = escalation_decision.should_escalate
        should_respond = (
            supervisor_review.approved and
            not should_escalate and
            primary_output.response_content is not None
        )
        
        if should_escalate:
            final_phase = OrchestrationPhase.ESCALATION_HANDOFF
            phases_completed.append(OrchestrationPhase.ESCALATION_HANDOFF)
        elif should_respond:
            final_phase = OrchestrationPhase.RESPONSE_DELIVERY
            phases_completed.append(OrchestrationPhase.RESPONSE_DELIVERY)
        else:
            final_phase = OrchestrationPhase.COMPLETED
        
        phases_completed.append(OrchestrationPhase.COMPLETED)
        
        return OrchestrationResult(
            interaction_id=state.interaction_id,
            final_phase=final_phase,
            phases_completed=phases_completed,
            primary_output=primary_output,
            supervisor_review=supervisor_review,
            escalation_decision=escalation_decision,
            should_respond=should_respond,
            should_escalate=should_escalate,
            response_content=primary_output.response_content if should_respond else None,
            total_duration_ms=duration_ms,
            started_at=start_time,
            completed_at=end_time,
        )

    def _update_state_from_result(
        self,
        state: InteractionState,
        result: OrchestrationResult,
    ) -> None:
        """Update interaction state based on orchestration result."""
        state.last_updated = datetime.now(timezone.utc)
        
        if result.should_escalate:
            state.is_escalated = True
            state.requires_human = result.escalation_decision.escalation_type in [
                EscalationType.HUMAN_IMMEDIATE,
                EscalationType.HUMAN_QUEUE,
            ]
            
            if result.escalation_decision:
                outcome = result.escalation_decision.to_escalation_outcome()
                if outcome:
                    state.escalation_history.append(outcome)
        
        if result.final_phase == OrchestrationPhase.COMPLETED:
            state.is_completed = True

    def _create_initial_context(
        self,
        interaction: CustomerInteraction,
    ) -> ConversationContext:
        """Create initial conversation context for an interaction."""
        return ConversationContext(
            interaction_id=interaction.interaction_id,
            customer_id=interaction.customer_id,
            turn_count=0,
            current_intent=None,
            current_emotion=None,
            intent_history=[],
            emotion_history=[],
            key_topics=[],
            unresolved_issues=[],
            resolved_issues=[],
            agents_involved=[AgentType.PRIMARY],
            pending_actions=[],
            requires_human_review=False,
            sensitive_topic_detected=False,
            last_updated=datetime.now(timezone.utc),
        )

    def _create_error_result(
        self,
        interaction_id: UUID,
        error: str,
        error_phase: OrchestrationPhase,
        start_time: datetime,
        phases_completed: Optional[List[OrchestrationPhase]] = None,
    ) -> OrchestrationResult:
        """Create an error result when orchestration fails."""
        end_time = datetime.now(timezone.utc)
        return OrchestrationResult(
            interaction_id=interaction_id,
            final_phase=OrchestrationPhase.FAILED,
            phases_completed=phases_completed or [],
            should_respond=False,
            should_escalate=True,
            total_duration_ms=int((end_time - start_time).total_seconds() * 1000),
            started_at=start_time,
            completed_at=end_time,
            error=error,
            error_phase=error_phase,
        )

    async def end_interaction(
        self,
        interaction_id: UUID,
        resolution: Optional[ResolutionType] = None,
    ) -> Optional[InteractionState]:
        """
        End an interaction with analytics finalization and persistence.
        
        Args:
            interaction_id: Interaction to end.
            resolution: How the interaction was resolved.
            
        Returns:
            Final state for persistence/logging.
        """
        state = self._active_states.get(interaction_id)
        end_time = datetime.now(timezone.utc)
        
        # Determine resolution type
        if resolution is None:
            if state and state.is_escalated:
                resolution = ResolutionType.HUMAN_ESCALATED
            elif state and state.is_completed:
                resolution = ResolutionType.AI_RESOLVED
            else:
                resolution = ResolutionType.ABANDONED
        
        # End in context store
        await self._context_store.end_interaction(interaction_id)
        
        # End in metrics engine with resolution
        await self._metrics_engine.end_interaction(
            interaction_id=interaction_id,
            resolution_type=resolution,
        )
        
        # Persist interaction end
        status = "completed" if resolution == ResolutionType.AI_RESOLVED else \
                 "escalated" if resolution == ResolutionType.HUMAN_ESCALATED else \
                 "abandoned"
        self._persist_interaction_status_update(
            interaction_id,
            status,
            ended_at=end_time,
        )
        
        # Remove from active states
        state = self._active_states.pop(interaction_id, None)
        if state:
            state.is_completed = True
            state.last_updated = end_time
        
        return state

    async def get_conversation_history(
        self,
        interaction_id: UUID,
    ) -> Optional[List[ConversationMessage]]:
        """Get full conversation history for an interaction."""
        return await self._context_store.get_full_history(interaction_id)

    async def get_decision_history(
        self,
        interaction_id: UUID,
    ) -> Optional[List[DecisionRecord]]:
        """Get full decision history for an interaction."""
        return await self._context_store.get_decision_history(interaction_id)

    async def get_interaction_metrics(
        self,
        interaction_id: UUID,
    ):
        """Get metrics for an interaction."""
        return await self._metrics_engine.get_interaction_metrics(interaction_id)

    async def get_aggregated_metrics(self):
        """Get aggregated metrics across all interactions."""
        return await self._metrics_engine.get_aggregated_metrics()

    def get_active_count(self) -> int:
        """Get count of active interactions being tracked."""
        return len(self._active_states)

    def get_past_interactions(
        self,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> list:
        """
        Retrieve past interactions from persistent storage.
        
        Args:
            status: Optional status filter.
            limit: Maximum number of results.
            
        Returns:
            List of interaction summaries.
        """
        return self._persistent_store.list_interactions(status=status, limit=limit)

    def get_past_messages(self, interaction_id: UUID) -> list:
        """
        Retrieve past messages from persistent storage.
        
        Args:
            interaction_id: The interaction to get messages for.
            
        Returns:
            List of stored messages.
        """
        return self._persistent_store.get_messages(interaction_id)

    def get_past_decisions(
        self,
        interaction_id: UUID,
        agent_type: Optional[str] = None,
    ) -> list:
        """
        Retrieve past agent decisions from persistent storage.
        
        Args:
            interaction_id: The interaction to get decisions for.
            agent_type: Optional filter by agent type.
            
        Returns:
            List of stored agent decisions.
        """
        return self._persistent_store.get_agent_decisions(
            interaction_id,
            agent_type=agent_type,
        )
