---
title: Diagrams
---

# NERV Type System Architecture

This document provides visual diagrams of the NERV architecture type system, showing relationships and organization.

## Type Hierarchy Overview

```mermaid
graph TD
    %% Core Type Categories
    CoreTypes["Core Types"] --> TypeVars["Type Variables"]
    CoreTypes --> Aliases["Type Aliases"]
    CoreTypes --> Enums["Enumerations"]
    CoreTypes --> DataClasses["Data Classes"]
    CoreTypes --> Protocols["Protocol Interfaces"]
    CoreTypes --> ErrorTypes["Error Types"]

    %% Implementation Categories
    Implementations["Implementations"] --> EventSystem["Event System"]
    Implementations --> StateSystem["State System"]
    Implementations --> PerspectiveSystem["Perspective System"]
    Implementations --> EffectSystem["Effect System"]
    Implementations --> ExecutionSystem["Execution System"]
    Implementations --> BoundarySystem["Boundary System"]

    %% Type Variables
    TypeVars --> T["T: Data"]
    TypeVars --> S["S: State"]
    TypeVars --> R["R: Result"]
    TypeVars --> E["E: Event"]
    TypeVars --> V["V: Value"]
    TypeVars --> P["P: Perspective"]
    TypeVars --> others["Other TypeVars..."]

    %% Aliases
    Aliases --> EntityId["EntityId = str"]
    Aliases --> VersionId["VersionId = str"]
    Aliases --> ResourceId["ResourceId = str"]
    Aliases --> EventId["EventId = str"]

    %% Protocols
    Protocols --> Observable["Observable[E]"]
    Protocols --> Versioned["Versioned[S]"]
    Protocols --> Projectable["Projectable[S,P]"]
    Protocols --> Effectful["Effectful[V]"]
    Protocols --> QuantumUnit["QuantumUnit[S,R]"]
    Protocols --> Boundary["Boundary[T_in,T_out]"]

    %% Error Types
    ErrorTypes --> AtlasError["AtlasError"]
    AtlasError --> BoundaryError["BoundaryError"]
    BoundaryError --> ValidationError["ValidationError"]
    BoundaryError --> NetworkError["NetworkError"]

    %% Implementation Relationships
    Observable --> EventSystem
    Versioned --> StateSystem
    Projectable --> PerspectiveSystem
    Effectful --> EffectSystem
    QuantumUnit --> ExecutionSystem
    Boundary --> BoundarySystem
```

## Core Protocols and Implementations

```mermaid
classDiagram
    class Observable~E~ {
        <<interface>>
        +add_observer(observer) Callable
        +remove_observer(observer) void
        +notify(event, data) void
    }

    class Versioned~S~ {
        <<interface>>
        +get_current_version_id() VersionId
        +get_version(version_id) S
        +commit(state, description) VersionId
        +get_history() List
    }

    class Projectable~S,P~ {
        <<interface>>
        +add_projection(name, projection_fn) void
        +project(projection) P
    }

    class Effectful~V~ {
        <<interface>>
        +with_effect(effect) Effectful
        +map(fn) Effectful
        +bind(fn) Effectful
        +run(handler) V
        +get_effects() List
    }

    class QuantumUnit~S,R~ {
        <<interface>>
        +can_execute(completed_units) bool
        +execute(context) R
        +get_dependencies() List
        +get_result() Optional~R~
    }

    class Boundary~T_in,T_out~ {
        <<interface>>
        +validate(data) ValidationResult
        +process(data) T_out
        +handle_error(error) BoundaryError
    }

    class EventBus {
        -_subscribers Map
        -_middleware List
        -_history List
        +subscribe(event_type, handler) Callable
        +publish(event_type, data, source) EventId
        +add_middleware(middleware) Callable
        +get_history(event_type, limit) List
    }

    class TemporalStore {
        -_versions Map
        -_current_version_id VersionId
        +commit(data, description) VersionId
        +get(version_id) Any
        +get_history() List
    }

    class PerspectiveAware~S,P~ {
        -_data S
        -_perspectives Map
        -_current_perspective string
        +add_perspective(name, transform_fn) void
        +remove_perspective(name) bool
        +set_default_perspective(name) void
        +view(perspective) Union~S,P~
        +get_available_perspectives() List
        +update_data(data) void
    }

    class StateProjector~S,P~ {
        -_initial_state S
        -_deltas List
        -_projections Map
        +apply_delta(delta, description, source, tags) int
        +add_projection(name, projection_fn) void
        +project(projection, until) P
        +get_current_state() S
        +get_delta_history(with_tags) List
        +reset_to_initial() void
    }

    class EffectMonad~V~ {
        -value V
        -effects List~Effect~
        +map(fn) EffectMonad
        +bind(fn) EffectMonad
        +run(handler) V
        +get_effects() List
        +with_effect(effect) EffectMonad
        +pure(value) EffectMonad
        +effect(type, payload, description) EffectMonad
    }

    class QuantumUnitImpl~S,R~ {
        -id string
        -name string
        -fn Callable
        -dependencies List
        -state UnitState
        -result UnitResult~R~
        -timeout float
        -metadata Map
        +can_execute(completed_units) bool
        +execute(context) UnitResult~R~
        +cancel() bool
        +get_dependencies() List
        +get_result() Optional~R~
    }

    class ExecutionPlan {
        -units Map
        -graph Map
        -levels List
        +get_level_count() int
        +get_units_at_level(level) List
        +get_maximum_parallelism() int
    }

    class QuantumPartitioner~S,R~ {
        -units List
        -results Map
        -completed Set
        -failed Set
        +add_unit(fn, dependencies, name, timeout) QuantumUnitImpl
        +build_execution_plan() ExecutionPlan
        +execute(context, max_parallel) Map
        +get_failed_units() List
        +cancel_all_pending() int
    }

    Observable <|.. EventBus
    Versioned <|.. TemporalStore
    Projectable <|.. PerspectiveAware
    Projectable <|.. StateProjector
    Effectful <|.. EffectMonad
    QuantumUnit <|.. QuantumUnitImpl

    QuantumUnitImpl --o ExecutionPlan
    ExecutionPlan --* QuantumPartitioner
```

## Data Models

```mermaid
classDiagram
    class Event~T~ {
        +id EventId
        +type EventType
        +data Optional~T~
        +timestamp float
        +source Optional~EntityId~
    }

    class Effect {
        +type EffectType
        +payload Any
        +description string
    }

    class Resource {
        +id ResourceId
        +type ResourceType
        +state LifecycleState
        +created_at float
        +metadata Dict
    }

    class VersionedState {
        +version_id string
        +data Any
        +parent_version_id Optional~string~
        +timestamp float
        +change_description string
    }

    class UnitResult~R~ {
        +success bool
        +value Optional~R~
        +error Optional~Exception~
        +execution_time float
        +metadata Dict
    }

    class ValidationResult~T~ {
        +is_valid bool
        +data Optional~T~
        +errors List
    }

    class DeltaMetadata {
        +timestamp float
        +source Optional~EntityId~
        +description string
        +tags List~string~
    }

    class Delta~S~ {
        <<abstract>>
        +apply(state) S
        +function_delta(fn) Delta~S~
        +patch_delta(patch) Delta~S~
    }

    class FunctionDelta~S~ {
        -fn Callable
        +apply(state) S
    }

    class PatchDelta~S~ {
        -patch Dict
        +apply(state) S
    }

    Delta <|-- FunctionDelta
    Delta <|-- PatchDelta

    EventBus --> Event : creates
    TemporalStore --> VersionedState : manages
    StateProjector --> Delta : applies
    StateProjector --> DeltaMetadata : tracks
    EffectMonad --> Effect : contains
    QuantumUnitImpl --> UnitResult : produces
    Boundary --> ValidationResult : returns
```

## Architectural Patterns and Implementations

```mermaid
flowchart TD
    subgraph "Architectural Patterns"
        ReactiveEventMesh["Reactive Event Mesh"]
        TemporalVersioning["Temporal Versioning"]
        PerspectiveShifting["Perspective Shifting"]
        StateProjection["State Projection"]
        EffectSystem["Effect System"]
        QuantumPartitioning["Quantum Partitioning"]
    end

    subgraph "Components"
        EventBus
        TemporalStore
        PerspectiveAware
        StateProjector
        EffectMonad
        EffectHandler
        QuantumUnitImpl
        ExecutionPlan
        QuantumPartitioner
    end

    %% Implementations of patterns
    ReactiveEventMesh --> EventBus
    TemporalVersioning --> TemporalStore
    PerspectiveShifting --> PerspectiveAware
    StateProjection --> StateProjector
    EffectSystem --> EffectMonad
    EffectSystem --> EffectHandler
    QuantumPartitioning --> QuantumUnitImpl
    QuantumPartitioning --> ExecutionPlan
    QuantumPartitioning --> QuantumPartitioner

    %% Core Data Classes
    Event["Event"]
    VersionedState["VersionedState"]
    Delta["Delta"]
    Effect["Effect"]
    UnitResult["UnitResult"]
    ValidationResult["ValidationResult"]

    %% Core dependencies
    EventBus --> Event
    TemporalStore --> VersionedState
    StateProjector --> Delta
    EffectMonad --> Effect
    QuantumUnitImpl --> UnitResult

    %% Cross-component dependencies
    EventBus -.-> StateProjector
    EventBus -.-> EffectHandler
    EffectHandler -.-> EffectMonad
    StateProjector -.-> EventBus
    QuantumPartitioner -.-> EventBus
    PerspectiveAware -.-> StateProjector
```

## Functional Systems

```mermaid
flowchart TD
    subgraph "Event System"
        EventBus
        Event
        EventType
    end

    subgraph "State System"
        TemporalStore
        VersionedState
        VersionId
    end

    subgraph "Perspective System"
        PerspectiveAware
        StateProjector
        Delta
        DeltaMetadata
    end

    subgraph "Effect System"
        EffectMonad
        Effect
        EffectType
        EffectHandler
    end

    subgraph "Execution System"
        QuantumUnitImpl
        ExecutionPlan
        QuantumPartitioner
        UnitState
        UnitResult
    end

    subgraph "Boundary System"
        Boundary
        ValidationResult
        BoundaryError
        ValidationError
        NetworkError
    end

    %% Core dependencies
    EventBus --> Event
    TemporalStore --> VersionedState
    StateProjector --> Delta
    EffectMonad --> Effect
    QuantumUnitImpl --> UnitResult
    Boundary --> ValidationResult

    %% Cross-system dependencies
    EventBus -.-> StateProjector
    EventBus -.-> EffectMonad
    EffectMonad -.-> QuantumUnitImpl
    StateProjector -.-> EventBus
    QuantumPartitioner -.-> EventBus
```

## Composite Systems

```mermaid
flowchart TD
    %% Components
    EventBus["EventBus"]
    TemporalStore["TemporalStore"]
    PerspectiveAware["PerspectiveAware"]
    StateProjector["StateProjector"]
    EffectMonad["EffectMonad"]
    EffectHandler["EffectHandler"]
    QuantumPartitioner["QuantumPartitioner"]

    %% Composite Systems
    subgraph "Event-Driven Architecture"
        EventBus --> EffectHandler
        EventBus --> TemporalStore
        EffectHandler --> EffectMonad
        EffectMonad --> TemporalStore
    end

    subgraph "Parallel Workflow Engine"
        QuantumPartitioner --> EventBus
        QuantumPartitioner --> StateProjector
        EventBus --> StateProjector
    end

    subgraph "Adaptive State Management"
        TemporalStore --> PerspectiveAware
        TemporalStore --> StateProjector
        PerspectiveAware --> StateProjector
    end

    %% Cross-cutting connections
    EventBus ===== EventDriven[Event-Driven Architecture]
    QuantumPartitioner ===== ParallelWorkflow[Parallel Workflow Engine]
    TemporalStore ===== AdaptiveState[Adaptive State Management]
```

## Temporal Versioning + State Projection Integration

This diagram shows how Temporal Versioning and State Projection work together as complementary patterns:

```mermaid
flowchart TD
    subgraph "Command Pattern Transitions"
        Delta1["Delta 1: Add Post"]
        Delta2["Delta 2: Edit Draft"]
        Delta3["Delta 3: Update Title"]
        Delta4["Delta 4: Publish"]
    end

    subgraph "State Projector"
        InitialState["Initial State"]
        StateT1["State T1"]
        StateT2["State T2"]
        StateT3["State T3"]
        CurrentState["Current State"]
    end

    subgraph "Temporal Store"
        VersionV1["Version 1: Creation"]
        VersionV2["Version 2: Published"]
    end

    %% State projector transitions (fine-grained)
    InitialState --> |"apply_delta()"| StateT1
    StateT1 --> |"apply_delta()"| StateT2
    StateT2 --> |"apply_delta()"| StateT3
    StateT3 --> |"apply_delta()"| CurrentState

    %% Temporal store snapshots (coarse milestone versions)
    InitialState -.-> |"commit()"| VersionV1
    CurrentState -.-> |"commit()"| VersionV2

    %% Command-to-state relationships
    Delta1 --> StateT1
    Delta2 --> StateT2
    Delta3 --> StateT3
    Delta4 --> CurrentState

    %% Delta relationships
    Delta1 --> Delta2
    Delta2 --> Delta3
    Delta3 --> Delta4

    %% Versioned relationships
    InitialState --> VersionV1
    CurrentState --> VersionV2
```

## NERV Integration with Atlas Architecture

This diagram shows how NERV components integrate with the existing Atlas architecture:

```mermaid
flowchart TD
    subgraph "Atlas Core Components"
        AtlasAgent["Atlas Agent"]
        ProviderSystem["Provider System"]
        KnowledgeSystem["Knowledge System"]
        AgentWorkers["Agent Workers"]
        Orchestrator["Orchestrator"]
    end

    subgraph "NERV Components"
        EventBus["Event Bus"]
        TemporalStore["Temporal Store"]
        EffectSystem["Effect System"]
        PerspectiveSystem["Perspective System"]
        StateProjector["State Projector"]
        QuantumPartitioner["Quantum Partitioner"]
    end

    %% Core integrations
    EventBus <--> |"Event Backbone"| AtlasAgent
    EventBus <--> |"Provider Events"| ProviderSystem
    EventBus <--> |"Knowledge Events"| KnowledgeSystem
    EventBus <--> |"Agent Events"| AgentWorkers
    EventBus <--> |"Workflow Events"| Orchestrator

    %% Feature-specific integrations
    TemporalStore <--> |"Versioned Config"| ProviderSystem
    TemporalStore <--> |"Session History"| AtlasAgent
    TemporalStore <--> |"Knowledge Versions"| KnowledgeSystem

    EffectSystem <--> |"Side Effect Tracking"| ProviderSystem
    EffectSystem <--> |"Tool Invocations"| AtlasAgent

    PerspectiveSystem <--> |"Role-Based Views"| KnowledgeSystem
    PerspectiveSystem <--> |"Context Adaptation"| AtlasAgent

    StateProjector <--> |"Incremental Changes"| KnowledgeSystem
    StateProjector <--> |"State Transitions"| Orchestrator

    QuantumPartitioner <--> |"Parallel Execution"| AgentWorkers
    QuantumPartitioner <--> |"Optimized Provider Dispatch"| ProviderSystem
```

## Document Publishing Workflow

```mermaid
sequenceDiagram
    participant Editor as Editor
    participant StateProj as StateProjector
    participant TempStore as TemporalStore
    participant EventSys as EventBus
    participant PerspectiveView as PerspectiveAware

    note over Editor,PerspectiveView: Document Creation Phase
    Editor->>StateProj: Create new document
    StateProj->>StateProj: Apply delta: add document
    StateProj->>EventSys: Emit DOCUMENT_ADDED event
    EventSys->>TempStore: Create initial version snapshot
    TempStore-->>Editor: Return version_id

    note over Editor,PerspectiveView: Draft Editing Phase
    loop Multiple edits
        Editor->>StateProj: Update document
        StateProj->>StateProj: Apply delta: update content
        StateProj->>EventSys: Emit DOCUMENT_PROCESSED event
    end

    note over Editor,PerspectiveView: Publishing Phase
    Editor->>StateProj: Publish document
    StateProj->>StateProj: Apply delta: set published=true
    StateProj->>EventSys: Emit DOCUMENT_PROCESSED with major_change=true
    EventSys->>TempStore: Create published version snapshot
    TempStore-->>Editor: Return version_id

    note over Editor,PerspectiveView: View Projection
    Editor->>PerspectiveView: Request public view
    PerspectiveView->>StateProj: Get current state
    StateProj-->>PerspectiveView: Return current state
    PerspectiveView->>PerspectiveView: Apply public projection
    PerspectiveView-->>Editor: Return filtered view
```

## Parallel Provider Execution

```mermaid
sequenceDiagram
    participant Client as Client
    participant QPart as QuantumPartitioner
    participant EffectSys as EffectSystem
    participant Prov1 as Provider-Primary
    participant Prov2 as Provider-Backup
    participant Prov3 as Provider-Fallback
    participant EventSys as EventBus

    Client->>QPart: Execute with prompt
    QPart->>QPart: Create execution plan

    par Provider Execution
        QPart->>Prov1: Execute provider unit
        Prov1->>EffectSys: Network connection effect
        EffectSys->>EventSys: Emit PROVIDER_CONNECTED event
        Prov1->>EffectSys: Model call effect
        EffectSys->>EventSys: Emit MODEL_CALL event
        EffectSys-->>Prov1: Return effect result
        Prov1-->>QPart: Return success result
    and
        QPart->>Prov2: Execute provider unit
        Prov2->>EffectSys: Network connection effect
        EffectSys->>EventSys: Emit PROVIDER_CONNECTED event
        Prov2->>EffectSys: Model call effect
        EffectSys->>EventSys: Emit MODEL_CALL event
        EffectSys-->>Prov2: Return effect result
        Prov2-->>QPart: Return error result
    and
        QPart->>Prov3: Execute provider unit
        Prov3->>EffectSys: Network connection effect
        EffectSys->>EventSys: Emit PROVIDER_CONNECTED event
        Prov3->>EffectSys: Model call effect
        EffectSys->>EventSys: Emit MODEL_CALL event
        EffectSys-->>Prov3: Return effect result
        Prov3-->>QPart: Return success result
    end

    QPart->>QPart: Collect results and sort by priority
    QPart-->>Client: Return primary provider result
    EventSys-->>Client: Provider execution events history
```

## Service Architecture (Runtime)

```mermaid
flowchart LR
    User((User)) --> Client

    subgraph "Client Layer"
        Client["Client Interface"]
        StreamHandler["Stream Handler"]
    end

    Client <--> API
    StreamHandler <-- streaming --> StreamController

    subgraph "API Layer"
        API["API Gateway"]
        StreamController["Stream Controller"]
        Throttler["Rate Limiter"]
    end

    API --> Orchestrator

    subgraph "Core Layer"
        Orchestrator["Workflow Orchestrator"]
        EventBus["Central Event Bus"]
        AgentController["Agent Controller"]
        Workers["Worker Agents"]
        ProviderManager["Provider Manager"]
    end

    Orchestrator <--> EventBus
    AgentController <--> EventBus
    Workers <--> EventBus
    ProviderManager <--> EventBus

    ProviderManager --> ProviderPool

    subgraph "Provider Layer"
        ProviderPool["Provider Connection Pool"]
        ProviderStrategy["Provider Selection Strategy"]
        Failover["Failover Handler"]
    end

    subgraph "Knowledge Layer"
        KnowledgeEngine["Knowledge Engine"]
        Retrieval["Retrieval System"]
        DocumentIndex["Document Index"]
    end

    EventBus <--> KnowledgeEngine
    KnowledgeEngine <--> Retrieval
    Retrieval <--> DocumentIndex

    %% NERV Component Integration
    subgraph "NERV Components"
        NervEventBus["EventBus Implementation"]
        TemporalStore["Temporal Store"]
        EffectHandler["Effect Handler"]
        QuantumPartitioner["Quantum Partitioner"]
    end

    EventBus <--> NervEventBus
    ProviderManager <--> TemporalStore
    ProviderManager <--> EffectHandler
    Orchestrator <--> QuantumPartitioner
    AgentController <--> QuantumPartitioner
```
