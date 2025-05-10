# Proposed Atlas Project Structure

This document outlines the refined structure for the Atlas project, focusing on clean architecture, minimal dependencies, and clear component boundaries. This structure represents a clean-break approach that simplifies the codebase while ensuring all required functionality is maintained.

## Status Legend
- ✅ Existing and complete
- 🚧 Partially implemented or in progress
- 🔲 Planned but not yet implemented
- 🗑️ To be removed or refactored

## Implementation Priority Legend
- 🔴 Core MVP - Essential for core user/developer experience
- 🟠 Next Phase - Important for established product with users
- 🟢 Future - Enhances capabilities for mature product

## Core Directory Structure

```
atlas/
├── __init__.py                      ✅  🔴  Main entry point exports
├── agent.py                         ✅  🔴  Base agent functionality
├── agents/                          🚧  🔴  Agent system module
│   ├── __init__.py                  ✅  🔴  Module initialization
│   ├── registry.py                  ✅  🔴  Agent registry for dynamic discovery
│   ├── messaging.py                 ✅  🔴  Unified messaging system (consolidation)
│   ├── controller.py                🚧  🔴  Controller agent implementation (needs provider integration)
│   ├── worker.py                    🚧  🔴  Worker agent implementation (needs provider integration)
│   └── specialized/                 🚧  🔴  Specialized agent implementations
│       ├── __init__.py              ✅  🔴  Module initialization
│       ├── task_aware.py            ✅  🔴  Task-aware agent implementation
│       └── tool_agent.py            🚧  🔴  Tool-using agent implementation
├── cli/                             ✅  🔴  Command-line interface
│   ├── __init__.py                  ✅  🔴  Module initialization
│   ├── config.py                    ✅  🔴  CLI configuration utilities
│   └── parser.py                    ✅  🔴  Command-line argument parsing
├── core/                            ✅  🔴  Core utilities and configuration
│   ├── __init__.py                  ✅  🔴  Module initialization
│   ├── config.py                    ✅  🔴  Configuration management
│   ├── env.py                       ✅  🔴  Environment variable handling
│   ├── errors.py                    ✅  🔴  Error handling system
│   ├── logging.py                   ✅  🔴  Logging configuration
│   ├── prompts.py                   ✅  🔴  System prompt management
│   ├── retry.py                     ✅  🔴  Retry mechanisms
│   ├── telemetry.py                 ✅  🔴  Telemetry and metrics
│   └── caching/                     🔲  🟠  Response caching system
│       ├── __init__.py              🔲  🟠  Module initialization
│       ├── cache.py                 🔲  🟠  Abstract cache interface
│       ├── semantic_cache.py        🔲  🟠  Embedding-based similarity caching
│       └── policies.py              🔲  🟠  Cache policies (TTL, eviction)
├── graph/                           🚧  🔴  Workflow orchestration
│   ├── __init__.py                  ✅  🔴  Module initialization
│   ├── state.py                     🚧  🔴  State management
│   ├── edges.py                     ✅  🔴  Conditional edge routing
│   ├── nodes.py                     ✅  🔴  Functional node definitions
│   └── workflows.py                 🚧  🔴  Reusable workflow patterns
├── knowledge/                       🚧  🔴  Knowledge management system
│   ├── __init__.py                  ✅  🔴  Module initialization
│   ├── chunking.py                  🚧  🔴  Document chunking strategies
│   ├── embedding.py                 ✅  🔴  Embedding generation
│   ├── ingest.py                    ✅  🔴  Document ingestion
│   ├── retrieval.py                 🚧  🔴  Document retrieval interface
│   ├── hybrid_search.py             🔲  🔴  Hybrid semantic+keyword search
│   ├── reranking.py                 🔲  🟠  Result reranking strategies
│   ├── search_scoring.py            🔲  🟠  Configurable relevance scoring
│   └── settings.py                  ✅  🔴  Retrieval settings configuration
├── memory/                          🔲  🟠  Conversation memory system
│   ├── __init__.py                  🔲  🟠  Module initialization
│   ├── buffer.py                    🔲  🟠  Conversation buffer with windowing
│   ├── persistence.py               🔲  🟠  Long-term conversation storage
│   └── session.py                   🔲  🟠  Session management with resumption
├── providers/                       🚧  🔴  Model provider system
│   ├── __init__.py                  ✅  🔴  Module initialization and exports
│   ├── base.py                      🚧  🔴  Base provider with streaming interface (needs enhancement)
│   ├── factory.py                   ✅  🔴  Provider factory and instantiation
│   ├── options.py                   ✅  🔴  Provider options and configuration
│   ├── capabilities.py              ✅  🔴  Provider capability framework
│   ├── registry.py                  ✅  🔴  Provider registry with capability tracking
│   ├── group.py                     ✅  🔴  ProviderGroup with selection strategies
│   ├── resolver.py                  ✅  🔴  Provider resolution system
│   ├── rate_limiting/               🔲  🟠  Rate limiting infrastructure
│   │   ├── __init__.py              🔲  🟠  Module initialization
│   │   ├── limits.py                🔲  🟠  Rate limit definitions
│   │   ├── governor.py              🔲  🟠  Request throttling implementation
│   │   └── backpressure.py          🔲  🟠  Backpressure mechanisms
│   ├── anthropic.py                 ✅  🔴  Anthropic provider
│   ├── openai.py                    ✅  🔴  OpenAI provider
│   ├── ollama.py                    ✅  🔴  Ollama provider
│   └── mock.py                      ✅  🔴  Mock provider for testing
├── query.py                         ✅  🔴  Query client interface
├── reasoning/                       🔲  🟢  Structured reasoning frameworks
│   ├── __init__.py                  🔲  🟢  Module initialization
│   ├── chain_of_thought.py          🔲  🟢  Chain-of-thought implementation
│   ├── verification.py              🔲  🟢  Self-verification mechanisms
│   └── reflection.py                🔲  🟢  Self-critique and improvement
├── security/                        🔲  🟠  Security and safety framework
│   ├── __init__.py                  🔲  🟠  Module initialization
│   ├── content_filter.py            🔲  🟠  Input/output content filtering
│   ├── privacy.py                   🔲  🟠  PII detection and redaction
│   └── sanitization.py              🔲  🟠  Input sanitization for safety
├── tools/                           🚧  🔴  Tools system
│   ├── __init__.py                  ✅  🔴  Module initialization
│   ├── base.py                      🚧  🔴  Base tool interface
│   ├── registry.py                  🔲  🔴  Tool registry and discovery
│   ├── standard/                    🚧  🔴  Standard built-in tools
│   │   ├── __init__.py              ✅  🔴  Module initialization
│   │   ├── knowledge.py             🚧  🔴  Knowledge management tools
│   │   └── system.py                🔲  🔴  System interaction tools
│   └── mcp/                         🔲  🟠  MCP integration tools
│       └── __init__.py              ✅  🟠  Module initialization
└── scripts/                         ✅  🔴  Utility scripts
    ├── __init__.py                  ✅  🔴  Module initialization
    └── debug/                       ✅  🔴  Debugging utilities
        ├── __init__.py              ✅  🔴  Module initialization
        ├── check_config.py          ✅  🔴  Configuration checker
        ├── check_db.py              ✅  🔴  Database checker
        └── check_models.py          ✅  🔴  Model checker
```

## Documentation Structure

```
docs/
├── architecture/                    ✅  🔴  Architecture overview
│   ├── components.md                ✅  🔴  Component architecture
│   ├── data_flow.md                 ✅  🔴  Data flow diagrams
│   ├── design_principles.md         ✅  🔴  Core design principles
│   └── index.md                     ✅  🔴  Architecture introduction
├── components/                      ✅  🔴  Detailed component documentation
│   ├── agents/                      ✅  🔴  Agent system documentation
│   │   ├── index.md                 🔲  🔴  Agent system overview
│   │   ├── controller.md            ✅  🔴  Controller agent
│   │   ├── messaging.md             ✅  🔴  Messaging system
│   │   ├── workers.md               ✅  🔴  Worker agents
│   │   └── specialized.md           ✅  🔴  Specialized agents
│   ├── core/                        ✅  🔴  Core utilities documentation
│   │   ├── index.md                 🔲  🔴  Core utilities overview
│   │   ├── config.md                ✅  🔴  Configuration management
│   │   ├── env.md                   ✅  🔴  Environment variables
│   │   ├── errors.md                ✅  🔴  Error handling
│   │   ├── logging.md               ✅  🔴  Logging system
│   │   ├── prompts.md               ✅  🔴  System prompts
│   │   ├── telemetry.md             ✅  🔴  Telemetry system
│   │   └── caching.md               🔲  🟠  Caching system
│   ├── graph/                       ✅  🔴  Graph system documentation
│   │   ├── index.md                 ✅  🔴  Graph system overview
│   │   ├── edges.md                 ✅  🔴  Graph edges
│   │   ├── nodes.md                 ✅  🔴  Graph nodes
│   │   └── state.md                 ✅  🔴  State management
│   ├── knowledge/                   ✅  🔴  Knowledge system documentation
│   │   ├── index.md                 ✅  🔴  Knowledge system overview
│   │   ├── chunking.md              🔲  🔴  Document chunking
│   │   ├── hybrid_search.md         🔲  🔴  Hybrid search strategies
│   │   ├── ingestion.md             ✅  🔴  Document ingestion
│   │   └── retrieval.md             ✅  🔴  Document retrieval
│   ├── memory/                      🔲  🟠  Memory system documentation
│   │   ├── index.md                 🔲  🟠  Memory system overview
│   │   ├── buffer.md                🔲  🟠  Conversation buffers
│   │   ├── persistence.md           🔲  🟠  Long-term storage
│   │   └── session.md               🔲  🟠  Session management
│   ├── providers/                   ✅  🔴  Provider system documentation
│   │   ├── index.md                 ✅  🔴  Provider system overview
│   │   ├── anthropic.md             ✅  🔴  Anthropic provider
│   │   ├── capabilities.md          ✅  🔴  Provider capabilities
│   │   ├── mock.md                  ✅  🔴  Mock provider
│   │   ├── ollama.md                ✅  🔴  Ollama provider
│   │   ├── openai.md                ✅  🔴  OpenAI provider
│   │   ├── provider_group.md        ✅  🔴  Provider group
│   │   ├── provider_selection.md    ✅  🔴  Provider selection
│   │   ├── rate_limiting.md         🔲  🟠  Rate limiting system
│   │   └── registry.md              ✅  🔴  Provider registry
│   ├── reasoning/                   🔲  🟢  Reasoning framework documentation
│   │   ├── index.md                 🔲  🟢  Reasoning system overview
│   │   ├── chain_of_thought.md      🔲  🟢  Chain-of-thought patterns
│   │   └── verification.md          🔲  🟢  Self-verification strategies
│   ├── security/                    🔲  🟠  Security framework documentation
│   │   ├── index.md                 🔲  🟠  Security system overview
│   │   ├── content_filtering.md     🔲  🟠  Content filtering guide
│   │   └── privacy.md               🔲  🟠  Privacy protection strategies
│   └── tools/                       ✅  🔴  Tool system documentation
│       ├── index.md                 ✅  🔴  Tool system overview
│       ├── core.md                  ✅  🔴  Core tool interfaces
│       ├── mcp.md                   ✅  🟠  MCP integration
│       └── standard.md              ✅  🔴  Standard tools
├── guides/                          ✅  🔴  User guides
│   ├── getting_started.md           ✅  🔴  Getting started guide
│   ├── configuration.md             ✅  🔴  Configuration guide
│   ├── testing.md                   ✅  🔴  Testing guide
│   ├── type_checking.md             ✅  🔴  Type checking guide
│   ├── hybrid_search.md             🔲  🔴  Hybrid search implementation guide
│   ├── caching.md                   🔲  🟠  Caching guide
│   ├── memory.md                    🔲  🟠  Memory management guide
│   ├── security.md                  🔲  🟠  Security best practices
│   └── rate_limiting.md             🔲  🟠  Rate limiting configuration
├── project-management/              ✅  🔴  Project management documentation
│   ├── index.md                     ✅  🔴  Project management overview
│   ├── audit/                       ✅  🔴  Audit reports and analysis
│   │   ├── implementation_audit.md  🔲  🔴  Implementation status audit
│   │   └── archive/                 ✅  🔴  Historical audit documents
│   │       ├── agent_system_update.md      ✅  🔴  Agent system audit
│   │       ├── doc_audit.md                ✅  🔴  Documentation audit
│   │       └── enhanced_provider_alignment.md ✅  🔴  Provider system audit
│   ├── business/                    ✅  🔴  Business planning and strategy
│   │   ├── commercialization_timeline.md ✅  🔴  Post-development commercialization plan
│   │   └── monetization_strategy.md ✅  🔴  Monetization approaches
│   ├── legal/                       ✅  🔴  Legal considerations
│   │   ├── compliance_roadmap.md    ✅  🔴  Compliance implementation timeline
│   │   └── license_selection.md     ✅  🔴  License selection rationale
│   ├── marketing/                   ✅  🔴  Marketing materials
│   │   ├── go_to_market_strategy.md ✅  🔴  Comprehensive go-to-market plan
│   │   ├── pitch_deck_outline.md    ✅  🔴  Pitch deck structure
│   │   ├── press_release_template.md ✅  🔴  Press release template
│   │   └── project_overview.md      ✅  🔴  Project overview for audiences
│   ├── planning/                    ✅  🔴  Planning documents
│   │   ├── accelerated_implementation_plan.md ✅  🔴  Accelerated execution plan
│   │   ├── architecture_planning.md ✅  🔴  Architecture design planning
│   │   ├── archive/                 ✅  🔴  Archived planning documents
│   │   │   ├── index.md             ✅  🔴  Archive documentation
│   │   │   ├── cli_planning_2025-05-10.md        ✅  🔴  CLI interface planning (archived)
│   │   │   ├── implementation_planning_2025-05-10.md ✅  🔴  Implementation strategy (archived)
│   │   │   └── mvp_completion_strategy_2025-05-10.md ✅  🔴  MVP roadmap (archived)
│   │   └── possible-future/         ✅  🟢  Future planning documents
│   │       ├── future_multi_modal_possibilities.md ✅  🟢  Multi-modal support
│   │       ├── hybrid_retrieval_strategies.md ✅  🟢  Advanced retrieval
│   │       ├── open_source_strategy.md ✅  🟢  Open source approach
│   │       └── test_suite_planning.md ✅  🟢  Test suite planning
│   ├── roadmap/                     ✅  🔴  Product roadmap
│   │   ├── product_roadmap.md       ✅  🔴  Comprehensive product roadmap
│   │   └── archive/                 ✅  🔴  Archived roadmap documents
│   │       ├── index.md             ✅  🔴  Archive documentation
│   │       └── mvp_strategy_2025-05-10.md  ✅  🔴  MVP strategy (archived)
│   └── tracking/                    ✅  🔴  Implementation tracking
│       ├── proposed_structure.md    ✅  🔴  Proposed code structure
│       ├── todo.md                  ✅  🔴  Current implementation tasks
│       └── archive/                 ✅  🔴  Historical tracking documents
│           └── enhanced_provider_todo.md ✅  🔴  Provider system tasks
├── reference/                       ✅  🔴  Reference documentation
│   ├── api.md                       ✅  🔴  API reference
│   ├── cli.md                       ✅  🔴  CLI options reference
│   ├── env_variables.md             ✅  🔴  Environment variables reference
│   ├── faq.md                       ✅  🔴  Frequently asked questions
│   └── licensing.md                 ✅  🔴  Licensing information
└── workflows/                       ✅  🔴  Workflow documentation
    ├── query.md                     ✅  🔴  Basic query workflow
    ├── retrieval.md                 ✅  🔴  Retrieval workflow
    ├── conversational.md            🔲  🟠  Conversational workflows
    ├── multi_agent.md               ✅  🔴  Multi-agent workflow
    └── custom_workflows.md          ✅  🔴  Custom workflow guide
```

## Example Structure

```
examples/
├── 01_query_simple.py               ✅  🔴  Basic query
├── 02_query_streaming.py            ✅  🔴  Streaming query
├── 03_provider_selection.py         ✅  🔴  Provider selection and options
├── 04_provider_group.py             ✅  🔴  Provider group with fallback
├── 05_task_aware_providers.py       ✅  🔴  Task-aware provider selection
├── 06_task_aware_agent.py           ✅  🔴  Task-aware agent implementation
├── 10_document_ingestion.py         ✅  🔴  Document ingestion
├── 11_basic_retrieval.py            ✅  🔴  Basic retrieval
├── 12_hybrid_retrieval.py           🚧  🔴  Hybrid retrieval
├── 15_advanced_filtering.py         ✅  🔴  Advanced metadata and content filtering
├── 20_tool_agent.py                 🚧  🔴  Tool agent usage
├── 21_multi_agent.py                🚧  🔴  Multi-agent system
├── 22_agent_workflows.py            🚧  🔴  Agent workflows
├── 30_memory_conversation.py        🔲  🟠  Memory-enabled conversations
├── 31_caching_example.py            🔲  🟠  Response caching demonstration
├── 32_rate_limiting.py              🔲  🟠  Rate limiting configuration
├── 33_security_filtering.py         🔲  🟠  Content filtering and security
├── 40_chain_of_thought.py           🔲  🟢  Chain-of-thought reasoning
├── 41_self_verification.py          🔲  🟢  Self-verification techniques
├── common.py                        ✅  🔴  Shared utilities for examples
├── EXAMPLES.md                      ✅  🔴  Example implementation standards
└── README.md                        ✅  🔴  Examples guide
```

## Key Simplifications and Enhancements

### 1. Core Functionality (MVP) 🔴

#### Provider System Completion
- Standardized provider interface with comprehensive streaming controls (current focus)
- Robust ProviderGroup with enhanced fallback mechanisms (current focus)
- Capability-based provider selection (completed)
- Error handling and lifecycle management improvements (current focus)

#### Knowledge System Enhancement
- Hybrid retrieval combining semantic and keyword search
- Improved chunking strategies for better document understanding
- Streamlined retrieval interface with unified search approach

#### Agent System Refinement
- Consolidated messaging system into a single file (completed)
- Clear base class responsibilities (completed)
- Specialized agent implementations (TaskAwareAgent completed, others in progress)
- Enhanced provider integration in agent system (current focus)
- Streaming control propagation to agents (current focus)

#### Tools System Implementation
- Simplified tool interface with validation
- Focused on essential tool categories
- Clear tool registry architecture

#### Graph System Refinement
- Enhanced state management for workflows
- Reusable workflow patterns
- Clean interfaces for new workflows

### 2. Next-Phase Improvements 🟠

#### Memory and Session Management
- Conversation buffer with windowing strategies
- Long-term conversation storage and retrieval
- Session management with resumption capabilities

#### Advanced Caching System
- Abstract cache interface with multiple backends
- Semantic similarity caching for non-exact matches
- Configurable policies for cache management

#### Rate Limiting Infrastructure
- Provider-specific rate limit definitions
- Request throttling and queueing implementation
- Backpressure mechanisms for overload situations

#### Security Framework
- Content filtering for inputs and outputs
- PII detection and redaction capabilities
- Input sanitization to prevent prompt injection

#### Enhanced Observability
- Detailed metrics collection across components
- Distributed tracing for complex operations
- Cost tracking and optimization features

### 3. Future Capabilities 🟢

#### Structured Reasoning Framework
- Chain-of-thought prompting implementation
- Self-verification mechanisms
- Self-critique and reflection capabilities

#### Advanced Knowledge Capabilities
- Sophisticated reranking strategies
- Multiple scoring algorithms for relevance
- Knowledge graph integration

#### Multi-Modal Support
- Image handling and embedding
- Audio processing capabilities
- Multi-modal prompt construction

#### Evaluation Framework
- Quality metrics for responses
- Automatic evaluations against benchmarks
- Feedback collection and processing

## Implementation Priorities

### Phase 1: Core MVP 🔴

#### 1. Streaming Infrastructure Enhancement (Current Sprint Focus)
- Update provider base class with standardized streaming interface
- Add stream control capabilities (pause, resume, cancel)
- Implement buffering mechanisms for stream manipulation
- Add performance metrics tracking during streaming
- Implement proper resource cleanup for all streams
- Ensure consistent error handling across streaming operations
- Enhance ProviderGroup streaming with fallback mechanisms

#### 2. Knowledge System Enhancements
- Implement hybrid retrieval combining semantic and keyword search
- Enhance chunking strategies for different document types
- Develop reusable search patterns across different retrieval approaches
- Implement configurable search interfaces

#### 3. Tool System Development
- Implement base Tool interface with validation
- Create tool registry for discovery and management
- Develop core set of knowledge and system tools
- Establish clear extension points for custom tools

#### 4. Agent System Refinements (Current Sprint Focus)
- Update agents to work with enhanced streaming providers
- Improve controller-worker communication with streaming controls
- Add provider capability awareness to agent implementations
- Create clean agent-provider interface protocol
- Implement provider performance tracking in agents

#### 5. Example Development (Current Sprint Focus)
- Create enhanced streaming example with controls
- Update multi-agent examples with provider groups
- Demonstrate provider fallback during streaming
- Illustrate provider capability utilization
- Ensure consistent error handling in examples

### Phase 2: Next Immediate Improvements 🟠

#### 1. Memory System Implementation
- Create conversation buffer with windowing strategies
- Implement persistent conversation storage
- Develop session management with resumption capabilities
- Integrate with existing agent architecture

#### 2. Caching Infrastructure
- Implement abstract cache interface
- Develop semantic similarity caching for non-exact matches
- Create configurable policies for TTL and eviction
- Integration with knowledge retrieval and providers

#### 3. Rate Limiting System
- Implement provider-specific rate limit definitions
- Develop request throttling and queueing system
- Create backpressure mechanisms for overload protection
- Integrate with provider selection strategies

#### 4. Security Framework
- Implement content filtering for inputs and outputs
- Develop PII detection and redaction capabilities
- Create input sanitization to prevent prompt injection
- Add configuration for security policy settings

#### 5. Enhanced Observability
- Expand telemetry to include detailed metrics
- Implement distributed tracing across components
- Add token usage and cost tracking features
- Develop performance monitoring and alerting

### Phase 3: Future Capabilities 🟢

#### 1. Structured Reasoning
- Implement chain-of-thought prompting patterns
- Develop self-verification mechanisms
- Create self-critique and reflection capabilities
- Integration with knowledge and agent systems

#### 2. Advanced Knowledge Capabilities
- Implement sophisticated reranking strategies
- Develop multiple scoring algorithms for relevance
- Create knowledge graph integration capabilities
- Support for diverse knowledge representation formats

#### 3. Multi-Modal Support
- Implement image handling and embedding
- Develop audio processing capabilities
- Create multi-modal prompt construction
- Integration with providers supporting multi-modal inputs

#### 4. Evaluation Framework
- Develop quality metrics for response evaluation
- Implement automatic benchmarking against standards
- Create feedback collection and processing system
- Integrate with existing components for continuous improvement

This enhanced structure maintains all essential MVP functionality while adding clear pathways for future development. The prioritization ensures that the core user experience is robust and complete before adding advanced capabilities. The implementation strategy allows for incremental adoption of new features while maintaining backward compatibility.