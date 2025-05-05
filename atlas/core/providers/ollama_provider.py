"""
Ollama provider implementation for Atlas.

This module implements the Ollama provider for local language models.
"""

import json
import requests
from typing import Dict, List, Any, Optional, Tuple

from atlas.core.providers.base import ModelProvider, ModelResponse, MessageContent

class OllamaProvider(ModelProvider):
    """Ollama language model provider for local models."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "llama3",
        max_tokens: int = 2000,
    ):
        """Initialize Ollama provider.

        Args:
            base_url: Base URL for the Ollama API.
            model_name: Name of the Ollama model to use.
            max_tokens: Maximum number of tokens in responses.
        """
        # Ollama API settings
        self.base_url = base_url
        self.model_name = model_name
        self.max_tokens = max_tokens

    def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
    ) -> ModelResponse:
        """Generate a response using the Ollama model.

        Args:
            system_prompt: System prompt to guide the model.
            messages: List of message dictionaries with 'role' and 'content'.
            max_tokens: Maximum number of tokens in response. If None, use instance default.

        Returns:
            ModelResponse containing the generated text and usage statistics.
        """
        # Format messages for Ollama
        formatted_messages = []
        
        # Add system message
        if system_prompt:
            formatted_messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add conversation messages
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            # Ollama supports user and assistant roles
            if role in ["user", "assistant"]:
                formatted_messages.append({
                    "role": role,
                    "content": content
                })
        
        # Prepare request payload
        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "options": {
                "max_tokens": max_tokens or self.max_tokens,
            },
            "stream": False,
        }
        
        # Send request to Ollama API
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract content from response
            content = result.get("message", {}).get("content", "")
            
            # Extract token usage if available
            prompt_eval_count = result.get("prompt_eval_count", 0)
            eval_count = result.get("eval_count", 0)
            
            # Return standardized response
            return ModelResponse(
                content=MessageContent(text=content),
                model=self.model_name,
                usage={
                    "input_tokens": prompt_eval_count,
                    "output_tokens": eval_count,
                    "total_tokens": prompt_eval_count + eval_count,
                },
                provider="ollama",
            )
        
        except requests.RequestException as e:
            raise RuntimeError(f"Ollama API error: {str(e)}")
    
    def calculate_cost(self, usage: Dict[str, int]) -> Tuple[float, float, float]:
        """Calculate approximate cost based on token usage.
        
        Args:
            usage: Dictionary with token usage statistics.
            
        Returns:
            Tuple of (input_cost, output_cost, total_cost) in USD.
        """
        # Ollama runs locally, so costs are zero
        return 0.0, 0.0, 0.0
        
    def list_models(self) -> List[str]:
        """List available models from Ollama.
        
        Returns:
            List of model names available in the local Ollama instance.
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            result = response.json()
            
            # Extract model names
            models = [model["name"] for model in result.get("models", [])]
            return models
            
        except requests.RequestException as e:
            raise RuntimeError(f"Error listing Ollama models: {str(e)}")
            
    def is_available(self) -> bool:
        """Check if Ollama API is available.
        
        Returns:
            Boolean indicating if Ollama is running and accessible.
        """
        try:
            response = requests.get(f"{self.base_url}/api/version")
            return response.status_code == 200
        except:
            return False