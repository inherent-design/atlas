"""
Provider options and configuration module.

This module defines the ProviderOptions class which centralizes all provider
configuration parameters and supports auto-detection and resolution of provider/model
combinations across different application entry points.
"""

import copy
from dataclasses import dataclass, field
from typing import Any, Union

from atlas.core import env
from atlas.core.logging import get_logger
from atlas.providers.capabilities import Capability, CapabilityLevel

logger = get_logger(__name__)


@dataclass
class ProviderOptions:
    """Options for creating and configuring model providers.

    This class centralizes all parameters used for provider selection, creation,
    and configuration. It supports auto-detection of providers from model names,
    capability-based model selection, and environment variable defaults.

    Attributes:
        provider_name: Name of the provider (e.g., "anthropic", "openai", "ollama", "mock")
        model_name: Name of the model to use
        capability: Capability required (e.g., "inexpensive", "efficient", "premium", "vision")
        max_tokens: Maximum tokens for model generation
        base_url: Base URL for provider API (primarily used for Ollama)
        streaming: Whether to enable streaming output for responses
        required_capabilities: Dictionary of capabilities required with minimum strength levels
        extra_params: Additional provider-specific parameters
    """

    # Core provider and model selection
    provider_name: str | None = None
    model_name: str | None = None
    capability: str | None = None

    # Performance and resource limits
    max_tokens: int | None = None

    # Connection parameters
    base_url: str | None = None

    # Streaming flag
    streaming: bool = False

    # Required capabilities with minimum strength levels
    required_capabilities: dict[str, CapabilityLevel] = field(default_factory=dict)

    # Additional provider-specific parameters
    extra_params: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> "ProviderOptions":
        """Create ProviderOptions based on environment variables.

        This factory method constructs ProviderOptions using values from
        environment variables, with appropriate defaults for missing values.

        Returns:
            Populated ProviderOptions instance
        """
        options = cls(
            provider_name=env.get_string("ATLAS_DEFAULT_PROVIDER", "anthropic"),
            model_name=env.get_string("ATLAS_DEFAULT_MODEL"),
            capability=env.get_string("ATLAS_DEFAULT_CAPABILITY", "inexpensive"),
            max_tokens=env.get_int("ATLAS_MAX_TOKENS", 2000),
        )

        # Provider-specific environment variables
        if options.provider_name == "ollama":
            options.base_url = env.get_string("ATLAS_OLLAMA_BASE_URL", "http://localhost:11434")

        return options

    def to_dict(self) -> dict[str, Any]:
        """Convert options to dictionary format.

        Returns:
            Dictionary representation of the options
        """
        result = {
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "capability": self.capability,
            "max_tokens": self.max_tokens,
            "streaming": self.streaming,
        }

        # Add optional parameters if set
        if self.base_url:
            result["base_url"] = self.base_url

        # Add required capabilities if any
        if self.required_capabilities:
            result["required_capabilities"] = {
                k: v.value for k, v in self.required_capabilities.items()
            }

        # Add any extra parameters
        result.update(self.extra_params)

        return result

    def require_capability(
        self, capability: Union[str, "Capability"], min_level: "CapabilityLevel" = None
    ) -> None:
        """Add a required capability with minimum strength level.

        Args:
            capability: The capability to require
            min_level: Minimum required capability level, defaults to MODERATE if None
        """
        if min_level is None:
            min_level = CapabilityLevel.MODERATE

        # Convert string capability to Capability enum if needed
        if isinstance(capability, str):
            # Check if it's already a valid string capability
            capability_str = capability
        else:
            # It's a Capability enum, convert to string
            capability_str = capability.value

        self.required_capabilities[capability_str] = min_level

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProviderOptions":
        """Create ProviderOptions from dictionary.

        Args:
            data: Dictionary containing provider options

        Returns:
            Populated ProviderOptions instance
        """
        # Extract known fields
        known_fields = [
            "provider_name",
            "model_name",
            "capability",
            "max_tokens",
            "base_url",
            "streaming",
        ]

        kwargs = {k: v for k, v in data.items() if k in known_fields}

        # Handle required capabilities separately
        required_capabilities = {}
        if "required_capabilities" in data:
            for cap, level in data["required_capabilities"].items():
                if isinstance(level, int):
                    required_capabilities[cap] = CapabilityLevel(level)
                else:
                    # Try to convert string to enum
                    try:
                        required_capabilities[cap] = CapabilityLevel[level.upper()]
                    except (KeyError, AttributeError):
                        # Default to MODERATE if conversion fails
                        required_capabilities[cap] = CapabilityLevel.MODERATE

        # Extract extra parameters
        extra_params = {
            k: v
            for k, v in data.items()
            if k not in known_fields and k != "required_capabilities" and not k.startswith("_")
        }

        # Create instance
        instance = cls(**kwargs, extra_params=extra_params)

        # Set required capabilities
        instance.required_capabilities = required_capabilities

        return instance

    def merge(self, other: "ProviderOptions") -> "ProviderOptions":
        """Create a new ProviderOptions by merging with another instance.

        This method creates a new ProviderOptions instance by combining values
        from self and other, with other's values taking precedence.

        Args:
            other: Another ProviderOptions instance to merge with

        Returns:
            New ProviderOptions instance with merged values
        """
        # Start with a copy of self
        merged_dict = self.to_dict()

        # Update with other's values, ignoring None values
        other_dict = other.to_dict()
        for key, value in other_dict.items():
            if value is not None:
                merged_dict[key] = value

        # Handle extra_params separately for deep merge
        merged_extra = copy.deepcopy(self.extra_params)
        merged_extra.update(other.extra_params)

        # Create new instance
        result = self.from_dict(merged_dict)
        result.extra_params = merged_extra

        # Merge required capabilities
        merged_required_capabilities = copy.deepcopy(self.required_capabilities)
        for cap, level in other.required_capabilities.items():
            # Use the higher capability level if both instances require the same capability
            if cap in merged_required_capabilities:
                merged_required_capabilities[cap] = max(merged_required_capabilities[cap], level)
            else:
                merged_required_capabilities[cap] = level

        result.required_capabilities = merged_required_capabilities

        return result
