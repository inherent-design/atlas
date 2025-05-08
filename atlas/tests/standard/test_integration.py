"""
Integration tests for Atlas components.

This module tests interactions between different components of the Atlas framework.
"""

import os
import sys
import unittest
import logging
from unittest import mock
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Import test helpers
from atlas.tests.test_helpers import (
    TestWithTokenTracking,
    api_test,
    mock_test,
    integration_test,
    create_mock_response,
    create_integration_test,
)

# Import Atlas components
from atlas.models import (
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ModelMessage,
    TokenUsage,
    CostEstimate,
)

# Import providers
from atlas.models.openai import OpenAIProvider
from atlas.models.mock import MockProvider
from atlas.models.factory import get_provider_class, create_provider

# Import agent components
from atlas.agents.base import BaseAgent
from atlas.agents.specialized.tool_agent import ToolCapableAgent

# Import tool components
from atlas.tools.base import BaseTool, ToolRegistry

# Configure logging
logger = logging.getLogger(__name__)


# Sample Tool Implementation
class CalculatorTool(BaseTool):
    """A simple calculator tool for testing."""
    
    name = "calculator"
    description = "Perform basic arithmetic operations"
    version = "1.0.0"
    
    def execute(self, operation: str, a: float, b: float) -> Dict[str, Any]:
        """Execute the calculator operation.
        
        Args:
            operation: The operation to perform (add, subtract, multiply, divide)
            a: First number
            b: Second number
            
        Returns:
            Dictionary with result
        """
        if operation == "add":
            return {"result": a + b}
        elif operation == "subtract":
            return {"result": a - b}
        elif operation == "multiply":
            return {"result": a * b}
        elif operation == "divide":
            if b == 0:
                raise ValueError("Cannot divide by zero")
            return {"result": a / b}
        else:
            raise ValueError(f"Unknown operation: {operation}")


class TestComponentIntegration(TestWithTokenTracking):
    """Test the integration between different Atlas components."""
    
    def setUp(self):
        """Set up for integration tests."""
        super().setUp()
        
        # Create a registry
        self.registry = ToolRegistry()
        
        # Register calculator tool
        self.registry.register(CalculatorTool())
        
        # Create a mock provider
        self.provider = MockProvider()
        
        # Create a tool-capable agent
        self.agent = ToolCapableAgent(
            provider=self.provider,
            system_prompt="You are a helpful assistant with access to tools.",
            tool_registry=self.registry
        )
    
    @mock_test
    def test_tool_agent_integration(self):
        """Test integration between agent and tools."""
        # Configure the mock provider to simulate tool usage
        tool_call_response = """
        I'll help you calculate 5 + 10.
        
        <tool_calls>
        <tool_call name="calculator">
        {"operation": "add", "a": 5, "b": 10}
        </tool_call>
        </tool_calls>
        """
        
        final_response = """
        The result of 5 + 10 = 15.
        """
        
        # Configure the mock provider to return tool calls then final response
        self.provider.set_response_sequence([
            tool_call_response,
            final_response
        ])
        
        # Create a query that will use the calculator tool
        query = "Calculate 5 + 10"
        
        # Execute the query
        response = self.agent.execute(query)
        
        # Check that the agent used the tool and got the result
        self.assertIn("15", response.content)
        
        # Check that the agent made two calls to the provider
        self.assertEqual(self.provider.call_count, 2)
    
    @integration_test
    def test_provider_factory_integration(self):
        """Test integration between provider factory and providers."""
        # Test provider factory integration with mock provider
        provider_name = "mock"
        provider_class = get_provider_class(provider_name)
        provider = create_provider(provider_name)
        
        # Check that the factory created the right provider
        self.assertEqual(provider.name, provider_name)
        self.assertIsInstance(provider, provider_class)
        
        # Test creating a request and generating a response
        request = ModelRequest(
            messages=[ModelMessage.user("Test message")],
            max_tokens=10
        )
        
        response = provider.generate(request)
        
        # Check the response
        self.assertIsInstance(response, ModelResponse)
        self.assertEqual(response.provider, provider_name)
    
    @integration_test
    def test_tool_registry_integration(self):
        """Test integration between tool registry and tools."""
        # Create a registry
        registry = ToolRegistry()
        
        # Register calculator tool
        registry.register(CalculatorTool())
        
        # Check that tool is registered
        self.assertTrue(registry.has_tool("calculator"))
        
        # Get tool
        calculator = registry.get_tool("calculator")
        
        # Test tool execution through registry
        result = calculator.execute(operation="add", a=7, b=3)
        
        # Check result
        self.assertEqual(result["result"], 10)
        
        # Test tool validation through registry
        with self.assertRaises(ValueError):
            calculator.execute(operation="unknown", a=1, b=2)
    
    @api_test
    def test_real_provider_tool_integration(self):
        """Test integration between real provider and tools.
        
        This test uses a real provider with the tool-capable agent.
        """
        # Skip if no API key
        if not os.environ.get("OPENAI_API_KEY"):
            self.skipTest("OPENAI_API_KEY not set")
        
        # Create a real provider (use cheaper model)
        provider = OpenAIProvider(model_name="gpt-3.5-turbo")
        
        # Create a registry
        registry = ToolRegistry()
        
        # Register calculator tool
        registry.register(CalculatorTool())
        
        # Create an agent with real provider
        agent = ToolCapableAgent(
            provider=provider,
            system_prompt="You are a helpful assistant with access to tools.",
            tool_registry=registry
        )
        
        # Create a query that should use the calculator tool
        query = "What is 15 + 27?"
        
        # Execute the query
        response = agent.execute(query)
        
        # Track token usage
        self.track_usage(response)
        
        # Check that the agent used the tool and got the correct result
        self.assertIn("42", response.content)
        

# Factory for creating integration tests
def create_component_test(component1, component2, test_func):
    """Create an integration test for two components.
    
    Args:
        component1: First component instance.
        component2: Second component instance.
        test_func: Function that tests the integration.
        
    Returns:
        A test function.
    """
    @integration_test
    def component_test_func(self):
        return test_func(self, component1, component2)
    return component_test_func


class TestDynamicIntegration(unittest.TestCase):
    """Test class that creates integration tests dynamically."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class by adding dynamic tests."""
        # Create components
        mock_provider = MockProvider()
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        
        # Example test function
        def test_calculator_integration(self, provider, tool_registry):
            calculator = tool_registry.get_tool("calculator")
            result = calculator.execute(operation="add", a=5, b=7)
            self.assertEqual(result["result"], 12)
        
        # Add test dynamically
        setattr(cls, "test_calculator_with_mock", 
                create_component_test(mock_provider, registry, test_calculator_integration))


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    unittest.main()