---
title: Interfaces
---

# Core Interfaces

This document defines the fundamental protocol interfaces that serve as building blocks for the NERV architecture. These interfaces form the foundation upon which the patterns and components are built.

## Core Protocols Overview

| Protocol               | Purpose                           | Used By                                |
| ---------------------- | --------------------------------- | -------------------------------------- |
| `Observable[E]`        | Emit events to observers          | Reactive Event Mesh, EventBus          |
| `Versioned[S]`         | Maintain version history          | Temporal Versioning, TemporalStore     |
| `Projectable[S,P]`     | Project data into different views | Perspective Shifting, State Projection |
| `Effectful[V]`         | Track operation side effects      | Effect System, EffectMonad             |
| `QuantumUnit[S,R]`     | Parallelizable computation unit   | Quantum Partitioning                   |
| `Boundary[T_in,T_out]` | System boundary converter         | API integration, Validation            |

## Observable[E]

The `Observable` protocol defines objects that can emit events to registered observers, enabling reactive programming patterns.

::: info Observable Protocol
**Interface Methods**:

- **`add_observer(observer: Callable[[E, Any], None]) -> Callable[[], None]`**:
  Adds an observer and returns a function to remove it.

- **`remove_observer(observer: Callable[[E, Any], None]) -> None`**:
  Removes an observer from this object.

- **`notify(event: E, data: Any = None) -> None`**:
  Notifies all observers of an event with optional associated data.
:::

### Key Characteristics

- **Observer Registration**: Allows adding/removing event handlers
- **Unsubscribe Token**: Returns a function for easy cleanup
- **Event Notification**: Broadcasts events to registered observers
- **Type Safety**: Generic event type ensures type safety

### Primary Implementations

- [EventBus](../components/event_bus.md): Central event dispatch system

## Versioned[S]

The `Versioned` protocol defines objects that maintain a history of state changes, enabling time travel and auditing.

::: info Versioned Protocol
**Interface Methods**:

- **`get_current_version_id() -> VersionId`**:
  Returns the ID of the current version.

- **`get_version(version_id: Optional[VersionId] = None) -> S`**:
  Returns a specific version of the state (or current version if None).

- **`commit(state: S, description: str = "") -> VersionId`**:
  Creates a new version with the given state and returns its ID.

- **`get_history() -> List[Tuple[VersionId, S, str, float]]`**:
  Returns the complete version history as tuples of (id, state, description, timestamp).
:::

### Key Characteristics

- **Version Identification**: Unique IDs for each version
- **State Retrieval**: Access any historical state
- **Version Creation**: Explicitly create new versions
- **History Access**: Retrieve complete version history

### Primary Implementations

- [TemporalStore](../components/temporal_store.md): Versioned state container

## Projectable[S, P]

The `Projectable` protocol defines objects that can provide different views or projections of the same underlying data.

::: info Projectable Protocol
**Interface Methods**:

- **`add_projection(name: str, projection_fn: Callable[[S], P]) -> None`**:
  Registers a named projection function to transform source data.

- **`project(projection: str = "default") -> P`**:
  Returns the data transformed through a specific named projection.
:::

### Key Characteristics

- **Named Projections**: Register transformations by name
- **Dynamic Views**: Create different views of the same data
- **Transformation Functions**: Apply functions to source data
- **Default Fallback**: Support default projection

### Primary Implementations

- [PerspectiveAware](../components/perspective_aware.md): Context-dependent views
- [StateProjector](../components/state_projector.md): Delta-based projections

## Effectful[V]

The `Effectful` protocol defines operations with explicit tracking of side effects, enabling reasoning about and controlling effects throughout the system.

::: info Effectful Protocol
**Interface Methods**:

- **`with_effect(effect: Effect) -> Effectful[V]`**:
  Adds an effect to this operation, returning a new operation.

- **`map(fn: Callable[[V], Any]) -> Effectful[Any]`**:
  Transforms the result value without adding effects.

- **`bind(fn: Callable[[V], Effectful[Any]]) -> Effectful[Any]`**:
  Chains with another effectful operation, combining effects.

- **`run(handler: Callable[[Effect], Any]) -> V`**:
  Executes the operation, handling all effects with the provided handler.

- **`get_effects() -> List[Effect]`**:
  Returns all effects associated with this operation.
:::

### Key Characteristics

- **Effect Declaration**: Explicitly state operation effects
- **Pure Transformation**: Transform values without adding effects
- **Effect Composition**: Chain operations with combined effects
- **Effect Handling**: Control how effects are processed
- **Effect Inspection**: Examine declared effects

### Primary Implementations

- [EffectMonad](../components/effect_monad.md): Monadic effect tracking

## QuantumUnit[S, R]

The `QuantumUnit` protocol defines self-contained computation units with explicit dependencies that can be parallelized.

::: info QuantumUnit Protocol
**Interface Methods**:

- **`can_execute(completed_units: Set[Any]) -> bool`**:
  Checks if this unit can be executed based on completed dependencies.

- **`execute(context: S) -> R`**:
  Runs this unit's computation with the provided context.

- **`get_dependencies() -> List[Any]`**:
  Returns this unit's dependencies.

- **`get_result() -> Optional[R]`**:
  Returns this unit's result if available, None otherwise.
:::

### Key Characteristics

- **Dependency Declaration**: Explicit dependencies between units
- **Execution Readiness**: Logic to determine if ready to execute
- **Context-Based Execution**: Execute with provided context
- **Result Retrieval**: Access execution results
- **Dependency Graph**: Form execution DAG with other units

### Primary Implementations

- [QuantumPartitioner](../components/quantum_partitioner.md): Dependency-based parallel execution

## Boundary[T_in, T_out]

The `Boundary` protocol defines interfaces for system boundaries where external data is converted to internal representations.

::: info Boundary Protocol
**Interface Methods**:

- **`validate(data: T_in) -> ValidationResult[T_out]`**:
  Validates incoming data, returning a result with validated data or errors.

- **`process(data: T_in) -> T_out`**:
  Processes data across the boundary, potentially raising BoundaryError.

- **`handle_error(error: Exception) -> BoundaryError`**:
  Transforms exceptions into appropriate boundary errors.
:::

### Key Characteristics

- **Type Conversion**: Convert between external and internal types
- **Validation**: Ensure data meets requirements
- **Error Handling**: Proper handling of boundary errors
- **Domain Separation**: Maintain clear separation between domains

### Primary Implementations

- Network boundaries for API integration
- File system boundaries for data storage
- User interface boundaries for user input
