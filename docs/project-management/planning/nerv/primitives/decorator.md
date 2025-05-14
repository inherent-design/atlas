---
title: Decorator
---

# Decorator Pattern

## Overview

The Decorator pattern attaches additional responsibilities to objects dynamically, providing a flexible alternative to subclassing for extending functionality. In NERV, this pattern enables composition of behaviors, enhancing objects with additional capabilities without modifying their core implementation.

## Key Concepts

- **Component Interface**: Common interface for both decorators and decorated objects
- **Concrete Component**: Base object that can be decorated
- **Decorator**: Maintains a reference to a component object and conforms to its interface
- **Concrete Decorator**: Adds responsibilities to the component

## Benefits

- **Dynamic Extension**: Add behaviors to objects at runtime
- **Composition Over Inheritance**: Avoid class explosion from inheritance hierarchies
- **Single Responsibility**: Keep classes focused on core functionality
- **Open/Closed Principle**: Extend behavior without modifying existing code
- **Combinatorial Flexibility**: Mix and match decorators in any order

## Implementation Considerations

- **Interface Conformance**: Ensure decorators preserve the component interface
- **Decoration Order**: Consider how order affects behavior when multiple decorators are used
- **Performance**: Be aware of potential overhead from multiple decorator layers
- **Transparency**: Make decorator presence transparent to clients
- **State Sharing**: Handle state consistently across decorator layers

## Core Interface

::: info Core Decorator Interface
The Effect Monad demonstrates the decorator pattern with its extension method:

```typescript
// TypeScript-like pseudo-code
interface Effectful<T> {
  withEffect(effect: Effect): Effectful<T>;
}
```
:::

## Pattern Variations

### Class-Based Decorator

Traditional implementation using object composition with the same interface.

::: tip Example
```typescript
// TypeScript-like pseudo-code
interface Component {
  operation(): string;
}

class ConcreteComponent implements Component {
  operation(): string {
    return "ConcreteComponent";
  }
}

abstract class Decorator implements Component {
  constructor(protected component: Component) {}
  abstract operation(): string;
}

class ConcreteDecoratorA extends Decorator {
  operation(): string {
    return `DecoratorA(${this.component.operation()})`;
  }
}

// Usage
const component = new ConcreteComponent();
const decorated = new ConcreteDecoratorA(component);
console.log(decorated.operation()); // Output: DecoratorA(ConcreteComponent)
```
:::

### Function-Based Decorator

Uses higher-order functions to wrap and enhance function behavior.

::: warning Common Pitfall
When using function decorators, be careful to preserve function metadata like name and docstrings, as they can be lost during decoration.
:::

### Parameterized Decorator

Decorators that accept parameters to customize their behavior.

### Mixin Decorator

Uses multiple inheritance to add functionality to a class.

## Integration in NERV

The Decorator pattern is used throughout NERV in these contexts:

- **Effect System**: Decorating operations with side effects
- **Stream Processing**: Adding behaviors to stream handlers
- **Middleware**: Enhancing event propagation in the event bus
- **Telemetry**: Adding observability to components

::: details EffectMonad Implementation
The EffectMonad uses the decorator pattern to attach side effects to operations. Each effect decorator wraps the original value while adding a new effect to the effect collection. The pattern allows for composing multiple effects while maintaining the original value's identity and providing a clean way to handle effects separately from core logic.
:::

## Usage in NERV Components

- **EffectMonad**: Uses decorator pattern to add effects to operations
- **StreamHandler**: Decorators add functionality like buffering or throttling
- **EventBus**: Middleware acts as decorators for event processing
- **ResourceManager**: Decorators add monitoring to resource operations

## Related NERV Patterns

- **[Effect System](../patterns/effect_system.md)**: Uses decorator pattern extensively
- **[Reactive Event Mesh](../patterns/reactive_event_mesh.md)**: Uses decorators for event middleware
- **[Temporal Versioning](../patterns/temporal_versioning.md)**: Can use decorators for versioning

## Related Design Patterns

- Composite Pattern
- Strategy Pattern
- Chain of Responsibility
- Proxy Pattern