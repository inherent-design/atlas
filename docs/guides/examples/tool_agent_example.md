# Tool-Capable Agent Example

This guide demonstrates how to use tool-capable agents with the structured messaging system. We'll build an agent that can use various tools to answer questions and perform tasks.

## Overview

In this example, you'll learn how to:

1. Create and register tools in the `AgentToolkit`
2. Initialize a `ToolCapableAgent` with access to tools
3. Use structured messages for communication
4. Process tool calls and results
5. Build a simple interactive agent session

## Prerequisites

- An API key for a supported model provider (Anthropic Claude recommended)
- Basic understanding of the Atlas agent architecture
- Knowledge of the tool system and structured messages

## Example Structure

The example consists of these main components:

1. **Tool Definitions**: Simple tools for the agent to use
2. **Toolkit Setup**: Creating and configuring the toolkit
3. **Agent Creation**: Initializing a tool-capable agent
4. **Query Processing**: Handling queries with tool capabilities
5. **Interactive Mode**: Optional interactive session

## Step 1: Define Tools

Let's start by defining some simple tools:

```python
# Define some simple tools
def calculate_area(length: float, width: float) -> float:
    """Calculate the area of a rectangle."""
    return length * width

def list_countries_by_continent(continent: str) -> List[str]:
    """Return a list of countries in a given continent."""
    countries = {
        "africa": ["Egypt", "Nigeria", "South Africa", "Ethiopia", "Kenya"],
        "asia": ["China", "India", "Japan", "Thailand", "Vietnam"],
        "europe": ["Germany", "France", "Spain", "Italy", "UK"],
        "north america": ["USA", "Canada", "Mexico", "Cuba", "Guatemala"],
        "south america": ["Brazil", "Argentina", "Chile", "Peru", "Colombia"],
        "oceania": ["Australia", "New Zealand", "Fiji", "Papua New Guinea", "Samoa"]
    }
    return countries.get(continent.lower(), [])
```

We can also define a custom tool class:

```python
class TimeConverterTool(Tool):
    """Tool for converting between time zones."""
    
    @property
    def schema(self) -> ToolSchema:
        """Get the schema for this tool."""
        return ToolSchema(
            name=self.name,
            description="Convert a time from one timezone to another",
            parameters={
                "type": "object",
                "properties": {
                    "time": {
                        "type": "string",
                        "description": "Time in format HH:MM"
                    },
                    "from_timezone": {
                        "type": "string",
                        "description": "Source timezone (e.g., 'UTC', 'America/New_York')"
                    },
                    "to_timezone": {
                        "type": "string",
                        "description": "Target timezone (e.g., 'UTC', 'America/Los_Angeles')"
                    }
                },
                "required": ["time", "from_timezone", "to_timezone"]
            }
        )
    
    def execute(self, time: str, from_timezone: str, to_timezone: str) -> str:
        """Convert time between timezones (simplified implementation)."""
        # Implementation details...
```

## Step 2: Set Up the Toolkit

Next, we'll create and configure the toolkit:

```python
# Initialize a toolkit
toolkit = AgentToolkit()

# Register function-based tools
toolkit.register_tool(calculate_area)
toolkit.register_tool(list_countries_by_continent)

# Register custom tool
toolkit.register_tool(TimeConverterTool())

# Optionally register knowledge tools
if args.knowledge_base:
    # Initialize knowledge base
    kb = KnowledgeBase(collection_name=args.knowledge_base)
    # Create knowledge search tool
    toolkit.register_tool(KnowledgeSearchTool(kb))
```

## Step 3: Create a Tool-Capable Agent

Now we can create an agent that can use these tools:

```python
# Create a tool-capable agent
agent = ToolCapableAgent(
    worker_id="assistant",
    specialization="Research and Problem Solving",
    toolkit=toolkit
)

# Grant permissions for all tools
toolkit.grant_all_permissions("assistant")

# Register capabilities
agent.register_capability("Mathematical calculations")
agent.register_capability("Geographic information")
agent.register_capability("Time conversion")
if kb:
    agent.register_capability("Knowledge base search")
```

## Step 4: Process Queries with Tools

We can now process queries that might require tools:

```python
def process_query(agent: ToolCapableAgent, query: str) -> None:
    """Process a single query with the agent."""
    # Create a structured message
    message = StructuredMessage(
        content=query,
        metadata={"type": MessageType.QUERY}
    )
    message.source_agent = "user"
    message.target_agent = "assistant"
    
    # Process the message
    logger.info(f"Processing query: {query}")
    response = agent.process_structured_message(message)
    
    # Display the response
    print("\n=== Agent Response ===")
    print(response.content)
    
    # Display any tool results
    if response.has_tool_results:
        print("\n=== Tool Results ===")
        for result in response.tool_results:
            print(f"\nTool: {result['name']}")
            print(f"Status: {result['status']}")
            if result['status'] == "error":
                print(f"Error: {result['error']}")
            else:
                print(f"Result: {json.dumps(result['result'], indent=2)}")
```

## Step 5: Interactive Mode

The example also includes an interactive mode:

```python
def run_interactive_mode(agent: ToolCapableAgent) -> None:
    """Run an interactive session with the agent."""
    print("\n=== Interactive Tool Agent Session ===")
    print("Type 'exit' or 'quit' to end the session")
    print("Available tools:")
    for name, tool in agent.toolkit.tools.items():
        print(f"- {name}: {tool.description}")
    print("\n")
    
    while True:
        # Get user input
        query = input("You: ")
        if query.lower() in ["exit", "quit", "bye"]:
            print("Ending session.")
            break
            
        # Process the query
        process_query(agent, query)
```

## Running the Example

You can run the example with:

```bash
# Run with a default query
python examples/tool_agent_example.py

# Run in interactive mode
python examples/tool_agent_example.py --interactive

# Run with a specific query
python examples/tool_agent_example.py --query "What is the area of a rectangle with length 10 and width 7?"

# Run with a knowledge base
python examples/tool_agent_example.py --knowledge_base atlas_knowledge_base
```

## Example Queries

Try these example queries to see the tools in action:

- "What is the area of a rectangle with length 5.2 and width 3.7?"
- "List the countries in Europe."
- "Convert 14:30 from UTC to America/New_York."
- "What time is it in Tokyo when it's 9:00 in London?"
- "What's the area of a square with sides of 4 units?" (Can use calculate_area)

## How It Works

When the agent receives a query that requires a tool:

1. The agent processes the query with its language model
2. The language model recognizes that a tool could help and includes a tool call
3. The agent extracts the tool call from the response
4. The agent executes the tool with the provided arguments
5. The agent incorporates the tool result into its response
6. The agent returns a structured message with both content and tool results

## Complete Example

The complete example is available at `examples/tool_agent_example.py` in the Atlas repository.

## Next Steps

After exploring this example, you might want to:

1. Create your own custom tools
2. Build a multi-agent system with specialized tool-capable agents
3. Add more complex tool workflows
4. Implement a web interface for your tool-capable agent
5. Explore the MCP integration for external tools