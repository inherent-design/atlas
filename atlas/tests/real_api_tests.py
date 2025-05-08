"""
Real API tests for Atlas providers.

These tests make actual API calls to provider services and should only be run
when specifically enabled via environment variables.

Usage:
    # Run only mock tests (default)
    python -m atlas.scripts.testing.run_tests

    # Run including real API tests
    RUN_API_TESTS=true python -m atlas.scripts.testing.run_tests

    # Run full test suite including expensive tests
    RUN_API_TESTS=true RUN_EXPENSIVE_TESTS=true python -m atlas.scripts.testing.run_tests
"""

import os
import sys
import unittest
import logging
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import Atlas components
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

# Import provider implementations
from atlas.models.openai import OpenAIProvider
from atlas.models.ollama import OllamaProvider
from atlas.models.anthropic import AnthropicProvider

# Setup logging
logger = logging.getLogger(__name__)

# Test decorators
def api_test(f):
    """Decorator for tests that make real API calls."""
    def wrapper(*args, **kwargs):
        if not os.environ.get("RUN_API_TESTS"):
            return unittest.skip("API tests disabled - set RUN_API_TESTS=true to enable")(f)(*args, **kwargs)
        return f(*args, **kwargs)
    return wrapper

def expensive_test(f):
    """Decorator for tests that make expensive API calls."""
    def wrapper(*args, **kwargs):
        if not os.environ.get("RUN_EXPENSIVE_TESTS"):
            return unittest.skip("Expensive tests disabled - set RUN_EXPENSIVE_TESTS=true to enable")(f)(*args, **kwargs)
        return f(*args, **kwargs)
    return wrapper

# Base class for token tracking
class TestWithTokenTracking(unittest.TestCase):
    """Base class for tests with token usage tracking."""
    
    def setUp(self):
        self.total_tokens_used = 0
        self.estimated_cost = 0.0
        
        # Reset token counters for each test
        self.reset_token_counters()
    
    def reset_token_counters(self):
        """Reset token usage counters."""
        self.total_tokens_used = 0
        self.estimated_cost = 0.0
    
    def track_usage(self, response):
        """Track token usage from a response."""
        if hasattr(response, "usage") and response.usage:
            self.total_tokens_used += response.usage.total_tokens
            if hasattr(response, "cost") and response.cost:
                self.estimated_cost += response.cost.total_cost
    
    def tearDown(self):
        """Report token usage."""
        logger.info(f"Test {self._testMethodName} used {self.total_tokens_used} tokens at an estimated cost of ${self.estimated_cost:.6f}")


class TestOpenAIRealAPI(TestWithTokenTracking):
    """Tests that make real OpenAI API calls."""
    
    def setUp(self):
        """Set up the test."""
        super().setUp()
        # Skip the whole test class if OpenAI API key is not set
        if not os.environ.get("OPENAI_API_KEY"):
            self.skipTest("OPENAI_API_KEY not set")
    
    @api_test
    def test_basic_api_call(self):
        """Test a basic API call with a cost-effective model."""
        # Use a cheaper model
        provider = OpenAIProvider(model_name="gpt-3.5-turbo")
        
        # Create a simple request
        request = ModelRequest(
            messages=[ModelMessage.user("Write a single word response: Hello")],
            max_tokens=5
        )
        
        # Generate a response
        response = provider.generate(request)
        
        # Track token usage
        self.track_usage(response)
        
        # Basic assertions
        self.assertIsNotNone(response.content)
        self.assertEqual(response.provider, "openai")
        self.assertIsNotNone(response.model)
        self.assertIsNotNone(response.usage)
        
        # Token usage should be reasonable for this request
        self.assertLessEqual(response.usage.total_tokens, 30)
    
    @api_test
    def test_streaming_api_call(self):
        """Test streaming API call with a cost-effective model."""
        # Use a cheaper model
        provider = OpenAIProvider(model_name="gpt-3.5-turbo")
        
        # Create a simple request
        request = ModelRequest(
            messages=[ModelMessage.user("Write a single word response: Hello")],
            max_tokens=5
        )
        
        # Collect streaming chunks
        collected_chunks = []
        
        def stream_callback(delta, response):
            collected_chunks.append(delta)
        
        # Stream with callback
        response = provider.stream_with_callback(request, stream_callback)
        
        # Track token usage
        self.track_usage(response)
        
        # Basic assertions
        self.assertIsNotNone(response.content)
        self.assertEqual(response.provider, "openai")
        self.assertGreater(len(collected_chunks), 0)
        self.assertLessEqual(response.usage.total_tokens, 30)
    
    @expensive_test
    def test_gpt4_api_call(self):
        """Test API call with GPT-4 (more expensive model)."""
        # Use GPT-4 model
        provider = OpenAIProvider(model_name="gpt-4")
        
        # Create a simple request
        request = ModelRequest(
            messages=[ModelMessage.user("Write a single word response: Hello")],
            max_tokens=5
        )
        
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


class TestOllamaRealAPI(TestWithTokenTracking):
    """Tests that make real Ollama API calls."""
    
    def setUp(self):
        """Set up the test."""
        super().setUp()
        # Check if Ollama is running
        self._ollama_available = self._is_ollama_running()
        if not self._ollama_available:
            self.skipTest("Ollama not running - start Ollama server to enable tests")
    
    def _is_ollama_running(self):
        """Check if Ollama is running."""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/version", timeout=2)
            return response.status_code == 200
        except Exception:
            return False
    
    def _get_available_model(self):
        """Get an available Ollama model by checking what's installed."""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get("models", [])
                if models:
                    # Return the first available model
                    return models[0]["name"]
            # Fallback to common models
            return "llama2"  # More commonly available than llama3
        except Exception:
            return "llama2"  # Fallback

    @api_test
    def test_basic_api_call(self):
        """Test a basic API call to Ollama."""
        # Get an available model
        model_name = self._get_available_model()
        
        # Create a provider
        provider = OllamaProvider(model_name=model_name)
        
        # Create a simple request
        request = ModelRequest(
            messages=[ModelMessage.user("Write a single word response: Hello")],
            max_tokens=5
        )
        
        # Generate a response
        response = provider.generate(request)
        
        # Track token usage
        self.track_usage(response)
        
        # Basic assertions
        self.assertIsNotNone(response.content)
        self.assertEqual(response.provider, "ollama")
        self.assertIsNotNone(response.model)
        self.assertIsNotNone(response.usage)
    
    @api_test
    def test_streaming_api_call(self):
        """Test streaming API call to Ollama."""
        # Get an available model
        model_name = self._get_available_model()
        
        # Create a provider
        provider = OllamaProvider(model_name=model_name)
        
        # Create a simple request
        request = ModelRequest(
            messages=[ModelMessage.user("Write a single word response: Hello")],
            max_tokens=5
        )
        
        # Collect streaming chunks
        collected_chunks = []
        
        def stream_callback(delta, response):
            collected_chunks.append(delta)
        
        # Stream with callback
        response = provider.stream_with_callback(request, stream_callback)
        
        # Track token usage
        self.track_usage(response)
        
        # Basic assertions
        self.assertIsNotNone(response.content)
        self.assertEqual(response.provider, "ollama")
        self.assertGreater(len(collected_chunks), 0)


class TestAnthropicRealAPI(TestWithTokenTracking):
    """Tests that make real Anthropic API calls."""
    
    def setUp(self):
        """Set up the test."""
        super().setUp()
        # Skip the whole test class if Anthropic API key is not set
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self.skipTest("ANTHROPIC_API_KEY not set")
    
    @api_test
    def test_basic_api_call(self):
        """Test a basic API call with a cost-effective model."""
        # Use Haiku model (cheaper)
        provider = AnthropicProvider(model_name="claude-3-haiku-20240307")
        
        # Create a simple request
        request = ModelRequest(
            messages=[ModelMessage.user("Write a single word response: Hello")],
            max_tokens=5
        )
        
        # Generate a response
        response = provider.generate(request)
        
        # Track token usage
        self.track_usage(response)
        
        # Basic assertions
        self.assertIsNotNone(response.content)
        self.assertEqual(response.provider, "anthropic")
        self.assertIsNotNone(response.model)
        self.assertIsNotNone(response.usage)
        
        # Token usage should be reasonable for this request
        self.assertLessEqual(response.usage.total_tokens, 30)
    
    @api_test
    def test_streaming_api_call(self):
        """Test streaming API call with a cost-effective model."""
        # Use Haiku model (cheaper)
        provider = AnthropicProvider(model_name="claude-3-haiku-20240307")
        
        # Create a simple request
        request = ModelRequest(
            messages=[ModelMessage.user("Write a single word response: Hello")],
            max_tokens=5
        )
        
        # Collect streaming chunks
        collected_chunks = []
        
        def stream_callback(delta, response):
            collected_chunks.append(delta)
        
        # Stream with callback
        response = provider.stream_with_callback(request, stream_callback)
        
        # Track token usage
        self.track_usage(response)
        
        # Basic assertions
        self.assertIsNotNone(response.content)
        self.assertEqual(response.provider, "anthropic")
        self.assertGreater(len(collected_chunks), 0)
        self.assertLessEqual(response.usage.total_tokens, 30)
    
    @expensive_test
    def test_opus_api_call(self):
        """Test API call with Claude Opus (more expensive model)."""
        # Use Opus model (more expensive)
        provider = AnthropicProvider(model_name="claude-3-opus-20240229")
        
        # Create a simple request
        request = ModelRequest(
            messages=[ModelMessage.user("Write a single word response: Hello")],
            max_tokens=5
        )
        
        # Generate a response
        response = provider.generate(request)
        
        # Track token usage
        self.track_usage(response)
        
        # Basic assertions
        self.assertIsNotNone(response.content)
        self.assertEqual(response.provider, "anthropic")
        self.assertIsNotNone(response.model)
        
        # Token usage should be reasonable
        self.assertLessEqual(response.usage.total_tokens, 30)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    unittest.main()