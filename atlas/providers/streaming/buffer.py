"""
Stream buffer implementation for Atlas providers.

This module provides thread-safe buffer implementations for handling
streaming content, allowing for controlled consumption with features
like pausing, rate limiting, and capacity management.
"""

import logging
import threading
import time
from collections import deque
from typing import Optional, List, Tuple, Callable, Any, Deque, Dict, Union

from atlas.providers.errors import ProviderConfigError
from atlas.schemas.streaming import (
    stream_buffer_config_schema,
    rate_limited_buffer_config_schema,
    batching_buffer_config_schema,
    validate_streaming_config
)

logger = logging.getLogger(__name__)


class StreamBuffer:
    """Thread-safe buffer for streaming content.
    
    This class provides a buffer for streaming content that can be
    safely accessed from multiple threads. It supports operations
    like pausing, closing, and waiting for content.
    """
    
    @validate_streaming_config
    def __init__(self, max_buffer_size: int = 1024 * 1024, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the stream buffer.
        
        Args:
            max_buffer_size: Maximum size of the buffer in characters.
            config: Optional configuration dictionary that will be validated using schema.
                   If provided, it overrides the max_buffer_size parameter.
        """
        from atlas.schemas.streaming import stream_buffer_config_schema
        
        # Basic validation
        if max_buffer_size <= 0:
            raise ValueError("Maximum buffer size must be positive")
        
        # Convert parameters to config dict for validation if None
        if config is None:
            config = {
                "max_buffer_size": max_buffer_size,
                "paused": False,
                "closed": False
            }
            
        # If config is provided via parameter, it's already been validated by the decorator
        # If we created it above, validate it now
        if not getattr(config, "_validated", False):
            try:
                # Explicitly validate the config
                config = stream_buffer_config_schema.load(config)
                # Mark as validated to avoid duplicate validation
                config._validated = True
            except Exception as e:
                logger.error(f"Error validating stream buffer config: {e}")
                # Use original parameters as fallback
                config = {
                    "max_buffer_size": max_buffer_size,
                    "paused": False,
                    "closed": False
                }
            
        # If config is an already instantiated buffer (via post_load), return it
        if isinstance(config, StreamBuffer):
            return config
        
        # Extract configuration
        max_buffer_size = config.get("max_buffer_size", max_buffer_size)
        initial_paused = config.get("paused", False)
        initial_closed = config.get("closed", False)

        # Initialize buffer with thread-safe components
        self._buffer: Deque[str] = deque()
        self._buffer_lock = threading.RLock()
        self._content_available = threading.Event()
        self._max_buffer_size = max_buffer_size
        self._current_size = 0
        self._closed = False
        self._last_activity_time = time.time()
        self._paused = False
        
        # Additional locks for better thread safety
        self._state_lock = threading.RLock()  # Lock for state changes (pause/resume/close)
        self._activity_lock = threading.Lock()  # Lock for activity time updates
        
        # Apply initial state if configured
        if initial_closed:
            self.close()
        if initial_paused:
            self.pause()
            
        # Store validated config
        self._config = config
    
    def add(self, content: str) -> bool:
        """
        Add content to the buffer.
        
        Args:
            content: Content to add.
            
        Returns:
            bool: True if content was added, False if buffer is closed or full.
        """
        if not content:
            return True  # Nothing to add
        
        # Check if buffer is closed (quick check without lock)
        if self._closed:
            return False
        
        with self._buffer_lock:
            # Double-check if buffer is closed (could have changed)
            if self._closed:
                return False
            
            # Get the buffer state with proper lock
            with self._state_lock:
                is_paused = self._paused
            
            if is_paused:
                # In paused state, we still accept content but don't notify consumers
                content_len = len(content)
                if self._current_size + content_len <= self._max_buffer_size:
                    self._buffer.append(content)
                    self._current_size += content_len
                    
                    # Update activity time with proper lock
                    with self._activity_lock:
                        self._last_activity_time = time.time()
                    
                    return True
                else:
                    # Buffer would overflow, only add what we can fit
                    available_space = self._max_buffer_size - self._current_size
                    if available_space > 0:
                        truncated = content[:available_space]
                        self._buffer.append(truncated)
                        self._current_size += len(truncated)
                        
                        # Update activity time with proper lock
                        with self._activity_lock:
                            self._last_activity_time = time.time()
                    
                    logger.warning(
                        f"Stream buffer overflow in paused state. Dropped {len(content) - available_space} characters."
                    )
                    return False
            
            # Normal operation (not paused)
            content_len = len(content)
            if self._current_size + content_len <= self._max_buffer_size:
                self._buffer.append(content)
                self._current_size += content_len
                self._content_available.set()
                
                # Update activity time with proper lock
                with self._activity_lock:
                    self._last_activity_time = time.time()
                
                return True
            else:
                # Buffer would overflow, only add what we can fit
                available_space = self._max_buffer_size - self._current_size
                if available_space > 0:
                    truncated = content[:available_space]
                    self._buffer.append(truncated)
                    self._current_size += len(truncated)
                    self._content_available.set()
                    
                    # Update activity time with proper lock
                    with self._activity_lock:
                        self._last_activity_time = time.time()
                
                logger.warning(
                    f"Stream buffer overflow. Dropped {len(content) - available_space} characters."
                )
                return False
    
    def get(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        Get content from the buffer, waiting if none is available.
        
        Args:
            timeout: How long to wait for content in seconds, or None to wait indefinitely.
            
        Returns:
            str: Content from the buffer, or None if timeout occurred or buffer is closed.
        """
        # Fast path for closed empty buffer
        with self._buffer_lock:
            if self._closed and not self._buffer:
                return None
            
            if self._paused:
                # In paused state, don't provide content
                return ""
            
            # If content is immediately available, return it without waiting
            if self._buffer:
                content = "".join(self._buffer)
                self._buffer.clear()
                self._current_size = 0
                self._content_available.clear()
                return content
        
        # Wait for content to become available
        if not self._content_available.wait(timeout):
            return None  # Timeout
        
        # Get content after wait
        with self._buffer_lock:
            if not self._buffer:
                self._content_available.clear()
                return ""
            
            content = "".join(self._buffer)
            self._buffer.clear()
            self._current_size = 0
            self._content_available.clear()
            return content
    
    def peek(self) -> str:
        """
        Peek at the buffer content without removing it.
        
        Returns:
            str: Current content in the buffer.
        """
        with self._buffer_lock:
            return "".join(self._buffer)
    
    def close(self) -> None:
        """
        Close the buffer, preventing further additions.
        """
        # Use the state lock for state changes
        with self._state_lock:
            # Only set if not already closed
            if not self._closed:
                self._closed = True
                self._content_available.set()  # Wake up any waiting consumers
                
                # Log the state change
                logger.debug("Buffer closed")
    
    def clear(self) -> None:
        """
        Clear the buffer contents.
        """
        # Use both locks for this operation that affects both content and state
        with self._buffer_lock, self._state_lock:
            self._buffer.clear()
            self._current_size = 0
            self._content_available.clear()
            
            # Update activity time
            with self._activity_lock:
                self._last_activity_time = time.time()
            
            # Log the operation
            logger.debug("Buffer cleared")
    
    def pause(self) -> None:
        """
        Pause the buffer, preventing consumers from getting content.
        """
        # Use the state lock for state changes
        with self._state_lock:
            # Only set if not already paused
            if not self._paused:
                self._paused = True
                
                # Log the state change
                logger.debug("Buffer paused")
    
    def resume(self) -> None:
        """
        Resume the buffer, allowing consumers to get content.
        """
        # Use the state lock for state changes
        with self._state_lock:
            was_paused = self._paused
            
            # Only change if currently paused
            if was_paused:
                self._paused = False
                
                # Check if we have content with buffer lock
                has_content = False
                with self._buffer_lock:
                    has_content = bool(self._buffer)
                
                # If we have content and were previously paused, notify consumers
                if has_content:
                    self._content_available.set()
                
                # Log the state change
                logger.debug("Buffer resumed")
    
    @property
    def is_closed(self) -> bool:
        """Whether the buffer is closed."""
        with self._state_lock:
            return self._closed
    
    @property
    def is_paused(self) -> bool:
        """Whether the buffer is paused."""
        with self._state_lock:
            return self._paused
    
    @property
    def size(self) -> int:
        """Current size of the buffer in characters."""
        with self._buffer_lock:
            return self._current_size
    
    @property
    def idle_time(self) -> float:
        """Time in seconds since the last activity."""
        with self._activity_lock:
            last_activity = self._last_activity_time
        return time.time() - last_activity


class RateLimitedBuffer(StreamBuffer):
    """Stream buffer with rate limiting capabilities.
    
    This extension of StreamBuffer adds rate limiting to control
    the flow of content to consumers, useful for throttling output
    for display purposes or to manage resource usage.
    """
    
    @validate_streaming_config
    def __init__(
        self,
        max_buffer_size: int = 1024 * 1024,
        tokens_per_second: Optional[float] = None,
        chars_per_token: int = 4,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the rate-limited stream buffer.
        
        Args:
            max_buffer_size: Maximum size of the buffer in characters.
            tokens_per_second: Maximum tokens per second to output, or None for no limit.
            chars_per_token: Approximate characters per token for estimation.
            config: Optional configuration dictionary that will be validated using schema.
                   If provided, it overrides other parameters.
        """
        from atlas.schemas.streaming import rate_limited_buffer_config_schema
        
        # Basic validation
        if max_buffer_size <= 0:
            raise ValueError("Maximum buffer size must be positive")
        if tokens_per_second is not None and tokens_per_second < 0:
            raise ValueError("Tokens per second must be non-negative")
        
        # Convert parameters to config dict for validation if None
        if config is None:
            config = {
                "max_buffer_size": max_buffer_size,
                "tokens_per_second": tokens_per_second,
                "chars_per_token": chars_per_token,
                "paused": False,
                "closed": False
            }
            
        # If config is provided via parameter, it's already been validated by the decorator
        # If we created it above, validate it now
        if not getattr(config, "_validated", False):
            try:
                # Explicitly validate the config
                config = rate_limited_buffer_config_schema.load(config)
                # Mark as validated to avoid duplicate validation
                config._validated = True
            except Exception as e:
                logger.error(f"Error validating rate limited buffer config: {e}")
                # Use original parameters as fallback
                config = {
                    "max_buffer_size": max_buffer_size,
                    "tokens_per_second": tokens_per_second,
                    "chars_per_token": chars_per_token,
                    "paused": False,
                    "closed": False
                }
        
        # If config is an already instantiated buffer (via post_load), return it
        if isinstance(config, StreamBuffer):
            return config
        
        # Extract configuration
        max_buffer_size = config.get("max_buffer_size", max_buffer_size)
        tokens_per_second = config.get("tokens_per_second", tokens_per_second)
        chars_per_token = config.get("chars_per_token", chars_per_token)
        initial_paused = config.get("paused", False)
        initial_closed = config.get("closed", False)
        
        # Initialize parent with parameters but without config to avoid recursion
        super().__init__(max_buffer_size=max_buffer_size)
        
        # Rate limiting configuration
        self._tokens_per_second = tokens_per_second
        self._chars_per_token = chars_per_token
        self._last_get_time = time.time()
        self._rate_lock = threading.RLock()  # Use RLock for thread safety
        
        # Apply initial state if configured
        if initial_closed:
            self.close()
        if initial_paused:
            self.pause()
            
        # Store validated config
        self._config = config
    
    def get(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        Get content from the buffer with rate limiting.
        
        Args:
            timeout: How long to wait for content in seconds, or None to wait indefinitely.
            
        Returns:
            str: Content from the buffer, or None if timeout occurred or buffer is closed.
        """
        # Get content from the parent class method
        content = super().get(timeout)
        
        # Apply rate limiting if content was retrieved and rate limiting is enabled
        if content and self._tokens_per_second is not None:
            self._apply_rate_limiting(content)
        
        return content
    
    def _apply_rate_limiting(self, content: str) -> None:
        """
        Apply rate limiting based on the size of the content.
        
        Args:
            content: The content that was retrieved.
        """
        # Use RLock for thread safety
        with self._rate_lock:
            now = time.time()
            
            # Estimate tokens in this content
            content_length = len(content)
            estimated_tokens = content_length / self._chars_per_token
            
            # If rate limiting is enabled, calculate delay
            if self._tokens_per_second is not None and self._tokens_per_second > 0:
                # Calculate ideal time for this many tokens
                ideal_time = estimated_tokens / self._tokens_per_second
                
                # Calculate actual time elapsed
                elapsed = now - self._last_get_time
                
                # If we're going too fast, sleep to maintain rate
                if elapsed < ideal_time:
                    sleep_time = ideal_time - elapsed
                    
                    # Log rate limiting
                    logger.debug(
                        f"Rate limiting: {estimated_tokens:.1f} tokens, "
                        f"sleeping for {sleep_time:.3f}s to maintain {self._tokens_per_second} tokens/sec"
                    )
                    
                    # Apply rate limiting by sleeping
                    time.sleep(sleep_time)
            
            # Update last get time after any sleep
            self._last_get_time = time.time()
            
            # Log token processing stats
            logger.debug(
                f"Processed chunk: {content_length} chars, ~{estimated_tokens:.1f} tokens, "
                f"rate: {estimated_tokens / max(0.001, elapsed):.1f} tokens/sec"
            )
    
    @property
    def tokens_per_second(self) -> Optional[float]:
        """Get the current token rate limit."""
        with self._rate_lock:
            return self._tokens_per_second
    
    @tokens_per_second.setter
    def tokens_per_second(self, value: Optional[float]) -> None:
        """Set the token rate limit."""
        # Validate new value
        if value is not None and value < 0:
            raise ValueError("Tokens per second must be non-negative")
        
        # Update with thread safety
        with self._rate_lock:
            self._tokens_per_second = value
            
            # Log rate change
            if value is None:
                logger.debug("Rate limiting disabled")
            else:
                logger.debug(f"Rate limit set to {value} tokens/sec")


class BatchingBuffer(StreamBuffer):
    """Stream buffer with content batching capabilities.
    
    This extension of StreamBuffer adds content batching to accumulate
    content until a specific condition is met (size, time, or delimiter).
    """
    
    @validate_streaming_config
    def __init__(
        self,
        max_buffer_size: int = 1024 * 1024,
        batch_size: Optional[int] = None,
        batch_timeout: Optional[float] = None,
        batch_delimiter: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the batching stream buffer.
        
        Args:
            max_buffer_size: Maximum size of the buffer in characters.
            batch_size: Minimum characters to accumulate before returning, or None for no minimum.
            batch_timeout: Maximum time to wait for a batch in seconds, or None for no timeout.
            batch_delimiter: Delimiter that triggers a batch return, or None for no delimiter.
            config: Optional configuration dictionary that will be validated using schema.
                   If provided, it overrides other parameters.
        """
        # Basic validation
        if max_buffer_size <= 0:
            raise ValueError("Maximum buffer size must be positive")
        if batch_size is not None and batch_size <= 0:
            raise ValueError("Batch size must be positive")
        if batch_timeout is not None and batch_timeout <= 0:
            raise ValueError("Batch timeout must be positive")
            
        # If config is provided, it has been validated by the decorator
        if config is not None:
            if isinstance(config, dict):
                # Extract parameters from config if not already a buffer
                max_buffer_size = config.get("max_buffer_size", max_buffer_size)
                batch_size = config.get("batch_size", batch_size)
                batch_timeout = config.get("batch_timeout", batch_timeout)
                batch_delimiter = config.get("batch_delimiter", batch_delimiter)
                initial_paused = config.get("paused", False)
                initial_closed = config.get("closed", False)
            else:
                # Config is already an instantiated buffer created by the schema
                return config
        
        # Initialize parent with parameters but without config to avoid recursion
        StreamBuffer.__init__(self, max_buffer_size=max_buffer_size)
        
        self._batch_size = batch_size
        self._batch_timeout = batch_timeout
        self._batch_delimiter = batch_delimiter
        self._last_batch_time = time.time()
        self._batch_lock = threading.Lock()
        
        # Apply initial state if configured
        if config is not None:
            if initial_closed:
                self.close()
            if initial_paused:
                self.pause()
    
    def get(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        Get content from the buffer with batching.
        
        Args:
            timeout: How long to wait for content in seconds, or None to wait indefinitely.
            
        Returns:
            str: Content from the buffer, or None if timeout occurred or buffer is closed.
        """
        # Adjust timeout based on batch_timeout if needed
        if self._batch_timeout is not None:
            if timeout is None:
                timeout = self._batch_timeout
            else:
                timeout = min(timeout, self._batch_timeout)
        
        with self._batch_lock:
            # Check if we have a batch ready
            peek_content = self.peek()
            
            # Check if we have enough content for a batch
            if self._batch_size and len(peek_content) >= self._batch_size:
                return super().get(0)  # No wait needed, batch size reached
            
            # Check if we have a delimiter in the content
            if self._batch_delimiter and self._batch_delimiter in peek_content:
                return super().get(0)  # No wait needed, delimiter found
            
            # Check if batch timeout has elapsed
            if (
                self._batch_timeout 
                and peek_content 
                and time.time() - self._last_batch_time >= self._batch_timeout
            ):
                self._last_batch_time = time.time()
                return super().get(0)  # No wait needed, timeout elapsed
        
        # No batch ready, wait for more content
        content = super().get(timeout)
        
        if content:
            self._last_batch_time = time.time()
        
        return content