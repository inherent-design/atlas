---

title: Proposed Project

---


# Proposed Project Structure

::: tip CURRENT STRUCTURE
This document outlines the current Atlas project structure as of May 16, 2025. The structure has been updated to reflect the NERV documentation port, V0/V1/V2 architecture organization, and the planned Textual CLI implementation.
:::

This document outlines the refined structure for the Atlas project, focusing on clean architecture, minimal dependencies, and clear component boundaries. This structure represents a clean-break approach that simplifies the codebase while ensuring all required functionality is maintained.

::: tip Core Principles
Atlas follows a **clean break philosophy** with a focus on best-in-class API design over backward compatibility. This structure prioritizes modularity, clear interfaces, and maintainable code.
:::

::: warning Current Focus (May 17-24, 2025)
We are currently focused on **Core Services Layer**, **Tool Execution Framework**, and **Tool Agent Enhancements**. Our immediate priority is implementing the foundational services that enable robust tool execution, event-driven communication, and improved state management. See the [current TODO list](./todo.md) for specific implementation tasks.
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
│   ├── controller.py                🚧  🔴  Controller agent implementation
│   ├── worker.py                    🚧  🔴  Worker agent implementation
│   └── specialized/                 🚧  🔴  Specialized agent implementations
│       ├── __init__.py              ✅  🔴  Module initialization
│       ├── task_aware.py            ✅  🔴  Task-aware agent implementation
│       └── tool_agent.py            🚧  🔴  Tool-using agent implementation
├── cli/                             🚧  🔴  Command-line interface
│   ├── __init__.py                  ✅  🔴  Module initialization
│   ├── config.py                    ✅  🔴  CLI configuration utilities
│   ├── parser.py                    🚧  🔴  Command-line argument parsing (needs Textual support)
│   ├── utils.py                     🔲  🔴  Utility functions from common.py
│   ├── formatting.py                🔲  🔴  Text formatting utilities from common.py
│   └── textual/                     🔲  🔴  Textual CLI implementation (planned)
│       ├── __init__.py              🔲  🔴  Module initialization
│       ├── app.py                   🔲  🔴  Main Textual application
│       ├── schema.py                🔲  🔴  Command and configuration schemas
│       ├── commands.py              🔲  🔴  Command execution system
│       ├── config.py                🔲  🔴  Configuration management
│       ├── serialization.py         🔲  🔴  Serialization utilities
│       ├── history.py               🔲  🔴  Command history management
│       ├── flags.py                 🔲  🔴  CLI flags mapping
│       ├── import_export.py         🔲  🔴  Configuration import/export
│       ├── utils/                   🔲  🔴  Utility functions
│       │   ├── __init__.py          🔲  🔴  Module initialization
│       │   ├── markdown.py          🔲  🔴  Markdown rendering
│       │   ├── color.py             🔲  🔴  Color utilities
│       │   ├── formatting.py        🔲  🔴  Text formatting utilities
│       │   └── streaming.py         🔲  🔴  Streaming utilities
│       ├── widgets/                 🔲  🔴  UI components
│       │   ├── __init__.py          🔲  🔴  Module initialization
│       │   ├── command_bar.py       🔲  🔴  Command input widget
│       │   ├── conversation.py      🔲  🔴  Conversation display
│       │   ├── status.py            🔲  🔴  Status display
│       │   ├── context.py           🔲  🔴  Context information panel
│       │   ├── directory_browser.py 🔲  🔴  Directory selection browser
│       │   ├── file_browser.py      🔲  🔴  File selection browser
│       │   ├── provider_selector.py 🔲  🔴  Provider selection widget
│       │   ├── stream_controls.py   🔲  🔴  Stream control buttons
│       │   └── tool_list.py         🔲  🔴  Tool listing and management widget
│       ├── screens/                 🔲  🔴  Screen implementations
│       │   ├── __init__.py          🔲  🔴  Module initialization
│       │   ├── main.py              🔲  🔴  Main application screen
│       │   ├── provider.py          🔲  🔴  Provider selection screen
│       │   ├── ingest.py            🔲  🔴  Document ingestion screen
│       │   ├── tools.py             🔲  🔴  Tool management screen
│       │   └── settings.py          🔲  🔴  Settings management screen
│       └── commands/                🔲  🔴  Command implementations
│           ├── __init__.py          🔲  🔴  Module initialization
│           ├── base.py              🔲  🔴  Base command class
│           ├── query.py             🔲  🔴  Query command
│           ├── ingest.py            🔲  🔴  Ingest command
│           ├── tool.py              🔲  🔴  Tool command
│           └── controller.py        🔲  🔴  Controller command
├── core/                            ✅  🔴  Core utilities and configuration
│   ├── __init__.py                  ✅  🔴  Module initialization
│   ├── config.py                    ✅  🔴  Configuration management
│   ├── env.py                       ✅  🔴  Environment variable handling
│   ├── errors.py                    ✅  🔴  Error handling system
│   ├── logging.py                   ✅  🔴  Logging configuration
│   ├── prompts.py                   ✅  🔴  System prompt management
│   ├── retry.py                     ✅  🔴  Retry mechanisms
│   ├── telemetry.py                 ✅  🔴  Telemetry and metrics
│   ├── types.py                     🚧  🔴  Type definitions
│   ├── services/                    🔲  🔴  Service architecture components
│   │   ├── __init__.py              🔲  🔴  Module initialization
│   │   ├── base.py                  🔲  🔴  Base service interfaces
│   │   ├── buffer.py                🔲  🔴  Thread-safe buffer implementations
│   │   ├── events.py                🔲  🔴  Event system implementation
│   │   ├── state.py                 🔲  🔴  State management utilities
│   │   ├── commands.py              🔲  🔴  Command pattern implementation
│   │   ├── boundaries.py            🔲  🔴  System boundary interfaces
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
│   ├── hybrid_search.py             ✅  🔴  Hybrid semantic+keyword search
│   ├── reranking.py                 🔲  🟠  Result reranking strategies
│   ├── search_scoring.py            🔲  🟠  Configurable relevance scoring
│   └── settings.py                  ✅  🔴  Retrieval settings configuration
├── providers/                       ✅  🔴  Model provider system
│   ├── __init__.py                  ✅  🔴  Module initialization and exports
│   ├── base.py                      ✅  🔴  Core provider interface only
│   ├── messages.py                  ✅  🔴  Message and request modeling
│   ├── errors.py                    ✅  🔴  Provider-specific error classes
│   ├── reliability.py               ✅  🔴  Retry and circuit breaker
│   ├── helpers.py                   🔲  🔴  Provider creation utilities from common.py
│   ├── streaming/                   ✅  🔴  Enhanced streaming infrastructure
│   │   ├── __init__.py              ✅  🔴  Module initialization
│   │   ├── base.py                  ✅  🔴  Base streaming interfaces
│   │   ├── control.py               ✅  🔴  Stream control implementation
│   │   └── buffer.py                ✅  🔴  Stream buffer management
│   ├── implementations/             ✅  🔴  Provider implementations
│   │   ├── __init__.py              ✅  🔴  Module initialization
│   │   ├── anthropic.py             ✅  🔴  Anthropic provider
│   │   ├── openai.py                ✅  🔴  OpenAI provider
│   │   ├── ollama.py                ✅  🔴  Ollama provider
│   │   └── mock.py                  ✅  🔴  Mock provider for testing
│   ├── group.py                     ✅  🔴  Provider group implementation
│   ├── registry.py                  ✅  🔴  Provider registry
│   ├── factory.py                   ✅  🔴  Provider factory
│   ├── resolver.py                  ✅  🔴  Provider auto-resolution
│   ├── capabilities.py              ✅  🔴  Provider capabilities
│   ├── options.py                   ✅  🔴  Provider options and configuration
│   └── validation.py                ✅  🔴  Schema-based validation utilities
├── query.py                         ✅  🔴  Query client interface
├── schemas/                         🚧  🔴  Schema-based validation and types
│   ├── __init__.py                  ✅  🔴  Module initialization
│   ├── base.py                      ✅  🔴  Base schema definitions and utilities
│   ├── messages.py                  ✅  🔴  Message schema definitions
│   ├── providers.py                 ✅  🔴  Provider schema definitions
│   ├── options.py                   ✅  🔴  Options and capabilities schemas
│   ├── config.py                    ✅  🔴  Configuration schemas
│   ├── types.py                     ✅  🔴  Schema-compatible type annotations
│   ├── agents.py                    🔲  🔴  Agent schema definitions
│   ├── knowledge.py                 🔲  🔴  Knowledge system schemas
│   ├── tools.py                     ✅  🔴  Tool schema definitions with validation
│   ├── cli.py                       🔲  🔴  CLI command and configuration schemas
│   └── validation.py                🔲  🔴  Validation utilities and decorators
├── tools/                           🚧  🔴  Tools system
│   ├── __init__.py                  ✅  🔴  Module initialization
│   ├── base.py                      ✅  🔴  Base tool interface with enhanced validation
│   ├── registry.py                  ✅  🔴  Tool registry and discovery
│   ├── execution.py                 🔲  🔴  Tool execution framework
│   ├── results.py                   🔲  🔴  Tool result processing
│   ├── chaining.py                  🔲  🔴  Tool chaining and composition
│   ├── standard/                    🚧  🔴  Standard built-in tools
│   │   ├── __init__.py              ✅  🔴  Module initialization
│   │   ├── knowledge_tools.py       🔲  🔴  Knowledge management tools
│   │   │   ├── RetrievalTool        🔲  🔴  Retrieval tool for knowledge base
│   │   │   ├── IngestTool           🔲  🔴  Document ingestion tool
│   │   │   ├── FilteringTool        🔲  🔴  Metadata filtering tool
│   │   │   └── SearchTool           🔲  🔴  Combined hybrid search tool
│   │   └── system.py                🔲  🔴  System interaction tools
│   │       ├── FileTool             🔲  🔴  File system interaction
│   │       ├── CommandTool          🔲  🔴  Command execution
│   │       └── EnvironmentTool      🔲  🔴  Environment variable access
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

## New Example Structure

```
examples/
├── 01_query_simple.py               ✅  🔴  Basic query 
├── 02_query_streaming.py            ✅  🔴  Streaming query
├── 03_provider_selection.py         ✅  🔴  Provider selection and options
├── 04_provider_group.py             ✅  🔴  Provider group with fallback
├── 05_agent_options_verification.py ✅  🔴  Agent options verification 
├── 06_task_aware_providers.py       ✅  🔴  Task-aware provider selection
├── 07_task_aware_agent.py           ✅  🔴  Task-aware agent implementation
├── 08_multi_agent_providers.py      ✅  🔴  Multi-agent provider example
├── 10_document_ingestion.py         ✅  🔴  Document ingestion
├── 11_basic_retrieval.py            ✅  🔴  Basic retrieval
├── 12_hybrid_retrieval.py           ✅  🔴  Hybrid retrieval
├── 15_advanced_filtering.py         ✅  🔴  Advanced metadata and content filtering
├── 16_schema_validation.py          ✅  🔴  Schema-based validation examples
├── 20_tool_agent.py                 ✅  🔴  Tool agent usage with enhanced permissions
├── 23_knowledge_tools.py            🔲  🔴  Knowledge tools implementation (planned)
├── 24_tool_chaining.py              🔲  🔴  Tool chaining and composition (planned)
├── 25_cli_commands.py               🔲  🔴  Command execution example (planned)
├── 26_cli_config.py                 🔲  🔴  Configuration example (planned)
├── 27_cli_batch.py                  🔲  🔴  Batch command example (planned)
├── 28_custom_tool_development.py    🔲  🔴  Custom tool example (planned)
├── common.py                        ✅  🔴  Shared utilities for examples (to be migrated)
├── EXAMPLES.md                      ✅  🔴  Example implementation standards
└── README.md                        ✅  🔴  Examples guide
```

## Key Simplifications and Enhancements

### Core Functionality (MVP) 🔴

#### 1. Textual CLI Implementation
- Design and implement serializable command schema
- Create command execution system with history
- Build UI components for different modes
- Implement dual-mode entry points (interactive and flags)
- Add configuration management with import/export
- Migrate utilities from common.py to appropriate modules

#### 2. Tool Agent Implementation
- Fix tool agent registration in examples (current focus)
- Enhance tool registry with proper permissions handling
- Improve tool discovery and initialization
- Add schema validation for tool execution
- Create knowledge tools integration
- Implement automatic tool granting to worker agents

#### 3. Core Services Layer
- Define boundary interfaces for system components
- Implement event system with subscription
- Create buffer system with thread-safety
- Add state management with versioning
- Develop resource lifecycle management

#### 4. Integration and Utilities
- Port common.py utilities to appropriate modules
- Enhance error handling and formatting
- Create reusable UI components
- Implement streaming display with controls
- Add session management and persistence

## Textual CLI Architecture

### Command Schema Design

The new CLI architecture is based on serializable commands and configurations that can be used in both interactive UI and command-line flag mode.

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from marshmallow import Schema, fields, validate, validates_schema, ValidationError

from atlas.schemas.base import BaseSchema
from atlas.providers.options import ProviderOptionsSchema


class ExecutionConfigSchema(BaseSchema):
    """Schema for base execution configuration."""
    mode = fields.Str(required=True, validate=validate.OneOf([
        "query", "ingest", "controller", "worker", "tool"
    ]))
    provider = fields.Nested(ProviderOptionsSchema)
    collection = fields.Str(default="atlas_knowledge_base")
    db_path = fields.Str(allow_none=True)
    system_prompt_file = fields.Str(allow_none=True)


class QueryConfigSchema(ExecutionConfigSchema):
    """Schema for query mode configuration."""
    mode = fields.Str(default="query", validate=validate.Equal("query"))
    query = fields.Str(allow_none=True)
    with_context = fields.Bool(default=True)
    stream = fields.Bool(default=False)
    include_sources = fields.Bool(default=True)
    
    
class CommandSchema(BaseSchema):
    """Schema for commands."""
    command_id = fields.Str(required=True)
    command_type = fields.Str(required=True)
    config = fields.Nested(ExecutionConfigSchema)
    timestamp = fields.DateTime()
    
    @validates_schema
    def validate_config_type(self, data, **kwargs):
        """Validate that config matches command_type."""
        command_type = data.get("command_type")
        config = data.get("config")
        if command_type == "query" and config.get("mode") != "query":
            raise ValidationError("Query command must have query config")


@dataclass
class ExecutionConfig:
    """Base configuration for all execution modes."""
    mode: str  # "query", "ingest", "controller", "worker", "tool"
    provider: Dict[str, Any]
    collection: str = "atlas_knowledge_base"
    db_path: Optional[str] = None
    system_prompt_file: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "mode": self.mode,
            "provider": self.provider,
            "collection": self.collection,
            "db_path": self.db_path,
            "system_prompt_file": self.system_prompt_file
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionConfig":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class QueryConfig(ExecutionConfig):
    """Configuration for query mode."""
    mode: str = "query"
    query: Optional[str] = None
    with_context: bool = True
    stream: bool = False
    include_sources: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        base_dict = super().to_dict()
        base_dict.update({
            "query": self.query,
            "with_context": self.with_context,
            "stream": self.stream,
            "include_sources": self.include_sources
        })
        return base_dict


@dataclass
class Command:
    """Base class for all commands."""
    command_id: str
    command_type: str
    config: ExecutionConfig
    timestamp: Optional[str] = None
    
    def execute(self) -> Dict[str, Any]:
        """Execute the command and return the result."""
        raise NotImplementedError
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "command_id": self.command_id,
            "command_type": self.command_type,
            "config": self.config.to_dict(),
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Command":
        """Create from dictionary."""
        config_data = data.get("config", {})
        mode = config_data.get("mode")
        
        if mode == "query":
            config = QueryConfig.from_dict(config_data)
        else:
            config = ExecutionConfig.from_dict(config_data)
            
        return cls(
            command_id=data["command_id"],
            command_type=data["command_type"],
            config=config,
            timestamp=data.get("timestamp")
        )


@dataclass
class CommandResult:
    """Result of command execution."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    command_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "command_id": self.command_id
        }
```

### UI Component Architecture

The UI follows a hierarchical design with screens, panels, and widgets:

```python
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Input, Static, Button
from textual.reactive import reactive
from textual.screen import Screen
from textual import events
from datetime import datetime
import uuid

from atlas.cli.textual.commands import Command, CommandResult
from atlas.cli.textual.config import ConfigurationManager


class CommandBar(Container):
    """Command input widget with completion and history."""
    
    def __init__(self, history=None):
        """Initialize command bar with history."""
        super().__init__()
        self.history = history or []
        self.history_index = len(self.history)
        
    def compose(self) -> ComposeResult:
        """Compose the command bar widget."""
        with Horizontal():
            yield Input(placeholder="Enter command...", id="command-input")
            yield Button("Send", id="send-button")
            
    def on_button_pressed(self, event: events.Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "send-button":
            self.submit_command()
            
    def on_input_submitted(self, event: events.Input.Submitted) -> None:
        """Handle input submission."""
        self.submit_command()
        
    def submit_command(self) -> None:
        """Submit the current command."""
        command_text = self.query_one("#command-input").value
        if not command_text:
            return
            
        # Add to history and reset index
        self.history.append(command_text)
        self.history_index = len(self.history)
        
        # Clear input
        self.query_one("#command-input").value = ""
        
        # Post message to handle command
        self.post_message(CommandSubmitted(command_text))
        

class ConversationDisplay(Container):
    """Widget for displaying conversation messages."""
    
    def __init__(self):
        """Initialize conversation display."""
        super().__init__()
        self.messages = []
        
    def compose(self) -> ComposeResult:
        """Compose the conversation display widget."""
        yield Static(id="conversation-content")
        
    def add_message(self, message: str, is_user: bool = False) -> None:
        """Add a message to the conversation."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        sender = "User" if is_user else "Atlas"
        message_html = f"<{timestamp}> [{sender}]: {message}\n"
        
        self.messages.append((message, is_user, timestamp))
        
        # Update display
        content = self.query_one("#conversation-content")
        current = content.render()
        content.update(current + message_html)
        
    def add_stream_chunk(self, chunk: str) -> None:
        """Add a streaming chunk to the last message."""
        if not self.messages:
            # No message to append to, create new one
            self.add_message(chunk)
            return
            
        # Append to the last message
        last_message, is_user, timestamp = self.messages[-1]
        if is_user:
            # Last message was from user, create new one
            self.add_message(chunk)
            return
            
        # Update last message
        self.messages[-1] = (last_message + chunk, is_user, timestamp)
        
        # Update display
        content = self.query_one("#conversation-content")
        current = content.render().rsplit("\n", 2)[0]
        message_html = f"<{timestamp}> [Atlas]: {last_message + chunk}\n"
        content.update(current + message_html)


class StreamControls(Container):
    """Controls for streaming operations."""
    
    def compose(self) -> ComposeResult:
        """Compose the stream controls widget."""
        with Horizontal():
            yield Button("Pause", id="stream-pause")
            yield Button("Resume", id="stream-resume", disabled=True)
            yield Button("Cancel", id="stream-cancel")
            
    def on_button_pressed(self, event: events.Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        
        if button_id == "stream-pause":
            self.post_message(StreamPaused())
            self.query_one("#stream-pause").disabled = True
            self.query_one("#stream-resume").disabled = False
            
        elif button_id == "stream-resume":
            self.post_message(StreamResumed())
            self.query_one("#stream-pause").disabled = False
            self.query_one("#stream-resume").disabled = True
            
        elif button_id == "stream-cancel":
            self.post_message(StreamCancelled())
            

class MainScreen(Screen):
    """Main application screen with command bar and conversation display."""
    
    def compose(self) -> ComposeResult:
        """Compose the main screen."""
        yield Header()
        with Container(id="main-container"):
            with Horizontal(id="content-area"):
                with Vertical(id="conversation-column"):
                    yield ConversationDisplay()
                    yield StreamControls()
                with Vertical(id="context-column"):
                    yield Static("Context Information", id="context-header")
                    yield Static("", id="context-content")
            with Horizontal(id="input-area"):
                yield CommandBar()
        yield Footer()
        
    def on_mount(self) -> None:
        """Handle screen mounting."""
        self.title = "Atlas CLI"
        
    def handle_command(self, command_text: str) -> None:
        """Handle a submitted command."""
        # Add to conversation
        conversation = self.query_one(ConversationDisplay)
        conversation.add_message(command_text, is_user=True)
        
        # Parse and execute command
        # (This would call the command execution system)
        
        
class AtlasApp(App):
    """Main Atlas Textual application."""
    CSS_PATH = "atlas.css"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("h", "help", "Help"),
        ("c", "command", "Command Mode"),
    ]
    
    def __init__(self):
        """Initialize the application."""
        super().__init__()
        self.config_manager = ConfigurationManager()
        self.command_executor = CommandExecutor()
        
    def on_mount(self):
        """Handle application mounting."""
        self.push_screen("main")
```

### Command Execution System

The command execution system provides a clear flow from user input to execution and result presentation:

```python
import uuid
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from atlas.cli.textual.schema import Command, CommandResult


class CommandExecutor:
    """Executes commands with proper context and error handling."""
    
    def __init__(self):
        """Initialize command executor."""
        self.history = CommandHistory()
        self.logger = logging.getLogger(__name__)
        
    def execute_command(self, command: Command) -> CommandResult:
        """Execute a command and return the result."""
        try:
            # Pre-execution validation
            self.validate_command(command)
            
            # Log command execution
            self.logger.info(f"Executing command: {command.command_type}")
            
            # Command execution
            result = command.execute()
            
            # Create result object
            command_result = CommandResult(
                success=True,
                data=result,
                command_id=command.command_id
            )
            
            # Post-execution actions
            self.record_history(command, command_result)
            
            return command_result
        except Exception as e:
            # Log error
            self.logger.error(f"Error executing command: {e}")
            
            # Create error result
            error_result = CommandResult(
                success=False,
                error=str(e),
                command_id=command.command_id
            )
            
            # Record in history
            self.record_history(command, error_result)
            
            return error_result
            
    def validate_command(self, command: Command) -> None:
        """Validate command before execution."""
        # Perform schema validation
        schema = get_schema_for_command(command)
        schema.load(command.to_dict())
        
    def record_history(self, command: Command, result: CommandResult) -> None:
        """Record command and result in history."""
        self.history.add_entry(command, result)
        
    def create_command(self, command_type: str, config: Dict[str, Any]) -> Command:
        """Create a command from type and config."""
        command_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        return Command(
            command_id=command_id,
            command_type=command_type,
            config=config,
            timestamp=timestamp
        )


class CommandHistory:
    """Manages command execution history."""
    
    def __init__(self, max_entries: int = 100):
        """Initialize command history."""
        self.max_entries = max_entries
        self.entries: List[Dict[str, Any]] = []
        
    def add_entry(self, command: Command, result: CommandResult) -> None:
        """Add command and result to history."""
        entry = {
            "command": command.to_dict(),
            "result": result.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
        
        self.entries.append(entry)
        
        # Trim history if needed
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]
            
    def get_last_n_entries(self, n: int) -> List[Dict[str, Any]]:
        """Get the last N entries from history."""
        return self.entries[-n:]
        
    def save_to_file(self, filename: str) -> None:
        """Save history to file."""
        with open(filename, "w") as f:
            json.dump(self.entries, f, indent=2)
            
    def load_from_file(self, filename: str) -> None:
        """Load history from file."""
        try:
            with open(filename, "r") as f:
                data = json.load(f)
                # Validate entries
                if not isinstance(data, list):
                    raise ValueError("Invalid history format")
                self.entries = data
        except Exception as e:
            logging.error(f"Error loading history: {e}")


class ConfigurationManager:
    """Manages configuration storage, loading, and validation."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration manager."""
        self.config_dir = config_dir or os.path.expanduser("~/.atlas")
        self.logger = logging.getLogger(__name__)
        
        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)
        
    def save_config(self, name: str, config: Dict[str, Any]) -> None:
        """Save a configuration to file."""
        filepath = os.path.join(self.config_dir, f"{name}.json")
        
        try:
            with open(filepath, "w") as f:
                json.dump(config, f, indent=2)
            self.logger.info(f"Configuration saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            raise
            
    def load_config(self, name: str) -> Dict[str, Any]:
        """Load a configuration from file."""
        filepath = os.path.join(self.config_dir, f"{name}.json")
        
        try:
            with open(filepath, "r") as f:
                config = json.load(f)
            self.logger.info(f"Configuration loaded from {filepath}")
            return config
        except FileNotFoundError:
            self.logger.warning(f"Configuration file not found: {filepath}")
            return {}
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            raise
            
    def list_configs(self) -> List[str]:
        """List available configurations."""
        try:
            files = os.listdir(self.config_dir)
            return [f[:-5] for f in files if f.endswith(".json")]
        except Exception as e:
            self.logger.error(f"Error listing configurations: {e}")
            return []
```

### Command Integration with CLI Flags

The new CLI will support both interactive mode and traditional flag-based execution:

```python
import argparse
import sys
from typing import Dict, Any, Optional
import uuid
from datetime import datetime

from atlas.cli.textual.schema import Command, QueryConfig
from atlas.cli.textual.commands import CommandExecutor


def create_parser() -> argparse.ArgumentParser:
    """Create the main CLI parser with textual support."""
    parser = argparse.ArgumentParser(description="Atlas CLI")
    
    # Add textual flag
    parser.add_argument(
        "--textual",
        action="store_true",
        help="Launch the Textual UI"
    )
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Run a query")
    query_parser.add_argument("-q", "--query", help="Query text")
    query_parser.add_argument("--no-context", action="store_true", help="Disable context")
    query_parser.add_argument("--stream", action="store_true", help="Enable streaming")
    
    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents")
    ingest_parser.add_argument("-d", "--directory", help="Directory to ingest")
    
    # Tool command
    tool_parser = subparsers.add_parser("tool", help="Execute a tool")
    tool_parser.add_argument("--name", help="Tool name")
    tool_parser.add_argument("--args", help="Tool arguments as JSON")
    
    # Add common arguments to all subparsers
    for subparser in [query_parser, ingest_parser, tool_parser]:
        subparser.add_argument("--provider", help="Provider name")
        subparser.add_argument("--model", help="Model name")
        subparser.add_argument("--collection", help="Collection name")
        subparser.add_argument("--db-path", help="Database path")
    
    return parser


def convert_args_to_command(args: argparse.Namespace) -> Optional[Command]:
    """Convert command line arguments to Command object."""
    command_type = args.command
    
    if not command_type:
        return None
        
    # Create base config with common args
    base_config = {
        "provider": {
            "provider_name": args.provider if hasattr(args, "provider") and args.provider else None,
            "model_name": args.model if hasattr(args, "model") and args.model else None
        },
        "collection": args.collection if hasattr(args, "collection") and args.collection else "atlas_knowledge_base",
        "db_path": args.db_path if hasattr(args, "db_path") and args.db_path else None
    }
    
    # Create command-specific config
    if command_type == "query":
        config = QueryConfig(
            mode="query",
            provider=base_config["provider"],
            collection=base_config["collection"],
            db_path=base_config["db_path"],
            query=args.query if hasattr(args, "query") else None,
            with_context=not args.no_context if hasattr(args, "no_context") else True,
            stream=args.stream if hasattr(args, "stream") else False
        )
    elif command_type == "ingest":
        # Create IngestConfig
        config = IngestConfig(
            mode="ingest",
            provider=base_config["provider"],
            collection=base_config["collection"],
            db_path=base_config["db_path"],
            directory=args.directory if hasattr(args, "directory") else None
        )
    elif command_type == "tool":
        # Create ToolConfig
        config = ToolConfig(
            mode="tool",
            provider=base_config["provider"],
            collection=base_config["collection"],
            db_path=base_config["db_path"],
            tool_name=args.name if hasattr(args, "name") else None,
            tool_args=json.loads(args.args) if hasattr(args, "args") and args.args else {}
        )
    else:
        return None
        
    # Create command
    return Command(
        command_id=str(uuid.uuid4()),
        command_type=command_type,
        config=config,
        timestamp=datetime.now().isoformat()
    )


def run_cli():
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Check if textual UI was requested
    if args.textual:
        from atlas.cli.textual.app import AtlasApp
        app = AtlasApp()
        app.run()
        return
        
    # Handle regular CLI command
    command = convert_args_to_command(args)
    
    if not command:
        parser.print_help()
        return
        
    # Execute command
    executor = CommandExecutor()
    result = executor.execute_command(command)
    
    # Print result
    if result.success:
        print(json.dumps(result.data, indent=2))
    else:
        print(f"Error: {result.error}", file=sys.stderr)
```

## Implementation Roadmap

::: timeline Core Services Layer
- **May 17-20, 2025**
- Create core services module foundation
- Implement event system with subscription management
- Develop thread-safe buffer implementations
- Add state management with versioning
- Create resource lifecycle management
:::

::: timeline Tool Execution Framework
- **May 20-22, 2025**
- Create standardized tool execution pipeline
- Implement tool result processing and validation
- Add execution metrics and telemetry
- Create hooks for pre/post execution processing
- Implement comprehensive error handling
:::

::: timeline Knowledge Tools Integration
- **May 22-24, 2025**
- Implement RetrievalTool for knowledge base searches
- Create IngestTool for document processing
- Add FilteringTool for metadata filtering
- Design SearchTool for combined hybrid search
- Integrate knowledge tools with agent system
:::

::: timeline Tool Chaining Implementation
- **May 24-26, 2025**
- Create tool chain builder interface
- Implement sequential tool execution
- Add parallel tool execution with result merging
- Design conditional execution based on tool results
- Implement result transformation between tools
:::