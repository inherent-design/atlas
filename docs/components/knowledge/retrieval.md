# Retrieval System

This document explains the knowledge retrieval system in Atlas, which enables agents to find and use contextually relevant information.

## Overview

The retrieval system in Atlas provides semantic search capabilities that allow agents to find relevant information based on natural language queries. Key features include:

1. **Semantic Search**: Find documents based on meaning, not just keywords
2. **Relevance Ranking**: Sort results by similarity to the query
3. **Metadata Filtering**: Filter documents by version, source, or other attributes
4. **LangGraph Integration**: Seamless use in graph-based workflows
5. **Persistent Storage**: Efficient access to stored knowledge

The system is designed to be:

- **Accurate**: Return the most contextually relevant information
- **Efficient**: Optimize search performance for interactive use
- **Flexible**: Support various query types and filtering options
- **Robust**: Handle errors and edge cases gracefully

## Core Components

### KnowledgeBase Class

The `KnowledgeBase` class is the central interface for knowledge retrieval:

```python
from atlas.knowledge.retrieval import KnowledgeBase

# Initialize the knowledge base
kb = KnowledgeBase(
    collection_name="atlas_knowledge_base",  # Optional, default value shown
    db_path=None  # Optional, defaults to ~/atlas_chroma_db or environment variable
)

# Basic retrieval
documents = kb.retrieve("What is the trimodal methodology?", n_results=5)

# Retrieval with version filter
documents = kb.retrieve(
    "What is the trimodal methodology?",
    n_results=5,
    version_filter="3"
)
```

#### Constructor Parameters

| Parameter         | Type            | Description                 | Default                                                          |
| ----------------- | --------------- | --------------------------- | ---------------------------------------------------------------- |
| `collection_name` | `Optional[str]` | Name of ChromaDB collection | From `ATLAS_COLLECTION_NAME` env var or `"atlas_knowledge_base"` |
| `db_path`         | `Optional[str]` | Path to ChromaDB storage    | From `ATLAS_DB_PATH` env var or `~/atlas_chroma_db`              |

#### Key Methods

- `retrieve()`: Find documents relevant to a query
- `get_versions()`: Get all available document versions
- `search_by_topic()`: Find documents on a specific topic

### ChromaDB Integration

The retrieval system integrates with ChromaDB for vector search:

```python
self.chroma_client = chromadb.PersistentClient(path=self.db_path)
self.collection = self.chroma_client.get_or_create_collection(
    name=self.collection_name
)
```

This provides:
- Persistent storage of embeddings
- Efficient vector search capabilities
- Collection-based organization
- Error handling with fallback options

### LangGraph Integration

For use with LangGraph workflows, the system provides the `retrieve_knowledge` function:

```python
from atlas.knowledge.retrieval import retrieve_knowledge

# Update state with retrieved knowledge
updated_state = retrieve_knowledge(
    state=current_state,
    query="What is the trimodal methodology?",
    collection_name="atlas_knowledge_base",
    db_path=None
)

# Retrieved documents are in updated_state["context"]["documents"]
```

This function:
- Initializes the knowledge base
- Extracts the query from state or parameters
- Retrieves relevant documents
- Updates the state with the results

## Retrieval Process

### Basic Retrieval Flow

The standard retrieval process follows these steps:

1. **Query Preparation**: The user's query is processed
2. **Vector Search**: ChromaDB performs a similarity search
3. **Result Processing**: Raw results are converted to a structured format
4. **Relevance Sorting**: Documents are sorted by relevance score
5. **Return to Caller**: Processed documents are returned

```python
def retrieve(self, query: str, n_results: int = 5, version_filter: Optional[str] = None):
    # Prepare filters if any
    where_clause = {}
    if version_filter:
        where_clause["version"] = version_filter

    # Query the collection
    results = self.collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where_clause if where_clause else None,
    )

    # Format results
    documents = []
    for i, (doc, metadata, distance) in enumerate(
        zip(results["documents"][0], results["metadatas"][0], results["distances"][0])
    ):
        documents.append({
            "content": doc,
            "metadata": metadata,
            "relevance_score": 1.0 - distance,  # Convert distance to relevance score
        })

    return documents
```

### Document Format

Retrieved documents follow a consistent format:

```json
{
  "content": "# Trimodal Methodology\n\nThe Atlas Trimodal Methodology is a framework...",
  "metadata": {
    "path": "src-markdown/prev/v3/core/TRIMODAL_PRINCIPLES.md",
    "source": "src-markdown/prev/v3/core/TRIMODAL_PRINCIPLES.md",
    "file_name": "TRIMODAL_PRINCIPLES.md",
    "section_title": "Trimodal Methodology",
    "version": "3",
    "chunk_size": 1843
  },
  "relevance_score": 0.945
}
```

Key attributes:
- **content**: The actual text of the document
- **metadata**: Source information and document attributes
- **relevance_score**: Similarity to the query (0-1 scale)

### Filtering with Metadata

The system supports filtering documents by metadata attributes:

```python
# Filter by version
docs = kb.retrieve(query, version_filter="3")

# Filter by other metadata (implemented through the where_clause)
where_clause = {"section_title": "Trimodal Methodology"}
```

Currently, version filtering is directly implemented, while other metadata filtering would require customization of the `retrieve` method.

## Version Support

The system provides special support for document versioning:

```python
# Get all available versions
versions = kb.get_versions()
print(f"Available versions: {versions}")  # e.g., ["1", "2", "3", "5"]

# Filter retrieval by version
v3_docs = kb.retrieve(query, version_filter="3")
```

This enables:
- Discovering what versions exist in the knowledge base
- Retrieving documents from specific versions
- Comparing information across versions

## Integration with Agents

### Basic Agent Integration

The retrieval system integrates with Atlas agents to provide context for responses:

```python
def process_message(self, message: str) -> str:
    # Retrieve relevant documents from the knowledge base
    documents = self.query_knowledge_base(message)

    # Create system message with context
    system_msg = self.system_prompt
    if documents:
        context_text = self.format_knowledge_context(documents)
        system_msg = system_msg + context_text

    # Generate response using the model provider
    model_request = ModelRequest(
        messages=[ModelMessage.user(msg["content"]) for msg in self.messages],
        system_prompt=system_msg,
        max_tokens=self.config.max_tokens,
    )

    response = self.provider.generate(model_request)
    # ...
```

The agent uses retrieved documents to augment the system prompt with relevant context, enabling more informed responses.

### Context Formatting

Retrieved documents are formatted for inclusion in the system prompt:

```python
def format_knowledge_context(self, documents: List[Dict[str, Any]]) -> str:
    if not documents:
        return ""

    context_text = "\n\n## Relevant Knowledge\n\n"

    # Use only the top 3 most relevant documents to avoid token limits
    for i, doc in enumerate(documents[:3]):
        source = doc["metadata"].get("source", "Unknown")
        content = doc["content"]
        context_text += f"### Document {i + 1}: {source}\n{content}\n\n"

    return context_text
```

This structured format:
- Clearly identifies relevant knowledge
- Maintains document attribution
- Preserves formatting of the original content
- Limits context to the most relevant documents

## Direct Usage Examples

### Basic Retrieval

```python
from atlas.knowledge.retrieval import KnowledgeBase

# Initialize the knowledge base
kb = KnowledgeBase()

# Retrieve documents
documents = kb.retrieve("How does Atlas handle knowledge graphs?")

# Display results
print(f"Found {len(documents)} relevant documents:")
for i, doc in enumerate(documents):
    score = doc["relevance_score"]
    source = doc["metadata"]["source"]
    title = doc["metadata"]["section_title"]
    print(f"Document {i+1}: {title} (from {source}) - Relevance: {score:.4f}")
    print(f"  Preview: {doc['content'][:100]}...\n")
```

### Version-Specific Retrieval

```python
from atlas.knowledge.retrieval import KnowledgeBase

# Initialize the knowledge base
kb = KnowledgeBase()

# Get available versions
versions = kb.get_versions()
print(f"Available Atlas versions: {versions}")

# Compare information across versions
query = "Explain the trimodal methodology"
for version in versions:
    print(f"\nRetrieving from version {version}:")
    docs = kb.retrieve(query, n_results=1, version_filter=version)
    if docs:
        print(f"Source: {docs[0]['metadata']['source']}")
        print(f"Content summary: {docs[0]['content'][:150]}...")
    else:
        print(f"No relevant documents found in version {version}")
```

### Topic-Based Search

```python
from atlas.knowledge.retrieval import KnowledgeBase

# Initialize the knowledge base
kb = KnowledgeBase()

# Search for a specific topic
topic_docs = kb.search_by_topic("Knowledge Graph", n_results=3)

print(f"Documents about Knowledge Graphs:")
for doc in topic_docs:
    title = doc["metadata"]["section_title"]
    version = doc["metadata"]["version"]
    print(f"- {title} (version {version})")
```

### With LangGraph Workflows

```python
from langgraph.graph import StateGraph
from atlas.knowledge.retrieval import retrieve_knowledge

# Define state type
State = Dict[str, Any]

# Create a workflow
workflow = StateGraph()

# Add nodes
workflow.add_node("retrieve_context", retrieve_knowledge)
workflow.add_node("process_query", process_query_node)
workflow.add_node("generate_response", generate_response_node)

# Define edges
workflow.add_edge("retrieve_context", "process_query")
workflow.add_edge("process_query", "generate_response")

# Create the runnable
runnable = workflow.compile()

# Run with initial state
initial_state = {
    "messages": [{"role": "user", "content": "What is the trimodal methodology?"}]
}
result = runnable.invoke(initial_state)
```

## Configuration Options

### Environment Variables

- `ATLAS_COLLECTION_NAME`: The name of the ChromaDB collection (default: "atlas_knowledge_base")
- `ATLAS_DB_PATH`: Path to store ChromaDB files (default: "~/atlas_chroma_db")

### Runtime Parameters

The `KnowledgeBase` class accepts:
- `collection_name`: Override for the collection name
- `db_path`: Override for the database path

### Command Line Options

When using the Atlas CLI, several retrieval-related options are available:

```
python main.py -m query -q "What is the trimodal methodology?" -c custom_collection --db-path custom_db_path
```

- `-q/--query`: The query to process
- `-c/--collection`: Specify the collection name
- `--db-path`: Override the database path

## Performance Considerations

### Optimizing Retrieval Results

For best results:

1. **Query Formulation**: Specific, well-formed queries yield better results
   - Good: "Explain the trimodal methodology framework"
   - Less effective: "methodology"

2. **Result Count**: Request appropriate number of results
   - For agent context: 3-5 documents (avoid prompt token limits)
   - For research: 5-10 documents (broader coverage)

3. **Metadata Filtering**: Use filters to narrow the search when appropriate
   - Version filtering for specific documentation versions
   - Future: source filtering for specific document types

### Handling Large Collections

For larger knowledge bases:

1. **Collection Organization**: Use separate collections for different domains
2. **Query Specificity**: More specific queries perform better at scale
3. **Result Limiting**: Start with fewer results and increase if needed

## Error Handling

The retrieval system includes robust error handling:

1. **Database Connection**: Falls back to in-memory DB if persistent connection fails
2. **Empty Collections**: Warns and returns empty results for empty collections
3. **Query Execution**: Catches and logs exceptions during query execution
4. **Result Processing**: Handles null or unexpected values in results

```python
try:
    # Query the collection
    results = self.collection.query(...)
    # Process results...
except Exception as e:
    print(f"Error retrieving from knowledge base: {str(e)}")
    print(f"Query was: {query[:50]}...")
    return []  # Return empty results on error
```

## Future Enhancements

Planned improvements to the retrieval system include:

1. **Hybrid Search**: Combining embedding similarity with keyword matching
2. **Re-ranking**: Post-retrieval scoring to improve relevance
3. **Enhanced Filtering**: More flexible metadata filtering options
4. **Result Enrichment**: Adding contextual information to search results
5. **Query Expansion**: Automatically enhancing queries for better results

## Related Documentation

- [Knowledge System Overview](./) - Overview of the knowledge management system
- [Document Ingestion](./ingestion.md) - Information about document processing
- [Agent Documentation](../agents/controller.md) - Documentation for Atlas agents that use the retrieval system
- [LangGraph Integration](../graph/nodes.md) - Documentation on graph nodes including knowledge retrieval
