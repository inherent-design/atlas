"""
Service-enabled provider implementation.

This module provides the ServiceEnabledProvider class, which is the foundation
for all provider implementations that leverage the core services layer. It integrates
with the state management, event system, buffer system, and command pattern to provide
a comprehensive service-oriented provider implementation.
"""

import uuid
from typing import Any

from atlas.core.logging import get_logger
from atlas.core.services.commands import CommandExecutor
from atlas.core.services.component import ServiceEnabledComponent
from atlas.core.services.events import EventSystem
from atlas.core.services.registry import ServiceRegistry
from atlas.core.services.state import StateContainer
from atlas.providers.base import BaseProvider

# Create a logger for this module
logger = get_logger(__name__)


class ServiceEnabledProvider(BaseProvider, ServiceEnabledComponent):
    """Provider implementation that leverages core services.

    This class serves as the foundation for all service-enabled provider implementations,
    demonstrating how to properly integrate with the core services layer.
    """

    def __init__(
        self,
        provider_type: str,
        model_name: str,
        api_key: str | None = None,
        service_registry: ServiceRegistry | None = None,
        **kwargs,
    ):
        """Initialize the service-enabled provider.

        Args:
            provider_type: The type of provider (e.g., "anthropic", "openai")
            model_name: The name of the model to use
            api_key: Optional API key for the provider
            service_registry: Optional service registry to use
            **kwargs: Additional provider-specific options
        """
        BaseProvider.__init__(
            self, provider_type=provider_type, model_name=model_name, api_key=api_key, **kwargs
        )
        ServiceEnabledComponent.__init__(
            self,
            component_id=f"{provider_type}_{model_name}_{uuid.uuid4()}",
            component_type=f"Provider-{provider_type}",
            service_registry=service_registry,
        )

        # Initialize service references
        self.initialize_services()

        # Initialize provider state
        self._initialize_state()

        logger.debug(
            f"Created ServiceEnabledProvider with type {provider_type} and model {model_name}"
        )

    def _setup_service_references(self) -> None:
        """Set up references to required services."""
        # Get service references from registry
        self._state_container = self.get_service(StateContainer)
        self._event_system = self.get_service(EventSystem)
        self._command_executor = self.get_service(CommandExecutor)

        logger.debug(
            f"Set up service references for provider {self.provider_type} "
            f"with model {self.model_name}"
        )

    def _initialize_state(self) -> None:
        """Initialize the provider state container."""
        # Create initial state
        initial_state = {
            "provider_type": self.provider_type,
            "model_name": self.model_name,
            "is_streaming": False,
            "active_requests": 0,
            "total_requests": 0,
            "total_tokens": 0,
            "last_error": None,
            "status": "ready",
        }

        # Create provider-specific state container
        self._state = self._state_container.create_container(
            container_type="provider",
            container_id=f"{self.provider_type}_{self.model_name}_{self.component_id}",
            initial_state=initial_state,
        )

        logger.debug(f"Initialized state for provider {self.provider_type}")

    def _create_command(self, command_type: str, **kwargs) -> Any:
        """Create a command instance for the specified operation.

        Args:
            command_type: The type of command to create
            **kwargs: Command-specific parameters

        Returns:
            The created command instance
        """
        # Import the commands module here to avoid circular imports
        from atlas.providers import commands

        # Get the appropriate command class based on command_type
        command_map = {
            "generate": commands.GenerateCommand,
            "stream": commands.StreamCommand,
            "validate": commands.ValidateCommand,
            "cancel": commands.CancelCommand,
        }

        if command_type not in command_map:
            raise ValueError(f"Unsupported command type: {command_type}")

        command_class = command_map[command_type]

        # Create and return the command instance
        command = command_class(
            provider=self, state_container=self._state, event_system=self._event_system, **kwargs
        )

        logger.debug(f"Created {command_type} command for provider {self.provider_type}")
        return command

    def generate(self, request: dict[str, Any]) -> dict[str, Any]:
        """Generate a response for the given request.

        This method creates and executes a GenerateCommand to handle
        the request and return the response.

        Args:
            request: The generation request

        Returns:
            The generation response
        """
        # Create the command
        command = self._create_command("generate", request=request)

        # Execute the command through the command executor
        return self._command_executor.execute(command)

    def stream(self, request: dict[str, Any]) -> Any:
        """Stream a response for the given request.

        This method creates and executes a StreamCommand to handle
        the request and return a streaming response.

        Args:
            request: The generation request

        Returns:
            A streamable object that yields response chunks
        """
        # Create the command
        command = self._create_command("stream", request=request)

        # Execute the command through the command executor
        return self._command_executor.execute(command)

    def validate(self, request: dict[str, Any]) -> bool:
        """Validate the given request.

        This method creates and executes a ValidateCommand to validate
        the request parameters.

        Args:
            request: The request to validate

        Returns:
            True if the request is valid, False otherwise
        """
        # Create the command
        command = self._create_command("validate", request=request)

        # Execute the command through the command executor
        return self._command_executor.execute(command)

    def cancel(self, request_id: str) -> bool:
        """Cancel an in-progress request.

        This method creates and executes a CancelCommand to cancel
        an in-progress request.

        Args:
            request_id: The ID of the request to cancel

        Returns:
            True if the request was cancelled, False otherwise
        """
        # Create the command
        command = self._create_command("cancel", request_id=request_id)

        # Execute the command through the command executor
        return self._command_executor.execute(command)

    def _generate_implementation(self, request: dict[str, Any]) -> dict[str, Any]:
        """Implement the generate method.

        This method should be overridden by subclasses to implement
        provider-specific generation logic.

        Args:
            request: The generation request

        Returns:
            The generation response

        Raises:
            NotImplementedError: If not overridden by subclasses
        """
        raise NotImplementedError("Subclasses must implement _generate_implementation")

    def _stream_implementation(self, request: dict[str, Any]) -> Any:
        """Implement the stream method.

        This method should be overridden by subclasses to implement
        provider-specific streaming logic.

        Args:
            request: The generation request

        Returns:
            A streamable object that yields response chunks

        Raises:
            NotImplementedError: If not overridden by subclasses
        """
        raise NotImplementedError("Subclasses must implement _stream_implementation")

    def _validate_implementation(self, request: dict[str, Any]) -> bool:
        """Implement the validate method.

        This method should be overridden by subclasses to implement
        provider-specific validation logic.

        Args:
            request: The request to validate

        Returns:
            True if the request is valid, False otherwise

        Raises:
            NotImplementedError: If not overridden by subclasses
        """
        raise NotImplementedError("Subclasses must implement _validate_implementation")

    def _cancel_implementation(self, request_id: str) -> bool:
        """Implement the cancel method.

        This method should be overridden by subclasses to implement
        provider-specific cancellation logic.

        Args:
            request_id: The ID of the request to cancel

        Returns:
            True if the request was cancelled, False otherwise

        Raises:
            NotImplementedError: If not overridden by subclasses
        """
        raise NotImplementedError("Subclasses must implement _cancel_implementation")
