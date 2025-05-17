#!/usr/bin/env python
"""
Complex serialization test for MessageContent and ModelMessage.

This script demonstrates a direct approach to serialization/deserialization
without relying on the schema validation system's to_dict method.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, cast

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from atlas.core.types import MessageRole
from atlas.providers.messages import (
    MessageContent, 
    ModelMessage,
)

def manual_serialize_message_content(content: MessageContent) -> Dict[str, Any]:
    """Manually serialize a MessageContent object to dictionary.
    
    Args:
        content: The MessageContent object to serialize.
        
    Returns:
        Dictionary representation with all fields.
    """
    result = {"type": content.type}
    
    # Include text field if present
    if content.text is not None:
        result["text"] = content.text
    
    # Include image_url field if present
    if content.image_url is not None:
        result["image_url"] = content.image_url
    
    return result

def manual_serialize_model_message(message: ModelMessage) -> Dict[str, Any]:
    """Manually serialize a ModelMessage object to dictionary.
    
    Args:
        message: The ModelMessage object to serialize.
        
    Returns:
        Dictionary representation with all fields.
    """
    # Start with basic fields
    result = {
        "role": message.role.value,
        "name": message.name
    }
    
    # Handle content based on its type
    if isinstance(message.content, str):
        # String content
        result["content"] = message.content
    elif isinstance(message.content, MessageContent):
        # MessageContent object
        if message.content.type == "text":
            # Simplify text content to just the text
            result["content"] = message.content.text
        else:
            # For non-text content, include all fields
            result["content"] = manual_serialize_message_content(message.content)
    elif isinstance(message.content, list):
        # List of content
        content_list = []
        for item in message.content:
            if isinstance(item, MessageContent):
                content_list.append(manual_serialize_message_content(item))
            else:
                content_list.append(item)
        result["content"] = content_list
    
    return result

def test_manual_serialization():
    """Test manual serialization of messages."""
    print("\n=== Testing Manual Serialization ===")
    
    # 1. Test text content
    text_content = MessageContent.create_text("Manual serialization test")
    text_dict = manual_serialize_message_content(text_content)
    print(f"Text content manual dict: {text_dict}")
    
    # Verify fields
    assert "type" in text_dict
    assert "text" in text_dict
    assert text_dict["type"] == "text"
    assert text_dict["text"] == "Manual serialization test"
    
    # 2. Test image content
    image_content = MessageContent.create_image_url("https://example.com/image.jpg")
    image_dict = manual_serialize_message_content(image_content)
    print(f"Image content manual dict: {image_dict}")
    
    # Verify fields
    assert "type" in image_dict
    assert "image_url" in image_dict
    assert image_dict["type"] == "image_url"
    assert image_dict["image_url"]["url"] == "https://example.com/image.jpg"
    
    # 3. Test text message
    text_message = ModelMessage.user("Text message")
    text_msg_dict = manual_serialize_model_message(text_message)
    print(f"Text message manual dict: {text_msg_dict}")
    
    # Verify fields
    assert "role" in text_msg_dict
    assert "content" in text_msg_dict
    assert "name" in text_msg_dict
    assert text_msg_dict["role"] == "USER"
    assert text_msg_dict["content"] == "Text message"
    
    # 4. Test message with content object
    content_message = ModelMessage.user(text_content)
    content_msg_dict = manual_serialize_model_message(content_message)
    print(f"Content message manual dict: {content_msg_dict}")
    
    # Verify fields
    assert "role" in content_msg_dict
    assert "content" in content_msg_dict
    assert content_msg_dict["role"] == "USER"
    assert content_msg_dict["content"] == "Manual serialization test"
    
    # 5. Test mixed content message
    mixed_content = [
        MessageContent.create_text("Text item"),
        MessageContent.create_image_url("https://example.com/image1.jpg"),
        MessageContent.create_image_url("https://example.com/image2.jpg")
    ]
    mixed_message = ModelMessage.user(mixed_content)
    mixed_dict = manual_serialize_model_message(mixed_message)
    print(f"Mixed message manual dict: {json.dumps(mixed_dict, indent=2)}")
    
    # Verify fields
    assert "role" in mixed_dict
    assert "content" in mixed_dict
    assert isinstance(mixed_dict["content"], list)
    assert len(mixed_dict["content"]) == 3
    assert mixed_dict["content"][0]["type"] == "text"
    assert mixed_dict["content"][1]["type"] == "image_url"
    assert mixed_dict["content"][2]["type"] == "image_url"
    
    print("All manual serialization tests passed!")
    return text_dict, image_dict, text_msg_dict, content_msg_dict, mixed_dict

def main():
    """Main test function."""
    print("Testing Complex Message Serialization")
    print("===================================\n")
    
    try:
        # Test manual serialization
        test_manual_serialization()
        
        print("\nAll complex serialization tests completed successfully!")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()