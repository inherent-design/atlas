# Atlas Project TODO

## Implementation Sprint Focus

This file tracks immediate tasks for active development to reach MVP status. Implementation priority is given to core functionality and creating robust example-driven demonstrations of features.

## Module Implementation Status

### 1. Provider System: Well-implemented with robust functionality
- ✅ ProviderOptions and provider resolution
- ✅ Capability-based model selection
- ✅ Retry mechanism with exponential backoff
- ✅ Unified interface across providers
- 🚧 ProviderGroup implementation (pending)
- 🚧 Connection timeout handling (pending)
- 🚧 Client-side rate limiting (pending)

### 2. Knowledge System: Well-implemented with robust functionality
- ✅ Basic retrieval functionality
- ✅ Document processing pipeline
- ✅ Relevance scoring
- ✅ Advanced metadata filtering with ChromaDB 1.0.8+ compatibility
- ✅ Document content filtering with where_document parameter
- ✅ Standardized error handling for retrieval operations
- 🚧 Enhanced chunking strategies (partial)
- 🚧 Hybrid retrieval system (planned but not fully implemented)

### 3. Agent System: Requires updates to work with the latest provider system
- ✅ Basic agent implementation
- ✅ Query client interface
- 🚧 Update to work with provider options (critical blocker)
- 🚧 Tool discovery and capability interfaces (planned)
- 🚧 Multi-agent workflows (planned)

## Critical Path Tasks (High Priority)

### 🏗️ Core Architecture Rework

#### Streamline Streaming Architecture (Highest Priority)
- [ ] Refactor streaming interfaces for consistency
  - Create unified StreamResponse model
  - Standardize stream handlers across providers
  - Implement proper resource cleanup for all streams
- [ ] Add stream control capabilities
  - Create pause/resume functionality for streams
  - Add stream cancellation support
  - Implement backpressure handling

#### Agent-Toolkit Integration (High Priority)
- [ ] Create clear separation between agents and tools
  - Define tool discovery and capability interfaces
  - Implement standardized tool invocation patterns
  - Create tool result handling framework
- [ ] Enhance agent orchestration
  - Implement agent communication protocols
  - Create workflow state management system
  - Add message passing interfaces between agents

#### Provider System Enhancements (High Priority)
- [x] ~~Create centralized `ProviderOptions` data class for all provider parameters~~ ✅
- [x] ~~Implement provider/model/capability resolution in the factory~~ ✅
- [x] ~~Move provider detection logic from CLI to factory layer~~ ✅
- [ ] Implement ProviderGroup for aggregation and fallback
  - Create ProviderGroup class that implements BaseProvider interface
  - Create ProviderSelectionStrategy with multiple strategies:
    - Failover: Try providers in sequence until one works
    - Round-robin: Rotate through available providers
    - Cost-optimized: Select providers based on estimated cost
  - Implement provider health monitoring and recovery
  - Add automatic retry with different providers
  - Create configuration options for group behavior
  - Update factory to support creating provider groups
- [ ] Update AtlasAgent to work with provider instances
  - Add direct provider instance support in constructor
  - Update provider initialization logic
  - Maintain backward compatibility with string provider names
  - Add support for provider group configuration
- [ ] Update CLI and configuration for provider groups
  - Add --providers argument for specifying multiple providers
  - Add --provider-strategy argument for selection strategy
  - Update configuration to support provider groups
  - Create example demonstrating provider group usage
- [ ] Standardize provider interfaces
  - Ensure consistent method signatures across providers
  - Create clear provider capability discovery
  - Implement provider feature detection
- [ ] Add thorough documentation of the provider architecture
  - Create architecture diagrams
  - Document provider selection logic
  - Add examples for different provider configurations
  - Update API reference documentation

### 🔌 Provider Implementation Completion
- [x] ~~Implement retry mechanism with exponential backoff for transient failures~~ ✅ (Completed with circuit breaker pattern)
- [x] ~~Implement capability-based model selection~~ ✅ (Completed with capability tagging system)
  - Added capability tags (inexpensive, efficient, premium, vision) to models
  - Added auto-detection of providers from model names
  - Created CLI integration with --capability flag
  - Updated documentation with capability-based examples
- [x] ~~Add connection timeout handling with configurable parameters~~ ✅ (Completed for Ollama provider)
  - Updated Ollama provider with timeout configuration
  - Added environment variables and CLI parameters for timeouts
  - Created provider-specific endpoint configuration
  - Updated documentation with provider-specific options
- [ ] Create client-side rate limiting to prevent API blocks
  - Add token bucket rate limiting for API requests
- [ ] Implement token usage tracking and optimization
  - Create comprehensive token accounting
  - Add token usage analytics and reporting

### 🧠 Knowledge System Improvements
- [x] ~~Add metadata filtering and faceted search~~ ✅
  - ✅ Implement metadata extraction during ingestion
  - ✅ Create metadata-based filtering interface compatible with ChromaDB 1.0.8+
  - ✅ Add document content filtering with `where_document` parameter
- [x] ~~Fix metadata handling in query_with_context function~~ ✅
- [x] ~~Create advanced filtering example~~ ✅
  - ✅ Added examples/15_advanced_filtering.py with filtering demonstrations
  - ✅ Updated documentation on filtering capabilities
- [x] ~~Standard error handling for filtering operations~~ ✅
  - ✅ Added handle_example_error utility in common.py
  - ✅ Standardized filtering error messages
  - ✅ Updated examples with consistent error handling
- [ ] Implement hybrid retrieval system
  - Create combined keyword + semantic search
  - Add relevance scoring mechanism
  - Implement configurable weighting between approaches
- [ ] Implement enhanced chunking strategies for different document types
  - Create semantic-aware chunking
  - Add overlap control and configuration
- [ ] Optimize for performance
  - Add caching layer for frequent queries
  - Implement bulk operations for efficiency

### 🛠️ Agent System Updates
- [ ] Update the agent system to work with provider options (critical unblocker)
- [ ] Create simplified tool interface
- [ ] Design and implement Tool base class
  - Add schema validation for tool inputs/outputs
  - Create standardized tool interface
  - Implement error handling and reporting
- [ ] Build dynamic tool discovery system
  - Create ToolRegistry for finding and loading tools
  - Implement discovery from multiple locations
  - Add tool versioning and compatibility checks

## Implementation Plan by Phase

### Phase 1: Implement Enhanced Provider System (highest priority)

#### 1.1 Create Provider Registry
- [ ] Implement `ProviderRegistry` in `providers/registry.py`
  - [ ] **Core Data Structures**
    - [ ] Create provider-to-class mapping
    - [ ] Create provider-to-models mapping
    - [ ] Create model-to-provider mapping
    - [ ] Create model-to-capabilities mapping
    - [ ] Create capability-to-models mapping
  - [ ] **Registration Methods**
    - [ ] Implement `register_provider` method
    - [ ] Implement `register_model_capability` method with strength levels
    - [ ] Add method chaining support for fluent API
  - [ ] **Query Methods**
    - [ ] Implement `get_provider_for_model` method
    - [ ] Implement `get_models_by_capability` with strength filtering
    - [ ] Implement `get_models_for_provider` method
    - [ ] Implement `get_capabilities_for_model` method
    - [ ] Implement `find_provider_by_model` method
    - [ ] Implement `find_models_with_capabilities` for multi-capability queries
  - [ ] **Factory Methods**
    - [ ] Implement `create_provider` method for provider instantiation
    - [ ] Add capability-based provider creation
  - [ ] **Helper Methods**
    - [ ] Add `get_all_providers`, `get_all_models`, `get_all_capabilities` methods
    - [ ] Implement global registry instance
    - [ ] Add registration hooks for provider modules

#### 1.2 Implement Enhanced Capability System
- [ ] Create `providers/capabilities.py` module
  - [ ] **Capability Strength System**
    - [ ] Implement `CapabilityStrength` enum with levels (BASIC through EXCEPTIONAL)
    - [ ] Add comparison operators for strength levels
  - [ ] **Define Capability Constants**
    - [ ] Define operational capabilities (inexpensive, efficient, premium)
    - [ ] Define task capabilities (code, reasoning, creative, extraction, etc.)
    - [ ] Define domain-specific capabilities (science, finance, legal, etc.)
    - [ ] Create `ALL_CAPABILITIES` set with all capability types
  - [ ] **Task Capability Mapping**
    - [ ] Create `TASK_CAPABILITY_REQUIREMENTS` dictionary
    - [ ] Map common tasks to capability requirements
    - [ ] Implement capability strength requirements for each task
  - [ ] **Helper Functions**
    - [ ] Implement `get_capabilities_for_task` function
    - [ ] Create `detect_task_type_from_prompt` heuristic function
    - [ ] Add utility functions for capability manipulation

#### 1.3 Implement ProviderGroup
- [ ] Create `ProviderGroup` class in `providers/group.py`
  - [ ] **Core Implementation**
    - [ ] Implement `ProviderGroup` class inheriting from `BaseProvider`
    - [ ] Add constructor for multiple provider instances
    - [ ] Implement required BaseProvider interface methods
    - [ ] Create provider health tracking system
  - [ ] **Selection Strategies**
    - [ ] Implement `ProviderSelectionStrategy` static class
    - [ ] Create `failover` strategy (sequential provider usage)
    - [ ] Create `round_robin` strategy (load balancing)
    - [ ] Create `cost_optimized` strategy (cheapest provider first)
    - [ ] Implement `TaskAwareSelectionStrategy` for capability-based selection
  - [ ] **Provider Operations**
    - [ ] Implement `generate` method with fallback between providers
    - [ ] Implement `generate_stream` method with fallback
    - [ ] Add provider health monitoring and recovery
    - [ ] Implement retry logic for failed providers
    - [ ] Add context tracking for stateful strategies

#### 1.4 Update Factory and Integration
- [ ] Update factory to use registry and support provider groups
  - [ ] **Factory Integration**
    - [ ] Integrate `ProviderRegistry` with `factory.py`
    - [ ] Update `create_provider` to use registry
    - [ ] Implement `create_provider_group` function
    - [ ] Add model-based detection using registry
    - [ ] Create task-aware provider selection method
  - [ ] **Provider Options Updates**
    - [ ] Enhance `ProviderOptions` to support capabilities
    - [ ] Add provider group configuration options
    - [ ] Create task type field for task-aware selection
    - [ ] Add capability requirements field
  - [ ] **Base Provider Updates**
    - [ ] Add capability retrieval methods to `BaseProvider`
    - [ ] Implement `get_capability_strength` method
    - [ ] Add capability registration in provider constructors

#### 1.5 Update Agent System
- [ ] Enhance agent system to work with registry and provider groups
  - [ ] **Agent Updates**
    - [ ] Modify `AtlasAgent` to accept provider instances directly
    - [ ] Update provider initialization logic
    - [ ] Add support for task-aware provider selection
    - [ ] Maintain backward compatibility with string provider names
  - [ ] **Task-Aware Agent**
    - [ ] Create `TaskAwareAgent` class extending `AtlasAgent`
    - [ ] Implement task type detection in query method
    - [ ] Add dynamic provider selection based on task
    - [ ] Create prompting strategies for different tasks

#### 1.6 CLI and Configuration Updates
- [ ] Add CLI and configuration support for enhanced provider system
  - [ ] **CLI Arguments**
    - [ ] Add `--providers` argument for multiple providers
    - [ ] Add `--provider-strategy` argument for selection strategies
    - [ ] Add `--capabilities` argument for capability requirements
    - [ ] Add `--task-type` argument for task-aware selection
    - [ ] Create parser for capability format (name:strength)
  - [ ] **Configuration Integration**
    - [ ] Update `AtlasConfig` to support provider groups
    - [ ] Add capability configuration options
    - [ ] Create task type configuration option
    - [ ] Update environment variables for new options
  - [ ] **Runtime Configuration**
    - [ ] Add dynamic configuration based on task detection
    - [ ] Implement capability parsing from string format
    - [ ] Create helper functions for CLI argument handling

#### 1.7 Documentation and Examples
- [ ] Create examples and documentation
  - [ ] **Provider Group Example**
    - [ ] Create `04_provider_group.py` demonstrating provider groups
    - [ ] Show different selection strategies in action
    - [ ] Demonstrate fallback behavior with simulated failures
    - [ ] Add health monitoring demonstration
  - [ ] **Task-Aware Provider Example**
    - [ ] Create `05_task_aware_providers.py` with capability-based selection
    - [ ] Demonstrate different task types with appropriate providers
    - [ ] Show automatic task type detection
    - [ ] Implement benchmark comparison between strategies
  - [ ] **Documentation**
    - [ ] Update API reference for provider system
    - [ ] Create provider registry architecture documentation
    - [ ] Document capability system with examples
    - [ ] Add developer guide for extending capabilities
    - [ ] Create visualization of provider selection process

### Phase 2: Streamline Streaming Architecture
- [ ] Create unified StreamResponse model
- [ ] Standardize stream handlers across providers
- [ ] Implement proper resource cleanup for all streams
- [ ] Add stream control capabilities

### Phase 3: Enhance Agent System with Tools
- [ ] Update AtlasAgent to work with provider options
- [ ] Create simplified tool interface
- [ ] Define tool discovery and capability interfaces
- [ ] Implement standardized tool invocation patterns

### Phase 4: Implement Hybrid Retrieval
- [ ] Implement combined keyword + semantic search
- [ ] Add relevance scoring mechanism
- [ ] Create configurable weighting system
- [ ] Add example demonstrating hybrid search

### Phase 5: Multi-Agent Workflows
- [ ] Implement agent communication protocols
- [ ] Create workflow state management system
- [ ] Update multi-agent examples

## Recently Completed Tasks

### Example System Improvements
- ✅ Standardize error handling across examples
  - Created handle_example_error utility in common.py
  - Updated all examples to use consistent error handling
  - Added debug logging for troubleshooting
- ✅ Fix import statements in all examples
  - Ensured proper imports from common.py
  - Fixed relative imports for all examples
  - Made imports consistent across example files
- ✅ Update todo example files with common utilities
  - Added standardized structure to todo files
  - Ensured consistent CLI argument handling
  - Prepared for future implementations
- ✅ Standardize CLI arguments
  - Removed duplicate CLI arguments
  - Fixed argument conflicts
  - Improved help documentation

### Knowledge System Improvements
- ✅ Implement advanced metadata filtering for ChromaDB 1.0.8+ compatibility
  - Added comprehensive filtering operators ($eq, $ne, $gt, $gte, $lt, $lte, $in, $nin)
  - Implemented RetrievalFilter builder class with chainable methods
  - Enhanced error handling for filter operations
  - Added auto-correction of operator syntax
- ✅ Add document content filtering
  - Implemented where_document parameter support
  - Added document_contains and document_not_contains helper methods
  - Created combined metadata and content filtering capabilities
  - Updated query_with_context to support document filtering
- ✅ Create documentation and examples for filtering
  - Added comprehensive ChromaDB usage guide
  - Created 15_advanced_filtering.py example
  - Updated knowledge system documentation
  - Added hybrid retrieval design document

### Provider Improvements
- ✅ Implement capability-based model selection
  - Added capability tags (inexpensive, efficient, premium, vision, standard) to models
  - Implemented provider auto-detection from model names
  - Created centralized model configuration system
  - Added capability-aware factory methods
  - Updated CLI interface with --capability option
  - Enhanced documentation with capability-based examples
- ✅ Implement robust retry mechanism with exponential backoff
  - Added configurable retry limits, delays, and backoff factors
  - Implemented jitter to prevent thundering herd problems
  - Created circuit breaker pattern to prevent cascading failures
  - Added comprehensive documentation and examples
- ✅ Improve Ollama provider integration
  - Added dynamic model discovery using Ollama API
  - Implemented robust error handling for server unavailability
  - Added configurable timeouts for connection and requests
  - Created provider-specific environment variables and CLI parameters
  - Improved model compatibility detection for custom models
  - Updated documentation with Ollama-specific configuration options
- ✅ Complete streaming implementation for all providers
- ✅ Implement enhanced error handling with standardized error types
- ✅ Create mock provider for API-free testing
- ✅ Add token usage tracking and cost calculation
- ✅ Create provider-specific mock libraries for consistent testing

### System Reliability
- ✅ Implement lazy initialization for telemetry metrics
- ✅ Fix core logging system configuration
- ✅ Improve error handling across all providers
- ✅ Remove test-specific code from provider implementations
- ✅ Rename `models` module to `providers` for better terminology consistency