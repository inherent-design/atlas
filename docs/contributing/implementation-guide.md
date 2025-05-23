---
title: Implementation Guide
---

# Implementation Guide

This guide provides technical setup instructions and implementation patterns for contributing to Atlas. It covers development environment setup, schema validation, and common implementation patterns.

## Development Environment

Atlas uses `uv` for environment management and package installation to ensure reproducible builds and fast dependency resolution.

### Environment Setup

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

### Running Tests

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

### Code Quality Tools

#### Type Checking with mypy

```bash
# Run type checking on the entire project
uv run mypy atlas

# Run type checking on specific modules
uv run mypy atlas/core atlas/providers
```

#### Linting and Formatting with ruff

```bash
# Run linting
uv run ruff check .

# Fix linting issues automatically
uv run ruff check --fix .

# Format code
uv run ruff format .
```

#### Pre-commit Hooks

```bash
# Run all pre-commit hooks on all files
uv run pre-commit run --all-files

# Run a specific hook
uv run pre-commit run ruff --all-files
```

### Running Atlas CLI During Development

```bash
# Run the standard CLI
uv run python main.py --help

# Run a query
uv run python main.py query -q "Your query here" --provider openai

# Run with the TextUI interface
uv run python main.py --tui
```

### Running Example Scripts

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

### Using MockProvider for Development

The `MockProvider` enables development without requiring API keys:

```bash
# Run with mock provider
uv run python main.py cli --provider mock

# Run examples with mock provider
uv run python examples/query_example.py --provider mock
```

### Documentation Development

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

## Schema Validation

Atlas uses marshmallow for schema validation to ensure that data structures conform to expected formats. This validation happens at API boundaries and provides several benefits:

- Type safety and validation
- Consistent serialization/deserialization
- Self-documenting data structures
- Improved error messages

### Basic Schema Usage

```python
from atlas.schemas.messages import text_content_schema

# Validate text content
content = {
    "type": "text",
    "text": "This is a sample message"
}
validated_content = text_content_schema.load(content)
```

### Creating Custom Schemas

```python
from atlas.schemas.base import AtlasSchema
from marshmallow import fields

class MyCustomSchema(AtlasSchema):
    """Schema for my custom data structure."""

    id = fields.String(required=True)
    name = fields.String(required=True)
    value = fields.Integer(required=False, load_default=0)

my_schema = MyCustomSchema()
```

### Validation Decorators

Atlas provides several decorators for schema validation:

```python
from atlas.schemas.validation import validate_with_schema
from atlas.schemas.providers import model_request_schema

@validate_with_schema(model_request_schema)
def process_request(request):
    # request is guaranteed to be valid
    ...
```

### Migrating to Marshmallow 4.0.0

::: warning
In marshmallow 4.0.0, the `default` parameter for fields has been replaced by separate `load_default` and `dump_default` parameters.
:::

#### Changes from Marshmallow 3.x

Marshmallow 4.0.0 introduces several breaking changes, with the most important being the replacement of the `default` parameter:

- **Old (3.x)**: `fields.Boolean(required=False, default=True)`
- **New (4.0.0)**: `fields.Boolean(required=False, load_default=True)`

The separation into `load_default` and `dump_default` provides more control over serialization and deserialization defaults:

- `load_default`: Default value when deserializing (loading) data
- `dump_default`: Default value when serializing (dumping) data

#### Migration Examples

##### Before (Marshmallow 3.x)

```python
class DatabaseConfigSchema(AtlasSchema):
    provider = fields.String(required=True)
    persistent = fields.Boolean(required=False, default=True)
    options = fields.Dict(keys=fields.String(), values=fields.Raw(), required=False)
```

##### After (Marshmallow 4.0.0)

```python
class DatabaseConfigSchema(AtlasSchema):
    provider = fields.String(required=True)
    persistent = fields.Boolean(required=False, load_default=True)
    options = fields.Dict(keys=fields.String(), values=fields.Raw(), required=False)
```

#### Other Considerations

1. For fields where you want different default values for loading and dumping:

```python
class UserSchema(AtlasSchema):
    active = fields.Boolean(load_default=False, dump_default=True)
```

2. For validators, make sure to add `**kwargs` to your method signatures:

```python
@validates("field_name")
def validate_field(self, value, **kwargs):
    # Validation logic
```

### Common Schema Types

Atlas provides many built-in schemas:

- `ModelMessageSchema`: For model messages
- `TokenUsageSchema`: For token usage tracking
- `ProviderOptionsSchema`: For provider options
- `AgentConfigSchema`: For agent configuration
- `RetrievalSettingsSchema`: For knowledge retrieval settings

### Example: Complete Schema Validation

For a complete example of schema validation, see the `examples/16_schema_validation.py` file, which demonstrates:

1. Basic schema validation for messages and data structures
2. Provider options validation
3. Using the SchemaValidated wrapper for guaranteed validation
4. Creating custom schemas for application-specific objects
5. Validating data at API boundaries
6. Mapping schema validation errors to provider-specific errors
7. Advanced validation decorators for functions and classes

### Migration from TypedDict

Atlas is in the process of migrating from TypedDict-based type annotations to schema-based validation.

### Using Schema Validation with Static Types

The ideal pattern is to combine static typing with runtime validation:

```python
from typing import Dict, Any
from atlas.schemas.validation import validate_with_schema
from atlas.schemas.messages import model_message_schema

# Static type hints + runtime validation
@validate_with_schema(model_message_schema)
def process_message(message: Dict[str, Any]) -> str:
    # message is guaranteed to be valid
    return f"Processing {message['role']} message"
```

## Implementation Patterns

### Provider Implementation Pattern

When implementing new providers, follow this pattern:

```python
from atlas.providers.base import BaseProvider
from atlas.core.types import ModelRequest, ModelResponse

class CustomProvider(BaseProvider):
    """Custom provider implementation."""

    def __init__(self, model_name: str, **options):
        super().__init__(model_name=model_name, **options)
        # Initialize provider-specific resources

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response using the custom provider."""
        # Implement provider-specific logic
        # Return standardized ModelResponse
        pass

    def generate_streaming(self, request: ModelRequest, callback=None) -> ModelResponse:
        """Generate a streaming response."""
        # Implement streaming logic if supported
        pass
```

### Agent Implementation Pattern

For implementing new agent types:

```python
from atlas.agents.base import BaseAgent
from atlas.core.types import AgentState

class CustomAgent(BaseAgent):
    """Custom agent implementation."""

    def __init__(self, name: str, **config):
        super().__init__(name=name, **config)
        # Initialize agent-specific resources

    def process_task(self, task: str, state: AgentState) -> AgentState:
        """Process a task and return updated state."""
        # Implement task processing logic
        # Return updated state
        pass
```

### Tool Implementation Pattern

For implementing new tools:

```python
from atlas.tools.base import BaseTool
from typing import Dict, Any

class CustomTool(BaseTool):
    """Custom tool implementation."""

    name = "custom_tool"
    description = "Description of what this tool does"

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        # Implement tool-specific logic
        # Return results
        pass
```

### Error Handling Pattern

Implement consistent error handling:

```python
from atlas.core.errors import AtlasError, ProviderError

def my_function():
    try:
        # Risky operation
        result = some_operation()
        return result
    except SpecificException as e:
        # Convert to Atlas error
        raise ProviderError(f"Operation failed: {e}") from e
    except Exception as e:
        # Generic fallback
        raise AtlasError(f"Unexpected error: {e}") from e
```

### Configuration Pattern

For components requiring configuration:

```python
from atlas.core.config import AtlasConfig
from typing import Optional

class MyComponent:
    """Component with configuration support."""

    def __init__(self, config: Optional[AtlasConfig] = None):
        self.config = config or AtlasConfig.get_default()
        self._initialize_from_config()

    def _initialize_from_config(self):
        """Initialize component based on configuration."""
        # Use self.config to set up component
        pass
```

### Testing Pattern

When writing tests, follow this pattern:

```python
import pytest
from atlas.providers import MockProvider

class TestMyFeature:
    """Test suite for my feature."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = MockProvider()

    def test_basic_functionality(self):
        """Test basic functionality."""
        # Arrange
        input_data = {"key": "value"}

        # Act
        result = my_function(input_data)

        # Assert
        assert result is not None
        assert result["status"] == "success"

    def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(AtlasError):
            my_function(invalid_input)
```

## Best Practices

### Code Organization

1. **Module Structure**: Follow the established module structure
2. **Import Organization**: Group imports logically (standard library, third-party, Atlas)
3. **Class Organization**: Methods in logical order (init, public, private)
4. **Function Size**: Keep functions focused and reasonably sized

### Documentation

1. **Docstrings**: Include comprehensive docstrings for all public methods
2. **Type Hints**: Use comprehensive type hints
3. **Comments**: Add comments for complex logic
4. **Examples**: Include usage examples in docstrings

### Error Handling

1. **Specific Exceptions**: Use specific exception types
2. **Error Messages**: Provide clear, actionable error messages
3. **Logging**: Log errors with appropriate levels
4. **Recovery**: Implement graceful error recovery where possible

### Performance

1. **Lazy Loading**: Use lazy loading for expensive resources
2. **Caching**: Implement caching for frequently accessed data
3. **Connection Pooling**: Use connection pooling for external services
4. **Resource Cleanup**: Ensure proper resource cleanup

### Security

1. **Input Validation**: Validate all external inputs
2. **Secret Management**: Use secure methods for handling secrets
3. **Sanitization**: Sanitize data before logging or display
4. **Access Control**: Implement appropriate access controls

By following this implementation guide, you'll create high-quality, maintainable code that integrates well with the Atlas architecture and follows project conventions.