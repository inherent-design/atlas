"""
Agent registry for Atlas.

This module provides a registry system for Atlas agents with dynamic discovery
and instantiation capabilities.
"""

import logging
import importlib
import inspect
from typing import Dict, List, Type, Any, Optional, Set, Callable, TypeVar, cast

from atlas.core.telemetry import traced, TracedClass
from atlas.agents.base import AtlasAgent

logger = logging.getLogger(__name__)

# Type variable for agent classes
T = TypeVar("T", bound=AtlasAgent)

# Registry of agent implementations
_AGENT_REGISTRY: Dict[str, str] = {
    "atlas": "atlas.agents.base.AtlasAgent",
    "controller": "atlas.agents.controller.ControllerAgent",
    "worker": "atlas.agents.worker.WorkerAgent",
    "task_aware": "atlas.agents.specialized.task_aware_agent.TaskAwareAgent",
}

# Registry of agent constructors
_AGENT_CONSTRUCTORS: Dict[str, Callable[..., AtlasAgent]] = {}

# Cache for agent class objects
_AGENT_CLASSES: Dict[str, Type[AtlasAgent]] = {}


@traced(name="register_agent")
def register_agent(agent_name: str, class_path: str) -> None:
    """Register a new agent implementation.

    Args:
        agent_name: The name of the agent.
        class_path: The import path to the agent class.
    """
    global _AGENT_REGISTRY
    _AGENT_REGISTRY[agent_name] = class_path
    logger.debug(f"Registered agent '{agent_name}' with class path '{class_path}'")

    # Invalidate cached classes and constructors
    if agent_name in _AGENT_CLASSES:
        del _AGENT_CLASSES[agent_name]
    if agent_name in _AGENT_CONSTRUCTORS:
        del _AGENT_CONSTRUCTORS[agent_name]


@traced(name="register_agent_class")
def register_agent_class(agent_name: str, agent_class: Type[AtlasAgent]) -> None:
    """Register a new agent class directly.

    Args:
        agent_name: The name of the agent.
        agent_class: The agent class.
    """
    # Add to cache directly
    global _AGENT_CLASSES
    _AGENT_CLASSES[agent_name] = agent_class

    # Add to registry
    module_name = agent_class.__module__
    class_name = agent_class.__name__
    class_path = f"{module_name}.{class_name}"
    register_agent(agent_name, class_path)


@traced(name="register_agent_constructor")
def register_agent_constructor(
    agent_name: str, constructor: Callable[..., AtlasAgent]
) -> None:
    """Register a constructor function for an agent.

    Args:
        agent_name: The name of the agent.
        constructor: A function that constructs an agent instance.
    """
    global _AGENT_CONSTRUCTORS
    _AGENT_CONSTRUCTORS[agent_name] = constructor
    logger.debug(f"Registered constructor for agent '{agent_name}'")


@traced(name="get_agent_class")
def get_agent_class(agent_name: str) -> Type[AtlasAgent]:
    """Get the agent class for a given agent name.

    Args:
        agent_name: The name of the agent.

    Returns:
        The agent class.

    Raises:
        ValueError: If the agent is not supported or the class cannot be loaded.
    """
    # Check cache first
    if agent_name in _AGENT_CLASSES:
        return _AGENT_CLASSES[agent_name]

    if agent_name not in _AGENT_REGISTRY:
        raise ValueError(f"Unsupported agent: {agent_name}")

    # Get agent class path
    agent_class_path = _AGENT_REGISTRY[agent_name]

    # Split into module path and class name
    module_path, class_name = agent_class_path.rsplit(".", 1)

    try:
        # Dynamically import the module
        module = importlib.import_module(module_path)

        # Get the agent class
        agent_class = getattr(module, class_name)

        # Verify it's an AtlasAgent subclass
        if not issubclass(agent_class, AtlasAgent):
            raise ValueError(f"Class {class_name} is not a subclass of AtlasAgent")

        # Cache the class
        _AGENT_CLASSES[agent_name] = agent_class

        return agent_class

    except ImportError as e:
        raise ValueError(f"Failed to import agent module for {agent_name}: {e}")
    except AttributeError as e:
        raise ValueError(f"Failed to find agent class for {agent_name}: {e}")
    except Exception as e:
        raise ValueError(f"Error loading agent class for {agent_name}: {e}")


@traced(name="create_agent")
def create_agent(
    agent_name: str = "atlas",
    agent_type: Optional[Type[T]] = None,
    **kwargs: Any,
) -> T:
    """Create an agent instance.

    Args:
        agent_name: Name of the agent to create.
        agent_type: Optional type hint for the agent class to help with type checking.
        **kwargs: Additional agent-specific parameters.

    Returns:
        Agent instance of the specified type.

    Raises:
        ValueError: If the agent is not supported or required configuration is missing.
    """
    # Check for custom constructor first
    if agent_name in _AGENT_CONSTRUCTORS:
        agent = _AGENT_CONSTRUCTORS[agent_name](**kwargs)
        logger.debug(f"Created agent '{agent_name}' using custom constructor")

        # Verify type if requested
        if agent_type and not isinstance(agent, agent_type):
            raise ValueError(
                f"Custom constructor for '{agent_name}' returned {type(agent)}, expected {agent_type}"
            )

        return cast(T, agent)

    # Get the agent class
    agent_class = get_agent_class(agent_name)

    # Verify type if requested
    if agent_type and not issubclass(agent_class, agent_type):
        raise ValueError(
            f"Agent class for '{agent_name}' is {agent_class}, not a subclass of {agent_type}"
        )

    # Filter kwargs to only include parameters accepted by the constructor
    filtered_kwargs = {}
    sig = inspect.signature(agent_class.__init__)

    for param_name, param in sig.parameters.items():
        if param_name in kwargs and param_name != "self":
            filtered_kwargs[param_name] = kwargs[param_name]

    # Create agent instance
    try:
        agent = agent_class(**filtered_kwargs)
        logger.debug(f"Created agent '{agent_name}'")
        return cast(T, agent)

    except Exception as e:
        logger.error(f"Failed to create agent '{agent_name}': {e}")
        raise ValueError(f"Error creating agent '{agent_name}': {e}")


@traced(name="get_registered_agents")
def get_registered_agents() -> List[str]:
    """Get a list of all registered agent names.

    Returns:
        A list of agent identifiers.
    """
    return list(_AGENT_REGISTRY.keys())


@traced(name="discover_agents")
def discover_agents() -> Set[str]:
    """Discover available agents.

    Returns:
        Set of available agent names.
    """
    return set(_AGENT_REGISTRY.keys())


class AgentRegistry(TracedClass):
    """Registry for creating and managing agents."""

    def __init__(self):
        """Initialize the agent registry."""
        self._agents: Dict[str, AtlasAgent] = {}
        self._default_agent: Optional[str] = None

    def register(
        self,
        agent_name: str,
        agent_class: Optional[Type[AtlasAgent]] = None,
        class_path: Optional[str] = None,
        constructor: Optional[Callable[..., AtlasAgent]] = None,
    ) -> None:
        """Register an agent with the registry.

        Args:
            agent_name: The name of the agent.
            agent_class: Optional agent class to register directly.
            class_path: Optional import path to the agent class.
            constructor: Optional constructor function for the agent.

        Raises:
            ValueError: If no registration information is provided.
        """
        if agent_class:
            register_agent_class(agent_name, agent_class)
        elif class_path:
            register_agent(agent_name, class_path)
        elif constructor:
            register_agent_constructor(agent_name, constructor)
        else:
            raise ValueError(
                "Must provide one of agent_class, class_path, or constructor"
            )

    def create(self, agent_name: str = "atlas", **kwargs: Any) -> AtlasAgent:
        """Create an agent instance.

        Args:
            agent_name: Name of the agent to create.
            **kwargs: Additional agent-specific parameters.

        Returns:
            Agent instance.

        Raises:
            ValueError: If the agent is not supported.
        """
        agent = create_agent(agent_name, **kwargs)

        # Store the agent in the registry
        self._agents[agent_name] = agent

        # Set as default if no default is set
        if self._default_agent is None:
            self._default_agent = agent_name

        return agent

    def get(self, agent_name: Optional[str] = None) -> AtlasAgent:
        """Get an agent instance.

        Args:
            agent_name: Name of the agent to get. If None, use the default agent.

        Returns:
            Agent instance.

        Raises:
            ValueError: If the agent is not available.
        """
        # Use the default agent if not specified
        if agent_name is None:
            if self._default_agent is None:
                # Try to find a suitable default
                available = discover_agents()
                if "atlas" in available:
                    agent_name = "atlas"
                elif available:
                    agent_name = next(iter(available))
                else:
                    raise ValueError("No default agent available")
            else:
                agent_name = self._default_agent

        # Check if the agent is already created
        if agent_name in self._agents:
            return self._agents[agent_name]

        # Create the agent
        return self.create(agent_name)

    def set_default(self, agent_name: str) -> None:
        """Set the default agent.

        Args:
            agent_name: Name of the agent to set as default.

        Raises:
            ValueError: If the agent is not available.
        """
        # Check if the agent is available
        available = discover_agents()
        if agent_name not in available:
            raise ValueError(f"Agent '{agent_name}' is not available")

        self._default_agent = agent_name

    def list(self) -> List[str]:
        """List all registered agents.

        Returns:
            A list of agent names.
        """
        return get_registered_agents()
