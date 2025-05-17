"""
Ollama provider implementation for Atlas.

This module provides integration with Ollama for local model inference.
"""

import logging
import threading
import json
import time
from typing import List, Dict, Any, Optional, Tuple, Union, Iterator, Callable, cast, TypeVar

from atlas.core.telemetry import traced, TracedClass
from atlas.core import env
from atlas.core.errors import (
    APIError,
    ValidationError,
    ErrorSeverity,
    safe_execute,
)

# Import the new provider abstractions
from atlas.providers.base import ModelProvider
from atlas.providers.messages import (
    ModelRequest,
    ModelResponse,
    ModelMessage,
    TokenUsage,
    CostEstimate,
)
from atlas.providers.streaming.base import StreamHandler
from atlas.providers.streaming.control import StreamState
from atlas.providers.reliability import ProviderRetryConfig, ProviderCircuitBreaker
from atlas.providers.errors import (
    ProviderError,
    ProviderValidationError,
    ProviderServerError,
    ProviderTimeoutError,
)

logger = logging.getLogger(__name__)

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    logger.warning("Requests package not installed. Install with 'uv add requests'")
    REQUESTS_AVAILABLE = False

# Import ModelProvider protocol from core.types for type compatibility
try:
    from atlas.core.types import ModelProvider as CoreModelProvider
except ImportError:
    # Define a fallback protocol for type checking if the import fails
    class CoreModelProvider:
        """Fallback protocol for ModelProvider when import fails."""
        pass


class OllamaStreamHandler(StreamHandler):
    """Stream handler for Ollama API responses."""

    def __init__(
        self,
        provider: "OllamaProvider",
        model: str,
        initial_response: ModelResponse,
        stream_response: requests.Response,
    ):
        """Initialize the Ollama stream handler."""
        # Use Any as an intermediate type to avoid direct casting between incompatible types
        # This is a safe type assertion since the provider conforms to the expected interface
        provider_for_handler: Any = provider
        
        super().__init__(
            content="",
            provider=provider_for_handler,
            model=model,
            initial_response=initial_response,
        )
        self.stream_response = stream_response

        # State tracking
        self._thread: Optional[threading.Thread] = None
        self._buffer_lock = threading.RLock()
        self._done = threading.Event()
        self._content_buffer: List[str] = []
        self._current_content = ""
        self._state = StreamState.INITIALIZING

        # Metrics tracking
        self._chunk_count = 0
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._metadata: Dict[str, Any] = {}
        self._error: Optional[Exception] = None

    def start(self) -> None:
        """Start streaming content in a background thread."""
        if self._thread is not None:
            return

        self._thread = threading.Thread(target=self._stream_content)
        self._thread.daemon = True
        self._start_time = time.time()
        self._thread.start()
        self._state = StreamState.ACTIVE

    def _stream_content(self) -> None:
        """Stream content chunks from the Ollama API."""
        try:
            # Create a line iterator from the streaming response
            line_iter = self.stream_response.iter_lines(decode_unicode=True)

            for line in line_iter:
                # Check if streaming should stop
                if self._state == StreamState.CANCELLED:
                    logger.debug(f"Cancelling Ollama stream for model {self.model}")
                    break

                # Skip processing if paused, but keep consuming to keep connection alive
                if self._state == StreamState.PAUSED:
                    continue

                # Skip empty lines
                if not line:
                    continue

                try:
                    # Parse the JSON chunk
                    chunk = json.loads(line)

                    # Extract content if available
                    if "response" in chunk:
                        content = chunk["response"]

                        # Add to buffer
                        with self._buffer_lock:
                            self._content_buffer.append(content)
                            self._current_content += content

                        # Update the response content
                        self.response.content = self._current_content

                        # Track metrics
                        self._chunk_count += 1

                    # Store metadata
                    for key, value in chunk.items():
                        if key != "response":
                            self._metadata[key] = value

                    # Check if this is the final chunk
                    if chunk.get("done", False):
                        self._finalize_response()
                        break

                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to decode JSON from Ollama stream: {e}")
                    continue

            # Mark as complete when done
            self._end_time = time.time()
            self._state = StreamState.COMPLETED
            self._done.set()

        except Exception as e:
            # Record the error and mark as done
            self._error = e
            self._state = StreamState.ERROR
            self._done.set()
            logger.error(f"Error in Ollama stream: {e}")

    def _finalize_response(self) -> None:
        """Update the final response with metadata and usage information."""
        # Extract token usage if available
        prompt_eval_count = self._metadata.get("prompt_eval_count", 0)
        eval_count = self._metadata.get("eval_count", 0)

        # If no token counts are available, estimate based on text length
        if prompt_eval_count == 0 and eval_count == 0:
            # Rough estimate: ~4 characters per token
            eval_count = len(self._current_content) // 4

        # Update usage information
        self.response.usage = TokenUsage(
            input_tokens=prompt_eval_count,
            output_tokens=eval_count,
            total_tokens=prompt_eval_count + eval_count,
        )

        # Calculate and update cost (always 0 for Ollama)
        # Use Any as an intermediate type to avoid direct casting between incompatible types
        provider: Any = self.provider  
        # Call calculate_cost via dynamic attribute access
        cost_estimate = provider.calculate_cost(self.response.usage, self.model)
        self.response.cost = cost_estimate

        # Update finish reason
        self.response.finish_reason = "stop"

        # Update raw response
        self.response.raw_response = self._metadata

    def read(self) -> Optional[str]:
        """Read the next available chunk from the buffer."""
        with self._buffer_lock:
            if not self._content_buffer:
                return None
            return self._content_buffer.pop(0)

    def read_all(self) -> List[str]:
        """Read all available chunks from the buffer."""
        with self._buffer_lock:
            chunks = self._content_buffer.copy()
            self._content_buffer.clear()
            return chunks

    def close(self) -> None:
        """Close the stream and clean up resources."""
        self._state = StreamState.CANCELLED

        # Close the response if possible
        try:
            self.stream_response.close()
        except Exception as e:
            logger.warning(f"Error closing Ollama stream response: {e}")

        self._done.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def get_iterator(self) -> Iterator[Union[str, Tuple[str, ModelResponse]]]:
        """Get an iterator for the stream.
        
        Returns:
            An iterator that yields chunks of the content.
        """
        # Start streaming if not already started
        if self._thread is None:
            self.start()
            
        # Loop until complete or cancelled
        while not self._done.is_set() or self._content_buffer:
            chunk = self.read()
            if chunk:
                yield chunk
            else:
                # Small sleep to avoid busy waiting
                time.sleep(0.01)
    
    def process_stream(self, callback: Optional[Callable[[str, ModelResponse], None]] = None) -> ModelResponse:
        """Process the entire stream with a callback function.
        
        Args:
            callback: Function to call for each chunk of content.
        
        Returns:
            The final response after processing the entire stream.
        """
        # Start streaming if not already started
        self.start()
        
        # Process until done
        for chunk in self.get_iterator():
            if callback and isinstance(chunk, str):
                callback(chunk, self.response)
                
        return self.response


class OllamaProvider(ModelProvider):
    """Ollama local language model provider implementation."""

    # Default Ollama API endpoint
    DEFAULT_API_ENDPOINT = "http://localhost:11434/api"

    # Default connection timeout in seconds
    DEFAULT_CONNECT_TIMEOUT = 2

    # Default request timeout in seconds
    DEFAULT_REQUEST_TIMEOUT = 60

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
        ],
    )

    DEFAULT_CIRCUIT_BREAKER = ProviderCircuitBreaker(
        failure_threshold=5,
        recovery_timeout=30.0,
        test_requests=1,
        reset_timeout=300.0,
    )
    
    # Class-level shared model cache: mapping from API endpoint to (models, last_fetch_time)
    _model_cache: Dict[str, Tuple[List[str], float]] = {}
    
    # Cache expiration time in seconds (5 minutes)
    _CACHE_EXPIRATION = 300

    def __init__(
        self,
        model_name: str = "llama3",
        max_tokens: int = 2000,
        api_endpoint: Optional[str] = None,
        connect_timeout: Optional[float] = None,
        request_timeout: Optional[float] = None,
        retry_config: Optional[ProviderRetryConfig] = None,
        circuit_breaker: Optional[ProviderCircuitBreaker] = None,
        options: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        """Initialize the Ollama provider."""
        super().__init__(
            retry_config=retry_config or self.DEFAULT_RETRY_CONFIG,
            circuit_breaker=circuit_breaker or self.DEFAULT_CIRCUIT_BREAKER,
        )

        # Check if Requests is available
        if not REQUESTS_AVAILABLE:
            raise ProviderValidationError(
                "Requests package is not installed. Install with 'uv add requests'",
                provider="ollama",
            )

        self._model_name = model_name
        self.max_tokens = max_tokens

        # Get API endpoint from env module or use default
        self.api_endpoint = api_endpoint or env.get_string(
            "OLLAMA_API_ENDPOINT", self.DEFAULT_API_ENDPOINT
        )

        # Normalize API endpoint (remove trailing slash)
        if self.api_endpoint is not None:
            self.api_endpoint = self.api_endpoint.rstrip("/")

        # Set timeouts with fallbacks to environment variables or defaults
        self.connect_timeout = connect_timeout or env.get_float(
            "OLLAMA_CONNECT_TIMEOUT", self.DEFAULT_CONNECT_TIMEOUT
        )
        self.request_timeout = request_timeout or env.get_float(
            "OLLAMA_REQUEST_TIMEOUT", self.DEFAULT_REQUEST_TIMEOUT
        )

        # Process options dictionary
        self.options = {}
        self.capabilities = {}
        
        # Apply provider-specific options
        if options:
            try:
                # Import here to avoid circular imports
                from atlas.schemas.options import ollama_options_schema
                
                # Validate options using schema
                validated_options = ollama_options_schema.load(options)
                
                # Extract capabilities specifically
                if "capabilities" in validated_options:
                    self.capabilities = validated_options.pop("capabilities")
                    
                # Store the rest of the options
                self.options = validated_options
            except ValidationError as e:
                raise ProviderValidationError(
                    f"Invalid Ollama provider options: {e}",
                    provider="ollama",
                    details={"validation_errors": e.messages}
                )
        
        # Apply specific Ollama parameters that were passed directly
        special_params = {
            "api_endpoint": self.api_endpoint,
            "connect_timeout": self.connect_timeout,
            "request_timeout": self.request_timeout
        }
        for key, value in special_params.items():
            if value is not None:
                self.options[key] = value
                
        # Apply any other kwargs to options
        for key, value in kwargs.items():
            if key not in ["api_endpoint", "connect_timeout", "request_timeout"]:
                self.options[key] = value
                
        # Store options separately as additional_params for backward compatibility
        self.additional_params = self.options
        
        # Retry state tracking
        self._retry_state: Dict[str, Dict[str, Any]] = {}

    @property
    def name(self) -> str:
        """Get the provider name."""
        return "ollama"
        
    @property
    def model_name(self) -> str:
        """Get the current model name."""
        return self._model_name
        
    @property
    def models(self) -> List[str]:
        """Get a list of available models for this provider.
        
        This implements the abstract property required by the ModelProvider protocol.
        """
        return self.get_available_models()
        
    def get_available_models(self) -> List[str]:
        """Get a list of available models for this provider."""
        # Use class-level model cache for efficient model list retrieval
        current_time = time.time()
        cache_key = self.api_endpoint or ""
        
        # Check if we have a valid cache entry for this API endpoint
        cache_entry = self._model_cache.get(cache_key)
        if cache_entry and (current_time - cache_entry[1] < self._CACHE_EXPIRATION):
            # Use cached models if not expired
            return cache_entry[0]
            
        # Fetch fresh models from the API
        models = self._fetch_models()
        
        # Update the class-level cache
        self._model_cache[cache_key] = (models, current_time)
        
        return models

    def _fetch_models(self) -> List[str]:
        """Fetch models directly from the Ollama API."""
        try:
            # Get models from API with configured timeouts
            timeout_value = 10.0
            if self.request_timeout is not None:
                timeout_value = min(10.0, self.request_timeout)
                
            response = requests.get(
                f"{self.api_endpoint}/tags",
                timeout=(self.connect_timeout, timeout_value),
            )

            # Check if the request was successful
            if response.status_code == 200:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]

                # Log the discovered models
                if models:
                    logger.info(f"Discovered {len(models)} models from Ollama server at {self.api_endpoint}")
                    return models
                else:
                    logger.warning(f"Ollama server at {self.api_endpoint} returned no models")
                    return []
            else:
                logger.warning(
                    f"Failed to get models from Ollama API at {self.api_endpoint} (status code {response.status_code})"
                )
                return []

        except Exception as e:
            logger.warning(f"Error fetching Ollama models from {self.api_endpoint}: {e}")
            return []

    @traced(name="ollama_provider_validate_api_key")
    def validate_api_key(self) -> bool:
        """Validate server availability."""
        try:
            # Try to get the Ollama version with configured connect timeout
            response = requests.get(
                f"{self.api_endpoint}/version", timeout=self.connect_timeout
            )
            if response.status_code == 200:
                return True
            else:
                logger.warning(
                    f"Ollama server responded with status code {response.status_code}"
                )
                return False
        except requests.RequestException as e:
            logger.warning(
                f"Error connecting to Ollama server at {self.api_endpoint}: {e}"
            )
            return False

    def validate_api_key_detailed(self) -> Dict[str, Any]:
        """Validate API key with detailed response."""
        # Perform the validation
        is_valid = self.validate_api_key()

        # Construct detailed response
        return {
            "valid": is_valid,
            "key_present": True,  # Ollama doesn't need an API key
            "provider": self.name,
            "error": (
                None
                if is_valid
                else f"Ollama server at {self.api_endpoint} is not accessible"
            ),
        }

    def _convert_messages(
        self, messages: List[ModelMessage]
    ) -> Tuple[str, Optional[str]]:
        """Convert Atlas message format to Ollama format."""
        system_content = None
        prompt_parts = []

        for message in messages:
            role = message.role.lower()

            # Extract content as string
            if isinstance(message.content, str):
                content = message.content
            else:
                # Handle content blocks (Ollama only supports text)
                if isinstance(message.content, list):
                    content = ""
                    for block in message.content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            content += block.get("text", "")
                        elif isinstance(block, str):
                            content += block
                else:
                    # Fallback - convert to string
                    content = str(message.content)

            # Format based on role
            if role == "system":
                system_content = content
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
            elif role == "function":
                # Ollama doesn't support function calls, so include as user messages
                name = getattr(message, "name", "function")
                prompt_parts.append(f"Function ({name}): {content}")

        # Add final assistant prompt if needed
        if prompt_parts and not prompt_parts[-1].startswith("Assistant:"):
            prompt_parts.append("Assistant:")

        # Build the final prompt
        prompt = "\n\n".join(prompt_parts)

        return prompt, system_content
        
    def _should_retry_request(self, request: ModelRequest) -> bool:
        """Determine if a request should be retried.
        
        Args:
            request: The model request to check.
            
        Returns:
            True if the request should be retried, False otherwise.
        """
        # Get retry settings from configuration
        retry_config = getattr(self, "retry_config", None)
        if not retry_config:
            # No retry configuration, use default behavior
            return True
            
        # Check if maximum retries is exceeded
        request_id = getattr(request, "id", str(id(request)))
        retry_state = self._retry_state.get(request_id, {"count": 0})
        
        # Check if we've reached the maximum number of retries
        if retry_state.get("count", 0) >= retry_config.max_retries:
            logger.debug(f"Maximum retries ({retry_config.max_retries}) reached for request {request_id}")
            return False
            
        # Update retry state
        retry_state["count"] = retry_state.get("count", 0) + 1
        self._retry_state[request_id] = retry_state
        
        return True

    @traced(name="ollama_provider_generate")
    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from the Ollama API."""
        # Validate request using schema
        try:
            # Import here to avoid circular imports
            from atlas.schemas.providers import model_request_schema
            
            # Validate request
            validated_request = model_request_schema.load(request.__dict__)
            
            # Convert validated request back to ModelRequest if needed
            if not isinstance(request, ModelRequest):
                request = ModelRequest(**validated_request)
                
        except ValidationError as e:
            raise ProviderValidationError(
                f"Invalid request: {e}",
                provider="ollama",
                details={"validation_errors": e.messages}
            )
            
        # Check if retry should be triggered
        should_retry = self._should_retry_request(request)

        try:
            # Get the model to use
            model = request.model or self._model_name

            # Convert messages to Ollama format
            prompt, system_content = self._convert_messages(request.messages)

            # Get parameters from request metadata or default
            request_metadata = getattr(request, "metadata", {}) or {}
            
            # Combine options with precedence: request parameters > instance options > defaults
            max_tokens = request_metadata.get("max_tokens", 
                           self.options.get("max_tokens", self.max_tokens))
            
            temperature = request_metadata.get("temperature", 
                            self.options.get("temperature", 0.7))

            # Prepare request parameters
            params: Dict[str, Any] = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                },
            }

            # Add system prompt if available
            if system_content or request.system_prompt:
                params["system"] = system_content or request.system_prompt

            # Add temperature if available
            if temperature is not None:
                params["options"]["temperature"] = temperature

            # Add additional options from self.options that aren't set above
            for key, value in self.options.items():
                if key not in params and key != "options" and key not in ["max_tokens", "temperature", "capabilities"]:
                    params[key] = value
                elif key == "options" and isinstance(value, dict):
                    for option_key, option_value in value.items():
                        if option_key not in params["options"]:
                            params["options"][option_key] = option_value

            # Make the API request
            response = requests.post(
                f"{self.api_endpoint}/generate",
                json=params,
                timeout=(self.connect_timeout, self.request_timeout),
            )

            # Check response status
            if response.status_code != 200:
                raise ProviderError(
                    f"Ollama API returned status code {response.status_code}: {response.text}",
                    provider="ollama",
                    retry_possible=should_retry and response.status_code >= 500,
                    details={
                        "status_code": response.status_code,
                        "response": response.text,
                    },
                )

            # Parse response
            response_data = response.json()

            # Extract content
            content = response_data.get("response", "")

            # Calculate token usage
            usage = self.calculate_token_usage(request, response_data)
            
            # Validate the usage with schema
            try:
                # Import here to avoid circular imports
                from atlas.schemas.providers import token_usage_schema
                
                # Validate usage
                validated_usage = token_usage_schema.load(usage.__dict__)
                
                # Create new TokenUsage if validation passed but types don't match
                if not isinstance(usage, TokenUsage):
                    usage = TokenUsage(**validated_usage)
                    
            except ValidationError as e:
                logger.warning(f"Token usage validation failed: {e}")
                # Continue with unvalidated usage as this is not critical

            # Create response
            model_response = ModelResponse(
                provider="ollama",
                model=model,
                content=content,
                usage=usage,
                raw_response=response_data,
                finish_reason=response_data.get("done", True) and "stop" or "unknown",
            )
            
            # Validate the response with schema
            try:
                # Import here to avoid circular imports
                from atlas.schemas.providers import model_response_schema
                
                # Validate response
                validated_response = model_response_schema.load(model_response.__dict__)
                
                # Create new ModelResponse if validation passed but types don't match
                if not isinstance(model_response, ModelResponse):
                    model_response = ModelResponse(**validated_response)
                    
            except ValidationError as e:
                logger.warning(f"Response validation failed: {e}")
                # Continue with unvalidated response as this is not critical

            return model_response

        except requests.RequestException as e:
            # Handle request exceptions
            if isinstance(e, requests.ConnectionError):
                error_message = (
                    f"Failed to connect to Ollama server at {self.api_endpoint}: {e}"
                )
            elif isinstance(e, requests.Timeout):
                error_message = f"Timeout connecting to Ollama server: {e}"
            else:
                error_message = f"Request error calling Ollama API: {e}"

            raise ProviderError(
                error_message, provider="ollama", retry_possible=should_retry, cause=e
            ) from e
        except ProviderError:
            # Re-raise provider errors
            raise
        except Exception as e:
            # Handle generic errors
            error_message = f"Error calling Ollama API: {e}"
            raise ProviderError(
                error_message, provider="ollama", retry_possible=should_retry, cause=e
            ) from e
    
    @traced(name="ollama_provider_stream")
    def stream(self, request: ModelRequest) -> Tuple[ModelResponse, StreamHandler]:
        """Stream a response from the model.
        
        This matches the signature in the base ModelProvider class.
        
        Args:
            request: The model request to stream.
            
        Returns:
            A tuple of (initial ModelResponse, StreamHandler).
        """
        # Call generate_stream which does the actual work
        return self.generate_stream(request)

    @traced(name="ollama_provider_stream_internal")
    def generate_stream(
        self, request: ModelRequest
    ) -> Tuple[ModelResponse, StreamHandler]:
        """Generate a streaming response from the Ollama API.
        
        This is an internal method that does the actual streaming work.
        """
        # Validate request using schema
        try:
            # Import here to avoid circular imports
            from atlas.schemas.providers import model_request_schema
            
            # Validate request
            validated_request = model_request_schema.load(request.__dict__)
            
            # Convert validated request back to ModelRequest if needed
            if not isinstance(request, ModelRequest):
                request = ModelRequest(**validated_request)
                
        except ValidationError as e:
            raise ProviderValidationError(
                f"Invalid request: {e}",
                provider="ollama",
                details={"validation_errors": e.messages}
            )
            
        # Check if retry should be triggered
        should_retry = self._should_retry_request(request)

        try:
            # Get the model to use
            model = request.model or self._model_name

            # Convert messages to Ollama format
            prompt, system_content = self._convert_messages(request.messages)

            # Get parameters from request metadata or default
            request_metadata = getattr(request, "metadata", {}) or {}
            
            # Combine options with precedence: request parameters > instance options > defaults
            max_tokens = request_metadata.get("max_tokens", 
                           self.options.get("max_tokens", self.max_tokens))
            
            temperature = request_metadata.get("temperature", 
                            self.options.get("temperature", 0.7))

            # Prepare request parameters
            params: Dict[str, Any] = {
                "model": model,
                "prompt": prompt,
                "stream": True,  # Enable streaming
                "options": {
                    "num_predict": max_tokens,
                },
            }

            # Add system prompt if available
            if system_content or request.system_prompt:
                params["system"] = system_content or request.system_prompt

            # Add temperature if available
            if temperature is not None:
                params["options"]["temperature"] = temperature

            # Add additional options from self.options that aren't set above
            for key, value in self.options.items():
                if key not in params and key != "options" and key not in ["max_tokens", "temperature", "capabilities", "stream"]:
                    params[key] = value
                elif key == "options" and isinstance(value, dict):
                    for option_key, option_value in value.items():
                        if option_key not in params["options"]:
                            params["options"][option_key] = option_value

            # Make the API request
            response = requests.post(
                f"{self.api_endpoint}/generate",
                json=params,
                timeout=(self.connect_timeout, self.request_timeout),
                stream=True,
            )

            # Check response status
            if response.status_code != 200:
                raise ProviderError(
                    f"Ollama API returned status code {response.status_code}: {response.text}",
                    provider="ollama",
                    retry_possible=should_retry and response.status_code >= 500,
                    details={
                        "status_code": response.status_code,
                        "response": response.text,
                    },
                )

            # Create initial response
            initial_response = ModelResponse(
                provider="ollama",
                model=model,
                content="",  # Empty initial content, will be updated during streaming
                usage=TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0),
                raw_response={"provider": "ollama", "model": model, "streaming": True},
            )
            
            # Validate the initial response
            try:
                # Import here to avoid circular imports
                from atlas.schemas.providers import model_response_schema
                
                # Validate response
                validated_response = model_response_schema.load(initial_response.__dict__)
                
                # Create new ModelResponse if validation passed but types don't match
                if not isinstance(initial_response, ModelResponse):
                    initial_response = ModelResponse(**validated_response)
                    
            except ValidationError as e:
                logger.warning(f"Initial response validation failed: {e}")
                # Continue with unvalidated response as this is not critical

            # Create and return stream handler
            handler = OllamaStreamHandler(
                provider=self,
                model=model,
                initial_response=initial_response,
                stream_response=response,
            )
            
            # Validate the stream handler
            try:
                # Import here to avoid circular imports
                from atlas.schemas.streaming import stream_handler_schema
                
                # Create a dict representation for validation
                handler_dict = {
                    "provider": self.name,
                    "model": model,
                    "content": "",
                    "initial_response": initial_response.__dict__,
                    "state": handler._state.value,
                }
                
                # Validate handler
                stream_handler_schema.load(handler_dict)
                
            except (ImportError, ValidationError) as e:
                logger.warning(f"Stream handler validation failed: {e}")
                # Continue with unvalidated handler as this is not critical

            # Start streaming in background
            handler.start()

            return initial_response, handler

        except requests.RequestException as e:
            # Handle request exceptions
            if isinstance(e, requests.ConnectionError):
                error_message = (
                    f"Failed to connect to Ollama server at {self.api_endpoint}: {e}"
                )
            elif isinstance(e, requests.Timeout):
                error_message = f"Timeout connecting to Ollama server: {e}"
            else:
                error_message = f"Request error calling Ollama API: {e}"

            raise ProviderError(
                error_message, provider="ollama", retry_possible=should_retry, cause=e
            ) from e
        except ProviderError:
            # Re-raise provider errors
            raise
        except Exception as e:
            # Handle generic errors
            error_message = f"Error calling Ollama API for streaming: {e}"
            raise ProviderError(
                error_message, provider="ollama", retry_possible=should_retry, cause=e
            ) from e

    def calculate_token_usage(self, request: ModelRequest, response: Any) -> TokenUsage:
        """Calculate token usage for a request and response."""
        # Ollama doesn't provide token counts consistently, so we estimate
        prompt_tokens = response.get("prompt_eval_count", 0)
        eval_tokens = response.get("eval_count", 0)

        # If prompt tokens is 0, estimate based on character count
        if prompt_tokens == 0 and request.messages:
            # Rough estimate: ~4 characters per token
            prompt_text = ""
            for message in request.messages:
                if isinstance(message.content, str):
                    prompt_text += message.content
                else:
                    # Try to extract text from content blocks
                    if isinstance(message.content, list):
                        for block in message.content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                prompt_text += block.get("text", "")
                            elif isinstance(block, str):
                                prompt_text += block
                    else:
                        # Fallback - convert to string
                        prompt_text += str(message.content)

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
        """Calculate cost for token usage."""
        # Local models have no API cost
        return CostEstimate(
            input_cost=0.0,
            output_cost=0.0,
            total_cost=0.0,
        )

    def get_capability_strength(self, capability: str) -> int:
        """Get the capability strength for the current model."""
        # Ollama has strong capabilities for local, private and inexpensive operation
        if capability in ["local", "private", "inexpensive"]:
            return 4  # Exceptional

        # All Ollama models provide some standard capabilities
        if capability == "standard":
            return 2  # Moderate

        # For model-specific capabilities, we would need more detailed information
        # For now, return a basic level for all other capabilities
        return 1  # Basic