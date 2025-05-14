---
title: Builder
---

# Builder Pattern

## Overview

The Builder pattern separates the construction of a complex object from its representation, allowing the same construction process to create different representations. In NERV, this pattern enables the creation of complex execution plans, workflows, and object trees while keeping construction logic separate from business logic.

## Key Concepts

- **Builder**: Interface or class that defines steps to create parts of a complex object
- **ConcreteBuilder**: Specific implementations of the builder interface
- **Director**: Optional class that constructs an object using the builder's interface
- **Product**: The complex object being built

## Benefits

- **Step-by-Step Construction**: Create complex objects one step at a time
- **Separate Construction Logic**: Keep construction code separate from business logic
- **Reusable Construction Process**: Same process can create different representations
- **Complex Object Creation**: Hide complexity of instantiation from clients
- **Parameter Control**: Avoid telescoping constructors

## Implementation Considerations

- **Builder Complexity**: Balance between flexibility and complexity
- **Required vs. Optional Parameters**: Handle varying parameters elegantly
- **Builder Reuse**: Design for builder reusability when appropriate
- **Validation**: Consider when to validate parameters (per-step or final product)
- **Immutability**: Decide whether builders should be immutable

## Core Interface

::: info Core Builder Interface
The QuantumPartitioner class demonstrates the builder interface:

- `add_unit()` - Adds a computation unit with its dependencies
- `build_execution_plan()` - Constructs the final execution plan
:::

## Pattern Variations

### Fluent Builder

Provides method chaining for a more readable and fluid API.

::: tip Example Usage
```typescript
// TypeScript-like pseudo-code example
const workflow = new WorkflowBuilder()
  .addStep("download")
  .withTimeout(30)
  .addStep("process")
  .withRetries(3)
  .build();
```
:::

### Stepwise Builder

Forces construction in a specific sequence to ensure correct initialization.

### Recursive Builder

Builders that can build hierarchical or nested structures.

### Type-Safe Builder

Uses generics and type parameters to ensure type safety during construction.

## Integration in NERV

The Builder pattern is primarily implemented in these NERV components:

- **QuantumPartitioner**: Builds complex execution plans step by step
- **ExecutionPlan**: Constructed by the partitioner through staged building
- **WorkflowBuilder**: Constructs complex workflows with conditional paths
- **QueryBuilder**: Constructs sophisticated queries with multiple parameters

::: details Implementation Description
The implementation uses a fluent API with method chaining to build complex objects incrementally. It maintains type safety through generics and provides progressive construction with validation at each step. The builder keeps track of all added components and their relationships, ultimately constructing an optimized execution plan.
:::

## Usage in NERV Components

- **QuantumPartitioner**: Builds dependency-aware execution plans
- **ExecutionPlan**: Constructed incrementally with units and dependencies
- **WorkflowEngine**: Uses builders to construct complex workflows
- **QueryBuilder**: Constructs and executes sophisticated queries

## Related NERV Patterns

- **[Quantum Partitioning](../patterns/quantum_partitioning.md)**: Built directly on Builder pattern
- **[State Projection](../patterns/state_projection.md)**: Uses builder concepts for projection setup
- **[Effect System](../patterns/effect_system.md)**: Can use builders for complex effect chains

## Related Design Patterns

- Factory Method Pattern
- Abstract Factory Pattern
- Composite Pattern
- Fluent Interface