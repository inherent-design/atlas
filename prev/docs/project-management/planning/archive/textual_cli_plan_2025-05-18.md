---
title: Textual CLI
---

# Textual CLI Implementation Plan - May 18, 2025

This document outlines the approach for implementing a rich terminal user interface for Atlas using the Textual framework, focusing on a pragmatic, user-oriented flow.

## Core Design Philosophy

The Atlas Textual CLI will follow a form-like flow structure prioritizing user experience and organic interactions. The design emphasizes:

1. **Progressive Disclosure**: Guide users through configuration options step-by-step
2. **Mode-Based Operation**: Clear paths for one-shot queries, knowledge operations, and continuous chat
3. **Direct Manipulation**: Simple, intuitive controls for common operations
4. **Extensibility**: Framework for later integration of advanced features

## Flow Structure

### 1. Launch & Welcome

**Primary Screen: WelcomeScreen**
- Atlas logo/header with version information
- Mode selection presented as clear options:
  - Query Mode (one-shot LLM interactions)
  - Knowledge Mode (ingestion, retrieval, management)
  - Chat Mode (continuous conversation)
- Quick access to recent configurations
- Keyboard shortcuts for power users

### 2. Configure & Select

**Provider Configuration Screens**
- Provider selection (Anthropic, OpenAI, Ollama, Mock)
- Model selection based on chosen provider
- Configuration options specific to selected mode
- Capability-based provider selection alternative

**Mode-Specific Configuration**
- Query: Parameters for one-shot operation
- Knowledge: Collection selection, chunking options
- Chat: System prompt, conversation memory settings

### 3. Execution Screens

**Query Execution (One-shot Mode)**
- Input area for query text
- Results displayed with formatting
- Provider and model information
- Usage statistics and cost estimates
- Option to save results or switch modes

**Knowledge Operations**
- File/directory selection for ingestion
- Retrieval interface with filtering options
- Collection management tools
- Progress indicators for long-running operations

**Chat Interface (Continuous Mode)**
- Conversation history with proper formatting
- Input area with command support
- Streaming output with pause/resume controls
- Session management (save, load, export)

## Implementation Strategy

### Phase 1: Minimal Viable UI (Target: May 20, 2025)

Focus on creating a functional UI with direct component interactions:

1. **Application Structure**
   - Main Textual app with screen management
   - Basic UI layout with consistent design
   - Direct function calls between components

2. **Core Screens**
   - WelcomeScreen with mode selection
   - ProviderScreen for provider/model selection
   - QueryScreen for basic query execution
   - ChatScreen for conversation mode

3. **Essential Widgets**
   - ConversationView for message display
   - CommandBar for input handling
   - ProviderSelector for model selection
   - StatusBar for state information

### Phase 2: Enhanced Functionality (Target: May 22, 2025)

Build on the foundation with more sophisticated features:

1. **Knowledge Integration**
   - Document browser for ingestion
   - Collection manager for knowledge base
   - Retrieval interface with filtering

2. **Advanced Conversation**
   - Streaming with visual indicators
   - Pause/resume/cancel controls
   - Token counting and cost estimation
   - Command history and autocompletion

3. **Configuration Management**
   - Save/load configurations
   - Preference management
   - Environment variable integration

### Phase 3: Polish & Extensions (Target: May 24, 2025)

Add polish and prepare for future extensions:

1. **UI Refinements**
   - Keyboard shortcuts for all operations
   - Theme customization
   - Responsive layout adjustments

2. **Tool Integration**
   - Basic tool panel for available tools
   - Command shortcuts for tool invocation
   - Tool result visualization
   - Permission management interface

3. **Event System Hooks**
   - Prepare abstraction points for future event bus
   - Document interaction patterns
   - Create clean component boundaries

## Tool Integration Approach

### Command-Based Tool Invocation

Implement a lightweight command system for tool invocation:

1. **Command Format**: `/tool_name [params]`
2. **Auto-completion**: Tab completion for tool names and parameters
3. **Parameter Prompting**: Interactive parameter collection after command
4. **Result Display**: Specialized rendering for different result types

### Tool UI Components

1. **Tool Panel**: Sidebar or bottom panel showing available tools
2. **Tool Configuration**: Simple settings for each tool
3. **Tool History**: Track recently used tools and parameters
4. **Favorites**: Allow marking frequently used tools as favorites

## Directory Structure

```
atlas/
├── cli/
│   ├── __init__.py
│   ├── config.py            # Configuration utilities
│   ├── parser.py            # Command-line argument parsing
│   └── textual/             # Textual CLI components
│       ├── __init__.py
│       ├── app.py           # Main application class
│       ├── commands.py      # Command execution system
│       ├── config.py        # Configuration management
│       ├── screens/         # Screen implementations
│       │   ├── __init__.py
│       │   ├── welcome.py   # Welcome/mode selection screen
│       │   ├── provider.py  # Provider selection screen
│       │   ├── query.py     # Query execution screen
│       │   ├── chat.py      # Chat interface screen
│       │   ├── knowledge.py # Knowledge operations screen
│       │   └── tools.py     # Tool management screen
│       ├── widgets/         # Custom widget components
│       │   ├── __init__.py
│       │   ├── command_bar.py    # Command input bar
│       │   ├── conversation.py   # Message display area
│       │   ├── provider_selector.py # Provider selection
│       │   ├── status_bar.py     # Status information
│       │   └── stream_controls.py # Streaming control widgets
│       └── styles/          # CSS styles for the application
│           ├── __init__.py
│           └── atlas.css    # Main application styles
```

## Key Components

### Main Application

```python
# atlas/cli/textual/app.py
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from atlas.cli.textual.screens.welcome import WelcomeScreen

class AtlasApp(App):
    """Atlas Textual TUI application."""

    CSS_PATH = "styles/atlas.css"
    TITLE = "Atlas Framework"
    SUB_TITLE = "Advanced Multi-Modal Agent System"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield self.current_screen  # Initially WelcomeScreen
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app when mounted."""
        # Load configuration
        self.load_config()
        # Show welcome screen
        self.push_screen(WelcomeScreen())
```

### Conversation View

```python
# atlas/cli/textual/widgets/conversation.py
from textual.widgets import RichLog
from textual.reactive import reactive
from rich.markdown import Markdown
from rich.text import Text

class ConversationView(RichLog):
    """Widget for displaying conversations."""

    def __init__(self, *args, **kwargs):
        """Initialize the conversation view."""
        super().__init__(*args, **kwargs)
        self.messages = []

    def add_user_message(self, text):
        """Add a user message to the conversation."""
        self.messages.append({"role": "user", "content": text})

        # Format and display the message
        user_text = Text(f"You: {text}")
        user_text.stylize("bold magenta")
        self.write(user_text)
        self.write("")  # Add blank line
```

### Command Bar

```python
# atlas/cli/textual/widgets/command_bar.py
from textual.widgets import Input
from textual.reactive import reactive

class CommandBar(Input):
    """Command input bar with history and auto-completion."""

    def __init__(self, *args, **kwargs):
        """Initialize the command bar."""
        super().__init__(*args, **kwargs)
        self.history = []
        self.history_position = 0

    def on_key(self, event):
        """Handle key events for history navigation."""
        if event.key == "up":
            self.navigate_history(-1)
            event.prevent_default()
        elif event.key == "down":
            self.navigate_history(1)
            event.prevent_default()
        elif event.key == "tab":
            self.auto_complete()
            event.prevent_default()
```

## Implementation Priorities

1. **First Priority**: Functional UI with basic query flow
   - Welcome screen → Provider selection → Query execution
   - Direct function calls between components
   - Simple but working implementation
   - ✅ Fixed Select widget initialization for proper value handling

2. **Second Priority**: Add continuous conversation mode
   - Chat interface with history
   - Basic streaming support
   - Session persistence

3. **Third Priority**: Knowledge operations
   - Document ingestion interface
   - Retrieval with basic filtering
   - Collection management

4. **Fourth Priority**: Tool integration
   - Command-based tool invocation
   - Tool result visualization
   - Basic permission management

5. **Final Priority**: Polish and prepare for future event bus
   - Clean component boundaries
   - Documentation of interaction patterns
   - Hooks for future event system

## Future Extensions

While focusing on getting a working UI first, we will design with these future extensions in mind:

1. **Event Bus Integration**
   - UI components will publish events and subscribe to responses
   - Business logic will subscribe to commands and publish results
   - Cleaner separation of concerns

2. **Advanced Agent Integration**
   - Multi-agent workflow visualization
   - Agent task delegation interface
   - Workflow orchestration controls

3. **Advanced Knowledge Management**
   - Knowledge graph visualization
   - Advanced metadata filtering
   - Document relationship management

4. **Enterprise Features**
   - User management and permissions
   - Audit logging and compliance tools
   - Advanced configuration management

## Success Criteria

1. **Functional**: All core operations (query, knowledge, chat) work correctly
2. **Usable**: Interface is intuitive and responsive
3. **Reliable**: Error handling is comprehensive and informative
4. **Extendable**: Framework allows for future enhancements
5. **Documented**: Code and usage are well-documented
6. **Tested**: Components have unit tests with IsolatedAsyncioTestCase

### Testing Strategy

We've implemented a comprehensive testing strategy for Textual UI components:

1. **Unit Testing**: Using Python's unittest framework with IsolatedAsyncioTestCase for async components
2. **Component Isolation**: Testing UI components in isolation with appropriate mocks
3. **Headless Testing**: Using Textual's run_test() method for testing UI components without a visible terminal
4. **Event Verification**: Testing event handling and message passing between components
5. **Mock Provider Registry**: Using mock providers and models for testing the provider selection components

## Timeline

| Date         | Milestone              | Deliverables                                             |
| ------------ | ---------------------- | -------------------------------------------------------- |
| May 20, 2025 | Basic Structure        | App, screen flow, welcome and provider screens           |
| May 21, 2025 | Query & Chat           | Command bar, conversation view, basic query execution    |
| May 22, 2025 | Knowledge Operations   | File browser, collection management, retrieval interface |
| May 23, 2025 | Tool Integration       | Command system, tool panel, result visualization         |
| May 24, 2025 | Polish & Documentation | Keyboard shortcuts, help system, documentation           |

## Conclusion

This implementation plan provides a pragmatic approach to creating a rich terminal interface for Atlas using Textual. By focusing first on a working UI with direct component interactions, we will deliver value quickly while establishing a foundation that can later evolve to include a more sophisticated event-based architecture.

The form-like flow structure ensures an intuitive user experience, while the modular design allows for future extensions and enhancements. This approach balances immediate functionality with long-term architectural goals.
