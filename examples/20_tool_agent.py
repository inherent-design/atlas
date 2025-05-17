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
        # Create provider directly to avoid model_name setter issue
        from atlas.providers.implementations.mock import MockProvider
        
        # Use mock provider for testing
        provider = MockProvider(model_name="mock-standard")
        logger.info(f"Created provider: {provider.name} with model {provider.model_name}")

        # Create tool agent directly with the provider
        tools = [Calculator(), WeatherTool()]
        toolkit = AgentToolkit()
        
        # Register tools in the toolkit
        for tool in tools:
            toolkit.register_tool(tool)
            
        # Create tool agent with the provider directly
        tool_agent = ToolCapableAgent(
            worker_id="tool_worker",
            specialization="Tool Execution and Augmented Reasoning",
            toolkit=toolkit,
            provider=provider
        )
        
        # Display registered tools
        tools = tool_agent.toolkit.get_accessible_tools(tool_agent.worker_id)
        if not tools:
            print("\n🧰 No tools registered or accessible.")
        else:
            tool_names = list(tools.keys())
            print(f"\n🧰 Registered Tools: {', '.join(tool_names)}")
            
        # Print all tools from the toolkit as an alternative
        all_tools = [tool.name for tool in toolkit.tools if hasattr(tool, 'name')]
        if all_tools:
            print(f"💼 Available Tools: {', '.join(all_tools)}")

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
        response = tool_agent.process_message(query, capabilities={"tool_use": True})
        
        print(f"\n📝 Response:\n{response}")

        # Run a second query to demonstrate tool reuse
        if not args.query:
            query_index = 1
            query2 = queries[query_index % len(queries)]
            
            print(f"\n🔎 Follow-up Query: \"{query2}\"")
            print("\nProcessing follow-up query with tool agent...")
            
            response2 = tool_agent.process_message(query2, capabilities={"tool_use": True})
            
            print(f"\n📝 Response:\n{response2}")

    except Exception as e:
        handle_example_error(logger, e, "Error running tool agent")

    # Print footer
    print_example_footer()


if __name__ == "__main__":
    main()