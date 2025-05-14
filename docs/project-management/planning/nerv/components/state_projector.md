---
title: State Projector
---

# StateProjector Implementation

## Overview

The StateProjector implements the State Projection pattern, managing state through a series of deltas (changes) rather than storing complete state copies. It supports multiple projections of the same underlying state evolution.

## Architectural Role

StateProjector provides an efficient approach to state management:

- **Workflow State**: Tracking execution progress efficiently
- **Document Processing**: Managing incremental document changes
- **Configuration Evolution**: Tracking configuration changes over time
- **User Settings**: Managing personalization changes
- **Application State**: Efficient state management for UIs

## Implementation Details

### Library: Pyrsistent

The StateProjector uses Pyrsistent for immutable data structures, providing:

- **Immutable Collections**: PMap, PVector, PSet for immutable state
- **Structural Sharing**: Efficient memory usage across state versions
- **Type Safety**: PRecord for type-safe state schemas
- **Side-Effect Prevention**: Guarantees against accidental state mutation
- **Functional Updates**: Declarative transformations with pure functions

### Key Features

The StateProjector implementation features:

1. **Delta-based state tracking** for space efficiency
2. **Multiple projection functions** for different views
3. **Tagging system** for categorizing and filtering changes
4. **Metadata tracking** for change attribution and timing
5. **Selective application** for partial state reconstruction

### Core Data Types

```python
from typing import TypeVar, Generic, Callable, Dict, List, Set, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from pyrsistent import pmap, pvector, pset, PMap, PVector, PSet, freeze, thaw

# Type variables
T = TypeVar('T')  # State type
P = TypeVar('P')  # Projection result type

@dataclass(frozen=True)
class DeltaMetadata:
    """Metadata for a state delta."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    author: Optional[str] = None
    description: Optional[str] = None
    tags: PSet[str] = field(default_factory=pset)

# Delta function type - takes a state and returns a new state
DeltaFn = Callable[[T], T]

# Projection function type - takes a state and returns a projected view
ProjectionFn = Callable[[T], P]
```

### Implementation Structure

```python
class StateProjector(Generic[T]):
    """
    Manages state through a series of deltas, supporting multiple projections.
    Uses Pyrsistent for immutable data structures.
    """

    def __init__(self, initial_state: T):
        """Initialize a new state projector with the given initial state."""
        # Convert the initial state to an immutable structure
        self._initial_state = freeze(initial_state)

        # Store deltas as an immutable vector
        self._deltas: PVector[Delta[T]] = pvector()

        # Cache of current state to avoid recomputation
        self._current_state: Optional[T] = self._initial_state

        # Map of projection functions
        self._projections: PMap[str, ProjectionFn] = pmap()

        # Cache of projection results
        self._projection_cache: Dict[str, Any] = {}
```

## Performance Considerations

Using Pyrsistent for the StateProjector implementation provides several performance benefits:

### Memory Efficiency

Pyrsistent's structural sharing minimizes memory usage:

```python
# Memory efficiency through structural sharing
def add_delta(self, delta_fn: DeltaFn[T], metadata: Optional[DeltaMetadata] = None) -> str:
    """Add a new delta to the state history."""
    # Create delta with metadata
    delta = Delta(delta_fn, metadata or DeltaMetadata.create())

    # Add to immutable vector of deltas with structural sharing
    self._deltas = self._deltas.append(delta)

    # Update current state efficiently using the previous state
    if self._current_state is not None:
        self._current_state = delta.apply(self._current_state)

    # Invalidate projection caches
    self._projection_cache = {}

    return metadata.id
```

### Performance Optimization

The implementation includes several optimizations for better performance:

- **State Caching**: Maintains current state to avoid recomputation
- **Projection Caching**: Caches projection results until invalidation
- **Selective Computation**: Applies only necessary deltas based on filters
- **Lazy Evaluation**: Computes states only when needed
- **Efficient Filtering**: Uses metadata tags for fast filtering

### Memory Usage Analysis

Pyrsistent's structural sharing significantly reduces memory usage:

```python
# Type definitions only - not full implementation
def memory_analysis():
    """Analyze memory usage of the StateProjector."""
    import sys
    from pyrsistent import m

    # Create a large initial state with 10,000 items
    initial_data = {f"key_{i}": f"value_{i}" for i in range(10000)}
    initial_state = m(**initial_data)

    # Create a state projector
    projector = StateProjector(initial_state)
    initial_size = sys.getsizeof(projector)

    # Add 1000 deltas, each modifying a single key
    for i in range(1000):
        projector.add_delta(
            lambda state, i=i: state.set(f"key_{i}", f"modified_{i}")
        )

    # Check memory usage
    final_size = sys.getsizeof(projector)

    # With structural sharing, memory usage is much lower than storing 1000 complete copies
    return {
        "initial_bytes": initial_size,
        "final_bytes": final_size,
        "bytes_per_delta": (final_size - initial_size) / 1000,
        "full_copy_savings": 1 - (final_size - initial_size) / (sys.getsizeof(initial_state) * 1000)
    }
```

## Integration Patterns

The StateProjector integrates with other NERV components through several patterns:

### Integration with EventBus

```python
# Type definition only - not full implementation
class EventEmittingProjector(Generic[T]):
    """StateProjector that emits events on state changes."""

    def __init__(self, initial_state: T, event_bus):
        self.projector = StateProjector(initial_state)
        self.event_bus = event_bus

    def add_delta(self, delta_fn: DeltaFn[T], metadata: Optional[DeltaMetadata] = None) -> str:
        """Add a delta and emit events."""
        # Get previous state
        previous_state = self.projector.get_current_state()

        # Add delta
        delta_id = self.projector.add_delta(delta_fn, metadata)

        # Get new state
        new_state = self.projector.get_current_state()

        # Emit event
        self.event_bus.publish(
            EventType.STATE_CHANGED,
            {
                "delta_id": delta_id,
                "metadata": metadata,
                "diff": self._compute_diff(previous_state, new_state)
            }
        )

        return delta_id
```

### Integration with TemporalStore

```python
# Type definition only - not full implementation
class VersionedStateProjector(Generic[T]):
    """StateProjector with temporal versioning support."""

    def __init__(self, initial_state: T, temporal_store):
        self.projector = StateProjector(initial_state)
        self.temporal_store = temporal_store
        self.versions = {}

    def save_version(self, version_name: str) -> None:
        """Save the current state as a named version."""
        # Get current delta index
        index = self.projector.get_delta_count() - 1

        # Save to version map
        self.versions[version_name] = index

        # Save to temporal store
        self.temporal_store.save_version(
            version_name,
            thaw(self.projector.get_current_state())
        )
```

### Integration with EffectMonad

```python
# Type definition only - not full implementation
from effect import Effect, sync_perform, TypeDispatcher

# Delta application effect
class ApplyDelta(Generic[T]):
    """Effect for applying a delta to state."""
    def __init__(self, delta: Delta[T], state: T):
        self.delta = delta
        self.state = state

# Effect handler
def apply_delta_handler(effect):
    """Handle ApplyDelta effect."""
    return effect.delta.apply(effect.state)

# Use in StateProjector
def get_state_with_effects(self, filter_fn) -> T:
    """Get filtered state using effect monad."""
    # Create dispatcher
    dispatcher = TypeDispatcher({ApplyDelta: apply_delta_handler})

    # Start with initial state
    state = self._initial_state

    # Apply deltas through effects
    for delta in self._deltas:
        if filter_fn(delta.metadata):
            # Create effect
            effect = Effect(ApplyDelta(delta, state))
            # Perform effect
            state = sync_perform(dispatcher, effect)

    return state
```

## Usage Patterns

### Basic State Evolution

::: info Basic State Management
```python
from pyrsistent import pmap

# Create initial state
initial_state = pmap({"count": 0, "name": "example"})

# Create state projector
projector = StateProjector(initial_state)

# Add deltas with metadata
projector.add_delta(
    lambda state: state.set("count", state["count"] + 1),
    DeltaMetadata.create(author="alice", tags=["counter"])
)

projector.add_delta(
    lambda state: state.set("name", "updated example"),
    DeltaMetadata.create(author="bob", tags=["metadata"])
)

# Get current state
current = projector.get_current_state()
print(f"Count: {current['count']}, Name: {current['name']}")
```
:::

### Filtered States

::: tip Filtered State Access
```python
# Type definitions only - not full implementation
# Get state with only specific author's changes
alice_state = projector.get_state_with_filter(
    lambda metadata: metadata.author == "alice"
)

# Get state with only specific tags
metadata_state = projector.get_state_with_tags(["metadata"])

# Get state at a specific point in time
past_state = projector.get_state_at_time(
    datetime(2023, 6, 1, 12, 0, 0)
)
```
:::

### Projections

::: warning Using Projections
```python
# Type definitions only - not full implementation
# Add projections
projector.add_projection(
    "stats",
    lambda state: {"count": state["count"], "name_length": len(state["name"])}
)

projector.add_projection(
    "summary",
    lambda state: f"Count: {state['count']}, Name: {state['name']}"
)

# Use projections
stats = projector.project("stats")
summary = projector.project("summary")
```
:::

### Time Travel

::: details Time Travel Operations
```python
# Type definitions only - not full implementation
# Get state at specific delta index
state_after_first = projector.get_state_at_index(0)

# Get delta history
history = projector.get_delta_history()
for i, metadata in enumerate(history):
    print(f"Delta {i}: {metadata.description} by {metadata.author}")

# Reset to earlier state
projector.reset_to_index(1)  # Remove all deltas after index 1
```
:::

## Advanced Implementation Patterns

### Batch Delta Application

For better performance when applying multiple deltas:

```python
# Type definitions only - not full implementation
def add_deltas_batch(self, delta_fns: List[DeltaFn[T]],
                   metadatas: Optional[List[DeltaMetadata]] = None) -> List[str]:
    """Add multiple deltas in a single batch operation."""
    if metadatas is None:
        metadatas = [DeltaMetadata.create() for _ in range(len(delta_fns))]

    # Validate input
    if len(metadatas) != len(delta_fns):
        raise ValueError("Must provide same number of metadatas as delta functions")

    # Create deltas
    deltas = [Delta(fn, meta) for fn, meta in zip(delta_fns, metadatas)]

    # Use evolver for efficient batch updates
    deltas_evolver = self._deltas.evolver()
    for delta in deltas:
        deltas_evolver.append(delta)

    # Update deltas vector
    self._deltas = deltas_evolver.persistent()

    # Update current state
    if self._current_state is not None:
        for delta in deltas:
            self._current_state = delta.apply(self._current_state)

    # Invalidate caches
    self._projection_cache = {}

    # Return delta IDs
    return [delta.metadata.id for delta in deltas]
```

### Optimized Projection Caching

For efficiently handling frequently accessed projections:

```python
# Type definitions only - not full implementation
class CachingStateProjector(StateProjector[T]):
    """StateProjector with advanced caching strategies."""

    def __init__(self, initial_state: T, cache_limit: int = 100):
        super().__init__(initial_state)
        self._projection_cache = {}
        self._state_cache = {}
        self._cache_limit = cache_limit
        self._cache_hits = 0
        self._cache_misses = 0

    def project(self, name: str) -> Any:
        """Get projection result with caching."""
        # Try cache first
        cache_key = f"{name}_{len(self._deltas)}"
        if cache_key in self._projection_cache:
            self._cache_hits += 1
            return self._projection_cache[cache_key]

        # Cache miss
        self._cache_misses += 1

        # Compute projection
        result = self._projections[name](self.get_current_state())

        # Cache result with eviction policy
        if len(self._projection_cache) >= self._cache_limit:
            # Simple LRU - remove oldest entry
            oldest_key = next(iter(self._projection_cache))
            del self._projection_cache[oldest_key]

        self._projection_cache[cache_key] = result
        return result
```

## Relationship to Patterns

Implements:
- **[State Projection](../patterns/state_projection.md)**: Primary implementation

Supports:
- **[Reactive Event Mesh](../patterns/reactive_event_mesh.md)**: Can emit events on state changes
- **[Temporal Versioning](../patterns/temporal_versioning.md)**: Complementary approach to versioning
- **[Perspective Shifting](../patterns/perspective_shifting.md)**: Projections create different perspectives
- **[Effect System](../patterns/effect_system.md)**: State changes can be modeled as effects
