#!/usr/bin/env python3
"""
Basic Query Example (01_query_simple.py)

This example demonstrates the core querying capabilities of Atlas:
1. Simple query generation
2. Document retrieval (retrieve-only)
3. Query with context (showing retrieved documents)

It uses the new provider options system to select and configure providers
with capability-based model selection and auto-detection.
"""

import sys
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


def print_documents(documents: List[Dict[str, Any]], limit: int = 3) -> None:
    """Print retrieved documents in a nice format.

    Args:
        documents: List of retrieved documents
        limit: Maximum number of documents to show
    """
    for i, doc in enumerate(documents[:limit]):
        # Handle both dictionary and RetrievalResult formats
        if hasattr(doc, "metadata"):
            # It's a RetrievalResult object
            source = doc.metadata.get("source", "Unknown")
            relevance = doc.relevance_score
            content = doc.content
        else:
            # It's a dictionary
            source = doc["metadata"].get("source", "Unknown")
            relevance = doc["relevance_score"]
            content = doc["content"]

        print(f"\nDocument {i+1}: {source}")
        print(f"Relevance: {relevance:.4f}")
        print(f"Excerpt: {content[:150]}...")


def add_example_arguments(parser):
    """Add example-specific arguments to the parser."""
    parser.add_argument("--max-tokens", type=int, help="Maximum tokens for response generation")
    parser.add_argument("--query", type=str, help="Query to use instead of example queries")


def main():
    """Run the basic query example."""
    # Set up the example with standardized logging and argument parsing
    args = setup_example("Atlas Basic Query Example", add_example_arguments)
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
            e,
            message="Error initializing query client",
            user_message="This error might occur if you're using a provider without a valid API key\nTry running with '--provider mock' for API-free testing",
            exit_code=1,
        )

    # Example 1: Simple query
    print("\n" + "-" * 50)
    print("Example 1: Simple Query")
    print("-" * 50)

    # Use provided query if available, otherwise use default
    query = args.query or "What is the trimodal methodology in Atlas?"
    print(f"Query: {query}")

    print("\nResponse:")
    try:
        response = client.query(query)
        print(response)
    except Exception as e:
        handle_example_error(
            e,
            message="Error processing query",
            user_message="This error might occur if you're using a provider without a valid API key\nTry running with '--provider mock' for API-free testing",
        )

    # Example 2: Document retrieval only
    print("\n" + "-" * 50)
    print("Example 2: Document Retrieval Only")
    print("-" * 50)

    query = "How does Atlas handle knowledge representation?"
    print(f"Query: {query}")

    try:
        # Just retrieve documents without LLM response
        documents = client.retrieve_only(query)
        print(f"\nRetrieved {len(documents)} documents. Top results:")
        print_documents(documents)
    except Exception as e:
        handle_example_error(e, message="Error retrieving documents")

    # Example 3: Query with context
    print("\n" + "-" * 50)
    print("Example 3: Query with Context")
    print("-" * 50)

    query = "How does the trimodal methodology integrate with knowledge graphs in Atlas?"
    print(f"Query: {query}")

    try:
        # Use query_with_context to get both response and supporting documents
        result = client.query_with_context(query)
        print(f"\nResponse with {len(result['context']['documents'])} supporting documents:")
        print(result["response"])

        print("\nSupporting Documents:")
        print_documents(result["context"]["documents"])
    except Exception as e:
        handle_example_error(e, message="Error processing query with context")

    # Print footer
    print_example_footer()


if __name__ == "__main__":
    main()
