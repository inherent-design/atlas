"""
Test OpenAI provider implementation.

This module tests the functionality of the OpenAI provider, including
streaming capabilities and error handling.
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
)

# Import OpenAI provider directly for mock patching
from atlas.models.openai import OpenAIProvider, StreamHandler

# Set environment variable for tests
os.environ["SKIP_API_KEY_CHECK"] = "true"


class TestOpenAIProvider(unittest.TestCase):
    """Test the OpenAIProvider class."""

    def setUp(self):
        """Set up the test."""
        # Create a provider for testing
        self.provider = OpenAIProvider(api_key="test-key")

    def tearDown(self):
        """Clean up after the test."""
        pass

    def test_provider_creation(self):
        """Test creating an OpenAI provider."""
        # Create a provider with default settings
        provider = OpenAIProvider(api_key="test-key")

        # Check provider name
        self.assertEqual(provider.name, "openai")

        # Check default model
        self.assertEqual(provider._model_name, "gpt-4o")

        # Create with custom parameters
        custom_provider = OpenAIProvider(
            model_name="gpt-3.5-turbo",
            max_tokens=1000,
            api_key="test-key",
            organization="test-org",
            temperature=0.7,
        )

        self.assertEqual(custom_provider._model_name, "gpt-3.5-turbo")
        self.assertEqual(custom_provider._max_tokens, 1000)
        self.assertEqual(custom_provider._api_key, "test-key")
        self.assertEqual(custom_provider._organization, "test-org")
        self.assertEqual(custom_provider._additional_params["temperature"], 0.7)

    @mock.patch("openai.OpenAI")
    def test_generate(self, mock_openai_class):
        """Test generating a response."""
        # Create mock OpenAI client
        mock_client = mock.MagicMock()
        mock_completion = mock.MagicMock()
        mock_choice = mock.MagicMock()
        mock_message = mock.MagicMock()
        mock_usage = mock.MagicMock()

        # Set up the mock response chain
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_completion
        mock_completion.choices = [mock_choice]
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        mock_message.content = "This is a test response from OpenAI."
        mock_completion.usage.prompt_tokens = 10
        mock_completion.usage.completion_tokens = 15
        mock_completion.usage.total_tokens = 25
        mock_completion.model_dump.return_value = {"mock": "response"}

        # Create a simple request
        request = ModelRequest(
            messages=[ModelMessage.user("Test message")],
            max_tokens=100
        )

        # Generate a response
        response = self.provider.generate(request)

        # Check that the mock was called correctly
        mock_client.chat.completions.create.assert_called_once()
        args, kwargs = mock_client.chat.completions.create.call_args
        self.assertEqual(kwargs["model"], "gpt-4o")
        self.assertEqual(kwargs["max_tokens"], 100)
        self.assertEqual(len(kwargs["messages"]), 1)
        self.assertEqual(kwargs["messages"][0]["role"], "user")
        self.assertEqual(kwargs["messages"][0]["content"], "Test message")

        # Check that the response has the expected structure
        self.assertIsInstance(response, ModelResponse)
        self.assertEqual(response.content, "This is a test response from OpenAI.")
        self.assertEqual(response.provider, "openai")
        self.assertEqual(response.model, "gpt-4o")
        self.assertEqual(response.finish_reason, "stop")
        
        # Check token usage
        self.assertIsInstance(response.usage, TokenUsage)
        self.assertEqual(response.usage.input_tokens, 10)
        self.assertEqual(response.usage.output_tokens, 15)
        self.assertEqual(response.usage.total_tokens, 25)
        
        # Check cost
        self.assertIsInstance(response.cost, CostEstimate)
        
        # Check raw response
        self.assertEqual(response.raw_response, {"mock": "response"})

    @mock.patch("openai.OpenAI")
    def test_streaming(self, mock_openai_class):
        """Test streaming a response."""
        # Create mock OpenAI client
        mock_client = mock.MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Create a mock stream - This is a bit complex as we need to mock an iterator
        # Define a mock chunk class to simulate OpenAI's streaming response chunks
        class MockChunk:
            """Mock chunk for streaming response."""
            
            def __init__(self, content=None, finish_reason=None, usage=None):
                """Initialize with optional content and finish_reason."""
                self.choices = [
                    mock.MagicMock(
                        delta=mock.MagicMock(content=content),
                        finish_reason=finish_reason
                    )
                ]
                self.usage = usage
        
        # Generate several chunks to simulate streaming
        chunks = [
            MockChunk(content="This "),
            MockChunk(content="is "),
            MockChunk(content="a "),
            MockChunk(content="test "),
            MockChunk(content="streaming "),
            MockChunk(content="response "),
            MockChunk(content="from "),
            MockChunk(content="OpenAI."),
            MockChunk(
                finish_reason="stop", 
                usage=mock.MagicMock(
                    prompt_tokens=10,
                    completion_tokens=15,
                    total_tokens=25
                )
            )
        ]
        
        # Mock the stream as an iterator
        mock_stream = mock.MagicMock()
        mock_stream.__iter__.return_value = iter(chunks)
        mock_client.chat.completions.create.return_value = mock_stream
        
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
        self.assertEqual(initial_response.provider, "openai")
        self.assertEqual(initial_response.model, "gpt-4o")
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
        mock_client.chat.completions.create.assert_called_once()
        args, kwargs = mock_client.chat.completions.create.call_args
        self.assertTrue(kwargs["stream"])
        
        # Check that we received the expected number of text chunks
        self.assertEqual(len(chunks_received), 8)  # 8 content chunks, 1 finish chunk
        
        # Check the collected full text
        self.assertEqual(full_text, "This is a test streaming response from OpenAI.")
        
    @mock.patch("openai.OpenAI")
    def test_stream_with_callback(self, mock_openai_class):
        """Test streaming with a callback function."""
        # Create mock OpenAI client same as in test_streaming
        mock_client = mock.MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Define the mock chunk class
        class MockChunk:
            def __init__(self, content=None, finish_reason=None, usage=None):
                self.choices = [
                    mock.MagicMock(
                        delta=mock.MagicMock(content=content),
                        finish_reason=finish_reason
                    )
                ]
                self.usage = usage
        
        # Generate chunks
        chunks = [
            MockChunk(content="This "),
            MockChunk(content="is "),
            MockChunk(content="a "),
            MockChunk(content="callback "),
            MockChunk(content="test."),
            MockChunk(
                finish_reason="stop", 
                usage=mock.MagicMock(
                    prompt_tokens=8,
                    completion_tokens=10,
                    total_tokens=18
                )
            )
        ]
        
        # Mock the stream
        mock_stream = mock.MagicMock()
        mock_stream.__iter__.return_value = iter(chunks)
        mock_client.chat.completions.create.return_value = mock_stream
        
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
        self.assertEqual(final_response.provider, "openai")
        self.assertEqual(final_response.model, "gpt-4o")
        self.assertEqual(final_response.finish_reason, "stop")
        
        # Check token usage in final response
        self.assertEqual(final_response.usage.input_tokens, 8)
        self.assertEqual(final_response.usage.output_tokens, 10)
        self.assertEqual(final_response.usage.total_tokens, 18)
        
        # Check cost calculation
        self.assertIsInstance(final_response.cost, CostEstimate)

    @mock.patch("openai.OpenAI")
    def test_error_handling(self, mock_openai_class):
        """Test error handling during API calls."""
        # Create OpenAI API errors for testing
        import openai
        
        # Create mock client that raises errors
        mock_client = mock.MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Create a simple request
        request = ModelRequest(
            messages=[ModelMessage.user("Test message")],
            max_tokens=100
        )
        
        # Test authentication error
        mock_client.chat.completions.create.side_effect = openai.AuthenticationError("Invalid API key")
        
        with self.assertRaises(Exception) as context:
            self.provider.generate(request)
        
        # Check that the error was properly converted to our error type
        self.assertIn("authentication", str(context.exception).lower())
        self.assertIn("openai", str(context.exception).lower())
        
        # Test rate limit error
        mock_client.chat.completions.create.side_effect = openai.RateLimitError("Rate limit exceeded")
        
        with self.assertRaises(Exception) as context:
            self.provider.generate(request)
        
        # Check that the error was properly converted to our error type
        self.assertIn("rate limit", str(context.exception).lower())
        self.assertIn("openai", str(context.exception).lower())
        
        # Test API status error
        mock_client.chat.completions.create.side_effect = openai.APIStatusError(
            message="Internal server error",
            response=mock.MagicMock(status_code=500),
            body=None
        )
        
        with self.assertRaises(Exception) as context:
            self.provider.generate(request)
        
        # Check that the error was properly converted to our error type
        self.assertIn("api error", str(context.exception).lower())
        self.assertIn("openai", str(context.exception).lower())
        
    def test_token_usage_calculation(self):
        """Test token usage calculation."""
        # Create a response object with token usage
        class MockResponse:
            def __init__(self):
                self.usage = mock.MagicMock(
                    prompt_tokens=15,
                    completion_tokens=25,
                    total_tokens=40
                )
        
        # Create a request
        request = ModelRequest(
            messages=[ModelMessage.user("Test message")],
            max_tokens=100
        )
        
        # Calculate token usage
        usage = self.provider.calculate_token_usage(request, MockResponse())
        
        # Check the calculated usage
        self.assertEqual(usage.input_tokens, 15)
        self.assertEqual(usage.output_tokens, 25)
        self.assertEqual(usage.total_tokens, 40)
        
    def test_cost_calculation(self):
        """Test cost calculation for different models."""
        # Create a token usage
        usage = TokenUsage(input_tokens=1000, output_tokens=500)
        
        # Calculate cost for different models
        cost_4o = self.provider.calculate_cost(usage, "gpt-4o")
        cost_4_turbo = self.provider.calculate_cost(usage, "gpt-4-turbo")
        cost_4 = self.provider.calculate_cost(usage, "gpt-4")
        cost_3_5 = self.provider.calculate_cost(usage, "gpt-3.5-turbo")
        
        # Check the calculated costs
        self.assertEqual(cost_4o.input_cost, (1000 / 1_000_000) * 5.0)
        self.assertEqual(cost_4o.output_cost, (500 / 1_000_000) * 15.0)
        
        self.assertEqual(cost_4_turbo.input_cost, (1000 / 1_000_000) * 10.0)
        self.assertEqual(cost_4_turbo.output_cost, (500 / 1_000_000) * 30.0)
        
        self.assertEqual(cost_4.input_cost, (1000 / 1_000_000) * 30.0)
        self.assertEqual(cost_4.output_cost, (500 / 1_000_000) * 60.0)
        
        self.assertEqual(cost_3_5.input_cost, (1000 / 1_000_000) * 0.5)
        self.assertEqual(cost_3_5.output_cost, (500 / 1_000_000) * 1.5)
        
        # Test with unknown model (should use default)
        cost_unknown = self.provider.calculate_cost(usage, "unknown-model")
        self.assertEqual(cost_unknown.input_cost, (1000 / 1_000_000) * 10.0)  # Default


if __name__ == "__main__":
    unittest.main()