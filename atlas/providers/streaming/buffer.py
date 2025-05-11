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
from typing import Optional, List, Tuple, Callable, Any

logger = logging.getLogger(__name__)


class StreamBuffer:
    """Thread-safe buffer for streaming content.
    
    This class provides a buffer for streaming content that can be
    safely accessed from multiple threads. It supports operations
    like pausing, closing, and waiting for content.
    """
    
    def __init__(self, max_buffer_size: int = 1024 * 1024):
        """
        Initialize the stream buffer.
        
        Args:
            max_buffer_size: Maximum size of the buffer in characters.
        """
        self._buffer = deque()
        self._buffer_lock = threading.RLock()
        self._content_available = threading.Event()
        self._max_buffer_size = max_buffer_size
        self._current_size = 0
        self._closed = False
        self._last_activity_time = time.time()
        self._paused = False
    
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
        
        with self._buffer_lock:
            # Check if buffer is closed or paused
            if self._closed:
                return False
            
            if self._paused:
                # In paused state, we still accept content but don't notify consumers
                content_len = len(content)
                if self._current_size + content_len <= self._max_buffer_size:
                    self._buffer.append(content)
                    self._current_size += content_len
                    self._last_activity_time = time.time()
                    return True
                else:
                    # Buffer would overflow, only add what we can fit
                    available_space = self._max_buffer_size - self._current_size
                    if available_space > 0:
                        truncated = content[:available_space]
                        self._buffer.append(truncated)
                        self._current_size += len(truncated)
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
        with self._buffer_lock:
            self._closed = True
            self._content_available.set()  # Wake up any waiting consumers
    
    def clear(self) -> None:
        """
        Clear the buffer contents.
        """
        with self._buffer_lock:
            self._buffer.clear()
            self._current_size = 0
            self._content_available.clear()
    
    def pause(self) -> None:
        """
        Pause the buffer, preventing consumers from getting content.
        """
        with self._buffer_lock:
            self._paused = True
    
    def resume(self) -> None:
        """
        Resume the buffer, allowing consumers to get content.
        """
        with self._buffer_lock:
            was_paused = self._paused
            self._paused = False
            
            # If we have content and were previously paused, notify consumers
            if was_paused and self._buffer:
                self._content_available.set()
    
    @property
    def is_closed(self) -> bool:
        """Whether the buffer is closed."""
        return self._closed
    
    @property
    def is_paused(self) -> bool:
        """Whether the buffer is paused."""
        return self._paused
    
    @property
    def size(self) -> int:
        """Current size of the buffer in characters."""
        with self._buffer_lock:
            return self._current_size
    
    @property
    def idle_time(self) -> float:
        """Time in seconds since the last activity."""
        return time.time() - self._last_activity_time


class RateLimitedBuffer(StreamBuffer):
    """Stream buffer with rate limiting capabilities.
    
    This extension of StreamBuffer adds rate limiting to control
    the flow of content to consumers, useful for throttling output
    for display purposes or to manage resource usage.
    """
    
    def __init__(
        self,
        max_buffer_size: int = 1024 * 1024,
        tokens_per_second: Optional[float] = None,
        chars_per_token: int = 4
    ):
        """
        Initialize the rate-limited stream buffer.
        
        Args:
            max_buffer_size: Maximum size of the buffer in characters.
            tokens_per_second: Maximum tokens per second to output, or None for no limit.
            chars_per_token: Approximate characters per token for estimation.
        """
        super().__init__(max_buffer_size)
        self._tokens_per_second = tokens_per_second
        self._chars_per_token = chars_per_token
        self._last_get_time = time.time()
        self._rate_lock = threading.Lock()
    
    def get(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        Get content from the buffer with rate limiting.
        
        Args:
            timeout: How long to wait for content in seconds, or None to wait indefinitely.
            
        Returns:
            str: Content from the buffer, or None if timeout occurred or buffer is closed.
        """
        content = super().get(timeout)
        
        if content and self._tokens_per_second:
            self._apply_rate_limiting(content)
        
        return content
    
    def _apply_rate_limiting(self, content: str) -> None:
        """
        Apply rate limiting based on the size of the content.
        
        Args:
            content: The content that was retrieved.
        """
        with self._rate_lock:
            now = time.time()
            
            # Estimate tokens in this content
            estimated_tokens = len(content) / self._chars_per_token
            
            # If rate limiting is enabled, calculate delay
            if self._tokens_per_second and self._tokens_per_second > 0:
                # Calculate ideal time for this many tokens
                ideal_time = estimated_tokens / self._tokens_per_second
                
                # Calculate actual time elapsed
                elapsed = now - self._last_get_time
                
                # If we're going too fast, sleep to maintain rate
                if elapsed < ideal_time:
                    sleep_time = ideal_time - elapsed
                    time.sleep(sleep_time)
            
            self._last_get_time = time.time()
    
    @property
    def tokens_per_second(self) -> Optional[float]:
        """Get the current token rate limit."""
        return self._tokens_per_second
    
    @tokens_per_second.setter
    def tokens_per_second(self, value: Optional[float]) -> None:
        """Set the token rate limit."""
        self._tokens_per_second = value


class BatchingBuffer(StreamBuffer):
    """Stream buffer with content batching capabilities.
    
    This extension of StreamBuffer adds content batching to accumulate
    content until a specific condition is met (size, time, or delimiter).
    """
    
    def __init__(
        self,
        max_buffer_size: int = 1024 * 1024,
        batch_size: Optional[int] = None,
        batch_timeout: Optional[float] = None,
        batch_delimiter: Optional[str] = None
    ):
        """
        Initialize the batching stream buffer.
        
        Args:
            max_buffer_size: Maximum size of the buffer in characters.
            batch_size: Minimum characters to accumulate before returning, or None for no minimum.
            batch_timeout: Maximum time to wait for a batch in seconds, or None for no timeout.
            batch_delimiter: Delimiter that triggers a batch return, or None for no delimiter.
        """
        super().__init__(max_buffer_size)
        self._batch_size = batch_size
        self._batch_timeout = batch_timeout
        self._batch_delimiter = batch_delimiter
        self._last_batch_time = time.time()
        self._batch_lock = threading.Lock()
    
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