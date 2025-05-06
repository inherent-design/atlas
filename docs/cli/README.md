# Atlas CLI Tools

This document lists all the command-line tools available in the Atlas project, along with their available options and usage examples.

## Main Entry Points

### main.py

The primary CLI interface for the Atlas framework.

**Usage:**
```bash
uv run python main.py [options]
```

**Modes:**
- `-m cli` - Interactive CLI mode (default)
- `-m ingest` - Document ingestion mode
- `-m query` - Single query mode
- `-m controller` - Multi-agent controller mode
- `-m worker` - Worker agent mode

**Common Options:**
```
  -h, --help            show this help message and exit
  -m {cli,ingest,query,worker,controller}, --mode {cli,ingest,query,worker,controller}
                        Operation mode for Atlas (default: cli)
  -s SYSTEM_PROMPT, --system-prompt SYSTEM_PROMPT
                        Path to system prompt file
  -c COLLECTION, --collection COLLECTION
                        Name of the ChromaDB collection to use (default: atlas_knowledge_base)
  --db-path DB_PATH     Path to ChromaDB database directory
```

**Ingestion Options:**
```
  -d DIRECTORY, --directory DIRECTORY
                        Directory to ingest documents from
  -r, --recursive       Recursively process directories
```

**LangGraph Options:**
```
  --parallel            Enable parallel processing with LangGraph
  --workers WORKERS     Number of worker agents to spawn in controller mode (default: 3)
  --workflow {rag,advanced,custom,retrieval,analysis,draft}
                        LangGraph workflow to use or worker type in worker mode (default: rag)
```

**Model Provider Options:**
```
  --provider {anthropic,openai,ollama}
                        Model provider to use (default: anthropic)
  --model MODEL         Model to use (provider-specific, e.g., claude-3-opus-20240229, gpt-4o, llama3)
                        (default: claude-3-7-sonnet-20250219)
  --max-tokens MAX_TOKENS
                        Maximum tokens in model responses (default: 2000)
  --base-url BASE_URL   Base URL for API (used primarily with Ollama, default: http://localhost:11434)
```

**Query Options:**
```
  -q QUERY, --query QUERY
                        Single query to process (query mode only)
```

**Examples:**
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

# Run with Ollama provider
uv run python main.py --provider ollama --model llama3

# Run as a worker agent
uv run python main.py -m worker --workflow retrieval
```

## Testing Scripts

### atlas/scripts/testing/run_tests.py

A unified test runner for Atlas.

**Usage:**
```bash
uv run python atlas/scripts/testing/run_tests.py [options]
```

**Options:**
```
  -h, --help            show this help message and exit
  -t {unit,mock,minimal,api,all}, --test-type {unit,mock,minimal,api,all}
                        Type of tests to run (default: mock)
  -m MODULE, --module MODULE
                        Module to test (e.g., 'models', 'env')
  --api-test {base,controller,coordinator,workflows,all}
                        API test to run (default: base)
  -s SYSTEM_PROMPT, --system-prompt SYSTEM_PROMPT
                        Path to system prompt file for API tests
  -q QUERY, --query QUERY
                        Query to test with for API tests
```

**Examples:**
```bash
# Run mock tests (no API key required)
uv run python atlas/scripts/testing/run_tests.py --test-type mock

# Run unit tests for a specific module
uv run python atlas/scripts/testing/run_tests.py --test-type unit --module models

# Run minimal tests (basic functionality verification)
uv run python atlas/scripts/testing/run_tests.py --test-type minimal

# Run API tests for the base agent
uv run python atlas/scripts/testing/run_tests.py --test-type api --api-test base

# Run API tests with a custom query
uv run python atlas/scripts/testing/run_tests.py --test-type api --api-test base --query "Your query here"

# Run all tests
uv run python atlas/scripts/testing/run_tests.py --test-type all
```

### scripts/testing/test_new_modules.py

Tests new modules added to the Atlas framework.

**Usage:**
```bash
uv run python scripts/testing/test_new_modules.py
```

## Debug Scripts

### atlas/scripts/debug/check_db.py

Checks the ChromaDB database status and contents.

**Usage:**
```bash
uv run python atlas/scripts/debug/check_db.py [options]
```

**Options:**
```
  -h, --help                show this help message and exit
  -p PATH, --path PATH      Path to ChromaDB database (default: ~/atlas_chroma_db)
  -c NAME, --collection NAME
                           Collection name to inspect (default: atlas_knowledge_base)
  -l, --list-collections    List all collections in the database
  -d, --details            Show detailed information about the collection
  -s QUERY, --search QUERY  Search for documents containing the query
```

**Examples:**
```bash
# List collections in the database
uv run python atlas/scripts/debug/check_db.py --list-collections

# Show details about the default collection
uv run python atlas/scripts/debug/check_db.py --details

# Search for documents
uv run python atlas/scripts/debug/check_db.py --search "trimodal methodology"
```

### atlas/scripts/debug/check_models.py

Tests model provider connectivity and functionality.

**Usage:**
```bash
uv run python atlas/scripts/debug/check_models.py [options]
```

**Options:**
```
  -h, --help                  show this help message and exit
  -p {anthropic,openai,ollama,all}, --provider {anthropic,openai,ollama,all}
                             Provider to test (default: all)
  -m MODEL, --model MODEL     Specific model to test with the provider
  -q QUERY, --query QUERY     Test query to send to the model (default: "Hello, world!")
  -v, --validate-only         Only validate API keys without making API calls
```

**Examples:**
```bash
# Test the Anthropic provider
uv run python atlas/scripts/debug/check_models.py --provider anthropic

# Test a specific model
uv run python atlas/scripts/debug/check_models.py --provider openai --model gpt-4

# Test with a custom query
uv run python atlas/scripts/debug/check_models.py --query "What is Atlas?"

# Validate API keys without making API calls
uv run python atlas/scripts/debug/check_models.py --validate-only
```

## Example Files

These are not CLI tools per se, but demonstrate how to use the Atlas framework in your own code.

### examples/query_example.py

Demonstrates basic query functionality.

**Usage:**
```bash
uv run python examples/query_example.py
```

**Environment Variables:**
- `SKIP_API_KEY_CHECK=true` - Run with mock responses instead of actual API calls

### examples/streaming_example.py

Demonstrates streaming responses.

**Usage:**
```bash
uv run python examples/streaming_example.py
```

**Environment Variables:**
- `SKIP_API_KEY_CHECK=true` - Run with mock responses instead of actual API calls

### examples/retrieval_example.py

Demonstrates document retrieval without requiring an API key.

**Usage:**
```bash
uv run python examples/retrieval_example.py
```

## Environment Variables

All of these CLI tools respect the environment variables defined in the project. See [ENV_VARIABLES.md](../ENV_VARIABLES.md) for a complete list of available environment variables.