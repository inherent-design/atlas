"""
Schema definitions for tools in the Atlas framework.

This module provides basic schema definitions for tools without post_load methods
to avoid circular import issues.
"""

from typing import Dict, List, Any, Optional
from marshmallow import Schema, fields, validates_schema, ValidationError, pre_load

from atlas.schemas.base import AtlasSchema as BaseSchema


class ToolParameterSchemaDefinition(BaseSchema):
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


class ToolDefinitionSchemaDefinition(BaseSchema):
    """Schema for validating tool definitions."""
    
    name = fields.String(required=True)
    description = fields.String(required=True)
    schema = fields.Nested(ToolSchemaDefinitionSchema, required=True)


class ToolPermissionSchemaDefinition(BaseSchema):
    """Schema for tool permissions."""
    
    agent_id = fields.String(required=True)
    tool_name = fields.String(required=True)
    granted_at = fields.Float(required=True)
    granted_by = fields.String(allow_none=True)
    scope = fields.String(required=True)


class ToolCallSchemaDefinition(BaseSchema):
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


class ToolResultSchemaDefinition(BaseSchema):
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