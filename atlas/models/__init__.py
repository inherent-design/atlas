"""
Models package for Atlas framework.

This package provides a unified interface for different model providers,
abstracting away provider-specific implementations and providing a consistent
API for the rest of the framework.
"""

# Core interface classes
from atlas.models.base import (
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ModelMessage,
    MessageContent,
    ModelRole,
    TokenUsage,
    CostEstimate,
)

# Factory functions
from atlas.models.factory import (
    discover_providers,
    create_provider,
    get_all_providers,
    register_provider,
    set_default_model,
    ProviderFactory,
)

# Provider implementations
try:
    from atlas.models.anthropic import AnthropicProvider

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from atlas.models.openai import OpenAIProvider

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from atlas.models.ollama import OllamaProvider

    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

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
    # Factory functions
    "discover_providers",
    "create_provider",
    "get_all_providers",
    "register_provider",
    "set_default_model",
    "ProviderFactory",
    # Provider implementations
    "AnthropicProvider",
    "OpenAIProvider",
    "OllamaProvider",
    # Availability flags
    "ANTHROPIC_AVAILABLE",
    "OPENAI_AVAILABLE",
    "OLLAMA_AVAILABLE",
]
