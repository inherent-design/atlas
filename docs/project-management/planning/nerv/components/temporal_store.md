---
title: Temporal Store
---

# TemporalStore Implementation

## Overview

The TemporalStore provides a versioned state container that maintains a complete history of all changes. It enables time travel, auditing, and analysis by preserving the entire state evolution.

## Architectural Role

The TemporalStore serves as the foundation for stateful components in Atlas:

- **Configuration**: Versioned configuration management
- **Provider State**: Historical provider performance and behavior
- **Agent State**: Evolution of agent behavior and decisions
- **Knowledge**: Document version history
- **Workflows**: Execution state snapshots

## Implementation Details

The TemporalStore implementation features:

1. **Immutable state versions** using deep copying
2. **Parent-child relationships** between versions
3. **Metadata** such as timestamps and descriptions
4. **Traversable history** for analysis and recovery
5. **Optional branching** for exploring alternative states
6. **Event-sourced architecture** for reliable persistence and recovery

## Key Components

- **VersionedState**: Dataclass containing state data and metadata
- **VersionId**: Unique identifier for each version
- **Version Graph**: Structure representing parent-child relationships
- **Commit**: Operation that creates a new version
- **Event Store**: Storage for domain events
- **Snapshot Strategy**: Optimization for faster recovery

## Implementation Library: Eventsourcing

The TemporalStore is implemented using the Python Eventsourcing library, which provides a robust foundation for building event-sourced systems. The Eventsourcing library offers:

- **Domain-driven design support** for developing event-sourced applications
- **Event storage and retrieval** mechanisms with various database backends
- **Snapshotting** for optimized application recovery
- **Version-based concurrency control** to prevent conflicts
- **Transcript recording** for reliable auditing and debugging

The Eventsourcing library uses a domain-driven design approach where the state of an application is determined by a sequence of events. This perfectly aligns with the TemporalStore's goals of maintaining complete history and enabling time travel.

### Core Eventsourcing Concepts

The TemporalStore leverages several key concepts from the Eventsourcing library:

1. **Domain Events**: Immutable records of things that happened
   
   Events like `DocumentCreated` and `DocumentEdited` capture state changes with all relevant metadata including timestamps, authors, and specific changes made. These events form the foundation of the event-sourced system, allowing complete state reconstruction.

2. **Aggregate Root**: Entity that maintains consistency boundaries
   
   The Aggregate pattern provides a clean boundary for state changes, ensuring that all modifications happen in a consistent way through well-defined methods. Each aggregate (like a Document) maintains its internal state and triggers appropriate events when that state changes.

3. **Application**: Coordinates aggregates and provides access to state
   
   The Application layer (such as DocumentManager) handles the coordination between client code and aggregates, providing high-level operations like creating and editing documents. It's responsible for persisting events and retrieving aggregates when needed.

4. **Event Store**: Persistence mechanism for domain events
   
   The Event Store persists all domain events, providing the foundation for reconstructing state. Eventsourcing supports multiple database backends including PostgreSQL and SQLite, with configurable serialization options.

5. **Snapshots**: Optimization for faster aggregate recovery
   
   Snapshots provide a performance optimization by periodically capturing the complete state of an aggregate, reducing the number of events that need to be replayed during recovery. This is especially important for aggregates with many events.

### TemporalStore Implementation Architecture

Our TemporalStore implementation builds on the Eventsourcing library to provide a comprehensive solution for versioned state management. This implementation is structured around several core components:

#### Domain Events

The system defines specific event types that represent changes to versioned state:

- `StateCreated`: Marks the creation of initial state
- `StateUpdated`: Records updates to existing state
- `BranchCreated`: Tracks the creation of new branches
- `BranchMerged`: Records branch merge operations

#### Core Components

1. **VersionedStateAggregate**: The central aggregate that manages state versions, with functionalities for:
   - Maintaining the current state data
   - Managing version metadata including timestamps and descriptions
   - Supporting branching operations with branch creation and switching
   - Providing version history traversal
   - Implementing merge strategies for branch reconciliation

2. **TemporalStore**: The application layer providing high-level operations:
   - Creating new versioned stores
   - Managing state updates and version creation
   - Retrieving current and historical states
   - Providing version metadata for analysis
   - Supporting branch operations and version control features

3. **SnapshottingTemporalStore**: An optimized implementation that adds:
   - Periodic snapshots of aggregate state
   - Improved performance for long-lived state histories
   - Configurable snapshot frequency based on event count

## Performance Considerations

The TemporalStore implementation incorporates several performance optimizations to ensure efficient operation even with large histories:

- **Memory Usage**: Optimized by storing references when safe and using efficient event serialization
- **Copy Depth**: Configurable to balance safety and performance
- **Garbage Collection**: Optional pruning of old versions to manage memory growth
- **Serialization**: Support for externalization of versions to persistent storage
- **Snapshots**: Strategic snapshots to reduce event replay during recovery
- **Batched Operations**: Optimized event batch processing for bulk operations

### Eventsourcing Performance Optimizations

With the Eventsourcing library, several key performance optimizations are implemented:

1. **Custom Compression for Event Data**
   
   A specialized `CompressingJSONTranscoder` provides automatic compression of event data using zlib, reducing storage requirements and improving I/O throughput. This is particularly effective for large state objects with repeated data structures.

2. **Memory-Optimized Repository for Development**
   
   When working in development environments, an in-memory repository configuration uses weak references to allow garbage collection of unused aggregates, reducing memory pressure during development and testing.

3. **Batched Operations for Better Performance**
   
   The implementation supports batched operations for better throughput, automatically managing transactions and providing rollback capabilities. This significantly improves performance when making multiple updates in sequence.

4. **Optimized Event Serialization**
   
   Specialized encoders and decoders minimize serialization overhead, with custom handling for dataclasses and other common structures. This reduces both CPU usage and storage size.

### Performance Benchmarks and Scaling

The TemporalStore implementation includes comprehensive benchmarking capabilities to measure:

- Creation time for new stores
- Update throughput (events per second)
- Retrieval time for current state
- Retrieval time for historical versions
- Metadata retrieval performance

Benchmark results show significant performance improvements when using snapshotting, particularly for historical state retrieval, with performance differences becoming more pronounced as the event history grows.

### Memory Optimization Techniques

To optimize memory usage in production systems with the Eventsourcing library, several techniques are implemented:

1. **Strategic Snapshotting**
   
   The implementation supports adaptive snapshotting strategies that can trigger snapshots based on:
   - Number of events since last snapshot
   - Size of accumulated events
   - Time elapsed since last snapshot

2. **Event Stream Compaction**
   
   For long-running systems, event stream compaction techniques minimize storage requirements by creating snapshots and archiving old events that are no longer needed for immediate access.

3. **Selective Event Storage**
   
   The system optimizes event payloads by:
   - Replacing large binary data with references
   - Compressing large collections within events
   - Storing only differential changes when appropriate

## Integration with Atlas

The TemporalStore is used by:

- **Configuration System**: For configuration versioning
- **Agent Framework**: For tracking agent state evolution
- **Provider System**: For provider configuration history
- **Knowledge Store**: For document versioning
- **Graph System**: For graph state evolution

## Usage Patterns

### Linear Version History

::: info Basic Versioning Example
The TemporalStore provides a straightforward API for linear version history tracking:

1. **Creating a store** with initial state (document, configuration, etc.)
2. **Committing new versions** with descriptive messages and metadata
3. **Retrieving current state** to work with the latest version
4. **Exploring version history** to understand the evolution of state

This pattern is ideal for tracking document edits, configuration changes, or any state that evolves linearly over time.
:::

### Time Travel

::: tip Time Travel Operations
The TemporalStore supports rich time-travel operations:

1. **Retrieving specific versions** by version number or identifier
2. **Getting state at a timestamp** to see what was current at a specific time
3. **Reverting to previous versions** as a basis for new changes
4. **Navigating relative versions** (N versions back or forward)

These capabilities enable powerful use cases like "undo/redo" functionality, historical audits, and point-in-time recovery.
:::

### Version Analysis

::: details Version Metadata Analysis
Beyond basic versioning, the TemporalStore provides rich metadata capabilities:

1. **Collecting version metadata** across the entire history
2. **Filtering versions by author** to track individual contributions
3. **Analyzing edit patterns** such as frequency, timing, and content focus
4. **Comparing versions** to understand what changed between points in time

These analytical features enable insights into collaborative workflows, usage patterns, and state evolution over time.
:::

### Branching (Advanced)

::: warning Advanced Branching
For more complex scenarios, the TemporalStore supports Git-like branching operations:

1. **Creating branches** from any version point
2. **Working on parallel branches** with independent version histories
3. **Switching between branches** to work in different contexts
4. **Merging branches** with configurable merge strategies

This advanced functionality enables experimental work, parallel feature development, and complex collaborative workflows.
:::

## Relationship to Patterns

Implements:
- **[Temporal Versioning](../patterns/temporal_versioning.md)**: Primary implementation

Supports:
- **[Reactive Event Mesh](../patterns/reactive_event_mesh.md)**: Version changes can emit events
- **[Perspective Shifting](../patterns/perspective_shifting.md)**: Versions can be viewed in different ways
- **[State Projection](../patterns/state_projection.md)**: Complementary approach to state tracking
- **[Effect System](../patterns/effect_system.md)**: Version changes can be modeled as effects