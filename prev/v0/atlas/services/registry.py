"""
Service registry for dynamic service discovery.

This module provides a registry for services, allowing for dynamic discovery
and acquisition of services at runtime. It supports capability-based service
selection and dependency injection.
"""

import uuid
from collections.abc import Callable
from threading import RLock
from typing import (
    Any,
    Protocol,
    TypeAlias,
    TypeVar,
    runtime_checkable,
)

from atlas.core.errors import AtlasError, ErrorCategory, ErrorSeverity
from atlas.core.logging import get_logger

# Type aliases for improved clarity
ServiceId: TypeAlias = str
ServiceName: TypeAlias = str
ServiceFactory: TypeAlias = Callable[[], Any]
ServiceInstance = TypeVar("ServiceInstance")

# Create a logger for this module
logger = get_logger(__name__)


# Custom error classes for the service registry
class ServiceError(AtlasError):
    """Base class for service registry errors."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        service_id: str | None = None,
        service_name: str | None = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            service_id: The ID of the service causing the error.
            service_name: The name of the service causing the error.
        """
        details = details or {}

        if service_id:
            details["service_id"] = service_id

        if service_name:
            details["service_name"] = service_name

        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.CONFIGURATION,
            details=details,
            cause=cause,
        )


class ServiceNotFoundError(ServiceError):
    """Error indicating a service was not found."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        service_id: str | None = None,
        service_name: str | None = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            service_id: The ID of the service that wasn't found.
            service_name: The name of the service that wasn't found.
        """
        super().__init__(
            message=message,
            details=details,
            cause=cause,
            severity=severity,
            service_id=service_id,
            service_name=service_name,
        )


class DuplicateServiceError(ServiceError):
    """Error indicating a duplicate service registration."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        service_id: str | None = None,
        service_name: str | None = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            service_id: The ID of the duplicate service.
            service_name: The name of the duplicate service.
        """
        super().__init__(
            message=message,
            details=details,
            cause=cause,
            severity=severity,
            service_id=service_id,
            service_name=service_name,
        )


@runtime_checkable
class Service(Protocol):
    """Protocol defining the interface for services."""

    @property
    def service_id(self) -> str: ...

    @property
    def name(self) -> str: ...

    @property
    def status(self) -> str: ...

    @property
    def capabilities(self) -> dict[str, Any]: ...

    def start(self) -> None: ...

    def stop(self) -> None: ...


class ServiceRegistry:
    """Registry for service discovery and management."""

    def __init__(self):
        """Initialize a new service registry."""
        self._lock = RLock()
        self._services: dict[ServiceId, Service] = {}
        self._service_names: dict[ServiceName, set[ServiceId]] = {}
        self._capabilities: dict[str, set[ServiceId]] = {}

        logger.debug("Created ServiceRegistry")

    def register_service(self, service: Service, replace: bool = False) -> None:
        """Register a service with the registry.

        Args:
            service: The service to register.
            replace: If True, replace any existing service with the same ID.

        Raises:
            DuplicateServiceError: If a service with the same ID exists and replace is False.
        """
        service_id = service.service_id
        service_name = service.name

        with self._lock:
            # Check for existing service
            if service_id in self._services and not replace:
                raise DuplicateServiceError(
                    message=f"Service with ID {service_id} already exists",
                    service_id=service_id,
                    service_name=service_name,
                )

            # Add to services
            self._services[service_id] = service

            # Add to service names
            if service_name not in self._service_names:
                self._service_names[service_name] = set()

            self._service_names[service_name].add(service_id)

            # Add to capabilities
            for capability in service.capabilities:
                if capability not in self._capabilities:
                    self._capabilities[capability] = set()

                self._capabilities[capability].add(service_id)

        logger.debug(f"Registered service {service_id} with name {service_name}")

    def unregister_service(self, service_id: ServiceId) -> bool:
        """Unregister a service from the registry.

        Args:
            service_id: The ID of the service to unregister.

        Returns:
            True if the service was unregistered, False if not found.
        """
        with self._lock:
            if service_id not in self._services:
                return False

            service = self._services[service_id]
            service_name = service.name

            # Remove from services
            del self._services[service_id]

            # Remove from service names
            if service_name in self._service_names:
                self._service_names[service_name].discard(service_id)

                if not self._service_names[service_name]:
                    del self._service_names[service_name]

            # Remove from capabilities
            for capability, service_ids in list(self._capabilities.items()):
                service_ids.discard(service_id)

                if not service_ids:
                    del self._capabilities[capability]

        logger.debug(f"Unregistered service {service_id}")
        return True

    def get_service(self, service_id: ServiceId) -> Service | None:
        """Get a service by ID.

        Args:
            service_id: The ID of the service to get.

        Returns:
            The service if found, None otherwise.
        """
        with self._lock:
            return self._services.get(service_id)

    def get_service_by_name(
        self, name: ServiceName, capabilities: list[str] | None = None
    ) -> Service | None:
        """Get a service by name and optional capabilities.

        Args:
            name: The name of the service to get.
            capabilities: Optional list of required capabilities.

        Returns:
            The first matching service if found, None otherwise.
        """
        with self._lock:
            if name not in self._service_names:
                return None

            service_ids = self._service_names[name]

            # Filter by capabilities if provided
            if capabilities:
                matching_ids = service_ids

                for capability in capabilities:
                    if capability in self._capabilities:
                        matching_ids = matching_ids.intersection(self._capabilities[capability])
                    else:
                        return None  # Required capability not found

                if not matching_ids:
                    return None  # No services with all required capabilities

                service_ids = matching_ids

            # Return the first matching service
            if service_ids:
                return self._services[next(iter(service_ids))]

            return None

    def get_services_by_name(
        self, name: ServiceName, capabilities: list[str] | None = None
    ) -> list[Service]:
        """Get all services with a given name and optional capabilities.

        Args:
            name: The name of the services to get.
            capabilities: Optional list of required capabilities.

        Returns:
            List of matching services.
        """
        with self._lock:
            if name not in self._service_names:
                return []

            service_ids = self._service_names[name]

            # Filter by capabilities if provided
            if capabilities:
                matching_ids = service_ids

                for capability in capabilities:
                    if capability in self._capabilities:
                        matching_ids = matching_ids.intersection(self._capabilities[capability])
                    else:
                        return []  # Required capability not found

                if not matching_ids:
                    return []  # No services with all required capabilities

                service_ids = matching_ids

            return [self._services[service_id] for service_id in service_ids]

    def get_services_by_capability(self, capability: str) -> list[Service]:
        """Get all services with a given capability.

        Args:
            capability: The capability to filter by.

        Returns:
            List of services with the capability.
        """
        with self._lock:
            if capability not in self._capabilities:
                return []

            return [self._services[service_id] for service_id in self._capabilities[capability]]

    def list_services(self) -> list[dict[str, Any]]:
        """List all registered services.

        Returns:
            List of service dictionaries.
        """
        with self._lock:
            return [
                {
                    "service_id": service.service_id,
                    "name": service.name,
                    "status": service.status,
                    "capabilities": service.capabilities,
                }
                for service in self._services.values()
            ]

    def list_service_names(self) -> list[str]:
        """List all registered service names.

        Returns:
            List of service names.
        """
        with self._lock:
            return list(self._service_names.keys())

    def list_capabilities(self) -> list[str]:
        """List all registered capabilities.

        Returns:
            List of capabilities.
        """
        with self._lock:
            return list(self._capabilities.keys())

    def start_service(self, service_id: ServiceId) -> bool:
        """Start a service.

        Args:
            service_id: The ID of the service to start.

        Returns:
            True if the service was started, False if not found.

        Raises:
            ServiceError: If the service fails to start.
        """
        with self._lock:
            service = self._services.get(service_id)

            if not service:
                return False

        try:
            service.start()
            logger.debug(f"Started service {service_id}")
            return True
        except Exception as e:
            raise ServiceError(
                message=f"Failed to start service {service_id}: {e}",
                cause=e,
                service_id=service_id,
                service_name=service.name,
            )

    def stop_service(self, service_id: ServiceId) -> bool:
        """Stop a service.

        Args:
            service_id: The ID of the service to stop.

        Returns:
            True if the service was stopped, False if not found.

        Raises:
            ServiceError: If the service fails to stop.
        """
        with self._lock:
            service = self._services.get(service_id)

            if not service:
                return False

        try:
            service.stop()
            logger.debug(f"Stopped service {service_id}")
            return True
        except Exception as e:
            raise ServiceError(
                message=f"Failed to stop service {service_id}: {e}",
                cause=e,
                service_id=service_id,
                service_name=service.name,
            )

    def restart_service(self, service_id: ServiceId) -> bool:
        """Restart a service.

        Args:
            service_id: The ID of the service to restart.

        Returns:
            True if the service was restarted, False if not found.

        Raises:
            ServiceError: If the service fails to restart.
        """
        if not self.stop_service(service_id):
            return False

        return self.start_service(service_id)

    def clear(self) -> None:
        """Clear all services from the registry."""
        with self._lock:
            self._services.clear()
            self._service_names.clear()
            self._capabilities.clear()

            logger.debug("Cleared service registry")


# Global service registry
_registry = ServiceRegistry()


def register_service(service: Service, replace: bool = False) -> None:
    """Register a service with the global registry.

    Args:
        service: The service to register.
        replace: If True, replace any existing service with the same ID.

    Raises:
        DuplicateServiceError: If a service with the same ID exists and replace is False.
    """
    _registry.register_service(service, replace)


def get_service(service_id: ServiceId) -> Service | None:
    """Get a service by ID from the global registry.

    Args:
        service_id: The ID of the service to get.

    Returns:
        The service if found, None otherwise.
    """
    return _registry.get_service(service_id)


def get_service_by_name(name: ServiceName, capabilities: list[str] | None = None) -> Service | None:
    """Get a service by name and optional capabilities from the global registry.

    Args:
        name: The name of the service to get.
        capabilities: Optional list of required capabilities.

    Returns:
        The first matching service if found, None otherwise.
    """
    return _registry.get_service_by_name(name, capabilities)


def list_services() -> list[dict[str, Any]]:
    """List all registered services in the global registry.

    Returns:
        List of service dictionaries.
    """
    return _registry.list_services()


def unregister_service(service_id: ServiceId) -> bool:
    """Unregister a service from the global registry.

    Args:
        service_id: The ID of the service to unregister.

    Returns:
        True if the service was unregistered, False if not found.
    """
    return _registry.unregister_service(service_id)


def get_registry() -> ServiceRegistry:
    """Get the global service registry.

    Returns:
        The global service registry.
    """
    return _registry


class BaseService:
    """Base class for services with standard functionality."""

    def __init__(
        self,
        name: str,
        capabilities: dict[str, Any] | None = None,
        service_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize a new service.

        Args:
            name: The name of the service.
            capabilities: Optional capabilities of the service.
            service_id: Optional unique identifier for this service.
            metadata: Optional metadata about the service.
        """
        self._service_id = service_id or str(uuid.uuid4())
        self._name = name
        self._capabilities = capabilities or {}
        self._metadata = metadata or {}
        self._status = "initializing"

        logger.debug(
            f"Created service {self._service_id} with name {name} "
            f"and capabilities {list(self._capabilities.keys())}"
        )

    @property
    def service_id(self) -> str:
        """Get the service ID.

        Returns:
            The service ID.
        """
        return self._service_id

    @property
    def name(self) -> str:
        """Get the service name.

        Returns:
            The service name.
        """
        return self._name

    @property
    def status(self) -> str:
        """Get the service status.

        Returns:
            The service status.
        """
        return self._status

    @property
    def capabilities(self) -> dict[str, Any]:
        """Get the service capabilities.

        Returns:
            The service capabilities.
        """
        return self._capabilities.copy()

    @property
    def metadata(self) -> dict[str, Any]:
        """Get the service metadata.

        Returns:
            The service metadata.
        """
        return self._metadata.copy()

    def start(self) -> None:
        """Start the service.

        Raises:
            ServiceError: If the service fails to start.
        """
        if self._status == "running":
            return

        try:
            self._start()
            self._status = "running"
            logger.debug(f"Started service {self._service_id}")
        except Exception as e:
            self._status = "error"
            raise ServiceError(
                message=f"Failed to start service {self._name}: {e}",
                cause=e,
                service_id=self._service_id,
                service_name=self._name,
            )

    def _start(self) -> None:
        """Start the service implementation.

        This method should be overridden by subclasses.
        """
        pass

    def stop(self) -> None:
        """Stop the service.

        Raises:
            ServiceError: If the service fails to stop.
        """
        try:
            # Call _stop regardless of current status to ensure proper cleanup
            self._stop()
            self._status = "stopped"
            logger.debug(f"Stopped service {self._service_id}")
        except Exception as e:
            self._status = "error"
            raise ServiceError(
                message=f"Failed to stop service {self._name}: {e}",
                cause=e,
                service_id=self._service_id,
                service_name=self._name,
            )

    def _stop(self) -> None:
        """Stop the service implementation.

        This method should be overridden by subclasses.
        """
        pass

    def to_dict(self) -> dict[str, Any]:
        """Convert the service to a dictionary.

        Returns:
            Dictionary representation of the service.
        """
        return {
            "service_id": self._service_id,
            "name": self._name,
            "status": self._status,
            "capabilities": self._capabilities,
            "metadata": self._metadata,
        }
