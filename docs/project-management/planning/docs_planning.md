# Atlas Documentation Planning

This document outlines the planning and tracking system for Atlas documentation, including the documentation structure, completed tasks, and ongoing plans for documentation improvement.

## Current Implementation Status

```
✅ Completed documentation     (60 files)
✅ Fixed import system issues  (Fixed circular imports, consolidated KnowledgeBase implementation)
✅ Verified hybrid search implementation with RetrievalSettings interface
✅ Enhanced document ID format (parent_dir/filename.md instead of full relative paths)
✅ Added progress indicators for ingestion and embedding processes
✅ Added consistent settings classes (RetrievalSettings, ProcessingSettings)
🚀 Next focus: Query caching system, Structured message format, Provider pooling
```

## Documentation Structure

```
docs/
├── architecture/             # Top-down design ✅
│   ├── components.md         # Component relationships ✅
│   ├── data_flow.md          # Data flow patterns ✅
│   ├── design_principles.md  # Design patterns & principles ✅
│   ├── index.md              # Architecture section index/overview ✅
│   ├── module_interaction.md # Module interaction and integration ✅
│   └── system_requirements.md # Dependencies & requirements ✅
├── components/               # Bottom-up implementation
│   ├── agents/               # Agent components ✅
│   │   ├── controller.md     # Controller agent ✅
│   │   └── workers.md        # Worker agents ✅
│   ├── core/                 # Core components ✅
│   │   ├── config.md         # Configuration ✅
│   │   ├── env.md            # Environment variables ✅
│   │   ├── errors.md         # Error handling ✅
│   │   ├── prompts.md        # Prompt system ✅
│   │   └── telemetry.md      # Telemetry and tracing ✅
│   ├── graph/                # Graph components ✅
│   │   ├── edges.md          # Graph edges ✅
│   │   ├── index.md          # Graph section index/overview ✅
│   │   ├── nodes.md          # Graph nodes ✅
│   │   └── state.md          # State management ✅
│   ├── knowledge/            # Knowledge components ✅
│   │   ├── index.md          # Knowledge section index/overview ✅
│   │   ├── ingestion.md      # Document ingestion ✅
│   │   └── retrieval.md      # Retrieval functionality ✅
│   └── models/               # Model providers ✅
│       ├── anthropic.md      # Anthropic integration ✅
│       ├── index.md          # Models section index/overview ✅
│       ├── mock.md           # Mock provider for testing ✅
│       ├── ollama.md         # Ollama integration ✅
│       └── openai.md         # OpenAI integration ✅
├── guides/                   # Developer guides ✅
│   ├── configuration.md      # Configuration guide ✅
│   ├── examples/             # Code examples ✅
│   │   ├── advanced_examples.md  # Advanced usage patterns ✅
│   │   ├── hybrid_retrieval_example.md  # Hybrid search example ✅
│   │   ├── index.md          # Examples index/overview (formerly README.md) ✅
│   │   ├── multi_agent_example.md # Multi-agent workflows ✅
│   │   ├── query_example.md  # Query client usage ✅
│   │   ├── retrieval_example.md # Document retrieval ✅
│   │   └── streaming_example.md # Streaming responses ✅
│   ├── getting_started.md    # Getting started guide ✅
│   ├── testing.md            # Testing guide ✅
│   └── type_checking.md      # Type checking guide ✅
├── index.md                  # Main documentation landing page ✅
├── project-management/       # Project management documents ✅
│   ├── planning/             # Planning documents ✅
│   │   └── docs_planning.md  # Documentation planning ✅
│   ├── roadmap/              # Project roadmaps ✅
│   │   └── mvp_strategy.md   # MVP implementation strategy ✅
│   └── tracking/             # Progress tracking ✅
│       └── todo.md           # Todo list and progress tracking ✅
├── reference/                # Reference documentation ✅
│   ├── api.md                # API reference ✅
│   ├── cli.md                # CLI options ✅
│   ├── env_variables.md      # Environment variables ✅
│   └── faq.md                # FAQ ✅
└── workflows/                # Holistic integration ✅
    ├── custom_workflows.md   # Creating custom workflows ✅
    ├── multi_agent.md        # Multi-agent workflows ✅
    ├── query.md              # Query workflow ✅
    └── retrieval.md          # Retrieval workflow ✅
```

## Completed Documentation Tasks

- [x] Core system components (config, env, errors, prompts)
- [x] Knowledge system (overview, ingestion, retrieval)
- [x] Graph system (state, nodes, edges)  
- [x] Model providers (base, anthropic, openai, ollama)
- [x] Workflow documentation (query, retrieval, multi-agent)
- [x] User guides (getting started, configuration, testing)
- [x] Reference documentation (API, CLI, env variables)

## Recent Implementation Changes

- [x] **Provider Implementations**
  - OpenAI and Ollama providers with streaming support
  - Token usage tracking and cost calculation
  - Enhanced error handling and API key validation
  - Updated pricing for all providers

- [x] **Token Usage System**
  - TokenUsage and CostEstimate classes with to_dict() methods
  - Cost formatting with precision based on magnitude
  - Provider-specific cost calculation implementations
  - Comprehensive token tracking tests

- [x] **Streaming Functionality**
  - Stream handler implementation for all providers
  - Callback-based streaming for interactive UIs
  - Token and cost tracking during streaming
  - Command-line argument support in examples

- [x] **Knowledge System Enhancements**
  - Adaptive document chunking with semantic boundaries
  - Content deduplication with normalized hashing
  - Real-time directory monitoring with watchdog
  - Hybrid semantic and keyword search retrieval
  - Customizable embedding strategies

## Content Migration Tracking

| Source Document    | Target Location(s)                               | Status     |
| ------------------ | ------------------------------------------------ | ---------- |
| CHROMADB_VIEWER.md | guides/examples/chromadb_viewer.md               | Deprecated |
| ENV_VARIABLES.md   | reference/env_variables.md                       | Complete ✅ |
| MODELS.md          | components/models/index.md                       | Complete ✅ |
| MODEL_PROVIDERS.MD | components/models/{anthropic,openai,ollama}.md   | Complete ✅ |
| MVP_STRATEGY.md    | project-management/roadmap/mvp_strategy.md       | Complete ✅ |
| TESTING.md         | guides/testing.md                                | Complete ✅ |
| TODO.md            | project-management/tracking/todo.md              | Complete ✅ |
| TYPE_CHECKING.md   | guides/type_checking.md                          | Complete ✅ |
| cli/README.md      | reference/cli.md                                 | Complete ✅ |
| DOCS_TODO.md       | project-management/planning/docs_planning.md     | Complete ✅ |
| index.md           | index.md (new structure)                         | Complete ✅ |
| README.md files    | Converted to index.md files for directory routes | Complete ✅ |

## Documentation Principles

### Trimodal Documentation Approach

The Atlas documentation follows a Trimodal approach that provides comprehensive coverage from multiple perspectives:

1. **Top-Down Design** (Architecture)
   - High-level architecture and design principles
   - System requirements and dependencies
   - Component relationships and patterns
   - Data flow diagrams and system interaction maps

2. **Bottom-Up Implementation** (Components)
   - Detailed component functionality and interfaces
   - Implementation details and patterns
   - API references and usage examples
   - Configuration options and customization

3. **Holistic Integration** (Workflows)
   - End-to-end workflow documentation
   - Integration patterns and best practices
   - Cross-cutting concerns and considerations
   - User journey and experience documentation

### Documentation Standards

All Atlas documentation adheres to the following standards:

1. **Structure and Organization**
   - Clear hierarchical structure with logical grouping
   - Consistent file naming and organization
   - Standardized table of contents and navigation
   - Proper cross-referencing between related documents
   - Index files (`index.md`) used for directory-level routes

2. **Content Quality**
   - Comprehensive coverage of all critical functionality
   - Clear, concise explanations with appropriate detail
   - Practical code examples that demonstrate usage
   - Consistent terminology and language throughout

3. **Formatting and Style**
   - Consistent Markdown formatting and styling
   - Proper use of headings, lists, tables, and code blocks
   - Diagrams and visual aids where appropriate
   - Clear distinction between different types of information

4. **Linking Practices**
   - Two different linking styles used for different contexts:
     
     a) **Regular Content Links** (for local Markdown compatibility):
     - Include `.md` extensions for all file links (e.g., `[Link Text](./path/to/file.md)`)
     - Use directory paths without trailing `index.md` for directory index files (e.g., `[Link Text](./directory/)`)
     - Links to sibling files use `./filename.md` format
     - Links to parent directory files use `../filename.md` format
     - Relative paths preferred for all internal documentation links

     b) **VitePress Frontmatter Links** (hero sections, config files):
     - Omit `.md` extensions in VitePress-specific sections (e.g., `/guides/getting_started`)
     - Use directory paths with trailing slash for index pages (e.g., `/directory/`) 
     - Use absolute paths for root-relative references in VitePress config

   - Links checked and verified during the build process

5. **Maintenance Process**
   - Regular reviews and updates alongside code changes
   - Version control for documentation aligned with code
   - Deprecation notices for outdated information
   - Collaborative editing and review process

6. **Diagram Standards**
   - Mermaid diagrams used for all technical diagrams
   - No inline styling in diagrams (rely on VitePress theme styling)
   - Consistent diagram types for similar content
   - Simple, focused diagrams that illustrate key concepts

## Documentation Update Tasks

### Provider Implementation Updates

1. **Update Model Provider Documentation**
   - [x] Update pricing information to match latest implementations (high priority)
     - [x] Update OpenAI pricing in openai.md with GPT-4.1, GPT-4.1-mini, and GPT-4.1-nano models
     - [x] Update GPT-4o pricing from $15.00/M to $20.00/M for output tokens
     - [x] Add o-series models (o3, o4-mini) documentation and pricing
     - [x] Update Anthropic pricing with Claude 3.5 Haiku ($0.80/M input, $4.0/M output)
   - [x] Update model lists and defaults in provider documentation
     - [x] Change OpenAI default model from GPT-4o to GPT-4.1 in examples
     - [x] Add GPT-4o-mini to model list and examples
     - [x] Add Claude 3.5 Haiku to Anthropic model list and examples
   - [x] Update code examples to use latest models and APIs
     - [x] Update streaming examples with latest implementation patterns
     - [x] Add command-line argument documentation for streaming_example.py
     - [x] Include token tracking and cost calculation examples

2. **Update Token Usage Documentation**
   - [x] Document the TokenUsage class and to_dict() method (OpenAI provider)
   - [x] Document the CostEstimate class and to_dict() method (OpenAI provider)
   - [x] Add examples of token usage tracking across different providers (OpenAI example)
   - [x] Document cost estimation formatting for different magnitudes
   - [x] Add troubleshooting section for token tracking issues

3. **Update Streaming Documentation**
   - [x] Add multi-provider streaming examples
   - [x] Document the streaming_example.py command-line interface
   - [x] Add token tracking during streaming examples
   - [x] Update stream_with_callback documentation with latest patterns
   - [x] Document streaming error handling and recovery strategies

4. **Knowledge System Enhancement Documentation**
   - [x] Document adaptive document chunking strategies
     - [x] Add description of ChunkingStrategy pattern and implementations 
     - [x] Document specialized chunkers (MarkdownChunker, CodeChunker)
     - [x] Document chunking factory and document type detection
   - [x] Document content deduplication system
     - [x] Add description of normalized content hashing
     - [x] Document duplicate detection and reference tracking
     - [x] Add examples of deduplication configuration and usage
   - [x] Document embedding strategy system
     - [x] Add description of EmbeddingStrategy pattern and implementations
     - [x] Document provider-specific embeddings (Anthropic, ChromaDB)
     - [x] Add explanation of hybrid embedding strategies
   - [x] Document enhanced retrieval features
     - [x] Add description of RetrievalFilter and its composition methods
     - [x] Document RetrievalResult class and relevance scoring
     - [x] Document hybrid retrieval with semantic and keyword search
     - [x] Add examples of metadata-based filtering and faceted search

5. **Testing Documentation Updates**
   - [x] Document mock provider usage for testing without API keys
   - [x] Document token usage testing patterns and tools
   - [x] Add examples of testing streaming functionality
   - [x] Document the token_usage test module structure and usage
   - [x] Add troubleshooting guide for common testing issues

## New Documentation Tasks

1. **Caching System Documentation**
   - [ ] Create new file: `knowledge/caching.md`
     - [ ] Document QueryCache implementation and interface
     - [ ] Document caching strategies (TTL, LRU, size limits)
     - [ ] Explain cache invalidation mechanisms
     - [ ] Provide examples of cache configuration
   - [ ] Add caching section to `knowledge/retrieval.md`
     - [ ] Document how caching integrates with retrieval
     - [ ] Explain performance benefits with metrics
     - [ ] Show configuration options for caching
   - [ ] Create example documentation: `guides/examples/caching_example.py`
     - [ ] Demonstrate cache usage patterns
     - [ ] Show performance comparison with/without caching
     - [ ] Include cache hit/miss statistics

2. **Structured Message Format Documentation**
   - [ ] Create new file: `components/agents/messaging.md`
     - [ ] Document StructuredMessage class and interface
     - [ ] Explain message metadata and serialization
     - [ ] Show message routing and delivery patterns
     - [ ] Document integration with LangGraph workflows
   - [ ] Update `workflows/multi_agent.md`
     - [ ] Add section on message passing protocols
     - [ ] Document message handling between agents
     - [ ] Include diagram of message flow patterns

3. **Provider Optimization Documentation**
   - [ ] Create new file: `components/models/pooling.md`
     - [ ] Document ProviderPool implementation and interface
     - [ ] Explain connection management strategies
     - [ ] Detail resource optimization techniques
     - [ ] Show configuration options for different providers
   - [ ] Update provider-specific documentation
     - [ ] Add sections on performance optimization
     - [ ] Document provider-specific pooling considerations
     - [ ] Include configuration examples

## Key Implementation Accomplishments

### 1. Import System Optimization

We've successfully cleaned up the import structure throughout the codebase:

1. **Fixed Circular Import Warning**
   - Standardized imports of `DocumentProcessor` from `atlas.knowledge.ingest` at the module level
   - Updated import patterns in main.py, agent.py, and hybrid_retrieval_example.py
   - Eliminated runtime warnings about circular imports

2. **Consolidated Duplicate Implementations**
   - Removed duplicate `KnowledgeBase` implementation from tools/knowledge_retrieval.py
   - Ensured all code uses the more advanced implementation from knowledge/retrieval.py
   - Re-exported the `retrieve_knowledge` function through the tools module

3. **Enhanced Code Organization**
   - Used consistent import patterns across all modules
   - Ensured imports are at the module level rather than within functions where possible
   - Identified potential circular dependency between core.env and models.factory for future work

### 2. Enhanced Document ID Format

We've improved the document ID format in the knowledge ingestion system:

1. **Simplified Document IDs**
   - Changed from full relative paths (e.g., "path/to/some/deep/folder/file.md") to simplified format ("folder/file.md")
   - Added a new `simple_id` field to the `FileMetadata` class to store this simplified format
   - Updated `_create_chunk_id` method to use the simplified ID format when creating chunk IDs
   - Maintained backward compatibility by keeping the full path in the `source` field

2. **Improved Readability**
   - Document IDs are now more concise and easier to read
   - Chunk IDs follow the format "folder/file.md#chunk_index"
   - Easier to identify and debug documents in the knowledge base

3. **Added Unit Tests**
   - Created comprehensive tests to verify the new ID format works correctly
   - Tests for nested files and root-level files to ensure correct behavior in all cases

### 3. Enhanced Progress Indicators

We've significantly improved progress reporting during document ingestion:

1. **File Processing Progress**
   - Added a visual progress bar showing percentage completion
   - Shows current file being processed with counter (e.g., "file.md (1/54)")
   - Clear completion indicators with 100% marker

2. **Embedding Generation Progress**
   - Initial estimates for token count and processing time
   - Phase-based progress reporting (Preparing, Embedding, Storing)
   - Spinner animation with elapsed time display
   - Performance summary with timing and throughput metrics

3. **Overall Process Summary**
   - Comprehensive summary at the end of the ingestion process
   - Statistics on files processed, chunks created, etc.
   - Duplicate detection reporting
   - Collection size information

### 4. Enhanced Retrieval System

The knowledge system's hybrid retrieval capability is fully implemented with a consistent interface:

```python
# Example using RetrievalSettings
from atlas.knowledge.settings import RetrievalSettings

# Create retrieval settings with hybrid search enabled
settings = RetrievalSettings(
    use_hybrid_search=True,  # Enable hybrid search
    semantic_weight=0.7,     # 70% weight for semantic results
    keyword_weight=0.3,      # 30% weight for keyword results
    num_results=5,           # Return top 5 documents
    min_relevance_score=0.25 # Minimum relevance threshold
)

# Perform retrieval with settings
documents = kb.retrieve(
    query="knowledge graph structure",
    settings=settings,
    filter=RetrievalFilter.from_metadata(file_type="md")
)
```

## Next Steps

1. **Query Caching System**
   - Implement caching for frequently accessed queries
   - Add cache invalidation mechanisms
   - Create performance benchmarks to measure improvements

2. **Enhanced Message Passing**
   - Develop structured message format for agent communication
   - Implement message routing between specialized workers
   - Create coordination patterns for complex workflows

3. **Provider Optimization**
   - Implement connection pooling for model providers
   - Add health monitoring and diagnostics
   - Create automated fallback mechanisms

## Documentation Review Process

To maintain high-quality documentation, all documentation changes go through the following review process:

1. **Technical Accuracy Review**
   - Verification of technical content by subject matter experts
   - Validation of code examples and functionality descriptions
   - Confirmation of API references and parameter descriptions

2. **Usability and Clarity Review**
   - Assessment of readability and understandability
   - Evaluation of organization and structure
   - Review of examples for practicality and relevance

3. **Consistency and Standards Review**
   - Verification of adherence to documentation standards
   - Check for consistent terminology and formatting
   - Validation of proper cross-referencing and linking

4. **Final Integration Review**
   - Verification of proper placement within documentation structure
   - Check for seamless integration with existing content
   - Validation of navigation and discovery paths