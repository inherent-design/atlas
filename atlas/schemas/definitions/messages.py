"""
Pure schema definitions for message types.

This module contains schema definitions without any post_load methods or references
to implementation classes, avoiding circular imports. These schemas define the 
structure and validation rules for various message types but don't handle conversion
to actual implementation objects.
"""

from typing import Any, Dict, List, Optional, Union
from marshmallow import fields, pre_load, validates, validates_schema, ValidationError

from atlas.schemas.base import AtlasSchema, EnumField, JsonField
from atlas.core.types import MessageRole

class MessageRoleSchema(AtlasSchema):
    """Schema for message roles."""
    
    role = EnumField(MessageRole, required=True)


class TextContentSchema(AtlasSchema):
    """Schema for text content in messages."""
    
    type = fields.Constant("text", required=True)
    text = fields.String(required=True)
    
    @validates("text")
    def validate_text(self, value: str, **kwargs) -> None:
        """Validate text content.
        
        Args:
            value: The text content to validate.
            **kwargs: Additional arguments passed by Marshmallow.
            
        Raises:
            ValidationError: If the text is empty or excessively large.
        """
        if not value:
            raise ValidationError("Text content cannot be empty")
        
        # Check for excessively large content
        if len(value) > 100000:
            raise ValidationError("Text content exceeds maximum length (100,000 characters)")


class ImageUrlSchema(AtlasSchema):
    """Schema for image URL details."""
    
    url = fields.String(required=True)
    detail = fields.String(validate=lambda x: x in ["auto", "high", "low"], required=False, load_default="auto")
    
    @validates("url")
    def validate_url(self, value: str, **kwargs) -> None:
        """Validate image URL.
        
        Args:
            value: The URL to validate.
            **kwargs: Additional arguments passed by Marshmallow.
            
        Raises:
            ValidationError: If the URL is invalid.
        """
        if not value:
            raise ValidationError("Image URL cannot be empty")
        
        # Basic URL validation - could be enhanced with regex pattern matching
        if not (value.startswith("http://") or value.startswith("https://") or value.startswith("data:")):
            raise ValidationError("Image URL must begin with http://, https://, or data:")


class ImageContentSchema(AtlasSchema):
    """Schema for image content in messages."""
    
    type = fields.Constant("image_url", required=True)
    image_url = fields.Nested(ImageUrlSchema, required=True)


class MessageContentSchema(AtlasSchema):
    """Schema for message content with polymorphic handling."""
    
    # Define required fields that should be handled by subschemas
    type = fields.String(required=True)
    
    @pre_load
    def determine_type(self, data: Any, **kwargs) -> Dict[str, Any]:
        """Determine the content type and pre-process accordingly.
        
        Args:
            data: The data to load.
            **kwargs: Additional arguments.
            
        Returns:
            Processed data dictionary.
            
        Raises:
            ValidationError: If content type is invalid or missing.
        """
        if isinstance(data, str):
            # Plain text content
            return {"type": "text", "text": data}
        
        if isinstance(data, dict):
            if "type" not in data:
                if "text" in data:
                    data["type"] = "text"
                elif "image_url" in data:
                    data["type"] = "image_url"
                else:
                    raise ValidationError("Cannot determine content type from data")
            
            # Make a copy to avoid modifying the input
            return dict(data)
        
        raise ValidationError(f"Invalid content format: {data}")
    
    @validates_schema
    def validate_content_by_type(self, data: Dict[str, Any], **kwargs) -> None:
        """Validate content based on its type.
        
        Args:
            data: The data to validate.
            **kwargs: Additional arguments.
            
        Raises:
            ValidationError: If content is invalid for its type.
        """
        content_type = data.get("type")
        
        if content_type == "text":
            # Validate with TextContentSchema
            TextContentSchema().validate(data)
        elif content_type == "image_url":
            # Validate with ImageContentSchema
            ImageContentSchema().validate(data)
        # Add validation for other content types as needed


class ModelMessageSchema(AtlasSchema):
    """Schema for model messages."""
    
    role = EnumField(MessageRole, required=True)
    content = fields.Raw(required=True)
    name = fields.String(required=False, allow_none=True)
    
    @validates_schema
    def validate_message(self, data: Dict[str, Any], **kwargs) -> None:
        """Validate the message structure holistically.
        
        Args:
            data: The data to validate.
            **kwargs: Additional arguments.
            
        Raises:
            ValidationError: If validation fails.
        """
        # Role-specific validations
        role = data.get("role")
        name = data.get("name")
        
        # Validate function/tool messages have names
        if role in [MessageRole.FUNCTION, MessageRole.TOOL] and not name:
            raise ValidationError(f"{role.value} messages must include a name")
        
    @pre_load
    def process_content(self, data: Any, **kwargs) -> Dict[str, Any]:
        """Pre-process message content during deserialization.
        
        Args:
            data: The data to load.
            **kwargs: Additional arguments.
            
        Returns:
            Processed data dictionary.
        """
        # Handle ModelMessage objects
        if hasattr(data, '__iter__') and not isinstance(data, (dict, list, str)):
            # Convert iterable object to dict
            data_dict = {k: v for k, v in data}
            return self.process_content(data_dict, **kwargs)
        
        # Handle dictionaries
        if isinstance(data, dict):
            # Make a copy to avoid modifying the input
            result = {**data}
            
            # Extract required fields or set defaults
            if "role" not in result:
                result["role"] = MessageRole.USER
                
            # Handle content field
            content = result.get("content")
            
            # If content is missing, add a default
            if content is None:
                result["content"] = "Empty message"
            # If content is a list, process each item
            elif isinstance(content, list):
                try:
                    result["content"] = [
                        MessageContentSchema().load(item) 
                        for item in content
                    ]
                except Exception:
                    # Default to a simple string if processing fails
                    result["content"] = str(content)
            
            return result
            
        # For other types (like strings), create a basic message
        if isinstance(data, str):
            return {
                "role": MessageRole.USER,
                "content": data
            }
            
        # Last resort fallback
        return {
            "role": MessageRole.USER,
            "content": str(data)
        }


# Export schema instances for convenient use
message_role_schema = MessageRoleSchema()
text_content_schema = TextContentSchema()
image_url_schema = ImageUrlSchema()
image_content_schema = ImageContentSchema()
message_content_schema = MessageContentSchema()
model_message_schema = ModelMessageSchema()