# Frequently Asked Questions

This document answers common questions about using, configuring, and developing with Atlas.

## Installation and Setup

### What are the minimum requirements to run Atlas?

- Python 3.13 or higher
- Anthropic API key (for default provider)
- `uv` for virtual environment and package management

### How do I install Atlas?

```bash
# Clone the repository
git clone <repository-url>
cd atlas

# Install uv (if you don't have it already)
pip install uv

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate  # On Windows

# Install dependencies
uv pip install -e .
```

### How do I set up my API keys?

Create a `.env` file in the project root with your API keys:

```
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
```

Or set them as environment variables in your terminal:

```bash
# On Linux/macOS:
export ANTHROPIC_API_KEY=your_anthropic_api_key
export OPENAI_API_KEY=your_openai_api_key

# On Windows:
# set ANTHROPIC_API_KEY=your_anthropic_api_key
# set OPENAI_API_KEY=your_openai_api_key
```

### Where does Atlas store its database?

- By default, the ChromaDB database is stored at `~/atlas_chroma_db`
- You can change this location using the `ATLAS_DB_PATH` environment variable

## Basic Usage

### How do I ingest documents into Atlas?

```bash
# Ingest default documentation
uv run python main.py -m ingest

# Ingest from a specific directory
uv run python main.py -m ingest -d ./my-documents
```

### How do I start an interactive chat with Atlas?

```bash
# Basic CLI mode
uv run python main.py -m cli

# With custom system prompt
uv run python main.py -m cli -s path/to/your/system_prompt.md
```

### How do I run a single query without starting an interactive session?

```bash
uv run python main.py -m query -q "What is the trimodal methodology in Atlas?"
```

### Can I use Atlas as a library in my own Python application?

Yes, Atlas provides a lightweight query client that you can use in your own applications:

```python
from atlas import create_query_client

# Create a client
client = create_query_client()

# Simple query
response = client.query("What is the trimodal methodology?")
print(response)

# Document retrieval only (no API key needed)
documents = client.retrieve_only("knowledge graph structure")
print(f"Found {len(documents)} relevant documents")

# Streaming response
def print_streaming(delta, full_text):
    print(delta, end="", flush=True)

client.query_streaming("Explain conditional edge routing", print_streaming)
```

### Can I use a different model provider than Anthropic?

Yes, Atlas supports multiple model providers:

```bash
# Using OpenAI
uv run python main.py -m cli --provider openai --model gpt-4o

# Using Ollama
uv run python main.py -m cli --provider ollama --model llama3
```

## Model Providers

### Which model providers does Atlas support?

Atlas currently supports three model providers:

- **Anthropic** (Claude models, default)
- **OpenAI** (GPT models)
- **Ollama** (local open source models)

### What models are available for each provider?

- **Anthropic**:
  - claude-3-7-sonnet-20250219 (default)
  - claude-3-5-sonnet-20240620
  - claude-3-opus-20240229
  - claude-3-sonnet-20240229
  - claude-3-haiku-20240307

- **OpenAI**:
  - gpt-4o (default)
  - gpt-4-turbo
  - gpt-4
  - gpt-3.5-turbo

- **Ollama**:
  - llama3 (default)
  - mistral
  - gemma
  - And any other model you have installed in your Ollama setup

### Do I need API keys for all providers?

- **Anthropic** and **OpenAI** require API keys that you must obtain from their respective services
- **Ollama** doesn't need an API key but requires Ollama to be installed and running locally on your machine

### How do I use Ollama with Atlas?

1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Start the Ollama server: `ollama serve`
3. Pull the model you want to use: `ollama pull llama3`
4. Run Atlas with Ollama provider: `uv run python main.py -m cli --provider ollama --model llama3`

## Configuration

### How do I configure Atlas using environment variables?

Create a `.env` file in the project root or set environment variables in your terminal. The key environment variables include:

- `ANTHROPIC_API_KEY`: API key for Anthropic Claude
- `OPENAI_API_KEY`: API key for OpenAI
- `ATLAS_DB_PATH`: Path to ChromaDB database
- `ATLAS_COLLECTION_NAME`: ChromaDB collection name
- `ATLAS_DEFAULT_PROVIDER`: Default model provider
- `ATLAS_DEFAULT_MODEL`: Default model to use
- `ATLAS_MAX_TOKENS`: Maximum tokens for model responses
- `ATLAS_ENABLE_TELEMETRY`: Enable or disable telemetry
- `SKIP_API_KEY_CHECK`: Skip API key validation (for testing)

See the [Environment Variables Reference](env_variables.md) for a complete list.

### What is the precedence order for configuration?

Atlas uses the following precedence order for configuration (highest to lowest priority):

1. Command-line arguments
2. Environment variables
3. Default values

### How do I set provider-specific default models?

Use environment variables specific to each provider:

- `ATLAS_ANTHROPIC_DEFAULT_MODEL`: Default model for Anthropic
- `ATLAS_OPENAI_DEFAULT_MODEL`: Default model for OpenAI
- `ATLAS_OLLAMA_DEFAULT_MODEL`: Default model for Ollama

## Knowledge Management

### How does Atlas store and retrieve knowledge?

Atlas uses ChromaDB as a vector database for storing document embeddings:

1. **Ingestion**: Documents are processed, chunked, and embedded during ingestion
2. **Storage**: Embeddings and metadata are stored in ChromaDB collections
3. **Retrieval**: Semantic search is used to find relevant documents for queries
4. **Context**: Relevant documents are used as context for the language model

### How do I customize document ingestion?

You can adjust the following settings:

- Chunk size and overlap (using the `--chunk-size` and `--chunk-overlap` CLI options)
- Input directories (using the `-d` or `--dir` option)
- File extensions (using the `--ext` option)

By default, Atlas uses gitignore-aware filtering to exclude irrelevant files.

### Can I view the contents of the knowledge base?

Yes, you can use the database inspection tool:

```bash
uv run python atlas/scripts/debug/check_db.py
```

A more comprehensive ChromaDB viewer is planned (see docs/CHROMADB_VIEWER.md).

## Testing

### How do I run tests for Atlas?

```bash
# Run all tests
uv run python -m atlas.scripts.testing.run_tests all

# Run only mock tests (no API key required)
uv run python -m atlas.scripts.testing.run_tests mock

# Run unit tests for a specific module
uv run python -m atlas.scripts.testing.run_tests unit --module models

# Run integration tests
uv run python -m atlas.scripts.testing.run_tests integration
```

### Can I test Atlas without API keys?

Yes, you have two options:

1. Use the mock tests:
   ```bash
   uv run python atlas/scripts/testing/run_tests.py --test-type mock
   ```

2. Run examples with `SKIP_API_KEY_CHECK=true`:
   ```bash
   SKIP_API_KEY_CHECK=true uv run python examples/query_example.py
   ```

### How does Atlas track API usage and costs?

Atlas includes built-in cost tracking for API calls. When running real tests with an API key, the system will report:

- Input tokens used and their cost
- Output tokens used and their cost
- Total API cost for the operation

Example output:
```
API Usage: 683 input tokens, 502 output tokens
Estimated Cost: $0.009579 (Input: $0.002049, Output: $0.007530)
```

## Architecture and Extensions

### What is the multi-agent architecture in Atlas?

Atlas uses a controller-worker pattern where:

- **Controller Agent**: Orchestrates workers and synthesizes results
- **Worker Agents**: Specialized for different tasks (retrieval, analysis, drafting)

This architecture enables complex workflows and parallel processing of tasks.

### How does the LangGraph integration work?

Atlas uses LangGraph for graph-based workflows:

- **StateGraph**: Defines the workflow topology with nodes and edges
- **State Models**: Define the data structure for each state transition
- **Node Functions**: Implement the logic for each step in the workflow
- **Conditional Edges**: Route execution based on dynamic conditions

Simple workflows use a direct graph with basic nodes, while advanced workflows use the controller-worker pattern with parallel processing.

### Can I extend Atlas with custom agents?

Yes, you can create custom agent implementations:

1. Create a new agent class that extends `atlas.agents.base.BaseAgent`
2. Implement the required methods (`process_message`, etc.)
3. Register your agent with the agent registry
4. Use your custom agent in workflows

See the [Custom Workflows Guide](../workflows/custom_workflows.md) for detailed instructions.

### How do I create custom workflows?

Atlas allows you to create custom workflows using LangGraph:

1. Define your state model using Pydantic
2. Create node functions for each step in your workflow
3. Build a StateGraph with your nodes and edges
4. Compile and execute the graph

See the [Custom Workflows Guide](../workflows/custom_workflows.md) for examples and best practices.

## Troubleshooting

### I'm getting authentication errors with API providers

- Verify your API keys are correctly set in environment variables
- Check if your API key has expired or has reached its usage limit
- Ensure you're using the correct API endpoint
- Check for network issues that might be preventing API access

### How do I diagnose issues with the knowledge base?

- Run the database inspection tool: `uv run python atlas/scripts/debug/check_db.py`
- Check if documents were properly ingested
- Verify that the ChromaDB path is correctly set
- Look for error messages in the logs

### Atlas is not finding relevant information from my documents

- Try re-ingesting documents with different chunk settings
- Make sure your documents are in a format that can be properly processed
- Check if the documents were successfully ingested into ChromaDB
- Try using more specific queries that match the content of your documents

### I can't connect to Ollama

- Make sure Ollama is installed and running: `ollama serve`
- Verify you have pulled the model you're trying to use: `ollama pull llama3`
- Check that Ollama is accessible at `http://localhost:11434`
- Look for error messages in the Ollama logs

### How do I handle rate limits with API providers?

- Implement backoff and retry logic in your code
- Use the built-in retry mechanisms in Atlas
- Consider spreading load across multiple API keys
- Monitor your API usage and adjust your implementation accordingly

## Development and Roadmap

### What is the current development status of Atlas?

- The core infrastructure is completed
- Multi-provider model support is implemented
- Knowledge retrieval and document processing are working
- Current focus is on enhancing provider implementations, testing, and documentation

### What's on the roadmap for future development?

- Enhanced knowledge retrieval with advanced embedding techniques
- Improved multi-agent intelligence with specialized workers
- Provider optimizations like connection pooling and health checks
- Better document chunking and metadata handling
- Advanced workflows with dynamic agent allocation

See the [TODO.md](../project-management/tracking/todo.md) file for a detailed implementation plan with specific tasks and priorities.

### How can I check which model providers are available on my system?

Run the model check utility:

```bash
uv run python atlas/scripts/debug/check_models.py --provider all
```

This will attempt to initialize each provider and report its status.

## Additional Resources

- [API Reference](api.md): Complete API documentation
- [Environment Variables Reference](env_variables.md): Configuration options
- [CLI Reference](cli.md): Command-line interface options
- [Getting Started Guide](../guides/getting_started.md): Introduction to Atlas
- [Testing Guide](../guides/testing.md): Testing Atlas components
- [Examples](https://github.com/inherent-design/atlas/tree/main/examples): Code examples and use cases