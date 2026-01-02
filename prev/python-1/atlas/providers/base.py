"""
Base LLM provider interface for Atlas.

This module defines the unified interface for all language model providers in Atlas,
providing a consistent API regardless of the underlying provider implementation.
"""

import abc
from typing import Any, ClassVar

from atlas.core.telemetry import TracedClass, traced
from atlas.providers.messages import CostEstimate, ModelRequest, ModelResponse, TokenUsage
from atlas.providers.reliability import ProviderCircuitBreaker, ProviderRetryConfig
from atlas.providers.streaming import StreamHandler


class ModelProvider(TracedClass, abc.ABC):
    """Abstract base class for language model providers.

    This interface defines the standard methods that all language model
    providers must implement, ensuring consistent behavior across different
    provider implementations.
    """

    # Default retry configuration for all providers
    DEFAULT_RETRY_CONFIG: ClassVar[ProviderRetryConfig] = ProviderRetryConfig(
        max_retries=3, initial_delay=1.0, backoff_factor=2.0, max_delay=60.0, jitter_factor=0.1
    )

    # Default circuit breaker configuration for all providers
    DEFAULT_CIRCUIT_BREAKER: ClassVar[ProviderCircuitBreaker] = ProviderCircuitBreaker(
        failure_threshold=5, recovery_timeout=60.0, test_requests=1
    )

    def __init__(
        self,
        retry_config: ProviderRetryConfig | None = None,
        circuit_breaker: ProviderCircuitBreaker | None = None,
    ):
        """Initialize the model provider with retry configuration.

        Args:
            retry_config: Custom retry configuration, or None to use the default
            circuit_breaker: Custom circuit breaker, or None to use the default
        """
        self.retry_config = retry_config or self.DEFAULT_RETRY_CONFIG
        self.circuit_breaker = circuit_breaker or self.DEFAULT_CIRCUIT_BREAKER
        super().__init__()

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Get the name of the provider.

        Returns:
            The provider's name as a string.
        """
        pass

    @property
    def model_name(self) -> str:
        """Get the name of the model.

        Returns:
            The model name as a string.

        Note:
            Providers should override this to return their specific model name.
            The default implementation falls back to the provider's internal storage.
        """
        # Try to get model name from various common attribute names
        for attr in ["_model_name", "model", "_model"]:
            if hasattr(self, attr):
                return getattr(self, attr)

        # Fall back to a generic name
        return "unnamed-model"

    @traced(name="provider_get_available_models")
    @abc.abstractmethod
    def get_available_models(self) -> list[str]:
        """Get a list of available models for this provider.

        Returns:
            A list of model identifiers.
        """
        pass

    @traced(name="provider_validate_api_key")
    @abc.abstractmethod
    def validate_api_key(self) -> bool:
        """Validate that the API key is set and valid.

        Returns:
            True if the API key is valid, False otherwise.
        """
        pass

    @traced(name="provider_validate_api_key_detailed")
    def validate_api_key_detailed(self) -> dict[str, Any]:
        """Validate API key with detailed information about the result.

        Returns:
            A dictionary with validation details:
            - valid: bool - Whether the key is valid
            - error: Optional[str] - Error message if validation failed
            - provider: str - Provider name
            - key_present: bool - Whether the key is present (but might be invalid)
        """
        try:
            # Try to validate the key
            valid = self.validate_api_key()

            # Build the response
            result = {
                "valid": valid,
                "provider": self.name,
                "key_present": bool(getattr(self, "_api_key", None)),
                "error": None,
            }

            if not valid:
                if not result["key_present"]:
                    result["error"] = f"No API key found for {self.name}"
                else:
                    result["error"] = f"API key for {self.name} is invalid"

            return result

        except Exception as e:
            # If validation throws an exception, capture it
            return {
                "valid": False,
                "provider": self.name,
                "key_present": bool(getattr(self, "_api_key", None)),
                "error": str(e),
            }

    @traced(name="provider_generate", log_args=True)
    @abc.abstractmethod
    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from the model.

        Args:
            request: The model request.

        Returns:
            A ModelResponse containing the generated content and metadata.
        """
        pass

    @traced(name="provider_calculate_token_usage")
    @abc.abstractmethod
    def calculate_token_usage(self, request: ModelRequest, response: Any) -> TokenUsage:
        """Calculate token usage for a request and response.

        Args:
            request: The model request.
            response: The raw response from the provider API.

        Returns:
            A TokenUsage object with token counts.
        """
        pass

    @traced(name="provider_calculate_cost")
    @abc.abstractmethod
    def calculate_cost(self, usage: TokenUsage, model: str) -> CostEstimate:
        """Calculate approximate cost based on token usage.

        Args:
            usage: Token usage statistics.
            model: The model used for the request.

        Returns:
            A CostEstimate with input, output, and total costs.
        """
        pass

    @traced(name="provider_stream")
    def stream(self, request: ModelRequest) -> tuple[ModelResponse, StreamHandler]:
        """Stream a response from the model (if supported).

        Args:
            request: The model request.

        Returns:
            A tuple of (final ModelResponse, StreamHandler).

        Raises:
            NotImplementedError: If streaming is not supported by this provider.
        """
        raise NotImplementedError(f"Streaming not supported by {self.name} provider")

    @traced(name="provider_get_capability_strength")
    def get_capability_strength(self, capability: str) -> int:
        """Get the strength level of a specific capability.

        Args:
            capability: The capability name.

        Returns:
            An integer representing the capability strength (0=None, 1=Basic,
            2=Moderate, 3=Strong, 4=Exceptional).
        """
        # Default implementation returns 0 (no capability)
        # Subclasses should override this to report their actual capabilities
        return 0
