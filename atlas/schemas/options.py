"""
Option and configuration schemas for Atlas.

This module provides Marshmallow schemas for provider options, capability
levels, and configuration structures used throughout the Atlas framework.

This module extends pure schema definitions with post_load methods that import
implementation classes when needed to avoid circular import issues.
"""

from typing import Any, Dict, List, Optional, Set, Type, Union, cast
from enum import Enum

from marshmallow import post_load, pre_load, validates, validates_schema, ValidationError, EXCLUDE

from atlas.schemas.base import AtlasSchema
from atlas.schemas.definitions.options import (
    capability_level_schema as base_capability_level_schema,
    provider_options_schema as base_provider_options_schema,
    provider_retry_config_schema as base_provider_retry_config_schema,
    provider_circuit_breaker_schema as base_provider_circuit_breaker_schema,
    provider_config_schema as base_provider_config_schema,
    KNOWN_CAPABILITIES
)


class CapabilityLevelSchema(base_capability_level_schema.__class__):
    """Schema for capability level values with implementation conversion."""
    
    @post_load
    def make_object(self, data: Union[str, int], **kwargs) -> Any:
        """Convert loaded data into a CapabilityLevel enum.
        
        Args:
            data: The capability level value.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A CapabilityLevel enum value.
            
        Raises:
            ValidationError: If the value is not a valid capability level.
        """
        try:
            # Import here to avoid circular imports
            from atlas.providers.capabilities import CapabilityLevel
            
            # Handle integer values
            if isinstance(data, int):
                return CapabilityLevel(data)
            
            # Handle string values
            if isinstance(data, str):
                # Try to match by name first
                try:
                    return CapabilityLevel[data.upper()]
                except KeyError:
                    # Try to match by value next
                    for level in CapabilityLevel:
                        if level.name.lower() == data.lower():
                            return level
                    
                    # Try to convert to int and match by value
                    try:
                        return CapabilityLevel(int(data))
                    except (ValueError, KeyError):
                        pass
            
            # If we get here, we couldn't match the value
            valid_values = [
                f"{level.name} ({level.value})" for level in CapabilityLevel
            ]
            raise ValidationError(
                f"Invalid capability level: {data}. Must be one of: {', '.join(valid_values)}"
            )
        except Exception as e:
            raise ValidationError(f"Invalid capability level: {data}") from e


class CapabilityValueSchema(base_capability_level_schema.__class__):
    """Schema for capability values with implementation conversion."""
    
    @post_load
    def make_object(self, data: Union[str, int], **kwargs) -> Any:
        """Convert loaded data into a CapabilityLevel enum.
        
        Args:
            data: The capability level value.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A CapabilityLevel enum value.
            
        Raises:
            ValidationError: If the value is not a valid capability level.
        """
        try:
            # Import here to avoid circular imports
            from atlas.providers.capabilities import CapabilityLevel
            
            # Handle integer values
            if isinstance(data, int):
                return CapabilityLevel(data)
            
            # Handle string levels (e.g. "moderate")
            if isinstance(data, str) and data.upper() in CapabilityLevel.__members__:
                return CapabilityLevel[data.upper()]
            
            # Handle numeric string (e.g. "2")
            if isinstance(data, str) and data.isdigit() and 0 <= int(data) <= 4:
                return CapabilityLevel(int(data))
                
            # If we get here, try to do a case-insensitive match 
            if isinstance(data, str):
                data_lower = data.lower()
                for level in CapabilityLevel:
                    if level.name.lower() == data_lower:
                        return level
                        
            # Last resort, try direct conversion (will raise if invalid)
            if isinstance(data, int) or isinstance(data, str) and data.isdigit():
                value = int(data)
                return CapabilityLevel(value)
                
            # If we still haven't returned, it's an invalid value
            raise ValueError(f"Invalid capability level: {data}")
            
        except Exception as e:
            valid_values = [
                f"{level.name} ({level.value})" for level in CapabilityLevel
            ]
            raise ValidationError(
                f"Invalid capability level: {data}. Must be one of: {', '.join(valid_values)}"
            ) from e


class ProviderOptionsSchema(base_provider_options_schema.__class__):
    """Schema for provider capability options with implementation conversion."""
    
    class Meta:
        """Schema metadata configuration."""
        # Exclude unknown fields by default, but preserve existing base class Meta
        unknown = getattr(base_provider_options_schema.__class__.Meta, 'unknown', EXCLUDE)
        
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Convert loaded data into implementation objects.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            The converted object.
        """
        # Import here to avoid circular imports
        from atlas.providers.capabilities import CapabilityLevel
        
        # Convert capability values to CapabilityLevel enums
        if "capabilities" in data and data["capabilities"]:
            capabilities = {}
            
            for cap_name, cap_value in data["capabilities"].items():
                # Skip already converted values
                if isinstance(cap_value, CapabilityLevel):
                    capabilities[cap_name] = cap_value
                    continue
                    
                # Convert using schema
                try:
                    capability_value_schema = CapabilityValueSchema()
                    capabilities[cap_name] = capability_value_schema.load(cap_value)
                except ValidationError:
                    # Fall back to simple conversion for safety
                    if isinstance(cap_value, int) and 0 <= cap_value <= 4:
                        capabilities[cap_name] = CapabilityLevel(cap_value)
                    elif isinstance(cap_value, str) and cap_value.upper() in CapabilityLevel.__members__:
                        capabilities[cap_name] = CapabilityLevel[cap_value.upper()]
                    elif isinstance(cap_value, str) and cap_value.isdigit() and 0 <= int(cap_value) <= 4:
                        capabilities[cap_name] = CapabilityLevel(int(cap_value))
                    else:
                        # Keep as is if we can't convert (will be caught in validation)
                        capabilities[cap_name] = cap_value
            
            data["capabilities"] = capabilities
        
        return data
    
    @validates("capabilities")
    def validate_capabilities(self, capabilities: Dict[str, Any], **kwargs) -> None:
        """Validate capability values.
        
        Args:
            capabilities: The capability dictionary to validate.
            **kwargs: Additional arguments passed to validates method.
            
        Raises:
            ValidationError: If any capability value is invalid.
        """
        if not capabilities:
            return
            
        # Import here to avoid circular imports
        from atlas.providers.capabilities import CapabilityLevel, ALL_CAPABILITIES
            
        # Track validation errors
        errors = {}
            
        # Create schema for validating individual capability values
        capability_schema = CapabilityValueSchema()
        
        # Check each capability and its value
        for cap_name, cap_value in capabilities.items():
            # Skip already converted values
            if isinstance(cap_value, CapabilityLevel):
                continue
                
            # Validate capability name (as a warning, not error)
            # This allows custom capabilities while still validating known ones
            if cap_name not in KNOWN_CAPABILITIES and cap_name not in ALL_CAPABILITIES:
                # Just log a warning, don't raise an error for custom capabilities
                pass
                
            # Validate capability value
            try:
                # Use the schema to validate and convert
                capability_schema.load(cap_value)
            except ValidationError as e:
                errors[f"capabilities.{cap_name}"] = e.messages
        
        # Raise all validation errors at once
        if errors:
            raise ValidationError(errors)


class ProviderRetryConfigSchema(base_provider_retry_config_schema.__class__):
    """Schema for provider retry configuration with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Convert loaded data into implementation objects.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            The converted object with proper typing.
        """
        # Import implementation class here to avoid circular imports
        try:
            from atlas.providers.reliability import RetryConfig
            
            # Create RetryConfig object from validated data
            return RetryConfig(**data)
        except ImportError:
            # If implementation is not available, just return the data
            return data


class ProviderCircuitBreakerSchema(base_provider_circuit_breaker_schema.__class__):
    """Schema for provider circuit breaker configuration with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Convert loaded data into implementation objects.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            The converted object with proper typing.
        """
        # Import implementation class here to avoid circular imports
        try:
            from atlas.providers.reliability import CircuitBreaker
            
            # Create CircuitBreaker object from validated data
            return CircuitBreaker(**data)
        except ImportError:
            # If implementation is not available, just return the data
            return data


class ProviderConfigSchema(base_provider_config_schema.__class__):
    """Schema for provider configuration with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Convert loaded data into implementation objects.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            The converted data with implementation objects.
        """
        # Process nested options with provider-specific schemas
        if "options" in data and data["options"]:
            try:
                # Get provider type
                provider_type = data.get("provider_type", "default")
                
                # Get the appropriate schema based on provider type
                options_schema = PROVIDER_OPTIONS_SCHEMAS.get(
                    provider_type, 
                    PROVIDER_OPTIONS_SCHEMAS["default"]
                )
                
                # Convert options using the provider-specific schema
                data["options"] = options_schema.load(data["options"])
            except ValidationError:
                # If options conversion fails, keep as is (validation will catch it)
                pass
        
        # Process nested retry_config
        if "retry_config" in data and data["retry_config"]:
            try:
                # Convert retry_config
                data["retry_config"] = provider_retry_config_schema.load(data["retry_config"])
            except ValidationError:
                # If retry_config conversion fails, keep as is (validation will catch it) 
                pass
        
        # Process nested circuit_breaker
        if "circuit_breaker" in data and data["circuit_breaker"]:
            try:
                # Convert circuit_breaker
                data["circuit_breaker"] = provider_circuit_breaker_schema.load(data["circuit_breaker"])
            except ValidationError:
                # If circuit_breaker conversion fails, keep as is (validation will catch it)
                pass
        
        return data
        
    @validates_schema
    def validate_provider_specific_config(self, data: Dict[str, Any], **kwargs) -> None:
        """Validate provider-specific configuration.
        
        Args:
            data: The data to validate.
            **kwargs: Additional arguments.
            
        Raises:
            ValidationError: If provider configuration is invalid.
        """
        # Additional provider-specific validation
        provider_type = data.get("provider_type")
        
        # Validate options based on provider type if present
        if "options" in data and data["options"]:
            options = data["options"]
            
            # Skip validation if options is not a dict
            if not isinstance(options, dict):
                return
                
            # Apply provider-specific validation
            errors = {}
            
            if provider_type == "anthropic":
                # Anthropic-specific validation
                if "functions" in options or "tools" in options:
                    errors["options"] = "Anthropic provider does not support functions or tools"
                    
            elif provider_type == "openai":
                # OpenAI-specific validation
                if "functions" in options and "tools" in options:
                    errors["options"] = "OpenAI provider cannot use both functions and tools simultaneously"
                    
            elif provider_type == "ollama":
                # Ollama-specific validation
                if "functions" in options or "tools" in options:
                    errors["options"] = "Ollama provider does not support functions or tools"
            
            # Raise validation errors if any were found
            if errors:
                raise ValidationError(errors)


# Create schema instances with implementation conversion
capability_level_schema = CapabilityLevelSchema()
capability_value_schema = CapabilityValueSchema()
provider_options_schema = ProviderOptionsSchema()

# Provider-specific option schemas
from atlas.schemas.definitions.options import (
    AnthropicOptionsSchema as BaseAnthropicOptionsSchema,
    OpenAIOptionsSchema as BaseOpenAIOptionsSchema,
    OllamaOptionsSchema as BaseOllamaOptionsSchema
)

class AnthropicOptionsSchema(BaseAnthropicOptionsSchema):
    """Schema for Anthropic-specific provider options with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Convert loaded data into implementation objects.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            The converted options dictionary.
        """
        # First apply the general provider options conversion
        data = ProviderOptionsSchema.make_object(self, data, **kwargs)
        
        return data

class OpenAIOptionsSchema(BaseOpenAIOptionsSchema):
    """Schema for OpenAI-specific provider options with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Convert loaded data into implementation objects.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            The converted options dictionary.
        """
        # First apply the general provider options conversion
        data = ProviderOptionsSchema.make_object(self, data, **kwargs)
        
        return data

class OllamaOptionsSchema(BaseOllamaOptionsSchema):
    """Schema for Ollama-specific provider options with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Convert loaded data into implementation objects.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            The converted options dictionary.
        """
        # First apply the general provider options conversion
        data = ProviderOptionsSchema.make_object(self, data, **kwargs)
        
        return data

# Create provider-specific schema instances
anthropic_options_schema = AnthropicOptionsSchema()
openai_options_schema = OpenAIOptionsSchema()
ollama_options_schema = OllamaOptionsSchema()

# Other schema instances
provider_retry_config_schema = ProviderRetryConfigSchema()
provider_circuit_breaker_schema = ProviderCircuitBreakerSchema()
provider_config_schema = ProviderConfigSchema()

# Map of provider type to specific options schema
PROVIDER_OPTIONS_SCHEMAS = {
    "anthropic": anthropic_options_schema,
    "openai": openai_options_schema,
    "ollama": ollama_options_schema,
    # Default to the base schema for unknown providers
    "default": provider_options_schema,
}