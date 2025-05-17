"""
Provider schemas for Atlas.

This module provides Marshmallow schemas for provider-related structures,
including model requests, responses, token usage, and cost estimates.

This module extends pure schema definitions with post_load methods
that convert validated data into actual implementation objects.
"""

from typing import Any, Dict, List, Optional, Set, Type, Union
from enum import Enum

from marshmallow import (
    fields,
    post_load, 
    validates, 
    validates_schema,
    ValidationError
)

from atlas.schemas.base import AtlasSchema, JsonField
from atlas.schemas.definitions.providers import (
    token_usage_schema as base_token_usage_schema,
    cost_estimate_schema as base_cost_estimate_schema,
    model_request_schema as base_model_request_schema,
    model_response_schema as base_model_response_schema
)
from atlas.schemas.messages import model_message_schema


class TokenUsageSchema(base_token_usage_schema.__class__):
    """Schema for token usage statistics with implementation conversion."""
    
    @validates_schema
    def validate_totals(self, data: Dict[str, Any], **kwargs) -> None:
        """Validate that total tokens is the sum of input and output tokens.
        
        Args:
            data: The data to validate.
            **kwargs: Additional arguments.
            
        Raises:
            ValidationError: If total tokens doesn't match input + output.
        """
        input_tokens = data.get("input_tokens", 0)
        output_tokens = data.get("output_tokens", 0)
        total_tokens = data.get("total_tokens", 0)
        
        expected_total = input_tokens + output_tokens
        
        if total_tokens != expected_total:
            raise ValidationError(
                f"Total tokens ({total_tokens}) must equal input ({input_tokens}) + output ({output_tokens})"
            )
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Any:
        """Convert loaded data into a TokenUsage object.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A TokenUsage object.
        """
        # Import here to avoid circular imports
        from atlas.providers.messages import TokenUsage
        return TokenUsage(
            input_tokens=data["input_tokens"],
            output_tokens=data["output_tokens"],
            total_tokens=data["total_tokens"]
        )


class CostEstimateSchema(base_cost_estimate_schema.__class__):
    """Schema for cost estimate information with implementation conversion."""
    
    @validates_schema
    def validate_totals(self, data: Dict[str, Any], **kwargs) -> None:
        """Validate that total cost is the sum of input and output costs.
        
        Args:
            data: The data to validate.
            **kwargs: Additional arguments.
            
        Raises:
            ValidationError: If total cost doesn't match input + output.
        """
        input_cost = data.get("input_cost", 0.0)
        output_cost = data.get("output_cost", 0.0)
        total_cost = data.get("total_cost", 0.0)
        
        # Use an epsilon for float comparison
        epsilon = 1e-10
        expected_total = input_cost + output_cost
        
        if abs(total_cost - expected_total) > epsilon:
            raise ValidationError(
                f"Total cost ({total_cost}) must equal input ({input_cost}) + output ({output_cost})"
            )
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Any:
        """Convert loaded data into a CostEstimate object.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A CostEstimate object.
        """
        # Import here to avoid circular imports
        from atlas.providers.messages import CostEstimate
        return CostEstimate(
            input_cost=data["input_cost"],
            output_cost=data["output_cost"],
            total_cost=data["total_cost"]
        )


class ResponseFormatSchema(AtlasSchema):
    """Schema for model response format specifications."""
    
    type = fields.String(required=True)
    schema = JsonField(required=False)


class ModelRequestSchema(base_model_request_schema.__class__):
    """Schema for model requests with implementation conversion."""
    
    @validates('messages')
    def validate_messages(self, value: List[Any], **kwargs) -> None:
        """Validate the message list.
        
        Args:
            value: The list of messages to validate.
            **kwargs: Additional arguments passed to validates method.
            
        Raises:
            ValidationError: If messages are invalid.
        """
        if not value:
            raise ValidationError("At least one message is required")
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Any:
        """Convert loaded data into a ModelRequest object.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A ModelRequest object.
        """
        # Import here to avoid circular imports
        from atlas.providers.messages import ModelRequest, ModelMessage
        from atlas.core.types import MessageRole
        
        # Create instance directly to avoid validation loops
        instance = ModelRequest.__new__(ModelRequest)
        
        # Process messages to ensure proper object types
        if "messages" in data:
            # Make sure we have ModelMessage objects, not dicts
            messages = []
            for msg in data["messages"]:
                if not isinstance(msg, ModelMessage):
                    # This must be a dict, convert to ModelMessage
                    if isinstance(msg, dict):
                        role = msg.get("role")
                        content = msg.get("content", "")
                        name = msg.get("name")
                        
                        # Create ModelMessage based on role
                        if role == "system" or role == MessageRole.SYSTEM:
                            messages.append(ModelMessage.system(content))
                        elif role == "user" or role == MessageRole.USER:
                            messages.append(ModelMessage.user(content, name))
                        elif role == "assistant" or role == MessageRole.ASSISTANT:
                            messages.append(ModelMessage.assistant(content, name))
                        elif role == "function" or role == MessageRole.FUNCTION:
                            messages.append(ModelMessage.function(content, name or "unknown_function"))
                        elif role == "tool" or role == MessageRole.TOOL:
                            messages.append(ModelMessage.tool(content, name or "unknown_tool"))
                        else:
                            # Create a default message for unknown roles
                            user_message = ModelMessage.__new__(ModelMessage)
                            user_message.role = MessageRole.USER
                            user_message.content = str(content) if content else "Empty message"
                            user_message.name = name
                            messages.append(user_message)
                else:
                    messages.append(msg)
            
            # Set messages attribute
            setattr(instance, "messages", messages)
        else:
            # Default to empty messages list
            setattr(instance, "messages", [])
        
        # Add other fields 
        optional_fields = [
            "max_tokens", "temperature", "system_prompt", "model", 
            "stop_sequences", "top_p", "frequency_penalty", 
            "presence_penalty", "response_format", "metadata"
        ]
        
        for field in optional_fields:
            if field in data:
                setattr(instance, field, data[field])
            else:
                # Set defaults
                if field == "metadata":
                    setattr(instance, field, {})
                else:
                    setattr(instance, field, None)
        
        # Handle system prompt logic
        if (hasattr(instance, "system_prompt") and instance.system_prompt and 
            not any(getattr(msg, "role", None) == MessageRole.SYSTEM for msg in instance.messages)):
            
            # Create system message
            system_message = ModelMessage.system(instance.system_prompt)
            
            # Insert at the beginning
            instance.messages.insert(0, system_message)
        
        return instance


class ModelResponseSchema(base_model_response_schema.__class__):
    """Schema for model responses with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Any:
        """Convert loaded data into a ModelResponse object.
        
        Args:
            data: The deserialized data dictionary.
            **kwargs: Additional arguments passed to post_load.
            
        Returns:
            A ModelResponse object.
        """
        # Import here to avoid circular imports
        from atlas.providers.messages import ModelResponse, TokenUsage, CostEstimate
        
        constructor_args = {}
        
        # Extract required fields
        required_fields = ["content", "model", "provider"]
        for field in required_fields:
            if field in data:
                constructor_args[field] = data[field]
        
        # Process nested objects properly
        if "usage" in data:
            usage_data = data["usage"]
            if not isinstance(usage_data, TokenUsage):
                # Create TokenUsage object
                if isinstance(usage_data, dict):
                    constructor_args["usage"] = TokenUsage(
                        input_tokens=usage_data.get("input_tokens", 0),
                        output_tokens=usage_data.get("output_tokens", 0),
                        total_tokens=usage_data.get("total_tokens", 0)
                    )
                else:
                    # Default usage
                    constructor_args["usage"] = TokenUsage()
            else:
                constructor_args["usage"] = usage_data
        
        if "cost" in data:
            cost_data = data["cost"]
            if not isinstance(cost_data, CostEstimate):
                # Create CostEstimate object
                if isinstance(cost_data, dict):
                    constructor_args["cost"] = CostEstimate(
                        input_cost=cost_data.get("input_cost", 0.0),
                        output_cost=cost_data.get("output_cost", 0.0),
                        total_cost=cost_data.get("total_cost", 0.0)
                    )
                else:
                    # Default cost
                    constructor_args["cost"] = CostEstimate()
            else:
                constructor_args["cost"] = cost_data
        
        # Add optional fields
        optional_fields = ["finish_reason", "raw_response"]
        for field in optional_fields:
            if field in data:
                constructor_args[field] = data[field]
        
        # Create instance with constructor
        try:
            return ModelResponse(**constructor_args)
        except Exception as e:
            # Fallback to direct attribute setting if constructor fails
            instance = ModelResponse.__new__(ModelResponse)
            
            # Set attributes directly
            for key, value in constructor_args.items():
                setattr(instance, key, value)
            
            # Ensure required attributes exist
            if not hasattr(instance, "usage") or instance.usage is None:
                instance.usage = TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0)
                
            if not hasattr(instance, "cost") or instance.cost is None:
                instance.cost = CostEstimate(input_cost=0.0, output_cost=0.0, total_cost=0.0)
            
            # Ensure other required fields exist
            for field in required_fields:
                if not hasattr(instance, field):
                    if field == "content":
                        setattr(instance, field, "")
                    elif field == "model":
                        setattr(instance, field, "unknown")
                    elif field == "provider":
                        setattr(instance, field, "unknown")
            
            return instance


# Create schema instances
token_usage_schema = TokenUsageSchema()
cost_estimate_schema = CostEstimateSchema()
response_format_schema = ResponseFormatSchema()
model_request_schema = ModelRequestSchema()
model_response_schema = ModelResponseSchema()