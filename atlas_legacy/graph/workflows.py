"""
Workflow definitions for LangGraph in Atlas.

This module defines the graph workflows used by Atlas agents.
"""

from typing import Any

from langgraph.graph import END, StateGraph

from atlas.core.config import AtlasConfig
from atlas.graph.nodes import (
    create_worker_tasks,
    generate_final_response,
    generate_response,
    process_worker_results,
    retrieve_knowledge,
    route_to_workers,
    should_end,
)
from atlas.graph.state import AgentState, ControllerState


def create_basic_rag_graph(
    system_prompt_file: str | None = None, config: AtlasConfig | None = None
) -> StateGraph:
    """Create a basic RAG workflow graph.

    Args:
        system_prompt_file: Optional path to a system prompt file.
        config: Optional configuration. If not provided, default values are used.

    Returns:
        A StateGraph for the basic RAG workflow.
    """
    # Create StateGraph with AgentState
    builder = StateGraph(AgentState)

    # Use currying to pass additional parameters to node functions
    def retrieve(state: AgentState) -> AgentState:
        return retrieve_knowledge(state, config)

    def generate(state: AgentState) -> AgentState:
        return generate_response(state, system_prompt_file, config)

    # Add nodes
    builder.add_node("retrieve_knowledge", retrieve)
    builder.add_node("generate_response", generate)

    # Define edges
    builder.add_edge("retrieve_knowledge", "generate_response")
    builder.add_conditional_edges(
        "generate_response", should_end, {True: END, False: "retrieve_knowledge"}
    )

    # Set the entry point
    builder.set_entry_point("retrieve_knowledge")

    # Compile the graph
    return builder.compile()


def create_controller_worker_graph(
    system_prompt_file: str | None = None, config: AtlasConfig | None = None
) -> StateGraph:
    """Create a controller-worker workflow graph.

    Args:
        system_prompt_file: Optional path to a system prompt file.
        config: Optional configuration. If not provided, default values are used.

    Returns:
        A StateGraph for the controller-worker workflow.
    """
    # Create StateGraph with ControllerState
    builder = StateGraph(ControllerState)

    # Use currying to pass additional parameters to node functions
    def final_response(state: ControllerState) -> ControllerState:
        return generate_final_response(state, system_prompt_file, config)

    # Add nodes
    builder.add_node("retrieve_knowledge", retrieve_knowledge)
    builder.add_node("create_worker_tasks", create_worker_tasks)
    builder.add_node("process_worker_results", process_worker_results)
    builder.add_node("generate_final_response", final_response)

    # Add conditional edges for routing (instead of using router)
    builder.add_node("route_workers", route_to_workers)
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

    # Define edges
    builder.add_edge("retrieve_knowledge", "route_workers")
    builder.add_edge("create_worker_tasks", "route_workers")
    builder.add_edge("process_worker_results", "route_workers")
    builder.add_edge("generate_final_response", END)

    # Set the entry point
    builder.set_entry_point("retrieve_knowledge")

    # Compile the graph
    return builder.compile()


def get_workflow_graph(
    workflow_type: str = "rag",
    system_prompt_file: str | None = None,
    config: AtlasConfig | None = None,
) -> StateGraph:
    """Get a workflow graph based on the specified type.

    Args:
        workflow_type: Type of workflow graph to create ('rag' or 'controller').
        system_prompt_file: Optional path to a system prompt file.
        config: Optional configuration. If not provided, default values are used.

    Returns:
        A StateGraph for the specified workflow type.
    """
    if workflow_type == "rag":
        return create_basic_rag_graph(system_prompt_file, config)
    elif workflow_type in ["controller", "advanced"]:
        return create_controller_worker_graph(system_prompt_file, config)
    else:
        raise ValueError(f"Unknown workflow type: {workflow_type}")


# Examples of how to run the workflows
def run_rag_workflow(
    query: str,
    system_prompt_file: str | None = None,
    config: AtlasConfig | None = None,
) -> dict[str, Any]:
    """Run the basic RAG workflow.

    Args:
        query: User query to process.
        system_prompt_file: Optional path to a system prompt file.
        config: Optional configuration. If not provided, default values are used.

    Returns:
        Final state after workflow execution.
    """
    # Create the graph
    graph = create_basic_rag_graph(system_prompt_file, config)

    # Create initial state
    initial_state = AgentState(messages=[{"role": "user", "content": query}])

    # Run the graph
    final_state = graph.invoke(initial_state)

    return final_state


def run_controller_workflow(
    query: str,
    system_prompt_file: str | None = None,
    config: AtlasConfig | None = None,
) -> dict[str, Any]:
    """Run the controller-worker workflow.

    Args:
        query: User query to process.
        system_prompt_file: Optional path to a system prompt file.
        config: Optional configuration. If not provided, default values are used.

    Returns:
        Final state after workflow execution.
    """
    # Create the graph
    graph = create_controller_worker_graph(system_prompt_file, config)

    # Create initial state
    initial_state = ControllerState(messages=[{"role": "user", "content": query}])

    # Run the graph
    final_state = graph.invoke(initial_state)

    return final_state
