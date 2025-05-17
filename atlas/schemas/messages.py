"""
Message schemas for Atlas.

This module provides Marshmallow schemas for message objects used in
provider interactions, including content formats, message roles, and
related structures. These schemas are used to validate and transform
message data at runtime, ensuring type safety and data integrity.

This module extends pure schema definitions with post_load methods
that convert validated data into actual implementation objects.
"""

from typing import Any, Dict, List, Optional, Union, cast, Type
from enum import Enum

from marshmallow import post_load, Schema

from atlas.schemas.base import AtlasSchema
from atlas.schemas.definitions.messages import (
    message_role_schema as base_message_role_schema,
    text_content_schema as base_text_content_schema,
    image_url_schema,
    image_content_schema as base_image_content_schema,
    message_content_schema as base_message_content_schema,
    model_message_schema as base_model_message_schema,
)
from atlas.schemas.validation import validate_with_schema
from atlas.core.types import MessageRole


class MessageRoleSchema(base_message_role_schema.__class__):
    """Schema for message roles with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> MessageRole:
        """Convert loaded data into a MessageRole enum.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A MessageRole enum value.
        """
        return data["role"]


class TextContentSchema(base_text_content_schema.__class__):
    """Schema for text content in messages with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Any:
        """Convert loaded data into a TextContent object.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A MessageContent object with text type.
        """
        # Import here to avoid circular imports
        from atlas.providers.messages import MessageContent
        # Create with direct parameters (prevent recursion)
        return MessageContent.__new__(
            MessageContent,
            type="text",
            text=data["text"]
        )


class ImageContentSchema(base_image_content_schema.__class__):
    """Schema for image content in messages with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Any:
        """Convert loaded data into an ImageContent object.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A MessageContent object with image_url type.
        """
        # Import here to avoid circular imports
        from atlas.providers.messages import MessageContent
        # Create with direct parameters (prevent recursion)
        return MessageContent.__new__(
            MessageContent,
            type="image_url",
            image_url=data["image_url"]
        )


class MessageContentSchema(base_message_content_schema.__class__):
    """Schema for message content with polymorphic handling and implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Any:
        """Convert loaded data into the appropriate content object.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A MessageContent object.
            
        Raises:
            ValidationError: If content type is unsupported.
        """
        # Import here to avoid circular imports
        from atlas.providers.messages import MessageContent
        
        # Get the content type, defaulting to "text"
        content_type = data.get("type", "text")
        
        # Create appropriate content object based on type
        if content_type == "text":
            text = data.get("text", "")
            return MessageContent.create_direct(type="text", text=text)
        elif content_type == "image_url":
            image_url = data.get("image_url", {})
            return MessageContent.create_direct(type="image_url", image_url=image_url)
        else:
            # For any other content type, use generic approach
            return MessageContent.create_direct(
                type=content_type,
                text=data.get("text"),
                image_url=data.get("image_url")
            )


class ModelMessageSchema(base_model_message_schema.__class__):
    """Schema for model messages with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Any:
        """Convert loaded data into a ModelMessage object.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A ModelMessage object.
        """
        # Import here to avoid circular imports
        from atlas.providers.messages import ModelMessage
        
        # Process role to ensure it's a proper enum
        role = data.get("role")
        if isinstance(role, str):
            from atlas.core.types import MessageRole
            try:
                role = MessageRole(role)
                data["role"] = role
            except ValueError:
                # Default to USER role if conversion fails
                data["role"] = MessageRole.USER
                
        # Process content field to ensure it exists
        if "content" not in data or data["content"] is None:
            data["content"] = "Empty message"
            
        # Ensure name is provided (None is acceptable for USER and ASSISTANT roles)
        if "name" not in data:
            data["name"] = None
        
        # Create directly to avoid schema validation recursive loop
        instance = ModelMessage.__new__(ModelMessage)
        
        # Set attributes directly
        for key, value in data.items():
            setattr(instance, key, value)
            
        return instance


# Create schema instances
message_role_schema = MessageRoleSchema()
text_content_schema = TextContentSchema()
image_content_schema = ImageContentSchema()
message_content_schema = MessageContentSchema()
model_message_schema = ModelMessageSchema()

# Export the validation decorators alongside the schemas
__all__ = [
    'message_role_schema',
    'text_content_schema',
    'image_content_schema',
    'message_content_schema',
    'model_message_schema',
    'validate_message_content',
    'validate_model_message',
    'validate_message_list',
    'validate_message_param',
    'validate_messages_param',
    'validate_content_param',
]


# Additional utility functions for message validation
import functools
from typing import Callable, TypeVar, cast

F = TypeVar('F', bound=Callable[..., Any])

def validate_message_content(content: Any) -> Any:
    """Validate and convert message content.
    
    Args:
        content: The content to validate.
        
    Returns:
        Validated MessageContent object.
        
    Raises:
        ValidationError: If validation fails.
    """
    return message_content_schema.load(content)


def validate_model_message(message: Dict[str, Any]) -> Any:
    """Validate and convert a model message.
    
    Args:
        message: The message to validate.
        
    Returns:
        Validated ModelMessage object.
        
    Raises:
        ValidationError: If validation fails.
    """
    return model_message_schema.load(message)


def validate_message_list(messages: List[Dict[str, Any]]) -> List[Any]:
    """Validate a list of messages.
    
    Args:
        messages: The list of messages to validate.
        
    Returns:
        List of validated ModelMessage objects.
        
    Raises:
        ValidationError: If validation of any message fails.
    """
    validated_messages = []
    errors = {}
    
    for i, message in enumerate(messages):
        try:
            validated_message = model_message_schema.load(message)
            validated_messages.append(validated_message)
        except ValidationError as e:
            errors[f"message[{i}]"] = e.messages
    
    if errors:
        raise ValidationError(errors)
    
    return validated_messages


# Decorator functions for message-related validation

def validate_message_param(func: F) -> F:
    """Decorator to validate a message parameter.
    
    This decorator ensures that a 'message' parameter is properly validated
    against the model_message_schema.
    
    Args:
        func: The function to decorate.
        
    Returns:
        Decorated function with validation.
        
    Example:
        ```python
        @validate_message_param
        def process_message(self, message: Dict[str, Any]) -> Any:
            # message is guaranteed to be valid
            ...
        ```
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if "message" in kwargs:
            try:
                # Validate using the schema
                validated = model_message_schema.load(kwargs["message"])
                kwargs["message"] = validated
            except ValidationError as e:
                raise ValidationError(f"Invalid message: {e.messages}")
        
        # Call the original function
        return func(*args, **kwargs)
    
    return cast(F, wrapper)


def validate_messages_param(func: F) -> F:
    """Decorator to validate a list of messages.
    
    This decorator ensures that a 'messages' parameter containing a list of
    messages is properly validated against the model_message_schema.
    
    Args:
        func: The function to decorate.
        
    Returns:
        Decorated function with validation.
        
    Example:
        ```python
        @validate_messages_param
        def process_messages(self, messages: List[Dict[str, Any]]) -> Any:
            # messages are guaranteed to be valid
            ...
        ```
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if "messages" in kwargs and isinstance(kwargs["messages"], list):
            try:
                # Validate using the validate_message_list function
                validated = validate_message_list(kwargs["messages"])
                kwargs["messages"] = validated
            except ValidationError as e:
                raise ValidationError(f"Invalid messages: {e.messages}")
        
        # Call the original function
        return func(*args, **kwargs)
    
    return cast(F, wrapper)


def validate_content_param(func: F) -> F:
    """Decorator to validate a content parameter.
    
    This decorator ensures that a 'content' parameter is properly validated
    against the message_content_schema.
    
    Args:
        func: The function to decorate.
        
    Returns:
        Decorated function with validation.
        
    Example:
        ```python
        @validate_content_param
        def process_content(self, content: Dict[str, Any]) -> Any:
            # content is guaranteed to be valid
            ...
        ```
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if "content" in kwargs:
            try:
                # Validate using the schema
                validated = message_content_schema.load(kwargs["content"])
                kwargs["content"] = validated
            except ValidationError as e:
                raise ValidationError(f"Invalid content: {e.messages}")
        
        # Call the original function
        return func(*args, **kwargs)
    
    return cast(F, wrapper)