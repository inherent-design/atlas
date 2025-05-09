"""
Ollama provider implementation for Atlas.

This module provides integration with Ollama for local language model inference.
"""

import logging
import threading
import json
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
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    logger.warning("Requests package not installed. Install with 'uv add requests'")
    REQUESTS_AVAILABLE = False


class OllamaProvider(ModelProvider):
    """Ollama local language model provider implementation."""

    # Default Ollama API endpoint
    DEFAULT_API_ENDPOINT = "http://localhost:11434/api"

    def __init__(
        self,
        model_name: str = "llama3",
        max_tokens: int = 2000,
        api_endpoint: Optional[str] = None,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        **kwargs: Any,
    ):
        """Initialize the Ollama provider.

        Args:
            model_name: Name of the Ollama model to use.
            max_tokens: Maximum tokens for model generation.
            api_endpoint: URL of the Ollama API endpoint.
            retry_config: Optional custom retry configuration.
            circuit_breaker: Optional custom circuit breaker.
            **kwargs: Additional provider-specific parameters.

        Raises:
            ValidationError: If the Requests package is not installed.
        """
        # Initialize base ModelProvider with retry configuration
        super().__init__(retry_config=retry_config, circuit_breaker=circuit_breaker)
        
        # Check if Requests is available
        if not REQUESTS_AVAILABLE:
            raise ValidationError(
                message="Requests package is not installed",
                severity=ErrorSeverity.ERROR,
            )

        self._model_name = model_name
        self._max_tokens = max_tokens
        self._additional_params = kwargs or {}

        # Get API endpoint from env module or use default
        self._api_endpoint = api_endpoint or env.get_string(
            "OLLAMA_API_ENDPOINT", default=self.DEFAULT_API_ENDPOINT
        )

        # Normalize API endpoint (remove trailing slash) - handle possible None
        if self._api_endpoint is not None:
            self._api_endpoint = self._api_endpoint.rstrip("/")
        else:
            self._api_endpoint = self.DEFAULT_API_ENDPOINT

        logger.debug(
            f"Initialized Ollama provider with model {model_name} at {self._api_endpoint}"
        )

    @property
    def name(self) -> str:
        """Get the name of the provider.

        Returns:
            The provider's name as a string.
        """
        return "ollama"

    def validate_api_key(self) -> bool:
        """Validate that the API endpoint is accessible.

        Returns:
            True if the API endpoint is accessible, False otherwise.
        """
        # For Ollama, we're validating server availability rather than an API key
        # Wrap this in safe_execute for consistent error handling
        def check_server_availability() -> bool:
            # Try to get the Ollama version
            response = requests.get(f"{self._api_endpoint}/version", timeout=2)
            if response.status_code == 200:
                logger.info(f"Successfully connected to Ollama server at {self._api_endpoint}")
                return True
            else:
                logger.warning(
                    f"Ollama server responded with status code {response.status_code}"
                )
                return False

        # Use safe execution to handle errors
        result = safe_execute(
            check_server_availability,
            default=False,
            error_msg=f"Failed to connect to Ollama server at {self._api_endpoint}",
            error_cls=APIError,
            log_error=True,
        )

        return result

    def get_available_models(self) -> List[str]:
        """Get a list of available models for this provider.

        Returns:
            A list of model identifiers.
        """
        # Define function for the API call
        def fetch_models() -> List[str]:
            # Get models from API
            response = requests.get(f"{self._api_endpoint}/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            else:
                logger.warning(
                    f"Failed to get models from Ollama API (status code {response.status_code})"
                )
                return ["llama3", "mistral", "gemma"]

        # Use safe execution to handle errors
        models = safe_execute(
            fetch_models,
            default=["llama3", "mistral", "gemma"],  # Default models
            error_msg="Failed to get available models from Ollama API",
            error_cls=APIError,
            log_error=True,
        )

        return models

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from the model.

        Args:
            request: The model request.

        Returns:
            A ModelResponse containing the generated content and metadata.

        Raises:
            APIError: If there is an error with the API call.
        """
        # Ollama doesn't support the ChatML format directly, so we need to convert
        # the request to a prompt string

        # Get the model to use
        model = request.model or self._model_name

        # Build the prompt from messages
        system_content = None
        prompt_parts = []

        # Process the messages to build a prompt Ollama can understand
        def build_prompt() -> Dict[str, Any]:
            nonlocal system_content, prompt_parts

            for message in request.messages:
                role = message.role.value
                if isinstance(message.content, str):
                    content = message.content
                else:
                    # Handle complex content - Ollama only supports text
                    content = (
                        message.content.text
                        if hasattr(message.content, "text")
                        else str(message.content)
                    )

                if role == "system":
                    system_content = content
                elif role == "user":
                    prompt_parts.append(f"User: {content}")
                elif role == "assistant":
                    prompt_parts.append(f"Assistant: {content}")
                elif role == "function":
                    # Ollama doesn't support function calls, so we include them as user messages
                    prompt_parts.append(f"Function ({message.name}): {content}")

            # Add final user prompt if not already included
            if prompt_parts and not prompt_parts[-1].startswith("User:"):
                prompt_parts.append("Assistant:")

            # Build the final prompt
            prompt = "\n\n".join(prompt_parts)

            # Prepare the API request
            api_request = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": request.max_tokens or self._max_tokens,
                },
            }

            # Add system content if available
            if system_content:
                api_request["system"] = system_content

            # Add additional parameters
            if request.temperature is not None:
                api_request["options"]["temperature"] = request.temperature

            # Add any additional parameters from initialization
            for key, value in self._additional_params.items():
                if key not in api_request and key != "options":
                    api_request[key] = value
                elif key == "options":
                    for option_key, option_value in value.items():
                        if option_key not in api_request["options"]:
                            api_request["options"][option_key] = option_value

            return api_request

        # Define a function for the API call for use with safe_execute
        def make_api_call() -> ModelResponse:

            # Build API request
            api_request = build_prompt()
            logger.debug(f"Calling Ollama API with model {model}")

            # Make the actual API call
            response = requests.post(
                f"{self._api_endpoint}/generate",
                json=api_request,
                timeout=60,
            )

            if response.status_code != 200:
                raise APIError(
                    message=f"Ollama API returned status code {response.status_code}: {response.text}",
                    severity=ErrorSeverity.ERROR,
                    details={"status_code": response.status_code, "response": response.text},
                )

            response_data = response.json()

            # Extract content
            content = response_data.get("response", "")

            # Calculate token usage (estimated)
            usage = self.calculate_token_usage(request, response_data)

            # Calculate cost (always 0 for local models)
            cost = self.calculate_cost(usage, model)

            # Create the response
            return ModelResponse(
                content=content,
                model=model,
                provider=self.name,
                usage=usage,
                cost=cost,
                finish_reason=response_data.get("done", True) and "stop" or "unknown",
                raw_response=response_data,
            )

        # Error handler for API errors - transforms specific errors to Atlas errors
        def api_error_handler(e: Exception) -> Optional[Exception]:
            # Handle connection errors
            if isinstance(e, requests.ConnectionError):
                return APIError(
                    message=f"Failed to connect to Ollama server at {self._api_endpoint}: {e}",
                    cause=e,
                    retry_possible=True,
                    severity=ErrorSeverity.ERROR,
                    details={"endpoint": self._api_endpoint},
                )

            # Handle timeout errors
            if isinstance(e, requests.Timeout):
                return APIError(
                    message=f"Timeout connecting to Ollama server: {e}",
                    cause=e,
                    retry_possible=True,
                    severity=ErrorSeverity.WARNING,
                )
                
            # Handle API response errors
            if isinstance(e, APIError) and hasattr(e, "details"):
                status_code = e.details.get("status_code", 500)
                retry_possible = status_code in (500, 502, 503, 504)
                return APIError(
                    message=f"Ollama API error: {e}",
                    cause=e,
                    details={"status_code": status_code, **e.details},
                    retry_possible=retry_possible,
                    severity=ErrorSeverity.WARNING if retry_possible else ErrorSeverity.ERROR,
                )

            # General API errors
            return APIError(
                message=f"Error calling Ollama API: {e}", 
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
            logger.error(f"Error calling Ollama API: {e}", exc_info=True)
            raise  # Re-raise the error after logging it

    def calculate_token_usage(self, request: ModelRequest, response: Any) -> TokenUsage:
        """Calculate token usage for a request and response.

        Args:
            request: The model request.
            response: The raw response from the Ollama API.

        Returns:
            A TokenUsage object with token counts.
        """
        # Ollama doesn't provide token counts in responses, so we estimate
        prompt_tokens = response.get("prompt_eval_count", 0)
        eval_tokens = response.get("eval_count", 0)

        # If prompt tokens is 0, estimate based on character count
        if prompt_tokens == 0 and hasattr(request, "messages") and isinstance(request.messages, list):
            # Rough estimate: ~4 characters per token
            prompt_text = "".join(
                [
                    (
                        str(m.content)
                        if isinstance(m.content, str)
                        else (
                            m.content.text
                            if hasattr(m.content, "text")
                            else str(m.content)
                        )
                    )
                    for m in request.messages
                ]
            )
            prompt_tokens = len(prompt_text) // 4

        # If eval tokens is 0, estimate based on character count
        if eval_tokens == 0 and "response" in response:
            # Rough estimate: ~4 characters per token
            eval_tokens = len(response["response"]) // 4

        return TokenUsage(
            input_tokens=prompt_tokens,
            output_tokens=eval_tokens,
            total_tokens=prompt_tokens + eval_tokens,
        )

    def calculate_cost(self, usage: TokenUsage, model: str) -> CostEstimate:
        """Calculate approximate cost based on token usage.

        For Ollama, this is always 0 as it uses local models.

        Args:
            usage: Token usage statistics.
            model: The model used for the request.

        Returns:
            A CostEstimate with input, output, and total costs (all 0).
        """
        # Local models have no API cost
        return CostEstimate(
            input_cost=0.0,
            output_cost=0.0,
            total_cost=0.0,
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
        # Get the model to use
        model = request.model or self._model_name

        # Build the prompt from messages - similar to generate() method
        system_content = None
        prompt_parts = []

        # Process the messages to build a prompt Ollama can understand
        def build_prompt() -> Dict[str, Any]:
            nonlocal system_content, prompt_parts

            for message in request.messages:
                role = message.role.value
                if isinstance(message.content, str):
                    content = message.content
                else:
                    # Handle complex content - Ollama only supports text
                    content = (
                        message.content.text
                        if hasattr(message.content, "text")
                        else str(message.content)
                    )

                if role == "system":
                    system_content = content
                elif role == "user":
                    prompt_parts.append(f"User: {content}")
                elif role == "assistant":
                    prompt_parts.append(f"Assistant: {content}")
                elif role == "function":
                    prompt_parts.append(f"Function ({message.name}): {content}")

            # Add final user prompt if not already included
            if prompt_parts and not prompt_parts[-1].startswith("User:"):
                prompt_parts.append("Assistant:")

            # Build the final prompt
            prompt = "\n\n".join(prompt_parts)

            # Prepare the API request
            api_request = {
                "model": model,
                "prompt": prompt,
                "stream": True,  # Enable streaming
                "options": {
                    "num_predict": request.max_tokens or self._max_tokens,
                },
            }

            # Add system content if available
            if system_content:
                api_request["system"] = system_content

            # Add additional parameters
            if request.temperature is not None:
                api_request["options"]["temperature"] = request.temperature

            # Add any additional parameters from initialization
            for key, value in self._additional_params.items():
                if key not in api_request and key != "options":
                    api_request[key] = value
                elif key == "options":
                    for option_key, option_value in value.items():
                        if option_key not in api_request["options"]:
                            api_request["options"][option_key] = option_value

            return api_request

        # Define function for API call to use with safe_execute
        def create_stream():

            # Build API request
            api_request = build_prompt()
            logger.debug(f"Calling Ollama API with streaming for model {model}")

            # Make the API call
            response = requests.post(
                f"{self._api_endpoint}/generate",
                json=api_request,
                timeout=60,
                stream=True,
            )

            if response.status_code != 200:
                raise APIError(
                    message=f"Ollama API returned status code {response.status_code}: {response.text}",
                    severity=ErrorSeverity.ERROR,
                    details={"status_code": response.status_code, "response": response.text},
                )

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
                response, self, model, initial_response
            )

        # Error handler for API errors
        def stream_error_handler(e: Exception) -> Optional[Exception]:
            # Handle connection errors
            if isinstance(e, requests.ConnectionError):
                return APIError(
                    message=f"Failed to connect to Ollama server at {self._api_endpoint}: {e}",
                    cause=e,
                    retry_possible=True,
                    severity=ErrorSeverity.ERROR,
                    details={"endpoint": self._api_endpoint},
                )

            # Handle timeout errors
            if isinstance(e, requests.Timeout):
                return APIError(
                    message=f"Timeout connecting to Ollama server: {e}",
                    cause=e,
                    retry_possible=True,
                    severity=ErrorSeverity.WARNING,
                )
                
            # Handle API response errors
            if isinstance(e, APIError) and hasattr(e, "details"):
                status_code = e.details.get("status_code", 500)
                retry_possible = status_code in (500, 502, 503, 504)
                return APIError(
                    message=f"Ollama API streaming error: {e}",
                    cause=e,
                    details={"status_code": status_code, **e.details},
                    retry_possible=retry_possible,
                    severity=ErrorSeverity.WARNING if retry_possible else ErrorSeverity.ERROR,
                )

            # General API errors
            return APIError(
                message=f"Error calling Ollama streaming API: {e}", 
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
                f"Error calling Ollama API for streaming: {e}", exc_info=True
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
    """Handler for processing Ollama streaming responses."""

    def __init__(self, stream, provider, model, initial_response):
        """Initialize the stream handler.

        Args:
            stream: The Ollama stream response object.
            provider: The OllamaProvider instance.
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
        self.line_iter = self.stream.iter_lines(decode_unicode=True)
        self.metadata = {}

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

        try:
            # Get the next line from the stream
            line = next(self.line_iter)

            # Skip empty lines
            if not line:
                return "", self.response

            # Process the JSON response
            try:
                chunk = json.loads(line)
                return self._process_chunk(chunk)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to decode JSON from Ollama stream: {e}")
                return "", self.response

        except StopIteration:
            self.finished = True
            self._finalize_response()
            raise
        except Exception as e:
            logger.error(f"Error processing Ollama stream: {e}", exc_info=True)
            self.finished = True
            self._finalize_response()
            raise StopIteration

    def _process_chunk(self, chunk):
        """Process a chunk from the Ollama stream.

        Args:
            chunk: The chunk data as a Python dict.

        Returns:
            A tuple of (delta, ModelResponse).
        """
        with self._lock:
            self.event_count += 1
            delta = ""

            # Store metadata
            for key, value in chunk.items():
                if key != "response":
                    self.metadata[key] = value

            # Extract content
            if "response" in chunk:
                delta = chunk["response"]
                self.full_text += delta
                self.response.content = self.full_text

            # Check if this is the final chunk
            if chunk.get("done", False):
                self.finished = True
                self._finalize_response()

            return delta, self.response

    def _finalize_response(self):
        """Update the final response with metadata and token usage."""
        # Extract token usage if available
        prompt_eval_count = self.metadata.get("prompt_eval_count", 0)
        eval_count = self.metadata.get("eval_count", 0)

        # If no token counts are available, estimate based on text length
        if prompt_eval_count == 0 and eval_count == 0:
            # Rough estimate: ~4 characters per token
            eval_count = len(self.full_text) // 4

        # Update usage information
        self.usage = TokenUsage(
            input_tokens=prompt_eval_count,
            output_tokens=eval_count,
            total_tokens=prompt_eval_count + eval_count,
        )
        self.response.usage = self.usage

        # Calculate and update cost (always 0 for Ollama)
        self.response.cost = self.provider.calculate_cost(self.usage, self.model)

        # Update finish reason
        self.response.finish_reason = "stop"

        # Update raw response
        self.response.raw_response = self.metadata

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
                message=f"Error processing Ollama stream: {e}", 
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