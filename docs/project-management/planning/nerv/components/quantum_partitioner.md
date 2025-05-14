---
title: Quantum Partitioner
---

# QuantumPartitioner Implementation

## Overview

The QuantumPartitioner implements the Quantum Partitioning pattern, breaking operations into parallelizable units that maintain explicit dependencies. It enables maximum concurrency while respecting execution order constraints.

## Architectural Role

QuantumPartitioner powers parallel execution in Atlas:

- **Retrieval System**: Parallel document processing
- **Provider System**: Concurrent provider operations
- **Agent Framework**: Parallel task execution
- **Knowledge System**: Concurrent document transformations
- **Workflow Engine**: Parallel node execution
- **Ingestion Pipeline**: Concurrent document processing stages

## Implementation Library: TaskMap

The QuantumPartitioner is implemented using the [TaskMap](https://github.com/dask/taskmap) library, which provides efficient dependency-based parallel execution with advanced scheduling capabilities.

### Core Library Features

| TaskMap Feature                 | Description                  | Usage in QuantumPartitioner        |
| ------------------------------- | ---------------------------- | ---------------------------------- |
| `TaskMap` class                 | Core execution engine        | Base for execution plan management |
| `run_tasks` function            | Sequential execution         | Used for debugging and tracing     |
| `run_parallel` function         | Parallel process execution   | Used for CPU-bound workloads       |
| `run_parallel_threads` function | Parallel thread execution    | Used for IO-bound workloads        |
| `run_async` function            | Async/await execution        | Used for async operations          |
| `build_graph` function          | Dependency graph constructor | Used for execution planning        |
| Task callbacks                  | Execution hooks              | Used for monitoring and telemetry  |
| Execution tracking              | Progress monitoring          | Used for status reporting          |
| Error handling                  | Robust exception management  | Used for fault tolerance           |

### Core Implementation Structure

```python
from typing import Generic, TypeVar, List, Dict, Set, Optional, Callable, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from taskmap import TaskMap, run_parallel, run_parallel_threads, run_async, build_graph
from taskmap.exceptions import TaskError, CircularDependency

T = TypeVar('T')  # Input context type
R = TypeVar('R')  # Result type

class UnitState(Enum):
    """Lifecycle states for execution units."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELED = "canceled"
    TIMEOUT = "timeout"

@dataclass
class QuantumUnit(Generic[T, R]):
    """A self-contained unit of computation with dependencies."""
    id: str
    function: Callable[[T], R]
    dependencies: List[str] = field(default_factory=list)
    timeout: Optional[float] = None
    retries: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    state: UnitState = UnitState.PENDING
    result: Optional[R] = None
    error: Optional[Exception] = None
    execution_time: Optional[float] = None

@dataclass
class ExecutionPlan:
    """Graph-based execution scheduler."""
    units: Dict[str, QuantumUnit]
    execution_order: List[List[str]]
    max_level: int

    @property
    def unit_count(self) -> int:
        return len(self.units)

    @property
    def max_parallel_units(self) -> int:
        return max(len(level) for level in self.execution_order)

class ExecutionMode(Enum):
    """Execution strategies for quantum units."""
    SEQUENTIAL = "sequential"
    PROCESS = "process"
    THREAD = "thread"
    ASYNC = "async"
    CUSTOM = "custom"

class QuantumPartitioner(Generic[T, R]):
    """Parallel execution engine with dependency-based scheduling."""

    def __init__(self,
                 max_workers: Optional[int] = None,
                 default_execution_mode: ExecutionMode = ExecutionMode.THREAD):
        """Initialize the quantum partitioner."""
        self.units: Dict[str, QuantumUnit[T, R]] = {}
        self.max_workers = max_workers
        self.default_execution_mode = default_execution_mode
        self.completed_units: Set[str] = set()
        self.failed_units: Set[str] = set()
        self._execution_plan: Optional[ExecutionPlan] = None
```

### TaskMap Integration Details

The QuantumPartitioner leverages TaskMap's architecture while adding NERV-specific features:

```python
class QuantumPartitioner(Generic[T, R]):
    # [...previous code...]

    def add_unit(self,
                fn: Callable[[T], R],
                dependencies: List[str] = None,
                name: Optional[str] = None,
                timeout: Optional[float] = None,
                retries: int = 0,
                metadata: Optional[Dict[str, Any]] = None) -> QuantumUnit[T, R]:
        """Add a computation unit to the partitioner."""
        unit_id = name or f"unit_{len(self.units)}"
        unit = QuantumUnit(
            id=unit_id,
            function=fn,
            dependencies=dependencies or [],
            timeout=timeout,
            retries=retries,
            metadata=metadata or {}
        )
        self.units[unit_id] = unit
        # Reset execution plan when units change
        self._execution_plan = None
        return unit

    def build_execution_plan(self) -> ExecutionPlan:
        """Analyze dependencies and build optimal execution plan."""
        # Verify no circular dependencies
        task_dict = {unit_id: unit.dependencies for unit_id, unit in self.units.items()}
        try:
            graph = build_graph(task_dict)
        except CircularDependency as e:
            # Provide detailed error about circular dependencies
            raise CircularDependencyError(f"Circular dependency detected: {e}")

        # Build execution levels (units that can run in parallel)
        execution_levels = []
        remaining = set(self.units.keys())

        while remaining:
            # Find units with all dependencies satisfied
            level = set()
            for unit_id in remaining:
                deps = self.units[unit_id].dependencies
                if all(dep not in remaining for dep in deps):
                    level.add(unit_id)

            if not level:
                # Should never happen if no circular dependencies
                raise RuntimeError("Could not resolve execution plan")

            execution_levels.append(list(level))
            remaining -= level

        # Create and cache execution plan
        self._execution_plan = ExecutionPlan(
            units=self.units.copy(),
            execution_order=execution_levels,
            max_level=len(execution_levels)
        )
        return self._execution_plan

    def execute(self,
                context: T,
                execution_mode: Optional[ExecutionMode] = None,
                max_workers: Optional[int] = None,
                custom_executor: Any = None) -> Dict[str, R]:
        """Execute all units respecting dependencies."""
        # Ensure we have a current execution plan
        if not self._execution_plan:
            self.build_execution_plan()

        # Prepare TaskMap format
        tasks = {}
        for unit_id, unit in self.units.items():
            # Create wrapped function that handles retries and timeout
            task_fn = self._create_task_function(unit)
            tasks[unit_id] = (task_fn, unit.dependencies)

        # Select execution strategy
        mode = execution_mode or self.default_execution_mode
        workers = max_workers or self.max_workers

        # Convert to TaskMap
        task_map = TaskMap(tasks)

        # Execute based on selected mode
        try:
            if mode == ExecutionMode.SEQUENTIAL:
                results = task_map.run(context)
            elif mode == ExecutionMode.PROCESS:
                with ProcessPoolExecutor(max_workers=workers) as executor:
                    results = run_parallel(task_map, context, executor=executor)
            elif mode == ExecutionMode.THREAD:
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    results = run_parallel_threads(task_map, context, executor=executor)
            elif mode == ExecutionMode.ASYNC:
                results = run_async(task_map, context)
            elif mode == ExecutionMode.CUSTOM and custom_executor:
                # Run with user-provided executor
                results = run_parallel(task_map, context, executor=custom_executor)
            else:
                raise ValueError(f"Invalid execution mode: {mode}")

            # Update unit states and results
            for unit_id, result in results.items():
                unit = self.units[unit_id]
                unit.state = UnitState.COMPLETED
                unit.result = result
                self.completed_units.add(unit_id)

            return results

        except TaskError as e:
            # Handle task failures, update unit states
            for unit_id, err in e.errors.items():
                unit = self.units[unit_id]
                unit.state = UnitState.FAILED
                unit.error = err
                self.failed_units.add(unit_id)

            # Return partial results
            return e.partial_results
```

## Key Components

### Quantum Unit

TaskMap-powered execution units with rich metadata:

```python
@dataclass
class QuantumUnit(Generic[T, R]):
    """A self-contained unit of computation with dependencies."""
    id: str  # Unique identifier
    function: Callable[[T], R]  # The computation function
    dependencies: List[str]  # IDs of units this depends on
    timeout: Optional[float] = None  # Maximum execution time
    retries: int = 0  # Number of retry attempts
    priority: int = 0  # Execution priority (higher = sooner)
    metadata: Dict[str, Any] = field(default_factory=dict)  # Custom metadata

    # Runtime state
    state: UnitState = field(default=UnitState.PENDING)
    result: Optional[R] = None
    error: Optional[Exception] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    attempt: int = 0

    def can_execute(self, completed_units: Set[str]) -> bool:
        """Check if all dependencies are satisfied."""
        return all(dep in completed_units for dep in self.dependencies)

    def get_execution_time(self) -> Optional[float]:
        """Get execution time if completed."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
```

### Execution Plan

TaskMap-optimized strategy for parallel execution:

```python
@dataclass
class ExecutionPlan:
    """Optimized execution strategy with levels of parallelism."""
    units: Dict[str, QuantumUnit]  # All execution units
    levels: List[List[str]]  # Units grouped by execution level
    dependencies: Dict[str, Set[str]]  # Unit dependencies
    dependents: Dict[str, Set[str]]  # Units depending on this unit

    @property
    def critical_path(self) -> List[str]:
        """Identify the critical execution path."""
        # Implementation uses TaskMap's graph analysis
        # to find the longest dependency chain

    def visualize(self) -> str:
        """Generate DOT graph visualization of the execution plan."""
        # Implementation generates a GraphViz DOT diagram
        # showing units and their dependencies
```

### Execution Context

TaskMap-enhanced execution environment:

```python
@dataclass
class ExecutionContext(Dict[str, Any]):
    """Enriched context for quantum unit execution."""
    unit_results: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, Any] = field(default_factory=dict)

    def get_dependency_result(self, unit_id: str) -> Any:
        """Get the result of a dependency unit."""
        return self.unit_results.get(unit_id)

    def record_metric(self, name: str, value: Any) -> None:
        """Record execution metric."""
        self.metrics[name] = value
```

## Advanced TaskMap Integration

### Custom Execution Strategies

The TaskMap library enables specialized execution approaches:

```python
class QuantumPartitioner(Generic[T, R]):
    # [...previous code...]

    def execute_with_strategy(self, context: T, strategy: str) -> Dict[str, R]:
        """Execute with specialized strategies."""
        plan = self.build_execution_plan()

        if strategy == "priority":
            # Execute units in priority order within each level
            for level in plan.levels:
                priority_sorted = sorted(
                    level,
                    key=lambda unit_id: self.units[unit_id].priority,
                    reverse=True
                )
                # Use TaskMap to execute this level's units

        elif strategy == "resource_balanced":
            # Group units by resource requirements
            cpu_units = []
            io_units = []

            for unit_id, unit in self.units.items():
                if unit.metadata.get("resource_type") == "cpu":
                    cpu_units.append(unit_id)
                else:
                    io_units.append(unit_id)

            # Use ProcessPoolExecutor for CPU units
            # Use ThreadPoolExecutor for I/O units

        elif strategy == "adaptive":
            # Dynamically adjust workers based on system load
            import psutil

            # Monitor system resources during execution
            def resource_monitor():
                while execution_active:
                    cpu_percent = psutil.cpu_percent()
                    mem_percent = psutil.virtual_memory().percent
                    # Adjust worker count based on usage

        # Return combined results
```

### Execution Monitoring and Telemetry

TaskMap's callback system enables detailed execution tracking:

```python
class QuantumPartitioner(Generic[T, R]):
    # [...previous code...]

    def execute_with_monitoring(self, context: T) -> Dict[str, R]:
        """Execute with detailed monitoring."""
        import time

        # Execution metrics
        metrics = {
            "start_time": time.time(),
            "end_time": None,
            "unit_times": {},
            "total_units": len(self.units),
            "completed_units": 0,
            "failed_units": 0,
            "execution_trace": []
        }

        # TaskMap callbacks
        def on_start(task_name):
            metrics["unit_times"][task_name] = {"start": time.time()}
            metrics["execution_trace"].append(
                {"event": "start", "unit": task_name, "time": time.time()}
            )

        def on_complete(task_name, result):
            metrics["unit_times"][task_name]["end"] = time.time()
            metrics["unit_times"][task_name]["duration"] = (
                metrics["unit_times"][task_name]["end"] -
                metrics["unit_times"][task_name]["start"]
            )
            metrics["completed_units"] += 1
            metrics["execution_trace"].append(
                {"event": "complete", "unit": task_name, "time": time.time()}
            )

        def on_error(task_name, error):
            metrics["unit_times"][task_name]["end"] = time.time()
            metrics["unit_times"][task_name]["error"] = str(error)
            metrics["failed_units"] += 1
            metrics["execution_trace"].append(
                {"event": "error", "unit": task_name, "time": time.time(),
                 "error": str(error)}
            )

        # Create task map with callbacks
        task_dict = {unit_id: (unit.function, unit.dependencies)
                    for unit_id, unit in self.units.items()}
        task_map = TaskMap(task_dict)
        task_map.on_task_start = on_start
        task_map.on_task_complete = on_complete
        task_map.on_task_error = on_error

        # Execute with monitoring
        try:
            results = run_parallel_threads(task_map, context,
                                          max_workers=self.max_workers)
            return results
        finally:
            metrics["end_time"] = time.time()
            metrics["total_duration"] = metrics["end_time"] - metrics["start_time"]
            self.last_execution_metrics = metrics
```

### Fault Tolerance and Recovery

TaskMap enables sophisticated error handling strategies:

```python
class QuantumPartitioner(Generic[T, R]):
    # [...previous code...]

    def execute_with_recovery(self, context: T) -> Dict[str, R]:
        """Execute with fault tolerance and recovery."""
        # Prepare TaskMap with retryable tasks
        retryable_tasks = {}

        for unit_id, unit in self.units.items():
            # Create retrying wrapper for each function
            max_retries = unit.retries

            def retryable_fn(ctx, original_fn=unit.function,
                           unit_id=unit_id, retries=max_retries):
                attempt = 0
                while True:
                    try:
                        return original_fn(ctx)
                    except Exception as e:
                        attempt += 1
                        if attempt > retries:
                            raise
                        # Log retry attempt
                        print(f"Retrying {unit_id}, attempt {attempt}/{retries}")
                        # Short delay before retry
                        time.sleep(min(2 ** attempt * 0.1, 5))

            retryable_tasks[unit_id] = (retryable_fn, unit.dependencies)

        # Create TaskMap with recovery capabilities
        recoverable = TaskMap(retryable_tasks)

        # Execute with recovery
        try:
            return run_parallel_threads(recoverable, context)
        except TaskError as e:
            # Handle partial results case
            results = e.partial_results
            failed = e.failed_tasks

            # Check if we can continue with partial results
            if self._can_continue_with_partial(failed):
                # Create substitute results for failed tasks
                for task_id in failed:
                    unit = self.units[task_id]
                    if unit.metadata.get("fallback_value") is not None:
                        results[task_id] = unit.metadata["fallback_value"]

                # Execute remaining tasks that depend on previously failed ones
                # but now have fallback values available
                return self._complete_execution_with_fallbacks(results, failed, context)
            else:
                raise
```

## Performance Considerations

TaskMap provides sophisticated performance optimizations for the QuantumPartitioner:

### Worker Pool Management

```python
def select_optimal_workers(units: Dict[str, QuantumUnit],
                          execution_plan: ExecutionPlan) -> int:
    """Select optimal worker count based on workload characteristics."""
    import os

    # Get available CPU cores
    available_cores = os.cpu_count() or 4

    # Consider these factors:
    # 1. Maximum parallelism in the plan
    max_parallel = execution_plan.max_parallel_units

    # 2. CPU vs. I/O bound workloads
    cpu_bound = sum(1 for u in units.values()
                   if u.metadata.get("resource_type") == "cpu")
    io_bound = len(units) - cpu_bound

    # For CPU-bound workloads, limit to available cores
    if cpu_bound > io_bound:
        return min(max_parallel, available_cores)
    else:
        # For I/O-bound workloads, can use more workers
        return min(max_parallel, available_cores * 2)
```

### Execution Strategies

```python
def select_execution_strategy(units: Dict[str, QuantumUnit]) -> ExecutionMode:
    """Select optimal execution strategy based on workload types."""
    # Count different workload types
    cpu_units = 0
    io_units = 0
    async_units = 0

    for unit in units.values():
        resource_type = unit.metadata.get("resource_type", "cpu")
        if resource_type == "cpu":
            cpu_units += 1
        elif resource_type == "io":
            io_units += 1
        elif resource_type == "async":
            async_units += 1

    # Select appropriate execution mode
    if async_units > (cpu_units + io_units):
        return ExecutionMode.ASYNC
    elif io_units > cpu_units:
        return ExecutionMode.THREAD
    else:
        return ExecutionMode.PROCESS
```

### Caching and Memoization

```python
class CachingQuantumPartitioner(QuantumPartitioner[T, R]):
    """QuantumPartitioner with result caching capabilities."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def _create_task_function(self, unit: QuantumUnit[T, R]) -> Callable[[T], R]:
        """Create a cached version of the task function."""
        original_fn = unit.function
        unit_id = unit.id

        # Check if unit is cacheable
        if not unit.metadata.get("cacheable", False):
            return original_fn

        # Create caching wrapper
        def cached_fn(context: T) -> R:
            # Create cache key from unit ID and relevant context
            relevant_keys = unit.metadata.get("cache_keys", [])
            if not relevant_keys:
                # Default to using the whole context
                cache_dict = dict(context)
            else:
                # Use only specified keys from context
                cache_dict = {k: context.get(k) for k in relevant_keys
                             if k in context}

            cache_key = f"{unit_id}:{hash(frozenset(cache_dict.items()))}"

            # Check cache
            if cache_key in self.cache:
                self.cache_hits += 1
                return self.cache[cache_key]

            # Cache miss - execute function
            self.cache_misses += 1
            result = original_fn(context)

            # Store in cache
            self.cache[cache_key] = result
            return result

        return cached_fn
```

## Integration with Atlas

The QuantumPartitioner with TaskMap is used throughout Atlas:

### Provider System Integration

```python
# Set up parallel model calls across providers
def create_provider_execution_plan(providers, query, max_workers=3):
    """Create execution plan for parallel provider operations."""
    partitioner = QuantumPartitioner(max_workers=max_workers,
                                    default_execution_mode=ExecutionMode.THREAD)

    # Create parallel units for each provider
    for provider in providers:
        partitioner.add_unit(
            fn=lambda ctx, p=provider: p.generate(ctx["query"]),
            dependencies=[],  # No dependencies
            name=f"provider_{provider.id}",
            timeout=10.0,  # 10-second timeout
            metadata={"resource_type": "io", "provider": provider.id}
        )

    # Add aggregation unit that depends on all provider units
    provider_units = [f"provider_{p.id}" for p in providers]
    partitioner.add_unit(
        fn=lambda ctx: aggregate_responses(ctx),
        dependencies=provider_units,
        name="aggregate_responses"
    )

    return partitioner
```

### Document Processing Pipeline

```python
# Document processing workflow
def create_document_pipeline(documents, embedding_model):
    """Create parallel document processing pipeline."""
    partitioner = QuantumPartitioner(max_workers=4)

    # Add extraction units for each document
    for i, doc in enumerate(documents):
        partitioner.add_unit(
            fn=lambda ctx, d=doc: extract_text(d),
            dependencies=[],  # No dependencies
            name=f"extract_{i}",
            metadata={"document_id": doc.id, "resource_type": "cpu"}
        )

        # Add chunking units depending on extraction
        partitioner.add_unit(
            fn=lambda ctx, i=i: chunk_text(ctx[f"extract_{i}"]),
            dependencies=[f"extract_{i}"],
            name=f"chunk_{i}",
            metadata={"document_id": doc.id, "resource_type": "cpu"}
        )

        # Add embedding units depending on chunking
        partitioner.add_unit(
            fn=lambda ctx, i=i, model=embedding_model:
                generate_embeddings(ctx[f"chunk_{i}"], model),
            dependencies=[f"chunk_{i}"],
            name=f"embed_{i}",
            metadata={"document_id": doc.id, "resource_type": "io"}
        )

    # Add final indexing unit depending on all embedding units
    embedding_units = [f"embed_{i}" for i in range(len(documents))]
    partitioner.add_unit(
        fn=lambda ctx: index_embeddings(ctx),
        dependencies=embedding_units,
        name="index_embeddings"
    )

    return partitioner
```

### Multi-Agent Orchestration

```python
# Multi-agent workflow with dependencies
def create_agent_workflow(query, available_agents):
    """Create dependency-based multi-agent workflow."""
    partitioner = QuantumPartitioner(max_workers=len(available_agents))

    # Add retrieval agent unit
    partitioner.add_unit(
        fn=lambda ctx: available_agents["retrieval"].process(ctx["query"]),
        dependencies=[],  # No dependencies
        name="retrieval_agent",
        metadata={"agent_type": "retrieval", "resource_type": "io"}
    )

    # Add reasoning agent unit depending on retrieval
    partitioner.add_unit(
        fn=lambda ctx: available_agents["reasoning"].process(
            ctx["query"], ctx["retrieval_agent"]),
        dependencies=["retrieval_agent"],
        name="reasoning_agent",
        metadata={"agent_type": "reasoning", "resource_type": "cpu"}
    )

    # Add parallel tool agent units depending on reasoning
    for tool in available_agents["reasoning"].get_required_tools():
        partitioner.add_unit(
            fn=lambda ctx, t=tool: available_agents["tool"].process_tool(
                ctx["reasoning_agent"], tool=t),
            dependencies=["reasoning_agent"],
            name=f"tool_agent_{tool}",
            metadata={"agent_type": "tool", "tool": tool, "resource_type": "io"}
        )

    # Add final response agent depending on all tool agents
    tool_units = [unit_id for unit_id in partitioner.units
                 if unit_id.startswith("tool_agent_")]
    partitioner.add_unit(
        fn=lambda ctx: available_agents["response"].generate_response(
            ctx["query"], ctx["reasoning_agent"],
            {unit_id: ctx[unit_id] for unit_id in tool_units}),
        dependencies=["reasoning_agent"] + tool_units,
        name="response_agent",
        metadata={"agent_type": "response", "resource_type": "cpu"}
    )

    return partitioner
```

## Usage Patterns

### Basic Parallel Execution

TaskMap-powered parallel execution with dependency management:

```python
# Create partitioner instance
partitioner = QuantumPartitioner(max_workers=4)

# Add computational units with dependencies
partitioner.add_unit(
    fn=load_data,
    dependencies=[],  # No dependencies
    name="load_data"
)

partitioner.add_unit(
    fn=process_data,
    dependencies=["load_data"],  # Depends on load_data
    name="process_data"
)

partitioner.add_unit(
    fn=validate_data,
    dependencies=["load_data"],  # Depends on load_data
    name="validate_data"
)

partitioner.add_unit(
    fn=store_results,
    dependencies=["process_data", "validate_data"],  # Depends on both
    name="store_results"
)

# Build and visualize the execution plan
plan = partitioner.build_execution_plan()
print(f"Execution levels: {plan.levels}")
print(f"Critical path: {plan.critical_path}")

# Execute with context
results = partitioner.execute({"input_data": data})

# Access individual results
processed_data = results["process_data"]
validation_result = results["validate_data"]
```

### Advanced Execution Control

TaskMap provides fine-grained execution control:

```python
# Create partitioner with custom execution strategy
partitioner = QuantumPartitioner(
    max_workers=8,
    default_execution_mode=ExecutionMode.PROCESS
)

# Add computation units
# ... [units added as in previous example]

# Execute with monitoring
metrics = {}
def start_monitor(unit_id):
    metrics[unit_id] = {"start_time": time.time()}

def end_monitor(unit_id, result):
    metrics[unit_id]["end_time"] = time.time()
    metrics[unit_id]["duration"] = (
        metrics[unit_id]["end_time"] - metrics[unit_id]["start_time"]
    )

# Set up monitoring callbacks
partitioner.on_unit_start = start_monitor
partitioner.on_unit_complete = end_monitor

# Execute with specific mode
results = partitioner.execute(
    context={"input_data": data},
    execution_mode=ExecutionMode.THREAD,  # Override default mode
    max_workers=4  # Override default worker count
)

# Analyze execution metrics
total_time = sum(m["duration"] for m in metrics.values())
max_time = max(m["duration"] for m in metrics.values())
print(f"Total execution time: {total_time:.2f}s")
print(f"Critical path time: {max_time:.2f}s")
print(f"Parallelism efficiency: {total_time/max_time:.2f}x")
```

### Error Handling and Recovery

Advanced error handling with TaskMap:

```python
# Create partitioner with retry capabilities
partitioner = QuantumPartitioner(max_workers=4)

# Add units with retry and timeout configuration
partitioner.add_unit(
    fn=fetch_data_from_api,
    dependencies=[],
    name="fetch_data",
    retries=3,  # Retry up to 3 times
    timeout=5.0,  # 5-second timeout
    metadata={
        "fallback_value": {"status": "error", "data": []},
        "resource_type": "io"
    }
)

# Add error handling to function
def process_with_error_handling(context):
    try:
        data = context["fetch_data"]
        if data["status"] == "error":
            # Handle error case
            return {"processed": False}
        # Normal processing
        return {"processed": True, "result": process(data["data"])}
    except Exception as e:
        # Log error and return safe result
        print(f"Error in processing: {e}")
        return {"processed": False, "error": str(e)}

partitioner.add_unit(
    fn=process_with_error_handling,
    dependencies=["fetch_data"],
    name="process_data"
)

# Execute with error handling
try:
    results = partitioner.execute({"api_url": "https://example.com/api"})
    # Use results
except Exception as e:
    # Handle execution failure
    print(f"Execution failed: {e}")
    # Check partial results
    partial_results = partitioner.get_partial_results()
    # Check failed units
    failed_units = partitioner.get_failed_units()
```

## Relationship to Patterns

Implements:
- **[Quantum Partitioning](../patterns/quantum_partitioning.md)**: Primary implementation with TaskMap
- **[DAG](../primitives/dag.md)**: TaskMap's directed acyclic graph for dependency management

Supports:
- **[Reactive Event Mesh](../patterns/reactive_event_mesh.md)**: Units can emit events through EventBus
- **[Temporal Versioning](../patterns/temporal_versioning.md)**: Execution plans can be versioned with TemporalStore
- **[Perspective Shifting](../patterns/perspective_shifting.md)**: Results can be viewed through different PerspectiveAware schemas
- **[Effect System](../patterns/effect_system.md)**: Units can track effects with EffectMonad
- **[State Projection](../patterns/state_projection.md)**: Can project execution state with StateProjector
