---

title: Core Services

---


# Core Services Architecture

This document details the architecture for the core services module in Atlas, providing standardized interfaces for service components across the framework.

## Overview

The `atlas.core.services` module will provide a comprehensive set of interfaces and implementations for key architectural patterns used throughout Atlas. These components will enable unified patterns for streaming, state management, resource lifecycle, and command execution.

## Service Module Structure

```
atlas/core/services/
  ├── __init__.py       # Module exports
  ├── base.py           # Base service interfaces
  ├── buffer.py         # Thread-safe buffer implementations
  ├── state.py          # State management patterns
  ├── commands.py       # Command pattern implementation
  ├── concurrency.py    # Thread safety utilities
  └── resources.py      # Resource lifecycle management
```

## Interface Definitions

### 1. Base Interfaces (base.py)

```python
from abc import ABC, abstractmethod
from typing import Callable, Dict, Any, Optional, TypeVar, Generic

S = TypeVar('S')  # State type
T = TypeVar('T')  # Content type

class Controllable(ABC):
    """
    Interface for components that support control operations.

    This interface defines standard control operations that can be
    applied to various components throughout the system.
    """

    @property
    @abstractmethod
    def state(self) -> S:
        """Get the current state of the component."""
        pass

    @property
    @abstractmethod
    def can_pause(self) -> bool:
        """Whether this component supports pausing."""
        pass

    @property
    @abstractmethod
    def can_resume(self) -> bool:
        """Whether this component can be resumed from a paused state."""
        pass

    @property
    @abstractmethod
    def can_cancel(self) -> bool:
        """Whether this component supports cancellation."""
        pass

    @abstractmethod
    def pause(self) -> bool:
        """
        Pause the component if supported.

        Returns:
            bool: True if the component was paused, False otherwise.
        """
        pass

    @abstractmethod
    def resume(self) -> bool:
        """
        Resume the component if paused.

        Returns:
            bool: True if the component was resumed, False otherwise.
        """
        pass

    @abstractmethod
    def cancel(self) -> bool:
        """
        Cancel the component if supported.

        Returns:
            bool: True if the component was cancelled, False otherwise.
        """
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get component performance metrics.

        Returns:
            Dict containing metrics such as processing rates, throughput, etc.
        """
        pass

    @abstractmethod
    def register_state_change_callback(self, callback: Callable[[S], None]) -> None:
        """
        Register a callback to be called when the state changes.

        Args:
            callback: Function to call with the new state.
        """
        pass


class ProgressReporter(ABC):
    """Interface for components that report progress."""

    @property
    @abstractmethod
    def progress(self) -> float:
        """Get the current progress as a value between 0.0 and 1.0."""
        pass

    @abstractmethod
    def register_progress_callback(self, callback: Callable[[float], None]) -> None:
        """
        Register a callback to be called when progress changes.

        Args:
            callback: Function to call with the new progress value.
        """
        pass


class DataProducer(Generic[T], ABC):
    """Interface for components that produce data."""

    @abstractmethod
    def register_data_callback(self, callback: Callable[[T], None]) -> None:
        """
        Register a callback to be called when new data is produced.

        Args:
            callback: Function to call with the new data.
        """
        pass


class ServiceComponent(ABC):
    """
    Base interface for all service components.

    Defines the common lifecycle methods that all service components
    should implement.
    """

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the component.

        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        pass

    @abstractmethod
    def dispose(self) -> None:
        """
        Clean up resources used by the component.

        This method should be idempotent and safe to call multiple times.
        """
        pass

    def __enter__(self) -> 'ServiceComponent':
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.dispose()
```

### 2. Buffer Interface (buffer.py)

```python
from abc import ABC, abstractmethod
from typing import Optional, Generic, TypeVar, List, Callable, Any

T = TypeVar('T')  # Generic type for buffer contents

class Buffer(Generic[T], ABC):
    """
    Thread-safe buffer for storing and retrieving content with flow control.

    This interface defines a thread-safe buffer with pause/resume functionality
    and optional capacity constraints. It's designed for producer-consumer
    scenarios where flow control is important.
    """

    @property
    @abstractmethod
    def is_paused(self) -> bool:
        """Whether the buffer is currently paused."""
        pass

    @property
    @abstractmethod
    def is_closed(self) -> bool:
        """Whether the buffer has been closed."""
        pass

    @property
    @abstractmethod
    def size(self) -> int:
        """Current size of the buffer."""
        pass

    @property
    @abstractmethod
    def capacity(self) -> Optional[int]:
        """Maximum capacity of the buffer or None if unbounded."""
        pass

    @abstractmethod
    def add(self, item: T) -> bool:
        """
        Add an item to the buffer.

        Args:
            item: The item to add to the buffer.

        Returns:
            bool: True if the item was added, False if the buffer is closed or full.
        """
        pass

    @abstractmethod
    def get(self, timeout: Optional[float] = None) -> Optional[T]:
        """
        Get an item from the buffer, waiting if none is available.

        Args:
            timeout: How long to wait for an item in seconds, or None to wait indefinitely.

        Returns:
            The next item from the buffer, or None if timeout occurred or buffer is closed.
        """
        pass

    @abstractmethod
    def peek(self) -> Optional[T]:
        """
        View the next item without removing it.

        Returns:
            The next item or None if the buffer is empty.
        """
        pass

    @abstractmethod
    def pause(self) -> None:
        """Pause the buffer, preventing consumers from getting content."""
        pass

    @abstractmethod
    def resume(self) -> None:
        """Resume the buffer, allowing consumers to get content."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the buffer, preventing further additions."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all content from the buffer."""
        pass

    @abstractmethod
    def register_item_callback(self, callback: Callable[[T], None]) -> None:
        """
        Register a callback to be called when a new item is added.

        Args:
            callback: Function to call with each new item.
        """
        pass


class MemoryBuffer(Buffer[T]):
    """Basic in-memory implementation of Buffer interface."""
    pass


class RateLimitedBuffer(Buffer[T]):
    """Buffer with rate limiting capabilities."""
    pass


class BatchingBuffer(Buffer[T]):
    """Buffer that accumulates items until batch criteria are met."""
    pass
```

### 3. State Management Interface (state.py)

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Dict, Any, List, Optional, TypeVar, Generic

S = TypeVar('S', bound=Enum)  # State type variable
E = TypeVar('E')  # Event type variable

class StateTransitionError(Exception):
    """Error raised when a state transition is invalid."""
    pass


class StateMachine(Generic[S, E], ABC):
    """
    Generic state machine interface for managing component states.

    This interface defines a state machine with controlled transitions
    and event-based notifications.
    """

    @property
    @abstractmethod
    def state(self) -> S:
        """Get the current state."""
        pass

    @abstractmethod
    def can_transition_to(self, target_state: S) -> bool:
        """
        Check if a transition to the target state is valid.

        Args:
            target_state: The state to check transition to.

        Returns:
            bool: True if the transition is valid, False otherwise.
        """
        pass

    @abstractmethod
    def transition_to(self, target_state: S, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Transition to the target state if valid.

        Args:
            target_state: The state to transition to.
            data: Optional data associated with the transition.

        Returns:
            bool: True if the transition was successful, False otherwise.

        Raises:
            StateTransitionError: If the transition is invalid.
        """
        pass

    @abstractmethod
    def register_state_change_callback(self, callback: Callable[[S, Dict[str, Any]], None]) -> None:
        """
        Register a callback to be called when the state changes.

        Args:
            callback: Function to call with new state and transition data.
        """
        pass

    @abstractmethod
    def handle_event(self, event: E, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Process an event that may trigger a state transition.

        Args:
            event: The event to process.
            data: Optional data associated with the event.

        Returns:
            bool: True if the event triggered a transition, False otherwise.
        """
        pass

    @abstractmethod
    def get_allowed_transitions(self) -> Dict[S, List[S]]:
        """
        Get all allowed state transitions.

        Returns:
            Dict mapping states to lists of states they can transition to.
        """
        pass


class EventDrivenStateMachine(StateMachine[S, E]):
    """Implementation of a state machine driven by events."""
    pass
```

### 4. Command Pattern Interface (commands.py)

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Generic, TypeVar, List, Optional, Callable

S = TypeVar('S')  # State type
R = TypeVar('R')  # Result type

class Command(Generic[S, R], ABC):
    """
    Command pattern interface for state-modifying operations.

    This interface defines a command that can be executed against a state,
    with execution tracking and optional undo capabilities.
    """

    @abstractmethod
    def execute(self, state: S) -> R:
        """
        Execute the command against the state, returning a result.

        Args:
            state: The state to execute against.

        Returns:
            The result of the command execution.
        """
        pass

    @abstractmethod
    def can_execute(self, state: S) -> bool:
        """
        Check if the command can be executed in the current state.

        Args:
            state: The state to check.

        Returns:
            bool: True if the command can be executed, False otherwise.
        """
        pass

    @property
    @abstractmethod
    def is_undoable(self) -> bool:
        """Whether this command can be undone."""
        pass

    @abstractmethod
    def undo(self, state: S) -> None:
        """
        Undo the command if possible.

        Args:
            state: The state to undo against.

        Raises:
            NotImplementedError: If the command is not undoable.
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this command.

        Returns:
            Dict containing command metadata.
        """
        return {}


class CommandProcessor(Generic[S]):
    """
    Processes commands and maintains execution history.

    This class is responsible for executing commands against a state,
    maintaining a command history, and providing undo capabilities.
    """

    def __init__(self, initial_state: S):
        """
        Initialize the command processor.

        Args:
            initial_state: The initial state to process commands against.
        """
        self.state = initial_state
        self.history: List[Command] = []
        self.observers: List[Callable[[Command], None]] = []

    def execute(self, command: Command[S, R]) -> R:
        """
        Execute a command and record it in history.

        Args:
            command: The command to execute.

        Returns:
            The result of command execution.

        Raises:
            ValueError: If the command cannot be executed in the current state.
        """
        if not command.can_execute(self.state):
            raise ValueError(f"Command {command} cannot be executed in current state")

        result = command.execute(self.state)
        self.history.append(command)
        self._notify_observers(command)
        return result

    def undo_last(self) -> Optional[Command]:
        """
        Undo the last undoable command if any.

        Returns:
            The command that was undone, or None if no undoable commands.
        """
        # Find last undoable command
        for i in range(len(self.history) - 1, -1, -1):
            cmd = self.history[i]
            if cmd.is_undoable:
                cmd.undo(self.state)
                return cmd
        return None

    def add_observer(self, observer: Callable[[Command], None]) -> None:
        """
        Add an observer for command execution.

        Args:
            observer: Function to call with each executed command.
        """
        self.observers.append(observer)

    def _notify_observers(self, command: Command) -> None:
        """
        Notify observers about command execution.

        Args:
            command: The command that was executed.
        """
        for observer in self.observers:
            observer(command)


class PauseCommand(Command[S, bool]):
    """Example command to pause a controllable component."""
    pass


class ResumeCommand(Command[S, bool]):
    """Example command to resume a controllable component."""
    pass


class CancelCommand(Command[S, bool]):
    """Example command to cancel a controllable component."""
    pass
```

### 5. Concurrency Utilities (concurrency.py)

```python
from abc import ABC, abstractmethod
from typing import Optional, Callable, Any, TypeVar, Generic, List

T = TypeVar('T')  # Return type for callable

class CancellationToken:
    """
    Token for coordinating cancellation across threads.

    This class provides a way to request cancellation of operations
    across different threads, with callback notification.
    """

    def __init__(self):
        """Initialize a new cancellation token."""
        self._cancelled = False
        self._callbacks = []

    @property
    def is_cancelled(self) -> bool:
        """Whether cancellation has been requested."""
        return self._cancelled

    def cancel(self) -> None:
        """Request cancellation."""
        if not self._cancelled:
            self._cancelled = True
            for callback in self._callbacks:
                try:
                    callback()
                except Exception:
                    pass  # Swallow errors in callbacks

    def register_callback(self, callback: Callable[[], None]) -> None:
        """
        Register a callback to be called when cancellation is requested.

        Args:
            callback: Function to call on cancellation.
        """
        if self._cancelled:
            # If already cancelled, call immediately
            try:
                callback()
            except Exception:
                pass
        else:
            self._callbacks.append(callback)

    def throw_if_cancelled(self) -> None:
        """
        Throw OperationCanceledException if cancellation has been requested.

        Raises:
            OperationCanceledException: If cancellation has been requested.
        """
        if self._cancelled:
            raise OperationCanceledException()


class OperationCanceledException(Exception):
    """Exception thrown when an operation is cancelled."""
    pass


class ThreadSafeCounter:
    """Thread-safe counter implementation."""
    pass


class AsyncResult(Generic[T]):
    """
    A thread-safe container for an asynchronously computed value.

    This is similar to Future/Promise but simplified for our needs.
    """

    def __init__(self):
        """Initialize a new AsyncResult."""
        self._result = None
        self._exception = None
        self._is_set = False
        self._callbacks = []

    def set_result(self, result: T) -> None:
        """
        Set the result value.

        Args:
            result: The result value.
        """
        self._result = result
        self._is_set = True
        self._notify_callbacks()

    def set_exception(self, exception: Exception) -> None:
        """
        Set an exception as the result.

        Args:
            exception: The exception that occurred.
        """
        self._exception = exception
        self._is_set = True
        self._notify_callbacks()

    def get(self, timeout: Optional[float] = None) -> T:
        """
        Get the result, waiting if it's not yet available.

        Args:
            timeout: How long to wait in seconds, or None to wait indefinitely.

        Returns:
            The result value.

        Raises:
            Exception: If an exception was set as the result.
            TimeoutError: If the timeout expires before the result is available.
        """
        # Implementation details
        pass

    def add_done_callback(self, callback: Callable[[Any], None]) -> None:
        """
        Add a callback to be called when the result becomes available.

        Args:
            callback: Function to call with the result.
        """
        # Implementation details
        pass

    def _notify_callbacks(self) -> None:
        """Notify all registered callbacks."""
        # Implementation details
        pass


class ThreadPool:
    """
    Simple thread pool for executing tasks.

    This provides a simplified subset of concurrent.futures.ThreadPoolExecutor
    functionality focused on our specific needs.
    """
    pass
```

### 6. Resource Management Interface (resources.py)

```python
from abc import ABC, abstractmethod
from typing import Optional, Callable, List, Dict, Any, TypeVar, Generic

T = TypeVar('T')  # Resource type

class ManagedResource(ABC):
    """
    Interface for resources with lifecycle management.

    This interface defines standard lifecycle operations for resources
    that need initialization and cleanup.
    """

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Whether the resource has been initialized."""
        pass

    @property
    @abstractmethod
    def is_disposed(self) -> bool:
        """Whether the resource has been disposed."""
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the resource.

        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        pass

    @abstractmethod
    def dispose(self) -> None:
        """
        Clean up the resource.

        This method should be idempotent and safe to call multiple times.
        """
        pass

    def __enter__(self) -> 'ManagedResource':
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.dispose()


class ResourceManager(ABC):
    """
    Manager for tracking and coordinating multiple resources.

    This interface defines operations for managing multiple resources
    with dependency tracking and coordinated initialization/disposal.
    """

    @abstractmethod
    def register_resource(self, resource: ManagedResource,
                        dependencies: Optional[List[ManagedResource]] = None) -> None:
        """
        Register a resource with the manager.

        Args:
            resource: The resource to register.
            dependencies: Optional list of resources this resource depends on.
        """
        pass

    @abstractmethod
    def unregister_resource(self, resource: ManagedResource) -> None:
        """
        Unregister a resource from the manager.

        Args:
            resource: The resource to unregister.
        """
        pass

    @abstractmethod
    def initialize_all(self) -> bool:
        """
        Initialize all registered resources in dependency order.

        Returns:
            bool: True if all resources were initialized successfully, False otherwise.
        """
        pass

    @abstractmethod
    def dispose_all(self) -> None:
        """
        Dispose all registered resources in reverse dependency order.
        """
        pass

    @abstractmethod
    def get_resource_status(self) -> Dict[ManagedResource, Dict[str, Any]]:
        """
        Get status information for all registered resources.

        Returns:
            Dict mapping resources to their status information.
        """
        pass
```

## Application in Atlas Components

This standardized service architecture will be applied across multiple Atlas components:

### 1. Provider System Integration

The provider system will use the service components as follows:

- **StreamBuffer** will extend `Buffer[str]` from `core.services.buffer`
- **StreamControl** will implement `Controllable` from `core.services.base`
- **ProviderGroup** will use `CommandProcessor` for tracking provider selection
- **ProviderReliability** will integrate with `ManagedResource` for cleanup

### 2. Agent Communication

Agents will communicate using the service architecture:

- **AgentStreams** will use `Buffer[Message]` for controlled message flow
- **AgentLifecycle** will implement `ManagedResource` for proper initialization/cleanup
- **AgentCommands** will use the command pattern for task execution tracking
- **ControllerAgent** will use `CommandProcessor` for orchestrating worker agents

### 3. Knowledge Integration

The knowledge system will leverage service components:

- **StreamingRetrieval** will use `Buffer` for progressive document loading
- **RetrievalCommands** will track all document access operations
- **KnowledgeResources** will use `ResourceManager` for connection pooling

### 4. Graph Execution

The graph system will utilize the service architecture:

- **NodeStreaming** will implement `Buffer` for data flow between nodes
- **EdgeTransitions** will use `StateMachine` for managing graph traversal
- **GraphCommands** will track execution flow for debugging and monitoring

## Implementation Timeline

Implementation will proceed in these phases:

1. **Core Services Module Structure** (May 17-18, 2025)
   - Set up basic module structure and interfaces
   - Implement buffer and state management
   - Extract patterns from provider streaming

2. **Command Pattern Integration** (May 18-19, 2025)
   - Implement command pattern interface
   - Create command processor
   - Build telemetry integration

3. **Provider System Migration** (May 19-20, 2025)
   - Update streaming to use core services
   - Integrate with command pattern
   - Add telemetry hooks

4. **Agent System Integration** (May 20-24, 2025)
   - Implement agent communication with services
   - Create agent-specific commands
   - Add command tracking to agent workflows

5. **Knowledge and Graph Integration** (May 25-31, 2025)
   - Update knowledge system to use services
   - Enhance graph execution with command tracking
   - Implement progressive retrieval with buffers

## Architectural Impact

This architecture will unify patterns across Atlas, providing:

1. **Complete Observability**: Tracking all operations through commands
2. **Consistent State Management**: Standardized state transitions
3. **Resource Safety**: Proper initialization and cleanup
4. **Thread Safety**: Consistent concurrency patterns
5. **Interruptible Processing**: Pause/resume/cancel capabilities everywhere
6. **Telemetry Integration**: Performance metrics across all components

The command pattern in particular will enable powerful diagnostic capabilities, execution tracing, and undo functionality that can be leveraged for more sophisticated user interactions.
