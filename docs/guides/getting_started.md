# Getting Started with Atlas

This guide will help you get started with the Atlas framework, from installation to basic usage patterns.

## Installation

Atlas requires Python 3.13 or later. We recommend using `uv` for dependency management, but pip will also work.

### Installing with uv

```bash
# Install uv if you don't have it
pip install uv

# Clone the repository
git clone https://github.com/inherent-design/atlas.git
cd atlas

# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .
```

### Installing with pip

```bash
# Clone the repository
git clone https://github.com/inherent-design/atlas.git
cd atlas

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Configuration

Atlas uses environment variables for configuration. Create a `.env` file in the project root:

```bash
# Model provider settings
ATLAS_DEFAULT_PROVIDER=anthropic
ATLAS_DEFAULT_MODEL=claude-3-7-sonnet-20250219
ATLAS_MAX_TOKENS=2000

# API keys (required for actual usage)
ANTHROPIC_API_KEY=your_api_key_here
# OPENAI_API_KEY=your_openai_key_here  # Uncomment if using OpenAI

# Knowledge base settings
ATLAS_DB_PATH=~/atlas_chroma_db
ATLAS_COLLECTION_NAME=atlas_knowledge_base
```

See the [Environment Variables](../reference/env_variables.md) documentation for a complete list of configuration options.

## Basic Usage

### Using the CLI

The simplest way to use Atlas is through the command-line interface:

```bash
# Start an interactive CLI session
uv run python main.py -m cli

# Run a single query
uv run python main.py -m query -q "What is the trimodal methodology in Atlas?"

# Ingest documents into the knowledge base
uv run python main.py -m ingest -d /path/to/your/documents/
```

### Using the Atlas Query Client

For programmatic usage, Atlas provides a lightweight query client:

```python
from atlas import create_query_client

# Create a client
client = create_query_client()

# Simple query
response = client.query("What is the trimodal methodology?")
print(response)

# Streaming response with callback
def print_streaming(delta, full_text):
    print(delta, end="", flush=True)

client.query_streaming("Explain conditional edge routing", print_streaming)

# Retrieve documents without generating a response
documents = client.retrieve_only("knowledge graph")
print(f"Found {len(documents)} relevant documents")
```

### Running in Multi-Agent Mode

For more complex scenarios, you can use the multi-agent controller mode:

```bash
# Run in controller mode with parallel processing
uv run python main.py -m controller --parallel --workflow advanced

# Run as a specialized worker
uv run python main.py -m worker --workflow retrieval
```

## Example Workflows

### Basic RAG Query

The most common use case is a simple RAG (Retrieval-Augmented Generation) query:

```python
from atlas import create_query_client

client = create_query_client()

# Query with context
result = client.query_with_context("How does Atlas handle document retrieval?")

# Access the response
print(result["response"])

# Access the retrieved documents
for doc in result["context"]["documents"]:
    print(f"Source: {doc['source']}")
    print(f"Relevance: {doc['relevance_score']}")
    print(doc["content"][:100] + "...")  # Show first 100 chars
```

### Document Ingestion

To add documents to Atlas's knowledge base:

```python
from atlas.knowledge.ingest import ingest_directory

# Ingest all documents in a directory
ingest_directory("/path/to/docs", recursive=True)

# Verify ingestion
from atlas.knowledge.retrieval import KnowledgeBase
kb = KnowledgeBase()
stats = kb.get_collection_stats()
print(f"Collection contains {stats['count']} documents")
```

## Testing the Installation

Atlas includes built-in test modules to verify your installation:

```bash
# Run minimal tests (no API key required)
uv run python -m atlas.tests.test_minimal

# Run mock tests (no API key required)
uv run python -m atlas.tests.test_mock

# Run the unified test runner
uv run python -m atlas.scripts.testing.run_tests mock
```

## Troubleshooting

### API Key Issues

If you encounter errors related to API keys:

- Verify that your API key is correctly set in the `.env` file
- Test your API key with the checker: `uv run python atlas/scripts/debug/check_models.py --validate-only`
- For testing without an API key, use `SKIP_API_KEY_CHECK=true` when running examples

### ChromaDB Issues

If you encounter ChromaDB-related errors:

- Check your ChromaDB installation: `uv run python atlas/scripts/debug/check_db.py --list-collections`
- Verify the database path exists and is writable
- If using a custom embeddings model, ensure it's correctly installed

### Model Provider Issues

If you have issues with model providers:

- Test the provider connection: `uv run python atlas/scripts/debug/check_models.py --provider anthropic`
- For Ollama, ensure the local server is running: `curl http://localhost:11434/api/version`
- Check that you're using the correct model name for your provider

## Next Steps

- Learn about [Atlas Architecture](../architecture/)
- Explore [Query Workflows](../workflows/query.md)
- See the [CLI Reference](../reference/cli.md) for all available options
