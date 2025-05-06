"""
Base model provider interface for Atlas.

This module defines the unified interface for all model providers in Atlas,
providing a consistent API regardless of the underlying provider.
"""

import abc
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum
import logging

from atlas.core.telemetry import traced, TracedClass

logger = logging.getLogger(__name__)


class ModelRole(str, Enum):
    """Roles in a conversation with a model."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class MessageContent:
    """Content of a message in the conversation."""

    text: str
    """The text content of the message."""

    mime_type: str = "text/plain"
    """The MIME type of the content."""


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
            result["content"] = self.content.text
        elif isinstance(self.content, list):
            # For multi-modal content, this would need to be adapted per provider
            if len(self.content) == 1:
                result["content"] = self.content[0].text
            else:
                # Explicitly type the list to avoid type inconsistency
                content_texts: List[str] = [c.text for c in self.content]
                result["content"] = content_texts

        # Add name if provided
        if self.name:
            result["name"] = self.name

        return result


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
        return f"${self.total_cost:.6f} (Input: ${self.input_cost:.6f}, Output: ${self.output_cost:.6f})"


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
    """Abstract base class for model providers."""

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
