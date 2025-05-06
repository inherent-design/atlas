# Atlas Development Guidelines for Claude Code

This file contains essential instructions and guidelines for Claude Code when working on the Atlas project. These instructions serve as a reference for both human developers and Claude to ensure consistent development practices.

## Project Status 2024 Update

### Completed Milestones

- ✅ **Foundation Stabilization**: Unified agent implementations, agent registry with dynamic discovery, error handling, conditional edge routing, query-only client
- ✅ **Environment Configuration**: Centralized environment management, configuration precedence, validation logic
- ✅ **Documentation System**: Complete VitePress-based documentation with comprehensive coverage of all components, workflows, and APIs
- ✅ **Core Component Design**: Established architecture patterns, module structure, and interaction protocols

### Current Focus

1. **Knowledge System Enhancements**:
   - Improving document chunking and content boundary detection
   - Enhancing metadata handling for better document retrieval
   - Implementing more sophisticated relevance scoring algorithms
   - Adding filtering capabilities to narrow search results

2. **Provider Implementation Completion**:
   - Completing streaming implementation for OpenAI and Ollama providers
   - Adding comprehensive error handling and fallback mechanisms
   - Implementing connection pooling and resource management
   - Creating provider health monitoring

3. **Testing Infrastructure**:
   - Developing mocked provider implementations for test isolation
   - Creating comprehensive test suite for all components
   - Implementing test coverage metrics and reporting
   - Building scenario-based integration tests

### Next Steps (Immediate)

1. Create comprehensive mock providers for API-free testing
2. Complete OpenAI and Ollama provider implementations
3. Enhance error handling with better fallback mechanisms
4. Improve document chunking strategies for better retrieval
5. Add metadata filtering capabilities to knowledge base retrieval
6. Optimize provider resource usage with connection pooling

## Core Development Principles

### 1. Clean Break Philosophy with Careful Testing

**CRITICAL**: Prioritize a best-in-class, robust, and consistent API over backwards compatibility.

- Don't hesitate to refactor or replace incorrect implementations, but document breaking changes thoroughly.
- When testing functionality, never temporarily simplify production code - instead, create separate test files or modules.
- Always maintain the full LangGraph integration and multi-agent architecture in the main codebase.
- Use temporary test environments to isolate features for testing rather than removing complexity from production code.

### 2. Incremental Development with Quality Focus

- Build new features using high-quality implementations from the start.
- Don't be afraid to rewrite or replace existing components if they aren't meeting quality standards.
- Prefer clean, maintainable code over perfect backward compatibility.
- Use composition over inheritance when possible to increase flexibility and testability.

### 3. Testing Strategy

- Create isolated test modules when testing specific components.
- Implement unit tests alongside feature development.
- When testing complex workflows, create test-specific wrapper modules rather than modifying production code.
- Prefer mock tests that don't require API keys for faster and more reliable testing.

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
  - `scripts/testing/`: Testing utilities and test runners

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

## Testing and Debugging

### Testing Directory Structure

Atlas differentiates between formal tests, usage examples, and testing utilities:

- **`atlas/tests/`**: Contains all unit tests and integration tests
  - Test files are named with a `test_` prefix (e.g., `test_models.py`)
  - Each test file focuses on testing a specific module or component

- **`atlas/scripts/testing/`**: Contains utility scripts for running tests
  - `run_tests.py`: Unified test runner with various test types
  - Other utilities for test setup and configuration

- **`examples/`**: Contains example scripts demonstrating Atlas functionality
  - These are **not** formal tests but usage demonstrations
  - Can be run with or without an API key (using `SKIP_API_KEY_CHECK=true`)

### Test Implementation

- Create comprehensive unit tests for all components
- Implement mock tests that don't require API keys
- Use the agent registry for testing with different agent implementations
- Create mocked provider implementations for testing without API calls
- Document testing strategies and expected outcomes

### Test Types

- **Unit Tests**: Test individual components in isolation
- **Mock Tests**: Use mocked components to test without API dependencies
- **Integration Tests**: Verify that different components work together
- **API Tests**: Test real API interactions (requires API keys)

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
   - When finding discrepancies between documentation and implementation needs:
     - Evaluate which approach provides better API design, performance, and maintainability
     - Update documentation to match implementation when technical requirements necessitate changes
     - Preserve the original design intent while adapting to technical realities
   - Keep both implementation and documentation in sync throughout development
   - Use documentation as a design tool to clarify requirements before implementation
   - Document any implementation decisions that deviate from original specifications

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

- **Priority**: Medium
- **Status**: Planning
- **Goals**:
  - Create interactive code examples in documentation
  - Build more comprehensive example applications
  - Develop tutorials for common usage patterns
  - Add troubleshooting guides and problem-solving trees
  - Create visual explanations of key concepts

## Development Environment

### Key Requirements

- Python version: >=3.13
- Key dependencies: langgraph==0.4.1, chromadb>=1.0.7, anthropic>=0.50.0
- Environment management: uv for virtual environments and dependencies
- Documentation: VitePress for documentation site
- Testing: pytest for tests, with custom test runner

### Important Commands

```bash
# Development setup
uv venv
source .venv/bin/activate
uv pip install -e .

# Testing
uv run python atlas/scripts/testing/run_tests.py --test-type mock
uv run python atlas/scripts/testing/run_tests.py --test-type unit

# Run Atlas
uv run python main.py -m cli
uv run python main.py -m query -q "Your query here"
uv run python main.py -m ingest -d /path/to/docs/

# Documentation
cd docs
pnpm dev    # Start dev server
pnpm build  # Build documentation
```

## Future Vision

Atlas is evolving toward a fully distributed multi-agent framework that implements:

1. **Quantum-Inspired Knowledge Partitioning**: Multi-perspective knowledge representation
2. **Self-Organizing Agent Topology**: Dynamic agent relationships and specialization
3. **Context-Aware Relevance**: Adaptive information retrieval based on user needs
4. **Emergent Pattern Recognition**: Identifying reusable patterns across domains
5. **Transparent Reasoning**: Making agent decision processes understandable

By following these guidelines and principles, we will continue to build Atlas into a powerful framework that combines flexibility, robustness, and extensibility.