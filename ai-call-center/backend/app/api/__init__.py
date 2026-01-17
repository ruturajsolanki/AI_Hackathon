"""
API Module

Aggregates all API routers for registration in the main application.
"""

from fastapi import APIRouter

from app.api.interactions import router as interactions_router

router = APIRouter()

# Register sub-routers
router.include_router(interactions_router)


@router.get("/", tags=["API"])
async def api_root():
    """API root endpoint."""
    return {"message": "AI Call Center API", "status": "operational"}
