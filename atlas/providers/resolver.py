"""
Provider resolution and creation module.

This module provides functionality for resolving provider options with auto-detection
and creating provider instances from resolved options.
"""

import copy
import logging
from typing import Optional

from atlas.core import env
from atlas.providers.factory import (
    create_provider, 
    detect_model_provider, 
    get_model_by_capability,
    is_model_compatible_with_provider
)
from atlas.providers.base import ModelProvider
from atlas.providers.options import ProviderOptions

logger = logging.getLogger(__name__)


def resolve_provider_options(options: ProviderOptions) -> ProviderOptions:
    """Resolve provider options by filling in missing details with auto-detection.
    
    This function takes incomplete ProviderOptions and enhances them with
    auto-detection, environment defaults, and capability-based selection.
    
    Args:
        options: Original provider options, potentially incomplete
        
    Returns:
        Resolved options with all fields filled in appropriately
    """
    # Create a copy to avoid modifying the input
    resolved = copy.deepcopy(options)
    
    # Auto-detect provider from model name if needed
    if resolved.model_name and not resolved.provider_name:
        detected_provider = detect_model_provider(resolved.model_name)
        if detected_provider:
            resolved.provider_name = detected_provider
            logger.debug(f"Auto-detected provider '{detected_provider}' from model '{resolved.model_name}'")
    
    # Apply provider name from environment if not specified
    if not resolved.provider_name:
        resolved.provider_name = env.get_string("ATLAS_DEFAULT_PROVIDER", "anthropic")
        logger.debug(f"Using default provider '{resolved.provider_name}' from environment")
    
    # Handle special case for mock models with non-mock provider
    if resolved.model_name and "mock" in resolved.model_name.lower() and resolved.provider_name != "mock":
        logger.warning(f"Auto-correcting provider from {resolved.provider_name} to 'mock' based on mock model name")
        resolved.provider_name = "mock"
    
    # The most important check happens first: if we have BOTH provider_name and capability
    # but no model_name, use the capability to select the model BEFORE trying any defaults
    if resolved.provider_name and resolved.capability and not resolved.model_name:
        # Use capability-based model selection for the SPECIFIC provider
        resolved.model_name = get_model_by_capability(resolved.provider_name, resolved.capability)
        logger.debug(f"Selected model '{resolved.model_name}' for provider '{resolved.provider_name}' based on capability '{resolved.capability}'")

    # Apply environment-based default model if STILL needed
    if not resolved.model_name:
        # Try provider-specific default model
        if resolved.provider_name:  # Only try if we have a provider
            env_var = f"ATLAS_{resolved.provider_name.upper()}_DEFAULT_MODEL"
            env_model = env.get_string(env_var)
            if env_model:
                resolved.model_name = env_model
                logger.debug(f"Using provider-specific default model '{resolved.model_name}' from env")

        # Fall back to generic default model, BUT ONLY if compatible with provider
        if not resolved.model_name:
            env_model = env.get_string("ATLAS_DEFAULT_MODEL")
            if env_model and (not resolved.provider_name or is_model_compatible_with_provider(env_model, resolved.provider_name)):
                resolved.model_name = env_model
                logger.debug(f"Using general default model '{resolved.model_name}' from env")

        # Ultimate fallback to capability-based selection
        if not resolved.model_name and resolved.provider_name:
            capability = resolved.capability or env.get_string("ATLAS_DEFAULT_CAPABILITY", "inexpensive")
            model = get_model_by_capability(resolved.provider_name, capability)
            resolved.model_name = model
            logger.debug(f"Selected model '{resolved.model_name}' based on capability '{capability}'")
    
    # Apply default max_tokens if not specified
    if not resolved.max_tokens:
        resolved.max_tokens = env.get_int("ATLAS_MAX_TOKENS", 2000)
    
    # Apply default base_url for Ollama if not specified
    if resolved.provider_name == "ollama" and not resolved.base_url:
        resolved.base_url = env.get_string("ATLAS_OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Log the resolution result
    logger.debug(f"Resolved provider options: {resolved.to_dict()}")
    
    return resolved


def create_provider_from_options(options: ProviderOptions) -> ModelProvider:
    """Create a provider instance from ProviderOptions.
    
    This function resolves the ProviderOptions and creates a provider instance
    using the resolved options.
    
    Args:
        options: Provider options (will be resolved automatically)
        
    Returns:
        Initialized ModelProvider instance
        
    Raises:
        ValueError: If the options can't be resolved or provider creation fails
    """
    # Resolve the options first
    resolved = resolve_provider_options(options)
    
    # Extract kwargs for provider creation
    kwargs = {}
    
    # Add base_url if present
    if resolved.base_url:
        kwargs["base_url"] = resolved.base_url
    
    # Add any extra parameters
    if resolved.extra_params:
        kwargs.update(resolved.extra_params)
    
    # Create and return the provider
    return create_provider(
        provider_name=resolved.provider_name,
        model_name=resolved.model_name,
        max_tokens=resolved.max_tokens,
        **kwargs
    )