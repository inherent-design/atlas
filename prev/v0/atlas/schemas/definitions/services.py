"""
Pure schema definitions for service-related types.

This module contains schema definitions without any post_load methods or references
to implementation classes, avoiding circular imports. These schemas define the
structure and validation rules for service types but don't handle conversion
to actual implementation objects.
"""

from typing import Any, Literal, TypeAlias

from marshmallow import ValidationError, fields, validate, validates, validates_schema

from atlas.schemas.base import AtlasSchema

# Type aliases for improved clarity
ServiceId: TypeAlias = str
ResourceId: TypeAlias = str
EventId: TypeAlias = str
CommandId: TypeAlias = str
BufferId: TypeAlias = str
ComponentId: TypeAlias = str
SubscriptionId: TypeAlias = str
StateId: TypeAlias = str
TransitionId: TypeAlias = str
MiddlewareId: TypeAlias = str

# Literal type definitions
ServiceStatus: TypeAlias = Literal["initializing", "running", "paused", "stopped", "error"]
ResourceState: TypeAlias = Literal["initializing", "ready", "in_use", "released", "error"]
BufferStatus: TypeAlias = Literal["active", "paused", "closed"]
EventPriority: TypeAlias = Literal["low", "normal", "high", "critical"]
CommandStatus: TypeAlias = Literal["pending", "executing", "completed", "failed", "cancelled"]
ComponentStatus: TypeAlias = Literal["initializing", "ready", "active", "paused", "stopping", "terminated", "error"]


class ServiceSchema(AtlasSchema):
    """Schema for service metadata and status."""

    service_id = fields.UUID(required=True)
    name = fields.String(required=True)
    status = fields.String(
        required=True,
        validate=validate.OneOf(["initializing", "running", "paused", "stopped", "error"]),
    )
    capabilities = fields.Dict(load_default=dict)
    metadata = fields.Dict(load_default=dict)

    @validates_schema
    def validate_service(self, data: dict[str, Any], **kwargs) -> None:
        """Validate that the service schema is consistent.

        Args:
            data: The data to validate.
            **kwargs: Additional arguments passed by Marshmallow.

        Raises:
            ValidationError: If the service data is inconsistent.
        """
        # Ensure names follow convention
        if not data.get("name", "").isalnum() and "_" not in data.get("name", ""):
            raise ValidationError("Service name must be alphanumeric with optional underscores")


class BufferConfigSchema(AtlasSchema):
    """Schema for buffer configuration."""

    buffer_id = fields.UUID(required=False, allow_none=True)
    buffer_type = fields.String(required=False, allow_none=True)
    max_size = fields.Integer(required=False, load_default=1024 * 1024)
    paused = fields.Boolean(required=False, load_default=False)
    closed = fields.Boolean(required=False, load_default=False)
    name = fields.String(required=False, allow_none=True)

    @validates("max_size")
    def validate_max_size(self, value: int, **kwargs) -> None:
        """Validate max_size value.

        Args:
            value: The max_size value to validate.
            **kwargs: Additional arguments passed by Marshmallow.

        Raises:
            ValidationError: If the value is not positive.
        """
        if value <= 0:
            raise ValidationError("Maximum buffer size must be greater than 0")


class BufferItemSchema(AtlasSchema):
    """Schema for items stored in buffer."""

    item_id = fields.UUID(required=True)
    timestamp = fields.DateTime(required=True)
    data = fields.Dict(required=True)
    metadata = fields.Dict(load_default=dict)


class RateLimitedBufferConfigSchema(BufferConfigSchema):
    """Schema for rate-limited buffer configuration."""

    tokens_per_second = fields.Float(required=False, allow_none=True)
    chars_per_token = fields.Integer(required=False, load_default=4)
    initial_token_budget = fields.Float(required=False, allow_none=True)

    @validates("tokens_per_second")
    def validate_tokens_per_second(self, value: float | None, **kwargs) -> None:
        """Validate tokens_per_second value.

        Args:
            value: The tokens_per_second value to validate.
            **kwargs: Additional arguments passed by Marshmallow.

        Raises:
            ValidationError: If the value is negative.
        """
        if value is not None and value < 0:
            raise ValidationError("Tokens per second must be greater than or equal to 0")


class BatchingBufferConfigSchema(BufferConfigSchema):
    """Schema for batching buffer configuration."""

    batch_size = fields.Integer(required=False, allow_none=True)
    batch_timeout = fields.Float(required=False, allow_none=True)
    batch_delimiter = fields.String(required=False, allow_none=True)

    @validates("batch_size")
    def validate_batch_size(self, value: int | None, **kwargs) -> None:
        """Validate batch_size value.

        Args:
            value: The batch_size value to validate.
            **kwargs: Additional arguments passed by Marshmallow.

        Raises:
            ValidationError: If the value is not positive.
        """
        if value is not None and value <= 0:
            raise ValidationError("Batch size must be greater than 0")

    @validates("batch_timeout")
    def validate_batch_timeout(self, value: float | None, **kwargs) -> None:
        """Validate batch_timeout value.

        Args:
            value: The batch_timeout value to validate.
            **kwargs: Additional arguments passed by Marshmallow.

        Raises:
            ValidationError: If the value is not positive.
        """
        if value is not None and value <= 0:
            raise ValidationError("Batch timeout must be greater than 0")


class EventSchema(AtlasSchema):
    """Schema for event data."""

    event_id = fields.UUID(required=True)
    event_type = fields.String(required=True)
    source = fields.String(required=True)
    timestamp = fields.DateTime(required=True)
    data = fields.Dict(required=True)
    priority = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(["low", "normal", "high", "critical"]),
    )
    metadata = fields.Dict(load_default=dict)

    @validates("event_type")
    def validate_event_type(self, value: str, **kwargs) -> None:
        """Validate the event type format.

        Args:
            value: The event type to validate.
            **kwargs: Additional arguments passed by Marshmallow.

        Raises:
            ValidationError: If the event type is invalid.
        """
        if not value or not all(part.isalnum() or part == "_" for part in value.split(".")):
            raise ValidationError(
                "Event type must be dot-separated alphanumeric segments (e.g., 'system.service.started')"
            )


class SubscriptionSchema(AtlasSchema):
    """Schema for event subscription."""

    subscription_id = fields.UUID(required=True)
    event_type = fields.String(required=True)
    source_filter = fields.String(allow_none=True)
    callback_name = fields.String(required=True)
    priority = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(["low", "normal", "high", "critical"]),
    )

    @validates("event_type")
    def validate_event_type(self, value: str, **kwargs) -> None:
        """Validate that event_type has valid format.

        Args:
            value: The event_type value to validate.
            **kwargs: Additional arguments passed by Marshmallow.

        Raises:
            ValidationError: If the value has invalid format.
        """
        # Allow wildcards for event type patterns
        parts = value.split(".")
        for part in parts:
            if part != "*" and not all(c.isalnum() or c == "_" for c in part):
                raise ValidationError(
                    "Event type must be dot-separated alphanumeric segments or wildcards"
                )


class StateSchema(AtlasSchema):
    """Schema for state container."""

    version = fields.Integer(required=True)
    data = fields.Dict(required=True)
    timestamp = fields.DateTime(required=True)
    metadata = fields.Dict(load_default=dict)

    @validates("version")
    def validate_version(self, value: int, **kwargs) -> None:
        """Validate version number.

        Args:
            value: The version value to validate.
            **kwargs: Additional arguments passed by Marshmallow.

        Raises:
            ValidationError: If the version is not positive.
        """
        if value <= 0:
            raise ValidationError("Version must be greater than 0")


class TransitionSchema(AtlasSchema):
    """Schema for state transition."""

    transition_id = fields.UUID(required=True)
    from_state = fields.Dict(required=True)
    to_state = fields.Dict(required=True)
    validator = fields.String(required=True)
    metadata = fields.Dict(load_default=dict)

    @validates_schema
    def validate_transition(self, data: dict[str, Any], **kwargs) -> None:
        """Validate the state transition.

        Args:
            data: The data to validate.
            **kwargs: Additional arguments passed by Marshmallow.

        Raises:
            ValidationError: If the transition is invalid.
        """
        # Ensure from_state and to_state aren't identical
        if data.get("from_state") == data.get("to_state"):
            raise ValidationError("Transition can't have identical from_state and to_state")


class CommandSchema(AtlasSchema):
    """Schema for command pattern."""

    command_id = fields.UUID(required=True)
    name = fields.String(required=True)
    parameters = fields.Dict(load_default=dict)
    target_service = fields.String(required=True)
    is_undoable = fields.Boolean(load_default=False)
    metadata = fields.Dict(load_default=dict)
    status = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(["pending", "executing", "completed", "failed", "cancelled"]),
    )
    timestamp = fields.DateTime(required=True)


class CommandResultSchema(AtlasSchema):
    """Schema for command execution result."""

    result_id = fields.UUID(required=True)
    command_id = fields.UUID(required=True)
    success = fields.Boolean(required=True)
    data = fields.Dict(required=False, allow_none=True)
    error = fields.String(required=False, allow_none=True)
    execution_time = fields.Float(required=True)
    timestamp = fields.DateTime(required=True)


class ResourceSchema(AtlasSchema):
    """Schema for resource lifecycle management."""

    resource_id = fields.UUID(required=True)
    type = fields.String(required=True)
    state = fields.String(
        required=True,
        validate=validate.OneOf(["initializing", "ready", "in_use", "released", "error"]),
    )
    owner_service = fields.String(allow_none=True)
    acquisition_time = fields.DateTime(allow_none=True)
    release_time = fields.DateTime(allow_none=True)
    metadata = fields.Dict(load_default=dict)

    @validates_schema
    def validate_resource(self, data: dict[str, Any], **kwargs) -> None:
        """Validate resource state consistency.

        Args:
            data: The data to validate.
            **kwargs: Additional arguments passed by Marshmallow.

        Raises:
            ValidationError: If the resource state is inconsistent.
        """
        state = data.get("state")
        owner = data.get("owner_service")
        acquisition_time = data.get("acquisition_time")

        # Resource must have owner and acquisition time when in use
        if state == "in_use" and (not owner or not acquisition_time):
            raise ValidationError(
                "Resources in 'in_use' state must have owner_service and acquisition_time"
            )

        # Released resources must have release_time
        if state == "released" and not data.get("release_time"):
            raise ValidationError("Resources in 'released' state must have release_time")


class ComponentConfigSchema(AtlasSchema):
    """Schema for service-enabled component configuration."""
    
    component_id = fields.UUID(required=True)
    component_type = fields.String(required=True)
    services = fields.List(fields.String(), required=True)
    metadata = fields.Dict(load_default=dict)


class MiddlewareSchema(AtlasSchema):
    """Schema for middleware components."""
    
    middleware_id = fields.UUID(required=True)
    name = fields.String(required=True)
    priority = fields.Integer(required=False, load_default=0)
    enabled = fields.Boolean(required=False, load_default=True)
    metadata = fields.Dict(load_default=dict)


# Export schema instances for convenient use
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
component_config_schema = ComponentConfigSchema()
middleware_schema = MiddlewareSchema()