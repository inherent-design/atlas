---

title: System Requirements

---


# System Requirements

This document outlines the technical requirements, dependencies, and system specifications for the Atlas framework.

## Overview

Atlas is a Python-based framework for building advanced, knowledge-augmented multi-agent systems. This document specifies the requirements for developing, deploying, and using Atlas.

## Software Requirements

### Python Environment

Atlas requires a Python environment with the following specifications:

| Requirement         | Specification    | Notes                                                        |
| ------------------- | ---------------- | ------------------------------------------------------------ |
| Python Version      | >=3.13           | Earlier versions are not supported due to type hint features |
| Package Manager     | uv (recommended) | pip can be used but uv provides better dependency management |
| Virtual Environment | Required         | Isolated environment to avoid dependency conflicts           |

### Core Dependencies

The following core dependencies are required for Atlas:

| Dependency | Version  | Purpose                                      |
| ---------- | -------- | -------------------------------------------- |
| langgraph  | >=0.4.1  | Multi-agent workflow orchestration           |
| chromadb   | >=1.0.7  | Vector database for knowledge storage        |
| anthropic  | >=0.50.0 | Anthropic Claude API client                  |
| pydantic   | >=2.11.4 | Data validation and settings management      |
| pathspec   | >=0.12.1 | File pattern matching for document ingestion |
| requests   | >=2.31.0 | HTTP client for API communication            |

### Optional Dependencies

These dependencies are optional but recommended for specific functionality:

| Dependency     | Version  | Purpose                          |
| -------------- | -------- | -------------------------------- |
| openai         | >=1.20.0 | OpenAI API client for GPT models |
| types-requests | >=2.31.0 | Type stubs for requests package  |
| mypy           | >=1.8.0  | Static type checking             |
| ruff           | >=0.3.0  | Linting and code formatting      |
| black          | >=24.3.0 | Code formatting                  |
| pytest         | >=8.0.0  | Unit and integration testing     |

## Hardware Requirements

### Development Environment

Minimum specifications for a development environment:

| Component        | Minimum               | Recommended  |
| ---------------- | --------------------- | ------------ |
| CPU              | 2 cores               | 4+ cores     |
| RAM              | 4 GB                  | 8+ GB        |
| Disk Space       | 2 GB                  | 5+ GB        |
| Operating System | Linux, macOS, Windows | Linux, macOS |

### Production Environment

Recommended specifications for a production environment:

| Component  | Minimum                      | Recommended                        |
| ---------- | ---------------------------- | ---------------------------------- |
| CPU        | 4 cores                      | 8+ cores                           |
| RAM        | 8 GB                         | 16+ GB                             |
| Disk Space | 10 GB + knowledge base       | 20+ GB + knowledge base            |
| Network    | Reliable internet connection | High-speed, low-latency connection |

Note: The disk space required depends on the size of the knowledge base. Vector databases can grow significantly for large document collections.

## API Requirements

### Anthropic API

For using the Anthropic provider:

| Requirement  | Details                                                          |
| ------------ | ---------------------------------------------------------------- |
| API Key      | Valid Anthropic API key with active subscription                 |
| Rate Limits  | Sufficient rate limits for your usage patterns                   |
| Token Budget | Adequate token budget for your usage volume                      |
| Models       | Access to Claude models (claude-3-7-sonnet-20250219 recommended) |

### OpenAI API (Optional)

For using the OpenAI provider:

| Requirement  | Details                                        |
| ------------ | ---------------------------------------------- |
| API Key      | Valid OpenAI API key with active subscription  |
| Rate Limits  | Sufficient rate limits for your usage patterns |
| Token Budget | Adequate token budget for your usage volume    |
| Models       | Access to GPT models (gpt-4o recommended)      |

### Ollama (Optional)

For using the Ollama provider:

| Requirement         | Details                                      |
| ------------------- | -------------------------------------------- |
| Ollama Installation | Ollama installed and running                 |
| Models              | Required models pulled and available         |
| Hardware            | Sufficient GPU/CPU for local model inference |

## Network Requirements

Atlas requires network connectivity for API access:

| Service       | Access            | Port         | Notes                           |
| ------------- | ----------------- | ------------ | ------------------------------- |
| Anthropic API | api.anthropic.com | 443 (HTTPS)  | Required for Anthropic provider |
| OpenAI API    | api.openai.com    | 443 (HTTPS)  | Required for OpenAI provider    |
| Ollama API    | localhost         | 11434 (HTTP) | Required for Ollama provider    |

## Storage Requirements

### ChromaDB Storage

ChromaDB requires storage for the vector database:

| Requirement | Specification              | Notes                                                       |
| ----------- | -------------------------- | ----------------------------------------------------------- |
| Path        | User-configurable          | Defaults to ~/atlas_chroma_db                               |
| Permissions | Read/write access          | The application needs permission to create and modify files |
| Space       | Depends on document volume | Approximately 1-5 KB per document chunk plus embeddings     |
| Backup      | Recommended                | Regular backups of the database directory                   |

### Document Storage

For document ingestion:

| Requirement | Specification                  | Notes                                         |
| ----------- | ------------------------------ | --------------------------------------------- |
| File Types  | Text, Markdown, etc.           | Support varies by file type                   |
| Access      | Read access to source files    | Application needs permission to read files    |
| Processing  | Temporary space for processing | Used during chunking and embedding generation |

## Memory Requirements

Memory usage depends on several factors:

| Component              | Memory Usage                 | Scaling Factors                 |
| ---------------------- | ---------------------------- | ------------------------------- |
| Base Operation         | ~200-500 MB                  | -                               |
| ChromaDB               | ~50-100 MB + collection size | Scales with number of documents |
| Document Processing    | ~100-500 MB                  | Scales with document size       |
| Multi-Agent Operations | ~100 MB per active agent     | Scales with number of agents    |
| Streaming              | Minimal overhead             | -                               |

## Environment Variables

Atlas uses environment variables for configuration:

### Required Variables

| Variable          | Purpose                      | Default |
| ----------------- | ---------------------------- | ------- |
| ANTHROPIC_API_KEY | Anthropic API authentication | None    |

### Optional Variables

| Variable               | Purpose                      | Default                    |
| ---------------------- | ---------------------------- | -------------------------- |
| OPENAI_API_KEY         | OpenAI API authentication    | None                       |
| OPENAI_ORGANIZATION    | OpenAI organization ID       | None                       |
| ATLAS_DB_PATH          | ChromaDB storage location    | ~/atlas_chroma_db          |
| ATLAS_COLLECTION_NAME  | ChromaDB collection name     | atlas_knowledge_base       |
| ATLAS_DEFAULT_MODEL    | Default model to use         | claude-3-7-sonnet-20250219 |
| ATLAS_DEFAULT_PROVIDER | Default provider to use      | anthropic                  |
| ATLAS_MAX_TOKENS       | Maximum tokens for responses | 2000                       |
| ATLAS_LOG_LEVEL        | Logging verbosity            | INFO                       |
| ATLAS_ENABLE_TELEMETRY | Enable telemetry             | true                       |
| SKIP_API_KEY_CHECK     | Skip API key validation      | false                      |

## Installation Process

### Basic Installation

```bash
# Create and activate a virtual environment
uv venv
source .venv/bin/activate

# Install Atlas
uv pip install -e .

# Install development tools
uv pip install ruff black mypy pytest
```

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd atlas

# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install in development mode
uv pip install -e .

# Install development dependencies
uv pip install ruff black mypy pytest
```

## Deployment Considerations

### Environment Configuration

- Use environment variables or a `.env` file for configuration
- Set appropriate logging levels
- Configure appropriate token limits
- Set up proper error handling

### Performance Optimization

- Tune ChromaDB parameters for retrieval performance
- Configure appropriate token limits to balance quality and cost
- Consider parallel processing for multi-agent workflows
- Monitor and adjust worker count based on load

### Security Considerations

- Secure API keys using environment variables or secure storage
- Implement proper access controls for the knowledge base
- Consider data privacy when ingesting and storing documents
- Validate and sanitize user inputs

### Monitoring and Maintenance

- Implement logging for system activity
- Monitor API usage and costs
- Regularly back up the vector database
- Plan for dependency updates

## Compatibility Notes

### LangGraph Compatibility

Atlas requires LangGraph 0.4.1 or later, which includes several API changes from older versions:

- `MemorySaver` import path changed to `from langgraph.saver import MemorySaver`
- `CheckpointAt` is now available in the checkpoint module
- Graph compilation API has been enhanced with additional options
- State management has improved type safety

### Anthropic API Compatibility

Atlas works with the Anthropic API v0.50.0 or later:

- Uses the Messages API format
- Supports structured content formats
- Handles streaming through the official SDK

### ChromaDB Compatibility

Atlas requires ChromaDB 1.0.7 or later:

- Uses the PersistentClient for storage
- Implements the latest embedding and retrieval APIs
- Handles collections using the latest API format

## Related Documentation

- [Design Principles](./design_principles.md) - Overview of Atlas design philosophy
- Environment Variables Reference - Detailed list of configuration options (deprecated)
- CLI Reference - Command-line interface documentation (deprecated)
- Testing Guide - Testing approach and instructions (deprecated)
