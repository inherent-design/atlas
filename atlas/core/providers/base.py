"""
Base model provider interface for Atlas.

This module defines the interface for model providers.
"""

import abc
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple, Union


@dataclass
class MessageContent:
    """Content of a message from the model."""

    text: str
    """The text content of the message."""


@dataclass
class ModelResponse:
    """Response from a language model."""

    content: MessageContent
    """The content of the response."""

    model: str
    """The name of the model that generated the response."""

    usage: Dict[str, int]
    """Token usage statistics."""

    provider: str
    """The provider that generated the response."""

    # Additional fields that might be useful for specific providers
    additional_data: Dict[str, Any] = None


class ModelProvider(abc.ABC):
    """Abstract base class for model providers."""

    @abc.abstractmethod
    def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
    ) -> ModelResponse:
        """Generate a response from the model.

        Args:
            system_prompt: System prompt to guide the model.
            messages: List of message dictionaries with 'role' and 'content'.
            max_tokens: Maximum number of tokens to generate.

        Returns:
            ModelResponse containing the generated content and usage statistics.
        """
        pass

    @abc.abstractmethod
    def calculate_cost(self, usage: Dict[str, int]) -> Tuple[float, float, float]:
        """Calculate approximate cost based on token usage.

        Args:
            usage: Dictionary with token usage statistics.

        Returns:
            Tuple of (input_cost, output_cost, total_cost) in USD.
        """
        pass
