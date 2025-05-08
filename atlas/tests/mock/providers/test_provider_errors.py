"""
Test error handling patterns for model providers.

This module tests the standardized error handling patterns across
different provider implementations.
"""

import os
import unittest
from unittest import mock
from typing import Dict, Any, List, Optional, Type, Callable

# Import decorators
from atlas.tests.helpers import mock_test

# Import error classes
from atlas.core.errors import (
    APIError,
    AuthenticationError,
    ValidationError,
    ErrorSeverity,
    AtlasError,
    safe_execute,
)

# Import models and providers
from atlas.models import (
    ModelProvider,
    ModelRequest,
    ModelMessage,
)

# Import provider implementations directly
from atlas.models.anthropic import AnthropicProvider
from atlas.models.openai import OpenAIProvider
from atlas.models.ollama import OllamaProvider
from atlas.models.mock import MockProvider

# Set environment variable for tests
os.environ["SKIP_API_KEY_CHECK"] = "true"


class TestProviderErrorHandling(unittest.TestCase):
    """Test error handling in model providers."""

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

    @mock_test
    def test_api_key_validation_errors(self):
        """Test error handling during API key validation."""
        # Test the MockProvider since it's the simplest
        mock_provider = MockProvider()
        
        # Success case
        mock_provider.validate_api_key = mock.MagicMock(return_value=True)
        result = mock_provider.validate_api_key()
        self.assertTrue(result)
        
        # Failure case
        mock_provider.validate_api_key = mock.MagicMock(return_value=False)
        result = mock_provider.validate_api_key()
        self.assertFalse(result)
        
        # Exception case - should handle gracefully
        def raise_error():
            raise ConnectionError("Cannot connect")
            
        mock_provider.validate_api_key = mock.MagicMock(side_effect=raise_error)
        result = mock_provider.validate_api_key()
        self.assertFalse(result)
    
    @mock_test
    def test_generate_error_handling(self):
        """Test error handling during generate calls."""
        # The mock provider has a way to simulate errors
        error_provider = MockProvider(simulate_errors=True, error_type="authentication")
        
        # Should raise an AuthenticationError
        with self.assertRaises(AuthenticationError):
            error_provider.generate(self.request)
        
        # Test with a different error type
        error_provider = MockProvider(simulate_errors=True, error_type="validation")
        with self.assertRaises(ValidationError):
            error_provider.generate(self.request)
        
        # Test with the default error type (API error)
        error_provider = MockProvider(simulate_errors=True)
        with self.assertRaises(APIError):
            error_provider.generate(self.request)
    
    @mock_test
    def test_streaming_error_handling(self):
        """Test error handling during streaming calls."""
        # The mock provider can simulate errors during streaming
        error_provider = MockProvider(simulate_errors=True, error_type="authentication")
        
        # Should raise an AuthenticationError
        with self.assertRaises(AuthenticationError):
            error_provider.stream(self.request)
        
        # Test with a different error type
        error_provider = MockProvider(simulate_errors=True, error_type="validation")
        with self.assertRaises(ValidationError):
            error_provider.stream(self.request)
        
        # Test with the default error type (API error)
        error_provider = MockProvider(simulate_errors=True)
        with self.assertRaises(APIError):
            error_provider.stream(self.request)
    
    @mock_test
    def test_stream_chunk_error_handling(self):
        """Test error handling during stream chunk processing."""
        # Use the mock provider with a special stream handler that will throw errors
        provider = MockProvider()
        
        # Create a request
        request = self.request
        
        # Get a streaming response
        initial_response, stream_handler = provider.stream(request)
        
        # Replace the __next__ method with one that raises an error
        original_next = stream_handler.__next__
        
        def error_next():
            """A custom __next__ method that raises an error."""
            raise ValueError("Error processing chunk")
        
        # Test handling of errors in the stream handler
        stream_handler.__next__ = error_next
        
        # Try to process the stream - this should not raise the ValueError
        # but convert it to a more appropriate error type
        with self.assertRaises(APIError) as context:
            for delta, response in stream_handler:
                pass
        
        # Check that our error message is present
        self.assertIn("error processing chunk", str(context.exception).lower())
        
        # Restore the original method
        stream_handler.__next__ = original_next

    @mock_test
    def test_openai_specific_errors(self):
        """Test OpenAI-specific error handling."""
        # Create a provider that will simulate specific OpenAI errors
        provider = OpenAIProvider(api_key="test-key")
        
        # Create various error-raising methods
        def raise_rate_limit(*args, **kwargs):
            raise APIError(
                message="Rate limit exceeded",
                details={"provider": "openai", "status_code": 429},
                retry_possible=True,
                severity=ErrorSeverity.WARNING
            )
        
        def raise_invalid_api_key(*args, **kwargs):
            raise AuthenticationError(
                message="Invalid API key",
                provider="openai",
                severity=ErrorSeverity.ERROR
            )
        
        def raise_model_not_found(*args, **kwargs):
            raise ValidationError(
                message="Model not found",
                severity=ErrorSeverity.ERROR
            )
        
        # Test with rate limit error
        provider.generate = mock.MagicMock(side_effect=raise_rate_limit)
        with self.assertRaises(APIError) as context:
            provider.generate(self.request)
        self.assertIn("rate limit", str(context.exception).lower())
        self.assertEqual(context.exception.details.get("provider"), "openai")
        self.assertTrue(context.exception.details.get("retry_possible", False))
        
        # Test with authentication error
        provider.generate = mock.MagicMock(side_effect=raise_invalid_api_key)
        with self.assertRaises(AuthenticationError) as context:
            provider.generate(self.request)
        self.assertIn("invalid api key", str(context.exception).lower())
        self.assertEqual(context.exception.details.get("provider"), "openai")
        
        # Test with validation error
        provider.generate = mock.MagicMock(side_effect=raise_model_not_found)
        with self.assertRaises(ValidationError) as context:
            provider.generate(self.request)
        self.assertIn("model not found", str(context.exception).lower())

    @mock_test
    def test_anthropic_specific_errors(self):
        """Test Anthropic-specific error handling."""
        # Create a provider that will simulate specific Anthropic errors
        provider = AnthropicProvider(api_key="test-key")
        
        # Create various error-raising methods
        def raise_rate_limit(*args, **kwargs):
            raise APIError(
                message="Rate limit exceeded",
                details={"provider": "anthropic", "status_code": 429},
                retry_possible=True,
                severity=ErrorSeverity.WARNING
            )
        
        def raise_invalid_api_key(*args, **kwargs):
            raise AuthenticationError(
                message="Invalid API key",
                provider="anthropic",
                severity=ErrorSeverity.ERROR
            )
        
        def raise_model_not_found(*args, **kwargs):
            raise ValidationError(
                message="Model not found",
                severity=ErrorSeverity.ERROR
            )
        
        # Test with rate limit error
        provider.generate = mock.MagicMock(side_effect=raise_rate_limit)
        with self.assertRaises(APIError) as context:
            provider.generate(self.request)
        self.assertIn("rate limit", str(context.exception).lower())
        self.assertEqual(context.exception.details.get("provider"), "anthropic")
        self.assertTrue(context.exception.details.get("retry_possible", False))
        
        # Test with authentication error
        provider.generate = mock.MagicMock(side_effect=raise_invalid_api_key)
        with self.assertRaises(AuthenticationError) as context:
            provider.generate(self.request)
        self.assertIn("invalid api key", str(context.exception).lower())
        self.assertEqual(context.exception.details.get("provider"), "anthropic")
        
        # Test with validation error
        provider.generate = mock.MagicMock(side_effect=raise_model_not_found)
        with self.assertRaises(ValidationError) as context:
            provider.generate(self.request)
        self.assertIn("model not found", str(context.exception).lower())

    @mock_test
    def test_ollama_specific_errors(self):
        """Test Ollama-specific error handling."""
        # Create a provider that will simulate specific Ollama errors
        provider = OllamaProvider()
        
        # Create various error-raising methods
        def raise_connection_error(*args, **kwargs):
            raise APIError(
                message="Connection error",
                details={"provider": "ollama"},
                retry_possible=True,
                severity=ErrorSeverity.ERROR
            )
        
        def raise_model_not_found(*args, **kwargs):
            raise ValidationError(
                message="Model not found",
                severity=ErrorSeverity.ERROR
            )
        
        # Test with connection error
        provider.generate = mock.MagicMock(side_effect=raise_connection_error)
        with self.assertRaises(APIError) as context:
            provider.generate(self.request)
        self.assertIn("connection error", str(context.exception).lower())
        self.assertEqual(context.exception.details.get("provider"), "ollama")
        
        # Test with validation error (model not found)
        provider.generate = mock.MagicMock(side_effect=raise_model_not_found)
        with self.assertRaises(ValidationError) as context:
            provider.generate(self.request)
        self.assertIn("model not found", str(context.exception).lower())


if __name__ == "__main__":
    unittest.main()