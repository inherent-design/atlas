---
title: Primitives
---

# Primitives: Foundational Design Patterns

This document describes the fundamental design patterns that serve as primitives in the NERV architecture - the basic building blocks from which more complex patterns and components are constructed.

## Overview

While the NERV architecture defines its own higher-level patterns (Reactive Event Mesh, Temporal Versioning, etc.), these patterns are built upon well-established foundational design patterns from software engineering. These primitives form the atomic building blocks of our architecture - they are the basic elements from which all higher-level components are constructed.

## Core Primitive Patterns

| Pattern | Purpose | NERV Usage | Implementation Library |
|---------|---------|------------|------------------------|
| **[Observer](observer.md)** | Enable notification of state changes | Event notification and reactive programming | Blinker |
| **[Command](command.md)** | Encapsulate operations as objects | Explicit side effect management | Effect |
| **[Monad](monad.md)** | Encapsulate computation with context | Functional composition with effects | Effect |
| **[Strategy](strategy.md)** | Define family of interchangeable algorithms | Runtime algorithm selection | Python protocols |
| **[Builder](builder.md)** | Construct complex objects step by step | Multi-stage object construction | Python dataclasses |
| **[DAG](dag.md)** | Organize nodes with dependencies | Dependency-based scheduling | TaskMap |
| **[Factory](factory.md)** | Delegate object creation to specialized methods | Object creation with configuration | Static methods |
| **[Decorator](decorator.md)** | Add behavior to objects dynamically | Adding capabilities without inheritance | Python decorators |

## Pattern Relationships to NERV Architecture

The primitives form the foundation for NERV's higher-level architectural patterns:

| NERV Pattern | Primitive Composition | Implementation Libraries |
|--------------|------------------------|-------------------------|
| [Reactive Event Mesh](../patterns/reactive_event_mesh.md) | Observer + Command + Factory | Blinker |
| [Temporal Versioning](../patterns/temporal_versioning.md) | Command + Decorator + Factory | Eventsourcing |
| [Perspective Shifting](../patterns/perspective_shifting.md) | Strategy + Decorator + Factory | Marshmallow |
| [State Projection](../patterns/state_projection.md) | Command + Strategy + Builder | Pyrsistent |
| [Effect System](../patterns/effect_system.md) | Command + Monad + Decorator | Effect |
| [Quantum Partitioning](../patterns/quantum_partitioning.md) | Builder + DAG + Factory | TaskMap |

## Key Primitive Implementations

Each primitive pattern is implemented using specific libraries within NERV:

- **Observer Pattern**: [Blinker](https://pythonhosted.org/blinker/) library for signal dispatch (EventBus)
- **Command Pattern**: [Effect](https://github.com/python-effect/effect) library for effect descriptions
- **Monad Pattern**: [Effect](https://github.com/python-effect/effect) library for monadic operations
- **Strategy Pattern**: Python protocols with [Marshmallow](https://marshmallow.readthedocs.io/en/stable/) for schema-based transformations
- **Builder Pattern**: Python dataclasses with builder methods in QuantumPartitioner
- **DAG Pattern**: [TaskMap](https://github.com/dask/taskmap) library for dependency execution
- **Factory Pattern**: Static factory methods on various domain classes
- **Decorator Pattern**: Python decorators and function wrappers for aspect-oriented programming

## Implementation Guidance

When implementing NERV components, consider these primitive patterns:

1. **Favor composition over inheritance** by using these patterns to combine behaviors
2. **Make interfaces explicit** by clearly defining the pattern relationships
3. **Consider pattern combinations** to solve complex problems
4. **Document pattern usage** to explain design decisions and architecture
5. **Leverage library primitives** when available to reduce custom implementation

Understanding these primitives is crucial for effective implementation of the NERV architecture, as they form the foundation upon which all higher-level patterns and components are built.

## Cross-Cutting Architectural Properties

The primitive patterns combined in NERV create these emergent architectural properties:

| Property | Description | Enabled By | Primary Libraries |
|----------|-------------|------------|--------------------|
| **Decoupling** | Components can evolve independently | Observer, Command | Blinker, Effect |
| **Composability** | Simple units combine into complex behaviors | Monad, Decorator | Effect, Python decorators |
| **Extensibility** | New behaviors without changing core code | Strategy, Factory | Marshmallow, Python protocols |
| **Observability** | Introspection of system behavior | Observer, Command | Blinker, Effect |
| **Parallelism** | Efficient concurrent execution | DAG, Builder | TaskMap |
| **Flexibility** | Runtime adaptation to changing needs | Strategy, Decorator | Marshmallow, Python decorators |

## Learn More

For detailed explanations and implementation examples of each primitive pattern, see their individual documentation pages:

- [Observer Pattern](observer.md): Event notification system (Blinker)
- [Command Pattern](command.md): Encapsulated operations (Effect)
- [Monad Pattern](monad.md): Computation with context (Effect)
- [Strategy Pattern](strategy.md): Interchangeable algorithms (Python protocols)
- [Builder Pattern](builder.md): Step-by-step construction (Python dataclasses)
- [DAG Pattern](dag.md): Dependency management (TaskMap)
- [Factory Pattern](factory.md): Delegated object creation (Static methods)
- [Decorator Pattern](decorator.md): Dynamic behavior addition (Python decorators)