"""
Test the StructuredMessage class for agent communication.
"""

import unittest
import json
import time
import uuid
from atlas.agents.messaging.message import StructuredMessage, MessageType


class TestStructuredMessage(unittest.TestCase):
    """Test cases for the StructuredMessage class."""

    def test_basic_initialization(self):
        """Test basic initialization of a StructuredMessage."""
        msg = StructuredMessage(content="Hello, agent!")
        
        # Verify content is set
        self.assertEqual(msg.content, "Hello, agent!")
        
        # Verify default values
        self.assertIsInstance(msg.metadata, dict)
        self.assertEqual(len(msg.metadata), 0)
        self.assertIsInstance(msg.task_id, str)
        self.assertIsInstance(msg.timestamp, float)
        self.assertLessEqual(msg.timestamp, time.time())
        self.assertEqual(len(msg.tool_calls), 0)
        self.assertEqual(len(msg.tool_results), 0)
        self.assertIsNone(msg.source_agent)
        self.assertIsNone(msg.target_agent)
        
    def test_initialization_with_parameters(self):
        """Test initialization with all parameters."""
        task_id = str(uuid.uuid4())
        metadata = {"type": "query", "priority": "high"}
        tool_calls = [{"name": "search", "arguments": {"query": "test"}, "id": "123"}]
        tool_results = [{"name": "search", "result": ["result1", "result2"], "call_id": "123"}]
        
        msg = StructuredMessage(
            content="Search for test",
            metadata=metadata,
            task_id=task_id,
            tool_calls=tool_calls,
            tool_results=tool_results
        )
        
        # Verify all fields are set correctly
        self.assertEqual(msg.content, "Search for test")
        self.assertEqual(msg.metadata, metadata)
        self.assertEqual(msg.task_id, task_id)
        self.assertEqual(msg.tool_calls, tool_calls)
        self.assertEqual(msg.tool_results, tool_results)
        
    def test_message_type_property(self):
        """Test the message_type property."""
        # Test known message type
        msg = StructuredMessage(content="Test", metadata={"type": MessageType.QUERY})
        self.assertEqual(msg.message_type, MessageType.QUERY)
        
        # Test unknown message type
        msg = StructuredMessage(content="Test")
        self.assertEqual(msg.message_type, "unknown")
        
    def test_tool_calls_properties(self):
        """Test the has_tool_calls and has_tool_results properties."""
        # Message with no tools
        msg = StructuredMessage(content="Test")
        self.assertFalse(msg.has_tool_calls)
        self.assertFalse(msg.has_tool_results)
        
        # Message with tool calls
        msg = StructuredMessage(
            content="Test",
            tool_calls=[{"name": "search", "arguments": {"query": "test"}, "id": "123"}]
        )
        self.assertTrue(msg.has_tool_calls)
        self.assertFalse(msg.has_tool_results)
        
        # Message with tool results
        msg = StructuredMessage(
            content="Test",
            tool_results=[{"name": "search", "result": ["result1"], "call_id": "123"}]
        )
        self.assertFalse(msg.has_tool_calls)
        self.assertTrue(msg.has_tool_results)
        
    def test_add_tool_call(self):
        """Test adding a tool call to a message."""
        msg = StructuredMessage(content="Test")
        call_id = msg.add_tool_call("search", {"query": "test query"})
        
        # Verify tool call was added
        self.assertEqual(len(msg.tool_calls), 1)
        self.assertEqual(msg.tool_calls[0]["name"], "search")
        self.assertEqual(msg.tool_calls[0]["arguments"]["query"], "test query")
        self.assertEqual(msg.tool_calls[0]["id"], call_id)
        self.assertTrue(msg.has_tool_calls)
        
    def test_add_tool_result(self):
        """Test adding a tool result to a message."""
        msg = StructuredMessage(content="Test")
        call_id = "test-call-123"
        msg.add_tool_result("search", ["result1", "result2"], call_id)
        
        # Verify tool result was added
        self.assertEqual(len(msg.tool_results), 1)
        self.assertEqual(msg.tool_results[0]["name"], "search")
        self.assertEqual(msg.tool_results[0]["result"], ["result1", "result2"])
        self.assertEqual(msg.tool_results[0]["call_id"], call_id)
        self.assertEqual(msg.tool_results[0]["status"], "success")
        self.assertIsNone(msg.tool_results[0]["error"])
        self.assertTrue(msg.has_tool_results)
        
    def test_add_tool_result_with_error(self):
        """Test adding a tool result with an error."""
        msg = StructuredMessage(content="Test")
        call_id = "test-call-123"
        msg.add_tool_result(
            "search", 
            None, 
            call_id, 
            status="error", 
            error="Search failed: Service unavailable"
        )
        
        # Verify tool result was added with error
        self.assertEqual(len(msg.tool_results), 1)
        self.assertEqual(msg.tool_results[0]["status"], "error")
        self.assertEqual(msg.tool_results[0]["error"], "Search failed: Service unavailable")
        
    def test_to_dict(self):
        """Test converting a message to a dictionary."""
        msg = StructuredMessage(
            content="Test message",
            metadata={"type": MessageType.QUERY},
            task_id="task-123"
        )
        msg.source_agent = "user"
        msg.target_agent = "assistant"
        msg.add_tool_call("search", {"query": "test"})
        
        # Convert to dict
        data = msg.to_dict()
        
        # Verify dictionary structure
        self.assertEqual(data["content"], "Test message")
        self.assertEqual(data["metadata"], {"type": MessageType.QUERY})
        self.assertEqual(data["task_id"], "task-123")
        self.assertEqual(data["source_agent"], "user")
        self.assertEqual(data["target_agent"], "assistant")
        self.assertEqual(len(data["tool_calls"]), 1)
        self.assertEqual(data["tool_calls"][0]["name"], "search")
        
    def test_to_json(self):
        """Test converting a message to JSON."""
        msg = StructuredMessage(content="Test JSON", task_id="json-test-123")
        
        # Convert to JSON
        json_str = msg.to_json()
        
        # Parse JSON and verify
        data = json.loads(json_str)
        self.assertEqual(data["content"], "Test JSON")
        self.assertEqual(data["task_id"], "json-test-123")
        
    def test_from_dict(self):
        """Test creating a message from a dictionary."""
        data = {
            "content": "Reconstructed message",
            "metadata": {"type": MessageType.RESPONSE},
            "task_id": "reconstruct-123",
            "timestamp": time.time(),
            "tool_calls": [{"name": "calculate", "arguments": {"x": 5, "y": 10}, "id": "calc-1"}],
            "tool_results": [],
            "source_agent": "calculator",
            "target_agent": "user"
        }
        
        # Create from dict
        msg = StructuredMessage.from_dict(data)
        
        # Verify reconstruction
        self.assertEqual(msg.content, "Reconstructed message")
        self.assertEqual(msg.metadata, {"type": MessageType.RESPONSE})
        self.assertEqual(msg.task_id, "reconstruct-123")
        self.assertEqual(msg.timestamp, data["timestamp"])
        self.assertEqual(msg.source_agent, "calculator")
        self.assertEqual(msg.target_agent, "user")
        self.assertEqual(len(msg.tool_calls), 1)
        self.assertEqual(msg.tool_calls[0]["name"], "calculate")
        
    def test_from_json(self):
        """Test creating a message from JSON."""
        # Create a message and convert to JSON
        original = StructuredMessage(content="JSON roundtrip")
        json_str = original.to_json()
        
        # Reconstruct from JSON
        reconstructed = StructuredMessage.from_json(json_str)
        
        # Verify reconstruction
        self.assertEqual(reconstructed.content, "JSON roundtrip")
        self.assertEqual(reconstructed.task_id, original.task_id)
        self.assertEqual(reconstructed.timestamp, original.timestamp)
        
    def test_create_response(self):
        """Test creating a response message."""
        # Create original message
        original = StructuredMessage(
            content="Original query",
            metadata={"type": MessageType.QUERY},
        )
        original.source_agent = "user"
        original.target_agent = "assistant"
        
        # Create response
        response = StructuredMessage.create_response("Response content", original)
        
        # Verify response
        self.assertEqual(response.content, "Response content")
        self.assertEqual(response.metadata["type"], MessageType.RESPONSE)
        self.assertEqual(response.metadata["in_reply_to"], original.task_id)
        self.assertEqual(response.source_agent, "assistant")
        self.assertEqual(response.target_agent, "user")
        
    def test_create_error(self):
        """Test creating an error message."""
        # Create original message
        original = StructuredMessage(content="Original query")
        original.source_agent = "user"
        original.target_agent = "assistant"
        
        # Create error response
        error = StructuredMessage.create_error("An error occurred", original)
        
        # Verify error
        self.assertEqual(error.content, "An error occurred")
        self.assertEqual(error.metadata["type"], MessageType.ERROR)
        self.assertEqual(error.metadata["in_reply_to"], original.task_id)
        self.assertEqual(error.source_agent, "assistant")
        self.assertEqual(error.target_agent, "user")
        
        # Test error without original message
        standalone_error = StructuredMessage.create_error("Standalone error")
        self.assertEqual(standalone_error.content, "Standalone error")
        self.assertEqual(standalone_error.metadata["type"], MessageType.ERROR)
        self.assertNotIn("in_reply_to", standalone_error.metadata)
        
    def test_create_task(self):
        """Test creating a task message."""
        task = StructuredMessage.create_task(
            content="Analyze this document",
            source_agent="controller",
            target_agent="analysis_worker",
            task_data={"priority": "high", "deadline": "1h"}
        )
        
        # Verify task
        self.assertEqual(task.content, "Analyze this document")
        self.assertEqual(task.metadata["type"], MessageType.TASK)
        self.assertEqual(task.metadata["priority"], "high")
        self.assertEqual(task.metadata["deadline"], "1h")
        self.assertEqual(task.source_agent, "controller")
        self.assertEqual(task.target_agent, "analysis_worker")


if __name__ == "__main__":
    unittest.main()