"""
Test Ollama provider with real API calls.

This module tests the Ollama provider's functionality by making
real API calls to a local Ollama server. These tests require Ollama
to be running locally.
"""

import os
import unittest
from typing import Dict, Any, List, Optional

# Import base test classes and decorators
from atlas.tests.helpers import (
    api_test, ollama_test, expensive_test,
    OllamaProviderTestBase, TestWithTokenTracking
)

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

# Import Ollama provider directly
from atlas.models.ollama import OllamaProvider


class TestOllamaAPI(OllamaProviderTestBase):
    """Test the OllamaProvider class with real API calls."""

    provider_class = OllamaProvider
    provider_name = "ollama"
    
    def setUp(self):
        """Set up the test environment for Ollama API tests."""
        super().setUp()
        
        # Verify if Ollama is available - this uses the _check_api_key method
        # from OllamaProviderTestBase which checks server availability
        if not self._check_api_key():
            self.skipTest("Ollama is not running locally")
        
        # Log the available models for debugging
        available_models = self._get_available_models()
        if available_models:
            print(f"Available Ollama models: {available_models}")
            # Use the first available model if any are available
            self.default_model = available_models[0]
        else:
            self.skipTest("No models available in local Ollama server")

    @api_test
    @ollama_test
    def test_generate_api(self):
        """Test generating a response with the real Ollama API."""
        # Create a simple request with minimal tokens for cost control
        request = self._create_request("Write a single word response: Hello", max_tokens=5)
        
        # Generate a response
        response = self.provider.generate(request)
        
        # Track token usage
        self.track_usage(response)
        
        # Verify the response structure
        self.assertIsNotNone(response)
        self.assertIsNotNone(response.content)
        self.assertEqual(response.provider, self.provider_name)
        self.assertEqual(response.model, self.default_model)
        
        # Check for token usage - Ollama doesn't always provide exact counts
        # but our provider should estimate them
        self.assertIsNotNone(response.usage)
        self.assertGreater(response.usage.input_tokens, 0)
        self.assertGreater(response.usage.output_tokens, 0)
        
        # Ollama is free, so cost should be 0
        self.assertEqual(response.cost.total_cost, 0.0)

    @api_test
    @ollama_test
    def test_streaming_api(self):
        """Test streaming a response with the real Ollama API."""
        # Create a simple request
        request = self._create_request("Write a short greeting", max_tokens=10)
        
        # Get the streaming response
        initial_response, stream_handler = self.provider.stream(request)
        
        # Check initial response structure
        self.assertIsNotNone(initial_response)
        self.assertEqual(initial_response.content, "")  # Empty initially
        self.assertEqual(initial_response.provider, self.provider_name)
        self.assertEqual(initial_response.model, self.default_model)
        
        # Process the stream
        chunks_received = []
        final_response = None
        
        try:
            while True:
                # Get next chunk
                delta, response = next(stream_handler)
                if delta:
                    chunks_received.append(delta)
                final_response = response
        except StopIteration:
            # Stream ended
            pass
        
        # Check that we received chunks
        self.assertGreater(len(chunks_received), 0)
        
        # Check the final response
        self.assertIsNotNone(final_response)
        self.assertGreater(len(final_response.content), 0)
        self.assertEqual(final_response.provider, self.provider_name)
        self.assertEqual(final_response.model, self.default_model)
        
        # Track token usage
        self.track_usage(final_response)

    @api_test
    @ollama_test
    def test_stream_with_callback_api(self):
        """Test streaming with a callback function using real Ollama API."""
        # Create a simple request
        request = self._create_request("Write a short greeting", max_tokens=10)
        
        # Prepare callback variables
        chunks_received = []
        responses_received = []
        
        def callback(delta, response):
            chunks_received.append(delta)
            responses_received.append(response.content)
        
        # Stream with callback
        final_response = self.provider.stream_with_callback(request, callback)
        
        # Check that we received chunks
        self.assertGreater(len(chunks_received), 0)
        
        # Verify the final response
        self.assertIsNotNone(final_response)
        self.assertGreater(len(final_response.content), 0)
        self.assertEqual(final_response.provider, self.provider_name)
        self.assertEqual(final_response.model, self.default_model)
        
        # The final response content should match the last response in the callback
        if responses_received:
            self.assertEqual(final_response.content, responses_received[-1])
        
        # Track token usage
        self.track_usage(final_response)


if __name__ == "__main__":
    unittest.main()