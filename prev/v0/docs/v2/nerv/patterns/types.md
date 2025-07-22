---
title: Types
---

# Core Types

This document defines the fundamental type definitions that serve as building blocks for the NERV architecture. These types form the foundation upon which the patterns and components are built.

## Type Variables

Type variables enable generic programming throughout the NERV architecture, allowing for type-safe abstractions.

::: info Type Variables for Generic Definitions
| Variable | Purpose      | Used For                        |
| -------- | ------------ | ------------------------------- |
| `T`      | General data | Any generic data type           |
| `S`      | State        | Component state representations |
| `R`      | Result       | Operation results               |
| `E`      | Event        | Event data types                |
| `V`      | Value        | Values in effectful operations  |
| `P`      | Perspective  | Projected views of data         |
| `K`      | Key          | Dictionary/map keys             |
| `C`      | Context      | Execution context               |
| `M`      | Message      | Communication messages          |
| `T_in`   | Input        | Boundary input types            |
| `T_out`  | Output       | Boundary output types           |
:::

### Purpose and Usage

Each type variable has a specific semantic meaning within the NERV architecture:

| Variable | Purpose      | Used For                        |
| -------- | ------------ | ------------------------------- |
| `T`      | General data | Any generic data type           |
| `S`      | State        | Component state representations |
| `R`      | Result       | Operation results               |
| `E`      | Event        | Event data types                |
| `V`      | Value        | Values in effectful operations  |
| `P`      | Perspective  | Projected views of data         |
| `K`      | Key          | Dictionary/map keys             |
| `C`      | Context      | Execution context               |
| `M`      | Message      | Communication messages          |
| `T_in`   | Input        | Boundary input types            |
| `T_out`  | Output       | Boundary output types           |

## Identity Types

Identity types provide unique identification for various entities in the system.

::: info Identity Types
| Type         | Definition        | Purpose                                        |
| ------------ | ----------------- | ---------------------------------------------- |
| `EntityId`   | String identifier | Unique identifier for any entity in the system |
| `VersionId`  | String identifier | Unique identifier for a versioned state        |
| `ResourceId` | String identifier | Identifier for a resource                      |
| `EventId`    | String identifier | Identifier for an event                        |
:::

### Purpose and Usage

These identity types provide consistent identification across the system:

| Type         | Purpose             | Used For               |
| ------------ | ------------------- | ---------------------- |
| `EntityId`   | Identify any entity | Component references   |
| `VersionId`  | Identify versions   | State history tracking |
| `ResourceId` | Identify resources  | Resource management    |
| `EventId`    | Identify events     | Event correlation      |

## Core Enumerations

Enumerations define fixed sets of values for various aspects of the system.

::: details EventType Enumeration
The EventType enumeration defines the core event types in the system:

**System Lifecycle Events**
- `SYSTEM_INIT`: System initialization
- `SYSTEM_SHUTDOWN`: System shutdown

**Provider Events**
- `PROVIDER_CREATED`: Provider instance created
- `PROVIDER_CONNECTED`: Provider connected to service
- `PROVIDER_DISCONNECTED`: Provider disconnected from service
- `PROVIDER_ERROR`: Provider encountered an error

*(Plus many more event types...)*
:::

::: details EffectType Enumeration
The EffectType enumeration defines types of side effects in the system:

**I/O Effects**
- `FILE_READ`: Reading from a file
- `FILE_WRITE`: Writing to a file
- `NETWORK_REQUEST`: Making a network request
- `DATABASE_QUERY`: Querying a database

*(Plus more effect types...)*
:::

::: details LifecycleState Enumeration
The LifecycleState enumeration defines lifecycle states for stateful components:

- `CREATED`: Component has been instantiated
- `INITIALIZING`: Component is initializing resources
- `READY`: Component is ready but not active
- `ACTIVE`: Component is actively processing
- `PAUSED`: Component is temporarily paused
- `STOPPING`: Component is in the process of stopping
- `STOPPED`: Component has stopped but not disposed
- `ERROR`: Component is in an error state
- `DISPOSED`: Component has been disposed
:::

::: details StreamState Enumeration
The StreamState enumeration defines states for streaming operations:

- `PENDING`: Stream operation pending start
- `ACTIVE`: Stream is actively flowing
- `PAUSED`: Stream is temporarily paused
- `COMPLETED`: Stream has successfully completed
- `CANCELLED`: Stream was cancelled by user
- `ERROR`: Stream encountered an error
:::

::: details ResourceType Enumeration
The ResourceType enumeration defines types of managed resources:

- `CONNECTION`: Network connection resource
- `FILE`: File system resource
- `THREAD`: Thread resource
- `PROCESS`: Process resource
- `SOCKET`: Socket resource
- `DATABASE`: Database connection resource
- `MODEL`: Model resource
:::

::: details UnitState Enumeration
The UnitState enumeration defines possible states for a quantum unit:

- `PENDING`: Not yet executed
- `READY`: Ready to execute (dependencies satisfied)
- `RUNNING`: Currently executing
- `COMPLETED`: Successfully completed
- `FAILED`: Execution failed
- `CANCELLED`: Execution cancelled
:::

## Core Data Classes

Data classes define structured data types used throughout the system.

::: details Event Data Class
The Event data class represents the core event structure for the event bus:

**Fields**:
- `id`: EventId - Unique identifier generated using UUID
- `type`: EventType - The type of event
- `data`: Optional[T] - Optional event payload data
- `timestamp`: float - When the event occurred
- `source`: Optional[EntityId] - Optional source entity ID
:::

::: details Effect Data Class
The Effect data class represents a side effect:

**Fields**:
- `type`: EffectType - The type of effect
- `payload`: Any - Optional effect payload
- `description`: str - Human-readable description
:::

::: details Resource Data Class
The Resource data class represents a managed resource:

**Fields**:
- `id`: ResourceId - Unique resource identifier
- `type`: ResourceType - The type of resource
- `state`: LifecycleState - Current lifecycle state
- `created_at`: float - Creation timestamp
- `metadata`: Dict[str, Any] - Additional resource metadata
:::

::: details VersionedState Data Class
The VersionedState data class represents a state with version history information:

**Fields**:
- `version_id`: str - Unique version identifier
- `data`: Any - The versioned data
- `parent_version_id`: Optional[str] - Optional parent version
- `timestamp`: float - When this version was created
- `change_description`: str - Description of the change
:::

::: details UnitResult Data Class
The UnitResult data class represents the result of a quantum unit execution:

**Fields**:
- `success`: bool - Whether execution succeeded
- `value`: Optional[R] - Optional result value
- `error`: Optional[Exception] - Optional error if failed
- `execution_time`: float - How long execution took
- `metadata`: Dict[str, Any] - Additional execution metadata
:::

::: details ValidationResult Data Class
The ValidationResult data class represents the result of data validation at a boundary:

**Fields**:
- `is_valid`: bool - Whether validation succeeded
- `data`: Optional[T_out] - Optional validated data
- `errors`: List[Dict[str, Union[str, int, float, bool]]] - Validation errors
:::

::: details DeltaMetadata Data Class
The DeltaMetadata data class contains metadata about a delta change:

**Fields**:
- `timestamp`: float - When the delta was created
- `source`: Optional[EntityId] - Optional source entity
- `description`: str - Human-readable description
- `tags`: List[str] - Optional categorization tags
:::

## Error Types

Error classes define the hierarchy of exceptions used in the system.

::: warning Error Hierarchy
**Base Error Class**:
- `AtlasError`: Base class for all Atlas errors
  - Fields: message, details dictionary

**Boundary Error Classes**:
- `BoundaryError`: Base class for boundary errors
  - Additional field: boundary name
  - Inherits from AtlasError

**Specialized Boundary Errors**:
- `ValidationError`: For validation failures
  - Additional field: validation_errors list
  - Inherits from BoundaryError
- `NetworkError`: For network failures
  - Additional fields: status_code, response
  - Inherits from BoundaryError
:::

## Abstract Base Classes

Abstract base classes provide partial implementations of interfaces.

::: info Delta Abstract Base Class
The Delta abstract base class represents a change to be applied to a state:

**Factory Methods**:
- `function_delta(fn)`: Creates a delta from a state transformation function
- `patch_delta(patch)`: Creates a delta from a dictionary patch

**Abstract Methods**:
- `apply(state)`: Abstract method to apply the delta to a state
:::

::: details Delta Implementations
**FunctionDelta**:
- Represents a delta as a function that transforms state
- Takes a transform function in constructor
- Implements apply() by calling the function on the state

**PatchDelta**:
- Represents a delta as a dictionary patch
- Takes a patch dictionary in constructor
- Implements apply() by merging the patch with the state dictionary
:::

## Type Relationships

These core types form the foundation of the NERV architecture:

- **Type Variables** enable generic programming across the system
- **Identity Types** provide consistent identification schemes
- **Enumerations** define fixed sets of values with semantic meaning
- **Data Classes** define structured data with clear semantics
- **Error Types** provide a consistent error handling hierarchy
- **Abstract Base Classes** provide partial implementations for reuse

These core types are used to build the more complex [interfaces](interfaces.md) that define component behavior, which in turn are implemented by the [components](../components/index.md) of the system.
