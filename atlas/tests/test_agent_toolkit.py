"""
Test the AgentToolkit for tool registration and management.
"""

import unittest
from typing import List, Dict, Any, Optional

from atlas.tools.base import AgentToolkit, Tool, ToolSchema, FunctionTool


# Simple test functions to use as tools
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

def get_weather(location: str, unit: str = "celsius") -> Dict[str, Any]:
    """Get weather information for a location."""
    # Mock implementation
    return {
        "location": location,
        "temperature": 22 if unit == "celsius" else 72,
        "unit": unit,
        "conditions": "sunny"
    }


# A custom tool class for testing
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
                        "enum": ["add", "subtract", "multiply", "divide"]
                    },
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["operation", "a", "b"]
            },
            returns={
                "type": "number"
            }
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


class TestAgentToolkit(unittest.TestCase):
    """Test cases for the AgentToolkit class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.toolkit = AgentToolkit()
        
        # Register some tools
        self.toolkit.register_tool(add_numbers)
        self.toolkit.register_tool(get_weather)
        self.toolkit.register_tool(CalculatorTool())
        
        # Set up some permissions
        self.toolkit.grant_permission("agent1", "add_numbers")
        self.toolkit.grant_permission("agent1", "get_weather")
        self.toolkit.grant_permission("agent2", "CalculatorTool")
        self.toolkit.grant_all_permissions("admin")
    
    def test_register_tool_function(self):
        """Test registering a function as a tool."""
        # Register a new function
        def test_func(x: str) -> str:
            """Test function."""
            return x.upper()
            
        name = self.toolkit.register_tool(test_func)
        
        # Verify it was registered
        self.assertEqual(name, "test_func")
        self.assertIn("test_func", self.toolkit.tools)
        
        # Verify it's a FunctionTool
        tool = self.toolkit.tools["test_func"]
        self.assertIsInstance(tool, FunctionTool)
        
        # Verify schema was created correctly
        self.assertEqual(tool.schema.name, "test_func")
        self.assertEqual(tool.schema.description, "Test function.")
        self.assertIn("x", tool.schema.parameters["properties"])
        self.assertIn("x", tool.schema.parameters["required"])
    
    def test_register_duplicate_tool(self):
        """Test that registering a duplicate tool name raises an error."""
        with self.assertRaises(ValueError):
            self.toolkit.register_tool(add_numbers)
    
    def test_get_tool(self):
        """Test getting a tool by name."""
        # Get existing tool
        tool = self.toolkit.get_tool("add_numbers")
        self.assertIsNotNone(tool)
        self.assertEqual(tool.name, "add_numbers")
        
        # Try to get non-existent tool
        tool = self.toolkit.get_tool("non_existent")
        self.assertIsNone(tool)
    
    def test_permissions(self):
        """Test permission management."""
        # Check initial permissions
        self.assertTrue(self.toolkit.has_permission("agent1", "add_numbers"))
        self.assertTrue(self.toolkit.has_permission("agent1", "get_weather"))
        self.assertFalse(self.toolkit.has_permission("agent1", "CalculatorTool"))
        
        self.assertTrue(self.toolkit.has_permission("agent2", "CalculatorTool"))
        self.assertFalse(self.toolkit.has_permission("agent2", "add_numbers"))
        
        self.assertTrue(self.toolkit.has_permission("admin", "add_numbers"))
        self.assertTrue(self.toolkit.has_permission("admin", "get_weather"))
        self.assertTrue(self.toolkit.has_permission("admin", "CalculatorTool"))
        
        # Revoke a permission
        self.toolkit.revoke_permission("agent1", "add_numbers")
        self.assertFalse(self.toolkit.has_permission("agent1", "add_numbers"))
        self.assertTrue(self.toolkit.has_permission("agent1", "get_weather"))
        
        # Grant a new permission
        self.toolkit.grant_permission("agent1", "CalculatorTool")
        self.assertTrue(self.toolkit.has_permission("agent1", "CalculatorTool"))
        
        # Test unknown agent
        self.assertFalse(self.toolkit.has_permission("unknown", "add_numbers"))
    
    def test_get_accessible_tools(self):
        """Test getting accessible tools for an agent."""
        # Check agent1's accessible tools
        accessible = self.toolkit.get_accessible_tools("agent1")
        self.assertEqual(len(accessible), 2)
        self.assertIn("add_numbers", accessible)
        self.assertIn("get_weather", accessible)
        
        # Check admin's accessible tools (should be all)
        accessible = self.toolkit.get_accessible_tools("admin")
        self.assertEqual(len(accessible), 3)
        
        # Check unknown agent (should be empty)
        accessible = self.toolkit.get_accessible_tools("unknown")
        self.assertEqual(len(accessible), 0)
    
    def test_get_tool_descriptions(self):
        """Test getting tool descriptions for an agent."""
        descriptions = self.toolkit.get_tool_descriptions("agent1")
        
        # Should have 2 descriptions
        self.assertEqual(len(descriptions), 2)
        
        # Check content of descriptions
        names = [desc["name"] for desc in descriptions]
        self.assertIn("add_numbers", names)
        self.assertIn("get_weather", names)
        
        # Each description should have name, description, and parameters
        for desc in descriptions:
            self.assertIn("name", desc)
            self.assertIn("description", desc)
            self.assertIn("parameters", desc)
    
    def test_execute_tool(self):
        """Test executing a tool."""
        # Execute add_numbers as agent1
        result = self.toolkit.execute_tool("agent1", "add_numbers", {"a": 5, "b": 7})
        self.assertEqual(result, 12)
        
        # Execute get_weather with default parameter
        result = self.toolkit.execute_tool("agent1", "get_weather", {"location": "New York"})
        self.assertEqual(result["location"], "New York")
        self.assertEqual(result["unit"], "celsius")
        
        # Execute CalculatorTool as agent2
        result = self.toolkit.execute_tool("agent2", "CalculatorTool", {
            "operation": "multiply", 
            "a": 6, 
            "b": 7
        })
        self.assertEqual(result, 42)
        
        # Try to execute without permission
        with self.assertRaises(PermissionError):
            self.toolkit.execute_tool("agent1", "CalculatorTool", {
                "operation": "add", 
                "a": 1, 
                "b": 2
            })
        
        # Try to execute non-existent tool
        with self.assertRaises(ValueError):
            self.toolkit.execute_tool("admin", "non_existent", {})
    
    def test_function_tool_arg_validation(self):
        """Test that FunctionTool validates arguments correctly."""
        # Missing required argument
        with self.assertRaises(ValueError):
            self.toolkit.execute_tool("agent1", "add_numbers", {"a": 5})
        
        # Execute with all required arguments
        result = self.toolkit.execute_tool("agent1", "add_numbers", {"a": 5, "b": 7})
        self.assertEqual(result, 12)
        
        # Execute with optional argument
        result = self.toolkit.execute_tool("agent1", "get_weather", {
            "location": "London",
            "unit": "fahrenheit"
        })
        self.assertEqual(result["temperature"], 72)
    
    def test_custom_tool_validation(self):
        """Test that custom Tool validates arguments correctly."""
        # Missing required argument
        with self.assertRaises(ValueError):
            calculator = self.toolkit.get_tool("CalculatorTool")
            calculator.execute(operation="add", a=5)
        
        # Invalid operation
        with self.assertRaises(ValueError):
            self.toolkit.execute_tool("agent2", "CalculatorTool", {
                "operation": "power", 
                "a": 2, 
                "b": 3
            })
        
        # Division by zero error
        with self.assertRaises(ValueError):
            self.toolkit.execute_tool("agent2", "CalculatorTool", {
                "operation": "divide", 
                "a": 10, 
                "b": 0
            })


if __name__ == "__main__":
    unittest.main()