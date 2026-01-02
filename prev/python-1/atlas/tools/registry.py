"""
Registry for tools that can be used by agents in the Atlas framework.

This module provides a centralized registry for discovering and loading tools,
with automatic registration of built-in tools and the ability to register
custom tools.
"""

import importlib
import inspect
import logging
import os
import pkgutil

from atlas.core.telemetry import traced
from atlas.tools.base import AgentToolkit, Tool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Global registry of available tools.

    This class provides a centralized registry for discovering and managing
    tools available in the Atlas framework. It automatically discovers tools
    in the standard tools directory and allows registering custom tools.
    """

    def __init__(self):
        """Initialize the tool registry."""
        self._tools: dict[str, type[Tool]] = {}
        self._initialized = False

    @traced(name="initialize")
    def initialize(self) -> None:
        """Initialize the registry by discovering standard tools.

        This method discovers all tool classes in the standard tools directory
        and registers them in the registry.
        """
        if self._initialized:
            return

        # Discover standard tools
        self._discover_standard_tools()

        self._initialized = True
        logger.info(f"Tool registry initialized with {len(self._tools)} tools")

    def _discover_standard_tools(self) -> None:
        """Discover and register standard tools from the tools directory."""
        from atlas.tools import standard

        # Get the package directory
        package_dir = os.path.dirname(standard.__file__)

        # Iterate through all modules in the package
        for _, module_name, is_pkg in pkgutil.iter_modules([package_dir]):
            if is_pkg:
                continue

            try:
                # Import the module
                module = importlib.import_module(f"atlas.tools.standard.{module_name}")

                # Iterate through all items in the module
                for name, obj in inspect.getmembers(module):
                    # Check if it's a Tool subclass (but not Tool itself)
                    if inspect.isclass(obj) and issubclass(obj, Tool) and obj is not Tool:
                        # Get tool name
                        tool_name = getattr(obj, "name", None) or obj.__name__

                        # Register the tool
                        self.register_tool_class(obj, override=False)

            except Exception as e:
                logger.error(f"Error loading tools from module {module_name}: {e!s}")

    @traced(name="register_tool_class")
    def register_tool_class(self, tool_class: type[Tool], override: bool = False) -> None:
        """Register a tool class in the registry.

        Args:
            tool_class: The tool class to register.
            override: Whether to override existing tools with the same name.

        Raises:
            ValueError: If a tool with the same name already exists and override is False.
        """
        if not self._initialized:
            self.initialize()

        # Get tool name from class
        tool_name = getattr(tool_class, "name", None) or tool_class.__name__

        # Check for existing tool
        if tool_name in self._tools and not override:
            raise ValueError(f"Tool '{tool_name}' is already registered")

        # Register the tool
        self._tools[tool_name] = tool_class
        logger.info(f"Registered tool class {tool_class.__name__} as '{tool_name}'")

    @traced(name="get_tool_class")
    def get_tool_class(self, name: str) -> type[Tool] | None:
        """Get a tool class by name.

        Args:
            name: The name of the tool class to get.

        Returns:
            The tool class if found, None otherwise.
        """
        if not self._initialized:
            self.initialize()

        return self._tools.get(name)

    @traced(name="list_available_tools")
    def list_available_tools(self) -> list[str]:
        """List all available tool names.

        Returns:
            A list of available tool names.
        """
        if not self._initialized:
            self.initialize()

        return list(self._tools.keys())

    @traced(name="create_tool")
    def create_tool(self, name: str, **kwargs) -> Tool | None:
        """Create a tool instance by name.

        Args:
            name: The name of the tool to create.
            **kwargs: Arguments to pass to the tool constructor.

        Returns:
            A tool instance if the tool class exists, None otherwise.
        """
        if not self._initialized:
            self.initialize()

        tool_class = self.get_tool_class(name)
        if not tool_class:
            return None

        try:
            return tool_class(**kwargs)
        except Exception as e:
            logger.error(f"Error creating tool '{name}': {e!s}")
            return None

    @traced(name="create_toolkit")
    def create_toolkit(self, tool_names: list[str], agent_id: str | None = None) -> AgentToolkit:
        """Create a toolkit with the specified tools.

        Args:
            tool_names: List of tool names to include in the toolkit.
            agent_id: Optional agent ID to grant permissions to.

        Returns:
            An AgentToolkit with the specified tools registered.
        """
        if not self._initialized:
            self.initialize()

        toolkit = AgentToolkit()

        for name in tool_names:
            tool = self.create_tool(name)
            if tool:
                toolkit.register_tool(tool)
                if agent_id:
                    toolkit.grant_permission(agent_id, tool.name)

        return toolkit


# Create a global tool registry instance
_global_registry = ToolRegistry()


def initialize() -> None:
    """Initialize the global tool registry."""
    _global_registry.initialize()


def register_tool_class(tool_class: type[Tool], override: bool = False) -> None:
    """Register a tool class in the global registry.

    Args:
        tool_class: The tool class to register.
        override: Whether to override existing tools with the same name.
    """
    _global_registry.register_tool_class(tool_class, override)


def get_tool_class(name: str) -> type[Tool] | None:
    """Get a tool class by name from the global registry.

    Args:
        name: The name of the tool class to get.

    Returns:
        The tool class if found, None otherwise.
    """
    return _global_registry.get_tool_class(name)


def list_available_tools() -> list[str]:
    """List all available tool names from the global registry.

    Returns:
        A list of available tool names.
    """
    return _global_registry.list_available_tools()


def create_tool(name: str, **kwargs) -> Tool | None:
    """Create a tool instance by name from the global registry.

    Args:
        name: The name of the tool to create.
        **kwargs: Arguments to pass to the tool constructor.

    Returns:
        A tool instance if the tool class exists, None otherwise.
    """
    return _global_registry.create_tool(name, **kwargs)


def create_toolkit(tool_names: list[str], agent_id: str | None = None) -> AgentToolkit:
    """Create a toolkit with the specified tools from the global registry.

    Args:
        tool_names: List of tool names to include in the toolkit.
        agent_id: Optional agent ID to grant permissions to.

    Returns:
        An AgentToolkit with the specified tools registered.
    """
    return _global_registry.create_toolkit(tool_names, agent_id)


def create_toolkit_with_all_tools(agent_id: str | None = None) -> AgentToolkit:
    """Create a toolkit with all available tools.

    Args:
        agent_id: Optional agent ID to grant permissions to.

    Returns:
        An AgentToolkit with all available tools registered.
    """
    tool_names = list_available_tools()
    return create_toolkit(tool_names, agent_id)
