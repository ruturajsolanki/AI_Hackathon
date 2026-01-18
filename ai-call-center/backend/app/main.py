"""
AI-Powered Digital Call Center - Application Entry Point

This module initializes the FastAPI application, registers routers,
and configures middleware. It contains no business logic.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as api_router
from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    app.state.started_at = datetime.now(timezone.utc)
    
    # Try to connect to MongoDB (optional, falls back gracefully)
    try:
        from app.persistence.mongodb import get_mongodb_store
        mongodb = get_mongodb_store()
        connected = await mongodb.connect()
        app.state.mongodb_connected = connected
        if connected:
            logger.info("MongoDB connected successfully")
        else:
            logger.warning("MongoDB not available, using SQLite fallback")
    except Exception as e:
        logger.warning(f"MongoDB initialization failed: {e}, using SQLite fallback")
        app.state.mongodb_connected = False
    
    yield
    
    # Shutdown
    try:
        from app.persistence.mongodb import get_mongodb_store
        mongodb = get_mongodb_store()
        await mongodb.disconnect()
    except Exception:
        pass


def create_application() -> FastAPI:
    """
    Application factory.
    Creates and configures the FastAPI application instance.
    """
    application = FastAPI(
        title=settings.APP_NAME,
        description="AI-Powered Digital Call Center API",
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # Middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    application.include_router(api_router, prefix="/api")

    return application


app = create_application()


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns service status for load balancers and monitoring.
    """
    mongodb_status = getattr(app.state, 'mongodb_connected', False)
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.APP_VERSION,
        "database": "mongodb" if mongodb_status else "sqlite",
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness check endpoint.
    Indicates whether the service is ready to accept traffic.
    """
    return {
        "ready": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
