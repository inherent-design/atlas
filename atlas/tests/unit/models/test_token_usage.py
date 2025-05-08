"""
Test token usage tracking and cost calculation.

This module tests the token usage tracking and cost calculation
functionality across different provider implementations.
"""

import os
import unittest
from unittest import mock
from typing import Dict, Any, List, Optional, Type, Callable

from atlas.tests.helpers.decorators import unit_test

# Import models module
from atlas.models import (
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ModelMessage,
    MessageContent,
    ModelRole,
    TokenUsage,
    CostEstimate,
)

# Import provider implementations directly
from atlas.models.anthropic import AnthropicProvider
from atlas.models.openai import OpenAIProvider
from atlas.models.ollama import OllamaProvider
from atlas.models.mock import MockProvider

# Set environment variable for tests
os.environ["SKIP_API_KEY_CHECK"] = "true"


class TestTokenUsageBase(unittest.TestCase):
    """Test the TokenUsage base class functionality."""

    @unit_test
    def test_token_usage_creation(self):
        """Test creating TokenUsage instances."""
        # Create with explicit values
        usage = TokenUsage(input_tokens=10, output_tokens=20, total_tokens=30)
        self.assertEqual(usage.input_tokens, 10)
        self.assertEqual(usage.output_tokens, 20)
        self.assertEqual(usage.total_tokens, 30)

        # Create with automatic total calculation
        usage = TokenUsage(input_tokens=15, output_tokens=25)
        self.assertEqual(usage.input_tokens, 15)
        self.assertEqual(usage.output_tokens, 25)
        self.assertEqual(usage.total_tokens, 40)  # Should be sum of input + output

        # Create with defaults
        usage = TokenUsage()
        self.assertEqual(usage.input_tokens, 0)
        self.assertEqual(usage.output_tokens, 0)
        self.assertEqual(usage.total_tokens, 0)

    @unit_test
    def test_token_usage_string_representation(self):
        """Test the string representation of TokenUsage."""
        usage = TokenUsage(input_tokens=100, output_tokens=200)
        
        # Check that the string representation contains the token counts
        string_repr = str(usage)
        self.assertIn("100", string_repr)
        self.assertIn("200", string_repr)
        self.assertIn("300", string_repr)  # Total
        
    @unit_test
    def test_token_usage_dictionary_conversion(self):
        """Test converting TokenUsage to a dictionary."""
        usage = TokenUsage(input_tokens=50, output_tokens=75)
        
        # Convert to dictionary
        usage_dict = usage.to_dict()
        
        # Check dictionary contents
        self.assertEqual(usage_dict["input_tokens"], 50)
        self.assertEqual(usage_dict["output_tokens"], 75)
        self.assertEqual(usage_dict["total_tokens"], 125)


class TestCostEstimateBase(unittest.TestCase):
    """Test the CostEstimate base class functionality."""

    @unit_test
    def test_cost_estimate_creation(self):
        """Test creating CostEstimate instances."""
        # Create with explicit values
        cost = CostEstimate(input_cost=0.01, output_cost=0.02, total_cost=0.03)
        self.assertEqual(cost.input_cost, 0.01)
        self.assertEqual(cost.output_cost, 0.02)
        self.assertEqual(cost.total_cost, 0.03)

        # Create with automatic total calculation
        cost = CostEstimate(input_cost=0.015, output_cost=0.025)
        self.assertEqual(cost.input_cost, 0.015)
        self.assertEqual(cost.output_cost, 0.025)
        self.assertEqual(cost.total_cost, 0.04)  # Should be sum of input + output

        # Create with defaults
        cost = CostEstimate()
        self.assertEqual(cost.input_cost, 0.0)
        self.assertEqual(cost.output_cost, 0.0)
        self.assertEqual(cost.total_cost, 0.0)

    @unit_test
    def test_cost_estimate_string_representation(self):
        """Test the string representation of CostEstimate."""
        cost = CostEstimate(input_cost=0.01, output_cost=0.02)
        
        # Check that the string representation contains the costs
        string_repr = str(cost)
        self.assertIn("$0.01", string_repr)
        self.assertIn("$0.02", string_repr)
        self.assertIn("$0.03", string_repr)  # Total
        
    @unit_test
    def test_cost_estimate_dictionary_conversion(self):
        """Test converting CostEstimate to a dictionary."""
        cost = CostEstimate(input_cost=0.05, output_cost=0.075)
        
        # Convert to dictionary
        cost_dict = cost.to_dict()
        
        # Check dictionary contents
        self.assertEqual(cost_dict["input_cost"], 0.05)
        self.assertEqual(cost_dict["output_cost"], 0.075)
        self.assertEqual(cost_dict["total_cost"], 0.125)
        
    @unit_test
    def test_cost_estimate_formatting(self):
        """Test cost formatting in different scenarios."""
        # Test very small cost
        tiny_cost = CostEstimate(input_cost=0.0000001, output_cost=0.0000002)
        tiny_str = str(tiny_cost)
        # Should use at least 7 decimal places or scientific notation for tiny costs
        self.assertTrue(
            "$0.0000003" in tiny_str or 
            "3.0e-07" in tiny_str or 
            "3e-07" in tiny_str, 
            f"Expected tiny cost format not found in {tiny_str}"
        )
        
        # Test larger cost
        large_cost = CostEstimate(input_cost=1.5, output_cost=2.5)
        large_str = str(large_cost)
        # Should show rounded to 2 decimal places for larger costs
        self.assertTrue(
            "$4.00" in large_str or 
            "$4.0" in large_str, 
            f"Expected large cost format not found in {large_str}"
        )


class TestProviderCostCalculation(unittest.TestCase):
    """Test cost calculation across providers."""

    def setUp(self):
        """Set up the test."""
        # Create provider instances
        self.anthropic = AnthropicProvider(api_key="test-key")
        self.openai = OpenAIProvider(api_key="test-key")
        self.ollama = OllamaProvider()
        self.mock = MockProvider()

    @unit_test
    def test_anthropic_cost_calculation(self):
        """Test Anthropic cost calculation for different models."""
        # Define a token usage
        usage = TokenUsage(input_tokens=1000, output_tokens=500)
        
        # Test calculation for various Claude models
        models = [
            "claude-3-opus-20240229",  # More expensive model
            "claude-3-sonnet-20240229",  # Standard model
            "claude-3-haiku-20240307",  # Less expensive model
            "claude-3-7-sonnet-20250219",  # Latest model
            "claude-3-5-sonnet-20240613",  # Claude 3.5 Sonnet
            "claude-3-5-haiku-20240620",  # Claude 3.5 Haiku
        ]
        
        for model in models:
            cost = self.anthropic.calculate_cost(usage, model)
            
            # Verify cost is calculated
            self.assertIsInstance(cost, CostEstimate)
            self.assertGreaterEqual(cost.input_cost, 0)
            self.assertGreaterEqual(cost.output_cost, 0)
            self.assertEqual(cost.total_cost, cost.input_cost + cost.output_cost)
            
            # Verify model-specific pricing is applied
            if "opus" in model:
                # Opus is $15/M input tokens, $75/M output tokens
                self.assertEqual(cost.input_cost, (1000 / 1_000_000) * 15.0)
                self.assertEqual(cost.output_cost, (500 / 1_000_000) * 75.0)
            elif "haiku" in model and "3-5" in model:
                # Claude 3.5 Haiku is $0.80/M input tokens, $4/M output tokens
                self.assertEqual(cost.input_cost, (1000 / 1_000_000) * 0.80)
                self.assertEqual(cost.output_cost, (500 / 1_000_000) * 4.0)
            elif "haiku" in model:
                # Claude 3 Haiku is $0.25/M input tokens, $1.25/M output tokens
                self.assertEqual(cost.input_cost, (1000 / 1_000_000) * 0.25)
                self.assertEqual(cost.output_cost, (500 / 1_000_000) * 1.25)
            else:
                # All Sonnet models (3.7, 3.5, 3) are $3/M input tokens, $15/M output tokens
                self.assertEqual(cost.input_cost, (1000 / 1_000_000) * 3.0)
                self.assertEqual(cost.output_cost, (500 / 1_000_000) * 15.0)

    @unit_test
    def test_openai_cost_calculation(self):
        """Test OpenAI cost calculation for different models."""
        # Define a token usage
        usage = TokenUsage(input_tokens=1000, output_tokens=500)
        
        # Test calculation for various OpenAI models
        models = [
            # Latest models (GPT-4.1 series)
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4.1-nano",
            
            # GPT-4o series
            "gpt-4o",
            "gpt-4o-mini",
            
            # Reasoning models
            "o3",
            "o4-mini",
            
            # Legacy models
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ]
        
        for model in models:
            cost = self.openai.calculate_cost(usage, model)
            
            # Verify cost is calculated
            self.assertIsInstance(cost, CostEstimate)
            self.assertGreaterEqual(cost.input_cost, 0)
            self.assertGreaterEqual(cost.output_cost, 0)
            self.assertEqual(cost.total_cost, cost.input_cost + cost.output_cost)
            
            # Verify model-specific pricing is applied
            if model == "gpt-4.1":
                self.assertEqual(cost.input_cost, (1000 / 1_000_000) * 2.0)
                self.assertEqual(cost.output_cost, (500 / 1_000_000) * 8.0)
            elif model == "gpt-4.1-mini":
                self.assertEqual(cost.input_cost, (1000 / 1_000_000) * 0.4)
                self.assertEqual(cost.output_cost, (500 / 1_000_000) * 1.6)
            elif model == "gpt-4.1-nano":
                self.assertEqual(cost.input_cost, (1000 / 1_000_000) * 0.1)
                self.assertEqual(cost.output_cost, (500 / 1_000_000) * 0.4)
            elif model == "o3":
                self.assertEqual(cost.input_cost, (1000 / 1_000_000) * 10.0)
                self.assertEqual(cost.output_cost, (500 / 1_000_000) * 40.0)
            elif model == "o4-mini":
                self.assertEqual(cost.input_cost, (1000 / 1_000_000) * 1.1)
                self.assertEqual(cost.output_cost, (500 / 1_000_000) * 4.4)
            elif model == "gpt-4o":
                self.assertEqual(cost.input_cost, (1000 / 1_000_000) * 5.0)
                self.assertEqual(cost.output_cost, (500 / 1_000_000) * 20.0)
            elif model == "gpt-4o-mini":
                self.assertEqual(cost.input_cost, (1000 / 1_000_000) * 0.6)
                self.assertEqual(cost.output_cost, (500 / 1_000_000) * 2.4)
            elif model == "gpt-4-turbo":
                self.assertEqual(cost.input_cost, (1000 / 1_000_000) * 10.0)
                self.assertEqual(cost.output_cost, (500 / 1_000_000) * 30.0)
            elif model == "gpt-4":
                self.assertEqual(cost.input_cost, (1000 / 1_000_000) * 30.0)
                self.assertEqual(cost.output_cost, (500 / 1_000_000) * 60.0)
            elif model == "gpt-3.5-turbo":
                self.assertEqual(cost.input_cost, (1000 / 1_000_000) * 0.5)
                self.assertEqual(cost.output_cost, (500 / 1_000_000) * 1.5)

    @unit_test
    def test_ollama_cost_calculation(self):
        """Test Ollama cost calculation."""
        # Define a token usage
        usage = TokenUsage(input_tokens=1000, output_tokens=500)
        
        # Test calculation for Ollama models - should always be 0 cost
        models = ["llama3", "mistral", "gemma"]
        
        for model in models:
            cost = self.ollama.calculate_cost(usage, model)
            
            # Verify cost is calculated as 0
            self.assertIsInstance(cost, CostEstimate)
            self.assertEqual(cost.input_cost, 0.0)
            self.assertEqual(cost.output_cost, 0.0)
            self.assertEqual(cost.total_cost, 0.0)

    @unit_test
    def test_mock_cost_calculation(self):
        """Test mock provider cost calculation."""
        # Define a token usage
        usage = TokenUsage(input_tokens=1000, output_tokens=500)
        
        # Test calculation for mock models with different pricing
        models = ["mock-basic", "mock-standard", "mock-advanced"]
        
        for model in models:
            cost = self.mock.calculate_cost(usage, model)
            
            # Verify cost is calculated
            self.assertIsInstance(cost, CostEstimate)
            self.assertGreaterEqual(cost.input_cost, 0)
            self.assertGreaterEqual(cost.output_cost, 0)
            self.assertEqual(cost.total_cost, cost.input_cost + cost.output_cost)
            
            # Verify model-specific pricing is applied
            if model == "mock-basic":
                self.assertEqual(cost.input_cost, (1000 / 1_000_000) * 0.5)
                self.assertEqual(cost.output_cost, (500 / 1_000_000) * 1.5)
            elif model == "mock-standard":
                self.assertEqual(cost.input_cost, (1000 / 1_000_000) * 3.0)
                self.assertEqual(cost.output_cost, (500 / 1_000_000) * 15.0)
            elif model == "mock-advanced":
                self.assertEqual(cost.input_cost, (1000 / 1_000_000) * 10.0)
                self.assertEqual(cost.output_cost, (500 / 1_000_000) * 30.0)


class TestProviderTokenUsageTracking(unittest.TestCase):
    """Test token usage tracking across providers."""

    def setUp(self):
        """Set up the test."""
        # Create provider instances
        self.anthropic = AnthropicProvider(api_key="test-key")
        self.openai = OpenAIProvider(api_key="test-key")
        self.ollama = OllamaProvider()
        self.mock = MockProvider()
        
        # Create a simple request for testing
        self.request = ModelRequest(
            messages=[ModelMessage.user("Test message")],
            max_tokens=100
        )

    @unit_test
    @mock.patch("anthropic.Anthropic")
    def test_anthropic_token_usage(self, mock_anthropic_class):
        """Test Anthropic token usage tracking."""
        # Create mock response
        mock_client = mock.MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        # Configure the mock response
        mock_response = mock.MagicMock()
        mock_response.content = [mock.MagicMock(text="Test response")]
        mock_response.usage = mock.MagicMock(
            input_tokens=15,
            output_tokens=8,
            total_tokens=23
        )
        mock_client.messages.create.return_value = mock_response
        
        # Generate a response
        response = self.anthropic.generate(self.request)
        
        # Check token usage tracking
        self.assertGreater(response.usage.input_tokens, 0)
        self.assertGreater(response.usage.output_tokens, 0)
        self.assertEqual(response.usage.total_tokens, response.usage.input_tokens + response.usage.output_tokens)
        
        # Check cost calculation based on usage
        self.assertIsInstance(response.cost, CostEstimate)
        
        # Check that costs are properly calculated and the structure is valid
        self.assertGreaterEqual(response.cost.input_cost, 0.0)
        self.assertGreaterEqual(response.cost.output_cost, 0.0)
        self.assertGreaterEqual(response.cost.total_cost, 0.0)
        
        # Verify total cost equals sum of input and output costs
        self.assertAlmostEqual(response.cost.total_cost, 
                              response.cost.input_cost + response.cost.output_cost, 
                              places=10)

    @unit_test
    @mock.patch("openai.OpenAI")
    def test_openai_token_usage(self, mock_openai_class):
        """Test OpenAI token usage tracking."""
        # Create mock client
        mock_client = mock.MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Configure the mock response
        mock_completion = mock.MagicMock()
        mock_choice = mock.MagicMock()
        mock_message = mock.MagicMock()
        
        mock_client.chat.completions.create.return_value = mock_completion
        mock_completion.choices = [mock_choice]
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        mock_message.content = "Test response"
        mock_completion.usage.prompt_tokens = 12
        mock_completion.usage.completion_tokens = 10
        mock_completion.usage.total_tokens = 22
        mock_completion.model_dump.return_value = {"mock": "response"}
        
        # Generate a response
        response = self.openai.generate(self.request)
        
        # Check token usage tracking
        self.assertGreater(response.usage.input_tokens, 0)
        self.assertGreater(response.usage.output_tokens, 0)
        self.assertEqual(response.usage.total_tokens, response.usage.input_tokens + response.usage.output_tokens)
        
        # Check cost calculation based on usage
        self.assertIsInstance(response.cost, CostEstimate)

    @unit_test
    @mock.patch("requests.post")
    def test_ollama_token_usage(self, mock_post):
        """Test Ollama token usage tracking."""
        # Create mock response
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "llama3",
            "response": "Test response",
            "done": True,
            "prompt_eval_count": 16,
            "eval_count": 7,
            "total_eval_count": 23,
        }
        mock_post.return_value = mock_response
        
        # Generate a response
        response = self.ollama.generate(self.request)
        
        # Check token usage tracking
        self.assertGreater(response.usage.input_tokens, 0)
        self.assertGreater(response.usage.output_tokens, 0)
        self.assertEqual(response.usage.total_tokens, response.usage.input_tokens + response.usage.output_tokens)
        
        # Check cost calculation (should be 0 for Ollama)
        self.assertIsInstance(response.cost, CostEstimate)
        self.assertEqual(response.cost.total_cost, 0.0)
        
        # Test Ollama's token estimation when counts are not provided
        mock_response.json.return_value = {
            "model": "llama3",
            "response": "Test response without token counts",
            "done": True,
        }
        
        # Generate another response
        response = self.ollama.generate(self.request)
        
        # Check token usage estimation
        self.assertGreater(response.usage.input_tokens, 0)  # Should estimate based on request
        self.assertGreater(response.usage.output_tokens, 0)  # Should estimate based on response
        self.assertEqual(response.usage.total_tokens, response.usage.input_tokens + response.usage.output_tokens)

    @unit_test
    def test_mock_token_usage(self):
        """Test mock provider token usage tracking."""
        # Generate a response
        response = self.mock.generate(self.request)
        
        # Check token usage tracking
        self.assertGreater(response.usage.input_tokens, 0)
        self.assertGreater(response.usage.output_tokens, 0)
        self.assertEqual(response.usage.total_tokens, response.usage.input_tokens + response.usage.output_tokens)
        
        # Check cost calculation
        self.assertIsInstance(response.cost, CostEstimate)
        self.assertGreaterEqual(response.cost.input_cost, 0.0)
        self.assertGreaterEqual(response.cost.output_cost, 0.0)
        self.assertEqual(response.cost.total_cost, response.cost.input_cost + response.cost.output_cost)


class TestStreamingTokenUsage(unittest.TestCase):
    """Test token usage tracking during streaming."""

    def setUp(self):
        """Set up the test."""
        # Create a mock provider that doesn't make API calls
        self.mock = MockProvider(delay_ms=1)  # Fast testing
        
        # Create a simple request for testing
        self.request = ModelRequest(
            messages=[ModelMessage.user("Test streaming message")],
            max_tokens=100
        )

    @unit_test
    def test_stream_token_usage_tracking(self):
        """Test token usage tracking during streaming."""
        # Get streaming response
        initial_response, stream_handler = self.mock.stream(self.request)
        
        # Check initial token tracking
        self.assertGreater(initial_response.usage.input_tokens, 0)  # Should have input tokens
        self.assertEqual(initial_response.usage.output_tokens, 0)  # No output tokens yet
        
        # Process the entire stream
        for delta, response in stream_handler:
            # Usage should be updated during streaming
            if delta:
                pass  # Just process the stream
        
        # Check final token usage tracking
        self.assertGreater(stream_handler.response.usage.input_tokens, 0)
        self.assertGreater(stream_handler.response.usage.output_tokens, 0)
        self.assertEqual(
            stream_handler.response.usage.total_tokens,
            stream_handler.response.usage.input_tokens + stream_handler.response.usage.output_tokens
        )
        
        # Check cost calculation based on final usage
        self.assertIsInstance(stream_handler.response.cost, CostEstimate)
        self.assertGreaterEqual(stream_handler.response.cost.input_cost, 0.0)
        self.assertGreaterEqual(stream_handler.response.cost.output_cost, 0.0)
        self.assertEqual(
            stream_handler.response.cost.total_cost,
            stream_handler.response.cost.input_cost + stream_handler.response.cost.output_cost
        )

    @unit_test
    def test_stream_with_callback_token_tracking(self):
        """Test token usage tracking during streaming with callback."""
        # Create a callback function
        received_deltas = []
        
        def callback(delta, response):
            received_deltas.append(delta)
        
        # Stream with callback
        final_response = self.mock.stream_with_callback(self.request, callback)
        
        # Check token usage in final response
        self.assertGreater(final_response.usage.input_tokens, 0)
        self.assertGreater(final_response.usage.output_tokens, 0)
        self.assertEqual(
            final_response.usage.total_tokens,
            final_response.usage.input_tokens + final_response.usage.output_tokens
        )
        
        # Check cost calculation
        self.assertIsInstance(final_response.cost, CostEstimate)
        
        # Check that we received some deltas through the callback
        self.assertGreater(len(received_deltas), 0)


if __name__ == "__main__":
    unittest.main()