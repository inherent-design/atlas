"""
Configuration schemas for Atlas.

This module provides Marshmallow schemas for Atlas configuration structures,
including environment variables, settings, and preferences.
"""

from typing import Any, Dict, List, Optional, Set, Type, Union
from enum import Enum

from marshmallow import (
    Schema, 
    fields, 
    post_load, 
    pre_load, 
    validates, 
    validates_schema,
    ValidationError,
    EXCLUDE
)

from atlas.schemas.base import AtlasSchema, EnumField, JsonField
from atlas.schemas.options import provider_config_schema


class DatabaseConfigSchema(AtlasSchema):
    """Schema for database configuration options."""
    
    provider = fields.String(required=True)
    connection_string = fields.String(required=False)
    host = fields.String(required=False)
    port = fields.Integer(required=False)
    username = fields.String(required=False)
    password = fields.String(required=False)
    database_name = fields.String(required=False)
    collection_name = fields.String(required=False)
    persistent = fields.Boolean(required=False, load_default=True)
    options = fields.Dict(keys=fields.String(), values=fields.Raw(), required=False)


class LoggingConfigSchema(AtlasSchema):
    """Schema for logging configuration options."""
    
    level = fields.String(
        required=False, 
        validate=lambda x: x.upper() in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    )
    format = fields.String(required=False)
    file = fields.String(required=False)
    structured = fields.Boolean(required=False)
    console = fields.Boolean(required=False)


class TelemetryConfigSchema(AtlasSchema):
    """Schema for telemetry configuration options."""
    
    enabled = fields.Boolean(required=False, load_default=False)
    endpoint = fields.String(required=False)
    service_name = fields.String(required=False)
    sample_rate = fields.Float(required=False, validate=lambda x: 0 <= x <= 1)


class AtlasConfigSchema(AtlasSchema):
    """Schema for the complete Atlas configuration."""
    
    providers = fields.Dict(
        keys=fields.String(),
        values=fields.Nested(provider_config_schema),
        required=False
    )
    database = fields.Nested(DatabaseConfigSchema, required=False)
    logging = fields.Nested(LoggingConfigSchema, required=False)
    telemetry = fields.Nested(TelemetryConfigSchema, required=False)
    default_provider = fields.String(required=False)
    default_model = fields.String(required=False)
    api_keys = fields.Dict(keys=fields.String(), values=fields.String(), required=False)
    
    @validates_schema
    def validate_default_provider(self, data: Dict[str, Any], **kwargs) -> None:
        """Validate that the default provider exists in the providers list.
        
        Args:
            data: The data to validate.
            **kwargs: Additional arguments.
            
        Raises:
            ValidationError: If the default provider doesn't exist.
        """
        default_provider = data.get("default_provider")
        providers = data.get("providers", {})
        
        if default_provider and providers and default_provider not in providers:
            raise ValidationError(
                f"Default provider '{default_provider}' not found in providers list"
            )


# Export schema instances for convenient use
database_config_schema = DatabaseConfigSchema()
logging_config_schema = LoggingConfigSchema()
telemetry_config_schema = TelemetryConfigSchema()
atlas_config_schema = AtlasConfigSchema()