# Proposed Final Project Structure

This document outlines the proposed final structure for the Atlas project after completing all tasks in the implementation plan. The structure represents the target state of the codebase once all planned features are implemented.

## Status Legend
- ✅ Existing and complete
- 🚧 Partially implemented or in progress
- 🔲 Planned but not yet implemented
- 🗑️ To be removed or refactored

## Core Directory Structure

```
atlas/
├── __init__.py                         ✅ Main entry point exports
├── agent.py                            ✅ Base agent functionality
├── agents/                             🚧 Agent system module (needs update)
│   ├── __init__.py                     ✅ Module initialization
│   ├── base.py                         🚧 Base agent (needs provider options update)
│   ├── controller.py                   🚧 Controller agent implementation
│   ├── messaging/                      ✅ Agent messaging system
│   │   ├── __init__.py                 ✅ Module initialization  
│   │   └── message.py                  ✅ Message object definitions
│   ├── registry.py                     ✅ Agent registry for dynamic discovery
│   ├── specialized/                    🚧 Specialized agent implementations
│   │   ├── __init__.py                 ✅ Module initialization
│   │   └── tool_agent.py               🚧 Tool-using agent implementation
│   └── worker.py                       🚧 Worker agent implementation
├── cli/                                ✅ Command-line interface
│   ├── __init__.py                     ✅ Module initialization
│   ├── config.py                       ✅ CLI configuration utilities
│   └── parser.py                       ✅ Command-line argument parsing
├── core/                               ✅ Core utilities and configuration
│   ├── __init__.py                     ✅ Module initialization
│   ├── config.py                       ✅ Configuration management
│   ├── env.py                          ✅ Environment variable handling
│   ├── errors.py                       ✅ Error handling system
│   ├── logging.py                      ✅ Logging configuration
│   ├── prompts.py                      ✅ System prompt management
│   ├── retry.py                        ✅ Retry mechanisms
│   └── telemetry.py                    ✅ Telemetry and metrics
├── graph/                              🚧 LangGraph integration
│   ├── __init__.py                     ✅ Module initialization
│   ├── edges.py                        ✅ Graph edge definitions
│   ├── nodes.py                        ✅ Graph node definitions
│   ├── state.py                        🚧 State management (needs updates)
│   └── workflows.py                    🚧 Workflow definitions (needs updates)
├── knowledge/                          🚧 Knowledge management system
│   ├── __init__.py                     ✅ Module initialization
│   ├── chunking.py                     🚧 Document chunking strategies (needs enhancement)
│   ├── embedding.py                    ✅ Embedding generation
│   ├── ingest.py                       ✅ Document ingestion
│   ├── retrieval.py                    ✅ Document retrieval with advanced filtering
│   └── settings.py                     ✅ Retrieval settings
├── orchestration/                      🔲 Agent orchestration (mostly planned)
│   ├── __init__.py                     ✅ Module initialization
│   ├── coordinator.py                  🚧 Multi-agent coordination
│   ├── messaging/                      🔲 Inter-agent messaging protocols
│   │   └── __init__.py                 ✅ Module initialization
│   ├── parallel.py                     🔲 Parallel processing utilities
│   ├── scheduler.py                    🔲 Task scheduling system
│   └── workflow/                       🔲 Workflow definitions
│       └── __init__.py                 ✅ Module initialization
├── providers/                          🚧 Model provider system
│   ├── __init__.py                     ✅ Module initialization and exports
│   ├── anthropic.py                    ✅ Anthropic provider
│   ├── base.py                         ✅ Base provider interface
│   ├── capabilities.py                 🔲 Enhanced capability system (to be added)
│   ├── factory.py                      ✅ Provider factory
│   ├── group.py                        🔲 ProviderGroup implementation (to be added)
│   ├── mock.py                         ✅ Mock provider for testing
│   ├── ollama.py                       ✅ Ollama provider
│   ├── openai.py                       ✅ OpenAI provider
│   ├── options.py                      ✅ Provider options data class
│   ├── registry.py                     🔲 Provider registry with capability tracking (to be added)
│   └── resolver.py                     ✅ Provider resolution system
├── query.py                            ✅ Query client interface with metadata filtering
├── scripts/                            ✅ Utility scripts
│   ├── __init__.py                     ✅ Module initialization
│   └── debug/                          ✅ Debugging utilities
│       ├── __init__.py                 ✅ Module initialization
│       ├── check_config.py             ✅ Configuration checker
│       ├── check_db.py                 ✅ Database checker
│       └── check_models.py             ✅ Model checker
└── tools/                              🔲 Tools system (mostly planned)
    ├── __init__.py                     ✅ Module initialization
    ├── base.py                         🔲 Base tool interface (to be implemented)
    ├── discovery.py                    🔲 Tool discovery (to be added)
    ├── mcp/                            🔲 MCP tools (planned)
    │   └── __init__.py                 ✅ Module initialization
    ├── registry.py                     🔲 Tool registry (to be added)
    └── standard/                       🔲 Standard tools (mostly planned)
        ├── __init__.py                 ✅ Module initialization
        ├── knowledge_tools.py          🚧 Knowledge tools
        ├── system_tools.py             🔲 System tools (to be added)
        └── web_tools.py                🔲 Web tools (to be added)
```

## New Files to be Created

1. **providers/group.py**
   - Implements ProviderGroup for aggregation and fallback between providers
   - Supports multiple provider selection strategies:
     - Failover: Try providers in sequence until one works
     - Round-robin: Rotate through available providers
     - Cost-optimized: Select providers based on estimated cost
   - Includes provider health monitoring and automatic recovery
   - Implements provider capability detection across multiple providers
   - Provides seamless integration with existing provider interface
   - Supports automatic retry with different providers when one fails

2. **tools/base.py**
   - Defines the base Tool class with standardized interface
   - Includes schema validation for tool inputs/outputs
   - Implements error handling and reporting

3. **tools/registry.py**
   - Implements dynamic tool discovery and registration
   - Supports loading tools from multiple locations
   - Handles tool versioning and compatibility

4. **tools/discovery.py**
   - Provides utilities for discovering and loading tools
   - Implements tool capability interfaces
   - Manages tool metadata

5. **orchestration/messaging/protocol.py**
   - Defines standardized messaging protocols between agents
   - Implements message serialization and deserialization
   - Supports different message types and priorities

6. **orchestration/workflow/executor.py**
   - Implements workflow execution engine
   - Manages workflow state transitions
   - Handles error recovery in workflows

## Files Needing Significant Updates

1. **agents/base.py**
   - Update to work with provider options
   - Support integration with the tool system
   - Implement more robust error handling

2. **providers/base.py**
   - Standardize streaming interfaces
   - Add stream control capabilities
   - Implement proper resource cleanup

3. **knowledge/retrieval.py**
   - Implement hybrid retrieval system
   - Improve relevance scoring algorithms
   - Add caching for performance optimization

4. **knowledge/chunking.py**
   - Implement enhanced chunking strategies
   - Add semantic-aware chunking
   - Improve overlap control and configuration

5. **graph/workflows.py**
   - Update to work with new agent system
   - Support multi-agent workflows
   - Integrate with tool discovery

## Target State for Examples

The examples directory will be organized to demonstrate progressive complexity and feature usage:

```
examples/
├── 01_query_simple.py                  ✅ Basic query
├── 02_query_streaming.py               ✅ Streaming query
├── 03_provider_selection.py            ✅ Provider selection and options
├── 04_provider_group.py                🔲 Provider group with fallback (to be added)
├── 05_task_aware_providers.py          🔲 Task-aware provider selection (to be added)
├── 06_agent_options_verification.py    ✅ Agent initialization with provider options
├── 10_document_ingestion.py            ✅ Document ingestion
├── 11_basic_retrieval.py               ✅ Basic retrieval
├── 15_advanced_filtering.py            ✅ Advanced metadata and content filtering
├── 12_hybrid_retrieval.py.todo         🚧 Hybrid retrieval (planned)
├── 20_tool_agent.py.todo               🚧 Tool agent (planned)
├── 21_multi_agent.py.todo              🚧 Multi-agent system (planned)
├── 22_agent_workflows.py.todo          🚧 Agent workflows (planned)
├── common.py                           ✅ Shared utilities for examples
├── EXAMPLES.md                         ✅ Example implementation standards
└── README.md                           ✅ Examples guide with implementation status
```

## Implementation Priority

The implementation priority follows the phased approach outlined in the todo.md document:

1. **Phase 1: Implement ProviderGroup**
   - Create ProviderGroup class implementing BaseProvider interface
   - Implement provider selection strategies (failover, round-robin, cost-based)
   - Add provider health monitoring and recovery
   - Update AtlasAgent to work with provider instances
   - Add CLI and configuration support for provider groups
   - Create examples demonstrating provider groups

2. **Phase 2: Streamline Streaming Architecture**
   - Create unified StreamResponse model
   - Standardize stream handlers across providers
   - Implement proper resource cleanup for all streams
   - Add stream control capabilities

3. **Phase 3: Enhance Agent System with Tools**
   - Update AtlasAgent to work with provider options
   - Create simplified tool interface
   - Define tool discovery and capability interfaces
   - Implement standardized tool invocation patterns

4. **Phase 4: Implement Hybrid Retrieval**
   - Implement combined keyword + semantic search
   - Add relevance scoring mechanism
   - Create configurable weighting system
   - Add example demonstrating hybrid search

5. **Phase 5: Multi-Agent Workflows**
   - Implement agent communication protocols
   - Create workflow state management system
   - Update multi-agent examples

This proposed structure represents the target state of the codebase after completing all planned features in the implementation plan. It provides a roadmap for development while maintaining compatibility with the existing architecture.