"""
Base LLM provider interface for Atlas.

This module defines the unified interface for all language model providers in Atlas,
providing a consistent API regardless of the underlying provider.
"""

import abc
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Union, ClassVar, Callable, TypeVar
from enum import Enum
import logging

from atlas.core.telemetry import traced, TracedClass
from atlas.core.retry import RetryConfig, CircuitBreaker
from atlas.core.errors import APIError

# Type variable for generic function return type
T = TypeVar("T")

logger = logging.getLogger(__name__)


class ModelRole(str, Enum):
    """Roles in a conversation with a model."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"  # Add Tool role for message factory method tests


@dataclass
class MessageContent:
    """Content of a message in the conversation."""

    type: str
    """The type of the content."""

    text: Optional[str] = None
    """The text content of the message."""

    image_url: Optional[Dict[str, Any]] = None
    """The image URL and details for image content."""

    @classmethod
    def text(cls, text: str) -> "MessageContent":
        """Create a text content.
        
        Args:
            text: The text content.
            
        Returns:
            A MessageContent instance with text type.
        """
        return cls(type="text", text=text)
        
    @classmethod
    def image_url(cls, url: str, detail: str = "auto") -> "MessageContent":
        """Create an image URL content.
        
        Args:
            url: The URL of the image.
            detail: The detail level for the image (auto, high, low).
            
        Returns:
            A MessageContent instance with image_url type.
        """
        return cls(
            type="image_url",
            image_url={"url": url, "detail": detail}
        )


@dataclass
class ModelMessage:
    """A message in a conversation with a model."""

    role: ModelRole
    """The role of the message sender."""

    content: Union[str, MessageContent, List[MessageContent]]
    """The content of the message."""

    name: Optional[str] = None
    """Optional name for the sender of the message."""

    @classmethod
    def system(cls, content: str) -> "ModelMessage":
        """Create a system message.

        Args:
            content: The text content of the message.

        Returns:
            A ModelMessage with the system role.
        """
        return cls(role=ModelRole.SYSTEM, content=content)

    @classmethod
    def user(
        cls,
        content: Union[str, MessageContent, List[MessageContent]],
        name: Optional[str] = None,
    ) -> "ModelMessage":
        """Create a user message.

        Args:
            content: The content of the message.
            name: Optional name for the user.

        Returns:
            A ModelMessage with the user role.
        """
        return cls(role=ModelRole.USER, content=content, name=name)

    @classmethod
    def assistant(
        cls,
        content: Union[str, MessageContent, List[MessageContent]],
        name: Optional[str] = None,
    ) -> "ModelMessage":
        """Create an assistant message.

        Args:
            content: The content of the message.
            name: Optional name for the assistant.

        Returns:
            A ModelMessage with the assistant role.
        """
        return cls(role=ModelRole.ASSISTANT, content=content, name=name)

    @classmethod
    def function(cls, content: str, name: str) -> "ModelMessage":
        """Create a function message.

        Args:
            content: The text content of the message.
            name: Name of the function.

        Returns:
            A ModelMessage with the function role.
        """
        return cls(role=ModelRole.FUNCTION, content=content, name=name)
        
    @classmethod
    def tool(cls, content: str, name: str) -> "ModelMessage":
        """Create a tool message.
        
        Args:
            content: The text content of the message.
            name: Name of the tool.
            
        Returns:
            A ModelMessage with the tool role.
        """
        return cls(role=ModelRole.TOOL, content=content, name=name)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary.

        Returns:
            A dictionary representation of the message.
        """
        result: Dict[str, Any] = {"role": self.role.value}

        # Handle different content types
        if isinstance(self.content, str):
            result["content"] = self.content
        elif isinstance(self.content, MessageContent):
            # Handle individual message content
            if self.content.type == "text":
                result["content"] = self.content.text
            else:
                # For non-text content (like images), include the full content structure
                content_dict = {"type": self.content.type}
                if self.content.text:
                    content_dict["text"] = self.content.text
                if self.content.image_url:
                    content_dict["image_url"] = self.content.image_url
                result["content"] = content_dict
        elif isinstance(self.content, list):
            # For multi-modal content, convert each item to a dict
            if len(self.content) == 1 and self.content[0].type == "text":
                # Simplify to just text for single text content
                result["content"] = self.content[0].text
            else:
                # Create a list of content items
                content_list = []
                for item in self.content:
                    item_dict = {"type": item.type}
                    if item.text:
                        item_dict["text"] = item.text
                    if item.image_url:
                        item_dict["image_url"] = item.image_url
                    content_list.append(item_dict)
                result["content"] = content_list

        # Add name if provided
        if self.name:
            result["name"] = self.name

        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelMessage":
        """Create a ModelMessage from a dictionary.
        
        Args:
            data: Dictionary representation of a message.
            
        Returns:
            A ModelMessage instance.
        """
        role_str = data.get("role", "")
        try:
            role = ModelRole(role_str)
        except ValueError:
            # If role is not a valid ModelRole, default to USER
            role = ModelRole.USER
            
        content = data.get("content", "")
        name = data.get("name")
        
        return cls(role=role, content=content, name=name)


@dataclass
class ModelRequest:
    """A request to generate content from a model."""

    messages: List[ModelMessage]
    """The conversation history."""

    max_tokens: Optional[int] = None
    """Maximum number of tokens to generate."""

    temperature: Optional[float] = None
    """Temperature for sampling, higher values mean more randomness."""

    system_prompt: Optional[str] = None
    """Optional system prompt/instructions."""

    model: Optional[str] = None
    """Optional model override."""

    stop_sequences: Optional[List[str]] = None
    """Optional sequences that will stop generation."""

    top_p: Optional[float] = None
    """Nucleus sampling parameter."""

    frequency_penalty: Optional[float] = None
    """Penalty for token frequency."""

    presence_penalty: Optional[float] = None
    """Penalty for token presence."""

    response_format: Optional[Dict[str, Any]] = None
    """Optional response format specification."""

    def __post_init__(self):
        """Validate and process the request after initialization."""
        # If system prompt is provided but not in messages, add it
        if self.system_prompt and not any(
            msg.role == ModelRole.SYSTEM for msg in self.messages
        ):
            self.messages.insert(0, ModelMessage.system(self.system_prompt))

    def to_provider_request(self, provider_name: str) -> Dict[str, Any]:
        """Convert to a provider-specific request format.

        Args:
            provider_name: The name of the provider.

        Returns:
            A dictionary with the request in provider-specific format.
        """
        # Base request that works for most providers
        request = {
            "messages": [msg.to_dict() for msg in self.messages],
        }

        # Add optional parameters if specified
        if self.max_tokens:
            request["max_tokens"] = self.max_tokens

        if self.temperature is not None:
            request["temperature"] = self.temperature

        if self.stop_sequences:
            request["stop"] = self.stop_sequences

        if self.top_p is not None:
            request["top_p"] = self.top_p

        if self.response_format:
            request["response_format"] = self.response_format

        # Provider-specific adaptations
        if provider_name.lower() == "anthropic":
            # Anthropic uses system as a separate parameter
            system_messages = [
                msg for msg in self.messages if msg.role == ModelRole.SYSTEM
            ]
            if system_messages:
                # Use the first system message as the system parameter
                request["system"] = system_messages[0].to_dict()["content"]
                # Remove system messages from the messages list
                request["messages"] = [
                    msg.to_dict()
                    for msg in self.messages
                    if msg.role != ModelRole.SYSTEM
                ]

        elif provider_name.lower() == "openai":
            # OpenAI-specific adaptations if needed
            if self.frequency_penalty is not None:
                request["frequency_penalty"] = self.frequency_penalty

            if self.presence_penalty is not None:
                request["presence_penalty"] = self.presence_penalty

        # Add any other provider-specific adaptations as needed

        return request


@dataclass
class TokenUsage:
    """Token usage statistics for a model response."""

    input_tokens: int = 0
    """Number of input tokens."""

    output_tokens: int = 0
    """Number of output tokens."""

    total_tokens: int = 0
    """Total number of tokens."""

    def __post_init__(self):
        """Calculate total_tokens if not explicitly set."""
        if self.total_tokens == 0 and (self.input_tokens > 0 or self.output_tokens > 0):
            self.total_tokens = self.input_tokens + self.output_tokens
            
    def to_dict(self) -> Dict[str, int]:
        """Convert the token usage to a dictionary.
        
        Returns:
            A dictionary representation of the token usage.
        """
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens
        }


@dataclass
class CostEstimate:
    """Cost estimate for a model response."""

    input_cost: float = 0.0
    """Cost of input tokens in USD."""

    output_cost: float = 0.0
    """Cost of output tokens in USD."""

    total_cost: float = 0.0
    """Total cost in USD."""

    def __post_init__(self):
        """Calculate total_cost if not explicitly set."""
        if self.total_cost == 0.0 and (self.input_cost > 0.0 or self.output_cost > 0.0):
            self.total_cost = self.input_cost + self.output_cost

    def __str__(self) -> str:
        """Get a string representation of the cost estimate.

        Returns:
            A formatted cost string.
        """
        # Format costs based on their magnitude for better readability
        if self.total_cost < 0.0000001:
            # For extremely small costs (nearly zero), use scientific notation
            return f"${self.total_cost:.2e} (Input: ${self.input_cost:.2e}, Output: ${self.output_cost:.2e})"
        elif self.total_cost < 0.000001:
            # For extremely small costs, use 7 decimal places
            return f"${self.total_cost:.7f} (Input: ${self.input_cost:.7f}, Output: ${self.output_cost:.7f})"
        elif self.total_cost < 0.001:
            # For very small costs, use 6 decimal places
            return f"${self.total_cost:.6f} (Input: ${self.input_cost:.6f}, Output: ${self.output_cost:.6f})"
        elif self.total_cost < 0.01:
            # For small costs, use 4 decimal places
            return f"${self.total_cost:.4f} (Input: ${self.input_cost:.4f}, Output: ${self.output_cost:.4f})"
        else:
            # For larger costs, use 2 decimal places
            return f"${self.total_cost:.2f} (Input: ${self.input_cost:.2f}, Output: ${self.output_cost:.2f})"
            
    def to_dict(self) -> Dict[str, float]:
        """Convert the cost estimate to a dictionary.
        
        Returns:
            A dictionary representation of the cost estimate.
        """
        return {
            "input_cost": self.input_cost,
            "output_cost": self.output_cost,
            "total_cost": self.total_cost
        }


@dataclass
class ModelResponse:
    """Response from a language model."""

    content: str
    """The text content of the response."""

    model: str
    """The name of the model that generated the response."""

    provider: str
    """The provider that generated the response."""

    usage: TokenUsage = field(default_factory=TokenUsage)
    """Token usage statistics."""

    cost: CostEstimate = field(default_factory=CostEstimate)
    """Cost estimate for the response."""

    finish_reason: Optional[str] = None
    """The reason the model stopped generating."""

    raw_response: Optional[Dict[str, Any]] = None
    """The raw response from the provider API."""

    def __str__(self) -> str:
        """Get a string representation of the response.

        Returns:
            A summary of the response.
        """
        return (
            f"Response from {self.provider}/{self.model}:\n"
            f"Content ({len(self.content)} chars): {self.content[:100]}{'...' if len(self.content) > 100 else ''}\n"
            f"Usage: {self.usage.input_tokens} input, {self.usage.output_tokens} output tokens\n"
            f"Cost: {self.cost}"
        )


class ModelProvider(TracedClass, abc.ABC):
    """Abstract base class for language model providers."""
    # Note: The class name remains ModelProvider for backward compatibility
    # but will be renamed to LLMProvider in future versions
    
    # Default retry configuration for all providers
    DEFAULT_RETRY_CONFIG: ClassVar[RetryConfig] = RetryConfig(
        max_retries=3,
        initial_delay=1.0,
        backoff_factor=2.0,
        max_delay=60.0,
        jitter_factor=0.1
    )
    
    # Default circuit breaker configuration for all providers
    DEFAULT_CIRCUIT_BREAKER: ClassVar[CircuitBreaker] = CircuitBreaker(
        failure_threshold=5,
        recovery_timeout=60.0,
        test_requests=1
    )

    def __init__(self, retry_config: Optional[RetryConfig] = None, circuit_breaker: Optional[CircuitBreaker] = None):
        """Initialize the model provider with retry configuration.
        
        Args:
            retry_config: Custom retry configuration, or None to use the default
            circuit_breaker: Custom circuit breaker, or None to use the default
        """
        self.retry_config = retry_config or self.DEFAULT_RETRY_CONFIG
        self.circuit_breaker = circuit_breaker or self.DEFAULT_CIRCUIT_BREAKER
        super().__init__()
        
    def safe_execute_with_retry(
        self, 
        func: Callable[..., T], 
        *args: Any, 
        error_handler: Optional[Callable[[Exception], Optional[Exception]]] = None,
        default_value: Optional[T] = None,
        **kwargs: Any
    ) -> T:
        """Execute a function with retry logic and circuit breaker protection.
        
        This utility wraps function execution with:
        1. Circuit breaker protection to prevent overloading failing services
        2. Exponential backoff retry for transient errors
        3. Consistent error handling and logging
        
        Args:
            func: The function to execute
            *args: Arguments to pass to the function
            error_handler: Optional function to process errors before retrying
            default_value: Value to return if all retries fail and no error is raised
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The result of the function call
            
        Raises:
            Exception: If the function call fails after all retries and no default_value is provided
        """
        # First check the circuit breaker
        if not self.circuit_breaker.allow_request():
            logger.warning(
                f"{self.name} provider circuit breaker is open, request blocked"
            )
            if default_value is not None:
                return default_value
            raise APIError(
                message=f"{self.name} provider circuit breaker is open, request blocked",
                severity="WARNING",
                retry_possible=False,
            )
            
        retry_count = 0
        max_retries = self.retry_config.max_retries
        last_error = None
            
        while True:
            try:
                # Execute the function
                result = func(*args, **kwargs)
                # Record successful execution in circuit breaker
                self.circuit_breaker.record_success()
                return result
                
            except Exception as error:
                last_error = error
                
                # Allow custom error handling/transformation before retry logic
                if error_handler:
                    try:
                        transformed_error = error_handler(error)
                        if transformed_error:
                            last_error = transformed_error
                    except Exception as handler_error:
                        logger.warning(
                            f"Error in custom error handler: {handler_error}"
                        )
                
                # Check if we should retry
                if retry_count < max_retries:
                    should_retry = False
                    
                    # Check for rate limit and transient errors
                    if hasattr(error, "retry_possible") and getattr(error, "retry_possible"):
                        should_retry = True
                    elif hasattr(error, "status_code") and getattr(error, "status_code") in self.retry_config.retryable_status_codes:
                        should_retry = True
                    elif any(isinstance(error, err_type) for err_type in self.retry_config.retryable_errors):
                        should_retry = True
                        
                    if should_retry:
                        retry_count += 1
                        delay = self.retry_config.initial_delay * (self.retry_config.backoff_factor ** (retry_count - 1))
                        
                        # Apply jitter to prevent thundering herd
                        jitter = delay * self.retry_config.jitter_factor * random.random()
                        delay = min(delay + jitter, self.retry_config.max_delay)
                        
                        logger.warning(
                            f"Retryable error from {self.name} provider: {type(last_error).__name__}. "
                            f"Retrying in {delay:.2f}s ({retry_count}/{max_retries})"
                        )
                        time.sleep(delay)
                        continue
                
                # Record failure in circuit breaker if we're not retrying
                self.circuit_breaker.record_failure()
                
                # If we have a default value, return it instead of raising the error
                if default_value is not None:
                    logger.error(
                        f"Error from {self.name} provider after {retry_count} retries: {last_error}. "
                        f"Returning default value."
                    )
                    return default_value
                    
                # Otherwise, raise the last error
                raise last_error

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Get the name of the provider.

        Returns:
            The provider's name as a string.
        """
        pass

    @property
    def model_name(self) -> str:
        """Get the name of the model.

        Returns:
            The model name as a string.

        Note:
            Providers should override this to return their specific model name.
            The default implementation falls back to the provider's internal storage.
        """
        # Try to get model name from various common attribute names
        for attr in ["_model_name", "model", "_model"]:
            if hasattr(self, attr):
                return getattr(self, attr)

        # Fall back to a generic name
        return "unnamed-model"

    @traced(name="get_available_models")
    @abc.abstractmethod
    def get_available_models(self) -> List[str]:
        """Get a list of available models for this provider.

        Returns:
            A list of model identifiers.
        """
        pass

    @traced(name="validate_api_key")
    @abc.abstractmethod
    def validate_api_key(self) -> bool:
        """Validate that the API key is set and valid.

        Returns:
            True if the API key is valid, False otherwise.
        """
        pass

    @traced(name="validate_api_key_detailed")
    def validate_api_key_detailed(self) -> Dict[str, Any]:
        """Validate API key with detailed information about the result.

        Returns:
            A dictionary with validation details:
            - valid: bool - Whether the key is valid
            - error: Optional[str] - Error message if validation failed
            - provider: str - Provider name
            - key_present: bool - Whether the key is present (but might be invalid)
        """
        try:
            # Try to validate the key
            valid = self.validate_api_key()

            # Build the response
            result = {
                "valid": valid,
                "provider": self.name,
                "key_present": bool(getattr(self, "_api_key", None)),
                "error": None,
            }

            if not valid:
                if not result["key_present"]:
                    result["error"] = f"No API key found for {self.name}"
                else:
                    result["error"] = f"API key for {self.name} is invalid"

            return result

        except Exception as e:
            # If validation throws an exception, capture it
            logger.error(f"Error during API key validation for {self.name}: {str(e)}")
            return {
                "valid": False,
                "provider": self.name,
                "key_present": bool(getattr(self, "_api_key", None)),
                "error": str(e),
            }

    @traced(name="generate", log_args=True)
    @abc.abstractmethod
    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from the model.

        Args:
            request: The model request.

        Returns:
            A ModelResponse containing the generated content and metadata.
        """
        pass

    @traced(name="calculate_token_usage")
    @abc.abstractmethod
    def calculate_token_usage(self, request: ModelRequest, response: Any) -> TokenUsage:
        """Calculate token usage for a request and response.

        Args:
            request: The model request.
            response: The raw response from the provider API.

        Returns:
            A TokenUsage object with token counts.
        """
        pass

    @traced(name="calculate_cost")
    @abc.abstractmethod
    def calculate_cost(self, usage: TokenUsage, model: str) -> CostEstimate:
        """Calculate approximate cost based on token usage.

        Args:
            usage: Token usage statistics.
            model: The model used for the request.

        Returns:
            A CostEstimate with input, output, and total costs.
        """
        pass

    @traced(name="stream")
    def stream(self, request: ModelRequest) -> Tuple[ModelResponse, Any]:
        """Stream a response from the model (if supported).

        Args:
            request: The model request.

        Returns:
            A tuple of (final ModelResponse, stream iterator).

        Raises:
            NotImplementedError: If streaming is not supported by this provider.
        """
        raise NotImplementedError(f"Streaming not supported by {self.name} provider")
