# Reactive Event Mesh

## Overview

The Reactive Event Mesh forms the "central nervous system" of Atlas, enabling decoupled communication between components through a publish-subscribe architecture. It allows components to emit and respond to events without direct knowledge of each other.

## Key Concepts

- **Event Types**: Strongly typed classification of system events
- **Event Payload**: Data associated with an event occurrence
- **Publishers**: Components that emit events
- **Subscribers**: Components that receive and process events
- **Middleware**: Transformers and filters that process events in transit

## Benefits

- **Decoupling**: Components can evolve independently
- **Observability**: Events can be logged, analyzed, and replayed
- **Extensibility**: New functionality can be added by subscribing to existing events
- **Testing**: Components can be tested in isolation with simulated events

## Implementation Considerations

- **Thread Safety**: Must be thread-safe for concurrent publishers and subscribers
- **Performance**: Minimize overhead on critical event paths
- **Ordering Guarantees**: Consider event ordering requirements
- **Backpressure**: Handle fast publishers with slow subscribers
- **History**: Maintain event history for debugging and replay

## Implementation with Blinker

The Reactive Event Mesh pattern in NERV is implemented using the Blinker library, which provides a lightweight, thread-safe signal dispatcher for Python. Blinker was chosen for the following reasons:

1. **Simple and Lightweight**: Minimal implementation with few dependencies
2. **Thread Safety**: Safe for concurrent signal emission and handling
3. **Memory Management**: Uses weak references to prevent memory leaks
4. **Flexible API**: Supports named signals and anonymous signals
5. **Performance**: Optimized for fast signal dispatch with minimal overhead

### Core Blinker Components

| Component | Purpose |
|-----------|---------|
| **Signal** | Core signal class for connecting handlers and dispatching events |
| **NamedSignal** | Signal with a string identifier for global registration |
| **Namespace** | Registry for organizing related signals |
| **receiver_connected** | Decorator for subscribing to signals |

### Event Representation

In NERV, events are represented as structured data objects:

```python
from typing import TypeVar, Generic, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import uuid
import time

T = TypeVar('T')  # Event data type

@dataclass
class Event(Generic[T]):
    """Core event structure for the event bus."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType
    data: Optional[T] = None
    timestamp: float = field(default_factory=time.time)
    source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Performance Characteristics

The Blinker-based implementation offers:

- **Fast Signal Dispatch**: O(n) where n is the number of subscribers
- **Efficient Memory Usage**: Weak references prevent subscriber leaks
- **Thread-Safe Operations**: Thread-safe signal emission and subscription
- **Low Overhead**: Minimal processing overhead for signal dispatch
- **Bounded History**: Configurable event history with memory bounds

## Pattern Variations

### Local Event Bus

Best for in-process communication with minimal latency. Blinker's in-memory signal dispatching is ideal for this variation.

```python
# Type definitions only - not full implementation
from blinker import Signal

# Local event bus with in-memory signals
class LocalEventBus:
    def __init__(self):
        self._signals = {}  # Event type -> Signal mapping
        
    def subscribe(self, event_type, handler):
        if event_type not in self._signals:
            self._signals[event_type] = Signal()
        return self._signals[event_type].connect(handler)
        
    def publish(self, event_type, data=None):
        if event_type in self._signals:
            self._signals[event_type].send(data)
```

### Distributed Event Mesh

For cross-process or cross-service communication. Requires additional transport layer but can still use Blinker for local dispatch.

### Hierarchical Event Bus

Organizes events in parent-child relationships, allowing components to subscribe at different levels of granularity.

```python
# Type definitions only - not full implementation
class HierarchicalEventBus:
    def __init__(self, parent=None):
        self._signals = {}
        self._parent = parent
        
    def subscribe(self, event_pattern, handler):
        # Support hierarchical patterns like "system.provider.connected"
        pass
        
    def publish(self, event_type, data=None):
        # Publish to exact match and parent patterns
        pass
        
    def create_child_bus(self, prefix):
        # Create child bus with namespace prefix
        return HierarchicalEventBus(parent=self)
```

## Integration with Other NERV Patterns

### Integration with Effect System

```python
# Type definitions only - not full implementation
from effect import Effect, Dispatcher

# Event as effect
def publish_event_effect(event_type, data):
    return Effect(PublishEvent(event_type, data))

# Effect handler
@Dispatcher.register(PublishEvent)
def perform_publish_event(dispatcher, intent):
    event_bus.publish(intent.event_type, intent.data)
    return None
```

### Integration with State Projection

```python
# Type definitions only - not full implementation
class EventDrivenProjection:
    def __init__(self, event_bus):
        self.state = {}
        event_bus.subscribe(EventType.STATE_CHANGED, self.update_projection)
        
    def update_projection(self, event):
        # Apply event to projection state
        pass
```

### Integration with Quantum Partitioning

```python
# Type definitions only - not full implementation
class EventDrivenPartitioner:
    def __init__(self, event_bus):
        self.partitioner = QuantumPartitioner()
        event_bus.subscribe(EventType.TASK_CREATED, self.add_task)
        
    def add_task(self, event):
        # Add task to partitioner
        self.partitioner.add_unit(event.data["function"], event.data["dependencies"])
```

## Related Patterns

- Observer Pattern
- Publish-Subscribe Pattern
- Event Sourcing
- Command-Query Responsibility Segregation (CQRS)

## Implementation Reference

See the implementation component: [EventBus](../components/event_bus.md)