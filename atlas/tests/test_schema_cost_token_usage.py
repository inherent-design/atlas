#!/usr/bin/env python3
"""
Test schema validation for token usage and cost estimation.

This module tests the schema validation, serialization, and deserialization
of TokenUsage and CostEstimate classes, which are used to track token usage
and cost information for model responses.
"""

import unittest
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock

from marshmallow import ValidationError

from atlas.providers.messages import (
    TokenUsage,
    CostEstimate,
    ModelResponse
)
from atlas.schemas.providers import (
    token_usage_schema,
    cost_estimate_schema,
    model_response_schema
)


class TestTokenUsage(unittest.TestCase):
    """Test TokenUsage schema validation and serialization."""

    def test_token_usage_creation(self):
        """Test token usage creation and property access."""
        # Basic usage
        usage = TokenUsage(input_tokens=50, output_tokens=25)
        self.assertEqual(usage.input_tokens, 50)
        self.assertEqual(usage.output_tokens, 25)
        self.assertEqual(usage.total_tokens, 75)  # Auto-calculated
        
        # With explicit total
        usage_with_total = TokenUsage(input_tokens=30, output_tokens=20, total_tokens=60)
        self.assertEqual(usage_with_total.input_tokens, 30)
        self.assertEqual(usage_with_total.output_tokens, 20)
        self.assertEqual(usage_with_total.total_tokens, 60)  # Explicitly set
        
        # Zero tokens
        zero_usage = TokenUsage()
        self.assertEqual(zero_usage.input_tokens, 0)
        self.assertEqual(zero_usage.output_tokens, 0)
        self.assertEqual(zero_usage.total_tokens, 0)
    
    def test_create_direct(self):
        """Test the direct creation method that bypasses schema validation."""
        usage = TokenUsage.create_direct(input_tokens=100, output_tokens=50)
        self.assertEqual(usage.input_tokens, 100)
        self.assertEqual(usage.output_tokens, 50)
        self.assertEqual(usage.total_tokens, 150)
        
        # With custom total
        custom_total = TokenUsage.create_direct(
            input_tokens=10,
            output_tokens=5,
            total_tokens=20  # Doesn't match input+output but allowed in direct creation
        )
        self.assertEqual(custom_total.total_tokens, 20)
    
    def test_serialization(self):
        """Test serialization and deserialization of TokenUsage."""
        usage = TokenUsage(input_tokens=120, output_tokens=80)
        
        # Convert to dict
        usage_dict = usage.to_dict()
        self.assertEqual(usage_dict["input_tokens"], 120)
        self.assertEqual(usage_dict["output_tokens"], 80)
        self.assertEqual(usage_dict["total_tokens"], 200)
        
        # Convert back from dict via schema
        deserialized = token_usage_schema.load(usage_dict)
        self.assertEqual(deserialized.input_tokens, 120)
        self.assertEqual(deserialized.output_tokens, 80)
        self.assertEqual(deserialized.total_tokens, 200)
    
    def test_validation(self):
        """Test schema validation for TokenUsage."""
        # Valid data
        valid_data = {"input_tokens": 50, "output_tokens": 25, "total_tokens": 75}
        validated = token_usage_schema.load(valid_data)
        self.assertEqual(validated.input_tokens, 50)
        self.assertEqual(validated.output_tokens, 25)
        self.assertEqual(validated.total_tokens, 75)
        
        # Valid but missing total (should be calculated)
        valid_partial = {"input_tokens": 40, "output_tokens": 30}
        validated = token_usage_schema.load(valid_partial)
        self.assertEqual(validated.total_tokens, 70)
        
        # Invalid - total doesn't match sum
        invalid_total = {"input_tokens": 10, "output_tokens": 10, "total_tokens": 30}
        with self.assertRaises(ValidationError):
            token_usage_schema.load(invalid_total)
            
        # Invalid - negative tokens
        invalid_negative = {"input_tokens": -10, "output_tokens": 20}
        with self.assertRaises(ValidationError):
            token_usage_schema.load(invalid_negative)
            
        # Invalid - non-integer tokens
        invalid_type = {"input_tokens": "ten", "output_tokens": 20}
        with self.assertRaises(ValidationError):
            token_usage_schema.load(invalid_type)


class TestCostEstimate(unittest.TestCase):
    """Test CostEstimate schema validation and serialization."""

    def test_cost_estimate_creation(self):
        """Test cost estimate creation and property access."""
        # Basic usage
        cost = CostEstimate(input_cost=0.001, output_cost=0.002)
        self.assertEqual(cost.input_cost, 0.001)
        self.assertEqual(cost.output_cost, 0.002)
        self.assertEqual(cost.total_cost, 0.003)  # Auto-calculated
        
        # With explicit total
        cost_with_total = CostEstimate(
            input_cost=0.0005,
            output_cost=0.0015,
            total_cost=0.0025  # Explicitly set, even if inaccurate
        )
        self.assertEqual(cost_with_total.input_cost, 0.0005)
        self.assertEqual(cost_with_total.output_cost, 0.0015)
        self.assertEqual(cost_with_total.total_cost, 0.0025)
        
        # Zero cost
        zero_cost = CostEstimate()
        self.assertEqual(zero_cost.input_cost, 0.0)
        self.assertEqual(zero_cost.output_cost, 0.0)
        self.assertEqual(zero_cost.total_cost, 0.0)
    
    def test_create_direct(self):
        """Test the direct creation method that bypasses schema validation."""
        cost = CostEstimate.create_direct(input_cost=0.01, output_cost=0.02)
        self.assertEqual(cost.input_cost, 0.01)
        self.assertEqual(cost.output_cost, 0.02)
        self.assertEqual(cost.total_cost, 0.03)
        
        # With custom total
        custom_total = CostEstimate.create_direct(
            input_cost=0.05,
            output_cost=0.05,
            total_cost=0.15  # Doesn't match input+output but allowed in direct creation
        )
        self.assertEqual(custom_total.total_cost, 0.15)
    
    def test_string_representation(self):
        """Test string representation of cost estimates."""
        # Regular cost
        cost = CostEstimate(input_cost=0.01, output_cost=0.02)
        cost_str = str(cost)
        self.assertIn("$0.03", cost_str)
        self.assertIn("Input: $0.01", cost_str)
        self.assertIn("Output: $0.02", cost_str)
        
        # Small cost
        small_cost = CostEstimate(input_cost=0.0001, output_cost=0.0002)
        small_str = str(small_cost)
        self.assertIn("$0.0003", small_str)  # Should use more precise formatting
        
        # Very small cost
        tiny_cost = CostEstimate(input_cost=0.0000001, output_cost=0.0000002)
        tiny_str = str(tiny_cost)
        self.assertIn("$0.0000003", tiny_str)  # Should use scientific notation or extra precision
        
        # Zero cost
        zero_cost = CostEstimate()
        zero_str = str(zero_cost)
        self.assertIn("$0.00", zero_str)
    
    def test_serialization(self):
        """Test serialization and deserialization of CostEstimate."""
        cost = CostEstimate(input_cost=0.002, output_cost=0.003)
        
        # Convert to dict
        cost_dict = cost.to_dict()
        self.assertEqual(cost_dict["input_cost"], 0.002)
        self.assertEqual(cost_dict["output_cost"], 0.003)
        self.assertEqual(cost_dict["total_cost"], 0.005)
        
        # Convert back from dict via schema
        deserialized = cost_estimate_schema.load(cost_dict)
        self.assertEqual(deserialized.input_cost, 0.002)
        self.assertEqual(deserialized.output_cost, 0.003)
        self.assertEqual(deserialized.total_cost, 0.005)
    
    def test_validation(self):
        """Test schema validation for CostEstimate."""
        # Valid data
        valid_data = {"input_cost": 0.01, "output_cost": 0.02, "total_cost": 0.03}
        validated = cost_estimate_schema.load(valid_data)
        self.assertEqual(validated.input_cost, 0.01)
        self.assertEqual(validated.output_cost, 0.02)
        self.assertEqual(validated.total_cost, 0.03)
        
        # Valid but missing total (should be calculated)
        valid_partial = {"input_cost": 0.03, "output_cost": 0.04}
        validated = cost_estimate_schema.load(valid_partial)
        self.assertEqual(validated.total_cost, 0.07)
        
        # Invalid - total doesn't match sum (allowing for float precision)
        invalid_total = {"input_cost": 0.1, "output_cost": 0.1, "total_cost": 0.5}
        with self.assertRaises(ValidationError):
            cost_estimate_schema.load(invalid_total)
            
        # Invalid - negative cost
        invalid_negative = {"input_cost": -0.1, "output_cost": 0.2}
        with self.assertRaises(ValidationError):
            cost_estimate_schema.load(invalid_negative)
            
        # Invalid - non-numeric cost
        invalid_type = {"input_cost": "expensive", "output_cost": 0.2}
        with self.assertRaises(ValidationError):
            cost_estimate_schema.load(invalid_type)


class TestModelResponseWithMetrics(unittest.TestCase):
    """Test ModelResponse with TokenUsage and CostEstimate integration."""

    def test_model_response_creation(self):
        """Test ModelResponse creation with usage and cost metrics."""
        # Create component objects
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        cost = CostEstimate(input_cost=0.001, output_cost=0.002)
        
        # Create response with metrics
        response = ModelResponse(
            content="This is a test response",
            model="test-model",
            provider="test-provider",
            usage=usage,
            cost=cost,
            finish_reason="stop"
        )
        
        # Verify all properties
        self.assertEqual(response.content, "This is a test response")
        self.assertEqual(response.model, "test-model")
        self.assertEqual(response.provider, "test-provider")
        self.assertEqual(response.usage.input_tokens, 100)
        self.assertEqual(response.usage.output_tokens, 50)
        self.assertEqual(response.usage.total_tokens, 150)
        self.assertEqual(response.cost.input_cost, 0.001)
        self.assertEqual(response.cost.output_cost, 0.002)
        self.assertEqual(response.cost.total_cost, 0.003)
        self.assertEqual(response.finish_reason, "stop")
    
    def test_default_metrics(self):
        """Test ModelResponse creation with default usage and cost."""
        # Create response without specifying metrics
        response = ModelResponse(
            content="Response with defaults",
            model="test-model",
            provider="test-provider"
        )
        
        # Default metrics should be created
        self.assertIsNotNone(response.usage)
        self.assertEqual(response.usage.input_tokens, 0)
        self.assertEqual(response.usage.output_tokens, 0)
        self.assertEqual(response.usage.total_tokens, 0)
        
        self.assertIsNotNone(response.cost)
        self.assertEqual(response.cost.input_cost, 0.0)
        self.assertEqual(response.cost.output_cost, 0.0)
        self.assertEqual(response.cost.total_cost, 0.0)
    
    def test_response_serialization(self):
        """Test serialization and deserialization of ModelResponse with metrics."""
        # Create response
        response = ModelResponse(
            content="Serialization test",
            model="test-model",
            provider="test-provider",
            usage=TokenUsage(input_tokens=200, output_tokens=100),
            cost=CostEstimate(input_cost=0.002, output_cost=0.003),
            finish_reason="length",
            raw_response={"original": "response"}
        )
        
        # Convert to dict
        response_dict = response.to_dict()
        
        # Basic fields
        self.assertEqual(response_dict["content"], "Serialization test")
        self.assertEqual(response_dict["model"], "test-model")
        self.assertEqual(response_dict["provider"], "test-provider")
        
        # Nested objects
        self.assertIn("usage", response_dict)
        self.assertEqual(response_dict["usage"]["input_tokens"], 200)
        self.assertEqual(response_dict["usage"]["output_tokens"], 100)
        
        self.assertIn("cost", response_dict)
        self.assertEqual(response_dict["cost"]["input_cost"], 0.002)
        self.assertEqual(response_dict["cost"]["output_cost"], 0.003)
        
        # Validate raw_response is not included in serialized output
        self.assertNotIn("raw_response", response_dict)
        
        # Deserialize back
        deserialized = model_response_schema.load(response_dict)
        self.assertEqual(deserialized.content, "Serialization test")
        self.assertEqual(deserialized.usage.input_tokens, 200)
        self.assertEqual(deserialized.cost.total_cost, 0.005)
    
    def test_response_schema_validation(self):
        """Test schema validation for ModelResponse."""
        # Valid data
        valid_data = {
            "content": "Valid response",
            "model": "test-model",
            "provider": "test-provider",
            "usage": {"input_tokens": 50, "output_tokens": 30},
            "cost": {"input_cost": 0.001, "output_cost": 0.002}
        }
        validated = model_response_schema.load(valid_data)
        self.assertEqual(validated.content, "Valid response")
        self.assertEqual(validated.usage.total_tokens, 80)
        self.assertEqual(validated.cost.total_cost, 0.003)
        
        # Invalid - missing required fields
        invalid_missing = {
            "content": "Missing provider",
            "model": "test-model"
            # Missing provider field
        }
        with self.assertRaises(ValidationError):
            model_response_schema.load(invalid_missing)
            
        # Invalid - nested validation fails
        invalid_nested = {
            "content": "Invalid nested object",
            "model": "test-model",
            "provider": "test-provider",
            "usage": {"input_tokens": 50, "output_tokens": 30, "total_tokens": 100}  # Wrong total
        }
        with self.assertRaises(ValidationError):
            model_response_schema.load(invalid_nested)
    
    def test_string_representation(self):
        """Test string representation of ModelResponse."""
        # Create response with metrics
        response = ModelResponse(
            content="This is a test response with a somewhat longer content that should be truncated in the string representation",
            model="test-model",
            provider="test-provider",
            usage=TokenUsage(input_tokens=100, output_tokens=50),
            cost=CostEstimate(input_cost=0.001, output_cost=0.002),
            finish_reason="stop"
        )
        
        # Convert to string
        response_str = str(response)
        
        # Check that it contains relevant information
        self.assertIn("Response from test-provider/test-model", response_str)
        self.assertIn("Content", response_str)
        self.assertIn("This is a test response", response_str)
        self.assertIn("Usage: 100 input, 50 output tokens", response_str)
        self.assertIn("$0.003", response_str)  # Total cost
        
        # Very long content should be truncated in string representation
        self.assertIn("...", response_str)
    
    def test_create_direct(self):
        """Test the direct creation method that bypasses schema validation."""
        # Create with direct method
        response = ModelResponse.create_direct(
            content="Direct creation",
            model="test-model",
            provider="test-provider",
            usage=TokenUsage(input_tokens=30, output_tokens=20),
            cost=CostEstimate(input_cost=0.0003, output_cost=0.0004),
            finish_reason="stop"
        )
        
        self.assertEqual(response.content, "Direct creation")
        self.assertEqual(response.usage.total_tokens, 50)
        self.assertEqual(response.cost.total_cost, 0.0007)
        
        # Create with raw_response
        raw_data = {"completion": "Raw response data", "model": "actual-model"}
        response_with_raw = ModelResponse.create_direct(
            content="With raw data",
            model="test-model",
            provider="test-provider",
            raw_response=raw_data
        )
        
        self.assertEqual(response_with_raw.raw_response, raw_data)


if __name__ == "__main__":
    unittest.main()