# Agent Messaging System

The Atlas messaging system provides a standardized format for communication between agents, enabling rich interactions, tool usage, and structured data exchange. This system forms the foundation for multi-agent workflows and tool-enabled operations.

## Overview

The messaging system is built around the `StructuredMessage` class, which provides:

- Consistent message format with metadata
- Support for tool calls and tool results
- Serialization capabilities for message exchange
- Message type categorization
- Source and target agent tracking

## Message Structure

Each structured message contains:

```
StructuredMessage
├── content: str             # Main text content
├── metadata: Dict           # Additional information about the message
├── task_id: str             # Unique identifier for tracking related messages
├── timestamp: float         # When the message was created
├── tool_calls: List[Dict]   # Tool calls requested in this message
├── tool_results: List[Dict] # Results from tool executions
├── source_agent: str        # Agent that sent the message
└── target_agent: str        # Agent that should receive the message
```

## Message Types

The `MessageType` class defines standard message types:

| Type | Description |
|------|-------------|
| `QUERY` | Initial user query or question |
| `TASK` | Task assignment from one agent to another |
| `RESPONSE` | Response to a query or task |
| `RESULT` | Final or intermediate task result |
| `ERROR` | Error notification |
| `STATUS` | Status update or progress report |
| `TOOL_REQUEST` | Request to use a tool |
| `TOOL_RESPONSE` | Response containing tool execution results |

## Working with Messages

### Creating a Basic Message

```python
from atlas.agents.messaging.message import StructuredMessage, MessageType

# Create a simple message
message = StructuredMessage(
    content="What's the weather in New York?",
    metadata={"type": MessageType.QUERY, "priority": "high"},
    task_id="weather-task-123"  # Optional: auto-generated if not provided
)

# Set source and target
message.source_agent = "user"
message.target_agent = "weather_agent"
```

### Creating Response Messages

The `create_response` factory method simplifies creating replies:

```python
# Create a response to an existing message
response = StructuredMessage.create_response(
    content="The weather in New York is sunny and 72°F.",
    original_message=message
)

# Source and target are automatically swapped
assert response.source_agent == "weather_agent"
assert response.target_agent == "user"
assert response.metadata["type"] == MessageType.RESPONSE
assert response.metadata["in_reply_to"] == message.task_id
```

### Error Handling

The `create_error` factory method creates properly formatted error messages:

```python
# Create an error message
error = StructuredMessage.create_error(
    error_message="Failed to retrieve weather data: API unavailable",
    original_message=message
)

assert error.metadata["type"] == MessageType.ERROR
```

## Tool Integration

Messages can include both tool calls (requests to use a tool) and tool results (the output of tool execution).

### Adding Tool Calls

```python
# Add a tool call to a message
weather_message = StructuredMessage(
    content="Check the weather forecast for London"
)

# Add a tool call programmatically
call_id = weather_message.add_tool_call(
    name="get_weather",
    arguments={"location": "London", "unit": "celsius"}
)
```

### Adding Tool Results

```python
# Add a tool result to a response
response = StructuredMessage(
    content="Here's the weather information you requested:"
)

# Add the tool result
response.add_tool_result(
    name="get_weather",
    result={"temp": 22, "conditions": "sunny", "humidity": 45},
    call_id=call_id,
    status="success"
)

# For errors in tool execution
response.add_tool_result(
    name="get_weather",
    result=None,
    call_id="failed-call-id",
    status="error",
    error="API connection timeout"
)
```

## Serialization

Messages can be serialized for transport between processes or storage:

```python
# Convert to dictionary
message_dict = message.to_dict()

# Convert to JSON string
json_str = message.to_json()

# Recreate from dictionary
reconstructed_msg = StructuredMessage.from_dict(message_dict)

# Recreate from JSON
reconstructed_msg = StructuredMessage.from_json(json_str)
```

## Task Assignment

The `create_task` factory method simplifies creating task assignment messages:

```python
# Create a task assignment
task_msg = StructuredMessage.create_task(
    content="Analyze the sentiment of these customer reviews",
    source_agent="controller",
    target_agent="sentiment_analysis_worker",
    task_data={"priority": "high", "deadline": "2h"}
)
```

## Integration with Tool-Capable Agents

The `ToolCapableAgent` class can automatically process messages with tool calls:

```python
from atlas.agents.specialized.tool_agent import ToolCapableAgent
from atlas.tools.base import AgentToolkit

# Create toolkit with tools
toolkit = AgentToolkit()
# ... register tools and permissions ...

# Create tool-capable agent
agent = ToolCapableAgent(
    worker_id="research_agent",
    specialization="Information Research",
    toolkit=toolkit
)

# Process a message with tool calls
response = agent.process_structured_message(message)

# Any tool calls in the agent's response will be executed
# and results added to the response message
```

## Message Flow Patterns

### Simple Request-Response

The most basic pattern is a direct request and response:

```
User → [Query Message] → Agent → [Response Message] → User
```

### Task Delegation

A controller agent can assign tasks to specialized workers:

```
Controller → [Task Message] → Worker → [Result Message] → Controller
```

### Multi-step Tool Execution

Agents can use tools to enhance their capabilities:

```
User → [Query Message] → Agent → [Tool Request] → Tools 
                                 ↓
User ← [Response with Tool Results] ← Agent ← [Tool Results]
```

### Inter-agent Collaboration

Multiple agents can collaborate on complex tasks:

```
Controller → [Task Message 1] → Worker A → [Intermediate Result] → Worker B
                                                                     ↓
Controller ← [Final Result] ← Worker B
```

## Best Practices

1. **Always use task_id for tracking related messages** - This enables proper threading of conversations.

2. **Include message type in metadata** - Always specify the message type using the `MessageType` constants.

3. **Validate tool arguments before execution** - Ensure tool calls include all required arguments.

4. **Handle errors gracefully** - Use error messages with clear descriptions and proper error status.

5. **Include relevant metadata** - Add context-specific metadata that will help with processing and routing.

6. **Process tool results intelligently** - When receiving tool results, incorporate them meaningfully into responses.

7. **Secure sensitive information** - Be careful not to include sensitive data in messages that could be persisted.

## Implementation Details

The messaging system is designed to be extensible and integrates seamlessly with the Atlas agent architecture. Key implementation features include:

- Backwards compatibility with existing agent interfaces
- Thread-safe message handling
- Efficient serialization that handles complex data types
- Comprehensive telemetry and tracing
- Unit test coverage for all key functionality