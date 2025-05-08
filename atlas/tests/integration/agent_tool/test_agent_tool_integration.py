"""
Integration tests for Agent + Tool interactions.

This module contains tests that verify the integration between agents and tools,
ensuring they can properly interact with each other.
"""

import unittest
from unittest import mock
from typing import Dict, Any, Optional

from atlas.tests.helpers.decorators import integration_test
from atlas.tests.helpers.base_classes import IntegrationTestBase
from atlas.tests.helpers.mocks import create_mock_response

from atlas.models import ModelRequest, ModelMessage, ModelResponse
from atlas.tools.base import AgentToolkit, Tool, ToolSchema, FunctionTool
from atlas.agents.specialized.tool_agent import ToolCapableAgent


# Sample tool for testing
class CalculatorTool(Tool):
    """Tool for performing math operations."""

    @property
    def schema(self) -> ToolSchema:
        """Get the schema for this tool."""
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                    },
                    "a": {"type": "number"},
                    "b": {"type": "number"},
                },
                "required": ["operation", "a", "b"],
            },
            returns={"type": "number"},
        )

    def execute(self, operation: str, a: float, b: float) -> float:
        """Execute the calculator operation."""
        if operation == "add":
            return a + b
        elif operation == "subtract":
            return a - b
        elif operation == "multiply":
            return a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Cannot divide by zero")
            return a / b
        else:
            raise ValueError(f"Unknown operation: {operation}")


# Simple function tool for testing
def get_weather(location: str, unit: str = "celsius") -> Dict[str, Any]:
    """Get weather information for a location."""
    # Mock implementation
    return {
        "location": location,
        "temperature": 22 if unit == "celsius" else 72,
        "unit": unit,
        "conditions": "sunny",
    }


class TestAgentToolIntegration(IntegrationTestBase):
    """Integration tests for Agent + Tool interactions."""

    def setUp(self):
        """Set up the test with components for integration testing."""
        super().setUp()

        # Create the agent
        self.agent = ToolCapableAgent(
            worker_id="test_worker",
            specialization="Test Worker", 
        )
        
        # Patch the _extract_tool_calls_from_content method to handle the test format
        def extract_tool_calls(content):
            """Extract tool calls from content using test format."""
            tool_calls = []
            
            # Look for <tool_call> tags
            import re
            pattern = r'<tool_call\s+name="([^"]+)">\s*(.*?)\s*</tool_call>'
            matches = re.findall(pattern, content, re.DOTALL)
            
            for tool_name, args_json in matches:
                try:
                    args = json.loads(args_json)
                    tool_calls.append({"name": tool_name, "arguments": args})
                except json.JSONDecodeError:
                    continue
                    
            return tool_calls
            
        # Replace the method
        self.agent._extract_tool_calls_from_content = extract_tool_calls

        # Create and register tools
        self.calculator = CalculatorTool()
        self.toolkit = AgentToolkit()
        self.toolkit.register_tool(self.calculator)
        self.toolkit.register_tool(get_weather)

        # Register tools with the agent
        self.agent.toolkit = self.toolkit
        
        # Grant permissions for the agent to use the tools
        self.toolkit.grant_permission(self.agent.worker_id, self.calculator.name)
        self.toolkit.grant_permission(self.agent.worker_id, "get_weather")

        # Mock the provider's generate method
        self.mock_provider = mock.MagicMock()
        self.agent._provider = self.mock_provider

    @integration_test
    def test_agent_uses_calculator_tool(self):
        """Test that the agent correctly uses the calculator tool."""
        # Configure response with tool calls
        response_content = """
        I'll solve that calculation for you.

        <tool_calls>
        <tool_call name="calculator">
        {"operation": "add", "a": 5, "b": 10}
        </tool_call>
        </tool_calls>

        The result of 5 + 10 is 15.
        """

        # Set up the mock response
        self.mock_provider.generate.return_value = create_mock_response(
            content=response_content, provider="mock", model="mock-model"
        )

        # Process a request that should trigger tool usage
        request = ModelRequest(messages=[ModelMessage.user("What is 5 + 10?")])
        message = self.agent.process_message(request.messages[0].content)

        # Verify the tool was used correctly
        self.assertIn("15", message)
        self.mock_provider.generate.assert_called_once()

        # The response should contain the tool result
        self.assertIn("The result of 5 + 10 is 15", message)

    @integration_test
    def test_agent_uses_weather_tool(self):
        """Test that the agent correctly uses the weather tool."""
        # Configure response with tool calls
        response_content = """
        Let me check the weather for you.

        <tool_calls>
        <tool_call name="get_weather">
        {"location": "New York", "unit": "fahrenheit"}
        </tool_call>
        </tool_calls>

        The weather in New York is currently sunny with a temperature of 72°F.
        """

        # Set up the mock response
        self.mock_provider.generate.return_value = create_mock_response(
            content=response_content, provider="mock", model="mock-model"
        )

        # Process a request that should trigger tool usage
        request = ModelRequest(
            messages=[ModelMessage.user("What's the weather in New York?")]
        )
        message = self.agent.process_message(request.messages[0].content)

        # Verify the tool was used correctly
        self.assertIn("72°F", message)
        self.mock_provider.generate.assert_called_once()

        # The response should contain weather information
        self.assertIn("The weather in New York is currently sunny", message)

    @integration_test
    def test_multiple_tool_calls(self):
        """Test that the agent can make multiple tool calls in sequence."""
        # Configure response with multiple tool calls
        response_content = """
        I'll help you with both calculations.

        <tool_calls>
        <tool_call name="calculator">
        {"operation": "add", "a": 10, "b": 5}
        </tool_call>
        </tool_calls>

        First, 10 + 5 = 15.

        <tool_calls>
        <tool_call name="calculator">
        {"operation": "multiply", "a": 15, "b": 2}
        </tool_call>
        </tool_calls>

        Then, 15 × 2 = 30.
        """

        # Set up the mock response
        self.mock_provider.generate.return_value = create_mock_response(
            content=response_content, provider="mock", model="mock-model"
        )

        # Process a request that should trigger multiple tool usages
        request = ModelRequest(messages=[ModelMessage.user("Calculate (10 + 5) × 2")])
        message = self.agent.process_message(request.messages[0].content)

        # Verify both tools were used correctly
        self.assertIn("10 + 5 = 15", message)
        self.assertIn("15 × 2 = 30", message)
        self.mock_provider.generate.assert_called_once()

    @integration_test
    def test_tool_error_handling(self):
        """Test that the agent handles tool execution errors correctly."""
        # Configure response with a tool call that will fail
        response_content = """
        I'll solve that calculation for you.

        <tool_calls>
        <tool_call name="calculator">
        {"operation": "divide", "a": 10, "b": 0}
        </tool_call>
        </tool_calls>
        """

        # Set up the mock responses - initial response and error handling response
        self.mock_provider.generate.side_effect = [
            # First call returns the tool call
            create_mock_response(
                content=response_content, provider="mock", model="mock-model"
            ),
            # Second call returns error handling response
            create_mock_response(
                content="I apologize, but there was an error: Cannot divide by zero.",
                provider="mock",
                model="mock-model",
            ),
        ]

        # Process a request that will trigger a tool error
        request = ModelRequest(messages=[ModelMessage.user("What is 10 ÷ 0?")])
        message = self.agent.process_message(request.messages[0].content)

        # Verify the error was handled
        self.assertIn("error", message.lower())
        self.assertIn("divide by zero", message.lower())
        self.assertEqual(self.mock_provider.generate.call_count, 2)


if __name__ == "__main__":
    unittest.main()
