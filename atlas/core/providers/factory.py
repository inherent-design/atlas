"""
Factory for creating model providers.

This module defines functions for dynamically creating and managing model providers.
"""

import importlib
import os
from typing import Dict, List, Optional, Any, Type

from atlas.core.providers.base import ModelProvider


def get_available_providers() -> Dict[str, List[str]]:
    """Get a dictionary of available model providers and their supported models.
    
    Returns:
        Dictionary mapping provider names to lists of supported model names.
    """
    providers = {}
    
    # Check for Anthropic
    if os.environ.get("ANTHROPIC_API_KEY"):
        providers["anthropic"] = [
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-7-sonnet-20250219",  # Use this as the default
        ]
    
    # Check for OpenAI
    if os.environ.get("OPENAI_API_KEY"):
        providers["openai"] = [
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ]
    
    # Check for Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/version", timeout=1)
        if response.status_code == 200:
            # Try to get actual models
            try:
                models_response = requests.get("http://localhost:11434/api/tags", timeout=1)
                if models_response.status_code == 200:
                    data = models_response.json()
                    ollama_models = [model["name"] for model in data.get("models", [])]
                    providers["ollama"] = ollama_models if ollama_models else ["llama3", "mistral", "gemma"]
                else:
                    providers["ollama"] = ["llama3", "mistral", "gemma"]
            except:
                providers["ollama"] = ["llama3", "mistral", "gemma"]
    except:
        # Ollama is not available
        pass
    
    return providers


def create_provider(
    provider_name: str,
    model_name: Optional[str] = None,
    max_tokens: int = 2000,
    **kwargs: Any,
) -> ModelProvider:
    """Create a model provider instance.
    
    Args:
        provider_name: Name of the provider to create.
        model_name: Name of the model to use (if None, use provider default).
        max_tokens: Maximum tokens for model generation.
        **kwargs: Additional provider-specific parameters.
        
    Returns:
        ModelProvider instance.
        
    Raises:
        ValueError: If the provider is not supported or required configuration is missing.
    """
    # Map provider names to their implementation classes
    provider_map = {
        "anthropic": "atlas.core.providers.anthropic_provider.AnthropicProvider",
        "openai": "atlas.core.providers.openai_provider.OpenAIProvider",
        "ollama": "atlas.core.providers.ollama_provider.OllamaProvider",
    }
    
    if provider_name not in provider_map:
        raise ValueError(f"Unsupported provider: {provider_name}")
    
    # Get provider class path
    provider_class_path = provider_map[provider_name]
    
    # Split into module path and class name
    module_path, class_name = provider_class_path.rsplit(".", 1)
    
    try:
        # Dynamically import the module
        module = importlib.import_module(module_path)
        
        # Get the provider class
        provider_class: Type[ModelProvider] = getattr(module, class_name)
        
        # Set default model name if not provided
        if model_name is None:
            available_providers = get_available_providers()
            if provider_name in available_providers and available_providers[provider_name]:
                model_name = available_providers[provider_name][0]
            else:
                # Use sensible defaults for each provider
                if provider_name == "anthropic":
                    model_name = "claude-3-7-sonnet-20250219"
                elif provider_name == "openai":
                    model_name = "gpt-4o"
                elif provider_name == "ollama":
                    model_name = "llama3"
        
        # Create and return provider instance
        provider_kwargs = {
            "model_name": model_name,
            "max_tokens": max_tokens,
            **kwargs,
        }
        
        return provider_class(**provider_kwargs)
        
    except ImportError as e:
        raise ValueError(f"Failed to import provider module: {e}")
    except AttributeError as e:
        raise ValueError(f"Failed to find provider class: {e}")
    except Exception as e:
        raise ValueError(f"Error creating provider: {e}")