# Atlas: Advanced Multi-Modal Learning & Guidance Framework

Atlas is a comprehensive meta-framework for knowledge representation, documentation, and adaptive guidance systems. It integrates advanced graph-based knowledge structures with a controller-worker architecture and LangGraph implementation to create a powerful system for knowledge management and AI-assisted guidance.

## Key Features

- **Multi-Agent Architecture**: Controller-worker pattern for parallel processing and specialization
- **LangGraph Integration**: Graph-based workflows for complex agent behaviors
- **Knowledge Persistence**: Maintains context across sessions using ChromaDB vector storage
- **Documentation Indexing**: Automatically processes and indexes documentation with gitignore-aware filtering
- **Intelligent Retrieval**: Retrieves relevant context based on user queries
- **Consistent Identity**: Maintains the Atlas identity and principles in all interactions

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
python main.py -m ingest

# Ingest from a specific directory
python main.py -m ingest -d ./src-markdown/prev/v5
```

#### Interactive Chat

Start an interactive chat session with Atlas:

```bash
# Basic CLI mode
python main.py -m cli

# With custom system prompt
python main.py -m cli -s path/to/your/system_prompt.md

# Advanced controller mode with parallel processing
python main.py -m controller --parallel
```

#### Single Query

Run a single query without an interactive session:

```bash
python main.py -m query -q "What is the trimodal methodology in Atlas?"
```

### Development

#### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest test_atlas.py

# Run with coverage
uv run pytest --cov=atlas
```

#### Code Quality

```bash
# Run linting
uv run ruff .

# Run type checking
uv run mypy .

# Format code
uv run black .
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

### Quantum Knowledge Representation System

The framework includes an LLM-optimized knowledge representation language designed for maximum semantic density with minimal token usage, enabling complex knowledge structures to be compressed without information loss.

### Key Innovations

1. **Quantum Partitioning**: Natural boundary creation in complex information spaces
2. **Adaptive Perspective**: Multi-viewpoint framework for context-sensitive knowledge representation
3. **Trimodal Methodology**: Balanced approach integrating bottom-up, top-down, and holistic perspectives
4. **Temporal Evolution**: Advanced patterns for tracking knowledge development over time
5. **Knowledge Graph Framework**: Directed relationship structures with specialized edge and node types

## Development Roadmap

See `TODO.md` for a detailed implementation plan and roadmap.

## Contributing

Guidelines for contributing to Atlas can be found in `CLAUDE.md`.

## License

[Specify your license here]