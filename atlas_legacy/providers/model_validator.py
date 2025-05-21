"""
Model validation utilities for Atlas providers.

This module provides functions to validate model names and settings
for different provider types, ensuring compatibility and proper configuration.
"""

import re

from atlas.providers.errors import ProviderValidationError

# Anthropic model patterns and known models
ANTHROPIC_MODELS = {
    "claude-3-7-sonnet-20250219",
    "claude-3-5-sonnet-20240620",
    "claude-3-5-haiku-20240620",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
    # Legacy models for backward compatibility
    "claude-3",
    "claude-2",
    "claude-instant",
}

# OpenAI model patterns and known models
OPENAI_MODELS = {
    # Current models
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "o3",
    "o4-mini",
    "gpt-4o",
    "gpt-4o-mini",
    # Legacy models
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
}

# Ollama doesn't have a fixed set of models, but we can list common ones
OLLAMA_MODELS = {
    "llama3",
    "llama2",
    "mistral",
    "mixtral",
    "phi",
    "codellama",
    "vicuna",
    "orca",
    "wizard",
}


def validate_anthropic_model(model_name: str) -> tuple[bool, str | None]:
    """Validate that a model name is compatible with Anthropic.

    Args:
        model_name: The model name to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    # Check exact matches first
    if model_name in ANTHROPIC_MODELS:
        return True, None

    # Check if it matches a pattern like claude-3.*
    if model_name.startswith("claude-") and (
        re.match(r"^claude-\d+(\.\d+)?(-\w+)?(-\d+)?$", model_name)
    ):
        return True, None

    # Reject non-Claude models
    if not model_name.startswith("claude-"):
        return (
            False,
            f"Model '{model_name}' is not a valid Claude model. Model names should start with 'claude-'.",
        )

    # Return generic error for other cases
    return False, f"Model '{model_name}' is not a recognized Anthropic model."


def validate_openai_model(model_name: str) -> tuple[bool, str | None]:
    """Validate that a model name is compatible with OpenAI.

    Args:
        model_name: The model name to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    # Check exact matches first
    if model_name in OPENAI_MODELS:
        return True, None

    # Check known prefixes
    valid_prefixes = ["gpt-", "o", "text-", "davinci-"]
    if any(model_name.startswith(prefix) for prefix in valid_prefixes):
        return True, None

    # Custom models with ft- prefix are valid
    if model_name.startswith("ft-"):
        return True, None

    # Return error
    return False, f"Model '{model_name}' is not a recognized OpenAI model."


def validate_ollama_model(model_name: str) -> tuple[bool, str | None]:
    """Validate that a model name is compatible with Ollama.

    Args:
        model_name: The model name to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    # Ollama allows custom model names, so we're lenient
    # We check for common base models but allow any valid name

    # Check if it's a known model or starts with a known prefix
    for known_model in OLLAMA_MODELS:
        if model_name == known_model or model_name.startswith(f"{known_model}:"):
            return True, None

    # Check for invalid characters
    if re.search(r'[\s<>:"|*?]', model_name):
        return False, f"Model '{model_name}' contains invalid characters for Ollama."

    # Since Ollama allows custom model names, we're lenient and accept with a warning
    return True, None


def validate_model_for_provider(model_name: str, provider_type: str) -> tuple[bool, str | None]:
    """Validate that a model name is compatible with a specific provider.

    Args:
        model_name: The model name to validate.
        provider_type: The provider type ('anthropic', 'openai', 'ollama').

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not model_name:
        return False, "Model name cannot be empty"

    # Call the appropriate validator
    validators = {
        "anthropic": validate_anthropic_model,
        "openai": validate_openai_model,
        "ollama": validate_ollama_model,
    }

    validator = validators.get(provider_type.lower())
    if validator:
        return validator(model_name)

    # Unknown provider, return generic validation
    return True, None


def ensure_valid_model(model_name: str, provider_type: str) -> None:
    """Ensure that a model name is valid for a provider, raising an error if not.

    Args:
        model_name: The model name to validate.
        provider_type: The provider type ('anthropic', 'openai', 'ollama').

    Raises:
        ProviderValidationError: If the model is not valid.
    """
    is_valid, error_message = validate_model_for_provider(model_name, provider_type)
    if not is_valid:
        raise ProviderValidationError(
            error_message or f"Invalid model '{model_name}' for provider '{provider_type}'",
            provider=provider_type,
            details={
                "model_name": model_name,
                "provider_type": provider_type,
            },
        )


def get_default_model(provider_type: str) -> str:
    """Get the default model name for a provider type.

    Args:
        provider_type: The provider type ('anthropic', 'openai', 'ollama').

    Returns:
        The default model name.
    """
    defaults = {
        "anthropic": "claude-3-7-sonnet-20250219",
        "openai": "gpt-4.1",
        "ollama": "llama3",
    }

    return defaults.get(provider_type.lower(), "unknown")


def get_model_capabilities(model_name: str, provider_type: str) -> dict[str, int]:
    """Get the capabilities of a specific model.

    Args:
        model_name: The model name.
        provider_type: The provider type ('anthropic', 'openai', 'ollama').

    Returns:
        Dictionary mapping capability names to strength levels (0-4).
    """
    # Define a common capabilities rating system:
    # 0: None/Unavailable
    # 1: Basic
    # 2: Moderate
    # 3: Strong
    # 4: Exceptional

    # For Anthropic
    if provider_type.lower() == "anthropic":
        # Specific model mapping
        if model_name == "claude-3-7-sonnet-20250219":
            return {
                "premium": 3,  # Strong
                "vision": 3,  # Strong
                "standard": 3,  # Strong
                "reasoning": 3,  # Strong
                "code": 3,  # Strong
            }
        elif model_name == "claude-3-opus-20240229":
            return {
                "premium": 4,  # Exceptional
                "vision": 3,  # Strong
                "standard": 3,  # Strong
                "reasoning": 4,  # Exceptional
                "code": 3,  # Strong
                "creative": 3,  # Strong
            }
        elif "haiku" in model_name:
            return {
                "inexpensive": 3,  # Strong
                "efficient": 3,  # Strong
                "standard": 2,  # Moderate
            }
        # Default Anthropic capabilities
        return {
            "premium": 3,  # Strong
            "standard": 3,  # Strong
            "vision": 3,  # Strong
        }

    # For OpenAI
    elif provider_type.lower() == "openai":
        # Specific model mapping
        if model_name == "gpt-4.1":
            return {
                "premium": 3,  # Strong
                "vision": 3,  # Strong
                "standard": 3,  # Strong
                "reasoning": 3,  # Strong
                "code": 4,  # Exceptional
            }
        elif model_name == "o3":
            return {
                "premium": 4,  # Exceptional
                "reasoning": 4,  # Exceptional
                "standard": 3,  # Strong
                "code": 4,  # Exceptional
            }
        elif "3.5" in model_name:
            return {
                "efficient": 3,  # Strong
                "inexpensive": 3,  # Strong
                "standard": 2,  # Moderate
            }
        # Default OpenAI capabilities
        return {
            "premium": 3,  # Strong
            "standard": 3,  # Strong
        }

    # For Ollama
    elif provider_type.lower() == "ollama":
        # Ollama has strong capabilities for local, private operation
        base = {
            "local": 4,  # Exceptional
            "private": 4,  # Exceptional
            "inexpensive": 4,  # Exceptional
        }

        # Specific model adjustments
        if "llama3" in model_name:
            base["standard"] = 2  # Moderate
        elif "mixtral" in model_name:
            base["standard"] = 3  # Strong
        else:
            base["standard"] = 1  # Basic

        return base

    # Default empty capabilities
    return {}


# Export all public functions
__all__ = [
    "ANTHROPIC_MODELS",
    "OLLAMA_MODELS",
    "OPENAI_MODELS",
    "ensure_valid_model",
    "get_default_model",
    "get_model_capabilities",
    "validate_anthropic_model",
    "validate_model_for_provider",
    "validate_ollama_model",
    "validate_openai_model",
]
