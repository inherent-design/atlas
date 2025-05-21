"""
Core types and type definitions for Atlas.

This module provides typed structures, protocols, and utilities for
maintaining type safety throughout the codebase. Using these definitions
helps ensure consistency, maintainability, and proper IDE support.
"""

from collections.abc import Callable, Iterator
from enum import Enum
from typing import (
    Any,
    Literal,
    NotRequired,
    Protocol,
    TypedDict,
    Union,
)

# ======================================================================
# Generic Type Utilities
# ======================================================================


class JsonDict(TypedDict, total=False):
    """Base type for JSON-serializable dictionaries."""

    pass


# ======================================================================
# Message Type Definitions
# ======================================================================


class MessageRole(str, Enum):
    """Roles in a conversation with a model."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


class TextContent(TypedDict):
    """Text content type for messages."""

    type: Literal["text"]
    text: str


class ImageUrlDetail(TypedDict, total=False):
    """Image URL details."""

    url: str
    detail: NotRequired[Literal["auto", "high", "low"]]


class ImageContent(TypedDict):
    """Image content type for messages."""

    type: Literal["image_url"]
    image_url: ImageUrlDetail


# Union type for all content types
MessageContentItem = Union[TextContent, ImageContent]


class MessageDict(TypedDict, total=False):
    """Dictionary representation of a message."""

    role: str
    content: str | list[MessageContentItem] | MessageContentItem
    name: NotRequired[str]


# ======================================================================
# API Request/Response Types
# ======================================================================


class TokenUsageDict(TypedDict):
    """Token usage statistics."""

    input_tokens: int
    output_tokens: int
    total_tokens: int


class CostEstimateDict(TypedDict):
    """Cost estimate statistics."""

    input_cost: float
    output_cost: float
    total_cost: float


class ResponseFormatDict(TypedDict, total=False):
    """Format specification for model responses."""

    type: str
    schema: NotRequired[dict[str, Any]]


class ModelRequestDict(TypedDict, total=False):
    """Dictionary representation of a model request."""

    model: str
    messages: list[MessageDict]
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    stop: NotRequired[list[str]]
    top_p: NotRequired[float]
    frequency_penalty: NotRequired[float]
    presence_penalty: NotRequired[float]
    response_format: NotRequired[ResponseFormatDict]
    stream: NotRequired[bool]
    system: NotRequired[str]  # Anthropic-specific
    metadata: NotRequired[dict[str, Any]]  # Additional metadata


class ModelResponseDict(TypedDict, total=False):
    """Dictionary representation of a model response."""

    content: str
    model: str
    provider: str
    usage: TokenUsageDict
    cost: CostEstimateDict
    finish_reason: NotRequired[str]


# ======================================================================
# Provider Protocol Interfaces
# ======================================================================


class ModelProvider(Protocol):
    """Protocol defining the interface for model providers."""

    @property
    def name(self) -> str:
        """Get the provider name."""
        ...

    @property
    def models(self) -> list[str]:
        """Get available models for this provider."""
        ...

    def generate(self, request: ModelRequestDict) -> "ModelResponseDict":
        """Generate a response for the given request.

        Args:
            request: The model request configuration.

        Returns:
            The model's response.
        """
        ...

    def stream(self, request: ModelRequestDict) -> "StreamHandlerProtocol":
        """Stream a response for the given request.

        Args:
            request: The model request configuration.

        Returns:
            A stream handler for the response.
        """
        ...


# ======================================================================
# Retrieval Types
# ======================================================================


class DocumentMetadata(TypedDict, total=False):
    """Metadata for a document chunk."""

    source: str
    chunk_index: NotRequired[int]
    chunk_size: NotRequired[int]
    file_type: NotRequired[str]
    created_at: NotRequired[str]
    updated_at: NotRequired[str]
    tags: NotRequired[list[str]]
    custom: NotRequired[dict[str, Any]]


class DocumentChunkDict(TypedDict):
    """Dictionary representation of a document chunk."""

    id: str
    text: str
    metadata: DocumentMetadata


class RetrievalFilterDict(TypedDict, total=False):
    """Filter criteria for document retrieval."""

    where: NotRequired[dict[str, Any]]
    where_document: NotRequired[dict[str, Any]]
    limit: NotRequired[int]
    offset: NotRequired[int]
    include: NotRequired[list[str]]
    exclude: NotRequired[list[str]]


class RetrievalSettingsDict(TypedDict, total=False):
    """Settings for document retrieval."""

    filter: NotRequired[RetrievalFilterDict]
    top_k: NotRequired[int]
    namespace: NotRequired[str]
    score_threshold: NotRequired[float]
    include_embeddings: NotRequired[bool]
    include_metadata: NotRequired[bool]


class RetrievalResultDict(TypedDict):
    """Dictionary representation of a retrieval result."""

    id: str
    text: str
    metadata: DocumentMetadata
    score: float
    embedding: NotRequired[list[float]]


# ======================================================================
# Streaming Types
# ======================================================================


class StreamHandlerProtocol(Protocol):
    """Protocol for stream handlers that process streaming responses."""

    content: str
    """The current accumulated content."""

    provider: "ModelProvider"
    """The provider instance that created this handler."""

    model: str
    """The model used for generating the stream."""

    response: Any
    """The current response object."""

    def get_iterator(self) -> Iterator[str | tuple[str, Any]]:
        """Get an iterator for the stream.

        Returns:
            An iterator that yields chunks of the content.
        """
        ...

    def process_stream(self, callback: Callable[[str, Any], None] | None = None) -> Any:
        """Process the entire stream with a callback function.

        Args:
            callback: Function to call for each chunk of content.

        Returns:
            The final response after processing the entire stream.
        """
        ...


class StreamControlProtocol(Protocol):
    """Protocol for controlling streaming responses."""

    @property
    def state(self) -> str:
        """Get the current state of the stream."""
        ...

    @property
    def can_pause(self) -> bool:
        """Whether this stream supports pausing."""
        ...

    @property
    def can_resume(self) -> bool:
        """Whether this stream can be resumed from a paused state."""
        ...

    @property
    def can_cancel(self) -> bool:
        """Whether this stream supports cancellation."""
        ...

    def pause(self) -> bool:
        """Pause the stream if supported.

        Returns:
            bool: True if the stream was paused, False otherwise.
        """
        ...

    def resume(self) -> bool:
        """Resume the stream if paused.

        Returns:
            bool: True if the stream was resumed, False otherwise.
        """
        ...

    def cancel(self) -> bool:
        """Cancel the stream if supported.

        Returns:
            bool: True if the stream was cancelled, False otherwise.
        """
        ...

    def register_state_change_callback(self, callback: Callable[[str], None]) -> None:
        """Register a callback to be called when the stream state changes.

        Args:
            callback: Function to call with the new state.
        """
        ...

    def register_content_callback(self, callback: Callable[[str, Any], None]) -> None:
        """Register a callback to be called when new content is available.

        Args:
            callback: Function to call with new content and updated response.
        """
        ...

    def get_metrics(self) -> dict[str, Any]:
        """Get stream performance metrics.

        Returns:
            Dict containing stream metrics such as tokens processed, throughput, etc.
        """
        ...


# ======================================================================
# Tool Types
# ======================================================================


class ToolParameterSchema(TypedDict, total=False):
    """JSON Schema for tool parameters."""

    type: str
    properties: dict[str, Any]
    required: list[str]
    additionalProperties: NotRequired[bool]


class ToolSchemaDict(TypedDict):
    """Dictionary representation of a tool schema."""

    name: str
    description: str
    parameters: ToolParameterSchema
    returns: NotRequired[dict[str, Any]]


class ToolResultDict(TypedDict, total=False):
    """Dictionary representation of a tool execution result."""

    success: bool
    result: Any
    error: NotRequired[str]
    metadata: NotRequired[dict[str, Any]]


class ToolDefinitionDict(TypedDict):
    """Dictionary representation of a tool definition."""

    name: str
    description: str
    schema: ToolSchemaDict


class ToolExecutionDict(TypedDict):
    """Dictionary representation of a tool execution request."""

    name: str
    args: dict[str, Any]
    agent_id: NotRequired[str]


class ToolkitConfigDict(TypedDict, total=False):
    """Configuration for an agent toolkit."""

    tools: list[str]
    permissions: dict[str, list[str]]
    defaults: NotRequired[dict[str, Any]]
    registry: NotRequired[str]
