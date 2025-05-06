# API Reference

This document provides a comprehensive reference for the Atlas API, including all public classes, methods, and their parameters.

## Core API

The Atlas API provides a simple and flexible interface for querying and retrieving knowledge. It's designed to be easily integrated into other applications and workflows.

### Exported Symbols

Atlas exports the following symbols:

| Symbol | Description |
|--------|-------------|
| `AtlasAgent` | Base agent implementation for query processing |
| `AtlasConfig` | Configuration class for Atlas components |
| `AtlasQuery` | Lightweight query-only interface |
| `create_query_client` | Factory function to create an AtlasQuery instance |

## Query Client API

The recommended way to interact with Atlas is through the query client.

### Creating a Client

```python
from atlas import create_query_client

# Create a client with default configuration
client = create_query_client()

# Create a client with custom parameters
client = create_query_client(
    system_prompt_file="path/to/prompt.md",
    collection_name="my_collection",
    db_path="path/to/db",
    provider_name="anthropic",  # or "openai", "ollama"
    model_name="claude-3-7-sonnet-20250219"  # provider-specific model name
)
```

### `create_query_client`

Factory function to create an `AtlasQuery` instance.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `system_prompt_file` | `Optional[str]` | `None` | Path to a file containing the system prompt |
| `collection_name` | `Optional[str]` | `None` | Name of the ChromaDB collection to use (default from env) |
| `db_path` | `Optional[str]` | `None` | Path to the knowledge base (default from env) |
| `provider_name` | `Optional[str]` | `None` | Name of the model provider (default from env) |
| `model_name` | `Optional[str]` | `None` | Name of the model to use (default from env) |

**Returns:**

An initialized `AtlasQuery` instance.

**Environment Variables:**

If parameters are not specified, they will be loaded from environment variables:

- `ATLAS_DEFAULT_PROVIDER`: Model provider name (default: "anthropic")
- `ATLAS_COLLECTION_NAME`: ChromaDB collection name (default: "atlas_knowledge_base")
- `ATLAS_DB_PATH`: Path to the ChromaDB database (default: "~/atlas_chroma_db")
- `ATLAS_DEFAULT_MODEL`: Model name (provider-specific default)

## AtlasQuery Class

The `AtlasQuery` class provides a lightweight interface for querying the knowledge base and generating responses using the configured language model.

### Constructor

```python
from atlas import AtlasQuery

client = AtlasQuery(
    system_prompt_file=None,
    collection_name=None,
    db_path=None,
    provider_name=None,
    model_name=None,
    config=None
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `system_prompt_file` | `Optional[str]` | `None` | Path to a file containing the system prompt |
| `collection_name` | `Optional[str]` | `None` | Name of the ChromaDB collection to use |
| `db_path` | `Optional[str]` | `None` | Path to the knowledge base |
| `provider_name` | `Optional[str]` | `None` | Name of the model provider to use |
| `model_name` | `Optional[str]` | `None` | Name of the model to use |
| `config` | `Optional[AtlasConfig]` | `None` | Configuration object, if not provided a new one is created |

### Methods

#### `query`

```python
def query(self, query_text: str) -> str:
```

Query Atlas with a simple text input and receive a text response.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `query_text` | `str` | The text query to process |

**Returns:**

A string containing the response from the language model.

**Example:**

```python
response = client.query("What is the trimodal methodology in Atlas?")
print(response)
```

#### `query_with_context`

```python
def query_with_context(self, query_text: str) -> Dict[str, Any]:
```

Query Atlas and return both the response and context used.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `query_text` | `str` | The text query to process |

**Returns:**

A dictionary containing the response and context used:

```python
{
    "response": str,  # The text response
    "context": {
        "documents": [
            {
                "content": str,  # Document content
                "source": str,  # Document source
                "relevance_score": float  # Relevance score
            },
            # Additional documents...
        ],
        "query": str  # Original query
    }
}
```

**Example:**

```python
result = client.query_with_context("How does Atlas handle knowledge representation?")
print(f"Response: {result['response']}")
print(f"Documents used: {len(result['context']['documents'])}")
```

#### `query_streaming`

```python
def query_streaming(self, query_text: str, callback: Callable[[str, str], None]) -> str:
```

Query Atlas with streaming response for a more interactive experience.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `query_text` | `str` | The text query to process |
| `callback` | `Callable[[str, str], None]` | Function called for each chunk with arguments (delta_text, full_text) |

**Returns:**

The complete response text.

**Example:**

```python
def print_streaming(delta: str, full_text: str) -> None:
    """Print streaming output character by character."""
    print(delta, end="", flush=True)

client.query_streaming("Explain conditional edge routing", print_streaming)
```

#### `retrieve_only`

```python
def retrieve_only(self, query_text: str) -> List[Dict[str, Any]]:
```

Retrieve documents from the knowledge base without generating a response.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `query_text` | `str` | The text query to search for |

**Returns:**

A list of dictionaries containing the retrieved documents:

```python
[
    {
        "content": str,  # Document content
        "metadata": {
            "source": str,  # Document source
            # Other metadata fields...
        },
        "relevance_score": float  # Relevance score
    },
    # Additional documents...
]
```

**Example:**

```python
documents = client.retrieve_only("Atlas knowledge graph structure")
print(f"Found {len(documents)} relevant documents")

for i, doc in enumerate(documents[:3]):  # Show top 3
    print(f"Document {i+1}: {doc['metadata'].get('source', 'Unknown')}")
    print(f"Relevance: {doc['relevance_score']:.4f}")
    print(f"Excerpt: {doc['content'][:150]}...")
```

## Configuration API

### AtlasConfig

The `AtlasConfig` class provides a centralized configuration for Atlas components.

```python
from atlas import AtlasConfig

config = AtlasConfig(
    collection_name="my_collection",
    db_path="/path/to/db",
    model_name="claude-3-7-sonnet-20250219"
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `collection_name` | `Optional[str]` | `None` | Name of the ChromaDB collection to use |
| `db_path` | `Optional[str]` | `None` | Path to the knowledge base |
| `model_name` | `Optional[str]` | `None` | Name of the model to use |

## Agent API

### AtlasAgent

The `AtlasAgent` class provides the core agent functionality for processing queries.

```python
from atlas import AtlasAgent

agent = AtlasAgent(
    system_prompt_file="path/to/prompt.md",
    collection_name="my_collection",
    config=None,
    provider_name="anthropic",
    model_name="claude-3-7-sonnet-20250219"
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `system_prompt_file` | `Optional[str]` | `None` | Path to a file containing the system prompt |
| `collection_name` | `Optional[str]` | `None` | Name of the ChromaDB collection to use |
| `config` | `Optional[AtlasConfig]` | `None` | Configuration object |
| `provider_name` | `Optional[str]` | `None` | Name of the model provider to use |
| `model_name` | `Optional[str]` | `None` | Name of the model to use |

**Main Methods:**

- `process_message(query_text: str) -> str`: Process a query and return a response
- `process_message_streaming(query_text: str, callback: Callable[[str, str], None]) -> str`: Process a query with streaming response

## Error Handling

Atlas provides a comprehensive error handling system through the `atlas.core.errors` module. The main exception classes are:

- `APIError`: Base class for all Atlas API errors
- `ModelProviderError`: Errors related to model providers
- `ConfigurationError`: Errors related to configuration
- `KnowledgeBaseError`: Errors related to the knowledge base

Example error handling:

```python
from atlas import create_query_client
from atlas.core.errors import APIError

try:
    client = create_query_client()
    response = client.query("What is Atlas?")
    print(response)
except APIError as e:
    print(f"Atlas API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Testing

When testing with the Atlas API, you can skip the API key check by setting the `SKIP_API_KEY_CHECK` environment variable:

```python
import os
os.environ["SKIP_API_KEY_CHECK"] = "true"

from atlas import create_query_client
client = create_query_client()
```

This allows you to test document retrieval functionality without requiring a valid API key.