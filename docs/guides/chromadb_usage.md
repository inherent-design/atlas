# ChromaDB Usage Guide

This guide provides practical instructions and patterns for using ChromaDB effectively within the Atlas framework. ChromaDB serves as the vector database powering Atlas' knowledge retrieval system, enabling semantic search and contextual relevance for agents.

## Introduction

ChromaDB is a lightweight, embedded vector database that enables efficient storage and retrieval of embeddings and their metadata. In Atlas, it forms the foundation of the knowledge system, allowing agents to find and utilize relevant information based on semantic meaning rather than exact keyword matching.

## Getting Started

### Installation

Atlas includes ChromaDB as a dependency, so you don't need to install it separately. However, if you're building a standalone application using Atlas components, you can install ChromaDB directly:

```bash
pip install chromadb>=1.0.8
```

### Basic Setup

To create a ChromaDB client and collection in Atlas:

```python
import chromadb
from atlas.core import env

# Get database path from environment or use default
db_path = env.get_string("ATLAS_DB_PATH") or "~/atlas_chroma_db"

# Initialize client with persistent storage
client = chromadb.PersistentClient(path=db_path)

# Create or access a collection
collection_name = env.get_string("ATLAS_COLLECTION_NAME") or "atlas_knowledge_base"
collection = client.get_or_create_collection(name=collection_name)
```

## Core Operations

### Adding Documents

To add documents to a collection, you need three components:
- Documents (text content)
- Metadata (associated information)
- IDs (unique identifiers)

Here's a simple example:

```python
# Add documents to collection
collection.add(
    documents=["This is document 1", "This is document 2"],
    metadatas=[
        {"source": "file1.md", "category": "documentation"},
        {"source": "file2.md", "category": "examples"}
    ],
    ids=["doc1", "doc2"]
)
```

:::tip
When adding many documents, consider using batch operations for better performance.
:::

### Querying Documents

The primary operation in ChromaDB is similarity search based on vectors:

```python
# Basic query with text
results = collection.query(
    query_texts=["How to use ChromaDB?"],
    n_results=5
)

# Process results
for i, (doc, metadata, distance) in enumerate(
    zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    )
):
    print(f"Result {i+1}: {metadata.get('source', 'Unknown')}")
    print(f"Distance: {distance}")
    print(f"Content: {doc[:100]}...")
    print()
```

Note the nested list structure in the results - the outer list represents each query (usually just one), while the inner list contains multiple results.

## Metadata Filtering

ChromaDB allows filtering results based on document metadata. This is essential for retrieving relevant subsets of information in Atlas.

### Basic Filtering

```python
# Filter by exact metadata value
results = collection.query(
    query_texts=["Knowledge graph"],
    n_results=5,
    where={"category": "documentation"}
)
```

### Filtering Operators

ChromaDB 1.0.8+ supports a variety of filtering operators:

```python
# Equality operators
filter_eq = {"version": {"$eq": "3"}}  # Equal to "3" (recommended for 1.0.8+)
filter_eq_simple = {"version": "3"}    # Equal to "3" (alternative syntax)
filter_ne = {"version": {"$ne": "3"}}  # Not equal to "3"

# Numerical operators
filter_gt = {"version_num": {"$gt": 2}}  # Greater than 2
filter_gte = {"version_num": {"$gte": 2}}  # Greater than or equal to 2
filter_lt = {"version_num": {"$lt": 4}}  # Less than 4
filter_lte = {"version_num": {"$lte": 4}}  # Less than or equal to 4

# List operators
filter_in = {"category": {"$in": ["docs", "guides"]}}  # Matches any in list
filter_nin = {"category": {"$nin": ["temp", "draft"]}}  # Matches none in list

# Logical operators
filter_and = {
    "$and": [
        {"category": {"$eq": "documentation"}},
        {"version_num": {"$gte": 3}}
    ]
}

filter_or = {
    "$or": [
        {"category": {"$eq": "documentation"}},
        {"category": {"$eq": "guides"}}
    ]
}
```

:::warning
ChromaDB 1.0.8+ is more strict about filter syntax than previous versions. Always use the full operator syntax (e.g., `{"$eq": value}`) rather than the shorthand syntax where possible.
:::

### Using Atlas RetrievalFilter

Atlas provides a `RetrievalFilter` class that simplifies building ChromaDB-compatible filters:

```python
from atlas.knowledge.retrieval import RetrievalFilter

# Create a filter
filter = RetrievalFilter()
filter.add_filter("category", {"$eq": "documentation"})  # Using operator syntax
filter.add_operator_filter("version_num", "$gte", 3)     # Helper method for operators

# Create range filter (between min and max, inclusive)
filter.add_range_filter("version_num", 2, 4)  # Equivalent to $gte 2 AND $lte 4

# Create in filter (value must be in list)
filter.add_in_filter("file_name", ["index.md", "overview.md"])

# Create from metadata fields
filter = RetrievalFilter.from_metadata(
    source_path="docs/guides",
    file_type="md",
    version="3"
)

# Combine filters
combined = RetrievalFilter.combine_filters([filter1, filter2], operator="$and")

# Use with knowledge base
from atlas.knowledge.retrieval import KnowledgeBase
kb = KnowledgeBase()
documents = kb.retrieve(query, filter=filter)
```

The `RetrievalFilter` class handles ChromaDB 1.0.8's strict filter syntax requirements automatically and provides convenient helper methods for creating common filter patterns.

## Document Content Filtering

In addition to metadata filtering, ChromaDB allows filtering based on document content with the `where_document` parameter:

```python
# Find documents containing specific text
results = collection.query(
    query_texts=["architecture"],
    where_document={"$contains": "knowledge graph"},
    n_results=5
)
```

This is useful for finding documents that specifically mention certain terms or concepts.

## Retrieval Settings

Atlas extends ChromaDB's capabilities with retrieval settings that allow for more sophisticated search patterns:

```python
from atlas.knowledge.retrieval import KnowledgeBase
from atlas.knowledge.settings import RetrievalSettings

# Create knowledge base
kb = KnowledgeBase()

# Configure retrieval settings
settings = RetrievalSettings(
    use_hybrid_search=True,  # Combine vector and keyword search
    semantic_weight=0.7,     # Weight for vector similarity
    keyword_weight=0.3,      # Weight for keyword matching
    num_results=5,           # Number of results to return
    min_relevance_score=0.5, # Minimum similarity threshold
    rerank_results=True      # Apply custom reranking
)

# Retrieve with settings and filter
documents = kb.retrieve(
    query="How does Atlas handle knowledge graphs?",
    filter=filter,
    settings=settings
)
```

## Integration Patterns

### Query Client Pattern

Atlas provides a query client interface for retrieving knowledge from ChromaDB:

```python
from atlas import create_query_client

# Create a query client
client = create_query_client(
    collection_name="atlas_knowledge_base",
    provider_name="anthropic"  # Provider for completing the query
)

# Retrieve documents and generate a response
result = client.query_with_context(
    "Explain Atlas's knowledge graph structure",
    filter={"version": "latest"},
    max_results=3
)

# Access retrieved documents and response
print(result["response"])
print(f"Found {len(result['context']['documents'])} supporting documents:")
for doc in result['context']['documents']:
    print(f"- {doc['source']}")
```

### Direct ChromaDB Access

For more control, you can use ChromaDB's API directly:

```python
from atlas.knowledge.retrieval import KnowledgeBase

# Initialize knowledge base
kb = KnowledgeBase(collection_name="atlas_knowledge_base")

# Access the ChromaDB collection
collection = kb.collection

# Perform direct operations
count = collection.count()
print(f"Collection contains {count} documents")

# Get all metadata fields
results = collection.get(limit=100)
fields = set()
for metadata in results["metadatas"]:
    fields.update(metadata.keys())
print(f"Available metadata fields: {sorted(list(fields))}")

# Peek at collection contents
peek = collection.peek(limit=5)
for i, (doc, metadata) in enumerate(zip(peek["documents"], peek["metadatas"])):
    print(f"Document {i+1}: {metadata.get('source', 'Unknown')}")
    print(f"Content preview: {doc[:100]}...")
```

## Best Practices

### Optimizing Performance

1. **Batch Operations**: Use batch operations when adding multiple documents
   ```python
   collection.add(
       documents=many_documents,
       metadatas=many_metadatas,
       ids=many_ids
   )
   ```

2. **Specific Filters**: Make filters as specific as possible to reduce result set
   ```python
   # More specific is better
   filter = {"category": "documentation", "version": "3"}
   ```

3. **Filter Before Embedding**: Apply metadata filters before semantic search when possible
   ```python
   # More efficient
   results = collection.query(
       query_texts=["knowledge graph"],
       where={"category": "documentation"},
       n_results=5
   )
   ```

4. **Limit Result Count**: Only request as many results as needed
   ```python
   # For agent context, 3-5 results is often sufficient
   results = collection.query(query_texts=[query], n_results=3)
   ```

### Error Handling

Implement robust error handling for ChromaDB operations:

```python
try:
    results = collection.query(
        query_texts=[query],
        n_results=5,
        where=filter
    )
except Exception as e:
    logger.error(f"ChromaDB query failed: {e}")
    # Fall back to a simpler query
    try:
        results = collection.query(
            query_texts=[query],
            n_results=5
        )
    except Exception as e2:
        logger.error(f"Fallback query failed: {e2}")
        # Return empty results
        results = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
```

## Common Tasks

### Managing Document Versions

Use metadata to track document versions:

```python
# Add versioned documents
collection.add(
    documents=["Content for version 3", "Content for version 4"],
    metadatas=[
        {"source": "document.md", "version": "3"},
        {"source": "document.md", "version": "4"}
    ],
    ids=["doc_v3", "doc_v4"]
)

# Query specific version
results = collection.query(
    query_texts=["How to use the feature"],
    where={"version": "4"},
    n_results=5
)
```

### Document Categorization

Organize documents by category for targeted retrieval:

```python
# Add with categories
collection.add(
    documents=["Architecture document", "Implementation guide"],
    metadatas=[
        {"source": "arch.md", "category": "architecture"},
        {"source": "impl.md", "category": "implementation"}
    ],
    ids=["arch1", "impl1"]
)

# Query by category
results = collection.query(
    query_texts=["system design"],
    where={"category": "architecture"},
    n_results=5
)
```

### Document Updating

Update documents when content changes:

```python
# Update a specific document
collection.update(
    ids=["doc1"],
    documents=["Updated content for document 1"],
    metadatas=[{"source": "file1.md", "category": "documentation", "updated": True}]
)
```

### Finding Similar Documents

Find documents similar to an existing one:

```python
# Get a specific document
doc = collection.get(ids=["reference_doc"])

# Find similar documents
if doc["documents"]:
    results = collection.query(
        query_texts=[doc["documents"][0]],
        n_results=5
    )
```

## Troubleshooting

### Common Issues

1. **Filter Syntax Errors**: ChromaDB 1.0.8+ is strict about filter syntax
   ```python
   # Wrong: missing $ prefix for operator
   wrong_filter = {"version": {"gt": 3}}

   # Correct: includes $ prefix
   correct_filter = {"version": {"$gt": 3}}

   # Wrong: Using simple key-value in logical operators (in 1.0.8+)
   wrong_and = {"$and": [{"category": "documentation"}, {"version": "3"}]}

   # Correct: Using full operator syntax in logical operators
   correct_and = {"$and": [{"category": {"$eq": "documentation"}}, {"version": {"$eq": "3"}}]}
   ```

2. **Path Normalization Issues**: Path formats must match exactly
   ```python
   # Wrong: Using different path formats than what's stored
   wrong_filter = {"source": {"$eq": "some/partial/path"}}  # May not match actual path format

   # Better: Use exact path as stored in metadata
   better_filter = {"source": {"$eq": "docs/components/knowledge/index.md"}}
   ```

3. **Type Mismatch**: Type inconsistencies in filters
   ```python
   # Wrong: comparing string with number
   wrong_filter = {"version_num": {"$gt": "3"}}

   # Correct: consistent types
   correct_filter = {"version_num": {"$gt": 3}}
   ```

4. **Path Not Found**: Database path doesn't exist
   ```python
   # Ensure the directory exists
   import os
   os.makedirs(db_path, exist_ok=True)
   client = chromadb.PersistentClient(path=db_path)
   ```

5. **Exists Operator Issues**: The $exists operator is problematic in ChromaDB 1.0.8+
   ```python
   # Avoid using $exists operator
   problematic_filter = {"source": {"$exists": True}}

   # Better: Use specific value matching if possible
   better_filter = {"source": {"$ne": None}}
   ```

### Debugging Techniques

1. **Check Available Metadata**:
   ```python
   # Get all metadata fields
   results = collection.get(limit=100)
   fields = set()
   for metadata in results["metadatas"]:
     fields.update(metadata.keys())
   print(f"Available fields: {sorted(list(fields))}")
   ```

2. **Test Filters Directly**:
   ```python
   # Try filter without query to see if any documents match
   filter_test = collection.get(where=filter, limit=10)
   print(f"Filter matched {len(filter_test['ids'])} documents")
   ```

3. **Check Collection Content**:
   ```python
   # Peek at collection to verify content
   peek = collection.peek(limit=5)
   for i, (doc, metadata) in enumerate(zip(peek["documents"], peek["metadatas"])):
       print(f"Document {i}: {metadata}")
       print(f"Content: {doc[:50]}...")
   ```

## Conclusion

ChromaDB provides the vector database foundation that powers Atlas's knowledge retrieval system. By understanding how to effectively use ChromaDB for document storage, filtering, and similarity search, you can build powerful knowledge-enabled applications with Atlas.

The Atlas framework extends ChromaDB's capabilities with additional features like hybrid search, structured filtering, and tight integration with the agent system, making it easy to build sophisticated knowledge applications while still providing access to the underlying database when needed.

## Additional Resources

- [Official ChromaDB Documentation](https://docs.trychroma.com/)
- [Knowledge System Overview](../components/knowledge/index.md)
- [Retrieval System Documentation](../components/knowledge/retrieval.md)
- [Document Ingestion](../components/knowledge/ingestion.md)
