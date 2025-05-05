"""
Anthropic provider implementation for Atlas.

This module implements the Anthropic provider for Claude models.
"""

import os
from typing import Dict, List, Any, Optional, Tuple

from anthropic import Anthropic

from atlas.core.providers.base import ModelProvider, ModelResponse, MessageContent

class AnthropicProvider(ModelProvider):
    """Anthropic language model provider for Claude models."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "claude-3-5-sonnet-20240620",
        max_tokens: int = 2000,
    ):
        """Initialize Anthropic provider.

        Args:
            api_key: API key for Anthropic. If None, read from environment.
            model_name: Name of the Anthropic model to use.
            max_tokens: Maximum number of tokens in responses.
        """
        # API key (from args or environment)
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY must be provided or set as an environment variable"
            )

        # Initialize the Anthropic client
        self.client = Anthropic(api_key=self.api_key)
        
        # Model settings
        self.model_name = model_name
        self.max_tokens = max_tokens

    def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
    ) -> ModelResponse:
        """Generate a response using the Anthropic model.

        Args:
            system_prompt: System prompt to guide the model.
            messages: List of message dictionaries with 'role' and 'content'.
            max_tokens: Maximum number of tokens in response. If None, use instance default.

        Returns:
            ModelResponse containing the generated text and usage statistics.
        """
        # Generate response using Claude
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens or self.max_tokens,
            system=system_prompt,
            messages=messages,
        )

        # Extract response text
        content = response.content[0].text
        
        # Extract usage statistics
        input_tokens = getattr(response.usage, 'input_tokens', 0)
        output_tokens = getattr(response.usage, 'output_tokens', 0)
        
        # Return standardized response
        return ModelResponse(
            content=MessageContent(text=content),
            model=self.model_name,
            usage={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            },
            provider="anthropic",
        )
    
    def calculate_cost(self, usage: Dict[str, int]) -> Tuple[float, float, float]:
        """Calculate approximate cost based on token usage.
        
        Args:
            usage: Dictionary with token usage statistics.
            
        Returns:
            Tuple of (input_cost, output_cost, total_cost) in USD.
        """
        # Define cost per million tokens by model
        # Prices as of May 2024
        if "claude-3-5-sonnet" in self.model_name:
            input_cost_per_million = 3.0
            output_cost_per_million = 15.0
        elif "claude-3-opus" in self.model_name:
            input_cost_per_million = 15.0
            output_cost_per_million = 75.0
        elif "claude-3-sonnet" in self.model_name:
            input_cost_per_million = 3.0
            output_cost_per_million = 15.0
        elif "claude-3-haiku" in self.model_name:
            input_cost_per_million = 0.25
            output_cost_per_million = 1.25
        else:
            # Default to Claude 3.5 Sonnet pricing
            input_cost_per_million = 3.0
            output_cost_per_million = 15.0
        
        # Calculate costs
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        
        input_cost = (input_tokens / 1000000) * input_cost_per_million
        output_cost = (output_tokens / 1000000) * output_cost_per_million
        total_cost = input_cost + output_cost
        
        return input_cost, output_cost, total_cost