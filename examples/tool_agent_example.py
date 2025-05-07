#!/usr/bin/env python3
"""
Example of using tool-capable agents and the messaging system.

This example demonstrates how to create and use tool-capable agents with
the structured messaging system and the agent toolkit.
"""

import os
import argparse
import logging
import json
from typing import List, Dict, Any, Optional

from atlas.agents.specialized.tool_agent import ToolCapableAgent
from atlas.agents.messaging.message import StructuredMessage, MessageType
from atlas.tools.base import AgentToolkit, Tool, ToolSchema
from atlas.tools.standard.knowledge_tools import KnowledgeSearchTool
from atlas.knowledge.retrieval import KnowledgeBase


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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


# Define a custom tool class
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
        # This is a mock implementation for demonstration purposes
        # A real implementation would use pytz or datetime with timezone support
        
        # Parse time (assuming HH:MM format)
        hour, minute = map(int, time.split(':'))
        
        # Simplified timezone offsets (just for demo)
        timezone_offsets = {
            "UTC": 0,
            "America/New_York": -4,  # EDT
            "America/Chicago": -5,   # CDT
            "America/Denver": -6,    # MDT
            "America/Los_Angeles": -7,  # PDT
            "Europe/London": 1,      # BST
            "Europe/Paris": 2,       # CEST
            "Asia/Tokyo": 9,         # JST
            "Australia/Sydney": 10   # AEST
        }
        
        # Calculate time difference
        from_offset = timezone_offsets.get(from_timezone, 0)
        to_offset = timezone_offsets.get(to_timezone, 0)
        difference = to_offset - from_offset
        
        # Apply difference
        new_hour = (hour + difference) % 24
        
        # Format result
        return f"{new_hour:02d}:{minute:02d}"


def run_example(args: argparse.Namespace) -> None:
    """Run the tool agent example."""
    # Initialize a toolkit
    toolkit = AgentToolkit()
    
    # Register function-based tools
    toolkit.register_tool(calculate_area)
    toolkit.register_tool(list_countries_by_continent)
    
    # Register custom tool
    toolkit.register_tool(TimeConverterTool())
    
    # Register knowledge tool if a knowledge base is specified
    kb = None
    if args.knowledge_base:
        # Initialize knowledge base
        kb = KnowledgeBase(collection_name=args.knowledge_base)
        # Create knowledge search tool
        toolkit.register_tool(KnowledgeSearchTool(kb))
    
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
    
    # Display agent information
    logger.info(f"Agent created with {len(toolkit.tools)} tools available")
    logger.info(f"Agent capabilities: {agent.get_capabilities()}")
    
    # Interactive mode or single query
    if args.interactive:
        run_interactive_mode(agent)
    else:
        # Process the query
        process_query(agent, args.query)


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


def main():
    """Main entry point for the example."""
    parser = argparse.ArgumentParser(description="Tool Agent Example")
    parser.add_argument(
        "-q", "--query", type=str,
        help="Query to process",
        default="What is the area of a rectangle with length 5 and width 3?"
    )
    parser.add_argument(
        "-i", "--interactive", action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "-k", "--knowledge_base", type=str,
        help="Knowledge base collection name",
        default=""
    )
    
    args = parser.parse_args()
    
    # Check for API key if not in demo mode
    demo_mode = os.environ.get("SKIP_API_KEY_CHECK", "").lower() in ["true", "1", "yes"]
    if not demo_mode and not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        print("Please set the API key or run with SKIP_API_KEY_CHECK=true for demo mode.")
        return
        
    try:
        run_example(args)
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        logger.error(f"Error running example: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()