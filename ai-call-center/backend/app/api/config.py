"""
Configuration API Endpoints

Provides secure runtime configuration for the AI Call Center.
Handles LLM API key management and connection status.

Security Notes:
- API keys are stored in-memory only (not persisted)
- Keys are never logged or returned in responses
- Only key presence/validity status is exposed
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# In-Memory Configuration Store
# -----------------------------------------------------------------------------

class RuntimeConfig:
    """
    In-memory runtime configuration store.
    
    IMPORTANT: This is intentionally in-memory only.
    API keys are never persisted to disk or database.
    
    For production, consider:
    - Encrypted vault storage (HashiCorp Vault, AWS Secrets Manager)
    - Per-request key passing via secure headers
    - OAuth2 token-based LLM access
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._openai_key: Optional[str] = None
            cls._instance._key_configured_at: Optional[datetime] = None
            cls._instance._last_validation: Optional[datetime] = None
            cls._instance._is_valid: Optional[bool] = None
        return cls._instance
    
    def set_openai_key(self, key: str) -> None:
        """
        Set the OpenAI API key.
        
        The key is stored in-memory only.
        A hash is logged for audit purposes (never the actual key).
        """
        self._openai_key = key
        self._key_configured_at = datetime.now(timezone.utc)
        self._is_valid = None  # Reset validation status
        
        # Log key configuration (hash only, never the key)
        key_hash = hashlib.sha256(key.encode()).hexdigest()[:8]
        logger.info(f"LLM API key configured (hash prefix: {key_hash}...)")
    
    def get_openai_key(self) -> Optional[str]:
        """Get the OpenAI API key if configured."""
        return self._openai_key
    
    def clear_openai_key(self) -> None:
        """Clear the stored API key."""
        self._openai_key = None
        self._key_configured_at = None
        self._is_valid = None
        logger.info("LLM API key cleared")
    
    def is_configured(self) -> bool:
        """Check if an API key is configured."""
        return self._openai_key is not None and len(self._openai_key) > 0
    
    def get_configured_at(self) -> Optional[datetime]:
        """Get when the key was configured."""
        return self._key_configured_at
    
    def set_validation_status(self, is_valid: bool) -> None:
        """Set the validation status after testing the key."""
        self._is_valid = is_valid
        self._last_validation = datetime.now(timezone.utc)
    
    def get_validation_status(self) -> tuple[Optional[bool], Optional[datetime]]:
        """Get validation status and when it was last checked."""
        return self._is_valid, self._last_validation


def get_runtime_config() -> RuntimeConfig:
    """Get the runtime configuration singleton."""
    return RuntimeConfig()


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------

class SetApiKeyRequest(BaseModel):
    """Request to set the LLM API key."""
    
    api_key: str = Field(
        ...,
        min_length=10,
        description="The LLM provider API key (e.g., OpenAI API key)"
    )
    provider: str = Field(
        default="openai",
        description="LLM provider name"
    )
    
    @field_validator("api_key")
    @classmethod
    def validate_key_format(cls, v: str) -> str:
        """Basic validation of API key format."""
        v = v.strip()
        if len(v) < 10:
            raise ValueError("API key is too short")
        # OpenAI keys typically start with "sk-"
        # But we don't enforce this to allow other providers
        return v


class ApiKeyStatusResponse(BaseModel):
    """Response with API key status (never includes the actual key)."""
    
    configured: bool = Field(description="Whether an API key is configured")
    provider: str = Field(default="openai", description="LLM provider")
    configured_at: Optional[str] = Field(
        default=None, 
        description="When the key was configured (ISO format)"
    )
    validated: Optional[bool] = Field(
        default=None,
        description="Whether the key has been validated"
    )
    last_validated_at: Optional[str] = Field(
        default=None,
        description="When the key was last validated"
    )
    message: str = Field(description="Human-readable status message")


class SetApiKeyResponse(BaseModel):
    """Response after setting API key."""
    
    success: bool
    message: str
    configured_at: str


class ValidationResponse(BaseModel):
    """Response from key validation."""
    
    valid: bool
    message: str
    tested_at: str


# -----------------------------------------------------------------------------
# Router
# -----------------------------------------------------------------------------

router = APIRouter(prefix="/config", tags=["Configuration"])


@router.post(
    "/llm",
    response_model=SetApiKeyResponse,
    status_code=status.HTTP_200_OK,
    summary="Set LLM API Key",
    description="""
    Configure the LLM API key at runtime.
    
    **Security Notes:**
    - The key is stored in-memory only (not persisted to disk)
    - The key is never logged or returned in responses
    - Only the configuration status is exposed
    
    For production deployments, use environment variables or a secrets manager instead.
    """,
)
async def set_llm_api_key(request: SetApiKeyRequest) -> SetApiKeyResponse:
    """
    Set the LLM API key for AI operations.
    
    This endpoint accepts an API key and stores it in-memory.
    The key is used by agents for LLM-powered operations.
    """
    config = get_runtime_config()
    
    try:
        config.set_openai_key(request.api_key)
        
        return SetApiKeyResponse(
            success=True,
            message=f"API key configured for {request.provider}",
            configured_at=config.get_configured_at().isoformat() if config.get_configured_at() else "",
        )
    except Exception as e:
        logger.error(f"Failed to set API key: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to configure API key",
        )


@router.get(
    "/llm/status",
    response_model=ApiKeyStatusResponse,
    summary="Get LLM Configuration Status",
    description="Check if an LLM API key is configured and its validation status.",
)
async def get_llm_status() -> ApiKeyStatusResponse:
    """
    Get the current LLM configuration status.
    
    Returns whether a key is configured and validated,
    but never returns the actual key.
    """
    config = get_runtime_config()
    
    is_configured = config.is_configured()
    configured_at = config.get_configured_at()
    is_valid, last_validated = config.get_validation_status()
    
    if not is_configured:
        message = "No API key configured. Add your OpenAI API key to enable AI features."
    elif is_valid is None:
        message = "API key configured but not yet validated. Send a test message to validate."
    elif is_valid:
        message = "API key configured and validated successfully."
    else:
        message = "API key configured but validation failed. Please check your key."
    
    return ApiKeyStatusResponse(
        configured=is_configured,
        provider="openai",
        configured_at=configured_at.isoformat() if configured_at else None,
        validated=is_valid,
        last_validated_at=last_validated.isoformat() if last_validated else None,
        message=message,
    )


@router.post(
    "/llm/validate",
    response_model=ValidationResponse,
    summary="Validate LLM API Key",
    description="Test the configured API key by making a minimal API call.",
)
async def validate_llm_key() -> ValidationResponse:
    """
    Validate the configured LLM API key.
    
    Makes a minimal API call to verify the key works.
    """
    config = get_runtime_config()
    
    if not config.is_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No API key configured. Set a key first.",
        )
    
    try:
        # Import here to avoid circular imports
        from app.integrations.openai_client import OpenAIClient, OpenAIConfig
        
        # Create client with runtime key
        client_config = OpenAIConfig(api_key=config.get_openai_key())
        client = OpenAIClient(client_config)
        
        # Test with health check
        is_valid = await client.health_check()
        
        config.set_validation_status(is_valid)
        
        return ValidationResponse(
            valid=is_valid,
            message="API key is valid and working" if is_valid else "API key validation failed",
            tested_at=datetime.now(timezone.utc).isoformat(),
        )
        
    except Exception as e:
        logger.error(f"API key validation failed: {type(e).__name__}")
        config.set_validation_status(False)
        
        return ValidationResponse(
            valid=False,
            message=f"Validation failed: {str(e)}",
            tested_at=datetime.now(timezone.utc).isoformat(),
        )


@router.delete(
    "/llm",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear LLM API Key",
    description="Remove the configured API key from memory.",
)
async def clear_llm_key() -> None:
    """
    Clear the configured LLM API key.
    
    This removes the key from memory. AI features will use
    fallback logic until a new key is configured.
    """
    config = get_runtime_config()
    config.clear_openai_key()
