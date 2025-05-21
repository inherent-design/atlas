# Development Environment Setup

## Project Configuration

We've enhanced the development environment with comprehensive configurations in `pyproject.toml` for:

### 1. Mypy Static Type Checking

```toml
[tool.mypy]
python_version = "3.13"
strict = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
# ... additional options
```

Mypy helps catch type-related errors early in development by performing static analysis of Python code.

### 2. Black Code Formatting

```toml
[tool.black]
line-length = 100
target-version = ["py313"]
# ... additional options
```

Ensures consistent code formatting across the project.

### 3. Ruff Linting 

```toml
[tool.ruff]
# Enable linting rules
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "B",   # flake8-bugbear
    # ... other rules
]
```

Ruff provides fast linting with comprehensive rule sets and auto-fixing capabilities.

### 4. isort Import Sorting

```toml
[tool.isort]
profile = "black"
line_length = 100
# ... additional options
```

Automatically organizes imports according to conventions.

### 5. pytest Testing Configuration

```toml
[tool.pytest.ini_options]
testpaths = ["atlas/tests"]
python_files = "test_*.py"
# ... additional options
```

Comprehensive test configuration with logging and coverage support.

### 6. Coverage Reporting

The project uses a comprehensive coverage configuration to track test coverage and identify areas needing testing:

```toml
[tool.coverage.run]
source = ["atlas"]
omit = ["*/tests/*", "*/examples/*"]
branch = true  # Measure branch coverage as well
parallel = true  # Support combining multiple coverage runs
dynamic_context = "test_function"  # Record which tests covered each line

[tool.coverage.report]
fail_under = 80  # Fail if coverage is below 80%
skip_covered = true  # Focus on files needing attention
precision = 2  # Show 2 decimal places in percentages
```

Key features of our coverage setup:

- **Branch coverage**: Tests all possible code paths, not just statements
- **Per-test coverage**: Tracks which tests cover each line of code
- **Exclusion patterns**: Intelligently ignores code that doesn't need coverage (docstrings, defensive assertions, etc.)
- **CI integration**: Generates XML and JSON reports for continuous integration
- **Multi-environment support**: Combines coverage data from different test environments

### 7. Pre-commit Hooks

Added `.pre-commit-config.yaml` for automated quality checks during git commits:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [ --fix ]
      - id: ruff-format
```

## Current Test Coverage

After running tests on the core services module, we have:

- **Total coverage: 65%** (1,995 lines covered out of 3,075)
- **Commands module: 76%** covered
- **Buffer module: 94%** covered
- **Events module: 94%** covered
- **Resources module: 93%** covered
- **Registry module: 97%** covered
- **Transitions module: 97%** covered
- **Component module: 99%** covered

## Development Workflow

1. **Linting & Formatting**: Run automatically via pre-commit hooks
   ```bash
   pre-commit install  # One-time setup
   ```

2. **Type Checking**: Run mypy to verify type correctness
   ```bash
   uv run mypy atlas
   ```

3. **Running Tests**: Execute pytest with coverage
   ```bash
   uv run python -m pytest
   ```

4. **Coverage Reports**: View HTML coverage report
   ```bash
   # After running tests, open the HTML report
   open coverage_html/index.html
   ```

## Next Steps

1. **Increase test coverage** for modules with < 80% coverage
2. **Add docstrings** to improve API documentation
3. **Create integration tests** that test multiple components together
4. **Configure CI pipeline** to run these checks automatically