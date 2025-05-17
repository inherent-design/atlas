"""
Base tool interface and toolkit for Atlas agents.

This module defines the foundational components for tools that agents can use
to interact with external systems and perform specialized tasks.
"""

import abc
import json
import inspect
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Callable, Type, Union, TypeVar, Set, get_type_hints, Collection, cast, Generic
from typing_extensions import Protocol
import logging

from atlas.core.telemetry import traced, TracedClass
from atlas.core.types import (
    ToolSchemaDict, ToolResultDict, ToolDefinitionDict, ToolExecutionDict
)


logger = logging.getLogger(__name__)


@dataclass
class ToolSchema:
    """Schema for a tool, describing its inputs and outputs."""
    
    name: str
    """The name of the tool."""
    
    description: str
    """A description of what the tool does."""
    
    parameters: Dict[str, Any]
    """JSON Schema for the tool's parameters."""
    
    returns: Optional[Dict[str, Any]] = None
    """Optional JSON Schema for the tool's return value."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary format.
        
        Returns:
            The schema as a dictionary.
        """
        result = {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
        
        if self.returns:
            result["returns"] = self.returns
            
        return result
    
    @classmethod
    def from_function(cls, func: Callable, name: Optional[str] = None, description: Optional[str] = None) -> 'ToolSchema':
        """Create a schema from a function's signature and docstring.
        
        Args:
            func: The function to create a schema for.
            name: Optional custom name for the tool (defaults to function name).
            description: Optional custom description (defaults to function docstring).
            
        Returns:
            A ToolSchema for the function.
        """
        # Get function metadata
        func_name = name or func.__name__
        func_doc = description or inspect.getdoc(func) or "No description available"
        
        # Get parameter information
        signature = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        # Build parameters schema
        parameters: Dict[str, Any] = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param_name, param in signature.parameters.items():
            # Skip self for methods
            if param_name == 'self':
                continue
                
            # Get parameter type and add to schema
            param_type = type_hints.get(param_name, Any)
            param_schema = cls._type_to_json_schema(param_type)
            
            # Add parameter to properties
            parameters["properties"][param_name] = param_schema
            
            # Check if parameter is required
            if param.default is inspect.Parameter.empty:
                parameters["required"].append(param_name)
        
        # Build return schema if available
        returns = None
        if 'return' in type_hints:
            return_type = type_hints['return']
            if return_type is not None and return_type is not type(None):
                returns = cls._type_to_json_schema(return_type)
        
        return cls(
            name=func_name,
            description=func_doc,
            parameters=parameters,
            returns=returns
        )
    
    @staticmethod
    def _type_to_json_schema(type_hint: Any) -> Dict[str, Any]:
        """Convert a Python type hint to a JSON Schema type.
        
        Args:
            type_hint: The Python type hint.
            
        Returns:
            A JSON Schema representation of the type.
        """
        # Handle basic types
        if type_hint is str:
            return {"type": "string"}
        elif type_hint is int:
            return {"type": "integer"}
        elif type_hint is float:
            return {"type": "number"}
        elif type_hint is bool:
            return {"type": "boolean"}
        elif type_hint is list or type_hint is List:
            return {"type": "array"}
        elif type_hint is dict or type_hint is Dict:
            return {"type": "object"}
        elif hasattr(type_hint, "__origin__"):
            # Handle generics like List[str], Dict[str, int], etc.
            origin = type_hint.__origin__
            
            # Handle list-like types including Collection
            if origin is list or origin is List or (hasattr(Collection, "__origin__") and origin is Collection.__origin__):
                item_type = type_hint.__args__[0] if hasattr(type_hint, "__args__") else Any
                return {
                    "type": "array",
                    "items": ToolSchema._type_to_json_schema(item_type)
                }
            elif origin is dict or origin is Dict:
                value_type = type_hint.__args__[1] if len(getattr(type_hint, "__args__", [])) > 1 else Any
                return {
                    "type": "object",
                    "additionalProperties": ToolSchema._type_to_json_schema(value_type)
                }
            elif type_hint.__origin__ is Union:
                # Handle Optional[T] which is Union[T, None]
                if len(type_hint.__args__) == 2 and type(None) in type_hint.__args__:
                    # Get the non-None type
                    real_type = next(arg for arg in type_hint.__args__ if arg is not type(None))
                    schema = ToolSchema._type_to_json_schema(real_type)
                    # Make it nullable
                    if isinstance(schema, dict) and "type" in schema:
                        if isinstance(schema["type"], list):
                            if "null" not in schema["type"]:
                                schema["type"].append("null")
                        else:
                            schema["type"] = [schema["type"], "null"]
                    return schema
                else:
                    # Handle other unions with anyOf
                    return {
                        "anyOf": [ToolSchema._type_to_json_schema(arg) for arg in type_hint.__args__]
                    }
        
        # Default to any type for complex/unknown types
        return {}


# Type variable for tool result
R = TypeVar('R')

class Tool(TracedClass, abc.ABC, Generic[R]):
    """Base class for all tools usable by agents."""
    
    def __init__(self, name: Optional[str] = None, description: Optional[str] = None):
        """Initialize a tool.
        
        Args:
            name: Optional custom name for the tool.
            description: Optional custom description.
        """
        self._name = name or self.__class__.__name__
        self._description = description
    
    @property
    def name(self) -> str:
        """Get the name of the tool.
        
        Returns:
            The tool name.
        """
        return self._name
    
    @property
    def description(self) -> str:
        """Get the description of the tool.
        
        Returns:
            The tool description.
        """
        if self._description:
            return self._description
        
        # Fall back to class docstring
        return inspect.getdoc(self) or "No description available"
    
    @property
    @abc.abstractmethod
    def schema(self) -> ToolSchema:
        """Get the schema for this tool.
        
        Returns:
            A ToolSchema describing the tool's inputs and outputs.
        """
        pass
    
    @traced(name="execute")
    @abc.abstractmethod
    def execute(self, **kwargs) -> R:
        """Execute the tool with the given arguments.
        
        Args:
            **kwargs: Arguments for the tool.
            
        Returns:
            The result of executing the tool.
        """
        pass
    
    def to_dict(self) -> ToolDefinitionDict:
        """Convert the tool to a dictionary representation.
        
        Returns:
            A dictionary representation of the tool.
        """
        # Cast to ToolSchemaDict since we know the structure is compatible
        schema_dict = cast(ToolSchemaDict, self.schema.to_dict())
        return {
            "name": self.name,
            "description": self.description,
            "schema": schema_dict
        }
    
    @traced(name="validate_args")
    def validate_args(self, **kwargs) -> bool:
        """Validate the arguments against the tool's schema.
        
        Args:
            **kwargs: Arguments to validate.
            
        Returns:
            True if arguments are valid, False otherwise.
        """
        # Check required parameters
        required = self.schema.parameters.get("required", [])
        for param in required:
            if param not in kwargs:
                logger.error(f"Missing required parameter '{param}' for tool '{self.name}'")
                return False
        
        # For now, we just check presence of required parameters
        # A more thorough validation would check types against the schema
        return True


class FunctionTool(Tool[R]):
    """A tool that wraps a Python function."""
    
    def __init__(self, func: Callable[..., R], name: Optional[str] = None, description: Optional[str] = None):
        """Initialize a function tool.
        
        Args:
            func: The function to wrap.
            name: Optional custom name for the tool.
            description: Optional custom description.
        """
        super().__init__(name or func.__name__, description)
        self._func = func
        self._schema = ToolSchema.from_function(func, self._name, self._description)
    
    @property
    def schema(self) -> ToolSchema:
        """Get the schema for this tool.
        
        Returns:
            A ToolSchema describing the tool's inputs and outputs.
        """
        return self._schema
    
    @traced(name="execute")
    def execute(self, **kwargs) -> R:
        """Execute the wrapped function with the given arguments.
        
        Args:
            **kwargs: Arguments to pass to the function.
            
        Returns:
            The result of the function call.
        """
        if not self.validate_args(**kwargs):
            raise ValueError(f"Invalid arguments for tool '{self.name}'")
        
        return self._func(**kwargs)


class AgentToolkit(TracedClass):
    """Registry for tools that agents can use."""
    
    def __init__(self):
        """Initialize an agent toolkit."""
        self.tools: Dict[str, Tool] = {}
        self.permissions: Dict[str, Set[str]] = {}
    
    @traced(name="register_tool")
    def register_tool(self, tool: Union[Tool, Callable]) -> str:
        """Register a tool in the toolkit.
        
        Args:
            tool: The tool to register (either a Tool instance or a function to wrap).
            
        Returns:
            The name of the registered tool.
            
        Raises:
            ValueError: If a tool with the same name is already registered.
        """
        # Wrap functions in a FunctionTool
        if callable(tool) and not isinstance(tool, Tool):
            tool = FunctionTool(tool)
        
        # Check if the tool name is already taken
        if tool.name in self.tools:
            raise ValueError(f"A tool with name '{tool.name}' is already registered")
        
        # Register the tool
        self.tools[tool.name] = tool
        logger.info(f"Registered tool '{tool.name}'")
        
        return tool.name
    
    @traced(name="get_tool")
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name.
        
        Args:
            name: The name of the tool to get.
            
        Returns:
            The tool if found, None otherwise.
        """
        return self.tools.get(name)
    
    @traced(name="grant_permission")
    def grant_permission(self, agent_id: str, tool_name: str) -> None:
        """Grant an agent permission to use a specific tool.
        
        Args:
            agent_id: The ID of the agent.
            tool_name: The name of the tool.
            
        Raises:
            ValueError: If the tool does not exist.
        """
        if tool_name != "*" and tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' does not exist")
        
        if agent_id not in self.permissions:
            self.permissions[agent_id] = set()
        
        self.permissions[agent_id].add(tool_name)
        logger.info(f"Granted permission for tool '{tool_name}' to agent '{agent_id}'")
    
    @traced(name="grant_all_permissions")
    def grant_all_permissions(self, agent_id: str) -> None:
        """Grant an agent permission to use all tools.
        
        Args:
            agent_id: The ID of the agent.
        """
        self.grant_permission(agent_id, "*")
    
    @traced(name="revoke_permission")
    def revoke_permission(self, agent_id: str, tool_name: str) -> None:
        """Revoke an agent's permission to use a specific tool.
        
        Args:
            agent_id: The ID of the agent.
            tool_name: The name of the tool.
        """
        if agent_id in self.permissions and tool_name in self.permissions[agent_id]:
            self.permissions[agent_id].remove(tool_name)
            logger.info(f"Revoked permission for tool '{tool_name}' from agent '{agent_id}'")
    
    @traced(name="has_permission")
    def has_permission(self, agent_id: str, tool_name: str) -> bool:
        """Check if an agent has permission to use a specific tool.
        
        Args:
            agent_id: The ID of the agent.
            tool_name: The name of the tool.
            
        Returns:
            True if the agent has permission, False otherwise.
        """
        if agent_id not in self.permissions:
            return False
        
        return "*" in self.permissions[agent_id] or tool_name in self.permissions[agent_id]
    
    @traced(name="get_accessible_tools")
    def get_accessible_tools(self, agent_id: str) -> Dict[str, Tool]:
        """Get all tools that an agent has permission to use.
        
        Args:
            agent_id: The ID of the agent.
            
        Returns:
            A dictionary mapping tool names to Tool instances.
        """
        if agent_id not in self.permissions:
            return {}
        
        if "*" in self.permissions[agent_id]:
            return self.tools.copy()
        
        return {
            name: tool 
            for name, tool in self.tools.items() 
            if name in self.permissions[agent_id]
        }
    
    @traced(name="get_tool_descriptions")
    def get_tool_descriptions(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get descriptions of all tools an agent can access.
        
        Args:
            agent_id: The ID of the agent.
            
        Returns:
            A list of tool schemas in dictionary format.
        """
        accessible_tools = self.get_accessible_tools(agent_id)
        return [tool.schema.to_dict() for tool in accessible_tools.values()]
    
    @traced(name="execute_tool")
    def execute_tool(self, agent_id: str, tool_name: str, args: Dict[str, Any]) -> Any:
        """Execute a tool if the agent has permission.
        
        Args:
            agent_id: The ID of the agent requesting execution.
            tool_name: The name of the tool to execute.
            args: Arguments for the tool.
            
        Returns:
            The result of the tool execution.
            
        Raises:
            ValueError: If the tool does not exist.
            PermissionError: If the agent doesn't have permission to use the tool.
        """
        # Check if tool exists
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' does not exist")
        
        # Check permission
        if not self.has_permission(agent_id, tool_name):
            raise PermissionError(f"Agent '{agent_id}' doesn't have permission to use tool '{tool_name}'")
        
        # Log the execution
        logger.info(f"Executing tool '{tool_name}' for agent '{agent_id}'")
        
        # Execute the tool
        return tool.execute(**args)