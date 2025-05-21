"""
Provider group with fallback capabilities.

This module provides the ProviderGroup class that implements the BaseProvider interface
and enables fallback between multiple providers. It includes various selection strategies
for choosing which providers to use for different tasks.
"""

import random
import threading
import time
from collections.abc import Callable
from typing import Any

from atlas.core.logging import get_logger
from atlas.core.retry import RetryPolicy, RetryState, calculate_retry_delay
from atlas.core.telemetry import traced
from atlas.providers.base import ModelProvider
from atlas.providers.capabilities import (
    CapabilityStrength,
    detect_task_type_from_prompt,
    get_capabilities_for_task,
)
from atlas.providers.errors import ProviderError
from atlas.providers.messages import CostEstimate, ModelRequest, ModelResponse, TokenUsage
from atlas.providers.streaming.base import StreamHandler

logger = get_logger(__name__)


class ProviderSelectionStrategy:
    """Strategy for selecting providers from a group.

    This class provides various strategies for selecting providers from a group,
    including failover, round-robin, and cost-optimized approaches.
    """

    @staticmethod
    def failover(
        providers: list[ModelProvider], context: dict[str, Any] = None
    ) -> list[ModelProvider]:
        """Returns providers in order, for failover purposes.

        This strategy simply returns the providers in their original order,
        allowing the ProviderGroup to try them sequentially until one succeeds.

        Args:
            providers: List of provider instances
            context: Optional context for the strategy

        Returns:
            Providers in original order
        """
        return providers.copy()

    @staticmethod
    def round_robin(
        providers: list[ModelProvider], context: dict[str, Any] = None
    ) -> list[ModelProvider]:
        """Returns providers in round-robin order based on context.

        This strategy cycles through providers to distribute load evenly.

        Args:
            providers: List of provider instances
            context: Optional context for the strategy

        Returns:
            Providers in round-robin order
        """
        # Initialize context if needed
        context = context or {}
        index = context.get("round_robin_index", 0) % len(providers)

        # Update index for next call
        context["round_robin_index"] = (index + 1) % len(providers)

        # Reorder providers starting with the current index
        return providers[index:] + providers[:index]

    @staticmethod
    def random(
        providers: list[ModelProvider], context: dict[str, Any] = None
    ) -> list[ModelProvider]:
        """Returns providers in random order.

        This strategy shuffles providers randomly for each call.

        Args:
            providers: List of provider instances
            context: Optional context for the strategy

        Returns:
            Providers in random order
        """
        result = providers.copy()
        random.shuffle(result)
        return result

    @staticmethod
    def cost_optimized(
        providers: list[ModelProvider], context: dict[str, Any] = None
    ) -> list[ModelProvider]:
        """Returns providers ordered by estimated cost (lowest first).

        This strategy prioritizes lower-cost providers, falling back to
        higher-cost providers only when necessary.

        Args:
            providers: List of provider instances
            context: Optional context for the strategy

        Returns:
            Providers ordered by estimated cost (lowest first)
        """
        # Define relative cost rankings (lower is cheaper)
        provider_costs = {
            "mock": 0,  # Mock is free
            "ollama": 1,  # Ollama is local (only electricity cost)
            "openai": 2,  # OpenAI (mid-range pricing)
            "anthropic": 3,  # Anthropic (typically higher pricing)
        }

        # Sort providers by cost
        def get_provider_cost(provider):
            # Get provider name, with fallback if property doesn't exist
            provider_name = getattr(provider, "name", str(provider))
            return provider_costs.get(provider_name.lower(), 999)

        return sorted(providers, key=get_provider_cost)


class TaskAwareSelectionStrategy:
    """Strategy for selecting providers based on task requirements.

    This strategy analyzes prompts to detect task types and selects providers
    based on their capability strengths for the detected task.
    """

    @staticmethod
    def select(
        providers: list[ModelProvider], request: ModelRequest, context: dict[str, Any] = None
    ) -> list[ModelProvider]:
        """Select providers based on task detection and capability matching.

        Args:
            providers: List of provider instances
            request: The model request to analyze
            context: Optional context dictionary

        Returns:
            Providers in priority order for the detected task
        """
        # Extract user prompt for task detection
        prompt = ""
        for message in request.messages:
            if message.role.lower() == "user":
                prompt = message.content
                break

        if not prompt:
            # No user message found, return providers as-is
            return providers.copy()

        # Detect task type from prompt
        task_type = detect_task_type_from_prompt(prompt)

        # Get capability requirements for the task
        try:
            capabilities = get_capabilities_for_task(task_type)
        except ValueError:
            # Unknown task type, return providers as-is
            logger.warning(f"Unknown task type detected: {task_type}")
            return providers.copy()

        # Score providers based on capability match
        provider_scores = []

        for provider in providers:
            score = 0

            # Check each required capability
            for capability, required_strength in capabilities.items():
                # Get provider's strength for this capability
                provider_strength = CapabilityStrength.NONE

                # Try to get capability strength from provider if method exists
                if hasattr(provider, "get_capability_strength"):
                    provider_strength = provider.get_capability_strength(capability)

                # Score based on whether provider meets or exceeds required strength
                if provider_strength >= required_strength:
                    # Bonus points for exceeding requirements
                    score += 10 + (provider_strength.value - required_strength.value)
                else:
                    # Penalty for not meeting requirements
                    score -= 5 * (required_strength.value - provider_strength.value)

            provider_scores.append((provider, score))

        # Sort providers by score (highest first)
        provider_scores.sort(key=lambda x: x[1], reverse=True)

        # Log the selection results for debugging
        provider_names = [getattr(p[0], "name", str(p[0])) for p in provider_scores]
        provider_scores_str = [
            f"{name}:{score}"
            for (_, score), name in zip(provider_scores, provider_names, strict=False)
        ]
        logger.debug(
            f"Task-aware provider selection for {task_type}: {', '.join(provider_scores_str)}"
        )

        # Return sorted providers
        return [provider for provider, _ in provider_scores]


class ProviderGroup(ModelProvider):
    """A provider that encapsulates multiple providers with fallback capabilities.

    This class implements the ModelProvider interface and provides fallback
    between multiple provider instances. It includes health monitoring and
    various selection strategies.
    """

    def __init__(
        self,
        providers: list[ModelProvider],
        selection_strategy: Callable = ProviderSelectionStrategy.failover,
        name: str = "provider_group",
        retry_policy: RetryPolicy | None = None,
    ):
        """Initialize a provider group with a list of providers.

        Args:
            providers: List of provider instances
            selection_strategy: Function that orders providers for selection
            name: Name for this provider group
            retry_policy: Optional retry policy for fallback attempts

        Raises:
            ValueError: If providers list is empty
        """
        if not providers:
            raise ValueError("ProviderGroup requires at least one provider")

        self.providers = providers
        self.selection_strategy = selection_strategy
        self._name = name

        # Initialize health tracking
        self._health_status = dict.fromkeys(providers, True)
        self._error_counts = dict.fromkeys(providers, 0)
        self._last_success = {provider: time.time() for provider in providers}

        # Initialize context for stateful strategies
        self._context = {}

        # Initialize lock for thread safety
        self._lock = threading.RLock()

        # Retry policy for provider fallback
        if retry_policy is None:
            self.retry_policy = RetryPolicy(
                max_retries=len(providers) - 1,  # Try each provider once
                min_delay=0.1,  # Minimal delay between providers
                max_delay=2.0,  # Don't wait too long between attempts
                backoff_factor=2.0,  # Exponential backoff
                jitter=0.1,  # Add some randomness to delays
            )
        else:
            self.retry_policy = retry_policy

        # Get model name from first healthy provider, if any
        self._model_name = self._get_model_name()

    def _get_model_name(self) -> str:
        """Get the model name from the first healthy provider.

        Returns:
            Model name string or "unknown"
        """
        for provider in self.providers:
            if self._health_status.get(provider, True):
                return getattr(provider, "model_name", "unknown")

        # Fallback if no healthy providers
        return "multiple"

    @property
    def name(self) -> str:
        """Get the provider name."""
        return self._name

    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._model_name

    def _update_health(self, provider: ModelProvider, success: bool) -> None:
        """Update health status for a provider after a request.

        Args:
            provider: The provider instance
            success: Whether the request succeeded
        """
        with self._lock:
            if success:
                # Reset error count on success
                self._error_counts[provider] = 0
                self._last_success[provider] = time.time()

                # Mark as healthy if previously unhealthy
                if not self._health_status.get(provider, True):
                    logger.info(f"Provider {provider.name} recovered and is now healthy")
                    self._health_status[provider] = True
            else:
                # Increment error count
                self._error_counts[provider] = self._error_counts.get(provider, 0) + 1

                # Mark as unhealthy if too many consecutive errors
                if self._error_counts[provider] >= 3:
                    if self._health_status.get(provider, True):
                        logger.warning(
                            f"Provider {provider.name} marked unhealthy after {self._error_counts[provider]} consecutive errors"
                        )
                        self._health_status[provider] = False

    def _get_healthy_providers(self) -> list[ModelProvider]:
        """Get list of currently healthy providers.

        Returns:
            List of healthy provider instances
        """
        return [p for p in self.providers if self._health_status.get(p, True)]

    def _select_providers(self, request: ModelRequest) -> list[ModelProvider]:
        """Select and order providers for a request.

        Args:
            request: The model request

        Returns:
            Ordered list of providers to try
        """
        # Start with healthy providers only
        healthy_providers = self._get_healthy_providers()

        if not healthy_providers:
            # No healthy providers, try all providers as a last resort
            logger.warning("No healthy providers available, trying all providers")
            healthy_providers = self.providers.copy()

        # Apply selection strategy if it's task-aware
        if self.selection_strategy == TaskAwareSelectionStrategy.select:
            return self.selection_strategy(healthy_providers, request, self._context)

        # Otherwise apply standard provider ordering strategy
        return self.selection_strategy(healthy_providers, self._context)

    @traced(name="provider_group_generate")
    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response with provider fallback.

        This method tries each provider in order until one succeeds or all fail.

        Args:
            request: The model request

        Returns:
            Response from the successful provider

        Raises:
            ProviderError: If all providers fail
        """
        # Select providers to try
        providers_to_try = self._select_providers(request)

        if not providers_to_try:
            raise ProviderError("No providers available for request")

        # Initialize retry state
        retry_state = RetryState(
            attempt=0,
            max_retries=min(self.retry_policy.max_retries, len(providers_to_try) - 1),
            retry_policy=self.retry_policy,
        )

        # Keep track of all errors for detailed failure reporting
        all_errors = []

        # Try each provider until success or all fail
        for i, provider in enumerate(providers_to_try):
            try:
                logger.debug(f"Trying provider {provider.name} ({i + 1}/{len(providers_to_try)})")
                response = provider.generate(request)

                # Update health status on success
                self._update_health(provider, True)

                # Return successful response
                return response

            except Exception as e:
                # Update health status on failure
                self._update_health(provider, False)

                # Record error
                error_msg = f"Provider {provider.name} failed: {e!s}"
                logger.warning(error_msg)
                all_errors.append((provider, e))

                # Stop if this was the last provider
                if i >= len(providers_to_try) - 1:
                    break

                # Calculate delay before next attempt
                if self.retry_policy.enabled and i < len(providers_to_try) - 1:
                    retry_state.attempt = i
                    delay = calculate_retry_delay(retry_state)

                    if delay > 0:
                        logger.debug(f"Waiting {delay:.2f}s before trying next provider")
                        time.sleep(delay)

        # All providers failed, raise detailed error
        if all_errors:
            error_details = "; ".join(
                [f"{getattr(p, 'name', str(p))}: {e!s}" for p, e in all_errors]
            )
            raise ProviderError(f"All providers failed: {error_details}")
        else:
            raise ProviderError("No providers attempted the request")

    @traced(name="provider_group_stream")
    def generate_stream(self, request: ModelRequest) -> tuple[ModelResponse, StreamHandler]:
        """Generate a streaming response with provider fallback.

        This method tries each provider in order until one succeeds or all fail.

        Args:
            request: The model request

        Returns:
            Tuple of initial response and stream handler

        Raises:
            ProviderError: If all providers fail
        """
        # Select providers to try
        providers_to_try = self._select_providers(request)

        if not providers_to_try:
            raise ProviderError("No providers available for request")

        # Initialize retry state
        retry_state = RetryState(
            attempt=0,
            max_retries=min(self.retry_policy.max_retries, len(providers_to_try) - 1),
            retry_policy=self.retry_policy,
        )

        # Keep track of all errors for detailed failure reporting
        all_errors = []

        # Try each provider until success or all fail
        for i, provider in enumerate(providers_to_try):
            try:
                logger.debug(
                    f"Trying provider {provider.name} for streaming ({i + 1}/{len(providers_to_try)})"
                )
                response, stream_handler = provider.generate_stream(request)

                # Update health status on success
                self._update_health(provider, True)

                # Return successful response
                return response, stream_handler

            except Exception as e:
                # Update health status on failure
                self._update_health(provider, False)

                # Record error
                error_msg = f"Provider {provider.name} failed streaming: {e!s}"
                logger.warning(error_msg)
                all_errors.append((provider, e))

                # Stop if this was the last provider
                if i >= len(providers_to_try) - 1:
                    break

                # Calculate delay before next attempt
                if self.retry_policy.enabled and i < len(providers_to_try) - 1:
                    retry_state.attempt = i
                    delay = calculate_retry_delay(retry_state)

                    if delay > 0:
                        logger.debug(
                            f"Waiting {delay:.2f}s before trying next provider for streaming"
                        )
                        time.sleep(delay)

        # All providers failed, raise detailed error
        if all_errors:
            error_details = "; ".join(
                [f"{getattr(p, 'name', str(p))}: {e!s}" for p, e in all_errors]
            )
            raise ProviderError(f"All providers failed streaming: {error_details}")
        else:
            raise ProviderError("No providers attempted the streaming request")

    def get_available_models(self) -> list[str]:
        """Get a list of all available models across all providers.

        Returns:
            List of model names
        """
        all_models = set()

        for provider in self.providers:
            try:
                # Get models from this provider
                models = provider.get_available_models()
                all_models.update(models)
            except Exception as e:
                logger.warning(f"Failed to get models from provider {provider.name}: {e!s}")

        return sorted(list(all_models))

    def calculate_token_usage(self, request: ModelRequest, response: Any) -> TokenUsage:
        """Calculate token usage for a request and response.

        For the provider group, this delegates to the provider that generated the response.
        The implementation assumes the response contains information about which provider
        was used to generate it.

        Args:
            request: The model request.
            response: The raw response from the provider API.

        Returns:
            A TokenUsage object with token counts.
        """
        # If the response has provider information, use that provider's implementation
        provider_name = response.get("provider", "") if isinstance(response, dict) else ""

        # Find the provider that generated this response
        for provider in self.providers:
            if provider.name == provider_name:
                try:
                    return provider.calculate_token_usage(request, response)
                except Exception as e:
                    logger.warning(f"Error calculating token usage with {provider.name}: {e}")
                    break

        # Fallback to using the first provider in the list
        if self.providers:
            try:
                return self.providers[0].calculate_token_usage(request, response)
            except Exception as e:
                logger.warning(f"Error calculating token usage with fallback provider: {e}")

        # Last resort fallback
        return TokenUsage(
            input_tokens=len(str(request.messages)) // 4,  # Very rough approximation
            output_tokens=len(str(response)) // 4 if response else 0,  # Very rough approximation
            total_tokens=0,  # Will be calculated in __post_init__
        )

    def calculate_cost(self, usage: TokenUsage, model: str) -> CostEstimate:
        """Calculate approximate cost based on token usage.

        Delegates to the provider whose model was used, or uses a reasonable fallback.

        Args:
            usage: Token usage statistics.
            model: The model used for the request.

        Returns:
            A CostEstimate with input, output, and total costs.
        """
        # Try to find which provider owns this model
        for provider in self.providers:
            # First check if this provider's model matches
            if provider.model_name == model:
                try:
                    return provider.calculate_cost(usage, model)
                except Exception as e:
                    logger.warning(f"Error calculating cost with {provider.name}: {e}")
                    break

        # Fallback to using the first provider in the list
        if self.providers:
            try:
                return self.providers[0].calculate_cost(usage, model)
            except Exception as e:
                logger.warning(f"Error calculating cost with fallback provider: {e}")

        # Last resort fallback - generic low cost estimate
        return CostEstimate(
            input_cost=usage.input_tokens * 0.000001,  # $0.001 per 1000 tokens
            output_cost=usage.output_tokens * 0.000002,  # $0.002 per 1000 tokens
            total_cost=0,  # Will be calculated in __post_init__
        )

    def validate_api_key(self) -> bool:
        """Validate API keys for all providers.

        Returns:
            True if at least one provider has a valid API key
        """
        any_valid = False

        for provider in self.providers:
            try:
                valid = provider.validate_api_key()
                if valid:
                    any_valid = True
            except Exception as e:
                logger.warning(f"Error validating API key for {provider.name}: {e!s}")

        return any_valid

    def get_capability_strength(self, capability: str) -> CapabilityStrength:
        """Get the strength level of a specific capability.

        Returns the maximum capability strength across all healthy providers.

        Args:
            capability: The capability name

        Returns:
            CapabilityStrength enum value
        """
        max_strength = CapabilityStrength.NONE

        # Get healthy providers
        healthy_providers = self._get_healthy_providers()

        for provider in healthy_providers:
            # Get provider's strength for this capability
            provider_strength = CapabilityStrength.NONE

            # Try to get capability strength from provider if method exists
            if hasattr(provider, "get_capability_strength"):
                try:
                    provider_strength = provider.get_capability_strength(capability)
                except Exception as e:
                    logger.warning(
                        f"Error getting capability {capability} from {provider.name}: {e!s}"
                    )

            # Update max strength
            if provider_strength > max_strength:
                max_strength = provider_strength

        return max_strength
