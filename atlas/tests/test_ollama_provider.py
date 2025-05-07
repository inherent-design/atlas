"""
Test Ollama provider implementation.

This module tests the functionality of the Ollama provider, including
streaming capabilities and error handling.
"""

import os
import sys
import unittest
import json
from unittest import mock
from typing import Dict, Any, List, Optional, Iterator

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

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

# Import Ollama provider directly for mock patching
from atlas.models.ollama import OllamaProvider, StreamHandler

# Set environment variable for tests
os.environ["SKIP_API_KEY_CHECK"] = "true"


class TestOllamaProvider(unittest.TestCase):
    """Test the OllamaProvider class."""

    def setUp(self):
        """Set up the test."""
        # Create a provider for testing
        self.provider = OllamaProvider()

    def tearDown(self):
        """Clean up after the test."""
        pass

    def test_provider_creation(self):
        """Test creating an Ollama provider."""
        # Create a provider with default settings
        provider = OllamaProvider()

        # Check provider name
        self.assertEqual(provider.name, "ollama")

        # Check default model
        self.assertEqual(provider._model_name, "llama3")

        # Check default API endpoint
        self.assertEqual(provider._api_endpoint, "http://localhost:11434/api")

        # Create with custom parameters
        custom_provider = OllamaProvider(
            model_name="mistral",
            max_tokens=1000,
            api_endpoint="http://myserver:11434/api",
            temperature=0.7,
        )

        self.assertEqual(custom_provider._model_name, "mistral")
        self.assertEqual(custom_provider._max_tokens, 1000)
        self.assertEqual(custom_provider._api_endpoint, "http://myserver:11434/api")
        self.assertEqual(custom_provider._additional_params["temperature"], 0.7)

    @mock.patch("requests.post")
    def test_generate(self, mock_post):
        """Test generating a response."""
        # Create mock response
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "llama3",
            "response": "This is a test response from Ollama.",
            "done": True,
            "prompt_eval_count": 10,
            "eval_count": 15,
            "total_eval_count": 25,
        }
        mock_post.return_value = mock_response

        # Create a simple request
        request = ModelRequest(
            messages=[ModelMessage.user("Test message")],
            max_tokens=100
        )

        # Generate a response
        response = self.provider.generate(request)

        # Check that the mock was called correctly
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "http://localhost:11434/api/generate")
        self.assertEqual(kwargs["json"]["model"], "llama3")
        self.assertEqual(kwargs["json"]["options"]["num_predict"], 100)
        self.assertFalse(kwargs["json"]["stream"])  # Non-streaming
        self.assertIn("User: Test message", kwargs["json"]["prompt"])

        # Check that the response has the expected structure
        self.assertIsInstance(response, ModelResponse)
        self.assertEqual(response.content, "This is a test response from Ollama.")
        self.assertEqual(response.provider, "ollama")
        self.assertEqual(response.model, "llama3")
        self.assertEqual(response.finish_reason, "stop")
        
        # Check token usage
        self.assertIsInstance(response.usage, TokenUsage)
        self.assertEqual(response.usage.input_tokens, 10)
        self.assertEqual(response.usage.output_tokens, 15)
        self.assertEqual(response.usage.total_tokens, 25)
        
        # Check cost (should be 0 for Ollama)
        self.assertIsInstance(response.cost, CostEstimate)
        self.assertEqual(response.cost.total_cost, 0.0)
        
        # Check raw response
        self.assertEqual(response.raw_response, mock_response.json.return_value)

    @mock.patch("requests.post")
    def test_streaming(self, mock_post):
        """Test streaming a response."""
        # Create a mock for requests.post that returns a stream-like object
        class MockStreamResponse:
            def __init__(self, lines):
                self.lines = lines
                self.status_code = 200
            
            def iter_lines(self, decode_unicode=False):
                for line in self.lines:
                    yield line

        # Create mock stream lines (one JSON object per line as Ollama does)
        stream_lines = [
            json.dumps({"model": "llama3", "response": "This ", "done": False}).encode(),
            json.dumps({"model": "llama3", "response": "is ", "done": False}).encode(),
            json.dumps({"model": "llama3", "response": "a ", "done": False}).encode(),
            json.dumps({"model": "llama3", "response": "test ", "done": False}).encode(),
            json.dumps({"model": "llama3", "response": "streaming ", "done": False}).encode(),
            json.dumps({"model": "llama3", "response": "response ", "done": False}).encode(),
            json.dumps({"model": "llama3", "response": "from ", "done": False}).encode(),
            json.dumps({"model": "llama3", "response": "Ollama.", "done": False}).encode(),
            json.dumps({
                "model": "llama3", 
                "response": "", 
                "done": True,
                "prompt_eval_count": 10,
                "eval_count": 20,
                "total_eval_count": 30
            }).encode(),
        ]
        
        mock_post.return_value = MockStreamResponse(stream_lines)
        
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
        self.assertEqual(initial_response.provider, "ollama")
        self.assertEqual(initial_response.model, "llama3")
        self.assertIsNone(initial_response.finish_reason)  # Not completed yet
        
        # Check stream handler
        self.assertIsInstance(stream_handler, StreamHandler)
        
        # Process the stream manually and collect chunks
        chunks_received = []
        full_text = ""
        
        # Simulate manual iteration over the stream handler
        try:
            while True:
                delta, response = next(stream_handler)
                if delta:
                    chunks_received.append(delta)
                    full_text += delta
                    # Check that the response is updated with each chunk
                    self.assertEqual(response.content, full_text)
        except StopIteration:
            # Stream is complete
            pass
        
        # Check that the client was called with proper streaming parameters
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "http://localhost:11434/api/generate")
        self.assertTrue(kwargs["json"]["stream"])
        self.assertEqual(kwargs["json"]["model"], "llama3")
        
        # Check that we received the expected number of text chunks
        self.assertEqual(len(chunks_received), 8)  # 8 content chunks
        
        # Check the collected full text
        self.assertEqual(full_text, "This is a test streaming response from Ollama.")
        
    @mock.patch("requests.post")
    def test_stream_with_callback(self, mock_post):
        """Test streaming with a callback function."""
        # Create a mock for requests.post that returns a stream-like object
        class MockStreamResponse:
            def __init__(self, lines):
                self.lines = lines
                self.status_code = 200
            
            def iter_lines(self, decode_unicode=False):
                for line in self.lines:
                    yield line

        # Create mock stream lines
        stream_lines = [
            json.dumps({"model": "llama3", "response": "This ", "done": False}).encode(),
            json.dumps({"model": "llama3", "response": "is ", "done": False}).encode(),
            json.dumps({"model": "llama3", "response": "a ", "done": False}).encode(),
            json.dumps({"model": "llama3", "response": "callback ", "done": False}).encode(),
            json.dumps({"model": "llama3", "response": "test.", "done": False}).encode(),
            json.dumps({
                "model": "llama3", 
                "response": "", 
                "done": True,
                "prompt_eval_count": 8,
                "eval_count": 12,
                "total_eval_count": 20
            }).encode(),
        ]
        
        mock_post.return_value = MockStreamResponse(stream_lines)
        
        # Create a simple request
        request = ModelRequest(
            messages=[ModelMessage.user("Test with callback")],
            max_tokens=100
        )
        
        # Create a callback function that collects chunks
        chunks_received = []
        responses_received = []
        
        def callback(delta, response):
            chunks_received.append(delta)
            responses_received.append(response.content)
        
        # Stream with callback
        final_response = self.provider.stream_with_callback(request, callback)
        
        # Check that the callback was called for each chunk
        self.assertEqual(len(chunks_received), 5)  # Only content chunks call the callback
        
        # Check the final response
        self.assertIsInstance(final_response, ModelResponse)
        self.assertEqual(final_response.content, "This is a callback test.")
        self.assertEqual(final_response.provider, "ollama")
        self.assertEqual(final_response.model, "llama3")
        self.assertEqual(final_response.finish_reason, "stop")
        
        # Check token usage in final response
        self.assertEqual(final_response.usage.input_tokens, 8)
        self.assertEqual(final_response.usage.output_tokens, 12)
        self.assertEqual(final_response.usage.total_tokens, 20)
        
        # Check cost calculation (should be 0 for Ollama)
        self.assertIsInstance(final_response.cost, CostEstimate)
        self.assertEqual(final_response.cost.total_cost, 0.0)

    @mock.patch("requests.post")
    def test_error_handling(self, mock_post):
        """Test error handling during API calls."""
        # Create a simple request
        request = ModelRequest(
            messages=[ModelMessage.user("Test message")],
            max_tokens=100
        )
        
        # Test connection error
        mock_post.side_effect = Exception("Connection error")
        
        with self.assertRaises(Exception) as context:
            self.provider.generate(request)
        
        # Check that the error was properly converted to our error type
        self.assertIn("error calling ollama api", str(context.exception).lower())
        
        # Test HTTP error response
        mock_response = mock.MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_post.side_effect = None
        mock_post.return_value = mock_response
        
        with self.assertRaises(Exception) as context:
            self.provider.generate(request)
        
        # Check that the error was properly converted to our error type
        self.assertIn("status code 500", str(context.exception).lower())
        
    @mock.patch("requests.get")
    def test_validate_api_key(self, mock_get):
        """Test API key validation (server availability check for Ollama)."""
        # Mock the successful response
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Check validation - should succeed
        result = self.provider.validate_api_key()
        self.assertTrue(result)
        mock_get.assert_called_once_with(
            "http://localhost:11434/api/version", 
            timeout=2
        )
        
        # Mock a failed response
        mock_get.reset_mock()
        mock_response.status_code = 404
        result = self.provider.validate_api_key()
        self.assertFalse(result)
        
        # Mock a connection error
        mock_get.reset_mock()
        mock_get.side_effect = Exception("Connection error")
        result = self.provider.validate_api_key()
        self.assertFalse(result)
        
    def test_token_usage_calculation(self):
        """Test token usage calculation."""
        # Ollama often doesn't provide token counts, test with both cases
        
        # Case 1: Ollama provides token counts
        response_data = {
            "prompt_eval_count": 15,
            "eval_count": 25,
        }
        
        # Create a request
        request = ModelRequest(
            messages=[ModelMessage.user("Test message")],
            max_tokens=100
        )
        
        # Calculate token usage
        usage = self.provider.calculate_token_usage(request, response_data)
        
        # Check the calculated usage
        self.assertEqual(usage.input_tokens, 15)
        self.assertEqual(usage.output_tokens, 25)
        self.assertEqual(usage.total_tokens, 40)
        
        # Case 2: Ollama doesn't provide token counts - should estimate
        response_data = {
            "response": "This is a test response that should be about 14 tokens."
        }
        
        # Calculate token usage
        usage = self.provider.calculate_token_usage(request, response_data)
        
        # Check that estimates are reasonable
        self.assertGreater(usage.input_tokens, 0)  # Should estimate from request
        self.assertGreater(usage.output_tokens, 0)  # Should estimate from response
        self.assertEqual(usage.total_tokens, usage.input_tokens + usage.output_tokens)
        
    def test_cost_calculation(self):
        """Test cost calculation."""
        # Create a token usage
        usage = TokenUsage(input_tokens=1000, output_tokens=500)
        
        # Calculate cost for a model - should always be 0 for Ollama
        cost = self.provider.calculate_cost(usage, "llama3")
        
        # Check the calculated costs
        self.assertEqual(cost.input_cost, 0.0)
        self.assertEqual(cost.output_cost, 0.0)
        self.assertEqual(cost.total_cost, 0.0)


if __name__ == "__main__":
    unittest.main()