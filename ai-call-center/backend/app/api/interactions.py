"""
Interaction API Endpoints

Thin controllers for managing customer interactions.
All business logic is delegated to the CallOrchestrator.

Includes streaming endpoint for real-time AI responses.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
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
from app.core.models import IntentCategory, EmotionalState


# -----------------------------------------------------------------------------
# Quick Reply Generator
# -----------------------------------------------------------------------------

def _generate_quick_replies(
    intent: Optional[IntentCategory],
    emotion: Optional[EmotionalState],
    requires_followup: bool,
) -> list[str]:
    """
    Generate contextual quick reply suggestions for the customer.
    
    These help guide the conversation and speed up interactions.
    """
    replies = []
    
    # Context-specific replies based on intent
    intent_replies = {
        IntentCategory.BILLING_INQUIRY: [
            "Show my current balance",
            "View recent charges",
            "Payment options",
        ],
        IntentCategory.TECHNICAL_SUPPORT: [
            "I've tried restarting",
            "Show troubleshooting steps",
            "Connect me to a specialist",
        ],
        IntentCategory.ACCOUNT_MANAGEMENT: [
            "Update my email",
            "Reset my password",
            "View account settings",
        ],
        IntentCategory.ORDER_STATUS: [
            "Track my order",
            "Where's my package?",
            "Change delivery address",
        ],
        IntentCategory.CANCELLATION: [
            "I want to cancel",
            "What are my options?",
            "Talk to retention team",
        ],
        IntentCategory.PRODUCT_INFORMATION: [
            "Compare products",
            "Show features",
            "What's the price?",
        ],
        IntentCategory.COMPLAINT: [
            "Speak to a manager",
            "File a formal complaint",
            "I need a resolution now",
        ],
    }
    
    if intent and intent in intent_replies:
        replies.extend(intent_replies[intent][:2])
    
    # Add emotion-sensitive replies
    if emotion == EmotionalState.FRUSTRATED:
        replies.append("I need to speak to someone")
    elif emotion == EmotionalState.CONFUSED:
        replies.append("Can you explain that again?")
    elif emotion == EmotionalState.SATISFIED:
        replies.append("That's all, thank you!")
    
    # Add generic helpful options
    if requires_followup:
        replies.append("Yes, that's right")
        replies.append("No, I meant something else")
    else:
        if "That's all, thank you!" not in replies:
            replies.append("That's all I needed")
    
    # Limit to 4 suggestions for clean UX
    return replies[:4]


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
    
    # Quick replies for UX improvement
    suggested_replies: list[str] = Field(
        default_factory=list,
        description="Suggested quick reply options for the customer"
    )
    detected_intent: Optional[str] = None
    detected_emotion: Optional[str] = None
    
    # Source attribution for transparency
    source_attribution: Optional[str] = Field(
        default=None,
        description="Source of the response (e.g., 'Based on: Billing Policy')"
    )
    
    # Sentiment tracking
    sentiment_trend: Optional[str] = Field(
        default=None,
        description="Emotional trajectory: 'improving', 'declining', or 'stable'"
    )


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
_last_provider: Optional[str] = None
_last_ollama_url: Optional[str] = None


def get_orchestrator() -> CallOrchestrator:
    """
    Get or create the shared orchestrator instance.
    
    Recreates the orchestrator if the LLM provider has changed
    (e.g., user switched from OpenAI to Ollama in settings).
    """
    global _orchestrator, _last_provider, _last_ollama_url
    
    # Check current provider config
    from app.api.config import get_runtime_config
    runtime_config = get_runtime_config()
    current_provider = runtime_config.get_provider().value
    current_ollama_url = runtime_config.get_ollama_url() if current_provider == "ollama" else None
    
    # Recreate orchestrator if provider changed or Ollama URL changed
    provider_changed = _last_provider != current_provider
    ollama_url_changed = current_provider == "ollama" and _last_ollama_url != current_ollama_url
    
    if _orchestrator is None or provider_changed or ollama_url_changed:
        if provider_changed:
            import logging
            logging.getLogger(__name__).info(f"LLM provider changed from {_last_provider} to {current_provider}, recreating orchestrator")
        _orchestrator = CallOrchestrator()
        _last_provider = current_provider
        _last_ollama_url = current_ollama_url
    
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
        
        # Add confidence level, intent, emotion, and quick replies if available
        if result.primary_output:
            response.confidence_level = result.primary_output.confidence.level.value
            response.detected_intent = result.primary_output.detected_intent.value if result.primary_output.detected_intent else None
            response.detected_emotion = result.primary_output.detected_emotion.value if result.primary_output.detected_emotion else None
            
            # Generate quick reply suggestions based on context
            response.suggested_replies = _generate_quick_replies(
                result.primary_output.detected_intent,
                result.primary_output.detected_emotion,
                result.primary_output.requires_followup,
            )
            
            # Extract source attribution from context updates
            context_updates = result.primary_output.context_updates or {}
            if 'source_attribution' in context_updates:
                response.source_attribution = f"Based on: {context_updates['source_attribution']}"
        
        # Get sentiment trend from orchestrator
        try:
            state = orchestrator.get_state(interaction_id)
            if state and state.interaction:
                # Simple sentiment trend based on emotion history
                emotion_history = state.emotion_history if hasattr(state, 'emotion_history') else []
                if len(emotion_history) >= 2:
                    # Use simplified scoring
                    positive_emotions = ['satisfied', 'neutral']
                    recent = [e.value if hasattr(e, 'value') else str(e) for e in emotion_history[-3:]]
                    
                    first_half = recent[:len(recent)//2] if len(recent) > 1 else recent
                    second_half = recent[len(recent)//2:] if len(recent) > 1 else recent
                    
                    first_positive = sum(1 for e in first_half if e in positive_emotions)
                    second_positive = sum(1 for e in second_half if e in positive_emotions)
                    
                    if second_positive > first_positive:
                        response.sentiment_trend = "improving"
                    elif second_positive < first_positive:
                        response.sentiment_trend = "declining"
                    else:
                        response.sentiment_trend = "stable"
                else:
                    response.sentiment_trend = "stable"
        except Exception:
            response.sentiment_trend = "stable"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}",
        )


# -----------------------------------------------------------------------------
# Streaming Endpoint
# -----------------------------------------------------------------------------

async def stream_response_generator(
    interaction_id: UUID,
    content: str,
    metadata: Optional[dict],
) -> AsyncGenerator[str, None]:
    """
    Generator for streaming AI response via SSE.
    
    Sends events:
    - status: Processing status updates
    - token: Individual response tokens (simulated word-by-word)
    - complete: Final result with metadata
    - error: If something goes wrong
    """
    orchestrator = get_orchestrator()
    
    try:
        # Send initial status
        yield f"data: {json.dumps({'event': 'status', 'data': {'phase': 'processing', 'message': 'Processing your request...'}})}\n\n"
        await asyncio.sleep(0.1)
        
        # Process through orchestrator
        result: OrchestrationResult = await orchestrator.process_message(
            interaction_id=interaction_id,
            content=content,
            metadata=metadata,
        )
        
        if result.error:
            yield f"data: {json.dumps({'event': 'error', 'data': {'message': result.error}})}\n\n"
            return
        
        # Simulate streaming the response word by word
        if result.response_content:
            words = result.response_content.split()
            accumulated = ""
            
            for i, word in enumerate(words):
                accumulated += word + " "
                yield f"data: {json.dumps({'event': 'token', 'data': {'token': word + ' ', 'accumulated': accumulated.strip(), 'progress': (i + 1) / len(words)}})}\n\n"
                # Simulate typing delay (20-50ms per word)
                await asyncio.sleep(0.02 + (len(word) * 0.005))
        
        # Send complete event with full metadata
        complete_data = {
            'event': 'complete',
            'data': {
                'response': result.response_content,
                'should_escalate': result.should_escalate,
                'processing_time_ms': result.total_duration_ms,
                'escalation_type': result.escalation_decision.escalation_type.value if result.escalation_decision else None,
                'escalation_reason': result.escalation_decision.escalation_reason.value if (result.escalation_decision and result.escalation_decision.escalation_reason) else None,
                'confidence_level': result.primary_output.confidence.level.value if result.primary_output else None,
                'confidence_score': result.primary_output.confidence.overall_score if result.primary_output else None,
                'intent': result.primary_output.detected_intent.value if result.primary_output else None,
                'emotion': result.primary_output.detected_emotion.value if result.primary_output else None,
            }
        }
        yield f"data: {json.dumps(complete_data)}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'event': 'error', 'data': {'message': str(e)}})}\n\n"


@router.post(
    "/{interaction_id}/message/stream",
    response_class=StreamingResponse,
    responses={
        404: {"description": "Interaction not found"},
        500: {"description": "Internal error"},
    },
)
async def send_message_stream(
    interaction_id: UUID,
    request: SendMessageRequest,
):
    """
    Send a message and receive streaming AI response via SSE.
    
    Returns a Server-Sent Events stream with:
    - status: Processing phase updates
    - token: Individual response tokens (streamed as they arrive)
    - complete: Final result with full metadata
    - error: If an error occurs
    
    This provides a more responsive UX as users see the response
    being typed out in real-time rather than waiting for the full response.
    """
    orchestrator = get_orchestrator()
    
    # Validate interaction exists
    state = orchestrator.get_state(interaction_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interaction {interaction_id} not found",
        )
    
    if state.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interaction has already ended",
        )
    
    return StreamingResponse(
        stream_response_generator(interaction_id, request.content, request.metadata),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
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
