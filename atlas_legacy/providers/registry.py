"""
Provider registry module.

This module provides a central registry for provider, model, and capability information,
supporting the Enhanced Provider System. It enables capability-based model selection,
provider discovery, and task-aware provider creation.
"""

import threading
from collections.abc import Callable
from enum import IntEnum

from atlas.core.logging import get_logger
from atlas.providers.base import ModelProvider

# This will be imported once capabilities.py exists
# from atlas.providers.capabilities import CapabilityStrength


# Temporary definition until capabilities.py is created
class CapabilityStrength(IntEnum):
    """Enumeration of capability strength levels.

    This enum will be moved to capabilities.py in a future implementation.
    """

    NONE = 0  # No capability
    BASIC = 1  # Has the capability but limited
    MODERATE = 2  # Average capability
    STRONG = 3  # Excellent at this capability
    EXCEPTIONAL = 4  # Best-in-class for this capability


logger = get_logger(__name__)


class ProviderRegistry:
    """Central registry for provider, model, and capability information.

    This class maintains information about all available providers, their models,
    and the capability strengths of each model. It supports capability-based
    provider selection and model discovery.

    Thread-safe for concurrent registration and querying operations.
    """

    _instance = None
    _lock = threading.RLock()

    @classmethod
    def get_instance(cls) -> "ProviderRegistry":
        """Get the global singleton instance of the provider registry.

        Returns:
            The global ProviderRegistry instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize the registry with empty data structures."""
        # Guard against accidental direct instantiation
        if self.__class__._instance is not None:
            logger.warning(
                "ProviderRegistry should be accessed via get_instance(), not directly instantiated"
            )

        # Core data structures with thread safety
        self._lock = threading.RLock()

        # Provider-related mappings
        self._providers: dict[str, type[ModelProvider]] = {}  # name -> Provider class
        self._provider_models: dict[str, list[str]] = {}  # provider_name -> list of models
        self._model_providers: dict[str, str] = {}  # model_name -> provider_name

        # Capability-related mappings
        self._model_capabilities: dict[
            str, dict[str, CapabilityStrength]
        ] = {}  # model_name -> {capability -> strength}
        self._capability_models: dict[str, set[str]] = {}  # capability -> set of model names

        # Provider creation callbacks
        self._provider_factories: dict[str, Callable] = {}  # provider_name -> factory function

        # Initialization tracking
        self._initialized = False

    def register_provider(
        self,
        name: str,
        provider_class: type[ModelProvider],
        models: list[str] | None = None,
        factory: Callable | None = None,
    ) -> "ProviderRegistry":
        """Register a provider and its supported models.

        Args:
            name: The name of the provider (e.g., "anthropic", "openai")
            provider_class: The provider class
            models: Optional list of model names supported by this provider
            factory: Optional factory function for creating provider instances

        Returns:
            Self for method chaining
        """
        with self._lock:
            # Register the provider class
            self._providers[name] = provider_class

            # Register the factory function if provided
            if factory is not None:
                self._provider_factories[name] = factory

            # Register the supported models if provided
            if models:
                self._provider_models[name] = models

                # Update model to provider mapping
                for model in models:
                    self._model_providers[model] = name

                    # Ensure model has an entry in capabilities mapping
                    if model not in self._model_capabilities:
                        self._model_capabilities[model] = {}

            logger.debug(f"Registered provider '{name}' with {len(models) if models else 0} models")

            return self

    def register_model_capability(
        self,
        model_name: str,
        capability: str,
        strength: CapabilityStrength | int = CapabilityStrength.MODERATE,
    ) -> "ProviderRegistry":
        """Register a capability for a specific model.

        Args:
            model_name: The name of the model
            capability: The capability name
            strength: The strength level of the capability

        Returns:
            Self for method chaining

        Raises:
            ValueError: If the model is not registered
        """
        with self._lock:
            # Convert integer to CapabilityStrength if needed
            if isinstance(strength, int):
                strength = CapabilityStrength(strength)

            # Check if model is registered
            if model_name not in self._model_providers:
                logger.warning(
                    f"Model '{model_name}' not registered with any provider. Capability will still be recorded."
                )

            # Ensure model has an entry in model_capabilities
            if model_name not in self._model_capabilities:
                self._model_capabilities[model_name] = {}

            # Set the capability strength
            self._model_capabilities[model_name][capability] = strength

            # Ensure capability has an entry in capability_models
            if capability not in self._capability_models:
                self._capability_models[capability] = set()

            # Add model to the capability's model set if strength > NONE
            if strength > CapabilityStrength.NONE:
                self._capability_models[capability].add(model_name)
            # Remove model from capability's model set if strength is NONE
            elif model_name in self._capability_models[capability]:
                self._capability_models[capability].remove(model_name)

            logger.debug(f"Registered {capability}:{strength.name} for model '{model_name}'")

            return self

    def get_provider_for_model(self, model_name: str) -> str | None:
        """Get the provider name for a specific model.

        Args:
            model_name: The name of the model

        Returns:
            The provider name, or None if not found
        """
        with self._lock:
            return self._model_providers.get(model_name)

    def get_models_by_capability(
        self,
        capability: str,
        min_strength: CapabilityStrength | int = CapabilityStrength.BASIC,
        provider_name: str | None = None,
    ) -> list[str]:
        """Get models with a specific capability meeting minimum strength.

        Args:
            capability: The capability to search for
            min_strength: The minimum strength level required
            provider_name: Optional provider name to filter results

        Returns:
            List of model names meeting the criteria, sorted by strength (strongest first)
        """
        with self._lock:
            # Convert integer to CapabilityStrength if needed
            if isinstance(min_strength, int):
                min_strength = CapabilityStrength(min_strength)

            # Get all models with this capability
            if capability not in self._capability_models:
                return []

            # Create list of (model_name, strength) tuples for models meeting criteria
            result = []

            for model_name in self._capability_models[capability]:
                # Skip if provider doesn't match the filter
                if provider_name and self._model_providers.get(model_name) != provider_name:
                    continue

                # Get strength value
                strength = self._model_capabilities[model_name][capability]

                # Include if strength meets minimum
                if strength >= min_strength:
                    result.append((model_name, strength))

            # Sort by strength (descending)
            result.sort(key=lambda x: x[1], reverse=True)

            # Return just the model names
            return [model for model, _ in result]

    def get_models_for_provider(self, provider_name: str) -> list[str]:
        """Get all models registered for a specific provider.

        Args:
            provider_name: The name of the provider

        Returns:
            List of model names, or empty list if provider not found
        """
        with self._lock:
            return self._provider_models.get(provider_name, [])

    def get_capabilities_for_model(self, model_name: str) -> dict[str, CapabilityStrength]:
        """Get all capabilities for a specific model.

        Args:
            model_name: The name of the model

        Returns:
            Dictionary mapping capability names to strength levels
        """
        with self._lock:
            return self._model_capabilities.get(model_name, {}).copy()

    def find_provider_by_model(self, model_name: str) -> type[ModelProvider] | None:
        """Find the provider class for a specific model.

        Args:
            model_name: The name of the model

        Returns:
            The provider class, or None if not found
        """
        with self._lock:
            provider_name = self._model_providers.get(model_name)
            if provider_name:
                return self._providers.get(provider_name)
            return None

    def find_models_with_capabilities(
        self,
        capabilities: dict[str, CapabilityStrength | int],
        provider_name: str | None = None,
    ) -> list[str]:
        """Find models that satisfy multiple capability requirements.

        Args:
            capabilities: Dictionary mapping capability names to minimum strength levels
            provider_name: Optional provider name to filter results

        Returns:
            List of model names meeting all requirements, sorted by average strength (highest first)
        """
        with self._lock:
            if not capabilities:
                return []

            # Get all registered models
            all_models = set(self._model_capabilities.keys())

            # Filter by provider if specified
            if provider_name:
                all_models = {
                    model
                    for model in all_models
                    if self._model_providers.get(model) == provider_name
                }

            # Track models meeting all requirements with their average strength
            result = []

            for model_name in all_models:
                model_caps = self._model_capabilities.get(model_name, {})
                meets_requirements = True
                total_strength = 0

                for cap, min_strength in capabilities.items():
                    # Convert integer to CapabilityStrength if needed
                    if isinstance(min_strength, int):
                        min_strength = CapabilityStrength(min_strength)

                    # Check if model has required capability at minimum strength
                    model_strength = model_caps.get(cap, CapabilityStrength.NONE)
                    if model_strength < min_strength:
                        meets_requirements = False
                        break

                    total_strength += model_strength.value

                if meets_requirements:
                    # Calculate average strength across all required capabilities
                    avg_strength = total_strength / len(capabilities)
                    result.append((model_name, avg_strength))

            # Sort by average strength (descending)
            result.sort(key=lambda x: x[1], reverse=True)

            # Return just the model names
            return [model for model, _ in result]

    def create_provider(
        self,
        provider_name: str | None = None,
        model_name: str | None = None,
        capabilities: dict[str, CapabilityStrength | int] | None = None,
        **kwargs,
    ) -> ModelProvider | None:
        """Create a provider instance based on name, model, or capabilities.

        Args:
            provider_name: Optional name of the provider
            model_name: Optional name of the model
            capabilities: Optional capability requirements
            **kwargs: Additional arguments to pass to the provider constructor

        Returns:
            Provider instance, or None if no suitable provider found

        Raises:
            ValueError: If conflicting options are provided
        """
        with self._lock:
            # Case 1: Create by model name
            if model_name and not provider_name:
                provider_name = self.get_provider_for_model(model_name)
                if not provider_name:
                    raise ValueError(f"Could not find provider for model '{model_name}'")

            # Case 2: Create by capability requirements
            if capabilities and not model_name:
                models = self.find_models_with_capabilities(capabilities, provider_name)
                if not models:
                    capability_str = ", ".join(f"{c}:{s}" for c, s in capabilities.items())
                    if provider_name:
                        msg = f"No models for provider '{provider_name}' meet capabilities: {capability_str}"
                    else:
                        msg = f"No models meet capabilities: {capability_str}"
                    raise ValueError(msg)

                # Use the first (highest scoring) model
                model_name = models[0]

                # Update provider_name if not already set
                if not provider_name:
                    provider_name = self.get_provider_for_model(model_name)

            # Ensure we have a provider name by this point
            if not provider_name:
                raise ValueError(
                    "Could not determine provider - please specify provider_name, model_name, or capabilities"
                )

            # Find factory function or provider class
            factory = self._provider_factories.get(provider_name)
            provider_class = self._providers.get(provider_name)

            if factory:
                # Use factory function with kwargs
                return factory(model_name=model_name, **kwargs)
            elif provider_class:
                # Create instance directly
                return provider_class(model_name=model_name, **kwargs)
            else:
                raise ValueError(f"Provider '{provider_name}' is not registered")

    def get_all_providers(self) -> list[str]:
        """Get all registered provider names.

        Returns:
            List of provider names
        """
        with self._lock:
            return list(self._providers.keys())

    def get_all_models(self) -> list[str]:
        """Get all registered model names.

        Returns:
            List of model names
        """
        with self._lock:
            return list(self._model_providers.keys())

    def get_all_capabilities(self) -> set[str]:
        """Get all registered capability names.

        Returns:
            Set of capability names
        """
        with self._lock:
            return set(self._capability_models.keys())


# Global registry instance
def get_registry() -> ProviderRegistry:
    """Get the global provider registry instance.

    Returns:
        The global ProviderRegistry instance
    """
    return ProviderRegistry.get_instance()
