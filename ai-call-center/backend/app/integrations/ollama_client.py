"""
Ollama LLM Client

Local LLM client using Ollama. Runs models locally with no API quotas.
Supports models like llama3.2, mistral, phi-3, qwen2.5, etc.

Prerequisites:
1. Install Ollama: https://ollama.ai/download
2. Pull a model: ollama pull llama3.2
3. Start Ollama: ollama serve (runs on localhost:11434)
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type
from uuid import uuid4

import httpx
from pydantic import BaseModel

from app.core.llm import (
    CompletionRequest,
    CompletionResponse,
    CompletionStatus,
    GenerationConfig,
    LLMClient,
    StructuredCompletionResponse,
    TokenUsage,
)

logger = logging.getLogger(__name__)

# Default Ollama base URL (local) - can be overridden via environment variable
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


class OllamaConfig(BaseModel):
    """Configuration for Ollama client."""
    
    # Base URL for Ollama API - can be remote!
    # Examples:
    #   - http://localhost:11434 (local)
    #   - http://192.168.1.100:11434 (LAN)
    #   - http://my-ollama-server.com:11434 (remote)
    base_url: str = OLLAMA_BASE_URL
    
    # Default model to use
    # Recommended: llama3.2 (3B, fast), mistral (7B, good quality)
    default_model: str = "llama3.2"
    
    # Timeout for requests in seconds
    timeout_seconds: float = 120.0  # Remote/slow models may need more time
    
    # Max retries
    max_retries: int = 2
    
    @classmethod
    def from_env(cls) -> "OllamaConfig":
        """Load configuration from environment variables."""
        return cls(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            default_model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            timeout_seconds=float(os.getenv("OLLAMA_TIMEOUT", "120")),
        )


class OllamaClient(LLMClient):
    """
    Local LLM client using Ollama.
    
    Benefits:
    - No API quotas or rate limits
    - Complete privacy (runs locally)
    - Free to use
    - Works offline
    
    Requirements:
    - Ollama installed and running
    - At least one model pulled
    """
    
    # Common models that work well
    SUPPORTED_MODELS = [
        "llama3.2",           # 3B, fast and capable
        "llama3.2:1b",        # 1B, very fast
        "mistral",            # 7B, high quality
        "phi3",               # 3.8B, Microsoft's small model
        "qwen2.5:3b",         # 3B, good for chat
        "gemma2:2b",          # 2B, Google's small model
    ]
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        """Initialize Ollama client."""
        self._config = config or OllamaConfig()
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._config.timeout_seconds)
            )
        return self._http_client
    
    @property
    def provider_name(self) -> str:
        """Return 'ollama' as the provider name."""
        return "ollama"
    
    @property
    def default_model(self) -> str:
        """Return the configured default model."""
        return self._config.default_model
    
    @property
    def supported_models(self) -> List[str]:
        """Return list of common Ollama models."""
        return self.SUPPORTED_MODELS
    
    async def complete(
        self,
        request: CompletionRequest,
        model: Optional[str] = None,
    ) -> CompletionResponse:
        """
        Generate a completion using Ollama's API.
        """
        start_time = datetime.now(timezone.utc)
        model_name = model or self.default_model
        
        # Build messages
        messages = []
        
        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
            })
        
        # Add conversation history
        for msg in request.messages:
            messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        # Add current user prompt
        messages.append({
            "role": "user",
            "content": request.user_prompt
        })
        
        # Build request payload
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": request.config.temperature,
                "num_predict": request.config.max_tokens,
            }
        }
        
        if request.config.top_p is not None:
            payload["options"]["top_p"] = request.config.top_p
        
        if request.config.top_k is not None:
            payload["options"]["top_k"] = request.config.top_k
        
        # Attempt completion
        last_error = None
        for attempt in range(self._config.max_retries):
            try:
                client = await self._get_http_client()
                url = f"{self._config.base_url}/api/chat"
                
                response = await client.post(url, json=payload)
                
                if response.status_code != 200:
                    error_text = response.text
                    raise Exception(f"Ollama error ({response.status_code}): {error_text[:200]}")
                
                data = response.json()
                
                # Calculate latency
                end_time = datetime.now(timezone.utc)
                latency_ms = int((end_time - start_time).total_seconds() * 1000)
                
                # Extract content
                content = data.get("message", {}).get("content", "")
                
                # Extract usage stats
                prompt_tokens = data.get("prompt_eval_count", 0)
                completion_tokens = data.get("eval_count", 0)
                
                return CompletionResponse(
                    response_id=str(uuid4()),
                    request_id=request.request_id,
                    status=CompletionStatus.SUCCESS,
                    content=content,
                    model=model_name,
                    provider="ollama",
                    usage=TokenUsage(
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=prompt_tokens + completion_tokens,
                    ),
                    latency_ms=latency_ms,
                    timestamp=end_time,
                )
                
            except httpx.ConnectError as e:
                last_error = f"Cannot connect to Ollama. Is it running? (ollama serve) - {str(e)}"
                logger.warning(f"Ollama connection failed (attempt {attempt + 1}): {last_error}")
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Ollama request failed (attempt {attempt + 1}): {last_error}")
        
        # All retries failed
        return CompletionResponse(
            response_id=str(uuid4()),
            request_id=request.request_id,
            status=CompletionStatus.ERROR,
            content=None,
            model=model_name,
            provider="ollama",
            usage=TokenUsage(),
            latency_ms=0,
            timestamp=datetime.now(timezone.utc),
            error_message=last_error,
            error_code="OLLAMA_ERROR",
        )
    
    async def complete_structured(
        self,
        request: CompletionRequest,
        output_type: Type[BaseModel],
        model: Optional[str] = None,
    ) -> StructuredCompletionResponse:
        """
        Generate a structured completion.
        """
        # Add JSON format instruction to system prompt
        json_instruction = f"\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no explanation."
        
        modified_request = CompletionRequest(
            user_prompt=request.user_prompt,
            system_prompt=(request.system_prompt or "") + json_instruction,
            messages=request.messages,
            config=request.config,
            request_id=request.request_id,
        )
        
        base_response = await self.complete(modified_request, model)
        
        # Attempt to parse structured output
        parsed_output = None
        if base_response.is_success and base_response.content:
            try:
                from app.core.json_utils import extract_json_from_llm_response
                json_data = extract_json_from_llm_response(base_response.content)
                if json_data:
                    parsed_output = output_type.model_validate(json_data)
            except Exception as e:
                logger.debug(f"Failed to parse Ollama structured output: {e}")
        
        return StructuredCompletionResponse(
            response_id=base_response.response_id,
            request_id=base_response.request_id,
            status=base_response.status,
            content=base_response.content,
            structured_output=base_response.structured_output,
            model=base_response.model,
            provider=base_response.provider,
            usage=base_response.usage,
            latency_ms=base_response.latency_ms,
            timestamp=base_response.timestamp,
            error_message=base_response.error_message,
            error_code=base_response.error_code,
            parsed_output=parsed_output,
        )
    
    async def health_check(self) -> bool:
        """
        Check if Ollama is running and accessible.
        """
        try:
            client = await self._get_http_client()
            response = await client.get(f"{self._config.base_url}/api/tags")
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                if models:
                    logger.info(f"Ollama available with {len(models)} models")
                    return True
                else:
                    logger.warning("Ollama running but no models installed. Run: ollama pull llama3.2")
                    return False
            return False
            
        except httpx.ConnectError:
            logger.warning("Ollama not running. Start with: ollama serve")
            return False
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Rough estimate: ~4 chars per token
        return len(text) // 4
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List locally available Ollama models."""
        try:
            client = await self._get_http_client()
            response = await client.get(f"{self._config.base_url}/api/tags")
            
            if response.status_code == 200:
                data = response.json()
                models = []
                for model_info in data.get("models", []):
                    name = model_info.get("name", "")
                    # Remove tag if present
                    model_id = name.split(":")[0] if ":" in name else name
                    
                    models.append({
                        "id": name,
                        "name": model_info.get("name", name),
                        "description": f"Local model - {model_info.get('size', 'unknown size')}",
                        "supports_chat": True,
                    })
                return models
            return []
            
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
