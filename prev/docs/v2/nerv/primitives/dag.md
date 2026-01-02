---
title: DAG
---

# Directed Acyclic Graph (DAG) Pattern

## Overview

The Directed Acyclic Graph (DAG) pattern organizes nodes with directed edges to represent dependencies, ensuring no cycles exist. In NERV, this pattern enables dependency-aware scheduling, parallelizable computation, and complex workflow orchestration.

## Key Concepts

- **Node**: Discrete unit of computation, data, or logic
- **Edge**: Directed connection indicating dependency or data flow
- **Topological Ordering**: A sequence of nodes where dependencies come before dependents
- **Parallelization Levels**: Groups of nodes that can be processed in parallel

## Benefits

- **Clear Dependencies**: Explicit representation of dependencies between components
- **Optimal Parallelism**: Maximize parallelizable execution while respecting dependencies
- **Execution Planning**: Determine optimal execution order for complex tasks
- **Cycle Detection**: Ensure absence of circular dependencies
- **Resource Optimization**: Schedule tasks efficiently based on dependencies

## Implementation Considerations

- **Node Granularity**: Balance between too fine-grained and too coarse
- **Edge Representation**: Choose appropriate data structures for edges
- **Dynamic vs. Static**: Decide whether graph can change during execution
- **Cycle Detection**: Implement efficient cycle detection algorithms
- **Resource Constraints**: Consider resource limitations when scheduling

## Core Interface

::: info Core DAG Interface
The ExecutionPlan demonstrates the DAG pattern interface:

```typescript
// TypeScript-like pseudo-code
interface ExecutionPlan {
  buildDependencyGraph(): Map<string, Set<string>>;
  computeLevels(): string[][];
}
```
:::

## Pattern Variations

### In-Memory DAG

Represents graph structure entirely in memory for fast traversal.

::: tip Implementation Example
```typescript
// TypeScript-like pseudo-code for a basic in-memory DAG
class InMemoryDAG<T> {
  private nodes: Map<string, T> = new Map();
  private edges: Map<string, Set<string>> = new Map();

  addNode(id: string, data: T): void {
    this.nodes.set(id, data);
    this.edges.set(id, new Set());
  }

  addEdge(from: string, to: string): void {
    // Assuming cycle detection happens here
    this.edges.get(from)?.add(to);
  }

  getTopologicalOrder(): string[] {
    // Implementation details...
  }
}
```
:::

### Event-Driven DAG

Executes nodes when their dependencies are satisfied via event notifications.

### Persistent DAG

Stores graph structure persistently for recovery and long-running workflows.

### Hierarchical DAG

Organizes nodes in a hierarchical structure with nested DAGs.

## Integration in NERV

The DAG pattern is primarily implemented in the Quantum Partitioning pattern:

- **ExecutionPlan**: Core implementation of the DAG structure
- **Dependency Tracking**: Explicit tracking of node dependencies
- **Level Computation**: Determining execution levels for parallelism
- **Execution Scheduling**: Scheduling execution based on dependency satisfaction

::: details Implementation Approach
The NERV implementation uses adjacency lists for efficient edge representation, with both forward (dependencies) and reverse (dependents) edges for quick traversal in either direction. It implements Kahn's algorithm for topological sorting and level computation, and detects cycles during edge addition to prevent invalid states. The execution plan pre-computes parallelization levels to optimize resource utilization during runtime.
:::

## Usage in NERV Components

- **ExecutionPlan**: Organizes compute units based on dependencies
- **QuantumPartitioner**: Uses DAG for optimal parallelization
- **WorkflowEngine**: Models workflows as DAGs for execution
- **Build System**: Organizes build steps as a dependency graph

## Related NERV Patterns

- **[Quantum Partitioning](../patterns/quantum_partitioning.md)**: Built directly on DAG pattern
- **[Reactive Event Mesh](../patterns/reactive_event_mesh.md)**: Can model event flows using DAGs
- **[Temporal Versioning](../patterns/temporal_versioning.md)**: Uses DAG concepts for version history

## Related Design Patterns

- Builder Pattern
- Composite Pattern
- Iterator Pattern
- Chain of Responsibility
