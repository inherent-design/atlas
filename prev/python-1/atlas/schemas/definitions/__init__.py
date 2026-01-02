"""
Schema definitions package for Atlas.

This package contains pure schema definitions without circular dependencies.
These schemas define structure and validation rules but don't handle conversion
to implementation classes directly to avoid circular imports.
"""

from atlas.schemas.definitions.services import (
    batching_buffer_config_schema,
    buffer_config_schema,
    buffer_item_schema,
    command_result_schema,
    command_schema,
    event_schema,
    rate_limited_buffer_config_schema,
    resource_schema,
    service_schema,
    state_schema,
    subscription_schema,
    transition_schema,
)

__all__ = [
    # Services schemas
    "service_schema",
    "buffer_config_schema",
    "buffer_item_schema",
    "rate_limited_buffer_config_schema",
    "batching_buffer_config_schema",
    "event_schema",
    "subscription_schema",
    "state_schema",
    "transition_schema",
    "command_schema",
    "command_result_schema",
    "resource_schema",
]
