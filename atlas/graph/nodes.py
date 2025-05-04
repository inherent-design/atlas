"""
Node functions for LangGraph in Atlas.

This module defines the node functions used in LangGraph workflows.
"""

import os
import sys
from typing import Dict, List, Any, Optional, TypedDict, Union, Callable

from anthropic import Anthropic
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END

from atlas.core.prompts import load_system_prompt
from atlas.core.config import AtlasConfig
from atlas.knowledge.retrieval import KnowledgeBase
from atlas.graph.state import AgentState, ControllerState, Message


def retrieve_knowledge(
    state: AgentState,
    config: Optional[AtlasConfig] = None
) -> AgentState:
    """Retrieve knowledge from the Atlas knowledge base.

    Args:
        state: The current state of the agent.
        config: Optional configuration. If not provided, default values are used.

    Returns:
        Updated state with retrieved knowledge.
    """
    # Use default config if none provided
    cfg = config or AtlasConfig()
    
    # Initialize knowledge base
    kb = KnowledgeBase(collection_name=cfg.collection_name, db_path=cfg.db_path)
    
    # Get the query from the last user message
    messages = state.messages
    if not messages:
        print("No messages in state, cannot determine query")
        state.context = {"documents": [], "query": ""}
        return state
    
    # Find the last user message
    last_user_message = None
    for message in reversed(messages):
        if message["role"] == "user":
            last_user_message = message["content"]
            break
    
    if not last_user_message:
        print("No user messages found in state")
        state.context = {"documents": [], "query": ""}
        return state
    
    # Extract query and retrieve documents
    query = last_user_message
    print(f"Retrieving knowledge for query: {query[:50]}{'...' if len(query) > 50 else ''}")
    
    try:
        # Retrieve relevant documents
        documents = kb.retrieve(query)
        print(f"Retrieved {len(documents)} relevant documents")
        
        if documents:
            # Print the top document sources for debugging
            print("Top relevant documents:")
            for i, doc in enumerate(documents[:3]):
                source = doc["metadata"].get("source", "Unknown")
                score = doc["relevance_score"]
                print(f"  {i+1}. {source} (score: {score:.4f})")
        
        # Update state with retrieved documents
        state.context = {"documents": documents, "query": query}
    except Exception as e:
        print(f"Error retrieving knowledge: {str(e)}")
        state.error = f"Knowledge retrieval error: {str(e)}"
        state.context = {"documents": [], "query": query}
    
    return state


def generate_response(
    state: AgentState,
    system_prompt_file: Optional[str] = None,
    config: Optional[AtlasConfig] = None
) -> AgentState:
    """Generate a response using the Anthropic API.

    Args:
        state: The current state of the agent.
        system_prompt_file: Optional path to a system prompt file.
        config: Optional configuration. If not provided, default values are used.

    Returns:
        Updated state with the generated response.
    """
    # Use default config if none provided
    cfg = config or AtlasConfig()
    
    # Initialize Anthropic client
    client = Anthropic(api_key=cfg.anthropic_api_key)
    
    # Load system prompt
    system_msg = load_system_prompt(system_prompt_file)
    
    try:
        # Add context to system prompt if available
        if state.context and state.context.get("documents"):
            documents = state.context["documents"]
            context_text = "\n\n## Relevant Knowledge\n\n"
            for i, doc in enumerate(documents[:3]):  # Limit to top 3 most relevant docs
                source = doc["metadata"].get("source", "Unknown")
                content = doc["content"]
                context_text += f"### Document {i+1}: {source}\n{content}\n\n"
            
            system_msg = system_msg + context_text
        
        # Get conversation history
        conversation = state.messages
        
        # Generate response
        response = client.messages.create(
            model=cfg.model_name,
            max_tokens=cfg.max_tokens,
            system=system_msg,
            messages=conversation
        )
        
        # Extract response text
        assistant_message = response.content[0].text
        
        # Add assistant response to history
        state.messages.append({"role": "assistant", "content": assistant_message})
        
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        state.error = f"Response generation error: {str(e)}"
        error_msg = "I'm sorry, I encountered an error processing your request. Please try again."
        state.messages.append({"role": "assistant", "content": error_msg})
    
    # Mark processing as complete
    state.process_complete = True
    
    return state


def route_to_workers(state: ControllerState) -> Union[str, None]:
    """Route the flow based on whether to use workers.

    Args:
        state: The controller state.

    Returns:
        The next node name or None to continue.
    """
    if state.all_tasks_completed:
        return "generate_final_response"
    elif not state.all_tasks_assigned:
        return "create_worker_tasks"
    elif len(state.completed_workers) < len(state.active_workers):
        return "wait_for_workers"
    else:
        return "process_worker_results"


def create_worker_tasks(state: ControllerState) -> ControllerState:
    """Create tasks for worker agents.

    Args:
        state: The controller state.

    Returns:
        Updated controller state with tasks created.
    """
    # Extract the user's query from the messages
    user_query = ""
    for message in reversed(state.messages):
        if message["role"] == "user":
            user_query = message["content"]
            break
    
    if not user_query:
        state.error = "No user query found in messages"
        state.all_tasks_assigned = True
        state.all_tasks_completed = True
        return state
    
    # Simple task creation (can be enhanced with more sophisticated task planning)
    tasks = [
        {
            "task_id": "retrieve_data",
            "worker_id": "retrieval_worker",
            "description": "Retrieve relevant knowledge from the knowledge base",
            "query": user_query
        },
        {
            "task_id": "analyze_content",
            "worker_id": "analysis_worker",
            "description": "Analyze the query and identify key information needs",
            "query": user_query
        },
        {
            "task_id": "generate_draft",
            "worker_id": "draft_worker",
            "description": "Generate a draft response based on the query",
            "query": user_query
        }
    ]
    
    # Add tasks to state
    state.tasks = tasks
    
    # Initialize worker states
    for task in tasks:
        worker_id = task["worker_id"]
        if worker_id not in state.workers:
            # Create new worker state
            worker_state = AgentState(
                worker_id=worker_id,
                messages=[{"role": "user", "content": user_query}]
            )
            state.workers[worker_id] = worker_state
            state.active_workers.append(worker_id)
    
    state.all_tasks_assigned = True
    
    return state


def process_worker_results(state: ControllerState) -> ControllerState:
    """Process results from worker agents.

    Args:
        state: The controller state.

    Returns:
        Updated controller state with processed results.
    """
    # Collect results from all workers
    combined_results = []
    
    for worker_id in state.completed_workers:
        worker_state = state.workers.get(worker_id)
        if worker_state:
            # Get the last assistant message from the worker
            for message in reversed(worker_state.messages):
                if message["role"] == "assistant":
                    combined_results.append({
                        "worker_id": worker_id,
                        "content": message["content"]
                    })
                    break
    
    # Add combined results to state
    state.results = combined_results
    state.all_tasks_completed = True
    
    return state


def generate_final_response(
    state: ControllerState,
    system_prompt_file: Optional[str] = None,
    config: Optional[AtlasConfig] = None
) -> ControllerState:
    """Generate a final response based on worker results.

    Args:
        state: The controller state.
        system_prompt_file: Optional path to a system prompt file.
        config: Optional configuration. If not provided, default values are used.

    Returns:
        Updated controller state with final response.
    """
    # Use default config if none provided
    cfg = config or AtlasConfig()
    
    # Initialize Anthropic client
    client = Anthropic(api_key=cfg.anthropic_api_key)
    
    # Load system prompt
    system_msg = load_system_prompt(system_prompt_file)
    
    try:
        # Enhance system prompt with worker results
        if state.results:
            results_text = "\n\n## Worker Results\n\n"
            for i, result in enumerate(state.results):
                worker_id = result["worker_id"]
                content = result["content"]
                results_text += f"### Worker {i+1}: {worker_id}\n{content}\n\n"
            
            system_msg = system_msg + results_text
        
        # Create synthesized prompt for final response
        user_query = ""
        for message in reversed(state.messages):
            if message["role"] == "user":
                user_query = message["content"]
                break
        
        synthesis_prompt = [
            {"role": "user", "content": user_query},
            {"role": "user", "content": "Please synthesize a comprehensive response based on the worker results."}
        ]
        
        # Generate final response
        response = client.messages.create(
            model=cfg.model_name,
            max_tokens=cfg.max_tokens,
            system=system_msg,
            messages=synthesis_prompt
        )
        
        # Extract response text
        assistant_message = response.content[0].text
        
        # Add final response to main conversation
        state.messages.append({"role": "assistant", "content": assistant_message})
        
    except Exception as e:
        print(f"Error generating final response: {str(e)}")
        state.error = f"Final response generation error: {str(e)}"
        error_msg = "I'm sorry, I encountered an error synthesizing the results. Please try again."
        state.messages.append({"role": "assistant", "content": error_msg})
    
    return state


def should_end(state: Union[AgentState, ControllerState]) -> bool:
    """Determine if the graph execution should end.

    Args:
        state: The agent or controller state.

    Returns:
        True if execution should end, False otherwise.
    """
    if isinstance(state, AgentState):
        return state.process_complete
    else:  # ControllerState
        return state.all_tasks_completed and len(state.messages) > 0 and state.messages[-1]["role"] == "assistant"