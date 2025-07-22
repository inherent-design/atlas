"""
Unit tests for the buffer service in the core services module.

Tests the thread-safe buffer implementation, including memory buffer,
rate-limited buffer, and batching buffer.
"""

import threading
import time
import unittest
from unittest.mock import patch

from atlas.core.errors import BufferError, ClosedBufferError
from atlas.services.buffer import (
    BatchingBuffer,
    MemoryBuffer,
    RateLimitedBuffer,
    create_buffer,
    is_batching_buffer,
    is_memory_buffer,
    is_rate_limited_buffer,
)


class TestMemoryBuffer(unittest.TestCase):
    """Tests for the MemoryBuffer class."""

    def setUp(self):
        """Set up a new buffer for each test."""
        self.buffer = MemoryBuffer(max_size=10)

    def test_push_and_pop(self):
        """Test basic push and pop operations."""
        # Push an item
        result = self.buffer.push({"message": "test"})

        # Check push succeeded
        self.assertTrue(result)
        self.assertEqual(self.buffer.size, 1)
        self.assertFalse(self.buffer.is_empty)

        # Pop the item
        item = self.buffer.pop()

        # Check item data
        self.assertIsNotNone(item)
        self.assertEqual(item["data"]["message"], "test")
        self.assertIn("item_id", item)
        self.assertIn("timestamp", item)

        # Buffer should now be empty
        self.assertEqual(self.buffer.size, 0)
        self.assertTrue(self.buffer.is_empty)

        # Popping from empty buffer should return None
        self.assertIsNone(self.buffer.pop())

    def test_peek(self):
        """Test peeking at the next item without removing it."""
        # Push an item
        self.buffer.push({"message": "test"})

        # Peek at the item
        item = self.buffer.peek()

        # Item should still be in buffer
        self.assertIsNotNone(item)
        self.assertEqual(item["data"]["message"], "test")
        self.assertEqual(self.buffer.size, 1)

        # Peek again should return same item
        second_peek = self.buffer.peek()
        self.assertEqual(second_peek["item_id"], item["item_id"])

        # Peeking at empty buffer should return None
        self.buffer.pop()
        self.assertIsNone(self.buffer.peek())

    def test_buffer_full(self):
        """Test behavior when buffer is full."""
        # Fill the buffer to capacity
        for i in range(10):
            result = self.buffer.push({"index": i})
            self.assertTrue(result)

        # Buffer should be full
        self.assertTrue(self.buffer.is_full)

        # Pushing to full buffer should fail
        result = self.buffer.push({"overflow": True})
        self.assertFalse(result)

        # Size should still be max_size
        self.assertEqual(self.buffer.size, 10)

        # After popping one item, we should be able to push again
        self.buffer.pop()
        self.assertFalse(self.buffer.is_full)

        result = self.buffer.push({"new_item": True})
        self.assertTrue(result)

    def test_clear(self):
        """Test clearing the buffer."""
        # Add some items
        for i in range(5):
            self.buffer.push({"index": i})

        # Clear the buffer
        self.buffer.clear()

        # Buffer should be empty
        self.assertEqual(self.buffer.size, 0)
        self.assertTrue(self.buffer.is_empty)
        self.assertIsNone(self.buffer.pop())

    def test_close(self):
        """Test closing the buffer."""
        # Add an item
        self.buffer.push({"message": "test"})

        # Close the buffer
        self.buffer.close()

        # Buffer should be closed
        self.assertTrue(self.buffer.is_closed())

        # Operations should fail on closed buffer
        with self.assertRaises(ClosedBufferError):
            self.buffer.push({"message": "after close"})

        with self.assertRaises(ClosedBufferError):
            self.buffer.peek()

        with self.assertRaises(ClosedBufferError):
            self.buffer.clear()

        # Pop should still work to drain buffer
        item = self.buffer.pop()
        self.assertIsNotNone(item)
        self.assertEqual(item["data"]["message"], "test")

    def test_pause_resume(self):
        """Test pausing and resuming the buffer."""
        # Pause the buffer
        self.buffer.pause()

        # Push should fail when paused
        result = self.buffer.push({"message": "while paused"})
        self.assertFalse(result)
        self.assertTrue(self.buffer.is_empty)

        # Resume the buffer
        self.buffer.resume()

        # Push should work now
        result = self.buffer.push({"message": "after resume"})
        self.assertTrue(result)
        self.assertEqual(self.buffer.size, 1)

    def test_wait_until_not_empty(self):
        """Test waiting until buffer is not empty."""

        def add_delayed_item():
            """Add an item to the buffer after a delay."""
            time.sleep(0.1)
            self.buffer.push({"delayed": True})

        # Start thread to add item after delay
        thread = threading.Thread(target=add_delayed_item)
        thread.start()

        # Wait until buffer is not empty
        result = self.buffer.wait_until_not_empty(timeout=0.5)

        # Should return True since item was added
        self.assertTrue(result)
        self.assertEqual(self.buffer.size, 1)

        # Wait for thread to finish
        thread.join()

    def test_wait_until_not_full(self):
        """Test waiting until buffer is not full."""
        # Fill buffer
        for i in range(10):
            self.buffer.push({"index": i})

        def remove_delayed_item():
            """Remove an item from the buffer after a delay."""
            time.sleep(0.1)
            self.buffer.pop()

        # Start thread to remove item after delay
        thread = threading.Thread(target=remove_delayed_item)
        thread.start()

        # Wait until buffer is not full
        result = self.buffer.wait_until_not_full(timeout=0.5)

        # Should return True since item was removed
        self.assertTrue(result)
        self.assertEqual(self.buffer.size, 9)

        # Wait for thread to finish
        thread.join()

    def test_properties(self):
        """Test buffer property accessors."""
        # Initial state
        self.assertEqual(self.buffer.max_size, 10)
        self.assertEqual(self.buffer.size, 0)
        self.assertTrue(self.buffer.is_empty)
        self.assertFalse(self.buffer.is_full)
        self.assertFalse(self.buffer.is_paused)
        self.assertFalse(self.buffer.is_closed())

        # After changes
        self.buffer.push({"message": "test"})
        self.buffer.pause()

        self.assertEqual(self.buffer.size, 1)
        self.assertFalse(self.buffer.is_empty)
        self.assertFalse(self.buffer.is_full)
        self.assertTrue(self.buffer.is_paused)

        # After close
        self.buffer.close()
        self.assertTrue(self.buffer.is_closed())


class TestRateLimitedBuffer(unittest.TestCase):
    """Tests for the RateLimitedBuffer class."""

    def setUp(self):
        """Set up a new buffer for each test."""
        # Create a buffer without rate limiting for most tests
        self.buffer = RateLimitedBuffer(
            max_size=10,
            tokens_per_second=None,  # No rate limiting for basic tests
        )

    def test_basic_push_without_rate_limiting(self):
        """Test basic push operations with no rate limiting."""
        # Use buffer created in setUp which has no rate limiting
        result = self.buffer.push({"message": "test"})

        # This should succeed as there's no rate limiting
        self.assertTrue(result)
        self.assertEqual(self.buffer.size, 1)

        # Pop the item
        item = self.buffer.pop()

        # Check item data
        self.assertIsNotNone(item)
        self.assertEqual(item["data"]["message"], "test")

    def test_no_rate_limiting(self):
        """Test buffer with no rate limiting can push many items."""
        # Should be able to push many items quickly with no rate limiting
        for i in range(10):
            result = self.buffer.push({"index": i})
            self.assertTrue(result)

        # Buffer should be full
        self.assertTrue(self.buffer.is_full)

    def test_token_cost_calculation(self):
        """Test token cost calculation for items."""
        # Create a rate limited buffer for testing cost calculation
        rate_limited = RateLimitedBuffer(
            max_size=10, tokens_per_second=10.0, chars_per_token=4
        )

        # Try different item sizes
        small_item = {"small": "item"}
        large_item = {"large": "item" * 10}

        small_cost = rate_limited._calculate_token_cost(small_item)
        large_cost = rate_limited._calculate_token_cost(large_item)

        # Larger item should have higher token cost
        self.assertGreater(large_cost, small_cost)

    def test_token_budget_initialization(self):
        """Test that token budget is initialized correctly."""
        # Create a buffer with rate limiting
        rate_limited = RateLimitedBuffer(
            max_size=10,
            tokens_per_second=10.0,  # 10 tokens per second
            chars_per_token=4,  # 4 chars per token
        )

        # Check initial token budget
        # Default is now 50.0 / chars_per_token = 50.0 / 4 = 12.5 (new implementation)
        initial_budget = rate_limited._token_budget

        # Check reasonable initial budget
        self.assertGreater(initial_budget, 0.0)
        self.assertEqual(initial_budget, 50.0 / 4)  # Verify matches new implementation

    def test_token_budget_update(self):
        """Test that token budget updates over time."""
        # The token budget is updated during the push operation, not automatically over time.
        # This test verifies this behavior.

        # Create a buffer with rate limiting
        rate_limited = RateLimitedBuffer(
            max_size=10,
            tokens_per_second=100.0,  # 100 tokens per second for clear changes
            chars_per_token=4,
        )

        # Get initial budget
        initial_budget = rate_limited._token_budget

        # Set a non-zero last_push_time to simulate a previous push
        with rate_limited._lock:
            rate_limited._last_push_time = time.time() - 0.1  # 100ms ago

        # Create a test item that's small enough to succeed with our initial budget
        small_item = {"x": "y"}  # Very small

        # Push should succeed and update the budget
        result = rate_limited.push(small_item)

        # After pushing, the budget should be updated
        post_push_budget = rate_limited._token_budget

        # Since the budget is updated during push and we've modified last_push_time,
        # the post-push budget should be higher than initial due to time elapsed
        self.assertTrue(result, "First push with small item should succeed")
        self.assertGreater(
            post_push_budget,
            initial_budget,
            "Budget should increase after push due to time elapsed",
        )

        # Now test a more controlled scenario to verify budget calculation
        # Create a fresh buffer for a clean test
        test_buffer = RateLimitedBuffer(
            max_size=10,
            tokens_per_second=50.0,  # 50 tokens per second
            chars_per_token=4,
        )

        # Set up controlled timing values
        controlled_start_time = time.time() - 2.0  # 2 seconds ago
        with test_buffer._lock:
            test_buffer._token_budget = 10.0  # Start with 10 tokens
            test_buffer._last_push_time = controlled_start_time

        # Create a test item with known token cost
        test_item = {"message": "test message"}
        token_cost = test_buffer._calculate_token_cost(test_item)

        # Now push - this should succeed with our increased budget
        push_result = test_buffer.push(test_item)
        controlled_end_budget = test_buffer._token_budget

        # Verify the push succeeded and budget was updated correctly
        self.assertTrue(push_result, "Push should succeed with increased budget")
        self.assertGreater(
            controlled_end_budget,
            10.0,
            "Budget should increase overall despite token cost",
        )

    def test_rate_limiting_basic(self):
        """Test basic rate limiting by directly manipulating token budget."""
        # Create a buffer with rate limiting
        rate_limited = RateLimitedBuffer(
            max_size=10, tokens_per_second=10.0, chars_per_token=4
        )

        # Create a test item
        test_item = {"message": "test message"}

        # Calculate token cost
        token_cost = rate_limited._calculate_token_cost(test_item)

        # Set token budget to double the cost (should succeed)
        rate_limited._token_budget = token_cost * 2
        result = rate_limited.push(test_item)
        remaining_budget = rate_limited._token_budget

        self.assertTrue(result)
        self.assertLess(remaining_budget, token_cost * 2)

        # Clear the buffer
        rate_limited.clear()

        # Set token budget to half the cost (should fail)
        rate_limited._token_budget = token_cost * 0.5
        result = rate_limited.push(test_item)

        self.assertFalse(result)

    def test_no_rate_limiting(self):
        """Test buffer with no rate limiting."""
        # Create buffer with no rate limiting
        buffer = RateLimitedBuffer(max_size=10, tokens_per_second=None)

        # Should be able to push many items quickly
        for i in range(10):
            result = buffer.push({"index": i})
            self.assertTrue(result)

        # Buffer should be full
        self.assertTrue(buffer.is_full)

    def test_token_cost_calculation(self):
        """Test token cost calculation for items."""
        # Try different item sizes
        small_cost = self.buffer._calculate_token_cost({"small": "item"})
        large_cost = self.buffer._calculate_token_cost({"large": "item" * 10})

        # Larger item should have higher token cost
        self.assertGreater(large_cost, small_cost)


class TestBatchingBuffer(unittest.TestCase):
    """Tests for the BatchingBuffer class."""

    def setUp(self):
        """Set up a new buffer for each test."""
        self.buffer = BatchingBuffer(
            max_size=20, batch_size=3, batch_timeout=0.2, batch_delimiter=", "
        )

    def test_batching_by_size(self):
        """Test batching items by size."""
        # Push 3 items (batch size)
        for i in range(3):
            self.buffer.push({"message": f"item{i}"})

        # Pop should return a batch
        batch = self.buffer.pop()

        # Check batch properties
        self.assertIsNotNone(batch)
        self.assertEqual(batch["data"]["type"], "batch")
        self.assertEqual(len(batch["data"]["items"]), 3)
        self.assertEqual(batch["metadata"]["batch_size"], 3)

    def test_batching_by_timeout(self):
        """Test batching items by timeout."""
        # Push fewer than batch size
        self.buffer.push({"message": "item1"})

        # Wait for timeout
        time.sleep(0.3)

        # Pop should return single item batch due to timeout
        batch = self.buffer.pop()

        # Check batch
        self.assertIsNotNone(batch)
        self.assertEqual(batch["data"]["message"], "item1")

    def test_text_combining(self):
        """Test text combining with delimiter."""
        # Push items with text content
        self.buffer.push({"text": "Hello"})
        self.buffer.push({"text": "World"})
        self.buffer.push({"text": "Test"})

        # Pop should return batch with combined text
        batch = self.buffer.pop()

        # Check combined text
        self.assertIsNotNone(batch)
        self.assertIn("text", batch["data"])
        self.assertEqual(batch["data"]["text"], "Hello, World, Test")

    def test_wait_for_batch(self):
        """Test waiting for batch to be ready."""
        # Check initially - no batch ready
        self.assertFalse(self.buffer.wait_for_batch(timeout=0.01))

        # Add items to buffer
        self.buffer.push({"message": "item1"})
        self.buffer.push({"message": "item2"})
        self.buffer.push({"message": "item3"})  # This should make a full batch

        # Now a batch should be ready
        self.assertTrue(self.buffer.wait_for_batch(timeout=0.01))

        # Pop the batch
        batch = self.buffer.pop()
        self.assertIsNotNone(batch)


class TestBufferCreation(unittest.TestCase):
    """Tests for buffer creation and type checking functions."""

    def test_create_memory_buffer(self):
        """Test creating a memory buffer."""
        buffer = create_buffer({"buffer_type": "memory", "max_size": 100})
        self.assertTrue(is_memory_buffer(buffer))
        self.assertEqual(buffer.max_size, 100)

    def test_create_rate_limited_buffer(self):
        """Test creating a rate limited buffer."""
        buffer = create_buffer(
            {
                "buffer_type": "rate_limited",
                "max_size": 100,
                "tokens_per_second": 5.0,
                "chars_per_token": 5,
            }
        )
        self.assertTrue(is_rate_limited_buffer(buffer))
        self.assertEqual(buffer.max_size, 100)

    def test_create_batching_buffer(self):
        """Test creating a batching buffer."""
        buffer = create_buffer(
            {
                "buffer_type": "batching",
                "max_size": 100,
                "batch_size": 5,
                "batch_timeout": 0.5,
                "batch_delimiter": "|",
            }
        )
        self.assertTrue(is_batching_buffer(buffer))
        self.assertEqual(buffer.max_size, 100)

    def test_create_default_buffer(self):
        """Test creating a buffer with default settings."""
        buffer = create_buffer({})
        self.assertTrue(is_memory_buffer(buffer))
        self.assertEqual(buffer.max_size, MemoryBuffer.MAX_DEFAULT_SIZE)

    def test_create_invalid_buffer(self):
        """Test creating a buffer with invalid config raises error."""
        # Using a patch to check the function raises the right error
        with patch(
            "atlas.core.services.buffer.buffer_config_schema.load",
            side_effect=ValueError("Invalid config"),
        ):
            with self.assertRaises(BufferError):
                create_buffer({"buffer_type": "invalid"})

    def test_type_guards(self):
        """Test type guard functions."""
        memory_buffer = MemoryBuffer()
        rate_limited_buffer = RateLimitedBuffer()
        batching_buffer = BatchingBuffer()

        # Type guard tests
        self.assertTrue(is_memory_buffer(memory_buffer))
        self.assertTrue(is_memory_buffer(rate_limited_buffer))  # Subclass
        self.assertTrue(is_memory_buffer(batching_buffer))  # Subclass

        self.assertFalse(is_rate_limited_buffer(memory_buffer))
        self.assertTrue(is_rate_limited_buffer(rate_limited_buffer))
        self.assertFalse(is_rate_limited_buffer(batching_buffer))

        self.assertFalse(is_batching_buffer(memory_buffer))
        self.assertFalse(is_batching_buffer(rate_limited_buffer))
        self.assertTrue(is_batching_buffer(batching_buffer))


if __name__ == "__main__":
    unittest.main()
