"""
Pure schema definitions for provider-related types.

This module contains schema definitions without any post_load methods or references
to implementation classes, avoiding circular imports. These schemas define the 
structure and validation rules for provider types but don't handle conversion
to actual implementation objects.
"""

from typing import Any, Dict, List, Optional, Union
from marshmallow import fields, pre_load, validates, validates_schema, ValidationError

from atlas.schemas.base import AtlasSchema, EnumField, JsonField
from atlas.schemas.definitions.messages import ModelMessageSchema


class TokenUsageSchema(AtlasSchema):
    """Schema for token usage statistics."""
    
    input_tokens = fields.Integer(required=True)
    output_tokens = fields.Integer(required=True)
    total_tokens = fields.Integer(required=True)


class CostEstimateSchema(AtlasSchema):
    """Schema for cost estimation."""
    
    input_cost = fields.Float(required=True)
    output_cost = fields.Float(required=True)
    total_cost = fields.Float(required=True)


class ModelRequestSchema(AtlasSchema):
    """Schema for model requests."""
    
    messages = fields.List(fields.Nested(ModelMessageSchema), required=True)
    max_tokens = fields.Integer(required=False, allow_none=True)
    temperature = fields.Float(required=False, allow_none=True)
    system_prompt = fields.String(required=False, allow_none=True)
    model = fields.String(required=False, allow_none=True)
    stop_sequences = fields.List(fields.String(), required=False, allow_none=True)
    top_p = fields.Float(required=False, allow_none=True)
    frequency_penalty = fields.Float(required=False, allow_none=True)
    presence_penalty = fields.Float(required=False, allow_none=True)
    response_format = fields.Dict(required=False, allow_none=True)
    
    @validates("messages")
    def validate_messages(self, value: List[Dict[str, Any]], **kwargs) -> None:
        """Validate that messages list is not empty.
        
        Args:
            value: The messages list to validate.
            **kwargs: Additional arguments passed by Marshmallow.
            
        Raises:
            ValidationError: If the messages list is empty.
        """
        if not value:
            raise ValidationError("Messages list cannot be empty")
            
    @validates("temperature")
    def validate_temperature(self, value: Optional[float], **kwargs) -> None:
        """Validate temperature value.
        
        Args:
            value: The temperature value to validate.
            **kwargs: Additional arguments passed by Marshmallow.
            
        Raises:
            ValidationError: If the temperature is outside valid range.
        """
        if value is not None and (value < 0.0 or value > 2.0):
            raise ValidationError("Temperature must be between 0.0 and 2.0")
            
    @validates("top_p")
    def validate_top_p(self, value: Optional[float], **kwargs) -> None:
        """Validate top_p value.
        
        Args:
            value: The top_p value to validate.
            **kwargs: Additional arguments passed by Marshmallow.
            
        Raises:
            ValidationError: If the top_p is outside valid range.
        """
        if value is not None and (value < 0.0 or value > 1.0):
            raise ValidationError("Top_p must be between 0.0 and 1.0")


class ModelResponseSchema(AtlasSchema):
    """Schema for model responses."""
    
    content = fields.String(required=True)
    model = fields.String(required=True)
    provider = fields.String(required=True)
    usage = fields.Nested(TokenUsageSchema, required=False, allow_none=True)
    cost = fields.Nested(CostEstimateSchema, required=False, allow_none=True)
    finish_reason = fields.String(required=False, allow_none=True)
    raw_response = fields.Dict(required=False, allow_none=True)


# Export schema instances for convenient use
token_usage_schema = TokenUsageSchema()
cost_estimate_schema = CostEstimateSchema()
model_request_schema = ModelRequestSchema()
model_response_schema = ModelResponseSchema()