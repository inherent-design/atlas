"""
Unit tests for core services types and protocols.

These tests verify that the type system correctly identifies implementation classes,
validates type constraints, and ensures protocol conformance.
"""

import time
import unittest
import uuid
from datetime import datetime
from typing import Any, Protocol, Self, TypedDict, TypeVar, cast

from atlas.services.buffer import BatchingBuffer, MemoryBuffer, RateLimitedBuffer
from atlas.services.registry import BaseService
from atlas.services.types import (
    BatchingBufferProtocol,
    BufferProtocol,
    CommandProtocol,
    EventProtocol,
    ResourceProtocol,
    ServiceProtocol,
    StateManagementProtocol,
    StreamingBufferProtocol,
    is_batching_buffer,
    is_buffer,
    is_command,
    is_event_system,
    is_middleware,
    is_rate_limited_buffer,
    is_resource,
    is_service,
    is_service_enabled,
    is_service_registry,
    is_state_container,
    is_streaming_buffer,
    is_transition_registry,
    is_transition_validator,
)


class TestCoreServicesTypes(unittest.TestCase):
    """Tests for the core services type system."""

    def test_service_protocol(self):
        """Test ServiceProtocol type identification."""
        # Create a service instance
        service = BaseService(name="test_service", capabilities={"test": True})

        # Check protocol implementation
        self.assertTrue(is_service(service))
        self.assertIsInstance(service, ServiceProtocol)

        # Verify property access
        self.assertEqual(service.name, "test_service")
        self.assertEqual(service.status, "initializing")
        self.assertEqual(service.capabilities, {"test": True})
        self.assertIsInstance(service.service_id, str)

    def test_buffer_protocols(self):
        """Test buffer protocol implementation and nesting."""
        # Create buffer instances
        memory_buffer = MemoryBuffer()
        rate_limited_buffer = RateLimitedBuffer(tokens_per_second=10.0)
        batching_buffer = BatchingBuffer(batch_size=5)

        # Test base protocol
        for buffer in [memory_buffer, rate_limited_buffer, batching_buffer]:
            self.assertTrue(is_buffer(buffer))
            self.assertIsInstance(buffer, BufferProtocol)

        # Test streaming buffer protocol
        for buffer in [memory_buffer, rate_limited_buffer, batching_buffer]:
            self.assertTrue(is_streaming_buffer(buffer))
            self.assertIsInstance(buffer, StreamingBufferProtocol)

        # Test specialized buffer protocols
        self.assertTrue(is_rate_limited_buffer(rate_limited_buffer))
        self.assertIsInstance(rate_limited_buffer, RateLimitedBufferProtocol)

        self.assertTrue(is_batching_buffer(batching_buffer))
        self.assertIsInstance(batching_buffer, BatchingBufferProtocol)

        # Verify non-implementation
        self.assertFalse(is_rate_limited_buffer(memory_buffer))
        self.assertFalse(is_batching_buffer(memory_buffer))

    def test_buffer_protocol_properties(self):
        """Test buffer protocol property access."""
        buffer = MemoryBuffer(max_size=100)

        # Test property access
        self.assertEqual(buffer.max_size, 100)
        self.assertTrue(buffer.is_empty)
        self.assertFalse(buffer.is_full)
        self.assertEqual(buffer.size, 0)
        self.assertFalse(buffer.is_paused)

        # Add an item
        buffer.push({"test": "value"})

        # Verify property changes
        self.assertFalse(buffer.is_empty)
        self.assertEqual(buffer.size, 1)

        # Test method chaining
        buffer.pause().resume()

        # Verify streaming buffer methods
        self.assertIsInstance(buffer, StreamingBufferProtocol)
        self.assertTrue(hasattr(buffer, "wait_until_not_empty"))
        self.assertTrue(hasattr(buffer, "wait_until_not_full"))

    def test_rate_limited_buffer_protocol(self):
        """Test rate limited buffer protocol specifics."""
        rate_buffer = RateLimitedBuffer(
            tokens_per_second=20.0, chars_per_token=5, max_size=200
        )

        # Test protocol implementation
        self.assertIsInstance(rate_buffer, RateLimitedBufferProtocol)

        # Test specialized properties
        self.assertEqual(rate_buffer.tokens_per_second, 20.0)
        self.assertEqual(rate_buffer.chars_per_token, 5)
        self.assertIsInstance(rate_buffer.token_budget, float)

    def test_batching_buffer_protocol(self):
        """Test batching buffer protocol specifics."""
        batch_buffer = BatchingBuffer(
            batch_size=10, batch_timeout=2.0, batch_delimiter="\n", max_size=200
        )

        # Test protocol implementation
        self.assertIsInstance(batch_buffer, BatchingBufferProtocol)

        # Test specialized properties
        self.assertEqual(batch_buffer.batch_size, 10)
        self.assertEqual(batch_buffer.batch_timeout, 2.0)
        self.assertEqual(batch_buffer.batch_delimiter, "\n")

        # Test specialized methods
        self.assertTrue(hasattr(batch_buffer, "wait_for_batch"))

    def test_protocol_type_guards(self):
        """Test TypeGuard functions for protocols."""

        # Define a non-buffer class
        class NotABuffer:
            def __init__(self):
                self.data = []

        non_buffer = NotABuffer()
        memory_buffer = MemoryBuffer()

        # Test TypeGuard success
        self.assertTrue(is_buffer(memory_buffer))

        # Test TypeGuard failure
        self.assertFalse(is_buffer(non_buffer))
        self.assertFalse(is_buffer("not a buffer"))
        self.assertFalse(is_buffer(None))

        # Test other protocol guards
        self.assertFalse(is_service(memory_buffer))
        self.assertFalse(is_command(memory_buffer))
        self.assertFalse(is_event_system(memory_buffer))
        self.assertFalse(is_middleware(memory_buffer))
        self.assertFalse(is_resource(memory_buffer))
        self.assertFalse(is_service_enabled(memory_buffer))
        self.assertFalse(is_service_registry(memory_buffer))
        self.assertFalse(is_state_container(memory_buffer))
        self.assertFalse(is_transition_registry(memory_buffer))
        self.assertFalse(is_transition_validator(memory_buffer))


if __name__ == "__main__":
    unittest.main()
