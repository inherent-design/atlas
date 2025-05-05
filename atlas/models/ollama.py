"""
Ollama model provider implementation for Atlas.

This module provides integration with Ollama for local model inference.
"""

import logging
import json
from typing import List, Dict, Any, Optional, Tuple, Union

from atlas.core.telemetry import traced, TracedClass
from atlas.core import env
from atlas.models.base import (
    ModelProvider,
    ModelRequest,
    ModelResponse,
    TokenUsage,
    CostEstimate,
)

logger = logging.getLogger(__name__)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    logger.warning("Requests package not installed. Install with 'uv add requests'")
    REQUESTS_AVAILABLE = False


class OllamaProvider(ModelProvider):
    """Ollama local model provider."""
    
    # Default Ollama API endpoint
    DEFAULT_API_ENDPOINT = "http://localhost:11434/api"
    
    def __init__(
        self,
        model_name: str = "llama3",
        max_tokens: int = 2000,
        api_endpoint: Optional[str] = None,
        **kwargs: Any,
    ):
        """Initialize the Ollama provider.
        
        Args:
            model_name: Name of the Ollama model to use.
            max_tokens: Maximum tokens for model generation.
            api_endpoint: URL of the Ollama API endpoint.
            **kwargs: Additional provider-specific parameters.
        
        Raises:
            ValueError: If the Requests package is not installed.
        """
        # Check if Requests is available
        if not REQUESTS_AVAILABLE:
            raise ValueError("Requests package is not installed")
        
        self._model_name = model_name
        self._max_tokens = max_tokens
        
        # Get API endpoint from env module or use default
        self._api_endpoint = api_endpoint or env.get_string(
            "OLLAMA_API_ENDPOINT", 
            default=self.DEFAULT_API_ENDPOINT
        )
        
        # Normalize API endpoint (remove trailing slash)
        self._api_endpoint = self._api_endpoint.rstrip("/")
        
        logger.debug(f"Initialized Ollama provider with model {model_name} at {self._api_endpoint}")
        
        # Store additional parameters
        self._additional_params = kwargs
    
    @property
    def name(self) -> str:
        """Get the name of the provider.
        
        Returns:
            The provider's name as a string.
        """
        return "ollama"
    
    def validate_api_key(self) -> bool:
        """Validate that the API endpoint is accessible.
        
        Returns:
            True if the API endpoint is accessible, False otherwise.
        """
        # For Ollama, we're actually validating the server availability
        # rather than an API key
        try:
            # Try to get the Ollama version
            response = requests.get(f"{self._api_endpoint}/version", timeout=2)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Failed to connect to Ollama API at {self._api_endpoint}: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get a list of available models for this provider.
        
        Returns:
            A list of model identifiers.
        """
        try:
            # Get models from API
            response = requests.get(f"{self._api_endpoint}/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            else:
                logger.warning(f"Failed to get models from Ollama API (status code {response.status_code})")
                return ["llama3", "mistral", "gemma"]
        except Exception as e:
            logger.warning(f"Failed to get available models from Ollama API: {e}")
            # Return default models
            return ["llama3", "mistral", "gemma"]
    
    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from the model.
        
        Args:
            request: The model request.
            
        Returns:
            A ModelResponse containing the generated content and metadata.
        
        Raises:
            ValueError: If the model is not available.
        """
        # Ollama doesn't support the ChatML format directly, so we need to convert
        # the request to a prompt string
        
        # Get the model to use
        model = request.model or self._model_name
        
        # Build the prompt from messages
        system_content = None
        prompt_parts = []
        
        for message in request.messages:
            role = message.role.value
            if isinstance(message.content, str):
                content = message.content
            else:
                # Handle complex content - Ollama only supports text
                content = message.content.text if hasattr(message.content, "text") else str(message.content)
            
            if role == "system":
                system_content = content
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
            elif role == "function":
                # Ollama doesn't support function calls, so we include them as user messages
                prompt_parts.append(f"Function ({message.name}): {content}")
        
        # Add final user prompt if not already included
        if prompt_parts and not prompt_parts[-1].startswith("User:"):
            prompt_parts.append("Assistant:")
        
        # Build the final prompt
        prompt = "\n\n".join(prompt_parts)
        
        # Prepare the API request
        api_request = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": request.max_tokens or self._max_tokens,
            }
        }
        
        # Add system content if available
        if system_content:
            api_request["system"] = system_content
        
        # Add additional parameters
        if request.temperature is not None:
            api_request["options"]["temperature"] = request.temperature
        
        # Add any additional parameters from initialization
        for key, value in self._additional_params.items():
            if key not in api_request and key != "options":
                api_request[key] = value
            elif key == "options":
                for option_key, option_value in value.items():
                    if option_key not in api_request["options"]:
                        api_request["options"][option_key] = option_value
        
        logger.debug(f"Calling Ollama API with model {model}")
        
        # Make the API call
        try:
            response = requests.post(
                f"{self._api_endpoint}/generate",
                json=api_request,
                timeout=60,
            )
            
            if response.status_code != 200:
                raise ValueError(f"Ollama API returned status code {response.status_code}: {response.text}")
            
            response_data = response.json()
            
            # Extract content
            content = response_data.get("response", "")
            
            # Calculate token usage (estimated)
            usage = self.calculate_token_usage(request, response_data)
            
            # Calculate cost (always 0 for local models)
            cost = self.calculate_cost(usage, model)
            
            # Create the response
            model_response = ModelResponse(
                content=content,
                model=model,
                provider=self.name,
                usage=usage,
                cost=cost,
                finish_reason=response_data.get("done", True) and "stop" or "unknown",
                raw_response=response_data,
            )
            
            return model_response
            
        except Exception as e:
            logger.error(f"Error calling Ollama API: {e}")
            raise ValueError(f"Error calling Ollama API: {e}")
    
    def calculate_token_usage(self, request: ModelRequest, response: Any) -> TokenUsage:
        """Calculate token usage for a request and response.
        
        Args:
            request: The model request.
            response: The raw response from the Ollama API.
            
        Returns:
            A TokenUsage object with token counts.
        """
        # Ollama doesn't provide token counts in responses, so we estimate
        prompt_tokens = response.get("prompt_eval_count", 0)
        eval_tokens = response.get("eval_count", 0)
        
        # If prompt tokens is 0, estimate based on character count
        if prompt_tokens == 0 and isinstance(request.messages, list):
            # Rough estimate: ~4 characters per token
            prompt_text = "".join([
                str(m.content) if isinstance(m.content, str) else 
                (m.content.text if hasattr(m.content, "text") else str(m.content))
                for m in request.messages
            ])
            prompt_tokens = len(prompt_text) // 4
        
        # If eval tokens is 0, estimate based on character count
        if eval_tokens == 0 and "response" in response:
            # Rough estimate: ~4 characters per token
            eval_tokens = len(response["response"]) // 4
        
        return TokenUsage(
            input_tokens=prompt_tokens,
            output_tokens=eval_tokens,
            total_tokens=prompt_tokens + eval_tokens,
        )
    
    def calculate_cost(self, usage: TokenUsage, model: str) -> CostEstimate:
        """Calculate approximate cost based on token usage.
        
        For Ollama, this is always 0 as it uses local models.
        
        Args:
            usage: Token usage statistics.
            model: The model used for the request.
            
        Returns:
            A CostEstimate with input, output, and total costs (all 0).
        """
        # Local models have no API cost
        return CostEstimate(
            input_cost=0.0,
            output_cost=0.0,
            total_cost=0.0,
        )
    
    def stream(self, request: ModelRequest) -> Tuple[ModelResponse, Any]:
        """Stream a response from the model.
        
        Args:
            request: The model request.
            
        Returns:
            A tuple of (final ModelResponse, stream iterator).
        """
        # TODO: Implement streaming
        # This is a placeholder implementation similar to generate but with streaming
        
        # Get the model to use
        model = request.model or self._model_name
        
        # Build the prompt from messages
        system_content = None
        prompt_parts = []
        
        for message in request.messages:
            role = message.role.value
            if isinstance(message.content, str):
                content = message.content
            else:
                # Handle complex content - Ollama only supports text
                content = message.content.text if hasattr(message.content, "text") else str(message.content)
            
            if role == "system":
                system_content = content
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
            elif role == "function":
                prompt_parts.append(f"Function ({message.name}): {content}")
        
        # Add final user prompt if not already included
        if prompt_parts and not prompt_parts[-1].startswith("User:"):
            prompt_parts.append("Assistant:")
        
        # Build the final prompt
        prompt = "\n\n".join(prompt_parts)
        
        # Prepare the API request
        api_request = {
            "model": model,
            "prompt": prompt,
            "stream": True,  # Enable streaming
            "options": {
                "num_predict": request.max_tokens or self._max_tokens,
            }
        }
        
        # Add system content if available
        if system_content:
            api_request["system"] = system_content
        
        # Add additional parameters
        if request.temperature is not None:
            api_request["options"]["temperature"] = request.temperature
        
        # Add any additional parameters from initialization
        for key, value in self._additional_params.items():
            if key not in api_request and key != "options":
                api_request[key] = value
            elif key == "options":
                for option_key, option_value in value.items():
                    if option_key not in api_request["options"]:
                        api_request["options"][option_key] = option_value
        
        logger.debug(f"Calling Ollama API with streaming for model {model}")
        
        # Make the API call
        try:
            response = requests.post(
                f"{self._api_endpoint}/generate",
                json=api_request,
                timeout=60,
                stream=True,
            )
            
            if response.status_code != 200:
                raise ValueError(f"Ollama API returned status code {response.status_code}: {response.text}")
            
            # Return a partial response and the stream
            # The caller will need to handle processing the stream
            return ModelResponse(
                content="",  # Will be populated during streaming
                model=model,
                provider=self.name,
                usage=TokenUsage(),  # Will be populated at end of stream
                cost=CostEstimate(),  # Will be populated at end of stream
            ), response
            
        except Exception as e:
            logger.error(f"Error calling Ollama API for streaming: {e}")
            raise ValueError(f"Error calling Ollama API for streaming: {e}")