"""
Pure schema definitions for agent-related types.

This module contains schema definitions without any post_load methods or references
to implementation classes, avoiding circular imports. These schemas define the 
structure and validation rules for agent types but don't handle conversion
to actual implementation objects.
"""

from typing import Any, Dict, List, Optional, Union
from marshmallow import fields, pre_load, validates, validates_schema, ValidationError

from atlas.schemas.base import AtlasSchema, EnumField, JsonField


class AgentTypeSchema(AtlasSchema):
    """Schema for agent types."""
    
    type = fields.String(required=True)
    
    @validates("type")
    def validate_agent_type(self, value: str) -> None:
        """Validate that the agent type is supported.
        
        Args:
            value: The agent type to validate.
            
        Raises:
            ValidationError: If the agent type is not supported.
        """
        valid_types = ["base", "worker", "controller", "task_aware", "tool"]
        if value not in valid_types:
            raise ValidationError(
                f"Invalid agent type: {value}. Must be one of: {', '.join(valid_types)}"
            )


class AgentOptionsSchema(AtlasSchema):
    """Schema for agent options."""
    
    model = fields.String(required=False, allow_none=True)
    provider = fields.String(required=False, allow_none=True)
    system_prompt = fields.String(required=False, allow_none=True)
    max_tokens = fields.Integer(required=False, allow_none=True, validate=lambda x: x is None or x > 0)
    temperature = fields.Float(required=False, allow_none=True, validate=lambda x: x is None or 0 <= x <= 2)
    top_p = fields.Float(required=False, allow_none=True, validate=lambda x: x is None or 0 <= x <= 1)


class TaskSpecificationSchema(AtlasSchema):
    """Schema for task specifications."""
    
    type = fields.String(required=True)
    description = fields.String(required=True)
    parameters = fields.Dict(required=False, allow_none=True)
    priority = fields.Integer(required=False, allow_none=True, validate=lambda x: x is None or 0 <= x <= 10)
    
    @validates("type")
    def validate_task_type(self, value: str) -> None:
        """Validate that the task type is supported.
        
        Args:
            value: The task type to validate.
            
        Raises:
            ValidationError: If the task type is not supported.
        """
        valid_types = ["query", "retrieval", "analysis", "generation", "custom"]
        if value not in valid_types:
            raise ValidationError(
                f"Invalid task type: {value}. Must be one of: {', '.join(valid_types)}"
            )


class ToolParameterSchema(AtlasSchema):
    """Schema for tool parameters."""
    
    type = fields.String(required=True)
    description = fields.String(required=True)
    required = fields.Boolean(required=False, load_default=False)
    default = fields.Raw(required=False, allow_none=True)
    enum = fields.List(fields.Raw(), required=False, allow_none=True)
    
    @validates("type")
    def validate_parameter_type(self, value: str) -> None:
        """Validate that the parameter type is supported.
        
        Args:
            value: The parameter type to validate.
            
        Raises:
            ValidationError: If the parameter type is not supported.
        """
        valid_types = ["string", "number", "integer", "boolean", "array", "object"]
        if value not in valid_types:
            raise ValidationError(
                f"Invalid parameter type: {value}. Must be one of: {', '.join(valid_types)}"
            )


class ToolSchemaSchema(AtlasSchema):
    """Schema for tool schemas."""
    
    name = fields.String(required=True)
    description = fields.String(required=True)
    parameters = fields.Dict(keys=fields.String(), values=fields.Nested(ToolParameterSchema), required=True)
    returns = fields.Dict(required=False, allow_none=True)


class ToolAgentOptionsSchema(AgentOptionsSchema):
    """Schema for tool agent options."""
    
    tools = fields.List(fields.String(), required=True)
    permissions = fields.Dict(keys=fields.String(), values=fields.List(fields.String()), required=False, allow_none=True)
    timeout = fields.Integer(required=False, allow_none=True, validate=lambda x: x is None or x > 0)
    max_iterations = fields.Integer(required=False, allow_none=True, validate=lambda x: x is None or x > 0)


class TaskAwareAgentOptionsSchema(AgentOptionsSchema):
    """Schema for task-aware agent options."""
    
    task_types = fields.List(fields.String(), required=False, allow_none=True)
    capabilities = fields.Dict(keys=fields.String(), values=fields.Integer(), required=False, allow_none=True)
    requirements = fields.Dict(keys=fields.String(), values=fields.String(), required=False, allow_none=True)


class ControllerAgentOptionsSchema(AgentOptionsSchema):
    """Schema for controller agent options."""
    
    max_workers = fields.Integer(required=False, allow_none=True, validate=lambda x: x is None or x > 0)
    worker_types = fields.List(fields.String(), required=False, allow_none=True)
    coordination_strategy = fields.String(required=False, allow_none=True)
    
    @validates("coordination_strategy")
    def validate_coordination_strategy(self, value: str) -> None:
        """Validate that the coordination strategy is supported.
        
        Args:
            value: The coordination strategy to validate.
            
        Raises:
            ValidationError: If the coordination strategy is not supported.
        """
        if value is None:
            return
            
        valid_strategies = ["round_robin", "capability_based", "task_based", "custom"]
        if value not in valid_strategies:
            raise ValidationError(
                f"Invalid coordination strategy: {value}. Must be one of: {', '.join(valid_strategies)}"
            )


class WorkerAgentOptionsSchema(AgentOptionsSchema):
    """Schema for worker agent options."""
    
    specialization = fields.String(required=False, allow_none=True)
    capabilities = fields.Dict(keys=fields.String(), values=fields.Integer(), required=False, allow_none=True)
    max_tasks = fields.Integer(required=False, allow_none=True, validate=lambda x: x is None or x > 0)


class AgentConfigSchema(AtlasSchema):
    """Schema for agent configurations."""
    
    type = fields.String(required=True)
    id = fields.String(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    description = fields.String(required=False, allow_none=True)
    options = fields.Dict(required=False, allow_none=True)


# Export schema instances for convenient use
agent_type_schema = AgentTypeSchema()
agent_options_schema = AgentOptionsSchema()
task_specification_schema = TaskSpecificationSchema()
tool_parameter_schema = ToolParameterSchema()
tool_schema_schema = ToolSchemaSchema()
tool_agent_options_schema = ToolAgentOptionsSchema()
task_aware_agent_options_schema = TaskAwareAgentOptionsSchema()
controller_agent_options_schema = ControllerAgentOptionsSchema()
worker_agent_options_schema = WorkerAgentOptionsSchema()
agent_config_schema = AgentConfigSchema()