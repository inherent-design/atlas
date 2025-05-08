"""
Test mock provider implementation.

This module tests the functionality of the mock provider, ensuring it works
as expected for testing without API access.
"""

import os
import unittest
from unittest import mock
from typing import Dict, Any, List, Optional

from atlas.tests.helpers.decorators import mock_test

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
    discover_providers,
    create_provider,
)

# Import mock provider directly to ensure it's available
from atlas.models.mock import MockProvider, StreamHandler


class TestMockProvider(unittest.TestCase):
    """Test the MockProvider class."""

    def setUp(self):
        """Set up the test."""
        # Create a mock provider instance
        self.provider = MockProvider()

    @mock_test
    def test_provider_creation(self):
        """Test creating a mock provider."""
        # Check provider name
        self.assertEqual(self.provider.name, "mock")

        # Check default model
        self.assertEqual(self.provider._model_name, "mock-standard")

        # Create with custom parameters
        custom_provider = MockProvider(
            model_name="mock-advanced",
            max_tokens=1000,
            delay_ms=50
        )
        
        self.assertEqual(custom_provider._model_name, "mock-advanced")
        self.assertEqual(custom_provider._max_tokens, 1000)
        self.assertEqual(custom_provider._delay_ms, 50)

    @mock_test
    def test_api_key_validation(self):
        """Test API key validation."""
        # Check that validation always succeeds
        self.assertTrue(self.provider.validate_api_key())

    @mock_test
    def test_available_models(self):
        """Test getting available models."""
        # Check that the provider returns the expected models
        models = self.provider.get_available_models()
        self.assertIsInstance(models, list)
        self.assertGreater(len(models), 0)
        
        # Check specific models
        self.assertIn("mock-standard", models)
        self.assertIn("mock-basic", models)
        self.assertIn("mock-advanced", models)

    @mock_test
    def test_generate(self):
        """Test generating a response."""
        # Create a simple request
        request = ModelRequest(
            messages=[ModelMessage.user("Test message")],
            max_tokens=100
        )

        # Generate a response
        response = self.provider.generate(request)

        # Check that the response has the expected structure
        self.assertIsInstance(response, ModelResponse)
        self.assertIsNotNone(response.content)
        self.assertEqual(response.provider, "mock")
        self.assertEqual(response.model, "mock-standard")

        # Check token usage
        self.assertIsInstance(response.usage, TokenUsage)
        self.assertGreater(response.usage.input_tokens, 0)
        self.assertGreater(response.usage.output_tokens, 0)
        self.assertEqual(
            response.usage.total_tokens,
            response.usage.input_tokens + response.usage.output_tokens
        )

        # Check cost
        self.assertIsInstance(response.cost, CostEstimate)
        
        # Check finish reason
        self.assertEqual(response.finish_reason, "stop")

    @mock_test
    def test_error_simulation(self):
        """Test simulating API errors."""
        # Create a provider that simulates errors
        error_provider = MockProvider(simulate_errors=True, error_type="authentication")

        # Create a simple request
        request = ModelRequest(
            messages=[ModelMessage.user("Test message")],
            max_tokens=100
        )

        # Try to generate a response, which should raise an error
        with self.assertRaises(Exception) as context:
            error_provider.generate(request)

        # Check that the error message is as expected
        self.assertIn("authentication", str(context.exception).lower())

        # Test with a different error type
        error_provider = MockProvider(simulate_errors=True, error_type="validation")
        with self.assertRaises(Exception) as context:
            error_provider.generate(request)
        self.assertIn("validation", str(context.exception).lower())

        # Test with the default error type
        error_provider = MockProvider(simulate_errors=True)
        with self.assertRaises(Exception) as context:
            error_provider.generate(request)
        self.assertIn("api error", str(context.exception).lower())

    @mock_test
    def test_cost_calculation(self):
        """Test cost calculation."""
        # Create a simple usage
        usage = TokenUsage(input_tokens=1000, output_tokens=500)

        # Calculate cost for different models
        cost_standard = self.provider.calculate_cost(usage, "mock-standard")
        cost_basic = self.provider.calculate_cost(usage, "mock-basic")
        cost_advanced = self.provider.calculate_cost(usage, "mock-advanced")

        # Check that the costs are as expected
        self.assertEqual(cost_standard.input_cost, (1000 / 1_000_000) * 3.0)
        self.assertEqual(cost_standard.output_cost, (500 / 1_000_000) * 15.0)
        self.assertEqual(cost_standard.total_cost, cost_standard.input_cost + cost_standard.output_cost)

        self.assertEqual(cost_basic.input_cost, (1000 / 1_000_000) * 0.5)
        self.assertEqual(cost_basic.output_cost, (500 / 1_000_000) * 1.5)
        self.assertEqual(cost_basic.total_cost, cost_basic.input_cost + cost_basic.output_cost)

        self.assertEqual(cost_advanced.input_cost, (1000 / 1_000_000) * 10.0)
        self.assertEqual(cost_advanced.output_cost, (500 / 1_000_000) * 30.0)
        self.assertEqual(cost_advanced.total_cost, cost_advanced.input_cost + cost_advanced.output_cost)


class TestMockProviderStreaming(unittest.TestCase):
    """Test the streaming functionality of the MockProvider."""

    def setUp(self):
        """Set up the test."""
        # Create a mock provider with a small delay for faster tests
        self.provider = MockProvider(delay_ms=10)

    @mock_test
    def test_stream(self):
        """Test streaming a response."""
        # Create a simple request
        request = ModelRequest(
            messages=[ModelMessage.user("Test streaming message")],
            max_tokens=100
        )

        # Get streaming response
        initial_response, stream_handler = self.provider.stream(request)

        # Check initial response structure
        self.assertIsInstance(initial_response, ModelResponse)
        self.assertEqual(initial_response.content, "")  # Empty initially
        self.assertEqual(initial_response.provider, "mock")
        self.assertEqual(initial_response.model, "mock-standard")
        self.assertIsInstance(initial_response.usage, TokenUsage)
        self.assertIsNone(initial_response.finish_reason)  # Not completed yet

        # Check stream handler
        self.assertIsInstance(stream_handler, StreamHandler)

        # Process the stream and collect chunks
        chunks = []
        full_text = ""
        for delta, response in stream_handler:
            chunks.append(delta)
            full_text += delta
            
            # Check that the response is updated with each chunk
            self.assertEqual(response.content, full_text)
            self.assertEqual(response.provider, "mock")

        # Check that we received some chunks
        self.assertGreater(len(chunks), 0)
        
        # Check that the final text contains some expected content
        self.assertIn("mock", full_text.lower())
        self.assertIn("response", full_text.lower())

    @mock_test
    def test_stream_with_callback(self):
        """Test streaming with a callback function."""
        # Create a simple request
        request = ModelRequest(
            messages=[ModelMessage.user("Test streaming with callback")],
            max_tokens=100
        )

        # Create a callback function that collects chunks
        chunks = []
        full_texts = []
        
        def callback(delta, response):
            chunks.append(delta)
            full_texts.append(response.content)
        
        # Stream with callback
        final_response = self.provider.stream_with_callback(request, callback)
        
        # Check that we received some chunks
        self.assertGreater(len(chunks), 0)
        self.assertEqual(len(chunks), len(full_texts))
        
        # Check that the final response is complete
        self.assertIsInstance(final_response, ModelResponse)
        self.assertGreater(len(final_response.content), 0)
        self.assertEqual(final_response.provider, "mock")
        self.assertEqual(final_response.model, "mock-standard")
        self.assertIsInstance(final_response.usage, TokenUsage)
        self.assertEqual(final_response.finish_reason, "stop")  # Completed
        
        # Check that the last full text matches the final response content
        self.assertEqual(full_texts[-1], final_response.content)

    @mock_test
    def test_stream_error_simulation(self):
        """Test simulating errors during streaming."""
        # Create a provider that simulates errors
        error_provider = MockProvider(simulate_errors=True, error_type="authentication")

        # Create a simple request
        request = ModelRequest(
            messages=[ModelMessage.user("Test message")],
            max_tokens=100
        )

        # Try to stream a response, which should raise an error
        with self.assertRaises(Exception) as context:
            error_provider.stream(request)

        # Check that the error message is as expected
        self.assertIn("authentication", str(context.exception).lower())
        self.assertIn("streaming", str(context.exception).lower())


class TestMockProviderFactory(unittest.TestCase):
    """Test the mock provider with the factory."""

    @mock_test
    def test_discover_providers(self):
        """Test that the mock provider is discovered."""
        # Discover available providers
        providers = discover_providers()
        
        # Check that the mock provider is included
        self.assertIn("mock", providers)
        self.assertIn("mock-standard", providers["mock"])
        
    @mock_test
    def test_create_provider(self):
        """Test creating a mock provider using the factory."""
        # Create a mock provider
        provider = create_provider("mock")
        
        # Check that it's the correct type
        self.assertIsInstance(provider, MockProvider)
        self.assertEqual(provider.name, "mock")


if __name__ == "__main__":
    unittest.main()