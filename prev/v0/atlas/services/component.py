"""
Service-enabled component base class.

This module provides the ServiceEnabledComponent base class, which is the foundation
for all components that leverage the core services layer. It handles service
acquisition, initialization, and provides a consistent interface for working with
services.
"""

import threading
import uuid
from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from atlas.core.errors import AtlasError, ErrorCategory, ErrorSeverity
from atlas.core.logging import get_logger
from atlas.core.services.registry import ServiceRegistry, get_registry

# Create a logger for this module
logger = get_logger(__name__)


# Custom error classes for service-enabled components
class ServiceInitializationError(AtlasError):
    """Error during service initialization for a component."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        component_id: str | None = None,
        component_type: str | None = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            component_id: The ID of the component causing the error.
            component_type: The type of the component causing the error.
        """
        details = details or {}

        if component_id:
            details["component_id"] = component_id

        if component_type:
            details["component_type"] = component_type

        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.CONFIGURATION,
            details=details,
            cause=cause,
        )


class ServiceMissingError(AtlasError):
    """Error when a required service is missing."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        service_name: str | None = None,
        component_id: str | None = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            service_name: The name of the missing service.
            component_id: The ID of the component that requires the service.
        """
        details = details or {}

        if service_name:
            details["service_name"] = service_name

        if component_id:
            details["component_id"] = component_id

        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.CONFIGURATION,
            details=details,
            cause=cause,
        )


@runtime_checkable
class ServiceAware(Protocol):
    """Protocol for components that are service-aware."""

    @property
    def service_registry(self) -> ServiceRegistry:
        """Get the service registry."""
        ...


class ServiceEnabledComponent(ABC):
    """Base class for all service-enabled components.

    This class serves as the foundation for all components that leverage the
    core services layer. It handles service acquisition, initialization, and
    provides a consistent interface for working with services.
    """

    def __init__(
        self,
        component_id: str | None = None,
        component_type: str | None = None,
        service_registry: ServiceRegistry | None = None,
    ):
        """Initialize the service-enabled component.

        Args:
            component_id: Unique identifier for this component.
            component_type: Type of component.
            service_registry: Service registry to use.
        """
        self._component_id = component_id or str(uuid.uuid4())
        self._component_type = component_type or self.__class__.__name__
        self._service_registry = service_registry or get_registry()
        self._initialized_services = False
        self._services: dict[str, Any] = {}
        self._lock = threading.RLock()

        logger.debug(
            f"Created ServiceEnabledComponent with ID {self._component_id} "
            f"and type {self._component_type}"
        )

    @property
    def component_id(self) -> str:
        """Get the component ID.

        Returns:
            The component ID.
        """
        return self._component_id

    @property
    def component_type(self) -> str:
        """Get the component type.

        Returns:
            The component type.
        """
        return self._component_type

    @property
    def service_registry(self) -> ServiceRegistry:
        """Get the service registry.

        Returns:
            The service registry.
        """
        return self._service_registry

    def initialize_services(self) -> None:
        """Initialize service references.

        This method should be called during initialization to set up service references.
        It ensures services are only initialized once and handles any initialization errors.

        Raises:
            ServiceInitializationError: If service initialization fails.
        """
        with self._lock:
            if self._initialized_services:
                return

            try:
                self._setup_service_references()
                self._initialized_services = True
                logger.debug(f"Services initialized for component {self._component_id}")
            except Exception as e:
                logger.error(
                    f"Failed to initialize services for component {self._component_id}: {e}",
                    exc_info=True,
                )
                raise ServiceInitializationError(
                    message=f"Failed to initialize services: {e}",
                    cause=e,
                    component_id=self._component_id,
                    component_type=self._component_type,
                )

    @abstractmethod
    def _setup_service_references(self) -> None:
        """Set up references to required services.

        This method should be implemented by subclasses to acquire references
        to their required services from the service registry.

        Raises:
            ServiceMissingError: If a required service is missing.
        """
        pass

    def get_service(self, service_type: type[Any], required: bool = True) -> Any:
        """Get a service of the specified type.

        Args:
            service_type: The type of service to get.
            required: Whether the service is required.

        Returns:
            The service instance.

        Raises:
            ServiceMissingError: If the service is required but not available.
        """
        service_name = service_type.__name__

        if service_name in self._services:
            return self._services[service_name]

        # Try to get from the registry by name
        service = self._service_registry.get_service_by_name(service_name)

        if service is None:
            # Not found by name, try by interface
            services = self._service_registry.get_services_by_capability(service_name)
            if services:
                service = services[0]

        if service is None and required:
            raise ServiceMissingError(
                message=f"Required service {service_name} not found",
                service_name=service_name,
                component_id=self._component_id,
            )

        if service is not None:
            # Cache the service for future use
            self._services[service_name] = service

        return service
