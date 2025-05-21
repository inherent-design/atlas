"""
Mock model provider implementation for Atlas.

This module provides a mock provider for testing without API access.
It simulates the behavior of real providers (like Anthropic, OpenAI, and Ollama)
without making actual API calls.
"""

import logging
import random
import threading
import time
from collections.abc import Iterator
from typing import Any
from uuid import uuid4

from atlas.core.telemetry import traced

# Import the new provider abstractions
from atlas.providers.base import ModelProvider
from atlas.providers.errors import ProviderError, ProviderTimeoutError
from atlas.providers.messages import (
    CostEstimate,
    ModelRequest,
    ModelResponse,
    TokenUsage,
)
from atlas.providers.reliability import ProviderCircuitBreaker, ProviderRetryConfig
from atlas.providers.streaming.base import StreamHandler

logger = logging.getLogger(__name__)


class MockStreamHandler(StreamHandler):
    """Mock stream handler for testing streaming capabilities."""

    def __init__(
        self,
        provider: "MockProvider",
        model: str,
        initial_response: ModelResponse,
        chunks: list[str],
        delay: float = 0.1,
        error_after: int | None = None,
    ):
        """Initialize the mock stream handler.

        Args:
            provider: The provider instance
            model: The model name
            initial_response: Initial response to be updated
            chunks: List of content chunks to stream
            delay: Time delay between chunks in seconds
            error_after: If set, raise an error after this many chunks
        """
        content = ""  # Initial content is empty
        super().__init__(content, provider, model, initial_response)
        self.chunks = chunks
        self.delay = delay
        self.error_after = error_after
        self._done = threading.Event()
        self._thread = None
        self._position = 0
        self._buffer = []
        self._buffer_lock = threading.Lock()
        self._position_lock = threading.Lock()  # Lock for protecting the position variable
        self.iterator = None

    def get_iterator(self) -> Iterator:
        """Get an iterator for the stream.

        Returns:
            An iterator that yields chunks of the content.
        """
        # Ensure cost is calculated at end of stream
        if self._done.is_set() and not self.response.cost and self.response.usage:
            # Calculate final cost if not already set
            if hasattr(self.provider, "calculate_cost"):
                try:
                    self.response.cost = self.provider.calculate_cost(
                        self.response.usage, self.model
                    )
                except Exception as cost_err:
                    logger.debug(f"Error calculating final streaming cost in mock: {cost_err}")
        return self

    def __iter__(self) -> "MockStreamHandler":
        """Make the handler iterable for processing in a for loop."""
        with self._position_lock:
            self._position = 0
        return self

    def __next__(self) -> str:
        """Get the next chunk of content.

        Returns:
            The next chunk of content.

        Raises:
            StopIteration: When the content is exhausted.
        """
        # Check if we're at the end - use position lock for thread safety
        with self._position_lock:
            if self._position >= len(self.chunks):
                raise StopIteration

        # Simulate delay
        time.sleep(self.delay)

        # Check for simulated error
        if self.error_after is not None and self._position >= self.error_after:
            raise ProviderError("Simulated streaming error")

        try:
            # Use position lock to ensure thread safety
            with self._position_lock:
                # Get the next chunk
                chunk = self.chunks[self._position]
                self._position += 1

            # Update response content
            self.response.content += chunk

            return chunk
        except IndexError:
            # Handle case where the index is out of range
            # This can happen if the position was incremented in another thread
            logger.debug(
                f"Index out of range in MockStreamHandler: position {self._position}, chunks length {len(self.chunks)}"
            )
            raise StopIteration

    def start(self) -> None:
        """Start streaming content in a background thread."""
        if self._thread is not None:
            return

        self._thread = threading.Thread(target=self._stream_content)
        self._thread.daemon = True
        self._thread.start()

    def _stream_content(self) -> None:
        """Stream content chunks with simulated delays."""
        try:
            for i, chunk in enumerate(self.chunks):
                # Check if streaming should be stopped
                if self._done.is_set():
                    break

                # Simulate delay
                time.sleep(self.delay)

                # Simulate error if configured
                if self.error_after is not None and i >= self.error_after:
                    raise ProviderError("Simulated streaming error")

                # Add chunk to buffer and update position atomically
                with self._buffer_lock, self._position_lock:
                    self._buffer.append(chunk)
                    self._position += 1

                # Update response content
                self.response.content += chunk

            # Set cost if not already set
            if (
                not self.response.cost
                and self.response.usage
                and hasattr(self.provider, "calculate_cost")
            ):
                try:
                    self.response.cost = self.provider.calculate_cost(
                        self.response.usage, self.model
                    )
                except Exception as cost_err:
                    logger.debug(f"Error calculating streaming cost in mock provider: {cost_err}")

            # Mark as complete
            self._done.set()

        except Exception as e:
            # Record the error and mark as done
            self._error = e
            self._done.set()

    def done(self) -> bool:
        """Check if streaming is complete."""
        return self._done.is_set()

    def read(self) -> str | None:
        """Read the next available chunk."""
        with self._buffer_lock:
            if not self._buffer:
                return None
            return self._buffer.pop(0)

    def read_all(self) -> list[str]:
        """Read all available chunks."""
        with self._buffer_lock:
            chunks = self._buffer.copy()
            self._buffer.clear()
            return chunks

    def wait(self, timeout: float | None = None) -> bool:
        """Wait for streaming to complete.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if streaming completed, False if timed out
        """
        return self._done.wait(timeout)

    def close(self) -> None:
        """Close the stream and clean up resources."""
        self._done.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)


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

    # Default model responses for different types of tests
    DEFAULT_RESPONSES = {
        "standard": "This is a standard mock response from the Atlas framework. I'm designed to simulate provider responses without making actual API calls.",
        "streaming": [
            "This ",
            "is ",
            "a ",
            "streaming ",
            "mock ",
            "response ",
            "from ",
            "the ",
            "Atlas ",
            "framework. ",
            "I'm ",
            "designed ",
            "to ",
            "simulate ",
            "provider ",
            "responses ",
            "without ",
            "making ",
            "actual ",
            "API ",
            "calls.",
        ],
        "error": "ERROR: This is a simulated error response for testing error handling.",
    }

    # Default retry and circuit breaker configuration
    DEFAULT_RETRY_CONFIG = ProviderRetryConfig(
        max_retries=3,
        initial_delay=0.5,
        max_delay=5.0,
        backoff_factor=2.0,
        jitter_factor=0.25,
        retryable_errors=[
            ProviderTimeoutError,
        ],
    )

    DEFAULT_CIRCUIT_BREAKER = ProviderCircuitBreaker(
        failure_threshold=5, recovery_timeout=30.0, test_requests=1, reset_timeout=300.0
    )

    def __init__(
        self,
        model_name: str = "mock-standard",
        api_key: str | None = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        response_format: str = "standard",
        error_rate: float = 0.0,
        latency: float = 0.5,
        streaming_delay: float = 0.1,
        retry_config: ProviderRetryConfig | None = None,
        circuit_breaker: ProviderCircuitBreaker | None = None,
    ):
        """Initialize the mock provider.

        Args:
            model_name: The name of the model to use
            api_key: Optional API key (not used in mock)
            max_tokens: Maximum tokens to generate
            temperature: Temperature parameter
            response_format: Type of response to generate (standard, streaming, error)
            error_rate: Probability of simulating an error (0.0-1.0)
            latency: Simulated API latency in seconds
            streaming_delay: Delay between streaming chunks in seconds
            retry_config: Optional retry configuration
            circuit_breaker: Optional circuit breaker configuration
        """
        super().__init__(
            retry_config=retry_config or self.DEFAULT_RETRY_CONFIG,
            circuit_breaker=circuit_breaker or self.DEFAULT_CIRCUIT_BREAKER,
        )

        self._model_name = model_name or "mock-standard"
        self._api_key = api_key or "mock-api-key"
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.response_format = response_format
        self.error_rate = max(0.0, min(1.0, error_rate))  # Clamp to 0.0-1.0
        self.latency = max(0.0, latency)  # Ensure non-negative
        self.streaming_delay = max(0.01, streaming_delay)  # Minimum 10ms

        # Validate model name
        if self.model_name not in self.AVAILABLE_MODELS:
            logger.warning(f"Unknown mock model: {self.model_name}, defaulting to mock-standard")
            self._model_name = "mock-standard"

        # Additional internal state
        self._request_count = 0
        self._error_count = 0
        self._token_count = 0

    @property
    def name(self) -> str:
        """Get the provider name."""
        return "mock"

    @traced(name="mock_provider_generate")
    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from the mock provider.

        Args:
            request: The model request

        Returns:
            Model response with mock content

        Raises:
            ProviderError: If a simulated error occurs
        """
        # Simulate API latency
        time.sleep(self.latency)

        # Increment request counter
        self._request_count += 1

        # Simulate random errors based on error_rate
        if self.error_rate > 0.0 and random.random() < self.error_rate:
            self._error_count += 1
            raise ProviderError(f"Simulated error from MockProvider (error #{self._error_count})")

        # Calculate token usage
        input_tokens = len(str(request.messages)) // 4  # Very rough approximation
        output_tokens = self.max_tokens // 2  # Simulate using half of max_tokens
        self._token_count += input_tokens + output_tokens

        # Create the response based on requested format
        if self.response_format == "error":
            raise ProviderError("Simulated error response")

        # Generate response content
        content = self.DEFAULT_RESPONSES["standard"]

        # Create token usage directly to avoid validation recursion
        usage = TokenUsage.create_direct(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

        # Create and return response directly to avoid validation recursion
        return ModelResponse.create_direct(
            provider="mock",
            model=self.model_name,
            content=content,
            usage=usage,
            raw_response={
                "provider": "mock",
                "model": self.model_name,
                "request_id": str(uuid4()),
                "mock_request_count": self._request_count,
                "mock_token_count": self._token_count,
            },
        )

    @traced(name="mock_provider_stream")
    def generate_stream(self, request: ModelRequest) -> tuple[ModelResponse, StreamHandler]:
        """Generate a streaming response from the mock provider.

        Args:
            request: The model request

        Returns:
            Tuple of initial response and stream handler

        Raises:
            ProviderError: If a simulated error occurs
        """
        # Simulate API latency
        time.sleep(self.latency)

        # Increment request counter
        self._request_count += 1

        # Simulate random errors based on error_rate
        if self.error_rate > 0.0 and random.random() < self.error_rate:
            self._error_count += 1
            raise ProviderError(f"Simulated error from MockProvider (error #{self._error_count})")

        # Calculate token usage
        input_tokens = len(str(request.messages)) // 4  # Very rough approximation
        output_tokens = self.max_tokens // 2  # Simulate using half of max_tokens
        self._token_count += input_tokens + output_tokens

        # Create token usage directly to avoid validation recursion
        usage = TokenUsage.create_direct(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

        # Create initial response directly to avoid validation recursion
        initial_response = ModelResponse.create_direct(
            provider="mock",
            model=self.model_name,
            content="",  # Empty initial content, will be updated during streaming
            usage=usage,
            raw_response={
                "provider": "mock",
                "model": self.model_name,
                "request_id": str(uuid4()),
                "mock_request_count": self._request_count,
                "mock_token_count": self._token_count,
                "streaming": True,
            },
        )

        # Get content chunks for streaming
        chunks = self.DEFAULT_RESPONSES["streaming"]

        # Create and return stream handler
        handler = MockStreamHandler(
            provider=self,
            model=self.model_name,
            initial_response=initial_response,
            chunks=chunks,
            delay=self.streaming_delay,
            error_after=None,  # No simulated streaming error by default
        )

        # Start streaming in background
        handler.start()

        return initial_response, handler

    def get_available_models(self) -> list[str]:
        """Get a list of available models.

        Returns:
            List of available mock model names
        """
        return self.AVAILABLE_MODELS.copy()

    def validate_api_key(self) -> bool:
        """Validate the API key.

        Mock provider always returns True since no real API key is used.

        Returns:
            True, always
        """
        return True

    def validate_api_key_detailed(self) -> dict[str, Any]:
        """Validate the API key with detailed information.

        Mock provider always returns a valid result.

        Returns:
            Dict with validation information
        """
        return {"valid": True, "provider": "mock", "key_present": True, "error": None}

    def calculate_token_usage(self, request: ModelRequest, response: Any) -> TokenUsage:
        """Calculate token usage for a request and response.

        For mock provider, this provides estimated token usage.

        Args:
            request: The model request
            response: The raw response (ignored in mock implementation)

        Returns:
            TokenUsage object
        """
        # Simple approximation of token usage
        input_tokens = len(str(request.messages)) // 4
        output_tokens = len(str(response)) // 4 if response else 0

        return TokenUsage.create_direct(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

    def calculate_cost(self, usage: TokenUsage, model: str) -> CostEstimate:
        """Calculate cost for token usage.

        Args:
            usage: Token usage information
            model: The model name

        Returns:
            CostEstimate object
        """
        # Get pricing for the model, or use default
        pricing = self.PRICING.get(model, self.PRICING["default"])

        # Calculate costs
        input_cost = (usage.input_tokens / 1000000) * pricing["input"]
        output_cost = (usage.output_tokens / 1000000) * pricing["output"]

        return CostEstimate.create_direct(
            input_cost=input_cost, output_cost=output_cost, total_cost=input_cost + output_cost
        )

    def get_capability_strength(self, capability: str) -> "CapabilityStrength":
        """Get the capability strength for the current model.

        Args:
            capability: The capability name

        Returns:
            CapabilityStrength enum value
        """
        # Import here to avoid circular import
        from atlas.providers.capabilities import CapabilityStrength

        # Mock capability mappings
        capability_map = {
            "mock-basic": {
                "inexpensive": 3,  # Strong
                "efficient": 3,  # Strong
                "standard": 2,  # Moderate
                "streaming": 2,  # Moderate
            },
            "mock-standard": {
                "inexpensive": 1,  # Basic
                "efficient": 2,  # Moderate
                "standard": 2,  # Moderate
                "streaming": 2,  # Moderate
            },
            "mock-advanced": {
                "premium": 2,  # Moderate
                "vision": 2,  # Moderate
                "standard": 2,  # Moderate
                "streaming": 3,  # Strong
            },
        }

        # Get capability map for current model
        model_caps = capability_map.get(self.model_name, {})

        # Get integer strength or 0 if not found
        strength_int = model_caps.get(capability, 0)

        # Convert to enum
        return CapabilityStrength(strength_int)
