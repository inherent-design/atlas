"""
Base test classes for Atlas tests.

This module provides base test classes with common functionality for different
types of tests, making it easier to write tests that follow standard patterns.
"""

import os
import unittest
import logging
from typing import Dict, Any, List, Optional, Type, Callable, TypeVar, Union, Tuple

# Import decorators
from atlas.tests.helpers.decorators import (
    unit_test, mock_test, api_test, integration_test, expensive_test,
    openai_test, anthropic_test, ollama_test
)

# Configure logging
logger = logging.getLogger(__name__)


class TestWithTokenTracking(unittest.TestCase):
    """Base class for tests with token usage tracking."""
    
    def setUp(self):
        """Set up token tracking."""
        super().setUp()
        self.total_tokens_used = 0
        self.estimated_cost = 0.0
        self.max_cost_limit = float(os.environ.get("MAX_TEST_COST", "0.1"))
    
    def track_usage(self, response):
        """Track token usage from a response.
        
        Args:
            response: A ModelResponse object with usage information.
        """
        if hasattr(response, "usage") and response.usage:
            self.total_tokens_used += response.usage.total_tokens
            if hasattr(response, "cost") and response.cost:
                self.estimated_cost += response.cost.total_cost
                
                # Check if we've exceeded the cost limit
                if self.estimated_cost > self.max_cost_limit:
                    logger.warning(f"Test {self._testMethodName} has exceeded the cost limit of ${self.max_cost_limit:.4f}")
                    if os.environ.get("ENFORCE_COST_LIMIT", "").lower() == "true":
                        self.fail(f"Cost limit exceeded: ${self.estimated_cost:.4f} > ${self.max_cost_limit:.4f}")
    
    def tearDown(self):
        """Report token usage at the end of the test."""
        super().tearDown()
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


class OpenAIProviderTestBase(ProviderTestBase):
    """Base class for OpenAI provider tests."""
    
    provider_name = "openai"
    default_model = "gpt-4o"
    cheap_model = "gpt-3.5-turbo"
    expensive_model = "gpt-4"
    
    def _check_api_key(self) -> bool:
        """Check if OpenAI API key is set."""
        return os.environ.get("OPENAI_API_KEY") is not None


class AnthropicProviderTestBase(ProviderTestBase):
    """Base class for Anthropic provider tests."""
    
    provider_name = "anthropic"
    default_model = "claude-3-opus-20240229"
    cheap_model = "claude-3-haiku-20240307"
    expensive_model = "claude-3-opus-20240229"
    
    def _check_api_key(self) -> bool:
        """Check if Anthropic API key is set."""
        return os.environ.get("ANTHROPIC_API_KEY") is not None


class OllamaProviderTestBase(ProviderTestBase):
    """Base class for Ollama provider tests."""
    
    provider_name = "ollama"
    default_model = "llama2"
    
    def _check_api_key(self) -> bool:
        """Check if Ollama is running."""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/version", timeout=1)
            return response.status_code == 200
        except (ImportError, requests.RequestException):
            return False
    
    def _get_available_models(self):
        """Get available Ollama models."""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                data = response.json()
                
                # Try both formats - newer Ollama API returns a "models" array with "name" field
                models = []
                if "models" in data and isinstance(data["models"], list):
                    models = [model["name"] for model in data["models"]]
                
                # Older Ollama versions and some installations return a different format
                # with a "models" dict where keys are model names
                elif "models" in data and isinstance(data["models"], dict):
                    models = list(data["models"].keys())
                
                # If we got models, return them
                if models:
                    return models
                    
                # As a fallback, run the CLI command and parse output
                import subprocess
                try:
                    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
                    if result.returncode == 0:
                        # Parse output like:
                        # NAME                       ID              SIZE      MODIFIED
                        # chatmusician:latest        f72f075bbc32    19 GB     2 weeks ago
                        lines = result.stdout.splitlines()[1:]  # Skip header
                        return [line.split()[0] for line in lines if line.strip()]
                except (subprocess.SubprocessError, FileNotFoundError):
                    pass
            
            # Fall back to a default empty list
            return []
        except (ImportError, requests.RequestException):
            return []
    
    def _create_provider(self):
        """Create an Ollama provider instance with an available model."""
        if not self.provider_class:
            raise ValueError("Provider class not set")
            
        # Try to find an available model
        available_models = self._get_available_models()
        
        if available_models:
            # Prefer llama2 or similar if available
            preferred_models = ["llama2", "mistral", "gemma", "phi", "neural-chat"]
            for model in preferred_models:
                for available in available_models:
                    if model in available.lower():
                        return self.provider_class(model_name=available)
            
            # Fall back to the first available model
            return self.provider_class(model_name=available_models[0])
        
        # Fall back to default
        return self.provider_class()


class AgentTestBase(TestWithTokenTracking):
    """Base class for agent tests."""
    
    agent_class = None  # The agent class to test
    
    def setUp(self):
        """Set up the test with an agent instance."""
        super().setUp()
        
        # Skip the whole test class if the agent_class is not set
        if not self.agent_class:
            self.skipTest("Agent class not set")
            
        # Create an agent instance
        self.agent = self._create_agent()
    
    def _create_agent(self):
        """Create an agent instance for testing.
        
        Override this in subclasses.
        
        Returns:
            An agent instance.
        """
        if not self.agent_class:
            raise ValueError("Agent class not set")
        return self.agent_class()
    
    @mock_test
    def test_agent_creation(self):
        """Test creating an agent instance."""
        self.assertIsNotNone(self.agent)


class ToolTestBase(unittest.TestCase):
    """Base class for tool tests."""
    
    tool_class = None  # The tool class to test
    
    def setUp(self):
        """Set up the test with a tool instance."""
        super().setUp()
        
        # Skip the whole test class if the tool_class is not set
        if not self.tool_class:
            self.skipTest("Tool class not set")
            
        # Create a tool instance
        self.tool = self._create_tool()
    
    def _create_tool(self):
        """Create a tool instance for testing.
        
        Override this in subclasses.
        
        Returns:
            A tool instance.
        """
        if not self.tool_class:
            raise ValueError("Tool class not set")
        return self.tool_class()
    
    @unit_test
    def test_tool_creation(self):
        """Test creating a tool instance."""
        self.assertIsNotNone(self.tool)


class IntegrationTestBase(TestWithTokenTracking):
    """Base class for integration tests."""
    
    def setUp(self):
        """Set up the integration test."""
        super().setUp()
        
        # Initialize components for integration testing
        self._setup_components()
    
    def _setup_components(self):
        """Set up components for integration testing.
        
        Override this in subclasses.
        """
        pass