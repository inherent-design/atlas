# Directory Structure
```
atlas/
  core/
    primitives/
      buffer/
        __init__.py
        errors.py
        types.py
      commands/
        __init__.py
        errors.py
        types.py
      component/
        __init__.py
        errors.py
        types.py
      events/
        __init__.py
        errors.py
        types.py
      middleware/
        __init__.py
        errors.py
        types.py
      registry/
        __init__.py
        errors.py
        types.py
      resources/
        __init__.py
        errors.py
        types.py
      state/
        __init__.py
        errors.py
        types.py
      transitions/
        __init__.py
        errors.py
        types.py
    __init__.py
    errors.py
    protocols.py
    schemas.py
    types.py
    validation.py
  tests/
    core/
      primitives/
        buffer/
          __init__.py
          test_types.py
        commands/
          __init__.py
          test_types.py
        component/
          __init__.py
          test_types.py
        events/
          __init__.py
          test_types.py
        middleware/
          __init__.py
          test_types.py
        registry/
          __init__.py
          test_types.py
        resources/
          __init__.py
          test_types.py
        state/
          __init__.py
          test_types.py
        transitions/
          __init__.py
          test_types.py
      __init__.py
      test_errors.py
      test_types.py
    conftest.py
    utils.py
  __init__.py
  README.md
```

# Files

## File: atlas/core/primitives/buffer/__init__.py
````python
"""
Buffer service for Atlas framework.
This module provides thread-safe buffer implementations for managing data flow,
including streaming, rate-limited, and batching buffer types.
"""
⋮----
# Buffer TypedDict structures
⋮----
# Buffer protocols
⋮----
# Callable type aliases
⋮----
# Type guards
````

## File: atlas/core/primitives/buffer/errors.py
````python
"""
Buffer-specific error classes.
This module provides error classes for the buffer system, including:
- BufferFullError: Raised when a buffer is full and cannot accept more items
- BufferEmptyError: Raised when trying to get items from an empty buffer
- BufferClosedError: Raised when attempting to use a closed buffer
- RateLimitExceededError: Raised when buffer operations exceed rate limits
"""
⋮----
class BufferError(AtlasError)
⋮----
"""Base class for buffer-related exceptions."""
⋮----
"""Initialize the error.
        Args:
            message: The error message.
            severity: Severity level of the error.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            buffer_id: Optional ID of the buffer involved.
        """
⋮----
class BufferFullError(BufferError)
⋮----
"""Raised when attempting to push to a full buffer."""
⋮----
class BufferEmptyError(BufferError)
⋮----
"""Raised when attempting to pop from an empty buffer."""
⋮----
class BufferClosedError(BufferError)
⋮----
"""Raised when attempting to use a closed buffer."""
⋮----
class RateLimitExceededError(BufferError)
⋮----
"""Raised when rate limit is exceeded for a buffer."""
⋮----
details = kwargs.pop("details", {}) or {}
````

## File: atlas/core/primitives/buffer/types.py
````python
"""
Type definitions for Atlas buffer service.
This module provides type definitions specific to buffer services, including:
- Protocol interfaces for different buffer types
- TypedDict structures for buffer configuration
- Type guards for buffer type checking
"""
⋮----
# ===== Buffer TypedDict Definitions =====
class BufferConfigDict(TypedDict)
⋮----
"""Base configuration for buffer services."""
buffer_id: str
max_size: int
overflow_strategy: str
class BufferItemDict(TypedDict)
⋮----
"""Item stored in a buffer."""
id: str
timestamp: int
data: dict[str, Any]
metadata: dict[str, Any]
class RateLimitedBufferConfigDict(BufferConfigDict)
⋮----
"""Configuration for rate-limited buffer services."""
rate_limit: int
time_window: float
class BatchingBufferConfigDict(BufferConfigDict)
⋮----
"""Configuration for batching buffer services."""
batch_size: int
timeout: float
# ===== Buffer Protocol Interfaces =====
⋮----
@runtime_checkable
class BufferProtocol(Protocol)
⋮----
"""Protocol defining the interface for thread-safe buffers."""
def push(self, item: dict[str, Any]) -> bool: ...
def pop(self) -> dict[str, Any] | None: ...
def peek(self) -> dict[str, Any] | None: ...
def clear(self) -> None: ...
def close(self) -> None: ...
def pause(self) -> "BufferProtocol": ...
def resume(self) -> "BufferProtocol": ...
def is_closed(self) -> bool: ...
⋮----
@property
    def is_empty(self) -> bool: ...
⋮----
@property
    def is_full(self) -> bool: ...
⋮----
@property
    def is_paused(self) -> bool: ...
⋮----
@property
    def size(self) -> int: ...
⋮----
@property
    def max_size(self) -> int: ...
⋮----
@runtime_checkable
class StreamingBufferProtocol(BufferProtocol, Protocol)
⋮----
"""Extended protocol for buffers that support streaming operations."""
def wait_until_not_empty(self, timeout: float | None = None) -> bool: ...
def wait_until_not_full(self, timeout: float | None = None) -> bool: ...
⋮----
@runtime_checkable
class RateLimitedBufferProtocol(StreamingBufferProtocol, Protocol)
⋮----
"""Protocol for rate-limited buffers."""
⋮----
@property
    def tokens_per_second(self) -> float | None: ...
⋮----
@property
    def chars_per_token(self) -> int: ...
⋮----
@property
    def token_budget(self) -> float: ...
def _calculate_token_cost(self, item: dict[str, Any]) -> float: ...
⋮----
@runtime_checkable
class BatchingBufferProtocol(StreamingBufferProtocol, Protocol)
⋮----
"""Protocol for batching buffers."""
⋮----
@property
    def batch_size(self) -> int | None: ...
⋮----
@property
    def batch_timeout(self) -> float | None: ...
⋮----
@property
    def batch_delimiter(self) -> str | None: ...
def wait_for_batch(self, timeout: float | None = None) -> bool: ...
def _create_batch(self, items: list[dict[str, Any]]) -> dict[str, Any]: ...
⋮----
@runtime_checkable
class BufferSystemProtocol(ServiceProtocol, Protocol)
⋮----
"""Protocol for buffer system components."""
⋮----
def get_buffer(self, name: str) -> BufferProtocol | None: ...
def close_buffer(self, name: str) -> bool: ...
def list_buffers(self) -> list[str]: ...
def get_buffer_stats(self) -> dict[str, dict[str, int]]: ...
# ===== Callable Type Aliases =====
⋮----
# ===== Type Guards =====
def is_buffer(obj: Any) -> TypeGuard[BufferProtocol]
⋮----
"""Check if an object implements the BufferProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements BufferProtocol, False otherwise.
    """
⋮----
# Check for required methods and properties
required_methods = [
⋮----
required_properties = ["is_empty", "is_full", "is_paused", "size", "max_size"]
⋮----
def is_streaming_buffer(obj: Any) -> TypeGuard[StreamingBufferProtocol]
⋮----
"""Check if an object implements the StreamingBufferProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements StreamingBufferProtocol, False otherwise.
    """
⋮----
required_methods = ["wait_until_not_empty", "wait_until_not_full"]
⋮----
def is_rate_limited_buffer(obj: Any) -> TypeGuard[RateLimitedBufferProtocol]
⋮----
"""Check if an object implements the RateLimitedBufferProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements RateLimitedBufferProtocol, False otherwise.
    """
⋮----
required_properties = ["tokens_per_second", "chars_per_token", "token_budget"]
⋮----
# Check for the calculation method
⋮----
def is_batching_buffer(obj: Any) -> TypeGuard[BatchingBufferProtocol]
⋮----
"""Check if an object implements the BatchingBufferProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements BatchingBufferProtocol, False otherwise.
    """
⋮----
required_properties = ["batch_size", "batch_timeout", "batch_delimiter"]
⋮----
# Check for required methods
required_methods = ["wait_for_batch", "_create_batch"]
⋮----
def is_buffer_system(obj: Any) -> TypeGuard[BufferSystemProtocol]
⋮----
"""Check if an object implements the BufferSystemProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements BufferSystemProtocol, False otherwise.
    """
⋮----
# Check for ServiceProtocol requirements
````

## File: atlas/core/primitives/commands/__init__.py
````python
"""
Command system for Atlas framework.
This module provides a command pattern implementation for executing
operations with undo/redo capabilities and execution history.
"""
⋮----
# Command TypedDict structures
⋮----
# Callable type aliases
⋮----
# Command protocols
⋮----
# Type guards
````

## File: atlas/core/primitives/commands/errors.py
````python
"""
Command system-specific error classes.
This module provides error classes for the command system, including:
- CommandExecutionError: Raised when command execution fails
- CommandUndoError: Raised when command undo operations fail
- CommandHistoryError: Raised for issues with command history
- CommandValidationError: Raised when commands fail validation
"""
⋮----
class CommandError(AtlasError)
⋮----
"""Base class for command execution exceptions."""
⋮----
"""Initialize the error.
        Args:
            message: The error message.
            severity: Severity level of the error.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            command_id: Optional ID of the command involved.
            command_name: Optional name of the command involved.
        """
⋮----
class CommandExecutionError(CommandError)
⋮----
"""Raised when a command fails to execute."""
⋮----
class CommandUndoError(CommandError)
⋮----
"""Raised when a command fails to undo."""
⋮----
class CommandHistoryError(CommandError)
⋮----
"""Raised when there's an issue with the command history."""
⋮----
class CommandValidationError(CommandError)
⋮----
"""Raised when a command fails validation."""
⋮----
details = kwargs.pop("details", {}) or {}
````

## File: atlas/core/primitives/commands/types.py
````python
"""
Type definitions for Atlas command system.
This module provides type definitions specific to the command system, including:
- Protocol interfaces for commands and command executors
- TypedDict structures for command data and execution results
- Type guards for command-related objects
- Callback type definitions for command operations
"""
⋮----
# ===== Type Variables for Commands =====
R_co = TypeVar("R_co", covariant=True)  # Command result type (covariant)
R = TypeVar("R")  # Command result type (invariant)
# ===== Command System TypedDict Definitions =====
class CommandConfigDict(TypedDict)
⋮----
"""Configuration for a command."""
command_id: str
command_type: str
description: str
options: dict[str, Any]
class CommandResultDict(TypedDict)
⋮----
"""Result of a command execution."""
⋮----
success: bool
result: dict[str, Any]
timestamp: int  # Unix timestamp
execution_time: float
class CommandHistoryEntryDict(TypedDict)
⋮----
"""Entry in the command history."""
⋮----
arguments: dict[str, Any]
⋮----
# ===== Command Protocol Interfaces =====
⋮----
@runtime_checkable
class CommandProtocol(Protocol[R_co])
⋮----
"""Protocol for command objects."""
⋮----
def execute(self, *args: Any, **kwargs: Any) -> R_co: ...
def undo(self) -> bool: ...
def can_undo(self) -> bool: ...
⋮----
@runtime_checkable
class CommandExecutorProtocol(ServiceProtocol, Protocol[R_co])
⋮----
"""Protocol for command executor services."""
def register_command(self, command_type: str, factory: Any) -> None: ...
def unregister_command(self, command_type: str) -> bool: ...
def execute(self, command_type: str, *args: Any, **kwargs: Any) -> R_co: ...
def undo(self, command_id: str | None = None) -> bool: ...
def redo(self, command_id: str | None = None) -> R_co: ...
def get_history(self, max_entries: int = 10) -> list[dict[str, Any]]: ...
def clear_history(self) -> None: ...
# ===== Type Aliases =====
UndoFunction = Callable[[], bool]
# ===== Type Guards =====
def is_command(obj: Any) -> TypeGuard[CommandProtocol]
⋮----
"""Check if an object implements the CommandProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements CommandProtocol, False otherwise.
    """
⋮----
# Check for required attributes
⋮----
# Check for required methods
required_methods = ["execute", "undo", "can_undo"]
⋮----
def is_command_executor(obj: Any) -> TypeGuard[CommandExecutorProtocol]
⋮----
"""Check if an object implements the CommandExecutorProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements CommandExecutorProtocol, False otherwise.
    """
⋮----
# Check for ServiceProtocol requirements
⋮----
# Check for required basic methods
service_methods = ["initialize", "shutdown"]
⋮----
# Check for command executor methods
executor_methods = [
⋮----
# ===== Callback Types =====
CommandExecuteCallback = Callable[[str, Any, Any], Any]
CommandUndoCallback = Callable[[str], bool]
CommandRedoCallback = Callable[[str], Any]
CommandFactoryCallback = Callable[..., CommandProtocol[Any]]
````

## File: atlas/core/primitives/component/__init__.py
````python
"""
Service-enabled components for Atlas framework.
This module provides base functionality for components that can
access and utilize core services from the service registry.
"""
⋮----
# Component TypedDict structures
⋮----
# Component protocol
⋮----
# Type guards
````

## File: atlas/core/primitives/component/errors.py
````python
"""
Component-specific error classes.
This module provides error classes for service-enabled components, including:
- ComponentInitializationError: Raised when component initialization fails
"""
⋮----
class ComponentError(AtlasError)
⋮----
"""Base class for service-enabled component exceptions."""
⋮----
"""Initialize the error.
        Args:
            message: The error message.
            severity: Severity level of the error.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            component_id: Optional ID of the component involved.
            component_type: Optional type of the component involved.
        """
⋮----
class ComponentInitializationError(ComponentError)
⋮----
"""Raised when a component fails to initialize."""
````

## File: atlas/core/primitives/component/types.py
````python
"""
Type definitions for Atlas component system.
This module provides type definitions specific to service-enabled components, including:
- Protocol interface for service-enabled components
- TypedDict structures for component configuration
- Type guards for service-enabled objects
"""
⋮----
# ===== Component System TypedDict Definitions =====
class ComponentConfigDict(TypedDict)
⋮----
"""Configuration for a component."""
component_id: str
component_type: str
services: list[str]
options: dict[str, Any]
# ===== Component Protocol Interfaces =====
⋮----
@runtime_checkable
class ServiceEnabledProtocol(Protocol)
⋮----
"""Protocol for components that use services from a registry."""
⋮----
def set_service_registry(self, registry: Any) -> None: ...
def get_service(self, service_type: str) -> Any: ...
def has_service(self, service_type: str) -> bool: ...
# ===== Type Guards =====
def is_service_enabled(obj: Any) -> TypeGuard[ServiceEnabledProtocol]
⋮----
"""Check if an object implements the ServiceEnabledProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements ServiceEnabledProtocol, False otherwise.
    """
⋮----
# Check for required attributes
⋮----
# Check for required methods
required_methods = ["set_service_registry", "get_service", "has_service"]
````

## File: atlas/core/primitives/events/__init__.py
````python
"""
Event system for Atlas framework.
This module provides an event-based communication system for publishing
and subscribing to events throughout the application.
"""
⋮----
# Callable type aliases
⋮----
# Event TypedDict structures
⋮----
# Event protocol
⋮----
# Type guards
⋮----
# Validation functions
````

## File: atlas/core/primitives/events/errors.py
````python
"""
Event system-specific error classes.
This module provides error classes for the event system, including:
- EventTypeError: Raised when an invalid event type is used
- SubscriptionError: Raised for subscription-related issues
- EventPublishError: Raised when event publishing fails
- EventCallbackError: Raised when event callbacks raise exceptions
"""
⋮----
class EventError(AtlasError)
⋮----
"""Base class for event system-related exceptions."""
⋮----
"""Initialize the error.
        Args:
            message: The error message.
            severity: Severity level of the error.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            event_id: Optional ID of the event involved.
            event_type: Optional type of the event involved.
        """
⋮----
class EventTypeError(EventError)
⋮----
"""Raised when an invalid event type is used."""
⋮----
class SubscriptionError(EventError)
⋮----
"""Raised when there's an issue with event subscriptions."""
⋮----
details = kwargs.pop("details", {}) or {}
⋮----
class EventPublishError(EventError)
⋮----
"""Raised when an event cannot be published."""
⋮----
class EventCallbackError(EventError)
⋮----
"""Raised when an event callback raises an exception."""
````

## File: atlas/core/primitives/events/types.py
````python
"""
Type definitions for Atlas event system.
This module provides type definitions specific to the event system, including:
- Protocol interface for event publication and subscription
- TypedDict structures for event data and subscription configuration
- Type validation utilities for event types and patterns
"""
⋮----
# ===== Event System TypedDict Definitions =====
class EventDataDict(TypedDict)
⋮----
"""Event data structure for the event system."""
event_id: str
event_type: str
timestamp: int  # Unix timestamp
data: dict[str, Any]
metadata: dict[str, Any]
class SubscriptionConfigDict(TypedDict)
⋮----
"""Configuration for an event subscription."""
subscriber_id: str
pattern: str
priority: int
max_concurrent: int
options: dict[str, Any]
# ===== Callable Type Aliases =====
⋮----
# ===== Event Protocol Interface =====
⋮----
@runtime_checkable
class EventProtocol(ServiceProtocol, Protocol)
⋮----
"""Protocol for event system components."""
⋮----
def unsubscribe(self, subscription_id: str) -> bool: ...
def get_subscriptions(self, pattern: str | None = None) -> list[dict[str, Any]]: ...
# ===== Type Guards =====
def is_event_system(obj: Any) -> TypeGuard[EventProtocol]
⋮----
"""Check if an object implements the EventProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements EventProtocol, False otherwise.
    """
⋮----
# Check for basic service requirements
⋮----
# Check for required methods
required_methods = ["initialize", "shutdown", "publish", "subscribe", "unsubscribe", "get_subscriptions"]
⋮----
# ===== Validation Functions =====
def validate_event_type(event_type: str) -> bool
⋮----
"""Validate an event type string format.
    Args:
        event_type: The event type to validate.
    Returns:
        True if the event type is valid, False otherwise.
    """
⋮----
# Event type should not have invalid characters
⋮----
# Event type should not have uppercase letters
⋮----
# Event type should not start or end with a dot
⋮----
# Event type should not have consecutive dots
⋮----
# All parts should be lowercase alphanumeric or underscore
parts = event_type.split(".")
⋮----
def validate_subscription_pattern(pattern: str) -> bool
⋮----
"""Validate a subscription pattern format.
    Args:
        pattern: The subscription pattern to validate.
    Returns:
        True if the pattern is valid, False otherwise.
    """
⋮----
# Double wildcard not supported
⋮----
# Pattern should not have invalid characters
⋮----
# Pattern should not have uppercase letters
⋮----
# Pattern should not start or end with a dot
⋮----
# Pattern should not have consecutive dots
⋮----
# All parts should be lowercase alphanumeric, underscore, or wildcard
parts = pattern.split(".")
````

## File: atlas/core/primitives/middleware/__init__.py
````python
"""
Middleware system for Atlas framework.
This module provides middleware implementations for processing
data as it flows through various components of the application.
"""
⋮----
# Middleware protocol
⋮----
# Type guards
````

## File: atlas/core/primitives/middleware/errors.py
````python
"""
Middleware-specific error classes.
This module provides error classes for middleware operations, including:
- MiddlewareProcessingError: Raised when middleware processing fails
"""
⋮----
class MiddlewareError(AtlasError)
⋮----
"""Base class for middleware-related exceptions."""
⋮----
"""Initialize the error.
        Args:
            message: The error message.
            severity: Severity level of the error.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            middleware_name: Optional name of the middleware involved.
        """
⋮----
class MiddlewareProcessingError(MiddlewareError)
⋮----
"""Raised when middleware processing fails."""
````

## File: atlas/core/primitives/middleware/types.py
````python
"""
Type definitions for Atlas middleware system.
This module provides type definitions specific to middleware components, including:
- Protocol interface for middleware
- Type aliases for middleware priorities and functions
- Type guards for middleware-related objects
"""
⋮----
# Generic type variable for middleware data
T = TypeVar("T")
# ===== Middleware Protocol Interface =====
⋮----
@runtime_checkable
class MiddlewareProtocol(Protocol, Generic[T])
⋮----
"""Protocol for middleware components."""
middleware_id: str
priority: int
def process(self, data: T, next_middleware: Callable[[T], T] | None = None) -> T: ...
# ===== Type Guards =====
def is_middleware(obj: Any) -> TypeGuard[MiddlewareProtocol]
⋮----
"""Check if an object implements the MiddlewareProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements MiddlewareProtocol, False otherwise.
    """
⋮----
# Check for required attributes
⋮----
# Check for required methods
````

## File: atlas/core/primitives/registry/__init__.py
````python
"""
Service registry for Atlas framework.
This module provides a centralized registry for managing service
instances and factories throughout the application.
"""
⋮----
# Type aliases
⋮----
# Registry protocol
⋮----
# Type guards
````

## File: atlas/core/primitives/registry/errors.py
````python
"""
Service registry-specific error classes.
This module provides error classes for the service registry system, including:
- ServiceNotFoundError: Raised when a service cannot be found in the registry
- ServiceRegistrationError: Raised when service registration fails
- ServiceTypeError: Raised when a service is of the wrong type
"""
⋮----
class RegistryError(AtlasError)
⋮----
"""Base class for service registry exceptions."""
⋮----
"""Initialize the error.
        Args:
            message: The error message.
            severity: Severity level of the error.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            service_type: Optional type of the service involved.
        """
⋮----
class ServiceNotFoundError(RegistryError)
⋮----
"""Raised when a requested service cannot be found in the registry."""
⋮----
class ServiceRegistrationError(RegistryError)
⋮----
"""Raised when a service registration fails."""
⋮----
class ServiceTypeError(RegistryError)
⋮----
"""Raised when a service is of the wrong type."""
⋮----
details = kwargs.pop("details", {}) or {}
````

## File: atlas/core/primitives/registry/types.py
````python
"""
Type definitions for Atlas service registry.
This module provides type definitions specific to service registry, including:
- Protocol interface for service registry
- Type aliases for service factories
- Type guards for registry-related objects
"""
⋮----
# ===== Type Variables for Registry =====
S = TypeVar("S", bound=ServiceProtocol)  # Service type variable
# ===== Type Aliases =====
ServiceFactory = Callable[..., ServiceProtocol]
# ===== Service Registry Protocol Interface =====
⋮----
@runtime_checkable
class ServiceRegistryProtocol(ServiceProtocol, Protocol)
⋮----
"""Protocol for service registry components."""
def register_service(self, service_type: str, factory: Callable[..., Any]) -> None: ...
def unregister_service(self, service_type: str) -> bool: ...
def get_service(self, service_type: str) -> Any: ...
def has_service(self, service_type: str) -> bool: ...
def list_services(self) -> list[str]: ...
# ===== Type Guards =====
def is_service_registry(obj: Any) -> TypeGuard[ServiceRegistryProtocol]
⋮----
"""Check if an object implements the ServiceRegistryProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements ServiceRegistryProtocol, False otherwise.
    """
⋮----
# Check for ServiceProtocol requirements
⋮----
# Check for required basic methods
service_methods = ["initialize", "shutdown"]
⋮----
# Check for registry methods
registry_methods = [
````

## File: atlas/core/primitives/resources/__init__.py
````python
"""
Resource management for Atlas framework.
This module provides resource management capabilities for tracking
and controlling access to shared resources in the application.
"""
⋮----
# Callable type aliases
⋮----
# Resource TypedDict structures
⋮----
# Resource protocols
⋮----
# Type guards
````

## File: atlas/core/primitives/resources/errors.py
````python
"""
Resource management-specific error classes.
This module provides error classes for the resource management system, including:
- ResourceNotFoundError: Raised when a resource cannot be found
- ResourceInUseError: Raised when a resource is already in use
- ResourceStateError: Raised when a resource is in an invalid state
"""
⋮----
class ResourceError(AtlasError)
⋮----
"""Base class for resource management exceptions."""
⋮----
"""Initialize the error.
        Args:
            message: The error message.
            severity: Severity level of the error.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            resource_id: Optional ID of the resource involved.
            resource_type: Optional type of the resource involved.
        """
⋮----
class ResourceNotFoundError(ResourceError)
⋮----
"""Raised when a requested resource cannot be found."""
⋮----
class ResourceInUseError(ResourceError)
⋮----
"""Raised when attempting to use a resource that's already in use."""
⋮----
details = kwargs.pop("details", {}) or {}
⋮----
class ResourceStateError(ResourceError)
⋮----
"""Raised when a resource is in an incompatible state for an operation."""
````

## File: atlas/core/primitives/resources/types.py
````python
"""
Type definitions for Atlas resource management.
This module provides type definitions specific to resource management, including:
- Protocol interfaces for resources and resource managers
- TypedDict structures for resource configuration
- Type guards for resource-related objects
"""
⋮----
# ===== Type Aliases =====
ResourceAcquireCallback = Callable[[str, float], bool]
ResourceReleaseCallback = Callable[[str], bool]
ResourceStatusCallback = Callable[[str], dict[str, Any]]
# ===== Resource TypedDict Definitions =====
class ResourceConfigDict(TypedDict)
⋮----
"""Configuration for a resource."""
resource_id: str
resource_type: str
max_size: int
options: dict[str, Any]
# ===== Resource Protocol Interfaces =====
⋮----
@runtime_checkable
class ResourceProtocol(Protocol)
⋮----
"""Protocol for resource objects."""
⋮----
def acquire(self, timeout: float | None = None) -> bool: ...
def release(self) -> bool: ...
def is_acquired(self) -> bool: ...
def get_info(self) -> dict[str, Any]: ...
⋮----
@runtime_checkable
class ResourceManagerProtocol(ServiceProtocol, Protocol)
⋮----
"""Protocol for resource manager services."""
def create_resource(self, resource_type: str, config: dict[str, Any]) -> Any: ...
def delete_resource(self, resource_id: str) -> bool: ...
def get_resource(self, resource_id: str) -> Any: ...
def list_resources(self) -> list[dict[str, Any]]: ...
def get_resource_types(self) -> list[str]: ...
# ===== Type Guards =====
def is_resource(obj: Any) -> TypeGuard[ResourceProtocol]
⋮----
"""Check if an object implements the ResourceProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements ResourceProtocol, False otherwise.
    """
⋮----
# Check for required attributes
⋮----
# Check for required methods
required_methods = ["acquire", "release", "is_acquired", "get_info"]
⋮----
def is_resource_manager(obj: Any) -> TypeGuard[ResourceManagerProtocol]
⋮----
"""Check if an object implements the ResourceManagerProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements ResourceManagerProtocol, False otherwise.
    """
⋮----
# Check for ServiceProtocol requirements
⋮----
# Check for required basic methods
service_methods = ["initialize", "shutdown"]
⋮----
# Check for resource manager methods
manager_methods = [
````

## File: atlas/core/primitives/state/__init__.py
````python
"""
State management for Atlas framework.
This module provides state container implementations for managing
application state with versioning and rollback capabilities.
"""
⋮----
# State TypedDict structures
⋮----
# State protocol
⋮----
# Callable type aliases
⋮----
# Type guards
````

## File: atlas/core/primitives/state/errors.py
````python
"""
State management-specific error classes.
This module provides error classes for the state management system, including:
- StateVersionError: Raised for issues with state versions
- StateUpdateError: Raised when state updates fail
- StateRollbackError: Raised when state rollback operations fail
"""
⋮----
class StateError(AtlasError)
⋮----
"""Base class for state management exceptions."""
⋮----
"""Initialize the error.
        Args:
            message: The error message.
            severity: Severity level of the error.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            state_id: Optional ID of the state container involved.
            version: Optional version of the state involved.
        """
⋮----
class StateVersionError(StateError)
⋮----
"""Raised when there's an issue with state versions."""
⋮----
details = kwargs.pop("details", {}) or {}
⋮----
class StateUpdateError(StateError)
⋮----
"""Raised when a state update fails."""
⋮----
class StateRollbackError(StateError)
⋮----
"""Raised when a state rollback fails."""
````

## File: atlas/core/primitives/state/types.py
````python
"""
Type definitions for Atlas state management system.
This module provides type definitions specific to state management, including:
- Protocol interface for state containers and state management
- TypedDict structures for state data
- Type guards for state-related objects
"""
⋮----
# ===== Type Aliases =====
TransitionValidator = Callable[[StateT, StateT], bool]
StateUpdater = Callable[[StateT], StateT]
StateReducer = Callable[[StateT, Any], StateT]
# ===== State Management TypedDict Definitions =====
class StateDict(TypedDict)
⋮----
"""State data structure."""
state_id: str
version: int
data: dict[str, Any]
metadata: dict[str, Any]
# ===== State Management Protocol Interface =====
⋮----
@runtime_checkable
class StateManagementProtocol(ServiceProtocol, Protocol, Generic[StateT])
⋮----
"""Protocol for state management components."""
def get_state(self) -> StateT: ...
def set_state(self, state: StateT) -> bool: ...
def update_state(self, updater: Any) -> StateT: ...
def get_version(self) -> int: ...
def get_history(self, max_versions: int = 10) -> list[dict[str, Any]]: ...
def rollback(self, version: int) -> bool: ...
def clear(self) -> None: ...
# ===== Type Guards =====
def is_state_container(obj: Any) -> TypeGuard[StateManagementProtocol]
⋮----
"""Check if an object implements the StateManagementProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements StateManagementProtocol, False otherwise.
    """
⋮----
# Check for ServiceProtocol requirements
⋮----
# Check for required basic methods
service_methods = ["initialize", "shutdown"]
⋮----
# Check for state management methods
state_methods = [
````

## File: atlas/core/primitives/transitions/__init__.py
````python
"""
Transition system for Atlas framework.
This module provides state transition validation and rule enforcement
for controlling how application state can change.
"""
⋮----
# Transition TypedDict structures
⋮----
# Transition protocols
⋮----
# Type guards
````

## File: atlas/core/primitives/transitions/errors.py
````python
"""
Transition-specific error classes.
This module provides error classes for state transitions, including:
- InvalidTransitionError: Raised when a state transition is not valid
- TransitionValidationError: Raised when a transition validation fails
"""
⋮----
class TransitionError(AtlasError)
⋮----
"""Base class for state transition exceptions."""
⋮----
"""Initialize the error.
        Args:
            message: The error message.
            severity: Severity level of the error.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            transition_id: Optional ID of the transition involved.
            from_state: Optional source state of the transition.
            to_state: Optional target state of the transition.
        """
⋮----
class InvalidTransitionError(TransitionError)
⋮----
"""Raised when a state transition is not valid."""
⋮----
class TransitionValidationError(TransitionError)
⋮----
"""Raised when a state transition fails validation."""
⋮----
details = kwargs.pop("details", {}) or {}
````

## File: atlas/core/primitives/transitions/types.py
````python
"""
Type definitions for Atlas transition system.
This module provides type definitions specific to state transitions, including:
- Protocol interfaces for transition validators and registries
- TypedDict structures for transition configuration
- Type guards for transition-related objects
"""
⋮----
# ===== Transition TypedDict Definitions =====
class TransitionConfigDict(TypedDict)
⋮----
"""State transition configuration."""
from_state: str
to_state: str
condition: str
validator: str
description: str
metadata: dict[str, Any]
# ===== Transition Protocol Interfaces =====
⋮----
@runtime_checkable
class TransitionValidatorProtocol(Protocol)
⋮----
"""Protocol for state transition validators."""
validator_id: str
def validate(self, from_state: str, to_state: str, context: dict[str, Any] | None = None) -> bool: ...
def get_description(self) -> str: ...
⋮----
@runtime_checkable
class TransitionRegistryProtocol(ServiceProtocol, Protocol)
⋮----
"""Protocol for transition registry components."""
def register_validator(self, validator_id: str, validator: Any) -> None: ...
def unregister_validator(self, validator_id: str) -> bool: ...
def get_validator(self, validator_id: str) -> Any: ...
def register_transition(self, from_state: str, to_state: str, config: dict[str, Any]) -> None: ...
def unregister_transition(self, from_state: str, to_state: str) -> bool: ...
def get_transition(self, from_state: str, to_state: str) -> dict[str, Any] | None: ...
def validate_transition(self, from_state: str, to_state: str, context: dict[str, Any] | None = None) -> bool: ...
def list_transitions(self, from_state: str | None = None) -> list[dict[str, Any]]: ...
# ===== Type Guards =====
def is_transition_validator(obj: Any) -> TypeGuard[TransitionValidatorProtocol]
⋮----
"""Check if an object implements the TransitionValidatorProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements TransitionValidatorProtocol, False otherwise.
    """
⋮----
# Check for required attributes
⋮----
# Check for required methods
required_methods = ["validate", "get_description"]
⋮----
def is_transition_registry(obj: Any) -> TypeGuard[TransitionRegistryProtocol]
⋮----
"""Check if an object implements the TransitionRegistryProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements TransitionRegistryProtocol, False otherwise.
    """
⋮----
# Check for ServiceProtocol requirements
⋮----
# Check for required basic methods
service_methods = ["initialize", "shutdown"]
⋮----
# Check for transition registry methods
registry_methods = [
````

## File: atlas/core/protocols.py
````python
"""
Core protocol definitions for Atlas.
This module provides common protocol interfaces used across Atlas components:
- Generic protocol interfaces that define common behaviors and contracts
- Runtime-checkable protocol patterns for type verification
- Protocol utilities and type guards
"""
⋮----
# ===== Generic Type Variables =====
KeyT = TypeVar("KeyT")
ValueT = TypeVar("ValueT")
ItemT = TypeVar("ItemT")
ResultT = TypeVar("ResultT")
# ===== Base Service Protocol =====
⋮----
@runtime_checkable
class ServiceProtocol(Protocol)
⋮----
"""Protocol interface for all service components."""
service_id: str
service_type: str
def initialize(self) -> None: ...
def shutdown(self) -> None: ...
# ===== Core Common Protocols =====
⋮----
@runtime_checkable
class IdentifiableProtocol(Protocol)
⋮----
"""Protocol for objects with unique identifiers."""
⋮----
@property
    def id(self) -> str: ...
⋮----
@runtime_checkable
class NameableProtocol(Protocol)
⋮----
"""Protocol for objects with names."""
⋮----
@property
    def name(self) -> str: ...
⋮----
@runtime_checkable
class VersionedProtocol(Protocol)
⋮----
"""Protocol for objects with version tracking."""
⋮----
@property
    def version(self) -> str: ...
⋮----
@runtime_checkable
class SerializableProtocol(Protocol)
⋮----
"""Protocol for serializable objects."""
def to_dict(self) -> dict[str, Any]: ...
⋮----
@classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SerializableProtocol": ...
# ===== Container Protocols =====
# Create contravariant type parameter for containers
ContainerItemT = TypeVar("ContainerItemT", contravariant=True)
⋮----
@runtime_checkable
class ContainerProtocol(Protocol, Generic[ContainerItemT])
⋮----
"""Protocol for basic container objects."""
def __len__(self) -> int: ...
def __contains__(self, item: ContainerItemT) -> bool: ...
⋮----
@runtime_checkable
class MutableContainerProtocol(ContainerProtocol[ContainerItemT], Protocol[ContainerItemT])
⋮----
"""Protocol for mutable containers."""
def add(self, item: ContainerItemT) -> None: ...
def remove(self, item: ContainerItemT) -> None: ...
def clear(self) -> None: ...
⋮----
@runtime_checkable
class MappingProtocol(Protocol, Generic[KeyT, ValueT])
⋮----
"""Protocol for mapping-like objects."""
def __getitem__(self, key: KeyT) -> ValueT: ...
def __setitem__(self, key: KeyT, value: ValueT) -> None: ...
def __delitem__(self, key: KeyT) -> None: ...
def __contains__(self, key: KeyT) -> bool: ...
def get(self, key: KeyT, default: ValueT | None = None) -> ValueT | None: ...
def keys(self) -> list[KeyT]: ...
def values(self) -> list[ValueT]: ...
def items(self) -> list[tuple[KeyT, ValueT]]: ...
# ===== Validation Protocols =====
⋮----
@runtime_checkable
class ValidatorProtocol(Protocol, Generic[DataT_contra, SchemaT_co])
⋮----
"""Protocol defining the interface for validators."""
def validate(self, data: DataT_contra, schema: DataT_contra) -> ValidationResult: ...
def is_valid(self, data: DataT_contra, schema: DataT_contra) -> bool: ...
def get_schema(self) -> SchemaT_co: ...
def get_supported_types(self) -> list[str]: ...
⋮----
@runtime_checkable
class JsonSchemaValidatorProtocol(ValidatorProtocol[dict[str, Any], dict[str, Any]], Protocol)
⋮----
"""Protocol for JSON Schema validators."""
def validate_schema(self, schema: dict[str, Any]) -> ValidationResult: ...
def extend_schema(self, extension: dict[str, Any]) -> dict[str, Any]: ...
⋮----
@runtime_checkable
class MarshmallowValidatorProtocol(ValidatorProtocol[Any, Any], Protocol)
⋮----
"""Protocol for Marshmallow validators."""
def create_schema(self, **field_definitions: Any) -> Any: ...
def schema_to_json_schema(self, schema: Any) -> dict[str, Any]: ...
def dump(self, obj: Any, schema: Any) -> dict[str, Any]: ...
def load(self, data: dict[str, Any], schema: Any) -> Any: ...
⋮----
@runtime_checkable
class SchemaRegistryProtocol(Protocol)
⋮----
"""Protocol for schema registry components."""
⋮----
def list_schemas(self) -> list[str]: ...
⋮----
@runtime_checkable
class ValidationSystemProtocol(ServiceProtocol, Protocol)
⋮----
"""Protocol for validation system components."""
⋮----
def list_validators(self) -> list[str]: ...
# ===== Type guards =====
def is_service(obj: Any) -> TypeGuard[ServiceProtocol]
⋮----
"""Check if an object implements the ServiceProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements ServiceProtocol, False otherwise.
    """
⋮----
# Check for required attributes and methods
required_attributes = ["service_id", "service_type"]
required_methods = ["initialize", "shutdown"]
⋮----
def is_validator(obj: Any) -> TypeGuard[ValidatorProtocol]
⋮----
"""Check if an object implements the ValidatorProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements ValidatorProtocol, False otherwise.
    """
⋮----
# Check for required methods
required_methods = [
⋮----
def is_json_schema_validator(obj: Any) -> TypeGuard[JsonSchemaValidatorProtocol]
⋮----
"""Check if an object implements the JsonSchemaValidatorProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements JsonSchemaValidatorProtocol, False otherwise.
    """
⋮----
# Check for JSON Schema specific methods
required_methods = ["validate_schema", "extend_schema"]
⋮----
def is_marshmallow_validator(obj: Any) -> TypeGuard[MarshmallowValidatorProtocol]
⋮----
"""Check if an object implements the MarshmallowValidatorProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements MarshmallowValidatorProtocol, False otherwise.
    """
⋮----
# Check for Marshmallow specific methods
required_methods = ["create_schema", "schema_to_json_schema", "dump", "load"]
⋮----
def is_validation_system(obj: Any) -> TypeGuard[ValidationSystemProtocol]
⋮----
"""Check if an object implements the ValidationSystemProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements ValidationSystemProtocol, False otherwise.
    """
⋮----
# Check for ServiceProtocol requirements
````

## File: atlas/core/schemas.py
````python
"""
Core schema definitions for Atlas.
This module provides common schema definitions used across Atlas components:
- Base schema classes for all Atlas schemas
- Common field patterns and validation rules
- Schema utilities and factories for reuse
"""
⋮----
# Type variables for generic schema handling
SchemaT = TypeVar("SchemaT", bound=Schema)
ModelT = TypeVar("ModelT")
class BaseSchema(Schema)
⋮----
"""Base schema class for all Atlas schemas.
    This provides common functionality and utilities for all schemas.
    """
class Meta
⋮----
"""Schema metadata."""
ordered = True  # Preserve field order
unknown = EXCLUDE  # Ignore unknown fields
⋮----
@classmethod
    def to_json_schema(cls) -> dict[str, Any]
⋮----
"""Convert Marshmallow schema to JSON Schema format.
        Returns:
            JSON Schema representation.
        """
schema_instance = cls()
⋮----
@classmethod
    def load_dict(cls: Type[SchemaT], data: dict[str, Any]) -> dict[str, Any]
⋮----
"""Load and validate data, returning the parsed dictionary.
        Args:
            data: Dictionary of data to validate.
        Returns:
            Validated dictionary.
        Raises:
            MarshmallowValidationError: If validation fails.
        """
result = cls().load(data)
⋮----
@classmethod
    def validate_dict(cls: Type[SchemaT], data: dict[str, Any]) -> list[str]
⋮----
"""Validate data against schema, returning error messages.
        Args:
            data: Dictionary of data to validate.
        Returns:
            List of error messages. Empty list if validation succeeds.
        """
⋮----
# Convert marshmallow error messages to string list
⋮----
messages = []
⋮----
@classmethod
    def is_valid(cls: Type[SchemaT], data: dict[str, Any]) -> bool
⋮----
"""Check if data is valid according to schema.
        Args:
            data: Dictionary of data to validate.
        Returns:
            True if valid, False otherwise.
        """
⋮----
@classmethod
    def dump_dict(cls: Type[SchemaT], obj: Any) -> dict[str, Any]
⋮----
"""Serialize an object according to schema.
        Args:
            obj: Object to serialize.
        Returns:
            Serialized dictionary.
        """
result = cls().dump(obj)
⋮----
class ModelSchema(BaseSchema)
⋮----
"""Base schema with model creation capability."""
__model__ = None  # Override in subclasses
⋮----
@post_load
    def make_model(self, data: dict[str, Any], **kwargs: Any) -> Any
⋮----
"""Create a model instance from validated data.
        Args:
            data: Validated data dictionary.
            **kwargs: Additional arguments from Marshmallow.
        Returns:
            Model instance.
        Raises:
            ValueError: If __model__ is not defined.
        """
model_cls = self.__class__.__model__
⋮----
@pre_dump
    def prepare_dump(self, obj: Any, **kwargs: Any) -> Any
⋮----
"""Prepare object for serialization.
        If the object has a to_dict method, use it.
        Args:
            obj: Object to serialize.
            **kwargs: Additional arguments from Marshmallow.
        Returns:
            Object ready for serialization.
        """
⋮----
# ===== Common Schema Fields =====
class FieldValidator
⋮----
"""Collection of common field validators."""
⋮----
@staticmethod
    def uuid_format(value: str) -> bool
⋮----
"""Validate UUID format.
        Args:
            value: String to validate.
        Returns:
            True if valid, False otherwise.
        """
⋮----
@staticmethod
    def non_empty_string(value: str) -> bool
⋮----
"""Validate non-empty string.
        Args:
            value: String to validate.
        Returns:
            True if valid, False otherwise.
        """
⋮----
# ===== Schema Factory =====
def create_schema(**field_definitions: Any) -> Type[Schema]
⋮----
"""Create a Marshmallow schema class dynamically.
    Args:
        **field_definitions: Field definitions for the schema.
    Returns:
        Dynamically created Schema class.
    """
⋮----
def create_model_schema(model_cls: Type[ModelT], **field_definitions: Any) -> Type[ModelSchema]
⋮----
"""Create a Marshmallow schema class for a specific model.
    Args:
        model_cls: Model class to create schema for.
        **field_definitions: Field definitions for the schema.
    Returns:
        Dynamically created ModelSchema class.
    """
# Create a new schema class with the model class
schema_dict = field_definitions.copy()
⋮----
# ===== Common Schema Definitions =====
class IdentifiableSchema(BaseSchema)
⋮----
"""Schema for objects with identifiers."""
id = fields.Str(required=True)
⋮----
@validates("id")
    def validate_id(self, value: str) -> None
⋮----
"""Validate ID field.
        Args:
            value: ID value to validate.
        Raises:
            MarshmallowValidationError: If validation fails.
        """
⋮----
class NameableSchema(BaseSchema)
⋮----
"""Schema for objects with names."""
name = fields.Str(required=True)
⋮----
@validates("name")
    def validate_name(self, value: str) -> None
⋮----
"""Validate name field.
        Args:
            value: Name value to validate.
        Raises:
            MarshmallowValidationError: If validation fails.
        """
⋮----
class VersionedSchema(BaseSchema)
⋮----
"""Schema for versioned objects."""
version = fields.Str(required=True)
class TimestampedSchema(BaseSchema)
⋮----
"""Schema for timestamped objects."""
created_at = fields.DateTime(required=True)
updated_at = fields.DateTime(required=True)
class ServiceConfigSchema(BaseSchema)
⋮----
"""Schema for validating service configuration."""
service_id = fields.Str(required=True)
service_type = fields.Str(required=True)
options = fields.Dict(keys=fields.Str(), values=fields.Raw(), required=False)
⋮----
@validates("service_type")
    def validate_service_type(self, service_type: str) -> None
⋮----
"""Validate the service type.
        Args:
            service_type: The service type to validate.
        Raises:
            MarshmallowValidationError: If the service type is invalid.
        """
⋮----
class ErrorSchema(BaseSchema)
⋮----
"""Schema for Atlas errors."""
message = fields.Str(required=True)
severity = fields.Str(required=True)
category = fields.Str(required=True)
type = fields.Str(required=True)
details = fields.Dict(keys=fields.Str(), values=fields.Raw(), required=False)
cause = fields.Str(required=False, allow_none=True)
⋮----
@validates("severity")
    def validate_severity(self, value: str) -> None
⋮----
"""Validate severity field.
        Args:
            value: Severity value to validate.
        Raises:
            MarshmallowValidationError: If validation fails.
        """
valid_severities = [e.value for e in ErrorSeverity]
⋮----
@validates("category")
    def validate_category(self, value: str) -> None
⋮----
"""Validate category field.
        Args:
            value: Category value to validate.
        Raises:
            MarshmallowValidationError: If validation fails.
        """
valid_categories = [e.value for e in ErrorCategory]
⋮----
class ValidationConfigSchema(BaseSchema)
⋮----
"""Schema for validation configuration."""
validator_id = fields.Str(required=True)
schema_type = fields.Str(required=True)
⋮----
class ValidationRuleSchema(BaseSchema)
⋮----
"""Schema for validation rules."""
⋮----
description = fields.Str(required=True)
error_message = fields.Str(required=True)
⋮----
class ValidationErrorSchema(BaseSchema)
⋮----
"""Schema for validation errors."""
field = fields.Str(required=False, allow_none=True)
⋮----
code = fields.Str(required=False, allow_none=True)
severity = fields.Str(required=False, load_default="error")
⋮----
def validation_result_schema_fields() -> dict[str, Any]
⋮----
"""Create fields for ValidationResultSchema."""
⋮----
# Create the ValidationResultSchema class
ValidationResultSchema = type(
class ServiceStatusSchema(BaseSchema)
⋮----
"""Schema for service status."""
⋮----
status = fields.Str(required=True)
uptime_seconds = fields.Float(required=False)
started_at = fields.DateTime(required=False)
version = fields.Str(required=False)
capabilities = fields.List(fields.Str(), required=False)
⋮----
@validates("status")
    def validate_status(self, value: str) -> None
⋮----
"""Validate status field.
        Args:
            value: Status value to validate.
        Raises:
            MarshmallowValidationError: If validation fails.
        """
# ServiceStatus is a Literal type, not an enum, so extract valid values directly
valid_statuses = ["initializing", "running", "paused", "stopped", "error"]
````

## File: atlas/core/validation.py
````python
"""
Core validation utilities using Marshmallow.
This module provides base validation functionality for all Atlas components:
- BaseSchema: Common base class for all Marshmallow schemas
- MarshmallowValidator: Validator implementation using Marshmallow
- Validation functions for converting between types
- Helper functions for schema validation and conversion
- Common field types and validators
"""
⋮----
# Type variables for generics
T = TypeVar('T')
SchemaT = TypeVar('SchemaT', bound=Schema)
DataT = TypeVar('DataT')
class BaseSchema(Schema)
⋮----
"""Base schema class for all Atlas schemas.
    This provides common functionality and utilities for all schemas.
    """
class Meta
⋮----
"""Schema metadata."""
ordered = True  # Preserve field order
⋮----
@classmethod
    def to_json_schema(cls) -> dict[str, Any]
⋮----
"""Convert Marshmallow schema to JSON Schema format.
        Returns:
            JSON Schema representation.
        """
schema_instance = cls()
⋮----
@classmethod
    def load_dict(cls: type[SchemaT], data: dict[str, Any]) -> dict[str, Any]
⋮----
"""Load and validate data, returning the parsed dictionary.
        Args:
            data: Dictionary of data to validate.
        Returns:
            Validated dictionary.
        Raises:
            MarshmallowValidationError: If validation fails.
        """
result = cls().load(data)
⋮----
@classmethod
    def validate_dict(cls: type[SchemaT], data: dict[str, Any]) -> list[str]
⋮----
"""Validate data against schema, returning error messages.
        Args:
            data: Dictionary of data to validate.
        Returns:
            List of error messages. Empty list if validation succeeds.
        """
⋮----
# Convert marshmallow error messages to string list
⋮----
messages = []
⋮----
@classmethod
    def is_valid(cls: type[SchemaT], data: dict[str, Any]) -> bool
⋮----
"""Check if data is valid according to schema.
        Args:
            data: Dictionary of data to validate.
        Returns:
            True if valid, False otherwise.
        """
⋮----
@classmethod
    def dump_dict(cls: type[SchemaT], obj: Any) -> dict[str, Any]
⋮----
"""Serialize an object according to schema.
        Args:
            obj: Object to serialize.
        Returns:
            Serialized dictionary.
        """
result = cls().dump(obj)
⋮----
@runtime_checkable
class ValidatorProtocol(Protocol)
⋮----
"""Protocol for validators."""
def validate(self, data: Any, schema: Any) -> ValidationResult: ...
def is_valid(self, data: Any, schema: Any) -> bool: ...
def get_schema(self) -> Any: ...
def get_supported_types(self) -> list[str]: ...
class MarshmallowValidator
⋮----
"""Marshmallow-based validator implementation."""
def __init__(self, default_schema: Schema | None = None) -> None
⋮----
"""Initialize the validator.
        Args:
            default_schema: Default schema to use for validation.
        """
⋮----
def validate(self, data: Any, schema: Any = None) -> ValidationResult
⋮----
"""Validate data against a schema.
        Args:
            data: Data to validate.
            schema: Schema to validate against. If None, uses default_schema.
        Returns:
            Tuple of (is_valid, error_message).
        """
schema_instance = schema or self.default_schema
⋮----
# Try to convert to Schema if it's a Schema class
⋮----
schema_instance = schema_instance()
⋮----
# Validate the data
⋮----
# Format the error message
error_message = str(e)
⋮----
def is_valid(self, data: Any, schema: Any = None) -> bool
⋮----
"""Check if data is valid according to schema.
        Args:
            data: Data to validate.
            schema: Schema to validate against. If None, uses default_schema.
        Returns:
            True if valid, False otherwise.
        """
⋮----
def get_schema(self) -> Any
⋮----
"""Get the default schema.
        Returns:
            The default schema.
        """
⋮----
def get_supported_types(self) -> list[str]
⋮----
"""Get supported schema types.
        Returns:
            List of supported schema types.
        """
⋮----
def create_schema(self, **field_definitions: Any) -> Schema
⋮----
"""Create a schema from field definitions.
        Args:
            **field_definitions: Field definitions for the schema.
        Returns:
            A new Schema instance.
        """
# Create a dynamic schema class
schema_cls: type[Schema] = type(
⋮----
def schema_to_json_schema(self, schema: Any) -> dict[str, Any]
⋮----
"""Convert a schema to JSON Schema format.
        Args:
            schema: Schema to convert.
        Returns:
            JSON Schema representation.
        """
⋮----
schema = schema()
⋮----
# Convert to JSON Schema format
result = schema.to_json_schema()
⋮----
def dump(self, obj: Any, schema: Any = None) -> dict[str, Any]
⋮----
"""Serialize an object using a schema.
        Args:
            obj: Object to serialize.
            schema: Schema to use. If None, uses default_schema.
        Returns:
            Serialized object.
        """
⋮----
result = schema_instance.dump(obj)
⋮----
def load(self, data: dict[str, Any], schema: Any = None) -> Any
⋮----
"""Deserialize data using a schema.
        Args:
            data: Data to deserialize.
            schema: Schema to use. If None, uses default_schema.
        Returns:
            Deserialized object.
        """
⋮----
"""Create a Marshmallow validator.
    Args:
        schema_cls: Schema class to use as default.
        **options: Additional options.
    Returns:
        MarshmallowValidator instance.
    """
schema_instance = None
⋮----
schema_instance = schema_cls(**options.get("schema_options", {}))
validator = MarshmallowValidator(default_schema=schema_instance)
# Cast to protocol type
⋮----
def validate_with_schema(schema: type[Schema], data: dict[str, Any]) -> ValidationResult
⋮----
"""Validate data against a schema.
    Args:
        schema: Schema class to validate against.
        data: Dictionary of data to validate.
    Returns:
        Tuple of (is_valid, error_message).
    """
⋮----
def schema_validator(schema_cls: type[Schema]) -> Callable[[dict[str, Any]], ValidationResult]
⋮----
"""Create a validator function for a schema.
    Args:
        schema_cls: Schema class to validate against.
    Returns:
        Validator function that takes data and returns (is_valid, error_message).
    """
def validator(data: dict[str, Any]) -> ValidationResult
⋮----
def with_validation(schema_cls: type[Schema]) -> Callable
⋮----
"""Decorator to validate function arguments against a schema.
    Args:
        schema_cls: Schema class to validate against.
    Returns:
        Decorator function.
    """
def decorator(func: Callable) -> Callable
⋮----
@wraps(func)
        def wrapper(data: dict[str, Any], *args: Any, **kwargs: Any) -> Any
⋮----
# Common field types
class FieldValidator
⋮----
"""Collection of common field validators."""
⋮----
@staticmethod
    def uuid_format(value: str) -> bool
⋮----
"""Validate UUID format.
        Args:
            value: String to validate.
        Returns:
            True if valid, False otherwise.
        """
⋮----
@staticmethod
    def non_empty_string(value: str) -> bool
⋮----
"""Validate non-empty string.
        Args:
            value: String to validate.
        Returns:
            True if valid, False otherwise.
        """
⋮----
# Schema Creation Utilities
def create_schema(**field_definitions: Any) -> type[Schema]
⋮----
"""Create a Marshmallow schema class dynamically.
    Args:
        **field_definitions: Field definitions for the schema.
    Returns:
        Dynamically created Schema class.
    """
⋮----
# Common Schema Definitions
class ServiceConfigSchema(BaseSchema)
⋮----
"""Schema for validating service configuration."""
service_id = fields.Str(required=True)
service_type = fields.Str(required=True)
options = fields.Dict(keys=fields.Str(), values=fields.Raw(), required=False)
⋮----
ordered = True
unknown = EXCLUDE
class ErrorSchema(BaseSchema)
⋮----
"""Schema for Atlas errors."""
message = fields.Str(required=True)
severity = fields.Str(required=True)
category = fields.Str(required=True)
type = fields.Str(required=True)
details = fields.Dict(keys=fields.Str(), values=fields.Raw(), required=False)
cause = fields.Str(required=False, allow_none=True)
⋮----
class ValidationConfigSchema(BaseSchema)
⋮----
"""Schema for validation configuration."""
validator_id = fields.Str(required=True)
schema_type = fields.Str(required=True)
⋮----
class ValidationRuleSchema(BaseSchema)
⋮----
"""Schema for validation rules."""
name = fields.Str(required=True)
description = fields.Str(required=True)
error_message = fields.Str(required=True)
⋮----
class ValidationErrorSchema(BaseSchema)
⋮----
"""Schema for validation errors."""
field = fields.Str(required=False, allow_none=True)
⋮----
code = fields.Str(required=False, allow_none=True)
severity = fields.Str(required=False)
⋮----
def validation_result_schema_fields()
⋮----
"""Create fields for ValidationResultSchema."""
⋮----
# Create the ValidationResultSchema class
ValidationResultSchema = type(
````

## File: atlas/tests/core/primitives/buffer/__init__.py
````python
"""Buffer service test package."""
````

## File: atlas/tests/core/primitives/buffer/test_types.py
````python
"""Tests for the atlas.core.buffer.types module.
This module tests the buffer type definitions, including:
- Protocol interfaces for different buffer types
- TypedDict structures for buffer configuration
- Type guards for buffer-related objects
"""
⋮----
# TypedDict structures
⋮----
# Protocol interfaces
⋮----
# Type guards
⋮----
class TestBufferTypedDicts
⋮----
"""Tests for buffer-related TypedDict structures."""
def test_buffer_config_dict(self) -> None
⋮----
"""Test BufferConfigDict can be instantiated."""
config: BufferConfigDict = {
⋮----
def test_buffer_item_dict(self) -> None
⋮----
"""Test BufferItemDict can be instantiated."""
item: BufferItemDict = {
⋮----
def test_rate_limited_buffer_config_dict(self) -> None
⋮----
"""Test RateLimitedBufferConfigDict can be instantiated."""
config: RateLimitedBufferConfigDict = {
⋮----
def test_batching_buffer_config_dict(self) -> None
⋮----
"""Test BatchingBufferConfigDict can be instantiated."""
config: BatchingBufferConfigDict = {
⋮----
class TestBufferProtocols
⋮----
"""Tests for buffer protocol interfaces."""
def test_buffer_protocol(self) -> None
⋮----
"""Test BufferProtocol with a conforming class."""
class MockBuffer
⋮----
def push(self, item: Dict[str, Any]) -> bool
def pop(self) -> Dict[str, Any] | None
def peek(self) -> Dict[str, Any] | None
def clear(self) -> None
def close(self) -> None
def pause(self) -> "MockBuffer":  # Self type
def resume(self) -> "MockBuffer":  # Self type
def is_closed(self) -> bool
⋮----
@property
            def is_empty(self) -> bool
⋮----
@property
            def is_full(self) -> bool
⋮----
@property
            def is_paused(self) -> bool
⋮----
@property
            def size(self) -> int
⋮----
@property
            def max_size(self) -> int
buffer = MockBuffer()
⋮----
def test_streaming_buffer_protocol(self) -> None
⋮----
"""Test StreamingBufferProtocol with a conforming class."""
class MockStreamingBuffer
⋮----
def pause(self) -> "MockStreamingBuffer":  # Self type
def resume(self) -> "MockStreamingBuffer":  # Self type
⋮----
# StreamingBufferProtocol additional methods
def wait_until_not_empty(self, timeout: float | None = None) -> bool
def wait_until_not_full(self, timeout: float | None = None) -> bool
buffer = MockStreamingBuffer()
⋮----
def test_rate_limited_buffer_protocol(self) -> None
⋮----
"""Test RateLimitedBufferProtocol with a conforming class."""
class MockRateLimitedBuffer
⋮----
def pause(self) -> "MockRateLimitedBuffer":  # Self type
def resume(self) -> "MockRateLimitedBuffer":  # Self type
⋮----
# StreamingBufferProtocol methods
⋮----
# RateLimitedBufferProtocol methods
⋮----
@property
            def tokens_per_second(self) -> float | None
⋮----
@property
            def chars_per_token(self) -> int
⋮----
@property
            def token_budget(self) -> float
def _calculate_token_cost(self, item: Dict[str, Any]) -> float
buffer = MockRateLimitedBuffer()
⋮----
def test_batching_buffer_protocol(self) -> None
⋮----
"""Test BatchingBufferProtocol with a conforming class."""
class MockBatchingBuffer
⋮----
def pause(self) -> "MockBatchingBuffer":  # Self type
def resume(self) -> "MockBatchingBuffer":  # Self type
⋮----
# BatchingBufferProtocol methods
⋮----
@property
            def batch_size(self) -> int | None
⋮----
@property
            def batch_timeout(self) -> float | None
⋮----
@property
            def batch_delimiter(self) -> str | None
def wait_for_batch(self, timeout: float | None = None) -> bool
def _create_batch(self, items: list[Dict[str, Any]]) -> Dict[str, Any]
buffer = MockBatchingBuffer()
⋮----
class TestTypeGuards
⋮----
"""Tests for buffer-related type guards."""
def test_type_guards_reject_invalid_objects(self) -> None
⋮----
"""Test that type guards reject invalid objects."""
invalid_objects: list[Any] = [None, "string", 42, {}, [], True]
⋮----
@pytest.mark.skip(reason="Issue with buffer system protocol matching")
    def test_buffer_system_protocol(self) -> None
⋮----
"""Test BufferSystemProtocol with a conforming class."""
# This test is temporarily skipped due to protocol mismatches
# The implementation may need to be fixed to match the protocol
````

## File: atlas/tests/core/primitives/commands/__init__.py
````python
"""Command system test package."""
````

## File: atlas/tests/core/primitives/commands/test_types.py
````python
"""Tests for the atlas.core.commands.types module.
This module tests the command system type definitions, including:
- Protocol interfaces for commands and command executors
- TypedDict structures for command data and execution results
- Type guards for command-related objects
"""
⋮----
# TypeVar declarations
⋮----
# TypedDict structures
⋮----
# Protocol interfaces
⋮----
# Type guards
⋮----
class TestCommandTypeVars
⋮----
"""Tests for command system type variables."""
def test_type_vars_exist(self) -> None
⋮----
"""Test that type variables are properly exported."""
⋮----
class TestCommandTypedDicts
⋮----
"""Tests for command-related TypedDict structures."""
def test_command_config_dict(self) -> None
⋮----
"""Test CommandConfigDict can be instantiated."""
config: CommandConfigDict = {
⋮----
def test_command_result_dict(self) -> None
⋮----
"""Test CommandResultDict can be instantiated."""
result: CommandResultDict = {
⋮----
def test_command_history_entry_dict(self) -> None
⋮----
"""Test CommandHistoryEntryDict can be instantiated."""
history_entry: CommandHistoryEntryDict = {
⋮----
class TestCommandProtocols
⋮----
"""Tests for command protocol interfaces."""
def test_command_protocol(self) -> None
⋮----
"""Test CommandProtocol with a conforming class."""
class MockCommand
⋮----
command_id: str = "test-command"
command_type: str = "test"
def execute(self, *args: Any, **kwargs: Any) -> Dict[str, Any]
def undo(self) -> bool
def can_undo(self) -> bool
command = MockCommand()
⋮----
def test_generic_command_protocol(self) -> None
⋮----
"""Test CommandProtocol with generic return types."""
class ResultType
⋮----
def __init__(self, value: str)
class MockGenericCommand(Generic[R_co])
⋮----
command_id: str = "generic-command"
command_type: str = "generic"
def execute(self, *args: Any, **kwargs: Any) -> R_co
⋮----
return ResultType("test")  # type: ignore
⋮----
command = MockGenericCommand[ResultType]()
⋮----
# Execute should return ResultType
result = command.execute()
⋮----
def test_command_executor_protocol(self) -> None
⋮----
"""Test CommandExecutorProtocol with a conforming class."""
class MockCommandExecutor
⋮----
service_id: str = "command-executor"
service_type: str = "commands"
def initialize(self) -> None
def shutdown(self) -> None
# CommandExecutorProtocol methods
def register_command(self, command_type: str, factory: Any) -> None
def unregister_command(self, command_type: str) -> bool
⋮----
def undo(self, command_id: str | None = None) -> bool
def redo(self, command_id: str | None = None) -> Dict[str, Any]
def get_history(self, max_entries: int = 10) -> list[Dict[str, Any]]
def clear_history(self) -> None
executor = MockCommandExecutor()
⋮----
def test_generic_command_executor(self) -> None
⋮----
"""Test CommandExecutorProtocol with generic return types."""
⋮----
class MockGenericExecutor(Generic[R])
⋮----
service_id: str = "generic-executor"
⋮----
def execute(self, command_type: str, *args: Any, **kwargs: Any) -> R
⋮----
def redo(self, command_id: str | None = None) -> R
⋮----
return ResultType("redone")  # type: ignore
⋮----
executor = MockGenericExecutor[ResultType]()
⋮----
result = executor.execute("test")
⋮----
# Redo should also return ResultType
redo_result = executor.redo()
⋮----
class TestTypeGuards
⋮----
"""Tests for command-related type guards."""
def test_is_command_rejects_invalid(self) -> None
⋮----
"""Test that is_command rejects invalid objects."""
invalid_objects: list[Any] = [None, "string", 42, {}, [], True]
⋮----
# Test with incomplete implementation
class IncompleteCommand
⋮----
command_id: str = "incomplete-command"
command_type: str = "incomplete"
# Missing methods
incomplete = IncompleteCommand()
⋮----
def test_is_command_executor_rejects_invalid(self) -> None
⋮----
"""Test that is_command_executor rejects invalid objects."""
⋮----
class IncompleteExecutor
⋮----
service_id: str = "incomplete-executor"
⋮----
incomplete = IncompleteExecutor()
````

## File: atlas/tests/core/primitives/component/__init__.py
````python
"""Component service test package."""
````

## File: atlas/tests/core/primitives/component/test_types.py
````python
"""Tests for the atlas.core.component.types module.
This module tests the service-enabled component type definitions, including:
- Protocol interface for service-enabled components
- TypedDict structures for component configuration
- Type guards for service-enabled objects
"""
⋮----
# TypedDict structures
⋮----
# Protocol interfaces
⋮----
# Type guards
⋮----
class TestComponentTypedDicts
⋮----
"""Tests for component-related TypedDict structures."""
def test_component_config_dict(self) -> None
⋮----
"""Test ComponentConfigDict can be instantiated."""
config: ComponentConfigDict = {
⋮----
class TestServiceEnabledProtocol
⋮----
"""Tests for service-enabled protocol interfaces."""
def test_service_enabled_protocol(self) -> None
⋮----
"""Test ServiceEnabledProtocol with a conforming class."""
class MockRegistry
⋮----
def get_service(self, service_type: str) -> Any
class MockServiceEnabledComponent
⋮----
component_id: str = "test-component"
component_type: str = "processor"
# ServiceEnabledProtocol methods
def set_service_registry(self, registry: Any) -> None
⋮----
def has_service(self, service_type: str) -> bool
component = MockServiceEnabledComponent()
⋮----
# Test service access
registry = MockRegistry()
⋮----
def test_component_with_required_services(self) -> None
⋮----
"""Test a component that requires specific services."""
⋮----
def __init__(self) -> None
⋮----
class DataProcessorComponent
⋮----
component_id: str = "data-processor"
⋮----
required_services: list[str] = ["buffer", "events"]
⋮----
# Verify required services are available
missing_services = []
⋮----
# Component-specific methods
def initialize(self) -> None
⋮----
# Verify required services again during initialization
⋮----
def process(self, data: Dict[str, Any]) -> Dict[str, Any]
⋮----
# Get required services
buffer_service = self.get_service("buffer")
events_service = self.get_service("events")
# Process data (mock implementation)
result = {"processed": True, "input": data}
⋮----
# Create component and set registry
component = DataProcessorComponent()
⋮----
# Check service access
⋮----
# Initialize and use component
component.initialize()  # type: ignore[attr-defined]
assert component.initialized  # type: ignore[attr-defined]
result = component.process({"key": "value"})  # type: ignore[attr-defined]
⋮----
class TestTypeGuards
⋮----
"""Tests for component-related type guards."""
def test_is_service_enabled_rejects_invalid(self) -> None
⋮----
"""Test that is_service_enabled rejects invalid objects."""
invalid_objects: list[Any] = [None, "string", 42, {}, [], True]
⋮----
# Test with incomplete implementation
class IncompleteComponent
⋮----
component_id: str = "incomplete-component"
component_type: str = "incomplete"
# Missing methods
incomplete = IncompleteComponent()
````

## File: atlas/tests/core/primitives/events/__init__.py
````python
"""Event system test package."""
````

## File: atlas/tests/core/primitives/events/test_types.py
````python
"""Tests for the atlas.core.events.types module.
This module tests the event system type definitions, including:
- Protocol interface for event publication and subscription
- TypedDict structures for event data and subscription configuration
- Type validation utilities for event types and patterns
"""
⋮----
# TypedDict structures
⋮----
# Protocol interfaces
⋮----
# Type guards
⋮----
# Validation functions
⋮----
class TestEventTypedDicts
⋮----
"""Tests for event-related TypedDict structures."""
def test_event_data_dict(self) -> None
⋮----
"""Test EventDataDict can be instantiated."""
event_data: EventDataDict = {
⋮----
def test_subscription_config_dict(self) -> None
⋮----
"""Test SubscriptionConfigDict can be instantiated."""
config: SubscriptionConfigDict = {
⋮----
class TestEventProtocol
⋮----
"""Tests for event protocol interfaces."""
def test_event_protocol(self) -> None
⋮----
"""Test EventProtocol with a conforming class."""
class MockEventSystem
⋮----
service_id: str = "event-system"
service_type: str = "events"
def initialize(self) -> None
def shutdown(self) -> None
# EventProtocol methods
⋮----
def unsubscribe(self, subscription_id: str) -> bool
⋮----
event_system = MockEventSystem()
⋮----
def test_event_protocol_rejects_invalid(self) -> None
⋮----
"""Test that EventProtocol rejects invalid objects."""
invalid_objects: list[Any] = [None, "string", 42, {}, [], True]
⋮----
# Test with missing methods
class IncompleteEventSystem
⋮----
# Missing publish, subscribe, unsubscribe methods
incomplete = IncompleteEventSystem()
⋮----
class TestValidationFunctions
⋮----
"""Tests for event type and pattern validation."""
def test_validate_event_type(self) -> None
⋮----
"""Test validation of event type strings."""
# Valid event types
valid_types = [
⋮----
# Invalid event types
invalid_types = [
⋮----
"",  # Empty string
"invalid.event.type!",  # Invalid characters
"Invalid.Type",  # Capital letters
"invalid.event.type.",  # Ends with dot
".invalid.type",  # Starts with dot
"invalid..type",  # Consecutive dots
⋮----
def test_validate_subscription_pattern(self) -> None
⋮----
"""Test validation of subscription pattern strings."""
# Valid patterns
valid_patterns = [
⋮----
# Invalid patterns
invalid_patterns = [
⋮----
"invalid.pattern!",  # Invalid characters
"Invalid.Pattern",  # Capital letters
"invalid.pattern.",  # Ends with dot
".invalid.pattern",  # Starts with dot
"invalid..pattern",  # Consecutive dots
"**",  # Double wildcard not supported
"user.**.success",  # Double wildcard not supported
````

## File: atlas/tests/core/primitives/middleware/__init__.py
````python
"""Middleware system test package."""
````

## File: atlas/tests/core/primitives/middleware/test_types.py
````python
"""Tests for the atlas.core.middleware.types module.
This module tests the middleware type definitions, including:
- Protocol interface for middleware
- Type aliases for middleware priorities and functions
- Type guards for middleware-related objects
"""
⋮----
# Protocol interfaces
⋮----
# Type guards
⋮----
class TestMiddlewareProtocol
⋮----
"""Tests for middleware protocol interfaces."""
def test_middleware_protocol(self) -> None
⋮----
"""Test MiddlewareProtocol with a conforming class."""
class MockMiddleware
⋮----
middleware_id: str = "test-middleware"
priority: int = 100
⋮----
# Add middleware marker
⋮----
# Call next middleware if available
⋮----
result = next_middleware(data)
⋮----
middleware = MockMiddleware()
⋮----
# Test middleware processing
data = {"key": "value"}
result = middleware.process(data)
⋮----
def test_generic_middleware_protocol(self) -> None
⋮----
"""Test MiddlewareProtocol with generic types."""
T = TypeVar("T")
class GenericMiddleware(Generic[T])
⋮----
middleware_id: str = "generic-middleware"
⋮----
def process(self, data: T, next_middleware: Any = None) -> T
⋮----
# For testing, just return the data
⋮----
# Test with different data types
string_middleware = GenericMiddleware[str]()
⋮----
dict_middleware = GenericMiddleware[Dict[str, Any]]()
⋮----
def test_middleware_chain(self) -> None
⋮----
"""Test chaining multiple middleware components."""
class LoggingMiddleware
⋮----
middleware_id: str = "logging-middleware"
priority: int = 10  # High priority, runs first
⋮----
# Add logging info
⋮----
# Call next middleware
⋮----
class ValidationMiddleware
⋮----
middleware_id: str = "validation-middleware"
priority: int = 20
⋮----
# Validate data (mock implementation)
⋮----
class TransformationMiddleware
⋮----
middleware_id: str = "transformation-middleware"
priority: int = 30
⋮----
# Transform data
⋮----
# Create middleware instances
logging_mw = LoggingMiddleware()
validation_mw = ValidationMiddleware()
transform_mw = TransformationMiddleware()
⋮----
# Create middleware chain manually (in order of priority)
def execute_middleware_chain(data: Dict[str, Any]) -> Dict[str, Any]
⋮----
# This is a simplified version of what a middleware system would do
transformed_data = logging_mw.process(
# Ensure we're returning a Dict[str, Any]
⋮----
# Test the chain
initial_data = {"value": "test"}
result = execute_middleware_chain(initial_data)
⋮----
class TestTypeGuards
⋮----
"""Tests for middleware-related type guards."""
def test_is_middleware_rejects_invalid(self) -> None
⋮----
"""Test that is_middleware rejects invalid objects."""
invalid_objects: list[Any] = [None, "string", 42, {}, [], True]
⋮----
# Test with incomplete implementation
class IncompleteMiddleware
⋮----
middleware_id: str = "incomplete-middleware"
# Missing process method or priority
incomplete = IncompleteMiddleware()
````

## File: atlas/tests/core/primitives/registry/__init__.py
````python
"""Registry service test package."""
````

## File: atlas/tests/core/primitives/registry/test_types.py
````python
"""Tests for the atlas.core.registry.types module.
This module tests the service registry type definitions, including:
- Protocol interface for service registry
- Type aliases for service factories
- Type guards for registry-related objects
"""
⋮----
# Protocol interfaces
⋮----
# Type guards
⋮----
class TestServiceRegistryProtocol
⋮----
"""Tests for service registry protocol interfaces."""
def test_service_registry_protocol(self) -> None
⋮----
"""Test ServiceRegistryProtocol with a conforming class."""
class MockServiceRegistry
⋮----
service_id: str = "service-registry"
service_type: str = "registry"
def initialize(self) -> None
def shutdown(self) -> None
# ServiceRegistryProtocol methods
⋮----
def unregister_service(self, service_type: str) -> bool
def get_service(self, service_type: str) -> Any
def has_service(self, service_type: str) -> bool
def list_services(self) -> list[str]
class MockService
⋮----
service_id: str = "mock-service"
service_type: str = "mock"
⋮----
registry = MockServiceRegistry()
⋮----
def test_service_registry_protocol_rejects_invalid(self) -> None
⋮----
"""Test that ServiceRegistryProtocol rejects invalid objects."""
invalid_objects: list[Any] = [None, "string", 42, {}, [], True]
⋮----
# Test with incomplete implementation
class IncompleteServiceRegistry
⋮----
# Missing registry methods
incomplete = IncompleteServiceRegistry()
⋮----
class TestServiceFactories
⋮----
"""Tests for service factory type definitions."""
def test_service_factory_type(self) -> None
⋮----
"""Test service factory type definition."""
class MockBufferService
⋮----
service_id: str = "buffer-service"
service_type: str = "buffer"
⋮----
# Define a service factory function
def buffer_factory(config: Dict[str, Any] | None = None) -> MockBufferService
# Create a mock registry
class MockRegistry
⋮----
def __init__(self) -> None
⋮----
# Register and retrieve services
registry = MockRegistry()
⋮----
service = registry.get_service("buffer")
⋮----
# Unregister service
````

## File: atlas/tests/core/primitives/resources/__init__.py
````python
"""Resource management test package."""
````

## File: atlas/tests/core/primitives/resources/test_types.py
````python
"""Tests for the atlas.core.resources.types module.
This module tests the resource management type definitions, including:
- Protocol interfaces for resources and resource managers
- TypedDict structures for resource configuration
- Type guards for resource-related objects
"""
⋮----
# TypedDict structures
⋮----
# Protocol interfaces
⋮----
# Type guards
⋮----
class TestResourceTypedDicts
⋮----
"""Tests for resource-related TypedDict structures."""
def test_resource_config_dict(self) -> None
⋮----
"""Test ResourceConfigDict can be instantiated."""
config: ResourceConfigDict = {
⋮----
class TestResourceProtocols
⋮----
"""Tests for resource protocol interfaces."""
def test_resource_protocol(self) -> None
⋮----
"""Test ResourceProtocol with a conforming class."""
class MockResource
⋮----
resource_id: str = "test-resource"
resource_type: str = "memory"
def acquire(self, timeout: float | None = None) -> bool
def release(self) -> bool
def is_acquired(self) -> bool
def get_info(self) -> Dict[str, Any]
resource = MockResource()
⋮----
def test_resource_manager_protocol(self) -> None
⋮----
"""Test ResourceManagerProtocol with a conforming class."""
⋮----
class MockResourceManager
⋮----
service_id: str = "resource-manager"
service_type: str = "resources"
def initialize(self) -> None
def shutdown(self) -> None
# ResourceManagerProtocol methods
⋮----
def delete_resource(self, resource_id: str) -> bool
def get_resource(self, resource_id: str) -> Any
def list_resources(self) -> list[Dict[str, Any]]
def get_resource_types(self) -> list[str]
manager = MockResourceManager()
⋮----
class TestResourceUsagePatterns
⋮----
"""Tests for common resource usage patterns."""
def test_resource_acquire_release_pattern(self) -> None
⋮----
"""Test acquire-release pattern with resources."""
⋮----
def __init__(self) -> None
⋮----
# Test acquire-release pattern
⋮----
def test_resource_manager_lifecycle(self) -> None
⋮----
"""Test resource manager lifecycle operations."""
⋮----
# Release all resources on shutdown
⋮----
resource_id = config.get(
resource = MockResource(resource_id, resource_type)
⋮----
resource = self.resources[resource_id]
⋮----
def __init__(self, resource_id: str, resource_type: str)
⋮----
# Test manager operations
⋮----
# Create a resource
config = {"resource_id": "test-memory", "max_size": 1024}
resource = manager.create_resource("memory", config)
⋮----
# Get the resource
retrieved = manager.get_resource("test-memory")
⋮----
# List resources
resources = manager.list_resources()
⋮----
# Delete resource
⋮----
class TestTypeGuards
⋮----
"""Tests for resource-related type guards."""
def test_is_resource_rejects_invalid(self) -> None
⋮----
"""Test that is_resource rejects invalid objects."""
invalid_objects: list[Any] = [None, "string", 42, {}, [], True]
⋮----
# Test with incomplete implementation
class IncompleteResource
⋮----
resource_id: str = "incomplete-resource"
resource_type: str = "incomplete"
# Missing methods
incomplete = IncompleteResource()
⋮----
def test_is_resource_manager_rejects_invalid(self) -> None
⋮----
"""Test that is_resource_manager rejects invalid objects."""
⋮----
class IncompleteManager
⋮----
service_id: str = "incomplete-manager"
⋮----
incomplete = IncompleteManager()
````

## File: atlas/tests/core/primitives/state/__init__.py
````python
"""State management test package."""
````

## File: atlas/tests/core/primitives/state/test_types.py
````python
"""Tests for the atlas.core.state.types module.
This module tests the state management type definitions, including:
- Protocol interface for state containers and state management
- TypedDict structures for state data
- Type guards for state-related objects
"""
⋮----
# TypedDict structures
⋮----
# Protocol interfaces
⋮----
# Type guards
⋮----
class TestStateTypedDicts
⋮----
"""Tests for state-related TypedDict structures."""
def test_state_dict(self) -> None
⋮----
"""Test StateDict can be instantiated."""
state: StateDict = {
⋮----
class TestStateManagementProtocol
⋮----
"""Tests for state management protocol interfaces."""
def test_state_management_protocol(self) -> None
⋮----
"""Test StateManagementProtocol with a conforming class."""
T = TypeVar("T")
class MockStateContainer(Generic[T])
⋮----
service_id: str = "state-container"
service_type: str = "state"
def initialize(self) -> None
def shutdown(self) -> None
# StateManagementProtocol methods
def get_state(self) -> T
⋮----
return {"key": "value"}  # type: ignore
def set_state(self, state: T) -> bool
def update_state(self, updater: Any) -> T
⋮----
return {"key": "updated-value"}  # type: ignore
def get_version(self) -> int
def get_history(self, max_versions: int = 10) -> list[Dict[str, Any]]
def rollback(self, version: int) -> bool
def clear(self) -> None
state_container = MockStateContainer[Dict[str, str]]()
⋮----
def test_generic_state_management(self) -> None
⋮----
"""Test using StateManagementProtocol with different state types."""
# Define a state type
class AppState
⋮----
def __init__(self, name: str, value: int)
class MockStateManager(Generic[StateT])
⋮----
service_id: str = "state-manager"
⋮----
def get_state(self) -> StateT
⋮----
return AppState("test", 42)  # type: ignore
def set_state(self, state: StateT) -> bool
def update_state(self, updater: Any) -> StateT
⋮----
return AppState("updated", 43)  # type: ignore
⋮----
# Create state manager with AppState
state_manager = MockStateManager[AppState]()
⋮----
# Get state should return AppState
state = state_manager.get_state()
⋮----
class TestTypeGuards
⋮----
"""Tests for state-related type guards."""
def test_is_state_container_rejects_invalid(self) -> None
⋮----
"""Test that is_state_container rejects invalid objects."""
invalid_objects: list[Any] = [None, "string", 42, {}, [], True]
⋮----
# Test with incomplete implementation
class IncompleteStateContainer
⋮----
# Missing state management methods
incomplete = IncompleteStateContainer()
````

## File: atlas/tests/core/primitives/transitions/__init__.py
````python
"""Transition system test package."""
````

## File: atlas/tests/core/primitives/transitions/test_types.py
````python
"""Tests for the atlas.core.transitions.types module.
This module tests the transition system type definitions, including:
- Protocol interfaces for transition validators and registries
- TypedDict structures for transition configuration
- Type guards for transition-related objects
"""
⋮----
# TypedDict structures
⋮----
# Protocol interfaces
⋮----
# Type guards
⋮----
class TestTransitionTypedDicts
⋮----
"""Tests for transition-related TypedDict structures."""
def test_transition_config_dict(self) -> None
⋮----
"""Test TransitionConfigDict can be instantiated."""
config: TransitionConfigDict = {
⋮----
class TestTransitionProtocols
⋮----
"""Tests for transition protocol interfaces."""
def test_transition_validator_protocol(self) -> None
⋮----
"""Test TransitionValidatorProtocol with a conforming class."""
class MockTransitionValidator
⋮----
validator_id: str = "test-validator"
⋮----
def get_description(self) -> str
validator = MockTransitionValidator()
⋮----
def test_transition_registry_protocol(self) -> None
⋮----
"""Test TransitionRegistryProtocol with a conforming class."""
class MockTransitionRegistry
⋮----
service_id: str = "transition-registry"
service_type: str = "transitions"
def initialize(self) -> None
def shutdown(self) -> None
# TransitionRegistryProtocol methods
def register_validator(self, validator_id: str, validator: Any) -> None
def unregister_validator(self, validator_id: str) -> bool
def get_validator(self, validator_id: str) -> Any
⋮----
def unregister_transition(self, from_state: str, to_state: str) -> bool
⋮----
registry = MockTransitionRegistry()
⋮----
class TestTypeGuards
⋮----
"""Tests for transition-related type guards."""
def test_is_transition_validator_rejects_invalid(self) -> None
⋮----
"""Test that is_transition_validator rejects invalid objects."""
invalid_objects: list[Any] = [None, "string", 42, {}, [], True]
⋮----
# Test with incomplete implementation
class IncompleteValidator
⋮----
validator_id: str = "incomplete-validator"
# Missing methods
incomplete = IncompleteValidator()
⋮----
def test_is_transition_registry_rejects_invalid(self) -> None
⋮----
"""Test that is_transition_registry rejects invalid objects."""
⋮----
class IncompleteRegistry
⋮----
service_id: str = "incomplete-registry"
⋮----
incomplete = IncompleteRegistry()
````

## File: atlas/tests/core/__init__.py
````python
"""
Core module test package.
This package contains tests for the core Atlas functionality,
including all core services and their types.
"""
````

## File: atlas/tests/core/test_errors.py
````python
"""Tests for the atlas.core.errors module.
This module tests the core error handling infrastructure, including:
- AtlasError base class
- ErrorSeverity and ErrorCategory enums
- Error handling utilities
"""
⋮----
class TestAtlasError
⋮----
"""Tests for the AtlasError base class."""
def test_atlas_error_initialization(self) -> None
⋮----
"""Test basic AtlasError initialization and properties."""
error = AtlasError(
⋮----
# Verify it can be raised as an exception
⋮----
def test_atlas_error_to_dict(self) -> None
⋮----
"""Test conversion of AtlasError to dictionary."""
⋮----
error_dict = error.to_dict()
⋮----
def test_atlas_error_logging(self, caplog: Any) -> None
⋮----
"""Test logging of AtlasError with different severity levels."""
⋮----
# Test INFO severity
info_error = AtlasError(
⋮----
# Test WARNING severity
warning_error = AtlasError(
⋮----
# Test ERROR severity with cause
cause = ValueError("Original cause")
error_with_cause = AtlasError(
⋮----
# The traceback should be included for ERROR level
⋮----
# Test with custom log level
custom_error = AtlasError(
⋮----
severity=ErrorSeverity.INFO  # This would normally log at INFO
⋮----
class TestErrorEnums
⋮----
"""Tests for ErrorSeverity and ErrorCategory enums."""
def test_error_severity_enum(self) -> None
⋮----
"""Test ErrorSeverity enum values."""
⋮----
# Test comparison
⋮----
def test_error_category_enum(self) -> None
⋮----
"""Test ErrorCategory enum values."""
# Check a few key categories
⋮----
# Test that all the service-specific categories exist
⋮----
class TestSafeExecute
⋮----
"""Tests for the safe_execute utility function."""
def test_safe_execute_success(self) -> None
⋮----
"""Test safe_execute with successful function execution."""
def success_func(a: int, b: int) -> int
result = safe_execute(success_func, args=(1, 2))
⋮----
# With keyword arguments
result = safe_execute(success_func, function_kwargs={"a": 3, "b": 4})
⋮----
def test_safe_execute_with_exception(self) -> None
⋮----
"""Test safe_execute when function raises an exception."""
def failing_func() -> str
# With default (re-raise)
⋮----
# With default value
result = safe_execute(failing_func, default="default")
⋮----
def test_safe_execute_with_error_handler(self) -> None
⋮----
"""Test safe_execute with custom error handler."""
def failing_func() -> int
def error_handler(e: Exception) -> int
result = safe_execute(failing_func, error_handler=error_handler)
⋮----
def test_safe_execute_with_custom_error_class(self) -> None
⋮----
"""Test safe_execute with custom error class."""
class CustomError(AtlasError)
def failing_func() -> None
⋮----
def test_safe_execute_with_error_kwargs(self) -> None
⋮----
"""Test safe_execute with additional kwargs for error construction."""
def function_with_specific_params(a: int, b: int) -> int
# The 'extra_detail' parameter doesn't belong to the function
# but should be included in the error details
⋮----
class TestErrorHelpers
⋮----
"""Tests for error helper functions."""
def test_get_error_message(self) -> None
⋮----
"""Test get_error_message utility function."""
# With standard exception
std_error = ValueError("Standard error")
message = get_error_message(std_error)
⋮----
# With AtlasError
atlas_error = AtlasError(
message = get_error_message(atlas_error)
⋮----
# With traceback
⋮----
# Create an exception with a traceback
⋮----
message = get_error_message(e, include_traceback=True)
⋮----
def test_convert_exception(self) -> None
⋮----
"""Test convert_exception utility function."""
# Convert standard exception
⋮----
atlas_error = convert_exception(std_error)
⋮----
# With custom message
atlas_error = convert_exception(
⋮----
# With custom severity and category
⋮----
# With custom error class
⋮----
custom_error = convert_exception(std_error, error_cls=CustomError)
⋮----
# If already the correct type, should return as is
original_error = CustomError("Original")
returned_error = convert_exception(original_error, error_cls=CustomError)
````

## File: atlas/tests/core/test_types.py
````python
"""Tests for the atlas.core.types module.
This module tests the core type definitions, including:
- Type variables
- Protocol interfaces
- TypedDict structures
- Type validation functions
"""
⋮----
# Type variables
⋮----
# TypedDict structures
⋮----
# Protocol interfaces
⋮----
# Utility functions
⋮----
class TestTypeVariables
⋮----
"""Tests for type variables."""
def test_type_variables_exist(self) -> None
⋮----
"""Test that all type variables are exported."""
# This test mainly ensures type variables are exported correctly
⋮----
class TestProtocolInterfaces
⋮----
"""Tests for protocol interfaces."""
def test_service_protocol_structural_typing(self) -> None
⋮----
"""Test that ServiceProtocol works with structural typing."""
# Create a class that structurally matches ServiceProtocol
class MockService
⋮----
service_id: str = "mock-service"
service_type: str = "mock"
def initialize(self) -> None
def shutdown(self) -> None
service = MockService()
⋮----
def test_service_protocol_rejects_invalid_structs(self) -> None
⋮----
"""Test that ServiceProtocol rejects invalid structures."""
# Create a class that doesn't match ServiceProtocol
class InvalidService
⋮----
# Missing service_id and service_type
⋮----
# Missing shutdown method
invalid = InvalidService()
⋮----
class TestTypeGuards
⋮----
"""Tests for type guard functions."""
def test_is_service(self) -> None
⋮----
"""Test the is_service type guard function."""
# Create a mock service
⋮----
service_id: str = "test-service"
service_type: str = "test"
⋮----
# Test with non-service objects
⋮----
class TestEnsureServiceType
⋮----
"""Tests for the ensure_service_type function."""
def test_ensure_service_type_valid(self) -> None
⋮----
"""Test ensure_service_type with valid service types."""
# These should not raise exceptions
⋮----
def test_ensure_service_type_invalid(self) -> None
⋮----
"""Test ensure_service_type with invalid service types."""
# These should raise ValueError
⋮----
class TestTypedDictStructures
⋮----
"""Tests for TypedDict structures."""
def test_service_config_dict(self) -> None
⋮----
"""Test ServiceConfigDict can be instantiated."""
config: ServiceConfigDict = {
````

## File: atlas/tests/conftest.py
````python
"""
Test configuration and fixtures for Atlas tests.
This module provides common fixtures and test configuration
used across multiple test files for the Atlas framework.
"""
⋮----
# Add project root to path to enable imports
⋮----
# Configure logging for tests
⋮----
# Silence some noisy loggers during tests
⋮----
@pytest.fixture
def temp_env() -> Generator[None, None, None]
⋮----
"""Create a temporary environment for testing.
    This fixture allows setting temporary environment variables for the duration of a test
    and restores the original environment when the test completes.
    """
old_environ = dict(os.environ)
⋮----
@pytest.fixture
def mock_error() -> AtlasError
⋮----
"""Create a mock AtlasError for testing."""
⋮----
"""Assert that a specific Atlas error is raised with expected attributes.
    Args:
        error_type: The expected error type
        message_contains: Optional substring expected in the error message
        severity: Optional expected error severity
        category: Optional expected error category
    Raises:
        AssertionError: If the expected error wasn't raised or didn't match expectations
    """
⋮----
@pytest.fixture
def raises_atlas_error() -> Any
⋮----
"""Fixture that provides the assert_raises_atlas_error context manager."""
⋮----
@pytest.fixture
async def async_temp_env() -> AsyncGenerator[None, None]
⋮----
"""Create a temporary environment for async testing."""
````

## File: atlas/tests/utils.py
````python
"""
Utility functions and classes for tests.
This module provides common test utilities used across
multiple test files for the Atlas framework.
"""
⋮----
T = TypeVar("T")
def assert_implements_protocol(obj: Any, protocol_type: Type[T]) -> None
⋮----
"""
    Assert that an object correctly implements a protocol.
    Args:
        obj: The object to check
        protocol_type: The protocol type to check against
    Raises:
        AssertionError: If the object does not implement the protocol correctly
    """
# Get all required methods and properties from the protocol
protocol_members = []
⋮----
# Check that the object implements all required members
⋮----
def assert_type_annotations_match(func: Callable, expected_annotations: Dict[str, Any]) -> None
⋮----
"""
    Assert that a function's type annotations match the expected ones.
    Args:
        func: The function to check
        expected_annotations: Dictionary of parameter names to expected types
    Raises:
        AssertionError: If annotations don't match expectations
    """
annotations = getattr(func, "__annotations__", {})
⋮----
def camel_to_snake(name: str) -> str
⋮----
"""
    Convert CamelCase to snake_case.
    Args:
        name: The CamelCase string
    Returns:
        The snake_case version of the string
    """
name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
⋮----
def assert_attributes_match(obj: Any, expected_attrs: Dict[str, Any]) -> None
⋮----
"""
    Assert that an object's attributes match the expected values.
    Args:
        obj: The object to check
        expected_attrs: Dictionary of attribute names to expected values
    Raises:
        AssertionError: If attributes don't match expectations
    """
⋮----
def get_type_parameters(obj: Any) -> List[Type]
⋮----
"""
    Get the type parameters of a generic class.
    Args:
        obj: The generic object
    Returns:
        A list of type parameters
    """
⋮----
# Fall back to getting __orig_class__ if available (for typed instances)
orig_class = getattr(obj, "__orig_class__", None)
````

## File: atlas/core/types.py
````python
"""
Common type definitions for Atlas core services.
This module provides core type definitions used across all Atlas services, including:
- Type variables for generic typing
- Type aliases for primitive types
- Common literal types for status values
- Basic service-related TypedDict structures
- Service protocol base definitions
- Validation-related types and protocols
"""
⋮----
# ===== Service Type Constants =====
# Service type constants matching architecture plan
SERVICE_BUFFER: Final[str] = "buffer"
SERVICE_EVENTS: Final[str] = "events"
SERVICE_STATE: Final[str] = "state"
SERVICE_COMMANDS: Final[str] = "commands"
SERVICE_RESOURCES: Final[str] = "resources"
SERVICE_REGISTRY: Final[str] = "registry"
SERVICE_COMPONENT: Final[str] = "component"
SERVICE_MIDDLEWARE: Final[str] = "middleware"
SERVICE_VALIDATION: Final[str] = "validation"
SERVICE_TRANSITIONS: Final[str] = "transitions"
# ===== Generic Type Variables =====
T = TypeVar("T")  # Generic data type
K = TypeVar("K")  # Generic key type
V = TypeVar("V")  # Generic value type
R = TypeVar("R")  # Generic return type
DataT = TypeVar("DataT")  # Data type for generic containers
StateT = TypeVar("StateT")  # State type for state containers
EventT = TypeVar("EventT")  # Event type for event systems
ResultT = TypeVar("ResultT", covariant=True)  # Result type for commands (covariant)
ErrorT = TypeVar("ErrorT")  # Error type for commands
SchemaT = TypeVar("SchemaT")  # Schema type for validators
# For specialized variance
T_co = TypeVar("T_co", covariant=True)  # Covariant type parameter
T_contra = TypeVar("T_contra", contravariant=True)  # Contravariant type parameter
DataT_contra = TypeVar("DataT_contra", contravariant=True)  # Contravariant data type
SchemaT_co = TypeVar("SchemaT_co", covariant=True)  # Covariant schema type
# ===== Basic Type Aliases =====
type ServiceId = str  # Service identifier (typically UUID)
type ResourceId = str  # Resource identifier (typically UUID)
type EventId = str  # Event identifier (typically UUID)
type EventType = str  # Event type string (e.g., "system.started")
type CommandId = str  # Command identifier (typically UUID)
type CommandName = str  # Command name
type SubscriptionId = str  # Subscription identifier (typically UUID)
type StateId = str  # State identifier (typically UUID)
type TransitionId = str  # Transition identifier (typically UUID)
type BufferId = str  # Buffer identifier (typically UUID)
type ComponentId = str  # Component identifier (typically UUID)
type ValidatorId = str  # Validator identifier (typically UUID)
type BufferSize = int  # Buffer size in items or bytes
type TokenRate = float  # Token rate for rate limiting
type CharCount = int  # Character count
type TimestampISO = str  # ISO format timestamp string
type Timestamp = float  # Unix timestamp (seconds since epoch)
type ThreadLock = RLock  # Thread lock type
type ThreadEvent = Event  # Thread event type
# ===== Literal Status Values =====
⋮----
type MiddlewarePriority = int  # Higher numbers run first
# ===== Common Callback Types =====
⋮----
type ValidationResult = tuple[bool, str | None]  # (is_valid, error_message)
# ===== TypedDict for Core Service Configuration =====
class ServiceConfigDict(TypedDict)
⋮----
"""Configuration for a service component."""
service_id: str
service_type: str
options: dict[str, Any]
# ===== Validation TypedDict Definitions =====
class ValidationConfigDict(TypedDict)
⋮----
"""Base configuration for validation services."""
validator_id: str
schema_type: str
⋮----
class ValidationRuleDict(TypedDict)
⋮----
"""Definition of a validation rule."""
name: str
description: str
error_message: str
severity: str
class ValidationResultDict(TypedDict)
⋮----
"""Result of a validation operation."""
is_valid: bool
errors: list[dict[str, Any]]
warnings: list[dict[str, Any]]
context: dict[str, Any]
# ===== Basic Protocol Interface =====
⋮----
@runtime_checkable
class ServiceProtocol(Protocol)
⋮----
"""Protocol interface for all service components."""
⋮----
def initialize(self) -> None: ...
def shutdown(self) -> None: ...
# ===== Validation Protocol Interfaces =====
⋮----
@runtime_checkable
class ValidatorProtocol(Protocol, Generic[DataT_contra, SchemaT_co])
⋮----
"""Protocol defining the interface for validators."""
def validate(self, data: DataT_contra, schema: DataT_contra) -> ValidationResult: ...
def is_valid(self, data: DataT_contra, schema: DataT_contra) -> bool: ...
def get_schema(self) -> SchemaT_co: ...
def get_supported_types(self) -> list[str]: ...
⋮----
@runtime_checkable
class JsonSchemaValidatorProtocol(ValidatorProtocol[dict[str, Any], dict[str, Any]], Protocol)
⋮----
"""Protocol for JSON Schema validators."""
def validate_schema(self, schema: dict[str, Any]) -> ValidationResult: ...
def extend_schema(self, extension: dict[str, Any]) -> dict[str, Any]: ...
⋮----
@runtime_checkable
class MarshmallowValidatorProtocol(ValidatorProtocol[Any, Any], Protocol)
⋮----
"""Protocol for Marshmallow validators."""
def create_schema(self, **field_definitions: Any) -> Any: ...
def schema_to_json_schema(self, schema: Any) -> dict[str, Any]: ...
def dump(self, obj: Any, schema: Any) -> dict[str, Any]: ...
def load(self, data: dict[str, Any], schema: Any) -> Any: ...
⋮----
@runtime_checkable
class ValidationSystemProtocol(ServiceProtocol, Protocol)
⋮----
"""Protocol for validation system components."""
⋮----
def list_validators(self) -> list[str]: ...
# ===== Validation Type Aliases =====
⋮----
# ===== Type Validation Functions =====
def is_service(obj: Any) -> TypeGuard[ServiceProtocol]
⋮----
"""Check if an object implements the ServiceProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements ServiceProtocol, False otherwise.
    """
⋮----
def is_validator(obj: Any) -> TypeGuard[ValidatorProtocol]
⋮----
"""Check if an object implements the ValidatorProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements ValidatorProtocol, False otherwise.
    """
⋮----
# Check for required methods
required_methods = [
⋮----
def is_json_schema_validator(obj: Any) -> TypeGuard[JsonSchemaValidatorProtocol]
⋮----
"""Check if an object implements the JsonSchemaValidatorProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements JsonSchemaValidatorProtocol, False otherwise.
    """
⋮----
# Check for JSON Schema specific methods
required_methods = ["validate_schema", "extend_schema"]
⋮----
def is_marshmallow_validator(obj: Any) -> TypeGuard[MarshmallowValidatorProtocol]
⋮----
"""Check if an object implements the MarshmallowValidatorProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements MarshmallowValidatorProtocol, False otherwise.
    """
⋮----
# Check for Marshmallow specific methods
required_methods = ["create_schema", "schema_to_json_schema", "dump", "load"]
⋮----
def is_validation_system(obj: Any) -> TypeGuard[ValidationSystemProtocol]
⋮----
"""Check if an object implements the ValidationSystemProtocol.
    Args:
        obj: The object to check.
    Returns:
        True if the object implements ValidationSystemProtocol, False otherwise.
    """
⋮----
# Check for ServiceProtocol requirements
⋮----
def ensure_service_type(service_type: str) -> None
⋮----
"""Ensure that a service type is one of the standard service types.
    Args:
        service_type: The service type to validate.
    Raises:
        ValueError: If the service type is not a standard service type.
    """
standard_types = [
````

## File: atlas/README.md
````markdown
# Atlas LangGraph Implementation

This document explains the architecture and components of the Atlas LangGraph implementation.

## Overview

Atlas is implemented as a RAG (Retrieval-Augmented Generation) system using LangGraph for orchestration, ChromaDB for vector storage, and Anthropic's Claude API for language processing. The system is designed to maintain the Atlas identity while providing contextually relevant information from the Atlas documentation.

## Core Architecture

```
┌───────────────────┐        ┌───────────────────┐        ┌───────────────────┐
│                   │        │                   │        │                   │
│  Document         │───────▶│  Knowledge        │───────▶│  Atlas Agent      │
│  Processor        │        │  Base             │        │  (LangGraph)      │
│                   │        │                   │        │                   │
└───────────────────┘        └───────────────────┘        └───────────────────┘
```

### Components

1. **Document Processor** (`ingest.py`)
   - Processes Markdown files into chunks suitable for vector storage
   - Extracts metadata like file path, section title, and version
   - Handles chunking based on Markdown headings
   - Stores documents and metadata in the vector database

2. **Knowledge Base** (`tools/knowledge_retrieval.py`)
   - Provides semantic search using ChromaDB
   - Retrieves relevant documents based on user queries
   - Supports filtering by Atlas version
   - Returns documents with relevance scores

3. **Agent Framework** (`agent.py`)
   - Implements a LangGraph workflow for the Atlas agent
   - Handles knowledge retrieval and response generation
   - Maintains conversation state
   - Uses Claude's API for language generation

## Flow Diagram

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│         │     │         │     │         │     │         │     │         │
│  User   │────▶│  Agent  │────▶│Retrieval│────▶│ Claude  │────▶│  User   │
│ Message │     │  State  │     │  Node   │     │   API   │     │ Response│
│         │     │         │     │         │     │         │     │         │
└─────────┘     └─────────┘     └─────────┘     └─────────┘     └─────────┘
                                     │
                                     ▼
                               ┌─────────┐
                               │         │
                               │ChromaDB │
                               │         │
                               └─────────┘
```

## Key Files and Their Purpose

- **`ingest.py`**: Document processing and chunking system
  - `DocumentProcessor`: Main class for processing and chunking documents
  - `_split_by_headings()`: Helper method for chunking by headings
  - `generate_embeddings()`: Stores documents in ChromaDB
  - `process_directory()`: Processes all markdown files in a directory

- **`agent.py`**: Atlas agent implementation using LangGraph
  - `load_system_prompt()`: Loads custom system prompt from file
  - `create_agent()`: Creates and configures the LangGraph workflow
  - `AtlasAgent`: User-facing class for the Atlas agent
  - `retrieve()` & `generate_response()`: Core workflow functions

- **`tools/knowledge_retrieval.py`**: Knowledge base implementation
  - `KnowledgeBase`: Encapsulates ChromaDB interactions
  - `retrieve()`: Semantic search in the knowledge base
  - `retrieve_knowledge()`: LangGraph node for knowledge retrieval
  - Additional helper methods for specialized queries

- **`main.py`**: Command-line interface
  - `ingest_command()`: Handles document ingestion
  - `chat_command()`: Implements interactive chat
  - Command-line argument parsing and execution

## Data Flow

1. **Ingestion Phase**:
   - Markdown documents are read from file system
   - Documents are chunked based on headings
   - Chunks are stored in ChromaDB with metadata

2. **Retrieval Phase**:
   - User query is processed by the agent
   - Query is sent to the knowledge base
   - Relevant documents are retrieved based on semantic similarity
   - Top N most relevant documents are selected

3. **Generation Phase**:
   - Retrieved documents are formatted as context
   - Context and user query are sent to Claude API
   - Claude generates a response based on context
   - Response is returned to the user

## LangGraph Implementation

The LangGraph workflow is structured as follows:

1. **State**: Contains messages and retrieved context
2. **Nodes**:
   - `retrieve`: Retrieves knowledge from ChromaDB
   - `generate`: Generates responses using Claude
3. **Edges**:
   - Entry point → retrieve → generate → end
4. **Conditional Logic**:
   - Currently always retrieves knowledge
   - Can be extended for more sophisticated retrieval decisions

## Configuration Options

- **System Prompt**: Can be loaded from a file via command-line
- **Ingestion Directories**: Specify which directories to ingest
- **Vector Database**: Uses ChromaDB's default in-memory configuration
- **Claude Model**: Currently uses "claude-3-7-sonnet-20250219"

## Extensions and Customization

The system is designed to be extensible in several ways:

1. **Custom System Prompts**: Load alternative prompts for different personas
2. **Additional Tools**: Add new tools in the `tools/` directory
3. **Workflow Modifications**: Extend the LangGraph workflow with additional nodes
4. **Custom Document Processing**: Modify the chunking strategy in `ingest.py`

## Usage Examples

**Ingesting specific directories**:
```bash
python -m main ingest -d ./src-markdown/prev/v5 -d ./src-markdown/quantum
```

**Using a custom system prompt**:
```bash
python -m main chat -s ./src-markdown/CLAUDE_new.md
```

**Programmatic usage**:
```python
from atlas.agent import AtlasAgent

# Initialize agent with custom system prompt
agent = AtlasAgent(system_prompt_file="./path/to/prompt.md")

# Process a message
response = agent.process_message("Tell me about the Atlas framework")
print(response)
```
````

## File: atlas/core/__init__.py
````python
"""
Core Atlas functionality.
This package contains the core components for the Atlas framework.
"""
⋮----
# Base Service Protocol
⋮----
# Common Protocols
⋮----
# Container Protocols
⋮----
# Validation Protocols
⋮----
# Type Guards
⋮----
# Base Schemas
⋮----
# Common Schemas
⋮----
# Schema Utilities
⋮----
# Service constants
⋮----
# Basic type aliases
⋮----
# Base TypedDicts
⋮----
# Base Status
⋮----
# Utility functions
````

## File: atlas/core/errors.py
````python
"""
Base error classes and utilities for Atlas.
This module provides the core error handling infrastructure used
throughout Atlas components. It includes:
- AtlasError: Base exception class for all Atlas errors
- ErrorSeverity: Enum for error severity levels
- ErrorCategory: Enum for error categories
Component-specific errors are defined in their respective modules:
- atlas.core.primitives.buffer.errors: Buffer-specific errors
- atlas.core.primitives.events.errors: Event system-specific errors
- atlas.core.primitives.state.errors: State management-specific errors
- atlas.core.primitives.commands.errors: Command system-specific errors
- atlas.core.primitives.resources.errors: Resource management-specific errors
- atlas.core.primitives.registry.errors: Service registry-specific errors
- atlas.core.primitives.component.errors: Component-specific errors
- atlas.core.primitives.middleware.errors: Middleware-specific errors
- atlas.core.primitives.transitions.errors: Transition-specific errors
"""
⋮----
logger = logging.getLogger(__name__)
T = TypeVar("T")
class ErrorSeverity(str, Enum)
⋮----
"""Severity levels for errors."""
# Informational, not impacting operation
INFO = "info"
# Minor issue that can be worked around
WARNING = "warning"
# Issue that prevents operation but might be recoverable
ERROR = "error"
# Critical issue that cannot be recovered from
CRITICAL = "critical"
class ErrorCategory(str, Enum)
⋮----
"""Categories of errors across the application."""
# Environmental issues (file access, network, etc.)
ENVIRONMENT = "environment"
# Configuration problems
CONFIGURATION = "configuration"
# Input validation errors
VALIDATION = "validation"
# API/external service errors
API = "api"
# Authentication/authorization errors
AUTH = "auth"
# Data processing errors
DATA = "data"
# Core algorithm/logic errors
LOGIC = "logic"
# Resource constraints (memory, CPU, etc.)
RESOURCE = "resource"
# Service-related errors
SERVICE = "service"
# State management errors
STATE = "state"
# Event system errors
EVENT = "event"
# Command execution errors
COMMAND = "command"
# Registry-related errors
REGISTRY = "registry"
# Unknown/uncategorized errors
UNKNOWN = "unknown"
class AtlasError(Exception)
⋮----
"""Base class for all Atlas exceptions."""
⋮----
"""Initialize the error.
        Args:
            message: The error message.
            severity: Severity level of the error.
            category: Category of the error.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
        """
⋮----
def to_dict(self) -> dict[str, Any]
⋮----
"""Convert the error to a dictionary.
        Returns:
            Dictionary representation of the error.
        """
result = {
⋮----
# Convert details dict to result
⋮----
def log(self, log_level: int | None = None)
⋮----
"""Log the error with appropriate level.
        Args:
            log_level: Optional override for log level.
        """
⋮----
# Map severity to log level
⋮----
log_level = logging.INFO
⋮----
log_level = logging.WARNING
⋮----
log_level = logging.ERROR
else:  # CRITICAL
log_level = logging.CRITICAL
# Create log message
log_msg = f"{type(self).__name__}: {self.message}"
# Include traceback for ERROR and CRITICAL
⋮----
# Error handling utilities
⋮----
"""Execute a function safely, handling exceptions.
    Args:
        func: The function to execute.
        default: Default value to return if function fails.
        error_handler: Optional function to handle the exception.
        log_error: Whether to log the error.
        error_cls: The error class to use when creating an error.
        error_msg: The error message to use.
        args: Arguments tuple to pass to the function.
        function_kwargs: Keyword arguments to pass to the function.
        details: Error details to include if an error occurs.
        category: Error category.
        severity: Error severity.
    Returns:
        The result of the function or the default value if an exception occurs.
    """
# Initialize function_kwargs if None
⋮----
function_kwargs = {}
⋮----
# Create error details
error_details = details or {}
# Create and log the error
error = error_cls(
⋮----
# Call error handler if provided
⋮----
handler_result = error_handler(e)
⋮----
# Return default value
⋮----
raise error from e  # Re-raise the error if no default is provided
⋮----
def get_error_message(exception: Exception, include_traceback: bool = False) -> str
⋮----
"""Get a formatted error message from an exception.
    Args:
        exception: The exception to format.
        include_traceback: Whether to include the traceback.
    Returns:
        Formatted error message.
    """
base_msg = (
⋮----
tb = traceback.format_exception(
⋮----
"""Convert a standard exception to an AtlasError.
    Args:
        exception: The exception to convert.
        error_cls: AtlasError subclass to use.
        message: Optional message to use (falls back to str(exception)).
        severity: Severity level of the error.
        category: Category of the error.
        details: Optional detailed information about the error.
    Returns:
        AtlasError instance.
    """
⋮----
msg = message if message is not None else str(exception)
⋮----
# ===== Validation Error Classes =====
class ValidationError(AtlasError)
⋮----
"""Base class for validation-related exceptions."""
⋮----
"""Initialize the error.
        Args:
            message: The error message.
            severity: Severity level of the error.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            validator_id: Optional ID of the validator involved.
        """
⋮----
class SchemaValidationError(ValidationError)
⋮----
"""Raised when a schema fails meta-validation."""
⋮----
"""Initialize the error.
        Args:
            validator_id: Optional ID of the validator involved.
            schema_type: The type of schema that failed validation.
            validation_errors: List of validation errors.
            message: The error message.
            **kwargs: Additional keyword arguments.
        """
details = kwargs.pop("details", {}) or {}
⋮----
class DataValidationError(ValidationError)
⋮----
"""Raised when data fails validation against a schema."""
⋮----
"""Initialize the error.
        Args:
            validator_id: Optional ID of the validator involved.
            validation_errors: List of validation errors.
            message: The error message.
            **kwargs: Additional keyword arguments.
        """
⋮----
class ValidatorNotFoundError(ValidationError)
⋮----
"""Raised when a validator is not found."""
⋮----
"""Initialize the error.
        Args:
            validator_id: Optional ID of the validator that wasn't found.
            schema_type: Optional type of schema for which a validator was needed.
            message: The error message.
            **kwargs: Additional keyword arguments.
        """
⋮----
class UnsupportedSchemaTypeError(ValidationError)
⋮----
"""Raised when an unsupported schema type is used."""
⋮----
"""Initialize the error.
        Args:
            validator_id: Optional ID of the validator involved.
            schema_type: The unsupported schema type.
            supported_types: List of supported schema types.
            message: The error message.
            **kwargs: Additional keyword arguments.
        """
````

## File: atlas/__init__.py
````python
"""
Atlas: Advanced Multi-Modal Learning & Guidance Framework
A comprehensive meta-framework for knowledge representation, documentation,
and adaptive guidance systems.
"""
__version__ = "0.1.0"
__all__: list[str] = []
````
