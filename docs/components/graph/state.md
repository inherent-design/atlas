# State Management

This document explains the state management system in Atlas, which provides structured state models for LangGraph workflows.

## Overview

The state management system in Atlas provides:

1. **Structured State Models**: Pydantic models for representing workflow state
2. **Type Safety**: Type hints and validation for state data
3. **Message History**: Standardized conversation history tracking
4. **Context Management**: Storage for retrieved knowledge and metadata
5. **Worker Coordination**: State patterns for parallel agent workflows

The system is designed to be:

- **Consistent**: Provide uniform state access patterns
- **Extensible**: Support custom state attributes
- **Typesafe**: Leverage Pydantic's type validation
- **Compatible**: Integrate seamlessly with LangGraph

## Core Components

### Base Types and Classes

The state management system starts with basic type definitions:

```python
class Message(TypedDict):
    """Message in the conversation."""
    role: str
    content: str

class Document(TypedDict):
    """Document from the knowledge base."""
    content: str
    metadata: Dict[str, Any]
    relevance_score: float

class Context(TypedDict):
    """Context for the agent."""
    documents: List[Document]
    query: str
```

These types provide standardized structures for:
- **Message**: Conversation messages with role and content
- **Document**: Knowledge documents with content, metadata, and relevance
- **Context**: Container for retrieved documents and query information

### Worker Configuration

For specialized agents, the system defines the `WorkerConfig` class:

```python
class WorkerConfig(BaseModel):
    """Configuration for a worker agent."""
    worker_id: str = Field(description="Unique identifier for the worker")
    specialization: str = Field(description="What this worker specializes in")
    system_prompt: str = Field(description="System prompt for this worker")
```

This enables standardized configuration of worker agents with:
- **Identification**: Unique worker IDs
- **Specialization**: Worker roles and capabilities
- **Customization**: Worker-specific system prompts

### AgentState

The primary state model for individual agents is `AgentState`:

```python
class AgentState(BaseModel):
    """State for a LangGraph agent."""
    # Basic state
    messages: List[Message] = Field(
        default_factory=list, description="Conversation history"
    )
    context: Optional[Context] = Field(
        default=None, description="Retrieved context information"
    )

    # Worker agent state (for parallel processing)
    worker_id: Optional[str] = Field(
        default=None, description="ID of the current worker (if any)"
    )
    worker_results: Dict[str, Any] = Field(
        default_factory=dict, description="Results from worker agents"
    )
    worker_configs: List[WorkerConfig] = Field(
        default_factory=list, description="Configurations for worker agents"
    )

    # Flags
    process_complete: bool = Field(
        default=False, description="Whether processing is complete"
    )
    error: Optional[str] = Field(default=None, description="Error message if any")
```

The `AgentState` class maintains:
- **Conversation History**: List of user and assistant messages
- **Retrieved Knowledge**: Contextual information and documents
- **Worker Metadata**: ID and results for parallel processing
- **Status Flags**: Processing completion and error states

### ControllerState

For multi-agent orchestration, the system defines the `ControllerState` class:

```python
class ControllerState(BaseModel):
    """State for a controller agent managing multiple workers."""
    # Main state
    messages: List[Message] = Field(
        default_factory=list, description="Main conversation history"
    )
    context: Optional[Context] = Field(
        default=None, description="Retrieved context information"
    )

    # Worker management
    workers: Dict[str, AgentState] = Field(
        default_factory=dict, description="States for all workers"
    )
    active_workers: List[str] = Field(
        default_factory=list, description="Currently active worker IDs"
    )
    completed_workers: List[str] = Field(
        default_factory=list, description="IDs of workers that have completed"
    )

    # Task tracking
    tasks: List[Dict[str, Any]] = Field(
        default_factory=list, description="Tasks to be processed"
    )
    results: List[Dict[str, Any]] = Field(
        default_factory=list, description="Results from completed tasks"
    )

    # Flags
    all_tasks_assigned: bool = Field(
        default=False, description="Whether all tasks have been assigned"
    )
    all_tasks_completed: bool = Field(
        default=False, description="Whether all tasks have been completed"
    )
```

The `ControllerState` class manages:
- **Global Conversation**: User-facing conversation history
- **Worker Registry**: Tracking multiple worker agents
- **Task Management**: Distribution and collection of tasks
- **Completion Status**: Assignment and completion flags

## Integration with LangGraph

### State Graph Initialization

The state models integrate with LangGraph's `StateGraph`:

```python
from langgraph.graph import StateGraph
from atlas.graph.state import AgentState, ControllerState

# Create a graph with AgentState
basic_graph = StateGraph(AgentState)

# Create a graph with ControllerState for multi-agent workflows
controller_graph = StateGraph(ControllerState)
```

This ensures that:
- **Type Safety**: Graph nodes work with properly typed state
- **Validation**: State transitions validate against the model
- **Documentation**: State fields are self-documenting via descriptions

### Node Functions

Node functions in LangGraph receive and return the state:

```python
def retrieve_knowledge(state: AgentState, config: Optional[AtlasConfig] = None) -> AgentState:
    """Retrieve knowledge from the Atlas knowledge base."""
    # Initialize knowledge base
    kb = KnowledgeBase(collection_name=cfg.collection_name, db_path=cfg.db_path)
    
    # Extract query from state
    # ...
    
    # Update state with retrieved documents
    state.context = {"documents": documents, "query": query}
    
    return state
```

### Conditional Edges

State fields are used for graph routing decisions:

```python
# Add conditional edge based on state
builder.add_conditional_edges(
    "generate_response", 
    should_end,  # Function that examines state.process_complete
    {True: END, False: "retrieve_knowledge"}
)
```

## State Management Patterns

### Conversation State Management

The `AgentState` maintains a conversation history:

```python
# Initialize state with user message
initial_state = AgentState(messages=[{"role": "user", "content": "Hello"}])

# Add assistant response in a node function
def add_response(state: AgentState) -> AgentState:
    # Generate response using LLM
    response = "..."
    
    # Add to conversation history
    state.messages.append({"role": "assistant", "content": response})
    return state
```

### Context Management

Retrieved knowledge is stored in the context field:

```python
# Store retrieved documents in state context
def store_context(state: AgentState, documents: List[Document]) -> AgentState:
    state.context = {
        "documents": documents,
        "query": "original query"
    }
    return state

# Access context in another node
def use_context(state: AgentState) -> AgentState:
    if state.context and state.context["documents"]:
        documents = state.context["documents"]
        # Use documents...
    return state
```

### Error Handling

State includes error tracking:

```python
# Handle errors in node function
def node_with_error_handling(state: AgentState) -> AgentState:
    try:
        # Potentially risky operation...
        result = api_call()
    except Exception as e:
        # Record error in state
        state.error = f"API error: {str(e)}"
    
    return state

# Check for errors in conditional edge function
def check_for_errors(state: AgentState) -> bool:
    return state.error is not None
```

### Worker Orchestration

In multi-agent workflows, the `ControllerState` manages worker coordination:

```python
# Create tasks for workers
def create_worker_tasks(state: ControllerState) -> ControllerState:
    # Create tasks based on user query
    # ...
    
    # Add tasks to state
    state.tasks = tasks
    
    # Initialize worker states
    for task in tasks:
        worker_id = task["worker_id"]
        worker_state = AgentState(
            worker_id=worker_id, 
            messages=[{"role": "user", "content": query}]
        )
        state.workers[worker_id] = worker_state
        state.active_workers.append(worker_id)
    
    state.all_tasks_assigned = True
    return state

# Process results from workers
def process_worker_results(state: ControllerState) -> ControllerState:
    combined_results = []
    
    for worker_id in state.completed_workers:
        worker_state = state.workers.get(worker_id)
        if worker_state:
            # Extract results from worker state
            # ...
            combined_results.append({"worker_id": worker_id, "content": result})
    
    state.results = combined_results
    state.all_tasks_completed = True
    return state
```

## Usage Examples

### Basic Agent State

```python
from atlas.graph.state import AgentState
from atlas.graph.workflows import create_basic_rag_graph

# Create initial state
initial_state = AgentState(
    messages=[{"role": "user", "content": "What is the trimodal methodology?"}]
)

# Create and run graph
graph = create_basic_rag_graph()
final_state = graph.invoke(initial_state)

# Extract assistant's response from final state
assistant_response = final_state.messages[-1]["content"]
print(f"Response: {assistant_response}")
```

### Multi-Agent Controller State

```python
from atlas.graph.state import ControllerState
from atlas.graph.workflows import create_controller_worker_graph

# Create initial state
initial_state = ControllerState(
    messages=[{"role": "user", "content": "Explain knowledge graphs in Atlas"}]
)

# Create and run graph
graph = create_controller_worker_graph()
final_state = graph.invoke(initial_state)

# Access worker results
print(f"Completed workers: {final_state.completed_workers}")
for worker_id, result in final_state.results:
    print(f"Results from {worker_id}: {result[:100]}...")

# Get final response
final_response = final_state.messages[-1]["content"]
print(f"Final response: {final_response}")
```

### Creating Custom State

You can extend the base state models for specialized workflows:

```python
from pydantic import BaseModel, Field
from atlas.graph.state import AgentState

class CustomDocumentState(BaseModel):
    document_id: str
    processed: bool = False
    summary: Optional[str] = None

class DocumentProcessingState(AgentState):
    """Extended state for document processing workflows."""
    documents_to_process: List[CustomDocumentState] = Field(
        default_factory=list,
        description="Documents pending processing"
    )
    processed_documents: List[CustomDocumentState] = Field(
        default_factory=list,
        description="Documents that have been processed"
    )
    current_document_id: Optional[str] = Field(
        default=None,
        description="ID of the document currently being processed"
    )

# Use in a LangGraph workflow
from langgraph.graph import StateGraph

graph = StateGraph(DocumentProcessingState)
# Add nodes and edges...
```

## Advanced Patterns

### State Versioning

For long-running workflows, state versioning can be implemented:

```python
# Add version tracking to state
class VersionedAgentState(AgentState):
    version: int = Field(default=1, description="State schema version")
    state_history: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="History of state transitions"
    )
    
    def snapshot(self) -> None:
        """Create a snapshot of the current state."""
        snapshot = self.dict()
        del snapshot["state_history"]  # Don't include history in history
        self.state_history.append(snapshot)
```

### State Validation

Use Pydantic validation for custom state constraints:

```python
from pydantic import validator

class ValidatedAgentState(AgentState):
    max_history_length: int = Field(default=50, description="Maximum history length")
    
    @validator("messages")
    def validate_messages_length(cls, v, values):
        max_length = values.get("max_history_length", 50)
        if len(v) > max_length:
            # Truncate to the most recent messages
            return v[-max_length:]
        return v
```

### State Transformations

Create utility functions for common state transformations:

```python
def add_user_message(state: AgentState, message: str) -> AgentState:
    """Add a user message to the state."""
    state.messages.append({"role": "user", "content": message})
    return state

def add_assistant_message(state: AgentState, message: str) -> AgentState:
    """Add an assistant message to the state."""
    state.messages.append({"role": "assistant", "content": message})
    return state

def clear_context(state: AgentState) -> AgentState:
    """Clear the context from the state."""
    state.context = None
    return state
```

## Best Practices

### State Design Principles

1. **Single Source of Truth**: Keep all related data in one state object
2. **Immutability**: Treat state as immutable, return a new/updated state
3. **Minimal State**: Include only necessary information in the state
4. **Type Safety**: Use type hints and validation for all state fields
5. **Self-Documentation**: Include clear field descriptions

### Performance Considerations

For large state objects:

1. **Selective Updates**: Only update fields that have changed
2. **Pruning**: Remove unnecessary data from the state
3. **Lazy Loading**: Defer loading large data until needed
4. **Serialization**: Consider serialization efficiency for large objects

### Error Handling

Robust error handling with state:

1. **Error Fields**: Use dedicated fields for error information
2. **Validation**: Validate state before processing
3. **Recovery**: Include enough information to recover from errors
4. **Logging**: Log state transitions and errors

## Related Documentation

- [Graph Nodes](nodes.md) - Documentation for graph node functions
- [Graph Edges](edges.md) - Documentation for conditional edge routing
- [Workflows](/workflows/multi_agent.md) - Documentation for complete workflows using these state models