#!/usr/bin/env python3
"""
Test schema validation for response-related classes.

This module tests the serialization and deserialization of response-related
classes with schema validation, including TokenUsage, CostEstimate, and 
ModelResponse objects.
"""

import json
import unittest
from typing import Dict, Any, List, Optional, Union
from unittest.mock import patch, MagicMock

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
from marshmallow import ValidationError


class TestTokenUsage(unittest.TestCase):
    """Test TokenUsage serialization and deserialization."""
    
    def test_token_usage_creation(self):
        """Test TokenUsage creation and properties."""
        # Basic creation
        usage = TokenUsage(
            input_tokens=100,
            output_tokens=50
        )
        self.assertEqual(usage.input_tokens, 100)
        self.assertEqual(usage.output_tokens, 50)
        self.assertEqual(usage.total_tokens, 150)  # Auto-calculated
        
        # Explicit total
        usage = TokenUsage(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150
        )
        self.assertEqual(usage.total_tokens, 150)
        
        # Direct creation method
        direct_usage = TokenUsage.create_direct(
            input_tokens=200,
            output_tokens=100
        )
        self.assertEqual(direct_usage.input_tokens, 200)
        self.assertEqual(direct_usage.output_tokens, 100)
        self.assertEqual(direct_usage.total_tokens, 300)
    
    def test_token_usage_serialization(self):
        """Test TokenUsage serialization and deserialization."""
        # Create usage
        usage = TokenUsage(input_tokens=150, output_tokens=75)
        
        # Convert to dict
        usage_dict = usage.to_dict()
        self.assertEqual(usage_dict["input_tokens"], 150)
        self.assertEqual(usage_dict["output_tokens"], 75)
        self.assertEqual(usage_dict["total_tokens"], 225)
        
        # Deserialize with schema
        deserialized = token_usage_schema.load(usage_dict)
        self.assertEqual(deserialized.input_tokens, 150)
        self.assertEqual(deserialized.output_tokens, 75)
        self.assertEqual(deserialized.total_tokens, 225)
    
    def test_token_usage_validation(self):
        """Test TokenUsage schema validation."""
        # Valid usage
        valid_usage = {
            "input_tokens": 100,
            "output_tokens": 50,
            "total_tokens": 150
        }
        validated = token_usage_schema.load(valid_usage)
        self.assertEqual(validated.input_tokens, 100)
        self.assertEqual(validated.output_tokens, 50)
        self.assertEqual(validated.total_tokens, 150)
        
        # Invalid total (doesn't match input + output)
        invalid_total = {
            "input_tokens": 100,
            "output_tokens": 50,
            "total_tokens": 200  # Should be 150
        }
        with self.assertRaises(ValidationError):
            token_usage_schema.load(invalid_total)
        
        # Missing fields (should use defaults)
        missing_fields = {"input_tokens": 100}
        with self.assertRaises(ValidationError):
            # This should fail without output_tokens
            token_usage_schema.load(missing_fields)


class TestCostEstimate(unittest.TestCase):
    """Test CostEstimate serialization and deserialization."""
    
    def test_cost_estimate_creation(self):
        """Test CostEstimate creation and properties."""
        # Basic creation
        cost = CostEstimate(
            input_cost=0.0001,
            output_cost=0.0002
        )
        self.assertEqual(cost.input_cost, 0.0001)
        self.assertEqual(cost.output_cost, 0.0002)
        self.assertEqual(cost.total_cost, 0.0003)  # Auto-calculated
        
        # Explicit total
        cost = CostEstimate(
            input_cost=0.0001,
            output_cost=0.0002,
            total_cost=0.0003
        )
        self.assertEqual(cost.total_cost, 0.0003)
        
        # Direct creation method
        direct_cost = CostEstimate.create_direct(
            input_cost=0.0005,
            output_cost=0.0010
        )
        self.assertEqual(direct_cost.input_cost, 0.0005)
        self.assertEqual(direct_cost.output_cost, 0.0010)
        self.assertEqual(direct_cost.total_cost, 0.0015)
    
    def test_cost_estimate_serialization(self):
        """Test CostEstimate serialization and deserialization."""
        # Create cost estimate
        cost = CostEstimate(input_cost=0.0001, output_cost=0.0002)
        
        # Convert to dict
        cost_dict = cost.to_dict()
        self.assertEqual(cost_dict["input_cost"], 0.0001)
        self.assertEqual(cost_dict["output_cost"], 0.0002)
        self.assertEqual(cost_dict["total_cost"], 0.0003)
        
        # Deserialize with schema
        deserialized = cost_estimate_schema.load(cost_dict)
        self.assertEqual(deserialized.input_cost, 0.0001)
        self.assertEqual(deserialized.output_cost, 0.0002)
        self.assertEqual(deserialized.total_cost, 0.0003)
    
    def test_cost_estimate_validation(self):
        """Test CostEstimate schema validation."""
        # Valid cost
        valid_cost = {
            "input_cost": 0.0001,
            "output_cost": 0.0002,
            "total_cost": 0.0003
        }
        validated = cost_estimate_schema.load(valid_cost)
        self.assertEqual(validated.input_cost, 0.0001)
        self.assertEqual(validated.output_cost, 0.0002)
        self.assertEqual(validated.total_cost, 0.0003)
        
        # Invalid total (doesn't match input + output)
        invalid_total = {
            "input_cost": 0.0001,
            "output_cost": 0.0002,
            "total_cost": 0.0005  # Should be 0.0003
        }
        with self.assertRaises(ValidationError):
            cost_estimate_schema.load(invalid_total)
    
    def test_string_representation(self):
        """Test string representation of cost estimates."""
        # Test different cost magnitudes
        tiny_cost = CostEstimate(input_cost=0.0000001, output_cost=0.0000002)
        small_cost = CostEstimate(input_cost=0.0001, output_cost=0.0002)
        medium_cost = CostEstimate(input_cost=0.001, output_cost=0.002)
        large_cost = CostEstimate(input_cost=0.01, output_cost=0.02)
        
        # Check string representations
        tiny_str = str(tiny_cost)
        self.assertIn("$3", tiny_str)  # Should show scientific notation
        
        small_str = str(small_cost)
        self.assertIn("$0.0003", small_str)
        
        medium_str = str(medium_cost)
        self.assertIn("$0.003", medium_str)
        
        large_str = str(large_cost)
        self.assertIn("$0.03", large_str)


class TestModelResponse(unittest.TestCase):
    """Test ModelResponse serialization and deserialization."""
    
    def test_model_response_creation(self):
        """Test ModelResponse creation and properties."""
        # Basic creation
        response = ModelResponse(
            content="This is a test response",
            model="gpt-4",
            provider="openai"
        )
        self.assertEqual(response.content, "This is a test response")
        self.assertEqual(response.model, "gpt-4")
        self.assertEqual(response.provider, "openai")
        self.assertIsNotNone(response.usage)  # Should have default usage
        self.assertIsNotNone(response.cost)  # Should have default cost
        
        # With usage and cost
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        cost = CostEstimate(input_cost=0.0001, output_cost=0.0002)
        response = ModelResponse(
            content="Response with usage and cost",
            model="claude-3",
            provider="anthropic",
            usage=usage,
            cost=cost,
            finish_reason="stop"
        )
        self.assertEqual(response.usage.input_tokens, 100)
        self.assertEqual(response.usage.output_tokens, 50)
        self.assertEqual(response.cost.input_cost, 0.0001)
        self.assertEqual(response.cost.output_cost, 0.0002)
        self.assertEqual(response.finish_reason, "stop")
        
        # Direct creation method
        direct_response = ModelResponse.create_direct(
            content="Direct creation response",
            model="direct-model",
            provider="direct-provider",
            finish_reason="length"
        )
        self.assertEqual(direct_response.content, "Direct creation response")
        self.assertEqual(direct_response.finish_reason, "length")
    
    def test_model_response_serialization(self):
        """Test ModelResponse serialization and deserialization."""
        # Create response
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        cost = CostEstimate(input_cost=0.0001, output_cost=0.0002)
        response = ModelResponse(
            content="Test serialization",
            model="test-model",
            provider="test-provider",
            usage=usage,
            cost=cost,
            finish_reason="stop"
        )
        
        # Convert to dict
        response_dict = response.to_dict()
        self.assertEqual(response_dict["content"], "Test serialization")
        self.assertEqual(response_dict["model"], "test-model")
        self.assertEqual(response_dict["provider"], "test-provider")
        self.assertEqual(response_dict["finish_reason"], "stop")
        
        # Check nested usage and cost
        self.assertEqual(response_dict["usage"]["input_tokens"], 100)
        self.assertEqual(response_dict["usage"]["output_tokens"], 50)
        self.assertEqual(response_dict["cost"]["input_cost"], 0.0001)
        self.assertEqual(response_dict["cost"]["output_cost"], 0.0002)
        
        # Deserialize with schema
        deserialized = model_response_schema.load(response_dict)
        self.assertEqual(deserialized.content, "Test serialization")
        self.assertEqual(deserialized.model, "test-model")
        self.assertEqual(deserialized.provider, "test-provider")
        self.assertEqual(deserialized.finish_reason, "stop")
        
        # Check nested objects deserialized properly
        self.assertEqual(deserialized.usage.input_tokens, 100)
        self.assertEqual(deserialized.usage.output_tokens, 50)
        self.assertEqual(deserialized.cost.input_cost, 0.0001)
        self.assertEqual(deserialized.cost.output_cost, 0.0002)
    
    def test_model_response_validation(self):
        """Test ModelResponse schema validation."""
        # Valid response
        valid_response = {
            "content": "Valid response",
            "model": "test-model",
            "provider": "test-provider",
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150
            },
            "cost": {
                "input_cost": 0.0001,
                "output_cost": 0.0002,
                "total_cost": 0.0003
            },
            "finish_reason": "stop"
        }
        validated = model_response_schema.load(valid_response)
        self.assertEqual(validated.content, "Valid response")
        self.assertEqual(validated.model, "test-model")
        self.assertEqual(validated.provider, "test-provider")
        
        # Invalid response (missing required fields)
        invalid_response = {
            "model": "test-model",
            "provider": "test-provider"
            # Missing content field
        }
        with self.assertRaises(ValidationError):
            model_response_schema.load(invalid_response)
    
    def test_string_representation(self):
        """Test string representation of ModelResponse."""
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        cost = CostEstimate(input_cost=0.0001, output_cost=0.0002)
        response = ModelResponse(
            content="This is a test response with some length to it that will show truncation.",
            model="gpt-4",
            provider="openai",
            usage=usage,
            cost=cost
        )
        
        # Check string representation
        response_str = str(response)
        self.assertIn("openai/gpt-4", response_str)
        self.assertIn("100 input, 50 output", response_str)
        self.assertIn("$0.0003", response_str)
        self.assertIn("...", response_str)  # Should truncate the content
    
    def test_raw_response_handling(self):
        """Test raw_response is properly handled but not serialized."""
        raw_data = {"choices": [{"message": {"content": "Raw content"}}]}
        
        response = ModelResponse(
            content="Test response",
            model="test-model",
            provider="test-provider",
            raw_response=raw_data
        )
        
        # Raw response should be stored
        self.assertEqual(response.raw_response, raw_data)
        
        # But should not be included in serialization
        response_dict = response.to_dict()
        self.assertNotIn("raw_response", response_dict)


if __name__ == "__main__":
    unittest.main()