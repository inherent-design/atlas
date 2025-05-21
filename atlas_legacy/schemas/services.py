"""
Service component schemas for Atlas.

This module provides Marshmallow schemas for service-related structures,
including buffer system, event system, state management, command pattern,
and resource lifecycle management.

This module extends pure schema definitions with post_load methods
that convert validated data into actual implementation objects.
"""

from typing import Any, Protocol, Self, TypeGuard, runtime_checkable

from marshmallow import post_load

from atlas.core.validation.errors import ConfigurationError
from atlas.schemas.definitions.services import (
    BatchingBufferConfigSchema as BaseBatchingBufferConfigSchema,
)
from atlas.schemas.definitions.services import BufferConfigSchema as BaseBufferConfigSchema
from atlas.schemas.definitions.services import BufferItemSchema as BaseBufferItemSchema
from atlas.schemas.definitions.services import CommandResultSchema as BaseCommandResultSchema
from atlas.schemas.definitions.services import CommandSchema as BaseCommandSchema
from atlas.schemas.definitions.services import EventSchema as BaseEventSchema
from atlas.schemas.definitions.services import (
    RateLimitedBufferConfigSchema as BaseRateLimitedBufferConfigSchema,
)
from atlas.schemas.definitions.services import ResourceSchema as BaseResourceSchema
from atlas.schemas.definitions.services import ServiceSchema as BaseServiceSchema
from atlas.schemas.definitions.services import StateSchema as BaseStateSchema
from atlas.schemas.definitions.services import SubscriptionSchema as BaseSubscriptionSchema
from atlas.schemas.definitions.services import TransitionSchema as BaseTransitionSchema


@runtime_checkable
class BufferProtocol(Protocol):
    """Protocol defining the interface for thread-safe buffers."""

    def push(self, item: dict[str, Any]) -> bool: ...
    def pop(self) -> dict[str, Any] | None: ...
    def peek(self) -> dict[str, Any] | None: ...
    def clear(self) -> None: ...
    def is_closed(self) -> bool: ...
    def close(self) -> None: ...
    def pause(self) -> Self: ...
    def resume(self) -> Self: ...


class ServiceSchema(BaseServiceSchema):
    """Schema for service with implementation conversion."""

    @post_load
    def make_object(self, data: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Convert loaded data into a service dictionary.

        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.

        Returns:
            The service data dictionary.
        """
        # Simply return the validated data dictionary
        # The actual service instantiation happens elsewhere
        return data


class BufferConfigSchema(BaseBufferConfigSchema):
    """Schema for buffer configuration with implementation conversion."""

    @post_load
    def make_object(self, data: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Convert loaded data into buffer configuration.

        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.

        Returns:
            Buffer configuration dictionary.
        """
        return data


class BufferItemSchema(BaseBufferItemSchema):
    """Schema for buffer item with implementation conversion."""

    @post_load
    def make_object(self, data: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Convert loaded data into a buffer item.

        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.

        Returns:
            Buffer item dictionary.
        """
        return data


class RateLimitedBufferConfigSchema(BaseRateLimitedBufferConfigSchema):
    """Schema for rate-limited buffer with implementation conversion."""

    @post_load
    def make_object(self, data: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Convert loaded data into rate-limited buffer configuration.

        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.

        Returns:
            Rate-limited buffer configuration dictionary.
        """
        return data


class BatchingBufferConfigSchema(BaseBatchingBufferConfigSchema):
    """Schema for batching buffer with implementation conversion."""

    @post_load
    def make_object(self, data: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Convert loaded data into batching buffer configuration.

        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.

        Returns:
            Batching buffer configuration dictionary.
        """
        return data


class EventSchema(BaseEventSchema):
    """Schema for events with implementation conversion."""

    @post_load
    def make_object(self, data: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Convert loaded data into an event object.

        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.

        Returns:
            Event object dictionary.
        """
        # The actual event instantiation happens in the event system
        return data


class SubscriptionSchema(BaseSubscriptionSchema):
    """Schema for event subscription with implementation conversion."""

    @post_load
    def make_object(self, data: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Convert loaded data into a subscription object.

        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.

        Returns:
            Subscription object dictionary.
        """
        # The actual subscription instantiation happens in the event system
        return data


class StateSchema(BaseStateSchema):
    """Schema for state container with implementation conversion."""

    @post_load
    def make_object(self, data: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Convert loaded data into a state container.

        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.

        Returns:
            State container dictionary.
        """
        # The actual state container instantiation happens in the state system
        return data


class TransitionSchema(BaseTransitionSchema):
    """Schema for state transition with implementation conversion."""

    @post_load
    def make_object(self, data: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Convert loaded data into a state transition.

        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.

        Returns:
            State transition dictionary.
        """
        # The actual transition instantiation happens in the state system
        return data


class CommandSchema(BaseCommandSchema):
    """Schema for command with implementation conversion."""

    @post_load
    def make_object(self, data: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Convert loaded data into a command object.

        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.

        Returns:
            Command object dictionary.
        """
        # The actual command instantiation happens in the command system
        return data


class CommandResultSchema(BaseCommandResultSchema):
    """Schema for command result with implementation conversion."""

    @post_load
    def make_object(self, data: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Convert loaded data into a command result.

        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.

        Returns:
            Command result dictionary.
        """
        # The actual result instantiation happens in the command system
        return data


class ResourceSchema(BaseResourceSchema):
    """Schema for resource with implementation conversion."""

    @post_load
    def make_object(self, data: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Convert loaded data into a resource object.

        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.

        Returns:
            Resource object dictionary.
        """
        # The actual resource instantiation happens in the resource system
        return data


# Create schema instances for validation
service_schema = ServiceSchema()
buffer_config_schema = BufferConfigSchema()
buffer_item_schema = BufferItemSchema()
rate_limited_buffer_config_schema = RateLimitedBufferConfigSchema()
batching_buffer_config_schema = BatchingBufferConfigSchema()
event_schema = EventSchema()
subscription_schema = SubscriptionSchema()
state_schema = StateSchema()
transition_schema = TransitionSchema()
command_schema = CommandSchema()
command_result_schema = CommandResultSchema()
resource_schema = ResourceSchema()


# Type-checking utilities
def is_buffer_protocol(obj: Any) -> TypeGuard[BufferProtocol]:
    """Check if an object implements the BufferProtocol.

    Args:
        obj: The object to check.

    Returns:
        True if the object implements BufferProtocol, False otherwise.
    """
    return isinstance(obj, BufferProtocol)


# Validation decorators
def validate_service_config(func):
    """Decorator for validating service configuration.

    Args:
        func: The function to decorate.

    Returns:
        The decorated function.
    """
    from functools import wraps

    from marshmallow import ValidationError

    @wraps(func)
    def wrapper(*args, **kwargs):
        """Wrapper function that validates service configuration.

        Args:
            *args: Function arguments.
            **kwargs: Function keyword arguments.

        Returns:
            The result of the decorated function.

        Raises:
            ConfigurationError: If the configuration is invalid.
        """
        try:
            # Validate configuration
            config_arg_names = ["config", "configuration", "settings", "service_config"]

            for arg_name in config_arg_names:
                if arg_name in kwargs and kwargs[arg_name] is not None:
                    config = kwargs[arg_name]

                    # Skip if config is not a dict
                    if not isinstance(config, dict):
                        continue

                    # Use service schema for validation
                    kwargs[arg_name] = service_schema.load(config)

            # Call original function
            return func(*args, **kwargs)

        except ValidationError as e:
            # Convert to configuration error
            raise ConfigurationError(
                message=f"Invalid service configuration: {e.messages}", cause=e
            )

    return wrapper
