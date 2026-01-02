#!/usr/bin/env python3
"""
Streaming Query Example (02_query_streaming.py)

This example demonstrates how to use Atlas with streaming responses:
1. Basic streaming functionality with character-by-character output
2. Custom streaming callback handlers
3. How streaming degrades gracefully for providers that don't support it

It uses the new provider options system to select and configure providers
with capability-based model selection and auto-detection.
"""

import sys
import time
from typing import Any, Dict, List

# Import common utilities for Atlas examples
from common import (
    create_provider_from_args,
    handle_example_error,
    print_example_footer,
    setup_example,
)

# Import atlas package
from atlas import create_query_client
from atlas.core import logging


def slow_print_streaming(delta: str, full_text: str) -> None:
    """Print streaming output character by character with a delay.

    Args:
        delta: The new text chunk.
        full_text: The complete text so far.
    """
    # Print the delta without newline and flush immediately
    for char in delta:
        print(char, end="", flush=True)
        time.sleep(0.01)  # Small delay to simulate typing


def count_streaming_callback(delta: str, full_text: str) -> None:
    """Streaming callback that counts tokens and displays progress.

    Args:
        delta: The new text chunk.
        full_text: The complete text so far.
    """
    # Simple estimation - not accurate for all tokenizers
    tokens_estimate = len(full_text.split())

    # Print only for substantial chunks to avoid too many updates
    if len(delta) > 1:
        print(
            f"[Received ~{len(delta)} chars, ~{tokens_estimate} total tokens]", end="\r", flush=True
        )

    # Print the actual text
    print(delta, end="", flush=True)


def add_example_arguments(parser):
    """Add example-specific arguments to the parser."""
    parser.add_argument("--max-tokens", type=int, help="Maximum tokens for response generation")
    parser.add_argument("--query", type=str, help="Query to use instead of example queries")
    parser.add_argument(
        "--delay",
        type=float,
        default=0.01,
        help="Delay between characters when printing streaming output",
    )


def main():
    """Run the streaming query example."""
    # Set up the example with standardized logging and argument parsing
    args = setup_example("Atlas Streaming Query Example", add_example_arguments)
    logger = logging.get_logger(__name__)

    # Create provider from command line arguments
    try:
        # Create provider
        provider = create_provider_from_args(args)

        # Create Atlas query client with the provider
        logger.info(
            f"Initializing Atlas query client with {provider.name} provider and {provider.model_name} model..."
        )
        client = create_query_client(provider_name=provider.name, model_name=provider.model_name)
    except Exception as e:
        handle_example_error(
            logger,
            e,
            "Error initializing query client",
            "This error might occur if you're using a provider without a valid API key\nTry running with '--provider mock' for API-free testing",
            exit_code=1,
        )

    # Example 1: Basic streaming
    print("\n" + "-" * 50)
    print("Example 1: Basic Streaming")
    print("-" * 50)

    # Use provided query if available, otherwise use default
    query = (
        args.query
        or "Explain how Atlas can be integrated with other systems in a step-by-step guide."
    )
    print(f"Query: {query}")

    print("\nStreaming Response:")
    try:
        # Stream the response with the slow typing effect
        client.query_streaming(query, slow_print_streaming)
        print("\n")
    except Exception as e:
        handle_example_error(
            logger,
            e,
            "Error processing streaming query",
            "This error might occur if you're using a provider without streaming support\nFalling back to non-streaming query...",
        )

        try:
            response = client.query(query)
            print(response)
        except Exception as fallback_error:
            handle_example_error(logger, fallback_error, "Fallback query also failed")

    # Example 2: Custom streaming callback
    print("\n" + "-" * 50)
    print("Example 2: Custom Streaming Callback with Token Counting")
    print("-" * 50)

    query = "What is the knowledge graph structure in Atlas? Provide a detailed explanation."
    print(f"Query: {query}")

    print("\nStreaming Response with Token Counting:")
    try:
        # Stream with the token counting callback
        client.query_streaming(query, count_streaming_callback)
        print("\n")
    except Exception as e:
        handle_example_error(
            logger,
            e,
            "Error with custom streaming callback",
            "Falling back to non-streaming query...",
        )

        try:
            response = client.query(query)
            print(response)
        except Exception as fallback_error:
            handle_example_error(logger, fallback_error, "Fallback query also failed")

    # Example 3: Streaming with context
    print("\n" + "-" * 50)
    print("Example 3: Query with Context (Non-streaming)")
    print("-" * 50 + "\n")

    query = "How does Atlas handle error management and retry mechanisms?"
    print(f"Query: {query}")

    try:
        # Use query_with_context to get both response and supporting documents
        result = client.query_with_context(query)
        print(f"\nResponse with {len(result['context']['documents'])} context documents:")
        print(result["response"])

        # Print the first document for reference
        if result["context"]["documents"]:
            doc = result["context"]["documents"][0]
            print(
                f"\nTop supporting document: {doc['source'] if 'source' in doc else doc.get('metadata', {}).get('source', 'Unknown')}"
            )
            print(f"Relevance: {doc['relevance_score'] if 'relevance_score' in doc else 'Unknown'}")
    except Exception as e:
        handle_example_error(logger, e, "Error processing query with context")

    # Print footer with standard format
    print_example_footer()

    # Information about provider streaming support
    print("\nProvider Streaming Support Information:")
    print("- Anthropic: Full streaming support")
    print("- OpenAI: Full streaming support")
    print("- Ollama: Full streaming support")
    print("- Mock: Basic streaming simulation")
    print("\nNotes:")
    print("- If a provider doesn't support streaming, Atlas will fall back to non-streaming")
    print("- The streaming callback receives both the delta and full text accumulated so far")
    print("- You can create custom callbacks for progress bars, token counting, etc.")
    print("\nTry different providers with: --provider [anthropic|openai|ollama|mock]")


if __name__ == "__main__":
    main()
