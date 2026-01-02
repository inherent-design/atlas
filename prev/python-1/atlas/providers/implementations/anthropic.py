"""
Anthropic provider implementation for Atlas.

This module provides integration with Anthropic's Claude language models.
"""

import logging
import threading
import time
from collections.abc import Callable, Iterator
from typing import Any

from atlas.core import env
from atlas.core.errors import (
    ValidationError,
)
from atlas.core.telemetry import traced

# Import the new provider abstractions
from atlas.providers.base import ModelProvider
from atlas.providers.errors import (
    ProviderAuthenticationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderServerError,
    ProviderTimeoutError,
    ProviderValidationError,
)
from atlas.providers.messages import (
    CostEstimate,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TokenUsage,
)
from atlas.providers.reliability import ProviderCircuitBreaker, ProviderRetryConfig
from atlas.providers.streaming.base import StreamHandler
from atlas.providers.streaming.control import StreamState

logger = logging.getLogger(__name__)

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    logger.warning("Anthropic SDK not installed. Install with 'uv add anthropic'")
    ANTHROPIC_AVAILABLE = False


class AnthropicStreamHandler(StreamHandler):
    """Stream handler for Anthropic Claude API responses."""

    def __init__(
        self,
        provider: "AnthropicProvider",
        model: str,
        initial_response: ModelResponse,
        iterator: Iterator[Any],
        request_id: str,
    ):
        """Initialize the Anthropic stream handler.

        Args:
            provider: The provider instance
            model: The model name
            initial_response: Initial response to be updated
            iterator: Iterator of response chunks from Anthropic API
            request_id: Request ID from Anthropic API
        """
        # Use Any as an intermediate type to avoid direct casting
        provider_for_handler: Any = provider

        super().__init__(
            content="",
            provider=provider_for_handler,
            model=model,
            initial_response=initial_response,
        )
        self.iterator = iterator
        self.request_id = request_id

        # State tracking
        self._thread: threading.Thread | None = None
        self._buffer_lock = threading.RLock()
        self._done = threading.Event()
        self._content_buffer: list[str] = []
        self._current_content: str = ""
        self._state = StreamState.INITIALIZING

        # Metrics tracking
        self._chunk_count: int = 0
        self._start_time: float | None = None
        self._end_time: float | None = None

        # Initialize metrics attribute
        self._metrics: dict[str, Any] = {}

    def start(self) -> None:
        """Start streaming content in a background thread."""
        if self._thread is not None:
            return

        self._thread = threading.Thread(target=self._stream_content)
        self._thread.daemon = True
        self._start_time = time.time()
        self._thread.start()

    def _stream_content(self) -> None:
        """Stream content chunks from the Anthropic API."""
        try:
            for chunk in self.iterator:
                # Check if streaming should stop - use a lock to prevent race conditions
                with self._buffer_lock:  # Using buffer_lock as a general state lock
                    if self._state == StreamState.CANCELLED:
                        logger.debug(f"Cancelling Anthropic stream for request {self.request_id}")
                        should_break = True
                    else:
                        should_break = False

                    # Skip processing if paused, but keep consuming to keep connection alive
                    if self._state == StreamState.PAUSED:
                        should_continue = True
                    else:
                        should_continue = False

                # Apply the decision outside of the lock to minimize lock contention
                if should_break:
                    break
                if should_continue:
                    continue

                # Process the chunk
                if hasattr(chunk, "delta") and hasattr(chunk.delta, "text"):
                    # Extract text content from chunk
                    content = chunk.delta.text
                    if content:
                        # Add to buffer
                        with self._buffer_lock:
                            self._content_buffer.append(content)
                            self._current_content += content

                        # Update the response content
                        self.response.content = self._current_content

                        # Track metrics
                        self._chunk_count += 1

                # Update usage information if available
                try:
                    if hasattr(chunk, "usage") and chunk.usage is not None:
                        usage = chunk.usage

                        # Use the new from_provider_response method for consistent extraction
                        self.response.usage = TokenUsage.from_provider_response(
                            response=chunk, provider_name="anthropic"
                        )

                        # Calculate and set cost estimate based on updated usage
                        if self.response.usage and hasattr(self.provider, "calculate_cost"):
                            try:
                                self.response.cost = self.provider.calculate_cost(
                                    self.response.usage, self.model
                                )
                            except Exception as cost_err:
                                logger.debug(f"Error calculating streaming cost: {cost_err}")
                except Exception as usage_err:
                    logger.debug(f"Error processing usage in chunk: {usage_err}")

            # Set cost one final time if needed
            if (
                self.response.usage
                and not self.response.cost
                and hasattr(self.provider, "calculate_cost")
            ):
                try:
                    self.response.cost = self.provider.calculate_cost(
                        self.response.usage, self.model
                    )
                    logger.debug(f"Set final cost in _stream_content: {self.response.cost}")
                except Exception as cost_err:
                    logger.debug(f"Error calculating final streaming cost: {cost_err}")

            # Mark as complete when done - with proper locking
            self._end_time = time.time()
            with self._buffer_lock:
                self._state = StreamState.COMPLETED
            self._done.set()

        except Exception as e:
            # Record the error and mark as done - with proper locking
            self._error = e
            with self._buffer_lock:
                self._state = StreamState.ERROR
            self._done.set()
            logger.error(f"Error in Anthropic stream: {e}")

    def read(self) -> str | None:
        """Read the next available chunk from the buffer."""
        with self._buffer_lock:
            if not self._content_buffer:
                return None
            return self._content_buffer.pop(0)

    def read_all(self) -> list[str]:
        """Read all available chunks from the buffer."""
        with self._buffer_lock:
            chunks = self._content_buffer.copy()
            self._content_buffer.clear()
            return chunks

    def close(self) -> None:
        """Close the stream and clean up resources."""
        with self._buffer_lock:
            self._state = StreamState.CANCELLED

        if hasattr(self.iterator, "close"):
            try:
                self.iterator.close()
            except Exception as e:
                logger.warning(f"Error closing Anthropic stream: {e}")

        self._done.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    @property
    def state(self) -> StreamState:
        """Get the current state of the stream."""
        with self._buffer_lock:
            return self._state

    def pause(self) -> bool:
        """Pause the stream.

        Returns:
            True if the stream was paused, False otherwise.
        """
        with self._buffer_lock:
            if self._state == StreamState.ACTIVE:
                self._state = StreamState.PAUSED
                return True
            return False

    def resume(self) -> bool:
        """Resume the stream.

        Returns:
            True if the stream was resumed, False otherwise.
        """
        with self._buffer_lock:
            if self._state == StreamState.PAUSED:
                self._state = StreamState.ACTIVE
                return True
            return False

    def cancel(self) -> bool:
        """Cancel the stream.

        Returns:
            True if the stream was cancelled, False otherwise.
        """
        with self._buffer_lock:
            self._state = StreamState.CANCELLED

        self.close()
        return True

    @property
    def metrics(self) -> dict[str, Any]:
        """Get stream metrics."""
        # Initialize base metrics
        metrics = self._metrics.copy() if hasattr(self, "_metrics") else {}

        # Calculate duration if both start and end times are available
        duration = None
        if (
            hasattr(self, "_start_time")
            and hasattr(self, "_end_time")
            and self._start_time is not None
            and self._end_time is not None
        ):
            duration = self._end_time - self._start_time

        # Add Anthropic-specific metrics
        metrics.update(
            {
                "chunk_count": getattr(self, "_chunk_count", 0),
                "duration": duration,
                "request_id": getattr(self, "request_id", "unknown"),
            }
        )

        return metrics

    def process_stream(
        self, callback: Callable[[str, "ModelResponse"], None] | None = None
    ) -> "ModelResponse":
        """Process the entire stream with a callback function.

        Args:
            callback: Function to call for each chunk of content.

        Returns:
            The final response after processing the entire stream.
        """
        # Use the parent implementation first
        response = super().process_stream(callback)

        # After stream is complete, ensure usage and cost are set
        try:
            # If no usage data was received in streaming, estimate based on content
            if not response.usage or (
                response.usage.input_tokens == 0 and response.usage.output_tokens == 0
            ):
                # Get input token count from request if available
                input_tokens = 0
                if hasattr(self, "request") and hasattr(self.request, "messages"):
                    input_text = " ".join(str(msg.content) for msg in self.request.messages)
                    # Estimate based on text length - ~4 chars per token
                    input_tokens = len(input_text) // 4

                # Estimate output tokens based on content length
                output_tokens = len(response.content) // 4 if hasattr(response, "content") else 0

                logger.debug(
                    f"Estimating token usage for stream: {input_tokens} input, {output_tokens} output"
                )

                # Create token usage directly
                response.usage = TokenUsage.create_direct(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=input_tokens + output_tokens,
                )

            # Ensure cost is calculated if we have usage
            if response.usage and (
                not response.cost
                or (response.cost.input_cost == 0 and response.cost.output_cost == 0)
            ):
                if hasattr(self.provider, "calculate_cost"):
                    try:
                        response.cost = self.provider.calculate_cost(response.usage, self.model)
                        logger.debug(f"Calculated final cost in process_stream: {response.cost}")
                    except Exception as cost_err:
                        logger.debug(f"Error calculating final cost in process_stream: {cost_err}")
        except Exception as usage_err:
            logger.debug(f"Error handling final usage/cost calculation: {usage_err}")

        return response

    def get_iterator(self) -> Iterator[str | tuple[str, ModelResponse]]:
        """Get an iterator for the stream.

        Returns:
            An iterator that yields chunks of the content.

        Raises:
            ProviderStreamError: If the iterator is not initialized.
        """
        # Instead of consuming the self.iterator directly, we'll read from our buffer
        # which is populated by the _stream_content method in the background thread
        # This prevents "generator already executing" errors

        while not self._done.is_set() or self._content_buffer:
            try:
                chunk = self.read()
                if chunk:
                    # When we're done and this is the last chunk, ensure cost is calculated
                    try:
                        if (
                            self._done.is_set()
                            and len(self._content_buffer) == 0
                            and hasattr(self.response, "usage")
                            and self.response.usage
                            and (not hasattr(self.response, "cost") or not self.response.cost)
                        ):
                            # Calculate final cost if not already set
                            if hasattr(self.provider, "calculate_cost"):
                                try:
                                    self.response.cost = self.provider.calculate_cost(
                                        self.response.usage, self.model
                                    )
                                    logger.debug(f"Set cost in get_iterator: {self.response.cost}")
                                except Exception as cost_err:
                                    logger.debug(
                                        f"Error calculating final streaming cost in get_iterator: {cost_err}"
                                    )
                    except Exception as check_err:
                        logger.debug(f"Error checking final chunk status: {check_err}")

                    yield chunk
                else:
                    time.sleep(0.01)  # Small sleep to prevent CPU spinning
            except Exception as iter_err:
                logger.error(f"Error in stream iterator: {iter_err}")
                time.sleep(0.01)  # Sleep to prevent CPU spinning even on errors


class AnthropicProvider(ModelProvider):
    """Anthropic Claude language model provider implementation."""

    # Current Anthropic pricing per million tokens (as of the latest update - May 2025)
    # These should be moved to a configuration file in the future
    PRICING = {
        # Latest models
        "claude-3-7-sonnet-20250219": {
            "input": 3.0,
            "output": 15.0,
        },  # $3.00/M input, $15.00/M output
        "claude-3-5-sonnet-20240620": {
            "input": 3.0,
            "output": 15.0,
        },  # $3.00/M input, $15.00/M output
        "claude-3-5-haiku-20240620": {
            "input": 0.80,
            "output": 4.0,
        },  # $0.80/M input, $4.00/M output
        "claude-3-opus-20240229": {
            "input": 15.0,
            "output": 75.0,
        },  # $15.00/M input, $75.00/M output
        # Legacy models
        "claude-3-sonnet-20240229": {
            "input": 3.0,
            "output": 15.0,
        },  # $3.00/M input, $15.00/M output
        "claude-3-haiku-20240307": {
            "input": 0.25,
            "output": 1.25,
        },  # $0.25/M input, $1.25/M output
        # Fallback pricing for unknown models
        "default": {"input": 3.0, "output": 15.0},
    }

    def _should_retry_request(self, request: ModelRequest) -> bool:
        """Determine if a request should be retried based on circuit breaker state and retry policy.

        Args:
            request: The model request.

        Returns:
            Boolean indicating if retry is possible.
        """
        # Check circuit breaker state first
        if (
            hasattr(self, "circuit_breaker")
            and hasattr(self.circuit_breaker, "is_open")
            and self.circuit_breaker.is_open
        ):
            return False

        # Get retry configuration
        if hasattr(self, "retry_config") and self.retry_config:
            # Check if we have remaining retries
            return self.retry_config.max_retries > 0

        return False

    @property
    def models(self) -> list[str]:
        """Get a list of available models for this provider."""
        return self.get_available_models()

    # Default retry and circuit breaker configuration
    DEFAULT_RETRY_CONFIG = ProviderRetryConfig(
        max_retries=3,
        initial_delay=0.5,
        max_delay=5.0,
        backoff_factor=2.0,
        jitter_factor=0.25,
        retryable_errors=[
            ProviderTimeoutError,
            ProviderServerError,
            ProviderRateLimitError,
        ],
    )

    DEFAULT_CIRCUIT_BREAKER = ProviderCircuitBreaker(
        failure_threshold=5,
        recovery_timeout=30.0,
        test_requests=1,
        reset_timeout=300.0,
    )

    def __init__(
        self,
        model_name: str = "claude-3-7-sonnet-20250219",
        max_tokens: int = 2000,
        api_key: str | None = None,
        retry_config: ProviderRetryConfig | None = None,
        circuit_breaker: ProviderCircuitBreaker | None = None,
        options: dict[str, Any] | None = None,
        **kwargs: Any,
    ):
        """Initialize the Anthropic provider.

        Args:
            model_name: Name of the Claude model to use.
            max_tokens: Maximum tokens for model generation.
            api_key: Optional API key (defaults to ANTHROPIC_API_KEY environment variable).
            retry_config: Optional custom retry configuration.
            circuit_breaker: Optional custom circuit breaker.
            options: Optional provider-specific options and capabilities.
            **kwargs: Additional provider-specific parameters.

        Raises:
            ValidationError: If the Anthropic API key is missing, the SDK is not installed,
                            or if the requested model is not compatible.
        """
        super().__init__(
            retry_config=retry_config or self.DEFAULT_RETRY_CONFIG,
            circuit_breaker=circuit_breaker or self.DEFAULT_CIRCUIT_BREAKER,
        )

        # Check if Anthropic SDK is installed
        if not ANTHROPIC_AVAILABLE:
            raise ProviderValidationError(
                "Anthropic SDK not installed. Install with 'uv add anthropic'",
                provider="anthropic",
            )

        # Get API key from environment if not provided
        self.api_key = api_key or env.get_api_key("anthropic")
        if not self.api_key:
            raise ProviderAuthenticationError(
                "Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter.",
                provider="anthropic",
            )

        self._model_name = model_name
        self.max_tokens = max_tokens
        self.api_base = kwargs.get("api_base")

        # Process options dictionary
        self.options = {}
        self.capabilities = {}

        # Apply provider-specific options
        if options:
            try:
                # Import here to avoid circular imports
                from atlas.schemas.options import anthropic_options_schema

                # Validate options using schema
                validated_options = anthropic_options_schema.load(options)

                # Extract capabilities specifically
                if "capabilities" in validated_options:
                    self.capabilities = validated_options.pop("capabilities")

                # Store the rest of the options
                self.options = validated_options
            except ValidationError as e:
                raise ProviderValidationError(
                    f"Invalid Anthropic provider options: {e}",
                    provider="anthropic",
                    details={"validation_errors": e.messages},
                )

        # Apply any other kwargs to options
        for key, value in kwargs.items():
            if key not in ["api_base"]:  # Skip already processed keys
                self.options[key] = value

        # Client will be created lazily when needed
        self._client = None
        self._client_lock = threading.RLock()

    @property
    def name(self) -> str:
        """Get the provider name."""
        return "anthropic"

    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._model_name

    @model_name.setter
    def model_name(self, value: str) -> None:
        """Set the model name."""
        self._model_name = value

    @property
    def client(self) -> "anthropic.Anthropic":
        """Get the Anthropic API client with lazy initialization.

        Returns:
            An initialized Anthropic client.
        """
        # Create client lazily to allow for testing and mocking
        if self._client is None:
            with self._client_lock:
                if self._client is None:
                    client_params = {"api_key": self.api_key}
                    if self.api_base:
                        client_params["base_url"] = self.api_base
                    self._client = anthropic.Anthropic(**client_params)

        return self._client

    def _convert_messages(
        self, messages: list[ModelMessage]
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Convert Atlas message format to Anthropic's format.

        Args:
            messages: List of ModelMessage objects.

        Returns:
            A tuple containing:
            - List of messages in Anthropic's format.
            - System message content if found, otherwise None.

        Note:
            This will extract the system message to be passed as a top-level parameter
            in the Anthropic API, not in the messages array.
        """
        converted_messages = []
        system_message = None

        for message in messages:
            role = message.role.lower()

            # Extract system messages to be handled separately in the Anthropic API
            # (as a top-level parameter, not in the messages array)
            if role == "system":
                # Save the system message content
                if isinstance(message.content, str):
                    system_message = message.content
                elif isinstance(message.content, list):
                    # Join text content if it's a list of content blocks
                    system_parts = []
                    for block in message.content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            system_parts.append(block.get("text", ""))
                        elif isinstance(block, str):
                            system_parts.append(block)
                    if system_parts:
                        system_message = " ".join(system_parts)
                continue

            # Convert role names to Anthropic format
            if role == "user":
                role = "user"
            elif role in ["assistant", "model"]:
                role = "assistant"
            else:
                # Skip unsupported roles
                logger.warning(f"Unsupported role '{role}' for Anthropic, skipping message")
                continue

            # Convert content
            if isinstance(message.content, str):
                content = message.content
                converted_messages.append({"role": role, "content": content})
            elif isinstance(message.content, list):
                # Handle content blocks (like text and images)
                content_blocks = []

                for block in message.content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            content_blocks.append({"type": "text", "text": block.get("text", "")})
                        elif block.get("type") == "image" and "url" in block:
                            # Handle image content
                            content_blocks.append(
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": block.get("media_type", "image/jpeg"),
                                        "data": block.get("url", "").split("base64,", 1)[-1],
                                    },
                                }
                            )
                    elif isinstance(block, str):
                        content_blocks.append({"type": "text", "text": block})

                if content_blocks:
                    converted_messages.append({"role": role, "content": content_blocks})

        return converted_messages, system_message

    @traced(name="anthropic_provider_generate")
    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from the Anthropic API.

        Args:
            request: Model request containing messages and parameters.

        Returns:
            Model response with content and token usage.

        Raises:
            ProviderError: If the API request fails.
        """
        # Check if retry should be triggered
        should_retry = self._should_retry_request(request)

        try:
            # Convert messages to Anthropic format and extract system message
            messages, extracted_system = self._convert_messages(request.messages)

            # Get parameters from request or default
            request_parameters = getattr(request, "parameters", {}) or {}

            # Combine options with precedence: request parameters > instance options > defaults
            max_tokens = request_parameters.get(
                "max_tokens", self.options.get("max_tokens", self.max_tokens)
            )

            temperature = request_parameters.get(
                "temperature", self.options.get("temperature", 0.7)
            )

            # Prepare request parameters
            params = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            # Add additional options from self.options that aren't set above
            for key, value in self.options.items():
                if key not in ["max_tokens", "temperature", "capabilities", "system"]:
                    params[key] = value

            # System prompt precedence:
            # 1. Extracted from messages
            # 2. Explicit system_prompt in request
            # 3. System in options
            system_prompt = extracted_system or request.system_prompt or self.options.get("system")
            if system_prompt:
                params["system"] = system_prompt

            # Make the API request
            response = self.client.messages.create(**params)

            # Extract response content
            content = response.content[0].text if response.content else ""

            # Extract token usage with improved method
            usage = TokenUsage.from_provider_response(response=response, provider_name="anthropic")

            # Calculate cost based on usage
            cost = None
            if usage:
                try:
                    cost = self.calculate_cost(usage, self.model_name)
                except Exception as cost_err:
                    logger.debug(f"Error calculating cost: {cost_err}")

            # Create and return the response using direct method to bypass validation
            return ModelResponse.create_direct(
                provider="anthropic",
                model=self.model_name,
                content=content,
                usage=usage,
                cost=cost,
                raw_response=response.model_dump(),
            )

        except anthropic.APIError as e:
            # Convert Anthropic errors to Atlas errors
            error_message = f"Anthropic API error: {e}"

            details = {
                "status_code": getattr(e, "status_code", None),
                "original_error": str(e),
            }

            if hasattr(e, "status_code"):
                status_code = e.status_code

                # Handle different error types with proper kwargs for each error type
                if status_code == 401:
                    raise ProviderAuthenticationError(error_message, provider="anthropic")
                elif status_code == 429:
                    raise ProviderRateLimitError(
                        error_message,
                        provider="anthropic",
                        retry_after=getattr(e, "retry_after", None),
                        details=details,
                    )
                elif status_code >= 500:
                    raise ProviderServerError(
                        error_message,
                        provider="anthropic",
                        retry_possible=should_retry,
                        details=details,
                    )
                elif status_code == 400:
                    raise ProviderValidationError(
                        error_message, provider="anthropic", details=details
                    )
                elif status_code == 408:
                    raise ProviderTimeoutError(
                        error_message,
                        provider="anthropic",
                        retry_possible=should_retry,
                        details=details,
                    )

            # Default case - generic provider error
            raise ProviderError(
                error_message,
                provider="anthropic",
                retry_possible=should_retry,
                details=details,
                cause=e,
            )
        except Exception as e:
            # Handle generic errors
            error_message = f"Error calling Anthropic API: {e}"
            raise ProviderError(
                error_message,
                provider="anthropic",
                retry_possible=should_retry,
                cause=e,
            )

    @traced(name="anthropic_provider_stream")
    def generate_stream(self, request: ModelRequest) -> tuple[ModelResponse, StreamHandler]:
        """Generate a streaming response from the Anthropic API.

        Args:
            request: Model request containing messages and parameters.

        Returns:
            Tuple of initial response and stream handler.

        Raises:
            ProviderError: If the API request fails.
        """
        # Check if retry should be triggered
        should_retry = self._should_retry_request(request)

        try:
            # Convert messages to Anthropic format and extract system message
            messages, extracted_system = self._convert_messages(request.messages)

            # Get parameters from request or default
            request_parameters = getattr(request, "parameters", {}) or {}

            # Combine options with precedence: request parameters > instance options > defaults
            max_tokens = request_parameters.get(
                "max_tokens", self.options.get("max_tokens", self.max_tokens)
            )

            temperature = request_parameters.get(
                "temperature", self.options.get("temperature", 0.7)
            )

            # Prepare request parameters
            params = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True,
            }

            # Add additional options from self.options that aren't set above
            for key, value in self.options.items():
                if key not in ["max_tokens", "temperature", "capabilities", "stream", "system"]:
                    params[key] = value

            # System prompt precedence:
            # 1. Extracted from messages
            # 2. Explicit system_prompt in request
            # 3. System in options
            system_prompt = extracted_system or request.system_prompt or self.options.get("system")
            if system_prompt:
                params["system"] = system_prompt

            # Make the API request
            stream_response = self.client.messages.create(**params)

            # Create initial response with direct method to bypass validation
            initial_response = ModelResponse.create_direct(
                provider="anthropic",
                model=self.model_name,
                content="",  # Empty initial content, will be updated during streaming
                usage=TokenUsage.create_direct(input_tokens=0, output_tokens=0, total_tokens=0),
                raw_response={
                    "provider": "anthropic",
                    "model": self.model_name,
                    "streaming": True,
                },
            )

            # Create and return stream handler
            request_id = getattr(stream_response, "request_id", "unknown")
            handler = AnthropicStreamHandler(
                provider=self,
                model=self.model_name,
                initial_response=initial_response,
                iterator=stream_response,
                request_id=request_id,
            )

            # Store the request on the handler to ensure input token counting works
            handler.request = request

            # Start streaming in background
            handler.start()

            return initial_response, handler

        except anthropic.APIError as e:
            # Convert Anthropic errors to Atlas errors
            error_message = f"Anthropic API streaming error: {e}"

            details = {
                "status_code": getattr(e, "status_code", None),
                "original_error": str(e),
            }

            if hasattr(e, "status_code"):
                status_code = e.status_code

                # Handle different error types with proper kwargs for each error type
                if status_code == 401:
                    raise ProviderAuthenticationError(error_message, provider="anthropic")
                elif status_code == 429:
                    raise ProviderRateLimitError(
                        error_message,
                        provider="anthropic",
                        retry_after=getattr(e, "retry_after", None),
                        details=details,
                    )
                elif status_code >= 500:
                    raise ProviderServerError(
                        error_message,
                        provider="anthropic",
                        retry_possible=should_retry,
                        details=details,
                    )
                elif status_code == 400:
                    raise ProviderValidationError(
                        error_message, provider="anthropic", details=details
                    )
                elif status_code == 408:
                    raise ProviderTimeoutError(
                        error_message,
                        provider="anthropic",
                        retry_possible=should_retry,
                        details=details,
                    )

            # Default case - generic provider error
            raise ProviderError(
                error_message,
                provider="anthropic",
                retry_possible=should_retry,
                details=details,
                cause=e,
            )
        except Exception as e:
            # Handle generic errors
            error_message = f"Error calling Anthropic API for streaming: {e}"
            raise ProviderError(
                error_message,
                provider="anthropic",
                retry_possible=should_retry,
                cause=e,
            )

    def get_available_models(self) -> list[str]:
        """Get the list of available Anthropic models.

        Returns:
            List of model names.
        """
        return list(self.PRICING.keys())

    @traced(name="anthropic_provider_validate_api_key")
    def validate_api_key(self) -> bool:
        """Validate the Anthropic API key.

        Returns:
            True if the API key is valid, False otherwise.
        """
        try:
            # Perform a simple models.list call to validate the API key
            # Note: As of May 2025, the Anthropic API may not provide a models.list endpoint
            # This is a hypothetical implementation
            response = self.client.models.list()
            return True
        except Exception as e:
            logger.warning(f"Anthropic API key validation failed: {e}")
            return False

    def validate_api_key_detailed(self) -> dict[str, Any]:
        """Validate the API key with detailed information.

        Returns:
            Dict with validation information.
        """
        # Check if key exists
        key_present = bool(self.api_key)

        if not key_present:
            return {
                "valid": False,
                "provider": "anthropic",
                "key_present": False,
                "error": "API key is not set",
            }

        # Try to validate with API
        try:
            # Attempt a simple API call
            valid = self.validate_api_key()

            return {
                "valid": valid,
                "provider": "anthropic",
                "key_present": True,
                "error": None if valid else "API key validation failed",
            }
        except Exception as e:
            return {
                "valid": False,
                "provider": "anthropic",
                "key_present": True,
                "error": str(e),
            }

    def calculate_token_usage(self, request: ModelRequest, response: Any) -> TokenUsage:
        """Calculate token usage for a request and response.

        Args:
            request: The model request.
            response: The raw response from the Anthropic API.

        Returns:
            A TokenUsage object with token counts.
        """
        # Use our improved extraction method
        return TokenUsage.from_provider_response(response=response, provider_name="anthropic")

    def calculate_cost(self, usage: TokenUsage, model: str) -> CostEstimate:
        """Calculate cost for token usage.

        Args:
            usage: Token usage information.
            model: The model name.

        Returns:
            A CostEstimate with input, output, and total costs.
        """
        # Get pricing for the model, or use default
        pricing = self.PRICING.get(model, self.PRICING["default"])

        # Calculate costs per million tokens
        input_cost = (usage.input_tokens / 1000000) * pricing["input"]
        output_cost = (usage.output_tokens / 1000000) * pricing["output"]

        return CostEstimate.create_direct(
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=input_cost + output_cost,
        )

    @traced(name="anthropic_provider_stream")
    def stream(self, request: ModelRequest) -> tuple[ModelResponse, StreamHandler]:
        """Stream a response from the model.

        Args:
            request: The model request with messages and parameters.

        Returns:
            A tuple of (initial_response, stream_handler).
        """
        # Call generate_stream which does the actual work
        return self.generate_stream(request)

    def get_capability_strength(self, capability: str) -> int:
        """Get the capability strength for the current model.

        Args:
            capability: The capability name.

        Returns:
            Capability strength (0-4).
        """
        # First check if this capability is explicitly set in the options capabilities
        if hasattr(self, "capabilities") and capability in self.capabilities:
            cap_value = self.capabilities[capability]
            # If it's an integer enum value, convert to int
            if hasattr(cap_value, "value"):
                return cap_value.value
            # If it's already an int, return it
            elif isinstance(cap_value, int):
                return cap_value
            # Otherwise convert string to int if possible
            elif isinstance(cap_value, str) and cap_value.isdigit():
                return int(cap_value)

        # If not in capabilities or can't convert, use the default model capability map
        capability_map = {
            "claude-3-7-sonnet-20250219": {
                "premium": 3,  # Strong
                "vision": 3,  # Strong
                "standard": 3,  # Strong
                "reasoning": 3,  # Strong
                "code": 3,  # Strong
            },
            "claude-3-5-sonnet-20240620": {
                "premium": 3,  # Strong
                "vision": 3,  # Strong
                "standard": 3,  # Strong
            },
            "claude-3-5-haiku-20240620": {
                "efficient": 3,  # Strong
                "standard": 3,  # Strong
            },
            "claude-3-opus-20240229": {
                "premium": 4,  # Exceptional
                "vision": 3,  # Strong
                "standard": 3,  # Strong
                "reasoning": 4,  # Exceptional
                "code": 3,  # Strong
                "creative": 3,  # Strong
            },
            "claude-3-sonnet-20240229": {
                "premium": 3,  # Strong
                "vision": 3,  # Strong
                "standard": 3,  # Strong
            },
            "claude-3-haiku-20240307": {
                "inexpensive": 3,  # Strong
                "efficient": 3,  # Strong
                "standard": 2,  # Moderate
            },
        }

        # Get capability map for current model
        model_caps = capability_map.get(self.model_name, {})

        # Return capability strength or 0 if not found
        return model_caps.get(capability, 0)
