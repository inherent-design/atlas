---
title: Overview
---

# Atlas Examples

This directory contains documentation for the example applications that showcase Atlas functionality.

## Basic Examples

- [Query Example](./query_example.md) - How to use the Atlas query client for knowledge-augmented responses
- [Retrieval Example](./retrieval_example.md) - How to use document retrieval without requiring API calls
- [Streaming Example](./streaming_example.md) - How to implement streaming responses for interactive UIs

## Advanced Examples

- [Advanced Examples Overview](./advanced_examples.md) - Comprehensive guide to advanced integration patterns
- [Multi-Agent Example](./multi_agent_example.md) - How to use the controller-worker architecture for complex tasks

## Running the Examples

All examples are available as executable Python scripts in the `examples/` directory at the root of the project:

```bash
# Run the query example
uv run python examples/query_example.py

# Run the retrieval example
uv run python examples/retrieval_example.py

# Run the streaming example
uv run python examples/streaming_example.py
```

You can run the examples without an API key by setting the `SKIP_API_KEY_CHECK` environment variable:

```bash
SKIP_API_KEY_CHECK=true uv run python examples/query_example.py
```

## Example Features

These examples demonstrate key Atlas capabilities:

1. **Knowledge-augmented responses** - Using Atlas's document retrieval for contextual answers
2. **Document retrieval** - Finding relevant documents in the knowledge base
3. **Streaming responses** - Interactive generation for better UX
4. **Error handling** - Robust handling of network issues and fallbacks
5. **Mock responses** - Running examples without API keys for development

## Integration Patterns

These examples show how to integrate Atlas into your own applications:

1. **Simple integration** - Basic query functionality for most use cases
2. **Advanced customization** - Custom callbacks, filtering, and processing
3. **Independent retrieval** - Using Atlas as a knowledge base without LLM costs
4. **Error handling patterns** - Recovery strategies for production use

## Related Documentation

- [Query Workflow](../../workflows/query.md) - How the query process works
- [Retrieval Workflow](../../workflows/retrieval.md) - Details on document retrieval
- [Getting Started Guide](../getting_started.md) - Basic tutorial for using Atlas
