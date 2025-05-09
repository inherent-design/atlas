"""
Anthropic provider implementation for Atlas.

This module provides integration with Anthropic's Claude language models.
"""

import logging
import threading
from typing import List, Dict, Any, Optional, Tuple, Union, Iterator, Callable

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
)
from atlas.core.retry import RetryConfig, CircuitBreaker

logger = logging.getLogger(__name__)

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    logger.warning("Anthropic SDK not installed. Install with 'uv add anthropic'")
    ANTHROPIC_AVAILABLE = False


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

    def __init__(
        self,
        model_name: str = "claude-3-7-sonnet-20250219",
        max_tokens: int = 2000,
        api_key: Optional[str] = None,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        **kwargs: Any,
    ):
        """Initialize the Anthropic provider.

        Args:
            model_name: Name of the Claude model to use.
            max_tokens: Maximum tokens for model generation.
            api_key: Optional API key (defaults to ANTHROPIC_API_KEY environment variable).
            retry_config: Optional custom retry configuration.
            circuit_breaker: Optional custom circuit breaker.
            **kwargs: Additional provider-specific parameters.

        Raises:
            ValidationError: If the Anthropic API key is missing or the SDK is not installed.
        """
        # Initialize base ModelProvider with retry configuration
        super().__init__(retry_config=retry_config, circuit_breaker=circuit_breaker)
        
        self._model_name = model_name
        self._max_tokens = max_tokens
        self._additional_params = kwargs or {}

        # Check if Anthropic is available
        if not ANTHROPIC_AVAILABLE:
            raise ValidationError(
                message="Anthropic SDK is not installed",
                severity=ErrorSeverity.ERROR,
            )

        # Get API key from env module
        self._api_key = api_key or env.get_api_key("anthropic")

        # Validate API key is present
        if not self._api_key:
            raise ValidationError(
                message="Anthropic API key not provided and ANTHROPIC_API_KEY not set",
                severity=ErrorSeverity.ERROR,
            )

        # Initialize client
        self._client = anthropic.Anthropic(api_key=self._api_key)
        logger.debug(f"Initialized Anthropic provider with model {model_name}")

    @property
    def model_name(self) -> str:
        """Get the name of the model.

        Returns:
            The model name as a string.
        """
        return self._model_name

    @property
    def name(self) -> str:
        """Get the name of the provider.

        Returns:
            The provider's name as a string.
        """
        return "anthropic"

    def validate_api_key(self) -> bool:
        """Validate that the API key is set and valid by making a test API call.

        Returns:
            True if the API key is valid, False otherwise.

        Raises:
            AuthenticationError: If the API key is invalid.
        """
        # Use env module to check for API key
        if not self._api_key:
            # Try to get API key from environment
            self._api_key = env.get_api_key("anthropic")

        # Check if the key is now set
        if not self._api_key:
            logger.warning("No Anthropic API key found")
            return False

        # Make a minimal API call to validate the key
        try:
            # Define validation function to keep the try-except block small
            def validate_with_api_call() -> bool:
                # Create a temporary client with the key (in case our client isn't initialized yet)
                if not hasattr(self, "_client") or self._client is None:
                    self._client = anthropic.Anthropic(api_key=self._api_key)

                # Make a minimal API call that won't consume many tokens
                response = self._client.messages.create(
                    model="claude-3-haiku-20240307",  # Use cheapest model for validation
                    max_tokens=1,  # Minimize token usage
                    system="Respond with one letter only.",
                    messages=[{"role": "user", "content": "Say A"}],
                )

                # If we get here, the key is valid
                return True

            # Use our safe execution wrapper
            result = safe_execute(
                validate_with_api_call,
                default=False,
                error_msg="Failed to validate Anthropic API key",
                error_cls=AuthenticationError,
                log_error=True,
            )

            if result:
                logger.info("Anthropic API key validated successfully")

            return result

        except Exception as e:
            if hasattr(anthropic, "AuthenticationError") and isinstance(
                e, anthropic.AuthenticationError
            ):
                # Create a standardized authentication error
                auth_error = AuthenticationError(
                    message=f"Anthropic API key is invalid: {str(e)}",
                    cause=e,
                    severity=ErrorSeverity.ERROR,
                    provider="anthropic",
                    details={"api_key_present": bool(self._api_key)},
                )
                auth_error.log()
            else:
                # Log unexpected errors
                logger.error(
                    f"Unexpected error validating Anthropic API key: {str(e)}",
                    exc_info=True,
                )

            return False

    def get_available_models(self) -> List[str]:
        """Get a list of available models for this provider.

        Returns:
            A list of model identifiers.
        """
        # This is a static list as Anthropic doesn't provide an API for this yet
        return [
            # Latest models
            "claude-3-7-sonnet-20250219",
            "claude-3-5-sonnet-20240620",
            "claude-3-5-haiku-20240620",
            "claude-3-opus-20240229",
            
            # Legacy models
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from the model.

        Args:
            request: The model request.

        Returns:
            A ModelResponse containing the generated content and metadata.

        Raises:
            ValidationError: If the API key is missing.
            APIError: If there is an issue with the API call.
        """
        # Ensure client is initialized
        if not hasattr(self, "_client") or self._client is None:
            if not self._api_key:
                self._api_key = env.get_api_key("anthropic")

            if not self._api_key:
                raise ValidationError(
                    message="Anthropic API key not provided and ANTHROPIC_API_KEY not set",
                    severity=ErrorSeverity.ERROR,
                )

            self._client = anthropic.Anthropic(api_key=self._api_key)

        # Convert the request to Anthropic format
        anthropic_request = request.to_provider_request("anthropic")

        # Add model and max_tokens if not specified
        model = request.model or self._model_name
        anthropic_request["model"] = model
        anthropic_request["max_tokens"] = request.max_tokens or self._max_tokens

        # Add any additional parameters from initialization
        for key, value in self._additional_params.items():
            if key not in anthropic_request:
                anthropic_request[key] = value

        logger.debug(f"Calling Anthropic API with model {model}")

        # Define a function for the API call for use with safe_execute
        def make_api_call() -> ModelResponse:
            # Make the API call
            response = self._client.messages.create(**anthropic_request)

            # Extract content
            content = response.content[0].text

            # Calculate token usage
            usage = self.calculate_token_usage(request, response)

            # Calculate cost
            cost = self.calculate_cost(usage, model)

            # Create the response
            return ModelResponse(
                content=content,
                model=model,
                provider=self.name,
                usage=usage,
                cost=cost,
                finish_reason=response.stop_reason,
                raw_response=response.model_dump(),
            )

        # Error handler for API errors - transforms Anthropic errors to Atlas errors
        def api_error_handler(e: Exception) -> Optional[Exception]:
            # Determine if the error is an authentication issue
            if hasattr(anthropic, "AuthenticationError") and isinstance(
                e, anthropic.AuthenticationError
            ):
                return AuthenticationError(
                    message=f"Authentication error calling Anthropic API: {e}",
                    cause=e,
                    provider="anthropic",
                    retry_possible=False,
                    severity=ErrorSeverity.ERROR,
                )

            # Handle rate limiting and server errors
            if hasattr(anthropic, "RateLimitError") and isinstance(
                e, anthropic.RateLimitError
            ):
                return APIError(
                    message=f"Rate limit exceeded calling Anthropic API: {e}",
                    cause=e,
                    retry_possible=True,
                    severity=ErrorSeverity.WARNING,
                    details={"status_code": 429},
                )

            if hasattr(anthropic, "APIStatusError") and isinstance(
                e, anthropic.APIStatusError
            ):
                status_code = getattr(e, "status_code", 500)
                retry_possible = status_code in (500, 502, 503, 504)
                return APIError(
                    message=f"Anthropic API error: {e}",
                    cause=e,
                    details={"status_code": status_code},
                    retry_possible=retry_possible,
                    severity=ErrorSeverity.WARNING if retry_possible else ErrorSeverity.ERROR,
                )

            # Handle network errors
            if isinstance(e, (TimeoutError, ConnectionError)):
                return APIError(
                    message=f"Network error calling Anthropic API: {e}",
                    cause=e,
                    retry_possible=True,
                    severity=ErrorSeverity.WARNING,
                )

            # General API errors
            return APIError(
                message=f"Error calling Anthropic API: {e}", 
                cause=e,
                retry_possible=False,
                severity=ErrorSeverity.ERROR,
            )

        # Execute the API call with retry mechanism
        try:
            return self.safe_execute_with_retry(
                make_api_call,
                error_handler=api_error_handler,
            )
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {e}", exc_info=True)
            raise  # Re-raise the error after logging it

    def calculate_token_usage(self, request: ModelRequest, response: Any) -> TokenUsage:
        """Calculate token usage for a request and response.

        Args:
            request: The model request.
            response: The raw response from the Anthropic API.

        Returns:
            A TokenUsage object with token counts.
        """
        # Extract usage from the response
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
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
            A tuple of (final ModelResponse, StreamHandler).

        Raises:
            ValidationError: If the API key is missing.
            APIError: If there is an issue with the API call.
        """
        # Ensure client is initialized
        if not hasattr(self, "_client") or self._client is None:
            if not self._api_key:
                self._api_key = env.get_api_key("anthropic")

            if not self._api_key:
                raise ValidationError(
                    message="Anthropic API key not provided and ANTHROPIC_API_KEY not set",
                    severity=ErrorSeverity.ERROR,
                )

            self._client = anthropic.Anthropic(api_key=self._api_key)

        # Convert the request to Anthropic format
        anthropic_request = request.to_provider_request("anthropic")

        # Add model and max_tokens if not specified
        model = request.model or self._model_name
        anthropic_request["model"] = model
        anthropic_request["max_tokens"] = request.max_tokens or self._max_tokens
        anthropic_request["stream"] = True

        # Add any additional parameters from initialization
        for key, value in self._additional_params.items():
            if key not in anthropic_request:
                anthropic_request[key] = value

        logger.debug(f"Calling Anthropic API with streaming for model {model}")

        # Define function for API call to use with safe_execute
        def create_stream():
            # Create the streaming response
            stream = self._client.messages.create(**anthropic_request)

            # Create an initial response object that will be updated
            initial_response = ModelResponse(
                content="",  # Will be populated during streaming
                model=model,
                provider=self.name,
                usage=TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0),
                cost=CostEstimate(input_cost=0.0, output_cost=0.0, total_cost=0.0),
                finish_reason=None,
                raw_response={},
            )

            return initial_response, StreamHandler(
                stream, self, model, initial_response
            )

        # Error handler for API errors
        def stream_error_handler(e: Exception) -> Optional[Exception]:
            # Authentication errors
            if hasattr(anthropic, "AuthenticationError") and isinstance(
                e, anthropic.AuthenticationError
            ):
                return AuthenticationError(
                    message=f"Authentication error in Anthropic streaming API: {e}",
                    cause=e,
                    provider="anthropic",
                    retry_possible=False,
                    severity=ErrorSeverity.ERROR,
                )

            # Handle rate limiting and server errors
            if hasattr(anthropic, "RateLimitError") and isinstance(
                e, anthropic.RateLimitError
            ):
                return APIError(
                    message=f"Rate limit exceeded in Anthropic streaming API: {e}",
                    cause=e,
                    retry_possible=True,
                    severity=ErrorSeverity.WARNING,
                    details={"status_code": 429},
                )

            if hasattr(anthropic, "APIStatusError") and isinstance(
                e, anthropic.APIStatusError
            ):
                status_code = getattr(e, "status_code", 500)
                retry_possible = status_code in (500, 502, 503, 504)
                return APIError(
                    message=f"Anthropic streaming API error: {e}",
                    cause=e,
                    details={"status_code": status_code},
                    retry_possible=retry_possible,
                    severity=ErrorSeverity.WARNING if retry_possible else ErrorSeverity.ERROR,
                )

            # Handle network errors
            if isinstance(e, (TimeoutError, ConnectionError)):
                return APIError(
                    message=f"Network error calling Anthropic streaming API: {e}",
                    cause=e,
                    retry_possible=True,
                    severity=ErrorSeverity.WARNING,
                )

            # General API errors
            return APIError(
                message=f"Error calling Anthropic streaming API: {e}", 
                cause=e,
                retry_possible=False,
                severity=ErrorSeverity.ERROR,
            )

        # Execute the API call with retry mechanism
        try:
            result: Tuple[ModelResponse, "StreamHandler"] = self.safe_execute_with_retry(
                create_stream,
                error_handler=stream_error_handler,
            )
            return result
        except Exception as e:
            logger.error(
                f"Error calling Anthropic API for streaming: {e}", exc_info=True
            )
            raise  # Re-raise the error after logging it

    def stream_with_callback(self, request: ModelRequest, callback) -> ModelResponse:
        """Stream a response from the model and process it with a callback.

        Args:
            request: The model request.
            callback: Function taking (delta, response) parameters called for each chunk.

        Returns:
            The final ModelResponse after processing the entire stream.

        Raises:
            ValueError: If there is an error with the API call.
        """
        _, stream_handler = self.stream(request)
        return stream_handler.process_stream(callback)


class StreamHandler:
    """Handler for processing Anthropic streaming responses."""

    def __init__(self, stream, provider, model, initial_response):
        """Initialize the stream handler.

        Args:
            stream: The Anthropic stream object.
            provider: The AnthropicProvider instance.
            model: The model being used.
            initial_response: The initial ModelResponse object to update.
        """
        self.stream = stream
        self.provider = provider
        self.model = model
        self.response = initial_response
        self.full_text = ""
        self.event_count = 0
        self.finished = False
        self.usage = None
        self._lock = threading.Lock()

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

        # Define a function to process a chunk safely
        def process_chunk(chunk):
            with self._lock:
                self.event_count += 1

                # Extract content delta if present
                delta = ""
                if (
                    hasattr(chunk, "delta")
                    and hasattr(chunk.delta, "text")
                    and chunk.delta.text
                ):
                    delta = chunk.delta.text
                    self.full_text += delta
                    self.response.content = self.full_text
                elif (
                    hasattr(chunk, "content")
                    and chunk.content
                    and len(chunk.content) > 0
                ):
                    # Handle the case where content is provided directly
                    for content_item in chunk.content:
                        if hasattr(content_item, "text") and content_item.text:
                            delta = content_item.text
                            self.full_text += delta
                            self.response.content = self.full_text

                # Check if this is the final chunk
                if hasattr(chunk, "type") and chunk.type == "message_stop":
                    self.finished = True

                    # Get usage information if available
                    if hasattr(chunk, "usage"):
                        input_tokens = chunk.usage.input_tokens
                        output_tokens = chunk.usage.output_tokens
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

                    # Update finish reason if available
                    if hasattr(chunk, "stop_reason"):
                        self.response.finish_reason = chunk.stop_reason

                return delta, self.response

        try:
            # Get the next chunk from the stream
            chunk = next(self.stream)

            # Process the chunk with error handling
            try:
                return process_chunk(chunk)
            except Exception as chunk_error:
                error = APIError(
                    message=f"Error processing stream chunk: {chunk_error}",
                    cause=chunk_error,
                    severity=ErrorSeverity.WARNING,
                )
                error.log()
                # Return empty delta but keep the response updated
                return "", self.response

        except StopIteration:
            self.finished = True
            raise
        except Exception as stream_error:
            logger.error(
                f"Error getting next chunk from stream: {stream_error}", exc_info=True
            )
            self.finished = True
            # Convert to a more friendly StopIteration to avoid breaking client code
            raise StopIteration

    def process_stream(self, callback=None):
        """Process the entire stream, optionally calling a callback for each chunk.

        Args:
            callback: Optional function taking (delta, response) parameters
                     to call for each chunk of the stream.

        Returns:
            The final ModelResponse after processing the entire stream.
        """

        # Stream processing function for safe_execute
        def process_stream_safely():
            # Process all chunks in the stream
            for delta, response in self:
                if callback and delta:
                    try:
                        callback(delta, response)
                    except Exception as callback_error:
                        logger.error(f"Error in stream callback: {callback_error}")
                        # Continue processing even if callback fails

            return self.response

        # Error handler for stream processing errors
        def stream_error_handler(e: Exception) -> Optional[Exception]:
            # General API errors with potential retry
            retry_possible = isinstance(e, (TimeoutError, ConnectionError))
            return APIError(
                message=f"Error processing Anthropic stream: {e}", 
                cause=e,
                retry_possible=retry_possible,
                severity=ErrorSeverity.WARNING if retry_possible else ErrorSeverity.ERROR,
            )

        # Execute with retry mechanism from the provider
        result = self.provider.safe_execute_with_retry(
            process_stream_safely,
            error_handler=stream_error_handler,
            default_value=self.response,  # Return partial response on all errors
        )

        return result
