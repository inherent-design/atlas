#!/usr/bin/env python3
"""
Test provider schema validation.

This module tests the validation decorators and utilities specific to
provider implementations in Atlas, including request and response validation,
capability validation, and provider options validation.
"""

import unittest
from typing import Any, Dict, List, Optional
from unittest.mock import patch, MagicMock

from marshmallow import Schema, fields, ValidationError

from atlas.providers.validation import (
    validate_request,
    validate_response,
    validated_by,
    validate_options,
    validate_capabilities,
    provider_schema_validated,
    validate_stream_handler
)
from atlas.providers.errors import ProviderValidationError
from atlas.providers.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TokenUsage,
    CostEstimate
)
from atlas.core.types import MessageRole
from atlas.schemas.providers import (
    model_request_schema,
    model_response_schema
)


class TestRequestDecorator(unittest.TestCase):
    """Test @validate_request decorator."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock provider class
        class MockProvider:
            name = "mock-provider"
            
            @validate_request
            def generate(self, request):
                """Process a request and return a response."""
                return {
                    "content": "This is a test response",
                    "model": request.model if hasattr(request, "model") else "default-model",
                    "provider": self.name
                }
        
        self.provider_class = MockProvider
        self.provider = MockProvider()
    
    def test_valid_request_validation(self):
        """Test validation with a valid ModelRequest object."""
        # Create a valid request
        request = ModelRequest(
            messages=[ModelMessage.user("Test message")],
            model="test-model"
        )
        
        # Generate a response
        response = self.provider.generate(request)
        
        # Check response
        self.assertEqual(response["content"], "This is a test response")
        self.assertEqual(response["model"], "test-model")
        self.assertEqual(response["provider"], "mock-provider")
    
    def test_dict_request_validation(self):
        """Test validation with a request passed as a dictionary."""
        # Create a request as a dict
        request_dict = {
            "messages": [{"role": "user", "content": "Test message"}],
            "model": "dict-model"
        }
        
        # Generate a response
        response = self.provider.generate(request_dict)
        
        # Check response
        self.assertEqual(response["content"], "This is a test response")
        self.assertEqual(response["model"], "dict-model")
        self.assertEqual(response["provider"], "mock-provider")
    
    def test_invalid_request_validation(self):
        """Test validation with an invalid request."""
        # Create an invalid request (no messages)
        invalid_request = {
            "model": "invalid-model",
            "messages": []  # Empty messages list is invalid
        }
        
        # Generate a response - should raise error
        with self.assertRaises(ProviderValidationError):
            self.provider.generate(invalid_request)
    
    def test_already_validated_request(self):
        """Test with a request that's marked as already validated."""
        # Mock a SchemaValidated instance
        mock_request = MagicMock()
        mock_request.data = ModelRequest(
            messages=[ModelMessage.user("Already validated")],
            model="validated-model"
        )
        
        # Generate a response
        response = self.provider.generate(mock_request)
        
        # Check response
        self.assertEqual(response["content"], "This is a test response")
        self.assertEqual(response["model"], "validated-model")
        self.assertEqual(response["provider"], "mock-provider")


class TestResponseDecorator(unittest.TestCase):
    """Test @validate_response decorator."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock provider class
        class MockProvider:
            name = "mock-provider"
            
            @validate_response
            def create_response(self, content, model, usage=None):
                """Create and return a ModelResponse."""
                return ModelResponse(
                    content=content,
                    model=model,
                    provider=self.name,
                    usage=usage or TokenUsage(input_tokens=100, output_tokens=50)
                )
            
            @validate_response
            def return_dict(self, content, model):
                """Return a dict that should be converted to ModelResponse."""
                return {
                    "content": content,
                    "model": model,
                    "provider": self.name,
                    "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}
                }
            
            @validate_response
            def return_invalid(self):
                """Return an invalid response that should fail validation."""
                return {
                    "content": "Invalid response",
                    "model": "test-model",
                    # Missing provider field
                }
        
        self.provider_class = MockProvider
        self.provider = MockProvider()
    
    def test_valid_response_validation(self):
        """Test validation with a valid ModelResponse object."""
        # Create a response via the decorated method
        response = self.provider.create_response(
            content="Test response",
            model="test-model"
        )
        
        # Check response
        self.assertIsInstance(response, ModelResponse)
        self.assertEqual(response.content, "Test response")
        self.assertEqual(response.model, "test-model")
        self.assertEqual(response.provider, "mock-provider")
        self.assertEqual(response.usage.input_tokens, 100)
        self.assertEqual(response.usage.output_tokens, 50)
        self.assertEqual(response.usage.total_tokens, 150)
    
    def test_dict_response_validation(self):
        """Test validation when returning a dictionary."""
        # Create a response via the decorated method
        response = self.provider.return_dict(
            content="Dict response",
            model="dict-model"
        )
        
        # Check response
        self.assertIsInstance(response, ModelResponse)
        self.assertEqual(response.content, "Dict response")
        self.assertEqual(response.model, "dict-model")
        self.assertEqual(response.provider, "mock-provider")
        self.assertEqual(response.usage.input_tokens, 10)
        self.assertEqual(response.usage.output_tokens, 5)
        self.assertEqual(response.usage.total_tokens, 15)
    
    def test_invalid_response_validation(self):
        """Test validation with an invalid response."""
        # Create a response via the decorated method - should raise error
        with self.assertRaises(ProviderValidationError):
            self.provider.return_invalid()
    
    @patch("atlas.providers.validation.model_response_schema.load")
    def test_already_validated_response(self, mock_schema_load):
        """Test with a response that's marked as already validated."""
        # Skip validation for this test
        mock_schema_load.side_effect = Exception("Schema load should not be called")
        
        # Mock a SchemaValidated instance
        mock_response = MagicMock()
        mock_response.__class__ = ModelResponse  # Required for isinstance check
        
        # Create a mock provider method that returns the already validated response
        class TestProvider:
            name = "test-provider"
            
            @validate_response
            def return_validated(self):
                return mock_response
                
        provider = TestProvider()
        
        # Get the response - should not trigger validation
        response = provider.return_validated()
        
        # Check mock was not called
        mock_schema_load.assert_not_called()
        
        # Check response
        self.assertEqual(response, mock_response)


class TestValidatedByDecorator(unittest.TestCase):
    """Test @validated_by decorator for flexible schema validation."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a test schema
        class TestConfigSchema(Schema):
            """Test configuration schema."""
            name = fields.String(required=True)
            value = fields.Integer(required=True)
        
        self.schema = TestConfigSchema()
        
        # Create a mock provider class with decorated methods
        class MockProvider:
            name = "mock-provider"
            
            @validated_by(TestConfigSchema(), field_name="config")
            def configure(self, config):
                """Configure with validated config."""
                return config
                
            @validated_by(TestConfigSchema())
            def get_config(self):
                """Return a configuration that will be validated."""
                return {"name": "test", "value": 42}
                
            @validated_by(TestConfigSchema())
            def get_invalid_config(self):
                """Return an invalid configuration."""
                return {"name": "test"}  # Missing required value field
        
        self.provider_class = MockProvider
        self.provider = MockProvider()
    
    def test_parameter_validation(self):
        """Test validation of a method parameter."""
        # Call with valid parameter
        result = self.provider.configure(config={"name": "test", "value": 42})
        
        # Check result
        self.assertEqual(result["name"], "test")
        self.assertEqual(result["value"], 42)
        
        # Call with invalid parameter
        with self.assertRaises(ProviderValidationError):
            self.provider.configure(config={"name": "test"})  # Missing required value field
    
    def test_return_value_validation(self):
        """Test validation of a method return value."""
        # Call method with valid return value
        result = self.provider.get_config()
        
        # Check result
        self.assertEqual(result["name"], "test")
        self.assertEqual(result["value"], 42)
        
        # Call method with invalid return value
        with self.assertRaises(ProviderValidationError):
            self.provider.get_invalid_config()


class TestValidateOptionsDecorator(unittest.TestCase):
    """Test @validate_options decorator for class initialization options."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a test schema
        class ProviderOptionsSchema(Schema):
            """Test provider options schema."""
            api_key = fields.String(required=True)
            model = fields.String(required=True)
            temperature = fields.Float(required=False, validate=lambda n: 0 <= n <= 1)
        
        self.schema = ProviderOptionsSchema()
        
        # Create a mock provider class with decorated initialization
        @validate_options(ProviderOptionsSchema())
        class MockProvider:
            name = "mock-provider"
            
            def __init__(self, name=None, options=None, **kwargs):
                """Initialize with validated options."""
                self.name = name or self.name
                self.options = options or {}
        
        self.provider_class = MockProvider
    
    def test_valid_options(self):
        """Test initialization with valid options."""
        # Create instance with valid options
        provider = self.provider_class(
            name="test-provider",
            options={
                "api_key": "test-key",
                "model": "test-model",
                "temperature": 0.7
            }
        )
        
        # Check options were set
        self.assertEqual(provider.name, "test-provider")
        self.assertEqual(provider.options["api_key"], "test-key")
        self.assertEqual(provider.options["model"], "test-model")
        self.assertEqual(provider.options["temperature"], 0.7)
    
    def test_missing_options(self):
        """Test initialization with missing required options."""
        # Create instance with missing required option
        with self.assertRaises(ProviderValidationError):
            self.provider_class(
                options={
                    "api_key": "test-key",
                    # Missing required model field
                }
            )
    
    def test_invalid_options(self):
        """Test initialization with invalid options."""
        # Create instance with invalid temperature
        with self.assertRaises(ProviderValidationError):
            self.provider_class(
                options={
                    "api_key": "test-key",
                    "model": "test-model",
                    "temperature": 1.5  # Invalid: must be between 0 and 1
                }
            )
    
    def test_no_options(self):
        """Test initialization without options parameter."""
        # Create instance without options
        provider = self.provider_class(name="test-provider")
        
        # Should work fine with empty options
        self.assertEqual(provider.name, "test-provider")
        self.assertEqual(provider.options, {})


class TestValidateCapabilitiesDecorator(unittest.TestCase):
    """Test @validate_capabilities decorator for capability requirements."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock provider class with capabilities
        class MockProvider:
            name = "mock-provider"
            capabilities = {
                "text": 3,  # Strong text capability
                "vision": 1,  # Limited vision capability
                "streaming": 2  # Moderate streaming capability
            }
            
            @validate_capabilities(required_capabilities=["text"])
            def generate_text(self, prompt):
                """Generate text with validated text capability."""
                return f"Generated text: {prompt}"
                
            @validate_capabilities(
                required_capabilities=["vision", "text"],
                min_strengths={"vision": 2}
            )
            def process_image(self, image_url, prompt):
                """Process an image with validated vision capability."""
                return f"Image description for {image_url}: {prompt}"
                
            @validate_capabilities(
                required_capabilities=["audio"],
                min_strengths={"audio": 1}
            )
            def transcribe_audio(self, audio_url):
                """Transcribe audio with validated audio capability."""
                return f"Transcription for {audio_url}"
                
            @validate_capabilities(
                required_capabilities=["streaming"],
                min_strengths={"streaming": 3}
            )
            def stream_generation(self, prompt):
                """Stream generation with validated streaming capability."""
                return f"Streaming response for: {prompt}"
        
        self.provider_class = MockProvider
        self.provider = MockProvider()
    
    def test_basic_capability_requirement(self):
        """Test validation with a basic capability requirement."""
        # Call method requiring text capability
        result = self.provider.generate_text("Test prompt")
        
        # Should succeed as provider has text capability
        self.assertEqual(result, "Generated text: Test prompt")
    
    def test_multiple_capability_requirements(self):
        """Test validation with multiple capability requirements."""
        # Call method requiring vision and text capabilities
        # Should fail as provider has vision capability but at strength 1 (needs 2)
        with self.assertRaises(ProviderValidationError) as cm:
            self.provider.process_image("https://example.com/image.jpg", "Describe this")
        
        # Check error details
        error = cm.exception
        self.assertIn("insufficient capability strengths", str(error))
        self.assertEqual(error.details["insufficient_strengths"]["vision"]["required"], 2)
        self.assertEqual(error.details["insufficient_strengths"]["vision"]["actual"], 1)
    
    def test_missing_capability(self):
        """Test validation with a missing capability."""
        # Call method requiring audio capability
        # Should fail as provider has no audio capability
        with self.assertRaises(ProviderValidationError) as cm:
            self.provider.transcribe_audio("https://example.com/audio.mp3")
        
        # Check error details
        error = cm.exception
        self.assertIn("missing required capabilities", str(error))
        self.assertIn("audio", error.details["missing_capabilities"])
    
    def test_insufficient_capability_strength(self):
        """Test validation with insufficient capability strength."""
        # Call method requiring streaming capability at strength 3
        # Should fail as provider has streaming capability but at strength 2 (needs 3)
        with self.assertRaises(ProviderValidationError) as cm:
            self.provider.stream_generation("Test streaming")
        
        # Check error details
        error = cm.exception
        self.assertIn("insufficient capability strengths", str(error))
        self.assertEqual(error.details["insufficient_strengths"]["streaming"]["required"], 3)
        self.assertEqual(error.details["insufficient_strengths"]["streaming"]["actual"], 2)


class TestProviderSchemaValidatedDecorator(unittest.TestCase):
    """Test @provider_schema_validated decorator for provider classes."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a test schema
        class TestProviderSchema(Schema):
            """Test provider schema."""
            name = fields.String(required=True)
            model_name = fields.String(required=True)
            api_key = fields.String(required=False)
            temperature = fields.Float(required=False, validate=lambda n: 0 <= n <= 1)
        
        # Create a provider class with the decorator
        @provider_schema_validated(lambda: TestProviderSchema())
        class TestProvider:
            """Test provider class with schema validation."""
            
            def __init__(self, name, model_name, api_key=None, temperature=0.7, **kwargs):
                """Initialize with validated parameters."""
                self.name = name
                self.model_name = model_name
                self.api_key = api_key
                self.temperature = temperature
                self.extra_args = kwargs
        
        self.provider_class = TestProvider
    
    def test_initialization(self):
        """Test initialization with validated parameters."""
        # Create provider with valid parameters
        provider = self.provider_class(
            name="test-provider",
            model_name="test-model",
            api_key="test-key",
            temperature=0.5
        )
        
        # Check attributes were set
        self.assertEqual(provider.name, "test-provider")
        self.assertEqual(provider.model_name, "test-model")
        self.assertEqual(provider.api_key, "test-key")
        self.assertEqual(provider.temperature, 0.5)
    
    def test_invalid_initialization(self):
        """Test initialization with invalid parameters."""
        # Create provider with invalid temperature
        with self.assertRaises(ProviderValidationError):
            self.provider_class(
                name="test-provider",
                model_name="test-model",
                temperature=1.5  # Invalid: must be between 0 and 1
            )
        
        # Create provider with missing required field
        with self.assertRaises(ProviderValidationError):
            self.provider_class(
                name="test-provider"
                # Missing required model_name field
            )
    
    def test_from_dict_to_dict(self):
        """Test from_dict and to_dict methods added by decorator."""
        # Create data dict
        data = {
            "name": "dict-provider",
            "model_name": "dict-model",
            "temperature": 0.3
        }
        
        # Create provider from dict
        provider = self.provider_class.from_dict(data)
        
        # Check attributes were set
        self.assertEqual(provider.name, "dict-provider")
        self.assertEqual(provider.model_name, "dict-model")
        self.assertEqual(provider.temperature, 0.3)
        
        # Convert back to dict
        provider_dict = provider.to_dict()
        
        # Check dict contents
        self.assertEqual(provider_dict["name"], "dict-provider")
        self.assertEqual(provider_dict["model_name"], "dict-model")
        self.assertEqual(provider_dict["temperature"], 0.3)
    
    def test_schema_attribute(self):
        """Test schema attribute added by decorator."""
        # Check schema attribute
        self.assertIsNotNone(self.provider_class.schema)
        self.assertTrue(hasattr(self.provider_class.schema, "load"))
        self.assertTrue(hasattr(self.provider_class.schema, "dump"))


class TestStreamHandlerValidation(unittest.TestCase):
    """Test @validate_stream_handler decorator for streaming responses."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock stream handler class
        class MockStreamHandler:
            """Mock stream handler for testing."""
            
            def get_iterator(self):
                """Get an iterator for the stream."""
                return iter(["chunk1", "chunk2", "chunk3"])
            
            def process_stream(self, response):
                """Process a stream response."""
                return response
        
        # Create a mock invalid handler
        class InvalidHandler:
            """Invalid handler missing required methods."""
            
            def get_iterator(self):
                """Has get_iterator but not process_stream."""
                return iter(["chunk1", "chunk2"])
                
            # Missing process_stream method
        
        # Create a mock provider class
        class MockProvider:
            name = "mock-provider"
            
            @validate_stream_handler
            def stream(self, request):
                """Stream a response."""
                if not isinstance(request, ModelRequest):
                    request = ModelRequest.from_dict(request)
                    
                # Create and return a stream handler
                return MockStreamHandler()
                
            @validate_stream_handler
            def stream_invalid(self, request):
                """Return an invalid stream handler."""
                if not isinstance(request, ModelRequest):
                    request = ModelRequest.from_dict(request)
                    
                # Return an invalid handler
                return InvalidHandler()
                
            @validate_stream_handler
            def stream_dict(self, request):
                """Return a dict which is an invalid stream handler."""
                if not isinstance(request, ModelRequest):
                    request = ModelRequest.from_dict(request)
                    
                # Return a dict
                return {"chunks": ["chunk1", "chunk2"]}
        
        self.provider_class = MockProvider
        self.provider = MockProvider()
        self.stream_handler_class = MockStreamHandler
    
    def test_valid_handler(self):
        """Test validation with a valid stream handler."""
        # Create a valid request
        request = ModelRequest(
            messages=[ModelMessage.user("Test streaming")],
            model="test-model"
        )
        
        # Get stream handler
        handler = self.provider.stream(request)
        
        # Check handler
        self.assertIsInstance(handler, self.stream_handler_class)
        self.assertTrue(hasattr(handler, "get_iterator"))
        self.assertTrue(hasattr(handler, "process_stream"))
    
    def test_invalid_handler(self):
        """Test validation with an invalid stream handler."""
        # Create a valid request
        request = ModelRequest(
            messages=[ModelMessage.user("Test streaming")],
            model="test-model"
        )
        
        # Get stream handler - should raise error
        with self.assertRaises(ProviderValidationError):
            self.provider.stream_invalid(request)
    
    def test_dict_handler(self):
        """Test validation with a dict handler (invalid)."""
        # Create a valid request
        request = ModelRequest(
            messages=[ModelMessage.user("Test streaming")],
            model="test-model"
        )
        
        # Get stream handler - should raise error
        with self.assertRaises(ProviderValidationError):
            self.provider.stream_dict(request)
    
    def test_invalid_request(self):
        """Test validation with an invalid request."""
        # Create an invalid request
        request = {
            "model": "test-model",
            "messages": []  # Empty messages list is invalid
        }
        
        # Get stream handler - should raise error
        with self.assertRaises(ProviderValidationError):
            self.provider.stream(request)


if __name__ == "__main__":
    unittest.main()