# Atlas Development Guidelines for Claude Code

This file contains essential instructions and guidelines for Claude Code when working on the Atlas project. These instructions serve as a reference for both human developers and Claude to ensure consistent development practices.

## Project Status 2025 Update

### Project Status

Atlas is actively under development with a focus on building a robust, enterprise-ready framework. The project emphasizes quality implementation over rushed timelines.

### Completed Milestones

- ✅ **Foundation Stabilization**: Unified agent implementations, agent registry with dynamic discovery, error handling, conditional edge routing, query-only client
- ✅ **Environment Configuration**: Centralized environment management, configuration precedence, validation logic
- ✅ **Documentation System**: Complete VitePress-based documentation with comprehensive coverage of all components, workflows, and APIs
- ✅ **Core Component Design**: Established architecture patterns, module structure, and interaction protocols
- ✅ **Robust Provider Implementation**: Added retry mechanism with exponential backoff and circuit breaker pattern
- ✅ **Enhanced Provider System**: Implemented Provider Registry with capability-based selection and ProviderGroup with fallback strategies

### Current Focus

We are currently focused on Core Services & Textual CLI Implementation:

1. **Core Services Implementation**:
   - Creating core services module foundation
   - Implementing thread-safe buffer system with flow control
   - Developing event-based communication system with subscription
   - Adding state management with versioning and transitions
   - Creating resource lifecycle management and boundaries

2. **Textual CLI Implementation**:
   - Designing serializable command schema and execution pattern
   - Implementing UI components with command bar and message display
   - Creating mode-specific screens for different functionality
   - Building command execution system with streaming support
   - Implementing configuration management and serialization

See the [current TODO list](./docs/project-management/tracking/todo.md) for specific implementation tasks.

### Next Steps

Following our [Product Roadmap](./docs/project-management/roadmap/product_roadmap.md), upcoming phases include:

1. **Tool Framework Enhancement**:
   - Implementing tool chaining for sequential and parallel execution
   - Creating result transformation capabilities between tools
   - Developing conditional execution based on tool results
   - Building knowledge-specific tool implementations
   - Creating comprehensive tool examples

2. **Knowledge System Enhancements**:
   - Implementing hybrid retrieval combining semantic and keyword search
   - Enhancing document chunking strategies with semantic boundaries
   - Adding advanced metadata filtering and extraction
   - Implementing knowledge caching system

The complete implementation plan is detailed in our [Implementation Plan](./docs/project-management/planning/accelerated_implementation_plan.md), with corresponding business strategies in the [Commercialization Timeline](./docs/project-management/business/commercialization_timeline.md).

## Core Development Principles

### 1. Clean Break Philosophy with Example-Driven Validation

**CRITICAL**: Prioritize a best-in-class, robust, and consistent API over backwards compatibility.

- Don't hesitate to refactor or replace incorrect implementations, but document breaking changes thoroughly.
- When validating functionality, never temporarily simplify production code - instead, create dedicated example scripts.
- Always maintain the full LangGraph integration and multi-agent architecture in the main codebase.
- Use examples to demonstrate features rather than removing complexity from production code.

### 2. Incremental Development with Quality Focus

- Build new features using high-quality implementations from the start.
- Don't be afraid to rewrite or replace existing components if they aren't meeting quality standards.
- Prefer clean, maintainable code over perfect backward compatibility.
- Use composition over inheritance when possible to increase flexibility and testability.

### 3. Example-Driven Development Strategy

- Create functional examples that demonstrate each component's capabilities.
- Implement example scripts alongside feature development.
- When demonstrating complex workflows, create self-contained examples with clear documentation.
- Use MockProvider for examples that should run without API keys.

### 4. Error Handling

- Implement comprehensive error handling around all external API calls.
- Add appropriate fallbacks for critical components.
- Log detailed error information for debugging.
- Never let errors silently fail in production code.

## Code Structure and Style Guidelines

### File Organization

- Follow the established module structure (agents, core, graph, knowledge, orchestration, tools, scripts).
- Place new features in the appropriate module based on functionality.
- Create new subdirectories when introducing conceptually distinct components.
- Organize utility scripts in the `scripts` module with appropriate subdirectories:
  - `scripts/debug/`: Utilities for debugging and inspecting the system
  - `scripts/examples/`: Example runners and demonstration utilities

### Code Style

- Use comprehensive type hints for all function parameters and return values.
- Document all classes and functions with detailed docstrings.
- Maintain consistent naming conventions: snake_case for variables/functions, PascalCase for classes.
- Use meaningful variable and function names that clearly convey their purpose.

### Python Typing Best Practices

1. **Protocol Usage**: Enhance Protocol definitions with runtime_checkable
   ```python
   from typing import Protocol, runtime_checkable

   @runtime_checkable
   class BufferProtocol(Protocol):
       def push(self, item: Dict[str, Any]) -> bool: ...
       # ...
   ```

2. **Type Unions**: Use the `|` operator for unions in Python 3.13+
   ```python
   # Current/Legacy:
   ContentDict = Union[TextContentDict, ImageContentDict, str]

   # Modern (preferred):
   ContentDict = TextContentDict | ImageContentDict | str
   ```

3. **Typed Class Attributes**: Add class variable typing with ClassVar
   ```python
   from typing import ClassVar

   class StreamBuffer:
       MAX_DEFAULT_SIZE: ClassVar[int] = 1024 * 1024
   ```

4. **Final Classes/Methods**: Use Final for immutable design patterns
   ```python
   from typing import Final

   TOKEN_CHARSET: Final = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
   ```

5. **Self Type**: Update method return types to use Self type for fluid interfaces
   ```python
   from typing import Self

   class StreamBuffer:
       def pause(self) -> Self:
           self._paused = True
           return self
   ```

6. **TypeAlias**: Define clearer type aliases
   ```python
   from typing import TypeAlias

   StreamContent: TypeAlias = str
   TokenCount: TypeAlias = int
   ```

7. **Required/NotRequired**: Use consistently throughout TypedDict definitions
   ```python
   from typing_extensions import TypedDict, NotRequired, Required

   class ConfigDict(TypedDict):
       name: str  # Required by default
       version: str  # Required by default
       options: NotRequired[Dict[str, Any]]  # Optional field
   ```

8. **TypeGuard**: Add type narrowing functions
   ```python
   from typing import TypeGuard

   def is_string_content(content: ContentDict) -> TypeGuard[TextContentDict]:
       return isinstance(content, dict) and content.get("type") == "text"
   ```

9. **Literal Types**: Use for constrained string values
   ```python
   from typing import Literal

   StreamStateValue = Literal["initializing", "active", "paused", "cancelled", "completed", "error"]
   ```

### Documentation

- Document all key components and their interactions.
- Update documentation when adding or modifying features.
- Include docstrings with parameters, return values, and examples.
- Add inline comments for complex logic or algorithms.
- Use Mermaid diagrams for visualizing workflows and architecture but avoid inline styling.
- Follow the [documentation standards](./docs/contributing/documentation-standards.md) and [style guide](./docs/contributing/style-guide.md).
- Use [custom containers](./docs/contributing/content-containers.md) appropriately to highlight important information.
- Create [timeline components](./docs/contributing/timelines.md) for critical chronological processes.

## Working with LangGraph

### Graph Workflow Development

- Maintain the LangGraph StateGraph architecture for all agent workflows.
- Define clear node functions with appropriate state transformations.
- Use conditional edges for complex decision logic.
- Document graph topology with comments and diagrams.

### State Management

- Use the established state models (AgentState, ControllerState).
- Extend state classes with new fields rather than creating incompatible alternatives.
- Ensure all state mutations are clean and traceable.
- Verify state integrity before and after graph execution.

## Multi-Agent System Guidelines

### Controller-Worker Architecture

- Maintain the controller-worker pattern for all multi-agent operations.
- Follow the established communication protocols between agents.
- Use the agent registry for dynamic agent management.
- Document agent roles and responsibilities clearly.

### Agent Communication

- Design clean interfaces for agent communication.
- Use structured message formats with appropriate metadata.
- Ensure task context is properly passed between agents.
- Implement robust error handling for inter-agent communication.

## Database and Knowledge Management

### ChromaDB Integration

- Always use the PersistentClient for ChromaDB operations.
- Implement proper connection pooling and retry logic.
- Add appropriate error handling for database operations.
- Document data schemas and collection structures.

### Document Processing

- Follow the established chunking and processing strategies.
- Add proper metadata to all stored documents.
- Implement version control for knowledge base updates.
- Ensure proper indexing for efficient retrieval.

## Examples and Validation

### Example Directory Structure

Atlas uses functional examples to validate and demonstrate its capabilities:

- **`examples/`**: Contains example scripts demonstrating Atlas functionality
  - Script files are organized by feature area (e.g., `query_example.py`, `retrieval_example.py`)
  - Each example is self-contained and fully runnable
  - All examples include detailed comments explaining the workflow
  - Examples can run with or without API keys using the MockProvider

- **`atlas/scripts/debug/`**: Contains debug utilities for development
  - `check_models.py`: Verify available models for providers
  - `check_db.py`: Database connection and status verification
  - Other utilities for inspecting system state during development

### Validation Strategy

Atlas follows an example-driven development approach:

- Each core feature is validated through functional examples
- Examples serve as both documentation and validation
- All key API endpoints have corresponding example implementations
- Examples demonstrate both simple and complex use cases

### MockProvider for Development

Atlas provides comprehensive mocking utilities for development without API keys:

- **MockProvider**: A fully functional provider implementation that doesn't require API keys
- **Provider-specific mocks**: Specialized emulation for OpenAI, Anthropic, and Ollama behaviors
- **Deterministic responses**: Consistent outputs for development and debugging

Example of using MockProvider:
```python
# Create mock provider (no API key needed)
provider = MockProvider(model_name="mock-standard")

# Use it like any other provider
response = provider.generate(request)
```

### Running Examples

Examples can be run directly to validate functionality:

```bash
# Run a basic query example
uv run python examples/query_example.py

# Run retrieval example with mock provider
uv run python examples/retrieval_example.py --provider mock

# Run streaming example with OpenAI
uv run python examples/streaming_example.py --provider openai
```

## Implementation Notes for Claude Code

1. When working on this project, Claude should:
   - Start by understanding the existing architecture before making changes
   - Follow the file structure and coding patterns already established
   - Ensure all new code maintains compatibility with the existing system
   - Add detailed docstrings and comments for any new code
   - Test suggestions thoroughly before proposing them

2. When encountering a challenging implementation:
   - Break the problem down into smaller, manageable pieces
   - Prototype solutions in a way that doesn't disrupt existing code
   - Consider edge cases and error scenarios
   - Document design decisions and alternatives considered

3. When facing uncertainty:
   - Prefer asking clarifying questions over making assumptions
   - Reference existing code for patterns and conventions
   - Suggest alternatives with pros and cons clearly outlined
   - Be explicit about any limitations or potential issues

4. When working with documentation and implementation:
   - Use a documentation-driven implementation approach
   - Start by reviewing existing documentation to understand the design intent
   - Follow the established documentation standards in docs/contributing/
   - Use custom containers (info, tip, warning, danger, details) to highlight important information:
     - Info: For neutral information and general notes
     - Tip: For best practices and helpful advice
     - Warning: For potential pitfalls and important cautions
     - Danger: For critical warnings about breaking changes or security risks
     - Details: For collapsible content with additional information
   - Use code groups for alternative implementations or language versions:
     - Present parallel code examples using `::: code-group` with labeled tabs
     - Format labels as `[label]` after the language identifier
     - Use for different programming languages, alternative approaches, or configuration variations
   - Use colored diffs for showing code changes:
     - Use language-appropriate comment syntax with `[!code --]` or `[!code ++]` markers
     - Python: `# [!code --]`, JavaScript: `// [!code --]`, HTML: `<!-- [!code --] -->`
     - Use to highlight API changes, improvements, bug fixes, or subtle differences
   - Create timeline components only for critical chronological processes
     - Each `::: timeline` block represents one event in a complete timeline
     - Sequential timeline blocks automatically combine to form a single timeline
     - Use for development roadmaps, process workflows, and version histories
   - When finding discrepancies between documentation and implementation needs:
     - Evaluate which approach provides better API design, performance, and maintainability
     - Update documentation to match implementation when technical requirements necessitate changes
     - Preserve the original design intent while adapting to technical realities
   - Keep both implementation and documentation in sync throughout development
   - Use documentation as a design tool to clarify requirements before implementation
   - Document any implementation decisions that deviate from original specifications
   - Ensure code examples follow the standards in docs/contributing/code-examples.md

5. When implementing examples:
   - Create self-contained, runnable examples for each feature
   - Add detailed comments explaining the workflow
   - Use the MockProvider for examples that should run without API keys
   - Demonstrate both simple use cases and complex patterns
   - Ensure examples are educational and highlight best practices
   - Make examples runnable in isolation with minimal dependencies

6. When implementing provider features:
   - Ensure consistent behavior across all providers
   - Implement proper error handling with informative messages
   - Add graceful degradation when API calls fail
   - Verify streaming and non-streaming behavior works consistently
   - Ensure token usage tracking works correctly across providers

## Advanced Feature Development Areas

The following areas represent the most important development directions for advancing Atlas capabilities:

### 1. Textual CLI Implementation

- **Priority**: High
- **Status**: In Progress
- **Goals**:
  - Design and implement Textual-based rich terminal interface
  - Create consistent command structure with serialization
  - Build interactive conversation view with streaming support
  - Implement specialized screens for different operational modes
  - Develop configuration management with save/load capability
  - Provide visual state indicators and performance metrics

### 2. Enhanced Knowledge Management

- **Priority**: High
- **Status**: In Progress
- **Goals**:
  - Implement more sophisticated document chunking strategies
  - Add advanced metadata filtering and faceted search
  - Improve relevance scoring with hybrid approaches (semantic + keyword)
  - Create caching mechanisms for frequent queries
  - Support multimedia document types (beyond markdown)

### 3. Advanced Multi-Agent Orchestration

- **Priority**: Medium
- **Status**: Planned
- **Goals**:
  - Implement dynamic agent allocation based on task requirements
  - Create specialized worker agents for different domains
  - Develop better feedback mechanisms between agents
  - Enhance message passing with structured formats and metadata
  - Build visualization tools for agent interactions

### 4. Provider Performance Optimization

- **Priority**: High
- **Status**: In Progress
- **Goals**:
  - Complete streaming implementations for all providers
  - Implement connection pooling for performance
  - Add advanced retry and fallback mechanisms
  - Create provider switching based on cost/performance needs
  - Implement health monitoring and diagnostics

### 5. Interactive Documentation & Examples

- **Priority**: High
- **Status**: In Progress
- **Goals**:
  - Create interactive code examples in documentation
  - Build more comprehensive example applications
  - Develop tutorials for common usage patterns
  - Add troubleshooting guides and problem-solving trees
  - Create visual explanations of key concepts
  - Implement VitePress custom containers following our guidelines:
    - Use info/tip/warning/danger/details containers strategically
    - Follow container-specific usage guidance in docs/contributing/content-containers.md
    - Limit containers to 2-3 per page to prevent visual overload
  - Use code groups for presenting alternative implementations:
    - Create tabbed interfaces with `::: code-group` syntax
    - Label tabs appropriately with `[label]` after the language specifier
    - See docs/contributing/code-examples.md for implementation patterns
  - Use colored diffs to highlight code changes:
    - Use language-appropriate comment syntax with `[!code --]` and `[!code ++]` markers
    - Apply to API changes, improvements, or subtle differences
    - See docs/contributing/code-diffs.md for implementation details
  - Add timeline components for selected workflows and processes:
    - Follow the syntax with multiple `::: timeline` blocks for sequential events
    - Implement in key documents (roadmaps, implementation plans, etc.)
    - See docs/contributing/timelines.md for correct implementation patterns
  - Ensure consistent style and formatting across all documentation

## Development Environment

### Key Requirements

- Python version: >=3.13
- Key dependencies: langgraph==0.4.1, chromadb>=1.0.7, anthropic>=0.50.0
- Environment management: uv for virtual environments and dependencies
- Documentation: VitePress for documentation site
- Validation: Example-driven development with runnable demonstrations

### Important Commands

```bash
# Development setup
uv venv
source .venv/bin/activate
uv pip install -e .

# Run Atlas CLI
uv run python main.py cli

# Get CLI help information
uv run python main.py --help
uv run python main.py query --help

# Run Atlas with a specific query
uv run python main.py query -q "Your query here" --provider openai

# List available models for a provider
uv run python main.py query --provider openai --models

# Run Atlas with document ingestion
uv run python main.py ingest -d /path/to/docs/

# Run example scripts
uv run python examples/query_example.py
uv run python examples/retrieval_example.py
uv run python examples/streaming_example.py
uv run python examples/tool_agent_example.py

# Run debug utilities
uv run python atlas/scripts/debug/check_models.py
uv run python atlas/scripts/debug/check_db.py

# Documentation
cd docs
pnpm dev    # Start dev server
pnpm build  # Build documentation
```

### Development Tools Usage

With the project's enhanced configuration in pyproject.toml, you can now use simplified commands for testing and development:

```bash
# Testing with pytest (includes coverage automatically)
uv run pytest                                 # Run all tests with coverage
uv run pytest atlas/tests/core/services/     # Run specific tests with coverage
uv run pytest -k "test_buffer"               # Run tests matching pattern with coverage

# Pre-commit hooks
uv run pre-commit run --all-files            # Run all pre-commit hooks
```

For more granular coverage control, you can still use the explicit coverage module:

```bash
# Advanced coverage options
uv run python -m coverage html                # Generate HTML report
uv run python -m coverage report              # View coverage report in terminal
```

Thanks to the improved pyproject.toml configuration, test commands are now simpler while still providing all the necessary functionality.

### Using Atlas Without API Keys

For development without API keys, use the MockProvider:

```bash
# Run Atlas with mock provider
uv run python main.py cli --provider mock

# Run examples with mock provider
uv run python examples/query_example.py --provider mock
uv run python examples/streaming_example.py --provider mock
```

### Using Different Providers

Atlas supports multiple providers that can be specified for any operation:

```bash
# Run with OpenAI provider
uv run python examples/query_example.py --provider openai

# Run with Anthropic provider
uv run python examples/query_example.py --provider anthropic

# Run with Ollama provider (requires local Ollama server)
uv run python examples/query_example.py --provider ollama
```

### Textual CLI Implementation

The Atlas Textual CLI enhances the traditional command-line interface with a rich terminal UI:

```bash
# Run Atlas with the Textual interface
uv run python main.py --tui

# Run with specific initial mode
uv run python main.py --tui --mode query

# Run with saved configuration
uv run python main.py --tui --config /path/to/config.json
```

#### Textual CLI Architecture

The Textual CLI is organized in a modular structure:

```
atlas/
├── cli/
│   ├── __init__.py
│   ├── config.py            # Existing - Configuration utilities
│   ├── parser.py            # Existing - Command-line argument parsing
│   └── textual/             # New - Textual CLI components
│       ├── __init__.py
│       ├── app.py           # Main application class
│       ├── commands.py      # Command execution system
│       ├── schema.py        # Command schema definitions
│       ├── config.py        # Configuration management
│       ├── screens/         # Screen implementations
│       │   ├── __init__.py
│       │   ├── main.py      # Main application screen
│       │   ├── provider.py  # Provider selection screen
│       │   ├── ingest.py    # Document ingestion screen
│       │   └── tools.py     # Tool management screen
│       └── widgets/         # Custom widget components
│           ├── __init__.py
│           ├── command_bar.py    # Command input bar
│           ├── conversation.py   # Message display area
│           ├── status.py         # Status and metrics display
│           └── stream_controls.py # Streaming control widgets
```

#### Key Implementation Components

1. **Main Application**:

```python
# atlas/cli/textual/app.py
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from atlas.cli.textual.screens.main import MainScreen

class AtlasApp(App):
    """Atlas Textual TUI application."""

    CSS_PATH = "atlas.css"
    TITLE = "Atlas Framework"
    SUB_TITLE = "Advanced Multi-Modal Agent System"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield MainScreen()
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app when mounted."""
        # Load configuration
        self.load_config()

        # Initialize providers
        self.initialize_providers()

        # Set up key bindings
        self.setup_keybindings()

    def setup_keybindings(self) -> None:
        """Configure application key bindings."""
        self.bind("q", "quit", "Quit")
        self.bind("ctrl+p", "command_palette", "Command Palette")
        self.bind("ctrl+s", "toggle_sidebar", "Toggle Sidebar")
        self.bind("f1", "push_screen('help')", "Help")
```

2. **Command Schema and Execution**:

```python
# atlas/cli/textual/schema.py
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union, Type

@dataclass
class CommandSchema:
    """Schema definition for Atlas commands."""

    name: str
    description: str
    parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    returns: Dict[str, Any] = field(default_factory=dict)
    examples: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the schema to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "returns": self.returns,
            "examples": self.examples,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommandSchema":
        """Create a schema from a dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            parameters=data.get("parameters", {}),
            returns=data.get("returns", {}),
            examples=data.get("examples", []),
        )
```

3. **Command Execution**:

```python
# atlas/cli/textual/commands.py
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable, Awaitable

from atlas.core.logging import get_logger

logger = get_logger(__name__)

class Command(ABC):
    """Base class for Atlas commands in the Textual interface."""

    name: str = ""
    description: str = ""

    def __init__(self, app: Any = None) -> None:
        """Initialize the command."""
        self.app = app
        self.logger = get_logger(f"{__name__}.{self.name}")

    @abstractmethod
    async def execute(self, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the command with the given parameters."""
        pass

    async def validate(self, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate command parameters before execution."""
        # Default implementation just returns validated parameters
        return parameters or {}

class QueryCommand(Command):
    """Command for executing queries."""

    name = "query"
    description = "Execute a query with the selected provider"

    async def execute(self, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a query with the given parameters."""
        params = await self.validate(parameters)

        query_text = params.get("query")
        provider_name = params.get("provider")
        model_name = params.get("model")
        stream = params.get("stream", True)

        # Create query client
        from atlas.query import AtlasQuery
        query_client = AtlasQuery(
            provider_name=provider_name,
            model_name=model_name,
        )

        # Execute the query
        if stream:
            return await self._execute_stream(query_client, query_text)
        else:
            return await self._execute_basic(query_client, query_text)

    async def _execute_stream(self, query_client, query_text):
        """Execute a streaming query."""
        # Implementation for streaming query
        pass

    async def _execute_basic(self, query_client, query_text):
        """Execute a basic non-streaming query."""
        # Implementation for basic query
        pass
```

4. **Main Screen**:

```python
# atlas/cli/textual/screens/main.py
from textual.screen import Screen
from textual.widgets import Static, Input, Button
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive

from atlas.cli.textual.widgets.command_bar import CommandBar
from atlas.cli.textual.widgets.conversation import ConversationView
from atlas.cli.textual.widgets.status import StatusBar

class MainScreen(Screen):
    """Main application screen."""

    BINDINGS = [
        ("escape", "refocus", "Focus Command Bar"),
        ("ctrl+c", "copy_selection", "Copy Selection"),
    ]

    # Reactive state
    provider_name = reactive("anthropic")
    model_name = reactive("claude-3-haiku-20240307")

    def compose(self):
        """Create child widgets for the screen."""
        with Container(id="app-grid"):
            with Container(id="sidebar"):
                yield Static("Providers", id="sidebar-header")
                # Provider list would go here

            with Container(id="main-content"):
                yield ConversationView(id="conversation")

                with Horizontal(id="input-area"):
                    yield CommandBar(id="command-bar")
                    yield Button("Send", id="send-button")

                yield StatusBar(id="status-bar")

    def on_button_pressed(self, event):
        """Handle button press events."""
        if event.button.id == "send-button":
            self.send_command()

    def action_refocus(self):
        """Action to refocus the command bar."""
        self.query_one("#command-bar").focus()

    def send_command(self):
        """Send the current command."""
        command_bar = self.query_one("#command-bar")
        command_text = command_bar.value

        if not command_text:
            return

        # Clear the command bar
        command_bar.value = ""

        # Process the command
        self.app.run_command(command_text)
```

5. **Conversation View Widget**:

```python
# atlas/cli/textual/widgets/conversation.py
from textual.widgets import RichLog
from textual.reactive import reactive
from rich.console import Console
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

    def add_assistant_message(self, text, streaming=False):
        """Add an assistant message to the conversation."""
        if streaming:
            # Start a new message for streaming
            self.write(Text("Atlas: ", style="bold cyan"), end="")
            self._streaming_content = ""
            return

        # For non-streaming, add the complete message
        self.messages.append({"role": "assistant", "content": text})

        # Format and display the message
        assistant_text = Text(f"Atlas: {text}")
        assistant_text.stylize("bold cyan")
        self.write(assistant_text)
        self.write("")  # Add blank line

    def update_streaming(self, delta):
        """Update the current streaming message with new content."""
        self._streaming_content += delta

        # Replace the current line with updated content
        self.update(Text(delta, style="cyan"), append=True)

    def complete_streaming(self):
        """Complete the current streaming message."""
        # Add the full message to history
        self.messages.append({
            "role": "assistant",
            "content": self._streaming_content
        })

        # Add a blank line after the message
        self.write("")
```

### Developing New Features

When developing new features, create example scripts to validate functionality:

```bash
# Create a new example in examples/ directory
uv run python examples/my_new_feature_example.py

# Run example with debug logging
ATLAS_LOG_LEVEL=DEBUG uv run python examples/my_new_feature_example.py
```

## Future Vision

As outlined in our [Product Roadmap](./docs/project-management/roadmap/product_roadmap.md) and [Commercialization Timeline](./docs/project-management/business/commercialization_timeline.md), Atlas will evolve through these key phases:

1. **Atlas 1.0 Final (June 30, 2025)**
   - Feature-complete release with all MVP components
   - Comprehensive documentation and examples
   - Enterprise-ready security and compliance features
   - Cloud service foundations with multi-tenant architecture

2. **Commercial Launch (July 2025)**
   - Open-source public launch with Apache 2.0 license
   - Enterprise features release with tiered licensing model
   - Cloud service beta with usage-based pricing
   - Strategic partnerships with technology providers

3. **Post-Launch Features**
   - Advanced knowledge graph integration with pattern recognition
   - Self-organizing agent topology with dynamic specialization
   - Context-aware relevance with adaptive retrieval
   - Transparent reasoning with explainable decision processes

By following these guidelines and the detailed implementation plan, we will transform Atlas into a powerful, commercial-ready framework that combines flexibility, robustness, and extensibility, while delivering a clear go-to-market strategy upon completion.
