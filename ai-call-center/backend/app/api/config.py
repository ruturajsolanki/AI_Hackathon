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
from enum import Enum
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Provider Enum
# -----------------------------------------------------------------------------

class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    GEMINI = "gemini"
    OLLAMA = "ollama"  # Local LLM - no API key needed


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
            cls._instance._api_key: Optional[str] = None
            cls._instance._provider: LLMProvider = LLMProvider.OPENAI
            cls._instance._ollama_url: str = "http://localhost:11434"  # Ollama server URL
            cls._instance._key_configured_at: Optional[datetime] = None
            cls._instance._last_validation: Optional[datetime] = None
            cls._instance._is_valid: Optional[bool] = None
        return cls._instance
    
    def set_api_key(self, key: str, provider: LLMProvider = LLMProvider.OPENAI) -> None:
        """
        Set the LLM API key (or Ollama URL for local provider).
        
        The key is stored in-memory only.
        A hash is logged for audit purposes (never the actual key).
        """
        self._provider = provider
        self._key_configured_at = datetime.now(timezone.utc)
        self._is_valid = None  # Reset validation status
        
        # For Ollama, the "key" is actually the server URL
        if provider == LLMProvider.OLLAMA:
            self._ollama_url = key if key.startswith("http") else "http://localhost:11434"
            self._api_key = "ollama-local"  # Placeholder
            logger.info(f"Ollama configured with URL: {self._ollama_url}")
        else:
            self._api_key = key
            # Log key configuration (hash only, never the key)
            key_hash = hashlib.sha256(key.encode()).hexdigest()[:8]
            logger.info(f"LLM API key configured for {provider.value} (hash prefix: {key_hash}...)")
    
    def get_ollama_url(self) -> str:
        """Get the Ollama server URL."""
        return self._ollama_url
    
    def get_api_key(self) -> Optional[str]:
        """Get the LLM API key if configured."""
        return self._api_key
    
    def get_provider(self) -> LLMProvider:
        """Get the current LLM provider."""
        return self._provider
    
    def clear_api_key(self) -> None:
        """Clear the stored API key."""
        self._api_key = None
        self._key_configured_at = None
        self._is_valid = None
        logger.info("LLM API key cleared")
    
    def is_configured(self) -> bool:
        """Check if an API key is configured."""
        return self._api_key is not None and len(self._api_key) > 0
    
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
    
    # Backwards compatibility
    def set_openai_key(self, key: str) -> None:
        """Alias for set_api_key with OpenAI provider."""
        self.set_api_key(key, LLMProvider.OPENAI)
    
    def get_openai_key(self) -> Optional[str]:
        """Get API key if provider is OpenAI."""
        if self._provider == LLMProvider.OPENAI:
            return self._api_key
        return None
    
    def clear_openai_key(self) -> None:
        """Alias for clear_api_key."""
        self.clear_api_key()


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
        description="The LLM provider API key"
    )
    provider: str = Field(
        default="openai",
        description="LLM provider name (openai or gemini)"
    )
    
    @field_validator("api_key")
    @classmethod
    def validate_key_format(cls, v: str) -> str:
        """Basic validation of API key format."""
        v = v.strip()
        if len(v) < 10:
            raise ValueError("API key is too short")
        return v
    
    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider name."""
        v = v.lower().strip()
        if v not in ["openai", "gemini"]:
            raise ValueError("Provider must be 'openai' or 'gemini'")
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
    available_providers: list[str] = Field(
        default=["openai", "gemini"],
        description="List of supported LLM providers"
    )


class SetApiKeyResponse(BaseModel):
    """Response after setting API key."""
    
    success: bool
    message: str
    configured_at: str
    provider: str


class ValidationResponse(BaseModel):
    """Response from key validation."""
    
    valid: bool
    message: str
    tested_at: str
    provider: str


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
    
    Supported providers:
    - **openai**: OpenAI API (GPT-4, GPT-4o, etc.)
    - **gemini**: Google Gemini API (Gemini Pro, Gemini Flash, etc.)
    
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
        provider = LLMProvider.GEMINI if request.provider == "gemini" else LLMProvider.OPENAI
        config.set_api_key(request.api_key, provider)
        
        return SetApiKeyResponse(
            success=True,
            message=f"API key configured for {request.provider}",
            configured_at=config.get_configured_at().isoformat() if config.get_configured_at() else "",
            provider=request.provider,
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
    provider = config.get_provider().value
    
    if not is_configured:
        message = "No API key configured. Add your OpenAI or Gemini API key to enable AI features."
    elif is_valid is None:
        message = f"API key configured for {provider} but not yet validated. Send a test message to validate."
    elif is_valid:
        message = f"API key for {provider} configured and validated successfully."
    else:
        message = f"API key for {provider} configured but validation failed. Please check your key."
    
    return ApiKeyStatusResponse(
        configured=is_configured,
        provider=provider,
        configured_at=configured_at.isoformat() if configured_at else None,
        validated=is_valid,
        last_validated_at=last_validated.isoformat() if last_validated else None,
        message=message,
        available_providers=["openai", "gemini"],
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
    
    provider = config.get_provider()
    
    try:
        if provider == LLMProvider.GEMINI:
            # Use Gemini client
            from app.integrations.gemini_client import GeminiClient, GeminiConfig
            
            client_config = GeminiConfig(api_key=config.get_api_key())
            client = GeminiClient(client_config)
        else:
            # Use OpenAI client
            from app.integrations.openai_client import OpenAIClient, OpenAIConfig
            
            client_config = OpenAIConfig(api_key=config.get_api_key())
            client = OpenAIClient(client_config)
        
        # Test with health check
        is_valid = await client.health_check()
        
        config.set_validation_status(is_valid)
        
        return ValidationResponse(
            valid=is_valid,
            message=f"API key for {provider.value} is valid and working" if is_valid else f"API key validation failed for {provider.value}",
            tested_at=datetime.now(timezone.utc).isoformat(),
            provider=provider.value,
        )
        
    except Exception as e:
        logger.error(f"API key validation failed: {type(e).__name__}: {str(e)}")
        config.set_validation_status(False)
        
        return ValidationResponse(
            valid=False,
            message=f"Validation failed: {str(e)}",
            tested_at=datetime.now(timezone.utc).isoformat(),
            provider=provider.value,
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
    config.clear_api_key()


# -----------------------------------------------------------------------------
# Model Listing
# -----------------------------------------------------------------------------

class ModelInfo(BaseModel):
    """Information about an available model."""
    id: str = Field(description="Model identifier to use in API calls")
    name: str = Field(description="Human-readable model name")
    description: str = Field(default="", description="Model description")
    supports_chat: bool = Field(default=True, description="Whether model supports chat/generateContent")


class ModelsListResponse(BaseModel):
    """Response with list of available models."""
    provider: str
    models: list[ModelInfo]
    default_model: str


@router.get(
    "/llm/models",
    response_model=ModelsListResponse,
    summary="List Available Models",
    description="Fetch available models from the configured LLM provider.",
)
async def list_available_models() -> ModelsListResponse:
    """
    List all available models from the configured LLM provider.
    
    Fetches models dynamically from OpenAI, Gemini, or local Ollama.
    """
    config = get_runtime_config()
    provider = config.get_provider()
    
    # Ollama doesn't need an API key
    if provider == LLMProvider.OLLAMA:
        return await _list_ollama_models()
    
    if not config.is_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No API key configured. Set a key first.",
        )
    
    api_key = config.get_api_key()
    
    try:
        if provider == LLMProvider.GEMINI:
            return await _list_gemini_models(api_key)
        else:
            return await _list_openai_models(api_key)
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch models: {str(e)}",
        )


async def _list_gemini_models(api_key: str) -> ModelsListResponse:
    """Fetch available models from Gemini API."""
    import httpx
    
    url = "https://generativelanguage.googleapis.com/v1beta/models"
    params = {"key": api_key}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
        
        if response.status_code != 200:
            raise Exception(f"Gemini API error: {response.status_code}")
        
        data = response.json()
        models = []
        
        for model in data.get("models", []):
            model_name = model.get("name", "")
            # Filter to only show models that support generateContent
            supported_methods = model.get("supportedGenerationMethods", [])
            if "generateContent" not in supported_methods:
                continue
            
            # Extract just the model ID (e.g., "gemini-2.0-flash" from "models/gemini-2.0-flash")
            model_id = model_name.replace("models/", "")
            
            # Skip embedding models and other non-chat models
            if "embedding" in model_id.lower() or "aqa" in model_id.lower():
                continue
            
            models.append(ModelInfo(
                id=model_id,
                name=model.get("displayName", model_id),
                description=model.get("description", "")[:100] if model.get("description") else "",
                supports_chat=True,
            ))
        
        # Sort by name, putting newer versions first
        models.sort(key=lambda m: (
            "2.5" not in m.id,  # 2.5 first
            "2.0" not in m.id,  # then 2.0
            "1.5" not in m.id,  # then 1.5
            "flash" not in m.id.lower(),  # flash before pro
            m.id
        ))
        
        return ModelsListResponse(
            provider="gemini",
            models=models[:15],  # Limit to top 15
            default_model="gemini-2.5-flash",
        )


async def _list_openai_models(api_key: str) -> ModelsListResponse:
    """Fetch available models from OpenAI API."""
    import httpx
    
    url = "https://api.openai.com/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.status_code}")
        
        data = response.json()
        models = []
        
        # Filter to only chat models
        chat_model_prefixes = ["gpt-4", "gpt-3.5", "o1", "o3"]
        
        for model in data.get("data", []):
            model_id = model.get("id", "")
            
            # Only include chat-capable models
            if not any(model_id.startswith(prefix) for prefix in chat_model_prefixes):
                continue
            
            # Skip fine-tuned, instruct variants, vision-only, etc.
            if any(x in model_id for x in ["-instruct", "vision-preview", "realtime", "audio"]):
                continue
            
            # Create friendly name
            name = model_id
            if "gpt-4o-mini" in model_id:
                name = "GPT-4o Mini (Fast & Affordable)"
            elif "gpt-4o" in model_id and "mini" not in model_id:
                name = "GPT-4o (Most Capable)"
            elif "gpt-4-turbo" in model_id:
                name = "GPT-4 Turbo"
            elif "gpt-4" in model_id:
                name = "GPT-4"
            elif "gpt-3.5-turbo" in model_id:
                name = "GPT-3.5 Turbo"
            elif "o1" in model_id:
                name = f"O1 ({model_id})"
            elif "o3" in model_id:
                name = f"O3 ({model_id})"
            
            models.append(ModelInfo(
                id=model_id,
                name=name,
                description="",
                supports_chat=True,
            ))
        
        # Sort by capability (gpt-4o first, then gpt-4, then gpt-3.5)
        def model_sort_key(m):
            if "gpt-4o-mini" in m.id:
                return (1, m.id)
            if "gpt-4o" in m.id:
                return (0, m.id)
            if "gpt-4-turbo" in m.id:
                return (2, m.id)
            if "gpt-4" in m.id:
                return (3, m.id)
            if "o1" in m.id or "o3" in m.id:
                return (4, m.id)
            return (5, m.id)
        
        models.sort(key=model_sort_key)
        
        # Remove duplicates (keep first occurrence)
        seen = set()
        unique_models = []
        for m in models:
            if m.id not in seen:
                seen.add(m.id)
                unique_models.append(m)
        
        return ModelsListResponse(
            provider="openai",
            models=unique_models[:15],  # Limit to top 15
            default_model="gpt-4o-mini",
        )


async def _list_ollama_models() -> ModelsListResponse:
    """Fetch available models from Ollama installation (local or remote)."""
    import httpx
    
    # Get configured Ollama URL
    config = get_runtime_config()
    base_url = config.get_ollama_url()
    url = f"{base_url}/api/tags"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            
            if response.status_code != 200:
                raise Exception(f"Ollama not responding: {response.status_code}")
            
            data = response.json()
            models = []
            
            for model in data.get("models", []):
                model_name = model.get("name", "")
                size_bytes = model.get("size", 0)
                
                # Format size for display
                size_gb = size_bytes / (1024 ** 3)
                size_str = f"{size_gb:.1f}GB" if size_gb >= 1 else f"{size_bytes / (1024**2):.0f}MB"
                
                models.append(ModelInfo(
                    id=model_name,
                    name=model_name,
                    description=f"Local model - {size_str}",
                    supports_chat=True,
                ))
            
            if not models:
                # Return suggestion to install models
                return ModelsListResponse(
                    provider="ollama",
                    models=[
                        ModelInfo(
                            id="llama3.2",
                            name="llama3.2 (not installed)",
                            description="Run: ollama pull llama3.2",
                            supports_chat=True,
                        )
                    ],
                    default_model="llama3.2",
                )
            
            return ModelsListResponse(
                provider="ollama",
                models=models,
                default_model=models[0].id if models else "llama3.2",
            )
            
    except httpx.ConnectError:
        raise Exception("Ollama not running. Start with: ollama serve")
    except Exception as e:
        raise Exception(f"Failed to connect to Ollama: {str(e)}")
