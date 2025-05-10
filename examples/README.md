# Atlas Examples

This directory contains example applications demonstrating Atlas features and capabilities.

## Example Organization

Examples are numbered to create a logical learning progression:

### Basic Usage (01-09)

| Example | Status | Description |
|---------|--------|-------------|
| [01_query_simple.py](./01_query_simple.py) | ✅ Complete | Basic querying with different providers |
| [02_query_streaming.py](./02_query_streaming.py) | ✅ Complete | Streaming responses from language models |
| [03_provider_selection.py](./03_provider_selection.py) | ✅ Complete | Provider and model selection options |
| [03_agent_options_verification.py](./03_agent_options_verification.py) | ✅ Complete | Agent initialization with provider options |

### Knowledge & Retrieval (10-19)

| Example | Status | Description |
|---------|--------|-------------|
| [10_document_ingestion.py](./10_document_ingestion.py) | ✅ Complete | Document ingestion into knowledge base |
| [11_basic_retrieval.py](./11_basic_retrieval.py) | ✅ Complete | Document retrieval with filters |
| [12_hybrid_retrieval.py.todo](./12_hybrid_retrieval.py.todo) | 🚧 Planned | Combined semantic and keyword search |
| [15_advanced_filtering.py](./15_advanced_filtering.py) | ✅ Complete | Advanced metadata and document content filtering |

### Advanced Features (20-29)

| Example | Status | Description |
|---------|--------|-------------|
| [20_tool_agent.py.todo](./20_tool_agent.py.todo) | 🚧 Planned | Tool usage with agents |
| [21_multi_agent.py.todo](./21_multi_agent.py.todo) | 🚧 Planned | Multi-agent communication |
| [22_agent_workflows.py.todo](./22_agent_workflows.py.todo) | 🚧 Planned | Agent workflows with LangGraph |

## Running Examples

All examples can be run directly with a consistent command format:

```bash
# With default settings (mock provider)
uv run python examples/01_query_simple.py

# With a specific provider
uv run python examples/01_query_simple.py --provider anthropic
uv run python examples/01_query_simple.py --provider openai
uv run python examples/01_query_simple.py --provider ollama

# With a specific model
uv run python examples/01_query_simple.py --model claude-3-opus-20240229
uv run python examples/01_query_simple.py --model gpt-4o

# With capability-based model selection
uv run python examples/01_query_simple.py --capability premium
uv run python examples/01_query_simple.py --capability inexpensive

# With verbose logging
uv run python examples/01_query_simple.py -v
```

## Environment Setup

Examples respect the following environment variables:

```bash
# API keys
export ANTHROPIC_API_KEY=sk-ant-...  # Required for Anthropic Claude models
export OPENAI_API_KEY=sk-...         # Required for OpenAI models

# Default provider and model
export ATLAS_DEFAULT_PROVIDER=anthropic        # Default provider when not specified
export ATLAS_DEFAULT_MODEL=claude-3-sonnet-... # Default model when not specified

# Logging
export ATLAS_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# Database configuration (for knowledge examples)
export ATLAS_DB_PATH=/path/to/db                 # Optional custom DB path
export ATLAS_COLLECTION_NAME=custom_collection   # Optional custom collection
```

## Common Features

All examples feature:

1. **Standardized CLI Arguments**
   - `--provider`: Choose model provider (anthropic, openai, ollama, mock)
   - `--model`: Specify model name
   - `--capability`: Model capability (inexpensive, efficient, premium, vision, standard)
   - `-v, --verbose`: Enable verbose logging

2. **Error Handling**
   - Consistent error handling across examples
   - Graceful fallbacks for unsupported features
   - Clear error messages with debugging information

3. **Provider Flexibility**
   - Works with any supported provider
   - Mock provider for testing without API keys

4. **Knowledge Base Integration**
   - Examples 10+ work with the built-in knowledge base
   - Automatically ingest example documents when needed

## Implementation Status

- ✅ **Complete**: Example is fully implemented and works as expected
- 🚧 **Planned**: Example structure is in place but needs implementation of certain features
- ❌ **Blocked**: Example cannot be completed due to missing core functionality

Files with `.todo` extensions are planned for future implementation but may not work correctly yet.

## Dependencies

Some examples have dependencies:

- `10_document_ingestion.py` should be run before other knowledge examples
- `11_basic_retrieval.py` requires documents to be ingested first

## Contributing New Examples

When creating new examples:

1. Follow the established numbering scheme
2. Use the common utilities from `common.py`
3. Support all standard CLI arguments
4. Include detailed docstrings and comments
5. Add implementation status to this README.md

For more information, see [EXAMPLES.md](./EXAMPLES.md).