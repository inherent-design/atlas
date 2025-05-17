"""
Base stream handler implementations for Atlas providers.

This module provides enhanced stream handler classes for handling streaming
responses from various model providers with advanced features like stream
control, buffering, and performance metrics.
"""

import abc
import logging
import threading
import time
from typing import Dict, Any, Optional, Union, Iterator, List, Tuple, Callable, TypeVar, cast, Generic

from atlas.providers.streaming.control import StreamControl, StreamControlBase, StreamState
from atlas.providers.streaming.buffer import StreamBuffer, RateLimitedBuffer
from atlas.providers.errors import ProviderStreamError, ProviderConfigError
from atlas.core.errors import ErrorSeverity
from atlas.core.types import ModelProvider, StreamHandlerProtocol
from atlas.providers.messages import ModelResponse
from atlas.schemas.streaming import (
    stream_handler_config_schema,
    enhanced_stream_handler_config_schema,
    string_stream_handler_config_schema,
    validate_streaming_config
)

# Type variables
T = TypeVar('T')

logger = logging.getLogger(__name__)


class StreamHandler(abc.ABC, StreamHandlerProtocol):
    """Base class for handling streaming responses from model providers.

    This class provides a common interface for processing streaming responses
    from different model providers. Each provider implements its own subclass
    with provider-specific stream handling.
    """

    @validate_streaming_config
    def __init__(
        self,
        content: str,
        provider: "ModelProvider",
        model: str,
        initial_response: "ModelResponse",
        delay_ms: int = 50,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize a stream handler.

        Args:
            content: Initial or complete content to stream.
            provider: The provider instance that created this handler.
            model: The model used for generating the stream.
            initial_response: The initial ModelResponse to update during streaming.
            delay_ms: Optional delay between chunks in milliseconds (for throttling).
            config: Optional configuration dictionary that will be validated using schema.
                   If provided, it overrides other parameters.
        """
        from atlas.schemas.streaming import stream_handler_config_schema
        
        # Convert parameters to config dict for validation
        if config is None:
            config = {
                "content": content,
                "provider": getattr(provider, "name", str(provider)),
                "model": model,
                "delay_ms": delay_ms
            }
        
        # If config is provided via parameter, it's already been validated by the decorator
        # If we created it above, validate it now
        if not (isinstance(config, dict) and config.get("_validated", False)):
            try:
                # Explicitly validate the config
                config = stream_handler_config_schema.load(config)
                # Mark as validated to avoid duplicate validation - convert to dict with _validated
                config = dict(config)
                config["_validated"] = True
            except Exception as e:
                logger.error(f"Error validating stream handler config: {e}")
                # Use original parameters as fallback
                config = {
                    "content": content,
                    "provider": getattr(provider, "name", str(provider)),
                    "model": model,
                    "delay_ms": delay_ms
                }
            
        # Extract parameters from validated config
        content = config.get("content", content)
        # provider should not be overridden from config
        model = config.get("model", model)
        # initial_response should not be overridden from config
        delay_ms = config.get("delay_ms", delay_ms)
            
        # Set instance attributes
        self.content = content
        self.provider = provider
        self.model = model
        self.response = initial_response
        self.delay_ms = delay_ms
        self.iterator = None
        
        # Store the validated config
        self._config = config

    @abc.abstractmethod
    def get_iterator(self) -> Iterator[Union[str, Tuple[str, "ModelResponse"]]]:
        """Get an iterator for the stream.

        Returns:
            An iterator that yields chunks of the content.
            
        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError("Subclasses must implement get_iterator")

    def process_stream(self, callback: Optional[Callable[[str, "ModelResponse"], None]] = None) -> "ModelResponse":
        """Process the entire stream with a callback function.

        Args:
            callback: Function to call for each chunk of content.
                     It takes (delta, response) parameters where:
                     - delta is the new content chunk
                     - response is the updated ModelResponse

        Returns:
            The final ModelResponse after processing the entire stream.
        """
        iterator = self.get_iterator()
        
        # Handle the case where callback is None
        if callback is None:
            # Just consume the iterator without callbacks
            for chunk in iterator:
                # Handle both simple string chunks and tuple (delta, response) chunks
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    delta, response = chunk
                    if response:
                        self.response = response
                else:
                    # Just a string chunk, add to content
                    self.content += chunk
        else:
            # Process with callback
            for chunk in iterator:
                # Handle both simple string chunks and tuple (delta, response) chunks
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    delta, response = chunk
                    if response:
                        self.response = response
                    callback(delta, self.response)
                else:
                    # Simple string chunk
                    callback(chunk, self.response)
                    
        return self.response


class EnhancedStreamHandler(StreamHandler, StreamControlBase):
    """Enhanced stream handler with control capabilities.
    
    This class extends the base StreamHandler with advanced features like
    pause/resume/cancel, performance metrics, and thread-safe operations.
    It implements the StreamControl interface for standardized control.
    """
    
    @validate_streaming_config
    def __init__(
        self,
        provider: "ModelProvider",
        model: str,
        initial_response: "ModelResponse",
        content: str = "",
        max_buffer_size: int = 1024 * 1024,
        rate_limit: Optional[float] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the enhanced stream handler.
        
        Args:
            provider: The provider instance.
            model: The model being used.
            initial_response: The initial ModelResponse object.
            content: Initial content, if any.
            max_buffer_size: Maximum buffer size in characters.
            rate_limit: Optional rate limit in tokens per second.
            config: Optional configuration dictionary that will be validated using schema.
                   If provided, it overrides other parameters.
        """
        from atlas.schemas.streaming import enhanced_stream_handler_config_schema
        
        # Convert parameters to config dict for validation
        if config is None:
            config = {
                "content": content,
                "provider": getattr(provider, "name", str(provider)),
                "model": model,
                "max_buffer_size": max_buffer_size,
                "rate_limit": rate_limit
            }
        
        # If config is provided via parameter, it's already been validated by the decorator
        # If we created it above, validate it now
        if not (isinstance(config, dict) and config.get("_validated", False)):
            try:
                # Explicitly validate the config
                config = enhanced_stream_handler_config_schema.load(config)
                # Mark as validated to avoid duplicate validation - convert to dict with _validated
                config = dict(config)
                config["_validated"] = True
            except Exception as e:
                logger.error(f"Error validating enhanced stream handler config: {e}")
                # Use original parameters as fallback
                config = {
                    "content": content,
                    "provider": getattr(provider, "name", str(provider)),
                    "model": model,
                    "max_buffer_size": max_buffer_size,
                    "rate_limit": rate_limit
                }
            
        # Extract parameters from validated config
        content = config.get("content", content)
        # provider should not be overridden from config
        model = config.get("model", model)
        # initial_response should not be overridden from config
        max_buffer_size = config.get("max_buffer_size", max_buffer_size)
        rate_limit = config.get("rate_limit", rate_limit)

        # Initialize parent classes with validated config
        StreamHandler.__init__(
            self,
            content=content,
            provider=provider,
            model=model,
            initial_response=initial_response,
            config=config  # Pass the validated config
        )
        
        # Initialize StreamControlBase with validated config
        StreamControlBase.__init__(self, config=config)
        
        # Full text accumulated during streaming
        self.full_text = content if content else ""
        
        # Create buffer configuration with schema validation
        from atlas.schemas.streaming import rate_limited_buffer_config_schema
        
        buffer_config = {
            "max_buffer_size": max_buffer_size,
            "tokens_per_second": rate_limit
        }
        
        # Validate buffer config
        validated_buffer_config = rate_limited_buffer_config_schema.load(buffer_config)
        
        # Create a thread-safe buffer
        self._buffer = RateLimitedBuffer(config=validated_buffer_config)
        
        # Stream processing thread with enhanced thread safety
        self._processing_thread: Optional[threading.Thread] = None
        self._processing_event = threading.Event()
        self._processing_lock = threading.RLock()  # Lock for thread operations
        
        # For provider-specific state
        self.finished = False
        
        # Store the validated config
        self._config = config
    
    def start_processing(self) -> None:
        """
        Start processing the stream in a background thread.
        """
        if self._processing_thread is not None:
            return
        
        self._set_state(StreamState.ACTIVE)
        
        # Start processing thread
        thread = threading.Thread(
            target=self._processing_loop,
            daemon=True,
            name=f"stream-processor-{id(self)}"
        )
        self._processing_thread = thread
        thread.start()
    
    def _processing_loop(self) -> None:
        """
        Main processing loop for the stream.
        """
        try:
            iterator = self.get_iterator()
            
            while True:
                # Check if we should stop
                with self._state_lock:
                    if self._state in (StreamState.CANCELLED, StreamState.COMPLETED, StreamState.ERROR):
                        break
                    
                    if self._state == StreamState.PAUSED:
                        # Wait until resumed or cancelled
                        self._processing_event.clear()
                
                # Wait if paused
                if self._state == StreamState.PAUSED:
                    self._processing_event.wait()
                    continue
                
                # Get next chunk
                try:
                    chunk_data = next(iterator)
                    
                    # Handle both simple string chunks and tuple (delta, response) chunks
                    if isinstance(chunk_data, tuple) and len(chunk_data) == 2:
                        delta, response = chunk_data
                        if response:
                            self.response = response
                    else:
                        delta = chunk_data
                    
                    self._process_new_content(delta)
                    
                except StopIteration:
                    # Stream is complete
                    with self._metrics_lock:
                        self._metrics["end_time"] = time.time()
                    
                    with self._state_lock:
                        if self._state != StreamState.CANCELLED:
                            self._set_state(StreamState.COMPLETED)
                    break
                    
                except Exception as e:
                    logger.error(f"Error processing stream: {e}", exc_info=True)
                    self._set_state(StreamState.ERROR)
                    break
        
        except Exception as e:
            logger.error(f"Unexpected error in stream processing: {e}", exc_info=True)
            self._set_state(StreamState.ERROR)
        
        finally:
            # Close the buffer
            self._buffer.close()
            
            # Clean up resources
            self._cleanup()
    
    def _process_new_content(self, delta: str) -> None:
        """
        Process new content from the stream.
        
        Args:
            delta: New content.
        """
        if not delta:
            return
        
        # Update metrics
        self._update_metrics(delta)
        
        # Add to buffer
        self._buffer.add(delta)
        
        # Update response content
        with self._state_lock:
            self.full_text += delta
            self.response.content = self.full_text
        
        # Notify callbacks
        for callback in self._content_callbacks:
            try:
                callback(delta, self.response)
            except Exception as e:
                logger.error(f"Error in content callback: {e}", exc_info=True)
    
    def _pause_provider_stream(self) -> bool:
        """
        Provider-specific implementation to pause the stream.
        
        Returns:
            bool: True if the stream was paused, False otherwise.
        """
        self._buffer.pause()
        return True
    
    def _resume_provider_stream(self) -> bool:
        """
        Provider-specific implementation to resume the stream.
        
        Returns:
            bool: True if the stream was resumed, False otherwise.
        """
        self._buffer.resume()
        self._processing_event.set()  # Wake up processing thread
        return True
    
    def _cancel_provider_stream(self) -> bool:
        """
        Provider-specific implementation to cancel the stream.
        
        Returns:
            bool: True if the stream was cancelled, False otherwise.
        """
        self._buffer.close()
        self._processing_event.set()  # Wake up processing thread
        self.finished = True
        return True
    
    def _cleanup(self) -> None:
        """
        Clean up resources when the stream is done.
        """
        try:
            # Close the buffer
            self._buffer.close()
            
            # Stop the processing thread
            self._processing_event.set()
        except Exception as e:
            logger.error(f"Error cleaning up stream resources: {e}", exc_info=True)
    
    def process_stream(self, callback: Optional[Callable[[str, "ModelResponse"], None]] = None) -> "ModelResponse":
        """
        Process the entire stream, optionally calling a callback for each chunk.
        
        Args:
            callback: Optional function taking (delta, response) parameters
                    to call for each chunk of the stream.
        
        Returns:
            The final ModelResponse after processing the entire stream.
        """
        # Register callback if provided
        if callback:
            self.register_content_callback(callback)
        
        # Start processing thread
        self.start_processing()
        
        # Wait for processing to complete
        while self.state not in (StreamState.COMPLETED, StreamState.CANCELLED, StreamState.ERROR):
            try:
                # Get content from buffer with timeout
                content = self._buffer.get(timeout=0.1)
                if content and callback:
                    callback(content, self.response)
            except Exception as e:
                if not isinstance(e, (StopIteration, threading.BrokenBarrierError)):
                    logger.error(f"Error processing stream content: {e}", exc_info=True)
                    self._set_state(StreamState.ERROR)
                break
        
        # Join processing thread if it exists
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=2.0)
        
        return self.response
    
    def __del__(self) -> None:
        """Ensure resources are cleaned up when the object is garbage collected."""
        try:
            if self.state not in (StreamState.COMPLETED, StreamState.CANCELLED, StreamState.ERROR):
                self.cancel()
            self._cleanup()
        except:
            pass


class StringStreamHandler(EnhancedStreamHandler):
    """Stream handler for string-based content.
    
    This implementation provides a simple string-based stream for testing
    and for providers that return complete responses rather than true streams.
    """
    
    @validate_streaming_config
    def __init__(
        self,
        content: str,
        provider: "ModelProvider",
        model: str,
        initial_response: "ModelResponse",
        chunk_size: int = 10,
        delay_sec: float = 0.05,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a string-based stream handler.
        
        Args:
            content: The complete content to stream.
            provider: The provider instance.
            model: The model being used.
            initial_response: The initial response object.
            chunk_size: Size of each chunk to simulate streaming.
            delay_sec: Delay between chunks in seconds.
            config: Optional configuration dictionary that will be validated using schema.
                   If provided, it overrides other parameters.
        """
        # If config is provided, it has been validated by the decorator
        if config is not None:
            if isinstance(config, dict):
                # Override parameters with config values if present
                content = config.get("content", content)
                # provider should not be overridden from config
                model = config.get("model", model)
                # initial_response should not be overridden from config
                chunk_size = config.get("chunk_size", chunk_size)
                delay_sec = config.get("delay_sec", delay_sec)
                
                # Extract values for parent class
                enhanced_config = {
                    "content": content,
                    "model": model,
                    "max_buffer_size": config.get("max_buffer_size", 1024 * 1024),
                    "rate_limit": config.get("rate_limit", None)
                }
            else:
                enhanced_config = None
        else:
            enhanced_config = None
                
        # Initialize parent with optional merged config
        super().__init__(
            provider=provider,
            model=model,
            initial_response=initial_response,
            content=content,
            config=enhanced_config
        )
        
        self.chunk_size = chunk_size
        self.delay_sec = delay_sec
        self.content = content
        self.position = 0
    
    def get_iterator(self) -> Iterator[str]:
        """
        Get an iterator for the stream.
        
        Returns:
            An iterator that yields chunks of the content.
        """
        return self
    
    def __iter__(self) -> "StringStreamHandler":
        """Make the handler iterable for processing in a for loop."""
        self.position = 0
        return self
    
    def __next__(self) -> str:
        """
        Get the next chunk of content.
        
        Returns:
            The next chunk of content.
            
        Raises:
            StopIteration: When the content is exhausted.
        """
        # Check if we're finished
        if self.position >= len(self.content) or self.finished:
            raise StopIteration
        
        # Get the next chunk
        end = min(self.position + self.chunk_size, len(self.content))
        chunk = self.content[self.position:end]
        self.position = end
        
        # Simulate delay
        time.sleep(self.delay_sec)
        
        # Check for end of content
        if self.position >= len(self.content):
            self.finished = True
        
        return chunk