"""
OpenAI model provider implementation for Atlas.

This module provides integration with OpenAI's GPT models.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Union

from atlas.core.telemetry import traced, TracedClass
from atlas.core import env
from atlas.models.base import (
    ModelProvider,
    ModelRequest,
    ModelResponse,
    TokenUsage,
    CostEstimate,
)

logger = logging.getLogger(__name__)

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI SDK not installed. Install with 'uv add openai'")
    OPENAI_AVAILABLE = False


class OpenAIProvider(ModelProvider):
    """OpenAI model provider."""
    
    # Current OpenAI pricing per million tokens (as of the latest update)
    # These should be moved to a configuration file in the future
    PRICING = {
        "gpt-4o": {"input": 5.0, "output": 15.0},      # $5.00/M input, $15.00/M output
        "gpt-4-turbo": {"input": 10.0, "output": 30.0}, # $10.00/M input, $30.00/M output
        "gpt-4": {"input": 30.0, "output": 60.0},      # $30.00/M input, $60.00/M output
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5}, # $0.50/M input, $1.50/M output
        # Fallback pricing for unknown models
        "default": {"input": 10.0, "output": 30.0},
    }
    
    def __init__(
        self,
        model_name: str = "gpt-4o",
        max_tokens: int = 2000,
        api_key: Optional[str] = None,
        organization: Optional[str] = None,
        **kwargs: Any,
    ):
        """Initialize the OpenAI provider.
        
        Args:
            model_name: Name of the OpenAI model to use.
            max_tokens: Maximum tokens for model generation.
            api_key: Optional API key (defaults to OPENAI_API_KEY environment variable).
            organization: Optional organization ID.
            **kwargs: Additional provider-specific parameters.
        
        Raises:
            ValueError: If the OpenAI API key is missing or the SDK is not installed.
        """
        self._model_name = model_name
        self._max_tokens = max_tokens
        
        # Check if OpenAI is available
        if not OPENAI_AVAILABLE:
            raise ValueError("OpenAI SDK is not installed")
        
        # Get API key from env module
        self._api_key = api_key or env.get_api_key("openai")
        if not self._api_key:
            raise ValueError("OpenAI API key not provided and OPENAI_API_KEY not set")
        
        # Get organization from env module
        self._organization = organization or env.get_string("OPENAI_ORGANIZATION")
        
        # Initialize client
        client_kwargs = {"api_key": self._api_key}
        if self._organization:
            client_kwargs["organization"] = self._organization
        
        self._client = OpenAI(**client_kwargs)
        logger.debug(f"Initialized OpenAI provider with model {model_name}")
        
        # Store additional parameters
        self._additional_params = kwargs
    
    @property
    def name(self) -> str:
        """Get the name of the provider.
        
        Returns:
            The provider's name as a string.
        """
        return "openai"
    
    def validate_api_key(self) -> bool:
        """Validate that the API key is set and valid.
        
        Returns:
            True if the API key is valid, False otherwise.
        """
        # Use env module to check for API key
        if not self._api_key:
            # Try to get API key from environment
            self._api_key = env.get_api_key("openai")
        
        # Check if the key is now set
        if not self._api_key:
            return False
            
        # TODO: Implement a simple API call to verify the key is valid
        return True
    
    def get_available_models(self) -> List[str]:
        """Get a list of available models for this provider.
        
        Returns:
            A list of model identifiers.
        """
        try:
            # Get models from API
            models = self._client.models.list()
            model_ids = [model.id for model in models.data]
            
            # Filter to only include chat models
            chat_models = [
                model_id for model_id in model_ids
                if "gpt" in model_id.lower()
            ]
            
            return chat_models
        except Exception as e:
            logger.warning(f"Failed to get available models from OpenAI API: {e}")
            # Return default models
            return [
                "gpt-4o",
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo",
            ]
    
    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from the model.
        
        Args:
            request: The model request.
            
        Returns:
            A ModelResponse containing the generated content and metadata.
        
        Raises:
            ValueError: If the model is not available.
        """
        # TODO: Implement this method with the OpenAI API
        # This is a placeholder implementation
        
        # Convert the request to OpenAI format
        openai_request = request.to_provider_request("openai")
        
        # Add model and max_tokens if not specified
        model = request.model or self._model_name
        openai_request["model"] = model
        openai_request["max_tokens"] = request.max_tokens or self._max_tokens
        
        # Add any additional parameters from initialization
        for key, value in self._additional_params.items():
            if key not in openai_request:
                openai_request[key] = value
        
        logger.debug(f"Calling OpenAI API with model {model}")
        
        # Make the API call
        try:
            response = self._client.chat.completions.create(**openai_request)
            
            # Extract content
            content = response.choices[0].message.content
            
            # Calculate token usage
            usage = self.calculate_token_usage(request, response)
            
            # Calculate cost
            cost = self.calculate_cost(usage, model)
            
            # Create the response
            model_response = ModelResponse(
                content=content,
                model=model,
                provider=self.name,
                usage=usage,
                cost=cost,
                finish_reason=response.choices[0].finish_reason,
                raw_response=response.model_dump(),
            )
            
            return model_response
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise ValueError(f"Error calling OpenAI API: {e}")
    
    def calculate_token_usage(self, request: ModelRequest, response: Any) -> TokenUsage:
        """Calculate token usage for a request and response.
        
        Args:
            request: The model request.
            response: The raw response from the OpenAI API.
            
        Returns:
            A TokenUsage object with token counts.
        """
        # Extract usage from the response
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        
        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=response.usage.total_tokens,
        )
    
    def calculate_cost(self, usage: TokenUsage, model: str) -> CostEstimate:
        """Calculate approximate cost based on token usage.
        
        Args:
            usage: Token usage statistics.
            model: The model used for the request.
            
        Returns:
            A CostEstimate with input, output, and total costs.
        """
        # Get pricing for the model
        pricing = self.PRICING.get(model, self.PRICING["default"])
        
        # Calculate costs per million tokens
        input_cost = (usage.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (usage.output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        return CostEstimate(
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
        )
    
    def stream(self, request: ModelRequest) -> Tuple[ModelResponse, Any]:
        """Stream a response from the model.
        
        Args:
            request: The model request.
            
        Returns:
            A tuple of (final ModelResponse, stream iterator).
        """
        # TODO: Implement streaming
        # This is a placeholder implementation
        # Convert the request to OpenAI format
        openai_request = request.to_provider_request("openai")
        
        # Add model and max_tokens if not specified
        model = request.model or self._model_name
        openai_request["model"] = model
        openai_request["max_tokens"] = request.max_tokens or self._max_tokens
        openai_request["stream"] = True
        
        # Add any additional parameters from initialization
        for key, value in self._additional_params.items():
            if key not in openai_request:
                openai_request[key] = value
        
        logger.debug(f"Calling OpenAI API with streaming for model {model}")
        
        # Make the API call
        try:
            stream = self._client.chat.completions.create(**openai_request)
            
            # The final response will be populated during streaming
            final_response = None
            
            # Return a partial response and the stream
            # The caller will need to handle processing the stream
            return ModelResponse(
                content="",  # Will be populated during streaming
                model=model,
                provider=self.name,
                usage=TokenUsage(),  # Will be populated at end of stream
                cost=CostEstimate(),  # Will be populated at end of stream
            ), stream
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API for streaming: {e}")
            raise ValueError(f"Error calling OpenAI API for streaming: {e}")