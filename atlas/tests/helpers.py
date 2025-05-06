"""
Test helper functions for Atlas framework.

This module provides utilities and mock objects to make testing easier and more consistent.
"""

import os
from typing import Dict, Any, List, Optional
from unittest.mock import MagicMock

from atlas.core.config import AtlasConfig
from atlas.core.prompts import load_system_prompt


def create_mock_message_response(
    content: str, input_tokens: int = 100, output_tokens: int = 50
) -> MagicMock:
    """Create a mock Anthropic API message response.

    Args:
        content: The content text to include in the response.
        input_tokens: The number of input tokens to report in usage.
        output_tokens: The number of output tokens to report in usage.

    Returns:
        A MagicMock object that mimics an Anthropic API response.
    """
    # Import here to avoid circular import
    from atlas.models.base import CostEstimate

    # Create the main response mock
    mock_response = MagicMock()

    # Mock the content object
    mock_content = MagicMock()
    mock_content.text = content
    mock_response.content = [mock_content]

    # Mock the usage attribute for cost tracking
    mock_usage = MagicMock()
    mock_usage.input_tokens = input_tokens
    mock_usage.output_tokens = output_tokens
    mock_response.usage = mock_usage

    # Create a real CostEstimate object instead of a mock to handle string formatting
    input_cost = (input_tokens / 1000000) * 3
    output_cost = (output_tokens / 1000000) * 15
    mock_response.cost = CostEstimate(
        input_cost=input_cost,
        output_cost=output_cost,
        total_cost=input_cost + output_cost,
    )

    return mock_response


def create_mock_document(
    content: str, source: str = "test_document.md", relevance_score: float = 0.95
) -> Dict[str, Any]:
    """Create a mock document for knowledge base testing.

    Args:
        content: The document content.
        source: Source file name for the document.
        relevance_score: Relevance score for the document.

    Returns:
        A dictionary representing a document from the knowledge base.
    """
    return {
        "content": content,
        "metadata": {"source": source},
        "relevance_score": relevance_score,
    }


def create_test_config(
    anthropic_api_key: str = "mock_key",
    model_name: str = "claude-3-5-sonnet-20240620",
    max_tokens: int = 2000,
    worker_count: int = 3,
) -> AtlasConfig:
    """Create a test configuration for Atlas.

    Args:
        anthropic_api_key: API key for Anthropic.
        model_name: Model name to use.
        max_tokens: Maximum tokens for responses.
        worker_count: Number of worker agents.

    Returns:
        An AtlasConfig instance for testing.
    """
    return AtlasConfig(
        anthropic_api_key=anthropic_api_key,
        model_name=model_name,
        max_tokens=max_tokens,
        worker_count=worker_count,
    )


def setup_test_environment() -> None:
    """Set up the test environment with necessary environment variables."""
    # Set environment variables for testing
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key_for_testing"


def mock_anthropic_client() -> MagicMock:
    """Create a mock Anthropic client.

    Returns:
        A MagicMock object that mimics an Anthropic client.
    """
    mock_client = MagicMock()

    # Mock the messages.create method
    mock_create = MagicMock()
    mock_client.messages.create = mock_create

    # Set a default return value
    mock_response = create_mock_message_response("This is a mock response.")
    mock_create.return_value = mock_response

    return mock_client


def mock_knowledge_base(documents: Optional[List[Dict[str, Any]]] = None) -> MagicMock:
    """Create a mock knowledge base.

    Args:
        documents: Optional list of documents to return from retrieve method.

    Returns:
        A MagicMock object that mimics a KnowledgeBase.
    """
    mock_kb = MagicMock()

    # Set default documents if none provided
    if documents is None:
        documents = [
            create_mock_document("Sample document content", "document1.md", 0.95)
        ]

    # Mock the retrieve method
    mock_kb.retrieve.return_value = documents

    return mock_kb


def assert_cost_tracking_called(
    mock_response, input_tokens: int = 100, output_tokens: int = 50
) -> None:
    """Assert that the cost tracking attributes were accessed.

    Args:
        mock_response: The mock response object.
        input_tokens: Expected input tokens.
        output_tokens: Expected output tokens.
    """
    # Ensure usage attribute was accessed
    assert mock_response.usage.input_tokens == input_tokens
    assert mock_response.usage.output_tokens == output_tokens

    # Verify cost values are set correctly
    expected_input_cost = (input_tokens / 1000000) * 3
    expected_output_cost = (output_tokens / 1000000) * 15
    assert mock_response.cost.input_cost == expected_input_cost
    assert mock_response.cost.output_cost == expected_output_cost
    assert mock_response.cost.total_cost == expected_input_cost + expected_output_cost


def calculate_expected_cost(input_tokens: int, output_tokens: int) -> float:
    """Calculate expected API cost based on token counts.

    Args:
        input_tokens: Number of input tokens.
        output_tokens: Number of output tokens.

    Returns:
        Expected total cost in dollars.
    """
    # Claude 3 Sonnet: $3 per million input tokens, $15 per million output tokens
    input_cost = (input_tokens / 1000000) * 3
    output_cost = (output_tokens / 1000000) * 15
    return input_cost + output_cost
