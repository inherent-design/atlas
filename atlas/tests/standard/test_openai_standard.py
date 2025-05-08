"""
Standardized tests for OpenAI provider implementation.

This module uses the standardized test patterns to make tests more resilient
to implementation changes and easier to maintain.
"""

import os
import sys
import unittest
import logging
from unittest import mock
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Import test helpers
from atlas.tests.test_helpers import (
    ProviderTestBase,
    api_test,
    mock_test,
    expensive_test,
    create_mock_response,
    MockProvider,
)

# Import models module
from atlas.models import (
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ModelMessage,
    TokenUsage,
    CostEstimate,
)

# Import OpenAI provider
from atlas.models.openai import OpenAIProvider

# Import errors
from atlas.core.errors import APIError, AuthenticationError, ValidationError, ErrorSeverity

# Configure logging
logger = logging.getLogger(__name__)


class TestOpenAIProvider(ProviderTestBase):
    """Standardized tests for OpenAI provider using the base test class."""
    
    # Class configuration
    provider_class = OpenAIProvider
    provider_name = "openai"
    default_model = "gpt-4o"  # Current default in tests
    cheap_model = "gpt-3.5-turbo"  # For API tests
    expensive_model = "gpt-4"  # For expensive tests
    has_streaming = True
    
    def _check_api_key(self) -> bool:
        """Check if OpenAI API key is set."""
        return bool(os.environ.get("OPENAI_API_KEY"))
    
    def _create_provider(self):
        """Create a provider instance with appropriate configuration."""
        if os.environ.get("RUN_API_TESTS"):
            # Use cheap model for API tests
            return OpenAIProvider(model_name=self.cheap_model)
        else:
            # Use mock-compatible model for mock tests
            return OpenAIProvider(model_name="gpt-4o")
    
    def test_provider_creation(self):
        """Test creating an OpenAI provider."""
        # Test with base implementation
        super().test_provider_creation()
        
        # Additional provider-specific assertions - check for key attributes
        # but don't assume specific implementation details
        self.assertTrue(hasattr(self.provider, "_api_key"))
        
        # Test with custom parameters
        custom_provider = OpenAIProvider(
            model_name="gpt-4",
            max_tokens=1000,
            temperature=0.7,
        )
        
        # Extract model name without hardcoding it
        expected_model = "gpt-4"
        actual_model = custom_provider._model_name
        
        self.assertEqual(actual_model, expected_model)
        self.assertEqual(custom_provider._max_tokens, 1000)
        self.assertEqual(custom_provider._additional_params["temperature"], 0.7)
    
    @mock_test
    def test_generate_mocked(self):
        """Test generating a response with mocked API."""
        # Create a request
        request = self._create_request()
        
        # Set up a mock response
        expected_content = "This is a test response from OpenAI."
        
        # Mock the OpenAI client
        with mock.patch("atlas.models.openai.OpenAI") as mock_openai_class, \
             mock.patch("atlas.models.openai.env.get_bool") as mock_env_get_bool:
            
            # Configure mocks
            mock_env_get_bool.return_value = False
            
            # Mock the response
            mock_client = mock.MagicMock()
            mock_openai_class.return_value = mock_client
            
            # Set up the output content manually to avoid relying on internal structure
            def mock_create_completion(**kwargs):
                mock_completion = mock.MagicMock()
                mock_completion.choices = [mock.MagicMock()]
                mock_completion.choices[0].message.content = expected_content
                mock_completion.choices[0].finish_reason = "stop"
                mock_completion.usage.prompt_tokens = 10
                mock_completion.usage.completion_tokens = 15
                mock_completion.usage.total_tokens = 25
                return mock_completion
            
            # Configure the mock client
            mock_client.chat.completions.create.side_effect = mock_create_completion
            
            # Generate a response
            response = self.provider.generate(request)
            
            # Verify the response
            self.assertIsInstance(response, ModelResponse)
            self.assertEqual(response.content, expected_content)
            self.assertEqual(response.provider, "openai")
            self.assertEqual(response.finish_reason, "stop")
            
            # Verify token usage
            self.assertEqual(response.usage.input_tokens, 10)
            self.assertEqual(response.usage.output_tokens, 15)
            self.assertEqual(response.usage.total_tokens, 25)
    
    @mock_test
    def test_streaming_mocked(self):
        """Test streaming a response with mocked API."""
        # Create a request
        request = self._create_request()
        
        # Mock the OpenAI client
        with mock.patch("atlas.models.openai.OpenAI") as mock_openai_class, \
             mock.patch("atlas.models.openai.env.get_bool") as mock_env_get_bool:
            
            # Configure mocks
            mock_env_get_bool.return_value = False
            
            # Mock the client
            mock_client = mock.MagicMock()
            mock_openai_class.return_value = mock_client
            
            # Create mock chunks
            chunk_contents = ["This ", "is ", "a ", "test ", "response."]
            mock_chunks = []
            
            for content in chunk_contents:
                mock_chunk = mock.MagicMock()
                mock_chunk.choices = [mock.MagicMock()]
                mock_chunk.choices[0].delta.content = content
                mock_chunks.append(mock_chunk)
            
            # Add final chunk with finish_reason
            final_chunk = mock.MagicMock()
            final_chunk.choices = [mock.MagicMock()]
            final_chunk.choices[0].delta.content = None
            final_chunk.choices[0].finish_reason = "stop"
            mock_chunks.append(final_chunk)
            
            # Configure the mock client
            mock_client.chat.completions.create.return_value = mock_chunks
            
            # Collect streaming chunks
            collected_chunks = []
            
            def stream_callback(delta, response):
                collected_chunks.append(delta)
            
            # Stream with callback
            response = self.provider.stream_with_callback(request, stream_callback)
            
            # Verify the response
            self.assertIsInstance(response, ModelResponse)
            self.assertEqual(response.content, "This is a test response.")
            self.assertEqual(response.provider, "openai")
            self.assertEqual(response.finish_reason, "stop")
            
            # Verify collected chunks
            self.assertEqual(len(collected_chunks), len(chunk_contents))
            self.assertEqual("".join(collected_chunks), "This is a test response.")
    
    @mock_test
    def test_error_handling(self):
        """Test error handling during API calls."""
        # Create a request
        request = self._create_request()
        
        # Test authentication error
        with mock.patch("atlas.models.openai.OpenAI") as mock_openai_class, \
             mock.patch("atlas.models.openai.env.get_bool") as mock_env_get_bool:
            
            # Configure mocks
            mock_env_get_bool.return_value = False
            
            # Configure the mock client to raise an exception
            mock_client = mock.MagicMock()
            mock_openai_class.return_value = mock_client
            
            # Create a mock exception - don't rely on openai internals
            class MockAuthError(Exception):
                def __init__(self, message):
                    self.message = message
                    super().__init__(message)
            
            mock_client.chat.completions.create.side_effect = MockAuthError("Invalid API key")
            
            # This should raise an AuthenticationError
            with self.assertRaises(AuthenticationError) as context:
                self.provider.generate(request)
            
            # Check the error message
            self.assertIn("api key", str(context.exception).lower())
        
        # Test rate limit error
        with mock.patch("atlas.models.openai.OpenAI") as mock_openai_class, \
             mock.patch("atlas.models.openai.env.get_bool") as mock_env_get_bool:
            
            # Configure mocks
            mock_env_get_bool.return_value = False
            
            # Configure the mock client to raise an exception
            mock_client = mock.MagicMock()
            mock_openai_class.return_value = mock_client
            
            # Create a mock exception
            class MockRateLimitError(Exception):
                def __init__(self, message):
                    self.message = message
                    super().__init__(message)
            
            mock_client.chat.completions.create.side_effect = MockRateLimitError("Rate limit exceeded")
            
            # This should raise an APIError
            with self.assertRaises(APIError) as context:
                self.provider.generate(request)
            
            # Check the error message
            self.assertIn("rate limit", str(context.exception).lower())
    
    @mock_test
    def test_cost_calculation(self):
        """Test cost calculation."""
        # Create a usage object
        usage = TokenUsage(input_tokens=1000, output_tokens=500)
        
        # Calculate cost for different models without hardcoding prices
        for model_name in ["gpt-4", "gpt-3.5-turbo"]:
            cost = self.provider.calculate_cost(usage, model_name)
            
            # Check that the cost calculation works
            self.assertIsInstance(cost, CostEstimate)
            self.assertGreater(cost.input_cost, 0.0)
            self.assertGreater(cost.output_cost, 0.0)
            self.assertEqual(cost.total_cost, cost.input_cost + cost.output_cost)
            
            # Check that gpt-4 is more expensive than gpt-3.5-turbo
            if model_name == "gpt-4":
                gpt4_cost = cost.total_cost
            elif model_name == "gpt-3.5-turbo":
                gpt35_cost = cost.total_cost
        
        # Verify relative costs without hardcoding specific values
        self.assertGreater(gpt4_cost, gpt35_cost)
    
    @api_test
    def test_generate_api(self):
        """Test generate with real API call."""
        # Use base implementation
        super().test_generate_api()
    
    @api_test
    def test_streaming_api(self):
        """Test streaming with real API call."""
        # Use base implementation
        super().test_streaming_api()
    
    @expensive_test
    def test_gpt4_api_call(self):
        """Test API call with GPT-4 (more expensive model)."""
        # Create a provider with GPT-4
        provider = OpenAIProvider(model_name="gpt-4")
        
        # Create a simple request
        request = self._create_request("Write a single word response: Hello", max_tokens=5)
        
        # Generate a response
        response = provider.generate(request)
        
        # Track token usage
        self.track_usage(response)
        
        # Basic assertions
        self.assertIsNotNone(response.content)
        self.assertEqual(response.provider, "openai")
        self.assertIsNotNone(response.model)
        
        # Token usage should be reasonable
        self.assertLessEqual(response.usage.total_tokens, 30)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    unittest.main()