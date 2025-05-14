---
title: Command
---

# Command Pattern

## Overview

The Command pattern encapsulates a request or action as an object, allowing parameterization of clients with different requests, queuing of requests, and logging of operations. In NERV, this pattern forms the foundation for the Effect System and enables explicit tracking of side effects.

## Key Concepts

- **Command**: An object that encapsulates an action and its parameters
- **Invoker**: Triggers the command execution
- **Receiver**: Performs the actual work when the command is executed
- **Client**: Creates command objects and sets their receiver

## Benefits

- **Decoupling**: Separates object that invokes operations from objects that perform them
- **Extensibility**: New commands can be added without changing existing code
- **Composability**: Simple commands can be composed into complex ones
- **Undoable Operations**: Commands can store state for undoing operations
- **Queueing & Scheduling**: Commands can be queued, prioritized, and executed asynchronously
- **Logging & Auditing**: Command execution can be logged for debugging or compliance

## Implementation Considerations

- **Command Granularity**: Strike a balance between too fine-grained and too coarse
- **Undo/Redo**: Design commands to support reversible operations if needed
- **Performance**: Consider overhead of object creation for frequent commands
- **State Capture**: Determine how much state to capture for undo operations
- **Error Handling**: Decide how to handle command execution failures

## Core Interface

::: info Command Interface
The Command interface defines a standard structure for encapsulated operations:

- **`execute(): Result`**:  
  Executes the command and returns the result.

- **`can_execute(): boolean`**:  
  Determines if the command is valid to execute.

- **`undo(): void`** *(optional)*:  
  Reverses the effects of the command if supported.
:::

## Pattern Variations

### Simple Command

Basic implementation where commands encapsulate an action and its parameters.

### Macro Command

Composes multiple commands into a single command that executes them in sequence.

::: tip Macro Command Example
A macro command might combine several related operations:
```
SaveDocumentCommand
GenerateThumbnailCommand
UpdateIndexCommand
NotifyCollaboratorsCommand
```
These commands are grouped and executed together as a single command operation.
:::

### Undoable Command

Commands that store state to enable undoing the operation.

::: details Undoable Command Structure
An undoable command typically:
1. Captures the initial state before execution
2. Performs the requested operation
3. Maintains both initial and new states
4. Provides an undo method to revert to initial state
5. May support a redo operation to reapply changes
:::

### Queueable Command

Commands designed to be placed in a queue and executed asynchronously.

## Library Implementation: Effect

In NERV, we implement the Command pattern using the [Effect](https://github.com/python-effect/effect) library, which provides a framework for describing and executing effects as commands:

### Key Library Components

| Library Component | Description | Usage in NERV |
|-------------------|-------------|---------------|
| `Effect` base class | Core command representation | Foundation for all effect commands |
| `TypedEffect` class | Type-specific command variant | Domain-specific effect commands |
| `Dispatcher` class | Command invoker | Routes effect commands to handlers |
| `sync_performer` decorator | Command handler registration | Registers synchronous command handlers |
| `async_performer` decorator | Async command handler registration | Registers asynchronous command handlers |
| `perform` function | Command execution | Executes effect commands with appropriate handlers |
| `ComposedPerformer` class | Composite command handler | Combines multiple command handlers |

### Core Type Definitions

```python
from typing import TypeVar, Any, Dict
from enum import Enum, auto
from dataclasses import dataclass
from effect import Effect as EffectBase, TypedEffect

R = TypeVar('R')  # Result type

class EffectType(Enum):
    """Types of effect commands in the system."""
    FILE_READ = auto()
    FILE_WRITE = auto()
    MODEL_CALL = auto()
    TOOL_INVOKE = auto()
    # Additional effect types...

@dataclass
class Effect:
    """Command representation of a side effect."""
    type: EffectType
    payload: Any = None
    description: str = ""
```

### Command Execution Flow

The Effect library implements a sophisticated command execution flow:

1. **Command Creation**: Effects are created as immutable command objects
2. **Command Registration**: Handlers are registered for different command types
3. **Command Dispatch**: The dispatcher routes commands to appropriate handlers
4. **Command Execution**: Handlers execute the commands and return results
5. **Command Composition**: Multiple commands can be chained or combined

### Handler Implementation

The Effect library enables different handler implementation strategies:

```python
from effect import sync_performer, ComposedPerformer, TypeDispatcher

# Register a command handler
@sync_performer
def perform_file_read(dispatcher, effect):
    """Handler for file read commands."""
    path = effect.payload.get("path")
    with open(path, 'r') as f:
        return f.read()

# Compose multiple handlers
performer = ComposedPerformer([
    (FileReadEffect, perform_file_read),
    (ModelCallEffect, perform_model_call),
    (ToolInvokeEffect, perform_tool_invoke)
])
```

## Integration in NERV

The Command pattern is primarily implemented in the Effect System, where effects represent commands to be executed:

- **Effect Objects**: Immutable command objects describing side effects
- **Effect Handlers**: Receivers that process different types of effects
- **EffectMonad**: Manages and composes multiple effect commands
- **Higher-Order Effects**: Effects that modify or control other effects

::: details Command Implementation Strategy
The NERV implementation uses:

1. **Registry-Based Handling**:
   - Registry maps effect types to appropriate handlers
   - Dynamic registration of new handlers
   - Fallback handlers for unknown effect types

2. **Command Lifecycle**:
   - Creation: Command objects are immutable once created
   - Validation: Commands validate before execution
   - Execution: Handler processes the command
   - Auditing: Command execution is logged
   - Completion: Results returned to invoker

3. **Error Management**:
   - Error wrapping preserves context
   - Optional retry mechanisms
   - Compensating actions for partial failures
:::

## Usage in NERV Components

- **Effect System**: Modeling operations as explicit effects to be handled
- **State Projection**: Delta operations as commands to modify state
- **Resource Management**: Resource allocation/deallocation commands
- **Workflow Engine**: Tasks as commands within workflow execution

## Related NERV Patterns

- **[Effect System](../patterns/effect_system.md)**: Built directly on Command pattern
- **[State Projection](../patterns/state_projection.md)**: Uses commands to modify state
- **[Reactive Event Mesh](../patterns/reactive_event_mesh.md)**: Events often trigger commands

## Related Design Patterns

- **Monad Pattern**: Commands can be composed like monadic operations
- **Strategy Pattern**: Different command implementations provide alternative algorithms
- **Memento Pattern**: Commands can use mementos to support undo operations
- **Chain of Responsibility**: Commands can be processed through a handler chain
- **Visitor Pattern**: Commands can act as visitors to different object structures