"""
Test Ollama provider implementation.

This module tests the functionality of the Ollama provider, including
streaming capabilities and error handling, using mocked responses.
"""

import os
import json
import unittest
from unittest import mock
from typing import Dict, Any, List, Optional, Iterator

# Import base test classes and decorators
from atlas.tests.helpers import (
    mock_test, api_test, expensive_test,
    OllamaProviderTestBase, TestWithTokenTracking,
    create_mock_message, create_mock_request, create_mock_response,
    mock_ollama_response, mock_streaming_ollama_response
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

# Import Ollama provider directly for mock patching
from atlas.models.ollama import OllamaProvider, StreamHandler

# Import error types for testing
from atlas.core.errors import APIError, AuthenticationError, ValidationError, ErrorSeverity

# Set environment variable for tests to skip API key check
os.environ["SKIP_API_KEY_CHECK"] = "true"


class TestOllamaMockProvider(OllamaProviderTestBase):
    """Test the OllamaProvider class with mocked responses."""

    provider_class = OllamaProvider
    provider_name = "ollama"
    default_model = "llama3"
    
    def setUp(self):
        """Set up the test."""
        super().setUp()
        
        # Create a provider for testing
        self.provider = self.provider_class(model_name=self.default_model)
        self.api_endpoint = "http://localhost:11434/api"

    @mock_test
    def test_provider_creation(self):
        """Test creating an Ollama provider."""
        # Create a provider with default settings
        provider = self.provider_class()

        # Check provider name
        self.assertEqual(provider.name, self.provider_name)

        # Check default model
        self.assertEqual(provider._model_name, self.default_model)

        # Check default API endpoint
        self.assertEqual(provider._api_endpoint, self.api_endpoint)

        # Create with custom parameters
        custom_provider = self.provider_class(
            model_name="mistral",
            max_tokens=1000,
            api_endpoint="http://myserver:11434/api",
            temperature=0.7,
        )

        self.assertEqual(custom_provider._model_name, "mistral")
        self.assertEqual(custom_provider._max_tokens, 1000)
        self.assertEqual(custom_provider._api_endpoint, "http://myserver:11434/api")
        self.assertEqual(custom_provider._additional_params["temperature"], 0.7)

    @mock_test
    def test_generate_mocked(self):
        """Test generating a response with a mocked API."""
        # Create a simple request
        request = self._create_request("Test message")
        
        # Set up mocks with the with statement for better isolation
        # Also mock the environment check
        with mock.patch("requests.post") as mock_post, \
             mock.patch("atlas.models.ollama.env.get_bool") as mock_env_get_bool:
             
            # Make env.get_bool return False for SKIP_API_KEY_CHECK
            def mock_env_get_bool_impl(key, default=False):
                if key == "SKIP_API_KEY_CHECK":
                    return False
                return default
                
            mock_env_get_bool.side_effect = mock_env_get_bool_impl
            
            # Set up the mock response
            mock_response = mock.MagicMock()
            mock_response.status_code = 200
            
            # Use the helper to create a mock Ollama response structure
            mock_response_data = mock_ollama_response(
                content="This is a test response from Ollama.",
                model=self.default_model
            )
            mock_response.json.return_value = mock_response_data
            mock_post.return_value = mock_response
            
            # Generate a response
            response = self.provider.generate(request)
            
            # Verify the call was made with the expected parameters
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(args[0], f"{self.api_endpoint}/generate")
            self.assertEqual(kwargs["json"]["model"], self.default_model)
            self.assertEqual(kwargs["json"]["options"]["num_predict"], 10)  # From _create_request default
            self.assertFalse(kwargs["json"]["stream"])  # Non-streaming
            self.assertIn("User: Test message", kwargs["json"]["prompt"])

        # Check that the response has the expected structure
        self.assertIsInstance(response, ModelResponse)
        self.assertEqual(response.content, "This is a test response from Ollama.")
        self.assertEqual(response.provider, self.provider_name)
        self.assertEqual(response.model, self.default_model)
        self.assertEqual(response.finish_reason, "stop")
        
        # Check token usage (Ollama doesn't provide exact token counts, but our class estimates)
        self.assertIsInstance(response.usage, TokenUsage)
        self.assertGreater(response.usage.input_tokens, 0)
        self.assertGreater(response.usage.output_tokens, 0)
        
        # Check cost (should be 0 for Ollama)
        self.assertIsInstance(response.cost, CostEstimate)
        self.assertEqual(response.cost.total_cost, 0.0)
        
        # Check raw response
        self.assertEqual(response.raw_response, mock_response_data)

    @mock_test
    def test_streaming_mocked(self):
        """Test streaming a response with mocked chunk data."""
        # Create a simple request
        request = self._create_request("Test streaming message")
        
        # Create a mock for requests.post that returns a stream-like object
        with mock.patch("requests.post") as mock_post, \
             mock.patch("atlas.models.ollama.env.get_bool") as mock_env_get_bool:
             
            # Make env.get_bool return False for SKIP_API_KEY_CHECK
            def mock_env_get_bool_impl(key, default=False):
                if key == "SKIP_API_KEY_CHECK":
                    return False
                return default
                
            mock_env_get_bool.side_effect = mock_env_get_bool_impl
            
            # Create a properly mocked response with iter_lines method
            mock_response = mock.MagicMock()
            mock_response.status_code = 200
            
            # Create mock streaming responses
            full_content = "This is a test streaming response from Ollama."
            streaming_responses = mock_streaming_ollama_response(content=full_content, model=self.default_model, chunks=8)
            
            # Create mock stream lines (one JSON object per line as Ollama does)
            stream_lines = [
                json.dumps(response).encode() for response in streaming_responses
            ]
            
            # Create a proper iter_lines method
            mock_response.iter_lines = mock.MagicMock(return_value=iter(stream_lines))
            mock_post.return_value = mock_response
        
            # Get streaming response
            initial_response, stream_handler = self.provider.stream(request)
            
            # Check initial response structure
            self.assertIsInstance(initial_response, ModelResponse)
            self.assertEqual(initial_response.content, "")  # Empty initially
            self.assertEqual(initial_response.provider, self.provider_name)
            self.assertEqual(initial_response.model, self.default_model)
            self.assertIsNone(initial_response.finish_reason)  # Not completed yet
            
            # Check stream handler
            self.assertIsInstance(stream_handler, StreamHandler)
            
            # Process the stream manually and collect chunks
            chunks_received = []
            full_received_text = ""
            
            # Simulate manual iteration over the stream handler
            try:
                while True:
                    delta, response = next(stream_handler)
                    if delta:
                        chunks_received.append(delta)
                        full_received_text += delta
                        # Check that the response is updated with each chunk
                        self.assertEqual(response.content, full_received_text)
            except StopIteration:
                # Stream is complete
                pass
        
            # Check that the client was called with proper streaming parameters
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(args[0], f"{self.api_endpoint}/generate")
            self.assertTrue(kwargs["json"]["stream"])
            self.assertEqual(kwargs["json"]["model"], self.default_model)
            
            # Check that we received the expected number of text chunks
            self.assertEqual(len(chunks_received), 8)  # 8 content chunks
            
            # Check the collected full text
            self.assertEqual(full_received_text, full_content)

    @mock_test
    def test_stream_with_callback_mocked(self):
        """Test streaming with a callback function using mocked responses."""
        # Create a simple request
        request = self._create_request("Test with callback")
        
        # Create a mock for requests.post that returns a stream-like object
        with mock.patch("requests.post") as mock_post, \
             mock.patch("atlas.models.ollama.env.get_bool") as mock_env_get_bool:
             
            # Make env.get_bool return False for SKIP_API_KEY_CHECK
            def mock_env_get_bool_impl(key, default=False):
                if key == "SKIP_API_KEY_CHECK":
                    return False
                return default
                
            mock_env_get_bool.side_effect = mock_env_get_bool_impl
            
            # Create a properly mocked response with iter_lines method
            mock_response = mock.MagicMock()
            mock_response.status_code = 200
            
            # Create mock streaming responses
            full_content = "This is a callback test."
            streaming_responses = mock_streaming_ollama_response(content=full_content, model=self.default_model, chunks=5)
            
            # Create mock stream lines
            stream_lines = [
                json.dumps(response).encode() for response in streaming_responses
            ]
            
            # Create a proper iter_lines method
            mock_response.iter_lines = mock.MagicMock(return_value=iter(stream_lines))
            mock_post.return_value = mock_response
            
            # Create a callback function that collects chunks
            chunks_received = []
            responses_received = []
            
            def callback(delta, response):
                chunks_received.append(delta)
                responses_received.append(response.content)
            
            # Stream with callback
            final_response = self.provider.stream_with_callback(request, callback)
            
            # Check that the callback was called for each chunk
            self.assertEqual(len(chunks_received), 5)  # Content chunks call the callback
            
            # Check the final response
            self.assertIsInstance(final_response, ModelResponse)
            self.assertEqual(final_response.content, full_content)
            self.assertEqual(final_response.provider, self.provider_name)
            self.assertEqual(final_response.model, self.default_model)
            self.assertEqual(final_response.finish_reason, "stop")
            
            # Check token usage in final response (Ollama estimation)
            self.assertIsInstance(final_response.usage, TokenUsage)
            self.assertGreater(final_response.usage.input_tokens, 0)
            self.assertGreater(final_response.usage.output_tokens, 0)
            
            # Check cost calculation (should be 0 for Ollama)
            self.assertIsInstance(final_response.cost, CostEstimate)
            self.assertEqual(final_response.cost.total_cost, 0.0)

    @mock_test
    def test_error_handling(self):
        """Test error handling during API calls."""
        # Import error types for proper testing
        from atlas.core.errors import APIError
        import requests
        
        # Create a simple request
        request = self._create_request("Test error handling")
        
        # Test connection error
        with mock.patch("requests.post") as mock_post, \
             mock.patch("atlas.models.ollama.env.get_bool") as mock_env_get_bool:
        
            # Make env.get_bool return False for SKIP_API_KEY_CHECK
            def mock_env_get_bool_impl(key, default=False):
                if key == "SKIP_API_KEY_CHECK":
                    return False
                return default
                
            mock_env_get_bool.side_effect = mock_env_get_bool_impl
        
            # Set the connection error
            mock_post.side_effect = requests.ConnectionError("Connection error")
            
            # This should raise an APIError
            with self.assertRaises(APIError) as context:
                self.provider.generate(request)
            
            # Check that the error was properly converted to our error type
            self.assertIn("ollama api", str(context.exception).lower())
        
        # Test HTTP error response
        with mock.patch("requests.post") as mock_post, \
             mock.patch("atlas.models.ollama.env.get_bool") as mock_env_get_bool:
        
            # Make env.get_bool return False for SKIP_API_KEY_CHECK
            def mock_env_get_bool_impl(key, default=False):
                if key == "SKIP_API_KEY_CHECK":
                    return False
                return default
                
            mock_env_get_bool.side_effect = mock_env_get_bool_impl
            
            # Create a mock response with error status code
            mock_response = mock.MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal server error"
            mock_post.return_value = mock_response
            
            # This should raise an APIError
            with self.assertRaises(APIError) as context:
                self.provider.generate(request)
            
            # Check that the error was properly converted to our error type
            self.assertIn("ollama api", str(context.exception).lower())

    @mock_test
    def test_token_usage_calculation(self):
        """Test token usage calculation for Ollama."""
        # Ollama often doesn't provide token counts, test with both cases
        
        # Case 1: Ollama provides token counts
        response_data = {
            "prompt_eval_count": 15,
            "eval_count": 25,
        }
        
        # Create a request
        request = self._create_request("Test token usage")
        
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

    @mock_test
    def test_cost_calculation(self):
        """Test cost calculation for Ollama."""
        # Create a token usage
        usage = TokenUsage(input_tokens=1000, output_tokens=500)
        
        # Calculate cost - should always be 0 for Ollama
        cost = self.provider.calculate_cost(usage, self.default_model)
        
        # Check the calculated costs
        self.assertEqual(cost.input_cost, 0.0)
        self.assertEqual(cost.output_cost, 0.0)
        self.assertEqual(cost.total_cost, 0.0)
        
        # Test with different models - all should be 0
        cost_mistral = self.provider.calculate_cost(usage, "mistral")
        cost_llama2 = self.provider.calculate_cost(usage, "llama2")
        
        self.assertEqual(cost_mistral.total_cost, 0.0)
        self.assertEqual(cost_llama2.total_cost, 0.0)

    @mock_test
    def test_validate_api_key(self):
        """Test API key validation (server availability check for Ollama)."""
        # Mock the successful response
        with mock.patch("requests.get") as mock_get:
            mock_response = mock.MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            # Check validation - should succeed
            result = self.provider.validate_api_key()
            self.assertTrue(result)
            mock_get.assert_called_once_with(
                f"{self.api_endpoint}/version", 
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


if __name__ == "__main__":
    unittest.main()