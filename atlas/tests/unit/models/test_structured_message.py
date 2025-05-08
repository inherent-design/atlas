"""
Unit tests for structured message classes.

This module tests the functionality of message-related classes and utilities.
"""

import unittest
from typing import Dict, Any, List, Optional

from atlas.tests.helpers.decorators import unit_test

from atlas.models import (
    ModelMessage,
    MessageContent,
    ModelRole,
)


class TestModelMessage(unittest.TestCase):
    """Test cases for the ModelMessage class."""

    @unit_test
    def test_message_creation(self):
        """Test creating message instances."""
        # Test user message
        user_msg = ModelMessage(role=ModelRole.USER, content="Hello")
        self.assertEqual(user_msg.role, ModelRole.USER)
        self.assertEqual(user_msg.content, "Hello")
        self.assertIsNone(user_msg.name)
        
        # Test assistant message
        assistant_msg = ModelMessage(role=ModelRole.ASSISTANT, content="How can I help you?")
        self.assertEqual(assistant_msg.role, ModelRole.ASSISTANT)
        self.assertEqual(assistant_msg.content, "How can I help you?")
        
        # Test system message
        system_msg = ModelMessage(role=ModelRole.SYSTEM, content="You are a helpful assistant.")
        self.assertEqual(system_msg.role, ModelRole.SYSTEM)
        self.assertEqual(system_msg.content, "You are a helpful assistant.")
        
        # Test message with name
        named_msg = ModelMessage(role=ModelRole.USER, content="Question", name="User123")
        self.assertEqual(named_msg.role, ModelRole.USER)
        self.assertEqual(named_msg.content, "Question")
        self.assertEqual(named_msg.name, "User123")

    @unit_test
    def test_message_factory_methods(self):
        """Test the message factory methods."""
        # Test user message factory
        user_msg = ModelMessage.user("Hello")
        self.assertEqual(user_msg.role, ModelRole.USER)
        self.assertEqual(user_msg.content, "Hello")
        
        # Test assistant message factory
        assistant_msg = ModelMessage.assistant("How can I help you?")
        self.assertEqual(assistant_msg.role, ModelRole.ASSISTANT)
        self.assertEqual(assistant_msg.content, "How can I help you?")
        
        # Test system message factory
        system_msg = ModelMessage.system("You are a helpful assistant.")
        self.assertEqual(system_msg.role, ModelRole.SYSTEM)
        self.assertEqual(system_msg.content, "You are a helpful assistant.")
        
        # Test tool message factory
        tool_msg = ModelMessage.tool("Tool result", "calculator")
        self.assertEqual(tool_msg.role, ModelRole.TOOL)
        self.assertEqual(tool_msg.content, "Tool result")
        self.assertEqual(tool_msg.name, "calculator")

    @unit_test
    def test_message_string_representation(self):
        """Test string representation of messages."""
        # Test user message
        user_msg = ModelMessage.user("Hello")
        str_repr = str(user_msg)
        self.assertIn("USER", str_repr)
        self.assertIn("Hello", str_repr)
        
        # Test system message
        system_msg = ModelMessage.system("System instruction")
        str_repr = str(system_msg)
        self.assertIn("SYSTEM", str_repr)
        self.assertIn("System instruction", str_repr)
        
        # Test tool message
        tool_msg = ModelMessage.tool("42", "calculator")
        str_repr = str(tool_msg)
        self.assertIn("TOOL", str_repr)
        self.assertIn("calculator", str_repr)
        self.assertIn("42", str_repr)

    @unit_test
    def test_message_dictionary_conversion(self):
        """Test converting messages to dictionaries."""
        # Test user message
        user_msg = ModelMessage.user("Hello")
        msg_dict = user_msg.to_dict()
        self.assertEqual(msg_dict["role"], "user")
        self.assertEqual(msg_dict["content"], "Hello")
        
        # Test message with name
        tool_msg = ModelMessage.tool("42", "calculator")
        msg_dict = tool_msg.to_dict()
        self.assertEqual(msg_dict["role"], "tool")
        self.assertEqual(msg_dict["content"], "42")
        self.assertEqual(msg_dict["name"], "calculator")
        
        # Test message from dictionary
        msg_dict = {"role": "assistant", "content": "Response"}
        msg = ModelMessage.from_dict(msg_dict)
        self.assertEqual(msg.role, ModelRole.ASSISTANT)
        self.assertEqual(msg.content, "Response")
        self.assertIsNone(msg.name)

    @unit_test
    def test_complex_content(self):
        """Test messages with complex content (list of parts)."""
        # Create message with text and image content
        content = [
            MessageContent.text("Look at this image:"),
            MessageContent.image_url("https://example.com/image.jpg")
        ]
        
        msg = ModelMessage(role=ModelRole.USER, content=content)
        
        # Check content structure
        self.assertIsInstance(msg.content, list)
        self.assertEqual(len(msg.content), 2)
        self.assertEqual(msg.content[0].type, "text")
        self.assertEqual(msg.content[0].text, "Look at this image:")
        self.assertEqual(msg.content[1].type, "image_url")
        self.assertEqual(msg.content[1].image_url["url"], "https://example.com/image.jpg")
        
        # Test conversion to dictionary
        msg_dict = msg.to_dict()
        self.assertEqual(msg_dict["role"], "user")
        self.assertIsInstance(msg_dict["content"], list)
        self.assertEqual(len(msg_dict["content"]), 2)
        self.assertEqual(msg_dict["content"][0]["type"], "text")
        self.assertEqual(msg_dict["content"][1]["type"], "image_url")

    @unit_test
    def test_message_content_factory_methods(self):
        """Test the MessageContent factory methods."""
        # Test text content
        text_content = MessageContent.text("Hello")
        self.assertEqual(text_content.type, "text")
        self.assertEqual(text_content.text, "Hello")
        
        # Test image URL content
        image_content = MessageContent.image_url("https://example.com/image.jpg")
        self.assertEqual(image_content.type, "image_url")
        self.assertEqual(image_content.image_url["url"], "https://example.com/image.jpg")
        
        # Test image URL with detail level
        image_detail = MessageContent.image_url("https://example.com/image.jpg", detail="high")
        self.assertEqual(image_detail.image_url["url"], "https://example.com/image.jpg")
        self.assertEqual(image_detail.image_url["detail"], "high")


if __name__ == "__main__":
    unittest.main()