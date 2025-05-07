# Hybrid Retrieval Example

This guide demonstrates how to use Atlas's hybrid retrieval capabilities to combine semantic and keyword search for more accurate document retrieval.

## Overview

Atlas offers a hybrid retrieval approach that leverages both:

1. **Semantic Search**: Uses embeddings to find conceptually similar content even when keywords don't match
2. **Keyword Search**: Finds exact text matches for specific terms or phrases

By combining these approaches, Atlas can retrieve documents that are both semantically relevant and contain specific keywords.

## Example Code

```python
from atlas import create_query_client
from atlas.knowledge.retrieval import RetrievalFilter, RetrievalSettings

# Create a query client
client = create_query_client()

# Define retrieval settings with hybrid search enabled
settings = RetrievalSettings(
    use_hybrid_search=True,  # Enable hybrid search
    semantic_weight=0.7,     # 70% weight for semantic results
    keyword_weight=0.3,      # 30% weight for keyword results
    num_results=5            # Return top 5 documents
)

# Create filter (optional)
filter = RetrievalFilter(
    metadata_filters={
        "file_type": "markdown"  # Only retrieve markdown documents
    }
)

# Perform hybrid retrieval
documents = client.retrieve(
    query="knowledge graph structure with nodes and edges",
    settings=settings,
    filter=filter
)

# Process and display results
print(f"Found {len(documents)} relevant documents:")
for i, doc in enumerate(documents, 1):
    print(f"\n--- Document {i} ---")
    print(f"Source: {doc.metadata.get('simple_id', doc.metadata.get('source', 'Unknown'))}")
    print(f"Relevance Score: {doc.relevance_score:.4f}")
    print(f"First 100 chars: {doc.text[:100]}...")
```

## Running the Example

You can run this example directly from the examples directory:

```bash
# Make sure you have ingested documents first
uv run python main.py -m ingest

# Run the hybrid retrieval example
uv run python examples/hybrid_retrieval_example.py
```

## How It Works

The hybrid retrieval system combines results from two search methods:

1. **Vector Search**: Using embeddings to find semantically similar content
2. **BM25 Search**: Keyword-based search similar to what search engines use

The results are combined using a weighted approach:

- `semantic_weight`: Controls the influence of semantic search results
- `keyword_weight`: Controls the influence of keyword search results

Adjusting these weights allows you to customize the retrieval behavior for different types of queries.

## Customizing the Hybrid Search

You can adjust several parameters to fine-tune the hybrid retrieval:

```python
settings = RetrievalSettings(
    use_hybrid_search=True,     # Enable hybrid search
    semantic_weight=0.7,        # Weight for semantic results (0.0-1.0)
    keyword_weight=0.3,         # Weight for keyword results (0.0-1.0)
    num_results=5,              # Number of documents to return
    min_relevance_score=0.25,   # Minimum relevance score threshold
    rerank_results=True,        # Apply reranking after retrieval
    include_metadata=["source", "file_type", "simple_id"]  # Metadata to include
)
```

### Key Parameters

- **Weights**: Adjust `semantic_weight` and `keyword_weight` based on your needs:
  - For conceptual queries: higher semantic weight (e.g., 0.8/0.2)
  - For specific term queries: higher keyword weight (e.g., 0.3/0.7)
  - Equal weights (0.5/0.5) provide balanced results

- **Minimum Relevance**: Set `min_relevance_score` to filter out less relevant results

- **Reranking**: Enable `rerank_results` to apply a second relevance pass on retrieved documents

## Performance Considerations

Hybrid search performs two separate retrievals and combines the results, which can be slightly slower than a pure semantic or keyword search. However, the improved retrieval quality usually outweighs the small performance cost.

For very large document collections, consider these optimizations:

- Cache frequent queries
- Use more specific filters to reduce the search space
- Adjust the number of results to balance performance and recall

## See Also

- [Retrieval Guide](../../components/knowledge/retrieval.md) - Detailed documentation on retrieval capabilities
- [Retrieval Example](retrieval_example.md) - Basic retrieval example
- [Knowledge System Overview](../../components/knowledge/index.md) - Learn about Atlas's knowledge management system