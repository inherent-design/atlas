"""
Unit tests for the events service in the core services module.

Tests the event system implementation including subscription, publishing,
event filtering, middleware, and history management.
"""

import threading
import unittest
from unittest.mock import MagicMock

from atlas.services.events import (
    EventError,
    EventPublishError,
    EventSubscription,
    EventSubscriptionError,
    EventSystem,
    create_event_system,
    emit_event,
    on_event,
)
from atlas.services.middleware import (
    EventMiddleware,
    HistoryMiddleware,
    create_enrichment_middleware,
    create_filter_middleware,
    create_timing_middleware,
)


class TestEventSubscription(unittest.TestCase):
    """Tests for the EventSubscription class."""

    def test_create_subscription(self):
        """Test creating a subscription."""
        callback = MagicMock()
        subscription = EventSubscription(
            subscription_id="test-sub-1",
            event_type="test.event",
            callback=callback,
            source_filter=None,
        )

        self.assertEqual(subscription.subscription_id, "test-sub-1")
        self.assertEqual(subscription.event_type, "test.event")
        self.assertEqual(subscription.callback, callback)
        self.assertIsNone(subscription.source_filter)

    def test_exact_match(self):
        """Test exact event type matching."""
        subscription = EventSubscription(
            subscription_id="test-sub-1",
            event_type="test.event",
            callback=MagicMock(),
            source_filter=None,
        )

        # Should match exact event type
        self.assertTrue(subscription.matches("test.event"))

        # Should not match other event types
        self.assertFalse(subscription.matches("test.other"))
        self.assertFalse(subscription.matches("test"))
        self.assertFalse(subscription.matches("test.event.subtype"))

    def test_wildcard_match(self):
        """Test wildcard event type matching."""
        subscription = EventSubscription(
            subscription_id="test-sub-1",
            event_type="test.*",
            callback=MagicMock(),
            source_filter=None,
        )

        # Should match wildcard pattern
        self.assertTrue(subscription.matches("test.event"))
        self.assertTrue(subscription.matches("test.other"))

        # Should not match non-matching patterns
        self.assertFalse(subscription.matches("test"))
        self.assertFalse(subscription.matches("other.test"))

    def test_source_filter(self):
        """Test source filter matching."""
        subscription = EventSubscription(
            subscription_id="test-sub-1",
            event_type="test.event",
            callback=MagicMock(),
            source_filter="system.*",
        )

        # Should match correct event type and source
        self.assertTrue(subscription.matches("test.event", "system.service"))

        # Should not match incorrect source
        self.assertFalse(subscription.matches("test.event", "other.service"))

        # Should match event type without checking source if None provided
        self.assertTrue(subscription.matches("test.event", None))

    def test_notify(self):
        """Test notification of subscribers."""
        callback = MagicMock()
        subscription = EventSubscription(
            subscription_id="test-sub-1",
            event_type="test.event",
            callback=callback,
            source_filter=None,
        )

        # Create test event
        event = {
            "event_id": "event-1",
            "event_type": "test.event",
            "data": {"message": "test"},
            "source": "test.source",
        }

        # Notify subscription
        subscription.notify(event)

        # Callback should be called once with the event
        callback.assert_called_once_with(event)

    def test_notify_error_handling(self):
        """Test error handling in notification."""

        # Create callback that raises exception
        def failing_callback(event):
            raise ValueError("Test error")

        subscription = EventSubscription(
            subscription_id="test-sub-1",
            event_type="test.event",
            callback=failing_callback,
            source_filter=None,
        )

        # Create test event
        event = {
            "event_id": "event-1",
            "event_type": "test.event",
            "data": {"message": "test"},
            "source": "test.source",
        }

        # Notify should not raise exception
        try:
            subscription.notify(event)
        except Exception as e:
            self.fail(f"notify() raised {e} unexpectedly!")


class TestEventSystem(unittest.TestCase):
    """Tests for the EventSystem class."""

    def setUp(self):
        """Set up a new event system for each test."""
        self.event_system = EventSystem(max_history=10)

    def test_subscribe_and_publish(self):
        """Test basic subscribe and publish functionality."""
        # Create mock callback
        callback = MagicMock()

        # Subscribe to event type
        subscription_id = self.event_system.subscribe(
            event_type="test.event", callback=callback
        )

        # Publish event
        event_id = self.event_system.publish(
            event_type="test.event", data={"message": "test"}, source="test.source"
        )

        # Check callback was called
        callback.assert_called_once()

        # Check event properties
        event_arg = callback.call_args[0][0]
        self.assertEqual(event_arg["event_type"], "test.event")
        self.assertEqual(event_arg["data"]["message"], "test")
        self.assertEqual(event_arg["source"], "test.source")
        self.assertEqual(event_arg["event_id"], event_id)

    def test_wildcard_subscription(self):
        """Test wildcard subscription matching."""
        # Create mock callbacks
        callback1 = MagicMock()
        callback2 = MagicMock()
        callback3 = MagicMock()

        # Subscribe with different patterns
        self.event_system.subscribe(event_type="test.event", callback=callback1)

        self.event_system.subscribe(event_type="test.*", callback=callback2)

        self.event_system.subscribe(event_type="other.*", callback=callback3)

        # Publish test event
        self.event_system.publish(event_type="test.event", data={"message": "test"})

        # Check correct callbacks were called
        callback1.assert_called_once()
        callback2.assert_called_once()
        callback3.assert_not_called()

    def test_source_filtered_subscription(self):
        """Test source-filtered subscription."""
        # Create mock callbacks
        callback1 = MagicMock()
        callback2 = MagicMock()

        # Subscribe with different source filters
        self.event_system.subscribe(
            event_type="test.event", callback=callback1, source_filter="system.*"
        )

        self.event_system.subscribe(
            event_type="test.event", callback=callback2, source_filter="user.*"
        )

        # Publish from system source
        self.event_system.publish(
            event_type="test.event",
            data={"message": "system test"},
            source="system.service",
        )

        # Publish from user source
        self.event_system.publish(
            event_type="test.event", data={"message": "user test"}, source="user.action"
        )

        # Check correct callbacks were called
        callback1.assert_called_once()
        callback2.assert_called_once()

        # Check call arguments
        system_event = callback1.call_args[0][0]
        user_event = callback2.call_args[0][0]

        self.assertEqual(system_event["source"], "system.service")
        self.assertEqual(user_event["source"], "user.action")

    def test_unsubscribe(self):
        """Test unsubscribing from events."""
        # Create mock callback
        callback = MagicMock()

        # Subscribe to event type
        subscription_id = self.event_system.subscribe(
            event_type="test.event", callback=callback
        )

        # Unsubscribe
        result = self.event_system.unsubscribe(subscription_id)

        # Check unsubscribe was successful
        self.assertTrue(result)

        # Publish event
        self.event_system.publish(event_type="test.event", data={"message": "test"})

        # Check callback was not called
        callback.assert_not_called()

        # Unsubscribe again (should fail)
        result = self.event_system.unsubscribe(subscription_id)
        self.assertFalse(result)

    def test_event_history(self):
        """Test event history functionality."""
        # Publish multiple events
        for i in range(5):
            self.event_system.publish(event_type=f"test.event.{i}", data={"index": i})

        # Get all events
        events = self.event_system.get_events()

        # Should have 5 events, newest first
        self.assertEqual(len(events), 5)
        self.assertEqual(events[0]["data"]["index"], 4)
        self.assertEqual(events[4]["data"]["index"], 0)

        # Get events with type filter
        filtered_events = self.event_system.get_events(event_type="test.event.2")

        # Should have 1 event
        self.assertEqual(len(filtered_events), 1)
        self.assertEqual(filtered_events[0]["data"]["index"], 2)

        # Get events with limit
        limited_events = self.event_system.get_events(limit=2)

        # Should have 2 events, newest first
        self.assertEqual(len(limited_events), 2)
        self.assertEqual(limited_events[0]["data"]["index"], 4)
        self.assertEqual(limited_events[1]["data"]["index"], 3)

    def test_history_limit(self):
        """Test event history size limit."""
        # Create event system with small history limit
        small_history = EventSystem(max_history=3)

        # Publish more events than history size
        for i in range(5):
            small_history.publish(event_type=f"test.event.{i}", data={"index": i})

        # Should only keep the newest 3 events
        events = small_history.get_events()
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0]["data"]["index"], 4)
        self.assertEqual(events[2]["data"]["index"], 2)

    def test_clear_events(self):
        """Test clearing event history."""
        # Publish some events
        for i in range(3):
            self.event_system.publish(event_type=f"test.event.{i}", data={"index": i})

        # Clear events
        self.event_system.clear_events()

        # Should have no events
        events = self.event_system.get_events()
        self.assertEqual(len(events), 0)

    def test_get_stats(self):
        """Test getting event system statistics."""
        # Initial stats
        stats = self.event_system.get_stats()
        self.assertEqual(stats["subscription_count"], 0)
        self.assertEqual(stats["published_count"], 0)
        self.assertEqual(stats["delivery_count"], 0)

        # Add subscription and publish event
        callback = MagicMock()
        self.event_system.subscribe(event_type="test.event", callback=callback)

        self.event_system.publish(event_type="test.event", data={"message": "test"})

        # Updated stats
        stats = self.event_system.get_stats()
        self.assertEqual(stats["subscription_count"], 1)
        self.assertEqual(stats["published_count"], 1)
        self.assertEqual(stats["delivery_count"], 1)

    def test_get_specific_event(self):
        """Test getting a specific event by ID."""
        # Publish an event
        event_id = self.event_system.publish(
            event_type="test.event", data={"message": "test"}
        )

        # Get the specific event
        event = self.event_system.get_event(event_id)

        # Check event properties
        self.assertIsNotNone(event)
        self.assertEqual(event["event_id"], event_id)
        self.assertEqual(event["event_type"], "test.event")
        self.assertEqual(event["data"]["message"], "test")

        # Get non-existent event
        not_found = self.event_system.get_event("non-existent")
        self.assertIsNone(not_found)

    def test_get_subscriptions(self):
        """Test getting subscription information."""
        # Add subscriptions
        self.event_system.subscribe(event_type="test.event1", callback=MagicMock())

        self.event_system.subscribe(event_type="test.event2", callback=MagicMock())

        # Get all subscriptions
        subscriptions = self.event_system.get_subscriptions()

        # Should have 2 subscriptions
        self.assertEqual(len(subscriptions), 2)

        # Check subscription properties
        for sub_id, sub_info in subscriptions.items():
            self.assertIn(sub_info["event_type"], ["test.event1", "test.event2"])
            self.assertEqual(sub_info["subscription_id"], sub_id)

        # Get filtered subscriptions
        filtered = self.event_system.get_subscriptions(event_type="test.event1")
        self.assertEqual(len(filtered), 1)

        # Check filtered subscription
        sub_id, sub_info = next(iter(filtered.items()))
        self.assertEqual(sub_info["event_type"], "test.event1")

    def test_thread_safety(self):
        """Test thread safety of event operations."""
        # Set up shared data for threads
        callback_count = 0
        callback_lock = threading.Lock()

        def thread_safe_callback(event):
            nonlocal callback_count
            with callback_lock:
                callback_count += 1

        # Subscribe to event type
        self.event_system.subscribe(
            event_type="test.event", callback=thread_safe_callback
        )

        # Create threads to publish events
        threads = []
        for i in range(10):
            thread = threading.Thread(
                target=self.event_system.publish, args=("test.event", {"thread": i})
            )
            threads.append(thread)

        # Start threads
        for thread in threads:
            thread.start()

        # Wait for threads to finish
        for thread in threads:
            thread.join()

        # Check callback was called for each event
        self.assertEqual(callback_count, 10)

        # Check events were all recorded
        events = self.event_system.get_events()
        self.assertEqual(len(events), 10)


class TestEventDecorators(unittest.TestCase):
    """Tests for event system decorators."""

    def setUp(self):
        """Set up a new event system for each test."""
        self.event_system = EventSystem()

    def test_on_event_decorator(self):
        """Test on_event decorator for event subscription."""
        # Create mock function
        mock_func = MagicMock()
        mock_func.__name__ = "mock_func"  # Ensure it has a __name__ attribute

        # Apply decorator manually instead of as decorator to verify it works
        decorated = on_event(event_system=self.event_system, event_type="test.event")(
            mock_func
        )

        # Publish matching event
        self.event_system.publish(event_type="test.event", data={"message": "test"})

        # Function should be called
        mock_func.assert_called_once()

    def test_emit_event_decorator(self):
        """Test emit_event decorator for automatic event emission."""
        # Create mock callback
        callback = MagicMock()

        # Subscribe to event
        self.event_system.subscribe(event_type="func.called", callback=callback)

        # Create decorated function
        @emit_event(
            event_system=self.event_system,
            event_type="func.called",
            source="test.module",
        )
        def test_func(arg1, arg2=None):
            """Test function that emits event."""
            return f"{arg1}-{arg2}" if arg2 else arg1

        # Call function
        result = test_func("hello", arg2="world")

        # Check function result
        self.assertEqual(result, "hello-world")

        # Check event was emitted
        callback.assert_called_once()

        # Check event properties
        event = callback.call_args[0][0]
        self.assertEqual(event["event_type"], "func.called")
        self.assertEqual(event["source"], "test.module")
        self.assertEqual(event["data"]["result"], "hello-world")
        self.assertEqual(event["data"]["function"], "test_func")
        self.assertIn("args", event["data"])
        self.assertEqual(event["data"]["args"]["arg_0"], "hello")
        self.assertEqual(event["data"]["args"]["arg2"], "world")


class TestEventMiddleware(unittest.TestCase):
    """Tests for event middleware integration."""

    def setUp(self):
        """Set up a new event system for each test."""
        self.event_system = EventSystem()

    def test_filter_middleware(self):
        """Test filter middleware for event system."""

        # Create filter that blocks specific event types
        def filter_func(event):
            return event["event_type"] != "test.filtered"

        # Add filter middleware
        self.event_system.add_middleware(create_filter_middleware(filter_func))

        # Subscribe to all test events
        callback = MagicMock()
        self.event_system.subscribe(event_type="test.*", callback=callback)

        # Publish allowed event
        self.event_system.publish(
            event_type="test.allowed", data={"message": "should pass"}
        )

        # Publish filtered event
        self.event_system.publish(
            event_type="test.filtered", data={"message": "should be filtered"}
        )

        # Callback should be called once for allowed event
        callback.assert_called_once()

        # Check event type of the call
        event = callback.call_args[0][0]
        self.assertEqual(event["event_type"], "test.allowed")

    def test_enrichment_middleware(self):
        """Test enrichment middleware for event system."""
        # Create dict of data to enrich events with
        enrichment_data = {"enriched": True}

        # Add enrichment middleware with the enrichment data using the create_enrichment_middleware function
        enrichment_middleware = create_enrichment_middleware(enrichment_data)
        self.event_system.add_middleware(enrichment_middleware)

        # Subscribe to test events
        callback = MagicMock()
        self.event_system.subscribe(event_type="test.event", callback=callback)

        # Publish test event
        self.event_system.publish(event_type="test.event", data={"message": "test"})

        # Check event was enriched
        callback.assert_called_once()
        event = callback.call_args[0][0]
        self.assertTrue(event["data"]["enriched"])

    def test_timing_middleware(self):
        """Test timing middleware for event system."""
        # Add timing middleware
        self.event_system.add_middleware(create_timing_middleware())

        # Subscribe to test events
        callback = MagicMock()
        self.event_system.subscribe(event_type="test.event", callback=callback)

        # Publish test event
        self.event_system.publish(event_type="test.event", data={"message": "test"})

        # Check event has timing metadata
        callback.assert_called_once()
        event = callback.call_args[0][0]
        self.assertIn("metadata", event)
        self.assertIn("processing_time_ms", event["metadata"])

    def test_history_middleware(self):
        """Test history middleware for event system."""
        # Create history middleware
        history = HistoryMiddleware(max_history=5)

        # Add to event system
        self.event_system.add_middleware(history)

        # Publish multiple events
        for i in range(10):
            self.event_system.publish(event_type=f"test.event.{i}", data={"index": i})

        # Get history
        event_history = history.get_history()

        # Should have 5 events (max history)
        self.assertEqual(len(event_history), 5)

        # Should have newest events
        indices = [event["data"]["index"] for event in event_history]
        self.assertEqual(indices, [9, 8, 7, 6, 5])

        # Clear history
        history.clear_history()

        # History should be empty
        self.assertEqual(len(history.get_history()), 0)

    def test_middleware_order(self):
        """Test middleware execution order based on priority."""
        # Create middleware that track execution order
        execution_order = []

        class OrderTrackingMiddleware(EventMiddleware):
            def __init__(self, name):
                self.name = name

            def process(self, event, next):  # Fix: added next parameter
                execution_order.append(self.name)
                return next(event)  # Fix: Call next with event

        # Add middleware with different priorities
        middleware1 = OrderTrackingMiddleware("middleware1")
        middleware2 = OrderTrackingMiddleware("middleware2")
        middleware3 = OrderTrackingMiddleware("middleware3")

        self.event_system.add_middleware(middleware1, priority=10)  # Highest priority
        self.event_system.add_middleware(middleware2, priority=5)  # Medium priority
        self.event_system.add_middleware(middleware3, priority=1)  # Lowest priority

        # Publish event
        self.event_system.publish(event_type="test.event", data={"message": "test"})

        # Check execution order (highest to lowest priority)
        self.assertEqual(execution_order, ["middleware1", "middleware2", "middleware3"])

    def test_middleware_removal(self):
        """Test removing middleware."""
        # Create middleware
        middleware = HistoryMiddleware()

        # Add to event system
        self.event_system.add_middleware(middleware)

        # Verify middleware is present in stats
        stats = self.event_system.get_stats()
        self.assertEqual(stats["middleware_count"], 1)

        # Remove middleware
        result = self.event_system.remove_middleware(middleware)

        # Check removal was successful
        self.assertTrue(result)

        # Verify middleware count is updated
        stats = self.event_system.get_stats()
        self.assertEqual(stats["middleware_count"], 0)

        # Try removing non-existent middleware
        result = self.event_system.remove_middleware(middleware)
        self.assertFalse(result)


class TestEventSystemCreation(unittest.TestCase):
    """Tests for event system creation utility."""

    def test_create_event_system(self):
        """Test creating an event system."""
        # Create with default settings
        event_system = create_event_system()
        self.assertIsInstance(event_system, EventSystem)
        self.assertEqual(event_system._max_history, EventSystem.MAX_EVENT_HISTORY)

        # Create with custom settings
        custom_system = create_event_system(max_history=20)
        self.assertEqual(custom_system._max_history, 20)


class TestEventErrors(unittest.TestCase):
    """Tests for event system error classes."""

    def test_event_error(self):
        """Test EventError class."""
        # Create basic error
        error = EventError("Test error")
        self.assertEqual(str(error), "Test error")

        # Create error with details
        error_with_details = EventError(
            message="Test error with details", details={"key": "value"}
        )
        self.assertEqual(error_with_details.details.get("key"), "value")

    def test_subscription_error(self):
        """Test EventSubscriptionError class."""
        # Create subscription error
        error = EventSubscriptionError(
            message="Subscription error", subscription_id="sub-123"
        )
        self.assertEqual(str(error), "Subscription error")
        self.assertEqual(error.details.get("subscription_id"), "sub-123")

    def test_publish_error(self):
        """Test EventPublishError class."""
        # Create publish error
        error = EventPublishError(message="Publish error", event_type="test.event")
        self.assertEqual(str(error), "Publish error")
        self.assertEqual(error.details.get("event_type"), "test.event")


if __name__ == "__main__":
    unittest.main()
