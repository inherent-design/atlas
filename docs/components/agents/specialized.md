# Specialized Agent Types

Atlas provides specialized agent types that extend the core agent capabilities with additional features and behaviors tailored to specific use cases. This document covers the specialized agent types available in the framework.

## Overview

Specialized agents build upon the base `WorkerAgent` class to provide enhanced capabilities:

- **Tool-capable agents**: Agents that can use tools to enhance their capabilities
- **Knowledge-focused agents**: Agents specialized in knowledge base operations
- **Other specialized workers**: Agents with specific roles and specializations

## Tool-Capable Agents

The `ToolCapableAgent` class extends `WorkerAgent` with the ability to use tools to perform actions beyond basic language processing.

### Key Features

- Tool execution capabilities
- Permission-controlled tool access
- Tool call parsing from model responses
- Structured message support
- Capability advertising

### How It Works

Tool-capable agents use the `AgentToolkit` to manage and execute tools:

1. The agent receives a structured message or task with a user query
2. The agent processes the query using its underlying language model
3. If the model response includes tool calls, the agent extracts them
4. The agent executes the tools with the specified arguments
5. The tool results are incorporated into the response
6. The agent sends a structured response with both content and tool results

### Tool Call Format

The agent can recognize tool calls in model responses using this format:

```json
{
  "tool_calls": [
    {
      "name": "tool_name",
      "arguments": {
        "arg1": "value1",
        "arg2": "value2"
      }
    }
  ]
}
```

This JSON block should be included in code blocks in the model's response.

### Creating a Tool-Capable Agent

```python
from atlas.agents.specialized.tool_agent import ToolCapableAgent
from atlas.tools.base import AgentToolkit
from atlas.tools.standard.knowledge_tools import create_knowledge_toolkit

# Create a toolkit
toolkit = AgentToolkit()

# Register tools (functions or Tool instances)
def search_web(query: str, max_results: int = 5) -> list:
    """Search the web for information."""
    # Implementation...
    return results

toolkit.register_tool(search_web)

# Register knowledge tools
kb_tools = create_knowledge_toolkit(knowledge_base)
for tool in kb_tools:
    toolkit.register_tool(tool)

# Create the agent
agent = ToolCapableAgent(
    worker_id="research_assistant",
    specialization="Research and Information Gathering",
    toolkit=toolkit,
    system_prompt_file="prompts/research_agent.txt"
)

# Grant permissions
toolkit.grant_permission("research_assistant", "search_web")
toolkit.grant_permission("research_assistant", "knowledge_search")
```

### Using the Agent with Structured Messages

```python
from atlas.agents.messaging.message import StructuredMessage

# Create a message
message = StructuredMessage(
    content="Research the latest developments in quantum computing",
    metadata={"type": "query", "priority": "high"}
)
message.source_agent = "user"
message.target_agent = "research_assistant"

# Process the message
response = agent.process_structured_message(message)

# Check for tool results
if response.has_tool_results:
    for result in response.tool_results:
        print(f"Tool: {result['name']}")
        print(f"Result: {result['result']}")
```

### Using the Agent with Tasks

```python
# Create a task
task = {
    "task_id": "research-task-123",
    "query": "Research the latest developments in quantum computing",
    "tool_calls": [
        {
            "name": "knowledge_search",
            "arguments": {
                "query": "quantum computing latest developments",
                "max_results": 5
            }
        }
    ]
}

# Process the task
result = agent.process_task(task)

# Handle the result
print(f"Status: {result['status']}")
print(f"Content: {result['result']}")
if "tool_results" in result:
    for tool_result in result["tool_results"]:
        print(f"Tool: {tool_result['name']}")
        print(f"Result: {tool_result['result']}")
```

### Agent Capabilities

Tool-capable agents can advertise their capabilities:

```python
# Register capabilities
agent.register_capability("Web search and information retrieval")
agent.register_capability("Document analysis and summarization")

# Get capabilities
capabilities = agent.get_capabilities()
print(f"Agent capabilities: {capabilities}")
```

Capabilities include:
- Explicitly registered capabilities
- Tool-based capabilities (derived from available tools)
- Specialization-based capabilities

## Knowledge-Focused Agents

Future specialized agents will include knowledge-focused agents designed specifically for knowledge base operations.

Planned features:
- Advanced document processing
- Enhanced metadata management
- Specialized chunking strategies
- Document linking and relationship management
- Knowledge graph integration

## Research-Focused Agents

Future specialized agents will include research-focused agents designed for information gathering and analysis.

Planned features:
- Web search capabilities
- Source validation and credibility assessment
- Information synthesis across sources
- Citation management
- Structured research reporting

## Implementation Details

### System Prompt Enhancement

When a tool-capable agent is initialized, it automatically enhances its system prompt with tool descriptions:

```python
def _add_tool_instructions_to_prompt(self) -> None:
    """Add tool usage instructions to the system prompt."""
    # Get tool descriptions the agent has access to
    tool_descriptions = self.toolkit.get_tool_descriptions(self.worker_id)
    
    if not tool_descriptions:
        # No tools available, no need to modify prompt
        return
        
    # Format tool schemas for the prompt
    tool_schemas_str = json.dumps(tool_descriptions, indent=2)
    
    # Create tool instructions
    tool_instructions = f"""
## Available Tools

You have access to the following tools:

{tool_schemas_str}

To use a tool, include a tool call in your response with the following format:
```json
{{
  "tool_calls": [
    {{
      "name": "tool_name",
      "arguments": {{
        "arg1": "value1",
        "arg2": "value2"
      }}
    }}
  ]
}}
```

Multiple tool calls can be included in a single response. Include your reasoning before and after the tool call.
"""
    
    # Add to system prompt
    self.system_prompt = self.system_prompt + tool_instructions
```

This ensures the language model is aware of available tools and knows how to format tool calls.

### Tool Call Extraction

The agent extracts tool calls from model responses:

```python
def _extract_tool_calls_from_content(self, content: str) -> List[Dict[str, Any]]:
    """Extract tool calls from response content."""
    # Look for tool call JSON blocks in the content
    tool_calls = []
    
    # Simple JSON block extraction (could be enhanced with regex)
    start_marker = '```json'
    end_marker = '```'
    
    # Find all JSON blocks
    start_pos = 0
    while True:
        # Find the next JSON block
        start_idx = content.find(start_marker, start_pos)
        if start_idx == -1:
            break
            
        # Find the end of the block
        start_json = start_idx + len(start_marker)
        end_idx = content.find(end_marker, start_json)
        if end_idx == -1:
            break
            
        # Extract the JSON content
        json_text = content[start_json:end_idx].strip()
        
        try:
            # Parse the JSON
            json_obj = json.loads(json_text)
            
            # Extract tool calls if present
            if "tool_calls" in json_obj:
                tool_calls.extend(json_obj["tool_calls"])
        except json.JSONDecodeError as e:
            # Log error but continue processing
            logger.warning(f"Failed to parse JSON block: {str(e)}")
        
        # Move to the next position
        start_pos = end_idx + len(end_marker)
    
    return tool_calls
```

## Best Practices

1. **Provide clear tool descriptions**: Ensure tools have descriptive names and clear documentation.

2. **Use appropriate permissions**: Only grant access to tools an agent actually needs.

3. **Handle tool errors gracefully**: Implement proper error handling for tool execution failures.

4. **Use structured messages**: For complex interactions, use the structured message format.

5. **Maintain appropriate specialization**: Keep agents focused on specific domains.

6. **Register meaningful capabilities**: Add capabilities that accurately reflect agent abilities.

7. **Design for composability**: Create agents that can work together in multi-agent systems.

## Future Enhancements

Planned enhancements for specialized agents include:

1. **Dynamic tool discovery**: Agents will be able to discover and learn to use new tools.

2. **Context-aware tool selection**: Intelligent tool selection based on context and task.

3. **Tool composition**: Combining tools into more complex workflows.

4. **Tool learning**: Agents will improve their tool usage through feedback.

5. **MCP Integration**: Support for Model Context Protocol (MCP) tools.