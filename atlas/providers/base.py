"""
Base model provider interface for Atlas.

This module defines the abstract base class that all model providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union


class ModelProvider(ABC):
    """Abstract base class for model providers."""

    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """Initialize the model provider with configuration.
        
        Args:
            config: Provider-specific configuration dictionary.
        """
        pass

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Generate a response from the model.
        
        Args:
            system_prompt: The system prompt/instructions.
            messages: List of message dictionaries with 'role' and 'content' keys.
            max_tokens: Maximum number of tokens to generate.
            model: Optional model override.
            temperature: Optional temperature override.
            
        Returns:
            A dictionary containing the model response and metadata.
        """
        pass

    @abstractmethod
    def get_response_text(self, response: Dict[str, Any]) -> str:
        """Extract the response text from a model response.
        
        Args:
            response: The response object from the generate method.
            
        Returns:
            The text of the response.
        """
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get a list of available models for this provider.
        
        Returns:
            A list of model identifiers.
        """
        pass
    
    @abstractmethod
    def validate_api_key(self) -> bool:
        """Validate that the API key is set and valid.
        
        Returns:
            True if the API key is valid, False otherwise.
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the name of the provider.
        
        Returns:
            The provider's name as a string.
        """
        pass
        
    def get_token_usage(self, response: Dict[str, Any]) -> Dict[str, int]:
        """Get token usage statistics from a model response.
        
        Args:
            response: The response object from the generate method.
            
        Returns:
            A dictionary with 'input_tokens', 'output_tokens', and 'total_tokens' keys.
        """
        # Default implementation returns empty usage
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    
    def get_cost_estimate(self, response: Dict[str, Any]) -> Dict[str, float]:
        """Estimate the cost of a model response.
        
        Args:
            response: The response object from the generate method.
            
        Returns:
            A dictionary with 'input_cost', 'output_cost', and 'total_cost' keys.
        """
        # Default implementation returns zero cost
        return {"input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0}