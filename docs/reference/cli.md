# Atlas CLI Reference

This document provides a comprehensive reference for all command-line tools and interfaces available in the Atlas framework.

## Main Entry Point

The primary CLI interface for Atlas is through `main.py`.

```bash
uv run python main.py [options]
```

### Operation Modes

Atlas supports several operation modes through the `-m/--mode` flag:

| Mode         | Description                                                          |
| ------------ | -------------------------------------------------------------------- |
| `cli`        | Interactive CLI mode for direct conversational interaction (default) |
| `ingest`     | Document ingestion mode to add documents to the knowledge base       |
| `query`      | Single query mode for one-off questions                              |
| `controller` | Multi-agent controller mode for orchestrating worker agents          |
| `worker`     | Worker agent mode for specialized tasks in a multi-agent system      |

### Common Options

```
-h, --help            Show help message and exit
-m {cli,ingest,query,worker,controller}, --mode {cli,ingest,query,worker,controller}
                      Operation mode for Atlas (default: cli)
-s SYSTEM_PROMPT, --system-prompt SYSTEM_PROMPT
                      Path to system prompt file
-c COLLECTION, --collection COLLECTION
                      Name of the ChromaDB collection to use (default: atlas_knowledge_base)
--db-path DB_PATH     Path to ChromaDB database directory
```

### Ingestion Options

The following options are available in `ingest` mode:

```
-d DIRECTORY, --directory DIRECTORY
                      Directory to ingest documents from
-r, --recursive       Recursively process directories
```

### LangGraph Options

Options for multi-agent workflows with LangGraph:

```
--parallel            Enable parallel processing with LangGraph
--workers WORKERS     Number of worker agents to spawn in controller mode (default: 3)
--workflow {rag,advanced,custom,retrieval,analysis,draft}
                      LangGraph workflow to use or worker type in worker mode (default: rag)
```

### Model Provider Options

Options for selecting model providers and configurations:

```
--provider {anthropic,openai,ollama}
                      Model provider to use (default: anthropic)
--model MODEL         Model to use (provider-specific, e.g., claude-3-opus-20240229, gpt-4o, llama3)
                      (default: claude-3-7-sonnet-20250219)
--max-tokens MAX_TOKENS
                      Maximum tokens in model responses (default: 2000)
--base-url BASE_URL   Base URL for API (used primarily with Ollama, default: http://localhost:11434)
```

### Query Options

Options specific to `query` mode:

```
-q QUERY, --query QUERY
                      Single query to process (query mode only)
```

## Example Commands

### Basic Usage

```bash
# Run in CLI mode with default system prompt
uv run python main.py -m cli

# Run with custom system prompt
uv run python main.py -m cli -s path/to/your/system_prompt.md

# Ingest documents
uv run python main.py -m ingest -d path/to/your/documents/

# Run in controller mode with parallel processing
uv run python main.py -m controller --parallel

# Run a single query
uv run python main.py -m query -q "What is the trimodal methodology in Atlas?"
```

### Model Provider Examples

```bash
# Use the Anthropic provider (default)
uv run python main.py --provider anthropic --model claude-3-opus-20240229

# Use the OpenAI provider
uv run python main.py --provider openai --model gpt-4o

# Use the Ollama provider with a local model
uv run python main.py --provider ollama --model llama3 --base-url http://localhost:11434
```

### Multi-Agent Examples

```bash
# Run as a controller with 5 worker agents
uv run python main.py -m controller --workers 5

# Run as a retrieval worker
uv run python main.py -m worker --workflow retrieval

# Run an advanced workflow with parallel processing
uv run python main.py -m controller --workflow advanced --parallel
```

## Testing Tools

Atlas includes several testing utilities for verifying functionality.

### Unified Test Runner

The unified test runner is available at `atlas/scripts/testing/run_tests.py`:

```bash
uv run python -m atlas.scripts.testing.run_tests [test_types] [options]
```

#### Options

```
positional arguments:
  test_types            Types of tests to run: unit, mock, integration, api, all

options:
  -h, --help            Show help message and exit
  -m, --module MODULE   Module to filter tests by (e.g., 'core', 'models')
  -p, --provider {openai,anthropic,ollama}
                        Provider to filter API tests by
  --confirm             Skip confirmation prompt for API tests
  --expensive           Run expensive API tests (GPT-4, Claude Opus, etc.)
  --cost-limit COST_LIMIT
                        Maximum cost limit for API tests (default: 0.1)
  --enforce-cost-limit  Enforce cost limit by failing tests that exceed it
```

#### Test Types

| Test Type | Description                                         |
| --------- | --------------------------------------------------- |
| `mock`    | Tests using mock responses (no API key required)    |
| `unit`    | Unit tests for specific modules                     |
| `minimal` | Basic functionality verification                    |
| `api`     | Tests requiring actual API calls (API key required) |
| `all`     | All test types combined                             |

#### Examples

```bash
# Run mock tests (no API key required)
uv run python -m atlas.scripts.testing.run_tests mock

# Run unit tests for a specific module
uv run python -m atlas.scripts.testing.run_tests unit --module models

# Run API tests for a specific provider
uv run python -m atlas.scripts.testing.run_tests api --provider openai --confirm

# Run multiple test types at once
uv run python -m atlas.scripts.testing.run_tests unit mock integration

# Run all tests (will prompt for confirmation before running API tests)
uv run python -m atlas.scripts.testing.run_tests all
```

## Debug Tools

Atlas includes debug utilities for inspecting system components.

### Database Inspector

The ChromaDB database inspector is available at `atlas/scripts/debug/check_db.py`:

```bash
uv run python atlas/scripts/debug/check_db.py [options]
```

#### Options

```
-h, --help                Show help message and exit
-p PATH, --path PATH      Path to ChromaDB database (default: ~/atlas_chroma_db)
-c NAME, --collection NAME
                         Collection name to inspect (default: atlas_knowledge_base)
-l, --list-collections    List all collections in the database
-d, --details            Show detailed information about the collection
-s QUERY, --search QUERY  Search for documents containing the query
```

#### Examples

```bash
# List collections in the database
uv run python atlas/scripts/debug/check_db.py --list-collections

# Show details about the default collection
uv run python atlas/scripts/debug/check_db.py --details

# Search for documents
uv run python atlas/scripts/debug/check_db.py --search "trimodal methodology"
```

### Model Provider Checker

The model provider checker is available at `atlas/scripts/debug/check_models.py`:

```bash
uv run python atlas/scripts/debug/check_models.py [options]
```

#### Options

```
-h, --help                  Show help message and exit
-p {anthropic,openai,ollama,all}, --provider {anthropic,openai,ollama,all}
                           Provider to test (default: all)
-m MODEL, --model MODEL     Specific model to test with the provider
-q QUERY, --query QUERY     Test query to send to the model (default: "Hello, world!")
-v, --validate-only         Only validate API keys without making API calls
```

#### Examples

```bash
# Test the Anthropic provider
uv run python atlas/scripts/debug/check_models.py --provider anthropic

# Test a specific model
uv run python atlas/scripts/debug/check_models.py --provider openai --model gpt-4o

# Test with a custom query
uv run python atlas/scripts/debug/check_models.py --query "What is Atlas?"

# Validate API keys without making API calls
uv run python atlas/scripts/debug/check_models.py --validate-only
```

## Example Scripts

Atlas includes example scripts demonstrating framework functionality:

| Script                          | Description                          |
| ------------------------------- | ------------------------------------ |
| `examples/query_example.py`     | Basic query functionality            |
| `examples/streaming_example.py` | Streaming response demonstration     |
| `examples/retrieval_example.py` | Document retrieval without API calls |
| `examples/telemetry_example.py` | Telemetry system demonstration       |

These examples can be run with the `SKIP_API_KEY_CHECK=true` environment variable to use mock responses instead of actual API calls:

```bash
# Run with mock responses
SKIP_API_KEY_CHECK=true uv run python examples/query_example.py
```

## Environment Variables

Atlas CLI tools respect all environment variables defined in the project. See the [Environment Variables Reference](./env_variables.md) for a complete list.

## Related Documentation

- [Getting Started Guide](../guides/getting_started.md) - Basic tutorial for using Atlas
- [Environment Variables Reference](./env_variables.md) - Complete list of environment variables
- [Architecture Overview](../architecture/) - High-level system architecture
