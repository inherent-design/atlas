---

title: TODO

---


# TODO

::: tip Current Status (May 17, 2025)
This file tracks active development tasks for Atlas. For the current sprint (May 17-24), we're shifting our focus to implementing the core services layer and tool execution framework. We've completed schema validation for all provider implementations and the tool agent system, and now need to build the foundational services that enable robust tool execution, event-driven communication, and improved state management.
:::

::: timeline Core Services Implementation
- **Saturday-Tuesday (May 18-21, 2025)**
- Create core services module foundation
- Implement thread-safe buffer system with flow control
- Develop event-based communication system with subscription
- Add state management with versioning and transitions
- Create resource lifecycle management and boundaries
:::

::: timeline Tool Execution Framework
- **Tuesday-Thursday (May 21-23, 2025)**
- Create standardized tool execution pipeline
- Implement comprehensive error handling and recovery
- Add execution metrics and telemetry collection
- Develop result processing and validation system
- Build hooks for pre/post execution processing
:::

::: timeline Knowledge Tools Integration
- **Thursday-Saturday (May 23-25, 2025)**
- Implement knowledge retrieval tools with filtering
- Create document ingestion and processing tools
- Add hybrid search tools with customizable strategies
- Develop metadata filtering and faceted search tools
- Integrate knowledge tools with agent system
:::

## Current Sprint Focus: Core Services & Tool Execution Framework

::: warning Priority Requirements
Our focus for this sprint is entirely on:
1. Building the core services layer as a foundation for all systems
2. Implementing a robust tool execution framework
3. Creating knowledge tools for retrieval and processing
4. Developing tool chaining and composition capabilities
5. Implementing comprehensive error handling and telemetry
:::

::: tip Component Focus
- **Core Services**: Buffer system, event system, state management, and boundary interfaces
- **Tool Execution**: Standardized execution pipeline, error handling, and result processing
- **Knowledge Tools**: Retrieval tools, ingestion tools, and hybrid search integration
- **Tool Chaining**: Sequential and parallel execution, conditional routing, and result transformation
:::

## Textual CLI Implementation Tasks

### 1. CLI Architecture Design (Target: May 20, 2025)

**Architecture Design** (High Priority)
- [ ] Design serializable command schema in `atlas/cli/textual/schema.py`
- [ ] Create command execution pattern in `atlas/cli/textual/commands.py`
- [ ] Design UI component structure and interaction flow
- [ ] Implement configuration manager with save/load capability
- [ ] Create dual-mode entry points in `atlas/cli/parser.py`
- [ ] Port common.py utility functions to appropriate core modules

::: tip Core Files
- Create: `atlas/cli/textual/schema.py` (Command schemas)
- Create: `atlas/cli/textual/commands.py` (Command execution)
- Create: `atlas/cli/textual/config.py` (Configuration manager)
- Update: `atlas/cli/parser.py` (CLI entry point with Textual support)
- Create: `atlas/cli/textual/app.py` (Main Textual application)
- Create: `atlas/cli/utils.py` (Utility functions from common.py)
:::

### 2. Core UI Components (Target: May 21, 2025)

**UI Implementation** (High Priority)
- [ ] Create main application layout with command bar and status display
- [ ] Implement command bar with tab completion and history
- [ ] Design conversation view with message formatting
- [ ] Build context panel with provider and document information
- [ ] Create status bar with execution state information
- [ ] Add rich text formatting utilities from common.py

::: tip Core Files
- Create: `atlas/cli/textual/widgets/command_bar.py` (Command input)
- Create: `atlas/cli/textual/widgets/conversation.py` (Message display)
- Create: `atlas/cli/textual/widgets/status.py` (Status display)
- Create: `atlas/cli/textual/widgets/context.py` (Context information)
- Create: `atlas/cli/textual/screens/main.py` (Main screen)
- Create: `atlas/cli/textual/utils/formatting.py` (Text formatting)
:::

### 3. Mode-Specific Screens (Target: May 22, 2025)

**Specialized Views** (High Priority)
- [ ] Implement provider selection screen with model list
- [ ] Create document ingestion screen with directory selection
- [ ] Design tool management screen with tool list and execution
- [ ] Build settings screen for configuration management
- [ ] Implement markdown rendering for documentation
- [ ] Add file browser component for document selection

::: tip Core Files
- Create: `atlas/cli/textual/screens/provider.py` (Provider selection)
- Create: `atlas/cli/textual/screens/ingest.py` (Document ingestion)
- Create: `atlas/cli/textual/screens/tools.py` (Tool management)
- Create: `atlas/cli/textual/screens/settings.py` (Settings management)
- Create: `atlas/cli/textual/utils/markdown.py` (Markdown rendering)
- Create: `atlas/cli/textual/widgets/file_browser.py` (File browser)
:::

### 4. Command Execution System (Target: May 23, 2025)

**Command Infrastructure** (High Priority)
- [ ] Create base command class with execution interface
- [ ] Implement query command with streaming support
- [ ] Create ingest command with directory processing
- [ ] Design tool command with parameter validation
- [ ] Implement controller command for multi-agent system
- [ ] Add error handling and recovery for commands
- [ ] Port create_provider_from_args from common.py to relevant module

::: tip Core Files
- Create: `atlas/cli/textual/commands/base.py` (Base command)
- Create: `atlas/cli/textual/commands/query.py` (Query command)
- Create: `atlas/cli/textual/commands/ingest.py` (Ingest command)
- Create: `atlas/cli/textual/commands/tool.py` (Tool command)
- Create: `atlas/cli/textual/commands/controller.py` (Controller command)
- Create: `atlas/providers/helpers.py` (Provider creation utilities)
:::

### 5. Serialization and Config Management (Target: May 24, 2025)

**Serialization System** (Medium Priority)
- [ ] Implement config serialization to JSON/YAML
- [ ] Create command serialization and deserialization
- [ ] Add command history with persistent storage
- [ ] Implement configuration import/export
- [ ] Create CLI flags to command mapping
- [ ] Add environment variable integration from common.py

::: tip Core Files
- Create: `atlas/cli/textual/serialization.py` (Serialization utilities)
- Create: `atlas/cli/textual/history.py` (Command history)
- Update: `atlas/cli/textual/config.py` (Configuration management)
- Create: `atlas/cli/textual/flags.py` (CLI flags mapping)
- Create: `atlas/cli/textual/import_export.py` (Config import/export)
- Update: `atlas/core/env.py` (Environment integration)
:::

### 6. Streaming Integration (Target: May 24, 2025)

**Streaming Support** (High Priority)
- [ ] Implement streaming display in conversation widget
- [ ] Create stream control buttons (pause/resume/cancel)
- [ ] Add streaming progress indicators
- [ ] Implement token counting during streaming
- [ ] Create visual indicators for stream status
- [ ] Add stream control message passing system

::: tip Core Files
- Update: `atlas/cli/textual/widgets/conversation.py` (Streaming display)
- Create: `atlas/cli/textual/widgets/stream_controls.py` (Stream control buttons)
- Create: `atlas/cli/textual/utils/streaming.py` (Stream utilities)
- Update: `atlas/cli/textual/commands/query.py` (Streaming command integration)
- Update: `atlas/providers/streaming/control.py` (Stream control integration)
:::

## Tool Agent Enhancement Tasks

### 1. Tool Registration System (Target: May 21, 2025)

**Tool Registry** (High Priority)
- [x] Fix tool registration in tool_agent example
- [x] Enhance tool registry with proper initialization
- [x] Add schema validation for tools during registration
- [ ] Implement automatic tool discovery logic
- [x] Improve permission management for tools
- [x] Add docstrings and usage documentation

::: tip Core Files
- Update: `atlas/tools/registry.py` (Tool registry)
- Update: `atlas/tools/base.py` (Tool base class)
- Create: `atlas/schemas/tools.py` (Tool schemas)
- Update: `examples/20_tool_agent.py` (Tool agent example)
- Create: `atlas/tests/tools/test_registry.py` (Registry tests)
:::

### 2. Tool Agent Implementation (Target: May 22, 2025)

**Tool Agent Enhancements** (High Priority)
- [ ] Implement automatic tool granting to workers  
- [x] Enhance tool execution with better error handling
- [x] Add tool result processing with validation
- [x] Create standardized tool result formatting
- [x] Provide detailed execution logs for debugging

::: tip Core Files
- Update: `atlas/agents/specialized/tool_agent.py` (Tool agent)
- Create: `atlas/schemas/tools.py` (Tool schemas) ✅
- Create: `atlas/tools/execution.py` (Tool execution framework)
- Create: `atlas/tools/results.py` (Tool result processing)
- Create: `atlas/tests/tools/test_tool_agent.py` (Tool agent tests)
:::

### 3. Knowledge Tool Integration (Target: May 23, 2025)

**Knowledge Tools** (Medium Priority)
- [ ] Implement RetrievalTool for knowledge base searches
- [ ] Create IngestTool for document processing
- [ ] Add FilteringTool for metadata filtering
- [ ] Design SearchTool for combined hybrid search
- [ ] Implement schema validation for knowledge tools

::: tip Core Files
- Create: `atlas/tools/standard/knowledge_tools.py` (Knowledge tools)
- Update: `atlas/schemas/tools.py` (Tool schemas)
- Create: `examples/23_knowledge_tools.py` (Knowledge tools example)
- Create: `atlas/tests/tools/test_knowledge_tools.py` (Knowledge tools tests)
:::

### 4. Tool Chaining Implementation (Target: May 24, 2025)

**Tool Chaining** (Medium Priority)
- [ ] Create tool chain builder interface
- [ ] Implement sequential tool execution
- [ ] Add parallel tool execution with result merging
- [ ] Design conditional execution based on tool results
- [ ] Implement result transformation between tools

::: tip Core Files
- Create: `atlas/tools/chaining.py` (Tool chaining)
- Create: `examples/24_tool_chaining.py` (Tool chaining example)
- Create: `atlas/tests/tools/test_tool_chaining.py` (Tool chaining tests)
:::

## Core Services Implementation Tasks

### 1. Core Services Module Foundation (Target: May 20, 2025)

**Module Structure** (High Priority)
- [ ] Create `atlas/core/services/` directory structure
- [ ] Define core service interfaces and protocols
- [ ] Implement type system for core services
- [ ] Create boundary interfaces for system boundaries
- [ ] Develop base service protocols

::: tip Core Files
- Create: `atlas/core/services/__init__.py` (Module exports)
- Create: `atlas/core/services/types.py` (Type definitions)
- Create: `atlas/core/services/boundaries.py` (Boundary interfaces)
- Create: `atlas/core/services/base.py` (Base protocols)
:::

### 2. Buffer System Implementation (Target: May 21, 2025)

**Buffer Protocol** (High Priority)
- [ ] Define buffer protocol in `atlas/core/services/buffer.py`
- [ ] Implement thread-safe `MemoryBuffer` 
- [ ] Create `RateLimitedBuffer` with flow control
- [ ] Develop `BatchingBuffer` for chunked operations
- [ ] Add buffer metrics and observability

::: tip Core Files
- Create: `atlas/core/services/buffer.py` (Buffer system)
- Create: `atlas/tests/core/services/test_buffer.py` (Buffer tests)
:::

### 3. Event System Implementation (Target: May 22, 2025)

**Event Framework** (High Priority)
- [ ] Create event type system in `atlas/core/services/events.py`
- [ ] Implement event bus with subscription management
- [ ] Add event filtering and routing capabilities
- [ ] Develop event history tracking
- [ ] Create middleware support for event processing

::: tip Core Files
- Create: `atlas/core/services/events.py` (Event system)
- Create: `atlas/tests/core/services/test_events.py` (Event tests)
:::

### 4. State Management System (Target: May 23, 2025)

**State Tracking** (Medium Priority)
- [ ] Implement state machine protocol in `atlas/core/services/state.py`
- [ ] Create versioned state container
- [ ] Add state transition validation
- [ ] Implement state projection system
- [ ] Add state persistence capabilities

::: tip Core Files
- Create: `atlas/core/services/state.py` (State management)
- Create: `atlas/tests/core/services/test_state.py` (State tests)
:::

## Example Development Tasks

### 1. CLI Examples (Target: May 24, 2025)

**Example Scripts** (Medium Priority)
- [ ] Create example demonstrating serializable command execution
- [ ] Add example showing configuration export/import
- [ ] Develop example for CLI flag-based execution
- [ ] Create example showing command history usage
- [ ] Add example demonstrating batch command execution

::: tip Core Files
- Create: `examples/25_cli_commands.py` (Command execution example)
- Create: `examples/26_cli_config.py` (Configuration example)
- Create: `examples/27_cli_batch.py` (Batch command example)
:::

### 2. Tool Examples (Target: May 23, 2025)

**Example Scripts** (High Priority)
- [ ] Update tool agent example with registry enhancements
- [ ] Create knowledge tools integration example
- [ ] Add tool chaining demonstration
- [ ] Implement example with custom tool development
- [ ] Create example with tool permission management

::: tip Core Files
- Update: `examples/20_tool_agent.py` (Tool agent example)
- Create: `examples/23_knowledge_tools.py` (Knowledge tools example)
- Create: `examples/24_tool_chaining.py` (Tool chaining example)
- Create: `examples/28_custom_tool_development.py` (Custom tool example)
:::

## Implementation Roadmap

::: warning Sprint Priorities
This focused sprint prioritizes the core services layer, tool execution framework, and knowledge tool integration:

1. **Week 1 (May 17-24, 2025)**: Core Services & Tool Execution
   - Core services module foundation and implementation
   - Buffer system with thread safety and flow control
   - Event system with subscription and routing
   - Tool execution framework with error handling
   - Knowledge tools integration

2. **Week 2 (May 25-31, 2025)**: Tool Chaining & Example Development
   - Tool chaining implementation
   - Sequential and parallel execution patterns
   - Conditional execution based on results
   - Example development for all components
   - Testing and documentation
:::

::: timeline Buffer System Implementation
- **May 17-19, 2025**
- Define buffer protocol interfaces
- Implement thread-safe memory buffer
- Create rate-limited buffer with flow control
- Develop batching buffer for chunked operations
- Add buffer metrics and observability
:::

::: timeline Event System Implementation
- **May 19-21, 2025**
- Create event type system and registry
- Implement event bus with subscription management
- Add event filtering and routing capabilities
- Develop event history and replay functionality
- Create middleware support for event processing
:::

::: timeline State Management System
- **May 21-23, 2025**
- Define state machine protocol interfaces
- Create versioned state container implementation
- Implement state transition validation and rules
- Add state projection and derived state capabilities
- Develop persistence mechanisms for state recovery
:::

::: timeline Tool Chaining Implementation
- **May 24-26, 2025**
- Create tool chain builder interface and factory
- Implement sequential tool execution patterns
- Add parallel tool execution with result merging
- Develop conditional execution based on tool results
- Create result transformation utilities between tools
:::

## Key Files for Current Sprint

| Component                      | Key Files                                                                          | Priority | Owner         |
| ------------------------------ | ---------------------------------------------------------------------------------- | -------- | ------------- |
| **Core Services Foundation**   | `atlas/core/services/__init__.py`, `atlas/core/services/base.py`                   | Critical | Core Team     |
| **Buffer System**              | `atlas/core/services/buffer.py`, `atlas/tests/core/services/test_buffer.py`        | Critical | Core Team     |
| **Event System**               | `atlas/core/services/events.py`, `atlas/tests/core/services/test_events.py`        | Critical | Core Team     |
| **State Management**           | `atlas/core/services/state.py`, `atlas/tests/core/services/test_state.py`          | Critical | Core Team     |
| **Tool Execution Framework**   | `atlas/tools/execution.py`, `atlas/tools/results.py`                                | Critical | Tools Team    |
| **Knowledge Tools**            | `atlas/tools/standard/knowledge_tools.py`, `examples/23_knowledge_tools.py`         | Critical | Tools Team    |
| **Tool Chaining**              | `atlas/tools/chaining.py`, `examples/24_tool_chaining.py`                           | High     | Tools Team    |
| **Example Implementation**     | `examples/`, `atlas/tests/tools/`                                                   | Medium   | Example Team  |

## Recently Completed Tasks

::: tip Completed Today (May 17, 2025) 
- ✅ Enhanced tool system with schema validation for tool execution
- ✅ Fixed tool registration in the tool agent example
- ✅ Implemented permission system with scope validation
- ✅ Updated project roadmap to prioritize core services and tool execution
- ✅ Redesigned implementation timeline for tool framework development
- ✅ Created core services implementation plan with buffer and event systems as focus
:::