"""
State management for LangGraph in Atlas.

This module defines the state models used in LangGraph workflows.
"""

from typing import Any, TypedDict

from pydantic import BaseModel, Field


class Message(TypedDict):
    """Message in the conversation."""

    role: str
    content: str


class Document(TypedDict):
    """Document from the knowledge base."""

    content: str
    metadata: dict[str, Any]
    relevance_score: float


class Context(TypedDict):
    """Context for the agent."""

    documents: list[Document]
    query: str


class WorkerConfig(BaseModel):
    """Configuration for a worker agent."""

    worker_id: str = Field(description="Unique identifier for the worker")
    specialization: str = Field(description="What this worker specializes in")
    system_prompt: str = Field(description="System prompt for this worker")


class AgentState(BaseModel):
    """State for a LangGraph agent."""

    # Basic state
    messages: list[Message] = Field(default_factory=list, description="Conversation history")
    context: Context | None = Field(default=None, description="Retrieved context information")

    # Worker agent state (for parallel processing)
    worker_id: str | None = Field(default=None, description="ID of the current worker (if any)")
    worker_results: dict[str, Any] = Field(
        default_factory=dict, description="Results from worker agents"
    )
    worker_configs: list[WorkerConfig] = Field(
        default_factory=list, description="Configurations for worker agents"
    )

    # Flags
    process_complete: bool = Field(default=False, description="Whether processing is complete")
    error: str | None = Field(default=None, description="Error message if any")


class ControllerState(BaseModel):
    """State for a controller agent managing multiple workers."""

    # Main state
    messages: list[Message] = Field(default_factory=list, description="Main conversation history")
    context: Context | None = Field(default=None, description="Retrieved context information")

    # Worker management
    workers: dict[str, AgentState] = Field(
        default_factory=dict, description="States for all workers"
    )
    active_workers: list[str] = Field(
        default_factory=list, description="Currently active worker IDs"
    )
    completed_workers: list[str] = Field(
        default_factory=list, description="IDs of workers that have completed"
    )

    # Task tracking
    tasks: list[dict[str, Any]] = Field(default_factory=list, description="Tasks to be processed")
    results: list[dict[str, Any]] = Field(
        default_factory=list, description="Results from completed tasks"
    )

    # Flags
    all_tasks_assigned: bool = Field(
        default=False, description="Whether all tasks have been assigned"
    )
    all_tasks_completed: bool = Field(
        default=False, description="Whether all tasks have been completed"
    )
