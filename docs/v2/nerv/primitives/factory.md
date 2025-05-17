---
title: Factory
---


# Factory Pattern

## Overview

The Factory pattern delegates object creation to specialized methods, allowing subclasses to decide which class to instantiate. In NERV, this pattern enables flexible object creation with appropriate configuration, decoupling client code from specific implementations.

## Key Concepts

- **Creator**: Abstract class or interface that declares the factory method
- **Concrete Creator**: Class that implements the factory method
- **Product**: Interface or abstract class for the objects the factory creates
- **Concrete Product**: Specific implementation of the product interface

## Benefits

- **Decoupling**: Separates object creation from usage
- **Encapsulation**: Hides implementation details of object creation
- **Single Responsibility**: Centralizes complex object creation logic
- **Extension**: New products can be added without modifying client code
- **Consistency**: Ensures consistent object initialization

## Implementation Considerations

- **Factory Complexity**: Balance between factory simplicity and flexibility
- **Parameterization**: Determine how to parameterize the factory method
- **Factory Hierarchy**: Design appropriate inheritance for factory classes
- **Product Registration**: Consider dynamic product registration
- **Caching**: Decide whether to cache created objects

## Core Interface

::: info Delta Factory Interface
The Delta class provides factory methods for creating different types of state delta operations:

- **`function_delta(fn: Callable[[S], S]) -> Delta[S]`**:
  Creates a delta from a function that transforms state.

- **`patch_delta(patch: Dict[str, Any]) -> Delta[S]`**:
  Creates a delta from a dictionary patch.
:::

## Pattern Variations

### Simple Factory

A basic implementation with a single method creating objects based on parameters.

### Factory Method

An abstract method in a base class, implemented by subclasses to create appropriate objects.

### Abstract Factory

A family of related factory methods for creating families of related objects.

### Static Factory

Static methods that create objects, eliminating the need for factory instance creation.

## Integration in NERV

The Factory pattern is used throughout NERV for creating various objects:

- **Delta Factories**: Creating different types of state delta objects
- **Provider Factories**: Creating appropriate provider instances
- **Agent Factories**: Creating specialized agent instances
- **Resource Factories**: Creating managed system resources

## Implementation Details

::: details Factory Implementation Strategies
Common factory implementation strategies include:

### 1. Simple Factory
- Uses a static method with a type parameter
- Selects concrete implementation based on the type
- Initializes the instance with provided parameters
- Example: `SimpleFactory.create("A", param1=value1)`

### 2. Factory Method Pattern
- Abstract creator class defines factory method interface
- Concrete creator subclasses implement the factory method
- Creators can provide additional initialization logic
- Example: `ConcreteCreatorA().create_product(param1=value1)`

### 3. Abstract Factory Pattern
- Interface for creating families of related objects
- Multiple factory methods for different product types
- Concrete factory implementations for different product families
- Example: `ConcreteFactory1().create_product_a(param1=value1)`

### 4. Static Factory with Registration
- Registry of product classes mapped to type identifiers
- Dynamic registration of product implementations
- Creation based on registered types
- Example: `StaticFactory.register("A", ProductA)` and then `StaticFactory.create("A", param1=value1)`
:::

## State Delta Factory Example

::: tip State Delta Application
The state delta factory creates specialized delta objects:

1. **Function Delta**: Applies a transformation function to a state
   - Created with: `Delta.function_delta(lambda state: modified_state)`
   - Useful for complex transformations with custom logic

2. **Patch Delta**: Applies a dictionary patch to a state
   - Created with: `Delta.patch_delta({"field1": "new_value"})`
   - Useful for simple field updates or additions
:::

## Usage in NERV Components

- **StateProjector**: Creates appropriate delta types using factory methods
- **ProviderResolver**: Creates provider instances based on requirements
- **ResourceManager**: Creates managed resources with appropriate configuration
- **AgentController**: Creates worker agents for specific tasks

## Related NERV Patterns

- **[State Projection](../patterns/state_projection.md)**: Uses factory methods for delta creation
- **[Reactive Event Mesh](../patterns/reactive_event_mesh.md)**: Uses factories for event creation
- **[Effect System](../patterns/effect_system.md)**: Uses factories for effect creation

## Related Design Patterns

- Builder Pattern
- Abstract Factory Pattern
- Prototype Pattern
- Singleton Pattern
