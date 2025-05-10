"""
Mock model provider implementation for Atlas.

This module provides a mock provider for testing without API access.
It simulates the behavior of real providers (like Anthropic, OpenAI, and Ollama)
without making actual API calls.
"""

import logging
import threading
import time
from typing import List, Dict, Any, Optional, Tuple, Union, Iterator, Callable
from uuid import uuid4

from atlas.core.telemetry import traced, TracedClass
from atlas.core import env
from atlas.core.errors import (
    APIError,
    AuthenticationError,
    ValidationError,
    ErrorSeverity,
    safe_execute,
)
from atlas.providers.base import (
    ModelProvider,
    ModelRequest,
    ModelResponse,
    TokenUsage,
    CostEstimate,
    StreamHandler as BaseStreamHandler,
)

logger = logging.getLogger(__name__)


class MockProvider(ModelProvider):
    """Mock provider for testing without API access."""

    # Mock pricing per million tokens for cost calculation demonstration
    PRICING = {
        "mock-basic": {"input": 0.5, "output": 1.5},  # $0.50/M input, $1.50/M output
        "mock-standard": {"input": 3.0, "output": 15.0},  # $3.00/M input, $15.00/M output
        "mock-advanced": {"input": 10.0, "output": 30.0},  # $10.00/M input, $30.00/M output
        # Fallback pricing for unknown models
        "default": {"input": 3.0, "output": 15.0},
    }

    # Available mock models
    AVAILABLE_MODELS = [
        "mock-basic",
        "mock-standard",
        "mock-advanced",
    ]

    def __init__(
        self,
        model_name: str = "mock-standard",
        max_tokens: int = 2000,
        api_key: Optional[str] = None,
        delay_ms: int = 100,  # Simulated latency in milliseconds
        **kwargs: Any,
    ):
        """Initialize the mock provider.

        Args:
            model_name: Name of the mock model to use.
            max_tokens: Maximum tokens for model generation.
            api_key: Optional API key (for API signature compatibility).
            delay_ms: Simulated latency in milliseconds.
            **kwargs: Additional provider-specific parameters.
        """
        self._model_name = model_name
        self._max_tokens = max_tokens
        self._delay_ms = delay_ms
        self._additional_params = kwargs or {}

        # Set a mock API key if one was provided (just for testing)
        self._api_key = api_key or "mock-api-key"

        logger.debug(f"Initialized mock provider with model {model_name}")

    @property
    def name(self) -> str:
        """Get the name of the provider.

        Returns:
            The provider's name as a string.
        """
        return "mock"

    def validate_api_key(self) -> bool:
        """Validate that the API key is valid.

        Returns:
            Always returns True as this is a mock provider.
        """
        logger.info("Mock provider API key validation - always returns True")
        return True

    def get_available_models(self) -> List[str]:
        """Get a list of available models for this provider.

        Returns:
            A list of model identifiers.
        """
        return self.AVAILABLE_MODELS

    def _simulate_delay(self) -> None:
        """Simulate network latency for API calls."""
        if self._delay_ms > 0:
            time.sleep(self._delay_ms / 1000.0)

    def _generate_mock_response(
        self, request: ModelRequest, streaming: bool = False
    ) -> Dict[str, Any]:
        """Generate a mock response based on the request.

        Args:
            request: The model request.
            streaming: Whether this is for a streaming response.

        Returns:
            A dictionary containing the mock response data.
        """
        # Get the first user message content for response generation
        user_message = None
        for message in request.messages:
            if message.role.value == "user":
                if isinstance(message.content, str):
                    user_message = message.content
                    break
                else:
                    # Handle complex content types
                    user_message = str(message.content)
                    break

        # If no user message found, use a default
        if not user_message:
            user_message = "No user message provided."

        # Determine the length of the response based on request parameters
        response_length = min(
            len(user_message) * 2,  # Base length on input
            request.max_tokens or self._max_tokens,  # Respect max tokens
        )

        # Generate a mock response content
        if streaming:
            # For streaming, we'll return a minimal response to start
            content = ""
        else:
            # For non-streaming, generate a full response
            model_prefix = self._model_name.replace("mock-", "").capitalize()
            content = f"This is a {model_prefix} mock response to: {user_message[:50]}"
            content += "..." if len(user_message) > 50 else ""
            content += "\n\nThe mock provider generates synthetic responses without making actual API calls."
            content += "\nThis is useful for testing without incurring API costs."

        # Simulate token calculation based on content length
        # A simple approximation: 1 token ≈ 4 characters
        input_tokens = len("".join([str(m.content) for m in request.messages])) // 4
        output_tokens = len(content) // 4 if not streaming else 0
        total_tokens = input_tokens + output_tokens

        # Simulate API response structure
        mock_response = {
            "id": f"mock-{uuid4()}",
            "content": content,
            "model": self._model_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "finish_reason": "stop" if not streaming else None,
        }

        return mock_response

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from the model.

        Args:
            request: The model request.

        Returns:
            A ModelResponse containing the generated content and metadata.
        """
        # Use the model specified in the request or the default
        model = request.model or self._model_name

        # Define a function for mocking API call
        def make_mock_api_call() -> ModelResponse:
            # Simulate network latency
            self._simulate_delay()

            # Generate a mock response
            mock_response = self._generate_mock_response(request)

            # Extract content and token usage
            content = mock_response["content"]
            usage = TokenUsage(
                input_tokens=mock_response["input_tokens"],
                output_tokens=mock_response["output_tokens"],
                total_tokens=mock_response["total_tokens"],
            )

            # Calculate cost
            cost = self.calculate_cost(usage, model)

            # Create the response
            return ModelResponse(
                content=content,
                model=model,
                provider=self.name,
                usage=usage,
                cost=cost,
                finish_reason=mock_response["finish_reason"],
                raw_response=mock_response,
            )

        # Execute with error handling
        try:
            # Simulate possible API errors if configured
            if self._additional_params.get("simulate_errors", False):
                error_type = self._additional_params.get("error_type", "api")
                if error_type == "authentication":
                    raise AuthenticationError(
                        message="Simulated authentication error",
                        provider=self.name,
                        severity=ErrorSeverity.ERROR,
                    )
                elif error_type == "validation":
                    raise ValidationError(
                        message="Simulated validation error",
                        severity=ErrorSeverity.ERROR,
                    )
                else:
                    raise APIError(
                        message="Simulated API error",
                        severity=ErrorSeverity.ERROR,
                        retry_possible=True,
                    )

            return make_mock_api_call()
        except Exception as e:
            logger.error(f"Error generating mock response: {e}", exc_info=True)
            raise

    def calculate_token_usage(self, request: ModelRequest, response: Any) -> TokenUsage:
        """Calculate token usage for a request and response.

        Args:
            request: The model request.
            response: The raw response from the mock API.

        Returns:
            A TokenUsage object with token counts.
        """
        input_tokens = response.get("input_tokens", 0)
        output_tokens = response.get("output_tokens", 0)
        total_tokens = response.get("total_tokens", input_tokens + output_tokens)

        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )

    def calculate_cost(self, usage: TokenUsage, model: str) -> CostEstimate:
        """Calculate approximate cost based on token usage.

        Args:
            usage: Token usage statistics.
            model: The model used for the request.

        Returns:
            A CostEstimate with input, output, and total costs.
        """
        # Get pricing for the model
        pricing = self.PRICING.get(model, self.PRICING["default"])

        # Calculate costs per million tokens
        input_cost = (usage.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (usage.output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost

        return CostEstimate(
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
        )

    def stream(self, request: ModelRequest) -> Tuple[ModelResponse, "StreamHandler"]:
        """Stream a response from the model.

        Args:
            request: The model request.

        Returns:
            A tuple of (initial ModelResponse, StreamHandler).

        Raises:
            APIError: If there is an error with the API call.
        """
        # Use the model specified in the request or the default
        model = request.model or self._model_name

        # Define function for creating a stream
        def create_stream():
            # Generate initial mock response for streaming
            mock_response = self._generate_mock_response(request, streaming=True)

            # Create an initial response object that will be updated
            initial_response = ModelResponse(
                content="",  # Will be populated during streaming
                model=model,
                provider=self.name,
                usage=TokenUsage(
                    input_tokens=mock_response["input_tokens"],
                    output_tokens=0,  # Will be updated during streaming
                    total_tokens=mock_response["input_tokens"],  # Will be updated
                ),
                cost=CostEstimate(
                    input_cost=0.0, output_cost=0.0, total_cost=0.0
                ),  # Will be updated
                finish_reason=None,  # Will be updated during streaming
                raw_response=mock_response,
            )

            # Generate mock text to stream
            user_message = None
            for message in request.messages:
                if message.role.value == "user":
                    if isinstance(message.content, str):
                        user_message = message.content
                        break
                    else:
                        user_message = str(message.content)
                        break

            if not user_message:
                user_message = "No user message provided."

            model_prefix = self._model_name.replace("mock-", "").capitalize()
            stream_text = f"This is a {model_prefix} mock response to: {user_message[:50]}"
            stream_text += "..." if len(user_message) > 50 else ""
            stream_text += "\n\nThe mock provider generates synthetic responses without making actual API calls."
            stream_text += "\nThis is useful for testing without incurring API costs."

            # Create a stream handler with the text to stream
            return initial_response, StreamHandler(
                stream_text, self, model, initial_response, self._delay_ms
            )

        # Simulate possible API errors if configured
        if self._additional_params.get("simulate_errors", False):
            error_type = self._additional_params.get("error_type", "api")
            if error_type == "authentication":
                raise AuthenticationError(
                    message="Simulated authentication error in streaming API",
                    provider=self.name,
                    severity=ErrorSeverity.ERROR,
                )
            elif error_type == "validation":
                raise ValidationError(
                    message="Simulated validation error in streaming API",
                    severity=ErrorSeverity.ERROR,
                )
            else:
                raise APIError(
                    message="Simulated API error in streaming API",
                    severity=ErrorSeverity.ERROR,
                    retry_possible=True,
                )

        return create_stream()

    def stream_with_callback(
        self, request: ModelRequest, callback: Callable[[str, ModelResponse], None]
    ) -> ModelResponse:
        """Stream a response from the model and process it with a callback.

        Args:
            request: The model request.
            callback: Function taking (delta, response) parameters called for each chunk.

        Returns:
            The final ModelResponse after processing the entire stream.

        Raises:
            APIError: If there is an error with the API call.
        """
        _, stream_handler = self.stream(request)
        return stream_handler.process_stream(callback)


# StreamHandler already imported as BaseStreamHandler

class StreamHandler(BaseStreamHandler):
    """Handler for processing mock streaming responses."""

    def __init__(
        self, text_to_stream, provider, model, initial_response, delay_ms=50
    ):
        """Initialize the stream handler.

        Args:
            text_to_stream: The text to stream in chunks.
            provider: The MockProvider instance.
            model: The model being used.
            initial_response: The initial ModelResponse object to update.
            delay_ms: Simulated delay between chunks in milliseconds.
        """
        super().__init__(
            content="",  # Will be populated as we stream
            provider=provider,
            model=model,
            initial_response=initial_response,
            delay_ms=delay_ms
        )

        self.text_to_stream = text_to_stream
        self.full_text = ""
        self.event_count = 0
        self.finished = False
        self.usage = None
        self._lock = threading.Lock()

        # Word chunks to stream - simulates how real providers stream
        self.chunks = self.text_to_stream.split()
        self.current_chunk_index = 0

    def get_iterator(self):
        """Get an iterator for the stream.

        Returns:
            An iterator that yields chunks of the content.
        """
        return self

    def __iter__(self):
        """Make the handler iterable for processing in a for loop."""
        return self

    def __next__(self):
        """Process the next stream event.

        Returns:
            A tuple of (delta, ModelResponse) where delta is the new content.

        Raises:
            StopIteration: When the stream is exhausted.
        """
        if self.finished:
            raise StopIteration

        # Simulate network delay
        time.sleep(self._delay_ms / 1000.0)

        with self._lock:
            self.event_count += 1

            # Check if we've reached the end of the stream
            if self.current_chunk_index >= len(self.chunks):
                self.finished = True
                self._finalize_response()
                raise StopIteration

            # Get the next chunk (usually a word or punctuation)
            delta = self.chunks[self.current_chunk_index]
            
            # Add a space if not first chunk and not punctuation
            if self.current_chunk_index > 0 and delta not in ",.!?;:":
                delta = " " + delta
                
            self.current_chunk_index += 1
            
            # Update the full text and response
            self.full_text += delta
            self.response.content = self.full_text

            return delta, self.response

    def _finalize_response(self):
        """Update the final response with metadata and token usage."""
        # Calculate token usage based on final content
        # Using a simple approximation: 1 token ≈ 4 characters
        input_tokens = self.response.usage.input_tokens
        output_tokens = len(self.full_text) // 4
        total_tokens = input_tokens + output_tokens

        # Update usage information
        self.usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )
        self.response.usage = self.usage

        # Calculate and update cost
        cost = self.provider.calculate_cost(self.usage, self.model)
        self.response.cost = cost

        # Update finish reason
        self.response.finish_reason = "stop"

    def process_stream(self, callback=None):
        """Process the entire stream, optionally calling a callback for each chunk.

        Args:
            callback: Optional function taking (delta, response) parameters
                     to call for each chunk of the stream.

        Returns:
            The final ModelResponse after processing the entire stream.
        """
        # Process the stream
        for delta, response in self:
            if callback and delta:
                try:
                    callback(delta, response)
                except Exception as callback_error:
                    logger.error(f"Error in stream callback: {callback_error}")
                    # Continue processing even if callback fails

        return self.response