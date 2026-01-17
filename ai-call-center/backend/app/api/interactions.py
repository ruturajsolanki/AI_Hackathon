"""
Interaction API Endpoints

Thin controllers for managing customer interactions.
All business logic is delegated to the CallOrchestrator.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.models import (
    ChannelType,
    CustomerInteraction,
    InteractionStatus,
)
from app.services.orchestrator import (
    CallOrchestrator,
    OrchestrationPhase,
    OrchestrationResult,
)


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------

class StartInteractionRequest(BaseModel):
    """Request to start a new customer interaction."""
    customer_id: Optional[str] = Field(
        default=None,
        description="Customer identifier (optional for anonymous)"
    )
    channel: ChannelType = Field(
        default=ChannelType.CHAT,
        description="Communication channel"
    )
    initial_message: Optional[str] = Field(
        default=None,
        description="Optional first message from customer"
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Additional metadata"
    )


class StartInteractionResponse(BaseModel):
    """Response after starting an interaction."""
    interaction_id: UUID
    status: InteractionStatus
    channel: ChannelType
    started_at: datetime
    initial_response: Optional[str] = None
    message: str = "Interaction started successfully"


class SendMessageRequest(BaseModel):
    """Request to send a message in an interaction."""
    content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Message content"
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Additional metadata"
    )


class SendMessageResponse(BaseModel):
    """Response after processing a message."""
    interaction_id: UUID
    message_processed: bool
    response_content: Optional[str] = None
    should_escalate: bool = False
    escalation_type: Optional[str] = None
    escalation_reason: Optional[str] = None
    confidence_level: Optional[str] = None
    processing_time_ms: int


class EndInteractionRequest(BaseModel):
    """Request to end an interaction."""
    reason: Optional[str] = Field(
        default=None,
        description="Reason for ending interaction"
    )


class EndInteractionResponse(BaseModel):
    """Response after ending an interaction."""
    interaction_id: UUID
    status: InteractionStatus
    total_turns: int
    was_escalated: bool
    ended_at: datetime
    message: str = "Interaction ended successfully"


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    interaction_id: Optional[UUID] = None


# -----------------------------------------------------------------------------
# Router Setup
# -----------------------------------------------------------------------------

router = APIRouter(prefix="/interactions", tags=["Interactions"])

# Shared orchestrator instance (in production, use dependency injection)
_orchestrator: Optional[CallOrchestrator] = None


def get_orchestrator() -> CallOrchestrator:
    """Get or create the shared orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = CallOrchestrator()
    return _orchestrator


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.post(
    "/start",
    response_model=StartInteractionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal error"},
    },
)
async def start_interaction(
    request: StartInteractionRequest,
) -> StartInteractionResponse:
    """
    Start a new customer interaction.
    
    Creates a new interaction session and optionally processes
    an initial message from the customer.
    """
    orchestrator = get_orchestrator()
    
    try:
        # Create interaction entity
        interaction = CustomerInteraction(
            interaction_id=uuid4(),
            customer_id=request.customer_id,
            channel=request.channel,
            status=InteractionStatus.INITIATED,
            started_at=datetime.now(timezone.utc),
            metadata=request.metadata or {},
        )
        
        # Initialize in orchestrator
        state = await orchestrator.create_interaction(interaction)
        
        # Process initial message if provided
        initial_response = None
        if request.initial_message:
            result = await orchestrator.process_message(
                interaction_id=interaction.interaction_id,
                content=request.initial_message,
                metadata=request.metadata,
            )
            if result.should_respond and result.response_content:
                initial_response = result.response_content
        
        return StartInteractionResponse(
            interaction_id=interaction.interaction_id,
            status=InteractionStatus.IN_PROGRESS,
            channel=request.channel,
            started_at=interaction.started_at,
            initial_response=initial_response,
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start interaction: {str(e)}",
        )


@router.post(
    "/{interaction_id}/message",
    response_model=SendMessageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Interaction not found"},
        500: {"model": ErrorResponse, "description": "Internal error"},
    },
)
async def send_message(
    interaction_id: UUID,
    request: SendMessageRequest,
) -> SendMessageResponse:
    """
    Send a message in an active interaction.
    
    Processes the message through the full agent pipeline
    (Primary → Supervisor → Escalation) and returns the result.
    """
    orchestrator = get_orchestrator()
    
    # Validate interaction exists
    state = orchestrator.get_state(interaction_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interaction {interaction_id} not found",
        )
    
    # Check interaction is still active
    if state.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interaction has already ended",
        )
    
    try:
        # Process message through orchestrator
        result: OrchestrationResult = await orchestrator.process_message(
            interaction_id=interaction_id,
            content=request.content,
            metadata=request.metadata,
        )
        
        # Check for processing errors
        if result.error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error,
            )
        
        # Build response
        response = SendMessageResponse(
            interaction_id=interaction_id,
            message_processed=result.final_phase != OrchestrationPhase.FAILED,
            response_content=result.response_content,
            should_escalate=result.should_escalate,
            processing_time_ms=result.total_duration_ms,
        )
        
        # Add escalation details if applicable
        if result.should_escalate and result.escalation_decision:
            response.escalation_type = result.escalation_decision.escalation_type.value
            if result.escalation_decision.escalation_reason:
                response.escalation_reason = result.escalation_decision.escalation_reason.value
        
        # Add confidence level if available
        if result.primary_output:
            response.confidence_level = result.primary_output.confidence.level.value
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}",
        )


@router.post(
    "/{interaction_id}/end",
    response_model=EndInteractionResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Interaction not found"},
        500: {"model": ErrorResponse, "description": "Internal error"},
    },
)
async def end_interaction(
    interaction_id: UUID,
    request: Optional[EndInteractionRequest] = None,
) -> EndInteractionResponse:
    """
    End an active interaction.
    
    Marks the interaction as complete and returns final statistics.
    """
    orchestrator = get_orchestrator()
    
    # End interaction and get final state
    final_state = await orchestrator.end_interaction(interaction_id)
    
    if not final_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interaction {interaction_id} not found",
        )
    
    return EndInteractionResponse(
        interaction_id=interaction_id,
        status=InteractionStatus.RESOLVED,
        total_turns=final_state.turn_count,
        was_escalated=final_state.is_escalated,
        ended_at=datetime.now(timezone.utc),
    )


@router.get(
    "/{interaction_id}/status",
    responses={
        404: {"model": ErrorResponse, "description": "Interaction not found"},
    },
)
async def get_interaction_status(
    interaction_id: UUID,
) -> dict:
    """
    Get current status of an interaction.
    
    Returns basic status information without full state details.
    """
    orchestrator = get_orchestrator()
    state = orchestrator.get_state(interaction_id)
    
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interaction {interaction_id} not found",
        )
    
    return {
        "interaction_id": interaction_id,
        "phase": state.current_phase.value,
        "turn_count": state.turn_count,
        "is_escalated": state.is_escalated,
        "is_completed": state.is_completed,
        "current_intent": state.current_intent.value if state.current_intent else None,
        "current_emotion": state.current_emotion.value if state.current_emotion else None,
        "last_updated": state.last_updated.isoformat(),
    }
