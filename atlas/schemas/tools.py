"""
Schema validation for tools in the Atlas framework.

This module provides comprehensive schema validation for tool definitions,
tool calls, tool results, and tool permissions, ensuring proper validation
across all tool operations.
"""

import time
from typing import Dict, List, Any, Optional, Type
from marshmallow import Schema, fields, post_load, pre_load, validates_schema, ValidationError

from atlas.core.types import (
    ToolSchemaDict, ToolResultDict, ToolDefinitionDict, ToolExecutionDict
)
from atlas.schemas.base import AtlasSchema as BaseSchema


class ToolParameterSchema(BaseSchema):
    """Schema for tool parameters."""
    
    type = fields.String(required=True)
    description = fields.String(required=False)
    enum = fields.List(fields.Field(), required=False)
    minimum = fields.Number(required=False)
    maximum = fields.Number(required=False)
    format = fields.String(required=False)
    pattern = fields.String(required=False)
    items = fields.Dict(required=False)  # For array types
    properties = fields.Dict(keys=fields.String(), values=fields.Dict(), required=False)
    required = fields.List(fields.String(), required=False)
    additionalProperties = fields.Field(required=False)


class ToolSchemaDefinitionSchema(BaseSchema):
    """Schema for validating tool schemas."""
    
    name = fields.String(required=True)
    description = fields.String(required=True)
    parameters = fields.Dict(required=True)
    returns = fields.Dict(required=False)
    
    @validates_schema
    def validate_parameters(self, data, **kwargs):
        """Validate the parameters field follows JSON Schema format."""
        parameters = data.get("parameters", {})
        
        # Parameters should be an object
        if not isinstance(parameters, dict):
            raise ValidationError("Parameters must be an object", field_name="parameters")
            
        # Parameters should have a "type" field
        if "type" not in parameters:
            raise ValidationError("Parameters must have a 'type' field", field_name="parameters")
            
        # If type is "object", should have "properties"
        if parameters.get("type") == "object" and "properties" not in parameters:
            raise ValidationError("Object parameters must have 'properties'", field_name="parameters")
            
        # Verify required fields
        required = parameters.get("required", [])
        properties = parameters.get("properties", {})
        for req in required:
            if req not in properties:
                raise ValidationError(f"Required parameter '{req}' not defined in properties", field_name="parameters")


class ToolSchemaSchema(ToolSchemaDefinitionSchema):
    """Full schema for validating tool schemas with object creation."""
    
    @post_load
    def make_tool_schema(self, data, **kwargs):
        """Convert validated data to a ToolSchema object."""
        from atlas.tools.base import ToolSchema
        return ToolSchema(**data)


class ToolDefinitionSchema(BaseSchema):
    """Schema for validating tool definitions."""
    
    name = fields.String(required=True)
    description = fields.String(required=True)
    schema = fields.Nested(ToolSchemaDefinitionSchema, required=True)
    
    @post_load
    def make_tool_definition(self, data, **kwargs):
        """Convert validated data to a tool definition dictionary."""
        # Just return as a dictionary, as we don't have a specific class for tool definitions
        return data


class ToolPermissionSchema(BaseSchema):
    """Schema for tool permissions."""
    
    agent_id = fields.String(required=True)
    tool_name = fields.String(required=True)
    granted_at = fields.Float(required=True)
    granted_by = fields.String(allow_none=True)
    scope = fields.String(required=True)
    
    @post_load
    def make_tool_permission(self, data, **kwargs):
        """Convert validated data to a ToolPermission object."""
        from atlas.tools.base import ToolPermission
        return ToolPermission(**data)


class ToolCallSchema(BaseSchema):
    """Schema for tool calls."""
    
    name = fields.String(required=True)
    arguments = fields.Dict(required=True)
    id = fields.String(required=False)
    
    @validates_schema
    def validate_structure(self, data, **kwargs):
        """Validate the basic structure of a tool call."""
        if not data.get("name"):
            raise ValidationError("Tool call must have a name", field_name="name")
        
        arguments = data.get("arguments")
        if not isinstance(arguments, dict):
            raise ValidationError("Tool arguments must be an object", field_name="arguments")
    
    @validates_schema
    def validate_arguments(self, data, **kwargs):
        """Validate the arguments of a tool call.
        
        This performs additional validation to ensure the arguments
        are properly formatted as key-value pairs.
        """
        arguments = data.get("arguments", {})
        
        # Ensure arguments is a dictionary
        if not isinstance(arguments, dict):
            raise ValidationError("Tool arguments must be a key-value object", field_name="arguments")
        
        # Validate argument types (basic validation)
        for key, value in arguments.items():
            if not isinstance(key, str):
                raise ValidationError(f"Argument key '{key}' must be a string", field_name="arguments")
    
    @post_load
    def make_tool_call(self, data, **kwargs):
        """Convert validated data to a tool call dictionary."""
        # Return as a dictionary as we don't have a specific class for tool calls
        return data


class ToolResultSchema(BaseSchema):
    """Schema for tool execution results."""
    
    name = fields.String(required=True)
    result = fields.Field(required=True)
    call_id = fields.String(required=False)
    status = fields.String(required=False)
    error = fields.String(required=False, allow_none=True)
    
    @pre_load
    def set_default_status(self, data, **kwargs):
        """Set default status if not provided."""
        if 'status' not in data:
            data['status'] = "success"
        return data
    
    @validates_schema
    def validate_status(self, data, **kwargs):
        """Validate the status field of a tool result."""
        status = data.get("status")
        if status not in ["success", "error", "cancelled"]:
            raise ValidationError(
                f"Tool result status '{status}' must be one of: success, error, cancelled",
                field_name="status"
            )
    
    @post_load
    def make_tool_result(self, data, **kwargs):
        """Convert validated data to a tool result dictionary."""
        # Return as a dictionary as we don't have a specific class for tool results
        return data


class ToolExecutionSchema(BaseSchema):
    """Schema for tool execution requests."""
    
    agent_id = fields.String(required=True)
    tool_name = fields.String(required=True)
    arguments = fields.Dict(required=True)
    request_id = fields.String(required=False)
    
    @validates_schema
    def validate_execution(self, data, **kwargs):
        """Validate the execution request structure."""
        if not data.get("agent_id"):
            raise ValidationError("Tool execution must have an agent ID", field_name="agent_id")
        
        if not data.get("tool_name"):
            raise ValidationError("Tool execution must have a tool name", field_name="tool_name")
        
        arguments = data.get("arguments")
        if not isinstance(arguments, dict):
            raise ValidationError("Tool arguments must be an object", field_name="arguments")
    
    @post_load
    def make_execution(self, data, **kwargs):
        """Convert validated data to a tool execution dictionary."""
        # Return as a dictionary as we don't have a specific class for tool executions
        return data


# Validation utility functions

def validate_tool_schema(schema_dict: ToolSchemaDict) -> bool:
    """Validate a tool schema dictionary.
    
    Args:
        schema_dict: Tool schema dictionary to validate.
        
    Returns:
        True if validation succeeds, False otherwise.
        
    Raises:
        ValidationError: If validation fails.
    """
    schema = ToolSchemaSchema()
    schema.load(schema_dict)
    return True


def validate_tool_definition(definition_dict: ToolDefinitionDict) -> bool:
    """Validate a tool definition dictionary.
    
    Args:
        definition_dict: Tool definition dictionary to validate.
        
    Returns:
        True if validation succeeds, False otherwise.
        
    Raises:
        ValidationError: If validation fails.
    """
    schema = ToolDefinitionSchema()
    schema.load(definition_dict)
    return True


def validate_tool_call(call_dict: Dict[str, Any]) -> bool:
    """Validate a tool call dictionary.
    
    Args:
        call_dict: Tool call dictionary to validate.
        
    Returns:
        True if validation succeeds, False otherwise.
        
    Raises:
        ValidationError: If validation fails.
    """
    schema = ToolCallSchema()
    schema.load(call_dict)
    return True


def validate_tool_result(result_dict: ToolResultDict) -> bool:
    """Validate a tool result dictionary.
    
    Args:
        result_dict: Tool result dictionary to validate.
        
    Returns:
        True if validation succeeds, False otherwise.
        
    Raises:
        ValidationError: If validation fails.
    """
    schema = ToolResultSchema()
    schema.load(result_dict)
    return True


def validate_tool_execution(execution_dict: ToolExecutionDict) -> bool:
    """Validate a tool execution dictionary.
    
    Args:
        execution_dict: Tool execution dictionary to validate.
        
    Returns:
        True if validation succeeds, False otherwise.
        
    Raises:
        ValidationError: If validation fails.
    """
    schema = ToolExecutionSchema()
    schema.load(execution_dict)
    return True