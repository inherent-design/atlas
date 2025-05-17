"""
Agent schemas for Atlas.

This module provides Marshmallow schemas for agent-related structures,
including agent configurations, task specifications, and tool interfaces.

This module extends pure schema definitions with post_load methods that import
implementation classes when needed to avoid circular import issues.
"""

from typing import Any, Dict, List, Optional, Union, cast
from enum import Enum

from marshmallow import post_load, pre_load, ValidationError

from atlas.schemas.base import AtlasSchema
from atlas.schemas.definitions.agents import (
    agent_type_schema as base_agent_type_schema,
    agent_options_schema as base_agent_options_schema,
    task_specification_schema as base_task_specification_schema,
    tool_parameter_schema as base_tool_parameter_schema,
    tool_schema_schema as base_tool_schema_schema,
    tool_agent_options_schema as base_tool_agent_options_schema,
    task_aware_agent_options_schema as base_task_aware_agent_options_schema,
    controller_agent_options_schema as base_controller_agent_options_schema,
    worker_agent_options_schema as base_worker_agent_options_schema,
    agent_config_schema as base_agent_config_schema
)


class AgentTypeSchema(base_agent_type_schema.__class__):
    """Schema for agent types with implementation conversion."""
    pass


class AgentOptionsSchema(base_agent_options_schema.__class__):
    """Schema for agent options with implementation conversion."""
    pass


class TaskSpecificationSchema(base_task_specification_schema.__class__):
    """Schema for task specifications with implementation conversion."""
    pass


class ToolParameterSchema(base_tool_parameter_schema.__class__):
    """Schema for tool parameters with implementation conversion."""
    pass


class ToolSchemaSchema(base_tool_schema_schema.__class__):
    """Schema for tool schemas with implementation conversion."""
    pass


class ToolAgentOptionsSchema(base_tool_agent_options_schema.__class__):
    """Schema for tool agent options with implementation conversion."""
    pass


class TaskAwareAgentOptionsSchema(base_task_aware_agent_options_schema.__class__):
    """Schema for task-aware agent options with implementation conversion."""
    pass


class ControllerAgentOptionsSchema(base_controller_agent_options_schema.__class__):
    """Schema for controller agent options with implementation conversion."""
    pass


class WorkerAgentOptionsSchema(base_worker_agent_options_schema.__class__):
    """Schema for worker agent options with implementation conversion."""
    pass


class AgentConfigSchema(base_agent_config_schema.__class__):
    """Schema for agent configurations with implementation conversion."""
    
    @pre_load
    def process_options(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Pre-process options during deserialization.
        
        Args:
            data: The data to load.
            **kwargs: Additional arguments.
            
        Returns:
            Processed data dictionary.
        """
        # Make a copy to avoid modifying the input
        result = {**data}
        
        # Process options field based on agent type
        if "type" in result and "options" in result:
            agent_type = result["type"]
            options = result["options"]
            
            if agent_type == "tool" and isinstance(options, dict):
                result["options"] = ToolAgentOptionsSchema().load(options)
            elif agent_type == "task_aware" and isinstance(options, dict):
                result["options"] = TaskAwareAgentOptionsSchema().load(options)
            elif agent_type == "controller" and isinstance(options, dict):
                result["options"] = ControllerAgentOptionsSchema().load(options)
            elif agent_type == "worker" and isinstance(options, dict):
                result["options"] = WorkerAgentOptionsSchema().load(options)
        
        return result
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Union[Any, Dict[str, Any]]:
        """Convert loaded data into an agent object if possible.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            An agent object or the original data dictionary.
        """
        # To avoid circular imports, we'll make this a lightweight proxy
        # and just return the data during validation
        if kwargs.get("return_dict", False):
            return data
            
        # We're not actually creating objects here to avoid circular imports
        return data
    

# Create schema instances
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