"""
Base Agent Abstraction

Defines the standard interface for all autonomous AI agents in the system.
This abstract base class establishes the contract for decision-making,
input/output structures, and confidence reporting.

All concrete agent implementations must inherit from BaseAgent and
implement the required abstract methods.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.core.models import (
    AgentType,
    AgentDecision,
    ConfidenceLevel,
    ConversationContext,
    DecisionType,
    EmotionalState,
    IntentCategory,
)


# -----------------------------------------------------------------------------
# Agent Input/Output Structures
# -----------------------------------------------------------------------------

class AgentInput(BaseModel):
    """
    Structured input provided to an agent for processing.
    
    Contains all information an agent needs to make a decision,
    including the current message, conversation context, and
    any relevant metadata.
    """
    interaction_id: UUID = Field(description="Active interaction identifier")
    message_id: UUID = Field(default_factory=uuid4, description="Current message identifier")
    
    # Current turn
    content: str = Field(description="The message or input to process")
    content_type: str = Field(default="text", description="Type of content (text, audio_transcript)")
    
    # Context
    context: Optional[ConversationContext] = Field(
        default=None,
        description="Accumulated conversation context"
    )
    
    # Classification hints (if pre-processed)
    suggested_intent: Optional[IntentCategory] = Field(default=None)
    suggested_emotion: Optional[EmotionalState] = Field(default=None)
    
    # Metadata
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConfidenceReport(BaseModel):
    """
    Detailed confidence assessment for a decision.
    
    Provides transparency into how confident the agent is
    and what factors influenced that assessment.
    """
    overall_score: float = Field(
        ge=0.0, le=1.0,
        description="Overall confidence score (0.0 to 1.0)"
    )
    level: ConfidenceLevel = Field(description="Categorical confidence level")
    
    # Contributing factors
    intent_confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in intent detection"
    )
    emotion_confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in emotion detection"
    )
    context_confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in context understanding"
    )
    
    # Reasoning
    factors: List[str] = Field(
        default_factory=list,
        description="Factors that influenced confidence"
    )
    concerns: List[str] = Field(
        default_factory=list,
        description="Factors that reduced confidence"
    )
    
    # Thresholds
    meets_autonomous_threshold: bool = Field(
        description="Whether confidence is sufficient for autonomous action"
    )
    requires_supervision: bool = Field(
        description="Whether supervisor review is recommended"
    )
    requires_escalation: bool = Field(
        description="Whether escalation to human is recommended"
    )


class AgentOutput(BaseModel):
    """
    Structured output produced by an agent after processing.
    
    Contains the decision, response content, confidence assessment,
    and any recommended next actions.
    """
    decision_id: UUID = Field(default_factory=uuid4)
    interaction_id: UUID = Field(description="Associated interaction")
    agent_type: AgentType = Field(description="Agent that produced this output")
    
    # Decision
    decision_type: DecisionType = Field(description="Type of decision made")
    decision_summary: str = Field(description="Human-readable decision summary")
    
    # Response
    response_content: Optional[str] = Field(
        default=None,
        description="Response to deliver to customer (if applicable)"
    )
    
    # Classification
    detected_intent: Optional[IntentCategory] = Field(default=None)
    detected_emotion: Optional[EmotionalState] = Field(default=None)
    
    # Confidence
    confidence: ConfidenceReport = Field(description="Confidence assessment")
    
    # Reasoning (for explainability)
    reasoning: List[str] = Field(
        default_factory=list,
        description="Step-by-step reasoning for the decision"
    )
    
    # Next actions
    requires_followup: bool = Field(default=False)
    recommended_actions: List[str] = Field(
        default_factory=list,
        description="Suggested next actions"
    )
    escalation_target: Optional[AgentType] = Field(
        default=None,
        description="Target agent if escalation is recommended"
    )
    
    # Context updates
    context_updates: Dict[str, Any] = Field(
        default_factory=dict,
        description="Updates to apply to conversation context"
    )
    
    # Timing
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processing_duration_ms: Optional[int] = Field(default=None)

    def to_agent_decision(self) -> AgentDecision:
        """Convert output to an AgentDecision for persistence."""
        return AgentDecision(
            decision_id=self.decision_id,
            interaction_id=self.interaction_id,
            agent_type=self.agent_type,
            decision_type=self.decision_type,
            decision_summary=self.decision_summary,
            confidence_level=self.confidence.level,
            confidence_score=self.confidence.overall_score,
            reasoning_factors=self.reasoning,
            detected_intent=self.detected_intent,
            detected_emotion=self.detected_emotion,
            action_taken=self.decision_summary,
            requires_followup=self.requires_followup,
            decided_at=self.processed_at,
            reviewed_by_supervisor=False,
            supervisor_override=False,
        )


# -----------------------------------------------------------------------------
# Base Agent Abstract Class
# -----------------------------------------------------------------------------

class BaseAgent(ABC):
    """
    Abstract base class for all autonomous AI agents.
    
    Defines the standard interface that all agents must implement,
    ensuring consistent behavior across Primary, Supervisor, and
    Escalation agents.
    
    Concrete implementations must provide:
    - process(): Main decision-making logic
    - assess_confidence(): Confidence evaluation
    - get_agent_type(): Agent type identifier
    
    Optional overrides:
    - validate_input(): Custom input validation
    - pre_process(): Pre-processing hooks
    - post_process(): Post-processing hooks
    """

    def __init__(self, agent_id: Optional[str] = None):
        """
        Initialize the base agent.
        
        Args:
            agent_id: Optional unique identifier for this agent instance.
                     If not provided, a UUID will be generated.
        """
        self._agent_id = agent_id or str(uuid4())
        self._initialized_at = datetime.now(timezone.utc)

    @property
    def agent_id(self) -> str:
        """Unique identifier for this agent instance."""
        return self._agent_id

    @property
    @abstractmethod
    def agent_type(self) -> AgentType:
        """
        Return the type of this agent.
        
        Must be implemented by concrete classes to identify
        the agent type (PRIMARY, SUPERVISOR, ESCALATION).
        """
        pass

    @abstractmethod
    async def process(self, input_data: AgentInput) -> AgentOutput:
        """
        Process input and produce a decision.
        
        This is the main entry point for agent decision-making.
        Implementations should analyze the input, apply their
        specific logic, and return a structured output.
        
        Args:
            input_data: Structured input containing message and context.
            
        Returns:
            AgentOutput containing decision, response, and confidence.
        """
        pass

    @abstractmethod
    async def assess_confidence(
        self,
        input_data: AgentInput,
        preliminary_decision: DecisionType,
    ) -> ConfidenceReport:
        """
        Assess confidence in a preliminary decision.
        
        Evaluates how confident the agent is in the given decision
        based on the input data and context. This assessment
        influences whether the agent acts autonomously or escalates.
        
        Args:
            input_data: The input being processed.
            preliminary_decision: The decision being considered.
            
        Returns:
            ConfidenceReport with detailed confidence assessment.
        """
        pass

    def validate_input(self, input_data: AgentInput) -> bool:
        """
        Validate input data before processing.
        
        Override to add custom validation logic.
        Default implementation performs basic validation.
        
        Args:
            input_data: Input to validate.
            
        Returns:
            True if input is valid, False otherwise.
        """
        if not input_data.content:
            return False
        if not input_data.interaction_id:
            return False
        return True

    async def pre_process(self, input_data: AgentInput) -> AgentInput:
        """
        Pre-process input before main processing.
        
        Override to add pre-processing logic such as
        normalization, enrichment, or filtering.
        
        Args:
            input_data: Original input.
            
        Returns:
            Processed input (may be modified).
        """
        return input_data

    async def post_process(self, output: AgentOutput) -> AgentOutput:
        """
        Post-process output before returning.
        
        Override to add post-processing logic such as
        sanitization, logging, or enrichment.
        
        Args:
            output: Original output.
            
        Returns:
            Processed output (may be modified).
        """
        return output

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute the full agent processing pipeline.
        
        This method orchestrates the complete flow:
        1. Validate input
        2. Pre-process
        3. Process (main logic)
        4. Post-process
        
        Args:
            input_data: Input to process.
            
        Returns:
            Final processed output.
            
        Raises:
            ValueError: If input validation fails.
        """
        # Validate
        if not self.validate_input(input_data):
            raise ValueError("Invalid input data")
        
        # Pre-process
        processed_input = await self.pre_process(input_data)
        
        # Main processing
        output = await self.process(processed_input)
        
        # Post-process
        final_output = await self.post_process(output)
        
        return final_output

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._agent_id}, type={self.agent_type.value})"
