"""
Middleware pipeline implementation for event processing.

This module provides a thread-safe middleware implementation that allows for
intercepting, modifying, and filtering events before they reach subscribers.
"""

from collections.abc import Callable
from datetime import datetime
from threading import RLock
from typing import Any, Protocol, TypeAlias, runtime_checkable

from atlas.core.errors import AtlasError, ErrorCategory, ErrorSeverity
from atlas.core.logging import get_logger

# Type aliases for improved clarity
EventData: TypeAlias = dict[str, Any]
NextMiddleware: TypeAlias = Callable[[EventData], EventData | None]

# Create a logger for this module
logger = get_logger(__name__)


class MiddlewareError(AtlasError):
    """Error related to middleware processing."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        middleware_id: str | None = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            middleware_id: The ID of the middleware causing the error.
        """
        details = details or {}
        if middleware_id:
            details["middleware_id"] = middleware_id

        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.DATA,
            details=details,
            cause=cause,
        )


@runtime_checkable
class EventMiddleware(Protocol):
    """Protocol for event middleware components."""

    def process(self, event: EventData, next: NextMiddleware) -> EventData | None:
        """Process an event and pass it to the next middleware.

        Args:
            event: The event data to process.
            next: Callback to pass the event to the next middleware.

        Returns:
            The processed event data or None if the event should be dropped.
        """
        ...


class MiddlewarePipeline:
    """Thread-safe pipeline for processing events through middleware."""

    def __init__(self):
        """Initialize the middleware pipeline."""
        self._middleware: list[tuple[int, EventMiddleware]] = []
        self._lock = RLock()
        logger.debug("Created middleware pipeline")

    def add(self, middleware: EventMiddleware, priority: int = 0) -> None:
        """Add middleware to the pipeline.

        Args:
            middleware: The middleware to add.
            priority: The priority of the middleware (higher runs earlier).

        Raises:
            MiddlewareError: If the middleware doesn't implement EventMiddleware.
        """
        if not isinstance(middleware, EventMiddleware):
            raise MiddlewareError(
                message=f"Middleware must implement EventMiddleware protocol: {middleware}"
            )

        with self._lock:
            # Store as (priority, middleware) tuple
            # Find insertion point to maintain order by priority (descending)
            pos = 0
            for i, (p, _) in enumerate(self._middleware):
                if priority > p:
                    pos = i
                    break
                else:
                    pos = i + 1

            self._middleware.insert(pos, (priority, middleware))

        logger.debug(f"Added middleware {middleware.__class__.__name__} with priority {priority}")

    def remove(self, middleware: EventMiddleware) -> bool:
        """Remove middleware from the pipeline.

        Args:
            middleware: The middleware to remove.

        Returns:
            True if middleware was removed, False if not found.
        """
        with self._lock:
            # Find middleware in the list
            for i, (_, m) in enumerate(self._middleware):
                if m == middleware:
                    del self._middleware[i]
                    logger.debug(f"Removed middleware {middleware.__class__.__name__}")
                    return True

            return False

    def process(self, event: EventData) -> EventData | None:
        """Process an event through the middleware pipeline.

        Args:
            event: The event data to process.

        Returns:
            The processed event data or None if the event was filtered out.
        """
        # Create a copy of middleware list to avoid issues with concurrent modifications
        with self._lock:
            middleware = [(p, m) for p, m in self._middleware]

        if not middleware:
            return event  # No middleware, return event as is

        # Extract just the middleware objects (not priorities)
        middleware_objs = [m for _, m in middleware]

        # Create a chain of middleware functions
        def create_chain(index: int) -> NextMiddleware:
            if index >= len(middleware_objs):
                # End of chain, return event as is
                return lambda e: e

            # Create next function in chain
            next_middleware = create_chain(index + 1)

            # Create function that processes this middleware
            def process_middleware(event_data: EventData) -> EventData | None:
                try:
                    return middleware_objs[index].process(event_data, next_middleware)
                except Exception as e:
                    logger.error(
                        f"Error in middleware {middleware_objs[index].__class__.__name__}: {e}",
                        exc_info=True,
                    )
                    # Continue the chain despite the error
                    return next_middleware(event_data)

            return process_middleware

        # Start processing with the first middleware
        chain = create_chain(0)
        return chain(event)

    def get_middleware_count(self) -> int:
        """Get the number of middleware in the pipeline.

        Returns:
            The number of middleware in the pipeline.
        """
        with self._lock:
            return len(self._middleware)


# Common middleware implementations


def create_middleware(
    processor: Callable[[EventData, NextMiddleware], EventData | None],
) -> EventMiddleware:
    """Create a middleware from a function.

    Args:
        processor: The function to use as middleware.

    Returns:
        An event middleware.
    """

    class FunctionMiddleware:
        def process(self, event: EventData, next: NextMiddleware) -> EventData | None:
            return processor(event, next)

    return FunctionMiddleware()


class LoggingMiddleware:
    """Middleware that logs events."""

    def __init__(self, logger=None, log_level: str = "DEBUG"):
        """Initialize the middleware.

        Args:
            logger: Optional logger to use.
            log_level: Log level to use.
        """
        self.logger = logger or get_logger(f"{__name__}.logging")
        self.log_level = log_level.lower()

    def process(self, event: EventData, next: NextMiddleware) -> EventData | None:
        """Process an event by logging it.

        Args:
            event: The event data to process.
            next: Callback to pass the event to the next middleware.

        Returns:
            The processed event data.
        """
        log_func = getattr(self.logger, self.log_level)
        log_func(f"Event {event['event_id']}: {event['event_type']} from {event['source']}")
        return next(event)


class EventFilterMiddleware:
    """Middleware that filters events based on a predicate."""

    def __init__(self, predicate: Callable[[EventData], bool]):
        """Initialize the middleware.

        Args:
            predicate: Function to determine if an event should be kept.
        """
        self.predicate = predicate

    def process(self, event: EventData, next: NextMiddleware) -> EventData | None:
        """Process an event by filtering it.

        Args:
            event: The event data to process.
            next: Callback to pass the event to the next middleware.

        Returns:
            The processed event data or None if the event should be dropped.
        """
        if self.predicate(event):
            return next(event)
        return None


class EventEnrichmentMiddleware:
    """Middleware that enriches events with additional data."""

    def __init__(self, enrichment_data: dict[str, Any]):
        """Initialize the middleware.

        Args:
            enrichment_data: Data to add to events.
        """
        self.enrichment_data = enrichment_data

    def process(self, event: EventData, next: NextMiddleware) -> EventData | None:
        """Process an event by enriching it.

        Args:
            event: The event data to process.
            next: Callback to pass the event to the next middleware.

        Returns:
            The processed event data.
        """
        # Create a copy of the event to avoid modifying the original
        enriched_event = event.copy()

        # Add enrichment data to event data
        if "data" in enriched_event:
            # Create a copy of the data to avoid modifying the original
            enriched_event["data"] = enriched_event["data"].copy()
            enriched_event["data"].update(self.enrichment_data)

        return next(enriched_event)


class TimingMiddleware:
    """Middleware that adds timing information to events."""

    def process(self, event: EventData, next: NextMiddleware) -> EventData | None:
        """Process an event by adding timing information.

        Args:
            event: The event data to process.
            next: Callback to pass the event to the next middleware.

        Returns:
            The processed event data.
        """
        # Create a copy of the event
        event_copy = event.copy()

        # Ensure metadata exists
        if "metadata" not in event_copy:
            event_copy["metadata"] = {}
        else:
            event_copy["metadata"] = event_copy["metadata"].copy()

        # Add start time
        event_copy["metadata"]["processing_started"] = datetime.now().isoformat()

        # Process event
        result = next(event_copy)

        # Add end time if result is not None
        if result is not None:
            # Ensure metadata exists (might have been modified by another middleware)
            if "metadata" not in result:
                result["metadata"] = {}

            result["metadata"]["processing_completed"] = datetime.now().isoformat()

            # Calculate processing time if possible
            try:
                start = datetime.fromisoformat(result["metadata"]["processing_started"])
                end = datetime.fromisoformat(result["metadata"]["processing_completed"])
                result["metadata"]["processing_time_ms"] = (end - start).total_seconds() * 1000
            except (ValueError, KeyError):
                pass

        return result


class HistoryMiddleware:
    """Middleware that maintains a history of processed events with optional replay."""

    def __init__(self, max_history: int = 100):
        """Initialize the middleware.

        Args:
            max_history: Maximum number of events to keep in history.
        """
        self._history: list[EventData] = []
        self._lock = RLock()
        self._max_history = max_history

    def process(self, event: EventData, next: NextMiddleware) -> EventData | None:
        """Process an event by adding it to the history.

        Args:
            event: The event data to process.
            next: Callback to pass the event to the next middleware.

        Returns:
            The processed event data.
        """
        # Process event first
        result = next(event)

        # Add to history if not filtered out
        if result is not None:
            with self._lock:
                self._history.append(result.copy())

                # Trim history if needed
                if len(self._history) > self._max_history:
                    self._history = self._history[-self._max_history :]

        return result

    def get_history(
        self,
        event_type: str | None = None,
        source: str | None = None,
        limit: int | None = None,
    ) -> list[EventData]:
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
            events = self._history.copy()

            # Apply filters
            if event_type:
                events = [event for event in events if event["event_type"] == event_type]

            if source:
                events = [event for event in events if event["source"] == source]

            # Apply limit
            if limit and limit > 0:
                events = events[-limit:]

            # Return newest first
            return list(reversed(events))

    def replay_history(
        self,
        processor: Callable[[EventData], None],
        event_type: str | None = None,
        source: str | None = None,
    ) -> int:
        """Replay events from history through a processor function.

        Args:
            processor: Function to process each event.
            event_type: Optional event type filter.
            source: Optional source filter.

        Returns:
            The number of events replayed.
        """
        events = self.get_history(event_type=event_type, source=source)

        for event in events:
            try:
                processor(event)
            except Exception as e:
                logger.error(f"Error replaying event {event['event_id']}: {e}", exc_info=True)

        return len(events)

    def clear_history(self) -> None:
        """Clear the event history."""
        with self._lock:
            self._history = []


# Utility functions for creating middleware
def create_logging_middleware(log_level: str = "DEBUG") -> EventMiddleware:
    """Create a middleware that logs events.

    Args:
        log_level: The log level to use.

    Returns:
        An event middleware that logs events.
    """
    return LoggingMiddleware(log_level=log_level)


def create_filter_middleware(predicate: Callable[[EventData], bool]) -> EventMiddleware:
    """Create a middleware that filters events based on a predicate.

    Args:
        predicate: Function to determine if an event should be kept.

    Returns:
        An event middleware that filters events.
    """
    return EventFilterMiddleware(predicate)


def create_enrichment_middleware(enrichment_data: dict[str, Any]) -> EventMiddleware:
    """Create a middleware that enriches events with additional data.

    Args:
        enrichment_data: Data to add to events.

    Returns:
        An event middleware that enriches events.
    """
    return EventEnrichmentMiddleware(enrichment_data)


def create_timing_middleware() -> EventMiddleware:
    """Create a middleware that adds timing information to events.

    Returns:
        An event middleware that adds timing information.
    """
    return TimingMiddleware()


def create_history_middleware(max_history: int = 100) -> HistoryMiddleware:
    """Create a middleware that maintains a history of processed events.

    Args:
        max_history: Maximum number of events to keep in history.

    Returns:
        A history middleware instance.
    """
    return HistoryMiddleware(max_history=max_history)
