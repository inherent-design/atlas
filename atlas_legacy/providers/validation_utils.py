"""
Provider-specific validation utilities for Atlas.

This module provides validation functions specifically for
different provider types (Anthropic, OpenAI, Ollama) to ensure
proper configuration and option validation.
"""

import functools
import logging
from collections.abc import Callable
from typing import Any, TypeVar, cast

from marshmallow import ValidationError

from atlas.providers.errors import ProviderValidationError
from atlas.providers.validation import validate_options
from atlas.schemas.options import (
    anthropic_options_schema,
    ollama_options_schema,
    openai_options_schema,
    provider_options_schema,
)

# Type variables
F = TypeVar("F", bound=Callable[..., Any])
T = TypeVar("T")

logger = logging.getLogger(__name__)


def validate_anthropic_options(func: F) -> F:
    """Decorator to validate Anthropic-specific provider options.

    This decorator ensures that options passed to Anthropic provider methods
    are properly validated using the Anthropic options schema.

    Args:
        func: The function to decorate.

    Returns:
        The decorated function.

    Example:
        ```python
        @validate_anthropic_options
        def __init__(self, options: Optional[Dict[str, Any]] = None, **kwargs):
            # options is guaranteed to be valid for Anthropic
            ...
        ```
    """

    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        # Check if options are passed
        if kwargs.get("options"):
            try:
                # Validate options using Anthropic schema
                validated_options = anthropic_options_schema.load(kwargs["options"])
                kwargs["options"] = validated_options
            except ValidationError as e:
                provider_name = getattr(self, "name", "anthropic")
                raise ProviderValidationError(
                    f"Invalid options for Anthropic provider: {e.messages}",
                    provider=provider_name,
                    details={"validation_errors": e.messages},
                )

        # Call the original function
        return func(self, *args, **kwargs)

    return cast(F, wrapper)


def validate_openai_options(func: F) -> F:
    """Decorator to validate OpenAI-specific provider options.

    This decorator ensures that options passed to OpenAI provider methods
    are properly validated using the OpenAI options schema.

    Args:
        func: The function to decorate.

    Returns:
        The decorated function.

    Example:
        ```python
        @validate_openai_options
        def __init__(self, options: Optional[Dict[str, Any]] = None, **kwargs):
            # options is guaranteed to be valid for OpenAI
            ...
        ```
    """

    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        # Check if options are passed
        if kwargs.get("options"):
            try:
                # Validate options using OpenAI schema
                validated_options = openai_options_schema.load(kwargs["options"])
                kwargs["options"] = validated_options

                # Additional OpenAI-specific validation
                if "functions" in validated_options and "tools" in validated_options:
                    raise ProviderValidationError(
                        "OpenAI provider cannot use both functions and tools simultaneously",
                        provider="openai",
                        details={"error": "functions and tools are mutually exclusive"},
                    )
            except ValidationError as e:
                provider_name = getattr(self, "name", "openai")
                raise ProviderValidationError(
                    f"Invalid options for OpenAI provider: {e.messages}",
                    provider=provider_name,
                    details={"validation_errors": e.messages},
                )

        # Call the original function
        return func(self, *args, **kwargs)

    return cast(F, wrapper)


def validate_ollama_options(func: F) -> F:
    """Decorator to validate Ollama-specific provider options.

    This decorator ensures that options passed to Ollama provider methods
    are properly validated using the Ollama options schema.

    Args:
        func: The function to decorate.

    Returns:
        The decorated function.

    Example:
        ```python
        @validate_ollama_options
        def __init__(self, options: Optional[Dict[str, Any]] = None, **kwargs):
            # options is guaranteed to be valid for Ollama
            ...
        ```
    """

    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        # Check if options are passed
        if kwargs.get("options"):
            try:
                # Validate options using Ollama schema
                validated_options = ollama_options_schema.load(kwargs["options"])
                kwargs["options"] = validated_options

                # Additional Ollama-specific validation
                if "functions" in validated_options or "tools" in validated_options:
                    raise ProviderValidationError(
                        "Ollama provider does not support functions or tools",
                        provider="ollama",
                        details={"error": "unsupported options: functions, tools"},
                    )
            except ValidationError as e:
                provider_name = getattr(self, "name", "ollama")
                raise ProviderValidationError(
                    f"Invalid options for Ollama provider: {e.messages}",
                    provider=provider_name,
                    details={"validation_errors": e.messages},
                )

        # Call the original function
        return func(self, *args, **kwargs)

    return cast(F, wrapper)


def validate_provider_options(provider_type: str) -> Callable[[F], F]:
    """Factory to create provider-specific option validation decorators.

    This factory function returns a decorator that validates options
    according to the specified provider type.

    Args:
        provider_type: The type of provider ('anthropic', 'openai', 'ollama').

    Returns:
        A decorator function for the specified provider type.

    Example:
        ```python
        @validate_provider_options('anthropic')
        def configure(self, options: Dict[str, Any]) -> None:
            # options is guaranteed to be valid for the specified provider type
            ...
        ```
    """
    # Map provider types to their schema validators
    validators = {
        "anthropic": validate_anthropic_options,
        "openai": validate_openai_options,
        "ollama": validate_ollama_options,
    }

    # Return the appropriate validator or a generic one
    return validators.get(provider_type.lower(), validate_options(provider_options_schema))


def validate_model_compatibility(
    provider_type: str,
    allowed_models: list[str] | None = None,
    disallowed_models: list[str] | None = None,
    required_capabilities: dict[str, int] | None = None,
) -> Callable[[F], F]:
    """Decorator factory to validate model compatibility with a provider.

    This decorator ensures that the model requested is compatible with
    the provider and has the required capabilities.

    Args:
        provider_type: The type of provider ('anthropic', 'openai', 'ollama').
        allowed_models: Optional list of allowed model names.
        disallowed_models: Optional list of disallowed model names.
        required_capabilities: Optional dict of capability names to minimum levels.

    Returns:
        Decorator function.

    Example:
        ```python
        @validate_model_compatibility(
            provider_type='openai',
            allowed_models=['gpt-4', 'gpt-3.5-turbo'],
            required_capabilities={'streaming': 2}
        )
        def generate(self, request: ModelRequest) -> ModelResponse:
            # Model is guaranteed to be compatible
            ...
        ```
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Get the model name from the instance or request
            model_name = None

            # First check kwargs
            if "model_name" in kwargs:
                model_name = kwargs["model_name"]
            elif "model" in kwargs:
                model_name = kwargs["model"]
            elif args and len(args) > 0 and hasattr(args[0], "model"):
                # Check if first arg is a request with model
                model_name = args[0].model
            else:
                # Finally check instance attributes
                model_name = getattr(self, "model_name", None)

            if model_name:
                # Check allowed models
                if allowed_models and model_name not in allowed_models:
                    provider_name = getattr(self, "name", provider_type)
                    allowed_str = ", ".join(allowed_models)
                    raise ProviderValidationError(
                        f"Model {model_name} is not supported by {provider_name} provider. Allowed models: {allowed_str}",
                        provider=provider_name,
                        details={"allowed_models": allowed_models, "requested_model": model_name},
                    )

                # Check disallowed models
                if disallowed_models and model_name in disallowed_models:
                    provider_name = getattr(self, "name", provider_type)
                    raise ProviderValidationError(
                        f"Model {model_name} is not supported by {provider_name} provider",
                        provider=provider_name,
                        details={
                            "disallowed_models": disallowed_models,
                            "requested_model": model_name,
                        },
                    )

                # Check required capabilities
                if required_capabilities and hasattr(self, "get_capability_strength"):
                    missing_capabilities = {}
                    for capability, min_level in required_capabilities.items():
                        actual_level = self.get_capability_strength(capability)
                        if actual_level < min_level:
                            missing_capabilities[capability] = {
                                "required": min_level,
                                "actual": actual_level,
                            }

                    if missing_capabilities:
                        provider_name = getattr(self, "name", provider_type)
                        raise ProviderValidationError(
                            f"Model {model_name} does not meet capability requirements for {provider_name} provider",
                            provider=provider_name,
                            details={"missing_capabilities": missing_capabilities},
                        )

            # Call the original function
            return func(self, *args, **kwargs)

        return cast(F, wrapper)

    return decorator


def validate_provider_features(
    provider_type: str,
    required_features: list[str] | None = None,
    optional_features: list[str] | None = None,
    unsupported_features: list[str] | None = None,
) -> Callable[[F], F]:
    """Decorator factory to validate provider feature compatibility.

    This decorator ensures that a provider supports the required features
    and doesn't use unsupported features.

    Args:
        provider_type: The type of provider ('anthropic', 'openai', 'ollama').
        required_features: Optional list of required feature names.
        optional_features: Optional list of optional feature names.
        unsupported_features: Optional list of unsupported feature names.

    Returns:
        Decorator function.

    Example:
        ```python
        @validate_provider_features(
            provider_type='anthropic',
            required_features=['streaming'],
            unsupported_features=['functions', 'tools']
        )
        def configure(self, features: Dict[str, Any]) -> None:
            # Features are guaranteed to be compatible
            ...
        ```
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Get features from kwargs or options
            features = {}
            if "features" in kwargs:
                features = kwargs["features"]
            elif kwargs.get("options"):
                features = kwargs["options"]

            if features:
                # Check required features
                if required_features:
                    missing_features = [f for f in required_features if f not in features]
                    if missing_features:
                        provider_name = getattr(self, "name", provider_type)
                        raise ProviderValidationError(
                            f"Missing required features for {provider_name} provider: {', '.join(missing_features)}",
                            provider=provider_name,
                            details={"missing_features": missing_features},
                        )

                # Check unsupported features
                if unsupported_features:
                    used_unsupported = [f for f in unsupported_features if f in features]
                    if used_unsupported:
                        provider_name = getattr(self, "name", provider_type)
                        raise ProviderValidationError(
                            f"Unsupported features for {provider_name} provider: {', '.join(used_unsupported)}",
                            provider=provider_name,
                            details={"unsupported_features": used_unsupported},
                        )

            # Call the original function
            return func(self, *args, **kwargs)

        return cast(F, wrapper)

    return decorator


# Provider-specific model compatibility validators
validate_anthropic_model = validate_model_compatibility(
    provider_type="anthropic",
    # Default allowed models can be specified here, or left as None to allow any
)

validate_openai_model = validate_model_compatibility(
    provider_type="openai",
    # Default allowed models can be specified here, or left as None to allow any
)

validate_ollama_model = validate_model_compatibility(
    provider_type="ollama",
    # Default allowed models can be specified here, or left as None to allow any
)


# Export all public functions
__all__ = [
    "validate_anthropic_model",
    "validate_anthropic_options",
    "validate_model_compatibility",
    "validate_ollama_model",
    "validate_ollama_options",
    "validate_openai_model",
    "validate_openai_options",
    "validate_provider_features",
    "validate_provider_options",
]
