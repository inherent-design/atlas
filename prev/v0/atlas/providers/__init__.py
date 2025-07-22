"""
Providers package for Atlas framework.

This package provides a unified interface for different LLM providers,
abstracting away provider-specific implementations and providing a consistent
API for the rest of the framework.
"""

# Core interface classes
from atlas.providers.base import ModelProvider
from atlas.providers.capabilities import (
    CAPABILITY_ANALYSIS,
    CAPABILITY_CODE,
    CAPABILITY_CREATIVE,
    CAPABILITY_EFFICIENT,
    CAPABILITY_EXTRACTION,
    CAPABILITY_FORMATTING,
    CAPABILITY_INEXPENSIVE,
    CAPABILITY_LOGIC,
    CAPABILITY_MATH,
    CAPABILITY_PREMIUM,
    CAPABILITY_REASONING,
    CAPABILITY_STANDARD,
    CAPABILITY_STREAMING,
    CAPABILITY_SUMMARIZATION,
    CAPABILITY_VISION,
)

# Error classes
from atlas.providers.errors import (
    ProviderAuthenticationError,
    ProviderError,
    ProviderNetworkError,
    ProviderQuotaExceededError,
    ProviderRateLimitError,
    ProviderServerError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderValidationError,
)

# Factory functions
from atlas.providers.factory import (
    ProviderFactory,
    create_provider,
    create_provider_group,
    discover_providers,
    get_all_providers,
    register_provider,
    set_default_model,
)

# Provider implementations
from atlas.providers.implementations import (
    ANTHROPIC_AVAILABLE,
    MOCK_AVAILABLE,
    OLLAMA_AVAILABLE,
    OPENAI_AVAILABLE,
)
from atlas.providers.messages import (
    CostEstimate,
    MessageContent,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ModelRole,
    TokenUsage,
)

# Provider configuration and options
from atlas.providers.options import ProviderOptions

# Enhanced provider system
from atlas.providers.registry import CapabilityStrength, ProviderRegistry, get_registry
from atlas.providers.resolver import (
    create_provider_from_options,
    resolve_provider_options,
)
from atlas.providers.streaming.base import StreamHandler

# Streaming interfaces
from atlas.providers.streaming.control import StreamControl, StreamState

# Import provider classes when available
if ANTHROPIC_AVAILABLE:
    from atlas.providers.implementations.anthropic import AnthropicProvider

if OPENAI_AVAILABLE:
    from atlas.providers.implementations.openai import OpenAIProvider

if OLLAMA_AVAILABLE:
    from atlas.providers.implementations.ollama import OllamaProvider

# Mock is always available
# Import logging for registry initialization
import logging

from atlas.providers.implementations.mock import MockProvider

logger = logging.getLogger(__name__)

__all__ = [
    # Core interfaces
    "ModelProvider",
    "ModelRequest",
    "ModelResponse",
    "ModelMessage",
    "MessageContent",
    "ModelRole",
    "TokenUsage",
    "CostEstimate",
    # Provider configuration
    "ProviderOptions",
    "resolve_provider_options",
    "create_provider_from_options",
    # Factory functions
    "discover_providers",
    "create_provider",
    "create_provider_group",
    "get_all_providers",
    "register_provider",
    "set_default_model",
    "ProviderFactory",
    # Enhanced provider system
    "ProviderRegistry",
    "get_registry",
    "CapabilityStrength",
    # Provider implementations
    "AnthropicProvider",
    "OpenAIProvider",
    "OllamaProvider",
    "MockProvider",
    # Availability flags
    "ANTHROPIC_AVAILABLE",
    "OPENAI_AVAILABLE",
    "OLLAMA_AVAILABLE",
    "MOCK_AVAILABLE",
]


# Initialize provider registry function
def initialize_registry():
    """Initialize the provider registry with default providers, models and capabilities.

    This function registers all available providers, models, and their capabilities
    with the central provider registry. It's called automatically when the module
    is imported, but can be called again to refresh the registry if needed.
    """
    try:
        registry = get_registry()

        # Skip if already initialized
        if getattr(registry, "_initialized", False):
            return

        logger.info("Initializing provider registry with default models and capabilities")

        # Register Anthropic provider and models if available
        if ANTHROPIC_AVAILABLE:
            # Register provider with models
            registry.register_provider(
                "anthropic",
                AnthropicProvider,
                [
                    "claude-3-7-sonnet-20250219",
                    "claude-3-5-sonnet-20240620",
                    "claude-3-5-haiku-20240620",
                    "claude-3-opus-20240229",
                    "claude-3-sonnet-20240229",
                    "claude-3-haiku-20240307",
                ],
            )

            # Register model capabilities
            registry.register_model_capability(
                "claude-3-7-sonnet-20250219", CAPABILITY_PREMIUM, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "claude-3-7-sonnet-20250219", CAPABILITY_VISION, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "claude-3-7-sonnet-20250219", CAPABILITY_STANDARD, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "claude-3-7-sonnet-20250219", CAPABILITY_REASONING, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "claude-3-7-sonnet-20250219", CAPABILITY_CODE, CapabilityStrength.STRONG
            )

            registry.register_model_capability(
                "claude-3-5-sonnet-20240620", CAPABILITY_PREMIUM, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "claude-3-5-sonnet-20240620", CAPABILITY_VISION, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "claude-3-5-sonnet-20240620", CAPABILITY_STANDARD, CapabilityStrength.STRONG
            )

            registry.register_model_capability(
                "claude-3-5-haiku-20240620", CAPABILITY_EFFICIENT, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "claude-3-5-haiku-20240620", CAPABILITY_STANDARD, CapabilityStrength.STRONG
            )

            registry.register_model_capability(
                "claude-3-opus-20240229", CAPABILITY_PREMIUM, CapabilityStrength.EXCEPTIONAL
            )
            registry.register_model_capability(
                "claude-3-opus-20240229", CAPABILITY_VISION, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "claude-3-opus-20240229", CAPABILITY_STANDARD, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "claude-3-opus-20240229", CAPABILITY_REASONING, CapabilityStrength.EXCEPTIONAL
            )
            registry.register_model_capability(
                "claude-3-opus-20240229", CAPABILITY_CODE, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "claude-3-opus-20240229", CAPABILITY_CREATIVE, CapabilityStrength.STRONG
            )

            registry.register_model_capability(
                "claude-3-sonnet-20240229", CAPABILITY_PREMIUM, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "claude-3-sonnet-20240229", CAPABILITY_VISION, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "claude-3-sonnet-20240229", CAPABILITY_STANDARD, CapabilityStrength.STRONG
            )

            registry.register_model_capability(
                "claude-3-haiku-20240307", CAPABILITY_INEXPENSIVE, CapabilityStrength.MODERATE
            )
            registry.register_model_capability(
                "claude-3-haiku-20240307", CAPABILITY_EFFICIENT, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "claude-3-haiku-20240307", CAPABILITY_STANDARD, CapabilityStrength.MODERATE
            )

            logger.debug("Registered Anthropic provider with 6 models and capabilities")

        # Register OpenAI provider and models if available
        if OPENAI_AVAILABLE:
            # Register provider with models
            registry.register_provider(
                "openai",
                OpenAIProvider,
                [
                    "gpt-4.1",
                    "gpt-4.1-mini",
                    "gpt-4.1-nano",
                    "o3",
                    "o4-mini",
                    "gpt-4o",
                    "gpt-4o-mini",
                    "gpt-4-turbo",
                    "gpt-4",
                    "gpt-3.5-turbo",
                ],
            )

            # OpenAI model capabilities
            registry.register_model_capability(
                "gpt-4.1", CAPABILITY_PREMIUM, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "gpt-4.1", CAPABILITY_VISION, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "gpt-4.1", CAPABILITY_STANDARD, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "gpt-4.1", CAPABILITY_REASONING, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "gpt-4.1", CAPABILITY_CODE, CapabilityStrength.STRONG
            )

            registry.register_model_capability(
                "gpt-4.1-mini", CAPABILITY_STANDARD, CapabilityStrength.MODERATE
            )

            registry.register_model_capability(
                "gpt-4.1-nano", CAPABILITY_EFFICIENT, CapabilityStrength.MODERATE
            )
            registry.register_model_capability(
                "gpt-4.1-nano", CAPABILITY_INEXPENSIVE, CapabilityStrength.MODERATE
            )
            registry.register_model_capability(
                "gpt-4.1-nano", CAPABILITY_STANDARD, CapabilityStrength.MODERATE
            )

            registry.register_model_capability("o3", CAPABILITY_PREMIUM, CapabilityStrength.STRONG)
            registry.register_model_capability("o3", CAPABILITY_STANDARD, CapabilityStrength.STRONG)

            registry.register_model_capability(
                "o4-mini", CAPABILITY_STANDARD, CapabilityStrength.MODERATE
            )

            registry.register_model_capability(
                "gpt-4o", CAPABILITY_PREMIUM, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "gpt-4o", CAPABILITY_VISION, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "gpt-4o", CAPABILITY_STANDARD, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "gpt-4o", CAPABILITY_REASONING, CapabilityStrength.STRONG
            )
            registry.register_model_capability("gpt-4o", CAPABILITY_CODE, CapabilityStrength.STRONG)

            registry.register_model_capability(
                "gpt-4o-mini", CAPABILITY_STANDARD, CapabilityStrength.MODERATE
            )

            registry.register_model_capability(
                "gpt-4-turbo", CAPABILITY_PREMIUM, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "gpt-4-turbo", CAPABILITY_VISION, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "gpt-4-turbo", CAPABILITY_STANDARD, CapabilityStrength.STRONG
            )

            registry.register_model_capability(
                "gpt-4", CAPABILITY_PREMIUM, CapabilityStrength.MODERATE
            )
            registry.register_model_capability(
                "gpt-4", CAPABILITY_STANDARD, CapabilityStrength.MODERATE
            )

            registry.register_model_capability(
                "gpt-3.5-turbo", CAPABILITY_INEXPENSIVE, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "gpt-3.5-turbo", CAPABILITY_EFFICIENT, CapabilityStrength.STRONG
            )
            registry.register_model_capability(
                "gpt-3.5-turbo", CAPABILITY_STANDARD, CapabilityStrength.MODERATE
            )

            logger.debug("Registered OpenAI provider with 10 models and capabilities")

        # Register Mock provider (always available)
        # Register provider with models
        registry.register_provider(
            "mock", MockProvider, ["mock-standard", "mock-basic", "mock-advanced"]
        )

        # Mock model capabilities
        registry.register_model_capability(
            "mock-standard", CAPABILITY_STANDARD, CapabilityStrength.MODERATE
        )

        registry.register_model_capability(
            "mock-basic", CAPABILITY_INEXPENSIVE, CapabilityStrength.STRONG
        )
        registry.register_model_capability(
            "mock-basic", CAPABILITY_EFFICIENT, CapabilityStrength.STRONG
        )
        registry.register_model_capability(
            "mock-basic", CAPABILITY_STANDARD, CapabilityStrength.MODERATE
        )

        registry.register_model_capability(
            "mock-advanced", CAPABILITY_PREMIUM, CapabilityStrength.MODERATE
        )
        registry.register_model_capability(
            "mock-advanced", CAPABILITY_VISION, CapabilityStrength.MODERATE
        )
        registry.register_model_capability(
            "mock-advanced", CAPABILITY_STANDARD, CapabilityStrength.MODERATE
        )

        logger.debug("Registered Mock provider with 3 models and capabilities")

        # Note: Skipping Ollama models registration, as specified in the requirements
        # We'll just register the provider without models for completeness
        if OLLAMA_AVAILABLE:
            registry.register_provider("ollama", OllamaProvider)
            logger.debug("Registered Ollama provider without explicit models")

        # Register factories with the registry
        from .factory import create_provider

        for provider_name in ["anthropic", "openai", "ollama", "mock"]:
            if (
                (provider_name == "anthropic" and ANTHROPIC_AVAILABLE)
                or (provider_name == "openai" and OPENAI_AVAILABLE)
                or (provider_name == "ollama" and OLLAMA_AVAILABLE)
                or provider_name == "mock"
            ):
                # Create non-recursive factory function for each provider
                def make_factory(provider_class, prov_name):
                    def factory(**kwargs):
                        # Direct instantiation without calling create_provider to avoid recursion
                        model_name = kwargs.pop("model_name", None)
                        # Get model from available models if not specified
                        if not model_name and prov_name in registry._provider_models:
                            models = registry._provider_models.get(prov_name, [])
                            if models:
                                model_name = models[0]  # Use first available model
                        return provider_class(model_name=model_name, **kwargs)

                    return factory

                # Get the actual provider class
                provider_class = registry._providers.get(provider_name)
                if provider_class:
                    registry._provider_factories[provider_name] = make_factory(
                        provider_class, provider_name
                    )

        # Mark as initialized
        registry._initialized = True
        logger.info(
            "Provider registry initialized successfully with default models and capabilities"
        )

    except Exception as e:
        logger.warning(f"Error initializing provider registry: {e}")


# Initialize registry on module import
try:
    initialize_registry()
except Exception as e:
    logger.warning(f"Provider registry initialization failed: {e}")
