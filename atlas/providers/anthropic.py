"""
Anthropic model provider implementation for Atlas.

This module implements the ModelProvider interface for Anthropic's Claude models.
"""

import os
from typing import Dict, List, Any, Optional

try:
    from anthropic import Anthropic
except ImportError:
    raise ImportError(
        "The 'anthropic' package is required to use the Anthropic provider. "
        "Install it with: pip install anthropic"
    )

from atlas.providers.base import ModelProvider


class AnthropicProvider(ModelProvider):
    """Anthropic Claude model provider."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Anthropic provider.
        
        Args:
            config: Configuration dictionary with 'api_key' or using env var.
        """
        self.api_key = config.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key must be provided in config or as ANTHROPIC_API_KEY environment variable"
            )
            
        # Initialize the client
        self.client = Anthropic(api_key=self.api_key)
        
        # Set default model if provided in config
        self.default_model = config.get("model", "claude-3-7-sonnet-20250219")
        self.default_max_tokens = config.get("max_tokens", 2000)
        self.default_temperature = config.get("temperature", 0.7)
        
        # Define available models
        self._available_models = [
            "claude-3-7-sonnet-20250219",
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2",
        ]

    def generate(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Generate a response from Claude.
        
        Args:
            system_prompt: The system prompt/instructions.
            messages: List of message dictionaries with 'role' and 'content' keys.
            max_tokens: Maximum number of tokens to generate.
            model: Optional model override.
            temperature: Optional temperature override.
            
        Returns:
            The complete response object from Anthropic.
        """
        response = self.client.messages.create(
            model=model or self.default_model,
            max_tokens=max_tokens or self.default_max_tokens,
            temperature=temperature or self.default_temperature,
            system=system_prompt,
            messages=messages,
        )
        
        # Store model used for later cost calculation
        response.model_used = model or self.default_model
        
        return response

    def get_response_text(self, response: Dict[str, Any]) -> str:
        """Extract the response text from a Claude response.
        
        Args:
            response: The response object from the generate method.
            
        Returns:
            The text of the response.
        """
        if hasattr(response, "content") and response.content:
            return response.content[0].text
        return ""

    def get_available_models(self) -> List[str]:
        """Get a list of available Claude models.
        
        Returns:
            A list of model identifiers.
        """
        return self._available_models
        
    def validate_api_key(self) -> bool:
        """Validate that the Anthropic API key is set and valid.
        
        Returns:
            True if the API key is valid, False otherwise.
        """
        if not self.api_key:
            return False
        
        try:
            # Try a minimal API call to validate the key
            self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                system="You are a helpful assistant.",
                messages=[{"role": "user", "content": "Hello"}],
            )
            return True
        except Exception:
            return False
    
    @property
    def provider_name(self) -> str:
        """Get the name of the provider.
        
        Returns:
            The provider's name as a string.
        """
        return "anthropic"
        
    def get_token_usage(self, response: Dict[str, Any]) -> Dict[str, int]:
        """Get token usage statistics from a Claude response.
        
        Args:
            response: The response object from the generate method.
            
        Returns:
            A dictionary with 'input_tokens', 'output_tokens', and 'total_tokens' keys.
        """
        if hasattr(response, "usage"):
            return {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            }
        return super().get_token_usage(response)
    
    def get_cost_estimate(self, response: Dict[str, Any]) -> Dict[str, float]:
        """Estimate the cost of a Claude response based on token usage.
        
        Args:
            response: The response object from the generate method.
            
        Returns:
            A dictionary with 'input_cost', 'output_cost', and 'total_cost' keys.
        """
        usage = self.get_token_usage(response)
        
        # Define cost per million tokens based on model
        # These rates are subject to change - update as needed
        model = getattr(response, "model_used", self.default_model)
        
        # Latest Claude model pricing as of May 2023
        if "claude-3-opus" in model:
            input_rate = 15.0  # $15.00 per million tokens
            output_rate = 75.0  # $75.00 per million tokens
        elif "claude-3-sonnet" in model or "claude-3-7-sonnet" in model or "claude-3-5-sonnet" in model:
            input_rate = 3.0  # $3.00 per million tokens
            output_rate = 15.0  # $15.00 per million tokens
        elif "claude-3-haiku" in model:
            input_rate = 0.25  # $0.25 per million tokens
            output_rate = 1.25  # $1.25 per million tokens
        elif "claude-2" in model:
            input_rate = 8.0  # $8.00 per million tokens
            output_rate = 24.0  # $24.00 per million tokens
        else:  # claude-instant or unknown models
            input_rate = 0.8  # $0.80 per million tokens
            output_rate = 2.4  # $2.40 per million tokens
            
        input_cost = usage["input_tokens"] * (input_rate / 1_000_000)
        output_cost = usage["output_tokens"] * (output_rate / 1_000_000)
        total_cost = input_cost + output_cost
        
        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
        }