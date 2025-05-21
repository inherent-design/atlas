---
title: Development Environment
---

# Development Environment

This guide provides instructions for setting up and using the Atlas development environment, including best practices for running development tools.

## Environment Setup

Atlas uses `uv` for environment management and package installation to ensure reproducible builds and fast dependency resolution.

```bash
# Create a virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate  # On Unix/MacOS
# or
.\.venv\Scripts\activate  # On Windows

# Install Atlas and development dependencies
uv pip install -e .
uv pip install -e ".[dev]"
```

## Running Development Tools

### Critical Rule: Use `uv run python -m <package>` for Project Tools

⚠️ **IMPORTANT**: Always use `uv run python -m <package>` to execute Python tools that need access to local project dependencies. This ensures proper discovery of packages within the project structure.

```bash
# ✅ CORRECT: Use this pattern for running tools
uv run python -m pytest
uv run python -m coverage run -m pytest
uv run python -m mypy atlas

# ❌ INCORRECT: May fail due to import/discovery issues
uvx pytest
uvx coverage run
```

Using `uvx` directly might lead to broken imports or module discovery issues, especially for tools like pytest and coverage that need to build/execute the project itself.

## Testing

### Running Tests with pytest

With the project's enhanced pyproject.toml configuration, pytest has been configured to automatically include coverage reporting:

```bash
# Run all tests with coverage
uv run pytest

# Run specific test modules with coverage
uv run pytest atlas/tests/core/services/

# Run tests matching a pattern with coverage
uv run pytest -k "test_buffer"

# Run tests in parallel (faster) with coverage
uv run pytest -xvs -n auto
```

### Test Coverage

Coverage is already included when running pytest, but you can use these commands for viewing or generating different report formats:

```bash
# Show coverage report in terminal
uv run python -m coverage report

# Generate HTML coverage report
uv run python -m coverage html

# Open coverage report in browser
open coverage_html/index.html  # On MacOS
# or
start coverage_html/index.html  # On Windows
```

::: tip
The coverage configuration in pyproject.toml is pre-configured with optimal settings for the Atlas project, including branch coverage, report formats, and appropriate exclusions. This means you can use the simpler `uv run pytest` command for most testing needs while still getting complete coverage information.
:::

## Code Quality Tools

### Type Checking with mypy

```bash
# Run type checking on the entire project
uv run mypy atlas

# Run type checking on specific modules
uv run mypy atlas/core atlas/providers
```

### Linting and Formatting with ruff

```bash
# Run linting
uv run ruff check .

# Fix linting issues automatically
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Pre-commit Hooks

```bash
# Run all pre-commit hooks on all files
uv run pre-commit run --all-files

# Run a specific hook
uv run pre-commit run ruff --all-files
```

## Running Atlas CLI During Development

```bash
# Run the standard CLI
uv run python main.py --help

# Run a query
uv run python main.py query -q "Your query here" --provider openai

# Run with the TextUI interface
uv run python main.py --tui
```

## Running Example Scripts

Examples are a crucial part of the development process and serve as functional validation of features:

```bash
# Run example scripts
uv run python examples/query_example.py
uv run python examples/retrieval_example.py

# Use the mock provider for development without API keys
uv run python examples/query_example.py --provider mock

# Enable debug logging
ATLAS_LOG_LEVEL=DEBUG uv run python examples/streaming_example.py
```

## Using MockProvider for Development

The `MockProvider` enables development without requiring API keys:

```bash
# Run with mock provider
uv run python main.py cli --provider mock

# Run examples with mock provider
uv run python examples/query_example.py --provider mock
```

## Documentation Development

To work on the documentation site:

```bash
# Navigate to docs directory
cd docs

# Install dependencies (first time only)
pnpm install

# Start documentation dev server
pnpm dev

# Build documentation site
pnpm build
```

## Pre-commit Hooks

Atlas includes pre-commit hooks for code quality checks. While not mandatory, they can be helpful:

```bash
# Install pre-commit hooks
uv run python -m pre_commit install

# Run pre-commit hooks manually
uv run python -m pre_commit run --all-files

# Uninstall hooks if needed
uv run python -m pre_commit uninstall
```