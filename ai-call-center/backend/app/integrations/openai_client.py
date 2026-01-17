"""
OpenAI LLM Client

Concrete implementation of LLMClient for OpenAI's API.
Handles authentication, request formatting, and error handling.
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypeVar

from pydantic import BaseModel

from app.core.llm import (
    CompletionRequest,
    CompletionResponse,
    CompletionStatus,
    GenerationConfig,
    LLMClient,
    Message,
    MessageRole,
    ResponseFormat,
    StructuredCompletionRequest,
    StructuredCompletionResponse,
    TokenUsage,
)

T = TypeVar('T', bound=BaseModel)


class OpenAIConfig(BaseModel):
    """Configuration for OpenAI client."""
    
    api_key: Optional[str] = None
    organization: Optional[str] = None
    base_url: Optional[str] = None
    default_model: str = "gpt-4o-mini"
    timeout_seconds: float = 60.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0

    @classmethod
    def from_env(cls) -> "OpenAIConfig":
        """
        Load configuration from environment variables.
        
        Environment variables:
        - OPENAI_API_KEY: API key (required)
        - OPENAI_ORGANIZATION: Organization ID (optional)
        - OPENAI_BASE_URL: Base URL override (optional)
        - OPENAI_DEFAULT_MODEL: Default model (optional)
        - OPENAI_TIMEOUT: Timeout in seconds (optional)
        - OPENAI_MAX_RETRIES: Max retry attempts (optional)
        """
        return cls(
            api_key=os.getenv("OPENAI_API_KEY"),
            organization=os.getenv("OPENAI_ORGANIZATION"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            default_model=os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini"),
            timeout_seconds=float(os.getenv("OPENAI_TIMEOUT", "60")),
            max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "3")),
        )


class OpenAIClient(LLMClient):
    """
    OpenAI implementation of LLMClient.
    
    Uses the OpenAI Python SDK for API communication.
    Handles authentication, retries, and error mapping.
    
    Example:
        config = OpenAIConfig.from_env()
        client = OpenAIClient(config)
        
        response = await client.generate(
            user_prompt="Hello!",
            system_prompt="You are a helpful assistant."
        )
    """

    # Supported models
    SUPPORTED_MODELS = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
    ]

    def __init__(self, config: Optional[OpenAIConfig] = None):
        """
        Initialize the OpenAI client.
        
        Args:
            config: Configuration object. If None, loads from environment.
        """
        self._config = config or OpenAIConfig.from_env()
        self._client = None
        self._async_client = None

    def _get_client(self):
        """
        Get or create the OpenAI client.
        
        Lazy initialization to defer import until needed.
        """
        if self._async_client is None:
            try:
                from openai import AsyncOpenAI
                
                self._async_client = AsyncOpenAI(
                    api_key=self._config.api_key,
                    organization=self._config.organization,
                    base_url=self._config.base_url,
                    timeout=self._config.timeout_seconds,
                    max_retries=0,  # We handle retries ourselves
                )
            except ImportError:
                raise RuntimeError(
                    "OpenAI package not installed. "
                    "Install with: pip install openai"
                )
        
        return self._async_client

    @property
    def provider_name(self) -> str:
        """Return 'openai' as the provider name."""
        return "openai"

    @property
    def default_model(self) -> str:
        """Return the configured default model."""
        return self._config.default_model

    @property
    def supported_models(self) -> List[str]:
        """Return list of supported OpenAI models."""
        return self.SUPPORTED_MODELS

    async def complete(
        self,
        request: CompletionRequest,
        model: Optional[str] = None,
    ) -> CompletionResponse:
        """
        Generate a completion using OpenAI's API.
        
        Args:
            request: The completion request
            model: Optional model override
            
        Returns:
            CompletionResponse with generated content
        """
        start_time = datetime.now(timezone.utc)
        model = model or self.default_model
        
        # Build messages list
        messages = self._build_messages(request)
        
        # Build API parameters
        api_params = self._build_api_params(request.config, model, messages)
        
        # Attempt completion with retries
        last_error = None
        for attempt in range(self._config.max_retries):
            try:
                response = await self._make_request(api_params)
                
                # Calculate latency
                end_time = datetime.now(timezone.utc)
                latency_ms = int((end_time - start_time).total_seconds() * 1000)
                
                return self._parse_response(
                    request=request,
                    response=response,
                    model=model,
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
            model=model,
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
                json_data = json.loads(base_response.content)
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
        Check if the OpenAI API is accessible.
        
        Makes a minimal request to verify connectivity.
        """
        try:
            client = self._get_client()
            
            # Simple models list call to verify API access
            await client.models.list()
            return True
            
        except Exception:
            return False

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Uses tiktoken for accurate estimates when available,
        falls back to character-based estimation.
        """
        try:
            import tiktoken
            
            # Use cl100k_base encoding (used by GPT-4 and GPT-3.5-turbo)
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
            
        except ImportError:
            # Fallback: roughly 4 characters per token
            return len(text) // 4

    def _build_messages(self, request: CompletionRequest) -> List[Dict[str, str]]:
        """Convert request to OpenAI message format."""
        messages = []
        
        # Add system prompt
        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt,
            })
        
        # Add conversation history
        for msg in request.messages:
            messages.append({
                "role": msg.role.value,
                "content": msg.content,
            })
        
        # Add user prompt
        messages.append({
            "role": "user",
            "content": request.user_prompt,
        })
        
        return messages

    def _build_api_params(
        self,
        config: GenerationConfig,
        model: str,
        messages: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Build OpenAI API parameters from config."""
        params = {
            "model": model,
            "messages": messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
            "presence_penalty": config.presence_penalty,
            "frequency_penalty": config.frequency_penalty,
        }
        
        # Add stop sequences if provided
        if config.stop_sequences:
            params["stop"] = config.stop_sequences
        
        # Add seed for reproducibility
        if config.seed is not None:
            params["seed"] = config.seed
        
        # Add response format for JSON mode
        if config.response_format == ResponseFormat.JSON:
            params["response_format"] = {"type": "json_object"}
        
        return params

    async def _make_request(self, params: Dict[str, Any]) -> Any:
        """Make the API request."""
        client = self._get_client()
        return await client.chat.completions.create(**params)

    def _parse_response(
        self,
        request: CompletionRequest,
        response: Any,
        model: str,
        latency_ms: int,
    ) -> CompletionResponse:
        """Parse OpenAI response into CompletionResponse."""
        # Extract content
        content = ""
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content or ""
        
        # Extract usage
        usage = None
        if response.usage:
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
        
        # Parse structured output if JSON
        structured_output = None
        if request.config.response_format == ResponseFormat.JSON and content:
            try:
                structured_output = json.loads(content)
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
        
        # Try to extract OpenAI-specific error info
        if hasattr(error, 'status_code'):
            error_code = str(error.status_code)
        if hasattr(error, 'message'):
            error_message = error.message
        
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
        error_type = type(error).__name__
        error_str = str(error).lower()
        
        # Check for rate limiting
        if "rate" in error_str or "429" in error_str:
            return CompletionStatus.RATE_LIMITED
        
        # Check for timeout
        if "timeout" in error_type.lower() or "timeout" in error_str:
            return CompletionStatus.TIMEOUT
        
        # Check for content filter
        if "content" in error_str and "filter" in error_str:
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
        ]
        
        return any(pattern in error_str for pattern in retryable_patterns)
