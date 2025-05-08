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
- [x] Implement new test directory structure (unit, mock, integration, api)
- [x] Update test runner CLI to use explicit flags instead of environment variables
- [x] Create standardized test patterns with helper classes and decorators
- [x] Migrate existing provider tests to new structure
- [x] Implement proper API test cost controls and confirmation system
- [x] Add comprehensive integration tests for component interactions

#### Test Structure Migration Tracker

The following represents the target test directory structure and migration status:

```
atlas/tests/
├── unit/                 # Unit tests that don't require API calls
│   ├── core/             
│       ├── [✅] test_env.py             # DONE: Environment variable tests
│       ├── [✅] test_errors.py          # DONE: Core error classes tests
│       ├── [✅] test_config.py          # DONE: Configuration tests
│       └── [✅] test_telemetry.py       # DONE: Telemetry tests
│   ├── models/           
│       ├── [✅] test_base_models.py     # DONE: TokenUsage and base classes tests
│       ├── [✅] test_structured_message.py # DONE: Message structure tests
│       └── [ ] test_factory.py         # TODO: Model factory tests
│   ├── knowledge/        
│       ├── [✅] test_document_ids.py    # DONE: Document ID formatting tests
│       ├── [✅] test_chunking.py        # DONE: Chunking strategy tests
│       └── [✅] test_embedding.py       # DONE: Embedding functionality tests
│   ├── agents/           
│       ├── [✅] test_agent_toolkit.py   # DONE: Agent toolkit tests
│       ├── [ ] test_registry.py        # TODO: Agent registry tests
│       └── [ ] test_base.py            # TODO: Base agent tests
│   └── tools/            
│       ├── [ ] test_base_tool.py       # TODO: Base tool tests
│       └── [ ] test_tool_schemas.py    # TODO: Tool schema tests
│
├── mock/                 # Tests that use mocked providers/APIs
│   ├── providers/        
│       ├── [✅] test_mock_provider.py   # DONE: Mock provider tests
│       ├── [✅] test_openai_provider.py # DONE: OpenAI provider mock tests
│       ├── [✅] test_anthropic_provider.py # DONE: Anthropic provider mock tests
│       ├── [✅] test_ollama_provider.py # DONE: Ollama provider mock tests
│       ├── [✅] test_provider_errors.py # DONE: Provider error handling tests
│   ├── agents/           
│       ├── [✅] test_tool_capable_agent.py # DONE: Tool agent with mocked providers
│       └── [ ] test_worker_agent.py    # TODO: Worker agent with mocked providers
│   └── workflows/        
│       ├── [ ] test_query_workflow.py  # TODO: Query workflow tests
│       └── [ ] test_retrieval_workflow.py # TODO: Retrieval workflow tests
│
├── integration/          # Tests that connect multiple components
│   ├── agent_tool/       
│       ├── [✅] test_agent_tool_integration.py # DONE: Agent + Tool integration tests
│       └── [ ] test_agent_multi_tool.py # TODO: Agent with multiple tools
│   ├── knowledge_agent/  
│       ├── [ ] test_knowledge_query.py # TODO: Knowledge + Agent integration
│       └── [ ] test_retrieval_agent.py # TODO: Retrieval with Agent integration
│   └── workflow/         
│       ├── [ ] test_full_query_workflow.py # TODO: End-to-end query workflow
│       └── [ ] test_streaming_workflow.py # TODO: Streaming workflow tests
│
├── api/                  # Real API tests (expensive)
│   ├── openai/           
│       ├── [✅] test_openai_api.py      # DONE: OpenAI API tests
│       └── [ ] test_openai_streaming.py # TODO: OpenAI streaming API tests
│   ├── anthropic/        
│       ├── [✅] test_anthropic_api.py   # DONE: Anthropic API tests
│       └── [ ] test_anthropic_streaming.py # TODO: Anthropic streaming API tests
│   └── ollama/           
│       ├── [✅] test_ollama_api.py      # DONE: Ollama API tests
│       └── [ ] test_ollama_streaming.py # TODO: Ollama streaming API tests
│
├── helpers/              # Test helper functions and base classes
│   ├── [✅] __init__.py               # DONE: Helper module initialization
│   ├── [✅] decorators.py             # DONE: Test decorators 
│   ├── [✅] base_classes.py           # DONE: Base test classes
│   ├── [✅] mocks.py                  # DONE: Common mock functions
│   └── [ ] utils.py                  # TODO: Additional test utilities
│
└── [✅] __init__.py                   # DONE: Main test initialization
```

#### Remaining Test Migration Tasks
- [x] **Provider Tests**
  - [x] Migrate OpenAI provider tests (mock + API)
  - [x] Migrate Anthropic provider tests (mock + API)
  - [x] Migrate Ollama provider tests (mock + API)
  - [x] Migrate Mock provider tests
  - [x] Migrate Provider Errors tests
- [ ] **Agent Tests**
  - [x] Migrate Agent Toolkit tests
  - [x] Migrate Tool Capable Agent tests
  - [ ] Create agent integration tests with knowledge components
- [ ] **Core Component Tests**
  - [x] Migrate Environment module tests
  - [x] Migrate Model base classes tests
  - [x] Migrate Token Usage tests
  - [x] Migrate Error classes tests
  - [x] Migrate Telemetry tests
  - [x] Migrate Config tests
- [x] **Knowledge Tests**
  - [x] Migrate Document ID tests
  - [x] Migrate Chunking tests
  - [x] Migrate Embedding tests
  - [ ] Create knowledge component integration tests
- [ ] **Message/Structure Tests**
  - [x] Migrate Structured Message tests
  - [ ] Create message handling integration tests
- [ ] **Test Helpers**
  - [x] Migrate test helpers to the new structure (with decorators and base classes)
  - [ ] Create additional helper functions as needed for new test patterns
- [ ] **Examples and Documentation**
  - [ ] Create example tests for each test type
  - [ ] Add comments explaining test patterns and best practices
  - [ ] Update testing documentation with comprehensive examples

#### Next Migration Priorities
1. Create message handling integration tests
2. Create additional agent integration tests
3. Create knowledge component integration tests

#### Verification and Quality Tasks

##### Core Modules Verification - Completed ✅
We have successfully verified and fixed tests for all the core modules:
- Environment Module (test_env.py)
- Error Module (test_errors.py)
- Config Module (test_config.py) 
- Telemetry Module (test_telemetry.py)

##### Knowledge Modules Verification - Completed ✅
We have successfully verified and fixed tests for all the knowledge modules:
- Document IDs Module (test_document_ids.py)
- Chunking Module (test_chunking.py)
- Embedding Module (test_embedding.py)

##### Models Modules Verification - Completed ✅
We have successfully verified and fixed tests for all the models modules:
- Base Models Module (test_base_models.py)
- Structured Message Module (test_structured_message.py)

##### Remaining Verification Tasks

##### Core Module Verification
- [x] **Environment Module** (`test_env.py`)
  - [x] Run tests with `uv run python -m unittest atlas/tests/unit/core/test_env.py`
  - [x] Fix any failures in implementation or tests
  - [x] Ensure test coverage of all key functionality
  - [x] Verify correct decorator usage

- [x] **Error Module** (`test_errors.py`)
  - [x] Run tests with `uv run python -m unittest atlas/tests/unit/core/test_errors.py`
  - [x] Fix any failures in implementation or tests
  - [x] Ensure test coverage of all error classes and error handling utilities
  - [x] Verify correct decorator usage

- [x] **Config Module** (`test_config.py`)
  - [x] Run tests with `uv run python -m unittest atlas/tests/unit/core/test_config.py`
  - [x] Fix any failures in implementation or tests
  - [x] Ensure test coverage of environment variable handling, validation, and defaults
  - [x] Verify correct decorator usage

- [x] **Telemetry Module** (`test_telemetry.py`)
  - [x] Run tests with `uv run python -m unittest atlas/tests/unit/core/test_telemetry.py`
  - [x] Fix any failures in implementation or tests
  - [x] Ensure test coverage of initialization, configuration, tracing, and metrics
  - [x] Verify correct decorator usage

##### Knowledge Module Verification
- [x] **Document IDs** (`test_document_ids.py`)
  - [x] Run tests with `uv run python -m unittest atlas/tests/unit/knowledge/test_document_ids.py`
  - [x] Fix any failures in implementation or tests
  - [x] Ensure test coverage of ID formatting logic
  - [x] Verify correct decorator usage

- [x] **Chunking Module** (`test_chunking.py`)
  - [x] Run tests with `uv run python -m unittest atlas/tests/unit/knowledge/test_chunking.py`
  - [x] Fix any failures in implementation or tests
  - [x] Ensure test coverage of all chunking strategies (fixed, semantic, markdown, code)
  - [x] Verify correct decorator usage

- [x] **Embedding Module** (`test_embedding.py`)
  - [x] Run tests with `uv run python -m unittest atlas/tests/unit/knowledge/test_embedding.py`
  - [x] Fix any failures in implementation or tests
  - [x] Ensure test coverage of all embedding strategies (Anthropic, ChromaDB, Hybrid)
  - [x] Verify correct decorator usage

##### Models Module Verification
- [x] **Base Models** (`test_base_models.py`)
  - [x] Run tests with `uv run python -m unittest atlas/tests/unit/models/test_base_models.py`
  - [x] Fix any failures in implementation or tests
  - [x] Ensure test coverage of TokenUsage, CostEstimate, and base model classes
  - [x] Verify correct decorator usage

- [x] **Structured Message** (`test_structured_message.py`)
  - [x] Run tests with `uv run python -m unittest atlas/tests/unit/models/test_structured_message.py`
  - [x] Fix any failures in implementation or tests
  - [x] Ensure test coverage of message structure and formatting
  - [x] Verify correct decorator usage

##### Provider Tests Verification

##### Provider Tests Verification - In Progress
- [x] **Mock Provider** (`test_mock_provider.py`)
  - [x] Run tests with `uv run python -m unittest atlas/tests/mock/providers/test_mock_provider.py`
  - [x] Fix any failures in implementation or tests
  - [x] Ensure test coverage of all mock provider functionality
  - [x] Verify correct decorator usage

- [x] **OpenAI Provider** (Mock Tests)
  - [x] Run mock tests with `uv run python -m unittest atlas/tests/mock/providers/test_openai_provider.py`
  - [x] Fix any failures in implementation or tests
  - [x] Ensure test coverage of generation, streaming, error handling
  - [x] Verify correct decorator usage

- [x] **Anthropic Provider** (Mock Tests)
  - [x] Run mock tests with `uv run python -m unittest atlas/tests/mock/providers/test_anthropic_provider.py`
  - [x] Fix any failures in implementation or tests 
  - [x] Ensure test coverage of generation, streaming, error handling
  - [x] Verify correct decorator usage

- [x] **Anthropic Provider** (API Tests)
  - [x] Run API tests with `uv run python -m atlas.scripts.testing.run_tests api -p anthropic --confirm`
  - [x] Fix any failures in implementation or tests
  - [x] Ensure test coverage of generation, streaming, error handling

- [x] **OpenAI Provider** (API Tests)
  - [x] Run API tests with `uv run python -m atlas.scripts.testing.run_tests api -p openai --confirm`
  - [x] Fix any failures in implementation or tests
  - [x] Ensure test coverage of generation, streaming, error handling

- [x] **Ollama Provider** (Mock Tests)
  - [x] Run mock tests with `uv run python -m atlas.scripts.testing.run_tests mock -p ollama`
  - [x] Fix any failures in implementation or tests
  - [x] Ensure test coverage of generation, streaming, error handling
  - [x] Verify correct decorator usage

- [x] **Ollama Provider** (API Tests)
  - [x] Run API tests with `uv run python -m atlas.scripts.testing.run_tests api -p ollama --confirm`
  - [x] Fix any failures in implementation or tests
  - [x] Ensure test coverage of generation, streaming, error handling

- [x] **Provider Errors** (`test_provider_errors.py`)
  - [x] Run tests with `uv run python -m atlas.scripts.testing.run_tests mock -m providers`
  - [x] Fix any failures in implementation or tests
  - [x] Ensure test coverage of error handling across all providers
  - [x] Verify correct decorator usage

##### Agent Tests Verification
- [x] **Agent Toolkit** (`test_agent_toolkit.py`)
  - [x] Run tests with `uv run python -m atlas.scripts.testing.run_tests unit -m agents`
  - [x] Fix any failures in implementation or tests
  - [x] Ensure test coverage of toolkit registration and functionality
  - [x] Verify correct decorator usage

- [x] **Tool Capable Agent** (`test_tool_capable_agent.py`)
  - [x] Run tests with `uv run python -m atlas.scripts.testing.run_tests mock -m agents`
  - [x] Fix any failures in implementation or tests
  - [x] Ensure test coverage of tool execution and integration
  - [x] Verify correct decorator usage

##### Integration Tests Verification
- [x] **Agent Tool Integration** (`test_agent_tool_integration.py`)
  - [x] Run tests with `uv run python -m atlas.scripts.testing.run_tests integration -m agent_tool`
  - [x] Fix any failures in implementation or tests
  - [x] Ensure test coverage of agent-tool interactions
  - [x] Verify correct decorator usage

##### Test Runner Verification
- [x] Run test runner with all test types to verify functionality
  - [x] `uv run python -m atlas.scripts.testing.run_tests unit`
  - [x] `uv run python -m atlas.scripts.testing.run_tests mock`
  - [x] `uv run python -m atlas.scripts.testing.run_tests integration`
  - [x] `uv run python -m atlas.scripts.testing.run_tests unit mock integration`
  - [x] `uv run python -m atlas.scripts.testing.run_tests unit -m core`
  - [x] `uv run python -m atlas.scripts.testing.run_tests api -p openai --confirm`

Note: The old `run_tests.py` is now renamed to `run_tests.py.old`, and the new CLI interface is active. The new test runner has the following key features:
- Explicit CLI flags instead of environment variables
- Module-specific testing with `--module` flag
- Provider-specific API testing with `--provider` flag
- Cost control with `--cost-limit` and `--enforce-cost-limit` flags
- Confirmation prompt for API tests (can be skipped with `--confirm`)

##### Final Verification
- [x] Check for any import issues across all test modules
- [x] Ensure consistent use of test decorators across all tests
- [x] Verify test coverage metrics to ensure we maintain or improve coverage
- [x] Run full test suite to ensure all tests pass in the new structure
    - Note: The old test files (legacy structure) might still show a few errors with Ollama provider, but all tests in the new structure are passing

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