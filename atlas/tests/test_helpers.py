"""
Test helpers for Atlas tests.

This module provides standardized testing patterns and utilities to make tests
more resilient to implementation changes and easier to maintain.
"""

import os
import functools
import unittest
import logging
from typing import Dict, Any, List, Optional, Type, Callable, TypeVar, Union, Tuple

# Configure logging
logger = logging.getLogger(__name__)

# Type variables for generics
T = TypeVar('T')
ProviderType = TypeVar('ProviderType')
ModelRequestType = TypeVar('ModelRequestType')
ModelResponseType = TypeVar('ModelResponseType')


# Test Decorators
def mock_test(f):
    """Decorator for tests that use mocked responses.
    
    This decorator marks tests that don't make real API calls and should always run.
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    wrapper.__doc__ = f.__doc__ or ""
    wrapper.__doc__ += "\n\nThis test uses mocked responses and does not make API calls."
    return wrapper


def api_test(f):
    """Decorator for tests that make real API calls.
    
    This decorator will skip the test unless RUN_API_TESTS=true is set.
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not os.environ.get("RUN_API_TESTS"):
            return unittest.skip("API tests disabled - set RUN_API_TESTS=true to enable")(f)(*args, **kwargs)
        return f(*args, **kwargs)
    wrapper.__doc__ = f.__doc__ or ""
    wrapper.__doc__ += "\n\nThis test makes real API calls and may incur costs."
    return wrapper


def expensive_test(f):
    """Decorator for tests that make expensive API calls.
    
    This decorator will skip the test unless RUN_EXPENSIVE_TESTS=true is set.
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not os.environ.get("RUN_EXPENSIVE_TESTS"):
            return unittest.skip("Expensive tests disabled - set RUN_EXPENSIVE_TESTS=true to enable")(f)(*args, **kwargs)
        return f(*args, **kwargs)
    wrapper.__doc__ = f.__doc__ or ""
    wrapper.__doc__ += "\n\nThis test makes expensive API calls and may incur significant costs."
    return wrapper


def integration_test(f):
    """Decorator for integration tests that connect multiple components.
    
    This decorator will skip the test unless RUN_INTEGRATION_TESTS=true is set.
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not os.environ.get("RUN_INTEGRATION_TESTS"):
            return unittest.skip("Integration tests disabled - set RUN_INTEGRATION_TESTS=true to enable")(f)(*args, **kwargs)
        return f(*args, **kwargs)
    wrapper.__doc__ = f.__doc__ or ""
    wrapper.__doc__ += "\n\nThis is an integration test that connects multiple components."
    return wrapper


# Base Test Classes
class TestWithTokenTracking(unittest.TestCase):
    """Base class for tests with token usage tracking."""
    
    def setUp(self):
        """Set up token tracking."""
        self.total_tokens_used = 0
        self.estimated_cost = 0.0
    
    def track_usage(self, response):
        """Track token usage from a response.
        
        Args:
            response: A ModelResponse object with usage information.
        """
        if hasattr(response, "usage") and response.usage:
            self.total_tokens_used += response.usage.total_tokens
            if hasattr(response, "cost") and response.cost:
                self.estimated_cost += response.cost.total_cost
    
    def tearDown(self):
        """Report token usage at the end of the test."""
        logger.info(f"Test {self._testMethodName} used {self.total_tokens_used} tokens " +
                   f"at an estimated cost of ${self.estimated_cost:.6f}")


class ProviderTestBase(TestWithTokenTracking):
    """Base class for provider tests with standardized test methods."""
    
    # Override these in subclasses
    provider_class = None  # The provider class to test
    provider_name = None   # The expected provider name
    default_model = None   # The default model name for tests
    cheap_model = None     # A cheaper model for API tests
    expensive_model = None # A more expensive model for expensive tests
    has_streaming = True   # Whether the provider supports streaming
    
    def setUp(self):
        """Set up the test with a provider instance."""
        super().setUp()
        
        # Skip the whole test class if the provider_class is not set
        if not self.provider_class:
            self.skipTest("Provider class not set")
            
        # Skip if required API key is not set (when running API tests)
        if os.environ.get("RUN_API_TESTS") and not self._check_api_key():
            self.skipTest(f"API key not set for {self.provider_name} provider")
            
        # Create a provider instance
        self.provider = self._create_provider()
        
        # Set expected provider name if not set
        if not self.provider_name:
            self.provider_name = self.provider.name
            
        # Set default model if not set
        if not self.default_model and hasattr(self.provider, "_model_name"):
            self.default_model = self.provider._model_name
    
    def _check_api_key(self) -> bool:
        """Check if the required API key is set.
        
        Override this in subclasses to check for specific API keys.
        
        Returns:
            True if the API key is set, False otherwise.
        """
        return True
    
    def _create_provider(self):
        """Create a provider instance for testing.
        
        Override this in subclasses if needed.
        
        Returns:
            A provider instance.
        """
        if not self.provider_class:
            raise ValueError("Provider class not set")
        return self.provider_class()
    
    def _create_request(self, content="Test message", max_tokens=10):
        """Create a standard test request.
        
        Args:
            content: The message content.
            max_tokens: Maximum tokens for the response.
            
        Returns:
            A ModelRequest object.
        """
        from atlas.models import ModelRequest, ModelMessage
        
        # Create a simple request
        return ModelRequest(
            messages=[ModelMessage.user(content)],
            max_tokens=max_tokens
        )
    
    def test_provider_creation(self):
        """Test creating a provider instance."""
        self.assertIsNotNone(self.provider)
        self.assertEqual(self.provider.name, self.provider_name)
    
    @mock_test
    def test_generate_mocked(self):
        """Test generate with mocked response."""
        # This should be implemented in subclasses
        pass
    
    @api_test
    def test_generate_api(self):
        """Test generate with real API call."""
        # Create a request
        request = self._create_request("Write a single word response: Hello", max_tokens=5)
        
        # Generate a response
        response = self.provider.generate(request)
        
        # Track token usage
        self.track_usage(response)
        
        # Basic assertions
        self.assertIsNotNone(response.content)
        self.assertEqual(response.provider, self.provider_name)
        self.assertIsNotNone(response.usage)
        self.assertLessEqual(response.usage.total_tokens, 30)  # Reasonable limit
    
    @api_test
    def test_streaming_api(self):
        """Test streaming with real API call."""
        # Skip if streaming is not supported
        if not self.has_streaming:
            self.skipTest("Streaming not supported by this provider")
        
        # Create a request
        request = self._create_request("Write a single word response: Hello", max_tokens=5)
        
        # Collect streaming chunks
        collected_chunks = []
        
        def stream_callback(delta, response):
            collected_chunks.append(delta)
        
        # Stream with callback
        response = self.provider.stream_with_callback(request, stream_callback)
        
        # Track token usage
        self.track_usage(response)
        
        # Basic assertions
        self.assertIsNotNone(response.content)
        self.assertEqual(response.provider, self.provider_name)
        self.assertGreater(len(collected_chunks), 0)
        self.assertLessEqual(response.usage.total_tokens, 30)  # Reasonable limit


# Mock Response Factory Functions
def create_mock_message(role="user", content="Test message"):
    """Create a mock message for testing.
    
    Args:
        role: The message role.
        content: The message content.
        
    Returns:
        A ModelMessage object.
    """
    from atlas.models import ModelMessage, ModelRole
    
    return ModelMessage(
        role=ModelRole(role),
        content=content
    )


def create_mock_request(messages=None, model=None, max_tokens=100):
    """Create a mock request for testing.
    
    Args:
        messages: List of messages.
        model: Optional model name.
        max_tokens: Maximum tokens for the response.
        
    Returns:
        A ModelRequest object.
    """
    from atlas.models import ModelRequest
    
    if messages is None:
        messages = [create_mock_message()]
    
    return ModelRequest(
        messages=messages,
        model=model,
        max_tokens=max_tokens
    )


def create_mock_response(content="Mock response", provider="mock", model="mock-model"):
    """Create a mock response for testing.
    
    Args:
        content: The response content.
        provider: The provider name.
        model: The model name.
        
    Returns:
        A ModelResponse object.
    """
    from atlas.models import ModelResponse, TokenUsage, CostEstimate
    
    return ModelResponse(
        content=content,
        provider=provider,
        model=model,
        usage=TokenUsage(input_tokens=10, output_tokens=10, total_tokens=20),
        cost=CostEstimate(input_cost=0.0, output_cost=0.0, total_cost=0.0),
        finish_reason="stop",
        raw_response={}
    )


# Mock Context Managers
class MockProvider:
    """Context manager for mocking provider API calls."""
    
    def __init__(self, provider_class, **kwargs):
        """Initialize with provider class and mock responses.
        
        Args:
            provider_class: The provider class to mock.
            **kwargs: Additional configuration.
        """
        self.provider_class = provider_class
        self.mock_responses = kwargs.get('mock_responses', {})
        self.original_methods = {}
    
    def __enter__(self):
        """Set up mocking."""
        # Store original methods
        for method_name, mock_func in self.mock_responses.items():
            if hasattr(self.provider_class, method_name):
                self.original_methods[method_name] = getattr(self.provider_class, method_name)
                setattr(self.provider_class, method_name, mock_func)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Tear down mocking."""
        # Restore original methods
        for method_name, original_func in self.original_methods.items():
            setattr(self.provider_class, method_name, original_func)


# Integration Test Utilities
def create_integration_test(components: List[Any], test_func: Callable):
    """Create an integration test connecting multiple components.
    
    Args:
        components: List of component instances to connect.
        test_func: Function that performs the test.
        
    Returns:
        A test function.
    """
    @integration_test
    def integration_test_func(*args, **kwargs):
        return test_func(*args, components=components, **kwargs)
    return integration_test_func


# Example-based Test Utilities
def create_example_test_case(inputs: Dict[str, Any], expected_outputs: Dict[str, Any], 
                            test_func: Callable[[Dict[str, Any], Dict[str, Any]], None]):
    """Create a test case from examples.
    
    Args:
        inputs: Dictionary of test inputs.
        expected_outputs: Dictionary of expected outputs.
        test_func: Function that performs the test.
        
    Returns:
        A test function.
    """
    def example_test_func(*args, **kwargs):
        return test_func(*args, inputs=inputs, expected_outputs=expected_outputs, **kwargs)
    return example_test_func