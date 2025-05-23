"""
Example demonstrating middleware in the event system.

This example shows how to use middleware to intercept, modify, and filter events
in the Atlas event system.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from atlas.core.services.events import EventSystem
from atlas.core.services.middleware import (
    EventMiddleware,
    HistoryMiddleware,
    create_enrichment_middleware,
    create_filter_middleware,
    create_logging_middleware,
    create_middleware,
    create_timing_middleware,
)


def setup_logger():
    """Set up a logger for this example."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)


logger = setup_logger()


def example_logging_middleware():
    """Example of using a logging middleware."""
    # Create event system
    event_system = EventSystem()

    # Add logging middleware
    event_system.add_middleware(create_logging_middleware())

    # Subscribe to events
    event_system.subscribe(
        event_type="example.*",
        callback=lambda event: logger.info(f"Received event: {event['event_type']}"),
    )

    # Publish events
    event_system.publish(
        event_type="example.created", data={"item_id": "123", "name": "Example Item"}
    )

    event_system.publish(
        event_type="example.updated", data={"item_id": "123", "name": "Updated Example Item"}
    )

    # Show stats
    logger.info(f"Event system stats: {event_system.get_stats()}")


def example_filter_middleware():
    """Example of using a filter middleware."""
    # Create event system
    event_system = EventSystem()

    # Add filter middleware that only allows events of a certain type
    def allow_only_created_events(event):
        return event["event_type"].endswith(".created")

    event_system.add_middleware(create_filter_middleware(allow_only_created_events))

    # Subscribe to all events
    received_events = []
    event_system.subscribe(event_type="*", callback=lambda event: received_events.append(event))

    # Publish events
    event_system.publish(
        event_type="example.created", data={"item_id": "123", "name": "Example Item"}
    )

    event_system.publish(
        event_type="example.updated", data={"item_id": "123", "name": "Updated Example Item"}
    )

    # We should only receive the created event
    logger.info(f"Received {len(received_events)} events")
    for event in received_events:
        logger.info(f"Event type: {event['event_type']}")

    # Show stats with filtered count
    logger.info(f"Event system stats: {event_system.get_stats()}")


def example_enrichment_middleware():
    """Example of using an enrichment middleware."""
    # Create event system
    event_system = EventSystem()

    # Add enrichment middleware
    event_system.add_middleware(
        create_enrichment_middleware({"environment": "development", "version": "1.0.0"})
    )

    # Subscribe to events
    event_system.subscribe(
        event_type="example.*",
        callback=lambda event: logger.info(
            f"Received event: {event['event_type']} with data: {event['data']}"
        ),
    )

    # Publish event
    event_system.publish(
        event_type="example.created", data={"item_id": "123", "name": "Example Item"}
    )

    # The event data should include the enrichment data
    events = event_system.get_events(limit=1)
    if events:
        logger.info(f"Enriched data: {events[0]['data']}")


def example_timing_middleware():
    """Example of using a timing middleware."""
    # Create event system
    event_system = EventSystem()

    # Add timing middleware
    event_system.add_middleware(create_timing_middleware())

    # Add a delay middleware that simulates processing time
    def delay_middleware(event, next):
        time.sleep(0.1)  # Simulate processing time
        return next(event)

    event_system.add_middleware(create_middleware(delay_middleware))

    # Subscribe to events
    event_system.subscribe(
        event_type="example.*",
        callback=lambda event: logger.info(
            f"Received event: {event['event_type']} with metadata: {event['metadata']}"
        ),
    )

    # Publish event
    event_system.publish(
        event_type="example.created", data={"item_id": "123", "name": "Example Item"}
    )

    # The event metadata should include timing information
    events = event_system.get_events(limit=1)
    if events:
        logger.info(f"Event metadata: {events[0]['metadata']}")


def example_history_middleware():
    """Example of using a history middleware."""
    # Create event system
    event_system = EventSystem()

    # Add history middleware
    history_middleware = HistoryMiddleware(max_history=100)
    event_system.add_middleware(history_middleware)

    # Publish events
    for i in range(5):
        event_system.publish(
            event_type=f"example.item.{i}", data={"item_id": str(i), "name": f"Item {i}"}
        )

    # Get history
    history = history_middleware.get_history()
    logger.info(f"History contains {len(history)} events")

    # Filter history by event type
    filtered_history = history_middleware.get_history(event_type="example.item.0")
    logger.info(f"Filtered history contains {len(filtered_history)} events")

    # Replay history
    replay_count = 0

    def replay_processor(event):
        nonlocal replay_count
        replay_count += 1
        logger.info(f"Replayed event: {event['event_type']}")

    history_middleware.replay_history(replay_processor)
    logger.info(f"Replayed {replay_count} events")


def example_middleware_chain():
    """Example of using a chain of middleware."""
    # Create event system
    event_system = EventSystem()

    # Add multiple middleware in a chain
    # Order matters! Middleware added first runs first

    # 1. Logging middleware (runs first)
    event_system.add_middleware(create_logging_middleware(), priority=100)

    # 2. Filter middleware (runs second)
    def allow_only_item_events(event):
        return "item" in event["event_type"]

    event_system.add_middleware(create_filter_middleware(allow_only_item_events), priority=90)

    # 3. Enrichment middleware (runs third)
    event_system.add_middleware(
        create_enrichment_middleware({"environment": "development"}), priority=80
    )

    # 4. Timing middleware (runs fourth)
    event_system.add_middleware(create_timing_middleware(), priority=70)

    # 5. History middleware (runs last)
    history_middleware = HistoryMiddleware(max_history=100)
    event_system.add_middleware(history_middleware, priority=0)

    # Subscribe to events
    event_system.subscribe(
        event_type="*", callback=lambda event: logger.info(f"Received event: {event['event_type']}")
    )

    # Publish events
    event_system.publish(
        event_type="example.item.created", data={"item_id": "123", "name": "Example Item"}
    )

    event_system.publish(
        event_type="example.user.created", data={"user_id": "456", "name": "Example User"}
    )

    # The user event should be filtered out
    history = history_middleware.get_history()
    logger.info(f"History contains {len(history)} events")

    # Show stats
    logger.info(f"Event system stats: {event_system.get_stats()}")


def example_custom_middleware():
    """Example of creating a custom middleware."""
    # Create event system
    event_system = EventSystem()

    # Define a custom middleware that transforms event types
    class EventTypeTransformerMiddleware:
        def __init__(self, prefix: str):
            self.prefix = prefix

        def process(self, event, next):
            # Create a copy of the event
            transformed_event = event.copy()

            # Transform the event type
            if not transformed_event["event_type"].startswith(self.prefix):
                transformed_event["event_type"] = f"{self.prefix}.{transformed_event['event_type']}"

            # Continue processing
            return next(transformed_event)

    # Add custom middleware
    event_system.add_middleware(EventTypeTransformerMiddleware(prefix="app"))

    # Subscribe to events with the transformed prefix
    event_system.subscribe(
        event_type="app.*",
        callback=lambda event: logger.info(f"Received event: {event['event_type']}"),
    )

    # Publish event with original type
    event_system.publish(
        event_type="example.created", data={"item_id": "123", "name": "Example Item"}
    )

    # The event type should be transformed to app.example.created
    events = event_system.get_events(limit=1)
    if events:
        logger.info(f"Transformed event type: {events[0]['event_type']}")


def run():
    """Run the middleware examples."""
    logger.info("\n===== Logging Middleware =====")
    example_logging_middleware()

    logger.info("\n===== Filter Middleware =====")
    example_filter_middleware()

    logger.info("\n===== Enrichment Middleware =====")
    example_enrichment_middleware()

    logger.info("\n===== Timing Middleware =====")
    example_timing_middleware()

    logger.info("\n===== History Middleware =====")
    example_history_middleware()

    logger.info("\n===== Middleware Chain =====")
    example_middleware_chain()

    logger.info("\n===== Custom Middleware =====")
    example_custom_middleware()


if __name__ == "__main__":
    run()
