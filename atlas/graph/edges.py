"""
Edge definitions for LangGraph in Atlas.

This module defines the edge classes and factories for creating conditional
routing between graph nodes in LangGraph workflows.
"""

import logging
from typing import Callable, Dict, List, Any, Optional, Union, TypeVar, Generic, Tuple
from enum import Enum
import inspect

from atlas.core.telemetry import traced, TracedClass
from atlas.graph.state import AgentState, ControllerState

# Type aliases
StateType = TypeVar("StateType")
EdgeConditionFunction = Callable[[StateType], bool]
EdgeLabelType = Union[str, int, bool, None]

logger = logging.getLogger(__name__)


class EdgeType(str, Enum):
    """Types of edges in the graph."""

    NORMAL = "normal"  # Standard edge
    CONDITIONAL = "conditional"  # Edge with condition
    FALLBACK = "fallback"  # Edge taken when others fail
    DEFAULT = "default"  # Default edge for conditional routing


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
        """Initialize an edge.

        Args:
            source_node: Name of the source node.
            target_node: Name of the target node.
            edge_type: Type of edge.
            label: Optional label for the edge.
            description: Optional description of the edge.
        """
        self.source_node = source_node
        self.target_node = target_node
        self.edge_type = edge_type
        self.label = label
        self.description = description or f"Edge from {source_node} to {target_node}"

    def get_target(self, state: StateType) -> str:
        """Get the target node for this edge.

        Args:
            state: The current state.

        Returns:
            Name of the target node.
        """
        return self.target_node

    def should_follow(self, state: StateType) -> bool:
        """Determine if this edge should be followed.

        Args:
            state: The current state.

        Returns:
            True if this edge should be followed, False otherwise.
        """
        # Base edge is always followed
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert the edge to a dictionary representation.

        Returns:
            Dictionary representation of the edge.
        """
        return {
            "source": self.source_node,
            "target": self.target_node,
            "type": self.edge_type,
            "label": self.label,
            "description": self.description,
        }

    def __str__(self) -> str:
        """Get string representation of the edge.

        Returns:
            String representation.
        """
        return f"{self.source_node} -> {self.target_node} ({self.edge_type})"


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
        """Initialize a conditional edge.

        Args:
            source_node: Name of the source node.
            target_node: Name of the target node.
            condition: Function that determines if the edge should be followed.
            label: Optional label for the edge.
            description: Optional description of the edge.
        """
        super().__init__(
            source_node=source_node,
            target_node=target_node,
            edge_type=EdgeType.CONDITIONAL,
            label=label,
            description=description,
        )
        self.condition = condition

    def should_follow(self, state: StateType) -> bool:
        """Determine if this edge should be followed based on the condition.

        Args:
            state: The current state.

        Returns:
            True if this edge should be followed, False otherwise.
        """
        try:
            return self.condition(state)
        except Exception as e:
            logger.error(
                f"Error evaluating condition for edge {self}: {e}", exc_info=True
            )
            return False


class FallbackEdge(Edge[StateType]):
    """Edge that is followed when no other edges from the source are followed."""

    def __init__(
        self,
        source_node: str,
        target_node: str,
        label: EdgeLabelType = None,
        description: Optional[str] = None,
    ):
        """Initialize a fallback edge.

        Args:
            source_node: Name of the source node.
            target_node: Name of the target node.
            label: Optional label for the edge.
            description: Optional description of the edge.
        """
        super().__init__(
            source_node=source_node,
            target_node=target_node,
            edge_type=EdgeType.FALLBACK,
            label=label,
            description=description
            or f"Fallback edge from {source_node} to {target_node}",
        )

    def should_follow(self, state: StateType) -> bool:
        """Determine if this edge should be followed.

        For fallback edges, this method doesn't determine routing directly.
        The graph executor will try this edge if no other edges are followed.

        Args:
            state: The current state.

        Returns:
            Always returns True for fallback edges.
        """
        return True


@traced(name="create_edge")
def create_edge(
    source: str,
    target: str,
    edge_type: EdgeType = EdgeType.NORMAL,
    condition: Optional[EdgeConditionFunction] = None,
    label: EdgeLabelType = None,
    description: Optional[str] = None,
) -> Edge:
    """Create an edge based on the specified type.

    Args:
        source: Name of the source node.
        target: Name of the target node.
        edge_type: Type of edge to create.
        condition: For conditional edges, the condition function.
        label: Optional label for the edge.
        description: Optional description of the edge.

    Returns:
        The created edge.

    Raises:
        ValueError: If invalid parameters are provided.
    """
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


@traced(name="create_conditional_edge")
def create_conditional_edge(
    source: str,
    target: str,
    condition: EdgeConditionFunction,
    label: EdgeLabelType = None,
    description: Optional[str] = None,
) -> ConditionalEdge:
    """Create a conditional edge.

    Args:
        source: Name of the source node.
        target: Name of the target node.
        condition: Function that determines if the edge should be followed.
        label: Optional label for the edge.
        description: Optional description of the edge.

    Returns:
        A ConditionalEdge instance.
    """
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
    """Create a fallback edge.

    Args:
        source: Name of the source node.
        target: Name of the target node.
        label: Optional label for the edge.
        description: Optional description of the edge.

    Returns:
        A FallbackEdge instance.
    """
    return FallbackEdge(
        source_node=source,
        target_node=target,
        label=label,
        description=description,
    )


# Condition factory functions for common patterns
@traced(name="is_error_condition")
def is_error_condition(state: Union[AgentState, ControllerState]) -> bool:
    """Check if an error has occurred.

    Args:
        state: The agent or controller state.

    Returns:
        True if an error has occurred, False otherwise.
    """
    return bool(getattr(state, "error", None))


@traced(name="is_process_complete_condition")
def is_process_complete_condition(state: AgentState) -> bool:
    """Check if processing is complete.

    Args:
        state: The agent state.

    Returns:
        True if processing is complete, False otherwise.
    """
    return state.process_complete


@traced(name="are_all_tasks_assigned_condition")
def are_all_tasks_assigned_condition(state: ControllerState) -> bool:
    """Check if all tasks have been assigned.

    Args:
        state: The controller state.

    Returns:
        True if all tasks have been assigned, False otherwise.
    """
    return state.all_tasks_assigned


@traced(name="are_all_tasks_completed_condition")
def are_all_tasks_completed_condition(state: ControllerState) -> bool:
    """Check if all tasks have been completed.

    Args:
        state: The controller state.

    Returns:
        True if all tasks have been completed, False otherwise.
    """
    return state.all_tasks_completed


@traced(name="add_edges_to_graph")
def add_edges_to_graph(graph, edges: List[Edge]) -> None:
    """Add a list of edges to the graph.

    This function adapts the Edge objects to the format expected by LangGraph.

    Args:
        graph: A LangGraph StateGraph instance.
        edges: A list of Edge objects.
    """
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
