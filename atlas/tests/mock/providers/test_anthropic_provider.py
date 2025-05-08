"""
Test Anthropic provider implementation.

This module tests the functionality of the Anthropic provider using mocked responses.
"""

import os
import sys
import unittest
from unittest import mock
from typing import Dict, Any, List, Optional

from atlas.tests.helpers.decorators import mock_test
from atlas.tests.helpers.base_classes import AnthropicProviderTestBase

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
from atlas.models.anthropic import AnthropicProvider


class TestAnthropicMockProvider(AnthropicProviderTestBase):
    """Test the AnthropicProvider class with mocked responses."""

    provider_class = AnthropicProvider
    provider_name = "anthropic"
    default_model = "claude-3-7-sonnet-20250219"  # Update to match implementation default
    
    def setUp(self):
        """Set up the test."""
        super().setUp()
        # Set up API key for tests
        self.api_key = "test-api-key"
        
        # Create proper environment for tests with API key skipping
        self.env_patcher = mock.patch.dict(os.environ, {"SKIP_API_KEY_CHECK": "true"})
        self.env_patcher.start()
        self.provider = self.provider_class(api_key=self.api_key, model_name=self.default_model)
        
    def tearDown(self):
        """Tear down the test environment."""
        # Stop environment patching
        self.env_patcher.stop()
        super().tearDown()

    @mock_test
    def test_provider_creation(self):
        """Test creating a provider."""
        # Check provider name
        self.assertEqual(self.provider.name, self.provider_name)

        # Check default model
        self.assertEqual(self.provider._model_name, self.default_model)

        # Create with custom parameters
        custom_provider = self.provider_class(
            model_name="claude-3-haiku-20240307",
            api_key=self.api_key,
            max_tokens=1000
        )
        
        self.assertEqual(custom_provider._model_name, "claude-3-haiku-20240307")
        self.assertEqual(custom_provider._max_tokens, 1000)

    @mock_test
    def test_validate_api_key(self):
        """Test API key validation."""
        # Setup: Directly mock the env.get_bool function to ensure SKIP_API_KEY_CHECK returns True
        with mock.patch('atlas.core.env.get_bool', return_value=True):
            # Create a provider with a test API key
            provider = self.provider_class(api_key="test-api-key", model_name=self.default_model)
            
            # When SKIP_API_KEY_CHECK is true, validate_api_key should return True
            self.assertTrue(provider.validate_api_key())
            
            # Should also pass with empty key when SKIP_API_KEY_CHECK is true
            empty_provider = self.provider_class(api_key="", model_name=self.default_model)
            self.assertTrue(empty_provider.validate_api_key())
            
            # Should also pass with None key when SKIP_API_KEY_CHECK is true
            null_provider = self.provider_class(api_key=None, model_name=self.default_model)
            self.assertTrue(null_provider.validate_api_key())

    @mock_test
    def test_available_models(self):
        """Test getting available models."""
        # Check that the provider returns expected models
        models = self.provider.get_available_models()
        self.assertIsInstance(models, list)
        self.assertGreater(len(models), 0)
        
        # Claude models should be included
        self.assertIn("claude-3-opus-20240229", models)
        self.assertIn("claude-3-sonnet-20240229", models)
        self.assertIn("claude-3-haiku-20240307", models)

    @mock_test
    def test_generate(self):
        """Test generating a response."""
        # Create a request
        request = self._create_request("Test message")
        
        # Create custom mock response
        with mock.patch.dict(os.environ, {"SKIP_API_KEY_CHECK": "true"}):
            # Mock the client
            with mock.patch.object(self.provider, '_client') as mock_client:
                # Create a response object
                mock_response = type('Response', (), {
                    'content': [type('Content', (), {'text': "Test response"})],
                    'usage': type('Usage', (), {
                        'input_tokens': 10,
                        'output_tokens': 5
                    }),
                    'model': self.default_model,
                    'stop_reason': 'stop',
                    'model_dump': lambda: {}
                })
                
                # Configure mock to return our response
                mock_client.messages.create.return_value = mock_response
                
                # Generate a response
                response = self.provider.generate(request)
                
                # Check response structure
                self.assertIsInstance(response, ModelResponse)
                self.assertEqual(response.content, "Test response")
                self.assertEqual(response.provider, self.provider_name)
                self.assertEqual(response.model, self.default_model)
                
                # Check token usage
                self.assertIsInstance(response.usage, TokenUsage)
                self.assertEqual(response.usage.input_tokens, 10)
                self.assertEqual(response.usage.output_tokens, 5)
                self.assertEqual(response.usage.total_tokens, 15)
                
                # Check that the API was called correctly
                mock_client.messages.create.assert_called_once()
                create_args = mock_client.messages.create.call_args[1]
                self.assertEqual(create_args["model"], self.default_model)
                self.assertIn("messages", create_args)

    @mock.patch("anthropic.Anthropic")
    @mock_test
    def test_generate_with_parameters(self, mock_anthropic_class):
        """Test generating a response with custom parameters."""
        # Create mock response
        mock_client = mock.MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        mock_response = mock.MagicMock()
        mock_response.content = [mock.MagicMock(text="Custom response")]
        mock_response.usage.input_tokens = 12
        mock_response.usage.output_tokens = 8
        mock_response.model = "claude-3-haiku-20240307"
        mock_client.messages.create.return_value = mock_response
        
        # Create custom provider
        custom_provider = self.provider_class(
            model_name="claude-3-haiku-20240307",
            api_key=self.api_key,
            max_tokens=50,
            temperature=0.7
        )
        
        # Create a request with custom parameters
        request = ModelRequest(
            messages=[ModelMessage.user("Custom parameters test")],
            max_tokens=30,
            temperature=0.5,
            top_p=0.95
        )
        
        # Generate a response
        response = custom_provider.generate(request)
        
        # Check response
        self.assertEqual(response.content, "Custom response")
        self.assertEqual(response.model, "claude-3-haiku-20240307")
        
        # Check that the API was called with correct parameters
        mock_client.messages.create.assert_called_once()
        create_args = mock_client.messages.create.call_args[1]
        self.assertEqual(create_args["model"], "claude-3-haiku-20240307")
        self.assertEqual(create_args["max_tokens"], 30)  # Request overrides provider
        self.assertEqual(create_args["temperature"], 0.5)  # Request overrides provider
        self.assertEqual(create_args["top_p"], 0.95)

    @mock_test
    def test_stream(self):
        """Test streaming a response."""
        # Create a request
        request = self._create_request("Test streaming")
        
        # Create a simple stream generator function
        def simple_stream_generator():
            class SimpleChunk:
                def __init__(self, chunk_type, text=None, input_tokens=None, output_tokens=None, stop_reason=None):
                    self.type = chunk_type
                    if text:
                        self.delta = SimpleAttribute(text=text)
                    if input_tokens is not None and output_tokens is not None:
                        self.usage = SimpleAttribute(input_tokens=input_tokens, output_tokens=output_tokens)
                    if stop_reason:
                        self.stop_reason = stop_reason
            
            class SimpleAttribute:
                def __init__(self, **kwargs):
                    for key, value in kwargs.items():
                        setattr(self, key, value)
            
            # Yield content chunks
            yield SimpleChunk("content_block_delta", text="Hello")
            yield SimpleChunk("content_block_delta", text=" world")
            
            # Yield final chunk with usage info
            yield SimpleChunk(
                "message_stop", 
                input_tokens=10, 
                output_tokens=2,
                stop_reason="stop"
            )
        
        # Skip actual API call with environment variable
        with mock.patch.dict(os.environ, {"SKIP_API_KEY_CHECK": "true"}):
            # Mock the client's create method to return our simple stream
            with mock.patch.object(self.provider, '_client') as mock_client:
                mock_client.messages.create.return_value = simple_stream_generator()
                
                # Get streaming response
                initial_response, stream_handler = self.provider.stream(request)
                
                # Check initial response
                self.assertIsInstance(initial_response, ModelResponse)
                self.assertEqual(initial_response.content, "")
                
                # Process the stream
                chunks = []
                for delta, response in stream_handler:
                    if delta:  # Only append non-empty deltas
                        chunks.append(delta)
                
                # Check chunks
                self.assertEqual(chunks, ["Hello", " world"])
                
                # Check final response
                self.assertEqual(stream_handler.response.content, "Hello world")
                self.assertEqual(stream_handler.response.provider, self.provider_name)
                
                # Check token usage
                self.assertEqual(stream_handler.response.usage.input_tokens, 10)
                self.assertEqual(stream_handler.response.usage.output_tokens, 2)
                self.assertEqual(stream_handler.response.usage.total_tokens, 12)

    @mock_test
    def test_stream_with_callback(self):
        """Test streaming with a callback function."""
        # Create a request
        request = self._create_request("Test streaming callback")
        
        # Create a simple stream generator function
        def simple_stream_generator():
            class SimpleChunk:
                def __init__(self, chunk_type, text=None, input_tokens=None, output_tokens=None, stop_reason=None):
                    self.type = chunk_type
                    if text:
                        self.delta = SimpleAttribute(text=text)
                    if input_tokens is not None and output_tokens is not None:
                        self.usage = SimpleAttribute(input_tokens=input_tokens, output_tokens=output_tokens)
                    if stop_reason:
                        self.stop_reason = stop_reason
            
            class SimpleAttribute:
                def __init__(self, **kwargs):
                    for key, value in kwargs.items():
                        setattr(self, key, value)
            
            # Yield content chunks
            yield SimpleChunk("content_block_delta", text="Testing")
            yield SimpleChunk("content_block_delta", text=" callback")
            
            # Yield final chunk with usage info
            yield SimpleChunk(
                "message_stop", 
                input_tokens=10, 
                output_tokens=2,
                stop_reason="stop"
            )
        
        # Create callback function that collects chunks
        collected_chunks = []
        collected_responses = []
        
        def callback(delta, response):
            collected_chunks.append(delta)
            collected_responses.append(response.content)
        
        # Skip actual API call with environment variable
        with mock.patch.dict(os.environ, {"SKIP_API_KEY_CHECK": "true"}):
            # Mock the client's create method to return our simple stream
            with mock.patch.object(self.provider, '_client') as mock_client:
                mock_client.messages.create.return_value = simple_stream_generator()
                
                # Stream with callback
                final_response = self.provider.stream_with_callback(request, callback)
                
                # Check collected chunks
                self.assertEqual(collected_chunks, ["Testing", " callback"])
                
                # Check collected responses (progressive content building)
                self.assertEqual(collected_responses, ["Testing", "Testing callback"])
                
                # Check final response
                self.assertEqual(final_response.content, "Testing callback")
                self.assertEqual(final_response.provider, self.provider_name)
                
                # Check that the API was called correctly
                mock_client.messages.create.assert_called_once()
                create_args = mock_client.messages.create.call_args[1]
                self.assertTrue(create_args["stream"])

    @mock_test
    def test_cost_calculation(self):
        """Test cost calculation for different models."""
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
            cost = self.provider.calculate_cost(usage, model)
            
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

    @mock_test
    def test_error_handling(self):
        """Test error handling."""
        # Create a request for testing
        request = self._create_request("Test error handling")
        
        # Create a separate mock module for the Anthropic library
        mock_anthropic_module = mock.MagicMock()
        
        # Mock all error types we need to test
        mock_anthropic_module.AuthenticationError = type('AuthenticationError', (Exception,), {})
        mock_anthropic_module.RateLimitError = type('RateLimitError', (Exception,), {})
        mock_anthropic_module.APIStatusError = type('APIStatusError', (Exception,), {})
        
        # Test each error type
        with mock.patch.dict('sys.modules', {'anthropic': mock_anthropic_module}):
            # Create a provider instance that uses our mocked module
            with mock.patch.dict(os.environ, {"SKIP_API_KEY_CHECK": "true"}):
                provider = self.provider_class(api_key=self.api_key, model_name=self.default_model)
                
                # Test authentication error
                with mock.patch.object(provider, '_client') as mock_client:
                    # Make the client raise an AuthenticationError
                    mock_client.messages.create.side_effect = mock_anthropic_module.AuthenticationError()
                    
                    # Attempt to generate and expect an error
                    with self.assertRaises(Exception) as context:
                        provider.generate(request)
                    
                    # Verify the error message
                    error_message = str(context.exception)
                    self.assertTrue(
                        "Authentication" in error_message or "Failed to generate" in error_message,
                        f"Error message '{error_message}' doesn't contain expected text"
                    )
                
                # Test rate limit error
                with mock.patch.object(provider, '_client') as mock_client:
                    # Make the client raise a RateLimitError
                    mock_client.messages.create.side_effect = mock_anthropic_module.RateLimitError()
                    
                    # Attempt to generate and expect an error
                    with self.assertRaises(Exception) as context:
                        provider.generate(request)
                    
                    # Verify the error message
                    error_message = str(context.exception)
                    self.assertTrue(
                        "Rate limit" in error_message or "Failed to generate" in error_message,
                        f"Error message '{error_message}' doesn't contain expected text"
                    )
                
                # Test API error
                with mock.patch.object(provider, '_client') as mock_client:
                    # Make the client raise an APIStatusError
                    mock_client.messages.create.side_effect = mock_anthropic_module.APIStatusError()
                    
                    # Attempt to generate and expect an error
                    with self.assertRaises(Exception) as context:
                        provider.generate(request)
                    
                    # Verify the error message
                    error_message = str(context.exception)
                    self.assertTrue(
                        "API" in error_message or "Failed to generate" in error_message,
                        f"Error message '{error_message}' doesn't contain expected text"
                    )


if __name__ == "__main__":
    unittest.main()