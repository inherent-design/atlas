#!/usr/bin/env python3
"""
Tool Agent Example (20_tool_agent.py)

This example demonstrates how to use the Atlas tool agent framework:
1. Creating a tool agent with the provider options system
2. Defining and registering custom tools
3. Handling tool execution and results
4. Managing context between tool invocations

The example shows how to create specialized tools that extend the capabilities
of language models, allowing them to perform calculations, search for information,
and interact with external systems.
"""

import sys
import os
import json
import math
from typing import Dict, Any, List, Optional, Union

# Import common utilities for Atlas examples
from common import (
    setup_example,
    create_provider_from_args,
    print_example_header,
    print_example_footer,
    handle_example_error
)
from atlas.core import logging

# Import atlas modules
from atlas.providers.options import ProviderOptions
from atlas.providers.resolver import resolve_provider_options
from atlas.agents.specialized.tool_agent import create_tool_agent, ToolCapableAgent
from atlas.tools.base import Tool, ToolSchema, AgentToolkit


# Example calculator tool
class Calculator(Tool):
    """Simple calculator tool for basic arithmetic operations."""

    def __init__(self):
        """Initialize the calculator tool."""
        super().__init__(name="calculator")
    
    @property
    def schema(self) -> ToolSchema:
        """Get the schema for this tool.
        
        Returns:
            A ToolSchema describing the tool's inputs and outputs.
        """
        return ToolSchema(
            name=self.name,
            description="Performs basic arithmetic calculations. Supports +, -, *, /, ^, sqrt, sin, cos, tan.",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        )
    
    def execute(self, expression: str) -> str:
        """Execute the calculator tool.
        
        Args:
            expression: The mathematical expression to evaluate.
            
        Returns:
            The result of the calculation as a string.
        """
        try:
            # Create a safe math environment
            safe_math = {
                "abs": abs,
                "max": max,
                "min": min,
                "pow": pow,
                "round": round,
                "sum": sum,
                # Add common math functions
                "sqrt": math.sqrt,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "pi": math.pi,
                "e": math.e,
                # Convert operations to be explicit function calls
                "+": lambda x, y: x + y,
                "-": lambda x, y: x - y,
                "*": lambda x, y: x * y,
                "/": lambda x, y: x / y,
                "^": lambda x, y: x ** y,
            }
            
            # WARNING: In real code, use a safer approach than eval
            # This is just for demonstration purposes
            # Replace operators with safer function calls
            expression = expression.replace("^", "**")
            result = eval(expression, {"__builtins__": {}}, safe_math)
            
            return f"Result: {result}"
        except Exception as e:
            return f"Error calculating: {e}"


# Example weather tool
class WeatherTool(Tool):
    """Tool for getting weather information."""

    def __init__(self):
        """Initialize the weather tool."""
        super().__init__(name="weather")
    
    @property
    def schema(self) -> ToolSchema:
        """Get the schema for this tool.
        
        Returns:
            A ToolSchema describing the tool's inputs and outputs.
        """
        return ToolSchema(
            name=self.name,
            description="Gets current weather information for a location.",
            parameters={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The location to get weather for (city name)"
                    }
                },
                "required": ["location"]
            }
        )
    
    def execute(self, location: str) -> str:
        """Execute the weather tool.
        
        Args:
            location: The location to get weather for.
            
        Returns:
            Weather information for the location.
        """
        # This is a mock implementation for demonstration purposes
        mock_weather = {
            "new york": {"temp": 72, "condition": "Partly Cloudy", "humidity": 65},
            "los angeles": {"temp": 85, "condition": "Sunny", "humidity": 40},
            "chicago": {"temp": 65, "condition": "Windy", "humidity": 55},
            "miami": {"temp": 90, "condition": "Humid", "humidity": 80},
            "seattle": {"temp": 60, "condition": "Rainy", "humidity": 75},
        }
        
        location_lower = location.lower()
        if location_lower in mock_weather:
            weather = mock_weather[location_lower]
            return f"Weather for {location}: {weather['temp']}°F, {weather['condition']}, Humidity: {weather['humidity']}%"
        else:
            return f"Weather information not available for {location}"


def add_example_arguments(parser):
    """Add example-specific arguments to the parser."""
    parser.add_argument(
        "--query",
        type=str,
        help="Specific query to use instead of example queries"
    )
    
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Enable streaming output"
    )


def main():
    """Run the tool agent example."""
    # Set up the example with standardized logging and argument parsing
    args = setup_example("Atlas Tool Agent Example", add_example_arguments)
    logger = logging.get_logger(__name__)
    
    # Print example header
    print_example_header("Tool Agent Example")

    try:
        # Create provider from command line arguments
        provider = create_provider_from_args(args)
        logger.info(f"Created provider: {provider.name} with model {provider.model_name}")

        # Define worker ID for this agent
        worker_id = "tool_worker"
        
        # Create instance of tools
        tools = [Calculator(), WeatherTool()]
        
        # Two alternative approaches for creating a tool agent:
        
        # Method 1: Pre-configure toolkit and pass it to create_tool_agent
        # This approach gives more control over registration and permissions
        toolkit = AgentToolkit()
        
        # Register tools in toolkit with proper validation
        for tool in tools:
            # Validate the tool schema before registration
            from atlas.schemas.tools import validate_tool_schema
            try:
                # Validate the tool schema
                validate_tool_schema(tool.schema.to_dict())
                logger.info(f"Tool schema for {tool.name} is valid")
                
                # Register the tool
                toolkit.register_tool(tool)
                logger.info(f"Successfully registered tool: {tool.name}")
            except Exception as e:
                logger.error(f"Failed to validate or register tool {tool.name}: {e}")
                raise
        
        # Grant permissions with detailed tracking
        try:
            # 1. Grant calculator tool permission with admin as granter and execute scope
            toolkit.grant_permission(
                agent_id=worker_id, 
                tool_name="calculator",
                granted_by="admin",
                scope="execute"
            )
            logger.info(f"Granted 'execute' permission for 'calculator' tool to agent '{worker_id}'")
            
            # 2. Grant weather tool permission with system as granter and execute scope
            toolkit.grant_permission(
                agent_id=worker_id, 
                tool_name="weather",
                granted_by="system",
                scope="execute"
            )
            logger.info(f"Granted 'execute' permission for 'weather' tool to agent '{worker_id}'")
            
            # 3. Grant additional permission with read scope (demonstration only)
            toolkit.grant_permission(
                agent_id=worker_id, 
                tool_name="calculator",
                granted_by="system",
                scope="read"
            )
            logger.info(f"Granted 'read' permission for 'calculator' tool to agent '{worker_id}'")
        except Exception as e:
            logger.error(f"Failed to grant tool permissions: {e}")
            raise
        
        # Create agent with pre-configured toolkit
        tool_agent = create_tool_agent(
            worker_id=worker_id,
            specialization="Tool Execution and Augmented Reasoning",
            provider=provider,
            toolkit=toolkit
        )
        
        # Method 2 (alternative, not used here):
        # Let create_tool_agent handle registration
        # This would automatically register tools and grant permissions
        #
        # tool_agent = create_tool_agent(
        #     worker_id=worker_id,
        #     specialization="Tool Execution and Augmented Reasoning",
        #     provider=provider,
        #     tools=tools  # Pass tools directly instead of toolkit
        # )
        
        # Display registered tools
        accessible_tools = tool_agent.toolkit.get_accessible_tools(worker_id)
        if not accessible_tools:
            print("\n🧰 No tools registered or accessible.")
        else:
            accessible_tool_names = list(accessible_tools.keys())
            print(f"\n🧰 Accessible Tools: {', '.join(accessible_tool_names)}")
            
        # Print permission information for clarity
        permissions = tool_agent.toolkit.permissions.get(worker_id, set())
        print(f"🔑 Tool Permissions for {worker_id}: {permissions}")
        
        # Get and display detailed permission history with improved formatting
        permission_history = tool_agent.toolkit.get_permission_history(worker_id)
        print("\n📋 Permission History:")
        
        # Sort permissions by tool name and scope for clarity
        sorted_history = sorted(
            permission_history, 
            key=lambda x: (x.get("tool_name", ""), x.get("scope", ""))
        )
        
        # Format timestamp to readable format
        import datetime
        for record in sorted_history:
            granted_time = record.get("granted_at")
            tool = record.get("tool_name")
            granted_by = record.get("granted_by", "unknown")
            scope = record.get("scope")
            
            # Convert timestamp to human-readable format
            timestamp = datetime.datetime.fromtimestamp(granted_time).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"  - {tool}: granted by {granted_by} with scope '{scope}' at {timestamp}")
        
        # Demonstrate scope-based permissions
        print("\n🔍 Permission Scopes Verification:")
        # Check for calculator permissions with different scopes
        print(f"  - has execute permission for calculator: {toolkit.has_permission(worker_id, 'calculator', 'execute')}")
        print(f"  - has read permission for calculator: {toolkit.has_permission(worker_id, 'calculator', 'read')}")
        print(f"  - has manage permission for calculator: {toolkit.has_permission(worker_id, 'calculator', 'manage')}")
        
        # Check for weather permissions with different scopes
        print(f"  - has execute permission for weather: {toolkit.has_permission(worker_id, 'weather', 'execute')}")
        print(f"  - has read permission for weather: {toolkit.has_permission(worker_id, 'weather', 'read')}")
        
        # Get accessible tools for the agent based on execute permission
        accessible_tools = toolkit.get_accessible_tools(worker_id, scope="execute")
        print(f"\n🛠️ Tools accessible with 'execute' scope: {', '.join(accessible_tools.keys())}")
        
        # Get accessible tools for the agent based on read permission
        readable_tools = toolkit.get_accessible_tools(worker_id, scope="read")
        print(f"📖 Tools accessible with 'read' scope: {', '.join(readable_tools.keys()) if readable_tools else 'None'}")
        
        # Example queries for the tool agent
        queries = [
            "What is 234 * 456 + 789?",
            "What's the square root of 144 plus the cosine of 0 radians?",
            "What's the weather like in Miami today?",
            "Can you tell me the current temperature in Seattle and then calculate 75/3?"
        ]

        # Use provided query if available, otherwise use examples
        query_index = 0
        if args.query:
            query = args.query
        else:
            # Choose a different query each time
            query = queries[query_index % len(queries)]
        
        print(f"\n🔎 Query: \"{query}\"")
        print("\nProcessing query with tool agent...")

        # Execute the query with tools
        response = tool_agent.run_with_tools(query)
        
        print(f"\n📝 Response:\n{response}")

        # Run a second query to demonstrate tool reuse
        if not args.query:
            query_index = 1
            query2 = queries[query_index % len(queries)]
            
            print(f"\n🔎 Follow-up Query: \"{query2}\"")
            print("\nProcessing follow-up query with tool agent...")
            
            response2 = tool_agent.run_with_tools(query2)
            
            print(f"\n📝 Response:\n{response2}")

    except Exception as e:
        handle_example_error(logger, e, "Error running tool agent")

    # Print footer
    print_example_footer()


if __name__ == "__main__":
    main()