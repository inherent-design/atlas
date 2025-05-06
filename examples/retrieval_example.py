"""
Example of simple document retrieval using the Atlas query client.

This script demonstrates how to retrieve documents from the knowledge base
without requiring an API key or generating responses from a language model.
"""

import logging
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import atlas package
from atlas import create_query_client


def main():
    """Run a simple test."""
    print("Testing Atlas query client...")

    # Create a client
    client = create_query_client()

    # Retrieve documents only (doesn't require API key)
    query = "What is the trimodal methodology?"
    print(f"Query: {query}")

    # Just retrieve documents
    documents = client.retrieve_only(query)

    print(f"Retrieved {len(documents)} documents")

    # Show top 3 documents
    for i, doc in enumerate(documents[:3]):  # Show top 3
        print(f"\nDocument {i+1}: {doc['metadata'].get('source', 'Unknown')}")
        print(f"Relevance: {doc['relevance_score']:.4f}")
        print(f"Excerpt: {doc['content'][:150]}...")

    print("\nTest completed successfully!")


if __name__ == "__main__":
    main()
