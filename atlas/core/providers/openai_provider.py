"""
OpenAI provider implementation for Atlas.

This module implements the OpenAI provider for language models.
"""

import os
from typing import Dict, List, Any, Optional, Tuple

from openai import OpenAI

from atlas.core.providers.base import ModelProvider, ModelResponse, MessageContent

class OpenAIProvider(ModelProvider):
    """OpenAI language model provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4o",
        max_tokens: int = 2000,
    ):
        """Initialize OpenAI provider.

        Args:
            api_key: API key for OpenAI. If None, read from environment.
            model_name: Name of the OpenAI model to use.
            max_tokens: Maximum number of tokens in responses.
        """
        # API key (from args or environment)
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY must be provided or set as an environment variable"
            )

        # Initialize the OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        # Model settings
        self.model_name = model_name
        self.max_tokens = max_tokens

    def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
    ) -> ModelResponse:
        """Generate a response using the OpenAI model.

        Args:
            system_prompt: System prompt to guide the model.
            messages: List of message dictionaries with 'role' and 'content'.
            max_tokens: Maximum number of tokens in response. If None, use instance default.

        Returns:
            ModelResponse containing the generated text and usage statistics.
        """
        # Convert Atlas message format to OpenAI format
        openai_messages = [{"role": "system", "content": system_prompt}]
        
        # Add user and assistant messages
        for msg in messages:
            if msg["role"] in ["user", "assistant"]:
                openai_messages.append(msg)
        
        # Generate response
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=openai_messages,
            max_tokens=max_tokens or self.max_tokens,
        )
        
        # Extract text from response
        content = response.choices[0].message.content
        
        # Extract usage statistics
        input_tokens = getattr(response, "usage", {}).get("prompt_tokens", 0)
        output_tokens = getattr(response, "usage", {}).get("completion_tokens", 0)
        
        # Convert OpenAI response to standardized ModelResponse format
        return ModelResponse(
            content=MessageContent(text=content),
            model=self.model_name,
            usage={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            },
            provider="openai",
        )
    
    def calculate_cost(self, usage: Dict[str, int]) -> Tuple[float, float, float]:
        """Calculate approximate cost based on token usage.
        
        Args:
            usage: Dictionary with token usage statistics.
            
        Returns:
            Tuple of (input_cost, output_cost, total_cost) in USD.
        """
        # Define cost per million tokens for GPT-4o
        # These rates are as of May 2024 and may change
        if self.model_name == "gpt-4o":
            input_cost_per_million = 5.0  # $5 per million input tokens
            output_cost_per_million = 15.0  # $15 per million output tokens
        elif "gpt-4-turbo" in self.model_name:
            input_cost_per_million = 10.0
            output_cost_per_million = 30.0
        elif "gpt-4" in self.model_name:
            input_cost_per_million = 30.0
            output_cost_per_million = 60.0
        elif "gpt-3.5-turbo" in self.model_name:
            input_cost_per_million = 0.5
            output_cost_per_million = 1.5
        else:
            # Default to GPT-4o pricing for unknown models
            input_cost_per_million = 5.0
            output_cost_per_million = 15.0
        
        # Calculate costs
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        
        input_cost = (input_tokens / 1000000) * input_cost_per_million
        output_cost = (output_tokens / 1000000) * output_cost_per_million
        total_cost = input_cost + output_cost
        
        return input_cost, output_cost, total_cost