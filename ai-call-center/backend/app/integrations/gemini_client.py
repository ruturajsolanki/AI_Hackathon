"""
Google Gemini LLM Client

Concrete implementation of LLMClient for Google's Gemini API.
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
    ResponseFormat,
    StructuredCompletionRequest,
    StructuredCompletionResponse,
    TokenUsage,
)

T = TypeVar('T', bound=BaseModel)


class GeminiConfig(BaseModel):
    """Configuration for Gemini client."""
    
    api_key: Optional[str] = None
    default_model: str = "gemini-1.5-flash"
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
    
    Uses the Google Generative AI SDK for API communication.
    Handles authentication, retries, and error mapping.
    
    Example:
        config = GeminiConfig.from_env()
        client = GeminiClient(config)
        
        response = await client.generate(
            user_prompt="Hello!",
            system_prompt="You are a helpful assistant."
        )
    """

    # Supported models
    SUPPORTED_MODELS = [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
        "gemini-2.0-flash-exp",
        "gemini-pro",
    ]

    def __init__(self, config: Optional[GeminiConfig] = None):
        """
        Initialize the Gemini client.
        
        Args:
            config: Configuration object. If None, loads from environment.
        """
        self._config = config or GeminiConfig.from_env()
        self._client = None

    def _get_client(self):
        """
        Get or create the Gemini client.
        
        Lazy initialization to defer import until needed.
        """
        if self._client is None:
            try:
                import google.generativeai as genai
                
                genai.configure(api_key=self._config.api_key)
                self._client = genai
            except ImportError:
                raise RuntimeError(
                    "Google Generative AI package not installed. "
                    "Install with: pip install google-generativeai"
                )
        
        return self._client

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
        
        # Build the prompt
        prompt = self._build_prompt(request)
        
        # Attempt completion with retries
        last_error = None
        for attempt in range(self._config.max_retries):
            try:
                response = await self._make_request(model_name, prompt, request.config)
                
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
        """
        try:
            genai = self._get_client()
            
            # Simple model list call to verify API access
            model = genai.GenerativeModel(self.default_model)
            # Quick test prompt
            response = await asyncio.to_thread(
                model.generate_content,
                "Hi",
                generation_config={"max_output_tokens": 5}
            )
            return response is not None
            
        except Exception:
            return False

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Gemini uses a different tokenizer, roughly 4 chars per token.
        """
        # Gemini doesn't expose a public tokenizer, use approximation
        return len(text) // 4

    def _build_prompt(self, request: CompletionRequest) -> str:
        """Convert request to Gemini prompt format."""
        parts = []
        
        # Add system prompt as context
        if request.system_prompt:
            parts.append(f"[System Instructions]\n{request.system_prompt}\n")
        
        # Add conversation history
        for msg in request.messages:
            role_prefix = "User" if msg.role.value == "user" else "Assistant"
            parts.append(f"[{role_prefix}]\n{msg.content}\n")
        
        # Add user prompt
        parts.append(f"[User]\n{request.user_prompt}")
        
        return "\n".join(parts)

    async def _make_request(
        self, 
        model_name: str, 
        prompt: str, 
        config: GenerationConfig
    ) -> Any:
        """Make the API request."""
        genai = self._get_client()
        
        # Configure generation settings
        generation_config = {
            "temperature": config.temperature,
            "max_output_tokens": config.max_tokens,
            "top_p": config.top_p,
        }
        
        if config.top_k is not None:
            generation_config["top_k"] = config.top_k
        
        if config.stop_sequences:
            generation_config["stop_sequences"] = config.stop_sequences
        
        # Create model and generate
        model = genai.GenerativeModel(
            model_name,
            generation_config=generation_config
        )
        
        # Use asyncio.to_thread for the sync API
        response = await asyncio.to_thread(
            model.generate_content,
            prompt
        )
        
        return response

    def _parse_response(
        self,
        request: CompletionRequest,
        response: Any,
        model: str,
        latency_ms: int,
    ) -> CompletionResponse:
        """Parse Gemini response into CompletionResponse."""
        # Extract content
        content = ""
        try:
            if response.text:
                content = response.text
        except Exception:
            # Handle blocked content or other issues
            if hasattr(response, 'parts') and response.parts:
                content = response.parts[0].text
        
        # Estimate usage (Gemini doesn't always provide exact counts)
        usage = TokenUsage(
            prompt_tokens=self.estimate_tokens(request.user_prompt),
            completion_tokens=self.estimate_tokens(content),
            total_tokens=self.estimate_tokens(request.user_prompt) + self.estimate_tokens(content),
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
        
        # Try to extract error info
        if hasattr(error, 'status_code'):
            error_code = str(error.status_code)
        
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
        if "rate" in error_str or "429" in error_str or "quota" in error_str:
            return CompletionStatus.RATE_LIMITED
        
        # Check for timeout
        if "timeout" in error_type.lower() or "timeout" in error_str:
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
