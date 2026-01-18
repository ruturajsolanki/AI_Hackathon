"""
Google Gemini LLM Client

Concrete implementation of LLMClient for Google's Gemini API.
Uses REST API directly for Python 3.9 compatibility.
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypeVar

import httpx
from pydantic import BaseModel

from app.core.llm import (
    CompletionRequest,
    CompletionResponse,
    CompletionStatus,
    GenerationConfig,
    LLMClient,
    ResponseFormat,
    StructuredCompletionRequest,
    StructuredCompletionResponse,
    TokenUsage,
)

T = TypeVar('T', bound=BaseModel)

# Gemini API base URL - use v1 for stable API
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiConfig(BaseModel):
    """Configuration for Gemini client."""
    
    api_key: Optional[str] = None
    # Use gemini-2.5-flash for best free tier compatibility
    default_model: str = "gemini-2.5-flash"
    timeout_seconds: float = 60.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0

    @classmethod
    def from_env(cls) -> "GeminiConfig":
        """
        Load configuration from environment variables.
        
        Environment variables:
        - GEMINI_API_KEY: API key (required)
        - GEMINI_DEFAULT_MODEL: Default model (optional)
        - GEMINI_TIMEOUT: Timeout in seconds (optional)
        - GEMINI_MAX_RETRIES: Max retry attempts (optional)
        """
        return cls(
            api_key=os.getenv("GEMINI_API_KEY"),
            default_model=os.getenv("GEMINI_DEFAULT_MODEL", "gemini-1.5-flash"),
            timeout_seconds=float(os.getenv("GEMINI_TIMEOUT", "60")),
            max_retries=int(os.getenv("GEMINI_MAX_RETRIES", "3")),
        )


class GeminiClient(LLMClient):
    """
    Google Gemini implementation of LLMClient.
    
    Uses the Gemini REST API directly for Python 3.9 compatibility.
    
    Example:
        config = GeminiConfig.from_env()
        client = GeminiClient(config)
        
        response = await client.generate(
            user_prompt="Hello!",
            system_prompt="You are a helpful assistant."
        )
    """

    # Supported models (free tier compatible)
    SUPPORTED_MODELS = [
        "gemini-2.0-flash",        # Latest free tier model
        "gemini-1.5-flash-latest", # Latest 1.5 flash
        "gemini-1.5-pro-latest",   # Latest 1.5 pro
        "gemini-pro",              # Original Gemini Pro
    ]

    def __init__(self, config: Optional[GeminiConfig] = None):
        """
        Initialize the Gemini client.
        
        Args:
            config: Configuration object. If None, loads from environment.
        """
        self._config = config or GeminiConfig.from_env()
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._config.timeout_seconds)
            )
        return self._http_client

    @property
    def provider_name(self) -> str:
        """Return 'gemini' as the provider name."""
        return "gemini"

    @property
    def default_model(self) -> str:
        """Return the configured default model."""
        return self._config.default_model

    @property
    def supported_models(self) -> List[str]:
        """Return list of supported Gemini models."""
        return self.SUPPORTED_MODELS

    async def complete(
        self,
        request: CompletionRequest,
        model: Optional[str] = None,
    ) -> CompletionResponse:
        """
        Generate a completion using Gemini's API.
        
        Args:
            request: The completion request
            model: Optional model override
            
        Returns:
            CompletionResponse with generated content
        """
        start_time = datetime.now(timezone.utc)
        model_name = model or self.default_model
        
        # Build the request payload
        payload = self._build_request_payload(request)
        
        # Attempt completion with retries
        last_error = None
        for attempt in range(self._config.max_retries):
            try:
                response = await self._make_request(model_name, payload)
                
                # Calculate latency
                end_time = datetime.now(timezone.utc)
                latency_ms = int((end_time - start_time).total_seconds() * 1000)
                
                return self._parse_response(
                    request=request,
                    response=response,
                    model=model_name,
                    latency_ms=latency_ms,
                )
                
            except Exception as e:
                last_error = e
                
                # Check if error is retryable
                if not self._is_retryable_error(e):
                    break
                
                # Wait before retry
                if attempt < self._config.max_retries - 1:
                    await asyncio.sleep(
                        self._config.retry_delay_seconds * (attempt + 1)
                    )
        
        # All retries failed
        end_time = datetime.now(timezone.utc)
        latency_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return self._create_error_response(
            request=request,
            error=last_error,
            model=model_name,
            latency_ms=latency_ms,
        )

    async def complete_structured(
        self,
        request: StructuredCompletionRequest[T],
        output_type: type[T],
        model: Optional[str] = None,
    ) -> StructuredCompletionResponse[T]:
        """
        Generate a structured completion with typed output.
        
        Uses JSON mode and attempts to parse the response
        into the specified Pydantic model.
        """
        # Ensure JSON response format
        if request.config.response_format != ResponseFormat.JSON:
            request.config.response_format = ResponseFormat.JSON
        
        # Get base completion
        base_response = await self.complete(request, model)
        
        # Attempt to parse structured output
        parsed_output = None
        if base_response.is_success and base_response.content:
            try:
                # Try to extract JSON from the response
                content = base_response.content
                # Handle markdown code blocks
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                json_data = json.loads(content)
                parsed_output = output_type.model_validate(json_data)
            except (json.JSONDecodeError, ValueError):
                # Parsing failed, but we still return the raw content
                pass
        
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
        Check if the Gemini API is accessible.
        
        Makes a minimal request to verify connectivity.
        Returns True if key is valid (even if rate-limited).
        """
        try:
            client = await self._get_http_client()
            
            # Use a simple generateContent request to verify API access
            url = f"{GEMINI_API_BASE}/models/{self.default_model}:generateContent"
            params = {"key": self._config.api_key}
            payload = {
                "contents": [{"parts": [{"text": "Hi"}]}],
                "generationConfig": {"maxOutputTokens": 5}
            }
            
            response = await client.post(url, params=params, json=payload)
            
            # Check if successful
            if response.status_code == 200:
                return True
            
            # 429 = Rate limited - key is valid but quota exceeded
            # This is still a valid key, just temporarily limited
            if response.status_code == 429:
                print(f"Gemini API key valid but rate-limited (quota exceeded)")
                return True
            
            # 401/403 = Invalid key
            if response.status_code in (401, 403):
                print(f"Gemini API key invalid: {response.status_code}")
                return False
            
            # Log other errors for debugging
            print(f"Gemini health check failed: {response.status_code} - {response.text[:200]}")
            return False
            
        except Exception as e:
            print(f"Gemini health check error: {str(e)}")
            return False

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Gemini uses a different tokenizer, roughly 4 chars per token.
        """
        # Gemini doesn't expose a public tokenizer, use approximation
        return len(text) // 4

    def _build_request_payload(self, request: CompletionRequest) -> Dict[str, Any]:
        """Build the Gemini API request payload."""
        contents = []
        
        # Build messages as conversation
        if request.system_prompt:
            # Add system instruction as first user message context
            contents.append({
                "role": "user",
                "parts": [{"text": f"[System Instructions]\n{request.system_prompt}"}]
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "I understand. I will follow these instructions."}]
            })
        
        # Add conversation history
        for msg in request.messages:
            role = "user" if msg.role.value == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })
        
        # Add current user prompt
        contents.append({
            "role": "user",
            "parts": [{"text": request.user_prompt}]
        })
        
        # Build generation config
        generation_config = {
            "temperature": request.config.temperature,
            "maxOutputTokens": request.config.max_tokens,
            "topP": request.config.top_p,
        }
        
        if request.config.top_k is not None:
            generation_config["topK"] = request.config.top_k
        
        if request.config.stop_sequences:
            generation_config["stopSequences"] = request.config.stop_sequences
        
        return {
            "contents": contents,
            "generationConfig": generation_config,
        }

    async def _make_request(self, model_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make the API request."""
        client = await self._get_http_client()
        
        url = f"{GEMINI_API_BASE}/models/{model_name}:generateContent"
        params = {"key": self._config.api_key}
        
        response = await client.post(url, params=params, json=payload)
        
        if response.status_code != 200:
            error_msg = response.text
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_msg = error_data["error"].get("message", error_msg)
            except:
                pass
            raise Exception(f"Gemini API error ({response.status_code}): {error_msg}")
        
        return response.json()

    def _parse_response(
        self,
        request: CompletionRequest,
        response: Dict[str, Any],
        model: str,
        latency_ms: int,
    ) -> CompletionResponse:
        """Parse Gemini response into CompletionResponse."""
        # Extract content
        content = ""
        try:
            candidates = response.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    content = parts[0].get("text", "")
        except Exception:
            pass
        
        # Extract usage metadata
        usage_metadata = response.get("usageMetadata", {})
        usage = TokenUsage(
            prompt_tokens=usage_metadata.get("promptTokenCount", self.estimate_tokens(request.user_prompt)),
            completion_tokens=usage_metadata.get("candidatesTokenCount", self.estimate_tokens(content)),
            total_tokens=usage_metadata.get("totalTokenCount", 0),
        )
        
        # Parse structured output if JSON
        structured_output = None
        if request.config.response_format == ResponseFormat.JSON and content:
            try:
                # Handle markdown code blocks
                clean_content = content
                if "```json" in content:
                    clean_content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    clean_content = content.split("```")[1].split("```")[0].strip()
                
                structured_output = json.loads(clean_content)
            except json.JSONDecodeError:
                pass
        
        return CompletionResponse(
            request_id=request.request_id,
            status=CompletionStatus.SUCCESS,
            content=content,
            structured_output=structured_output,
            model=model,
            provider=self.provider_name,
            usage=usage,
            latency_ms=latency_ms,
        )

    def _create_error_response(
        self,
        request: CompletionRequest,
        error: Exception,
        model: str,
        latency_ms: int,
    ) -> CompletionResponse:
        """Create an error response from an exception."""
        # Determine error status
        status = self._map_error_to_status(error)
        
        # Extract error details
        error_message = str(error)
        error_code = None
        
        return CompletionResponse(
            request_id=request.request_id,
            status=status,
            content="",
            model=model,
            provider=self.provider_name,
            latency_ms=latency_ms,
            error_message=error_message,
            error_code=error_code,
        )

    def _map_error_to_status(self, error: Exception) -> CompletionStatus:
        """Map exception to CompletionStatus."""
        error_str = str(error).lower()
        
        # Check for rate limiting
        if "rate" in error_str or "429" in error_str or "quota" in error_str:
            return CompletionStatus.RATE_LIMITED
        
        # Check for timeout
        if "timeout" in error_str:
            return CompletionStatus.TIMEOUT
        
        # Check for content filter
        if "safety" in error_str or "blocked" in error_str:
            return CompletionStatus.CONTENT_FILTERED
        
        # Default to generic error
        return CompletionStatus.ERROR

    def _is_retryable_error(self, error: Exception) -> bool:
        """Determine if an error should trigger a retry."""
        error_str = str(error).lower()
        
        # Retryable: rate limits, timeouts, server errors
        retryable_patterns = [
            "rate",
            "429",
            "timeout",
            "500",
            "502",
            "503",
            "504",
            "connection",
            "network",
            "quota",
        ]
        
        return any(pattern in error_str for pattern in retryable_patterns)
    
    async def close(self):
        """Close the HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
