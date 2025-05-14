# State Projection

## Overview

State Projection stores minimal deltas and projection functions rather than complete states. This approach enables space-efficient history tracking and flexible views of the same state without redundant storage.

## Key Concepts

- **Initial State**: The base state from which all changes are applied
- **Delta**: A minimal change to be applied to a state
- **Projection Function**: Transforms state into a specific view
- **Delta Application**: The process of applying deltas to construct states
- **Tagged Deltas**: Changes with metadata for filtering and analysis

## Benefits

- **Efficiency**: Store only the changes, not redundant state copies
- **Flexibility**: Generate different views from the same history
- **Analysis**: Understand how specific changes impact the final state
- **Space Efficiency**: Minimal storage requirements for historical states
- **Selective Replay**: Apply only specific deltas for targeted views

## Implementation with Pyrsistent

The State Projection pattern in NERV is implemented using the Pyrsistent library, which provides persistent immutable data structures for Python. Pyrsistent was chosen for the following reasons:

1. **Immutable Data Structures**: Ensures state integrity during transformations
2. **Structural Sharing**: Efficiently shares unmodified portions of data structures
3. **Comprehensive Types**: PMap, PVector, PSet, and PRecord for different needs
4. **Type Safety**: Strong typing support with field validation
5. **Performance**: Optimized for efficient immutable operations

### Core Pyrsistent Data Structures

| Structure | Purpose | Usage in State Projection |
|-----------|---------|---------------------------|
| **PMap** | Immutable dictionary | Store key-value state properties |
| **PVector** | Immutable sequence | Store ordered collections like history |
| **PSet** | Immutable set | Store unique tags and identifiers |
| **PRecord** | Typed records | Define state schemas with validation |
| **Freeze/Thaw** | Convert between mutable/immutable | Interface with external systems |

### State Management Approach

Pyrsistent enables several key capabilities in the State Projection pattern:

1. **Non-destructive Updates**: Every state change creates a new state object
2. **Efficient Memory Usage**: Structural sharing minimizes memory footprint
3. **Safe Concurrency**: No locks needed for parallel state access
4. **History Preservation**: Previous states remain intact and accessible
5. **Pure Functional Transformations**: Clean, side-effect-free state transitions

```python
from typing import TypeVar, Generic, Callable, Dict, List, Any
from dataclasses import dataclass
from pyrsistent import pmap, pvector, PMap, PVector, freeze, thaw

T = TypeVar('T')  # State type
P = TypeVar('P')  # Projection result type

@dataclass
class Delta(Generic[T]):
    """A delta representing a change to state."""
    apply_fn: Callable[[T], T]
    metadata: Dict[str, Any]
    
    def apply(self, state: T) -> T:
        """Apply this delta to a state."""
        return self.apply_fn(state)
```

### Performance Characteristics

The Pyrsistent-based implementation offers:

- **Efficient Updates**: O(log n) for most operations
- **Structural Sharing**: Only changed parts allocate new memory
- **Copy-on-Write**: Unchanged parts are shared between versions
- **Memory Efficiency**: Lower memory footprint than full state copies
- **Delta Compression**: Only changes are stored, not entire states

## Pattern Variations

### Function-Based Deltas

Deltas represented as pure functions that transform state. This approach is highly flexible and can represent any kind of state transformation.

```python
# Type definitions only - not full implementation
def add_value_delta(key: str, value: Any) -> Callable[[PMap], PMap]:
    """Create a delta function that adds a value to a map."""
    def delta(state: PMap) -> PMap:
        return state.set(key, value)
    return delta

# Usage
projector.add_delta(
    add_value_delta("counter", 42),
    DeltaMetadata.create(tags=["counter", "init"])
)
```

### Patch-Based Deltas

Deltas represented as data patches that describe structural changes to state. More analyzable but potentially less expressive.

```python
# Type definitions only - not full implementation
@dataclass
class Patch:
    """A data patch representing changes to a state."""
    additions: Dict[str, Any] = field(default_factory=dict)
    removals: List[str] = field(default_factory=list)
    updates: Dict[str, Any] = field(default_factory=dict)
    
    def apply(self, state: PMap) -> PMap:
        """Apply this patch to a state."""
        # Start with a copy
        result = state
        
        # Apply removals
        for key in self.removals:
            if key in result:
                result = result.remove(key)
                
        # Apply updates and additions
        for key, value in {**self.additions, **self.updates}.items():
            result = result.set(key, value)
            
        return result
```

### Tagged Projections

Define projections based on delta tags for selective state construction:

```python
# Type definitions only - not full implementation
class TaggedProjector(Generic[T]):
    """A projector that applies deltas based on tags."""
    
    def __init__(self, initial_state: T):
        self.initial_state = freeze(initial_state)
        self.deltas: PVector[Delta[T]] = pvector()
        
    def project_with_tags(self, tags: List[str]) -> T:
        """Project state using only deltas with matching tags."""
        state = self.initial_state
        for delta in self.deltas:
            # Check if any tags match
            if any(tag in delta.metadata.get("tags", []) for tag in tags):
                state = delta.apply(state)
        return state
```

## Integration with Other NERV Patterns

### Integration with Effect System

```python
# Type definitions only - not full implementation
from effect import Effect, Dispatcher

# Define delta application as an effect
class ApplyDelta(Generic[T]):
    """An effect for applying a delta to state."""
    def __init__(self, delta: Delta[T], state: T):
        self.delta = delta
        self.state = state

# Effect handler
@Dispatcher.register(ApplyDelta)
def perform_apply_delta(dispatcher, intent):
    """Handle delta application effect."""
    return intent.delta.apply(intent.state)

# Usage in projection
def project_with_effects(initial_state: T, deltas: List[Delta[T]]) -> T:
    """Project state using effect system."""
    state = initial_state
    for delta in deltas:
        # Create and perform effect
        effect = Effect(ApplyDelta(delta, state))
        state = effect.perform()
    return state
```

### Integration with Temporal Versioning

```python
# Type definitions only - not full implementation
class TemporalStateProjector(Generic[T]):
    """A projector with temporal versioning support."""
    
    def __init__(self, initial_state: T):
        self.initial_state = freeze(initial_state)
        self.deltas: PVector[Delta[T]] = pvector()
        self.versions: PMap[str, int] = pmap()
        
    def create_version(self, version_id: str) -> None:
        """Create a named version at the current point."""
        self.versions = self.versions.set(version_id, len(self.deltas))
        
    def get_state_at_version(self, version_id: str) -> T:
        """Get state at a specific named version."""
        if version_id not in self.versions:
            raise ValueError(f"Unknown version: {version_id}")
            
        index = self.versions[version_id]
        return self.get_state_at_index(index)
```

### Integration with Reactive Event Mesh

```python
# Type definitions only - not full implementation
class ReactiveStateProjector(Generic[T]):
    """A projector that emits events on state changes."""
    
    def __init__(self, initial_state: T, event_bus):
        self.initial_state = freeze(initial_state)
        self.deltas: PVector[Delta[T]] = pvector()
        self.event_bus = event_bus
        self.current_state = initial_state
        
    def add_delta(self, delta_fn: Callable[[T], T], metadata: Dict[str, Any]) -> str:
        """Add a delta and emit events."""
        delta = Delta(delta_fn, metadata)
        
        # Add to deltas
        self.deltas = self.deltas.append(delta)
        
        # Update current state
        old_state = self.current_state
        self.current_state = delta.apply(old_state)
        
        # Emit events
        delta_id = metadata.get("id", str(len(self.deltas) - 1))
        self.event_bus.emit("delta_applied", {
            "delta_id": delta_id,
            "metadata": metadata
        })
        
        # Emit events for specific changes
        self._emit_state_change_events(old_state, self.current_state)
        
        return delta_id
```

## Related Patterns

- Command Pattern: Similar focus on operations rather than state
- Memento Pattern: Different approach to history preservation
- Event Sourcing: Related pattern with event log as source of truth
- CQRS: Complementary pattern separating reads and writes

## Implementation Reference

See the implementation component: [StateProjector](../components/state_projector.md)