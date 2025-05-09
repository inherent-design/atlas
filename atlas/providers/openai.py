"""
OpenAI provider implementation for Atlas.

This module provides integration with OpenAI's language models.
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
    import openai
    from openai import OpenAI
    from openai.types.chat import ChatCompletionMessage
    from openai import OpenAIError

    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI SDK not installed. Install with 'uv add openai'")
    OPENAI_AVAILABLE = False


class OpenAIProvider(ModelProvider):
    """OpenAI language model provider implementation."""

    # Current OpenAI pricing per million tokens (as of May 2025)
    # These should be moved to a configuration file in the future
    PRICING = {
        # Latest models (GPT-4.1 series)
        "gpt-4.1": {"input": 2.0, "output": 8.0},  # $2.00/M input, $8.00/M output
        "gpt-4.1-mini": {"input": 0.4, "output": 1.6},  # $0.40/M input, $1.60/M output
        "gpt-4.1-nano": {"input": 0.1, "output": 0.4},  # $0.10/M input, $0.40/M output
        
        # OpenAI o-series reasoning models
        "o3": {"input": 10.0, "output": 40.0},  # $10.00/M input, $40.00/M output
        "o4-mini": {"input": 1.1, "output": 4.4},  # $1.10/M input, $4.40/M output
        
        # GPT-4o series
        "gpt-4o": {"input": 5.0, "output": 20.0},  # $5.00/M input, $20.00/M output
        "gpt-4o-mini": {"input": 0.6, "output": 2.4},  # $0.60/M input, $2.40/M output
        
        # Legacy models
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},  # $10.00/M input, $30.00/M output
        "gpt-4": {"input": 30.0, "output": 60.0},  # $30.00/M input, $60.00/M output
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},  # $0.50/M input, $1.50/M output
        
        # Fallback pricing for unknown models
        "default": {"input": 5.0, "output": 20.0},  # Using GPT-4o pricing as default
    }

    def __init__(
        self,
        model_name: str = "gpt-4.1",  # Default to latest GPT-4.1 model
        max_tokens: int = 2000,
        api_key: Optional[str] = None,
        organization: Optional[str] = None,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        **kwargs: Any,
    ):
        """Initialize the OpenAI provider.

        Args:
            model_name: Name of the OpenAI model to use.
            max_tokens: Maximum tokens for model generation.
            api_key: Optional API key (defaults to OPENAI_API_KEY environment variable).
            organization: Optional organization ID.
            retry_config: Optional custom retry configuration.
            circuit_breaker: Optional custom circuit breaker.
            **kwargs: Additional provider-specific parameters.

        Raises:
            ValidationError: If the OpenAI API key is missing or the SDK is not installed.
        """
        # Initialize base ModelProvider with retry configuration
        super().__init__(retry_config=retry_config, circuit_breaker=circuit_breaker)
        
        self._model_name = model_name
        self._max_tokens = max_tokens
        self._additional_params = kwargs or {}

        # Check if OpenAI is available
        if not OPENAI_AVAILABLE:
            raise ValidationError(
                message="OpenAI SDK is not installed",
                severity=ErrorSeverity.ERROR,
            )

        # Get API key from env module
        self._api_key = api_key or env.get_api_key("openai")

        # Get organization from env module
        self._organization = organization or env.get_string("OPENAI_ORGANIZATION")

        # Check for API key
        if not self._api_key:
            raise ValidationError(
                message="OpenAI API key not provided and OPENAI_API_KEY not set",
                severity=ErrorSeverity.ERROR,
            )

        # Initialize client
        client_kwargs = {"api_key": self._api_key}
        if self._organization:
            client_kwargs["organization"] = self._organization

        self._client = OpenAI(**client_kwargs)
        logger.debug(f"Initialized OpenAI provider with model {model_name}")

    @property
    def name(self) -> str:
        """Get the name of the provider.

        Returns:
            The provider's name as a string.
        """
        return "openai"

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
            self._api_key = env.get_api_key("openai")

        # Check if the key is now set
        if not self._api_key:
            logger.warning("No OpenAI API key found")
            return False

        # Make a minimal API call to validate the key
        try:
            # Define validation function to keep the try-except block small
            def validate_with_api_call() -> bool:
                # Create a temporary client with the key (in case our client isn't initialized yet)
                if not hasattr(self, "_client") or self._client is None:
                    client_kwargs = {"api_key": self._api_key}
                    if self._organization:
                        client_kwargs["organization"] = self._organization
                    self._client = OpenAI(**client_kwargs)

                # Make a minimal API call that won't consume many tokens
                response = self._client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Use cheapest model for validation
                    max_tokens=1,  # Minimize token usage
                    messages=[
                        {"role": "system", "content": "Respond with one letter only."},
                        {"role": "user", "content": "Say A"},
                    ],
                )

                # If we get here, the key is valid
                return True

            # Use our safe execution wrapper
            result = safe_execute(
                validate_with_api_call,
                default=False,
                error_msg="Failed to validate OpenAI API key",
                error_cls=AuthenticationError,
                log_error=True,
            )

            if result:
                logger.info("OpenAI API key validated successfully")

            return result

        except Exception as e:
            if isinstance(e, openai.AuthenticationError):
                # Create a standardized authentication error
                auth_error = AuthenticationError(
                    message=f"OpenAI API key is invalid: {str(e)}",
                    cause=e,
                    severity=ErrorSeverity.ERROR,
                    provider="openai",
                    details={"api_key_present": bool(self._api_key)},
                )
                auth_error.log()
            else:
                # Log unexpected errors
                logger.error(
                    f"Unexpected error validating OpenAI API key: {str(e)}",
                    exc_info=True,
                )

            return False

    def get_available_models(self) -> List[str]:
        """Get a list of available models for this provider.

        Returns:
            A list of model identifiers.
        """
        try:
            # Use safe_execute to handle potential errors
            def fetch_models():
                # Get models from API
                models = self._client.models.list()
                model_ids = [model.id for model in models.data]

                # Filter to only include chat models
                chat_models = [
                    model_id for model_id in model_ids if "gpt" in model_id.lower()
                ]

                return chat_models

            # Use safe execution to handle errors
            models = safe_execute(
                fetch_models,
                default=[
                    "gpt-4o",
                    "gpt-4-turbo",
                    "gpt-4",
                    "gpt-3.5-turbo",
                ],
                error_msg="Failed to get available models from OpenAI API",
                error_cls=APIError,
                log_error=True,
            )

            return models

        except Exception as e:
            logger.warning(f"Failed to get available models from OpenAI API: {e}")
            # Return default models
            return [
                # Latest models (GPT-4.1 series)
                "gpt-4.1",
                "gpt-4.1-mini",
                "gpt-4.1-nano",
                
                # OpenAI o-series reasoning models
                "o3",
                "o4-mini",
                
                # GPT-4o series
                "gpt-4o",
                "gpt-4o-mini",
                
                # Legacy models
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo",
            ]

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from the model.

        Args:
            request: The model request.

        Returns:
            A ModelResponse containing the generated content and metadata.

        Raises:
            APIError: If there is an error with the API call.
        """
        # Ensure client is initialized
        if not hasattr(self, "_client") or self._client is None:
            if not self._api_key:
                self._api_key = env.get_api_key("openai")

            if not self._api_key:
                raise ValidationError(
                    message="OpenAI API key not provided and OPENAI_API_KEY not set",
                    severity=ErrorSeverity.ERROR,
                )

            if self._api_key:
                client_kwargs = {"api_key": self._api_key}
                if self._organization:
                    client_kwargs["organization"] = self._organization
                self._client = OpenAI(**client_kwargs)

        # Convert the request to OpenAI format
        openai_request = request.to_provider_request("openai")

        # Add model and max_tokens if not specified
        model = request.model or self._model_name
        openai_request["model"] = model
        openai_request["max_tokens"] = request.max_tokens or self._max_tokens

        # Add any additional parameters from initialization
        for key, value in self._additional_params.items():
            if key not in openai_request:
                openai_request[key] = value

        logger.debug(f"Calling OpenAI API with model {model}")

        # Define a function for the API call
        def make_api_call() -> ModelResponse:
            # Make the API call
            response = self._client.chat.completions.create(**openai_request)

            # Extract content
            content = response.choices[0].message.content

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
                finish_reason=response.choices[0].finish_reason,
                raw_response=response.model_dump(),
            )

        # Error handler for API errors - transforms OpenAI errors to Atlas errors
        def api_error_handler(e: Exception) -> Optional[Exception]:
            # Handle OpenAI-specific errors
            if isinstance(e, openai.AuthenticationError):
                return AuthenticationError(
                    message=f"Authentication error calling OpenAI API: {e}",
                    cause=e,
                    provider="openai",
                    retry_possible=False,
                    severity=ErrorSeverity.ERROR,
                )

            # Handle rate limiting and server errors
            if isinstance(e, openai.RateLimitError):
                return APIError(
                    message=f"Rate limit exceeded calling OpenAI API: {e}",
                    cause=e,
                    retry_possible=True,
                    severity=ErrorSeverity.WARNING,
                    status_code=429,
                )

            if isinstance(e, openai.APIStatusError):
                status_code = getattr(e, "status_code", 500)
                retry_possible = status_code in (500, 502, 503, 504)
                return APIError(
                    message=f"OpenAI API error: {e}",
                    cause=e,
                    details={"status_code": status_code},
                    retry_possible=retry_possible,
                    severity=ErrorSeverity.WARNING if retry_possible else ErrorSeverity.ERROR,
                    status_code=status_code,
                )

            # Handle network errors
            if isinstance(e, (TimeoutError, ConnectionError)):
                return APIError(
                    message=f"Network error calling OpenAI API: {e}",
                    cause=e,
                    retry_possible=True,
                    severity=ErrorSeverity.WARNING,
                )

            # General API errors
            return APIError(
                message=f"Error calling OpenAI API: {e}", 
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
            logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
            raise  # Re-raise the error after logging it

    def calculate_token_usage(self, request: ModelRequest, response: Any) -> TokenUsage:
        """Calculate token usage for a request and response.

        Args:
            request: The model request.
            response: The raw response from the OpenAI API.

        Returns:
            A TokenUsage object with token counts.
        """
        # Extract usage from the response
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens

        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=response.usage.total_tokens,
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
        # Ensure client is initialized
        if not hasattr(self, "_client") or self._client is None:
            if not self._api_key:
                self._api_key = env.get_api_key("openai")

            if not self._api_key:
                raise ValidationError(
                    message="OpenAI API key not provided and OPENAI_API_KEY not set",
                    severity=ErrorSeverity.ERROR,
                )

            if self._api_key:
                client_kwargs = {"api_key": self._api_key}
                if self._organization:
                    client_kwargs["organization"] = self._organization
                self._client = OpenAI(**client_kwargs)

        # Convert the request to OpenAI format
        openai_request = request.to_provider_request("openai")

        # Add model and max_tokens if not specified
        model = request.model or self._model_name
        openai_request["model"] = model
        openai_request["max_tokens"] = request.max_tokens or self._max_tokens
        openai_request["stream"] = True

        # Add any additional parameters from initialization
        for key, value in self._additional_params.items():
            if key not in openai_request:
                openai_request[key] = value

        logger.debug(f"Calling OpenAI API with streaming for model {model}")

        # Define function for API call
        def create_stream():
            # Create the streaming response
            stream = self._client.chat.completions.create(**openai_request)

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

        # Error handler for API errors - transforms OpenAI errors to Atlas errors
        def stream_error_handler(e: Exception) -> Optional[Exception]:
            # Handle OpenAI-specific errors
            if isinstance(e, openai.AuthenticationError):
                return AuthenticationError(
                    message=f"Authentication error in OpenAI streaming API: {e}",
                    cause=e,
                    provider="openai",
                    retry_possible=False,
                    severity=ErrorSeverity.ERROR,
                )

            # Handle rate limiting and server errors
            if isinstance(e, openai.RateLimitError):
                return APIError(
                    message=f"Rate limit exceeded in OpenAI streaming API: {e}",
                    cause=e,
                    retry_possible=True,
                    severity=ErrorSeverity.WARNING,
                    status_code=429,
                )

            if isinstance(e, openai.APIStatusError):
                status_code = getattr(e, "status_code", 500)
                retry_possible = status_code in (500, 502, 503, 504)
                return APIError(
                    message=f"OpenAI streaming API error: {e}",
                    cause=e,
                    details={"status_code": status_code},
                    retry_possible=retry_possible,
                    severity=ErrorSeverity.WARNING if retry_possible else ErrorSeverity.ERROR,
                    status_code=status_code,
                )

            # Handle network errors
            if isinstance(e, (TimeoutError, ConnectionError)):
                return APIError(
                    message=f"Network error calling OpenAI streaming API: {e}",
                    cause=e,
                    retry_possible=True,
                    severity=ErrorSeverity.WARNING,
                )

            # General API errors
            return APIError(
                message=f"Error calling OpenAI streaming API: {e}", 
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
                f"Error calling OpenAI API for streaming: {e}", exc_info=True
            )
            raise  # Re-raise the error after logging it

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


class StreamHandler:
    """Handler for processing OpenAI streaming responses."""

    def __init__(self, stream, provider, model, initial_response):
        """Initialize the stream handler.

        Args:
            stream: The OpenAI stream object.
            provider: The OpenAIProvider instance.
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
                    hasattr(chunk, "choices")
                    and len(chunk.choices) > 0
                    and hasattr(chunk.choices[0], "delta")
                    and hasattr(chunk.choices[0].delta, "content")
                    and chunk.choices[0].delta.content is not None
                ):
                    delta = chunk.choices[0].delta.content
                    self.full_text += delta
                    self.response.content = self.full_text

                # Check if this is the final chunk
                if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                    # Check for finish reason
                    if chunk.choices[0].finish_reason is not None:
                        self.finished = True
                        self.response.finish_reason = chunk.choices[0].finish_reason

                # Check for usage information
                if hasattr(chunk, "usage") and chunk.usage is not None:
                    input_tokens = chunk.usage.prompt_tokens
                    output_tokens = chunk.usage.completion_tokens
                    total_tokens = chunk.usage.total_tokens

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

            # For OpenAI, we might not get usage in the stream, so do a final calculation
            if not self.usage and self.full_text:
                # Rough estimate: ~4 characters per token for output
                output_tokens = len(self.full_text) // 4
                self.usage = TokenUsage(
                    input_tokens=0,  # We don't know this without querying OpenAI
                    output_tokens=output_tokens,
                    total_tokens=output_tokens,  # Also imprecise
                )
                self.response.usage = self.usage

                # Calculate and update cost (as an estimate)
                cost = self.provider.calculate_cost(self.usage, self.model)
                self.response.cost = cost

            return self.response

        # Error handler for stream processing errors
        def stream_error_handler(e: Exception) -> Optional[Exception]:
            # General API errors with potential retry
            retry_possible = isinstance(e, (TimeoutError, ConnectionError))
            return APIError(
                message=f"Error processing OpenAI stream: {e}", 
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