"""
Event system with subscription capability.

This module provides a publish-subscribe event system that enables components
to communicate through events without direct dependencies. The implementation
is thread-safe and supports wildcard pattern matching for event types.
"""

import fnmatch
import re
import uuid
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from threading import RLock
from typing import Any, ClassVar, Final, TypeAlias

from atlas.core.errors import AtlasError, ErrorCategory, ErrorSeverity
from atlas.core.logging import get_logger
from atlas.core.services.middleware import EventMiddleware, MiddlewarePipeline
from atlas.schemas.services import event_schema, subscription_schema

# Type aliases for improved clarity
EventType: TypeAlias = str
EventId: TypeAlias = str
EventData: TypeAlias = dict[str, Any]
SubscriptionId: TypeAlias = str
EventCallback: TypeAlias = Callable[[dict[str, Any]], None]

# Create a logger for this module
logger = get_logger(__name__)


# Custom error classes for the event system
class EventError(AtlasError):
    """Base class for event system errors."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
        """
        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.DATA,
            details=details,
            cause=cause,
        )


class EventSubscriptionError(EventError):
    """Error related to event subscription."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        subscription_id: str | None = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            subscription_id: The ID of the subscription causing the error.
        """
        details = details or {}
        if subscription_id:
            details["subscription_id"] = subscription_id

        super().__init__(
            message=message,
            details=details,
            cause=cause,
            severity=severity,
        )


class EventPublishError(EventError):
    """Error related to event publishing."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        event_type: str | None = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            event_type: The type of event causing the error.
        """
        details = details or {}
        if event_type:
            details["event_type"] = event_type

        super().__init__(
            message=message,
            details=details,
            cause=cause,
            severity=severity,
        )


class EventSubscription:
    """Represents a subscription to an event type or pattern."""

    def __init__(
        self,
        subscription_id: str,
        event_type: str,
        callback: EventCallback,
        source_filter: str | None = None,
    ):
        """Initialize a new event subscription.

        Args:
            subscription_id: Unique identifier for this subscription.
            event_type: The event type or pattern to subscribe to.
            callback: The function to call when a matching event is published.
            source_filter: Optional filter for event source.
        """
        self.subscription_id = subscription_id
        self.event_type = event_type
        self.callback = callback
        self.source_filter = source_filter

        # Convert the event type pattern to a regex for faster matching
        self._pattern = self._create_match_pattern(event_type)

        logger.debug(
            f"Created subscription {subscription_id} for event type {event_type} "
            f"with source filter {source_filter}"
        )

    def _create_match_pattern(self, event_type: str) -> str:
        """Convert an event type pattern to a regex pattern.

        Args:
            event_type: The event type pattern.

        Returns:
            A regex pattern string.
        """
        # Replace wildcard * with regex .*
        # Replace dots with escaped dots
        pattern = event_type.replace(".", r"\.")
        pattern = pattern.replace("*", ".*")
        return f"^{pattern}$"

    def matches(self, event_type: str, source: str | None = None) -> bool:
        """Check if this subscription matches the given event type and source.

        Args:
            event_type: The event type to check.
            source: The event source to check.

        Returns:
            True if the subscription matches, False otherwise.
        """
        # Check event type pattern
        if not re.match(self._pattern, event_type):
            return False

        # Check source filter if provided
        if self.source_filter and source:
            if not fnmatch.fnmatch(source, self.source_filter):
                return False

        return True

    def notify(self, event: dict[str, Any]) -> None:
        """Notify this subscription of an event.

        Args:
            event: The event data.
        """
        try:
            self.callback(event)
        except Exception as e:
            logger.error(
                f"Error in event callback for subscription {self.subscription_id}: {e}",
                exc_info=True,
            )


class EventSystem:
    """Thread-safe event system with publish-subscribe pattern and middleware support."""

    # Class constants
    MAX_EVENT_HISTORY: ClassVar[int] = 1000
    DEFAULT_SYSTEM_SOURCE: Final[str] = "atlas.core.events"

    def __init__(self, max_history: int = MAX_EVENT_HISTORY):
        """Initialize a new event system.

        Args:
            max_history: Maximum number of events to keep in history.
        """
        self._subscriptions: dict[SubscriptionId, EventSubscription] = {}
        self._events: list[dict[str, Any]] = []
        self._lock = RLock()
        self._max_history = max_history

        # Track stats
        self._published_count = 0
        self._delivery_count = 0
        self._filtered_count = 0

        # Middleware pipeline
        self._middleware_pipeline = MiddlewarePipeline()

        logger.debug(f"Created EventSystem with max_history={max_history}")

    def subscribe(
        self, event_type: str, callback: EventCallback, source_filter: str | None = None
    ) -> str:
        """Subscribe to events of a specific type or pattern.

        Args:
            event_type: The event type or pattern to subscribe to.
                Use '*' as a wildcard for any segment.
                Example: 'system.*.started' matches 'system.service.started'
            callback: Function to call when a matching event is published.
            source_filter: Optional filter for event source.

        Returns:
            The subscription ID.

        Raises:
            EventSubscriptionError: If the subscription parameters are invalid.
        """
        # Check callback is callable
        if not callable(callback):
            raise EventSubscriptionError(
                message="Callback must be callable", subscription_id=None, event_type=event_type
            )

        try:
            # Validate using schema
            subscription_data = subscription_schema.load(
                {
                    "subscription_id": str(uuid.uuid4()),
                    "event_type": event_type,
                    "source_filter": source_filter,
                    "callback_name": (
                        callback.__name__ if hasattr(callback, "__name__") else "anonymous"
                    ),
                }
            )

            subscription_id = subscription_data["subscription_id"]

            # Create subscription
            subscription = EventSubscription(
                subscription_id=subscription_id,
                event_type=event_type,
                callback=callback,
                source_filter=source_filter,
            )

            # Add to subscriptions
            with self._lock:
                self._subscriptions[subscription_id] = subscription

            logger.debug(
                f"Added subscription {subscription_id} for event type {event_type} "
                f"with source filter {source_filter}"
            )
            return subscription_id

        except Exception as e:
            raise EventSubscriptionError(
                f"Failed to create subscription for event type {event_type}: {e}", cause=e
            )

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events.

        Args:
            subscription_id: The subscription ID to remove.

        Returns:
            True if subscription was removed, False if not found.
        """
        with self._lock:
            if subscription_id in self._subscriptions:
                del self._subscriptions[subscription_id]
                logger.debug(f"Removed subscription {subscription_id}")
                return True
            return False

    def publish(self, event_type: str, data: dict[str, Any], source: str | None = None) -> str:
        """Publish an event to all matching subscribers.

        Args:
            event_type: The type of event to publish.
            data: The event data.
            source: The source of the event.

        Returns:
            The event ID.

        Raises:
            EventPublishError: If the event could not be published.
        """
        try:
            # Use default source if not provided
            source = source or self.DEFAULT_SYSTEM_SOURCE

            # Validate using schema
            event_data = event_schema.load(
                {
                    "event_id": str(uuid.uuid4()),
                    "event_type": event_type,
                    "source": source,
                    "timestamp": datetime.now().isoformat(),
                    "data": data,
                }
            )

            event_id = event_data["event_id"]

            # Process event through middleware pipeline
            processed_event = self._middleware_pipeline.process(event_data)

            # If event was filtered out, return ID but don't continue
            if processed_event is None:
                with self._lock:
                    self._filtered_count += 1

                logger.debug(
                    f"Event {event_id} of type {event_type} was filtered out by middleware"
                )
                return event_id

            # Use processed event for the rest of the flow
            event_data = processed_event

            # Add to history
            with self._lock:
                self._events.append(event_data)

                # Trim history if needed
                if len(self._events) > self._max_history:
                    self._events = self._events[-self._max_history :]

                # Track stats
                self._published_count += 1

                # Get matching subscriptions
                matching_subscriptions = [
                    subscription
                    for subscription in self._subscriptions.values()
                    if subscription.matches(event_data["event_type"], event_data["source"])
                ]

            # Notify subscribers outside the lock
            delivery_count = 0
            for subscription in matching_subscriptions:
                try:
                    subscription.notify(event_data)
                    delivery_count += 1
                except Exception as e:
                    logger.error(
                        f"Error delivering event {event_id} to subscription "
                        f"{subscription.subscription_id}: {e}",
                        exc_info=True,
                    )

            # Update delivery stats
            with self._lock:
                self._delivery_count += delivery_count

            logger.debug(
                f"Published event {event_id} of type {event_data['event_type']} from {event_data['source']} "
                f"to {delivery_count} subscribers"
            )
            return event_id

        except Exception as e:
            raise EventPublishError(
                f"Failed to publish event of type {event_type}: {e}", cause=e, event_type=event_type
            )

    def get_events(
        self,
        event_type: str | None = None,
        source: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get events from history with optional filtering.

        Args:
            event_type: Optional event type filter.
            source: Optional source filter.
            limit: Maximum number of events to return.

        Returns:
            List of matching events, newest first.
        """
        with self._lock:
            # Start with all events
            events = self._events.copy()

            # Apply filters
            if event_type:
                events = [event for event in events if event["event_type"] == event_type]

            if source:
                events = [event for event in events if event["source"] == source]

            # Apply limit and return newest first
            if limit:
                events = events[-limit:]

            # Return newest first
            return list(reversed(events))

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        """Get a specific event by ID.

        Args:
            event_id: The event ID to retrieve.

        Returns:
            The event data or None if not found.
        """
        with self._lock:
            for event in self._events:
                if event["event_id"] == event_id:
                    return event
            return None

    def clear_events(self) -> None:
        """Clear all events from history."""
        with self._lock:
            self._events = []
            logger.debug("Cleared event history")

    def add_middleware(self, middleware: EventMiddleware, priority: int = 0) -> None:
        """Add middleware to the event processing pipeline.

        Args:
            middleware: The middleware to add.
            priority: The priority of the middleware (higher runs earlier).
        """
        self._middleware_pipeline.add(middleware, priority)
        logger.debug(f"Added middleware {middleware.__class__.__name__} to event system")

    def remove_middleware(self, middleware: EventMiddleware) -> bool:
        """Remove middleware from the event processing pipeline.

        Args:
            middleware: The middleware to remove.

        Returns:
            True if middleware was removed, False if not found.
        """
        result = self._middleware_pipeline.remove(middleware)
        if result:
            logger.debug(f"Removed middleware {middleware.__class__.__name__} from event system")
        return result

    def get_stats(self) -> dict[str, Any]:
        """Get event system statistics.

        Returns:
            Dictionary of event system statistics.
        """
        with self._lock:
            return {
                "subscription_count": len(self._subscriptions),
                "event_history_size": len(self._events),
                "published_count": self._published_count,
                "delivery_count": self._delivery_count,
                "filtered_count": self._filtered_count,
                "middleware_count": self._middleware_pipeline.get_middleware_count(),
                "max_history": self._max_history,
            }

    def get_subscriptions(self, event_type: str | None = None) -> dict[str, dict[str, Any]]:
        """Get all subscriptions with optional filtering.

        Args:
            event_type: Optional event type filter.

        Returns:
            Dictionary of subscription IDs to subscription metadata.
        """
        with self._lock:
            if not event_type:
                # Return all subscriptions
                return {
                    sub_id: {
                        "event_type": sub.event_type,
                        "source_filter": sub.source_filter,
                        "subscription_id": sub.subscription_id,
                    }
                    for sub_id, sub in self._subscriptions.items()
                }

            # Filter by event type
            return {
                sub_id: {
                    "event_type": sub.event_type,
                    "source_filter": sub.source_filter,
                    "subscription_id": sub.subscription_id,
                }
                for sub_id, sub in self._subscriptions.items()
                if sub.event_type == event_type
            }


def create_event_system(max_history: int = EventSystem.MAX_EVENT_HISTORY) -> EventSystem:
    """Create a new event system.

    Args:
        max_history: Maximum number of events to keep in history.

    Returns:
        A new EventSystem instance.
    """
    return EventSystem(max_history=max_history)


# Event decorators
def on_event(event_system: EventSystem, event_type: str, source_filter: str | None = None):
    """Decorator to subscribe a function to an event.

    Args:
        event_system: The event system to subscribe to.
        event_type: The event type or pattern to subscribe to.
        source_filter: Optional filter for event source.

    Returns:
        A decorator function.
    """

    def decorator(func):
        """Decorator to subscribe a function to an event.

        Args:
            func: The function to subscribe.

        Returns:
            The original function.
        """
        subscription_id = event_system.subscribe(
            event_type=event_type, callback=func, source_filter=source_filter
        )

        # Store subscription ID on the function
        if not hasattr(func, "_event_subscriptions"):
            func._event_subscriptions = []
        func._event_subscriptions.append((event_system, subscription_id))

        return func

    return decorator


def emit_event(event_system: EventSystem, event_type: str, source: str | None = None):
    """Decorator to emit an event after a function is called.

    Args:
        event_system: The event system to publish to.
        event_type: The type of event to publish.
        source: The source of the event.

    Returns:
        A decorator function.
    """

    def decorator(func):
        """Decorator to emit an event after a function is called.

        Args:
            func: The function to decorate.

        Returns:
            The wrapped function.
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper to call the function and emit an event.

            Args:
                *args: Arguments to pass to the function.
                **kwargs: Keyword arguments to pass to the function.

            Returns:
                The result of the function.
            """
            result = func(*args, **kwargs)

            # Publish event
            event_data = {
                "result": result,
                "function": func.__name__,
                "timestamp": datetime.now().isoformat(),
            }

            # Include arguments if safe to serialize
            try:
                import json

                arg_data = {}

                # Add positional arguments
                for i, arg in enumerate(args):
                    if isinstance(arg, (str, int, float, bool, list, dict, tuple)) or arg is None:
                        arg_data[f"arg_{i}"] = arg

                # Add keyword arguments
                for key, value in kwargs.items():
                    if (
                        isinstance(value, (str, int, float, bool, list, dict, tuple))
                        or value is None
                    ):
                        arg_data[key] = value

                # Test serialization
                json.dumps(arg_data)
                event_data["args"] = arg_data

            except (TypeError, ValueError):
                # If serialization fails, just include the argument count
                event_data["arg_count"] = len(args) + len(kwargs)

            # Publish event
            actual_source = source or func.__module__
            event_system.publish(event_type=event_type, data=event_data, source=actual_source)

            return result

        return wrapper

    return decorator
