"""
Resource lifecycle management.

This module provides a system for managing resources with proper acquisition,
release, and lifecycle states. It ensures resources are properly tracked and
cleaned up when no longer needed.
"""

import contextlib
import time
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from threading import Event, RLock
from typing import Any, ClassVar, Generic, TypeAlias, TypeVar

from atlas.core.errors import AtlasError, ErrorCategory, ErrorSeverity
from atlas.core.logging import get_logger
from atlas.schemas.definitions.services import ResourceState

# Type aliases for improved clarity
ResourceId: TypeAlias = str
ResourceType: TypeAlias = str
ServiceId: TypeAlias = str
ResourceFactory: TypeAlias = Callable[[], Any]
ResourceCleanup: TypeAlias = Callable[[Any], None]

# Generic type for resource values
T = TypeVar("T")

# Create a logger for this module
logger = get_logger(__name__)


# Custom error classes for the resource system
class ResourceError(AtlasError):
    """Base class for resource management errors."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        resource_id: str | None = None,
        resource_type: str | None = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            resource_id: The ID of the resource causing the error.
            resource_type: The type of resource causing the error.
        """
        details = details or {}

        if resource_id:
            details["resource_id"] = resource_id

        if resource_type:
            details["resource_type"] = resource_type

        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.RESOURCE,
            details=details,
            cause=cause,
        )


class ResourceAcquisitionError(ResourceError):
    """Error related to resource acquisition."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        resource_id: str | None = None,
        resource_type: str | None = None,
        owner_service: str | None = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            resource_id: The ID of the resource causing the error.
            resource_type: The type of resource causing the error.
            owner_service: The service that tried to acquire the resource.
        """
        details = details or {}

        if owner_service:
            details["owner_service"] = owner_service

        super().__init__(
            message=message,
            details=details,
            cause=cause,
            severity=severity,
            resource_id=resource_id,
            resource_type=resource_type,
        )


class ResourceReleaseError(ResourceError):
    """Error related to resource release."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        resource_id: str | None = None,
        resource_type: str | None = None,
        owner_service: str | None = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            resource_id: The ID of the resource causing the error.
            resource_type: The type of resource causing the error.
            owner_service: The service that tried to release the resource.
        """
        details = details or {}

        if owner_service:
            details["owner_service"] = owner_service

        super().__init__(
            message=message,
            details=details,
            cause=cause,
            severity=severity,
            resource_id=resource_id,
            resource_type=resource_type,
        )


class Resource(Generic[T]):
    """Represents a managed resource with lifecycle states."""

    def __init__(
        self,
        resource_id: str,
        resource_type: str,
        value: T,
        cleanup_func: ResourceCleanup | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize a new resource.

        Args:
            resource_id: Unique identifier for this resource.
            resource_type: The type of resource.
            value: The actual resource value/object.
            cleanup_func: Optional function to call when releasing the resource.
            metadata: Optional metadata about the resource.
        """
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.value = value
        self.cleanup_func = cleanup_func
        self.metadata = metadata or {}
        self.state: ResourceState = "initializing"
        self.owner_service: str | None = None
        self.acquisition_time: datetime | None = None
        self.release_time: datetime | None = None
        self.create_time = datetime.now()

        logger.debug(
            f"Created resource {resource_id} of type {resource_type} with state {self.state}"
        )

    def initialize(self) -> None:
        """Initialize the resource.

        Raises:
            ResourceError: If the resource is not in the initializing state.
        """
        if self.state != "initializing":
            raise ResourceError(
                message=f"Cannot initialize resource in state {self.state}",
                resource_id=self.resource_id,
                resource_type=self.resource_type,
            )

        # Set state to ready
        self.state = "ready"
        logger.debug(f"Initialized resource {self.resource_id} to ready state")

    def acquire(self, owner_service: str) -> T:
        """Acquire the resource for use.

        Args:
            owner_service: The service acquiring the resource.

        Returns:
            The resource value.

        Raises:
            ResourceAcquisitionError: If the resource cannot be acquired.
        """
        if self.state != "ready":
            raise ResourceAcquisitionError(
                message=f"Cannot acquire resource in state {self.state}",
                resource_id=self.resource_id,
                resource_type=self.resource_type,
                owner_service=owner_service,
            )

        # Set acquisition info
        self.state = "in_use"
        self.owner_service = owner_service
        self.acquisition_time = datetime.now()

        logger.debug(
            f"Resource {self.resource_id} acquired by service {owner_service} "
            f"at {self.acquisition_time}"
        )

        return self.value

    def release(self, owner_service: str | None = None) -> None:
        """Release the resource.

        Args:
            owner_service: The service releasing the resource.

        Raises:
            ResourceReleaseError: If the resource cannot be released.
        """
        # Validate ownership if specified
        if owner_service and self.owner_service != owner_service:
            raise ResourceReleaseError(
                message=f"Resource owned by {self.owner_service}, cannot be released by {owner_service}",
                resource_id=self.resource_id,
                resource_type=self.resource_type,
                owner_service=owner_service,
            )

        if self.state != "in_use":
            raise ResourceReleaseError(
                message=f"Cannot release resource in state {self.state}",
                resource_id=self.resource_id,
                resource_type=self.resource_type,
                owner_service=owner_service,
            )

        # Run cleanup if provided
        if self.cleanup_func:
            try:
                self.cleanup_func(self.value)
            except Exception as e:
                logger.error(f"Error during resource cleanup: {e}", exc_info=True)

        # Set release info
        self.state = "released"
        self.release_time = datetime.now()

        logger.debug(
            f"Resource {self.resource_id} released by service {owner_service or self.owner_service} "
            f"at {self.release_time}"
        )

    def set_error(self, error: Exception | None = None) -> None:
        """Set the resource to error state.

        Args:
            error: Optional exception that caused the error.
        """
        self.state = "error"

        if error:
            self.metadata["error"] = str(error)
            self.metadata["error_type"] = type(error).__name__

        logger.debug(f"Resource {self.resource_id} set to error state")

    def to_dict(self) -> dict[str, Any]:
        """Convert the resource to a dictionary.

        Returns:
            Dictionary representation of the resource.
        """
        return {
            "resource_id": self.resource_id,
            "type": self.resource_type,
            "state": self.state,
            "owner_service": self.owner_service,
            "acquisition_time": (
                self.acquisition_time.isoformat() if self.acquisition_time else None
            ),
            "release_time": self.release_time.isoformat() if self.release_time else None,
            "create_time": self.create_time.isoformat(),
            "metadata": self.metadata,
        }


class ResourceManager:
    """Manages resources and their lifecycle."""

    # Class constants
    DEFAULT_ACQUIRE_TIMEOUT: ClassVar[float] = 5.0
    DEFAULT_WAIT_TIMEOUT: ClassVar[float] = 30.0

    def __init__(self):
        """Initialize a new resource manager."""
        self._lock = RLock()
        self._resources: dict[ResourceId, Resource] = {}
        self._available_events: dict[ResourceType, Event] = {}

        logger.debug("Created ResourceManager")

    def register_resource(
        self,
        resource_type: str,
        value: T,
        cleanup_func: ResourceCleanup | None = None,
        metadata: dict[str, Any] | None = None,
        resource_id: str | None = None,
    ) -> Resource[T]:
        """Register a new resource.

        Args:
            resource_type: The type of resource.
            value: The actual resource value/object.
            cleanup_func: Optional function to call when releasing the resource.
            metadata: Optional metadata about the resource.
            resource_id: Optional unique identifier for this resource.

        Returns:
            The registered resource.
        """
        # Generate resource ID if not provided
        resource_id = resource_id or str(uuid.uuid4())

        # Create resource
        resource = Resource(
            resource_id=resource_id,
            resource_type=resource_type,
            value=value,
            cleanup_func=cleanup_func,
            metadata=metadata,
        )

        # Initialize resource
        resource.initialize()

        # Add to resources
        with self._lock:
            self._resources[resource_id] = resource

            # Signal resource availability
            if resource_type in self._available_events:
                self._available_events[resource_type].set()

        logger.debug(f"Registered resource {resource_id} of type {resource_type}")
        return resource

    def create_resource(
        self,
        resource_type: str,
        factory_func: ResourceFactory,
        cleanup_func: ResourceCleanup | None = None,
        metadata: dict[str, Any] | None = None,
        resource_id: str | None = None,
    ) -> Resource[Any]:
        """Create a new resource using a factory function.

        Args:
            resource_type: The type of resource.
            factory_func: Function to create the resource value.
            cleanup_func: Optional function to call when releasing the resource.
            metadata: Optional metadata about the resource.
            resource_id: Optional unique identifier for this resource.

        Returns:
            The created resource.

        Raises:
            ResourceError: If the resource cannot be created.
        """
        try:
            # Create the resource value
            value = factory_func()

            # Register the resource
            return self.register_resource(
                resource_type=resource_type,
                value=value,
                cleanup_func=cleanup_func,
                metadata=metadata,
                resource_id=resource_id,
            )

        except Exception as e:
            raise ResourceError(
                message=f"Failed to create resource of type {resource_type}: {e}",
                cause=e,
                resource_type=resource_type,
                resource_id=resource_id,
            )

    def get_resource(self, resource_id: ResourceId) -> Resource | None:
        """Get a resource by ID.

        Args:
            resource_id: The ID of the resource.

        Returns:
            The resource if found, None otherwise.
        """
        with self._lock:
            return self._resources.get(resource_id)

    def find_resources(
        self,
        resource_type: str | None = None,
        state: ResourceState | None = None,
        owner_service: str | None = None,
    ) -> list[Resource]:
        """Find resources matching criteria.

        Args:
            resource_type: Optional resource type to filter by.
            state: Optional resource state to filter by.
            owner_service: Optional owner service to filter by.

        Returns:
            List of matching resources.
        """
        with self._lock:
            # Start with all resources
            resources = list(self._resources.values())

            # Apply filters
            if resource_type:
                resources = [r for r in resources if r.resource_type == resource_type]

            if state:
                resources = [r for r in resources if r.state == state]

            if owner_service:
                resources = [r for r in resources if r.owner_service == owner_service]

            return resources

    def acquire_resource(
        self, resource_type: str, owner_service: str, timeout: float = DEFAULT_ACQUIRE_TIMEOUT
    ) -> Resource:
        """Acquire a resource of the specified type.

        Args:
            resource_type: The type of resource to acquire.
            owner_service: The service acquiring the resource.
            timeout: Maximum time to wait for acquisition in seconds.

        Returns:
            The acquired resource.

        Raises:
            ResourceAcquisitionError: If no resources of the specified type are available.
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Find available resources of the specified type
            with self._lock:
                available_resources = [
                    r
                    for r in self._resources.values()
                    if r.resource_type == resource_type and r.state == "ready"
                ]

                if available_resources:
                    # Acquire the first available resource
                    resource = available_resources[0]
                    try:
                        resource.acquire(owner_service)
                        return resource
                    except ResourceAcquisitionError:
                        # If this resource can't be acquired, try the next one
                        continue

            # No resources available, wait a bit and try again
            time.sleep(0.1)

        # Timeout reached
        raise ResourceAcquisitionError(
            message=f"No available resources of type {resource_type} within timeout",
            resource_type=resource_type,
            owner_service=owner_service,
        )

    def wait_for_resource_type(
        self, resource_type: str, timeout: float = DEFAULT_WAIT_TIMEOUT
    ) -> bool:
        """Wait for a resource of the specified type to become available.

        Args:
            resource_type: The type of resource to wait for.
            timeout: Maximum time to wait in seconds.

        Returns:
            True if resources became available, False if timeout occurred.
        """
        # Check if any resources of this type are already available
        with self._lock:
            available_resources = [
                r
                for r in self._resources.values()
                if r.resource_type == resource_type and r.state == "ready"
            ]

            if available_resources:
                return True

            # Create event if not exists
            if resource_type not in self._available_events:
                self._available_events[resource_type] = Event()

        # Wait for the event
        return self._available_events[resource_type].wait(timeout)

    def release_resource(self, resource_id: ResourceId, owner_service: str | None = None) -> None:
        """Release a resource.

        Args:
            resource_id: The ID of the resource to release.
            owner_service: Optional service releasing the resource.

        Raises:
            ResourceReleaseError: If the resource cannot be released.
        """
        with self._lock:
            resource = self._resources.get(resource_id)

            if not resource:
                raise ResourceReleaseError(
                    message=f"Resource {resource_id} not found",
                    resource_id=resource_id,
                    owner_service=owner_service,
                )

            # Release the resource
            resource.release(owner_service)

    def remove_resource(self, resource_id: ResourceId) -> bool:
        """Remove a resource from management.

        Args:
            resource_id: The ID of the resource to remove.

        Returns:
            True if the resource was removed, False otherwise.
        """
        with self._lock:
            if resource_id in self._resources:
                # Get the resource
                resource = self._resources[resource_id]

                # Try to release if in use
                if resource.state == "in_use":
                    try:
                        resource.release()
                    except ResourceReleaseError as e:
                        logger.error(f"Error releasing resource during removal: {e}", exc_info=True)

                # Remove from management
                del self._resources[resource_id]
                logger.debug(f"Removed resource {resource_id}")
                return True

            return False

    def cleanup_resources(
        self, resource_type: str | None = None, older_than: timedelta | None = None
    ) -> int:
        """Clean up resources that are no longer needed.

        Args:
            resource_type: Optional type of resources to clean up.
            older_than: Optional time delta for resource age filtering.

        Returns:
            Number of resources cleaned up.
        """
        now = datetime.now()
        resource_ids_to_remove = []

        with self._lock:
            for resource_id, resource in self._resources.items():
                # Apply filters
                if resource_type and resource.resource_type != resource_type:
                    continue

                if older_than and now - resource.create_time < older_than:
                    continue

                # Only remove resources in terminal states
                if resource.state in ["released", "error"]:
                    resource_ids_to_remove.append(resource_id)

        # Remove resources outside the lock
        count = 0
        for resource_id in resource_ids_to_remove:
            if self.remove_resource(resource_id):
                count += 1

        logger.debug(f"Cleaned up {count} resources")
        return count

    def stats(self) -> dict[str, Any]:
        """Get resource manager statistics.

        Returns:
            Dictionary of resource manager statistics.
        """
        with self._lock:
            # Count resources by type and state
            resource_counts: dict[str, dict[str, int]] = {}

            for resource in self._resources.values():
                resource_type = resource.resource_type
                state = resource.state

                if resource_type not in resource_counts:
                    resource_counts[resource_type] = {}

                if state not in resource_counts[resource_type]:
                    resource_counts[resource_type][state] = 0

                resource_counts[resource_type][state] += 1

            # Count resources by owner
            owner_counts: dict[str, int] = {}

            for resource in self._resources.values():
                if resource.owner_service:
                    if resource.owner_service not in owner_counts:
                        owner_counts[resource.owner_service] = 0

                    owner_counts[resource.owner_service] += 1

            return {
                "total_resources": len(self._resources),
                "resource_counts": resource_counts,
                "owner_counts": owner_counts,
                "resource_types": list(set(r.resource_type for r in self._resources.values())),
            }


def create_resource_manager() -> ResourceManager:
    """Create a new resource manager.

    Returns:
        A new ResourceManager instance.
    """
    return ResourceManager()


@contextlib.contextmanager
def managed_resource(
    manager: ResourceManager,
    resource_type: str,
    owner_service: str,
    factory_func: ResourceFactory | None = None,
    cleanup_func: ResourceCleanup | None = None,
    timeout: float = ResourceManager.DEFAULT_ACQUIRE_TIMEOUT,
):
    """Context manager for automatic resource acquisition and release.

    Args:
        manager: The resource manager to use.
        resource_type: The type of resource to acquire or create.
        owner_service: The service acquiring the resource.
        factory_func: Optional function to create the resource if not found.
        cleanup_func: Optional function to call when releasing the resource.
        timeout: Maximum time to wait for acquisition in seconds.

    Yields:
        The acquired resource value.

    Raises:
        ResourceAcquisitionError: If no resources are available and no factory is provided.
        ResourceReleaseError: If the resource cannot be released.
    """
    resource = None

    try:
        # Try to acquire an existing resource
        try:
            resource = manager.acquire_resource(
                resource_type=resource_type, owner_service=owner_service, timeout=timeout
            )
        except ResourceAcquisitionError:
            # If no resources available and factory provided, create a new one
            if factory_func:
                resource = manager.create_resource(
                    resource_type=resource_type,
                    factory_func=factory_func,
                    cleanup_func=cleanup_func,
                )
                resource.acquire(owner_service)
            else:
                # Re-raise the acquisition error
                raise

        # Yield the resource value to the caller
        yield resource.value

    finally:
        # Always release the resource if acquired
        if resource and resource.state == "in_use":
            try:
                manager.release_resource(
                    resource_id=resource.resource_id, owner_service=owner_service
                )
            except ResourceReleaseError as e:
                logger.error(f"Error releasing resource in context manager: {e}", exc_info=True)
