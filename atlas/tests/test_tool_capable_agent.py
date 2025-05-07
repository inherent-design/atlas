"""
Test the ToolCapableAgent class.
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
import json

from atlas.agents.specialized.tool_agent import ToolCapableAgent
from atlas.agents.messaging.message import StructuredMessage
from atlas.tools.base import Tool, ToolSchema, AgentToolkit


# Simple test tools
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

def get_weather(location: str) -> str:
    """Get weather for a location (mock implementation)."""
    return f"The weather in {location} is sunny and 22°C."


class TestToolCapableAgent(unittest.TestCase):
    """Test cases for the ToolCapableAgent class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Patch provider initialization to avoid API calls
        self.mock_provider = Mock()
        self.mock_provider.name = "mock_provider"
        self.mock_provider.model_name = "mock_model"
        
        # Create a patcher for the provider
        self.provider_patcher = patch(
            'atlas.agents.base.create_provider',
            return_value=self.mock_provider
        )
        self.provider_patcher.start()
        
        # Patch knowledge base to avoid DB operations
        self.kb_patcher = patch('atlas.agents.base.KnowledgeBase')
        self.kb_patcher.start()
        
        # Create a toolkit with test tools
        self.toolkit = AgentToolkit()
        self.toolkit.register_tool(add_numbers)
        self.toolkit.register_tool(get_weather)
        
        # Create the agent
        self.agent = ToolCapableAgent(
            worker_id="test_agent",
            specialization="Testing",
            toolkit=self.toolkit
        )
        
        # Grant tool permissions
        self.toolkit.grant_permission("test_agent", "add_numbers")
        self.toolkit.grant_permission("test_agent", "get_weather")
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.provider_patcher.stop()
        self.kb_patcher.stop()
    
    def test_initialization(self):
        """Test that agent initializes correctly with toolkit."""
        # Check agent has toolkit
        self.assertIsInstance(self.agent.toolkit, AgentToolkit)
        
        # Check system prompt includes tool instructions
        self.assertIn("Available Tools", self.agent.system_prompt)
        self.assertIn("add_numbers", self.agent.system_prompt)
        self.assertIn("get_weather", self.agent.system_prompt)
    
    def test_register_capability(self):
        """Test registering agent capabilities."""
        # Register capabilities
        self.agent.register_capability("Math operations")
        self.agent.register_capability("Weather information")
        
        # Check capabilities were registered
        capabilities = self.agent.get_capabilities()
        self.assertIn("Math operations", capabilities)
        self.assertIn("Weather information", capabilities)
        
        # Check tool capabilities are included
        self.assertTrue(any("Can use tools:" in cap for cap in capabilities))
    
    def test_register_tool(self):
        """Test registering a new tool with the agent."""
        # Define a simple test tool
        def multiply(x: int, y: int) -> int:
            """Multiply two numbers."""
            return x * y
            
        # Register the tool
        tool_name = self.agent.register_tool(multiply)
        
        # Check tool was registered and permission granted
        self.assertEqual(tool_name, "multiply")
        self.assertTrue(self.agent.toolkit.has_permission("test_agent", "multiply"))
        
        # Check system prompt was updated
        self.assertIn("multiply", self.agent.system_prompt)
    
    def test_process_task_without_tools(self):
        """Test processing a basic task without tool calls."""
        # Mock the process_message method
        self.agent.process_message = Mock(return_value="Processed response")
        
        # Create a basic task
        task = {
            "task_id": "task123",
            "query": "Simple test query"
        }
        
        # Process the task
        result = self.agent.process_task(task)
        
        # Check result
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["result"], "Processed response")
        self.assertEqual(result["worker_id"], "test_agent")
        self.assertEqual(result["task_id"], "task123")
    
    def test_process_task_with_tools(self):
        """Test processing a task with tool calls."""
        # Create a task with tool calls
        task = {
            "task_id": "tool_task",
            "tool_calls": [
                {
                    "id": "call1",
                    "name": "add_numbers",
                    "arguments": {"a": 5, "b": 7}
                },
                {
                    "id": "call2",
                    "name": "get_weather",
                    "arguments": {"location": "London"}
                }
            ]
        }
        
        # Process the task
        result = self.agent.process_task(task)
        
        # Check result
        self.assertEqual(result["status"], "completed")
        self.assertEqual(len(result["tool_results"]), 2)
        
        # Check first tool result
        add_result = next(r for r in result["tool_results"] if r["name"] == "add_numbers")
        self.assertEqual(add_result["result"], 12)
        self.assertEqual(add_result["status"], "success")
        
        # Check second tool result
        weather_result = next(r for r in result["tool_results"] if r["name"] == "get_weather")
        self.assertEqual(weather_result["result"], "The weather in London is sunny and 22°C.")
        self.assertEqual(weather_result["status"], "success")
    
    def test_process_structured_message(self):
        """Test processing a structured message."""
        # Create a structured message
        message = StructuredMessage(
            content="Test message",
            task_id="test123",
        )
        message.source_agent = "controller"
        message.target_agent = "test_agent"
        
        # Mock process_message to return content with a tool call
        self.agent.process_message = Mock(return_value="""
        I'll help you with that calculation.
        
        ```json
        {
          "tool_calls": [
            {
              "id": "call1",
              "name": "add_numbers",
              "arguments": {
                "a": 10,
                "b": 20
              }
            }
          ]
        }
        ```
        
        After performing the calculation, the result is shown above.
        """)
        
        # Process the message
        response = self.agent.process_structured_message(message)
        
        # Check response
        self.assertEqual(response.source_agent, "test_agent")
        self.assertEqual(response.target_agent, "controller")
        self.assertEqual(response.message_type, "response")
        self.assertEqual(response.metadata["in_reply_to"], "test123")
        self.assertTrue(response.has_tool_results)
        
        # Check tool result
        self.assertEqual(len(response.tool_results), 1)
        self.assertEqual(response.tool_results[0]["name"], "add_numbers")
        self.assertEqual(response.tool_results[0]["result"], 30)
        self.assertEqual(response.tool_results[0]["status"], "success")
    
    def test_extract_tool_calls(self):
        """Test extracting tool calls from content."""
        # Content with tool calls
        content = """
        I need to perform two operations:
        
        First, add some numbers:
        ```json
        {
          "tool_calls": [
            {
              "name": "add_numbers",
              "arguments": {
                "a": 5,
                "b": 10
              }
            }
          ]
        }
        ```
        
        Then I'll check the weather:
        ```json
        {
          "tool_calls": [
            {
              "name": "get_weather",
              "arguments": {
                "location": "New York"
              }
            }
          ]
        }
        ```
        
        These operations will give us the information we need.
        """
        
        # Extract tool calls
        tool_calls = self.agent._extract_tool_calls_from_content(content)
        
        # Check extraction
        self.assertEqual(len(tool_calls), 2)
        
        # Check first tool call
        self.assertEqual(tool_calls[0]["name"], "add_numbers")
        self.assertEqual(tool_calls[0]["arguments"]["a"], 5)
        self.assertEqual(tool_calls[0]["arguments"]["b"], 10)
        
        # Check second tool call
        self.assertEqual(tool_calls[1]["name"], "get_weather")
        self.assertEqual(tool_calls[1]["arguments"]["location"], "New York")
    
    def test_error_handling_in_tool_execution(self):
        """Test error handling during tool execution."""
        # Create a task with an invalid tool call
        task = {
            "task_id": "error_task",
            "tool_calls": [
                {
                    "id": "call1",
                    "name": "add_numbers",
                    "arguments": {"a": 5}  # Missing required argument 'b'
                }
            ]
        }
        
        # Process the task
        result = self.agent.process_task(task)
        
        # Check result contains error information
        self.assertEqual(result["status"], "completed")
        self.assertEqual(len(result["tool_results"]), 1)
        
        tool_result = result["tool_results"][0]
        self.assertEqual(tool_result["status"], "error")
        self.assertIsNone(tool_result["result"])
        self.assertIn("Invalid arguments", tool_result["error"])


if __name__ == "__main__":
    unittest.main()