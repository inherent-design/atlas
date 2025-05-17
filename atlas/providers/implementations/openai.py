"""
OpenAI provider implementation for Atlas.

This module provides integration with OpenAI's language models.
"""

import logging
import threading
import time
from typing import List, Dict, Any, Optional, Tuple, Union, Iterator, Callable, cast

from atlas.core.telemetry import traced, TracedClass
from atlas.core import env
from atlas.core.errors import (
    APIError,
    AuthenticationError,
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
    MessageContent,
    ModelRole,
    TokenUsage,
    CostEstimate,
)
from atlas.providers.streaming.base import StreamHandler
from atlas.providers.streaming.control import StreamControl, StreamState
from atlas.providers.reliability import (
    ProviderRetryConfig, 
    ProviderCircuitBreaker
)
from atlas.providers.errors import (
    ProviderError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderServerError,
    ProviderValidationError
)

logger = logging.getLogger(__name__)

try:
    import openai
    from openai import OpenAI
    from openai.types.chat import ChatCompletionMessage
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI SDK not installed. Install with 'uv add openai'")
    OPENAI_AVAILABLE = False


class OpenAIStreamHandler(StreamHandler):
    """Stream handler for OpenAI API responses."""
    
    def process_stream(self, callback: Optional[Callable[[str, Any], None]] = None) -> ModelResponse:
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

    def __init__(
        self,
        provider: "OpenAIProvider",
        model: str,
        initial_response: ModelResponse,
        iterator: Iterator[Any],
        request_id: str,
    ):
        """Initialize the OpenAI stream handler.
        
        Args:
            provider: The provider instance
            model: The model name
            initial_response: Initial response to be updated
            iterator: Iterator of response chunks from OpenAI API
            request_id: Request ID from OpenAI API
        """
        # Initialize with empty content initially
        super().__init__(
            content="",
            provider=provider,
            model=model,
            initial_response=initial_response
        )
        
        # Override the iterator from parent class
        # In child class, we're overriding the iterator attribute with a real iterator
        setattr(self, 'iterator', iterator)
        self.request_id = request_id
        
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
        
    def start(self) -> None:
        """Start streaming content in a background thread."""
        if self._thread is not None:
            return
            
        # Create a new thread
        thread = threading.Thread(target=self._stream_content)
        thread.daemon = True
        self._thread = thread
        
        # Set start time and begin streaming
        self._start_time = time.time()
        thread.start()
        
    def _stream_content(self) -> None:
        """Stream content chunks from the OpenAI API."""
        try:
            # Set the state to active
            self._state = StreamState.ACTIVE
            
            # Iterate through chunks
            if self.iterator is not None:
                for chunk in self.iterator:
                    # Check if streaming should stop
                    if self._state == StreamState.CANCELLED:
                        logger.debug(f"Cancelling OpenAI stream for request {self.request_id}")
                        break
                        
                    # Skip processing if paused, but keep consuming to keep connection alive
                    if self._state == StreamState.PAUSED:
                        continue
                    
                    # Process the chunk
                    if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, 'content') and delta.content:
                            # Extract text content from chunk
                            content = delta.content
                            
                            # Add to buffer
                            with self._buffer_lock:
                                self._content_buffer.append(content)
                                self._current_content += content
                            
                            # Update the response content
                            self.response.content = self._current_content
                            self.content = self._current_content  # Update parent class content
                            
                            # Track metrics
                            self._chunk_count += 1
                    
                    # Update usage information if available
                    if hasattr(chunk, 'usage') and chunk.usage:
                        usage = chunk.usage
                        
                        # Extract token counts safely with defaults
                        input_tokens = getattr(usage, 'prompt_tokens', 0)
                        output_tokens = getattr(usage, 'completion_tokens', 0)
                        total_tokens = getattr(usage, 'total_tokens', 0)
                        
                        # If total_tokens is not provided but we have both input and output,
                        # calculate it ourselves
                        if total_tokens == 0 and (input_tokens > 0 or output_tokens > 0):
                            total_tokens = input_tokens + output_tokens
                                
                        # Create TokenUsage using direct method to bypass validation completely
                        self.response.usage = TokenUsage.create_direct(
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            total_tokens=total_tokens
                        )
                    
                    # Check if this is the final chunk
                    if (hasattr(chunk, 'choices') and len(chunk.choices) > 0 and
                        chunk.choices[0].finish_reason is not None):
                        
                        self.response.finish_reason = chunk.choices[0].finish_reason
            
            # Mark as complete when done
            self._end_time = time.time()
            self._state = StreamState.COMPLETED
            self._done.set()
            
        except Exception as e:
            # Record the error and mark as done
            self._error = getattr(self, '_error', None)
            if self._error is None:
                self._error = e
            self._state = StreamState.ERROR
            self._done.set()
            logger.error(f"Error in OpenAI stream: {e}")
    
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
        
        # Close the iterator if it has a close method
        if self.iterator is not None and hasattr(self.iterator, 'close'):
            try:
                self.iterator.close()
            except Exception as e:
                logger.warning(f"Error closing OpenAI stream: {e}")
        
        # Signal thread to stop and wait for it to finish
        self._done.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
    
    @property
    def metrics(self) -> Dict[str, Any]:
        """Get stream metrics."""
        metrics = {}
        
        # Add OpenAI-specific metrics
        metrics.update({
            "chunk_count": self._chunk_count,
            "duration": (self._end_time - self._start_time) if self._end_time and self._start_time else None,
            "request_id": self.request_id,
        })
        
        return metrics
        
    def get_iterator(self) -> Iterator[Union[str, Tuple[str, Any]]]:
        """Get an iterator for the stream.
        
        Returns:
            An iterator that yields chunks of the content.
        """
        # Implementation for the StreamHandlerProtocol
        while not self._done.is_set() or self._content_buffer:
            chunk = self.read()
            if chunk:
                yield chunk
            else:
                time.sleep(0.01)  # Small sleep to prevent CPU spinning


class OpenAIProvider(ModelProvider):
    """OpenAI language model provider implementation."""
    
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

    # Current OpenAI pricing per million tokens (as of May 2025)
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
        ]
    )
    
    DEFAULT_CIRCUIT_BREAKER = ProviderCircuitBreaker(
        failure_threshold=5,
        recovery_timeout=30.0,
        test_requests=1,
        reset_timeout=300.0,
    )

    def __init__(
        self,
        model_name: str = "gpt-4.1",
        max_tokens: int = 2000,
        api_key: Optional[str] = None,
        organization: Optional[str] = None,
        retry_config: Optional[ProviderRetryConfig] = None,
        circuit_breaker: Optional[ProviderCircuitBreaker] = None,
        options: Optional[Dict[str, Any]] = None,
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
            options: Optional provider-specific options and capabilities.
            **kwargs: Additional provider-specific parameters.

        Raises:
            ValidationError: If the OpenAI API key is missing, the SDK is not installed,
                            or if the requested model is not compatible.
        """
        super().__init__(
            retry_config=retry_config or self.DEFAULT_RETRY_CONFIG,
            circuit_breaker=circuit_breaker or self.DEFAULT_CIRCUIT_BREAKER
        )
        
        # Initialize retry state
        self._retry_state: Dict[str, Dict[str, Any]] = {}

        # Check if OpenAI SDK is installed
        if not OPENAI_AVAILABLE:
            raise ProviderValidationError(
                "OpenAI SDK not installed. Install with 'uv add openai'",
                provider="openai"
            )

        # Get API key from environment if not provided
        self.api_key = api_key or env.get_api_key("openai")
        if not self.api_key:
            raise ProviderAuthenticationError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.",
                provider="openai"
            )

        self._model_name = model_name
        self.max_tokens = max_tokens
        self.organization = organization or env.get_string("OPENAI_ORGANIZATION")
        
        # Process options dictionary
        self.options = {}
        self.capabilities = {}
        
        # Apply provider-specific options
        if options:
            try:
                # Import here to avoid circular imports
                from atlas.schemas.options import openai_options_schema
                
                # Validate options using schema
                validated_options = openai_options_schema.load(options)
                
                # Extract capabilities specifically
                if "capabilities" in validated_options:
                    self.capabilities = validated_options.pop("capabilities")
                    
                # Store the rest of the options
                self.options = validated_options
            except ValidationError as e:
                raise ProviderValidationError(
                    f"Invalid OpenAI provider options: {e}",
                    provider="openai",
                    details={"validation_errors": e.messages}
                )
        
        # Apply any other kwargs to options
        for key, value in kwargs.items():
            self.options[key] = value
            
        # Store the options separately as additional_params for backward compatibility
        self.additional_params = self.options
        
        # Client will be created lazily when needed
        self._client = None
        self._client_lock = threading.RLock()

    @property
    def name(self) -> str:
        """Get the provider name."""
        return "openai"
    
    @property
    def model_name(self) -> str:
        """Get the current model name."""
        return self._model_name
        
    @property
    def models(self) -> List[str]:
        """Get available models for this provider."""
        return self.get_available_models()

    @property
    def client(self) -> "OpenAI":
        """Get the OpenAI API client with lazy initialization.

        Returns:
            An initialized OpenAI client.
        """
        # Create client lazily to allow for testing and mocking
        if self._client is None:
            with self._client_lock:
                if self._client is None:
                    client_kwargs = {"api_key": self.api_key}
                    if self.organization:
                        client_kwargs["organization"] = self.organization
                    self._client = OpenAI(**client_kwargs)
        
        return self._client

    def _convert_messages(self, messages: List[ModelMessage]) -> List[Dict[str, Any]]:
        """Convert Atlas message format to OpenAI's format.

        Args:
            messages: List of ModelMessage objects.

        Returns:
            List of messages in OpenAI's format.
        """
        converted_messages = []
        
        for message in messages:
            role = message.role.lower()
            
            # Convert role names to OpenAI format
            if role == "user":
                role = "user"
            elif role in ["assistant", "model"]:
                role = "assistant"
            elif role == "system":
                role = "system"
            elif role == "function":
                role = "function"
            else:
                # Skip unsupported roles
                logger.warning(f"Unsupported role '{role}' for OpenAI, skipping message")
                continue
            
            # Convert content
            if isinstance(message.content, str):
                # Handle simple text content
                converted_messages.append({"role": role, "content": message.content})
            elif isinstance(message.content, list):
                # Handle content blocks (like text and images)
                content_blocks = []
                
                for block in message.content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            content_blocks.append({
                                "type": "text", 
                                "text": block.get("text", "")
                            })
                        elif block.get("type") == "image" and "url" in block:
                            # Handle image content
                            content_blocks.append({
                                "type": "image_url",
                                "image_url": {"url": block.get("url", "")}
                            })
                    elif isinstance(block, str):
                        content_blocks.append({"type": "text", "text": block})
                
                if content_blocks:
                    # Build a properly typed dictionary 
                    message_dict = {
                        "role": role,
                        "content": content_blocks
                    }
                    # Use type casting to satisfy mypy
                    converted_messages.append(cast(Dict[str, str], message_dict))
            
            # Handle function messages
            if role == "function" and hasattr(message, "name") and message.name is not None:
                converted_messages[-1]["name"] = message.name
        
        return converted_messages

    @traced(name="openai_provider_generate")
    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from the OpenAI API.

        Args:
            request: Model request containing messages and parameters.

        Returns:
            Model response with content and token usage.

        Raises:
            ProviderError: If the API request fails.
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
                provider="openai",
                details={"validation_errors": e.messages}
            )
            
        # Check if retry should be triggered
        should_retry = self._should_retry_request(request)
        
        try:
            # Convert messages to OpenAI format
            messages = self._convert_messages(request.messages)
            
            # Get parameters from request metadata or default
            request_metadata = getattr(request, "metadata", {}) or {}
            
            # Combine options with precedence: request parameters > instance options > defaults
            max_tokens = request_metadata.get("max_tokens", 
                            self.options.get("max_tokens", self.max_tokens))
            
            temperature = request_metadata.get("temperature", 
                            self.options.get("temperature", 0.7))
            
            # Prepare request parameters
            params = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            
            # Add additional options from self.options that aren't set above
            for key, value in self.options.items():
                if key not in ["max_tokens", "temperature", "capabilities"]:
                    params[key] = value
            
            # Add system prompt from request if available
            if request.system_prompt:
                # Insert a system message at the beginning if needed
                if not any(m.get("role") == "system" for m in messages):
                    messages.insert(0, {"role": "system", "content": request.system_prompt})
            
            # Make the API request
            response = self.client.chat.completions.create(**params)
            
            # Extract response content
            content = response.choices[0].message.content
            
            # Create usage information with direct method to bypass validation
            # Extract token counts safely with defaults
            input_tokens = getattr(response.usage, 'prompt_tokens', 0)
            output_tokens = getattr(response.usage, 'completion_tokens', 0)
            total_tokens = getattr(response.usage, 'total_tokens', 0)
            
            # If total_tokens is not provided, calculate it
            if total_tokens == 0 and (input_tokens > 0 or output_tokens > 0):
                total_tokens = input_tokens + output_tokens
                
            # Always use create_direct method to bypass schema validation
            usage = TokenUsage.create_direct(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens
            )
            
            # No additional validation needed since we're using create_direct to bypass validation
            
            # Create response with direct method to bypass validation
            model_response = ModelResponse.create_direct(
                provider="openai",
                model=self.model_name,
                content=content,
                usage=usage,
                raw_response=response.model_dump(),
                finish_reason=response.choices[0].finish_reason
            )
            
            return model_response
            
        except openai.OpenAIError as e:
            # Convert OpenAI errors to Atlas errors
            error_message = f"OpenAI API error: {e}"
            
            # Handle different error types based on status code
            if hasattr(e, "status_code"):
                status_code = e.status_code
                details = {"status_code": status_code, "original_error": str(e)}
                
                if status_code == 401:
                    raise ProviderAuthenticationError(error_message, provider="openai", details=details) from e
                elif status_code == 429:
                    raise ProviderRateLimitError(error_message, provider="openai", details=details) from e
                elif status_code >= 500:
                    raise ProviderServerError(error_message, provider="openai", details=details) from e
                elif status_code == 400:
                    raise ProviderValidationError(error_message, provider="openai", details=details) from e
                elif status_code == 408:
                    raise ProviderTimeoutError(error_message, provider="openai", details=details) from e
            
            # Default generic error when no status code is available
            raise ProviderError(
                error_message,
                provider="openai",
                details={"original_error": str(e)}
            ) from e
        except Exception as e:
            # Handle generic errors
            error_message = f"Error calling OpenAI API: {e}"
            raise ProviderError(
                error_message,
                provider="openai",
                details={"original_error": str(e)}
            ) from e

    @traced(name="openai_provider_stream")
    def stream(self, request: ModelRequest) -> Tuple[ModelResponse, StreamHandler]:
        """Stream a response for the given request.
        
        Args:
            request: Model request containing messages and parameters.
            
        Returns:
            A tuple containing the initial response and a stream handler.
            
        Raises:
            ProviderError: If the API request fails.
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
                provider="openai",
                details={"validation_errors": e.messages}
            )
            
        # Check if retry should be triggered
        should_retry = self._should_retry_request(request)
        
        try:
            # Convert messages to OpenAI format
            messages = self._convert_messages(request.messages)
            
            # Get parameters from request metadata or default
            request_metadata = getattr(request, "metadata", {}) or {}
            
            # Combine options with precedence: request parameters > instance options > defaults
            max_tokens = request_metadata.get("max_tokens", 
                            self.options.get("max_tokens", self.max_tokens))
            
            temperature = request_metadata.get("temperature", 
                            self.options.get("temperature", 0.7))
            
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
                if key not in ["max_tokens", "temperature", "capabilities", "stream"]:
                    params[key] = value
            
            # Add system prompt from request if available
            if request.system_prompt:
                # Insert a system message at the beginning if needed
                if not any(m.get("role") == "system" for m in messages):
                    messages.insert(0, {"role": "system", "content": request.system_prompt})
            
            # Make the API request
            stream_response = self.client.chat.completions.create(**params)
            
            # Create initial response with direct method to completely bypass validation
            initial_response = ModelResponse.create_direct(
                provider="openai",
                model=self.model_name,
                content="",  # Empty initial content, will be updated during streaming
                usage=TokenUsage.create_direct(
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0
                ),
                raw_response={"provider": "openai", "model": self.model_name, "streaming": True}
            )
            
            # Create and return stream handler
            request_id = getattr(stream_response, "id", "unknown")
            handler = OpenAIStreamHandler(
                provider=self,
                model=self.model_name,
                initial_response=initial_response,
                iterator=stream_response,
                request_id=request_id,
            )
            
            # Start streaming in background
            handler.start()
            
            return initial_response, handler
            
        except openai.OpenAIError as e:
            # Convert OpenAI errors to Atlas errors
            error_message = f"OpenAI API streaming error: {e}"
            
            # Handle different error types based on status code
            if hasattr(e, "status_code"):
                status_code = e.status_code
                details = {"status_code": status_code, "original_error": str(e)}
                
                if status_code == 401:
                    raise ProviderAuthenticationError(error_message, provider="openai", details=details) from e
                elif status_code == 429:
                    raise ProviderRateLimitError(error_message, provider="openai", details=details) from e
                elif status_code >= 500:
                    raise ProviderServerError(error_message, provider="openai", details=details) from e
                elif status_code == 400:
                    raise ProviderValidationError(error_message, provider="openai", details=details) from e
                elif status_code == 408:
                    raise ProviderTimeoutError(error_message, provider="openai", details=details) from e
            
            # Default generic error when no status code is available
            raise ProviderError(
                error_message,
                provider="openai",
                details={"original_error": str(e)}
            ) from e
        except Exception as e:
            # Handle generic errors
            error_message = f"Error calling OpenAI API for streaming: {e}"
            raise ProviderError(
                error_message,
                provider="openai",
                details={"original_error": str(e)}
            ) from e

    def get_available_models(self) -> List[str]:
        """Get the list of available OpenAI models.

        Returns:
            List of model names.
        """
        try:
            # Attempt to get models from API
            response = self.client.models.list()
            model_ids = [model.id for model in response.data]
            
            # Filter to only include chat models
            chat_models = [
                model_id for model_id in model_ids 
                if "gpt" in model_id.lower() or any(x in model_id.lower() for x in ["o3", "o4"])
            ]
            
            if chat_models:
                return chat_models
            else:
                # Return default models if no chat models found
                return list(self.PRICING.keys())
                
        except Exception as e:
            logger.warning(f"Failed to get available models from OpenAI API: {e}")
            # Return default models if API call fails
            return list(self.PRICING.keys())

    @traced(name="openai_provider_validate_api_key")
    def validate_api_key(self) -> bool:
        """Validate the OpenAI API key.

        Returns:
            True if the API key is valid, False otherwise.
        """
        try:
            # Make a minimal API call to validate the key
            # Use a cheaper model with minimal tokens
            self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "hello"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.warning(f"OpenAI API key validation failed: {e}")
            return False

    def validate_api_key_detailed(self) -> Dict[str, Any]:
        """Validate the API key with detailed information.

        Returns:
            Dict with validation information.
        """
        # Check if key exists
        key_present = bool(self.api_key)
        
        if not key_present:
            return {
                "valid": False,
                "provider": "openai",
                "key_present": False,
                "error": "API key is not set",
            }
        
        # Try to validate with API
        try:
            # Attempt a simple API call
            valid = self.validate_api_key()
            
            return {
                "valid": valid,
                "provider": "openai",
                "key_present": True,
                "error": None if valid else "API key validation failed",
            }
        except Exception as e:
            return {
                "valid": False,
                "provider": "openai",
                "key_present": True,
                "error": str(e),
            }

    def calculate_token_usage(self, request: ModelRequest, response: Any) -> TokenUsage:
        """Calculate token usage for a request and response.

        Args:
            request: The model request.
            response: The raw response from the OpenAI API.

        Returns:
            A TokenUsage object with token counts.
        """
        # Try to extract usage from the response
        if hasattr(response, "usage"):
            usage = response.usage
            
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            
            return TokenUsage.create_direct(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=usage.total_tokens
            )
        elif isinstance(response, dict) and "usage" in response:
            usage = response["usage"]
            
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            
            if total_tokens == 0:
                total_tokens = input_tokens + output_tokens
                
            return TokenUsage.create_direct(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens
            )
        
        # Fallback to approximation if detailed usage not available
        input_tokens = 0
        output_tokens = 0
        
        # Estimate input tokens from request
        for message in request.messages:
            if isinstance(message.content, str):
                # Roughly estimate string length in tokens (4 chars ~= 1 token)
                input_tokens += len(message.content) // 4
            elif isinstance(message.content, list):
                # Handle content blocks
                for block in message.content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        input_tokens += len(block.get("text", "")) // 4
                    elif isinstance(block, str):
                        input_tokens += len(block) // 4
        
        # Estimate output tokens from response content
        if hasattr(response, "choices") and response.choices:
            content = response.choices[0].message.content
            output_tokens = len(content) // 4
        elif isinstance(response, dict) and "choices" in response:
            choices = response["choices"]
            if choices and "message" in choices[0]:
                content = choices[0]["message"].get("content", "")
                output_tokens = len(content) // 4
        
        return TokenUsage.create_direct(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens
        )

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
            total_cost=input_cost + output_cost
        )
        
    def get_capability_strength(self, capability: str) -> int:
        """Get the capability strength for the current model.

        Args:
            capability: The capability name.

        Returns:
            Capability strength (0-4).
        """
        # Capability strength mappings for OpenAI models
        capability_map = {
            "gpt-4.1": {
                "premium": 3,       # Strong
                "vision": 3,        # Strong
                "standard": 3,      # Strong
                "reasoning": 3,     # Strong
                "code": 4,          # Exceptional
            },
            "gpt-4.1-mini": {
                "premium": 2,       # Moderate
                "vision": 3,        # Strong
                "standard": 3,      # Strong
                "code": 3,          # Strong
            },
            "gpt-4.1-nano": {
                "efficient": 3,     # Strong
                "standard": 2,      # Moderate
                "inexpensive": 3,   # Strong
            },
            "o3": {
                "premium": 4,       # Exceptional
                "reasoning": 4,     # Exceptional
                "standard": 3,      # Strong
                "code": 4,          # Exceptional
            },
            "o4-mini": {
                "premium": 3,       # Strong
                "reasoning": 4,     # Exceptional
                "standard": 3,      # Strong
            },
            "gpt-4o": {
                "premium": 3,       # Strong
                "vision": 3,        # Strong
                "standard": 3,      # Strong
            },
            "gpt-4o-mini": {
                "standard": 2,      # Moderate
                "vision": 2,        # Moderate
                "efficient": 2,     # Moderate
            },
            "gpt-4-turbo": {
                "premium": 3,       # Strong
                "vision": 2,        # Moderate
                "standard": 3,      # Strong
            },
            "gpt-4": {
                "premium": 3,       # Strong
                "standard": 3,      # Strong
            },
            "gpt-3.5-turbo": {
                "efficient": 3,     # Strong
                "inexpensive": 3,   # Strong
                "standard": 2,      # Moderate
            }
        }
        
        # Get capability map for current model
        model_caps = capability_map.get(self.model_name, {})
        
        # Return capability strength or 0 if not found
        return model_caps.get(capability, 0)
        
        
    @traced(name="openai_provider_generate_stream")
    def generate_stream(self, request: ModelRequest) -> Tuple[ModelResponse, StreamHandler]:
        """Generate a streaming response from the OpenAI API.
        
        This is an alias for the stream method to maintain compatibility with the agent interface.
        
        Args:
            request: Model request containing messages and parameters.
            
        Returns:
            A tuple containing the initial response and a stream handler.
            
        Raises:
            ProviderError: If the API request fails.
        """
        # Call the stream method directly to reuse its implementation
        return self.stream(request)


# This section is for code validation only (would be in a test file in practice)
if __name__ == "__main__":
    # Simple test to make sure our provider can be instantiated
    try:
        provider = OpenAIProvider(model_name="gpt-4.1", api_key="test_key")
        print(f"Provider name: {provider.name}")
        print(f"Model name: {provider.model_name}")
    except Exception as e:
        print(f"Error during validation: {e}")