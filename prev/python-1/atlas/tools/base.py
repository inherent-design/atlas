"""
Base tool interface and toolkit for Atlas agents.

This module defines the foundational components for tools that agents can use
to interact with external systems and perform specialized tasks.
"""

import abc
import inspect
import logging
import time
from collections.abc import Callable, Collection
from dataclasses import dataclass, field
from typing import (
    Any,
    Generic,
    TypeVar,
    Union,
    cast,
    get_type_hints,
)

from atlas.core.telemetry import TracedClass, traced
from atlas.core.types import ToolDefinitionDict, ToolSchemaDict

# Import schemas - with conditional import to avoid circular references
try:
    from atlas.schemas.tools import (
        ToolCallSchema,
        ToolDefinitionSchema,
        ToolPermissionSchema,
        ToolResultSchema,
        ToolSchemaDefinitionSchema,
    )

    SCHEMAS_AVAILABLE = True
except ImportError:
    SCHEMAS_AVAILABLE = False


logger = logging.getLogger(__name__)


@dataclass
class ToolSchema:
    """Schema for a tool, describing its inputs and outputs."""

    name: str
    """The name of the tool."""

    description: str
    """A description of what the tool does."""

    parameters: dict[str, Any]
    """JSON Schema for the tool's parameters."""

    returns: dict[str, Any] | None = None
    """Optional JSON Schema for the tool's return value."""

    def to_dict(self) -> dict[str, Any]:
        """Convert schema to dictionary format.

        Returns:
            The schema as a dictionary.

        Raises:
            ValidationError: If schema validation is enabled and validation fails.
        """
        result = {"name": self.name, "description": self.description, "parameters": self.parameters}

        if self.returns:
            result["returns"] = self.returns

        # Validate the schema if schemas are available
        if SCHEMAS_AVAILABLE:
            try:
                # Use the schema to validate
                schema = ToolSchemaDefinitionSchema()
                validated_result = schema.load(result)

                # Update result with validated data
                # This ensures any transformations from the validation are applied
                result = validated_result

                logger.debug(f"Tool schema validation passed for '{self.name}'")
            except Exception as e:
                logger.warning(f"Tool schema validation failed for '{self.name}': {e!s}")
                # We log but don't raise to maintain backward compatibility
                # In a future version, we could make this stricter by raising the exception

        return result

    @classmethod
    def from_function(
        cls, func: Callable, name: str | None = None, description: str | None = None
    ) -> "ToolSchema":
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
        parameters: dict[str, Any] = {"type": "object", "properties": {}, "required": []}

        for param_name, param in signature.parameters.items():
            # Skip self for methods
            if param_name == "self":
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
        if "return" in type_hints:
            return_type = type_hints["return"]
            if return_type is not None and return_type is not type(None):
                returns = cls._type_to_json_schema(return_type)

        return cls(name=func_name, description=func_doc, parameters=parameters, returns=returns)

    @staticmethod
    def _type_to_json_schema(type_hint: Any) -> dict[str, Any]:
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
        elif type_hint is list or type_hint is list:
            return {"type": "array"}
        elif type_hint is dict or type_hint is dict:
            return {"type": "object"}
        elif hasattr(type_hint, "__origin__"):
            # Handle generics like List[str], Dict[str, int], etc.
            origin = type_hint.__origin__

            # Handle list-like types including Collection
            if (
                origin is list
                or origin is list
                or (hasattr(Collection, "__origin__") and origin is Collection.__origin__)
            ):
                item_type = type_hint.__args__[0] if hasattr(type_hint, "__args__") else Any
                return {"type": "array", "items": ToolSchema._type_to_json_schema(item_type)}
            elif origin is dict or origin is dict:
                value_type = (
                    type_hint.__args__[1] if len(getattr(type_hint, "__args__", [])) > 1 else Any
                )
                return {
                    "type": "object",
                    "additionalProperties": ToolSchema._type_to_json_schema(value_type),
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
                        "anyOf": [
                            ToolSchema._type_to_json_schema(arg) for arg in type_hint.__args__
                        ]
                    }

        # Default to any type for complex/unknown types
        return {}


# Type variable for tool result
R = TypeVar("R")


class Tool(TracedClass, abc.ABC, Generic[R]):
    """Base class for all tools usable by agents."""

    def __init__(self, name: str | None = None, description: str | None = None):
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

        Raises:
            ValidationError: If schema validation is enabled and validation fails.
        """
        # Cast to ToolSchemaDict since we know the structure is compatible
        schema_dict = cast(ToolSchemaDict, self.schema.to_dict())

        result = {"name": self.name, "description": self.description, "schema": schema_dict}

        # Validate the tool definition if schemas are available
        if SCHEMAS_AVAILABLE:
            try:
                # Use the schema to validate
                schema = ToolDefinitionSchema()
                validated_result = schema.load(result)

                # Update result with validated data
                # This ensures any transformations from the validation are applied
                result = validated_result

                logger.debug(f"Tool definition validation passed for '{self.name}'")
            except Exception as e:
                logger.warning(f"Tool definition validation failed for '{self.name}': {e!s}")
                # We log but don't raise to maintain backward compatibility
                # In a future version, we could make this stricter by raising the exception

        return result

    @traced(name="validate_args")
    def validate_args(self, **kwargs) -> bool:
        """Validate the arguments against the tool's schema.

        Args:
            **kwargs: Arguments to validate.

        Returns:
            True if arguments are valid, False otherwise.

        Note:
            This performs basic validation of required parameters and type checking.
            For more complex validation, consider using a full JSON Schema validator.
        """
        # Get schema parameters
        parameters = self.schema.parameters
        required = parameters.get("required", [])
        properties = parameters.get("properties", {})

        # Use schema validation if available for more comprehensive validation
        if SCHEMAS_AVAILABLE:
            try:
                from atlas.schemas.tools import ToolCallSchema

                # Create a tool call object for validation
                tool_call = {"name": self.name, "arguments": kwargs}

                # Validate using schema
                schema = ToolCallSchema()
                schema.load(tool_call)

                logger.debug(f"Schema validation passed for tool '{self.name}' arguments")
            except Exception as e:
                logger.error(f"Schema validation failed for tool '{self.name}' arguments: {e!s}")
                return False

        # Continue with basic validation for better error messages
        # Check required parameters are present
        for param in required:
            if param not in kwargs:
                logger.error(f"Missing required parameter '{param}' for tool '{self.name}'")
                return False

        # Validate parameter types
        for param_name, param_value in kwargs.items():
            if param_name not in properties:
                logger.warning(f"Unknown parameter '{param_name}' for tool '{self.name}'")
                continue

            param_schema = properties[param_name]
            param_type = param_schema.get("type")

            # Skip validation if no type is specified
            if not param_type:
                continue

            # Check parameter type
            if param_type == "string" and not isinstance(param_value, str):
                logger.error(f"Parameter '{param_name}' for tool '{self.name}' should be a string")
                return False
            elif param_type == "number" and not isinstance(param_value, (int, float)):
                logger.error(f"Parameter '{param_name}' for tool '{self.name}' should be a number")
                return False
            elif param_type == "integer" and not isinstance(param_value, int):
                logger.error(
                    f"Parameter '{param_name}' for tool '{self.name}' should be an integer"
                )
                return False
            elif param_type == "boolean" and not isinstance(param_value, bool):
                logger.error(f"Parameter '{param_name}' for tool '{self.name}' should be a boolean")
                return False
            elif param_type == "array" and not isinstance(param_value, list):
                logger.error(f"Parameter '{param_name}' for tool '{self.name}' should be an array")
                return False
            elif param_type == "object" and not isinstance(param_value, dict):
                logger.error(f"Parameter '{param_name}' for tool '{self.name}' should be an object")
                return False

            # Additional validation for enums if specified
            if "enum" in param_schema and param_value not in param_schema["enum"]:
                logger.error(
                    f"Parameter '{param_name}' for tool '{self.name}' must be one of: {', '.join(map(str, param_schema['enum']))}"
                )
                return False

            # Additional validation for numeric ranges
            if param_type in ("number", "integer"):
                if "minimum" in param_schema and param_value < param_schema["minimum"]:
                    logger.error(
                        f"Parameter '{param_name}' for tool '{self.name}' must be greater than or equal to {param_schema['minimum']}"
                    )
                    return False

                if "maximum" in param_schema and param_value > param_schema["maximum"]:
                    logger.error(
                        f"Parameter '{param_name}' for tool '{self.name}' must be less than or equal to {param_schema['maximum']}"
                    )
                    return False

        return True


class FunctionTool(Tool[R]):
    """A tool that wraps a Python function."""

    def __init__(
        self, func: Callable[..., R], name: str | None = None, description: str | None = None
    ):
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


@dataclass
class ToolPermission:
    """Permission for an agent to use a tool."""

    agent_id: str
    """The ID of the agent."""

    tool_name: str
    """The name of the tool or '*' for all tools."""

    granted_at: float = field(default_factory=lambda: time.time())
    """Timestamp when permission was granted."""

    granted_by: str | None = None
    """ID of the agent who granted this permission."""

    scope: str = "execute"
    """Scope of the permission (e.g., 'execute', 'read', 'manage')."""


class AgentToolkit(TracedClass):
    """Registry for tools that agents can use."""

    def __init__(self):
        """Initialize an agent toolkit."""
        self.tools: dict[str, Tool] = {}
        self.permissions: dict[str, set[str]] = {}
        # Store detailed permission records
        self._permission_records: list[ToolPermission] = []

    @traced(name="register_tool")
    def register_tool(self, tool: Tool | Callable) -> str:
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
    def get_tool(self, name: str) -> Tool | None:
        """Get a tool by name.

        Args:
            name: The name of the tool to get.

        Returns:
            The tool if found, None otherwise.
        """
        return self.tools.get(name)

    @traced(name="grant_permission")
    def grant_permission(
        self,
        agent_id: str,
        tool_name: str,
        granted_by: str | None = None,
        scope: str = "execute",
    ) -> None:
        """Grant an agent permission to use a specific tool.

        Args:
            agent_id: The ID of the agent.
            tool_name: The name of the tool.
            granted_by: Optional ID of agent granting the permission.
            scope: Scope of the permission (e.g., 'execute', 'read', 'manage').

        Raises:
            ValueError: If the tool does not exist.
        """
        if tool_name != "*" and tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' does not exist")

        if agent_id not in self.permissions:
            self.permissions[agent_id] = set()

        self.permissions[agent_id].add(tool_name)

        # Record detailed permission
        permission = ToolPermission(
            agent_id=agent_id, tool_name=tool_name, granted_by=granted_by, scope=scope
        )
        self._permission_records.append(permission)

        logger.info(f"Granted permission for tool '{tool_name}' to agent '{agent_id}'")

    @traced(name="grant_all_permissions")
    def grant_all_permissions(
        self, agent_id: str, granted_by: str | None = None, scope: str = "execute"
    ) -> None:
        """Grant an agent permission to use all tools.

        Args:
            agent_id: The ID of the agent.
            granted_by: Optional ID of agent granting the permission.
            scope: Scope of the permission (e.g., 'execute', 'read', 'manage').
        """
        self.grant_permission(agent_id, "*", granted_by, scope)

    @traced(name="revoke_permission")
    def revoke_permission(self, agent_id: str, tool_name: str) -> None:
        """Revoke an agent's permission to use a specific tool.

        Args:
            agent_id: The ID of the agent.
            tool_name: The name of the tool.
        """
        if agent_id in self.permissions and tool_name in self.permissions[agent_id]:
            self.permissions[agent_id].remove(tool_name)

            # Filter out revoked permissions from detailed records
            self._permission_records = [
                p
                for p in self._permission_records
                if not (p.agent_id == agent_id and p.tool_name == tool_name)
            ]

            logger.info(f"Revoked permission for tool '{tool_name}' from agent '{agent_id}'")

    @traced(name="has_permission")
    def has_permission(self, agent_id: str, tool_name: str, scope: str = "execute") -> bool:
        """Check if an agent has permission to use a specific tool.

        Args:
            agent_id: The ID of the agent.
            tool_name: The name of the tool.
            scope: Scope of the permission to check.

        Returns:
            True if the agent has permission, False otherwise.
        """
        if agent_id not in self.permissions:
            return False

        # First check for wildcard permission
        has_wildcard = any(
            p.agent_id == agent_id and p.tool_name == "*" and p.scope == scope
            for p in self._permission_records
        )

        if has_wildcard:
            return True

        # Then check for specific tool permission
        has_specific = "*" in self.permissions[agent_id] or tool_name in self.permissions[agent_id]

        # Verify the scope matches
        if has_specific:
            matching_records = [
                p
                for p in self._permission_records
                if p.agent_id == agent_id and (p.tool_name == tool_name or p.tool_name == "*")
            ]

            for record in matching_records:
                if record.scope == scope:
                    return True

        return False

    @traced(name="get_accessible_tools")
    def get_accessible_tools(self, agent_id: str, scope: str = "execute") -> dict[str, Tool]:
        """Get all tools that an agent has permission to use.

        Args:
            agent_id: The ID of the agent.
            scope: Scope of the permission to check.

        Returns:
            A dictionary mapping tool names to Tool instances.
        """
        if agent_id not in self.permissions:
            return {}

        # Get all permissions for this agent
        agent_permissions = self.permissions[agent_id]

        # If wildcard permission, return all tools
        if "*" in agent_permissions:
            # Verify scope for wildcard
            wildcard_allowed = any(
                p.agent_id == agent_id and p.tool_name == "*" and p.scope == scope
                for p in self._permission_records
            )

            if wildcard_allowed:
                return self.tools.copy()

        # Return only specifically permitted tools with matching scope
        accessible_tools = {}
        for name, tool in self.tools.items():
            if name in agent_permissions:
                # Verify the scope
                allowed = any(
                    p.agent_id == agent_id and p.tool_name == name and p.scope == scope
                    for p in self._permission_records
                )

                if allowed:
                    accessible_tools[name] = tool

        return accessible_tools

    @traced(name="get_permission_history")
    def get_permission_history(self, agent_id: str | None = None) -> list[dict[str, Any]]:
        """Get the permission history for an agent or all agents.

        Args:
            agent_id: Optional ID of the agent to get history for.

        Returns:
            A list of permission records.
        """
        if agent_id:
            # Filter by agent ID
            records = [
                {
                    "agent_id": p.agent_id,
                    "tool_name": p.tool_name,
                    "granted_at": p.granted_at,
                    "granted_by": p.granted_by,
                    "scope": p.scope,
                }
                for p in self._permission_records
                if p.agent_id == agent_id
            ]
        else:
            # Get all records
            records = [
                {
                    "agent_id": p.agent_id,
                    "tool_name": p.tool_name,
                    "granted_at": p.granted_at,
                    "granted_by": p.granted_by,
                    "scope": p.scope,
                }
                for p in self._permission_records
            ]

        return records

    @traced(name="get_tool_descriptions")
    def get_tool_descriptions(self, agent_id: str) -> list[dict[str, Any]]:
        """Get descriptions of all tools an agent can access.

        Args:
            agent_id: The ID of the agent.

        Returns:
            A list of tool schemas in dictionary format.
        """
        accessible_tools = self.get_accessible_tools(agent_id)
        return [tool.schema.to_dict() for tool in accessible_tools.values()]

    @traced(name="execute_tool")
    def execute_tool(self, agent_id: str, tool_name: str, args: dict[str, Any]) -> Any:
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
            ValueError: If the arguments are invalid.
        """
        # Check if tool exists
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' does not exist")

        # Check permission
        if not self.has_permission(agent_id, tool_name):
            raise PermissionError(
                f"Agent '{agent_id}' doesn't have permission to use tool '{tool_name}'"
            )

        # Validate tool call using schema validation if available
        if SCHEMAS_AVAILABLE:
            try:
                # Create a tool call object for validation
                tool_call = {"name": tool_name, "arguments": args}

                # Validate the tool call
                schema = ToolCallSchema()
                schema.load(tool_call)
            except Exception as e:
                logger.error(f"Tool call validation failed: {e!s}")
                raise ValueError(f"Invalid tool call format: {e!s}")

        # Validate arguments against tool's schema
        if not tool.validate_args(**args):
            raise ValueError(f"Invalid arguments for tool '{tool_name}'")

        # Validate the arguments using schema validation if available
        if SCHEMAS_AVAILABLE:
            try:
                from atlas.schemas.tools import ToolExecutionSchema

                # Create an execution object for validation
                execution = {
                    "agent_id": agent_id,
                    "tool_name": tool_name,
                    "arguments": args,
                    "request_id": args.get("id"),
                }

                # Validate the execution
                schema = ToolExecutionSchema()
                validated_execution = schema.load(execution)
                logger.debug(f"Tool execution validation passed for '{tool_name}'")

                # Update args if needed (for example, if schema transformation occurred)
                args = validated_execution.get("arguments", args)
            except Exception as e:
                logger.error(f"Tool execution validation failed: {e!s}")
                raise ValueError(f"Schema validation failed for tool '{tool_name}': {e!s}")

        # Log the execution
        logger.info(f"Executing tool '{tool_name}' for agent '{agent_id}'")

        # Execute the tool with validated arguments
        result = tool.execute(**args)

        # Validate result if schema validation is available
        if SCHEMAS_AVAILABLE:
            try:
                # Create a tool result object for validation
                tool_result = {"name": tool_name, "result": result, "status": "success"}

                # Validate the result
                schema = ToolResultSchema()
                schema.load(tool_result)
            except Exception as e:
                logger.warning(f"Tool result validation failed: {e!s}")
                # We don't raise an exception here to avoid breaking existing code

        return result
