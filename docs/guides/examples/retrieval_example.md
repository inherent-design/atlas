# Retrieval Example

This example demonstrates how to use Atlas for document retrieval without requiring an API key or language model generation.

## Overview

The retrieval functionality in Atlas allows you to:

1. Search documents in the knowledge base using semantic similarity
2. View document metadata and relevance scores
3. Filter documents based on metadata criteria
4. Access document content for custom processing

This capability is particularly useful when you:
- Want to use Atlas as a knowledge base without generating responses
- Need to perform document retrieval without incurring API costs
- Want to build custom applications on top of Atlas's knowledge retrieval

## Setup

First, import the necessary modules and create a query client:

```python
import logging
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import atlas package
from atlas import create_query_client

# Create a client
client = create_query_client()
```

## Simple Document Retrieval

The most basic retrieval operation fetches documents relevant to a query:

```python
# Retrieve documents only (doesn't require API key)
query = "What is the trimodal methodology?"
documents = client.retrieve_only(query)

print(f"Retrieved {len(documents)} documents")

# Show top 3 documents
for i, doc in enumerate(documents[:3]):
    print(f"\nDocument {i+1}: {doc['metadata'].get('source', 'Unknown')}")
    print(f"Relevance: {doc['relevance_score']:.4f}")
    print(f"Excerpt: {doc['content'][:150]}...")
```

## Accessing Document Metadata

Each retrieved document includes metadata that provides additional context:

```python
document = documents[0]  # Get the most relevant document

# Access metadata
print(f"Source: {document['metadata'].get('source', 'Unknown')}")
print(f"Content Type: {document['metadata'].get('content_type', 'Unknown')}")
print(f"Chunk ID: {document['metadata'].get('chunk_id', 'Unknown')}")
print(f"Version: {document['metadata'].get('version', 'Unknown')}")

# Access relevance score (1.0 = exact match, 0.0 = no relevance)
print(f"Relevance: {document['relevance_score']:.4f}")

# Access content
print(f"Content length: {len(document['content'])} characters")
print(f"Preview: {document['content'][:200]}...")
```

## Direct Knowledge Base Access

For more advanced use cases, you can access the knowledge base directly:

```python
from atlas.knowledge.retrieval import KnowledgeBase

# Initialize knowledge base
kb = KnowledgeBase(
    collection_name="atlas_knowledge_base",
    db_path="~/atlas_chroma_db"
)

# Retrieve with version filtering
documents = kb.retrieve(
    "trimodal methodology",
    n_results=5,
    version_filter="v2"  # Only retrieve documents from version v2
)

# Get all available versions
versions = kb.get_versions()
print(f"Available versions: {versions}")
```

## Working with Multiple Queries

You can perform multiple retrievals in sequence for comparison or analysis:

```python
# Perform multiple retrievals
queries = [
    "trimodal methodology",
    "knowledge graph structure",
    "perspective framework"
]

# Store results for analysis
results = {}

for query in queries:
    documents = client.retrieve_only(query)
    results[query] = documents
    print(f"Query: '{query}' - Retrieved {len(documents)} documents")

# Analyze top document for each query
for query, documents in results.items():
    if documents:
        top_doc = documents[0]
        print(f"\nQuery: '{query}'")
        print(f"Top document: {top_doc['metadata'].get('source', 'Unknown')}")
        print(f"Relevance: {top_doc['relevance_score']:.4f}")
    else:
        print(f"\nQuery: '{query}' - No documents found")
```

## Document Comparison

You can compare different document retrieval results:

```python
# Get documents for two related queries
docs_a = client.retrieve_only("trimodal methodology")
docs_b = client.retrieve_only("holistic integration")

# Find common documents
common_sources = set()
for doc_a in docs_a:
    source_a = doc_a['metadata'].get('source', '')
    for doc_b in docs_b:
        source_b = doc_b['metadata'].get('source', '')
        if source_a == source_b:
            common_sources.add(source_a)

print(f"Found {len(common_sources)} common sources between queries")
```

## Complete Example

Here's a complete example demonstrating document retrieval functionality:

```python
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
    """Run a simple retrieval example."""
    print("Testing Atlas retrieval functionality...")

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

    # Try a different query
    query = "knowledge graph structure"
    print(f"\nNew query: {query}")

    documents = client.retrieve_only(query)
    print(f"Retrieved {len(documents)} documents")

    # Show top document
    if documents:
        top_doc = documents[0]
        print(f"\nTop document: {top_doc['metadata'].get('source', 'Unknown')}")
        print(f"Relevance: {top_doc['relevance_score']:.4f}")
        print(f"Excerpt: {top_doc['content'][:150]}...")

    print("\nTest completed successfully!")


if __name__ == "__main__":
    main()
```

## Performance Considerations

When working with document retrieval:

1. **Query Formulation**: More specific queries often yield better results than vague ones
2. **Result Filtering**: Consider filtering by version, content type, or other metadata
3. **Relevance Threshold**: For production use, consider implementing a minimum relevance score threshold
4. **Document Count**: Adjust the number of retrieved documents based on your application needs

## Error Handling

Implement proper error handling for production applications:

```python
try:
    documents = client.retrieve_only(query)

    if not documents:
        print("No relevant documents found")
    else:
        # Process documents
        print(f"Found {len(documents)} documents")
except Exception as e:
    print(f"Error retrieving documents: {e}")
    # Handle error appropriately
```

## Related Documentation

- [Retrieval Workflow](../../workflows/retrieval.md) - Detailed information about the retrieval process
- [Query Workflow](../../workflows/query.md) - How retrieval integrates with query processing
- [ChromaDB Configuration](../../components/core/env.md) - Environment configuration for ChromaDB
- [Knowledge Base API](../../components/knowledge/) - Complete API documentation for the knowledge base
