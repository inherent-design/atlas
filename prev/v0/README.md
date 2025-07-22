# Atlas

<div align="center">
  <!-- Add logo image once available -->
  <p><strong>Build sophisticated AI agent systems with deep knowledge integration, powerful multi-agent orchestration, and flexible provider support</strong><br/><strong>📚 Documentation:</strong> <a href="https://atlas.inherent.design">atlas.inherent.design</a></p>
</div>

> 🚧 **Work in Progress** - Atlas is in active development. The framework is functional but not yet production-ready. APIs may change and documentation is evolving.

Atlas is an open source framework that empowers organizations to build advanced AI agent systems with enterprise-grade reliability. It combines sophisticated document processing with powerful orchestration capabilities to create knowledge-driven applications while maintaining control, flexibility, and cost-efficiency.

## Key Features

- **Knowledge-First Design**: Advanced document processing with semantic chunking, rich metadata management, and sophisticated retrieval that goes beyond basic RAG implementations
- **Multi-Agent Orchestration**: Powerful coordination of specialized agents with structured messaging, conditional workflows, and parallel processing
- **Provider Independence**: Unified interface supporting Anthropic, OpenAI, and Ollama with streaming support and resource optimization
- **Enterprise Readiness**: Comprehensive error handling, detailed monitoring, and production-grade reliability features
- **LangGraph Integration**: Graph-based workflows for complex, conditional agent behaviors
- **Knowledge Persistence**: Maintains context across sessions using ChromaDB vector storage

## Getting Started

### Prerequisites

- Python 3.13 or higher
- Anthropic API key
- `uv` for virtual environment and package management

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd atlas
```

2. Create and activate a virtual environment with `uv`:

```bash
# Install uv if you don't have it
pip install uv

# Create virtual environment
uv venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate
```

3. Install the dependencies:

```bash
uv pip install -e .
```

4. Set your Anthropic API key:

```bash
# On Linux/macOS:
export ANTHROPIC_API_KEY=your_api_key_here

# On Windows:
# set ANTHROPIC_API_KEY=your_api_key_here
```

Or create a `.env` file in the project root with:

```
ANTHROPIC_API_KEY=your_api_key_here
```

### Usage

#### Ingesting Documentation

Before using Atlas, you need to ingest documentation:

```bash
# Ingest default documentation
uv run python main.py -m ingest

# Ingest from a specific directory
uv run python main.py -m ingest -d ./src-markdown/prev/v5
```

#### Interactive Chat

Start an interactive chat session with Atlas:

```bash
# Basic CLI mode
uv run python main.py -m cli

# With custom system prompt
uv run python main.py -m cli -s path/to/your/system_prompt.md

# Using different model providers
uv run python main.py -m cli --provider openai --model gpt-4o
uv run python main.py -m cli --provider ollama --model llama3

# Advanced controller mode with parallel processing
uv run python main.py -m controller --parallel
```

#### Single Query

Run a single query without an interactive session:

```bash
uv run python main.py -m query -q "What is the trimodal methodology in Atlas?"
```

### Development

#### Utility Scripts

Atlas includes a set of utility scripts for development, testing, and debugging, organized in the `atlas/scripts` module:

1. **Debug Utilities** (`atlas/scripts/debug/`):
   - `check_db.py` - Analyze and inspect ChromaDB database contents
   - `check_models.py` - Test available model providers and their models

2. **Testing Utilities** (`atlas/scripts/testing/`):
   - `run_tests.py` - Unified test runner for all test types
   - `test_query.py` - Run test queries with different providers
   - `test_providers.py` - Compare different model providers

These tools can be invoked either directly from their module paths or through convenience wrapper scripts in the project root.

#### Testing Architecture

Atlas follows a standardized testing approach with formal tests located in the `atlas/tests/` directory. See [Testing Documentation](docs/TESTING.md) for comprehensive details.

The testing framework includes:

1. **Unit Tests** (`atlas/tests/test_*.py`):
   - Tests for specific modules (e.g., `test_models.py`, `test_env.py`, `test_schema_message_validation.py`)
   - Uses Python's unittest framework
   - Includes mocked components to avoid external dependencies

2. **Mock Tests** (`atlas/tests/test_mock.py`) - Recommended for routine development:
   - No API key required - all external dependencies are mocked
   - Very fast execution with zero API costs
   - Suitable for continuous integration

3. **Schema Validation Tests** (`atlas/tests/test_schema_*.py`):
   - Validates schema-based validation for messages, requests, and responses
   - Ensures proper serialization and deserialization of data structures
   - Tests schema compatibility across components

4. **Integration Tests** (`atlas/tests/test_api.py`):
   - Tests full system integration with real components
   - Makes real API calls (requires API key)
   - Provides cost tracking information
   - Should be used sparingly due to API costs

All tests share standardized helper functions defined in the `atlas/tests/helpers.py` module and follow consistent patterns.

#### Examples vs. Tests

The project differentiates between formal tests and usage examples:

1. **Formal Tests** (`atlas/tests/`):
   - Structured test cases with assertions
   - Designed to verify correctness
   - Run with testing frameworks
   - Include mocking and fixtures

2. **Usage Examples** (`examples/`):
   - Demonstrate how to use the Atlas API
   - Provide starting points for implementations
   - Show best practices and patterns
   - Can be run without an API key using `SKIP_API_KEY_CHECK=true`

3. **Testing Utilities** (`atlas/scripts/testing/`):
   - Test runners and helpers
   - Tools for running specific test types
   - Utilities for test result analysis

This organization keeps the concerns separated: formal verification in `tests/`, demonstrations in `examples/`, and utilities in `scripts/testing/`.

#### Running Tests and Utilities

Use the unified test runner:

```bash
# Run the preferred mock tests (no API key required)
uv run python -m atlas.scripts.testing.run_tests mock

# Run unit tests for a specific module
uv run python -m atlas.scripts.testing.run_tests unit --module core

# Run API tests for a specific provider (requires API key)
uv run python -m atlas.scripts.testing.run_tests api --provider openai --confirm

# Run multiple test types at once
uv run python -m atlas.scripts.testing.run_tests unit mock integration

# Check available model providers and their models
uv run python check_models.py --provider all

# Inspect ChromaDB contents
uv run python check_db.py

# Test with different model providers
uv run python test_providers.py --provider ollama --model llama3
uv run python test_providers.py --provider openai --model gpt-4o -i
```

> **Important Testing Notes:**
>
> 1. Always prefer the mock tests for routine development as they provide comprehensive coverage without API costs
> 2. The API tests will make actual API calls and incur charges based on token usage
> 3. When developing new features, first create mock tests before implementing the feature
> 4. All tests automatically report API cost estimation when making real API calls

#### Cost Tracking

Atlas includes cost tracking for API calls to Anthropic. When running real tests with an API key, the system will report:
- Input tokens used and their cost
- Output tokens used and their cost
- Total API cost for the operation

This feature helps monitor usage during development and testing to avoid unexpected charges.

#### Code Quality

```bash
# Run linting
uv tool run ruff check

# Run type checking
uv tool run mypy .

# Format code
uv tool run black .
```

## Architecture

Atlas is built with a modular architecture designed for extensibility and parallel processing:

```
atlas/
├── __init__.py
├── main.py                  # Entry point
├── agents/                  # Agent implementations
│   ├── __init__.py
│   ├── base.py              # Base agent class
│   ├── controller.py        # Controller agent
│   ├── worker.py            # Worker agent
│   └── registry.py          # Agent registry
├── core/                    # Core functionality
│   ├── __init__.py
│   ├── config.py            # Configuration
│   ├── settings.py          # Settings
│   └── prompts.py           # System prompts
├── graph/                   # LangGraph implementation
│   ├── __init__.py
│   ├── nodes.py             # Graph nodes
│   ├── edges.py             # Graph edges
│   ├── state.py             # State management
│   └── workflows.py         # Workflow definitions
├── knowledge/               # Knowledge management
│   ├── __init__.py
│   ├── ingest.py            # Document ingestion
│   ├── retrieval.py         # Knowledge retrieval
│   └── embedding.py         # Embedding functions
├── orchestration/           # Agent orchestration
│   ├── __init__.py
│   ├── coordinator.py       # Agent coordination
│   ├── parallel.py          # Parallel processing
│   └── scheduler.py         # Task scheduling
├── scripts/                 # Utility scripts
│   ├── __init__.py
│   ├── debug/               # Debugging utilities
│   │   ├── __init__.py
│   │   ├── check_db.py      # Database inspection
│   │   └── check_models.py  # Model provider testing
│   └── testing/             # Testing utilities
│       ├── __init__.py
│       ├── run_tests.py     # Test runner
│       ├── test_query.py    # Query testing
│       └── test_providers.py # Provider testing
├── tests/                   # Test modules
│   ├── __init__.py
│   ├── helpers.py           # Test helper functions
│   ├── test_mock.py         # Mock tests without API calls
│   ├── test_minimal.py      # Minimal tests for setup verification
│   └── test_api.py          # API integration tests
└── tools/                   # Tool implementations
    ├── __init__.py
    └── utils.py             # Utility functions
```

### Key Components

1. **Multi-Agent System**:
   - **Controller Agent**: Orchestrates workers and synthesizes results
   - **Worker Agents**: Specialized for different tasks (retrieval, analysis, drafting)

2. **LangGraph Workflows**:
   - **Basic RAG**: Simple retrieval and generation workflow
   - **Controller-Worker**: Advanced parallel processing workflow

3. **Knowledge Management**:
   - **Document Processor**: Parses and chunks documents with gitignore awareness
   - **Knowledge Base**: ChromaDB vector store with persistent storage
   - **Retrieval System**: Semantic search with relevance scoring

4. **Orchestration**:
   - **Coordinator**: Manages agent communication and task routing
   - **Scheduler**: Handles task prioritization and assignment
   - **Parallel Processing**: Executes tasks concurrently for performance

## Framework Concepts

Atlas integrates multiple approaches to knowledge management through a layered architecture:

1. **Capabilities Layer**: Task guidance, problem-solving strategies, and adaptive workflows
2. **Core Layer**: Identity, collaboration patterns, communication principles, and ethical framework
3. **Temporal Layer**: Knowledge evolution, versioning, history preservation, and future projection
4. **Knowledge Layer**: Graph fundamentals, partitioning systems, perspective frameworks, and trimodal integration

### Multi-Provider Model Support

Atlas supports multiple model providers beyond the default Anthropic Claude models:

1. **Anthropic Claude**: High-quality reasoning models (default)
2. **OpenAI GPT**: Versatile language models with wide capabilities
3. **Ollama**: Local, self-hosted models for privacy or cost-sensitive applications

See [Model Providers Documentation](docs/MODEL_PROVIDERS.md) for detailed usage instructions.

### Quantum Knowledge Representation System

The framework includes an LLM-optimized knowledge representation language designed for maximum semantic density with minimal token usage, enabling complex knowledge structures to be compressed without information loss.

### Key Innovations

1. **Quantum Partitioning**: Natural boundary creation in complex information spaces
2. **Adaptive Perspective**: Multi-viewpoint framework for context-sensitive knowledge representation
3. **Trimodal Methodology**: Balanced approach integrating bottom-up, top-down, and holistic perspectives
4. **Temporal Evolution**: Advanced patterns for tracking knowledge development over time
5. **Knowledge Graph Framework**: Directed relationship structures with specialized edge and node types
6. **API Cost Tracking**: Monitoring token usage and estimated costs during development
7. **Provider Abstraction**: Seamless switching between different model providers

## Future Vision

Atlas is evolving toward a fully distributed multi-agent framework with the following target capabilities:

### 1. Quantum-Inspired Knowledge Architecture
- Process multiple knowledge partitions simultaneously
- Automatically identify natural conceptual boundaries in complex knowledge spaces
- Maintain multiple interpretations of knowledge simultaneously

### 2. Advanced Multi-Agent Orchestration
- Dynamically adjust agent relationships based on task requirements
- Enable diverse agent types with complementary capabilities
- Break complex problems into optimal sub-tasks automatically

### 3. Perspective-Driven Knowledge Graph
- Navigate knowledge from different technical and functional viewpoints
- Adjust information relevance based on user context
- Focus on relationships between concepts rather than isolated facts

### 4. Continuous Self-Improvement
- Track efficiency and quality metrics for ongoing optimization
- Optimize token usage based on task importance (✅ Started with API cost tracking)
- Identify reusable patterns across different domains

### 5. Seamless Human-AI Collaboration
- Understand user needs beyond explicit queries
- Adapt guidance based on user expertise level
- Make agent decision processes transparent and understandable

## Documentation

Atlas provides comprehensive documentation in the `docs/` directory:

- **[MVP Strategy](docs/MVP_STRATEGY.md)**: Implementation strategy for the minimum viable product
- **[Implementation Plan](docs/TODO.md)**: Detailed roadmap and task checklist
- **[Testing Guide](docs/TESTING.md)**: Comprehensive testing approach and patterns
- **[Environment Variables](docs/ENV_VARIABLES.md)**: Configuration options via environment variables
- **[Models](docs/MODELS.md)**: Supported language models and capabilities
- **[Model Providers](docs/MODEL_PROVIDERS.md)**: Available model providers and their integration
- **[ChromaDB Viewer](docs/CHROMADB_VIEWER.md)**: Tools for inspecting the vector database

To view the documentation with proper formatting:
```bash
# Navigate to the docs directory
cd docs

# Install dependencies
npm install

# Start the documentation server
npm run dev
```

Then open your browser to `http://localhost:5173/atlas/` to browse the documentation locally, or visit `https://atlas.inherent.design` for the published documentation.

## Contributing

Guidelines for contributing to Atlas can be found in `CLAUDE.md`.

## License

[Specify your license here]
