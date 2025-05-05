"""
Anthropic model provider implementation for Atlas.

This module provides integration with Anthropic's Claude models.
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
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    logger.warning("Anthropic SDK not installed. Install with 'uv add anthropic'")
    ANTHROPIC_AVAILABLE = False


class AnthropicProvider(ModelProvider):
    """Anthropic Claude model provider."""
    
    # Current Anthropic pricing per million tokens (as of the latest update)
    # These should be moved to a configuration file in the future
    PRICING = {
        "claude-3-5-sonnet-20240620": {"input": 3.0, "output": 15.0},  # $3.00/M input, $15.00/M output
        "claude-3-7-sonnet-20250219": {"input": 3.0, "output": 15.0},  # $3.00/M input, $15.00/M output
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},     # $15.00/M input, $75.00/M output
        "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},    # $3.00/M input, $15.00/M output
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},    # $0.25/M input, $1.25/M output
        # Fallback pricing for unknown models
        "default": {"input": 3.0, "output": 15.0},
    }
    
    def __init__(
        self,
        model_name: str = "claude-3-7-sonnet-20250219",
        max_tokens: int = 2000,
        api_key: Optional[str] = None,
        **kwargs: Any,
    ):
        """Initialize the Anthropic provider.
        
        Args:
            model_name: Name of the Claude model to use.
            max_tokens: Maximum tokens for model generation.
            api_key: Optional API key (defaults to ANTHROPIC_API_KEY environment variable).
            **kwargs: Additional provider-specific parameters.
        
        Raises:
            ValueError: If the Anthropic API key is missing or the SDK is not installed.
        """
        self._model_name = model_name
        self._max_tokens = max_tokens
        
        # Check if Anthropic is available
        if not ANTHROPIC_AVAILABLE:
            raise ValueError("Anthropic SDK is not installed")
        
        # Get API key from env module
        self._api_key = api_key or env.get_api_key("anthropic")
        if not self._api_key:
            raise ValueError("Anthropic API key not provided and ANTHROPIC_API_KEY not set")
        
        # Initialize client
        self._client = anthropic.Anthropic(api_key=self._api_key)
        logger.debug(f"Initialized Anthropic provider with model {model_name}")
        
        # Store additional parameters
        self._additional_params = kwargs
    
    @property
    def name(self) -> str:
        """Get the name of the provider.
        
        Returns:
            The provider's name as a string.
        """
        return "anthropic"
    
    def validate_api_key(self) -> bool:
        """Validate that the API key is set and valid.
        
        Returns:
            True if the API key is valid, False otherwise.
        """
        # Use env module to check for API key
        if not self._api_key:
            # Try to get API key from environment
            self._api_key = env.get_api_key("anthropic")
        
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
        # This is a static list as Anthropic doesn't provide an API for this yet
        return [
            "claude-3-7-sonnet-20250219",
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
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
        # TODO: Implement this method with the Anthropic API
        # This is a placeholder implementation
        
        # Convert the request to Anthropic format
        anthropic_request = request.to_provider_request("anthropic")
        
        # Add model and max_tokens if not specified
        model = request.model or self._model_name
        anthropic_request["model"] = model
        anthropic_request["max_tokens"] = request.max_tokens or self._max_tokens
        
        # Add any additional parameters from initialization
        for key, value in self._additional_params.items():
            if key not in anthropic_request:
                anthropic_request[key] = value
        
        logger.debug(f"Calling Anthropic API with model {model}")
        
        # Make the API call
        try:
            response = self._client.messages.create(**anthropic_request)
            
            # Extract content
            content = response.content[0].text
            
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
                finish_reason=response.stop_reason,
                raw_response=response.model_dump(),
            )
            
            return model_response
            
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {e}")
            raise ValueError(f"Error calling Anthropic API: {e}")
    
    def calculate_token_usage(self, request: ModelRequest, response: Any) -> TokenUsage:
        """Calculate token usage for a request and response.
        
        Args:
            request: The model request.
            response: The raw response from the Anthropic API.
            
        Returns:
            A TokenUsage object with token counts.
        """
        # Extract usage from the response
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        
        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
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
        # Convert the request to Anthropic format
        anthropic_request = request.to_provider_request("anthropic")
        
        # Add model and max_tokens if not specified
        model = request.model or self._model_name
        anthropic_request["model"] = model
        anthropic_request["max_tokens"] = request.max_tokens or self._max_tokens
        anthropic_request["stream"] = True
        
        # Add any additional parameters from initialization
        for key, value in self._additional_params.items():
            if key not in anthropic_request:
                anthropic_request[key] = value
        
        logger.debug(f"Calling Anthropic API with streaming for model {model}")
        
        # Make the API call
        try:
            stream = self._client.messages.create(**anthropic_request)
            
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
            logger.error(f"Error calling Anthropic API for streaming: {e}")
            raise ValueError(f"Error calling Anthropic API for streaming: {e}")