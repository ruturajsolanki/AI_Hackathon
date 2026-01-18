"""
Call History API Routes

Read-only endpoints for accessing interaction history.
Safe for production demos - no internal agent logic exposed.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.persistence.store import get_store

router = APIRouter(prefix="/history", tags=["History"])


def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO datetime string to datetime object."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None


# -----------------------------------------------------------------------------
# Response Models (UI-friendly structure)
# -----------------------------------------------------------------------------

class InteractionSummary(BaseModel):
    """Summary of an interaction for list views."""
    interaction_id: str
    customer_id: Optional[str] = None
    channel: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    message_count: int = 0
    was_escalated: bool = False


class MessageItem(BaseModel):
    """A single message in an interaction."""
    message_id: str
    role: str  # 'customer' | 'agent' | 'system'
    content: str
    timestamp: datetime
    intent: Optional[str] = None
    emotion: Optional[str] = None
    confidence: Optional[float] = None


class DecisionItem(BaseModel):
    """A single agent decision (simplified for UI)."""
    decision_id: str
    agent_type: str  # 'primary' | 'supervisor' | 'escalation'
    summary: str
    confidence: float
    confidence_level: str
    timestamp: datetime
    processing_time_ms: int


class InteractionDetail(BaseModel):
    """Full interaction details with messages and decisions."""
    interaction_id: str
    customer_id: Optional[str] = None
    channel: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    messages: List[MessageItem] = Field(default_factory=list)
    decisions: List[DecisionItem] = Field(default_factory=list)
    was_escalated: bool = False
    resolution_summary: Optional[str] = None


class InteractionListResponse(BaseModel):
    """Response for listing interactions."""
    interactions: List[InteractionSummary]
    total: int
    page: int
    page_size: int
    has_more: bool


# -----------------------------------------------------------------------------
# API Routes
# -----------------------------------------------------------------------------

@router.get(
    "/interactions",
    response_model=InteractionListResponse,
    summary="List all interactions",
    description="Returns a paginated list of interaction summaries. "
                "Does not include message content or detailed decisions.",
)
async def list_interactions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(
        None, 
        alias="status",
        description="Filter by status (e.g., 'completed', 'in_progress', 'escalated')"
    ),
    channel: Optional[str] = Query(
        None,
        description="Filter by channel (e.g., 'voice', 'chat')"
    ),
) -> InteractionListResponse:
    """
    List all interactions with optional filtering.
    
    Returns summary data only - no message content or internal logic exposed.
    """
    store = get_store()
    offset = (page - 1) * page_size
    
    # Get interactions from store
    interactions = store.list_interactions(
        status=status_filter,
        limit=page_size + 1,  # Get one extra to check if there's more
        offset=offset,
    )
    
    has_more = len(interactions) > page_size
    if has_more:
        interactions = interactions[:page_size]
    
    # Transform to UI-friendly format
    summaries = []
    for interaction in interactions:
        # Parse timestamps
        started_at = _parse_datetime(interaction.started_at)
        ended_at = _parse_datetime(interaction.ended_at)
        
        # Calculate duration if ended
        duration = None
        if ended_at and started_at:
            delta = ended_at - started_at
            duration = int(delta.total_seconds())
        
        # Check if escalated (from decision_count in summary)
        decisions = store.get_agent_decisions(UUID(interaction.interaction_id))
        was_escalated = any(
            d.agent_type == "escalation" and 
            d.details.get("should_escalate", False)
            for d in decisions
        )
        
        summaries.append(InteractionSummary(
            interaction_id=interaction.interaction_id,
            customer_id=interaction.customer_id,
            channel=interaction.channel,
            status=interaction.status,
            started_at=started_at or datetime.now(),
            ended_at=ended_at,
            duration_seconds=duration,
            message_count=interaction.message_count,
            was_escalated=was_escalated,
        ))
    
    # Get total count (simplified - in production use COUNT query)
    all_interactions = store.list_interactions(
        status=status_filter,
        limit=1000,
        offset=0,
    )
    
    return InteractionListResponse(
        interactions=summaries,
        total=len(all_interactions),
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


@router.get(
    "/interactions/{interaction_id}",
    response_model=InteractionDetail,
    summary="Get interaction details",
    description="Returns full interaction details including messages and decisions. "
                "Internal agent logic is not exposed.",
    responses={
        404: {"description": "Interaction not found"},
    },
)
async def get_interaction(
    interaction_id: UUID,
) -> InteractionDetail:
    """
    Get detailed information about a specific interaction.
    
    Includes:
    - All messages (customer and agent)
    - Agent decisions (simplified, no internal logic)
    - Timing and status information
    """
    store = get_store()
    
    # Get interaction
    interaction = store.get_interaction(interaction_id)
    if not interaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interaction {interaction_id} not found",
        )
    
    # Parse timestamps
    started_at = _parse_datetime(interaction.started_at)
    ended_at = _parse_datetime(interaction.ended_at)
    
    # Get messages
    raw_messages = store.get_messages(interaction_id)
    messages = [
        MessageItem(
            message_id=m.message_id,
            role=m.role,
            content=m.content,
            timestamp=_parse_datetime(m.timestamp) or datetime.now(),
            intent=m.metadata.get("intent"),
            emotion=m.metadata.get("emotion"),
            confidence=m.metadata.get("confidence"),
        )
        for m in raw_messages
    ]
    
    # Get decisions (simplified for UI)
    raw_decisions = store.get_agent_decisions(interaction_id)
    decisions = [
        DecisionItem(
            decision_id=d.decision_id,
            agent_type=d.agent_type,
            summary=d.decision_type,
            confidence=d.confidence,
            confidence_level=d.confidence_level,
            timestamp=_parse_datetime(d.timestamp) or datetime.now(),
            processing_time_ms=d.processing_time_ms,
        )
        for d in raw_decisions
    ]
    
    # Calculate duration
    duration = None
    if ended_at and started_at:
        delta = ended_at - started_at
        duration = int(delta.total_seconds())
    
    # Check escalation
    was_escalated = any(
        d.details.get("should_escalate", False)
        for d in raw_decisions
        if d.agent_type == "escalation"
    )
    
    # Generate resolution summary
    resolution_summary = None
    if interaction.status == "completed":
        if was_escalated:
            resolution_summary = "Escalated to human agent"
        else:
            resolution_summary = "Resolved by AI agent"
    elif interaction.status == "in_progress":
        resolution_summary = "In progress"
    
    return InteractionDetail(
        interaction_id=interaction.interaction_id,
        customer_id=interaction.customer_id,
        channel=interaction.channel,
        status=interaction.status,
        started_at=started_at or datetime.now(),
        ended_at=ended_at,
        duration_seconds=duration,
        messages=messages,
        decisions=decisions,
        was_escalated=was_escalated,
        resolution_summary=resolution_summary,
    )


@router.get(
    "/interactions/{interaction_id}/messages",
    response_model=List[MessageItem],
    summary="Get interaction messages",
    description="Returns only the messages for an interaction.",
    responses={
        404: {"description": "Interaction not found"},
    },
)
async def get_interaction_messages(
    interaction_id: UUID,
) -> List[MessageItem]:
    """
    Get just the messages for an interaction.
    
    Useful for real-time updates or pagination of long conversations.
    """
    store = get_store()
    
    # Verify interaction exists
    interaction = store.get_interaction(interaction_id)
    if not interaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interaction {interaction_id} not found",
        )
    
    raw_messages = store.get_messages(interaction_id)
    
    return [
        MessageItem(
            message_id=m.message_id,
            role=m.role,
            content=m.content,
            timestamp=_parse_datetime(m.timestamp) or datetime.now(),
            intent=m.metadata.get("intent"),
            emotion=m.metadata.get("emotion"),
            confidence=m.metadata.get("confidence"),
        )
        for m in raw_messages
    ]


@router.get(
    "/interactions/{interaction_id}/decisions",
    response_model=List[DecisionItem],
    summary="Get interaction decisions",
    description="Returns the agent decisions for an interaction (simplified).",
    responses={
        404: {"description": "Interaction not found"},
    },
)
async def get_interaction_decisions(
    interaction_id: UUID,
) -> List[DecisionItem]:
    """
    Get just the agent decisions for an interaction.
    
    Returns simplified decision data - internal agent logic is not exposed.
    """
    store = get_store()
    
    # Verify interaction exists
    interaction = store.get_interaction(interaction_id)
    if not interaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interaction {interaction_id} not found",
        )
    
    raw_decisions = store.get_agent_decisions(interaction_id)
    
    return [
        DecisionItem(
            decision_id=d.decision_id,
            agent_type=d.agent_type,
            summary=d.decision_type,
            confidence=d.confidence,
            confidence_level=d.confidence_level,
            timestamp=_parse_datetime(d.timestamp) or datetime.now(),
            processing_time_ms=d.processing_time_ms,
        )
        for d in raw_decisions
    ]


@router.get(
    "/stats",
    summary="Get call history statistics",
    description="Returns aggregate statistics about all interactions.",
)
async def get_history_stats() -> dict:
    """
    Get aggregate statistics for the call history.
    
    Returns counts and averages for dashboards.
    """
    store = get_store()
    
    # Get all interactions
    all_interactions = store.list_interactions(limit=10000)
    
    total = len(all_interactions)
    completed = sum(1 for i in all_interactions if i.status == "completed")
    in_progress = sum(1 for i in all_interactions if i.status == "in_progress")
    
    # Calculate average duration for completed
    durations = []
    for i in all_interactions:
        started = _parse_datetime(i.started_at)
        ended = _parse_datetime(i.ended_at)
        if ended and started:
            delta = ended - started
            durations.append(delta.total_seconds())
    
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    # Count by channel
    channels: dict[str, int] = {}
    for i in all_interactions:
        channels[i.channel] = channels.get(i.channel, 0) + 1
    
    return {
        "total_interactions": total,
        "completed": completed,
        "in_progress": in_progress,
        "average_duration_seconds": round(avg_duration, 1),
        "by_channel": channels,
    }
