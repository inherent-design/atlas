# Tool System Core Concepts

The Atlas tool system enables agents to interact with external systems, perform specialized operations, and extend their capabilities beyond basic language processing. This document covers the core concepts of the tool system architecture.

## Overview

The tool system is built around several key components:

- **Tool Interface**: Abstract base class defining what constitutes a tool
- **Tool Schema**: Formal description of tool inputs and outputs
- **Tool Registry**: Central management system for tools
- **Permission System**: Controls which agents can access which tools
- **Tool Execution**: Standardized way to invoke tools

## Key Components

### Tool Interface

The `Tool` abstract base class defines the contract that all tools must implement:

```python
class Tool(abc.ABC):
    @property
    def name(self) -> str:
        """Get the name of the tool."""
        pass
        
    @property
    def description(self) -> str:
        """Get the description of the tool."""
        pass
        
    @property
    @abc.abstractmethod
    def schema(self) -> ToolSchema:
        """Get the schema for this tool."""
        pass
        
    @abc.abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the tool with the given arguments."""
        pass
```

Every tool must provide:

- A name (how agents refer to the tool)
- A description (explains what the tool does)
- A schema (formal definition of inputs and outputs)
- An execution method (the actual implementation)

### Tool Schema

The `ToolSchema` class defines the inputs and outputs of a tool using JSON Schema:

```python
@dataclass
class ToolSchema:
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema for inputs
    returns: Optional[Dict[str, Any]] = None  # JSON Schema for outputs
```

Tool schemas are used for:

1. **Validation**: Ensure arguments match expected types and requirements
2. **Documentation**: Show users and agents how to use the tool
3. **Code Generation**: Help agents construct valid tool calls
4. **UI Generation**: Support automatic interface generation

### AgentToolkit (Registry)

The `AgentToolkit` class serves as a centralized registry for tools:

```python
class AgentToolkit:
    def register_tool(self, tool: Union[Tool, Callable]) -> str:
        """Register a tool in the toolkit."""
        pass
        
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        pass
        
    def has_permission(self, agent_id: str, tool_name: str) -> bool:
        """Check if an agent has permission to use a specific tool."""
        pass
        
    def execute_tool(self, agent_id: str, tool_name: str, args: Dict[str, Any]) -> Any:
        """Execute a tool if the agent has permission."""
        pass
```

The toolkit provides:

- Tool registration and discovery
- Permission management
- Execution routing
- Tool metadata and schema access

## Creating Tools

Tools can be created in two ways:

### 1. Function-Based Tools

The simplest way to create a tool is by converting a Python function:

```python
from atlas.tools.base import AgentToolkit

# Create a toolkit
toolkit = AgentToolkit()

# Register a function as a tool
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the distance between two geographic coordinates in kilometers."""
    # Implementation details...
    return distance

# Register the function (automatically converts to a FunctionTool)
toolkit.register_tool(calculate_distance)
```

The tool system will automatically:
- Extract the function name as the tool name
- Use the docstring as the description
- Generate a schema from type hints and default values
- Wrap the function in a `FunctionTool` that handles validation

### 2. Custom Tool Classes

For more complex tools, you can create a custom class:

```python
from atlas.tools.base import Tool, ToolSchema

class WeatherTool(Tool):
    """Tool for retrieving weather information."""
    
    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or coordinates"
                    },
                    "units": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "default": "celsius"
                    }
                },
                "required": ["location"]
            },
            returns={
                "type": "object",
                "properties": {
                    "temperature": {"type": "number"},
                    "conditions": {"type": "string"},
                    "humidity": {"type": "number"}
                }
            }
        )
        
    def execute(self, location: str, units: str = "celsius") -> Dict[str, Any]:
        """Get weather for the specified location."""
        # Implementation details...
        return {
            "temperature": 22.5,
            "conditions": "sunny",
            "humidity": 45
        }

# Register the custom tool
toolkit.register_tool(WeatherTool())
```

Custom tool classes are useful when:
- You need complex parameter validation
- The tool maintains internal state
- You want to provide detailed schema information
- The tool requires resource management (connections, etc.)

## Permission Management

The tool system includes a permission model to control which agents can access which tools:

```python
# Grant an agent permission to use a specific tool
toolkit.grant_permission("research_agent", "web_search")

# Grant access to all tools
toolkit.grant_all_permissions("admin_agent")

# Revoke a permission
toolkit.revoke_permission("basic_agent", "database_query")

# Check if an agent has permission
if toolkit.has_permission("agent_id", "tool_name"):
    # Allow operation
```

This permission system enables:

- Security controls for sensitive operations
- Role-based tool access
- Fine-grained capability management
- Auditing of tool usage

## Tool Execution

Tools can be executed through the toolkit:

```python
# Execute a tool with arguments
result = toolkit.execute_tool(
    agent_id="research_agent", 
    tool_name="web_search",
    args={"query": "Atlas framework", "max_results": 5}
)

# Handle the result
print(f"Found {len(result)} results")
```

The execution process:

1. Verifies the agent has permission to use the tool
2. Retrieves the tool from the registry
3. Validates the provided arguments against the tool's schema
4. Executes the tool with the arguments
5. Returns the result

## Error Handling

The tool system includes comprehensive error handling:

```python
try:
    result = toolkit.execute_tool(agent_id, tool_name, args)
except ValueError as e:
    # Invalid arguments or tool doesn't exist
    print(f"Tool error: {str(e)}")
except PermissionError as e:
    # Agent doesn't have permission
    print(f"Permission denied: {str(e)}")
except Exception as e:
    # Tool execution error
    print(f"Execution error: {str(e)}")
```

Common error types:
- `ValueError`: Invalid arguments or nonexistent tool
- `PermissionError`: Agent lacks permission
- `TypeError`: Argument type mismatch
- Tool-specific exceptions

## Integration with Agents

The tool system integrates with agents through the `ToolCapableAgent` class:

```python
from atlas.agents.specialized.tool_agent import ToolCapableAgent

# Create a tool-capable agent
agent = ToolCapableAgent(
    worker_id="research_agent",
    specialization="Research and Information Retrieval",
    toolkit=toolkit
)

# Agent can now use tools in its processing
response = agent.process_message("Find information about Atlas framework")
```

See [Tool-Capable Agents](../agents/specialized.md) for more details on agent integration.

## Best Practices

1. **Use descriptive names and documentation**: Tools should have clear names and thorough descriptions.

2. **Follow the single responsibility principle**: Each tool should do one thing well.

3. **Provide comprehensive schemas**: Include detailed parameter descriptions and validation rules.

4. **Handle errors gracefully**: Catch exceptions and provide meaningful error messages.

5. **Limit permissions appropriately**: Only grant access to tools an agent actually needs.

6. **Consider performance**: For long-running operations, implement asynchronous tools.

7. **Validate inputs thoroughly**: Ensure tools validate all inputs before performing operations.

8. **Include example usage**: In documentation, show concrete examples of how to use the tool.

## Implementation Details

The tool system is designed to be extensible and integrates with:

- The messaging system for tool call communication
- The agent architecture for tool-capable agents
- The MCP (Model Context Protocol) for external tool integration
- The telemetry system for tool execution tracking