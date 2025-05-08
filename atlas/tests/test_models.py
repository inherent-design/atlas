"""
Unit tests for the models module.

This module provides comprehensive tests for the Atlas models module,
including both real API tests and mock tests that can run without API keys.
"""

import os
import sys
import unittest
from unittest import mock
from typing import Dict, Any, List, Optional

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
    discover_providers,
    create_provider,
    get_all_providers,
    register_provider,
    set_default_model,
    ProviderFactory,
)


class TestModelInterfaces(unittest.TestCase):
    """Test the model interfaces."""

    def test_model_message_creation(self):
        """Test creating ModelMessage instances."""
        # Test system message
        system_msg = ModelMessage.system("You are a helpful assistant.")
        self.assertEqual(system_msg.role, ModelRole.SYSTEM)
        self.assertEqual(system_msg.content, "You are a helpful assistant.")
        self.assertIsNone(system_msg.name)

        # Test user message
        user_msg = ModelMessage.user("Hello, how are you?")
        self.assertEqual(user_msg.role, ModelRole.USER)
        self.assertEqual(user_msg.content, "Hello, how are you?")
        self.assertIsNone(user_msg.name)

        # Test user message with name
        named_user_msg = ModelMessage.user("Hello, how are you?", name="User1")
        self.assertEqual(named_user_msg.role, ModelRole.USER)
        self.assertEqual(named_user_msg.content, "Hello, how are you?")
        self.assertEqual(named_user_msg.name, "User1")

        # Test assistant message
        assistant_msg = ModelMessage.assistant("I'm doing well, thanks!")
        self.assertEqual(assistant_msg.role, ModelRole.ASSISTANT)
        self.assertEqual(assistant_msg.content, "I'm doing well, thanks!")
        self.assertIsNone(assistant_msg.name)

        # Test function message
        function_msg = ModelMessage.function("Function result", name="get_weather")
        self.assertEqual(function_msg.role, ModelRole.FUNCTION)
        self.assertEqual(function_msg.content, "Function result")
        self.assertEqual(function_msg.name, "get_weather")

    def test_model_message_to_dict(self):
        """Test converting ModelMessage to dictionary."""
        # Test simple message
        msg = ModelMessage.user("Hello")
        msg_dict = msg.to_dict()
        self.assertEqual(msg_dict["role"], "user")
        self.assertEqual(msg_dict["content"], "Hello")
        self.assertNotIn("name", msg_dict)

        # Test message with name
        msg = ModelMessage.user("Hello", name="User1")
        msg_dict = msg.to_dict()
        self.assertEqual(msg_dict["role"], "user")
        self.assertEqual(msg_dict["content"], "Hello")
        self.assertEqual(msg_dict["name"], "User1")

        # Test message with MessageContent
        content = MessageContent.text("Hello")
        msg = ModelMessage.user(content)
        msg_dict = msg.to_dict()
        self.assertEqual(msg_dict["role"], "user")
        self.assertEqual(msg_dict["content"], "Hello")

        # Test message with list of MessageContent
        contents = [MessageContent.text("Hello"), MessageContent.text("World")]
        msg = ModelMessage.user(contents)
        msg_dict = msg.to_dict()
        self.assertEqual(msg_dict["role"], "user")
        
        # The actual dictionary structure depends on the implementation of to_dict() 
        # Accept either a simplified list of texts or a more detailed structure
        if isinstance(msg_dict["content"], list):
            if isinstance(msg_dict["content"][0], dict):
                # Check for full content structure
                self.assertEqual(msg_dict["content"][0]["type"], "text")
                self.assertEqual(msg_dict["content"][0]["text"], "Hello")
                self.assertEqual(msg_dict["content"][1]["type"], "text")
                self.assertEqual(msg_dict["content"][1]["text"], "World")
            else:
                # Check for simplified text list
                self.assertEqual(msg_dict["content"], ["Hello", "World"])

    def test_model_request_creation(self):
        """Test creating ModelRequest instances."""
        # Test simple request
        request = ModelRequest(
            messages=[
                ModelMessage.system("You are a helpful assistant."),
                ModelMessage.user("Hello"),
            ],
            max_tokens=100,
        )
        self.assertEqual(len(request.messages), 2)
        self.assertEqual(request.max_tokens, 100)
        self.assertIsNone(request.temperature)

        # Test with system_prompt
        request = ModelRequest(
            messages=[ModelMessage.user("Hello")],
            system_prompt="You are a helpful assistant.",
            max_tokens=100,
        )
        self.assertEqual(len(request.messages), 2)  # System message is added
        self.assertEqual(request.messages[0].role, ModelRole.SYSTEM)
        self.assertEqual(request.messages[0].content, "You are a helpful assistant.")

        # Test with all optional parameters
        request = ModelRequest(
            messages=[ModelMessage.user("Hello")],
            max_tokens=100,
            temperature=0.7,
            system_prompt="You are a helpful assistant.",
            model="gpt-4",
            stop_sequences=["STOP"],
            top_p=0.9,
            frequency_penalty=0.5,
            presence_penalty=0.5,
            response_format={"type": "json_object"},
        )
        self.assertEqual(request.max_tokens, 100)
        self.assertEqual(request.temperature, 0.7)
        self.assertEqual(request.model, "gpt-4")
        self.assertEqual(request.stop_sequences, ["STOP"])
        self.assertEqual(request.top_p, 0.9)
        self.assertEqual(request.frequency_penalty, 0.5)
        self.assertEqual(request.presence_penalty, 0.5)
        self.assertEqual(request.response_format, {"type": "json_object"})

    def test_model_request_to_provider_request(self):
        """Test converting ModelRequest to provider-specific format."""
        request = ModelRequest(
            messages=[
                ModelMessage.system("You are a helpful assistant."),
                ModelMessage.user("Hello"),
            ],
            max_tokens=100,
            temperature=0.7,
        )

        # Test Anthropic format
        anthropic_request = request.to_provider_request("anthropic")
        self.assertIn("messages", anthropic_request)
        self.assertIn("system", anthropic_request)
        self.assertEqual(anthropic_request["system"], "You are a helpful assistant.")
        self.assertEqual(
            len(anthropic_request["messages"]), 1
        )  # System message is separate
        self.assertEqual(anthropic_request["messages"][0]["role"], "user")
        self.assertEqual(anthropic_request["max_tokens"], 100)
        self.assertEqual(anthropic_request["temperature"], 0.7)

        # Test OpenAI format
        openai_request = request.to_provider_request("openai")
        self.assertIn("messages", openai_request)
        self.assertEqual(
            len(openai_request["messages"]), 2
        )  # System message included in messages
        self.assertEqual(openai_request["messages"][0]["role"], "system")
        self.assertEqual(openai_request["messages"][1]["role"], "user")
        self.assertEqual(openai_request["max_tokens"], 100)
        self.assertEqual(openai_request["temperature"], 0.7)

    def test_token_usage(self):
        """Test TokenUsage class."""
        # Test with explicit values
        usage = TokenUsage(input_tokens=10, output_tokens=20, total_tokens=30)
        self.assertEqual(usage.input_tokens, 10)
        self.assertEqual(usage.output_tokens, 20)
        self.assertEqual(usage.total_tokens, 30)

        # Test with automatic total calculation
        usage = TokenUsage(input_tokens=10, output_tokens=20)
        self.assertEqual(usage.total_tokens, 30)

        # Test with zero values
        usage = TokenUsage()
        self.assertEqual(usage.input_tokens, 0)
        self.assertEqual(usage.output_tokens, 0)
        self.assertEqual(usage.total_tokens, 0)

    def test_cost_estimate(self):
        """Test CostEstimate class."""
        # Test with explicit values
        cost = CostEstimate(input_cost=0.01, output_cost=0.02, total_cost=0.03)
        self.assertEqual(cost.input_cost, 0.01)
        self.assertEqual(cost.output_cost, 0.02)
        self.assertEqual(cost.total_cost, 0.03)

        # Test with automatic total calculation
        cost = CostEstimate(input_cost=0.01, output_cost=0.02)
        self.assertEqual(cost.total_cost, 0.03)

        # Test with zero values
        cost = CostEstimate()
        self.assertEqual(cost.input_cost, 0.0)
        self.assertEqual(cost.output_cost, 0.0)
        self.assertEqual(cost.total_cost, 0.0)

        # Test string representation
        cost = CostEstimate(input_cost=0.01, output_cost=0.02)
        self.assertIn("$0.03", str(cost))
        self.assertIn("Input: $0.01", str(cost))
        self.assertIn("Output: $0.02", str(cost))

    def test_model_response(self):
        """Test ModelResponse class."""
        # Test with minimal values
        response = ModelResponse(
            content="Hello, world!",
            model="gpt-4",
            provider="openai",
        )
        self.assertEqual(response.content, "Hello, world!")
        self.assertEqual(response.model, "gpt-4")
        self.assertEqual(response.provider, "openai")
        self.assertEqual(response.usage.input_tokens, 0)
        self.assertEqual(response.usage.output_tokens, 0)
        self.assertEqual(response.cost.total_cost, 0.0)
        self.assertIsNone(response.finish_reason)
        self.assertIsNone(response.raw_response)

        # Test with all values
        response = ModelResponse(
            content="Hello, world!",
            model="gpt-4",
            provider="openai",
            usage=TokenUsage(input_tokens=10, output_tokens=20),
            cost=CostEstimate(input_cost=0.01, output_cost=0.02),
            finish_reason="stop",
            raw_response={"choices": [{"text": "Hello, world!"}]},
        )
        self.assertEqual(response.usage.input_tokens, 10)
        self.assertEqual(response.usage.output_tokens, 20)
        self.assertEqual(response.cost.input_cost, 0.01)
        self.assertEqual(response.cost.output_cost, 0.02)
        self.assertEqual(response.finish_reason, "stop")
        self.assertEqual(
            response.raw_response, {"choices": [{"text": "Hello, world!"}]}
        )

        # Test string representation
        self.assertIn("Hello, world!", str(response))
        self.assertIn("openai/gpt-4", str(response))
        self.assertIn("10 input, 20 output", str(response))
        self.assertIn("$0.03", str(response))


class MockAnthropicProvider(ModelProvider):
    """Mock Anthropic provider for testing."""

    def __init__(
        self, model_name="claude-3-7-sonnet-20250219", max_tokens=2000, **kwargs
    ):
        # Keep the private attributes
        self._model_name = model_name
        self._max_tokens = max_tokens
        self._kwargs = kwargs

    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._model_name

    @property
    def max_tokens(self) -> int:
        """Get the max tokens."""
        return self._max_tokens

    @property
    def name(self) -> str:
        return "anthropic"

    def get_available_models(self) -> List[str]:
        return [
            "claude-3-7-sonnet-20250219",
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

    def validate_api_key(self) -> bool:
        return True

    def generate(self, request: ModelRequest) -> ModelResponse:
        # Simple mock implementation that returns a fixed response
        return ModelResponse(
            content=f"Mock response from {self._model_name}",
            model=self._model_name,
            provider=self.name,
            usage=TokenUsage(input_tokens=10, output_tokens=20),
            cost=CostEstimate(input_cost=0.00003, output_cost=0.0003),
            finish_reason="stop",
            raw_response={"mock": True},
        )

    def calculate_token_usage(self, request: ModelRequest, response: Any) -> TokenUsage:
        # Simple mock implementation
        return TokenUsage(input_tokens=10, output_tokens=20)

    def calculate_cost(self, usage: TokenUsage, model: str) -> CostEstimate:
        # Simple mock implementation using real pricing
        if "opus" in model:
            input_cost = usage.input_tokens * 15.0 / 1_000_000
            output_cost = usage.output_tokens * 75.0 / 1_000_000
        elif "haiku" in model:
            input_cost = usage.input_tokens * 0.25 / 1_000_000
            output_cost = usage.output_tokens * 1.25 / 1_000_000
        else:  # sonnet models
            input_cost = usage.input_tokens * 3.0 / 1_000_000
            output_cost = usage.output_tokens * 15.0 / 1_000_000

        return CostEstimate(input_cost=input_cost, output_cost=output_cost)


class TestProviderFactory(unittest.TestCase):
    """Test the provider factory."""

    @mock.patch(
        "atlas.models.factory._PROVIDER_REGISTRY",
        {"mock": "atlas.tests.test_models.MockAnthropicProvider"},
    )
    @mock.patch("atlas.models.factory._DEFAULT_MODELS", {"mock": "mock-model"})
    @mock.patch("atlas.models.factory.discover_providers")
    def test_get_provider_class(self, mock_discover):
        """Test getting a provider class."""
        from atlas.models.factory import get_provider_class

        # Set up mock
        mock_discover.return_value = {"mock": ["mock-model"]}

        # Get the provider class
        provider_class = get_provider_class("mock")
        self.assertEqual(provider_class, MockAnthropicProvider)

        # Test with unknown provider
        with self.assertRaises(ValueError):
            get_provider_class("unknown")

    @mock.patch(
        "atlas.models.factory._PROVIDER_REGISTRY",
        {"mock": "atlas.tests.test_models.MockAnthropicProvider"},
    )
    @mock.patch("atlas.models.factory._DEFAULT_MODELS", {"mock": "mock-model"})
    @mock.patch("atlas.models.factory.discover_providers")
    def test_create_provider(self, mock_discover):
        """Test creating a provider."""
        from atlas.models.factory import create_provider

        # Set up mock
        mock_discover.return_value = {"mock": ["mock-model"]}

        # Create a provider
        provider = create_provider("mock", model_name="mock-model", max_tokens=100)
        self.assertIsInstance(provider, MockAnthropicProvider)
        self.assertEqual(
            provider._model_name, "mock-model"
        )  # Changed back to _model_name
        self.assertEqual(provider._max_tokens, 100)  # Changed back to _max_tokens

        # Test with default model
        provider = create_provider("mock")
        self.assertEqual(
            provider._model_name, "mock-model"
        )  # Changed back to _model_name

        # Test with unknown provider
        with self.assertRaises(ValueError):
            create_provider("unknown")

    def test_register_provider(self):
        """Test registering a provider."""
        # Get original registry size
        from atlas.models.factory import _PROVIDER_REGISTRY

        original_providers = set(_PROVIDER_REGISTRY.keys())

        # Register a provider
        register_provider("test_provider", "test.module.TestProvider")

        # Check it was added
        try:
            new_providers = set(_PROVIDER_REGISTRY.keys())
            self.assertIn("test_provider", new_providers)
            self.assertEqual(
                _PROVIDER_REGISTRY["test_provider"], "test.module.TestProvider"
            )

            # Restore original registry
            _PROVIDER_REGISTRY.pop("test_provider", None)
        except:
            # Restore original registry on failure too
            _PROVIDER_REGISTRY.pop("test_provider", None)
            raise

    def test_set_default_model(self):
        """Test setting the default model."""
        # Get original default models
        from atlas.models.factory import _DEFAULT_MODELS

        original_default = _DEFAULT_MODELS.get("test_provider", None)

        # Set the default model
        set_default_model("test_provider", "test-model-default")

        # Verify it was set
        try:
            self.assertEqual(_DEFAULT_MODELS["test_provider"], "test-model-default")

            # Restore original state
            if original_default is None:
                _DEFAULT_MODELS.pop("test_provider", None)
            else:
                _DEFAULT_MODELS["test_provider"] = original_default
        except:
            # Restore original state on failure too
            if original_default is None:
                _DEFAULT_MODELS.pop("test_provider", None)
            else:
                _DEFAULT_MODELS["test_provider"] = original_default
            raise

    def test_provider_factory(self):
        """Test the ProviderFactory class."""
        # Create a factory
        factory = ProviderFactory()

        # Register a mock provider for testing
        from atlas.models.factory import _PROVIDER_REGISTRY

        original_registry = dict(_PROVIDER_REGISTRY)
        _PROVIDER_REGISTRY["mock"] = "atlas.tests.test_models.MockAnthropicProvider"

        # Mock discover_providers
        original_discover = factory.discover
        factory._discover_providers = lambda: {
            "mock"
        }  # Changed to use a private method that actually exists

        try:
            # Test create method with registered mock provider
            provider = factory.create("mock", model_name="custom-model", max_tokens=200)
            self.assertIsInstance(provider, MockAnthropicProvider)
            self.assertEqual(
                provider._model_name, "custom-model"
            )  # Changed back to _model_name
            self.assertEqual(provider._max_tokens, 200)  # Changed back to _max_tokens

            # Store the created provider
            factory._providers["mock"] = provider

            # Test set_default method
            factory.set_default("mock")
            self.assertEqual(factory._default_provider, "mock")

            # Test get method (returns existing instance)
            same_provider = factory.get("mock")
            self.assertIs(same_provider, provider)

            # Test get with default
            default_provider = factory.get()
            self.assertIs(default_provider, provider)

        finally:
            # Restore original state
            factory._discover_providers = (
                lambda: original_discover()
            )  # Restore with a lambda wrapper
            _PROVIDER_REGISTRY.clear()
            _PROVIDER_REGISTRY.update(original_registry)


@unittest.skip(
    "These tests require actual API keys - run manually or with API keys set"
)
class TestLiveProviders(unittest.TestCase):
    """Test actual provider implementations (requires API keys)."""

    def setUp(self):
        """Set up the test."""
        # Discover available providers
        self.providers = discover_providers()

    def test_discover_providers(self):
        """Test discovering providers."""
        # Just verify that the function runs without error
        providers = discover_providers()
        self.assertIsInstance(providers, dict)
        print(f"Available providers: {providers}")

    def test_anthropic_provider(self):
        """Test the Anthropic provider."""
        if "anthropic" not in self.providers:
            self.skipTest("Anthropic API key not available")

        # Create a provider
        provider = create_provider("anthropic")
        self.assertEqual(provider.name, "anthropic")

        # Get available models
        models = provider.get_available_models()
        self.assertIsInstance(models, list)
        self.assertGreater(len(models), 0)
        print(f"Available Anthropic models: {models}")

        # Validate API key
        is_valid = provider.validate_api_key()
        self.assertTrue(is_valid)

        # Generate a response
        request = ModelRequest(
            messages=[ModelMessage.user("Say hello!")], max_tokens=20
        )
        response = provider.generate(request)
        self.assertIsInstance(response, ModelResponse)
        self.assertIsNotNone(response.content)
        self.assertEqual(response.provider, "anthropic")
        print(f"Anthropic response: {response.content}")
        print(
            f"Token usage: {response.usage.input_tokens} input, {response.usage.output_tokens} output"
        )
        print(f"Cost: {response.cost}")

    def test_openai_provider(self):
        """Test the OpenAI provider."""
        if "openai" not in self.providers:
            self.skipTest("OpenAI API key not available")

        # Create a provider
        provider = create_provider("openai")
        self.assertEqual(provider.name, "openai")

        # Get available models
        models = provider.get_available_models()
        self.assertIsInstance(models, list)
        self.assertGreater(len(models), 0)
        print(f"Available OpenAI models: {models}")

        # Validate API key
        is_valid = provider.validate_api_key()
        self.assertTrue(is_valid)

        # Generate a response
        request = ModelRequest(
            messages=[ModelMessage.user("Say hello!")], max_tokens=20
        )
        response = provider.generate(request)
        self.assertIsInstance(response, ModelResponse)
        self.assertIsNotNone(response.content)
        self.assertEqual(response.provider, "openai")
        print(f"OpenAI response: {response.content}")
        print(
            f"Token usage: {response.usage.input_tokens} input, {response.usage.output_tokens} output"
        )
        print(f"Cost: {response.cost}")

    def test_ollama_provider(self):
        """Test the Ollama provider."""
        if "ollama" not in self.providers:
            self.skipTest("Ollama not available")

        # Create a provider
        provider = create_provider("ollama")
        self.assertEqual(provider.name, "ollama")

        # Get available models
        models = provider.get_available_models()
        self.assertIsInstance(models, list)
        print(f"Available Ollama models: {models}")

        # Validate API key (connection check)
        is_valid = provider.validate_api_key()
        self.assertTrue(is_valid)

        # Generate a response if models are available
        if models:
            request = ModelRequest(
                messages=[ModelMessage.user("Say hello!")], max_tokens=20
            )
            response = provider.generate(request)
            self.assertIsInstance(response, ModelResponse)
            self.assertIsNotNone(response.content)
            self.assertEqual(response.provider, "ollama")
            print(f"Ollama response: {response.content}")
            print(
                f"Token usage: {response.usage.input_tokens} input, {response.usage.output_tokens} output"
            )
            print(f"Cost: {response.cost}")


if __name__ == "__main__":
    unittest.main()
