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

### Current Development Focus

The immediate development focus is on:

1. Enhancing the LangGraph integration with improved workflows
2. Expanding the controller-worker architecture for more complex tasks
3. Improving knowledge retrieval and processing
4. Implementing advanced orchestration capabilities
5. Adding comprehensive testing and debugging tools (✅ Mock testing framework added)
6. Tracking API usage and estimating costs for better resource management (✅ Implemented)

Refer to the TODO.md file for a detailed implementation plan with specific tasks and priorities.

### Future Vision and Target Architecture

Atlas is evolving toward a fully distributed multi-agent framework with these target capabilities:

#### 1. Quantum-Inspired Knowledge Partitioning
- **Parallel Context Processing**: Process multiple partitions of knowledge simultaneously
- **Dynamic Boundary Detection**: Automatically identify natural conceptual boundaries
- **State Superposition**: Maintain multiple interpretations of knowledge simultaneously
- **Measurement-Based Collapse**: Refine knowledge based on specific queries

#### 2. Advanced Multi-Agent Orchestration
- **Self-Organizing Agent Topology**: Dynamically adjust agent relationships based on task requirements
- **Heterogeneous Agent Specialization**: Enable diverse agent types with complementary capabilities
- **Adaptive Task Decomposition**: Break complex problems into optimal sub-tasks
- **Emergent Consensus Mechanisms**: Develop collaborative decision-making without centralized control

#### 3. Perspective-Driven Knowledge Graph
- **Multi-Perspective Traversal**: Navigate knowledge from different technical and functional viewpoints
- **Context-Aware Relevance**: Adjust information relevance based on user context
- **Temporal Evolution Tracking**: Maintain historical perspectives alongside current understanding
- **Relationship-First Architecture**: Focus on connections between concepts rather than isolated facts

#### 4. Continuous Self-Improvement
- **Performance Metrics Tracking**: Monitor various efficiency and quality metrics
- **Adaptive Resource Allocation**: Optimize token usage based on task importance
- **Knowledge Consolidation**: Regularly refine and improve knowledge representation
- **Emergent Pattern Recognition**: Identify reusable patterns across different domains

#### 5. Seamless Human-AI Collaboration
- **Intention-Based Communication**: Understand user needs beyond explicit queries
- **Progressive Scaffolding**: Adapt guidance based on user expertise level
- **Collaborative Problem Definition**: Work with users to refine problem statements
- **Transparent Reasoning**: Make agent decision processes understandable to users

## Development Environment Setup

### Requirements

- Python version: >=3.13
- Key dependencies: langgraph, chromadb, anthropic, pydantic, pathspec
- Environment variables required: ANTHROPIC_API_KEY
- Default DB path: ~/atlas_chroma_db
- Claude model: claude-3-7-sonnet-20250219

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
uv run python main.py -m cli

# Run with custom system prompt
uv run python main.py -m cli -s path/to/your/system_prompt.md

# Ingest documents
uv run python main.py -m ingest -d path/to/your/documents/

# Run in controller mode with parallel processing
uv run python main.py -m controller --parallel

# Run a single query
uv run python main.py -m query -q "What is the trimodal methodology in Atlas?"
```

### Development Commands

```bash
# Run tests
uv python -m pytest

# Run specific test file
uv python -m pytest test_atlas.py

# Run with coverage
uv python -m pytest --cov=atlas

# Run mock tests
uv python mock_test.py

# Run linting
uv tool run ruff check

# Run type checking
uv tool run mypy .

# Format code
uv tool run black .
```

### Dependency Management

Atlas uses the following key dependencies with specific version requirements to ensure compatibility:

```
langgraph==0.4.1
chromadb>=1.0.7
anthropic>=0.50.0
pydantic>=2.11.4
pathspec>=0.12.1
```

To install or update dependencies:

```bash
# Install dependencies from pyproject.toml
uv sync

# Add a specific dependency
uv add <package_name>==<version>

# Update all dependencies
uv pip compile pyproject.toml -o requirements.txt
uv pip sync requirements.txt
```

When updating dependency versions, ensure compatibility with existing code. Some packages have breaking API changes between versions that require code adaptations:

#### LangGraph Version Compatibility

- langgraph 0.0.27 → 0.4.1 upgrade notes:
  - `MemorySaver` import path changed to `from langgraph.saver import MemorySaver`
  - `CheckpointAt` is now available in the checkpoint module
  - The graph compilation API has been enhanced with additional options
  - State management has been improved with more type safety

#### Code Adaptations for LangGraph Upgrades

When updating from older versions of langgraph, make these changes:

```python
# Old import (0.0.27)
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver

# New imports (0.4.1)
from langgraph.graph import StateGraph, END
from langgraph.saver import MemorySaver
```

For projects using checkpoint features:

```python
# New checkpoint imports
from langgraph.checkpoint.base import CheckpointAt, Checkpoint
```

#### Other Dependency Upgrades

**Anthropic API Changes (anthropic ≥0.50.0)**:
- The Claude API has evolved with improved streaming capabilities
- Messages API is now the standard for all interactions
- Content handling now supports structured formats and multi-modal inputs
- Example usage:
  ```python
  # Modern Anthropic API usage
  response = client.messages.create(
      model="claude-3-7-sonnet-20250219",
      max_tokens=2000,
      system=system_prompt,
      messages=message_history
  )
  ```

**ChromaDB Changes (chromadb ≥1.0.7)**:
- Improved persistent storage handling
- Enhanced embedding functionality with better model support
- More robust error handling and connection management
- Metadata filtering improvements

**Pydantic Upgrades (pydantic ≥2.11.4)**:
- Better type validation and error messages
- Enhanced schema generation and serialization
- Improved performance for model validation

## Environment Setup and Troubleshooting

### Development Environment

```bash
# Create a new virtual environment
uv venv

# Activate the environment
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate  # On Windows

# Install all dependencies
uv sync
```

### Troubleshooting Common Issues

#### Import Errors
If you encounter import errors like `ModuleNotFoundError` or `ImportError`, check:
1. That all dependencies are installed with correct versions
2. That import paths match the installed package versions
3. Run `uv sync` to ensure all dependencies are up to date

#### LangGraph Compatibility Issues
If you encounter errors with LangGraph functionality:
1. Verify the LangGraph version with `uv pip show langgraph`
2. Check that import paths match the installed version
3. If needed, install the exact version specified in pyproject.toml: `uv add langgraph==0.4.1`

#### API Changes in Dependencies
When upgrading dependencies:
1. Review the changelog or release notes for each package
2. Test key functionality after upgrading
3. Update code to use new API patterns where needed

## Testing

### Running Tests

```bash
# RECOMMENDED: Run mock tests (fast, reliable, no API key required)
uv run python mock_test.py

# Run only the base agent test (requires API key)
uv run python test_atlas.py --test base

# Run specific base agent test with custom query (requires API key)
uv run python test_atlas.py --test base --query "Your query here"

# NOTE: The following tests may encounter LangGraph compatibility issues
# and are not recommended for regular development testing:
# uv run python test_atlas.py --test controller
# uv run python test_atlas.py --test coordinator
# uv run python test_atlas.py --test workflows
```

> **Important Testing Notes:**
>
> 1. The mock tests (`mock_test.py`) are the most reliable way to verify code functionality
> 2. The real tests using `test_atlas.py` work reliably for the base agent, but may encounter issues with controller and workflow components
> 3. Regular pytest integration (`uv tool run pytest`) is not recommended due to dependency and collection issues
> 4. Always run the mock tests before making changes to ensure you have a working baseline

### API Cost Tracking

Atlas includes built-in cost tracking for Anthropic API calls. This feature helps monitor usage during development and testing to avoid unexpected charges.

When running real tests with an API key, the system will automatically report:
- Input tokens used and their cost
- Output tokens used and their cost
- Total API cost for the operation

Example output:
```
API Usage: 683 input tokens, 502 output tokens
Estimated Cost: $0.009579 (Input: $0.002049, Output: $0.007530)
```

This cost tracking is based on current Anthropic pricing for the Claude 3.5 Sonnet model:
- Input tokens: $3 per million tokens
- Output tokens: $15 per million tokens

If Anthropic updates their pricing, you might need to update the cost calculation in the agent class.

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
