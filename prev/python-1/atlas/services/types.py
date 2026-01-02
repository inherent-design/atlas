"""
Type definitions for Atlas core services.

This module provides a centralized type system for Atlas core services, including:
- Type aliases for primitive and complex types
- Protocol interfaces for key components
- TypedDict structures for data schemas
- Generic types for flexible interfaces
- Type validation utilities
"""

from collections.abc import Callable
from threading import Event, RLock
from typing import (
    Any,
    Final,
    Generic,
    Literal,
    Protocol,
    Self,
    TypedDict,
    TypeGuard,
    TypeVar,
    runtime_checkable,
)

# ===== Standard Service Types =====
# Service type constants matching architecture plan
SERVICE_EVENT_SYSTEM: Final[str] = "event_system"
SERVICE_STATE_CONTAINER: Final[str] = "state_container"
SERVICE_COMMAND_SYSTEM: Final[str] = "command_system" 
SERVICE_BUFFER_SYSTEM: Final[str] = "buffer_system"
SERVICE_RESOURCE_MANAGER: Final[str] = "resource_manager"
SERVICE_TRANSITION_REGISTRY: Final[str] = "transition_registry"

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
type BufferSize = int  # Buffer size in items or bytes
type TokenRate = float  # Token rate for rate limiting
type CharCount = int  # Character count
type TimestampISO = str  # ISO format timestamp string
type Timestamp = float  # Unix timestamp (seconds since epoch)
type ThreadLock = RLock  # Thread lock type
type ThreadEvent = Event  # Thread event type

# ===== Literal Status Values =====
type ServiceStatus = Literal["initializing", "running", "paused", "stopped", "error"]
type ResourceState = Literal["initializing", "ready", "in_use", "released", "error"]
type BufferStatus = Literal["active", "paused", "closed"]
type EventSourceValue = str
type EventPriority = Literal["low", "normal", "high", "critical"]
type CommandStatus = Literal["pending", "executing", "completed", "failed", "cancelled"]
type MiddlewarePriority = int  # Higher numbers run first

# ===== TypedDicts for Core Data Structures =====
class ServiceConfigDict(TypedDict):
    """Configuration for a service component."""
    
    service_id: str
    name: str
    status: ServiceStatus
    capabilities: dict[str, Any]
    metadata: dict[str, Any]


class ResourceConfigDict(TypedDict):
    """Configuration for a managed resource."""
    
    resource_id: str
    type: str
    state: ResourceState
    owner_service: str | None
    acquisition_time: str | None
    release_time: str | None
    metadata: dict[str, Any]


class EventDataDict(TypedDict):
    """Event data structure for the event system."""
    
    event_id: str
    event_type: str
    source: str
    timestamp: str
    data: dict[str, Any]
    priority: EventPriority | None
    metadata: dict[str, Any]  # Added to match implementation


class SubscriptionConfigDict(TypedDict):
    """Configuration for an event subscription."""
    
    subscription_id: str
    event_type: str
    source_filter: str | None
    callback_name: str
    priority: EventPriority | None


class BufferConfigDict(TypedDict):
    """Base configuration for buffer services."""
    
    buffer_id: str | None
    buffer_type: str | None  # Added to match implementation
    max_size: int
    paused: bool
    closed: bool
    name: str | None


class RateLimitedBufferConfigDict(BufferConfigDict):
    """Configuration for rate-limited buffer services."""
    
    tokens_per_second: float | None
    chars_per_token: int
    initial_token_budget: float | None  # Added to match implementation


class BatchingBufferConfigDict(BufferConfigDict):
    """Configuration for batching buffer services."""
    
    batch_size: int | None
    batch_timeout: float | None
    batch_delimiter: str | None


class BufferItemDict(TypedDict):
    """Item stored in a buffer."""
    
    item_id: str
    timestamp: str
    data: dict[str, Any]
    metadata: dict[str, Any]


class StateDict(TypedDict):
    """State container data."""
    
    version: int
    data: dict[str, Any]
    timestamp: str
    metadata: dict[str, Any]


class TransitionConfigDict(TypedDict):
    """State transition configuration."""
    
    transition_id: str
    from_state: dict[str, Any]
    to_state: dict[str, Any]
    validator: str  # Name of validator function
    metadata: dict[str, Any]


class CommandConfigDict(TypedDict):
    """Command configuration."""
    
    command_id: str
    name: str
    parameters: dict[str, Any]
    target_service: str
    is_undoable: bool
    metadata: dict[str, Any]
    status: CommandStatus | None
    timestamp: str  # Added to match implementation


class CommandResultDict(TypedDict):
    """Command execution result."""
    
    result_id: str
    command_id: str
    success: bool
    data: dict[str, Any] | None
    error: str | None
    execution_time: float
    timestamp: str


class CommandHistoryEntryDict(TypedDict):
    """Command history entry in the command executor."""
    
    command: "CommandProtocol[Any]"
    context: dict[str, Any]
    result: Any | None
    success: bool
    start_time: float | None
    end_time: float | None
    execution_time: float | None
    error: str | None
    error_type: str | None


class ComponentConfigDict(TypedDict):
    """Service-enabled component configuration."""
    
    component_id: str
    component_type: str
    services: list[str]
    metadata: dict[str, Any]


# ===== Callable Type Aliases =====
type EventCallback = Callable[[dict[str, Any]], None]
type TransitionValidator = Callable[[dict[str, Any], dict[str, Any]], bool | str]
type CommandExecuteCallback = Callable[..., Any]
type UndoFunction = Callable[[], None]
type EventFilterFunction = Callable[[dict[str, Any]], bool | dict[str, Any]]
type ResourceAcquireCallback = Callable[[ResourceId, ServiceId], bool]
type ResourceReleaseCallback = Callable[[ResourceId], bool]
type BufferPushCallback = Callable[[Any], bool]
type BufferPopCallback = Callable[[], Any | None]
type ServiceFactory = Callable[[], Any]  # Factory function for creating services

# ===== Protocol Interfaces =====
@runtime_checkable
class ServiceProtocol(Protocol):
    """Protocol interface for all service components."""
    
    service_id: str
    name: str
    status: ServiceStatus
    
    def initialize(self) -> None: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def pause(self) -> None: ...
    def resume(self) -> None: ...
    def get_status(self) -> ServiceStatus: ...
    def get_capabilities(self) -> dict[str, Any]: ...
    def to_dict(self) -> ServiceConfigDict: ...


@runtime_checkable
class BufferProtocol(Protocol):
    """Protocol defining the interface for thread-safe buffers."""
    
    def push(self, item: dict[str, Any]) -> bool: ...
    def pop(self) -> dict[str, Any] | None: ...
    def peek(self) -> dict[str, Any] | None: ...
    def clear(self) -> None: ...
    def is_closed(self) -> bool: ...
    def close(self) -> None: ...
    def pause(self) -> Self: ...
    def resume(self) -> Self: ...
    
    @property
    def size(self) -> int: ...
    
    @property
    def max_size(self) -> int: ...
    
    @property
    def is_empty(self) -> bool: ...
    
    @property
    def is_full(self) -> bool: ...
    
    @property
    def is_paused(self) -> bool: ...


@runtime_checkable
class StreamingBufferProtocol(BufferProtocol, Protocol):
    """Extended protocol for buffers that support streaming operations."""
    
    def wait_until_not_empty(self, timeout: float | None = None) -> bool: ...
    def wait_until_not_full(self, timeout: float | None = None) -> bool: ...


@runtime_checkable
class RateLimitedBufferProtocol(StreamingBufferProtocol, Protocol):
    """Protocol for rate-limited buffers."""
    
    @property
    def tokens_per_second(self) -> float | None: ...
    
    @property
    def chars_per_token(self) -> int: ...
    
    @property
    def token_budget(self) -> float: ...
    
    def _calculate_token_cost(self, item: dict[str, Any]) -> float: ...


@runtime_checkable
class BatchingBufferProtocol(StreamingBufferProtocol, Protocol):
    """Protocol for batching buffers."""
    
    @property
    def batch_size(self) -> int | None: ...
    
    @property
    def batch_timeout(self) -> float | None: ...
    
    @property
    def batch_delimiter(self) -> str | None: ...
    
    def wait_for_batch(self, timeout: float | None = None) -> bool: ...
    
    def _create_batch(self, items: list[dict[str, Any]]) -> dict[str, Any]: ...


@runtime_checkable
class MiddlewareProtocol(Protocol, Generic[T]):
    """Protocol for middleware components."""
    
    def process(self, data: T) -> T | None: ...
    def get_name(self) -> str: ...
    def get_priority(self) -> int: ...


@runtime_checkable
class EventProtocol(Protocol):
    """Protocol for event system components."""
    
    def subscribe(
        self, event_type: str, callback: EventCallback, source_filter: str | None = None,
        priority: EventPriority | None = None
    ) -> SubscriptionId: ...
    
    def unsubscribe(self, subscription_id: SubscriptionId) -> bool: ...
    
    def publish(
        self, event_type: str, data: dict[str, Any], source: str | None = None,
        priority: EventPriority | None = None
    ) -> EventId: ...
    
    def get_events(
        self, event_type: str | None = None, source: str | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]: ...
    
    def get_event(self, event_id: EventId) -> dict[str, Any] | None: ...
    
    def clear_events(self) -> None: ...
    
    def add_middleware(self, middleware: "MiddlewareProtocol[dict[str, Any]]", priority: int = 0) -> None: ...
    
    def remove_middleware(self, middleware: "MiddlewareProtocol[dict[str, Any]]") -> bool: ...
    
    def get_stats(self) -> dict[str, Any]: ...


@runtime_checkable
class StateManagementProtocol(Protocol, Generic[StateT]):
    """Protocol for state management components."""
    
    def get_state(self, version: int | None = None) -> StateT: ...
    
    def update(
        self,
        new_data: dict[str, Any],
        validator: TransitionValidator | None = None,
        metadata: dict[str, Any] | None = None,
        merge: bool = True,
    ) -> StateT: ...
    
    def rollback(self, version: int) -> StateT: ...
    
    def get_history(self, limit: int | None = None) -> list[StateT]: ...
    
    def get_field(self, field_name: str) -> Any: ...
    
    def has_field(self, field_name: str) -> bool: ...
    
    @property
    def version(self) -> int: ...
    
    @property
    def data(self) -> dict[str, Any]: ...


@runtime_checkable
class CommandProtocol(Protocol[ResultT]):
    """Protocol for command pattern components."""
    
    command_id: str
    name: str
    parameters: dict[str, Any]
    target_service: str | None
    metadata: dict[str, Any]
    timestamp: str
    
    def execute(self, context: dict[str, Any] | None = None) -> ResultT: ...
    def undo(self) -> bool: ...
    def can_execute(self, context: dict[str, Any] | None = None) -> bool: ...
    
    @property
    def is_undoable(self) -> bool: ...
    
    def to_dict(self) -> dict[str, Any]: ...


@runtime_checkable
class CommandExecutorProtocol(Protocol[R]):
    """Protocol for command executor components."""
    
    def execute(self, command: CommandProtocol[R]) -> R: ...
    def undo_last(self) -> CommandId | None: ...
    def redo(self) -> CommandId | None: ...
    def clear_history(self) -> None: ...
    def get_history(self, limit: int | None = None) -> list[dict[str, Any]]: ...
    def get_results(self, limit: int | None = None) -> list[dict[str, Any]]: ...
    def get_command_result(self, command_id: CommandId) -> dict[str, Any] | None: ...
    def can_undo(self) -> bool: ...
    def can_redo(self) -> bool: ...
    def get_stats(self) -> dict[str, Any]: ...


@runtime_checkable
class ResourceProtocol(Protocol):
    """Protocol for resource management components."""
    
    resource_id: str
    type: str
    state: ResourceState
    owner_service: str | None
    acquisition_time: str | None
    release_time: str | None
    metadata: dict[str, Any]
    
    def acquire(self, owner_service: str) -> bool: ...
    def release(self) -> bool: ...
    def is_available(self) -> bool: ...
    def to_dict(self) -> ResourceConfigDict: ...


@runtime_checkable
class ResourceManagerProtocol(Protocol):
    """Protocol for resource manager components."""
    
    def create_resource(
        self, type: str, resource_id: str | None = None, metadata: dict[str, Any] | None = None
    ) -> ResourceProtocol: ...
    
    def get_resource(self, resource_id: ResourceId) -> ResourceProtocol | None: ...
    
    def mark_ready(self, resource_id: ResourceId) -> bool: ...
    
    def mark_error(self, resource_id: ResourceId, error: str | None = None) -> bool: ...
    
    def acquire_resource(self, resource_id: ResourceId, owner_service: str) -> bool: ...
    
    def release_resource(self, resource_id: ResourceId) -> bool: ...
    
    def delete_resource(self, resource_id: ResourceId) -> bool: ...
    
    def list_resources(self, type: str | None = None) -> list[dict[str, Any]]: ...


@runtime_checkable
class ServiceRegistryProtocol(Protocol):
    """Protocol for service registry components."""
    
    def register(self, service_type: str, service: Any) -> None: ...
    
    def register_factory(self, service_type: str, factory: ServiceFactory) -> None: ...
    
    def get(self, service_type: str) -> Any | None: ...
    
    def get_or_create(self, service_type: str) -> Any: ...
    
    def has(self, service_type: str) -> bool: ...
    
    def list_services(self) -> list[str]: ...
    
    @classmethod
    def get_instance(cls) -> "ServiceRegistryProtocol": ...


@runtime_checkable
class BufferSystemProtocol(Protocol):
    """Protocol for buffer system components."""
    
    def create_buffer(
        self, name: str | None = None, max_size: int = 1000, config: dict[str, Any] | None = None
    ) -> BufferProtocol: ...
    
    def get_buffer(self, name: str) -> BufferProtocol | None: ...
    
    def close_buffer(self, name: str) -> bool: ...
    
    def list_buffers(self) -> list[str]: ...
    
    def get_buffer_stats(self) -> dict[str, dict[str, int]]: ...


@runtime_checkable
class ServiceEnabledProtocol(Protocol):
    """Protocol for components that are service-enabled."""
    
    component_id: str
    
    @property
    def service_registry(self) -> ServiceRegistryProtocol: ...
    
    def get_service(self, service_type: str, required: bool = True) -> Any: ...
    def initialize_services(self) -> None: ...


@runtime_checkable
class TransitionValidatorProtocol(Protocol):
    """Protocol for state transition validators."""
    
    name: str
    description: str
    
    def validate(self, from_state: dict[str, Any], to_state: dict[str, Any]) -> bool | str: ...


@runtime_checkable
class TransitionRegistryProtocol(Protocol):
    """Protocol for transition registry components."""
    
    def register_validator(self, validator: TransitionValidatorProtocol) -> None: ...
    def get_validator(self, name: str) -> TransitionValidatorProtocol | None: ...
    def register_transition_rule(
        self, from_state: str, to_state: str, validator: str | TransitionValidatorProtocol
    ) -> None: ...
    def get_transition_validators(
        self, from_state: str, to_state: str
    ) -> list[TransitionValidatorProtocol]: ...
    def validate_transition(
        self,
        from_state_name: str,
        to_state_name: str,
        from_state: dict[str, Any],
        to_state: dict[str, Any],
    ) -> tuple[bool, str]: ...
    def get_allowed_transitions(self, from_state: str) -> set[str]: ...


# ===== TypeGuard Functions =====
def is_service(obj: Any) -> TypeGuard[ServiceProtocol]:
    """Check if an object implements the ServiceProtocol.
    
    Args:
        obj: The object to check.
        
    Returns:
        True if the object implements ServiceProtocol, False otherwise.
    """
    return isinstance(obj, ServiceProtocol)


def is_buffer(obj: Any) -> TypeGuard[BufferProtocol]:
    """Check if an object implements the BufferProtocol.
    
    Args:
        obj: The object to check.
        
    Returns:
        True if the object implements BufferProtocol, False otherwise.
    """
    return isinstance(obj, BufferProtocol)


def is_streaming_buffer(obj: Any) -> TypeGuard[StreamingBufferProtocol]:
    """Check if an object implements the StreamingBufferProtocol.
    
    Args:
        obj: The object to check.
        
    Returns:
        True if the object implements StreamingBufferProtocol, False otherwise.
    """
    return isinstance(obj, StreamingBufferProtocol)


def is_rate_limited_buffer(obj: Any) -> TypeGuard[RateLimitedBufferProtocol]:
    """Check if an object implements the RateLimitedBufferProtocol.
    
    Args:
        obj: The object to check.
        
    Returns:
        True if the object implements RateLimitedBufferProtocol, False otherwise.
    """
    return isinstance(obj, RateLimitedBufferProtocol)


def is_batching_buffer(obj: Any) -> TypeGuard[BatchingBufferProtocol]:
    """Check if an object implements the BatchingBufferProtocol.
    
    Args:
        obj: The object to check.
        
    Returns:
        True if the object implements BatchingBufferProtocol, False otherwise.
    """
    return isinstance(obj, BatchingBufferProtocol)


def is_event_system(obj: Any) -> TypeGuard[EventProtocol]:
    """Check if an object implements the EventProtocol.
    
    Args:
        obj: The object to check.
        
    Returns:
        True if the object implements EventProtocol, False otherwise.
    """
    return isinstance(obj, EventProtocol)


def is_state_container(obj: Any) -> TypeGuard[StateManagementProtocol]:
    """Check if an object implements the StateManagementProtocol.
    
    Args:
        obj: The object to check.
        
    Returns:
        True if the object implements StateManagementProtocol, False otherwise.
    """
    return isinstance(obj, StateManagementProtocol)


def is_command(obj: Any) -> TypeGuard[CommandProtocol]:
    """Check if an object implements the CommandProtocol.
    
    Args:
        obj: The object to check.
        
    Returns:
        True if the object implements CommandProtocol, False otherwise.
    """
    return isinstance(obj, CommandProtocol)


def is_command_executor(obj: Any) -> TypeGuard[CommandExecutorProtocol]:
    """Check if an object implements the CommandExecutorProtocol.
    
    Args:
        obj: The object to check.
        
    Returns:
        True if the object implements CommandExecutorProtocol, False otherwise.
    """
    return isinstance(obj, CommandExecutorProtocol)


def is_resource(obj: Any) -> TypeGuard[ResourceProtocol]:
    """Check if an object implements the ResourceProtocol.
    
    Args:
        obj: The object to check.
        
    Returns:
        True if the object implements ResourceProtocol, False otherwise.
    """
    return isinstance(obj, ResourceProtocol)


def is_resource_manager(obj: Any) -> TypeGuard[ResourceManagerProtocol]:
    """Check if an object implements the ResourceManagerProtocol.
    
    Args:
        obj: The object to check.
        
    Returns:
        True if the object implements ResourceManagerProtocol, False otherwise.
    """
    return isinstance(obj, ResourceManagerProtocol)


def is_middleware(obj: Any) -> TypeGuard[MiddlewareProtocol]:
    """Check if an object implements the MiddlewareProtocol.
    
    Args:
        obj: The object to check.
        
    Returns:
        True if the object implements MiddlewareProtocol, False otherwise.
    """
    return isinstance(obj, MiddlewareProtocol)


def is_service_registry(obj: Any) -> TypeGuard[ServiceRegistryProtocol]:
    """Check if an object implements the ServiceRegistryProtocol.
    
    Args:
        obj: The object to check.
        
    Returns:
        True if the object implements ServiceRegistryProtocol, False otherwise.
    """
    return isinstance(obj, ServiceRegistryProtocol)


def is_buffer_system(obj: Any) -> TypeGuard[BufferSystemProtocol]:
    """Check if an object implements the BufferSystemProtocol.
    
    Args:
        obj: The object to check.
        
    Returns:
        True if the object implements BufferSystemProtocol, False otherwise.
    """
    return isinstance(obj, BufferSystemProtocol)


def is_service_enabled(obj: Any) -> TypeGuard[ServiceEnabledProtocol]:
    """Check if an object implements the ServiceEnabledProtocol.
    
    Args:
        obj: The object to check.
        
    Returns:
        True if the object implements ServiceEnabledProtocol, False otherwise.
    """
    return isinstance(obj, ServiceEnabledProtocol)


def is_transition_validator(obj: Any) -> TypeGuard[TransitionValidatorProtocol]:
    """Check if an object implements the TransitionValidatorProtocol.
    
    Args:
        obj: The object to check.
        
    Returns:
        True if the object implements TransitionValidatorProtocol, False otherwise.
    """
    return isinstance(obj, TransitionValidatorProtocol)


def is_transition_registry(obj: Any) -> TypeGuard[TransitionRegistryProtocol]:
    """Check if an object implements the TransitionRegistryProtocol.
    
    Args:
        obj: The object to check.
        
    Returns:
        True if the object implements TransitionRegistryProtocol, False otherwise.
    """
    return isinstance(obj, TransitionRegistryProtocol)


# ===== Validation Functions =====

def validate_event_type(event_type: str) -> bool:
    """Validate an event type string format.
    
    Args:
        event_type: The event type to validate.
        
    Returns:
        True if the event type is valid, False otherwise.
    """
    if not event_type:
        return False
        
    parts = event_type.split(".")
    return all(all(c.isalnum() or c == "_" for c in part) for part in parts)


def validate_subscription_pattern(pattern: str) -> bool:
    """Validate a subscription pattern format.
    
    Args:
        pattern: The subscription pattern to validate.
        
    Returns:
        True if the pattern is valid, False otherwise.
    """
    if not pattern:
        return False
        
    parts = pattern.split(".")
    for part in parts:
        if part != "*" and not all(c.isalnum() or c == "_" for c in part):
            return False
            
    return True


def ensure_service_type(service_type: str) -> None:
    """Ensure that a service type is one of the standard service types.
    
    Args:
        service_type: The service type to validate.
        
    Raises:
        ValueError: If the service type is not a standard service type.
    """
    standard_types = [
        SERVICE_EVENT_SYSTEM,
        SERVICE_STATE_CONTAINER,
        SERVICE_COMMAND_SYSTEM,
        SERVICE_BUFFER_SYSTEM,
        SERVICE_RESOURCE_MANAGER,
        SERVICE_TRANSITION_REGISTRY,
    ]
    
    if service_type not in standard_types:
        raise ValueError(f"Unknown service type: {service_type}. Should be one of: {standard_types}")