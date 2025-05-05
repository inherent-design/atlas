# Atlas Project TODO

## At a Glance

**Completed:**
- ✅ Core infrastructure and testing framework
- ✅ Multi-provider model support with unified interfaces
- ✅ Environment management with centralized env.py module
- ✅ Telemetry with OpenTelemetry integration
- ✅ Knowledge retrieval and document processing

**Next Focus:**
- 🔄 Foundation: Complete provider module, unify agent implementations, create registry
- 📚 Knowledge: Enhance retrieval, optimize document processing, improve embeddings
- 🔀 Workflow: Implement graph edges, improve controller-worker communication

**Current Blockers:**
- Streaming implementation for model providers
- Unified agent implementation consolidation
- Agent registry for dynamic discovery

## MVP Implementation Strategy

The Atlas MVP follows a **Minimal Viable Pipeline** approach that creates a functioning end-to-end system with simplified implementations of all critical components. This ensures users can benefit from basic functionality across all key value areas before any single component is deeply optimized.

### Phase 1: Foundation Stabilization 🔄

**Critical Path [P0]:**
- [ ] Complete streaming implementation for Anthropic provider
- [ ] Implement basic API key validation mechanism
- [ ] Unify agent implementations (AtlasAgent and MultiProviderAgent)
- [ ] Create minimal agent registry with registration mechanism
- [ ] Enhance error handling across all core components

**Important [P1]:**
- [ ] Add missing unit tests for provider functionality
- [ ] Create simple mocked providers for testing
- [ ] Maintain backward compatibility for existing agent code
- [ ] Add basic telemetry throughout agent operations
- [ ] Implement simple factory methods for agent creation

**Nice to Have [P2]:**
- [ ] Add connection pooling for improved performance
- [ ] Create health checks for provider status
- [ ] Add dynamic provider switching capability
- [ ] Implement advanced agent class discovery
- [ ] Create comprehensive telemetry dashboard

### Phase 2: Knowledge Enhancements 📚

**Critical Path [P0]:**
- [ ] Verify and enhance document chunking strategies
- [ ] Improve metadata handling for documents
- [ ] Enhance retrieval with improved relevance scoring
- [ ] Add basic filtering capabilities for results

**Important [P1]:**
- [ ] Implement basic validation of ingested content
- [ ] Add better error handling for ingestion failures
- [ ] Create simple caching for frequent queries
- [ ] Add telemetry for knowledge operations
- [ ] Implement document versioning support

**Nice to Have [P2]:**
- [ ] Add support for multimedia document types
- [ ] Implement hierarchical document structures
- [ ] Create document relevance feedback system
- [ ] Add hybrid semantic-keyword search
- [ ] Implement faceted filtering options

### Phase 3: Workflow Improvements 🔀

**Critical Path [P0]:**
- [ ] Create basic Edge class with conditional routing
- [ ] Implement simple edge factories for common patterns
- [ ] Improve message passing between agents
- [ ] Add structured message formats with metadata

**Important [P1]:**
- [ ] Add validation for edge connections
- [ ] Create examples of useful workflow patterns
- [ ] Implement better error handling for communication
- [ ] Create simple coordination patterns
- [ ] Add logging for workflow execution

**Nice to Have [P2]:**
- [ ] Implement advanced branching logic for complex workflows
- [ ] Create visualization tools for workflows
- [ ] Add dynamic workflow creation capabilities
- [ ] Implement workflow versioning and history
- [ ] Create parallel execution optimization

## Acceleration Pathways

These pathways represent specialized areas of functionality that can be accelerated in parallel with the MVP approach, depending on specific user priorities and resource availability.

### Enhanced Knowledge Retrieval 🧠 [Accel]

- [ ] Implement advanced embedding with multi-provider support
- [ ] Create sophisticated chunking with overlap strategies
- [ ] Enhance retrieval with hybrid search (keywords + semantic)
- [ ] Add document metadata filtering and faceted search
- [ ] Implement caching layers for improved performance

### Multi-Agent Intelligence 🤖 [Accel]

- [ ] Build comprehensive agent registry with capability discovery
- [ ] Implement advanced workflow routing through graph edges
- [ ] Create specialized worker agents for different tasks
- [ ] Add dynamic agent allocation based on task requirements
- [ ] Implement feedback mechanisms between agents

### Provider Flexibility & Performance ⚡ [Accel]

- [ ] Complete full implementations for all providers (Anthropic, OpenAI, Ollama)
- [ ] Implement sophisticated streaming with token tracking
- [ ] Add connection pooling and performance optimizations
- [ ] Create provider switching based on cost/performance needs
- [ ] Implement fallback mechanisms between providers

## File Structure

### Target MVP Structure

```
atlas/
├── __init__.py                  ✅ DONE
├── main.py                      ✅ DONE  # Entry point with CLI interface
├── agents/                      ✅ DONE  # Agent implementations
│   ├── __init__.py             ✅ DONE
│   ├── base.py                 🚧 IN PROGRESS [P0]  # Unified agent base class
│   ├── controller.py           ✅ DONE  # Controller agent
│   ├── worker.py               ✅ DONE  # Worker agent
│   └── registry.py             ⏱️ PLANNED [P0]  # Agent registry with dynamic discovery
├── core/                        ✅ DONE  # Core functionality
│   ├── __init__.py             ✅ DONE
│   ├── config.py               ✅ DONE  # Configuration with provider support
│   ├── env.py                  ✅ DONE  # Environment variable management
│   ├── telemetry.py            ✅ DONE  # OpenTelemetry integration
│   └── prompts.py              ✅ DONE  # System prompts
├── graph/                       ✅ DONE  # LangGraph implementation
│   ├── __init__.py             ✅ DONE
│   ├── nodes.py                ✅ DONE  # Graph nodes
│   ├── edges.py                ⏱️ PLANNED [P0]  # Graph edges for routing
│   ├── state.py                ✅ DONE  # State management
│   └── workflows.py            ✅ DONE  # Workflow definitions
├── knowledge/                   ✅ DONE  # Knowledge management
│   ├── __init__.py             ✅ DONE
│   ├── ingest.py               ✅ DONE  # Document ingestion
│   ├── retrieval.py            ✅ DONE  # Knowledge retrieval
│   └── embedding.py            ⏱️ PLANNED [P1]  # Embedding functions
├── models/                      ✅ DONE  # Provider management (CONSOLIDATED)
│   ├── __init__.py             ✅ DONE  # Unified export interface
│   ├── base.py                 ✅ DONE  # Base provider interface
│   ├── factory.py              ✅ DONE  # Provider factory
│   ├── anthropic.py            🚧 IN PROGRESS [P0]  # Anthropic provider with streaming
│   ├── openai.py               🚧 IN PROGRESS [P1]  # OpenAI provider with streaming
│   ├── ollama.py               🚧 IN PROGRESS [P1]  # Ollama provider with streaming
│   └── mock.py                 ⏱️ PLANNED [P1]  # Mock provider for testing
├── orchestration/               ✅ DONE  # Agent orchestration
│   ├── __init__.py             ✅ DONE
│   ├── coordinator.py          ✅ DONE  # Agent coordination
│   ├── parallel.py             ✅ DONE  # Parallel processing
│   └── scheduler.py            ✅ DONE  # Task scheduling
├── scripts/                     ✅ DONE  # Utility scripts
│   ├── __init__.py             ✅ DONE
│   ├── debug/                  ✅ DONE  # Debugging utilities
│   │   ├── __init__.py         ✅ DONE
│   │   ├── check_db.py         ✅ DONE  # Database inspection
│   │   └── check_models.py     ✅ DONE  # Model provider testing
│   └── testing/                ✅ DONE  # Testing utilities
│       ├── __init__.py         ✅ DONE
│       └── run_tests.py        ✅ DONE  # Test runner
├── tests/                       ✅ DONE  # Test modules
│   ├── __init__.py             ✅ DONE
│   ├── helpers.py              ✅ DONE  # Test helper functions
│   ├── test_api.py             ✅ DONE  # Integration tests
│   ├── test_minimal.py         ✅ DONE  # Minimal verification tests
│   ├── test_mock.py            ✅ DONE  # Mock tests with no API calls
│   └── test_models.py          ✅ DONE  # Provider and models unit tests
└── tools/                       ✅ DONE  # Tool implementations
    ├── __init__.py             ✅ DONE
    └── knowledge_retrieval.py  ✅ DONE  # Knowledge retrieval tools
```

## Models Module Implementation Status

**Completed:**
- ✅ Base provider interface with standardized types
- ✅ Factory pattern with registration mechanism
- ✅ Provider auto-detection from environment
- ✅ Environment variable integration with env module
- ✅ Unit tests for provider functionality

**In Progress:**
- 🚧 Streaming implementation for providers
- 🚧 Enhanced API key validation
- 🚧 Comprehensive testing for all providers

**Planned:**
- ⏱️ Connection pooling for improved performance
- ⏱️ Provider health monitoring
- ⏱️ Advanced error handling with retries
- ⏱️ Cost optimization strategies

### Implementation Plan for Completion

1. **Complete Streaming Implementation**:
   - Finish implementation of streaming for Anthropic provider
   - Add robust error handling for streaming connections
   - Create comprehensive tests for streaming functionality

2. **Enhance Provider Testing**:
   - Create mocked provider implementations for testing
   - Implement comprehensive tests for all providers
   - Add tests for error conditions and edge cases

3. **Add Provider Optimizations**:
   - Implement connection pooling for performance
   - Add health checks for provider status
   - Create retry strategies for failed requests

## Completed Tasks Summary

Core infrastructure tasks completed:
- Created main.py entry point and established file structure
- Implemented LangGraph integration with controller-worker architecture
- Built comprehensive testing infrastructure with mock framework
- Added API cost tracking and telemetry with OpenTelemetry
- Implemented multi-provider support with unified interfaces
- Created centralized environment management with validation
- Standardized testing approach with comprehensive documentation

## Development Principles

1. **Clean Break Philosophy**: Prioritize building high-quality, robust APIs over maintaining backward compatibility with legacy code.
2. **Parallel Development**: Build new implementations alongside existing code until ready for complete cutover.
3. **Test-Driven Development**: Create comprehensive tests alongside or before implementation.
4. **Complete Documentation**: Provide thorough documentation for all new components with clear examples.
5. **Robust Error Handling**: Implement consistent, informative error handling throughout all components.
6. **Type Safety**: Use comprehensive type hints and validation for better code quality and reliability.
7. **Decisive Cutover**: Plan for complete transition to new implementations rather than maintaining dual systems.

See `docs/MVP_STRATEGY.md` for a detailed explanation of the MVP approach, implementation timelines, and prioritization framework.