"""
Provider validation implementations for Atlas.

This module provides concrete validation implementations for different
provider types, combining schemas, error handling, and provider-specific logic.
"""

import functools
import logging
import inspect
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar, Union, cast

from marshmallow import Schema, ValidationError

from atlas.schemas.options import (
    anthropic_options_schema,
    openai_options_schema,
    ollama_options_schema,
    provider_options_schema,
    provider_config_schema
)
from atlas.providers.errors import ProviderValidationError
from atlas.providers.validation import validate_options, validate_request, validate_response
from atlas.providers.validation_utils import (
    validate_anthropic_options,
    validate_openai_options,
    validate_ollama_options,
    validate_provider_options
)
from atlas.providers.model_validator import (
    ensure_valid_model,
    validate_model_for_provider,
    get_default_model
)


# Type variables for function signatures
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')

logger = logging.getLogger(__name__)


class AnthropicValidator:
    """Validation implementation for Anthropic provider."""
    
    @staticmethod
    def validate_init(func: F) -> F:
        """Validate Anthropic provider initialization parameters.
        
        Args:
            func: The __init__ function to decorate.
            
        Returns:
            The decorated function.
        """
        @functools.wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Validate API key
            api_key = kwargs.get("api_key")
            if not api_key:
                # Check for environment variable in the actual init method
                # This is just a basic check
                pass
            
            # Validate model name
            model_name = kwargs.get("model_name", "claude-3-7-sonnet-20250219")
            try:
                ensure_valid_model(model_name, "anthropic")
            except ProviderValidationError as e:
                # Log and continue since we'll let the init method handle this
                logger.warning(f"Problematic model name: {model_name}, error: {e}")
            
            # Validate options
            if "options" in kwargs and kwargs["options"]:
                validate_anthropic_options(lambda s, o: o)(self, options=kwargs["options"])
            
            # Call the original __init__ method
            return func(self, *args, **kwargs)
        
        return cast(F, wrapper)
    
    @staticmethod
    def validate_generate(func: F) -> F:
        """Validate Anthropic provider generate parameters.
        
        Args:
            func: The generate function to decorate.
            
        Returns:
            The decorated function.
        """
        # Combine our decorator with the built-in request/response validators
        decorated = validate_request(validate_response(func))
        
        @functools.wraps(decorated)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Forward to the decorated function
            return decorated(self, *args, **kwargs)
        
        return cast(F, wrapper)
    
    @staticmethod
    def validate_stream(func: F) -> F:
        """Validate Anthropic provider stream parameters.
        
        Args:
            func: The stream function to decorate.
            
        Returns:
            The decorated function.
        """
        # Use the built-in request validator (not response - streams don't have complete responses)
        decorated = validate_request(func)
        
        @functools.wraps(decorated)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Forward to the decorated function
            return decorated(self, *args, **kwargs)
        
        return cast(F, wrapper)


class OpenAIValidator:
    """Validation implementation for OpenAI provider."""
    
    @staticmethod
    def validate_init(func: F) -> F:
        """Validate OpenAI provider initialization parameters.
        
        Args:
            func: The __init__ function to decorate.
            
        Returns:
            The decorated function.
        """
        @functools.wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Validate API key
            api_key = kwargs.get("api_key")
            if not api_key:
                # Check for environment variable in the actual init method
                # This is just a basic check
                pass
            
            # Validate model name
            model_name = kwargs.get("model_name", "gpt-4.1")
            try:
                ensure_valid_model(model_name, "openai")
            except ProviderValidationError as e:
                # Log and continue since we'll let the init method handle this
                logger.warning(f"Problematic model name: {model_name}, error: {e}")
            
            # Validate options
            if "options" in kwargs and kwargs["options"]:
                validate_openai_options(lambda s, o: o)(self, options=kwargs["options"])
            
            # Call the original __init__ method
            return func(self, *args, **kwargs)
        
        return cast(F, wrapper)
    
    @staticmethod
    def validate_generate(func: F) -> F:
        """Validate OpenAI provider generate parameters.
        
        Args:
            func: The generate function to decorate.
            
        Returns:
            The decorated function.
        """
        # Combine our decorator with the built-in request/response validators
        decorated = validate_request(validate_response(func))
        
        @functools.wraps(decorated)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Forward to the decorated function
            return decorated(self, *args, **kwargs)
        
        return cast(F, wrapper)
    
    @staticmethod
    def validate_stream(func: F) -> F:
        """Validate OpenAI provider stream parameters.
        
        Args:
            func: The stream function to decorate.
            
        Returns:
            The decorated function.
        """
        # Use the built-in request validator (not response - streams don't have complete responses)
        decorated = validate_request(func)
        
        @functools.wraps(decorated)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Forward to the decorated function
            return decorated(self, *args, **kwargs)
        
        return cast(F, wrapper)


class OllamaValidator:
    """Validation implementation for Ollama provider."""
    
    @staticmethod
    def validate_init(func: F) -> F:
        """Validate Ollama provider initialization parameters.
        
        Args:
            func: The __init__ function to decorate.
            
        Returns:
            The decorated function.
        """
        @functools.wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Validate model name
            model_name = kwargs.get("model_name", "llama3")
            try:
                ensure_valid_model(model_name, "ollama")
            except ProviderValidationError as e:
                # Log and continue since we'll let the init method handle this
                logger.warning(f"Problematic model name: {model_name}, error: {e}")
            
            # Validate API endpoint
            api_endpoint = kwargs.get("api_endpoint")
            if api_endpoint and not api_endpoint.startswith(("http://", "https://")):
                raise ProviderValidationError(
                    f"Invalid Ollama API endpoint: {api_endpoint}",
                    provider="ollama",
                    details={"error": "API endpoint must start with http:// or https://"}
                )
            
            # Validate options
            if "options" in kwargs and kwargs["options"]:
                validate_ollama_options(lambda s, o: o)(self, options=kwargs["options"])
            
            # Call the original __init__ method
            return func(self, *args, **kwargs)
        
        return cast(F, wrapper)
    
    @staticmethod
    def validate_generate(func: F) -> F:
        """Validate Ollama provider generate parameters.
        
        Args:
            func: The generate function to decorate.
            
        Returns:
            The decorated function.
        """
        # Combine our decorator with the built-in request/response validators
        decorated = validate_request(validate_response(func))
        
        @functools.wraps(decorated)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Forward to the decorated function
            return decorated(self, *args, **kwargs)
        
        return cast(F, wrapper)
    
    @staticmethod
    def validate_stream(func: F) -> F:
        """Validate Ollama provider stream parameters.
        
        Args:
            func: The stream function to decorate.
            
        Returns:
            The decorated function.
        """
        # Use the built-in request validator (not response - streams don't have complete responses)
        decorated = validate_request(func)
        
        @functools.wraps(decorated)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Forward to the decorated function
            return decorated(self, *args, **kwargs)
        
        return cast(F, wrapper)


def get_validator_for_provider(provider_type: str) -> Any:
    """Get the validator class for a specific provider type.
    
    Args:
        provider_type: The provider type ('anthropic', 'openai', 'ollama').
        
    Returns:
        The validator class.
    """
    validators = {
        "anthropic": AnthropicValidator,
        "openai": OpenAIValidator,
        "ollama": OllamaValidator,
    }
    
    return validators.get(provider_type.lower())


def validate_provider_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a provider configuration dictionary.
    
    Args:
        config: The provider configuration dictionary.
        
    Returns:
        The validated configuration.
        
    Raises:
        ProviderValidationError: If validation fails.
    """
    try:
        # Apply base validation
        validated_config = provider_config_schema.load(config)
        
        # Apply provider-specific validation
        provider_type = validated_config.get("provider_type")
        if provider_type:
            # Validate model name
            model_name = validated_config.get("model_name")
            if model_name:
                is_valid, error_message = validate_model_for_provider(model_name, provider_type)
                if not is_valid:
                    raise ProviderValidationError(
                        error_message or f"Invalid model '{model_name}' for provider '{provider_type}'",
                        provider=provider_type,
                        details={
                            "model_name": model_name,
                            "provider_type": provider_type,
                        }
                    )
            
            # Validate options based on provider type
            if "options" in validated_config and validated_config["options"]:
                provider_validator = get_validator_for_provider(provider_type)
                if provider_validator:
                    # This doesn't actually validate because we don't have a function to decorate,
                    # but we can abuse the opcodes a bit to check for incompatible settings
                    try:
                        if provider_type == "anthropic":
                            validate_anthropic_options(lambda s, o: o)(None, options=validated_config["options"])
                        elif provider_type == "openai":
                            validate_openai_options(lambda s, o: o)(None, options=validated_config["options"])
                        elif provider_type == "ollama":
                            validate_ollama_options(lambda s, o: o)(None, options=validated_config["options"])
                    except ProviderValidationError as e:
                        # Re-raise with the same details
                        raise ProviderValidationError(
                            f"Invalid options for provider {provider_type}: {e}",
                            provider=provider_type,
                            details=e.details
                        )
        
        return validated_config
        
    except ValidationError as e:
        provider_type = config.get("provider_type", "unknown")
        raise ProviderValidationError(
            f"Invalid provider configuration for {provider_type}: {e.messages}",
            provider=provider_type,
            details={"validation_errors": e.messages}
        )


# Export all public elements
__all__ = [
    'AnthropicValidator',
    'OpenAIValidator',
    'OllamaValidator',
    'get_validator_for_provider',
    'validate_provider_config',
]