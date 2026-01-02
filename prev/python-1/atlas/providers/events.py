"""
Event-enabled provider system.

This module provides the integration between the core event system and the provider system,
enabling detailed event tracking for provider operations like generation and streaming.
"""

import time
import uuid
from datetime import datetime
from typing import Any, ClassVar

from atlas.core.logging import get_logger
from atlas.core.services.events import EventSystem, create_event_system
from atlas.core.services.middleware import (
    HistoryMiddleware,
    create_logging_middleware,
    create_timing_middleware,
)
from atlas.providers.base import ModelProvider
from atlas.providers.messages import ModelRequest, ModelResponse
from atlas.providers.streaming import StreamHandler

# Create logger for this module
logger = get_logger(__name__)


class EventEnabledProvider:
    """Mixin class that adds event system capabilities to providers.

    This class enables detailed telemetry, error tracking, performance monitoring,
    and debugging for provider operations by integrating with the Atlas event system.
    """

    # Standard event types
    EVENT_GENERATE_START: ClassVar[str] = "provider.generate.start"
    EVENT_GENERATE_END: ClassVar[str] = "provider.generate.end"
    EVENT_GENERATE_ERROR: ClassVar[str] = "provider.generate.error"
    EVENT_STREAM_START: ClassVar[str] = "provider.stream.start"
    EVENT_STREAM_CHUNK: ClassVar[str] = "provider.stream.chunk"
    EVENT_STREAM_END: ClassVar[str] = "provider.stream.end"
    EVENT_STREAM_ERROR: ClassVar[str] = "provider.stream.error"
    EVENT_VALIDATE_FAILURE: ClassVar[str] = "provider.validate.failure"
    EVENT_FALLBACK: ClassVar[str] = "provider.fallback"

    def __init__(self, event_system: EventSystem | None = None, **kwargs):
        """Initialize with an event system.

        Args:
            event_system: Event system to use for publishing events.
            **kwargs: Additional keyword arguments to pass to the parent class.
        """
        self.event_system = event_system or create_event_system()

        # Add middleware for event tracking
        self.event_system.add_middleware(create_logging_middleware())
        self.event_system.add_middleware(create_timing_middleware())

        # Initialize event history for debugging
        self.history_middleware = HistoryMiddleware(max_history=100)
        self.event_system.add_middleware(self.history_middleware)

        # Initialize timing metrics
        self._generation_start_times = {}
        self._stream_start_times = {}

        # Call parent class __init__
        super().__init__(**kwargs)

    def publish_event(self, event_type: str, data: dict[str, Any]):
        """Publish an event with the provider as the source.

        Args:
            event_type: Type of event to publish.
            data: Event data.
        """
        if self.event_system:
            # Get provider name - use parent class property
            if hasattr(super(), "name") and callable(super().name):
                provider_name = super().name
            else:
                provider_name = getattr(self, "name", "unknown_provider")

            # Add standard fields
            data["provider"] = provider_name

            # Add model name if available
            if hasattr(self, "model_name"):
                model_name = self.model_name
                if model_name:
                    data["model"] = model_name

            # Publish event
            self.event_system.publish(
                event_type=event_type, data=data, source=f"provider.{provider_name}"
            )

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from the model with event tracking.

        Args:
            request: The model request.

        Returns:
            A ModelResponse containing the generated content and metadata.
        """
        # Generate a request ID to correlate events
        request_id = str(uuid.uuid4())
        start_time = time.time()
        self._generation_start_times[request_id] = start_time

        # Publish generation start event
        self.publish_event(
            event_type=self.EVENT_GENERATE_START,
            data={
                "request_id": request_id,
                "request": request.to_dict(),
                "timestamp": datetime.now().isoformat(),
            },
        )

        try:
            # Call parent class implementation
            response = super().generate(request)

            # Calculate elapsed time
            end_time = time.time()
            elapsed = end_time - self._generation_start_times.get(request_id, start_time)

            # Publish generation end event
            self.publish_event(
                event_type=self.EVENT_GENERATE_END,
                data={
                    "request_id": request_id,
                    "latency": elapsed,
                    "token_count": getattr(response, "token_usage", None),
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Clean up timing data
            self._generation_start_times.pop(request_id, None)

            return response

        except Exception as e:
            # Calculate elapsed time
            end_time = time.time()
            elapsed = end_time - self._generation_start_times.get(request_id, start_time)

            # Publish error event
            self.publish_event(
                event_type=self.EVENT_GENERATE_ERROR,
                data={
                    "request_id": request_id,
                    "latency": elapsed,
                    "error": str(e),
                    "error_type": e.__class__.__name__,
                    "success": False,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Clean up timing data
            self._generation_start_times.pop(request_id, None)

            # Re-raise the exception
            raise

    def stream(self, request: ModelRequest) -> tuple[ModelResponse, StreamHandler]:
        """Stream a response from the model with event tracking.

        Args:
            request: The model request.

        Returns:
            A tuple of (final ModelResponse, StreamHandler).
        """
        # Generate a request ID to correlate events
        request_id = str(uuid.uuid4())
        start_time = time.time()
        self._stream_start_times[request_id] = start_time

        # Initialize stream metrics
        chunk_count = 0
        token_count = 0

        # Publish stream start event
        self.publish_event(
            event_type=self.EVENT_STREAM_START,
            data={
                "request_id": request_id,
                "request": request.to_dict(),
                "timestamp": datetime.now().isoformat(),
            },
        )

        try:
            # Call parent class implementation
            response, stream_handler = super().stream(request)

            # Create a wrapped stream handler to track events
            original_handler = stream_handler

            # Create a wrapper class to avoid modifying the original handler
            class EventTrackedStreamHandler(StreamHandler):
                """Stream handler that tracks events."""

                def __init__(
                    self,
                    original_handler: StreamHandler,
                    provider: EventEnabledProvider,
                    request_id: str,
                ):
                    """Initialize the tracked stream handler.

                    Args:
                        original_handler: The original stream handler.
                        provider: The provider instance.
                        request_id: The request ID for correlation.
                    """
                    self.original_handler = original_handler
                    self.provider = provider
                    self.request_id = request_id
                    self.chunk_count = 0
                    self.token_count = 0
                    self.complete = False

                def on_content(self, delta: str) -> None:
                    """Handle content updates with event tracking.

                    Args:
                        delta: The content delta.
                    """
                    # Track metrics
                    self.chunk_count += 1
                    estimated_tokens = len(delta.split()) / 4  # Very rough estimate
                    self.token_count += estimated_tokens

                    # Publish stream chunk event
                    self.provider.publish_event(
                        event_type=self.provider.EVENT_STREAM_CHUNK,
                        data={
                            "request_id": self.request_id,
                            "chunk_index": self.chunk_count,
                            "chunk_size": len(delta),
                            "estimated_tokens": estimated_tokens,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )

                    # Forward to original handler
                    if hasattr(self.original_handler, "on_content"):
                        self.original_handler.on_content(delta)

                def on_error(self, error: str) -> None:
                    """Handle errors with event tracking.

                    Args:
                        error: The error message.
                    """
                    # Calculate elapsed time
                    end_time = time.time()
                    start_time = self.provider._stream_start_times.get(self.request_id, end_time)
                    elapsed = end_time - start_time

                    # Publish stream error event
                    self.provider.publish_event(
                        event_type=self.provider.EVENT_STREAM_ERROR,
                        data={
                            "request_id": self.request_id,
                            "error": error,
                            "latency": elapsed,
                            "chunks_received": self.chunk_count,
                            "estimated_tokens": self.token_count,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )

                    # Forward to original handler
                    if hasattr(self.original_handler, "on_error"):
                        self.original_handler.on_error(error)

                def on_finish(self) -> None:
                    """Handle stream completion with event tracking."""
                    # Calculate elapsed time
                    end_time = time.time()
                    start_time = self.provider._stream_start_times.get(self.request_id, end_time)
                    elapsed = end_time - start_time

                    # Publish stream end event
                    self.provider.publish_event(
                        event_type=self.provider.EVENT_STREAM_END,
                        data={
                            "request_id": self.request_id,
                            "latency": elapsed,
                            "chunks_received": self.chunk_count,
                            "estimated_tokens": self.token_count,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )

                    # Mark as complete and clean up timing data
                    self.complete = True
                    self.provider._stream_start_times.pop(self.request_id, None)

                    # Forward to original handler
                    if hasattr(self.original_handler, "on_finish"):
                        self.original_handler.on_finish()

            # Return response with tracked handler
            return response, EventTrackedStreamHandler(
                original_handler=original_handler, provider=self, request_id=request_id
            )

        except Exception as e:
            # Calculate elapsed time
            end_time = time.time()
            elapsed = end_time - self._stream_start_times.get(request_id, start_time)

            # Publish error event
            self.publish_event(
                event_type=self.EVENT_STREAM_ERROR,
                data={
                    "request_id": request_id,
                    "latency": elapsed,
                    "error": str(e),
                    "error_type": e.__class__.__name__,
                    "success": False,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Clean up timing data
            self._stream_start_times.pop(request_id, None)

            # Re-raise the exception
            raise

    def validate_api_key(self) -> bool:
        """Validate that the API key is set and valid with event tracking.

        Returns:
            True if the API key is valid, False otherwise.
        """
        try:
            # Call parent class implementation
            result = super().validate_api_key()

            # If validation failed, publish event
            if not result:
                self.publish_event(
                    event_type=self.EVENT_VALIDATE_FAILURE,
                    data={
                        "validation_type": "api_key",
                        "error": "API key validation failed",
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            return result

        except Exception as e:
            # Publish error event
            self.publish_event(
                event_type=self.EVENT_VALIDATE_FAILURE,
                data={
                    "validation_type": "api_key",
                    "error": str(e),
                    "error_type": e.__class__.__name__,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Re-raise the exception
            raise

    def get_event_history(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Get the event history for this provider.

        Args:
            limit: Maximum number of events to return.

        Returns:
            List of events, newest first.
        """
        if not hasattr(self, "history_middleware"):
            return []

        history = self.history_middleware.get_history()

        if limit:
            history = history[-limit:]

        return history


class EventEnabledModelProvider(EventEnabledProvider, ModelProvider):
    """Model provider with integrated event system support.

    This class combines the standard ModelProvider interface with
    event system integration for detailed operation tracking.
    """

    pass


def create_event_enabled_provider(
    provider_class: type, event_system: EventSystem | None = None, **kwargs
) -> EventEnabledProvider:
    """Create an event-enabled provider from any provider class.

    Args:
        provider_class: The provider class to enhance with events.
        event_system: Optional event system to use.
        **kwargs: Additional arguments to pass to the provider constructor.

    Returns:
        An instance of the provider class with event capabilities.
    """

    # Create a new class that inherits from EventEnabledProvider and the given class
    class EventEnhancedProvider(EventEnabledProvider, provider_class):
        """Provider with event capabilities."""

        pass

    # Set proper class name
    EventEnhancedProvider.__name__ = f"EventEnabled{provider_class.__name__}"

    # Create an instance
    return EventEnhancedProvider(event_system=event_system, **kwargs)
