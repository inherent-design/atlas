"""
Base Marshmallow schema definitions for Atlas.

This module provides foundational schemas and utilities that other
schema definitions can build upon. These include common field types,
validation utilities, and base schemas.
"""

import re
import json
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union
from enum import Enum

from marshmallow import (
    Schema, 
    fields, 
    post_load, 
    pre_load, 
    post_dump, 
    validates, 
    validates_schema,
    ValidationError,
    EXCLUDE
)


class AtlasSchema(Schema):
    """Base schema for all Atlas schemas.
    
    Provides common functionality for all Atlas schemas, including:
    - Default unknown field handling (exclude them)
    - Utility methods for validation and conversion
    """
    
    class Meta:
        """Schema metadata configuration."""
        # Exclude unknown fields by default
        unknown = EXCLUDE
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Any:
        """Convert loaded data into a specific object type.
        
        Subclasses can override this to return specific object types.
        By default, returns the dictionary as-is.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            The converted object.
        """
        return data
    
    @classmethod
    def validate_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against the schema without deserialization.
        
        Args:
            data: The data to validate.
            
        Returns:
            The validated data.
            
        Raises:
            ValidationError: If validation fails.
        """
        return cls().load(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Any:
        """Create an object from a dictionary.
        
        Args:
            data: The dictionary to convert.
            
        Returns:
            The converted object.
            
        Raises:
            ValidationError: If conversion fails.
        """
        return cls().load(data)
    
    @classmethod
    def to_dict(cls, obj: Any) -> Dict[str, Any]:
        """Convert an object to a dictionary.
        
        Args:
            obj: The object to convert.
            
        Returns:
            The dictionary representation.
            
        Raises:
            ValidationError: If conversion fails.
        """
        return cls().dump(obj)


class EnumField(fields.Field):
    """Field that serializes/deserializes an Enum value.
    
    This field handles conversion between Enum values and their string
    representations. It provides validation to ensure only valid enum
    values are accepted.
    """
    
    def __init__(self, enum_class: Type[Enum], by_value: bool = False, *args, **kwargs):
        """Initialize an EnumField.
        
        Args:
            enum_class: The Enum class to use for conversion.
            by_value: If True, use the enum value instead of the name.
            *args: Additional arguments passed to Field.
            **kwargs: Additional keyword arguments passed to Field.
        """
        self.enum_class = enum_class
        self.by_value = by_value
        super().__init__(*args, **kwargs)
    
    def _serialize(self, value: Optional[Enum], attr: str, obj: Any, **kwargs) -> Optional[str]:
        """Serialize an Enum value to a string.
        
        Args:
            value: The Enum value to serialize.
            attr: The attribute name.
            obj: The object being serialized.
            **kwargs: Additional arguments.
            
        Returns:
            The serialized string representation or None if value is None.
        """
        if value is None:
            return None
        
        if isinstance(value, self.enum_class):
            return value.value if self.by_value else value.name
        return value
    
    def _deserialize(self, value: Any, attr: Optional[str], data: Optional[Dict[str, Any]], **kwargs) -> Enum:
        """Deserialize a string to an Enum value.
        
        Args:
            value: The string to deserialize.
            attr: The attribute name.
            data: The raw data being deserialized.
            **kwargs: Additional arguments.
            
        Returns:
            The deserialized Enum value.
            
        Raises:
            ValidationError: If value cannot be converted to an Enum value.
        """
        try:
            if isinstance(value, self.enum_class):
                return value
            
            if self.by_value:
                return self.enum_class(value)
            else:
                # Allow both name and value for flexibility
                try:
                    return self.enum_class[value]
                except (KeyError, TypeError):
                    return self.enum_class(value)
        except (ValueError, KeyError, TypeError) as e:
            valid_values = [
                f"{enum.name} ({enum.value})" for enum in self.enum_class
            ]
            raise ValidationError(
                f"Invalid enum value '{value}'. Must be one of: {', '.join(valid_values)}"
            ) from e


class JsonField(fields.Field):
    """Field that serializes/deserializes JSON data.
    
    This field handles conversion between Python objects and JSON strings.
    """
    
    def _serialize(self, value: Any, attr: str, obj: Any, **kwargs) -> Optional[str]:
        """Serialize a Python object to a JSON string.
        
        Args:
            value: The Python object to serialize.
            attr: The attribute name.
            obj: The object being serialized.
            **kwargs: Additional arguments.
            
        Returns:
            The serialized JSON string or None if value is None.
        """
        if value is None:
            return None
        
        if isinstance(value, str):
            # Assume it's already JSON
            try:
                # Validate that it's valid JSON
                json.loads(value)
                return value
            except json.JSONDecodeError:
                pass
        
        try:
            return json.dumps(value)
        except (TypeError, ValueError) as e:
            raise ValidationError(f"Cannot serialize to JSON: {e}")
    
    def _deserialize(self, value: Union[str, Dict[str, Any], List[Any]], attr: Optional[str], data: Optional[Dict[str, Any]], **kwargs) -> Any:
        """Deserialize a JSON string to a Python object.
        
        Args:
            value: The JSON string to deserialize.
            attr: The attribute name.
            data: The raw data being deserialized.
            **kwargs: Additional arguments.
            
        Returns:
            The deserialized Python object.
            
        Raises:
            ValidationError: If JSON cannot be parsed.
        """
        if isinstance(value, (dict, list)):
            # Already deserialized
            return value
        
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValidationError(f"Invalid JSON: {e}")


# Other common base schemas can be added here as needed