"""
Structured message format for agent communication.

This module defines a standardized message format for communication between agents
in the Atlas framework, with support for metadata, tool calls, and serialization.
"""

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Optional, TypeVar

from atlas.core.telemetry import TracedClass, traced


class MessageType:
    """Message type constants for classifying messages."""

    QUERY = "query"  # Initial user query
    TASK = "task"  # Task assignment
    RESPONSE = "response"  # Response to a query or task
    RESULT = "result"  # Task result
    ERROR = "error"  # Error notification
    STATUS = "status"  # Status update
    TOOL_REQUEST = "tool_request"  # Request to use a tool
    TOOL_RESPONSE = "tool_response"  # Response from a tool


@dataclass
class ToolCall:
    """A call to an external tool."""

    name: str
    """The name of the tool to call."""

    arguments: dict[str, Any]
    """The arguments to pass to the tool."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    """Unique identifier for this tool call."""


@dataclass
class ToolResult:
    """Result from a tool execution."""

    name: str
    """The name of the tool that was called."""

    result: Any
    """The result from the tool execution."""

    call_id: str
    """The ID of the original tool call."""

    status: str = "success"
    """Status of the tool execution (success, error)."""

    error: str | None = None
    """Error message if status is 'error'."""


T = TypeVar("T", bound="StructuredMessage")


class StructuredMessage(TracedClass):
    """Structured message format for agent communication."""

    def __init__(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
        task_id: str | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
        tool_results: list[dict[str, Any]] | None = None,
    ):
        """Initialize a structured message.

        Args:
            content: The main text content of the message.
            metadata: Optional metadata about the message.
            task_id: Optional task identifier. If not provided, a UUID will be generated.
            tool_calls: Optional list of tool calls included in this message.
            tool_results: Optional list of tool results included in this message.
        """
        self.content = content
        self.metadata = metadata or {}
        self.task_id = task_id or str(uuid.uuid4())
        self.timestamp = time.time()

        # Tool-related fields
        self.tool_calls = []
        if tool_calls:
            for call in tool_calls:
                if isinstance(call, dict):
                    # Ensure the call has an ID
                    if "id" not in call:
                        call["id"] = str(uuid.uuid4())
                    self.tool_calls.append(call)
                else:
                    # For backward compatibility with direct ToolCall objects
                    self.tool_calls.append(asdict(call))

        self.tool_results = []
        if tool_results:
            for result in tool_results:
                if isinstance(result, dict):
                    self.tool_results.append(result)
                else:
                    # For backward compatibility with direct ToolResult objects
                    self.tool_results.append(asdict(result))

        # Agent identification
        self.source_agent: str | None = None
        self.target_agent: str | None = None

    @property
    def message_type(self) -> str:
        """Get the type of this message based on metadata.

        Returns:
            The message type as a string.
        """
        return self.metadata.get("type", "unknown")

    @property
    def has_tool_calls(self) -> bool:
        """Check if this message contains tool calls.

        Returns:
            True if the message contains tool calls, False otherwise.
        """
        return len(self.tool_calls) > 0

    @property
    def has_tool_results(self) -> bool:
        """Check if this message contains tool results.

        Returns:
            True if the message contains tool results, False otherwise.
        """
        return len(self.tool_results) > 0

    @traced(name="add_tool_call")
    def add_tool_call(self, name: str, arguments: dict[str, Any]) -> str:
        """Add a tool call to this message.

        Args:
            name: The name of the tool to call.
            arguments: The arguments to pass to the tool.

        Returns:
            The ID of the created tool call.
        """
        call_id = str(uuid.uuid4())
        self.tool_calls.append({"id": call_id, "name": name, "arguments": arguments})
        return call_id

    @traced(name="add_tool_result")
    def add_tool_result(
        self,
        name: str,
        result: Any,
        call_id: str,
        status: str = "success",
        error: str | None = None,
    ) -> None:
        """Add a tool result to this message.

        Args:
            name: The name of the tool that was called.
            result: The result from the tool execution.
            call_id: The ID of the original tool call.
            status: Status of the tool execution (success, error).
            error: Error message if status is 'error'.
        """
        self.tool_results.append(
            {"name": name, "result": result, "call_id": call_id, "status": status, "error": error}
        )

    @traced(name="to_dict")
    def to_dict(self) -> dict[str, Any]:
        """Convert the message to a dictionary for serialization.

        Returns:
            A dictionary representation of the message.
        """
        return {
            "content": self.content,
            "metadata": self.metadata,
            "task_id": self.task_id,
            "timestamp": self.timestamp,
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
        }

    @traced(name="to_json")
    def to_json(self) -> str:
        """Convert the message to a JSON string.

        Returns:
            A JSON string representation of the message.
        """
        return json.dumps(self.to_dict())

    @classmethod
    @traced(name="from_dict")
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        """Create a message from a dictionary.

        Args:
            data: Dictionary containing message data.

        Returns:
            A new StructuredMessage instance.
        """
        # Create a basic instance
        msg = cls(
            content=data["content"],
            metadata=data["metadata"],
            task_id=data["task_id"],
            tool_calls=data.get("tool_calls", []),
            tool_results=data.get("tool_results", []),
        )

        # Set additional fields
        msg.timestamp = data["timestamp"]
        msg.source_agent = data.get("source_agent")
        msg.target_agent = data.get("target_agent")

        return msg

    @classmethod
    @traced(name="from_json")
    def from_json(cls: type[T], json_str: str) -> T:
        """Create a message from a JSON string.

        Args:
            json_str: JSON string containing message data.

        Returns:
            A new StructuredMessage instance.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    @traced(name="create_response")
    def create_response(cls: type[T], content: str, original_message: "StructuredMessage") -> T:
        """Create a response to an existing message.

        Args:
            content: The content of the response.
            original_message: The message being responded to.

        Returns:
            A new StructuredMessage instance configured as a response.
        """
        response = cls(
            content=content,
            metadata={"type": MessageType.RESPONSE, "in_reply_to": original_message.task_id},
        )

        # Swap source and target agents
        response.source_agent = original_message.target_agent
        response.target_agent = original_message.source_agent

        return response

    @classmethod
    @traced(name="create_error")
    def create_error(
        cls: type[T], error_message: str, original_message: Optional["StructuredMessage"] = None
    ) -> T:
        """Create an error message.

        Args:
            error_message: The error message content.
            original_message: Optional message that triggered the error.

        Returns:
            A new StructuredMessage instance configured as an error.
        """
        metadata = {"type": MessageType.ERROR}

        if original_message:
            metadata["in_reply_to"] = original_message.task_id

        error = cls(content=error_message, metadata=metadata)

        if original_message:
            error.source_agent = original_message.target_agent
            error.target_agent = original_message.source_agent

        return error

    @classmethod
    @traced(name="create_task")
    def create_task(
        cls: type[T],
        content: str,
        source_agent: str,
        target_agent: str,
        task_data: dict[str, Any] | None = None,
    ) -> T:
        """Create a task assignment message.

        Args:
            content: The task description.
            source_agent: The agent assigning the task.
            target_agent: The agent receiving the task.
            task_data: Optional additional task data.

        Returns:
            A new StructuredMessage instance configured as a task.
        """
        metadata = {"type": MessageType.TASK}

        if task_data:
            metadata.update(task_data)

        task = cls(content=content, metadata=metadata)

        task.source_agent = source_agent
        task.target_agent = target_agent

        return task
