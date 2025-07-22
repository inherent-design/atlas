---

title: Edges

---


# Edges

This document explains the edge routing system in Atlas, which provides conditional flow control in LangGraph workflows.

## Overview

The edge system in Atlas enables sophisticated flow control in LangGraph workflows with:

1. **Conditional Routing**: Directing flow based on state conditions
2. **Edge Types**: Different edge categories for various routing needs
3. **Fallback Mechanisms**: Handling unexpected conditions
4. **Edge Creation Utilities**: Helper functions for edge definition
5. **Common Conditions**: Pre-defined conditions for frequent routing patterns

The system is designed to be:

- **Flexible**: Supporting complex routing patterns
- **Type-Safe**: Using generics for state type checking
- **Declarative**: Clear definition of routing logic
- **Traceable**: Providing telemetry for edge traversal

## Core Components

### Edge Types

The system defines several edge types through the `EdgeType` enum:

```python
class EdgeType(str, Enum):
    """Types of edges in the graph."""
    NORMAL = "normal"      # Standard edge
    CONDITIONAL = "conditional"  # Edge with condition
    FALLBACK = "fallback"  # Edge taken when others fail
    DEFAULT = "default"    # Default edge for conditional routing
```

These types determine how edges behave in the workflow:
- **NORMAL**: Standard edge that always follows to the target
- **CONDITIONAL**: Edge that follows only when a condition is met
- **FALLBACK**: Edge that follows when no other edges are applicable
- **DEFAULT**: Edge that serves as a default route

### Base Edge Class

The `Edge` class serves as the foundation of the edge system:

```python
class Edge(TracedClass, Generic[StateType]):
    """Base class for graph edges in Atlas workflows."""

    def __init__(
        self,
        source_node: str,
        target_node: str,
        edge_type: EdgeType = EdgeType.NORMAL,
        label: EdgeLabelType = None,
        description: Optional[str] = None,
    ):
        """Initialize an edge."""
        self.source_node = source_node
        self.target_node = target_node
        self.edge_type = edge_type
        self.label = label
        self.description = description or f"Edge from {source_node} to {target_node}"

    def get_target(self, state: StateType) -> str:
        """Get the target node for this edge."""
        return self.target_node

    def should_follow(self, state: StateType) -> bool:
        """Determine if this edge should be followed."""
        # Base edge is always followed
        return True
```

The base `Edge` class provides:
- Source and target node identification
- Edge type specification
- Optional labels and descriptions
- Methods for determining routing

### Conditional Edge

The `ConditionalEdge` class enables condition-based routing:

```python
class ConditionalEdge(Edge[StateType]):
    """Edge with a condition function that determines if it should be followed."""

    def __init__(
        self,
        source_node: str,
        target_node: str,
        condition: EdgeConditionFunction[StateType],
        label: EdgeLabelType = None,
        description: Optional[str] = None,
    ):
        """Initialize a conditional edge."""
        super().__init__(
            source_node=source_node,
            target_node=target_node,
            edge_type=EdgeType.CONDITIONAL,
            label=label,
            description=description,
        )
        self.condition = condition

    def should_follow(self, state: StateType) -> bool:
        """Determine if this edge should be followed based on the condition."""
        try:
            return self.condition(state)
        except Exception as e:
            logger.error(
                f"Error evaluating condition for edge {self}: {e}", exc_info=True
            )
            return False
```

This class:
- Takes a condition function that evaluates the state
- Returns the result of the condition function in `should_follow()`
- Includes error handling for condition evaluation

### Fallback Edge

The `FallbackEdge` class provides a default path when no other edges apply:

```python
class FallbackEdge(Edge[StateType]):
    """Edge that is followed when no other edges from the source are followed."""

    def __init__(
        self,
        source_node: str,
        target_node: str,
        label: EdgeLabelType = None,
        description: Optional[str] = None,
    ):
        """Initialize a fallback edge."""
        super().__init__(
            source_node=source_node,
            target_node=target_node,
            edge_type=EdgeType.FALLBACK,
            label=label,
            description=description
            or f"Fallback edge from {source_node} to {target_node}",
        )

    def should_follow(self, state: StateType) -> bool:
        """Determine if this edge should be followed."""
        # Always returns True for fallback edges.
        # The graph executor will try this edge if no other edges are followed.
        return True
```

This class:
- Serves as a default route when no other edges from the source node are followed
- Always returns `True` from `should_follow()`, but is only traversed if no other edges are applicable

## Edge Creation Utilities

### Generic Edge Creation

The `create_edge` function provides a unified interface for creating edges of different types:

```python
@traced(name="create_edge")
def create_edge(
    source: str,
    target: str,
    edge_type: EdgeType = EdgeType.NORMAL,
    condition: Optional[EdgeConditionFunction] = None,
    label: EdgeLabelType = None,
    description: Optional[str] = None,
) -> Edge:
    """Create an edge based on the specified type."""
    if edge_type == EdgeType.CONDITIONAL:
        if condition is None:
            raise ValueError("Condition function required for conditional edges")
        return ConditionalEdge(
            source_node=source,
            target_node=target,
            condition=condition,
            label=label,
            description=description,
        )
    elif edge_type == EdgeType.FALLBACK:
        return FallbackEdge(
            source_node=source,
            target_node=target,
            label=label,
            description=description,
        )
    else:
        return Edge(
            source_node=source,
            target_node=target,
            edge_type=edge_type,
            label=label,
            description=description,
        )
```

This function:
- Takes parameters for creating any edge type
- Determines the appropriate edge class based on the specified type
- Creates and returns the edge instance
- Validates that conditional edges have a condition function

### Specialized Edge Creation

The system also provides specialized functions for creating specific edge types:

```python
@traced(name="create_conditional_edge")
def create_conditional_edge(
    source: str,
    target: str,
    condition: EdgeConditionFunction,
    label: EdgeLabelType = None,
    description: Optional[str] = None,
) -> ConditionalEdge:
    """Create a conditional edge."""
    return ConditionalEdge(
        source_node=source,
        target_node=target,
        condition=condition,
        label=label,
        description=description,
    )

@traced(name="create_fallback_edge")
def create_fallback_edge(
    source: str,
    target: str,
    label: EdgeLabelType = None,
    description: Optional[str] = None,
) -> FallbackEdge:
    """Create a fallback edge."""
    return FallbackEdge(
        source_node=source,
        target_node=target,
        label=label,
        description=description,
    )
```

These functions:
- Provide a clearer interface for creating specific edge types
- Include telemetry through the `@traced` decorator
- Handle type-specific parameters appropriately

## Common Condition Functions

The system includes pre-defined condition functions for common routing patterns:

```python
@traced(name="is_error_condition")
def is_error_condition(state: Union[AgentState, ControllerState]) -> bool:
    """Check if an error has occurred."""
    return bool(getattr(state, "error", None))

@traced(name="is_process_complete_condition")
def is_process_complete_condition(state: AgentState) -> bool:
    """Check if processing is complete."""
    return state.process_complete

@traced(name="are_all_tasks_assigned_condition")
def are_all_tasks_assigned_condition(state: ControllerState) -> bool:
    """Check if all tasks have been assigned."""
    return state.all_tasks_assigned

@traced(name="are_all_tasks_completed_condition")
def are_all_tasks_completed_condition(state: ControllerState) -> bool:
    """Check if all tasks have been completed."""
    return state.all_tasks_completed
```

These conditions:
- Provide reusable checks for common routing scenarios
- Work with specific state types (AgentState, ControllerState)
- Include telemetry for monitoring condition evaluation

## Integration with LangGraph

### Adding Edges to Graph

The `add_edges_to_graph` function integrates Atlas edges with LangGraph:

```python
@traced(name="add_edges_to_graph")
def add_edges_to_graph(graph, edges: List[Edge]) -> None:
    """Add a list of edges to the graph."""
    for edge in edges:
        if edge.edge_type == EdgeType.CONDITIONAL:
            graph.add_conditional_edge(
                edge.source_node,
                edge.target_node,
                # Use the should_follow method of the edge as the condition
                lambda state, edge=edge: edge.should_follow(state),
            )
        elif edge.edge_type == EdgeType.FALLBACK:
            # Add as a default edge, which LangGraph will use if no conditions are met
            graph.add_edge(edge.source_node, edge.target_node)
        else:
            # Add as a regular edge
            graph.add_edge(edge.source_node, edge.target_node)

        logger.debug(f"Added edge to graph: {edge}")
```

This function:
- Takes a LangGraph `StateGraph` instance and a list of Atlas edges
- Maps Atlas edge types to appropriate LangGraph edge types
- Creates appropriate lambda functions for conditional edges
- Adds each edge to the graph with the correct type

### Using Conditional Edges

In workflow definitions, conditional edges control the flow:

```python
# Basic RAG workflow
builder.add_conditional_edges(
    "generate_response",
    should_end,
    {True: END, False: "retrieve_knowledge"}
)

# Controller workflow with multiple conditions
builder.add_conditional_edges(
    "route_workers",
    lambda x: x,
    {
        "generate_final_response": lambda state: state.all_tasks_completed,
        "create_worker_tasks": lambda state: not state.all_tasks_assigned,
        "process_worker_results": lambda state: (
            state.all_tasks_assigned
            and len(state.completed_workers) >= len(state.active_workers)
        ),
    },
)
```

## Usage Examples

### Basic Edge Definition

```python
from atlas.graph.edges import (
    Edge, ConditionalEdge, FallbackEdge,
    EdgeType, create_edge, is_error_condition
)

# Create a normal edge
edge1 = Edge("node_a", "node_b")

# Create a conditional edge
edge2 = ConditionalEdge(
    source_node="node_b",
    target_node="node_c",
    condition=lambda state: len(state.messages) > 3,
    description="Edge followed when message count exceeds 3"
)

# Create a fallback edge
edge3 = FallbackEdge("node_b", "node_d", description="Default path from node_b")

# Use the creation utility
edge4 = create_edge(
    source="node_c",
    target="node_e",
    edge_type=EdgeType.CONDITIONAL,
    condition=is_error_condition,
    description="Error handling path"
)

# Define all edges for a workflow
workflow_edges = [edge1, edge2, edge3, edge4]
```

### Adding Edges to a Graph

```python
from langgraph.graph import StateGraph
from atlas.graph.edges import add_edges_to_graph
from atlas.graph.state import AgentState

# Create a graph
builder = StateGraph(AgentState)

# Add nodes
builder.add_node("node_a", node_a_function)
builder.add_node("node_b", node_b_function)
builder.add_node("node_c", node_c_function)
builder.add_node("node_d", node_d_function)
builder.add_node("node_e", node_e_function)

# Define edges
edges = [
    Edge("node_a", "node_b"),
    ConditionalEdge(
        source_node="node_b",
        target_node="node_c",
        condition=lambda state: len(state.messages) > 3
    ),
    FallbackEdge("node_b", "node_d"),
    ConditionalEdge(
        source_node="node_c",
        target_node="node_e",
        condition=is_error_condition
    )
]

# Add all edges at once
add_edges_to_graph(builder, edges)

# Set entry point and compile
builder.set_entry_point("node_a")
graph = builder.compile()
```

### Creating Custom Routing Conditions

```python
from typing import Union
from atlas.graph.state import AgentState, ControllerState
from atlas.core.telemetry import traced

@traced(name="has_relevant_documents")
def has_relevant_documents(state: Union[AgentState, ControllerState]) -> bool:
    """Check if the state has relevant documents with high scores."""
    if not state.context or not state.context.get("documents"):
        return False

    # Check if any document has relevance score above threshold
    threshold = 0.8
    return any(
        doc["relevance_score"] > threshold
        for doc in state.context["documents"]
    )

@traced(name="needs_clarification")
def needs_clarification(state: AgentState) -> bool:
    """Check if the query needs clarification based on context."""
    if not state.context:
        return False

    # Check if query is too short
    query = state.context.get("query", "")
    if len(query.split()) < 3:
        return True

    # Check if we have low relevance documents
    if state.context.get("documents"):
        avg_score = sum(
            doc["relevance_score"] for doc in state.context["documents"]
        ) / len(state.context["documents"])
        return avg_score < 0.5

    return False
```

### Complex Routing in a Workflow

```python
from langgraph.graph import StateGraph, END
from atlas.graph.state import AgentState
from atlas.graph.edges import create_conditional_edge, create_fallback_edge

def create_advanced_workflow() -> StateGraph:
    """Create a workflow with complex routing."""
    builder = StateGraph(AgentState)

    # Add nodes
    builder.add_node("retrieve_knowledge", retrieve_knowledge_function)
    builder.add_node("analyze_query", analyze_query_function)
    builder.add_node("clarify_query", clarify_query_function)
    builder.add_node("generate_response", generate_response_function)
    builder.add_node("handle_error", handle_error_function)

    # Define edges as list for clarity
    edges = [
        # First check for errors
        create_conditional_edge(
            "retrieve_knowledge",
            "handle_error",
            is_error_condition,
            description="Handle retrieval errors"
        ),

        # If we have relevant documents, generate response
        create_conditional_edge(
            "retrieve_knowledge",
            "generate_response",
            has_relevant_documents,
            description="Direct response when documents are relevant"
        ),

        # If we need clarification, go to clarify
        create_conditional_edge(
            "retrieve_knowledge",
            "clarify_query",
            needs_clarification,
            description="Request clarification for ambiguous queries"
        ),

        # Default path is to analyze
        create_fallback_edge(
            "retrieve_knowledge",
            "analyze_query",
            description="Default path to analyze query"
        ),

        # From analysis to response
        create_edge(
            "analyze_query",
            "generate_response",
            description="Generate response after analysis"
        ),

        # From clarification back to retrieval
        create_edge(
            "clarify_query",
            "retrieve_knowledge",
            description="Retry retrieval after clarification"
        ),

        # Error handling path
        create_edge(
            "handle_error",
            END,
            description="End workflow after error handling"
        ),

        # End workflow after response
        create_conditional_edge(
            "generate_response",
            END,
            lambda state: True,  # Always end after response
            description="End workflow after response"
        ),
    ]

    # Add all edges to graph
    add_edges_to_graph(builder, edges)

    # Set entry point
    builder.set_entry_point("retrieve_knowledge")

    return builder.compile()
```

## Advanced Patterns

### Dynamic Edge Targeting

For advanced workflows, you can create edges with dynamic targets:

```python
class DynamicTargetEdge(Edge[StateType]):
    """Edge that can dynamically determine its target node."""

    def __init__(
        self,
        source_node: str,
        target_selector: Callable[[StateType], str],
        label: EdgeLabelType = None,
        description: Optional[str] = None,
    ):
        """Initialize a dynamic target edge."""
        super().__init__(
            source_node=source_node,
            target_node="",  # Placeholder
            edge_type=EdgeType.CONDITIONAL,
            label=label,
            description=description,
        )
        self.target_selector = target_selector

    def get_target(self, state: StateType) -> str:
        """Dynamically determine the target node."""
        return self.target_selector(state)

    def should_follow(self, state: StateType) -> bool:
        """Always follow this edge if selected."""
        return True

# Example usage
def select_next_node(state: AgentState) -> str:
    """Select the next node based on state."""
    if state.error:
        return "handle_error"
    elif state.context and state.context.get("documents"):
        return "generate_response"
    else:
        return "fallback_response"

dynamic_edge = DynamicTargetEdge(
    source_node="process_input",
    target_selector=select_next_node,
    description="Dynamically route based on state"
)
```

### Weighted Routing

For probabilistic workflows, you can implement weighted edge selection:

```python
class WeightedEdge(ConditionalEdge[StateType]):
    """Edge with a weight for probabilistic routing."""

    def __init__(
        self,
        source_node: str,
        target_node: str,
        weight: float,
        condition: Optional[EdgeConditionFunction[StateType]] = None,
        label: EdgeLabelType = None,
        description: Optional[str] = None,
    ):
        """Initialize a weighted edge."""
        super().__init__(
            source_node=source_node,
            target_node=target_node,
            condition=condition or (lambda _: True),
            label=label,
            description=description,
        )
        self.weight = weight

# WeightedRouter to use with weighted edges
class WeightedRouter:
    """Router that selects edges based on weights."""

    def __init__(self, edges: List[WeightedEdge]):
        """Initialize with a list of weighted edges."""
        self.edges = edges

    def select_edge(self, state: StateType) -> Optional[Edge]:
        """Select an edge based on weights."""
        import random

        # Filter edges that should be followed based on their conditions
        eligible_edges = [
            edge for edge in self.edges if edge.should_follow(state)
        ]

        if not eligible_edges:
            return None

        # Calculate total weight
        total_weight = sum(edge.weight for edge in eligible_edges)

        # Select a random value in [0, total_weight)
        random_value = random.uniform(0, total_weight)

        # Find the selected edge
        current_weight = 0
        for edge in eligible_edges:
            current_weight += edge.weight
            if random_value <= current_weight:
                return edge

        # Should never reach here if weights sum properly
        return eligible_edges[-1]
```

### Retry Logic

Implement retry logic with conditional edges:

```python
class RetryEdge(ConditionalEdge[AgentState]):
    """Edge that implements retry logic."""

    def __init__(
        self,
        source_node: str,
        target_node: str,
        max_retries: int,
        retry_condition: EdgeConditionFunction[AgentState],
        label: EdgeLabelType = None,
        description: Optional[str] = None,
    ):
        """Initialize a retry edge."""
        # Closure to count retries
        self.retry_count = 0
        self.max_retries = max_retries
        self.retry_condition = retry_condition

        # Create condition function that tracks retries
        def retry_tracker(state: AgentState) -> bool:
            # Check base condition
            if not self.retry_condition(state):
                return False

            # Check retry count
            if self.retry_count >= self.max_retries:
                return False

            # Increment retry count
            self.retry_count += 1

            # Add retry info to state
            if not hasattr(state, "retries"):
                state.retries = {}
            state.retries[source_node] = self.retry_count

            return True

        super().__init__(
            source_node=source_node,
            target_node=target_node,
            condition=retry_tracker,
            label=label,
            description=description or f"Retry edge from {source_node} to {target_node}",
        )
```

## Best Practices

### Edge Design Principles

1. **Clarity**: Make edge conditions clear and focused
2. **Robustness**: Include error handling in condition functions
3. **Testability**: Design conditions that can be tested independently
4. **Observability**: Include logging and telemetry
5. **Independence**: Avoid edge conditions with side effects

### Organizing Complex Workflows

For workflows with many edges:

1. **Group by Source**: Organize edges by their source node
2. **Prioritize Conditions**: Order conditional edges by priority
3. **Document Decision Logic**: Add clear descriptions to edges
4. **Use Fallbacks**: Always include fallback edges for unexpected cases
5. **Visualize the Graph**: Create a visual representation of the workflow

### Performance Considerations

For optimal edge processing:

1. **Efficient Conditions**: Keep condition functions lightweight
2. **Avoid Database Calls**: Don't make API or database calls in conditions
3. **Cache Repeated Checks**: Cache results of expensive condition checks
4. **Limit Branching**: Use a reasonable number of outgoing edges per node

### Debugging Edge Routing

For troubleshooting routing issues:

1. **Verbose Logging**: Enable debug logging for edge traversal
2. **State Inspection**: Print state before condition evaluation
3. **Condition Testing**: Test conditions with sample states
4. **Fallback Edges**: Include fallbacks to detect unexpected routing paths

## Related Documentation

- [State Management](./state.md) - Documentation for state models
- [Graph Nodes](./nodes.md) - Documentation for graph node functions
- [Workflows](../../workflows/multi_agent.md) - Documentation for complete workflows
