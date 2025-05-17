"""
Streaming component schemas for Atlas.

This module provides Marshmallow schemas for streaming-related structures,
including stream handlers, buffers, and control interfaces.

This module extends pure schema definitions with post_load methods
that convert validated data into actual implementation objects.
"""

from typing import Any, Dict, List, Optional, Type, Union
from enum import Enum

from marshmallow import (
    fields,
    post_load, 
    validates, 
    validates_schema,
    ValidationError
)

from atlas.schemas.base import AtlasSchema, EnumField
from atlas.schemas.definitions.streaming import (
    stream_state_schema as base_stream_state_schema,
    stream_metrics_schema as base_stream_metrics_schema,
    stream_control_schema as base_stream_control_schema,
    stream_operation_result_schema as base_stream_operation_result_schema,
    stream_state_transition_schema as base_stream_state_transition_schema,
    stream_buffer_config_schema as base_stream_buffer_config_schema,
    rate_limited_buffer_config_schema as base_rate_limited_buffer_config_schema,
    batching_buffer_config_schema as base_batching_buffer_config_schema,
    stream_handler_config_schema as base_stream_handler_config_schema,
    enhanced_stream_handler_config_schema as base_enhanced_stream_handler_config_schema,
    string_stream_handler_config_schema as base_string_stream_handler_config_schema
)


class StreamStateSchema(base_stream_state_schema.__class__):
    """Schema for stream state with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Any:
        """Convert loaded data into a StreamState enum value.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A StreamState enum value.
        """
        # Import here to avoid circular imports
        from atlas.providers.streaming.control import StreamState
        
        value = data["value"]
        
        # Convert string value to enum
        if value == "initializing":
            return StreamState.INITIALIZING
        elif value == "active":
            return StreamState.ACTIVE
        elif value == "paused":
            return StreamState.PAUSED
        elif value == "cancelled":
            return StreamState.CANCELLED
        elif value == "completed":
            return StreamState.COMPLETED
        elif value == "error":
            return StreamState.ERROR
        else:
            # This should never happen due to validation, but handle just in case
            raise ValidationError(f"Invalid stream state: {value}")


class StreamMetricsSchema(base_stream_metrics_schema.__class__):
    """Schema for stream metrics with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Convert loaded data into a metrics dictionary.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A dictionary of stream metrics.
        """
        # Stream metrics is just a dictionary, so return data directly
        return data


class StreamControlSchema(base_stream_control_schema.__class__):
    """Schema for stream control interface with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Any:
        """Convert loaded data into a StreamControl object or dictionary.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A dictionary representation of StreamControl properties.
        """
        # Import here to avoid circular imports
        from atlas.providers.streaming.control import StreamState
        
        # Convert state string to enum
        if "state" in data and isinstance(data["state"], str):
            state_value = data["state"]
            if state_value == "initializing":
                data["state"] = StreamState.INITIALIZING
            elif state_value == "active":
                data["state"] = StreamState.ACTIVE
            elif state_value == "paused":
                data["state"] = StreamState.PAUSED
            elif state_value == "cancelled":
                data["state"] = StreamState.CANCELLED
            elif state_value == "completed":
                data["state"] = StreamState.COMPLETED
            elif state_value == "error":
                data["state"] = StreamState.ERROR
        
        return data


class StreamOperationResultSchema(base_stream_operation_result_schema.__class__):
    """Schema for stream operation results with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Convert loaded data into an operation result dictionary.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A dictionary of operation result.
        """
        # Import here to avoid circular imports
        from atlas.providers.streaming.control import StreamState
        
        # Convert state string to enum
        if "state" in data and isinstance(data["state"], str):
            state_value = data["state"]
            if state_value == "initializing":
                data["state"] = StreamState.INITIALIZING
            elif state_value == "active":
                data["state"] = StreamState.ACTIVE
            elif state_value == "paused":
                data["state"] = StreamState.PAUSED
            elif state_value == "cancelled":
                data["state"] = StreamState.CANCELLED
            elif state_value == "completed":
                data["state"] = StreamState.COMPLETED
            elif state_value == "error":
                data["state"] = StreamState.ERROR
        
        return data


class StreamStateTransitionSchema(base_stream_state_transition_schema.__class__):
    """Schema for stream state transitions with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Convert loaded data into a state transition dictionary.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A dictionary representing the state transition.
        """
        # Import here to avoid circular imports
        from atlas.providers.streaming.control import StreamState
        
        # Convert state strings to enums
        if "from_state" in data and isinstance(data["from_state"], str):
            from_state = data["from_state"]
            if from_state == "initializing":
                data["from_state"] = StreamState.INITIALIZING
            elif from_state == "active":
                data["from_state"] = StreamState.ACTIVE
            elif from_state == "paused":
                data["from_state"] = StreamState.PAUSED
            elif from_state == "cancelled":
                data["from_state"] = StreamState.CANCELLED
            elif from_state == "completed":
                data["from_state"] = StreamState.COMPLETED
            elif from_state == "error":
                data["from_state"] = StreamState.ERROR
        
        if "to_state" in data and isinstance(data["to_state"], str):
            to_state = data["to_state"]
            if to_state == "initializing":
                data["to_state"] = StreamState.INITIALIZING
            elif to_state == "active":
                data["to_state"] = StreamState.ACTIVE
            elif to_state == "paused":
                data["to_state"] = StreamState.PAUSED
            elif to_state == "cancelled":
                data["to_state"] = StreamState.CANCELLED
            elif to_state == "completed":
                data["to_state"] = StreamState.COMPLETED
            elif to_state == "error":
                data["to_state"] = StreamState.ERROR
        
        return data


class StreamBufferConfigSchema(base_stream_buffer_config_schema.__class__):
    """Schema for stream buffer configuration with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Any:
        """Convert loaded data into a StreamBuffer constructor arguments.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A StreamBuffer object or constructor arguments.
        """
        # Import here to avoid circular imports
        from atlas.providers.streaming.buffer import StreamBuffer
        
        # Get constructor arguments
        max_buffer_size = data.get("max_buffer_size", 1024*1024)
        
        # Create StreamBuffer instance
        buffer = StreamBuffer(max_buffer_size=max_buffer_size)
        
        # Apply any state settings
        if data.get("paused", False):
            buffer.pause()
        
        if data.get("closed", False):
            buffer.close()
        
        return buffer


class RateLimitedBufferConfigSchema(base_rate_limited_buffer_config_schema.__class__):
    """Schema for rate-limited buffer configuration with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Any:
        """Convert loaded data into a RateLimitedBuffer constructor arguments.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A RateLimitedBuffer object or constructor arguments.
        """
        # Import here to avoid circular imports
        from atlas.providers.streaming.buffer import RateLimitedBuffer
        
        # Get constructor arguments
        max_buffer_size = data.get("max_buffer_size", 1024*1024)
        tokens_per_second = data.get("tokens_per_second")
        chars_per_token = data.get("chars_per_token", 4)
        
        # Create RateLimitedBuffer instance
        buffer = RateLimitedBuffer(
            max_buffer_size=max_buffer_size,
            tokens_per_second=tokens_per_second,
            chars_per_token=chars_per_token
        )
        
        # Apply any state settings
        if data.get("paused", False):
            buffer.pause()
        
        if data.get("closed", False):
            buffer.close()
        
        return buffer


class BatchingBufferConfigSchema(base_batching_buffer_config_schema.__class__):
    """Schema for batching buffer configuration with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Any:
        """Convert loaded data into a BatchingBuffer constructor arguments.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A BatchingBuffer object or constructor arguments.
        """
        # Import here to avoid circular imports
        from atlas.providers.streaming.buffer import BatchingBuffer
        
        # Get constructor arguments
        max_buffer_size = data.get("max_buffer_size", 1024*1024)
        batch_size = data.get("batch_size")
        batch_timeout = data.get("batch_timeout")
        batch_delimiter = data.get("batch_delimiter")
        
        # Create BatchingBuffer instance
        buffer = BatchingBuffer(
            max_buffer_size=max_buffer_size,
            batch_size=batch_size,
            batch_timeout=batch_timeout,
            batch_delimiter=batch_delimiter
        )
        
        # Apply any state settings
        if data.get("paused", False):
            buffer.pause()
        
        if data.get("closed", False):
            buffer.close()
        
        return buffer


class StreamHandlerConfigSchema(base_stream_handler_config_schema.__class__):
    """Schema for stream handler configuration with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Return constructor arguments for StreamHandler.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A dictionary of constructor arguments.
        """
        # For StreamHandler, we just return the configuration
        # Implementation will use this to construct the actual handler
        return data


class EnhancedStreamHandlerConfigSchema(base_enhanced_stream_handler_config_schema.__class__):
    """Schema for enhanced stream handler configuration with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Return constructor arguments for EnhancedStreamHandler.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A dictionary of constructor arguments.
        """
        # For EnhancedStreamHandler, we just return the configuration
        # Implementation will use this to construct the actual handler
        return data


class StringStreamHandlerConfigSchema(base_string_stream_handler_config_schema.__class__):
    """Schema for string stream handler configuration with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Return constructor arguments for StringStreamHandler.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A dictionary of constructor arguments.
        """
        # For StringStreamHandler, we just return the configuration
        # Implementation will use this to construct the actual handler
        return data


# Create schema instances
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


# Validation decorator
def validate_streaming_config(func):
    """Decorator for validating streaming configuration.
    
    Args:
        func: The function to decorate.
        
    Returns:
        The decorated function.
    """
    def wrapper(*args, **kwargs):
        """Wrapper function that validates streaming configuration.
        
        Args:
            *args: Function arguments.
            **kwargs: Function keyword arguments.
            
        Returns:
            The result of the decorated function.
            
        Raises:
            ValidationError: If the configuration is invalid.
        """
        # Import here to avoid circular imports
        from atlas.providers.errors import ProviderConfigError
        
        try:
            # Validate configuration
            config_arg_names = ["config", "configuration", "settings"]
            
            for arg_name in config_arg_names:
                if arg_name in kwargs and kwargs[arg_name] is not None:
                    config = kwargs[arg_name]
                    
                    # Skip if config is not a dict (could be None or already a validated object)
                    if not isinstance(config, dict):
                        continue
                    
                    # Determine schema based on config type
                    if "buffer" in arg_name.lower():
                        if "rate" in arg_name.lower() or (isinstance(config, dict) and "tokens_per_second" in config):
                            schema = rate_limited_buffer_config_schema
                        elif "batch" in arg_name.lower() or (isinstance(config, dict) and any(k in config for k in ["batch_size", "batch_timeout", "batch_delimiter"])):
                            schema = batching_buffer_config_schema
                        else:
                            schema = stream_buffer_config_schema
                    elif "control" in arg_name.lower():
                        schema = stream_control_schema
                    elif "enhanced" in arg_name.lower() or (isinstance(config, dict) and "max_buffer_size" in config):
                        schema = enhanced_stream_handler_config_schema
                    elif "string" in arg_name.lower() or (isinstance(config, dict) and "chunk_size" in config):
                        schema = string_stream_handler_config_schema
                    else:
                        schema = stream_handler_config_schema
                    
                    # Validate and update with validated data
                    kwargs[arg_name] = schema.load(config)
            
            # Call original function
            return func(*args, **kwargs)
            
        except ValidationError as e:
            # Convert to provider-specific error
            raise ProviderConfigError(
                message=f"Invalid streaming configuration: {e.messages}",
                cause=e
            )
    
    return wrapper


# Validation function for stream state transitions
def validate_stream_transition(from_state: str, to_state: str, trigger: str) -> bool:
    """Validate that a stream state transition is valid.
    
    Args:
        from_state: The current state.
        to_state: The target state.
        trigger: The action causing the transition.
        
    Returns:
        True if the transition is valid, False otherwise.
    """
    try:
        # Validate using the schema
        stream_state_transition_schema.load({
            "from_state": from_state,
            "to_state": to_state,
            "trigger": trigger
        })
        return True
    except ValidationError:
        return False


# Add validation functions for stream operations
def validate_pause_operation(state: str) -> bool:
    """Validate that a stream can be paused.
    
    Args:
        state: The current stream state.
        
    Returns:
        True if the stream can be paused, False otherwise.
    """
    return validate_stream_transition(state, "paused", "pause")


def validate_resume_operation(state: str) -> bool:
    """Validate that a stream can be resumed.
    
    Args:
        state: The current stream state.
        
    Returns:
        True if the stream can be resumed, False otherwise.
    """
    return validate_stream_transition(state, "active", "resume")


def validate_cancel_operation(state: str) -> bool:
    """Validate that a stream can be cancelled.
    
    Args:
        state: The current stream state.
        
    Returns:
        True if the stream can be cancelled, False otherwise.
    """
    return validate_stream_transition(state, "cancelled", "cancel")