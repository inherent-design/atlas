"""
Thread-safe buffer system with flow control.

This module provides buffer implementations that can be used for inter-process
communication, streaming, and other data flow needs. The implementations are
thread-safe and support features like rate limiting and batching.
"""

import time
import uuid
from collections import deque
from datetime import datetime
from functools import wraps
from threading import Event, RLock
from typing import Any, ClassVar, Self, TypeAlias, TypeGuard

from atlas.core.errors import BufferError, ClosedBufferError
from atlas.core.logging import get_logger
from atlas.schemas.services import (
    BufferProtocol,
    batching_buffer_config_schema,
    buffer_config_schema,
    buffer_item_schema,
    rate_limited_buffer_config_schema,
)

# Type aliases for improved clarity
BufferItem: TypeAlias = dict[str, Any]
BufferSize: TypeAlias = int
TokenRate: TypeAlias = float
CharCount: TypeAlias = int

# Create a logger for this module
logger = get_logger(__name__)


def _ensure_open(method):
    """Decorator that ensures the buffer is open before executing a method.

    Args:
        method: The method to decorate.

    Returns:
        The decorated method.

    Raises:
        ClosedBufferError: If the buffer is closed.
    """

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """Check if buffer is open and then execute the method.

        Args:
            *args: Arguments passed to the method.
            **kwargs: Keyword arguments passed to the method.

        Returns:
            The result of the method.

        Raises:
            ClosedBufferError: If the buffer is closed.
        """
        if self.is_closed():
            raise ClosedBufferError("Cannot perform operation on closed buffer")
        return method(self, *args, **kwargs)

    return wrapper


def _ensure_not_paused(method):
    """Decorator to ensure the buffer is not paused.

    Args:
        method: The method to decorate.

    Returns:
        The decorated method.

    Note:
        This decorator assumes the method will be called on an instance with a
        _paused attribute and is expected to be used with MemoryBuffer or its subclasses.
    """

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """Check if buffer is not paused and then execute the method.

        Args:
            *args: Arguments passed to the method.
            **kwargs: Keyword arguments passed to the method.

        Returns:
            The result of the method if buffer is not paused, False otherwise.
        """
        if self._paused:
            logger.debug("Buffer is paused, operation skipped")
            return False
        return method(self, *args, **kwargs)

    return wrapper


class MemoryBuffer(BufferProtocol):
    """Thread-safe in-memory buffer implementation.

    This buffer provides a thread-safe mechanism for passing data between
    concurrent processes. It supports pushing, popping, and peeking at items,
    as well as pausing and resuming the buffer flow.
    """

    # Class constants
    MAX_DEFAULT_SIZE: ClassVar[int] = 1024 * 1024

    def __init__(self, max_size: int = MAX_DEFAULT_SIZE):
        """Initialize a new memory buffer.

        Args:
            max_size: The maximum size of the buffer in bytes.
        """
        self._buffer = deque()
        self._lock = RLock()
        self._not_empty = Event()
        self._not_full = Event()
        self._closed = False
        self._paused = False
        self._max_size = max_size
        self._current_size = 0

        # Set initial event states
        self._not_full.set()

        logger.debug(f"Created MemoryBuffer with max_size={max_size}")

    @_ensure_open
    @_ensure_not_paused
    def push(self, item: dict[str, Any]) -> bool:
        """Push an item to the buffer.

        Args:
            item: The item to push to the buffer.

        Returns:
            True if the item was pushed, False otherwise.

        Raises:
            ClosedBufferError: If the buffer is closed.
            BufferError: If there is an error pushing the item.
        """

        # Validate using schema
        try:
            validated_item = buffer_item_schema.load(
                {
                    "item_id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat(),
                    "data": item,
                    "metadata": {},
                }
            )
        except Exception as e:
            logger.error(f"Error validating buffer item: {e}")
            raise BufferError(f"Invalid buffer item: {e}")

        with self._lock:
            # Check if buffer is full
            if not self._not_full.is_set():
                logger.debug("Buffer is full, waiting for space")
                return False

            # Add item to buffer
            self._buffer.append(validated_item)

            # Update size tracking
            self._current_size += 1

            # Update events
            if self._current_size >= self._max_size:
                self._not_full.clear()

            # Signal that buffer is not empty
            self._not_empty.set()

            logger.debug(f"Pushed item to buffer, size now {self._current_size}")
            return True

    def pop(self) -> dict[str, Any] | None:
        """Pop an item from the buffer.

        Returns:
            The item if available, None if the buffer is empty.

        Note:
            Unlike other operations, pop is allowed on closed buffers
            to drain remaining items before final cleanup.
        """
        with self._lock:
            if not self._buffer:
                self._not_empty.clear()
                return None

            item = self._buffer.popleft()
            self._current_size -= 1

            # Update events
            if self._current_size == 0:
                self._not_empty.clear()

            # Signal that buffer is not full
            self._not_full.set()

            logger.debug(f"Popped item from buffer, size now {self._current_size}")
            return item

    @_ensure_open
    def peek(self) -> dict[str, Any] | None:
        """Peek at the next item in the buffer without removing it.

        Returns:
            The next item if available, None if the buffer is empty.

        Raises:
            ClosedBufferError: If the buffer is closed.
        """
        with self._lock:
            if not self._buffer:
                return None

            item = self._buffer[0]
            logger.debug("Peeked at buffer")
            return item

    @_ensure_open
    def clear(self) -> None:
        """Clear all items from the buffer.

        Raises:
            ClosedBufferError: If the buffer is closed.
        """
        with self._lock:
            self._buffer.clear()
            self._current_size = 0

            # Update events
            self._not_empty.clear()
            self._not_full.set()

            logger.debug("Cleared buffer")

    def is_closed(self) -> bool:
        """Check if the buffer is closed.

        Returns:
            True if the buffer is closed, False otherwise.
        """
        return self._closed

    def close(self) -> None:
        """Close the buffer.

        Once closed, no further operations can be performed on the buffer.
        """
        with self._lock:
            self._closed = True
            self._not_empty.set()  # Wake up any waiting consumers
            self._not_full.set()  # Wake up any waiting producers
            logger.debug("Closed buffer")

    def pause(self) -> Self:
        """Pause the buffer.

        While paused, push operations will be rejected, but pop operations
        will continue to work until the buffer is empty.

        Returns:
            Self for method chaining.
        """
        with self._lock:
            self._paused = True
            logger.debug("Paused buffer")
        return self

    def resume(self) -> Self:
        """Resume the buffer.

        Returns:
            Self for method chaining.
        """
        with self._lock:
            self._paused = False
            logger.debug("Resumed buffer")
        return self

    def wait_until_not_empty(self, timeout: float | None = None) -> bool:
        """Wait until the buffer has at least one item.

        Args:
            timeout: The maximum time to wait in seconds.

        Returns:
            True if the buffer has items, False if timeout occurred.
        """
        return self._not_empty.wait(timeout)

    def wait_until_not_full(self, timeout: float | None = None) -> bool:
        """Wait until the buffer has space for more items.

        Args:
            timeout: The maximum time to wait in seconds.

        Returns:
            True if the buffer has space, False if timeout occurred.
        """
        return self._not_full.wait(timeout)

    @property
    def size(self) -> int:
        """Get the current size of the buffer.

        Returns:
            The number of items in the buffer.
        """
        with self._lock:
            return self._current_size

    @property
    def max_size(self) -> int:
        """Get the maximum size of the buffer.

        Returns:
            The maximum number of items the buffer can hold.
        """
        return self._max_size

    @property
    def is_empty(self) -> bool:
        """Check if the buffer is empty.

        Returns:
            True if the buffer is empty, False otherwise.
        """
        with self._lock:
            return self._current_size == 0

    @property
    def is_full(self) -> bool:
        """Check if the buffer is full.

        Returns:
            True if the buffer is full, False otherwise.
        """
        with self._lock:
            return self._current_size >= self._max_size

    @property
    def is_paused(self) -> bool:
        """Check if the buffer is paused.

        Returns:
            True if the buffer is paused, False otherwise.
        """
        return self._paused


class RateLimitedBuffer(MemoryBuffer):
    """Thread-safe buffer with rate limiting capabilities.

    This buffer extends the basic memory buffer with rate limiting capabilities,
    allowing it to control the flow of data based on token rate and character count.
    """

    # Class constants
    DEFAULT_CHARS_PER_TOKEN: ClassVar[int] = 4

    def __init__(
        self,
        max_size: int = MemoryBuffer.MAX_DEFAULT_SIZE,
        tokens_per_second: float | None = None,
        chars_per_token: int = DEFAULT_CHARS_PER_TOKEN,
        initial_token_budget: float | None = None,
    ):
        """Initialize a new rate-limited buffer.

        Args:
            max_size: The maximum size of the buffer in bytes.
            tokens_per_second: The maximum tokens per second rate.
            chars_per_token: The number of characters per token.
            initial_token_budget: Optional initial token budget. If None, a default
                                value will be calculated based on other parameters.
        """
        super().__init__(max_size)
        self._tokens_per_second = tokens_per_second
        self._chars_per_token = chars_per_token

        # Initialize last_push_time to current time so first push gets proper budget
        self._last_push_time = time.time()

        # Initialize token budget
        if tokens_per_second is not None:
            if initial_token_budget is not None:
                # Use provided initial budget
                self._token_budget = initial_token_budget
            else:
                # Start with a more practical token budget - enough tokens for an average message
                # Approximately 50 characters worth, which should handle small messages
                self._token_budget = 50.0 / chars_per_token
        else:
            # No rate limiting
            self._token_budget = 0.0

        logger.debug(
            f"Created RateLimitedBuffer with tokens_per_second={tokens_per_second}, "
            f"chars_per_token={chars_per_token}, initial_budget={self._token_budget}"
        )

    @_ensure_open
    @_ensure_not_paused
    def push(self, item: dict[str, Any]) -> bool:
        """Push an item to the buffer with rate limiting.

        Args:
            item: The item to push to the buffer.

        Returns:
            True if the item was pushed, False otherwise.

        Raises:
            ClosedBufferError: If the buffer is closed.
            BufferError: If there is an error pushing the item.
        """

        if self._tokens_per_second is None:
            # No rate limiting, use parent implementation
            return super().push(item)

        # Apply rate limiting
        with self._lock:
            # Calculate token cost based on item size
            token_cost = self._calculate_token_cost(item)

            # Update token budget based on elapsed time
            current_time = time.time()
            elapsed = current_time - self._last_push_time
            self._token_budget += elapsed * self._tokens_per_second

            # Cap token budget at max of 2 seconds worth of tokens
            max_budget = 2 * self._tokens_per_second
            self._token_budget = min(self._token_budget, max_budget)

            # Log diagnostics at debug level
            logger.debug(
                f"Rate limiting - token cost: {token_cost}, current budget: {self._token_budget}, "
                f"rate: {self._tokens_per_second}/s, elapsed: {elapsed:.3f}s"
            )

            # Check if we have enough budget
            if self._token_budget < token_cost:
                logger.debug(
                    f"Rate limit exceeded, need {token_cost} tokens but have {self._token_budget}"
                )
                return False

            # Deduct tokens and update time
            self._token_budget -= token_cost
            self._last_push_time = current_time

            # Push item using parent implementation
            return super().push(item)

    def _calculate_token_cost(self, item: dict[str, Any]) -> float:
        """Calculate the token cost for an item.

        Args:
            item: The item to calculate the token cost for.

        Returns:
            The token cost for the item.
        """
        # Simple implementation - estimate string length in serialized item
        import json

        try:
            str_representation = json.dumps(item)
            token_count = len(str_representation) / self._chars_per_token
            return token_count
        except Exception:
            # Fallback to a default estimation if serialization fails
            return 10.0  # Default token cost


class BatchingBuffer(MemoryBuffer):
    """Thread-safe buffer with batching capabilities.

    This buffer extends the basic memory buffer with batching capabilities,
    allowing it to group items together for more efficient processing.
    """

    # Class constants
    DEFAULT_BATCH_SIZE: ClassVar[int] = 10
    DEFAULT_BATCH_TIMEOUT: ClassVar[float] = 1.0

    def __init__(
        self,
        max_size: int = MemoryBuffer.MAX_DEFAULT_SIZE,
        batch_size: int | None = DEFAULT_BATCH_SIZE,
        batch_timeout: float | None = DEFAULT_BATCH_TIMEOUT,
        batch_delimiter: str | None = None,
    ):
        """Initialize a new batching buffer.

        Args:
            max_size: The maximum size of the buffer in bytes.
            batch_size: The number of items to include in a batch.
            batch_timeout: The maximum time to wait for a full batch in seconds.
            batch_delimiter: An optional delimiter to add between batched items.
        """
        super().__init__(max_size)
        self._batch_size = batch_size
        self._batch_timeout = batch_timeout
        self._batch_delimiter = batch_delimiter
        self._batch_ready = Event()
        self._last_batch_time = time.time()

        logger.debug(
            f"Created BatchingBuffer with batch_size={batch_size}, "
            f"batch_timeout={batch_timeout}, batch_delimiter={batch_delimiter}"
        )

    @_ensure_open
    @_ensure_not_paused
    def push(self, item: dict[str, Any]) -> bool:
        """Push an item to the buffer and update batch status.

        Args:
            item: The item to push.

        Returns:
            True if the item was pushed, False if the buffer is full.

        Raises:
            ClosedBufferError: If the buffer is closed.
        """
        success = super().push(item)

        # If push was successful, update batch state
        if success:
            with self._lock:
                # Check if a batch is now ready
                if self._batch_size and len(self._buffer) >= self._batch_size:
                    self._batch_ready.set()

                # Reset batch timeout on first item
                if len(self._buffer) == 1:
                    self._last_batch_time = time.time()

        return success

    def pop(self) -> dict[str, Any] | None:
        """Pop a batch of items from the buffer.

        Returns:
            A batch of items if available, None if the buffer is empty.

        Note:
            Unlike other operations, pop is allowed on closed buffers
            to drain remaining items before final cleanup.
        """
        with self._lock:
            if not self._buffer:
                self._not_empty.clear()
                self._batch_ready.clear()
                return None

            # Check if we have a full batch or the timeout has expired
            current_time = time.time()

            # Handle cases where batch_timeout or batch_size might be None
            timeout_exists = self._batch_timeout is not None
            batch_timeout_expired = timeout_exists and (
                current_time - self._last_batch_time >= self._batch_timeout
            )

            size_exists = self._batch_size is not None
            full_batch_available = size_exists and (len(self._buffer) >= self._batch_size)

            if not (batch_timeout_expired or full_batch_available):
                # Not ready for a batch yet
                return None

            # Determine batch size
            batch_count = min(self._batch_size or 1, len(self._buffer))

            # Extract batch items
            batch_items = []
            for _ in range(batch_count):
                if not self._buffer:
                    break
                batch_items.append(self._buffer.popleft())
                self._current_size -= 1

            # Update events
            if self._current_size == 0:
                self._not_empty.clear()
                self._batch_ready.clear()

            # Signal that buffer is not full
            self._not_full.set()

            # Reset batch timeout
            self._last_batch_time = current_time

            # Combine batch into a single item
            if not batch_items:
                return None

            if len(batch_items) == 1:
                # Single item, no need to batch
                return batch_items[0]

            # Create a batch item
            batch_data = self._create_batch(batch_items)

            logger.debug(f"Created batch with {len(batch_items)} items")
            return batch_data

    def _create_batch(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        """Create a batch from a list of items.

        Args:
            items: The items to include in the batch.

        Returns:
            A batch item containing the items.
        """
        # Extract data from items
        data_items = [item.get("data", {}) for item in items]

        # Combine text content if present
        if self._batch_delimiter is not None:
            try:
                # Try to combine message content if available - adjust based on test data
                messages = []
                for item in data_items:
                    if "message" in item:
                        messages.append(item["message"])
                    elif "text" in item:
                        messages.append(item["text"])

                if messages:
                    combined_text = self._batch_delimiter.join(messages)
                    combined_data = {"items": data_items, "text": combined_text, "type": "batch"}
                else:
                    # Fallback for other data structures
                    combined_data = {"items": data_items, "type": "batch"}
            except (TypeError, AttributeError):
                # Fall back to list of items
                combined_data = {"items": data_items, "type": "batch"}
        else:
            # No delimiter, use list
            combined_data = {"items": data_items, "type": "batch"}

        # Create batch item
        batch_item = {
            "item_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "data": combined_data,
            "metadata": {
                "batch_size": len(items),
                "original_items": [
                    {"item_id": item.get("item_id"), "timestamp": item.get("timestamp")}
                    for item in items
                ],
            },
        }

        return batch_item

    def wait_for_batch(self, timeout: float | None = None) -> bool:
        """Wait until a batch is ready.

        Args:
            timeout: The maximum time to wait in seconds.

        Returns:
            True if a batch is ready, False if timeout occurred.
        """
        with self._lock:
            current_time = time.time()

            # Handle cases where batch_timeout or batch_size might be None
            timeout_exists = self._batch_timeout is not None
            batch_timeout_expired = timeout_exists and (
                current_time - self._last_batch_time >= self._batch_timeout
            )

            size_exists = self._batch_size is not None
            full_batch_available = size_exists and (len(self._buffer) >= self._batch_size)

            if batch_timeout_expired or full_batch_available:
                return True

        # Calculate remaining timeout time
        if timeout is not None and self._batch_timeout is not None:
            elapsed = time.time() - self._last_batch_time
            remaining = min(timeout, max(0, self._batch_timeout - elapsed))
        else:
            remaining = timeout

        # Wait for either not_empty or batch_ready
        return self._not_empty.wait(remaining)


def create_buffer(config: dict[str, Any]) -> BufferProtocol:
    """Create a buffer based on configuration.

    Args:
        config: The buffer configuration.

    Returns:
        A buffer instance.

    Raises:
        BufferError: If there is an error creating the buffer.
    """
    try:
        # Validate with schema
        buffer_type = config.get("buffer_type", "memory")

        if buffer_type == "rate_limited":
            config_data = rate_limited_buffer_config_schema.load(config)
            return RateLimitedBuffer(
                max_size=config_data.get("max_size", MemoryBuffer.MAX_DEFAULT_SIZE),
                tokens_per_second=config_data.get("tokens_per_second"),
                chars_per_token=config_data.get(
                    "chars_per_token", RateLimitedBuffer.DEFAULT_CHARS_PER_TOKEN
                ),
                initial_token_budget=config_data.get(
                    "initial_token_budget"
                ),  # Include new parameter
            )
        elif buffer_type == "batching":
            config_data = batching_buffer_config_schema.load(config)
            return BatchingBuffer(
                max_size=config_data.get("max_size", MemoryBuffer.MAX_DEFAULT_SIZE),
                batch_size=config_data.get("batch_size", BatchingBuffer.DEFAULT_BATCH_SIZE),
                batch_timeout=config_data.get(
                    "batch_timeout", BatchingBuffer.DEFAULT_BATCH_TIMEOUT
                ),
                batch_delimiter=config_data.get("batch_delimiter"),
            )
        else:
            # Default to memory buffer
            config_data = buffer_config_schema.load(config)
            return MemoryBuffer(max_size=config_data.get("max_size", MemoryBuffer.MAX_DEFAULT_SIZE))
    except Exception as e:
        logger.error(f"Error creating buffer: {e}")
        raise BufferError(f"Could not create buffer: {e}")


def is_memory_buffer(obj: Any) -> TypeGuard[MemoryBuffer]:
    """Check if an object is a MemoryBuffer.

    Args:
        obj: The object to check.

    Returns:
        True if the object is a MemoryBuffer, False otherwise.
    """
    return isinstance(obj, MemoryBuffer)


def is_rate_limited_buffer(obj: Any) -> TypeGuard[RateLimitedBuffer]:
    """Check if an object is a RateLimitedBuffer.

    Args:
        obj: The object to check.

    Returns:
        True if the object is a RateLimitedBuffer, False otherwise.
    """
    return isinstance(obj, RateLimitedBuffer)


def is_batching_buffer(obj: Any) -> TypeGuard[BatchingBuffer]:
    """Check if an object is a BatchingBuffer.

    Args:
        obj: The object to check.

    Returns:
        True if the object is a BatchingBuffer, False otherwise.
    """
    return isinstance(obj, BatchingBuffer)
