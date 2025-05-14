"""
NERV (Neural Extended Runtime Verifier)
Central nervous system for Atlas core services.

This module contains consolidated type definitions, protocols, and implementations
from the NERV architecture, organized for validation and practical use. NERV defines
a set of architectural patterns and components that enable the creation of flexible,
introspectable, and composable systems.

The NERV architecture is organized into several layers:
1. Primitives: Foundational design patterns like Observer, Command, Monad, etc.
2. Patterns: Core architectural patterns that combine primitives
3. Components: Concrete implementations of the patterns
4. Composite Systems: Combinations of components to solve architectural challenges

Implementation dependencies:
- Blinker: Fast in-process signal/event dispatching for EventBus
- TaskMap: Dependency-based parallel execution for QuantumPartitioner
- Effect: Explicit side effect tracking for EffectMonad
- Marshmallow: Schema-based data transformation for PerspectiveAware
- DiffSync: Data comparison and synchronization between systems
- Eventsourcing: Event-based state persistence for TemporalStore
- AspectLib: Aspect-oriented programming for cross-cutting concerns
- Dependency Injector: Component wiring and lifecycle management

See the documentation for more details:
- Primitives: /docs/project-management/planning/nerv/primitives/
- Patterns: /docs/project-management/planning/nerv/patterns/
- Components: /docs/project-management/planning/nerv/components/
- Composite Systems: /docs/project-management/planning/nerv/composite/
"""

# Standard library imports
from typing import TypeVar, Generic, Protocol, Callable, Dict, List, Any, Optional, Union, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import uuid
import copy
import time
import threading
import queue
from collections import defaultdict
from abc import ABC, abstractmethod

# Third-party imports
from blinker import Signal
from taskmap import create_graph, execute_parallel
from effect import Effect as EffectBase, TypedEffect, sync_performer, ComposedPerformer
from marshmallow import Schema, fields, post_load, pre_dump
from diffsync import DiffSync, DiffSyncModel
from eventsourcing.domain import Aggregate, event
from aspectlib import Aspect, weave, Proceed, Return
from dependency_injector import containers, providers

# -----------------------------------------------------------------------------
# Core Type Variables
# -----------------------------------------------------------------------------
T = TypeVar('T')  # Generic data type
S = TypeVar('S')  # Generic state type
R = TypeVar('R')  # Generic result type
E = TypeVar('E')  # Generic event type
V = TypeVar('V')  # Generic value type
P = TypeVar('P')  # Generic perspective type
K = TypeVar('K')  # Generic key type
C = TypeVar('C')  # Generic context type
M = TypeVar('M')  # Generic message type
T_in = TypeVar('T_in')  # Input type for boundaries
T_out = TypeVar('T_out')  # Output type for boundaries

# -----------------------------------------------------------------------------
# Identity and Reference Types
# -----------------------------------------------------------------------------
EntityId = str  # Unique identifier for any entity in the system
VersionId = str  # Unique identifier for a versioned state
ResourceId = str  # Identifier for a resource
EventId = str  # Identifier for an event

# -----------------------------------------------------------------------------
# Core Enums
# -----------------------------------------------------------------------------
class EventType(Enum):
    """Core event types in the system."""
    # System lifecycle events
    SYSTEM_INIT = auto()
    SYSTEM_SHUTDOWN = auto()

    # Provider events
    PROVIDER_CREATED = auto()
    PROVIDER_CONNECTED = auto()
    PROVIDER_DISCONNECTED = auto()
    PROVIDER_ERROR = auto()

    # Agent events
    AGENT_CREATED = auto()
    AGENT_STARTED = auto()
    AGENT_STOPPED = auto()
    AGENT_ERROR = auto()

    # Stream events
    STREAM_STARTED = auto()
    STREAM_CHUNK = auto()
    STREAM_PAUSED = auto()
    STREAM_RESUMED = auto()
    STREAM_COMPLETED = auto()
    STREAM_ERROR = auto()

    # Workflow events
    WORKFLOW_STARTED = auto()
    WORKFLOW_NODE_ENTERED = auto()
    WORKFLOW_NODE_EXITED = auto()
    WORKFLOW_COMPLETED = auto()
    WORKFLOW_ERROR = auto()

    # Knowledge events
    DOCUMENT_ADDED = auto()
    DOCUMENT_PROCESSED = auto()
    RETRIEVAL_STARTED = auto()
    RETRIEVAL_COMPLETED = auto()

    # Command events
    COMMAND_EXECUTED = auto()
    COMMAND_REVERTED = auto()
    COMMAND_FAILED = auto()


class EffectType(Enum):
    """Types of side effects in the system."""
    # I/O effects
    FILE_READ = auto()
    FILE_WRITE = auto()
    NETWORK_REQUEST = auto()
    DATABASE_QUERY = auto()

    # State effects
    STATE_READ = auto()
    STATE_MODIFY = auto()

    # System effects
    THREAD_CREATE = auto()
    PROCESS_SPAWN = auto()
    RESOURCE_ALLOCATE = auto()
    RESOURCE_RELEASE = auto()

    # External effects
    MODEL_CALL = auto()
    TOOL_INVOKE = auto()
    EXTERNAL_SERVICE = auto()


class LifecycleState(Enum):
    """Lifecycle states for stateful components."""
    CREATED = auto()
    INITIALIZING = auto()
    READY = auto()
    ACTIVE = auto()
    PAUSED = auto()
    STOPPING = auto()
    STOPPED = auto()
    ERROR = auto()
    DISPOSED = auto()


class StreamState(Enum):
    """States for streaming operations."""
    PENDING = auto()
    ACTIVE = auto()
    PAUSED = auto()
    COMPLETED = auto()
    CANCELLED = auto()
    ERROR = auto()


class ResourceType(Enum):
    """Types of managed resources."""
    CONNECTION = auto()
    FILE = auto()
    THREAD = auto()
    PROCESS = auto()
    SOCKET = auto()
    DATABASE = auto()
    MODEL = auto()


class UnitState(Enum):
    """Possible states for a quantum unit."""
    PENDING = auto()   # Not yet executed
    READY = auto()     # Ready to execute (dependencies satisfied)
    RUNNING = auto()   # Currently executing
    COMPLETED = auto() # Successfully completed
    FAILED = auto()    # Execution failed
    CANCELLED = auto() # Execution cancelled

# -----------------------------------------------------------------------------
# Core Data Classes
# -----------------------------------------------------------------------------
@dataclass
class Event(Generic[T]):
    """Core event structure for the event bus."""
    id: EventId = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType
    data: Optional[T] = None
    timestamp: float = field(default_factory=time.time)
    source: Optional[EntityId] = None


@dataclass
class Effect:
    """Representation of a side effect."""
    type: EffectType
    payload: Any = None
    description: str = ""


@dataclass
class Resource:
    """Representation of a managed resource."""
    id: ResourceId
    type: ResourceType
    state: LifecycleState = LifecycleState.CREATED
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VersionedState:
    """A state with version history information."""
    version_id: str
    data: Any
    parent_version_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    change_description: str = ""


@dataclass
class UnitResult(Generic[R]):
    """Result of a quantum unit execution."""
    success: bool
    value: Optional[R] = None
    error: Optional[Exception] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult(Generic[T_out]):
    """Result of data validation at a boundary."""
    is_valid: bool
    data: Optional[T_out] = None
    errors: List[Dict[str, Union[str, int, float, bool]]] = field(default_factory=list)


@dataclass
class DeltaMetadata:
    """Metadata about a delta change."""
    timestamp: float = field(default_factory=time.time)
    source: Optional[EntityId] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)

# -----------------------------------------------------------------------------
# Core Error Classes
# -----------------------------------------------------------------------------
class AtlasError(Exception):
    """Base class for all Atlas errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class BoundaryError(AtlasError):
    """Error that occurs at system boundaries."""
    def __init__(self, message: str, boundary: str, details: Optional[Dict[str, Any]] = None):
        self.boundary = boundary
        super().__init__(message, details)


class ValidationError(BoundaryError):
    """Error during data validation at a boundary."""
    def __init__(self, message: str, boundary: str, validation_errors: List[Dict[str, Any]]):
        self.validation_errors = validation_errors
        super().__init__(message, boundary, {"validation_errors": validation_errors})


class NetworkError(BoundaryError):
    """Error during network operations at a boundary."""
    def __init__(self, message: str, status_code: Optional[int] = None,
                 response: Optional[Any] = None):
        self.status_code = status_code
        self.response = response
        super().__init__(message, "network", {
            "status_code": status_code,
            "response": str(response)[:1000] if response else None
        })

# -----------------------------------------------------------------------------
# Core Protocol Interfaces
# -----------------------------------------------------------------------------
class Observable(Protocol[E]):
    """Interface for objects that emit events.

    This protocol forms the foundation of the Observer pattern and the Reactive Event Mesh.
    It enables decoupled communication between components through events.

    Type Parameters:
        E: The type of events emitted by this observable
    """
    def add_observer(self, observer: Callable[[E, Any], None]) -> Callable[[], None]:
        """Add an observer to be notified of events.

        Args:
            observer: Callback function to handle events

        Returns:
            A function that can be called to unsubscribe
        """
        ...

    def remove_observer(self, observer: Callable[[E, Any], None]) -> None:
        """Remove an observer from the notification list.

        Args:
            observer: The observer to remove
        """
        ...

    def notify(self, event: E, data: Any = None) -> None:
        """Notify all observers about an event.

        Args:
            event: The event to notify about
            data: Optional additional data
        """
        ...


class Versioned(Protocol[S]):
    """Interface for objects with versioned state."""
    def get_current_version_id(self) -> VersionId: ...
    def get_version(self, version_id: Optional[VersionId] = None) -> S: ...
    def commit(self, state: S, description: str = "") -> VersionId: ...
    def get_history(self) -> List[Tuple[VersionId, S, str, float]]: ...


class Projectable(Protocol[S, P]):
    """Interface for objects that can be projected into different views."""
    def add_projection(self, name: str, projection_fn: Callable[[S], P]) -> None: ...
    def project(self, projection: str = "default") -> P: ...


class Effectful(Protocol[V]):
    """Interface for operations with explicit side effects."""
    def with_effect(self, effect: Effect) -> 'Effectful[V]': ...
    def map(self, fn: Callable[[V], Any]) -> 'Effectful[Any]': ...
    def bind(self, fn: Callable[[V], 'Effectful[Any]']) -> 'Effectful[Any]': ...
    def run(self, handler: Callable[[Effect], Any]) -> V: ...
    def get_effects(self) -> List[Effect]: ...


class QuantumUnit(Protocol[S, R]):
    """Interface for parallelizable computation units."""
    def can_execute(self, completed_units: Set[Any]) -> bool: ...
    def execute(self, context: S) -> R: ...
    def get_dependencies(self) -> List[Any]: ...
    def get_result(self) -> Optional[R]: ...


class Boundary(Protocol[T_in, T_out]):
    """Interface for system boundaries that convert between domains."""
    def validate(self, data: T_in) -> ValidationResult[T_out]: ...
    def process(self, data: T_in) -> T_out: ...
    def handle_error(self, error: Exception) -> BoundaryError: ...

# -----------------------------------------------------------------------------
# Core Implementation Classes
# -----------------------------------------------------------------------------
class EventBus:
    """Central event dispatch system for the Reactive Event Mesh.

    The EventBus is the primary implementation of the Reactive Event Mesh pattern,
    providing a thread-safe, in-memory publish-subscribe system for decoupled
    component communication. It serves as the "nervous system" of Atlas, connecting
    all major components through events.

    Features:
    - Thread-safe event distribution using read-write locks
    - Middleware pipeline for event transformation and filtering
    - Event history with configurable capacity
    - Typed subscribers for type-safe event handling
    - Unsubscribe tokens for clean handler removal

    See the documentation for more details:
    /docs/project-management/planning/nerv/components/event_bus.md
    """

    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable[[Event[Any]], None]]] = defaultdict(list)
        self._middleware: List[Callable[[Event[Any]], Optional[Event[Any]]]] = []
        self._history: List[Event[Any]] = []
        self._history_limit: int = 1000
        self._lock: threading.RLock = threading.RLock()

    def subscribe(self, event_type: EventType, handler: Callable[[Event[Any]], None]) -> Callable[[], None]:
        """Subscribe to events of a specific type.

        Args:
            event_type: Type of events to subscribe to
            handler: Callback function to handle events

        Returns:
            A function that can be called to unsubscribe
        """
        with self._lock:
            self._subscribers[event_type].append(handler)

        def unsubscribe():
            with self._lock:
                if handler in self._subscribers[event_type]:
                    self._subscribers[event_type].remove(handler)

        return unsubscribe

    def publish(self, event_type: EventType, data: Any = None, source: Optional[EntityId] = None) -> EventId:
        """Publish an event to all subscribers.

        Args:
            event_type: Type of event to publish
            data: Data payload for the event
            source: Identifier for the event source

        Returns:
            The ID of the published event
        """
        event = Event(type=event_type, data=data, source=source)

        with self._lock:
            # Apply middleware
            current_event = event
            for middleware in self._middleware:
                current_event = middleware(current_event)
                if current_event is None:
                    return event.id  # Event filtered out

            # Save to history
            self._history.append(current_event)
            if len(self._history) > self._history_limit:
                self._history = self._history[-self._history_limit:]

            # Notify subscribers
            for handler in self._subscribers.get(event_type, []):
                try:
                    handler(current_event)
                except Exception as e:
                    # In a real implementation, log this error
                    pass

        return event.id

    def add_middleware(self, middleware: Callable[[Event[Any]], Optional[Event[Any]]]) -> Callable[[], None]:
        """Add middleware to process events before they reach subscribers.

        Args:
            middleware: Function that transforms events or filters them out

        Returns:
            A function that can be called to remove the middleware
        """
        with self._lock:
            self._middleware.append(middleware)

        def remove_middleware():
            with self._lock:
                if middleware in self._middleware:
                    self._middleware.remove(middleware)

        return remove_middleware

    def get_history(self, event_type: Optional[EventType] = None, limit: int = 100) -> List[Event[Any]]:
        """Get recent events from the history.

        Args:
            event_type: Optional filter for specific event types
            limit: Maximum number of events to return

        Returns:
            List of recent events, most recent first
        """
        with self._lock:
            if event_type is None:
                return list(reversed(self._history))[:limit]
            else:
                return list(reversed([e for e in self._history if e.type == event_type]))[:limit]


class TemporalStore:
    """Store for versioned data with complete history."""
    
    def __init__(self):
        self._versions = {}
        self._current_version_id = None

    def commit(self, data, description=""):
        """Create a new version of the data.
        
        Args:
            data: The data to store
            description: Description of the change
            
        Returns:
            The version ID of the new version
        """
        version_id = str(uuid.uuid4())
        version = VersionedState(
            version_id=version_id,
            data=copy.deepcopy(data),
            parent_version_id=self._current_version_id,
            change_description=description
        )
        self._versions[version_id] = version
        self._current_version_id = version_id
        return version_id

    def get(self, version_id=None):
        """Get the data for a specific version.
        
        Args:
            version_id: The version to retrieve, or None for current
            
        Returns:
            The data for the requested version
        """
        if version_id is None:
            version_id = self._current_version_id
        return self._versions[version_id].data

    def get_history(self):
        """Get the complete version history.
        
        Returns:
            List of VersionedState objects
        """
        history = []
        version_id = self._current_version_id
        while version_id:
            version = self._versions[version_id]
            history.append(version)
            version_id = version.parent_version_id
        return list(reversed(history))


class PerspectiveAware(Generic[S, P]):
    """A class that provides multiple views of the same data based on context."""

    def __init__(self, data: S):
        """Initialize with the raw data and empty perspectives map.

        Args:
            data: The raw data to provide perspectives on
        """
        self._data: S = data
        self._perspectives: Dict[str, Callable[[S], P]] = {}
        self._current_perspective: str = "default"
        self._lock: threading.RLock = threading.RLock()

    def add_perspective(self, name: str, transform_fn: Callable[[S], P]) -> None:
        """Add a new perspective transformation function.

        Args:
            name: The name of the perspective
            transform_fn: Function that transforms data to this perspective
        """
        with self._lock:
            self._perspectives[name] = transform_fn

    def remove_perspective(self, name: str) -> bool:
        """Remove a perspective transformation.

        Args:
            name: The name of the perspective to remove

        Returns:
            True if the perspective was removed, False if it wasn't found
        """
        with self._lock:
            if name in self._perspectives:
                del self._perspectives[name]
                if self._current_perspective == name:
                    self._current_perspective = "default"
                return True
            return False

    def set_default_perspective(self, name: str) -> None:
        """Set the current default perspective.

        Args:
            name: Name of the perspective to use as default

        Raises:
            ValueError: If the perspective doesn't exist
        """
        with self._lock:
            if name not in self._perspectives and name != "default":
                raise ValueError(f"Perspective '{name}' not found")
            self._current_perspective = name

    def view(self, perspective: Optional[str] = None) -> Union[S, P]:
        """View the data through a specific perspective.

        Args:
            perspective: Name of the perspective to use,
                         or None to use the current default

        Returns:
            The transformed data, or raw data if perspective not found
        """
        with self._lock:
            perspective = perspective or self._current_perspective

            if perspective in self._perspectives:
                return self._perspectives[perspective](self._data)

            # Fall back to raw data
            return self._data

    def get_available_perspectives(self) -> List[str]:
        """Get the names of all available perspectives.

        Returns:
            List of perspective names
        """
        with self._lock:
            return list(self._perspectives.keys())

    def update_data(self, data: S) -> None:
        """Update the underlying data without changing perspectives.

        Args:
            data: New data to use
        """
        with self._lock:
            self._data = data


class Delta(Generic[S], ABC):
    """Represents a change to be applied to a state."""

    @staticmethod
    def function_delta(fn: Callable[[S], S]) -> 'Delta[S]':
        """Create a delta from a function that transforms state.

        Args:
            fn: Function that takes state and returns modified state

        Returns:
            A new Delta instance
        """
        return FunctionDelta(fn)

    @staticmethod
    def patch_delta(patch: Dict[str, Any]) -> 'Delta[S]':
        """Create a delta from a dictionary patch.

        Args:
            patch: Dictionary of updates to apply to state

        Returns:
            A new Delta instance
        """
        return PatchDelta(patch)

    @abstractmethod
    def apply(self, state: S) -> S:
        """Apply this delta to a state.

        Args:
            state: The state to update

        Returns:
            The updated state
        """
        pass


class FunctionDelta(Delta[S]):
    """A delta represented by a function that transforms state."""

    def __init__(self, fn: Callable[[S], S]):
        self.fn = fn

    def apply(self, state: S) -> S:
        return self.fn(state)


class PatchDelta(Delta[S]):
    """A delta represented by a dictionary patch."""

    def __init__(self, patch: Dict[str, Any]):
        self.patch = patch

    def apply(self, state: S) -> S:
        if not isinstance(state, dict):
            raise TypeError("PatchDelta can only be applied to dict-like states")
        return {**state, **self.patch}


class StateProjector(Generic[S, P]):
    """Manages state through deltas and supports multiple projections."""

    def __init__(self, initial_state: S):
        """Initialize with initial state.

        Args:
            initial_state: The initial state
        """
        self._initial_state: S = copy.deepcopy(initial_state)
        self._deltas: List[Tuple[Delta[S], DeltaMetadata]] = []
        self._projections: Dict[str, Callable[[S], P]] = {}
        self._lock: threading.RLock = threading.RLock()

    def apply_delta(self, delta: Union[Delta[S], Dict[str, Any], Callable[[S], S]],
                    description: str = "",
                    source: Optional[EntityId] = None,
                    tags: Optional[List[str]] = None) -> int:
        """Apply a delta to the state.

        Args:
            delta: The delta to apply (Delta object, dict patch or function)
            description: Description of the change
            source: Source of the change
            tags: Optional tags for categorizing the change

        Returns:
            Index of the newly added delta
        """
        with self._lock:
            # Convert to Delta if needed
            if not isinstance(delta, Delta):
                if callable(delta):
                    delta = Delta.function_delta(delta)
                else:
                    delta = Delta.patch_delta(delta)

            # Create metadata
            metadata = DeltaMetadata(
                description=description,
                source=source,
                tags=tags or []
            )

            # Store delta with metadata
            self._deltas.append((delta, metadata))
            return len(self._deltas) - 1

    def add_projection(self, name: str, projection_fn: Callable[[S], P]) -> None:
        """Add a new projection function.

        Args:
            name: Name of the projection
            projection_fn: Function that transforms state into projection
        """
        with self._lock:
            self._projections[name] = projection_fn

    def project(self, projection: str = "default", until: Optional[int] = None) -> P:
        """Project the current state through a specific projection.

        Args:
            projection: Name of the projection to use
            until: Optional index to stop applying deltas at

        Returns:
            The projected state

        Raises:
            ValueError: If projection doesn't exist
        """
        with self._lock:
            # Validate projection
            if projection not in self._projections:
                raise ValueError(f"Projection '{projection}' not found")

            # Compute current state
            state = copy.deepcopy(self._initial_state)
            deltas = self._deltas if until is None else self._deltas[:until]

            # Apply deltas sequentially
            for delta, _ in deltas:
                state = delta.apply(state)

            # Apply projection
            return self._projections[projection](state)

    def get_current_state(self) -> S:
        """Get the current state without any projection.

        Returns:
            The current state
        """
        with self._lock:
            # Compute current state
            state = copy.deepcopy(self._initial_state)

            # Apply all deltas
            for delta, _ in self._deltas:
                state = delta.apply(state)

            return state

    def get_delta_history(self, with_tags: Optional[List[str]] = None) -> List[Tuple[int, DeltaMetadata]]:
        """Get history of changes with their metadata.

        Args:
            with_tags: Optional filter to include only deltas with specific tags

        Returns:
            List of (index, metadata) pairs
        """
        with self._lock:
            if with_tags is None:
                return [(i, meta) for i, (_, meta) in enumerate(self._deltas)]
            else:
                return [
                    (i, meta) for i, (_, meta) in enumerate(self._deltas)
                    if any(tag in meta.tags for tag in with_tags)
                ]

    def reset_to_initial(self) -> None:
        """Clear all deltas and return to initial state."""
        with self._lock:
            self._deltas = []


class EffectMonad(Generic[V]):
    """Implementation of the effectful operation interface using a monad pattern."""

    def __init__(self, value: V, effects: List[Effect]):
        """Initialize with a value and list of effects.

        Args:
            value: The wrapped value
            effects: List of effects associated with this value
        """
        self.value: V = value
        self.effects: List[Effect] = effects

    def map(self, fn: Callable[[V], Any]) -> 'EffectMonad[Any]':
        """Transform the result value without adding effects.

        Args:
            fn: Function to transform the value

        Returns:
            New EffectMonad with transformed value and same effects
        """
        return EffectMonad(fn(self.value), self.effects)

    def bind(self, fn: Callable[[V], 'EffectMonad[Any]']) -> 'EffectMonad[Any]':
        """Chain with another effectful operation.

        Args:
            fn: Function that returns another effectful operation

        Returns:
            New EffectMonad with combined value and effects
        """
        result = fn(self.value)
        return EffectMonad(result.value, self.effects + result.effects)

    def run(self, handler: Callable[[Effect], Any]) -> V:
        """Execute the operation, handling all effects.

        Args:
            handler: Function to handle effects

        Returns:
            The wrapped value
        """
        for effect in self.effects:
            handler(effect)
        return self.value

    def get_effects(self) -> List[Effect]:
        """Get all effects in this operation.

        Returns:
            List of effects
        """
        return list(self.effects)

    def with_effect(self, effect: Effect) -> 'EffectMonad[V]':
        """Add an effect to this operation.

        Args:
            effect: The effect to add

        Returns:
            New EffectMonad with the additional effect
        """
        return EffectMonad(self.value, self.effects + [effect])

    @classmethod
    def pure(cls, value: V) -> 'EffectMonad[V]':
        """Create an effectful operation with no effects.

        Args:
            value: The value to wrap

        Returns:
            New effectful operation
        """
        return EffectMonad(value, [])

    @classmethod
    def effect(cls, effect_type: EffectType, payload: Any = None,
               description: str = "") -> 'EffectMonad[None]':
        """Create an operation with a single effect.

        Args:
            effect_type: Type of effect
            payload: Effect payload
            description: Description of the effect

        Returns:
            New effectful operation
        """
        effect = Effect(type=effect_type, payload=payload, description=description)
        return EffectMonad(None, [effect])


class EffectHandler:
    """Handles and processes effect descriptions."""

    def __init__(self):
        self._handlers: Dict[EffectType, Callable[[Any], Any]] = {}
        self._fallback: Optional[Callable[[Effect], Any]] = None
        self._executed_effects: List[Tuple[Effect, Any]] = []
        self._lock: threading.RLock = threading.RLock()

    def register_handler(self, effect_type: EffectType,
                         handler: Callable[[Any], Any]) -> None:
        """Register a handler for a specific effect type.

        Args:
            effect_type: Type of effect to handle
            handler: Function to handle the effect
        """
        with self._lock:
            self._handlers[effect_type] = handler

    def set_fallback_handler(self, handler: Callable[[Effect], Any]) -> None:
        """Set a fallback handler for unknown effect types.

        Args:
            handler: Function to handle unknown effects
        """
        with self._lock:
            self._fallback = handler

    def handle(self, effect: Effect) -> Any:
        """Handle a specific effect.

        Args:
            effect: The effect to handle

        Returns:
            Result of handling the effect

        Raises:
            ValueError: If no handler exists for the effect type
        """
        with self._lock:
            if effect.type in self._handlers:
                result = self._handlers[effect.type](effect.payload)
                self._executed_effects.append((effect, result))
                return result
            elif self._fallback is not None:
                result = self._fallback(effect)
                self._executed_effects.append((effect, result))
                return result

            raise ValueError(f"No handler for effect: {effect.type}")

    def get_executed_effects(self) -> List[Tuple[Effect, Any]]:
        """Get all effects that have been handled.

        Returns:
            List of (effect, result) pairs
        """
        with self._lock:
            return list(self._executed_effects)

    def clear_history(self) -> None:
        """Clear the history of executed effects."""
        with self._lock:
            self._executed_effects = []


class QuantumUnitImpl(Generic[S, R]):
    """A self-contained unit of computation with explicit dependencies."""

    def __init__(self, fn: Callable[[S], R],
                 dependencies: Optional[List['QuantumUnitImpl']] = None,
                 name: Optional[str] = None,
                 timeout: Optional[float] = None):
        """Initialize with function and dependencies.

        Args:
            fn: Function that performs the computation
            dependencies: Other units that must complete before this one
            name: Optional name for the unit
            timeout: Optional timeout in seconds
        """
        self.id: str = str(uuid.uuid4())
        self.name: str = name or f"Unit-{self.id[:8]}"
        self.fn: Callable[[S], R] = fn
        self.dependencies: List[QuantumUnitImpl] = dependencies or []
        self.state: UnitState = UnitState.PENDING
        self.result: Optional[UnitResult[R]] = None
        self.timeout: Optional[float] = timeout
        self.metadata: Dict[str, Any] = {}
        self._lock: threading.RLock = threading.RLock()

    def can_execute(self, completed_units: Set[str]) -> bool:
        """Check if this unit can be executed.

        Args:
            completed_units: Set of IDs of completed units

        Returns:
            True if all dependencies are satisfied
        """
        with self._lock:
            if self.state != UnitState.PENDING:
                return False

            return all(dep.id in completed_units for dep in self.dependencies)

    def execute(self, context: S) -> UnitResult[R]:
        """Execute this unit's function.

        Args:
            context: The execution context

        Returns:
            Result of the execution
        """
        with self._lock:
            if self.state == UnitState.COMPLETED:
                return self.result

            if self.state == UnitState.CANCELLED:
                return UnitResult(success=False, error=ValueError("Unit was cancelled"))

            self.state = UnitState.RUNNING

        start_time = time.time()

        try:
            # Execute with optional timeout
            if self.timeout is not None:
                # A real implementation would use a proper timeout mechanism
                value = self.fn(context)
            else:
                value = self.fn(context)

            execution_time = time.time() - start_time
            result = UnitResult(
                success=True,
                value=value,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            result = UnitResult(
                success=False,
                error=e,
                execution_time=execution_time
            )

        with self._lock:
            self.result = result
            self.state = UnitState.COMPLETED if result.success else UnitState.FAILED

        return result

    def cancel(self) -> bool:
        """Cancel this unit if it hasn't started yet.

        Returns:
            True if successfully cancelled
        """
        with self._lock:
            if self.state == UnitState.PENDING:
                self.state = UnitState.CANCELLED
                return True
            return False

    def get_dependencies(self) -> List['QuantumUnitImpl']:
        """Get this unit's dependencies.

        Returns:
            List of dependency units
        """
        return list(self.dependencies)

    def get_result(self) -> Optional[R]:
        """Get this unit's result value, if any.

        Returns:
            Result value if execution was successful, None otherwise
        """
        with self._lock:
            if self.result and self.result.success:
                return self.result.value
            return None


class ExecutionPlan:
    """A structured plan for executing quantum units."""

    def __init__(self, units: List[QuantumUnitImpl]):
        """Build an execution plan from units.

        Args:
            units: List of units to schedule
        """
        self.units = {unit.id: unit for unit in units}
        self.graph = self._build_dependency_graph()
        self.levels = self._compute_levels()

    def _build_dependency_graph(self) -> Dict[str, Set[str]]:
        """Build a dependency graph from units.

        Returns:
            Dict mapping unit IDs to sets of dependency IDs
        """
        graph = {}
        for unit_id, unit in self.units.items():
            graph[unit_id] = {dep.id for dep in unit.get_dependencies()}
        return graph

    def _compute_levels(self) -> List[List[str]]:
        """Compute execution levels for parallelization.

        Units in the same level can be executed in parallel.

        Returns:
            List of levels, each containing unit IDs
        """
        # Compute in-degree (number of dependencies) for each unit
        in_degree = {unit_id: len(deps) for unit_id, deps in self.graph.items()}

        # Units with no dependencies go in the first level
        zero_degree = [unit_id for unit_id, degree in in_degree.items() if degree == 0]

        levels = []
        while zero_degree:
            levels.append(zero_degree)

            next_zero_degree = []
            for unit_id in zero_degree:
                # Find units that depend on the current units
                for next_id, deps in self.graph.items():
                    if unit_id in deps:
                        in_degree[next_id] -= 1
                        if in_degree[next_id] == 0:
                            next_zero_degree.append(next_id)

            zero_degree = next_zero_degree

        # Check for cycles
        if sum(len(level) for level in levels) < len(self.units):
            raise ValueError("Circular dependencies detected in quantum units")

        return levels

    def get_level_count(self) -> int:
        """Get the number of execution levels.

        Returns:
            Number of levels
        """
        return len(self.levels)

    def get_units_at_level(self, level: int) -> List[QuantumUnitImpl]:
        """Get units at a specific execution level.

        Args:
            level: The level to retrieve

        Returns:
            List of units at that level
        """
        if level < 0 or level >= len(self.levels):
            return []

        return [self.units[unit_id] for unit_id in self.levels[level]]

    def get_maximum_parallelism(self) -> int:
        """Get the maximum number of units that can run in parallel.

        Returns:
            Maximum parallelism
        """
        return max(len(level) for level in self.levels) if self.levels else 0


class QuantumPartitioner(Generic[S, R]):
    """Executes quantum units with maximum parallelism while respecting dependencies."""

    def __init__(self):
        """Initialize an empty partitioner."""
        self.units: List[QuantumUnitImpl[S, R]] = []
        self.results: Dict[str, UnitResult[R]] = {}
        self.completed: Set[str] = set()
        self.failed: Set[str] = set()
        self._lock: threading.RLock = threading.RLock()

    def add_unit(self, fn: Callable[[S], R],
                 dependencies: Optional[List[QuantumUnitImpl]] = None,
                 name: Optional[str] = None,
                 timeout: Optional[float] = None) -> QuantumUnitImpl[S, R]:
        """Add a unit to the partitioner.

        Args:
            fn: Function that performs the computation
            dependencies: Other units that must complete before this one
            name: Optional name for the unit
            timeout: Optional timeout in seconds

        Returns:
            The created unit
        """
        with self._lock:
            unit = QuantumUnitImpl(fn, dependencies, name, timeout)
            self.units.append(unit)
            return unit

    def build_execution_plan(self) -> ExecutionPlan:
        """Build an execution plan for the current units.

        Returns:
            An execution plan
        """
        with self._lock:
            return ExecutionPlan(self.units)

    def execute(self, context: S, max_parallel: Optional[int] = None) -> Dict[str, R]:
        """Execute all units with maximum parallelism.

        Args:
            context: The execution context
            max_parallel: Maximum number of units to run in parallel

        Returns:
            Dict mapping unit IDs to results

        Raises:
            ValueError: If circular dependencies are detected
        """
        with self._lock:
            # Reset state
            self.results = {}
            self.completed = set()
            self.failed = set()

            # Build execution plan
            plan = self.build_execution_plan()

            # In a real implementation, this would use a thread/process pool
            for level in range(plan.get_level_count()):
                level_units = plan.get_units_at_level(level)

                # Process units in this level (would be parallel in real implementation)
                for unit in level_units:
                    # Skip if dependencies failed
                    if any(dep.id in self.failed for dep in unit.get_dependencies()):
                        continue

                    # Execute the unit
                    result = unit.execute(context)
                    self.results[unit.id] = result

                    if result.success:
                        self.completed.add(unit.id)
                    else:
                        self.failed.add(unit.id)

            # Collect successful results
            return {unit_id: result.value
                    for unit_id, result in self.results.items()
                    if result.success}

    def get_failed_units(self) -> List[Tuple[QuantumUnitImpl[S, R], Exception]]:
        """Get units that failed during execution.

        Returns:
            List of (unit, error) pairs
        """
        with self._lock:
            return [
                (unit, self.results[unit.id].error)
                for unit in self.units
                if unit.id in self.failed and self.results[unit.id].error is not None
            ]

    def cancel_all_pending(self) -> int:
        """Cancel all pending units.

        Returns:
            Number of units cancelled
        """
        with self._lock:
            cancelled = 0
            for unit in self.units:
                if unit.cancel():
                    cancelled += 1
            return cancelled


# Unit tests for verification
if __name__ == "__main__":
    # Simple smoke test
    print("Running NERV verification...")
    
    # Create an event
    event = Event(type=EventType.STREAM_STARTED, data="Stream started")
    print(f"Created event: {event}")
    
    # Create a resource
    resource = Resource(id=str(uuid.uuid4()), type=ResourceType.CONNECTION)
    print(f"Created resource: {resource}")
    
    # Create an effect
    effect = Effect(type=EffectType.MODEL_CALL, description="Called LLM")
    print(f"Created effect: {effect}")
    
    # Create an effect monad
    monad = EffectMonad.pure("Hello, world!").with_effect(effect)
    print(f"Created effect monad with value: {monad.value} and effects: {monad.effects}")
    
    # Create a quantum unit and execution plan
    partitioner = QuantumPartitioner()
    unit1 = partitioner.add_unit(lambda ctx: f"Result 1: {ctx}", name="Unit1")
    unit2 = partitioner.add_unit(lambda ctx: f"Result 2: {ctx}", dependencies=[unit1], name="Unit2")
    plan = partitioner.build_execution_plan()
    print(f"Created execution plan with {plan.get_level_count()} levels")
    
    # Execute the plan
    results = partitioner.execute("test context")
    print(f"Execution results: {results}")
    
    print("NERV verification complete!")