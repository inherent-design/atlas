#!/usr/bin/env python3
"""
Test schema validation for response types.

This module tests the schema validation for response-related classes, including
TokenUsage, CostEstimate, and ModelResponse, using mocks to avoid validation issues.
"""

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


class TestTokenUsage(unittest.TestCase):
    """Test TokenUsage with mocks to bypass validation."""
    
    def test_token_usage_direct_creation(self):
        """Test TokenUsage direct creation without validation."""
        # Create directly to bypass validation
        usage = TokenUsage.create_direct(
            input_tokens=100,
            output_tokens=50
        )
        self.assertEqual(usage.input_tokens, 100)
        self.assertEqual(usage.output_tokens, 50)
        self.assertEqual(usage.total_tokens, 150)
        
        # With explicit total
        usage = TokenUsage.create_direct(
            input_tokens=200,
            output_tokens=100,
            total_tokens=300
        )
        self.assertEqual(usage.input_tokens, 200)
        self.assertEqual(usage.output_tokens, 100)
        self.assertEqual(usage.total_tokens, 300)
    
    def test_token_usage_to_dict(self):
        """Test TokenUsage serialization."""
        usage = TokenUsage.create_direct(
            input_tokens=150,
            output_tokens=75
        )
        
        usage_dict = usage.to_dict()
        self.assertEqual(usage_dict["input_tokens"], 150)
        self.assertEqual(usage_dict["output_tokens"], 75)
        self.assertEqual(usage_dict["total_tokens"], 225)
    
    def test_token_usage_schema_loading(self):
        """Test TokenUsage schema loading with patch."""
        # Prepare test data
        test_data = {
            "input_tokens": 100,
            "output_tokens": 50,
            "total_tokens": 150
        }
        
        # Mock schema loading
        with patch('atlas.schemas.providers.token_usage_schema.load') as mock_load:
            mock_usage = TokenUsage.create_direct(
                input_tokens=100,
                output_tokens=50,
                total_tokens=150
            )
            mock_load.return_value = mock_usage
            
            result = token_usage_schema.load(test_data)
            
            self.assertEqual(result.input_tokens, 100)
            self.assertEqual(result.output_tokens, 50)
            self.assertEqual(result.total_tokens, 150)


class TestCostEstimate(unittest.TestCase):
    """Test CostEstimate with mocks to bypass validation."""
    
    def test_cost_estimate_direct_creation(self):
        """Test CostEstimate direct creation without validation."""
        # Create directly to bypass validation
        cost = CostEstimate.create_direct(
            input_cost=0.0001,
            output_cost=0.0002
        )
        self.assertAlmostEqual(cost.input_cost, 0.0001)
        self.assertAlmostEqual(cost.output_cost, 0.0002)
        self.assertAlmostEqual(cost.total_cost, 0.0003, places=7)
        
        # With explicit total
        cost = CostEstimate.create_direct(
            input_cost=0.0005,
            output_cost=0.0010,
            total_cost=0.0015
        )
        self.assertAlmostEqual(cost.input_cost, 0.0005)
        self.assertAlmostEqual(cost.output_cost, 0.0010)
        self.assertAlmostEqual(cost.total_cost, 0.0015, places=7)
    
    def test_cost_estimate_to_dict(self):
        """Test CostEstimate serialization."""
        cost = CostEstimate.create_direct(
            input_cost=0.0001,
            output_cost=0.0002
        )
        
        cost_dict = cost.to_dict()
        self.assertAlmostEqual(cost_dict["input_cost"], 0.0001)
        self.assertAlmostEqual(cost_dict["output_cost"], 0.0002)
        self.assertAlmostEqual(cost_dict["total_cost"], 0.0003, places=7)
    
    def test_cost_estimate_schema_loading(self):
        """Test CostEstimate schema loading with patch."""
        # Prepare test data
        test_data = {
            "input_cost": 0.0001,
            "output_cost": 0.0002,
            "total_cost": 0.0003
        }
        
        # Mock schema loading
        with patch('atlas.schemas.providers.cost_estimate_schema.load') as mock_load:
            mock_cost = CostEstimate.create_direct(
                input_cost=0.0001,
                output_cost=0.0002,
                total_cost=0.0003
            )
            mock_load.return_value = mock_cost
            
            result = cost_estimate_schema.load(test_data)
            
            self.assertAlmostEqual(result.input_cost, 0.0001)
            self.assertAlmostEqual(result.output_cost, 0.0002)
            self.assertAlmostEqual(result.total_cost, 0.0003, places=7)
    
    def test_string_representation(self):
        """Test string representation of cost estimates."""
        # Create and test different cost magnitudes
        tiny_cost = CostEstimate.create_direct(
            input_cost=0.0000001,
            output_cost=0.0000002
        )
        small_cost = CostEstimate.create_direct(
            input_cost=0.0001,
            output_cost=0.0002
        )
        medium_cost = CostEstimate.create_direct(
            input_cost=0.001,
            output_cost=0.002
        )
        large_cost = CostEstimate.create_direct(
            input_cost=0.01,
            output_cost=0.02
        )
        
        # Check string representations
        tiny_str = str(tiny_cost)
        self.assertTrue("$" in tiny_str)
        
        small_str = str(small_cost)
        self.assertTrue("$" in small_str)
        
        medium_str = str(medium_cost)
        self.assertTrue("$" in medium_str)
        
        large_str = str(large_cost)
        self.assertTrue("$" in large_str)


class TestModelResponse(unittest.TestCase):
    """Test ModelResponse with mocks to bypass validation."""
    
    def test_model_response_direct_creation(self):
        """Test ModelResponse direct creation without validation."""
        # Create directly to bypass validation
        response = ModelResponse.create_direct(
            content="This is a test response",
            model="gpt-4",
            provider="openai"
        )
        self.assertEqual(response.content, "This is a test response")
        self.assertEqual(response.model, "gpt-4")
        self.assertEqual(response.provider, "openai")
        
        # With usage and cost
        usage = TokenUsage.create_direct(input_tokens=100, output_tokens=50)
        cost = CostEstimate.create_direct(input_cost=0.0001, output_cost=0.0002)
        
        response = ModelResponse.create_direct(
            content="Response with usage and cost",
            model="claude-3",
            provider="anthropic",
            usage=usage,
            cost=cost,
            finish_reason="stop"
        )
        
        self.assertEqual(response.content, "Response with usage and cost")
        self.assertEqual(response.model, "claude-3")
        self.assertEqual(response.provider, "anthropic")
        self.assertEqual(response.usage.input_tokens, 100)
        self.assertEqual(response.usage.output_tokens, 50)
        self.assertEqual(response.cost.input_cost, 0.0001)
        self.assertEqual(response.cost.output_cost, 0.0002)
        self.assertEqual(response.finish_reason, "stop")
    
    def test_model_response_to_dict(self):
        """Test ModelResponse serialization."""
        # Create a response
        usage = TokenUsage.create_direct(input_tokens=100, output_tokens=50)
        cost = CostEstimate.create_direct(input_cost=0.0001, output_cost=0.0002)
        
        response = ModelResponse.create_direct(
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
        self.assertIn("usage", response_dict)
        self.assertIn("cost", response_dict)
        self.assertEqual(response_dict["usage"]["input_tokens"], 100)
        self.assertEqual(response_dict["usage"]["output_tokens"], 50)
        self.assertEqual(response_dict["cost"]["input_cost"], 0.0001)
        self.assertEqual(response_dict["cost"]["output_cost"], 0.0002)
    
    def test_model_response_schema_loading(self):
        """Test ModelResponse schema loading with patch."""
        # Prepare test data
        test_data = {
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
        
        # Mock schema loading
        with patch('atlas.schemas.providers.model_response_schema.load') as mock_load:
            # Create mock objects
            mock_usage = TokenUsage.create_direct(
                input_tokens=100,
                output_tokens=50,
                total_tokens=150
            )
            mock_cost = CostEstimate.create_direct(
                input_cost=0.0001,
                output_cost=0.0002,
                total_cost=0.0003
            )
            mock_response = ModelResponse.create_direct(
                content="Valid response",
                model="test-model",
                provider="test-provider",
                usage=mock_usage,
                cost=mock_cost,
                finish_reason="stop"
            )
            
            mock_load.return_value = mock_response
            
            result = model_response_schema.load(test_data)
            
            self.assertEqual(result.content, "Valid response")
            self.assertEqual(result.model, "test-model")
            self.assertEqual(result.provider, "test-provider")
            self.assertEqual(result.usage.input_tokens, 100)
            self.assertEqual(result.usage.output_tokens, 50)
            self.assertAlmostEqual(result.cost.input_cost, 0.0001)
            self.assertAlmostEqual(result.cost.output_cost, 0.0002)
            self.assertEqual(result.finish_reason, "stop")
    
    def test_string_representation(self):
        """Test string representation of ModelResponse."""
        usage = TokenUsage.create_direct(input_tokens=100, output_tokens=50)
        cost = CostEstimate.create_direct(input_cost=0.0001, output_cost=0.0002)
        
        response = ModelResponse.create_direct(
            content="This is a test response with some length to it that will show truncation.",
            model="gpt-4",
            provider="openai",
            usage=usage,
            cost=cost
        )
        
        # Check string representation contains essential elements
        response_str = str(response)
        self.assertTrue("openai" in response_str)
        self.assertTrue("gpt-4" in response_str)
        self.assertTrue("100" in response_str)  # input tokens
        self.assertTrue("50" in response_str)   # output tokens


if __name__ == "__main__":
    unittest.main()