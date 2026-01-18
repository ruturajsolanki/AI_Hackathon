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

router = APIRouter()

# Register sub-routers
router.include_router(interactions_router)
router.include_router(analytics_router)
router.include_router(history_router)
router.include_router(agents_router)
router.include_router(config_router)


@router.get("/", tags=["API"])
async def api_root():
    """API root endpoint."""
    return {"message": "AI Call Center API", "status": "operational"}
