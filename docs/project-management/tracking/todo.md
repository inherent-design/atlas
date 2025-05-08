# Atlas Project TODO

## Current Implementation Focus

This file tracks immediate tasks for active development. For comprehensive planning and development guidance, refer to:

| Planning Document | Purpose | Link |
|-------------------|---------|------|
| **Architecture Planning** | System architecture, file structure, and implementation strategies | [architecture_planning.md](../planning/architecture_planning.md) |
| **Documentation Planning** | Documentation system organization and content requirements | [docs_planning.md](../planning/docs_planning.md) |
| **CLI Planning** | CLI architecture, logging system, and command structure | [cli_planning.md](../planning/cli_planning.md) |
| **Test Suite Planning** | Test structure, organization, and implementation strategy | [test_suite_planning.md](../planning/test_suite_planning.md) |

For long-term roadmap and MVP strategy, see [mvp_strategy.md](../roadmap/mvp_strategy.md).

## High Priority Tasks

### 🧪 Test Suite Refactoring
*See detailed analysis in [test_suite_planning.md](../planning/test_suite_planning.md)*
- [ ] Implement new test directory structure (unit, mock, integration, api)
- [ ] Update test runner CLI to use explicit flags instead of environment variables
- [ ] Create standardized test patterns with helper classes and decorators
- [ ] Migrate existing tests to new structure
- [ ] Implement proper API test cost controls and confirmation system
- [ ] Add comprehensive integration tests for component interactions

### 🔌 Provider Implementation Completion
*See detailed plans in [architecture_planning.md](../planning/architecture_planning.md#provider-flexibility--performance-accel)*
- [ ] Implement additional error handling for streaming edge cases
- [ ] Add comprehensive retry mechanisms for transient API failures
- [ ] Create connection pooling for performance optimization
- [ ] Implement provider health monitoring and statistics gathering
- [ ] Add dynamic provider switching based on performance/cost needs

### 💻 CLI Improvements 
*See detailed implementation guidance in [cli_planning.md](../planning/cli_planning.md)*
- [x] Implement centralized logging system with structlog
- [x] Configure third-party library log suppression (ChromaDB, OpenTelemetry)
- [x] Fix telemetry initialization issues and empty reader errors
- [x] Implement lazy initialization for metrics to prevent errors when telemetry is disabled
- [ ] Add verbosity controls and log formatting options
- [ ] Create consistent command structure with subcommands
- [ ] Improve error reporting with contextual information
- [ ] Add progress indicators for long-running operations

## Medium Priority Tasks

### 🛠️ Tool System Implementation
*See initial structure in [architecture_planning.md](../planning/architecture_planning.md#multi-agent-intelligence-accel)*
- [ ] Create Tool base class with schema validation
- [ ] Implement ToolRegistry for tool discovery
- [ ] Add permission system for tool access control
- [ ] Develop standard tool set for common operations
- [ ] Create MCP adapter for external tool integration

### 🧠 Knowledge System Enhancements
*See related documentation in [architecture_planning.md](../planning/architecture_planning.md#enhanced-knowledge-retrieval-accel)*
- [ ] Implement query caching for improved performance
- [ ] Add telemetry for knowledge operations
- [ ] Support more document types and formats
- [ ] Enhance filtering with more advanced options
- [ ] Create document relevance feedback mechanisms

## Long-Term / Low Priority Tasks

### 📊 System Improvements
- [ ] Add visualization tools for workflow inspection
- [ ] Create more comprehensive documentation examples
- [ ] Implement advanced parallel processing optimizations

### 📚 Content Enhancements
- [ ] Add multimedia document support to knowledge system
- [ ] Create interactive examples in documentation
- [ ] Develop dashboard for system monitoring and visualization

## Recently Completed Tasks

### 🏁 Provider Improvements
- ✅ Complete streaming implementation for all providers (Anthropic, OpenAI, Ollama)
- ✅ Implement enhanced error handling with standardized error types
- ✅ Create mock provider for API-free testing
- ✅ Add token usage tracking and cost calculation

### 🔧 System Reliability
- ✅ Fix telemetry initialization issues and empty reader errors
- ✅ Implement lazy initialization for metrics to prevent errors when telemetry is disabled
- ✅ Fix provider error tests to align with error class implementation
- ✅ Update documentation to match new logging and telemetry behavior

### 📝 Documentation & Planning
- ✅ Update documentation with latest implementation details
- ✅ Ensure consistency between environment variables and their documentation
- ✅ Reorganize project planning into focused documents
- ✅ Create CLI planning document
- ✅ Set up initial tools structure and documentation