"""
Provider options and configuration module.

This module defines the ProviderOptions class which centralizes all provider
configuration parameters and supports auto-detection and resolution of provider/model
combinations across different application entry points.
"""

import copy
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union, List

from atlas.core import env
from atlas.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ProviderOptions:
    """Options for creating and configuring model providers.
    
    This class centralizes all parameters used for provider selection, creation,
    and configuration. It supports auto-detection of providers from model names,
    capability-based model selection, and environment variable defaults.
    
    Attributes:
        provider_name: Name of the provider (e.g., "anthropic", "openai", "ollama", "mock")
        model_name: Name of the model to use
        capability: Capability required (e.g., "inexpensive", "efficient", "premium", "vision")
        max_tokens: Maximum tokens for model generation
        base_url: Base URL for provider API (primarily used for Ollama)
        extra_params: Additional provider-specific parameters
    """
    
    # Core provider and model selection
    provider_name: Optional[str] = None
    model_name: Optional[str] = None
    capability: Optional[str] = None
    
    # Performance and resource limits
    max_tokens: Optional[int] = None
    
    # Connection parameters
    base_url: Optional[str] = None
    
    # Additional provider-specific parameters
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_env(cls) -> 'ProviderOptions':
        """Create ProviderOptions based on environment variables.
        
        This factory method constructs ProviderOptions using values from
        environment variables, with appropriate defaults for missing values.
        
        Returns:
            Populated ProviderOptions instance
        """
        options = cls(
            provider_name=env.get_string("ATLAS_DEFAULT_PROVIDER", "anthropic"),
            model_name=env.get_string("ATLAS_DEFAULT_MODEL"),
            capability=env.get_string("ATLAS_DEFAULT_CAPABILITY", "inexpensive"),
            max_tokens=env.get_int("ATLAS_MAX_TOKENS", 2000),
        )
        
        # Provider-specific environment variables
        if options.provider_name == "ollama":
            options.base_url = env.get_string("ATLAS_OLLAMA_BASE_URL", "http://localhost:11434")
            
        return options
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert options to dictionary format.
        
        Returns:
            Dictionary representation of the options
        """
        result = {
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "capability": self.capability,
            "max_tokens": self.max_tokens,
        }
        
        # Add optional parameters if set
        if self.base_url:
            result["base_url"] = self.base_url
            
        # Add any extra parameters
        result.update(self.extra_params)
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProviderOptions':
        """Create ProviderOptions from dictionary.
        
        Args:
            data: Dictionary containing provider options
            
        Returns:
            Populated ProviderOptions instance
        """
        # Extract known fields
        known_fields = [
            "provider_name", "model_name", "capability", 
            "max_tokens", "base_url"
        ]
        
        kwargs = {k: v for k, v in data.items() if k in known_fields}
        
        # Extract extra parameters
        extra_params = {k: v for k, v in data.items() 
                       if k not in known_fields and not k.startswith("_")}
        
        return cls(**kwargs, extra_params=extra_params)
    
    def merge(self, other: 'ProviderOptions') -> 'ProviderOptions':
        """Create a new ProviderOptions by merging with another instance.
        
        This method creates a new ProviderOptions instance by combining values
        from self and other, with other's values taking precedence.
        
        Args:
            other: Another ProviderOptions instance to merge with
            
        Returns:
            New ProviderOptions instance with merged values
        """
        # Start with a copy of self
        merged_dict = self.to_dict()
        
        # Update with other's values, ignoring None values
        other_dict = other.to_dict()
        for key, value in other_dict.items():
            if value is not None:
                merged_dict[key] = value
        
        # Handle extra_params separately for deep merge
        merged_extra = copy.deepcopy(self.extra_params)
        merged_extra.update(other.extra_params)
        
        # Create new instance
        result = self.from_dict(merged_dict)
        result.extra_params = merged_extra
        
        return result