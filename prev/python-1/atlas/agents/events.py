"""
Event-enabled agent system.

This module provides the integration between the core event system and the agent system,
enabling detailed event tracking for agent operations like task execution and message processing.
"""

import time
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any, ClassVar

from atlas.agents.base import AtlasAgent
from atlas.core.logging import get_logger
from atlas.core.services.events import EventSystem, create_event_system
from atlas.core.services.middleware import (
    HistoryMiddleware,
    create_logging_middleware,
    create_timing_middleware,
)
from atlas.knowledge.retrieval import RetrievalFilter, RetrievalSettings

# Create logger for this module
logger = get_logger(__name__)


class EventEnabledAgent:
    """Mixin class that adds event system capabilities to agents.

    This class enables detailed telemetry, error tracking, performance monitoring,
    and debugging for agent operations by integrating with the Atlas event system.
    """

    # Standard event types
    EVENT_TASK_START: ClassVar[str] = "agent.task.start"
    EVENT_TASK_COMPLETE: ClassVar[str] = "agent.task.complete"
    EVENT_TASK_ERROR: ClassVar[str] = "agent.task.error"
    EVENT_MESSAGE_SENT: ClassVar[str] = "agent.message.sent"
    EVENT_STATE_CHANGE: ClassVar[str] = "agent.state.change"
    EVENT_TOOL_USE: ClassVar[str] = "agent.tool.use"
    EVENT_TOOL_RESULT: ClassVar[str] = "agent.tool.result"
    EVENT_RETRIEVAL: ClassVar[str] = "agent.retrieval"

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
        self._task_start_times = {}
        self._message_start_times = {}

        # Call parent class __init__
        super().__init__(**kwargs)

    def publish_event(self, event_type: str, data: dict[str, Any]):
        """Publish an event with the agent as the source.

        Args:
            event_type: Type of event to publish.
            data: Event data.
        """
        if self.event_system:
            # Add standard fields
            data["agent_id"] = getattr(self, "agent_id", "unknown_agent")
            data["agent_type"] = self.__class__.__name__

            # Publish event
            self.event_system.publish(
                event_type=event_type,
                data=data,
                source=f"agent.{getattr(self, 'agent_id', 'unknown_agent')}",
            )

    def query_knowledge_base(
        self,
        query: str,
        filter: Any | None = None,
        settings: Any | None = None,
    ) -> list[dict[str, Any]]:
        """Query the knowledge base for relevant information with event tracking.

        Args:
            query: The query string.
            filter: Optional filter for retrieval.
            settings: Optional retrieval settings for fine-grained control.

        Returns:
            A list of relevant documents.
        """
        # Generate a query ID to correlate events
        query_id = str(uuid.uuid4())
        start_time = time.time()

        # Publish retrieval start event
        self.publish_event(
            event_type=self.EVENT_RETRIEVAL,
            data={
                "query_id": query_id,
                "query": query,
                "action": "start",
                "timestamp": datetime.now().isoformat(),
            },
        )

        try:
            # Call parent class implementation
            results = super().query_knowledge_base(query, filter=filter, settings=settings)

            # Calculate elapsed time
            end_time = time.time()
            elapsed = end_time - start_time

            # Publish retrieval complete event
            self.publish_event(
                event_type=self.EVENT_RETRIEVAL,
                data={
                    "query_id": query_id,
                    "action": "complete",
                    "result_count": len(results),
                    "latency": elapsed,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            return results

        except Exception as e:
            # Calculate elapsed time
            end_time = time.time()
            elapsed = end_time - start_time

            # Publish error event
            self.publish_event(
                event_type=self.EVENT_RETRIEVAL,
                data={
                    "query_id": query_id,
                    "action": "error",
                    "error": str(e),
                    "error_type": e.__class__.__name__,
                    "latency": elapsed,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Re-raise the exception
            raise

    def process_message(
        self,
        message: str,
        filter: dict[str, Any] | RetrievalFilter | None = None,
        use_hybrid_search: bool = False,
        settings: RetrievalSettings | None = None,
        task_type: str | None = None,
        capabilities: dict[str, Any] | None = None,
    ) -> str:
        """Process a user message and return the agent's response with event tracking.

        Args:
            message: The user's message.
            filter: Optional metadata filter to apply during retrieval.
            use_hybrid_search: Whether to use hybrid search combining semantic and keyword search.
            settings: Optional retrieval settings for fine-grained control.
            task_type: Optional explicit task type for provider selection.
            capabilities: Optional capability requirements for provider selection.

        Returns:
            The agent's response.
        """
        # Generate a message ID to correlate events
        message_id = str(uuid.uuid4())
        start_time = time.time()
        self._message_start_times[message_id] = start_time

        # Publish message start event
        self.publish_event(
            event_type=self.EVENT_MESSAGE_SENT,
            data={
                "message_id": message_id,
                "direction": "user_to_agent",
                "message_type": "text",
                "message_length": len(message),
                "task_type": task_type,
                "capabilities": capabilities,
                "timestamp": datetime.now().isoformat(),
            },
        )

        try:
            # Call parent class implementation
            response = super().process_message(
                message=message,
                filter=filter,
                use_hybrid_search=use_hybrid_search,
                settings=settings,
                task_type=task_type,
                capabilities=capabilities,
            )

            # Calculate elapsed time
            end_time = time.time()
            elapsed = end_time - self._message_start_times.get(message_id, start_time)

            # Publish message complete event
            self.publish_event(
                event_type=self.EVENT_MESSAGE_SENT,
                data={
                    "message_id": message_id,
                    "direction": "agent_to_user",
                    "message_type": "text",
                    "message_length": len(response),
                    "response_time": elapsed,
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Clean up timing data
            self._message_start_times.pop(message_id, None)

            return response

        except Exception as e:
            # Calculate elapsed time
            end_time = time.time()
            elapsed = end_time - self._message_start_times.get(message_id, start_time)

            # Publish error event
            self.publish_event(
                event_type=self.EVENT_TASK_ERROR,
                data={
                    "message_id": message_id,
                    "error": str(e),
                    "error_type": e.__class__.__name__,
                    "execution_time": elapsed,
                    "success": False,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Clean up timing data
            self._message_start_times.pop(message_id, None)

            # Re-raise the exception
            raise

    def process_message_streaming(
        self,
        message: str,
        callback: Callable[[str, str], None],
        filter: dict[str, Any] | RetrievalFilter | None = None,
        use_hybrid_search: bool = False,
        settings: RetrievalSettings | None = None,
        task_type: str | None = None,
        capabilities: dict[str, Any] | None = None,
        streaming_control: dict[str, Any] | None = None,
    ) -> str:
        """Process a user message with streaming response and event tracking.

        Args:
            message: The user's message.
            callback: Function called for each chunk of the response.
            filter: Optional metadata filter to apply during retrieval.
            use_hybrid_search: Whether to use hybrid search combining semantic and keyword search.
            settings: Optional retrieval settings for fine-grained control.
            task_type: Optional explicit task type for provider selection.
            capabilities: Optional capability requirements for provider selection.
            streaming_control: Optional controls for streaming behavior.

        Returns:
            The complete agent response.
        """
        # Generate a message ID to correlate events
        message_id = str(uuid.uuid4())
        start_time = time.time()
        self._message_start_times[message_id] = start_time

        # Initialize stream metrics
        chunk_count = 0

        # Publish message start event
        self.publish_event(
            event_type=self.EVENT_MESSAGE_SENT,
            data={
                "message_id": message_id,
                "direction": "user_to_agent",
                "message_type": "text",
                "streaming": True,
                "message_length": len(message),
                "task_type": task_type,
                "capabilities": capabilities,
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Create a wrapped callback to track chunks
        def event_tracked_callback(delta: str, full_text: str):
            """Callback that tracks streaming events."""
            nonlocal chunk_count
            chunk_count += 1

            # Only publish events for every 5th chunk to avoid overwhelming the event system
            if chunk_count % 5 == 0:
                self.publish_event(
                    event_type="agent.stream.chunk",
                    data={
                        "message_id": message_id,
                        "chunk_index": chunk_count,
                        "chunk_size": len(delta),
                        "total_length": len(full_text),
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            # Call the original callback
            callback(delta, full_text)

        try:
            # Call parent class implementation with our tracked callback
            response = super().process_message_streaming(
                message=message,
                callback=event_tracked_callback,
                filter=filter,
                use_hybrid_search=use_hybrid_search,
                settings=settings,
                task_type=task_type,
                capabilities=capabilities,
                streaming_control=streaming_control,
            )

            # Calculate elapsed time
            end_time = time.time()
            elapsed = end_time - self._message_start_times.get(message_id, start_time)

            # Publish message complete event
            self.publish_event(
                event_type=self.EVENT_MESSAGE_SENT,
                data={
                    "message_id": message_id,
                    "direction": "agent_to_user",
                    "message_type": "text",
                    "streaming": True,
                    "message_length": len(response),
                    "chunks_received": chunk_count,
                    "response_time": elapsed,
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Clean up timing data
            self._message_start_times.pop(message_id, None)

            return response

        except Exception as e:
            # Calculate elapsed time
            end_time = time.time()
            elapsed = end_time - self._message_start_times.get(message_id, start_time)

            # Publish error event
            self.publish_event(
                event_type=self.EVENT_TASK_ERROR,
                data={
                    "message_id": message_id,
                    "error": str(e),
                    "error_type": e.__class__.__name__,
                    "execution_time": elapsed,
                    "success": False,
                    "streaming": True,
                    "chunks_received": chunk_count,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Clean up timing data
            self._message_start_times.pop(message_id, None)

            # Re-raise the exception
            raise

    def reset_conversation(self):
        """Reset the conversation history with event tracking."""
        # Publish event before reset
        self.publish_event(
            event_type=self.EVENT_STATE_CHANGE,
            data={
                "change_type": "conversation_reset",
                "previous_message_count": len(getattr(self, "messages", [])),
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Call parent class implementation
        super().reset_conversation()

    def get_event_history(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Get the event history for this agent.

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


class EventEnabledAtlasAgent(EventEnabledAgent, AtlasAgent):
    """Atlas agent with integrated event system support.

    This class combines the standard AtlasAgent interface with
    event system integration for detailed operation tracking.
    """

    pass


def create_event_enabled_agent(
    agent_class: type, event_system: EventSystem | None = None, **kwargs
) -> EventEnabledAgent:
    """Create an event-enabled agent from any agent class.

    Args:
        agent_class: The agent class to enhance with events.
        event_system: Optional event system to use.
        **kwargs: Additional arguments to pass to the agent constructor.

    Returns:
        An instance of the agent class with event capabilities.
    """

    # Create a new class that inherits from EventEnabledAgent and the given class
    class EventEnhancedAgent(EventEnabledAgent, agent_class):
        """Agent with event capabilities."""

        pass

    # Set proper class name
    EventEnhancedAgent.__name__ = f"EventEnabled{agent_class.__name__}"

    # Create an instance
    return EventEnhancedAgent(event_system=event_system, **kwargs)
