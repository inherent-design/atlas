"""
Pure schema definitions for option-related types.

This module contains schema definitions without any post_load methods or references
to implementation classes, avoiding circular imports. These schemas define the 
structure and validation rules for option types but don't handle conversion
to actual implementation objects.
"""

from typing import Any, Dict, List, Optional, Union, Set
from enum import Enum

from marshmallow import fields, pre_load, validates, validates_schema, ValidationError

from atlas.schemas.base import AtlasSchema, EnumField, JsonField


# Capability constants (duplicated from capabilities.py to avoid import cycles)
KNOWN_CAPABILITIES = {
    # Operational capabilities
    "inexpensive", "efficient", "premium", "standard", "streaming", "vision",
    
    # Task capabilities
    "reasoning", "logic", "math", "analysis", "code", "creative", 
    "summarization", "extraction", "formatting", "tool_use", "json_output",
    
    # Domain capabilities
    "science", "finance", "legal", "medical", "technical", "multilingual"
}


class CapabilityLevelSchema(AtlasSchema):
    """Schema for capability level values."""
    
    @pre_load
    def process_input(self, data: Any, **kwargs) -> Union[str, int]:
        """Pre-process input to handle different capability level formats.
        
        Args:
            data: The data to load.
            **kwargs: Additional arguments.
            
        Returns:
            Processed capability level.
        """
        if hasattr(data, 'value'):  # Handle enum objects
            return data.value
        
        if isinstance(data, str):
            # Handle string capability levels (e.g., "required", "moderate")
            return data.lower()
        
        # Handle numerical values (0-4)
        if isinstance(data, int) and 0 <= data <= 4:
            return data
            
        # Handle numerical values as strings
        if isinstance(data, str) and data.isdigit() and 0 <= int(data) <= 4:
            return int(data)
            
        return data
    
    @validates_schema
    def validate_level(self, data: Any, **kwargs) -> None:
        """Validate capability level values.
        
        Args:
            data: The data to validate.
            **kwargs: Additional arguments.
            
        Raises:
            ValidationError: If the level is not a valid capability level.
        """
        # When validating just a raw value
        if not isinstance(data, dict):
            value = data
            
            # Check numerical values
            if isinstance(value, int) and 0 <= value <= 4:
                return
                
            # Check string values that map to known levels
            if isinstance(value, str):
                valid_names = {"none", "basic", "moderate", "strong", "exceptional"}
                if value.lower() in valid_names:
                    return
                    
                # Check for numeric strings
                if value.isdigit() and 0 <= int(value) <= 4:
                    return
            
            raise ValidationError(
                f"Invalid capability level: {value}. Must be 0-4 or one of: none, basic, moderate, strong, exceptional"
            )


class CapabilityValueField(fields.Field):
    """Field for capability values that supports different formats (int, string, enum)."""
    
    def _serialize(self, value: Any, attr: str, obj: Any, **kwargs) -> Any:
        """Serialize capability value.
        
        Args:
            value: The value to serialize.
            attr: The attribute name.
            obj: The object being serialized.
            **kwargs: Additional arguments.
            
        Returns:
            Serialized value.
        """
        if hasattr(value, 'value'):  # Handle enum objects
            return value.value
        return value
    
    def _deserialize(self, value: Any, attr: Optional[str], data: Optional[Dict[str, Any]], **kwargs) -> Any:
        """Deserialize capability value.
        
        Args:
            value: The value to deserialize.
            attr: The attribute name.
            data: The raw data being deserialized.
            **kwargs: Additional arguments.
            
        Returns:
            Deserialized value.
            
        Raises:
            ValidationError: If value cannot be converted to a valid capability level.
        """
        try:
            # Handle string values like "moderate", "strong"
            if isinstance(value, str):
                value_lower = value.lower()
                level_map = {
                    "none": 0, "basic": 1, "moderate": 2, "strong": 3, "exceptional": 4
                }
                
                # Check for named levels
                if value_lower in level_map:
                    return level_map[value_lower]
                    
                # Try to convert numeric strings
                if value.isdigit():
                    numeric_value = int(value)
                    if 0 <= numeric_value <= 4:
                        return numeric_value
            
            # Handle integer values directly
            if isinstance(value, int) and 0 <= value <= 4:
                return value
                
            # If we get here, it's an invalid value
            raise ValidationError(
                f"Invalid capability level: {value}. Must be 0-4 or one of: none, basic, moderate, strong, exceptional"
            )
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid capability level: {value}")


class ProviderOptionsSchema(AtlasSchema):
    """Schema for provider capability options."""
    
    # Common model generation options
    temperature = fields.Float(required=False, allow_none=True, 
                              validate=lambda x: x is None or 0 <= x <= 1)
    top_p = fields.Float(required=False, allow_none=True,
                        validate=lambda x: x is None or 0 <= x <= 1)
    top_k = fields.Integer(required=False, allow_none=True,
                         validate=lambda x: x is None or x > 0)
    frequency_penalty = fields.Float(required=False, allow_none=True, 
                                   validate=lambda x: x is None or 0 <= x <= 2)
    presence_penalty = fields.Float(required=False, allow_none=True,
                                  validate=lambda x: x is None or 0 <= x <= 2)
    max_tokens = fields.Integer(required=False, allow_none=True,
                              validate=lambda x: x is None or x > 0)
    
    # Response format options
    response_format = fields.Dict(required=False, allow_none=True)
    
    # Stream control
    stream = fields.Boolean(required=False, allow_none=True)
    
    # Using a dict field with custom validation for capabilities
    capabilities = fields.Dict(
        keys=fields.String(),
        values=CapabilityValueField(),
        required=False,
        allow_none=True
    )
    
    @pre_load
    def process_capabilities(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Pre-process capabilities to standardize format.
        
        Args:
            data: The data to load.
            **kwargs: Additional arguments.
            
        Returns:
            Processed data dictionary.
        """
        if not isinstance(data, dict):
            return data
            
        if "capabilities" not in data:
            # Create a capabilities dict if not present
            capabilities = {}
            
            # Extract well-known model parameters
            known_params = {
                "temperature", "top_p", "top_k", "frequency_penalty", 
                "presence_penalty", "max_tokens", "response_format",
                "stream", "capabilities", "provider_type", "model_name"
            }
            
            # Move any capability-like keys to the capabilities dict
            for key, value in list(data.items()):
                if key not in known_params and key in KNOWN_CAPABILITIES:
                    capabilities[key] = value
                    data.pop(key)
            
            if capabilities:
                data["capabilities"] = capabilities
        
        return data
    
    @validates("capabilities")
    def validate_capabilities(self, capabilities: Dict[str, Any], **kwargs) -> None:
        """Validate capability entries.
        
        Args:
            capabilities: The capabilities dictionary.
            **kwargs: Additional arguments.
            
        Raises:
            ValidationError: If any capability is invalid.
        """
        if not capabilities:
            return
            
        if not isinstance(capabilities, dict):
            raise ValidationError("Capabilities must be a dictionary")
            
        # Track validation errors
        errors = {}
            
        # Check each capability and its value
        for cap_name, cap_value in capabilities.items():
            # Validate capability name
            if not isinstance(cap_name, str):
                errors[f"capabilities.{cap_name}"] = "Capability name must be a string"
                continue
                
            # Warn about unknown capabilities
            if cap_name not in KNOWN_CAPABILITIES:
                # This is a warning, not an error - we allow custom capabilities
                pass
                
            # Validate capability value
            try:
                # Check if value is a valid level
                if isinstance(cap_value, int) and 0 <= cap_value <= 4:
                    continue
                    
                if isinstance(cap_value, str):
                    value_lower = cap_value.lower()
                    if value_lower in {"none", "basic", "moderate", "strong", "exceptional"}:
                        continue
                    if cap_value.isdigit() and 0 <= int(cap_value) <= 4:
                        continue
                
                # If we reach here, the value is invalid
                errors[f"capabilities.{cap_name}"] = (
                    f"Invalid capability value: {cap_value}. Must be 0-4 or one of: "
                    "none, basic, moderate, strong, exceptional"
                )
            except (ValueError, TypeError):
                errors[f"capabilities.{cap_name}"] = f"Invalid capability value: {cap_value}"
        
        # Raise all validation errors at once
        if errors:
            raise ValidationError(errors)
            
    @validates("response_format")
    def validate_response_format(self, response_format: Dict[str, Any], **kwargs) -> None:
        """Validate response format options.
        
        Args:
            response_format: The response format dictionary.
            **kwargs: Additional arguments.
            
        Raises:
            ValidationError: If response format is invalid.
        """
        if not response_format:
            return
            
        if not isinstance(response_format, dict):
            raise ValidationError("Response format must be a dictionary")
            
        # Validate required type field
        if "type" not in response_format:
            raise ValidationError({"response_format.type": "Response format must include a 'type' field"})
            
        # Validate type field value
        valid_types = {"text", "json", "json_object"}
        if response_format.get("type") not in valid_types:
            raise ValidationError({
                "response_format.type": f"Response format type must be one of: {', '.join(valid_types)}"
            })
            
        # Validate schema field if present for json_object type
        if response_format.get("type") == "json_object" and "schema" in response_format:
            schema = response_format.get("schema")
            if not isinstance(schema, dict):
                raise ValidationError({"response_format.schema": "JSON schema must be a dictionary"})


class AnthropicOptionsSchema(ProviderOptionsSchema):
    """Schema for Anthropic-specific provider options."""
    
    # Anthropic-specific options
    system = fields.String(required=False, allow_none=True)
    
    @validates_schema
    def validate_anthropic_options(self, data: Dict[str, Any], **kwargs) -> None:
        """Validate Anthropic-specific options.
        
        Args:
            data: The data to validate.
            **kwargs: Additional arguments.
            
        Raises:
            ValidationError: If options are incompatible.
        """
        # Validate temperature is within Anthropic's bounds
        if "temperature" in data and data["temperature"] is not None:
            temp = data["temperature"]
            if not 0 <= temp <= 1:
                raise ValidationError(
                    {"temperature": f"Temperature must be between 0 and 1 for Anthropic, got {temp}"}
                )


class OpenAIOptionsSchema(ProviderOptionsSchema):
    """Schema for OpenAI-specific provider options."""
    
    # OpenAI-specific options
    functions = fields.List(fields.Dict, required=False, allow_none=True)
    function_call = fields.Raw(required=False, allow_none=True)  # Can be "auto", "none", or a dict
    tools = fields.List(fields.Dict, required=False, allow_none=True)
    tool_choice = fields.Raw(required=False, allow_none=True)  # Can be "auto", "none", or a dict
    
    @validates_schema
    def validate_openai_options(self, data: Dict[str, Any], **kwargs) -> None:
        """Validate OpenAI-specific options.
        
        Args:
            data: The data to validate.
            **kwargs: Additional arguments.
            
        Raises:
            ValidationError: If options are incompatible.
        """
        # Validate functions and tools are not used together
        if data.get("functions") and data.get("tools"):
            raise ValidationError(
                "OpenAI options cannot include both 'functions' and 'tools' - use only one"
            )
            
        # Validate function_call if functions are provided
        if data.get("functions") and data.get("function_call"):
            function_call = data["function_call"]
            if not (isinstance(function_call, str) or isinstance(function_call, dict)):
                raise ValidationError(
                    {"function_call": "Function call must be a string ('auto'/'none') or a dictionary"}
                )
                
        # Validate tool_choice if tools are provided
        if data.get("tools") and data.get("tool_choice"):
            tool_choice = data["tool_choice"]
            if not (isinstance(tool_choice, str) or isinstance(tool_choice, dict)):
                raise ValidationError(
                    {"tool_choice": "Tool choice must be a string ('auto'/'none') or a dictionary"}
                )


class OllamaOptionsSchema(ProviderOptionsSchema):
    """Schema for Ollama-specific provider options."""
    
    # Ollama-specific options
    mirostat = fields.Integer(required=False, allow_none=True,
                            validate=lambda x: x is None or 0 <= x <= 2)
    mirostat_eta = fields.Float(required=False, allow_none=True,
                              validate=lambda x: x is None or x > 0)
    mirostat_tau = fields.Float(required=False, allow_none=True,
                              validate=lambda x: x is None or x > 0)
    num_ctx = fields.Integer(required=False, allow_none=True,
                           validate=lambda x: x is None or x > 0)
    repeat_last_n = fields.Integer(required=False, allow_none=True,
                                 validate=lambda x: x is None or x >= 0)
    repeat_penalty = fields.Float(required=False, allow_none=True,
                                validate=lambda x: x is None or x > 0)
    seed = fields.Integer(required=False, allow_none=True)
    stop = fields.List(fields.String(), required=False, allow_none=True)
    tfs_z = fields.Float(required=False, allow_none=True)
    num_predict = fields.Integer(required=False, allow_none=True,
                               validate=lambda x: x is None or x > 0)


class ProviderRetryConfigSchema(AtlasSchema):
    """Schema for provider retry configuration."""
    
    max_retries = fields.Integer(required=True, validate=lambda x: x >= 0)
    initial_delay = fields.Float(required=True, validate=lambda x: x > 0)
    max_delay = fields.Float(required=True, validate=lambda x: x > 0)
    backoff_factor = fields.Float(required=True, validate=lambda x: x >= 1)
    jitter_factor = fields.Float(required=True, validate=lambda x: 0 <= x <= 1)
    retryable_errors = fields.List(fields.String(), required=False, allow_none=True)
    
    @validates_schema
    def validate_delays(self, data: Dict[str, Any], **kwargs) -> None:
        """Validate delay values.
        
        Args:
            data: The data to validate.
            **kwargs: Additional arguments.
            
        Raises:
            ValidationError: If delay values are inconsistent.
        """
        initial_delay = data.get("initial_delay", 0)
        max_delay = data.get("max_delay", 0)
        
        if initial_delay > max_delay:
            raise ValidationError(
                "initial_delay must be less than or equal to max_delay"
            )


class ProviderCircuitBreakerSchema(AtlasSchema):
    """Schema for provider circuit breaker configuration."""
    
    failure_threshold = fields.Integer(required=True, validate=lambda x: x > 0)
    recovery_timeout = fields.Float(required=True, validate=lambda x: x > 0)
    test_requests = fields.Integer(required=True, validate=lambda x: x > 0)
    reset_timeout = fields.Float(required=True, validate=lambda x: x > 0)


class ProviderConfigSchema(AtlasSchema):
    """Schema for provider configuration."""
    
    provider_type = fields.String(required=True)
    model_name = fields.String(required=True)
    api_key = fields.String(required=False, allow_none=True)
    api_base = fields.String(required=False, allow_none=True)
    max_tokens = fields.Integer(required=False, allow_none=True, validate=lambda x: x is None or x > 0)
    retry_config = fields.Nested(ProviderRetryConfigSchema, required=False, allow_none=True)
    circuit_breaker = fields.Nested(ProviderCircuitBreakerSchema, required=False, allow_none=True)
    options = fields.Dict(required=False, allow_none=True)
    
    @validates_schema
    def validate_provider_config(self, data: Dict[str, Any], **kwargs) -> None:
        """Validate provider configuration.
        
        Args:
            data: The data to validate.
            **kwargs: Additional arguments.
            
        Raises:
            ValidationError: If provider configuration is inconsistent.
        """
        provider_type = data.get("provider_type")
        
        # Validate API key and base depending on provider type
        if provider_type in {"openai", "anthropic"}:
            if not data.get("api_key") and "api_key" in data:
                raise ValidationError(
                    {"api_key": f"API key is required for {provider_type} provider"}
                )
        
        # Validate options based on provider type
        if "options" in data and data["options"]:
            options = data["options"]
            
            # Use the base provider options schema for options validation
            # Provider-specific validation will be handled by higher-level schemas
            try:
                # For the base schema, we just do some basic validation
                if not isinstance(options, dict):
                    raise ValidationError({"options": "Options must be a dictionary"})
                
                # Validate common fields that exist in all provider options
                if "temperature" in options and options["temperature"] is not None:
                    temp = options["temperature"]
                    if not isinstance(temp, (int, float)) or temp < 0 or temp > 1:
                        raise ValidationError(
                            {"options.temperature": f"Temperature must be between 0 and 1, got {temp}"}
                        )
                
                if "max_tokens" in options and options["max_tokens"] is not None:
                    max_tokens = options["max_tokens"]
                    if not isinstance(max_tokens, int) or max_tokens <= 0:
                        raise ValidationError(
                            {"options.max_tokens": f"Max tokens must be a positive integer, got {max_tokens}"}
                        )
                
            except ValidationError as e:
                raise ValidationError({"options": e.messages})


# Export schema instances for convenient use
capability_level_schema = CapabilityLevelSchema()
provider_options_schema = ProviderOptionsSchema()
provider_retry_config_schema = ProviderRetryConfigSchema()
provider_circuit_breaker_schema = ProviderCircuitBreakerSchema()
provider_config_schema = ProviderConfigSchema()