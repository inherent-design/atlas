# Atlas Development Guidelines for Claude Code

This file contains essential instructions and guidelines for Claude Code when working on the Atlas project. These instructions serve as a reference for both human developers and Claude to ensure consistent development practices.

## Project Status 2025 Update

### Project Timeline

- **Project Start**: Late April 2025
- **Current Date**: May 10, 2025
- **Completion Deadline**: June 30, 2025
- **Commercial Launch**: July 2025

### Completed Milestones

- ✅ **Foundation Stabilization**: Unified agent implementations, agent registry with dynamic discovery, error handling, conditional edge routing, query-only client
- ✅ **Environment Configuration**: Centralized environment management, configuration precedence, validation logic
- ✅ **Documentation System**: Complete VitePress-based documentation with comprehensive coverage of all components, workflows, and APIs
- ✅ **Core Component Design**: Established architecture patterns, module structure, and interaction protocols
- ✅ **Robust Provider Implementation**: Added retry mechanism with exponential backoff and circuit breaker pattern
- ✅ **Enhanced Provider System**: Implemented Provider Registry with capability-based selection and ProviderGroup with fallback strategies

### Current Focus (May 10-17, 2025)

Per the [Accelerated Implementation Plan](./docs/project-management/planning/accelerated_implementation_plan.md), we are currently in Phase 1 focused on Provider System Finalization:

1. **Enhanced Streaming Infrastructure**:
   - Updating BaseStreamHandler with standardized StreamControl interface
   - Implementing stream control capabilities (pause, resume, cancel)
   - Adding performance metrics tracking during streaming
   - Ensuring proper resource cleanup and consistent error handling

2. **Provider Lifecycle Management**:
   - Adding connection pooling for providers
   - Implementing connection reuse mechanisms
   - Adding health checking and circuit breaking
   - Enhancing error handling with detailed categorization

See the [current TODO list](./docs/project-management/tracking/todo.md) for specific implementation tasks.

### Next Steps (May 18-31, 2025)

Following our [Product Roadmap](./docs/project-management/roadmap/product_roadmap.md), upcoming phases include:

1. **Agent-Provider Integration (May 18-24)**:
   - Enhancing agent-provider interface with streaming controls
   - Optimizing provider capability utilization in agents
   - Updating controller-worker communication for streaming
   - Creating enhanced streaming examples

2. **Knowledge System Enhancements (May 25-31)**:
   - Implementing hybrid retrieval combining semantic and keyword search
   - Enhancing document chunking strategies with semantic boundaries
   - Adding advanced metadata filtering and extraction
   - Implementing knowledge caching system

The complete implementation timeline is detailed in our [Accelerated Implementation Plan](./docs/project-management/planning/accelerated_implementation_plan.md), with corresponding business strategies in the [Commercialization Timeline](./docs/project-management/business/commercialization_timeline.md).

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

### Documentation

- Document all key components and their interactions.
- Update documentation when adding or modifying features.
- Include docstrings with parameters, return values, and examples.
- Add inline comments for complex logic or algorithms.
- Use Mermaid diagrams for visualizing workflows and architecture but avoid inline styling.
- Follow the [documentation standards](./docs/contributing/documentation-standards.md) and [style guide](./docs/contributing/style-guide.md).
- Use [custom containers](./docs/contributing/content-containers.md) appropriately to highlight important information.
- Create [timeline components](./docs/contributing/timelines.md) for critical chronological processes (limit to 5-7 across all documentation).

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
   - Create timeline components only for critical chronological processes (max 5-7 across all docs)
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

### 1. Enhanced Knowledge Management

- **Priority**: High
- **Status**: In Progress
- **Goals**:
  - Implement more sophisticated document chunking strategies
  - Add advanced metadata filtering and faceted search
  - Improve relevance scoring with hybrid approaches (semantic + keyword)
  - Create caching mechanisms for frequent queries
  - Support multimedia document types (beyond markdown)

### 2. Advanced Multi-Agent Orchestration

- **Priority**: Medium
- **Status**: Planned
- **Goals**:
  - Implement dynamic agent allocation based on task requirements
  - Create specialized worker agents for different domains
  - Develop better feedback mechanisms between agents
  - Enhance message passing with structured formats and metadata
  - Build visualization tools for agent interactions

### 3. Provider Performance Optimization

- **Priority**: High
- **Status**: In Progress
- **Goals**:
  - Complete streaming implementations for all providers
  - Implement connection pooling for performance
  - Add advanced retry and fallback mechanisms
  - Create provider switching based on cost/performance needs
  - Implement health monitoring and diagnostics

### 4. Interactive Documentation & Examples

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
    - Implement in 5-7 key documents maximum (roadmaps, implementation plans, etc.)
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