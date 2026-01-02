"""
Core service components for Atlas.

This module provides essential services that other components can build upon,
including:
- Thread-safe buffer system with flow control
- Event-based communication with subscription
- State management with versioning and transitions
- Command pattern with execution/undo capabilities
- Resource lifecycle management with state transitions
"""

# Import and re-export service components
from .buffer import BatchingBuffer, MemoryBuffer, RateLimitedBuffer, create_buffer
from .commands import Command, CommandExecutor, create_command_executor
from .events import EventSubscription, EventSystem, create_event_system

# Service registry for dynamic service discovery and management
from .registry import ServiceRegistry, get_service, list_services, register_service
from .resources import Resource, ResourceManager, create_resource_manager
from .state import StateContainer, StateTransition, create_state_container

__all__ = [
    # Buffer system
    "MemoryBuffer",
    "RateLimitedBuffer",
    "BatchingBuffer",
    "create_buffer",
    # Event system
    "EventSystem",
    "EventSubscription",
    "create_event_system",
    # State management
    "StateContainer",
    "StateTransition",
    "create_state_container",
    # Command pattern
    "Command",
    "CommandExecutor",
    "create_command_executor",
    # Resource management
    "Resource",
    "ResourceManager",
    "create_resource_manager",
    # Service registry
    "ServiceRegistry",
    "register_service",
    "get_service",
    "list_services",
]
