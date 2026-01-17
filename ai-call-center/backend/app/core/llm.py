"""
LLM Client Abstraction

Vendor-agnostic interface for Large Language Model interactions.
Designed for enterprise use with provider flexibility.

This module defines:
- Standard interfaces for LLM communication
- Structured request/response models
- Abstract base class for provider implementations

Concrete implementations (OpenAI, Anthropic, Azure, etc.) should
inherit from LLMClient and implement the abstract methods.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar, Generic
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Enumerations
# -----------------------------------------------------------------------------

class MessageRole(str, Enum):
    """Roles for messages in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ResponseFormat(str, Enum):
    """Expected format of the LLM response."""
    TEXT = "text"
    JSON = "json"
    STRUCTURED = "structured"


class CompletionStatus(str, Enum):
    """Status of the completion request."""
    SUCCESS = "success"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    CONTENT_FILTERED = "content_filtered"


# -----------------------------------------------------------------------------
# Request Models
# -----------------------------------------------------------------------------

class Message(BaseModel):
    """
    A single message in a conversation.
    
    Represents either a system instruction, user input,
    or assistant response.
    """
    role: MessageRole = Field(description="Role of the message sender")
    content: str = Field(description="Content of the message")
    name: Optional[str] = Field(
        default=None,
        description="Optional name for the message sender"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the message"
    )


class GenerationConfig(BaseModel):
    """
    Configuration for text generation.
    
    Controls the behavior of the LLM during generation.
    All parameters are optional with sensible defaults.
    """
    # Sampling parameters
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Controls randomness. Lower = more deterministic"
    )
    top_p: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling threshold"
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        description="Top-k sampling (if supported)"
    )
    
    # Length parameters
    max_tokens: int = Field(
        default=1024,
        ge=1,
        description="Maximum tokens to generate"
    )
    min_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        description="Minimum tokens to generate (if supported)"
    )
    
    # Control parameters
    stop_sequences: List[str] = Field(
        default_factory=list,
        description="Sequences that stop generation"
    )
    presence_penalty: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Penalty for token presence"
    )
    frequency_penalty: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Penalty for token frequency"
    )
    
    # Response format
    response_format: ResponseFormat = Field(
        default=ResponseFormat.TEXT,
        description="Expected format of response"
    )
    json_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description="JSON schema for structured output (if supported)"
    )
    
    # Reproducibility
    seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility (if supported)"
    )


class CompletionRequest(BaseModel):
    """
    Request for LLM text completion.
    
    Encapsulates all information needed to generate a response.
    """
    request_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this request"
    )
    
    # Messages
    system_prompt: Optional[str] = Field(
        default=None,
        description="System-level instructions for the model"
    )
    messages: List[Message] = Field(
        default_factory=list,
        description="Conversation history"
    )
    user_prompt: str = Field(
        description="The user's current input"
    )
    
    # Configuration
    config: GenerationConfig = Field(
        default_factory=GenerationConfig,
        description="Generation configuration"
    )
    
    # Metadata
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for logging/tracing"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Request timestamp"
    )

    def to_messages(self) -> List[Message]:
        """
        Convert request to a flat list of messages.
        
        Combines system prompt, conversation history, and user prompt
        into a single message list suitable for the LLM.
        """
        result = []
        
        if self.system_prompt:
            result.append(Message(
                role=MessageRole.SYSTEM,
                content=self.system_prompt,
            ))
        
        result.extend(self.messages)
        
        result.append(Message(
            role=MessageRole.USER,
            content=self.user_prompt,
        ))
        
        return result


# -----------------------------------------------------------------------------
# Response Models
# -----------------------------------------------------------------------------

class TokenUsage(BaseModel):
    """Token usage statistics for a completion."""
    prompt_tokens: int = Field(description="Tokens in the prompt")
    completion_tokens: int = Field(description="Tokens in the completion")
    total_tokens: int = Field(description="Total tokens used")
    
    # Cost tracking (optional, provider-dependent)
    estimated_cost: Optional[float] = Field(
        default=None,
        description="Estimated cost in USD"
    )


class CompletionResponse(BaseModel):
    """
    Response from LLM text completion.
    
    Provides the generated content along with metadata
    about the generation process.
    """
    response_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this response"
    )
    request_id: UUID = Field(
        description="ID of the originating request"
    )
    
    # Status
    status: CompletionStatus = Field(
        description="Status of the completion"
    )
    
    # Content
    content: str = Field(
        default="",
        description="Generated text content"
    )
    
    # Structured output (if requested)
    structured_output: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parsed structured output (if JSON/structured format)"
    )
    
    # Metadata
    model: str = Field(
        description="Model identifier used for generation"
    )
    provider: str = Field(
        description="LLM provider name"
    )
    
    # Usage
    usage: Optional[TokenUsage] = Field(
        default=None,
        description="Token usage statistics"
    )
    
    # Timing
    latency_ms: int = Field(
        default=0,
        description="Generation latency in milliseconds"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response timestamp"
    )
    
    # Error handling
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if status is not SUCCESS"
    )
    error_code: Optional[str] = Field(
        default=None,
        description="Provider-specific error code"
    )

    @property
    def is_success(self) -> bool:
        """Check if the completion was successful."""
        return self.status == CompletionStatus.SUCCESS

    @property
    def is_error(self) -> bool:
        """Check if the completion failed."""
        return self.status != CompletionStatus.SUCCESS


# -----------------------------------------------------------------------------
# Structured Output Support
# -----------------------------------------------------------------------------

T = TypeVar('T', bound=BaseModel)


class StructuredCompletionRequest(CompletionRequest, Generic[T]):
    """
    Request for structured LLM output.
    
    Extends CompletionRequest with type information for
    automatic parsing of structured responses.
    """
    output_type: Optional[type] = Field(
        default=None,
        exclude=True,
        description="Pydantic model type for output parsing"
    )


class StructuredCompletionResponse(CompletionResponse, Generic[T]):
    """
    Response with typed structured output.
    
    Extends CompletionResponse with parsed output of
    the specified type.
    """
    parsed_output: Optional[T] = Field(
        default=None,
        description="Parsed and validated output object"
    )


# -----------------------------------------------------------------------------
# LLM Client Interface
# -----------------------------------------------------------------------------

class LLMClient(ABC):
    """
    Abstract base class for LLM client implementations.
    
    Defines the standard interface for interacting with
    Large Language Models. Concrete implementations should
    handle provider-specific details while conforming to
    this interface.
    
    This abstraction allows:
    - Swapping LLM providers without changing agent code
    - Consistent error handling across providers
    - Unified logging and monitoring
    - Easy testing with mock implementations
    
    Example usage:
        # In production
        client = OpenAIClient(config)
        
        # In testing
        client = MockLLMClient()
        
        # Same interface for both
        response = await client.complete(request)
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Return the name of the LLM provider.
        
        Used for logging, metrics, and response metadata.
        
        Returns:
            Provider name (e.g., "openai", "anthropic", "azure")
        """
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """
        Return the default model identifier.
        
        Used when no specific model is requested.
        
        Returns:
            Model identifier (e.g., "gpt-4", "claude-3-opus")
        """
        pass

    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """
        Return list of supported model identifiers.
        
        Used for validation and model selection.
        
        Returns:
            List of supported model identifiers
        """
        pass

    @abstractmethod
    async def complete(
        self,
        request: CompletionRequest,
        model: Optional[str] = None,
    ) -> CompletionResponse:
        """
        Generate a text completion.
        
        This is the primary method for LLM interaction.
        Implementations should handle:
        - Message formatting for the specific provider
        - API communication
        - Error handling and retries
        - Response parsing
        
        Args:
            request: The completion request containing prompts and config
            model: Optional model override (uses default if not specified)
            
        Returns:
            CompletionResponse with generated content and metadata
            
        Note:
            Implementations should never raise exceptions for API errors.
            Instead, return a CompletionResponse with appropriate error status.
        """
        pass

    @abstractmethod
    async def complete_structured(
        self,
        request: StructuredCompletionRequest[T],
        output_type: type[T],
        model: Optional[str] = None,
    ) -> StructuredCompletionResponse[T]:
        """
        Generate a structured completion with typed output.
        
        Extends complete() with automatic parsing of the
        response into a Pydantic model.
        
        Args:
            request: The completion request
            output_type: Pydantic model class for output parsing
            model: Optional model override
            
        Returns:
            StructuredCompletionResponse with parsed output
            
        Note:
            If parsing fails, the response will have is_success=False
            and the raw content will still be available.
        """
        pass

    async def generate(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
        model: Optional[str] = None,
    ) -> CompletionResponse:
        """
        Simplified generation interface.
        
        Convenience method for simple prompt-response interactions
        without needing to construct a full CompletionRequest.
        
        Args:
            user_prompt: The user's input
            system_prompt: Optional system instructions
            config: Optional generation configuration
            model: Optional model override
            
        Returns:
            CompletionResponse with generated content
        """
        request = CompletionRequest(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            config=config or GenerationConfig(),
        )
        return await self.complete(request, model)

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the LLM service is available.
        
        Used for readiness probes and monitoring.
        
        Returns:
            True if the service is healthy, False otherwise
        """
        pass

    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in text.
        
        Used for request planning and cost estimation.
        Provider implementations should use their specific
        tokenizer for accurate estimates.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        pass

    def validate_model(self, model: str) -> bool:
        """
        Validate that a model is supported.
        
        Args:
            model: Model identifier to validate
            
        Returns:
            True if the model is supported
        """
        return model in self.supported_models


# -----------------------------------------------------------------------------
# Mock Client for Testing
# -----------------------------------------------------------------------------

class MockLLMClient(LLMClient):
    """
    Mock LLM client for testing and development.
    
    Returns configurable responses without making API calls.
    Useful for:
    - Unit testing agents
    - Development without API access
    - Demo environments
    """

    def __init__(
        self,
        default_response: str = "This is a mock response.",
        latency_ms: int = 100,
    ):
        """
        Initialize the mock client.
        
        Args:
            default_response: Response to return for all requests
            latency_ms: Simulated latency in milliseconds
        """
        self._default_response = default_response
        self._latency_ms = latency_ms
        self._call_count = 0
        self._last_request: Optional[CompletionRequest] = None

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def default_model(self) -> str:
        return "mock-model"

    @property
    def supported_models(self) -> List[str]:
        return ["mock-model", "mock-model-large"]

    async def complete(
        self,
        request: CompletionRequest,
        model: Optional[str] = None,
    ) -> CompletionResponse:
        """Return a mock response."""
        import asyncio
        
        self._call_count += 1
        self._last_request = request
        
        # Simulate latency
        await asyncio.sleep(self._latency_ms / 1000)
        
        return CompletionResponse(
            request_id=request.request_id,
            status=CompletionStatus.SUCCESS,
            content=self._default_response,
            model=model or self.default_model,
            provider=self.provider_name,
            usage=TokenUsage(
                prompt_tokens=self.estimate_tokens(request.user_prompt),
                completion_tokens=self.estimate_tokens(self._default_response),
                total_tokens=100,
            ),
            latency_ms=self._latency_ms,
        )

    async def complete_structured(
        self,
        request: StructuredCompletionRequest[T],
        output_type: type[T],
        model: Optional[str] = None,
    ) -> StructuredCompletionResponse[T]:
        """Return a mock structured response."""
        base_response = await self.complete(request, model)
        
        return StructuredCompletionResponse(
            **base_response.model_dump(),
            parsed_output=None,  # Mock doesn't parse
        )

    async def health_check(self) -> bool:
        """Always returns True for mock."""
        return True

    def estimate_tokens(self, text: str) -> int:
        """Rough estimate: ~4 characters per token."""
        return len(text) // 4

    @property
    def call_count(self) -> int:
        """Number of times complete() was called."""
        return self._call_count

    @property
    def last_request(self) -> Optional[CompletionRequest]:
        """The most recent request received."""
        return self._last_request

    def set_response(self, response: str) -> None:
        """Set the response to return."""
        self._default_response = response
