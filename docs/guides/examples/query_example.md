# Basic Query Example

This example demonstrates how to use the Atlas query client for knowledge-augmented text generation in your applications, with support for the new provider options system.

## Overview

The query client provides a lightweight interface to access Atlas's RAG capabilities. It can be used to:

1. Generate knowledge-augmented responses to user queries
2. Stream responses for interactive UIs
3. Retrieve relevant documents without generating responses
4. Return both responses and source documents

## Provider Options System

Atlas now uses a flexible provider options system that supports:

1. **Direct Provider Selection**: Specify the provider you want to use
2. **Capability-Based Model Selection**: Select models based on capabilities like "inexpensive" or "premium"
3. **Auto-Detection**: Automatically determine the provider from a model name
4. **Default Fallback**: Use sensible defaults when no specifics are provided

## Setup

First, import the necessary modules and create a query client:

```python
from atlas import create_query_client
from atlas.providers import ProviderOptions, resolve_provider_options, create_provider_from_options

# Create a query client with default settings
client = create_query_client()

# Create a client with provider options
options = ProviderOptions(
    provider_name="anthropic",       # Specify provider directly
    model_name="claude-3-7-sonnet-20250219", # Specific model
    capability="inexpensive",       # Or use capability-based selection
    max_tokens=2000                 # Additional parameters
)

# Resolve provider options (auto-detection happens here)
resolved_options = resolve_provider_options(options)

# Create provider from resolved options
provider = create_provider_from_options(resolved_options)

# Create query client with the provider
custom_client = create_query_client(
    provider_name=provider.name,
    model_name=provider.model_name,
    system_prompt_file="path/to/custom_prompt.md",
    collection_name="custom_collection",
    db_path="/path/to/custom/db"
)
```

## Simple Query

The simplest way to use Atlas is to send a query and receive a response:

```python
# Simple query with knowledge augmentation
query = "What is the trimodal methodology in Atlas?"
response = client.query(query)
print(response)
```

## Document Retrieval Only

For applications that only need document retrieval without generating responses:

```python
# Retrieve documents without LLM response (no API key needed)
query = "knowledge graph structure"
documents = client.retrieve_only(query)

print(f"Found {len(documents)} relevant documents")

# Examine the top 3 documents
for i, doc in enumerate(documents[:3]):
    print(f"\nDocument {i+1}: {doc['metadata'].get('source', 'Unknown')}")
    print(f"Relevance: {doc['relevance_score']:.4f}")
    print(f"Excerpt: {doc['content'][:150]}...")
```

## Streaming Responses

For interactive UIs that show responses as they're generated:

```python
def print_streaming(delta: str, full_text: str) -> None:
    """Print streaming output character by character."""
    # Print the delta without newline and flush immediately
    print(delta, end="", flush=True)

# Stream the response
query = "Explain how Atlas can be integrated with other systems."
client.query_streaming(query, print_streaming)
print("\n")  # Add a newline after streaming completes
```

## Query with Context

To get both the response and the context documents used to generate it:

```python
# Get response with context information
query = "How does the trimodal methodology integrate with knowledge graphs?"
result = client.query_with_context(query)

# Access the response
print(result["response"])

# Access the context documents
print(f"\nBased on {len(result['context']['documents'])} documents:")
for i, doc in enumerate(result["context"]["documents"]):
    print(f"Document {i+1}: {doc['source']}")
    print(f"Relevance: {doc['relevance_score']:.4f}")
```

## Error Handling

Always implement proper error handling in production code:

```python
try:
    response = client.query("What is the trimodal methodology?")
    print(response)
except Exception as e:
    print(f"Error processing query: {e}")
    
    # Fallback to document retrieval if LLM generation fails
    print("Falling back to document retrieval:")
    documents = client.retrieve_only("trimodal methodology")
    
    print("Documents Retrieved:")
    for i, doc in enumerate(documents[:3]):
        print(f"Document {i+1}: {doc['metadata'].get('source', 'Unknown')}")
        print(f"Relevance: {doc['relevance_score']:.4f}")
        print(f"Excerpt: {doc['content'][:150]}...")
```

## Testing Without API Keys

You can test your application without incurring API costs by using mock responses:

```python
import os

# Set environment variable to skip API key check
os.environ["SKIP_API_KEY_CHECK"] = "true"

# Create client
client = create_query_client()

# All methods will use mock responses instead of actual API calls
response = client.query("Test query")
print(response)
```

## Complete Example

Here's a complete example demonstrating all these features:

```python
import logging
import os
import sys
import time

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import atlas package
from atlas import create_query_client


def print_streaming(delta: str, full_text: str) -> None:
    """Print streaming output character by character."""
    # Print the delta without newline and flush immediately
    print(delta, end="", flush=True)


def main():
    """Run the example."""
    # Use mock responses for testing
    os.environ["SKIP_API_KEY_CHECK"] = "true"

    # Create a query client
    print("Initializing Atlas query client...")
    try:
        client = create_query_client()
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
        print("This error might occur if you don't have a valid API key")
        print("However, we can still demonstrate document retrieval functionality")

    # Example 2: Query with context - focus on document retrieval
    print("\n### Example 2: Query with Context (Documents Only) ###")
    query = "How does Atlas handle knowledge representation?"
    print(f"Query: {query}")

    # Just retrieve documents without requiring LLM response
    documents = client.retrieve_only(query)

    print("Documents Retrieved:")
    for i, doc in enumerate(documents[:3]):  # Show top 3
        print(f"Document {i+1}: {doc['metadata'].get('source', 'Unknown')}")
        print(f"Relevance: {doc['relevance_score']:.4f}")
        print(f"Excerpt: {doc['content'][:150]}...\n")

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

        # Fallback to document retrieval
        print("\nFalling back to document retrieval:")
        documents = client.retrieve_only(query)

        print("Documents Retrieved:")
        for i, doc in enumerate(documents[:3]):  # Show top 3
            print(f"Document {i+1}: {doc['metadata'].get('source', 'Unknown')}")
            print(f"Relevance: {doc['relevance_score']:.4f}")
            print(f"Excerpt: {doc['content'][:150]}...\n")

    # Example 4: Query with context
    print("\n### Example 4: Query with Context ###")
    query = (
        "How does the trimodal methodology integrate with knowledge graphs in Atlas?"
    )
    print(f"Query: {query}")

    try:
        result = client.query_with_context(query)
        print(f"Response with {len(result['context']['documents'])} context documents:")
        print(result["response"])
        print("\n")
    except Exception as e:
        print(f"Error processing query with context: {e}")

    print("\n--- End of Examples ---\n")


if __name__ == "__main__":
    main()
```

## Related Documentation

- [Query Workflow](../../workflows/query.md) - Detailed information about the query workflow
- [Retrieval Workflow](../../workflows/retrieval.md) - How document retrieval works
- [Streaming Example](./streaming_example.md) - More details on streaming responses
- [API Reference](../../reference/api.md) - Complete API documentation