# Atlas Usage Examples

This directory contains example scripts that demonstrate how to use various features of the Atlas framework, especially the query-only client that can be used from other agentic clients.

These examples are meant to demonstrate functionality and provide a starting point for your own implementations. They are not formal tests.

## Available Examples

### 1. Query Client (`query_example.py`)

Demonstrates the main features of the Atlas query client:
- Simple query with knowledge retrieval
- Retrieval-only mode (for when you don't need LLM generation)
- Streaming responses
- Queries with context

```bash
# Run the example
uv run python examples/query_example.py
```

### 2. Document Retrieval (`retrieval_example.py`)

Shows how to retrieve documents from the knowledge base without requiring an API key:
- Initialize the query client
- Retrieve documents for a query
- Display document metadata and content

```bash
# Run the retrieval example
uv run python examples/retrieval_example.py
```

### 3. Streaming Responses (`streaming_example.py`)

Demonstrates how to use streaming functionality for a more interactive experience:
- Character-by-character output
- Handling streaming callbacks
- Error handling and fallbacks

```bash
# Run the streaming example
uv run python examples/streaming_example.py
```

## Testing vs. Examples

Note that these scripts are **examples**, not formal tests. Formal tests for the Atlas framework are located in the `atlas/tests/` directory and follow a more structured approach with assertions and test cases.

The examples in this directory are designed to:
1. Demonstrate functionality in a realistic usage context
2. Provide a starting point for your own implementations
3. Show best practices for using Atlas features

If you want to run formal tests or verify that Atlas is working correctly, please use the testing framework in `atlas/tests/` instead.

## Running Without an API Key

For demonstration purposes, these examples can be run without an actual API key by setting the `SKIP_API_KEY_CHECK` environment variable:

```bash
# Run with mock responses (no API key needed)
SKIP_API_KEY_CHECK=true uv run python examples/query_example.py
```

This will use mock responses instead of making actual API calls, which is useful for demonstration and testing.