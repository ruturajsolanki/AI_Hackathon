"""
API Module

Aggregates all API routers for registration in the main application.
"""

from fastapi import APIRouter

from app.api.interactions import router as interactions_router
from app.api.analytics import router as analytics_router
from app.api.history import router as history_router
from app.api.agents import router as agents_router
from app.api.config import router as config_router
from app.api.agent_config import router as agent_config_router
from app.api.auth import router as auth_router
from app.api.tickets import router as tickets_router

# Create session router to expose session endpoints at /api/session
from app.api.tickets import (
    get_session_status,
    get_session_messages,
    send_session_message,
    agent_join_session,
    end_session,
)

session_router = APIRouter(prefix="/session", tags=["Live Sessions"])
session_router.add_api_route("/{session_id}/status", get_session_status, methods=["GET"])
session_router.add_api_route("/{session_id}/messages", get_session_messages, methods=["GET"])
session_router.add_api_route("/{session_id}/message", send_session_message, methods=["POST"])
session_router.add_api_route("/{session_id}/agent-join", agent_join_session, methods=["POST"])
session_router.add_api_route("/{session_id}/end", end_session, methods=["POST"])

router = APIRouter()

# Register sub-routers
router.include_router(auth_router)  # Auth first for login endpoint
router.include_router(interactions_router)
router.include_router(analytics_router)
router.include_router(history_router)
router.include_router(agents_router)
router.include_router(config_router)
router.include_router(agent_config_router)
router.include_router(tickets_router)
router.include_router(session_router)  # Live session endpoints


@router.get("/", tags=["API"])
async def api_root():
    """API root endpoint."""
    return {"message": "AI Call Center API", "status": "operational"}
