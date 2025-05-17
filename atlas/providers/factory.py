"""
Factory for creating model providers.

This module provides functions for discovering, creating, and managing
model providers in a unified way.
"""

import importlib
import logging
import threading
from typing import Dict, List, Optional, Any, Type, Tuple, Callable, Set, Union

from atlas.core.telemetry import traced, TracedClass
from atlas.core import env
from atlas.providers.base import ModelProvider
from atlas.providers.options import ProviderOptions
from atlas.providers.capabilities import CapabilityStrength

logger = logging.getLogger(__name__)

# Registry of provider implementations
_PROVIDER_REGISTRY: Dict[str, str] = {
    "anthropic": "atlas.providers.implementations.anthropic.AnthropicProvider",
    "openai": "atlas.providers.implementations.openai.OpenAIProvider",
    "ollama": "atlas.providers.implementations.ollama.OllamaProvider",
    "mock": "atlas.providers.implementations.mock.MockProvider",
}

# Provider model configuration - centralized model information
PROVIDER_MODELS = {
    "anthropic": {
        "default": "claude-3-7-sonnet-20250219",
        "inexpensive": "claude-3-haiku-20240307",
        "efficient": "claude-3-haiku-20240307",
        "premium": "claude-3-opus-20240229",
        "vision": "claude-3-7-sonnet-20250219",
        "models": {
            # Latest models
            "claude-3-7-sonnet-20250219": ["premium", "vision", "standard"],
            "claude-3-5-sonnet-20240620": ["premium", "vision", "standard"],
            "claude-3-5-haiku-20240620": ["efficient", "standard"],
            "claude-3-opus-20240229": ["premium", "vision", "standard"],
            # Legacy models
            "claude-3-sonnet-20240229": ["premium", "vision", "standard"],
            "claude-3-haiku-20240307": ["inexpensive", "efficient", "standard"],
        },
        "identifiers": ["claude", "sonnet", "opus", "haiku"],
        "pricing_category": "premium"
    },
    "openai": {
        "default": "gpt-4o",
        "inexpensive": "gpt-3.5-turbo",
        "efficient": "gpt-3.5-turbo",
        "premium": "gpt-4o",
        "vision": "gpt-4o",
        "models": {
            # Latest models
            "gpt-4.1": ["premium", "vision", "standard"],
            "gpt-4.1-mini": ["standard"],
            "gpt-4.1-nano": ["efficient", "inexpensive", "standard"],
            # o-series
            "o3": ["premium", "standard"],
            "o4-mini": ["standard"],
            # GPT-4o series
            "gpt-4o": ["premium", "vision", "standard"],
            "gpt-4o-mini": ["standard"],
            # Legacy models
            "gpt-4-turbo": ["premium", "vision", "standard"],
            "gpt-4": ["premium", "standard"],
            "gpt-3.5-turbo": ["inexpensive", "efficient", "standard"],
        },
        "identifiers": ["gpt-", "text-", "o", "ft:", "dall-e"],
        "pricing_category": "standard"
    },
    "ollama": {
        "default": "llama3",
        "inexpensive": "llama3",
        "efficient": "llama3",
        "premium": "llama3",
        "vision": "llava",
        "models": {
            "llama3": ["inexpensive", "efficient", "standard"],
            "mistral": ["inexpensive", "efficient", "standard"],
            "gemma": ["inexpensive", "efficient", "standard"],
            "phi": ["inexpensive", "efficient", "standard"],
            "mamba": ["efficient", "standard"],
            "yarn-mistral": ["standard"],
            "codellama": ["standard"],
            "openchat": ["standard"],
            "wizard-math": ["standard"],
            "llava": ["vision", "standard"],
            "qwen": ["standard"],
        },
        "identifiers": ["llama", "mistral", "gemma", "phi", "mamba", "yarn", "code", "chat", "wizard", "llava", "qwen"],
        "pricing_category": "free"
    },
    "mock": {
        "default": "mock-standard",
        "inexpensive": "mock-basic",
        "efficient": "mock-basic",
        "premium": "mock-advanced",
        "vision": "mock-advanced",
        "models": {
            "mock-standard": ["standard"],
            "mock-basic": ["inexpensive", "efficient", "standard"],
            "mock-advanced": ["premium", "vision", "standard"],
        },
        "identifiers": ["mock"],
        "pricing_category": "free"
    }
}

# Default models by provider - extracted for backward compatibility
_DEFAULT_MODELS: Dict[str, str] = {
    provider: config["default"] for provider, config in PROVIDER_MODELS.items()
}

# Default capability to use when none is specified
DEFAULT_CAPABILITY = "inexpensive"

# Cache for provider availability
_AVAILABLE_PROVIDERS: Optional[Dict[str, List[str]]] = None

# Global provider registry instance
_PROVIDER_REGISTRY_INSTANCE = None
_REGISTRY_LOCK = threading.RLock()


def get_provider_registry():
    """Get the global provider registry instance.
    
    Returns:
        The global provider registry instance.
    """
    # Import here to avoid circular imports
    from atlas.providers.registry import get_registry
    return get_registry()


def is_model_compatible_with_provider(model_name: str, provider_name: str) -> bool:
    """Check if a model is compatible with a provider.

    Args:
        model_name: The name of the model to check.
        provider_name: The name of the provider.

    Returns:
        True if the model is compatible with the provider, False otherwise.
    """
    if not model_name:
        return True  # No model specified means default model is compatible

    # Check if provider exists
    if provider_name not in PROVIDER_MODELS:
        return False

    # Handle special case for mock models explicitly
    if provider_name == "mock" and "mock" in model_name.lower():
        return True

    # Handle special case where provider was manually specified with a mock model
    if "mock" in model_name.lower() and provider_name != "mock":
        return False  # Mock models only work with mock provider

    # Special case for Ollama: all models with a colon are assumed to be valid
    # This allows for custom models like "qwq:32b" or "llama2:latest"
    if provider_name == "ollama" and ":" in model_name:
        return True

    # Check if model is in provider's model list
    if model_name in PROVIDER_MODELS[provider_name]["models"]:
        return True

    # Check if model contains a known identifier for this provider
    for identifier in PROVIDER_MODELS[provider_name]["identifiers"]:
        if model_name.lower().startswith(identifier) or identifier in model_name.lower():
            return True

    # Unknown model for this provider
    return False


def detect_model_provider(model_name: str) -> Optional[str]:
    """Detect which provider a model belongs to.

    Args:
        model_name: The name of the model to check.

    Returns:
        The name of the provider if detected, None otherwise.
    """
    if not model_name:
        return None

    # Handle special case for mock models explicitly
    if "mock" in model_name.lower():
        return "mock"

    # Direct check for common patterns
    model_lower = model_name.lower()
    if any(id in model_lower for id in ["gpt", "text-", "o1", "o2", "o3", "o4"]):
        return "openai"
    elif any(id in model_lower for id in ["claude", "opus", "sonnet", "haiku"]):
        return "anthropic"
    elif any(id in model_lower for id in ["llama", "mistral", "gemma", "phi"]):
        return "ollama"

    # Check each provider's identifiers and models
    for provider_name, config in PROVIDER_MODELS.items():
        # Direct match with known models
        if model_name in config["models"]:
            return provider_name

        # Check identifiers
        for identifier in config["identifiers"]:
            if model_name.lower().startswith(identifier) or identifier in model_name.lower():
                return provider_name

    # Unknown model
    return None


def get_model_capabilities(provider_name: str, model_name: str) -> List[str]:
    """Get the capabilities of a model.

    Args:
        provider_name: The name of the provider.
        model_name: The name of the model.

    Returns:
        A list of capabilities supported by the model.
    """
    if provider_name in PROVIDER_MODELS and model_name in PROVIDER_MODELS[provider_name]["models"]:
        return PROVIDER_MODELS[provider_name]["models"][model_name]
    return []


def get_model_by_capability(provider_name: str, capability: str = DEFAULT_CAPABILITY) -> str:
    """Get a model with a specific capability for a provider.

    Args:
        provider_name: The name of the provider.
        capability: The required capability.

    Returns:
        The name of a model with the requested capability, or the default model if none found.
    """
    logger.debug(f"Selecting model for {provider_name} with capability: {capability}")

    if provider_name in PROVIDER_MODELS:
        # First check if there's a direct capability mapping
        if capability in PROVIDER_MODELS[provider_name]:
            selected_model = PROVIDER_MODELS[provider_name][capability]
            logger.debug(f"Found direct capability mapping for {capability}: {selected_model}")
            return selected_model

        # Otherwise, look for a model with the capability
        for model_name, capabilities in PROVIDER_MODELS[provider_name]["models"].items():
            if capability in capabilities:
                logger.debug(f"Found model {model_name} with capability {capability}")
                return model_name

        # Fall back to default model if capability not found
        logger.debug(f"No model found for capability {capability}, using default: {PROVIDER_MODELS[provider_name]['default']}")
        return PROVIDER_MODELS[provider_name]["default"]

    # Provider not found, return empty string (will be caught later)
    logger.error(f"Provider {provider_name} not found in provider models configuration")
    return ""


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
        providers["anthropic"] = list(PROVIDER_MODELS["anthropic"]["models"].keys())
        logger.debug("Discovered Anthropic provider with API key")

    # Check for OpenAI
    if available_providers.get("openai", False):
        providers["openai"] = list(PROVIDER_MODELS["openai"]["models"].keys())
        logger.debug("Discovered OpenAI provider with API key")

    # Check for Ollama
    if available_providers.get("ollama", False):
        try:
            import requests

            # Get API endpoint from environment or fall back to default
            api_endpoint = env.get_provider_endpoint("ollama") or "http://localhost:11434/api"

            # Get connect timeout from environment with default
            connect_timeout = env.get_provider_timeout("ollama", "connect") or 2

            # Verify Ollama is running with appropriate timeout
            try:
                response = requests.get(f"{api_endpoint}/version", timeout=connect_timeout)
                if response.status_code == 200:
                    # Try to get actual models
                    try:
                        models_response = requests.get(
                            f"{api_endpoint}/tags", timeout=connect_timeout
                        )
                        if models_response.status_code == 200:
                            data = models_response.json()
                            ollama_models = [
                                model["name"] for model in data.get("models", [])
                            ]
                            if ollama_models:
                                providers["ollama"] = ollama_models
                                logger.debug(
                                    f"Discovered Ollama provider with {len(ollama_models)} models: "
                                    f"{', '.join(ollama_models[:5])}" +
                                    (f" and {len(ollama_models) - 5} more" if len(ollama_models) > 5 else "")
                                )
                            else:
                                # Only use hardcoded models if no models are found from API
                                # This allows new/custom models to appear in discovery
                                providers["ollama"] = list(PROVIDER_MODELS["ollama"]["models"].keys())
                                logger.warning("Ollama server returned no models, using known models as fallback")
                        else:
                            # Fall back to known models if the models endpoint fails
                            providers["ollama"] = list(PROVIDER_MODELS["ollama"]["models"].keys())
                            logger.warning(
                                f"Failed to get models from Ollama API (status code {models_response.status_code}), "
                                f"using known models as fallback"
                            )
                    except Exception as model_error:
                        # Fall back to known models if the models endpoint raises an exception
                        providers["ollama"] = list(PROVIDER_MODELS["ollama"]["models"].keys())
                        logger.warning(
                            f"Error getting models from Ollama API: {model_error}, "
                            f"using known models as fallback"
                        )
                else:
                    logger.warning(f"Ollama server not responsive: status code {response.status_code}")
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Unable to connect to Ollama server at {api_endpoint}: {e}")
            except requests.exceptions.Timeout as e:
                logger.warning(f"Timeout connecting to Ollama server at {api_endpoint}: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error checking Ollama availability: {e}")
        except ImportError as e:
            logger.warning(f"Requests package not available for Ollama discovery: {e}")
        except Exception as e:
            # Catch-all for unexpected exceptions
            logger.warning(f"Ollama provider discovery failed: {e}")

    # Always include the mock provider, which doesn't need any API key
    providers["mock"] = list(PROVIDER_MODELS["mock"]["models"].keys())
    logger.debug("Added mock provider for testing without API access")

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
    logger.debug(
        f"Registered provider '{provider_name}' with class path '{class_path}'"
    )

    # Invalidate the provider cache
    global _AVAILABLE_PROVIDERS
    _AVAILABLE_PROVIDERS = None
    
    # Register with the registry if it's initialized
    try:
        registry = get_provider_registry()
        provider_class = get_provider_class(provider_name)
        registry.register_provider(
            name=provider_name,
            provider_class=provider_class
        )
        logger.debug(f"Registered provider '{provider_name}' with provider registry")
    except Exception as e:
        logger.debug(f"Could not register with provider registry: {e}")


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
    capability: Optional[str] = None,
    max_tokens: Optional[int] = None,
    **kwargs: Any,
) -> ModelProvider:
    """Create a model provider instance.

    Args:
        provider_name: Name of the provider to create (if None, use environment default).
        model_name: Name of the model to use (if None, use capability or provider default).
        capability: Model capability to use (if model_name is None).
        max_tokens: Maximum tokens for model generation (if None, use environment default).
        **kwargs: Additional provider-specific parameters.

    Returns:
        ModelProvider instance.

    Raises:
        ValueError: If the provider is not supported or required configuration is missing.
    """
    # First check if we should use the registry
    try:
        registry = get_provider_registry()
        if registry:
            # Try to use registry for provider creation
            if model_name:
                # Create by specific model name
                return registry.create_provider(
                    provider_name=provider_name,
                    model_name=model_name,
                    max_tokens=max_tokens,
                    **kwargs
                )
            elif capability:
                # Create by capability
                capabilities = {capability: CapabilityStrength.MODERATE}
                return registry.create_provider(
                    provider_name=provider_name,
                    capabilities=capabilities,
                    max_tokens=max_tokens,
                    **kwargs
                )
            elif provider_name:
                # Create by provider name only
                return registry.create_provider(
                    provider_name=provider_name,
                    max_tokens=max_tokens,
                    **kwargs
                )
    except Exception as e:
        logger.warning(f"Registry-based provider creation failed, falling back to direct creation: {e}")

    # Fall back to legacy direct provider creation
    
    # Handle auto-detecting provider from model (if model is specified but provider isn't)
    if model_name is not None and provider_name is None:
        # Try to detect provider from model name
        detected_provider = detect_model_provider(model_name)
        if detected_provider:
            provider_name = detected_provider
            logger.debug(f"Auto-detected provider '{provider_name}' from model '{model_name}'")
        else:
            # Fall back to default provider
            provider_name = env.get_string("ATLAS_DEFAULT_PROVIDER", "anthropic")
            logger.debug(f"Could not detect provider from model '{model_name}', using default: {provider_name}")
    # Get default provider from environment if not specified
    elif provider_name is None:
        provider_name = env.get_string("ATLAS_DEFAULT_PROVIDER", "anthropic")
        logger.debug(f"Using default provider: {provider_name}")

    # Normalize provider name (ensure it's not None)
    if provider_name is None:
        provider_name = "anthropic"

    provider_name = provider_name.lower()

    # Get the provider class
    provider_class = get_provider_class(provider_name)

    # Get default max_tokens from environment if not specified
    if max_tokens is None:
        max_tokens = env.get_int("ATLAS_MAX_TOKENS", 2000)

    # Model selection logic:
    # 1. If model_name is explicitly provided, use it (after validation)
    # 2. If capability is provided, get the appropriate model for that capability
    # 3. Otherwise check environment variables and defaults
    if model_name is None:
        # If the model isn't specified but capability is, use capability-based selection
        if capability is not None:
            # Use capability-based model selection
            model_name = get_model_by_capability(provider_name, capability)
            logger.debug(f"Selected model '{model_name}' based on capability '{capability}'")
        else:
            # Try to get from environment first
            env_model_var = f"ATLAS_{provider_name.upper()}_DEFAULT_MODEL"
            env_model = env.get_string(env_model_var)

            if env_model:
                model_name = env_model
                logger.debug(f"Using model '{model_name}' from environment variable {env_model_var}")
            else:
                # Then check the general default model variable
                general_default = env.get_string("ATLAS_DEFAULT_MODEL")

                # Only use general default if it's compatible with this provider
                if general_default and is_model_compatible_with_provider(general_default, provider_name):
                    model_name = general_default
                    logger.debug(f"Using model '{model_name}' from ATLAS_DEFAULT_MODEL")
                else:
                    # Get the default capability from env or use the predefined default
                    env_capability = env.get_string("ATLAS_DEFAULT_CAPABILITY", DEFAULT_CAPABILITY)
                    model_name = get_model_by_capability(provider_name, env_capability)
                    logger.debug(f"Using {env_capability} model: {model_name}")

    # If model_name is still None at this point, use provider's default model
    if model_name is None or model_name == "":
        model_name = PROVIDER_MODELS[provider_name]["default"]
        logger.debug(f"Using default model for {provider_name}: {model_name}")

    # Handle special case for mock models with non-mock provider (common error)
    if "mock" in model_name.lower() and provider_name != "mock":
        logger.warning(f"Model '{model_name}' appears to be a mock model but provider is '{provider_name}'.")
        logger.warning(f"Switching provider to 'mock' to match model")
        provider_name = "mock"
        provider_class = get_provider_class("mock")

    # Validate model compatibility with provider (after possible provider adjustment)
    if not is_model_compatible_with_provider(model_name, provider_name):
        # Model was explicitly provided but isn't compatible with the provider
        # Detect which provider this model likely belongs to
        likely_provider = detect_model_provider(model_name)
        provider_models = list(PROVIDER_MODELS[provider_name]["models"].keys())[:3]

        if likely_provider and likely_provider != provider_name:
            # We know which provider this model belongs to
            raise ValueError(
                f"Model '{model_name}' is not compatible with the {provider_name} provider. "
                f"It appears to be a {likely_provider} model. "
                f"Available {provider_name} models include: {', '.join(provider_models)}..."
            )
        else:
            # We don't recognize this model for any provider
            raise ValueError(
                f"Model '{model_name}' is not recognized as compatible with the {provider_name} provider. "
                f"Available {provider_name} models include: {', '.join(provider_models)}..."
            )

    # Create provider instance
    try:
        # Process and validate provider options
        provider_options = kwargs.pop("options", {}) or {}
        
        # Extract capabilities from the model configuration
        model_capabilities = {}
        if provider_name in PROVIDER_MODELS:
            model_info = PROVIDER_MODELS[provider_name]["models"].get(model_name, [])
            for capability in model_info:
                # Set reasonable strength levels based on capability type
                if capability in ["premium", "vision"]:
                    strength = CapabilityStrength.STRONG
                elif capability in ["efficient"]:
                    strength = CapabilityStrength.MODERATE
                elif capability in ["inexpensive"]:
                    strength = CapabilityStrength.BASIC
                else:
                    strength = CapabilityStrength.MODERATE
                
                model_capabilities[capability] = strength
        
        # Add capabilities to provider options
        if model_capabilities and "capabilities" not in provider_options:
            provider_options["capabilities"] = model_capabilities
            
        # Construct provider kwargs
        provider_kwargs = {
            "model_name": model_name,
            "max_tokens": max_tokens,
            "options": provider_options,
            **kwargs,
        }

        # Validate provider options using schema validation
        try:
            # Import here to avoid circular imports
            from atlas.schemas.options import PROVIDER_OPTIONS_SCHEMAS
            
            # Validate options with the appropriate schema
            options_schema = PROVIDER_OPTIONS_SCHEMAS.get(
                provider_name, 
                PROVIDER_OPTIONS_SCHEMAS["default"]
            )
            
            # If options exist and are not empty, validate them
            if provider_options:
                provider_options = options_schema.load(provider_options)
                provider_kwargs["options"] = provider_options
                
        except ImportError:
            # Schema validation module not available, log warning but continue
            logger.warning("Schema validation module not available, skipping options validation")
        except Exception as e:
            # Log validation error but continue (will be caught by provider constructor)
            logger.warning(f"Provider options validation failed: {e}")
            
        # Create the provider with validated arguments
        provider = provider_class(**provider_kwargs)
        logger.debug(f"Created provider '{provider_name}' with model '{model_name}'")
        
        # Register model capabilities with registry if available
        try:
            registry = get_provider_registry()
            if registry and provider_name in PROVIDER_MODELS:
                model_info = PROVIDER_MODELS[provider_name]["models"].get(model_name, [])
                for capability in model_info:
                    if capability in ["premium", "vision"]:
                        strength = CapabilityStrength.STRONG
                    elif capability in ["efficient"]:
                        strength = CapabilityStrength.MODERATE
                    elif capability in ["inexpensive"]:
                        strength = CapabilityStrength.BASIC
                    else:
                        strength = CapabilityStrength.MODERATE
                    
                    registry.register_model_capability(model_name, capability, strength)
        except Exception as e:
            logger.debug(f"Could not register model capabilities: {e}")
        
        return provider

    except Exception as e:
        logger.error(f"Failed to create provider '{provider_name}': {e}")
        raise ValueError(f"Error creating provider '{provider_name}': {e}")


@traced(name="create_provider_group")
def create_provider_group(
    providers: List[Union[str, ModelProvider]],
    selection_strategy: str = "failover",
    name: str = "provider_group",
    **kwargs: Any
) -> ModelProvider:
    """Create a provider group with multiple providers and fallback capability.
    
    Args:
        providers: List of provider names or provider instances
        selection_strategy: Strategy for selecting providers ("failover", "round_robin", "random", "cost_optimized")
        name: Name for the provider group
        **kwargs: Additional parameters for provider creation
        
    Returns:
        ProviderGroup instance
        
    Raises:
        ValueError: If no providers are specified or an invalid selection strategy is provided
    """
    from atlas.providers.group import ProviderGroup, ProviderSelectionStrategy, TaskAwareSelectionStrategy
    
    if not providers:
        raise ValueError("At least one provider must be specified")
    
    # Convert provider names to provider instances if needed
    provider_instances = []
    
    for provider in providers:
        if isinstance(provider, str):
            # Create provider instance from name
            provider_instances.append(create_provider(provider_name=provider, **kwargs))
        else:
            # Already a provider instance
            provider_instances.append(provider)
    
    # Get the selection strategy function
    strategy_function = None
    
    if selection_strategy == "failover":
        strategy_function = ProviderSelectionStrategy.failover
    elif selection_strategy == "round_robin":
        strategy_function = ProviderSelectionStrategy.round_robin
    elif selection_strategy == "random":
        strategy_function = ProviderSelectionStrategy.random
    elif selection_strategy == "cost_optimized":
        strategy_function = ProviderSelectionStrategy.cost_optimized
    elif selection_strategy == "task_aware":
        strategy_function = TaskAwareSelectionStrategy.select
    else:
        raise ValueError(f"Invalid selection strategy: {selection_strategy}")
    
    # Create provider group
    return ProviderGroup(
        providers=provider_instances,
        selection_strategy=strategy_function,
        name=name
    )


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
def validate_api_keys(
    providers: Optional[List[str]] = None, skip_validation: bool = False
) -> Dict[str, Dict[str, Any]]:
    """Validate API keys for specified providers.

    This function creates and validates provider instances for the specified providers.

    Args:
        providers: List of provider names to validate. If None, validates all available providers.
        skip_validation: If True, skips actual API calls and only checks if keys are present.
                        This is useful for quick validation and performance reasons.

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

    for provider_name in providers:
        # Skip if provider not in registry
        if provider_name not in _PROVIDER_REGISTRY:
            results[provider_name] = {
                "valid": False,
                "provider": provider_name,
                "key_present": False,
                "error": f"Unsupported provider: {provider_name}",
            }
            continue

        # For the mock provider, validation always succeeds
        if provider_name == "mock":
            results[provider_name] = {
                "valid": True,
                "provider": provider_name,
                "key_present": True,
                "error": None,
            }
            continue

        try:
            if skip_validation:
                # Just check if the key exists without making API calls
                api_key = env.get_api_key(provider_name)
                results[provider_name] = {
                    "valid": bool(api_key),
                    "provider": provider_name,
                    "key_present": bool(api_key),
                    "error": (
                        None if api_key else f"No API key found for {provider_name}"
                    ),
                }
            else:
                # Try to create the provider - this will validate the API key
                try:
                    provider = create_provider(provider_name=provider_name)

                    # Validate the API key
                    validation_result = provider.validate_api_key_detailed()
                    results[provider_name] = validation_result
                except Exception as e:
                    # Handle provider creation/validation errors
                    results[provider_name] = {
                        "valid": False,
                        "provider": provider_name,
                        "key_present": False,
                        "error": str(e),
                    }
        except Exception as e:
            # Handle any other errors
            results[provider_name] = {
                "valid": False,
                "provider": provider_name,
                "key_present": False,
                "error": str(e),
            }

    return results


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
        capability: Optional[str] = None,
        max_tokens: int = 2000,
        **kwargs: Any,
    ) -> ModelProvider:
        """Create a provider instance.

        Args:
            provider_name: Name of the provider to create.
            model_name: Name of the model to use (if None, use provider default).
            capability: Capability to use for model selection.
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
            capability=capability,
            max_tokens=max_tokens,
            **kwargs,
        )

        # Store the provider in the cache
        self._providers[provider_name] = provider

        # Set as default if no default is set
        if self._default_provider is None:
            self._default_provider = provider_name

        return provider
        
    def create_group(
        self,
        providers: List[str],
        selection_strategy: str = "failover",
        name: str = "provider_group",
        **kwargs: Any
    ) -> ModelProvider:
        """Create a provider group.
        
        Args:
            providers: List of provider names to include in the group
            selection_strategy: Strategy for provider selection
            name: Name for the provider group
            **kwargs: Additional provider creation parameters
            
        Returns:
            ProviderGroup instance
        """
        # Create provider instances for each name
        provider_instances = []
        for provider_name in providers:
            # Check if provider is already created
            if provider_name in self._providers:
                provider_instances.append(self._providers[provider_name])
            else:
                # Create new provider
                provider = self.create(provider_name, **kwargs)
                provider_instances.append(provider)
        
        # Create provider group
        group = create_provider_group(
            providers=provider_instances,
            selection_strategy=selection_strategy,
            name=name
        )
        
        # Store in cache under the group name
        self._providers[name] = group
        
        return group

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