"""
Pure schema definitions for streaming-related types.

This module contains schema definitions without any post_load methods or references
to implementation classes, avoiding circular imports. These schemas define the 
structure and validation rules for streaming types but don't handle conversion
to actual implementation objects.
"""

from typing import Any, Dict, List, Optional, Union
from marshmallow import fields, pre_load, validates, validates_schema, ValidationError

from atlas.schemas.base import AtlasSchema, EnumField, JsonField


class StreamStateSchema(AtlasSchema):
    """Schema for stream state enum values."""
    
    value = fields.String(required=True)
    
    @validates("value")
    def validate_value(self, value: str, **kwargs) -> None:
        """Validate that the value is a valid stream state.
        
        Args:
            value: The stream state value to validate.
            **kwargs: Additional arguments passed by Marshmallow.
            
        Raises:
            ValidationError: If the value is not a valid stream state.
        """
        valid_states = [
            "initializing", "active", "paused", "cancelled", "completed", "error"
        ]
        
        if value not in valid_states:
            raise ValidationError(
                f"Invalid stream state '{value}'. Must be one of: {', '.join(valid_states)}"
            )


class StreamMetricsSchema(AtlasSchema):
    """Schema for stream performance metrics."""
    
    start_time = fields.Float(required=False, allow_none=True)
    end_time = fields.Float(required=False, allow_none=True)
    tokens_processed = fields.Integer(required=False)
    chars_processed = fields.Integer(required=False)
    chunks_processed = fields.Integer(required=False)
    avg_token_per_sec = fields.Float(required=False)
    total_tokens = fields.Integer(required=False)
    
    @validates_schema
    def validate_timestamps(self, data: Dict[str, Any], **kwargs) -> None:
        """Validate that end_time is after start_time if both are present.
        
        Args:
            data: The data to validate.
            **kwargs: Additional arguments.
            
        Raises:
            ValidationError: If end_time is before start_time.
        """
        start_time = data.get("start_time")
        end_time = data.get("end_time")
        
        if start_time is not None and end_time is not None:
            if end_time < start_time:
                raise ValidationError("End time must be after start time")


class StreamControlSchema(AtlasSchema):
    """Schema for stream control interface."""
    
    state = fields.String(required=True)
    can_pause = fields.Boolean(required=True)
    can_resume = fields.Boolean(required=True)
    can_cancel = fields.Boolean(required=True)
    
    @validates("state")
    def validate_state(self, value: str, **kwargs) -> None:
        """Validate the state value.
        
        Args:
            value: The state value to validate.
            **kwargs: Additional arguments passed by Marshmallow.
            
        Raises:
            ValidationError: If the value is not a valid stream state.
        """
        valid_states = [
            "initializing", "active", "paused", "cancelled", "completed", "error"
        ]
        
        if value not in valid_states:
            raise ValidationError(
                f"Invalid stream state '{value}'. Must be one of: {', '.join(valid_states)}"
            )


class StreamOperationResultSchema(AtlasSchema):
    """Schema for stream operation results."""
    
    success = fields.Boolean(required=True)
    state = fields.String(required=True)
    error = fields.String(required=False, allow_none=True)
    
    @validates("state")
    def validate_state(self, value: str, **kwargs) -> None:
        """Validate the state value.
        
        Args:
            value: The state value to validate.
            **kwargs: Additional arguments passed by Marshmallow.
            
        Raises:
            ValidationError: If the value is not a valid stream state.
        """
        valid_states = [
            "initializing", "active", "paused", "cancelled", "completed", "error"
        ]
        
        if value not in valid_states:
            raise ValidationError(
                f"Invalid stream state '{value}'. Must be one of: {', '.join(valid_states)}"
            )


class StreamStateTransitionSchema(AtlasSchema):
    """Schema for stream state transitions."""
    
    from_state = fields.String(required=True)
    to_state = fields.String(required=True)
    trigger = fields.String(required=True)
    
    @validates("from_state")
    def validate_from_state(self, value: str, **kwargs) -> None:
        """Validate the from_state value.
        
        Args:
            value: The from_state value to validate.
            **kwargs: Additional arguments passed by Marshmallow.
            
        Raises:
            ValidationError: If the value is not a valid stream state.
        """
        valid_states = [
            "initializing", "active", "paused", "cancelled", "completed", "error"
        ]
        
        if value not in valid_states:
            raise ValidationError(
                f"Invalid stream state '{value}'. Must be one of: {', '.join(valid_states)}"
            )
    
    @validates("to_state")
    def validate_to_state(self, value: str, **kwargs) -> None:
        """Validate the to_state value.
        
        Args:
            value: The to_state value to validate.
            **kwargs: Additional arguments passed by Marshmallow.
            
        Raises:
            ValidationError: If the value is not a valid stream state.
        """
        valid_states = [
            "initializing", "active", "paused", "cancelled", "completed", "error"
        ]
        
        if value not in valid_states:
            raise ValidationError(
                f"Invalid stream state '{value}'. Must be one of: {', '.join(valid_states)}"
            )
    
    @validates("trigger")
    def validate_trigger(self, value: str, **kwargs) -> None:
        """Validate the trigger value.
        
        Args:
            value: The trigger value to validate.
            **kwargs: Additional arguments passed by Marshmallow.
            
        Raises:
            ValidationError: If the value is not a valid trigger.
        """
        valid_triggers = [
            "initialize", "start", "pause", "resume", "cancel", "complete", "error", "reset"
        ]
        
        if value not in valid_triggers:
            raise ValidationError(
                f"Invalid trigger '{value}'. Must be one of: {', '.join(valid_triggers)}"
            )
    
    @validates_schema
    def validate_transition(self, data: Dict[str, Any], **kwargs) -> None:
        """Validate that the state transition is valid.
        
        Args:
            data: The data to validate.
            **kwargs: Additional arguments.
            
        Raises:
            ValidationError: If the transition is invalid.
        """
        from_state = data.get("from_state")
        to_state = data.get("to_state")
        trigger = data.get("trigger")
        
        # Valid transitions (from_state -> trigger -> to_state)
        valid_transitions = {
            "initializing": {
                "start": "active",
                "error": "error"
            },
            "active": {
                "pause": "paused",
                "cancel": "cancelled",
                "complete": "completed",
                "error": "error"
            },
            "paused": {
                "resume": "active",
                "cancel": "cancelled",
                "error": "error"
            },
            "cancelled": {
                "reset": "initializing"
            },
            "completed": {
                "reset": "initializing"
            },
            "error": {
                "reset": "initializing"
            }
        }
        
        # Check if the transition is valid
        if from_state in valid_transitions and trigger in valid_transitions[from_state]:
            expected_to_state = valid_transitions[from_state][trigger]
            if to_state != expected_to_state:
                raise ValidationError(
                    f"Invalid state transition: {from_state} -> {trigger} -> {to_state}. "
                    f"Expected {from_state} -> {trigger} -> {expected_to_state}"
                )
        else:
            raise ValidationError(
                f"Invalid state transition: {from_state} -> {trigger} -> {to_state}"
            )


class StreamBufferConfigSchema(AtlasSchema):
    """Schema for stream buffer configuration."""
    
    max_buffer_size = fields.Integer(required=False)
    paused = fields.Boolean(required=False)
    closed = fields.Boolean(required=False)


class RateLimitedBufferConfigSchema(StreamBufferConfigSchema):
    """Schema for rate-limited buffer configuration."""
    
    tokens_per_second = fields.Float(required=False, allow_none=True)
    chars_per_token = fields.Integer(required=False)
    
    @validates("tokens_per_second")
    def validate_tokens_per_second(self, value: Optional[float], **kwargs) -> None:
        """Validate tokens_per_second value.
        
        Args:
            value: The tokens_per_second value to validate.
            **kwargs: Additional arguments passed by Marshmallow.
            
        Raises:
            ValidationError: If the value is negative.
        """
        if value is not None and value < 0:
            raise ValidationError("Tokens per second must be greater than or equal to 0")


class BatchingBufferConfigSchema(StreamBufferConfigSchema):
    """Schema for batching buffer configuration."""
    
    batch_size = fields.Integer(required=False, allow_none=True)
    batch_timeout = fields.Float(required=False, allow_none=True)
    batch_delimiter = fields.String(required=False, allow_none=True)
    
    @validates("batch_size")
    def validate_batch_size(self, value: Optional[int], **kwargs) -> None:
        """Validate batch_size value.
        
        Args:
            value: The batch_size value to validate.
            **kwargs: Additional arguments passed by Marshmallow.
            
        Raises:
            ValidationError: If the value is negative.
        """
        if value is not None and value <= 0:
            raise ValidationError("Batch size must be greater than 0")
    
    @validates("batch_timeout")
    def validate_batch_timeout(self, value: Optional[float], **kwargs) -> None:
        """Validate batch_timeout value.
        
        Args:
            value: The batch_timeout value to validate.
            **kwargs: Additional arguments passed by Marshmallow.
            
        Raises:
            ValidationError: If the value is negative.
        """
        if value is not None and value <= 0:
            raise ValidationError("Batch timeout must be greater than 0")


class StreamHandlerConfigSchema(AtlasSchema):
    """Schema for stream handler configuration."""
    
    content = fields.String(required=False)
    provider = fields.String(required=True)
    model = fields.String(required=True)
    delay_ms = fields.Integer(required=False)
    
    @validates("delay_ms")
    def validate_delay_ms(self, value: int, **kwargs) -> None:
        """Validate delay_ms value.
        
        Args:
            value: The delay_ms value to validate.
            **kwargs: Additional arguments passed by Marshmallow.
            
        Raises:
            ValidationError: If the value is negative.
        """
        if value < 0:
            raise ValidationError("Delay must be greater than or equal to 0")


class EnhancedStreamHandlerConfigSchema(StreamHandlerConfigSchema):
    """Schema for enhanced stream handler configuration."""
    
    max_buffer_size = fields.Integer(required=False)
    rate_limit = fields.Float(required=False, allow_none=True)
    
    @validates("max_buffer_size")
    def validate_max_buffer_size(self, value: int, **kwargs) -> None:
        """Validate max_buffer_size value.
        
        Args:
            value: The max_buffer_size value to validate.
            **kwargs: Additional arguments passed by Marshmallow.
            
        Raises:
            ValidationError: If the value is not positive.
        """
        if value <= 0:
            raise ValidationError("Maximum buffer size must be greater than 0")
    
    @validates("rate_limit")
    def validate_rate_limit(self, value: Optional[float], **kwargs) -> None:
        """Validate rate_limit value.
        
        Args:
            value: The rate_limit value to validate.
            **kwargs: Additional arguments passed by Marshmallow.
            
        Raises:
            ValidationError: If the value is not positive.
        """
        if value is not None and value <= 0:
            raise ValidationError("Rate limit must be greater than 0")


class StringStreamHandlerConfigSchema(EnhancedStreamHandlerConfigSchema):
    """Schema for string stream handler configuration."""
    
    chunk_size = fields.Integer(required=False)
    delay_sec = fields.Float(required=False)
    
    @validates("chunk_size")
    def validate_chunk_size(self, value: int, **kwargs) -> None:
        """Validate chunk_size value.
        
        Args:
            value: The chunk_size value to validate.
            **kwargs: Additional arguments passed by Marshmallow.
            
        Raises:
            ValidationError: If the value is not positive.
        """
        if value <= 0:
            raise ValidationError("Chunk size must be greater than 0")
    
    @validates("delay_sec")
    def validate_delay_sec(self, value: float, **kwargs) -> None:
        """Validate delay_sec value.
        
        Args:
            value: The delay_sec value to validate.
            **kwargs: Additional arguments passed by Marshmallow.
            
        Raises:
            ValidationError: If the value is negative.
        """
        if value < 0:
            raise ValidationError("Delay must be greater than or equal to 0")


# Export schema instances for convenient use
stream_state_schema = StreamStateSchema()
stream_metrics_schema = StreamMetricsSchema()
stream_control_schema = StreamControlSchema()
stream_operation_result_schema = StreamOperationResultSchema()
stream_state_transition_schema = StreamStateTransitionSchema()
stream_buffer_config_schema = StreamBufferConfigSchema()
rate_limited_buffer_config_schema = RateLimitedBufferConfigSchema()
batching_buffer_config_schema = BatchingBufferConfigSchema()
stream_handler_config_schema = StreamHandlerConfigSchema()
enhanced_stream_handler_config_schema = EnhancedStreamHandlerConfigSchema()
string_stream_handler_config_schema = StringStreamHandlerConfigSchema()