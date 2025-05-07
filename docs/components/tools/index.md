# Atlas Tool System

The Atlas tool system enables agents to extend their capabilities beyond basic language processing by interacting with external systems and performing specialized tasks. This section covers the tool system architecture, available tools, and how to create and use custom tools.

## Overview

The tool system is built around several key components:

- **Tool Interface**: Standard interface for all tools
- **Tool Registry**: Central management for tool registration and discovery
- **Permission System**: Control which agents can access which tools
- **Integration**: Seamless integration with the agent architecture

## Key Concepts

- **Tool**: A function or class that performs a specific task
- **ToolSchema**: Formal description of a tool's inputs and outputs
- **AgentToolkit**: Registry for tool registration and execution
- **Tool Execution**: Process of calling a tool with arguments
- **Tool Permissions**: Control which agents can use which tools

## Tool Categories

Atlas provides several categories of tools:

- **Knowledge Tools**: Tools for interacting with the knowledge base
- **Utility Tools**: General-purpose utility functions
- **Web Tools**: Tools for web interactions
- **MCP Tools**: Integration with Model Context Protocol

## Documentation Sections

- [Core Concepts](./core.md): Detailed overview of the tool system architecture
- [Standard Tools](./standard.md): Documentation for built-in tools (coming soon)
- [MCP Integration](./mcp.md): Information about Model Context Protocol integration (coming soon)

## Using Tools

Tools can be used in several ways:

1. **Directly with the Toolkit**:
   ```python
   # Execute a tool
   result = toolkit.execute_tool(
       agent_id="agent_id",
       tool_name="tool_name",
       args={"param1": "value1"}
   )
   ```

2. **Through a Tool-Capable Agent**:
   ```python
   # Agent will use tools automatically based on query
   response = agent.process_message("Query that might need a tool")
   ```

3. **Explicitly in Structured Messages**:
   ```python
   # Create a message with tool calls
   message = StructuredMessage(content="Process this query")
   message.add_tool_call("tool_name", {"param1": "value1"})
   
   # Process message
   response = agent.process_structured_message(message)
   ```

## Creating Custom Tools

You can create custom tools in two ways:

1. **Function-Based Tools**:
   ```python
   # Define a function
   def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
       """Calculate the distance between two coordinates."""
       # Implementation...
       return distance
   
   # Register it
   toolkit.register_tool(calculate_distance)
   ```

2. **Class-Based Tools**:
   ```python
   class WeatherTool(Tool):
       @property
       def schema(self) -> ToolSchema:
           # Define schema...
       
       def execute(self, location: str, units: str = "celsius") -> Dict[str, Any]:
           # Implementation...
   
   # Register it
   toolkit.register_tool(WeatherTool())
   ```

## Integration with Agents

The `ToolCapableAgent` class integrates seamlessly with the tool system:

```python
# Create a toolkit with tools
toolkit = AgentToolkit()
toolkit.register_tool(calculate_area)
toolkit.register_tool(get_weather)

# Create a tool-capable agent
agent = ToolCapableAgent(
    worker_id="assistant",
    specialization="Research and Problem Solving",
    toolkit=toolkit
)

# Grant permissions
toolkit.grant_permission("assistant", "calculate_area")
toolkit.grant_permission("assistant", "get_weather")

# Process queries that might use tools
result = agent.process_message("What's the area of a 5x3 rectangle?")
```

See [Specialized Agents](../agents/specialized.md) for more details on tool-capable agents.