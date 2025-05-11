# Nodes

This document explains the graph node functions in Atlas, which form the building blocks of LangGraph workflows.

## Overview

Graph nodes in Atlas are Python functions that process state in LangGraph workflows. They provide:

1. **Modular Processing**: Self-contained units of functionality
2. **State Transformations**: Functions that transform state objects
3. **Error Handling**: Robust error management for each processing step
4. **LLM Integration**: Interaction with model providers
5. **Knowledge Retrieval**: Access to the knowledge base

The node system is designed to be:

- **Composable**: Nodes can be combined into diverse workflows
- **Stateless**: Nodes derive all information from the input state
- **Reusable**: Common functionality is encapsulated for reuse
- **Debuggable**: Clear logging and error messages

## Core Node Functions

### Knowledge Retrieval

The `retrieve_knowledge` node retrieves relevant documents from the knowledge base:

```python
def retrieve_knowledge(
    state: AgentState, config: Optional[AtlasConfig] = None
) -> AgentState:
    """Retrieve knowledge from the Atlas knowledge base."""
    # Use default config if none provided
    cfg = config or AtlasConfig()

    # Initialize knowledge base
    kb = KnowledgeBase(collection_name=cfg.collection_name, db_path=cfg.db_path)

    # Extract query from state
    last_user_message = get_last_user_message(state.messages)

    # Retrieve documents
    documents = kb.retrieve(last_user_message)

    # Update state with retrieved documents
    state.context = {"documents": documents, "query": last_user_message}

    return state
```

This node:
- Accepts an `AgentState` object and optional configuration
- Initializes the knowledge base with configuration parameters
- Extracts the query from the user's last message
- Retrieves relevant documents based on the query
- Updates the state with the retrieved documents
- Returns the updated state

### Response Generation

The `generate_response` node generates responses using the model provider:

```python
def generate_response(
    state: AgentState,
    system_prompt_file: Optional[str] = None,
    config: Optional[AtlasConfig] = None,
) -> AgentState:
    """Generate a response using the Anthropic API."""
    # Use default config if none provided
    cfg = config or AtlasConfig()

    # Initialize Anthropic client
    client = Anthropic(api_key=cfg.anthropic_api_key)

    # Load system prompt
    system_msg = load_system_prompt(system_prompt_file)

    # Add context to system prompt if available
    if state.context and state.context.get("documents"):
        context_text = format_documents_as_context(state.context["documents"])
        system_msg = system_msg + context_text

    # Generate response
    response = client.messages.create(
        model=cfg.model_name,
        max_tokens=cfg.max_tokens,
        system=system_msg,
        messages=state.messages,
    )

    # Add assistant response to history
    state.messages.append({"role": "assistant", "content": response.content[0].text})

    # Mark processing as complete
    state.process_complete = True

    return state
```

This node:
- Accepts an `AgentState`, optional system prompt file, and optional configuration
- Initializes the model client with the appropriate API key
- Loads the system prompt (default or custom)
- Enhances the system prompt with retrieved context if available
- Generates a response using the model provider
- Adds the response to the conversation history
- Marks processing as complete
- Returns the updated state

## Controller-Worker Nodes

### Worker Task Creation

The `create_worker_tasks` node creates tasks for worker agents:

```python
def create_worker_tasks(state: ControllerState) -> ControllerState:
    """Create tasks for worker agents."""
    # Extract the user's query
    user_query = get_last_user_message(state.messages)

    # Create tasks for different worker types
    tasks = [
        {
            "task_id": "retrieve_data",
            "worker_id": "retrieval_worker",
            "description": "Retrieve relevant knowledge",
            "query": user_query,
        },
        {
            "task_id": "analyze_content",
            "worker_id": "analysis_worker",
            "description": "Analyze the query",
            "query": user_query,
        },
        {
            "task_id": "generate_draft",
            "worker_id": "draft_worker",
            "description": "Generate a draft response",
            "query": user_query,
        },
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

    # Mark all tasks as assigned
    state.all_tasks_assigned = True

    return state
```

This node:
- Extracts the user query from the conversation history
- Creates task definitions for different worker types
- Initializes worker states with the user query
- Marks all tasks as assigned
- Returns the updated controller state

### Worker Results Processing

The `process_worker_results` node collects and processes results from worker agents:

```python
def process_worker_results(state: ControllerState) -> ControllerState:
    """Process results from worker agents."""
    # Collect results from all workers
    combined_results = []

    for worker_id in state.completed_workers:
        worker_state = state.workers.get(worker_id)
        if worker_state:
            # Get the last assistant message from the worker
            for message in reversed(worker_state.messages):
                if message["role"] == "assistant":
                    combined_results.append(
                        {"worker_id": worker_id, "content": message["content"]}
                    )
                    break

    # Add combined results to state
    state.results = combined_results
    state.all_tasks_completed = True

    return state
```

This node:
- Collects the latest assistant message from each completed worker
- Adds the combined results to the controller state
- Marks all tasks as completed
- Returns the updated controller state

### Final Response Generation

The `generate_final_response` node synthesizes a final response from worker results:

```python
def generate_final_response(
    state: ControllerState,
    system_prompt_file: Optional[str] = None,
    config: Optional[AtlasConfig] = None,
) -> ControllerState:
    """Generate a final response based on worker results."""
    # Use default config if none provided
    cfg = config or AtlasConfig()

    # Initialize model client
    client = Anthropic(api_key=cfg.anthropic_api_key)

    # Load system prompt
    system_msg = load_system_prompt(system_prompt_file)

    # Enhance system prompt with worker results
    if state.results:
        results_text = format_worker_results(state.results)
        system_msg = system_msg + results_text

    # Extract user query
    user_query = get_last_user_message(state.messages)

    # Generate synthesized response
    synthesis_prompt = [
        {"role": "user", "content": user_query},
        {
            "role": "user",
            "content": "Please synthesize a comprehensive response based on the worker results.",
        },
    ]

    # Generate final response
    response = client.messages.create(
        model=cfg.model_name,
        max_tokens=cfg.max_tokens,
        system=system_msg,
        messages=synthesis_prompt,
    )

    # Add final response to main conversation
    state.messages.append({"role": "assistant", "content": response.content[0].text})

    return state
```

This node:
- Initializes the model client
- Loads the system prompt
- Enhances the prompt with worker results
- Creates a synthesis prompt with the original query
- Generates a final response that synthesizes the worker results
- Adds the response to the main conversation history
- Returns the updated controller state

## Routing Nodes

### Flow Routing

The `route_to_workers` node determines the flow in controller-worker workflows:

```python
def route_to_workers(state: ControllerState) -> ControllerState:
    """Route the flow based on whether to use workers."""
    # This function now just returns the state itself
    # The routing logic is implemented in conditional edges
    return state
```

This node acts as a transition point where conditional edges determine the next step.

### End Condition

The `should_end` function determines when workflow execution should end:

```python
def should_end(state: Union[AgentState, ControllerState]) -> bool:
    """Determine if the graph execution should end."""
    if isinstance(state, AgentState):
        return state.process_complete
    else:  # ControllerState
        return (
            state.all_tasks_completed
            and len(state.messages) > 0
            and state.messages[-1]["role"] == "assistant"
        )
```

This function:
- Handles both `AgentState` and `ControllerState` types
- Checks different completion conditions based on the state type
- Returns a boolean indicating whether execution should end

## Integration with Workflows

### Basic RAG Workflow

The basic RAG workflow integrates the `retrieve_knowledge` and `generate_response` nodes:

```python
def create_basic_rag_graph(
    system_prompt_file: Optional[str] = None, config: Optional[AtlasConfig] = None
) -> StateGraph:
    """Create a basic RAG workflow graph."""
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

    return builder.compile()
```

### Controller-Worker Workflow

The controller-worker workflow integrates multiple node functions:

```python
def create_controller_worker_graph(
    system_prompt_file: Optional[str] = None, config: Optional[AtlasConfig] = None
) -> StateGraph:
    """Create a controller-worker workflow graph."""
    # Create StateGraph with ControllerState
    builder = StateGraph(ControllerState)

    # Use currying to pass additional parameters
    def final_response(state: ControllerState) -> ControllerState:
        return generate_final_response(state, system_prompt_file, config)

    # Add nodes
    builder.add_node("retrieve_knowledge", retrieve_knowledge)
    builder.add_node("create_worker_tasks", create_worker_tasks)
    builder.add_node("process_worker_results", process_worker_results)
    builder.add_node("generate_final_response", final_response)
    builder.add_node("route_workers", route_to_workers)

    # Add conditional edges for routing
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

    return builder.compile()
```

## Usage Examples

### Running a Basic RAG Node

```python
from atlas.graph.nodes import retrieve_knowledge, generate_response
from atlas.graph.state import AgentState
from atlas.core.config import AtlasConfig

# Create configuration
config = AtlasConfig(model_name="claude-3-7-sonnet-20250219")

# Create initial state
initial_state = AgentState(
    messages=[{"role": "user", "content": "What is the trimodal methodology?"}]
)

# Run the knowledge retrieval node
state_with_knowledge = retrieve_knowledge(initial_state, config)

# Run the response generation node
final_state = generate_response(state_with_knowledge, config=config)

# Get the response
response = final_state.messages[-1]["content"]
print(f"Response: {response}")
```

### Creating a Custom Node

```python
from typing import Optional
from atlas.graph.state import AgentState
from atlas.core.config import AtlasConfig
from atlas.core.telemetry import traced

@traced(name="summarize_documents")
def summarize_documents(
    state: AgentState, config: Optional[AtlasConfig] = None
) -> AgentState:
    """Summarize the retrieved documents and add summary to state."""
    # Use default config if none provided
    cfg = config or AtlasConfig()

    # Skip if no context or documents
    if not state.context or not state.context.get("documents"):
        return state

    documents = state.context["documents"]

    # Create a prompt for summarization
    summary_prompt = "Summarize the following documents concisely:\n\n"
    for i, doc in enumerate(documents[:3]):  # Limit to top 3
        summary_prompt += f"Document {i+1}: {doc['content'][:500]}...\n\n"

    # Add to conversation temporarily
    state.messages.append({"role": "user", "content": summary_prompt})

    # Generate summary
    summary_state = generate_response(state, config=cfg)

    # Extract summary and remove temporary messages
    summary = summary_state.messages[-1]["content"]
    state.messages = state.messages[:-2]  # Remove temp messages

    # Store summary in state (could extend AgentState for this)
    if not hasattr(state, "summaries"):
        state.summaries = []
    state.summaries.append(summary)

    return state
```

### Integrating with a Custom Workflow

```python
from langgraph.graph import StateGraph, END
from atlas.graph.state import AgentState
from atlas.core.config import AtlasConfig

def create_custom_workflow(
    system_prompt_file: Optional[str] = None,
    config: Optional[AtlasConfig] = None
) -> StateGraph:
    """Create a custom workflow with document summarization."""
    # Create StateGraph with AgentState
    builder = StateGraph(AgentState)

    # Define node functions with configuration
    def retrieve(state: AgentState) -> AgentState:
        return retrieve_knowledge(state, config)

    def summarize(state: AgentState) -> AgentState:
        return summarize_documents(state, config)

    def generate(state: AgentState) -> AgentState:
        return generate_response(state, system_prompt_file, config)

    # Add nodes
    builder.add_node("retrieve_knowledge", retrieve)
    builder.add_node("summarize_documents", summarize)
    builder.add_node("generate_response", generate)

    # Define edges
    builder.add_edge("retrieve_knowledge", "summarize_documents")
    builder.add_edge("summarize_documents", "generate_response")
    builder.add_conditional_edges(
        "generate_response", should_end, {True: END, False: "retrieve_knowledge"}
    )

    # Set the entry point
    builder.set_entry_point("retrieve_knowledge")

    return builder.compile()
```

## Advanced Patterns

### Parallel Node Execution

For complex workflows, you can implement parallel node execution:

```python
def execute_parallel_tasks(state: ControllerState) -> ControllerState:
    """Execute multiple tasks in parallel."""
    import concurrent.futures

    # Define task functions that operate on copies of state
    tasks = {
        "retrieve": lambda s: retrieve_knowledge(s.copy(), config),
        "analyze": lambda s: analyze_query(s.copy(), config),
        "draft": lambda s: draft_response(s.copy(), config),
    }

    results = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit all tasks
        futures = {
            task_name: executor.submit(task_func, state)
            for task_name, task_func in tasks.items()
        }

        # Collect results as they complete
        for task_name, future in futures.items():
            try:
                task_state = future.result()
                results[task_name] = task_state
            except Exception as e:
                # Handle task failure
                print(f"Task {task_name} failed: {e}")

    # Merge results back into the original state
    for task_name, task_state in results.items():
        if task_name == "retrieve" and task_state.context:
            state.context = task_state.context
        elif task_name == "analyze" and hasattr(task_state, "analysis"):
            state.analysis = task_state.analysis
        elif task_name == "draft" and task_state.messages:
            state.draft = task_state.messages[-1]["content"]

    return state
```

### Stateful Callbacks

For complex nodes that need to track progress, you can use stateful callbacks:

```python
def generate_streaming_response(
    state: AgentState,
    system_prompt_file: Optional[str] = None,
    config: Optional[AtlasConfig] = None,
    callback: Optional[Callable[[str, str], None]] = None,
) -> AgentState:
    """Generate a response with streaming and callback."""
    # Use default config if none provided
    cfg = config or AtlasConfig()

    # Initialize model client
    client = Anthropic(api_key=cfg.anthropic_api_key)

    # Load system prompt
    system_msg = load_system_prompt(system_prompt_file)

    # Add context if available
    if state.context and state.context.get("documents"):
        context_text = format_documents_as_context(state.context["documents"])
        system_msg = system_msg + context_text

    # Track the full content
    full_content = ""

    # Define streaming callback
    def stream_callback(delta, response):
        nonlocal full_content
        full_content += delta
        if callback:
            callback(delta, full_content)

    # Generate streaming response
    model_request = ModelRequest(
        messages=[ModelMessage.user(msg["content"]) for msg in state.messages],
        system_prompt=system_msg,
        max_tokens=cfg.max_tokens,
    )

    response = client.stream(model_request, stream_callback)

    # Add response to history
    state.messages.append({"role": "assistant", "content": full_content})
    state.process_complete = True

    return state
```

### Node Result Caching

For performance optimization, implement node result caching:

```python
# Cache for node results
NODE_CACHE = {}

def cached_node(
    node_func: Callable[[AgentState], AgentState],
    cache_key_func: Callable[[AgentState], str],
    max_age_seconds: int = 300,
) -> Callable[[AgentState], AgentState]:
    """Create a cached version of a node function."""
    import time

    def wrapper(state: AgentState) -> AgentState:
        # Generate cache key based on state
        cache_key = cache_key_func(state)

        # Check if result is in cache and still valid
        if cache_key in NODE_CACHE:
            cached_result, timestamp = NODE_CACHE[cache_key]
            if time.time() - timestamp < max_age_seconds:
                print(f"Using cached result for {node_func.__name__}")
                return cached_result

        # Execute the node function
        result = node_func(state)

        # Store result in cache
        NODE_CACHE[cache_key] = (result, time.time())

        return result

    return wrapper

# Example usage
def cache_key_for_retrieval(state: AgentState) -> str:
    """Generate a cache key for retrieval node."""
    query = ""
    for msg in reversed(state.messages):
        if msg["role"] == "user":
            query = msg["content"]
            break
    return f"retrieve:{hash(query)}"

# Create cached version of retrieve_knowledge
cached_retrieve = cached_node(
    retrieve_knowledge,
    cache_key_for_retrieval,
    max_age_seconds=3600  # Cache for 1 hour
)
```

## Best Practices

### Node Function Design

1. **Pure Functions**: Design nodes as pure functions where possible
2. **Single Responsibility**: Each node should have one clear purpose
3. **Error Handling**: Include robust error handling in every node
4. **Logging**: Add appropriate logging for monitoring and debugging
5. **Type Annotations**: Use proper type hints for parameters and return values

### State Management

1. **Immutability**: Treat state as immutable, returning a new state
2. **Complete Updates**: Return the full state, not just changed parts
3. **Validation**: Validate state before and after processing
4. **Default Values**: Use sensible defaults for optional parameters

### Performance

1. **Efficient Processing**: Optimize for computational efficiency
2. **Resource Management**: Release resources when they're no longer needed
3. **Caching**: Use caching for expensive operations
4. **Streaming**: Support streaming for large responses when possible

## Related Documentation

- [State Management](state.md) - Documentation for state models
- [Graph Edges](edges.md) - Documentation for graph routing
- [Workflows](../../workflows/multi_agent.md) - Documentation for complete workflows
