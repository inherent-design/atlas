# Quantum Partitioning

## Overview

Quantum Partitioning breaks operations into parallelizable units that maintain explicit relationships. It enables dynamic scheduling of concurrent operations based on their dependencies, allowing maximum parallelism while ensuring correct execution order.

## Key Concepts

- **Quantum Unit**: Self-contained unit of computation with explicit dependencies
- **Dependency Graph**: Network of relationships between units
- **Execution Level**: Set of units that can execute in parallel
- **Execution Plan**: Optimized schedule for unit execution
- **Unit State**: Lifecycle status of computation units
- **Execution Strategy**: Approach for running units across available resources

## Benefits

- **Concurrency**: Automatic parallelism without explicit thread management
- **Declarative**: Express relationships without imperative scheduling
- **Adaptability**: Scales from single-threaded to many-core execution
- **Safety**: Automatically detects dependency cycles
- **Resource Awareness**: Can align execution with available resources
- **Monitoring**: Detailed insights into execution performance and bottlenecks
- **Resilience**: Configurable retry and error handling mechanisms

## Implementation Considerations

- **Granularity**: Right size for computation units
- **Scheduling Strategy**: Thread pool sizing and allocation
- **Error Propagation**: Handling failures in dependent units
- **Resource Constraints**: Limiting concurrency based on system resources
- **Execution Guarantees**: Ensuring deterministic results despite parallelism
- **Worker Types**: Process vs. thread vs. async workers
- **State Sharing**: Inter-unit communication approach
- **Timeout Handling**: Dealing with units that don't complete

## Core Interfaces

```
QuantumUnit[S, R]
├── can_execute(completed_units) -> bool
├── execute(context) -> R
├── get_dependencies() -> List[str]
├── get_result() -> Optional[R]
└── get_id() -> str

QuantumPartitioner
├── add_unit(fn, dependencies, name, timeout) -> QuantumUnit
├── build_execution_plan() -> ExecutionPlan
├── execute(context, max_workers) -> Dict[str, Any]
├── get_failed_units() -> List[QuantumUnit]
└── visualize_plan() -> str
```

## Implementation with TaskMap Library

NERV implements the Quantum Partitioning pattern using the [TaskMap](https://github.com/dask/taskmap) library, which provides efficient parallel task execution with dependency management:

### Core Library Components

| Component                 | Description                                       | NERV Integration                         |
| ------------------------- | ------------------------------------------------- | ---------------------------------------- |
| `TaskMap` class           | Core executor for dependency-based tasks          | Extended as QuantumPartitioner           |
| `run_parallel` function   | Executes task graph with parallel workers         | Used for distributed computation         |
| `run_async` function      | Executes task graph with asyncio                  | Used for IO-bound workloads              |
| `run_tasks` function      | Base execution function                           | Extended for custom execution strategies |
| `build_graph` function    | Constructs dependency graph from task definitions | Used for execution plan creation         |
| `PriorityTaskQueue` class | Optimized queue for dependency-aware scheduling   | Used for execution prioritization        |

### Core Type Definitions

```python
from typing import Dict, List, Any, Callable, Optional, Set, Union, TypeVar
from dataclasses import dataclass, field
import time

T = TypeVar('T')  # Input context type
R = TypeVar('R')  # Result type

@dataclass
class QuantumTask:
    """Definition of an executable quantum unit."""
    id: str
    function: Callable[[T], R]
    dependencies: List[str] = field(default_factory=list)
    timeout: Optional[float] = None
    retries: int = 0
    priority: int = 0
    tags: Set[str] = field(default_factory=set)

    # Runtime state
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[R] = None
    error: Optional[Exception] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    def execution_time(self) -> Optional[float]:
        """Calculate execution time if completed."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
```

### TaskMap Execution Model

TaskMap provides several execution strategies that NERV leverages:

```python
from taskmap import TaskMap, run_parallel

# Define execution strategy based on workload type
def execute_quantum_plan(tasks: Dict[str, QuantumTask],
                        context: Any,
                        max_workers: int = None,
                        execution_mode: str = "parallel") -> Dict[str, Any]:
    """Execute a quantum plan with appropriate execution strategy."""

    # Convert NERV tasks to TaskMap format
    taskmap_tasks = {}
    dependencies = {}

    for task_id, task in tasks.items():
        taskmap_tasks[task_id] = lambda ctx, tid=task_id: tasks[tid].function(ctx)
        dependencies[task_id] = task.dependencies

    # Create TaskMap instance
    task_map = TaskMap(taskmap_tasks, dependencies)

    # Select execution strategy
    if execution_mode == "parallel":
        # Process-based parallelism for CPU-bound tasks
        return run_parallel(task_map, context, nprocs=max_workers)
    elif execution_mode == "threaded":
        # Thread-based parallelism for IO-bound tasks
        return run_parallel(task_map, context, nprocs=max_workers, use_threads=True)
    elif execution_mode == "async":
        # Asyncio-based execution for async tasks
        return run_async(task_map, context)
    else:
        # Sequential execution for debugging or simple cases
        return run_tasks(task_map, context)
```

### Execution Visualization and Monitoring

TaskMap enables detailed execution visualization:

```python
def visualize_execution_plan(tasks: Dict[str, QuantumTask]) -> str:
    """Generate a visualization of the execution plan."""
    # Create dependency graph structure
    dependencies = {task_id: task.dependencies for task_id, task in tasks.items()}

    # Build graph representation
    from taskmap import build_graph
    graph = build_graph(dependencies)

    # Generate DOT representation for visualization
    dot_graph = "digraph execution_plan {\n"

    # Add nodes
    for task_id in tasks:
        task = tasks[task_id]
        color = "white"
        if task.status == "completed":
            color = "green"
        elif task.status == "running":
            color = "yellow"
        elif task.status == "failed":
            color = "red"

        dot_graph += f'  "{task_id}" [style=filled, fillcolor={color}];\n'

    # Add edges
    for task_id, deps in dependencies.items():
        for dep in deps:
            dot_graph += f'  "{dep}" -> "{task_id}";\n'

    dot_graph += "}\n"
    return dot_graph
```

## TaskMap Integration with Atlas

The Quantum Partitioning pattern implemented with TaskMap integrates with multiple Atlas subsystems:

1. **Agent System**: Optimizing multi-agent coordination
   ```python
   # Define agent tasks with dependencies
   quantum_partitioner.add_unit(
       fn=knowledge_agent.retrieve,
       dependencies=[],
       name="knowledge_retrieval"
   )

   quantum_partitioner.add_unit(
       fn=reasoning_agent.analyze,
       dependencies=["knowledge_retrieval"],
       name="reasoning_analysis"
   )

   quantum_partitioner.add_unit(
       fn=tool_agent.execute,
       dependencies=["reasoning_analysis"],
       name="tool_execution"
   )
   ```

2. **Provider System**: Parallel API calls with optimal resource usage
   ```python
   # Concurrent provider operations with dependencies
   for i, chunk in enumerate(document_chunks):
       quantum_partitioner.add_unit(
           fn=lambda ctx, c=chunk: process_chunk(ctx, c),
           dependencies=[],
           name=f"chunk_processing_{i}"
       )

   quantum_partitioner.add_unit(
       fn=combine_results,
       dependencies=[f"chunk_processing_{i}" for i in range(len(document_chunks))],
       name="result_combination"
   )
   ```

3. **Knowledge System**: Optimized document processing workflows
   ```python
   # Document processing pipeline
   quantum_partitioner.add_unit(
       fn=extract_text,
       dependencies=[],
       name="text_extraction"
   )

   quantum_partitioner.add_unit(
       fn=chunk_document,
       dependencies=["text_extraction"],
       name="document_chunking"
   )

   quantum_partitioner.add_unit(
       fn=generate_embeddings,
       dependencies=["document_chunking"],
       name="embedding_generation"
   )

   quantum_partitioner.add_unit(
       fn=store_in_database,
       dependencies=["embedding_generation"],
       name="database_storage"
   )
   ```

## Performance Considerations

TaskMap offers several performance optimization options:

1. **Worker Pool Management**:
   - Configure process vs. thread workers based on workload type
   - Adjust worker count based on system resources and workload
   - Use custom worker pools for specialized resources

2. **Execution Strategies**:
   - Use process-based parallelism for CPU-bound tasks
   - Use thread-based parallelism for IO-bound tasks
   - Use asyncio-based execution for async workloads
   - Selectively apply mixed execution strategies

3. **Task Prioritization**:
   - Assign priorities to critical-path tasks
   - Implement custom scheduling strategies for resource-intensive tasks
   - Use dynamic priority adjustment based on execution metrics

4. **Resource Management**:
   - Implement timeout controls for long-running tasks
   - Use resource pools for limiting concurrent resource usage
   - Monitor and adjust concurrency based on system load

## Pattern Variations

### Static Partitioning

Fixed dependency graph known at design time using TaskMap's explicit dependencies.

```python
# Static dependency graph
tasks = {
    "task1": QuantumTask(id="task1", function=process_data, dependencies=[]),
    "task2": QuantumTask(id="task2", function=transform_data, dependencies=["task1"]),
    "task3": QuantumTask(id="task3", function=validate_data, dependencies=["task1"]),
    "task4": QuantumTask(id="task4", function=store_results, dependencies=["task2", "task3"])
}

# Execute with static dependencies
results = execute_quantum_plan(tasks, input_data)
```

### Dynamic Partitioning

Dependencies determined at runtime based on data or conditions, using TaskMap's dynamic task generation.

```python
# Initial tasks
tasks = {
    "data_loading": QuantumTask(id="data_loading", function=load_data, dependencies=[])
}

# Function that adds tasks dynamically
def add_processing_tasks(data, partitioner):
    # Analyze data to determine task graph
    for segment in data.segments:
        segment_id = segment.id

        # Add segment-specific processing task
        partitioner.add_unit(
            fn=lambda ctx, s=segment: process_segment(ctx, s),
            dependencies=["data_loading"],
            name=f"process_segment_{segment_id}"
        )

        # Add result tasks with dependencies on specific segments
        if segment.requires_validation:
            partitioner.add_unit(
                fn=lambda ctx, s=segment: validate_segment(ctx, s),
                dependencies=[f"process_segment_{segment_id}"],
                name=f"validate_segment_{segment_id}"
            )

    # Add final aggregation task
    all_segment_tasks = [
        f"validate_segment_{s.id}" if s.requires_validation
        else f"process_segment_{s.id}"
        for s in data.segments
    ]

    partitioner.add_unit(
        fn=aggregate_results,
        dependencies=all_segment_tasks,
        name="result_aggregation"
    )
```

### Hierarchical Partitioning

Tasks organized in nested groups for multi-level parallelism, implemented with TaskMap's task composition.

```python
# Create sub-workflow tasks
def create_document_workflow(document_id):
    """Create a document processing sub-workflow."""
    subtasks = {}

    # Document extraction task
    subtasks[f"extract_{document_id}"] = QuantumTask(
        id=f"extract_{document_id}",
        function=lambda ctx: extract_document(ctx, document_id),
        dependencies=[]
    )

    # Document analysis task
    subtasks[f"analyze_{document_id}"] = QuantumTask(
        id=f"analyze_{document_id}",
        function=lambda ctx: analyze_document(ctx, document_id),
        dependencies=[f"extract_{document_id}"]
    )

    # Document indexing task
    subtasks[f"index_{document_id}"] = QuantumTask(
        id=f"index_{document_id}",
        function=lambda ctx: index_document(ctx, document_id),
        dependencies=[f"analyze_{document_id}"]
    )

    return subtasks, f"index_{document_id}"  # Return tasks and final task ID

# Create main workflow with sub-workflows
main_tasks = {}
final_dependencies = []

# Document sub-workflows
for doc_id in document_ids:
    doc_tasks, final_task_id = create_document_workflow(doc_id)
    # Add sub-workflow tasks to main workflow
    main_tasks.update(doc_tasks)
    # Track final sub-workflow tasks for dependency
    final_dependencies.append(final_task_id)

# Add final aggregation task depending on all sub-workflows
main_tasks["aggregate_results"] = QuantumTask(
    id="aggregate_results",
    function=aggregate_all_documents,
    dependencies=final_dependencies
)
```

## Integration with Other Patterns

- **Reactive Event Mesh**: Units can emit and consume events through the EventBus
- **Temporal Versioning**: Execution plans can be versioned in TemporalStore for reproducibility
- **Effect System**: Units can declare and handle effects using the EffectMonad
- **State Projection**: Units can apply state projections through the StateProjector
- **Perspective Shifting**: Results can be viewed through different perspectives

## Related Patterns

- Fork-Join Pattern: Similar parallel execution with synchronization point
- MapReduce Pattern: Similar distributed computation approach
- Actor Model: Alternative concurrency model with message passing
- Directed Acyclic Graph (DAG) Processing: Foundational approach for dependency graphs
- Future/Promise Pattern: Asynchronous result representation
