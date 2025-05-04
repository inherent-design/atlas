# Atlas Development Guidelines for Claude Code

This file contains essential instructions and guidelines for Claude Code when working on the Atlas project. These instructions serve as a reference for both human developers and Claude to ensure consistent development practices.

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

### 4. Error Handling

- Implement comprehensive error handling around all external API calls.
- Add appropriate fallbacks for critical components.
- Log detailed error information for debugging.
- Never let errors silently fail in production code.

## Code Structure and Style Guidelines

### File Organization

- Follow the established module structure (agents, core, graph, knowledge, orchestration, tools).
- Place new features in the appropriate module based on functionality.
- Create new subdirectories when introducing conceptually distinct components.

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

### Test Implementation

- Create comprehensive unit tests for all components.
- Implement integration tests for key workflows.
- Use mock objects for external dependencies in tests.
- Document testing strategies and expected outcomes.

### Debugging

- Add detailed logging throughout the codebase.
- Implement debug modes with increased verbosity.
- Create visualization tools for complex workflows.
- Document common debugging scenarios and solutions.

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

## Project Roadmap Reference

The immediate development focus is on:

1. Enhancing the LangGraph integration with improved workflows
2. Expanding the controller-worker architecture for more complex tasks
3. Improving knowledge retrieval and processing
4. Implementing advanced orchestration capabilities
5. Adding comprehensive testing and debugging tools

Refer to the TODO.md file for a detailed implementation plan with specific tasks and priorities.

## Development Environment Setup

### Requirements

- Python version: >=3.13
- Key dependencies: langgraph, chromadb, anthropic, pydantic, pathspec
- Environment variables required: ANTHROPIC_API_KEY
- Default DB path: ~/atlas_chroma_db
- Claude model: claude-3-sonnet-20240229

### Setting Up Development Environment

We use `uv` for virtual environment and package management. If you don't have it installed:

```bash
# Install uv
pip install uv
```

Setting up the project:

```bash
# Clone the repository (if you haven't already)
git clone <repository-url>
cd atlas

# Create and activate virtual environment
uv venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
uv pip install -e .
```

### Environment Variables

Create a `.env` file in the project root with:

```
ANTHROPIC_API_KEY=your_api_key_here
```

Or set environment variables directly:

```bash
# On Linux/macOS:
export ANTHROPIC_API_KEY=your_api_key_here

# On Windows:
# set ANTHROPIC_API_KEY=your_api_key_here
```

## Running Atlas

### Basic Usage

```bash
# Run in CLI mode with default system prompt
python main.py -m cli

# Run with custom system prompt
python main.py -m cli -s path/to/your/system_prompt.md

# Ingest documents
python main.py -m ingest -d path/to/your/documents/

# Run in controller mode with parallel processing
python main.py -m controller --parallel

# Run a single query
python main.py -m query -q "What is the trimodal methodology in Atlas?"
```

### Development Commands

```bash
# Run tests
uv run pytest

# Run linting
uv run ruff .

# Run type checking
uv run mypy .

# Format code
uv run black .
```

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest test_atlas.py

# Run with coverage
uv run pytest --cov=atlas

# Run tests with detailed output
uv run pytest -v
```

### Creating New Tests

When creating new tests:

1. Create test files in the project root or a `tests/` directory
2. Name test files with `test_` prefix (e.g., `test_agents.py`)
3. Name test functions with `test_` prefix
4. Use pytest fixtures for common setup

Example test:

```python
def test_atlas_agent():
    agent = AtlasAgent()
    response = agent.process_message("test query")
    assert response is not None
```

## Commit Guidelines

- Write clear, descriptive commit messages
- Reference related issues or tasks in commit messages
- Group related changes in single commits
- Ensure the codebase remains in a working state after each commit

By following these guidelines, we can maintain a high-quality, robust implementation of the Atlas framework while continually expanding its capabilities.