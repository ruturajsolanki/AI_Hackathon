"""
Ticket Management API

Handles escalated calls as tickets that human agents can pick up.
Provides endpoints for listing, accepting, and managing tickets.
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.persistence.store import get_store

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

class TicketStatus(str, Enum):
    """Ticket lifecycle status."""
    PENDING = "pending"           # Waiting for human agent
    ACCEPTED = "accepted"         # Human agent has accepted
    IN_PROGRESS = "in_progress"   # Human agent is working on it
    RESOLVED = "resolved"         # Issue resolved
    ABANDONED = "abandoned"       # Customer disconnected


class TicketPriority(str, Enum):
    """Ticket priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# -----------------------------------------------------------------------------
# In-Memory Ticket Store (Production would use database)
# -----------------------------------------------------------------------------

class Ticket(BaseModel):
    """Represents an escalated call ticket."""
    ticket_id: UUID = Field(default_factory=uuid4)
    interaction_id: UUID
    status: TicketStatus = TicketStatus.PENDING
    priority: TicketPriority = TicketPriority.MEDIUM
    
    # Customer info
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    
    # AI Summary
    issue_summary: str
    ai_attempts: int = 0
    escalation_reason: str
    detected_intent: Optional[str] = None
    detected_emotion: Optional[str] = None
    
    # Conversation history
    message_count: int = 0
    last_customer_message: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    accepted_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Agent assignment
    assigned_agent_id: Optional[str] = None
    assigned_agent_name: Optional[str] = None
    
    # Live session
    session_url: Optional[str] = None
    session_active: bool = False


# In-memory ticket store
_tickets: Dict[UUID, Ticket] = {}


def get_ticket(ticket_id: UUID) -> Optional[Ticket]:
    """Get a ticket by ID."""
    return _tickets.get(ticket_id)


def get_tickets_by_interaction(interaction_id: UUID) -> List[Ticket]:
    """Get all tickets for an interaction."""
    return [t for t in _tickets.values() if t.interaction_id == interaction_id]


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------

class TicketSummary(BaseModel):
    """Brief ticket info for list views."""
    ticket_id: UUID
    interaction_id: UUID
    status: TicketStatus
    priority: TicketPriority
    issue_summary: str
    escalation_reason: str
    customer_name: Optional[str]
    created_at: datetime
    wait_time_seconds: int


class TicketDetail(BaseModel):
    """Full ticket information for detail view."""
    ticket_id: UUID
    interaction_id: UUID
    status: TicketStatus
    priority: TicketPriority
    
    # Customer
    customer_id: Optional[str]
    customer_name: Optional[str]
    
    # AI Summary
    issue_summary: str
    ai_attempts: int
    escalation_reason: str
    detected_intent: Optional[str]
    detected_emotion: Optional[str]
    
    # Conversation
    message_count: int
    last_customer_message: Optional[str]
    conversation_history: List[dict]
    
    # AI Decision Trail
    ai_decisions: List[dict]
    
    # Suggested Actions
    suggested_actions: List[str]
    
    # Timestamps
    created_at: datetime
    wait_time_seconds: int
    
    # Session
    session_url: Optional[str]


class AcceptTicketRequest(BaseModel):
    """Request to accept a ticket."""
    agent_id: str
    agent_name: str


class AcceptTicketResponse(BaseModel):
    """Response after accepting a ticket."""
    success: bool
    ticket_id: UUID
    session_url: str
    message: str


class ResolveTicketRequest(BaseModel):
    """Request to resolve a ticket."""
    resolution_notes: str
    resolution_type: str = "resolved"  # resolved, transferred, callback_scheduled


# -----------------------------------------------------------------------------
# Router
# -----------------------------------------------------------------------------

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get(
    "",
    response_model=List[TicketSummary],
    summary="List all tickets",
)
async def list_tickets(
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
) -> List[TicketSummary]:
    """
    List all tickets, optionally filtered by status or priority.
    
    Returns tickets sorted by priority (critical first) then by wait time.
    """
    now = datetime.now(timezone.utc)
    
    tickets = list(_tickets.values())
    
    # Filter by status
    if status:
        tickets = [t for t in tickets if t.status == status]
    
    # Filter by priority
    if priority:
        tickets = [t for t in tickets if t.priority == priority]
    
    # Sort by priority then by creation time
    priority_order = {
        TicketPriority.CRITICAL: 0,
        TicketPriority.HIGH: 1,
        TicketPriority.MEDIUM: 2,
        TicketPriority.LOW: 3,
    }
    tickets.sort(key=lambda t: (priority_order[t.priority], t.created_at))
    
    return [
        TicketSummary(
            ticket_id=t.ticket_id,
            interaction_id=t.interaction_id,
            status=t.status,
            priority=t.priority,
            issue_summary=t.issue_summary,
            escalation_reason=t.escalation_reason,
            customer_name=t.customer_name,
            created_at=t.created_at,
            wait_time_seconds=int((now - t.created_at).total_seconds()),
        )
        for t in tickets
    ]


@router.get(
    "/pending",
    response_model=List[TicketSummary],
    summary="List pending tickets",
)
async def list_pending_tickets() -> List[TicketSummary]:
    """Get all tickets waiting for human agents."""
    return await list_tickets(status=TicketStatus.PENDING)


@router.get(
    "/{ticket_id}",
    response_model=TicketDetail,
    summary="Get ticket details",
)
async def get_ticket_detail(ticket_id: UUID) -> TicketDetail:
    """
    Get full ticket details including conversation history and AI decisions.
    """
    ticket = get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found",
        )
    
    # Fetch conversation history from persistent store
    store = get_store()
    messages = store.get_messages(ticket.interaction_id)
    decisions = store.get_decisions(ticket.interaction_id)
    
    conversation_history = [
        {
            "role": m.role,
            "content": m.content,
            "timestamp": m.timestamp.isoformat() if m.timestamp else None,
        }
        for m in messages
    ]
    
    ai_decisions = [
        {
            "agent_type": d.agent_type.value if hasattr(d.agent_type, 'value') else str(d.agent_type),
            "decision_type": d.decision_type.value if hasattr(d.decision_type, 'value') else str(d.decision_type),
            "summary": d.decision_summary,
            "confidence": d.confidence_score,
            "timestamp": d.decided_at.isoformat() if d.decided_at else None,
        }
        for d in decisions
    ]
    
    # Generate suggested actions based on context
    suggested_actions = _generate_suggested_actions(ticket, messages, decisions)
    
    now = datetime.now(timezone.utc)
    
    return TicketDetail(
        ticket_id=ticket.ticket_id,
        interaction_id=ticket.interaction_id,
        status=ticket.status,
        priority=ticket.priority,
        customer_id=ticket.customer_id,
        customer_name=ticket.customer_name,
        issue_summary=ticket.issue_summary,
        ai_attempts=ticket.ai_attempts,
        escalation_reason=ticket.escalation_reason,
        detected_intent=ticket.detected_intent,
        detected_emotion=ticket.detected_emotion,
        message_count=len(messages),
        last_customer_message=ticket.last_customer_message,
        conversation_history=conversation_history,
        ai_decisions=ai_decisions,
        suggested_actions=suggested_actions,
        created_at=ticket.created_at,
        wait_time_seconds=int((now - ticket.created_at).total_seconds()),
        session_url=ticket.session_url,
    )


@router.post(
    "/{ticket_id}/accept",
    response_model=AcceptTicketResponse,
    summary="Accept a ticket",
)
async def accept_ticket(
    ticket_id: UUID,
    request: AcceptTicketRequest,
) -> AcceptTicketResponse:
    """
    Accept a ticket and get a live session URL.
    
    Creates a unique session for the human agent to continue
    the conversation with the customer.
    """
    ticket = get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found",
        )
    
    if ticket.status != TicketStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ticket is already {ticket.status.value}",
        )
    
    # Update ticket
    ticket.status = TicketStatus.ACCEPTED
    ticket.accepted_at = datetime.now(timezone.utc)
    ticket.assigned_agent_id = request.agent_id
    ticket.assigned_agent_name = request.agent_name
    
    # Use interaction_id as session ID so customer and agent share same session
    session_id = ticket.interaction_id
    ticket.session_url = f"/session/{session_id}"
    ticket.session_active = True
    
    # Store session mapping (use string for consistency)
    _session_to_ticket[session_id] = ticket_id
    
    # Initialize session with agent info
    session_id_str = str(session_id)
    if session_id_str not in _sessions:
        _sessions[session_id_str] = {
            "is_active": True,
            "agent_connected": True,
            "agent_name": request.agent_name,
            "customer_connected": True,
            "messages": [],
        }
    else:
        _sessions[session_id_str]["agent_connected"] = True
        _sessions[session_id_str]["agent_name"] = request.agent_name
        _sessions[session_id_str]["is_active"] = True
    
    logger.info(f"Ticket {ticket_id} accepted by agent {request.agent_name}")
    
    return AcceptTicketResponse(
        success=True,
        ticket_id=ticket_id,
        session_url=ticket.session_url,
        message=f"Ticket accepted. Session ready for customer.",
    )


@router.post(
    "/{ticket_id}/resolve",
    summary="Resolve a ticket",
)
async def resolve_ticket(
    ticket_id: UUID,
    request: ResolveTicketRequest,
) -> dict:
    """
    Mark a ticket as resolved.
    """
    ticket = get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found",
        )
    
    ticket.status = TicketStatus.RESOLVED
    ticket.resolved_at = datetime.now(timezone.utc)
    ticket.session_active = False
    
    logger.info(f"Ticket {ticket_id} resolved: {request.resolution_notes}")
    
    return {
        "success": True,
        "ticket_id": ticket_id,
        "status": ticket.status.value,
        "resolved_at": ticket.resolved_at.isoformat(),
    }


# -----------------------------------------------------------------------------
# Session Management
# -----------------------------------------------------------------------------

_session_to_ticket: Dict[UUID, UUID] = {}


@router.get(
    "/session/{session_id}",
    summary="Get session info",
)
async def get_session_info(session_id: UUID) -> dict:
    """Get session information for a live chat."""
    ticket_id = _session_to_ticket.get(session_id)
    if not ticket_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    ticket = get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )
    
    return {
        "session_id": session_id,
        "ticket_id": ticket_id,
        "interaction_id": ticket.interaction_id,
        "customer_name": ticket.customer_name,
        "issue_summary": ticket.issue_summary,
        "agent_name": ticket.assigned_agent_name,
        "active": ticket.session_active,
    }


# -----------------------------------------------------------------------------
# Ticket Creation (called by orchestrator on escalation)
# -----------------------------------------------------------------------------

def create_ticket_from_escalation(
    interaction_id: UUID,
    escalation_reason: str,
    issue_summary: str,
    priority: TicketPriority = TicketPriority.MEDIUM,
    customer_id: Optional[str] = None,
    customer_name: Optional[str] = None,
    detected_intent: Optional[str] = None,
    detected_emotion: Optional[str] = None,
    ai_attempts: int = 0,
    last_customer_message: Optional[str] = None,
) -> Ticket:
    """
    Create a new ticket when a call is escalated.
    
    Called by the orchestrator when escalation is triggered.
    """
    ticket = Ticket(
        interaction_id=interaction_id,
        escalation_reason=escalation_reason,
        issue_summary=issue_summary,
        priority=priority,
        customer_id=customer_id,
        customer_name=customer_name or f"Customer-{str(interaction_id)[:8]}",
        detected_intent=detected_intent,
        detected_emotion=detected_emotion,
        ai_attempts=ai_attempts,
        last_customer_message=last_customer_message,
    )
    
    _tickets[ticket.ticket_id] = ticket
    logger.info(f"Created ticket {ticket.ticket_id} for interaction {interaction_id}")
    
    return ticket


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def _generate_suggested_actions(ticket: Ticket, messages: list, decisions: list) -> List[str]:
    """Generate suggested actions based on context."""
    actions = []
    
    # Based on intent
    if ticket.detected_intent:
        intent = ticket.detected_intent.lower()
        if "billing" in intent:
            actions.append("Review customer's billing history")
            actions.append("Check for any pending refunds or credits")
        elif "technical" in intent:
            actions.append("Check recent support tickets")
            actions.append("Review account configuration")
        elif "cancel" in intent:
            actions.append("Review retention offers")
            actions.append("Check customer tenure and value")
        elif "complaint" in intent:
            actions.append("Acknowledge customer frustration")
            actions.append("Offer compensation if appropriate")
    
    # Based on emotion
    if ticket.detected_emotion:
        emotion = ticket.detected_emotion.lower()
        if emotion in ["angry", "frustrated"]:
            actions.insert(0, "Start with empathy and acknowledgment")
            actions.append("Consider supervisor involvement if needed")
    
    # Based on AI attempts
    if ticket.ai_attempts > 2:
        actions.append("AI made multiple attempts - review conversation for context")
    
    # Default actions
    if not actions:
        actions = [
            "Review conversation history",
            "Introduce yourself and acknowledge the wait",
            "Confirm the customer's issue",
        ]
    
    return actions[:5]  # Max 5 suggestions


# -----------------------------------------------------------------------------
# Live Session Management
# -----------------------------------------------------------------------------

# In-memory session storage
_sessions: Dict[str, dict] = {}


class SessionMessage(BaseModel):
    """A message in a live session."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: str  # "customer" | "agent" | "system"
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_human: bool = True


class SendMessageRequest(BaseModel):
    """Request to send a message in a session."""
    role: str
    content: str


class SessionStatus(BaseModel):
    """Status of a live session."""
    session_id: str
    is_active: bool
    agent_connected: bool
    agent_name: Optional[str]
    customer_connected: bool
    message_count: int


class SessionMessagesResponse(BaseModel):
    """Response with session messages."""
    messages: List[dict]


@router.get(
    "/session/{session_id}/status",
    response_model=SessionStatus,
    summary="Get session status",
)
async def get_session_status(session_id: str) -> SessionStatus:
    """Get the current status of a live session."""
    session = _sessions.get(session_id, {})
    
    return SessionStatus(
        session_id=session_id,
        is_active=session.get("is_active", False),
        agent_connected=session.get("agent_connected", False),
        agent_name=session.get("agent_name"),
        customer_connected=session.get("customer_connected", True),
        message_count=len(session.get("messages", [])),
    )


@router.get(
    "/session/{session_id}/messages",
    response_model=SessionMessagesResponse,
    summary="Get session messages",
)
async def get_session_messages(session_id: str) -> SessionMessagesResponse:
    """Get all messages in a live session."""
    session = _sessions.get(session_id, {})
    messages = session.get("messages", [])
    
    return SessionMessagesResponse(messages=messages)


@router.post(
    "/session/{session_id}/message",
    summary="Send a message in session",
)
async def send_session_message(session_id: str, request: SendMessageRequest):
    """Send a message in a live session."""
    if session_id not in _sessions:
        _sessions[session_id] = {
            "is_active": True,
            "agent_connected": False,
            "customer_connected": True,
            "messages": [],
        }
    
    message = {
        "id": str(uuid4()),
        "role": request.role,
        "content": request.content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "is_human": True,
    }
    
    _sessions[session_id]["messages"].append(message)
    
    return {"success": True, "message_id": message["id"]}


@router.post(
    "/session/{session_id}/agent-join",
    summary="Agent joins session",
)
async def agent_join_session(session_id: str, agent_name: str = "Human Agent"):
    """Mark that an agent has joined the session."""
    if session_id not in _sessions:
        _sessions[session_id] = {
            "is_active": True,
            "agent_connected": False,
            "customer_connected": True,
            "messages": [],
        }
    
    _sessions[session_id]["agent_connected"] = True
    _sessions[session_id]["agent_name"] = agent_name
    
    # Add system message
    system_message = {
        "id": str(uuid4()),
        "role": "system",
        "content": f"{agent_name} has joined the chat.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "is_human": False,
    }
    _sessions[session_id]["messages"].append(system_message)
    
    return {"success": True, "message": f"Agent {agent_name} joined session"}


@router.post(
    "/session/{session_id}/end",
    summary="End session",
)
async def end_session(session_id: str, resolution: str = "resolved"):
    """End a live session."""
    if session_id in _sessions:
        _sessions[session_id]["is_active"] = False
        
        # Add system message
        system_message = {
            "id": str(uuid4()),
            "role": "system",
            "content": f"Session ended. Resolution: {resolution}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "is_human": False,
        }
        _sessions[session_id]["messages"].append(system_message)
    
    return {"success": True, "message": "Session ended"}
