"""
Factory for creating model providers.

This module provides functions for discovering, creating, and managing
model providers in a unified way.
"""

import importlib
import logging
from typing import Dict, List, Optional, Any, Type, Tuple, Callable, Set

from atlas.core.telemetry import traced, TracedClass
from atlas.core import env
from atlas.models.base import ModelProvider

logger = logging.getLogger(__name__)

# Registry of provider implementations
_PROVIDER_REGISTRY: Dict[str, str] = {
    "anthropic": "atlas.models.anthropic.AnthropicProvider",
    "openai": "atlas.models.openai.OpenAIProvider",
    "ollama": "atlas.models.ollama.OllamaProvider",
}

# Default models by provider
_DEFAULT_MODELS: Dict[str, str] = {
    "anthropic": "claude-3-7-sonnet-20250219",
    "openai": "gpt-4o",
    "ollama": "llama3",
}

# Cache for provider availability
_AVAILABLE_PROVIDERS: Optional[Dict[str, List[str]]] = None


@traced(name="discover_providers")
def discover_providers() -> Dict[str, List[str]]:
    """Discover available model providers and their supported models.
    
    This function checks the environment for available model providers
    and returns a dictionary mapping provider names to lists of supported
    model names.
    
    Returns:
        Dictionary mapping provider names to lists of supported model names.
    """
    global _AVAILABLE_PROVIDERS
    
    # Return cached results if available
    if _AVAILABLE_PROVIDERS is not None:
        return _AVAILABLE_PROVIDERS
    
    # Use env module to get available providers
    available_providers = env.get_available_providers()
    providers: Dict[str, List[str]] = {}
    
    # Check for Anthropic
    if available_providers.get("anthropic", False):
        providers["anthropic"] = [
            "claude-3-7-sonnet-20250219",  # Most recent as default
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]
        logger.debug("Discovered Anthropic provider with API key")
    
    # Check for OpenAI
    if available_providers.get("openai", False):
        providers["openai"] = [
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ]
        logger.debug("Discovered OpenAI provider with API key")
    
    # Check for Ollama
    if available_providers.get("ollama", False):
        try:
            import requests
            # Verify Ollama is running
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
                    logger.debug(f"Discovered Ollama provider with models: {providers['ollama']}")
                except Exception as e:
                    providers["ollama"] = ["llama3", "mistral", "gemma"]
                    logger.debug(f"Discovered Ollama provider with default models. Error: {e}")
            else:
                logger.debug("Ollama server not responsive")
        except Exception as e:
            # Ollama is not available
            logger.debug(f"Ollama provider not available: {e}")
    
    # Cache the results
    _AVAILABLE_PROVIDERS = providers
    return providers


@traced(name="register_provider")
def register_provider(provider_name: str, class_path: str) -> None:
    """Register a new provider implementation.
    
    Args:
        provider_name: The name of the provider.
        class_path: The import path to the provider class.
    """
    global _PROVIDER_REGISTRY
    _PROVIDER_REGISTRY[provider_name] = class_path
    logger.debug(f"Registered provider '{provider_name}' with class path '{class_path}'")
    
    # Invalidate the provider cache
    global _AVAILABLE_PROVIDERS
    _AVAILABLE_PROVIDERS = None


@traced(name="set_default_model")
def set_default_model(provider_name: str, model_name: str) -> None:
    """Set the default model for a provider.
    
    Args:
        provider_name: The name of the provider.
        model_name: The name of the default model.
    """
    global _DEFAULT_MODELS
    _DEFAULT_MODELS[provider_name] = model_name
    logger.debug(f"Set default model for '{provider_name}' to '{model_name}'")


@traced(name="get_provider_class")
def get_provider_class(provider_name: str) -> Type[ModelProvider]:
    """Get the provider class for a given provider name.
    
    Args:
        provider_name: The name of the provider.
        
    Returns:
        The provider class.
        
    Raises:
        ValueError: If the provider is not supported or the class cannot be loaded.
    """
    if provider_name not in _PROVIDER_REGISTRY:
        raise ValueError(f"Unsupported provider: {provider_name}")
    
    # Get provider class path
    provider_class_path = _PROVIDER_REGISTRY[provider_name]
    
    # Split into module path and class name
    module_path, class_name = provider_class_path.rsplit(".", 1)
    
    try:
        # Dynamically import the module
        module = importlib.import_module(module_path)
        
        # Get the provider class
        provider_class: Type[ModelProvider] = getattr(module, class_name)
        return provider_class
    
    except ImportError as e:
        raise ValueError(f"Failed to import provider module for {provider_name}: {e}")
    except AttributeError as e:
        raise ValueError(f"Failed to find provider class for {provider_name}: {e}")
    except Exception as e:
        raise ValueError(f"Error loading provider class for {provider_name}: {e}")


@traced(name="create_provider")
def create_provider(
    provider_name: Optional[str] = None,
    model_name: Optional[str] = None,
    max_tokens: Optional[int] = None,
    **kwargs: Any,
) -> ModelProvider:
    """Create a model provider instance.
    
    Args:
        provider_name: Name of the provider to create (if None, use environment default).
        model_name: Name of the model to use (if None, use provider default from environment).
        max_tokens: Maximum tokens for model generation (if None, use environment default).
        **kwargs: Additional provider-specific parameters.
        
    Returns:
        ModelProvider instance.
        
    Raises:
        ValueError: If the provider is not supported or required configuration is missing.
    """
    # Get default provider from environment if not specified
    if provider_name is None:
        provider_name = env.get_string("ATLAS_DEFAULT_PROVIDER", "anthropic")
    
    # Normalize provider name
    provider_name = provider_name.lower()
    
    # Get the provider class
    provider_class = get_provider_class(provider_name)
    
    # Get default max_tokens from environment if not specified
    if max_tokens is None:
        max_tokens = env.get_int("ATLAS_MAX_TOKENS", 2000)
    
    # Set default model name if not provided
    if model_name is None:
        # First check environment variable for this specific provider
        env_model_var = f"ATLAS_{provider_name.upper()}_DEFAULT_MODEL"
        env_model = env.get_string(env_model_var)
        
        if env_model:
            model_name = env_model
        else:
            # Then check the general default model variable
            model_name = env.get_string("ATLAS_DEFAULT_MODEL")
            
        # If still not found, use the provider's available models
        if not model_name:
            available_providers = discover_providers()
            if provider_name in available_providers and available_providers[provider_name]:
                model_name = available_providers[provider_name][0]
            else:
                # Fall back to hardcoded defaults
                model_name = _DEFAULT_MODELS.get(provider_name)
                if model_name is None:
                    raise ValueError(f"No default model available for provider: {provider_name}")
    
    # Create provider instance
    try:
        provider_kwargs = {
            "model_name": model_name,
            "max_tokens": max_tokens,
            **kwargs,
        }
        
        provider = provider_class(**provider_kwargs)
        logger.debug(f"Created provider '{provider_name}' with model '{model_name}'")
        return provider
        
    except Exception as e:
        logger.error(f"Failed to create provider '{provider_name}': {e}")
        raise ValueError(f"Error creating provider '{provider_name}': {e}")


@traced(name="get_all_providers")
def get_all_providers(
    max_tokens: int = 2000,
    **kwargs: Any,
) -> Dict[str, ModelProvider]:
    """Create instances of all available providers.
    
    Args:
        max_tokens: Maximum tokens for model generation.
        **kwargs: Additional provider-specific parameters.
        
    Returns:
        Dictionary mapping provider names to provider instances.
    """
    providers = {}
    available = discover_providers()
    
    for provider_name in available:
        try:
            providers[provider_name] = create_provider(
                provider_name=provider_name,
                max_tokens=max_tokens,
                **kwargs,
            )
        except Exception as e:
            logger.warning(f"Failed to create provider '{provider_name}': {e}")
    
    return providers


@traced(name="validate_api_keys")
def validate_api_keys(providers: Optional[List[str]] = None, skip_validation: bool = False) -> Dict[str, Dict[str, Any]]:
    """Validate API keys for specified providers.
    
    This function creates and validates provider instances for the specified providers.
    
    Args:
        providers: List of provider names to validate. If None, validates all available providers.
        skip_validation: If True, skips actual API calls and only checks if keys are present.
        
    Returns:
        Dictionary mapping provider names to validation results with the following keys:
        - valid: Whether the key is valid
        - error: Error message if validation failed
        - key_present: Whether the key is present (but might be invalid)
        - provider: Provider name
    """
    if providers is None:
        # Get all available providers based on environment variables
        available = discover_providers()
        providers = list(available.keys())
    
    results = {}
    
    # Set SKIP_API_KEY_CHECK environment variable if skip_validation is True
    if skip_validation:
        env.set_env_var("SKIP_API_KEY_CHECK", "true")
    
    try:
        for provider_name in providers:
            # Skip if provider not in registry
            if provider_name not in _PROVIDER_REGISTRY:
                results[provider_name] = {
                    "valid": False,
                    "provider": provider_name,
                    "key_present": False,
                    "error": f"Unsupported provider: {provider_name}"
                }
                continue
                
            try:
                # Try to create the provider
                provider = create_provider(provider_name=provider_name)
                
                # Validate the API key
                validation_result = provider.validate_api_key_detailed()
                results[provider_name] = validation_result
                
            except Exception as e:
                results[provider_name] = {
                    "valid": False,
                    "provider": provider_name,
                    "key_present": False,
                    "error": str(e)
                }
        
        return results
        
    finally:
        # Reset SKIP_API_KEY_CHECK if we set it
        if skip_validation:
            env.set_env_var("SKIP_API_KEY_CHECK", "false")


class ProviderFactory(TracedClass):
    """Factory for creating and managing model providers."""
    
    def __init__(self):
        """Initialize the provider factory."""
        self._providers: Dict[str, ModelProvider] = {}
        self._default_provider: Optional[str] = None
    
    def discover(self) -> Set[str]:
        """Discover available providers.
        
        Returns:
            Set of available provider names.
        """
        available = discover_providers()
        return set(available.keys())
    
    def create(
        self,
        provider_name: str,
        model_name: Optional[str] = None,
        max_tokens: int = 2000,
        **kwargs: Any,
    ) -> ModelProvider:
        """Create a provider instance.
        
        Args:
            provider_name: Name of the provider to create.
            model_name: Name of the model to use (if None, use provider default).
            max_tokens: Maximum tokens for model generation.
            **kwargs: Additional provider-specific parameters.
            
        Returns:
            ModelProvider instance.
            
        Raises:
            ValueError: If the provider is not supported.
        """
        provider = create_provider(
            provider_name=provider_name,
            model_name=model_name,
            max_tokens=max_tokens,
            **kwargs,
        )
        
        # Store the provider in the cache
        self._providers[provider_name] = provider
        
        # Set as default if no default is set
        if self._default_provider is None:
            self._default_provider = provider_name
        
        return provider
    
    def get(self, provider_name: Optional[str] = None) -> ModelProvider:
        """Get a provider instance.
        
        Args:
            provider_name: Name of the provider to get. If None, use the default provider.
            
        Returns:
            ModelProvider instance.
            
        Raises:
            ValueError: If the provider is not available.
        """
        # Use the default provider if not specified
        if provider_name is None:
            if self._default_provider is None:
                # Try to find a suitable default
                available = self.discover()
                if "anthropic" in available:
                    provider_name = "anthropic"
                elif "openai" in available:
                    provider_name = "openai"
                elif available:
                    provider_name = next(iter(available))
                else:
                    raise ValueError("No default provider available")
            else:
                provider_name = self._default_provider
        
        # Check if the provider is already created
        if provider_name in self._providers:
            return self._providers[provider_name]
        
        # Create the provider
        return self.create(provider_name)
    
    def set_default(self, provider_name: str) -> None:
        """Set the default provider.
        
        Args:
            provider_name: Name of the provider to set as default.
            
        Raises:
            ValueError: If the provider is not available.
        """
        # Check if the provider is available
        available = self.discover()
        if provider_name not in available:
            raise ValueError(f"Provider '{provider_name}' is not available")
        
        self._default_provider = provider_name