"""
Unit tests for the middleware service in the core services module.

Tests the middleware pipeline, middleware interfaces, and built-in middleware
implementations like logging, filtering, enrichment, timing, and history middleware.
"""

import threading
import time
import unittest
from unittest.mock import MagicMock

from atlas.services.middleware import (
    EventEnrichmentMiddleware,
    EventFilterMiddleware,
    EventMiddleware,
    HistoryMiddleware,
    LoggingMiddleware,
    MiddlewareError,
    MiddlewarePipeline,
    TimingMiddleware,
    create_enrichment_middleware,
    create_filter_middleware,
    create_history_middleware,
    create_logging_middleware,
    create_middleware,
    create_timing_middleware,
)


class TestMiddlewarePipeline(unittest.TestCase):
    """Tests for the MiddlewarePipeline class."""

    def setUp(self):
        """Set up a new middleware pipeline for each test."""
        self.pipeline = MiddlewarePipeline()

    def test_empty_pipeline(self):
        """Test that empty pipeline returns event unchanged."""
        # Create test event
        event = {"event_id": "test-event", "data": {"message": "test"}}

        # Process through empty pipeline
        result = self.pipeline.process(event)

        # Event should be unchanged
        self.assertEqual(result, event)

    def test_middleware_ordering_by_priority(self):
        """Test that middleware is executed in priority order."""
        # Create tracking list for execution order
        execution_order = []

        # Create middleware instances
        class TestMiddleware(EventMiddleware):
            def __init__(self, name):
                self.name = name

            def process(self, event, next):
                execution_order.append(self.name)
                return next(event)

        # Add middleware with different priorities
        self.pipeline.add(TestMiddleware("low-priority"), priority=0)
        self.pipeline.add(TestMiddleware("medium-priority"), priority=50)
        self.pipeline.add(TestMiddleware("high-priority"), priority=100)

        # Process test event
        event = {"event_id": "test-event", "data": {"message": "test"}}
        self.pipeline.process(event)

        # Check execution order (high to low priority)
        self.assertEqual(
            execution_order, ["high-priority", "medium-priority", "low-priority"]
        )

    def test_middleware_modification(self):
        """Test that middleware can modify events."""

        # Create middleware that adds fields
        class AddFieldMiddleware(EventMiddleware):
            def __init__(self, field, value):
                self.field = field
                self.value = value

            def process(self, event, next):
                # Create a copy to avoid modifying the original
                new_event = event.copy()
                if "data" not in new_event:
                    new_event["data"] = {}

                # Create a copy of data dict
                new_event["data"] = new_event["data"].copy()
                new_event["data"][self.field] = self.value

                return next(new_event)

        # Add multiple field-adding middleware
        self.pipeline.add(AddFieldMiddleware("field1", "value1"))
        self.pipeline.add(AddFieldMiddleware("field2", "value2"))

        # Process test event
        event = {"event_id": "test-event", "data": {"original": "data"}}
        result = self.pipeline.process(event)

        # Check fields were added
        self.assertEqual(result["data"]["original"], "data")
        self.assertEqual(result["data"]["field1"], "value1")
        self.assertEqual(result["data"]["field2"], "value2")

        # Original event should be unchanged
        self.assertNotIn("field1", event["data"])

    def test_middleware_filtering(self):
        """Test that middleware can filter out events."""

        # Create filter middleware
        class FilterMiddleware(EventMiddleware):
            def __init__(self, filter_value):
                self.filter_value = filter_value

            def process(self, event, next):
                # Only pass events with matching filter value
                if event.get("filter_field") == self.filter_value:
                    return next(event)
                return None

        # Add filter middleware
        self.pipeline.add(FilterMiddleware("pass"))

        # Test with matching event
        passing_event = {
            "event_id": "pass-event",
            "filter_field": "pass",
            "data": {"message": "should pass"},
        }

        # Test with non-matching event
        filtered_event = {
            "event_id": "filtered-event",
            "filter_field": "filtered",
            "data": {"message": "should be filtered"},
        }

        # Process events
        passing_result = self.pipeline.process(passing_event)
        filtered_result = self.pipeline.process(filtered_event)

        # Check results
        self.assertIsNotNone(passing_result)
        self.assertEqual(passing_result["event_id"], "pass-event")
        self.assertIsNone(filtered_result)

    def test_add_remove_middleware(self):
        """Test adding and removing middleware from the pipeline."""

        # Create simple middleware
        class TestMiddleware(EventMiddleware):
            def process(self, event, next):
                return next(event)

        # Create test middleware
        middleware = TestMiddleware()

        # Add middleware
        self.pipeline.add(middleware)

        # Middleware count should be 1
        self.assertEqual(self.pipeline.get_middleware_count(), 1)

        # Remove middleware
        result = self.pipeline.remove(middleware)

        # Check removal was successful
        self.assertTrue(result)
        self.assertEqual(self.pipeline.get_middleware_count(), 0)

        # Removing non-existent middleware should fail
        result = self.pipeline.remove(middleware)
        self.assertFalse(result)

    def test_middleware_error_handling(self):
        """Test that errors in middleware don't break the pipeline."""

        # Create middleware that raises exception
        class ErrorMiddleware(EventMiddleware):
            def process(self, event, next):
                raise ValueError("Middleware error")

        # Create middleware that adds a field
        class AddFieldMiddleware(EventMiddleware):
            def process(self, event, next):
                # Create a copy to avoid modifying the original
                new_event = event.copy()
                if "data" not in new_event:
                    new_event["data"] = {}

                # Create a copy of data dict
                new_event["data"] = new_event["data"].copy()
                new_event["data"]["added_field"] = "added_value"

                return next(new_event)

        # Add both middleware - error middleware first, then field middleware
        self.pipeline.add(ErrorMiddleware())
        self.pipeline.add(AddFieldMiddleware())

        # Process test event
        event = {"event_id": "test-event", "data": {"original": "data"}}

        # Process should not throw and should still apply second middleware
        result = self.pipeline.process(event)

        # Field should still be added despite error in first middleware
        self.assertEqual(result["data"]["original"], "data")
        self.assertEqual(result["data"]["added_field"], "added_value")

    def test_thread_safety(self):
        """Test thread safety of middleware pipeline."""
        # Create shared counter
        counter = 0
        counter_lock = threading.Lock()

        # Create middleware that counts
        class CountingMiddleware(EventMiddleware):
            def process(self, event, next):
                nonlocal counter
                with counter_lock:
                    counter += 1
                return next(event)

        # Add middleware
        self.pipeline.add(CountingMiddleware())

        # Create events
        events = [{"event_id": f"event-{i}"} for i in range(10)]

        # Thread function to process events
        def process_events():
            for event in events:
                self.pipeline.process(event)

        # Create and start threads
        threads = []
        for _ in range(5):  # 5 threads
            thread = threading.Thread(target=process_events)
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        # Counter should be 50 (5 threads × 10 events)
        self.assertEqual(counter, 50)


class TestMiddlewareImplementations(unittest.TestCase):
    """Tests for the built-in middleware implementations."""

    def test_logging_middleware(self):
        """Test the logging middleware."""
        # Create mock logger
        mock_logger = MagicMock()

        # Create middleware
        middleware = LoggingMiddleware(logger=mock_logger, log_level="debug")

        # Create test event
        event = {
            "event_id": "test-event",
            "event_type": "test.event",
            "source": "test.source",
            "data": {"message": "test"},
        }

        # Mock next function
        next_func = lambda e: e

        # Process event
        middleware.process(event, next_func)

        # Verify logger called
        mock_logger.debug.assert_called_once()
        log_message = mock_logger.debug.call_args[0][0]
        self.assertIn("test-event", log_message)
        self.assertIn("test.event", log_message)
        self.assertIn("test.source", log_message)

    def test_filter_middleware(self):
        """Test the filter middleware."""

        # Create filter function
        def filter_func(event):
            return event["event_type"] != "filtered.event"

        # Create middleware
        middleware = EventFilterMiddleware(filter_func)

        # Create test events
        passing_event = {
            "event_id": "pass-event",
            "event_type": "pass.event",
            "data": {"message": "should pass"},
        }

        filtered_event = {
            "event_id": "filtered-event",
            "event_type": "filtered.event",
            "data": {"message": "should be filtered"},
        }

        # Mock next function with tracking
        next_calls = []

        def next_func(e):
            next_calls.append(e)
            return e

        # Process events
        pass_result = middleware.process(passing_event, next_func)
        filtered_result = middleware.process(filtered_event, next_func)

        # Check results
        self.assertEqual(pass_result, passing_event)
        self.assertIsNone(filtered_result)

        # Next should only be called for passing event
        self.assertEqual(len(next_calls), 1)
        self.assertEqual(next_calls[0], passing_event)

    def test_enrichment_middleware(self):
        """Test the enrichment middleware."""
        # Create enrichment data
        enrichment_data = {"enriched": True, "env": "test"}

        # Create middleware
        middleware = EventEnrichmentMiddleware(enrichment_data)

        # Create test event
        event = {
            "event_id": "test-event",
            "event_type": "test.event",
            "data": {"original": "data"},
        }

        # Mock next function
        next_func = lambda e: e

        # Process event
        result = middleware.process(event, next_func)

        # Check enrichment
        self.assertEqual(result["data"]["original"], "data")
        self.assertTrue(result["data"]["enriched"])
        self.assertEqual(result["data"]["env"], "test")

        # Original event should be unmodified
        self.assertNotIn("enriched", event["data"])

    def test_timing_middleware(self):
        """Test the timing middleware."""
        # Create middleware
        middleware = TimingMiddleware()

        # Create test event
        event = {
            "event_id": "test-event",
            "event_type": "test.event",
            "data": {"message": "test"},
        }

        # Add delay to next function to test timing
        def next_with_delay(e):
            time.sleep(0.01)  # Short delay
            return e

        # Process event
        result = middleware.process(event, next_with_delay)

        # Check timing metadata
        self.assertIn("metadata", result)
        self.assertIn("processing_started", result["metadata"])
        self.assertIn("processing_completed", result["metadata"])
        self.assertIn("processing_time_ms", result["metadata"])

        # Processing time should be greater than zero but less than 1000ms
        self.assertGreater(result["metadata"]["processing_time_ms"], 0)
        self.assertLess(result["metadata"]["processing_time_ms"], 1000)

    def test_history_middleware(self):
        """Test the history middleware."""
        # Create middleware
        middleware = HistoryMiddleware(max_history=5)

        # Create test events
        events = []
        for i in range(10):
            events.append(
                {
                    "event_id": f"event-{i}",
                    "event_type": f"test.event.{i % 3}",  # 3 different event types
                    "source": f"source.{i % 2}",  # 2 different sources
                    "data": {"index": i},
                }
            )

        # Process events
        for event in events:
            middleware.process(event, lambda e: e)

        # History should contain only the last 5 events
        history = middleware.get_history()
        self.assertEqual(len(history), 5)

        # Newest events first
        self.assertEqual(history[0]["event_id"], "event-9")
        self.assertEqual(history[4]["event_id"], "event-5")

        # Test filtering by event type
        type_0_events = middleware.get_history(event_type="test.event.0")
        self.assertGreater(len(type_0_events), 0)
        for event in type_0_events:
            self.assertEqual(event["event_type"], "test.event.0")

        # Test filtering by source
        source_1_events = middleware.get_history(source="source.1")
        self.assertGreater(len(source_1_events), 0)
        for event in source_1_events:
            self.assertEqual(event["source"], "source.1")

        # Test limit
        limited_history = middleware.get_history(limit=2)
        self.assertEqual(len(limited_history), 2)
        self.assertEqual(limited_history[0]["event_id"], "event-9")
        self.assertEqual(limited_history[1]["event_id"], "event-8")

        # Test replaying history
        replay_calls = []
        middleware.replay_history(lambda e: replay_calls.append(e["event_id"]))
        self.assertEqual(len(replay_calls), 5)
        self.assertEqual(replay_calls[0], "event-9")

        # Test clear history
        middleware.clear_history()
        self.assertEqual(len(middleware.get_history()), 0)


class TestMiddlewareFactoryFunctions(unittest.TestCase):
    """Tests for the middleware factory functions."""

    def test_create_middleware(self):
        """Test creating middleware from a function."""

        # Create a function to use as middleware
        def add_field(event, next):
            event_copy = event.copy()
            if "data" not in event_copy:
                event_copy["data"] = {}
            event_copy["data"] = event_copy["data"].copy()
            event_copy["data"]["added_field"] = "added_value"
            return next(event_copy)

        # Create middleware
        middleware = create_middleware(add_field)

        # Verify it's an EventMiddleware
        self.assertIsInstance(middleware, EventMiddleware)

        # Test it works
        event = {"event_id": "test-event", "data": {}}
        result = middleware.process(event, lambda e: e)

        self.assertEqual(result["data"]["added_field"], "added_value")

    def test_create_logging_middleware(self):
        """Test logging middleware factory function."""
        # Create middleware
        middleware = create_logging_middleware(log_level="INFO")

        # Verify it's a LoggingMiddleware
        self.assertTrue(isinstance(middleware, LoggingMiddleware))
        self.assertEqual(middleware.log_level, "info")

    def test_create_filter_middleware(self):
        """Test filter middleware factory function."""

        # Create predicate function
        def predicate(event):
            return event.get("pass", False)

        # Create middleware
        middleware = create_filter_middleware(predicate)

        # Verify it's an EventFilterMiddleware
        self.assertTrue(isinstance(middleware, EventFilterMiddleware))
        self.assertEqual(middleware.predicate, predicate)

        # Test it works
        passing_event = {"event_id": "pass", "pass": True}
        filtered_event = {"event_id": "filtered", "pass": False}

        self.assertIsNotNone(middleware.process(passing_event, lambda e: e))
        self.assertIsNone(middleware.process(filtered_event, lambda e: e))

    def test_create_enrichment_middleware(self):
        """Test enrichment middleware factory function."""
        # Create enrichment data
        enrichment_data = {"enriched": True}

        # Create middleware
        middleware = create_enrichment_middleware(enrichment_data)

        # Verify it's an EventEnrichmentMiddleware
        self.assertTrue(isinstance(middleware, EventEnrichmentMiddleware))
        self.assertEqual(middleware.enrichment_data, enrichment_data)

        # Test it works
        event = {"event_id": "test", "data": {}}
        result = middleware.process(event, lambda e: e)

        self.assertTrue(result["data"]["enriched"])

    def test_create_timing_middleware(self):
        """Test timing middleware factory function."""
        # Create middleware
        middleware = create_timing_middleware()

        # Verify it's a TimingMiddleware
        self.assertTrue(isinstance(middleware, TimingMiddleware))

        # Test it adds timing metadata
        event = {"event_id": "test"}
        result = middleware.process(event, lambda e: e)

        self.assertIn("metadata", result)
        self.assertIn("processing_started", result["metadata"])

    def test_create_history_middleware(self):
        """Test history middleware factory function."""
        # Create middleware
        middleware = create_history_middleware(max_history=10)

        # Verify it's a HistoryMiddleware
        self.assertTrue(isinstance(middleware, HistoryMiddleware))
        self.assertEqual(middleware._max_history, 10)


class TestMiddlewareErrors(unittest.TestCase):
    """Tests for middleware error handling."""

    def test_middleware_error(self):
        """Test MiddlewareError class."""
        # Create error
        error = MiddlewareError(
            message="Test middleware error",
            details={"key": "value"},
            middleware_id="test-middleware",
        )

        # Check error properties
        self.assertEqual(str(error), "Test middleware error")
        self.assertEqual(error.details.get("key"), "value")
        self.assertEqual(error.details.get("middleware_id"), "test-middleware")

    def test_add_invalid_middleware(self):
        """Test adding invalid middleware raises error."""
        # Create pipeline
        pipeline = MiddlewarePipeline()

        # Adding non-middleware should raise error
        with self.assertRaises(MiddlewareError):
            pipeline.add("not a middleware")

        # Add object without process method
        class InvalidMiddleware:
            pass

        with self.assertRaises(MiddlewareError):
            pipeline.add(InvalidMiddleware())


if __name__ == "__main__":
    unittest.main()
