"""
Example usage of the Atlas query-only client.

This script demonstrates how to use the Atlas query client for simple
knowledge-augmented text generation in another application.
"""

import logging
import os
import sys
import time

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add parent directory to path so we can import atlas from the development directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import atlas package
from atlas import create_query_client


def print_streaming(delta: str, full_text: str) -> None:
    """Print streaming output character by character.

    Args:
        delta: The new text chunk.
        full_text: The complete text so far.
    """
    # Print the delta without newline and flush immediately
    for char in delta:
        print(char, end="", flush=True)
        time.sleep(0.01)  # Small delay to simulate typing


def main():
    """Run the example."""
    # Parse command line arguments for provider
    import argparse
    parser = argparse.ArgumentParser(description="Atlas Query Client Example")
    parser.add_argument("--provider", type=str, default="mock", 
                        choices=["mock", "anthropic", "openai", "ollama"],
                        help="Model provider to use (default: mock)")
    parser.add_argument("--model", type=str, help="Specific model to use")
    args = parser.parse_args()

    # Create a query client with the specified provider
    print(f"Initializing Atlas query client with {args.provider} provider...")
    try:
        client = create_query_client(provider_name=args.provider, model_name=args.model)
    except Exception as e:
        print(f"Error initializing query client: {e}")
        return

    print("\n--- Atlas Query Client Example ---\n")

    # Example 1: Simple query
    print("\n### Example 1: Simple Query ###")
    query = "What is the trimodal methodology in Atlas?"
    print(f"Query: {query}")

    print("Response:")
    try:
        response = client.query(query)
        print(response)
    except Exception as e:
        print(f"Error processing query: {e}")
        print("This error might occur if you're using a provider without a valid API key")
        print("Try running with '--provider mock' for API-free testing")
        print("However, we can still demonstrate document retrieval functionality")

    # Example 2: Query with context - focus on document retrieval
    print("\n### Example 2: Query with Context (Documents Only) ###")
    query = "How does Atlas handle knowledge representation?"
    print(f"Query: {query}")

    # Just retrieve documents without requiring LLM response
    documents = client.retrieve_only(query)

    print("Documents Retrieved:")
    for i, doc in enumerate(documents[:3]):  # Show top 3
        # Handle both dictionary and RetrievalResult formats
        if hasattr(doc, 'metadata'):
            # It's a RetrievalResult object
            source = doc.metadata.get('source', 'Unknown')
            relevance = doc.relevance_score
            content = doc.content
        else:
            # It's a dictionary
            source = doc['metadata'].get('source', 'Unknown')
            relevance = doc['relevance_score']
            content = doc['content']
            
        print(f"Document {i+1}: {source}")
        print(f"Relevance: {relevance:.4f}")
        print(f"Excerpt: {content[:150]}...\n")

    # Example 3: Streaming response
    print("\n### Example 3: Streaming Response ###")
    query = "Explain how Atlas can be integrated with other systems."
    print(f"Query: {query}")

    try:
        print("Streaming Response:")
        client.query_streaming(query, print_streaming)
        print("\n")
    except Exception as e:
        print(f"Error processing streaming query: {e}")
        print("This error might occur if you're using a provider without a valid API key")
        print("Try running with '--provider mock' for API-free testing")

        # Fallback to document retrieval
        print("\nFalling back to document retrieval:")
        documents = client.retrieve_only(query)

        print("Documents Retrieved:")
        for i, doc in enumerate(documents[:3]):  # Show top 3
            # Handle both dictionary and RetrievalResult formats
            if hasattr(doc, 'metadata'):
                # It's a RetrievalResult object
                source = doc.metadata.get('source', 'Unknown')
                relevance = doc.relevance_score
                content = doc.content
            else:
                # It's a dictionary
                source = doc['metadata'].get('source', 'Unknown')
                relevance = doc['relevance_score']
                content = doc['content']
                
            print(f"Document {i+1}: {source}")
            print(f"Relevance: {relevance:.4f}")
            print(f"Excerpt: {content[:150]}...\n")

    # Example 4: Retrieve only with a different query
    print("\n### Example 4: Final Knowledge Retrieval Example ###")
    query = "Atlas knowledge graph structure"
    print(f"Query: {query}")

    documents = client.retrieve_only(query)
    print(f"Found {len(documents)} relevant documents:")

    for i, doc in enumerate(documents[:3]):  # Show top 3
        # Handle both dictionary and RetrievalResult formats
        if hasattr(doc, 'metadata'):
            # It's a RetrievalResult object
            source = doc.metadata.get('source', 'Unknown')
            relevance = doc.relevance_score
            content = doc.content
        else:
            # It's a dictionary
            source = doc['metadata'].get('source', 'Unknown')
            relevance = doc['relevance_score']
            content = doc['content']
            
        print(f"\nDocument {i+1}: {source}")
        print(f"Relevance: {relevance:.4f}")
        print(f"Excerpt: {content[:150]}...")

    # Example 5: Stream with context
    print("\n### Example 5: Stream with Context ###")
    query = (
        "How does the trimodal methodology integrate with knowledge graphs in Atlas?"
    )
    print(f"Query: {query}")

    try:
        print("Streaming Response with Context:")
        # Use query_with_context and then normal streaming
        result = client.query_with_context(query)
        print(f"Response with {len(result['context']['documents'])} context documents:")
        print(result["response"])
        print("\n")
    except Exception as e:
        print(f"Error processing streaming query with context: {e}")
        print("This error might occur if you're using a provider without a valid API key")
        print("Try running with '--provider mock' for API-free testing")

    print("\n--- End of Examples ---\n")


if __name__ == "__main__":
    main()
