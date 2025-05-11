# Proposed Project Structure

This document outlines the refined structure for the Atlas project, focusing on clean architecture, minimal dependencies, and clear component boundaries. This structure represents a clean-break approach that simplifies the codebase while ensuring all required functionality is maintained.

::: tip Core Principles
Atlas follows a **clean break philosophy** with a focus on best-in-class API design over backward compatibility. This structure prioritizes modularity, clear interfaces, and maintainable code.
:::

::: warning Current Focus (May 10-17, 2025)
We are currently focused on **Provider System Finalization** with enhanced streaming capabilities, provider lifecycle management, and robust error handling. See the [current TODO list](./todo.md) for specific implementation tasks.
:::

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
│   ├── services/                    🔲  🔴  Service architecture components
│   │   ├── __init__.py              🔲  🔴  Module initialization
│   │   ├── base.py                  🔲  🔴  Base service interfaces
│   │   ├── buffer.py                🔲  🔴  Thread-safe buffer implementations
│   │   ├── state.py                 🔲  🔴  State management utilities
│   │   ├── commands.py              🔲  🔴  Command pattern implementation
│   │   ├── concurrency.py           🔲  🔴  Thread safety utilities
│   │   └── resources.py             🔲  🔴  Resource lifecycle management
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
│   ├── base.py                      ✅  🔴  Core provider interface only
│   ├── messages.py                  ✅  🔴  Message and request modeling
│   ├── errors.py                    ✅  🔴  Provider-specific error classes
│   ├── reliability.py               ✅  🔴  Retry and circuit breaker
│   ├── streaming/                   ✅  🔴  Enhanced streaming infrastructure
│   │   ├── __init__.py              ✅  🔴  Module initialization
│   │   ├── base.py                  ✅  🔴  Base streaming interfaces
│   │   ├── control.py               ✅  🔴  Stream control implementation
│   │   └── buffer.py                ✅  🔴  Stream buffer management
│   ├── implementations/             🚧  🔴  Provider implementations
│   │   ├── __init__.py              ✅  🔴  Module initialization
│   │   ├── anthropic.py             ✅  🔴  Anthropic provider
│   │   ├── openai.py                🔲  🔴  OpenAI provider
│   │   ├── ollama.py                🔲  🔴  Ollama provider
│   │   └── mock.py                  ✅  🔴  Mock provider for testing
│   ├── group.py                     ✅  🔴  Provider group implementation
│   ├── registry.py                  ✅  🔴  Provider registry
│   ├── factory.py                   ✅  🔴  Provider factory
│   ├── resolver.py                  ✅  🔴  Provider auto-resolution
│   ├── capabilities.py              ✅  🔴  Provider capabilities
│   ├── options.py                   ✅  🔴  Provider options and configuration
│   ├── anthropic.py                 🗑️  🔴  Legacy Anthropic provider (moved to implementations)
│   ├── openai.py                    🗑️  🔴  Legacy OpenAI provider (to be moved)
│   ├── ollama.py                    🗑️  🔴  Legacy Ollama provider (to be moved)
│   └── mock.py                      🗑️  🔴  Legacy Mock provider (moved to implementations)
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
│   │   ├── implementations/         🔲  🔴  Provider implementations documentation
│   │   │   ├── anthropic.md         ✅  🔴  Anthropic provider
│   │   │   ├── openai.md            ✅  🔴  OpenAI provider
│   │   │   ├── ollama.md            ✅  🔴  Ollama provider
│   │   │   └── mock.md              ✅  🔴  Mock provider
│   │   ├── streaming/               🚧  🔴  Streaming documentation
│   │   │   ├── index.md             🔲  🔴  Streaming overview
│   │   │   ├── control.md           🔲  🔴  Stream control interface
│   │   │   └── buffer.md            🔲  🔴  Stream buffering
│   │   ├── capabilities.md          ✅  🔴  Provider capabilities
│   │   ├── group.md                 ✅  🔴  Provider group implementation
│   │   ├── messages.md              ✅  🔴  Message and request modeling
│   │   ├── errors.md                ✅  🔴  Error handling and categorization
│   │   ├── reliability.md           ✅  🔴  Retry and circuit breaker patterns
│   │   ├── selection.md             ✅  🔴  Provider selection strategies
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
├── contributing/                    🚧  🔴  Contribution guides and standards
│   ├── index.md                     🔲  🔴  Overview of contribution process
│   ├── documentation-standards.md   🔲  🔴  Documentation writing guidelines
│   ├── content-containers.md        🔲  🔴  Custom container usage guide
│   ├── timelines.md                 🔲  🔴  Timeline component usage guide
│   ├── code-examples.md             🔲  🔴  Standards for code examples
│   └── style-guide.md               🔲  🔴  Writing style and terminology standards
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
│   │       ├── agent_system_update_2025-05-09.md   ✅  🔴  Agent system audit
│   │       ├── doc_audit_2025-05-09.md             ✅  🔴  Documentation audit
│   │       └── enhanced_provider_alignment_2025-05-09.md ✅  🔴  Provider system audit
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
│           └── enhanced_provider_todo_2025-05-10.md ✅  🔴  Provider system tasks
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

### Core Functionality (MVP) 🔴

#### 1. Provider System Completion
- Standardized provider interface with comprehensive streaming controls (current focus)
- Robust ProviderGroup with enhanced fallback mechanisms (current focus)
- Capability-based provider selection (completed)
- Error handling and lifecycle management improvements (current focus)

#### 2. Knowledge System Enhancement
- Hybrid retrieval combining semantic and keyword search
- Improved chunking strategies for better document understanding
- Streamlined retrieval interface with unified search approach

#### 3. Agent System Refinement
- Consolidated messaging system into a single file (completed)
- Clear base class responsibilities (completed)
- Specialized agent implementations (TaskAwareAgent completed, others in progress)
- Enhanced provider integration in agent system (current focus)
- Streaming control propagation to agents (current focus)

#### 4. Tools System Implementation
- Simplified tool interface with validation
- Focused on essential tool categories
- Clear tool registry architecture

#### 5. Graph System Refinement
- Enhanced state management for workflows
- Reusable workflow patterns
- Clean interfaces for new workflows

### Next-Phase Improvements 🟠

#### 1. Memory and Session Management
- Conversation buffer with windowing strategies
- Long-term conversation storage and retrieval
- Session management with resumption capabilities

#### 2. Advanced Caching System
- Abstract cache interface with multiple backends
- Semantic similarity caching for non-exact matches
- Configurable policies for cache management

#### 3. Rate Limiting Infrastructure
- Provider-specific rate limit definitions
- Request throttling and queueing implementation
- Backpressure mechanisms for overload situations

#### 4. Security Framework
- Content filtering for inputs and outputs
- PII detection and redaction capabilities
- Input sanitization to prevent prompt injection

#### 5. Enhanced Observability
- Detailed metrics collection across components
- Distributed tracing for complex operations
- Cost tracking and optimization features

### Future Capabilities 🟢

#### 1. Structured Reasoning Framework
- Chain-of-thought prompting implementation
- Self-verification mechanisms
- Self-critique and reflection capabilities

#### 2. Advanced Knowledge Capabilities
- Sophisticated reranking strategies
- Multiple scoring algorithms for relevance
- Knowledge graph integration

#### 3. Multi-Modal Support
- Image handling and embedding
- Audio processing capabilities
- Multi-modal prompt construction

#### 4. Evaluation Framework
- Quality metrics for responses
- Automatic evaluations against benchmarks
- Feedback collection and processing

## Implementation Roadmap

::: timeline Provider System Finalization
- **May 10-17, 2025**
- Enhanced streaming with controls
- Provider lifecycle management
- Improved fallback mechanisms
:::

::: timeline Agent-Provider Integration
- **May 18-24, 2025**
- Agent streaming controls
- Provider capability utilization
- Controller-worker improvements
:::

::: timeline Knowledge System Enhancements
- **May 25-31, 2025**
- Hybrid retrieval implementation
- Advanced metadata extraction
- Document-specific chunkers
:::

::: timeline Multi-Agent Orchestration
- **June 1-7, 2025**
- Specialized worker agents
- Coordination patterns
- Parallel processing
:::

::: timeline Enterprise Features
- **June 8-14, 2025**
- Security and access control
- Compliance tools
- Advanced monitoring
:::

::: timeline Cloud Service Foundations
- **June 15-22, 2025**
- Multi-tenant architecture
- Usage tracking and metering
- Self-service capabilities
:::

::: timeline Finalization & Documentation
- **June 23-30, 2025**
- Bug fixes and stabilization
- Complete documentation
- Final examples and testing
:::

::: warning Backward Compatibility
Remember that Atlas follows a **clean break philosophy** - we prioritize best-in-class API design over backward compatibility. When implementing new features, focus on creating the best possible developer experience rather than maintaining compatibility with earlier design decisions.
:::

## Key Files for Current Sprint

| Component                    | Key Files                                                                                | Priority | Owner         |
| ---------------------------- | ---------------------------------------------------------------------------------------- | -------- | ------------- |
| **Provider Streaming**       | `atlas/providers/base.py`, `atlas/providers/group.py`                                    | Critical | Provider Team |
| **Provider Implementations** | `atlas/providers/anthropic.py`, `atlas/providers/openai.py`, `atlas/providers/ollama.py` | High     | Provider Team |
| **Agent Integration**        | `atlas/agents/controller.py`, `atlas/agents/worker.py`                                   | High     | Agent Team    |
| **Specialized Agents**       | `atlas/agents/specialized/tool_agent.py`, `atlas/agents/specialized/task_aware_agent.py` | Medium   | Agent Team    |
| **Examples**                 | `examples/07_enhanced_streaming.py`, `examples/08_multi_agent_providers.py`              | Medium   | Examples Team |

## Resource Allocation

- **Primary Focus**: Provider system enhancements with streaming controls
- **Secondary Focus**: Agent-provider integration optimization
- **On Hold**: Knowledge system, tool system implementation
- **Team Distribution**: See the [Accelerated Implementation Plan](../planning/accelerated_implementation_plan.md) for detailed team allocations
