"""
Provider implementations for Atlas.

This module contains the concrete implementations of various language model providers,
each implementing the common ModelProvider interface with provider-specific features.
"""

# Provider availability flags
ANTHROPIC_AVAILABLE = False
OPENAI_AVAILABLE = False
OLLAMA_AVAILABLE = False
MOCK_AVAILABLE = True  # Mock is always available as it has no external dependencies

# Try importing Anthropic
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# Try importing OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Try importing Ollama (no specific package required, just check capabilities)
try:
    import requests
    try:
        # Test if we can import the requests module which is needed for Ollama
        OLLAMA_AVAILABLE = True
    except Exception:
        OLLAMA_AVAILABLE = False
except ImportError:
    OLLAMA_AVAILABLE = False

# Import provider implementations as they are moved
from .mock import MockProvider

# Import AnthropicProvider if available
if ANTHROPIC_AVAILABLE:
    from .anthropic import AnthropicProvider

# Remaining providers to be migrated
# from .openai import OpenAIProvider
# from .ollama import OllamaProvider

__all__ = [
    # Availability flags
    "ANTHROPIC_AVAILABLE",
    "OPENAI_AVAILABLE",
    "OLLAMA_AVAILABLE",
    "MOCK_AVAILABLE",
    
    # Provider classes
    "MockProvider",
]

# Add provider classes to __all__ if available
if ANTHROPIC_AVAILABLE:
    __all__.append("AnthropicProvider")