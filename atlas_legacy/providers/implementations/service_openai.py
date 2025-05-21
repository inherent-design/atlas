"""
Service-enabled OpenAI provider implementation.

This module provides a service-enabled implementation of the OpenAI provider
that leverages the core services layer for enhanced capabilities.
"""

import logging
import threading
import time
from typing import Any

from atlas.core import env
from atlas.core.errors import ValidationError
from atlas.core.services.registry import ServiceRegistry
from atlas.core.telemetry import traced
from atlas.providers.errors import (
    ProviderAuthenticationError,
    ProviderValidationError,
)
from atlas.providers.implementations.openai import (
    OPENAI_AVAILABLE,
    OpenAIProvider,
    OpenAIStreamHandler,
)
from atlas.providers.messages import (
    CostEstimate,
    ModelRequest,
    ModelResponse,
    TokenUsage,
)
from atlas.providers.service_enabled import ServiceEnabledProvider

# Create a logger for this module
logger = logging.getLogger(__name__)


class ServiceEnabledOpenAIProvider(ServiceEnabledProvider):
    """Service-enabled implementation of the OpenAI provider.

    This class integrates the OpenAIProvider with the service-enabled
    architecture to provide state management, event publication, and
    command-based operations.
    """

    def __init__(
        self,
        model_name: str = "gpt-4.1",
        max_tokens: int = 2000,
        api_key: str | None = None,
        service_registry: ServiceRegistry | None = None,
        options: dict[str, Any] | None = None,
        **kwargs: Any,
    ):
        """Initialize the service-enabled OpenAI provider.

        Args:
            model_name: Name of the OpenAI model to use.
            max_tokens: Maximum tokens for model generation.
            api_key: Optional API key (defaults to OPENAI_API_KEY environment variable).
            service_registry: Optional service registry to use.
            options: Optional provider-specific options and capabilities.
            **kwargs: Additional provider-specific parameters.

        Raises:
            ProviderValidationError: If the OpenAI API key is missing, the SDK is not installed,
                                    or if the requested model is not compatible.
        """
        # Initialize the ServiceEnabledProvider
        ServiceEnabledProvider.__init__(
            self,
            provider_type="openai",
            model_name=model_name,
            api_key=api_key,
            service_registry=service_registry,
            **kwargs,
        )

        # Check if OpenAI SDK is installed
        if not OPENAI_AVAILABLE:
            raise ProviderValidationError(
                "OpenAI SDK not installed. Install with 'uv add openai'",
                provider="openai",
            )

        # Get API key from environment if not provided
        self.api_key = api_key or env.get_api_key("openai")
        if not self.api_key:
            raise ProviderAuthenticationError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.",
                provider="openai",
            )

        self.max_tokens = max_tokens
        self.organization = kwargs.get("organization") or env.get_string("OPENAI_ORGANIZATION")

        # Process options dictionary
        self.options = {}
        self.capabilities = {}

        # Apply provider-specific options
        if options:
            try:
                # Import here to avoid circular imports
                from atlas.schemas.options import openai_options_schema

                # Validate options using schema
                validated_options = openai_options_schema.load(options)

                # Extract capabilities specifically
                if "capabilities" in validated_options:
                    self.capabilities = validated_options.pop("capabilities")

                # Store the rest of the options
                self.options = validated_options
            except ValidationError as e:
                raise ProviderValidationError(
                    f"Invalid OpenAI provider options: {e}",
                    provider="openai",
                    details={"validation_errors": e.messages},
                )

        # Apply any other kwargs to options
        for key, value in kwargs.items():
            if key not in ["organization"]:  # Skip already processed keys
                self.options[key] = value

        # Client will be created lazily when needed
        self._client = None
        self._client_lock = threading.RLock()

        # Add provider-specific capabilities to the state
        self._update_state(
            {
                "provider_capabilities": self.capabilities,
                "available_models": self.get_available_models(),
                "options": self.options,
            }
        )

        logger.debug(f"Created ServiceEnabledOpenAIProvider with model {model_name}")

    @property
    def name(self) -> str:
        """Get the provider name."""
        return "openai"

    @property
    def client(self) -> "OpenAI":
        """Get the OpenAI API client with lazy initialization.

        Returns:
            An initialized OpenAI client.
        """
        if self._client is None:
            try:
                from openai import OpenAI

                with self._client_lock:
                    if self._client is None:
                        client_kwargs = {"api_key": self.api_key}
                        if self.organization:
                            client_kwargs["organization"] = self.organization
                        self._client = OpenAI(**client_kwargs)
            except ImportError:
                raise ProviderValidationError(
                    "OpenAI SDK not installed. Install with 'uv add openai'",
                    provider="openai",
                )

        return self._client

    def _convert_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert Atlas message format to OpenAI's format.

        Args:
            messages: List of message objects.

        Returns:
            List of messages in OpenAI's format.
        """
        # Import the OpenAI provider for implementation

        # Create temporary instance to use its _convert_messages method
        temp_provider = OpenAIProvider(model_name=self.model_name, api_key=self.api_key)

        return temp_provider._convert_messages(messages)

    def _generate_implementation(self, request: dict[str, Any]) -> dict[str, Any]:
        """Implement the generate method for OpenAI.

        Args:
            request: The generation request.

        Returns:
            The generation response.
        """
        # Create ModelRequest from the request dict
        model_request = ModelRequest.from_dict(request)

        # Publish event for generation start
        self._publish_event("generate.start", {"request": request, "model": self.model_name})

        try:
            # Convert messages to OpenAI format
            messages = self._convert_messages(model_request.messages)

            # Get parameters from request metadata or default
            request_metadata = getattr(model_request, "metadata", {}) or {}

            # Combine options with precedence: request parameters > instance options > defaults
            max_tokens = request_metadata.get(
                "max_tokens", self.options.get("max_tokens", self.max_tokens)
            )

            temperature = request_metadata.get("temperature", self.options.get("temperature", 0.7))

            # Prepare request parameters
            params = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            # Add additional options from self.options that aren't set above
            for key, value in self.options.items():
                if key not in ["max_tokens", "temperature", "capabilities"]:
                    params[key] = value

            # Add system prompt from request if available
            if model_request.system_prompt:
                # Insert a system message at the beginning if needed
                if not any(m.get("role") == "system" for m in messages):
                    messages.insert(0, {"role": "system", "content": model_request.system_prompt})

            # Track generation start time
            start_time = time.time()

            # Make the API request
            response = self.client.chat.completions.create(**params)

            # Track generation time
            generation_time = time.time() - start_time

            # Extract response content
            content = response.choices[0].message.content

            # Extract token usage
            usage = TokenUsage.from_provider_response(response=response, provider_name="openai")

            # Calculate cost based on usage
            cost = None
            if usage:
                try:
                    cost = self.calculate_cost(usage, self.model_name)
                except Exception as cost_err:
                    logger.debug(f"Error calculating cost: {cost_err}")

            # Create the response
            model_response = ModelResponse.create_direct(
                provider="openai",
                model=self.model_name,
                content=content,
                usage=usage,
                cost=cost,
                raw_response=response.model_dump(),
                finish_reason=response.choices[0].finish_reason,
            )

            # Update state with usage information
            self._update_state(
                {
                    "total_tokens": self._state.data.get("total_tokens", 0)
                    + (usage.total_tokens if usage else 0),
                    "last_generation_time": generation_time,
                    "status": "ready",
                }
            )

            # Publish event for generation completion
            self._publish_event(
                "generate.end",
                {
                    "request": request,
                    "response": content,
                    "token_count": usage.total_tokens if usage else 0,
                    "generation_time": generation_time,
                },
            )

            return model_response.to_dict()

        except Exception as e:
            # Publish event for generation error
            self._publish_event(
                "generate.error",
                {"request": request, "error": str(e), "error_type": e.__class__.__name__},
            )

            # Re-raise the exception to be handled by the command
            raise

    def _stream_implementation(self, request: dict[str, Any]) -> Any:
        """Implement the stream method for OpenAI.

        Args:
            request: The generation request.

        Returns:
            A streamable object that yields response chunks.
        """
        # Create ModelRequest from the request dict
        model_request = ModelRequest.from_dict(request)

        # Publish event for stream start
        self._publish_event("stream.start", {"request": request, "model": self.model_name})

        try:
            # Convert messages to OpenAI format
            messages = self._convert_messages(model_request.messages)

            # Get parameters from request metadata or default
            request_metadata = getattr(model_request, "metadata", {}) or {}

            # Combine options with precedence: request parameters > instance options > defaults
            max_tokens = request_metadata.get(
                "max_tokens", self.options.get("max_tokens", self.max_tokens)
            )

            temperature = request_metadata.get("temperature", self.options.get("temperature", 0.7))

            # Prepare request parameters
            params = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True,
            }

            # Add additional options from self.options that aren't set above
            for key, value in self.options.items():
                if key not in ["max_tokens", "temperature", "capabilities", "stream"]:
                    params[key] = value

            # Add system prompt from request if available
            if model_request.system_prompt:
                # Insert a system message at the beginning if needed
                if not any(m.get("role") == "system" for m in messages):
                    messages.insert(0, {"role": "system", "content": model_request.system_prompt})

            # Make the API request to get stream
            stream_response = self.client.chat.completions.create(**params)

            # Update state to indicate streaming is active
            self._update_state({"is_streaming": True, "status": "streaming"})

            # Create initial response
            initial_response = ModelResponse.create_direct(
                provider="openai",
                model=self.model_name,
                content="",  # Empty initial content, will be updated during streaming
                usage=TokenUsage.create_direct(input_tokens=0, output_tokens=0, total_tokens=0),
                raw_response={
                    "provider": "openai",
                    "model": self.model_name,
                    "streaming": True,
                },
            )

            # Create stream handler
            request_id = getattr(stream_response, "id", "unknown")
            handler = OpenAIStreamHandler(
                provider=self,
                model=self.model_name,
                initial_response=initial_response,
                iterator=stream_response,
                request_id=request_id,
            )

            # Store the request on the handler to ensure input token counting works
            handler.request = model_request

            # Start streaming in background
            handler.start()

            # Return the handler
            return handler

        except Exception as e:
            # Publish event for stream error
            self._publish_event(
                "stream.error",
                {"request": request, "error": str(e), "error_type": e.__class__.__name__},
            )

            # Re-raise the exception to be handled by the command
            raise

    def _validate_implementation(self, request: dict[str, Any]) -> bool:
        """Implement the validate method for OpenAI.

        Args:
            request: The request to validate.

        Returns:
            True if the request is valid, False otherwise.
        """
        try:
            # Create ModelRequest from the request dict
            model_request = ModelRequest.from_dict(request)

            # Publish event for validation start
            self._publish_event("validate.start", {"request": request})

            # Validate model name
            if self.model_name not in self.get_available_models():
                logger.warning(f"Model {self.model_name} not in available models list")
                self._publish_event(
                    "validate.failure",
                    {"request": request, "reason": f"Model {self.model_name} not available"},
                )
                return False

            # Validate messages format
            if not model_request.messages:
                logger.warning("No messages in request")
                self._publish_event(
                    "validate.failure", {"request": request, "reason": "No messages in request"}
                )
                return False

            # Attempt to convert messages to validate format
            try:
                messages = self._convert_messages(model_request.messages)
                if not messages:
                    logger.warning("Failed to convert messages to OpenAI format")
                    self._publish_event(
                        "validate.failure",
                        {
                            "request": request,
                            "reason": "Failed to convert messages to OpenAI format",
                        },
                    )
                    return False
            except Exception as e:
                logger.warning(f"Error converting messages: {e}")
                self._publish_event(
                    "validate.failure",
                    {"request": request, "reason": f"Error converting messages: {e}"},
                )
                return False

            # Validate parameters
            metadata = getattr(model_request, "metadata", {}) or {}

            # Check max_tokens
            max_tokens = metadata.get("max_tokens", self.options.get("max_tokens", self.max_tokens))
            if max_tokens <= 0:
                logger.warning(f"Invalid max_tokens: {max_tokens}")
                self._publish_event(
                    "validate.failure",
                    {"request": request, "reason": f"Invalid max_tokens: {max_tokens}"},
                )
                return False

            # Check temperature
            temperature = metadata.get("temperature", self.options.get("temperature", 0.7))
            if not 0 <= temperature <= 1:
                logger.warning(f"Invalid temperature: {temperature}")
                self._publish_event(
                    "validate.failure",
                    {"request": request, "reason": f"Invalid temperature: {temperature}"},
                )
                return False

            # Publish event for validation success
            self._publish_event("validate.success", {"request": request})

            return True

        except Exception as e:
            # Publish event for validation error
            self._publish_event(
                "validate.error",
                {"request": request, "error": str(e), "error_type": e.__class__.__name__},
            )

            # Log the error
            logger.error(f"Error validating request: {e}", exc_info=True)

            return False

    def _cancel_implementation(self, request_id: str) -> bool:
        """Implement the cancel method for OpenAI.

        Args:
            request_id: The ID of the request to cancel.

        Returns:
            True if the request was cancelled, False otherwise.
        """
        # Publish event for cancellation attempt
        self._publish_event("cancel.attempt", {"request_id": request_id})

        try:
            # Currently OpenAI doesn't provide a direct way to cancel a request
            # But we can update our internal state to reflect the cancellation

            # Update state
            self._update_state({"is_streaming": False, "status": "ready"})

            # Publish event for cancellation result
            self._publish_event("cancel.success", {"request_id": request_id})

            # Return True to indicate we've done everything we can
            return True

        except Exception as e:
            # Publish event for cancellation error
            self._publish_event(
                "cancel.error",
                {"request_id": request_id, "error": str(e), "error_type": e.__class__.__name__},
            )

            # Log the error
            logger.error(f"Error cancelling request {request_id}: {e}", exc_info=True)

            return False

    def get_available_models(self) -> list[str]:
        """Get a list of available models for this provider.

        Returns:
            List of model names.
        """
        # Import the OpenAIProvider for its implementation

        # Create temporary instance to use its get_available_models method
        temp_provider = OpenAIProvider(model_name=self.model_name, api_key=self.api_key)

        return temp_provider.get_available_models()

    @traced(name="openai_provider_validate_api_key")
    def validate_api_key(self) -> bool:
        """Validate the OpenAI API key.

        Returns:
            True if the API key is valid, False otherwise.
        """
        try:
            # Publish event for validation attempt
            self._publish_event("validate_api_key.attempt", {})

            # Make a minimal API call to validate the key
            # Use a cheaper model with minimal tokens
            self.client.chat.completions.create(
                model="gpt-3.5-turbo", messages=[{"role": "user", "content": "hello"}], max_tokens=1
            )

            # Publish event for validation success
            self._publish_event("validate_api_key.success", {})

            return True
        except Exception as e:
            # Publish event for validation failure
            self._publish_event(
                "validate_api_key.failure", {"error": str(e), "error_type": e.__class__.__name__}
            )

            logger.warning(f"OpenAI API key validation failed: {e}")
            return False

    def calculate_token_usage(self, request: ModelRequest, response: Any) -> TokenUsage:
        """Calculate token usage for a request and response.

        Args:
            request: The model request.
            response: The raw response from the OpenAI API.

        Returns:
            A TokenUsage object with token counts.
        """
        # Use our improved extraction method
        return TokenUsage.from_provider_response(response=response, provider_name="openai")

    def calculate_cost(self, usage: TokenUsage, model: str) -> CostEstimate:
        """Calculate cost for token usage.

        Args:
            usage: Token usage information.
            model: The model name.

        Returns:
            A CostEstimate with input, output, and total costs.
        """
        # Import the OpenAIProvider for its PRICING dictionary

        # Get pricing for the model, or use default
        pricing = OpenAIProvider.PRICING.get(model, OpenAIProvider.PRICING["default"])

        # Calculate costs per million tokens
        input_cost = (usage.input_tokens / 1000000) * pricing["input"]
        output_cost = (usage.output_tokens / 1000000) * pricing["output"]

        return CostEstimate.create_direct(
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=input_cost + output_cost,
        )

    def get_capability_strength(self, capability: str) -> int:
        """Get the capability strength for the current model.

        Args:
            capability: The capability name.

        Returns:
            Capability strength (0-4).
        """
        # Import the OpenAIProvider for implementation

        # Create temporary instance to use its get_capability_strength method
        temp_provider = OpenAIProvider(model_name=self.model_name, api_key=self.api_key)

        return temp_provider.get_capability_strength(capability)
