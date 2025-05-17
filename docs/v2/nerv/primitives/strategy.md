---
title: Strategy
---

# Strategy Pattern

## Overview

The Strategy pattern defines a family of algorithms, encapsulates each one, and makes them interchangeable at runtime. This pattern enables selecting an algorithm's implementation independently from clients that use it. In NERV, this pattern forms the foundation for Perspective Shifting and State Projection.

## Key Concepts

- **Strategy Interface**: Common interface for all algorithm variants
- **Concrete Strategies**: Specific implementations of the algorithm
- **Context**: Maintains a reference to a strategy object and delegates to it
- **Client**: Configures the context with the desired strategy

## Benefits

- **Flexibility**: Algorithms can be selected and switched at runtime
- **Isolation**: Implementation details are isolated from clients
- **Elimination of Conditionals**: Replaces complex conditionals with strategy selection
- **Extension**: New strategies can be added without modifying existing code
- **Testability**: Strategies can be tested independently

## Implementation Considerations

- **Strategy Granularity**: Determine the right scope for strategy interfaces
- **State Sharing**: Consider how strategies share state with their context
- **Performance**: Be aware of potential overhead from strategy switching
- **Default Strategies**: Provide sensible defaults for common cases
- **Strategy Creation**: Consider using factories for complex strategy creation

## Core Interface

::: info Core Strategy Interface
The Projectable interface demonstrates the Strategy pattern:

```typescript
// TypeScript-like pseudo-code
interface Projectable<S, P> {
  addProjection(name: string, projectionFn: (source: S) => P): void;
  project(projection: string = "default"): P;
}
```
:::

## Pattern Variations

### Function-Based Strategy

Uses function objects instead of strategy classes, ideal for simple algorithms.

::: tip Example
```typescript
// TypeScript-like pseudo-code for function-based strategy
interface SortStrategy<T> {
  (items: T[]): T[];
}

class Sorter<T> {
  constructor(private strategy: SortStrategy<T>) {}

  sort(items: T[]): T[] {
    return this.strategy(items);
  }

  setStrategy(strategy: SortStrategy<T>): void {
    this.strategy = strategy;
  }
}

// Usage
const quickSort = <T>(items: T[]): T[] => { /* implementation */ };
const mergeSort = <T>(items: T[]): T[] => { /* implementation */ };

const sorter = new Sorter(quickSort);
sorter.setStrategy(mergeSort); // Switch strategy at runtime
```
:::

### Parameterized Strategy

Strategies that accept parameters to customize their behavior.

### Composite Strategy

Strategies composed of multiple sub-strategies.

### Adaptive Strategy

Strategies that can change their behavior based on execution context.

## Integration in NERV

The Strategy pattern is primarily implemented in these NERV patterns:

- **Perspective Shifting**: Different projection strategies for the same data
- **State Projection**: Different strategies for projecting state
- **Provider Selection**: Different strategies for selecting providers

::: details Implementation Description
The NERV implementation supports both function-based and class-based strategy approaches. Function-based strategies are lightweight and ideal for simpler algorithms, while class-based strategies are better for more complex implementations that need to maintain internal state. The system includes a registry for named strategies, allowing dynamic selection at runtime, and supports parameterized strategies for customizable behavior.
:::

## Usage in NERV Components

- **PerspectiveAware**: Uses strategies to provide different views of data
- **StateProjector**: Uses strategies to project state in different ways
- **ProviderResolver**: Uses strategies to select appropriate providers
- **QuantumPartitioner**: Uses strategies for partitioning execution plans

## Related NERV Patterns

- **[Perspective Shifting](../patterns/perspective_shifting.md)**: Built directly on Strategy pattern
- **[State Projection](../patterns/state_projection.md)**: Uses strategies for projections
- **[Effect System](../patterns/effect_system.md)**: Can use strategies for effect handling

## Related Design Patterns

- Command Pattern
- Decorator Pattern
- Factory Method Pattern
- Template Method Pattern
