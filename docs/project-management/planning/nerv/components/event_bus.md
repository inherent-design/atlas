---
title: Event Bus
---

# EventBus Implementation

## Overview

The EventBus is the central implementation of the Reactive Event Mesh pattern in Atlas. It provides a thread-safe, in-memory publish-subscribe system for decoupled component communication using the Blinker library.

## Architectural Role

The EventBus serves as the "nervous system" of Atlas, connecting all major components:

- **Providers**: Emit connection events and response events
- **Agents**: Coordinate through task and state events
- **Knowledge**: Share retrieval and document processing events
- **Orchestration**: Emit workflow state transitions
- **Core Services**: Monitor system health and metrics

## Implementation Details

### Library: Blinker

Blinker is chosen for EventBus implementation because it provides:

- **Fast signal dispatching** with minimal overhead
- **Thread-safe event handling** for concurrent operations
- **Flexible subscription model** with support for named signals
- **Memory-efficient design** with weak references to prevent leaks
- **Lightweight footprint** for minimizing dependencies

### Key Features

The EventBus implementation includes:

1. **Thread-safe event distribution** using read-write locks
2. **Middleware pipeline** for event transformation and filtering
3. **Event history** with configurable capacity
4. **Typed subscribers** for type-safe event handling
5. **Unsubscribe tokens** for clean handler removal

### Core Data Types

```python
from typing import TypeVar, Generic, Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import uuid
import time
import threading
from blinker import Signal

# Type variables
T = TypeVar('T')  # Event data type
EventId = str

class EventType(Enum):
    """Core event types in the system."""
    # System lifecycle events
    SYSTEM_INIT = auto()
    SYSTEM_SHUTDOWN = auto()
    
    # Provider events
    PROVIDER_CREATED = auto()
    PROVIDER_CONNECTED = auto()
    # More event types...

@dataclass
class Event(Generic[T]):
    """Core event structure for the event bus."""
    id: EventId = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType
    data: Optional[T] = None
    timestamp: float = field(default_factory=time.time)
    source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Implementation Structure

The EventBus implementation uses Blinker's Signal class for event distribution:

```python
class EventBus:
    """Central event dispatch system for the Reactive Event Mesh."""
    
    def __init__(self, history_limit: int = 1000):
        """Initialize the event bus with configurable history limit."""
        self._signals: Dict[EventType, Signal] = {}
        self._middleware: List[Callable] = []
        self._history: List[Event[Any]] = []
        self._history_limit: int = history_limit
        self._lock: threading.RLock = threading.RLock()
        
    def subscribe(self, event_type: EventType, 
                 handler: Callable[[Event[Any]], None]) -> Callable[[], None]:
        """Subscribe to events with unsubscribe token return."""
        # Implementation details...
        
    def publish(self, event_type: EventType, data: Any = None,
               source: Optional[str] = None) -> EventId:
        """Publish event to all subscribers with middleware processing."""
        # Implementation details...
```

## Performance Considerations

Blinker is designed for high performance, but there are several optimizations in the EventBus implementation:

### Signal Management

The EventBus maintains a private registry of signals instead of using Blinker's global registry:

```python
# Private signal creation for better isolation
def get_signal(self, event_type: EventType) -> Signal:
    """Get or create a signal for an event type."""
    with self._lock:
        if event_type not in self._signals:
            self._signals[event_type] = Signal(str(event_type))
        return self._signals[event_type]
```

### Thread Safety

The EventBus uses a reentrant lock for thread safety, ensuring concurrent access is properly synchronized:

```python
# Thread-safe publishing with lock separation
def publish(self, event_type: EventType, data: Any = None) -> EventId:
    # Create event
    event = Event(type=event_type, data=data)
    
    # Critical section: apply middleware and store history
    with self._lock:
        # Apply middleware...
        # Store in history...
        pass
        
    # Send event outside lock to prevent deadlocks during handler execution
    signal = self._signals.get(event_type)
    if signal:
        signal.send(event)
```

### Memory Management

Blinker's weak references help prevent memory leaks from accumulated handlers:

```python
# Use weak references for handler connections
self._signals[event_type].connect(handler, weak=True)
```

### Bounded History

The EventBus maintains a bounded history to prevent unbounded memory growth:

```python
# Bounded history with size limit
self._history.append(current_event)
if len(self._history) > self._history_limit:
    self._history = self._history[-self._history_limit:]
```

## Integration Patterns

### Provider Integration

```python
# Type definition only - not full implementation
class ProviderManager:
    """Manager for provider lifecycle events."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.providers = {}
        
        # Subscribe to provider events
        self.event_bus.subscribe(EventType.PROVIDER_CREATED, 
                               self._handle_provider_created)
```

### Agent Integration

```python
# Type definition only - not full implementation
class AgentController:
    """Controller for agent coordination events."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.agents = {}
        
        # Subscribe to agent lifecycle events
        self.event_bus.subscribe(EventType.AGENT_STARTED,
                               self._handle_agent_started)
```

### Workflow Integration

```python
# Type definition only - not full implementation
class WorkflowEngine:
    """Engine for workflow execution events."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        
    def execute_node(self, workflow_id: str, node_id: str,
                    input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow node with event notifications."""
        # Emit node entered event
        self.event_bus.publish(EventType.WORKFLOW_NODE_ENTERED,
                             {"workflow_id": workflow_id, "node_id": node_id})
```

## Usage Patterns

### Basic Publish/Subscribe

::: info Basic Usage with Blinker
```python
# Create event bus
event_bus = EventBus()

# Subscribe to events
unsubscribe = event_bus.subscribe(
    EventType.STREAM_STARTED,
    lambda event: print(f"Stream started: {event.data}")
)

# Publish event
event_id = event_bus.publish(
    EventType.STREAM_STARTED,
    {"stream_id": "stream1", "provider": "anthropic"}
)

# Unsubscribe when done
unsubscribe()
```
:::

### Event Middleware

::: tip Event Transformation
```python
# Type definition only - not full implementation
def add_timestamp_middleware(event: Event) -> Event:
    """Add ISO timestamp to event metadata."""
    if event.metadata is None:
        event.metadata = {}
    
    event.metadata["iso_time"] = format_iso_time(event.timestamp)
    return event

# Add middleware to event bus
remove_middleware = event_bus.add_middleware(add_timestamp_middleware)
```
:::

### Error Handling

::: warning Safe Subscription
```python
# Type definition only - not full implementation
def safe_subscribe(event_bus: EventBus, event_type: EventType, 
                  handler: Callable[[Event], None]) -> Callable[[], None]:
    """Subscribe with error handling wrapper."""
    def safe_handler(event: Event) -> None:
        try:
            handler(event)
        except Exception as e:
            # Log error and publish error event
            event_bus.publish(
                EventType.HANDLER_ERROR,
                {"original_event": event.id, "error": str(e)}
            )
    
    return event_bus.subscribe(event_type, safe_handler)
```
:::

### Scoped Event Bus

::: details Hierarchical Event Scope
```python
# Type definition only - not full implementation
class ScopedEventBus:
    """Event bus with hierarchical scoping."""
    
    def __init__(self, parent=None, scope_name=None):
        self.event_bus = EventBus()
        self.parent_bus = parent
        self.scope_name = scope_name or str(uuid.uuid4())[:8]
        
    def publish(self, event_type, data=None):
        """Publish in current scope and propagate to parent."""
        # Publish locally
        event_id = self.event_bus.publish(event_type, data)
        
        # Propagate to parent if available
        if self.parent_bus:
            self.parent_bus.publish(event_type, data)
            
        return event_id
```
:::

## Performance Optimization

The EventBus implementation includes several performance optimizations:

1. **Signal Caching**: Reusing signal instances for each event type
2. **Lock Minimization**: Using lock only for critical sections
3. **Weak References**: Preventing memory leaks from handler references
4. **Bounded Collections**: Limiting history size for memory efficiency
5. **Dispatch Separation**: Separating event creation from dispatch

## Relationship to Patterns

Implements:
- **[Reactive Event Mesh](../patterns/reactive_event_mesh.md)**: Primary implementation

Supports:
- **[Temporal Versioning](../patterns/temporal_versioning.md)**: Events can trigger version creation
- **[State Projection](../patterns/state_projection.md)**: Events can trigger projections
- **[Effect System](../patterns/effect_system.md)**: Events can be modeled as effects
- **[Quantum Partitioning](../patterns/quantum_partitioning.md)**: Events can coordinate parallel execution