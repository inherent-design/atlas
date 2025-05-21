# Atlas LangGraph Implementation

This document explains the architecture and components of the Atlas LangGraph implementation.

## Overview

Atlas is implemented as a RAG (Retrieval-Augmented Generation) system using LangGraph for orchestration, ChromaDB for vector storage, and Anthropic's Claude API for language processing. The system is designed to maintain the Atlas identity while providing contextually relevant information from the Atlas documentation.

## Core Architecture

```
┌───────────────────┐        ┌───────────────────┐        ┌───────────────────┐
│                   │        │                   │        │                   │
│  Document         │───────▶│  Knowledge        │───────▶│  Atlas Agent      │
│  Processor        │        │  Base             │        │  (LangGraph)      │
│                   │        │                   │        │                   │
└───────────────────┘        └───────────────────┘        └───────────────────┘
```

### Components

1. **Document Processor** (`ingest.py`)
   - Processes Markdown files into chunks suitable for vector storage
   - Extracts metadata like file path, section title, and version
   - Handles chunking based on Markdown headings
   - Stores documents and metadata in the vector database

2. **Knowledge Base** (`tools/knowledge_retrieval.py`)
   - Provides semantic search using ChromaDB
   - Retrieves relevant documents based on user queries
   - Supports filtering by Atlas version
   - Returns documents with relevance scores

3. **Agent Framework** (`agent.py`)
   - Implements a LangGraph workflow for the Atlas agent
   - Handles knowledge retrieval and response generation
   - Maintains conversation state
   - Uses Claude's API for language generation

## Flow Diagram

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│         │     │         │     │         │     │         │     │         │
│  User   │────▶│  Agent  │────▶│Retrieval│────▶│ Claude  │────▶│  User   │
│ Message │     │  State  │     │  Node   │     │   API   │     │ Response│
│         │     │         │     │         │     │         │     │         │
└─────────┘     └─────────┘     └─────────┘     └─────────┘     └─────────┘
                                     │
                                     ▼
                               ┌─────────┐
                               │         │
                               │ChromaDB │
                               │         │
                               └─────────┘
```

## Key Files and Their Purpose

- **`ingest.py`**: Document processing and chunking system
  - `DocumentProcessor`: Main class for processing and chunking documents
  - `_split_by_headings()`: Helper method for chunking by headings
  - `generate_embeddings()`: Stores documents in ChromaDB
  - `process_directory()`: Processes all markdown files in a directory

- **`agent.py`**: Atlas agent implementation using LangGraph
  - `load_system_prompt()`: Loads custom system prompt from file
  - `create_agent()`: Creates and configures the LangGraph workflow
  - `AtlasAgent`: User-facing class for the Atlas agent
  - `retrieve()` & `generate_response()`: Core workflow functions

- **`tools/knowledge_retrieval.py`**: Knowledge base implementation
  - `KnowledgeBase`: Encapsulates ChromaDB interactions
  - `retrieve()`: Semantic search in the knowledge base
  - `retrieve_knowledge()`: LangGraph node for knowledge retrieval
  - Additional helper methods for specialized queries

- **`main.py`**: Command-line interface
  - `ingest_command()`: Handles document ingestion
  - `chat_command()`: Implements interactive chat
  - Command-line argument parsing and execution

## Data Flow

1. **Ingestion Phase**:
   - Markdown documents are read from file system
   - Documents are chunked based on headings
   - Chunks are stored in ChromaDB with metadata

2. **Retrieval Phase**:
   - User query is processed by the agent
   - Query is sent to the knowledge base
   - Relevant documents are retrieved based on semantic similarity
   - Top N most relevant documents are selected

3. **Generation Phase**:
   - Retrieved documents are formatted as context
   - Context and user query are sent to Claude API
   - Claude generates a response based on context
   - Response is returned to the user

## LangGraph Implementation

The LangGraph workflow is structured as follows:

1. **State**: Contains messages and retrieved context
2. **Nodes**:
   - `retrieve`: Retrieves knowledge from ChromaDB
   - `generate`: Generates responses using Claude
3. **Edges**:
   - Entry point → retrieve → generate → end
4. **Conditional Logic**:
   - Currently always retrieves knowledge
   - Can be extended for more sophisticated retrieval decisions

## Configuration Options

- **System Prompt**: Can be loaded from a file via command-line
- **Ingestion Directories**: Specify which directories to ingest
- **Vector Database**: Uses ChromaDB's default in-memory configuration
- **Claude Model**: Currently uses "claude-3-7-sonnet-20250219"

## Extensions and Customization

The system is designed to be extensible in several ways:

1. **Custom System Prompts**: Load alternative prompts for different personas
2. **Additional Tools**: Add new tools in the `tools/` directory
3. **Workflow Modifications**: Extend the LangGraph workflow with additional nodes
4. **Custom Document Processing**: Modify the chunking strategy in `ingest.py`

## Usage Examples

**Ingesting specific directories**:
```bash
python -m main ingest -d ./src-markdown/prev/v5 -d ./src-markdown/quantum
```

**Using a custom system prompt**:
```bash
python -m main chat -s ./src-markdown/CLAUDE_new.md
```

**Programmatic usage**:
```python
from atlas.agent import AtlasAgent

# Initialize agent with custom system prompt
agent = AtlasAgent(system_prompt_file="./path/to/prompt.md")

# Process a message
response = agent.process_message("Tell me about the Atlas framework")
print(response)
```
