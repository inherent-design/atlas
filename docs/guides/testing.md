# Testing Guide 🚧

> **Current Development Status:** Atlas is currently focusing on example-driven development rather than comprehensive test-driven development. The testing infrastructure described in this document represents the planned testing architecture, but is not fully implemented at this time. We are prioritizing functional examples and usage demonstrations as the primary verification method while the codebase is actively evolving.

This guide provides a comprehensive overview of the planned testing approaches and practices for the Atlas framework.

## Testing Philosophy

Atlas follows a robust testing philosophy that includes:

1. **Comprehensive Test Coverage**: Testing all critical components with both unit and integration tests
2. **Mock-First Testing**: Using mocks to enable testing without requiring API keys
3. **Test Isolation**: Ensuring tests are independent and don't rely on shared state
4. **Continuous Validation**: Running tests frequently during development

## Testing Directory Structure

The Atlas testing infrastructure is organized into a structured directory hierarchy for better separation of concerns:

```
atlas/
├── tests/                        # Core test modules
│   ├── __init__.py
│   ├── unit/                     # Unit tests for specific components
│   │   ├── core/                 # Tests for core features
│   │   ├── models/               # Tests for model abstractions
│   │   ├── knowledge/            # Tests for knowledge features
│   │   ├── agents/               # Tests for agent features
│   │   └── tools/                # Tests for tool features
│   ├── mock/                     # Tests that use mocked providers/APIs
│   │   ├── providers/            # Mocked provider tests
│   │   ├── agents/               # Agent tests with mocked providers
│   │   └── workflows/            # Workflow tests with mocked components
│   ├── integration/              # Tests connecting multiple components
│   │   ├── agent_tool/           # Agent + Tool integration tests
│   │   ├── knowledge_agent/      # Knowledge + Agent integration tests
│   │   └── workflow/             # Full workflow integration tests
│   ├── api/                      # Real API tests (may incur costs)
│   │   ├── openai/               # OpenAI-specific API tests
│   │   ├── anthropic/            # Anthropic-specific API tests
│   │   └── ollama/               # Ollama-specific API tests
│   ├── fixtures/                 # Test fixtures and data
│   │   ├── documents/            # Test documents
│   │   ├── responses/            # Sample API responses
│   │   └── tools/                # Test tool implementations
│   └── helpers/                  # Test helper functions and utilities
│       ├── __init__.py
│       ├── decorators.py         # Test decorators
│       ├── base_classes.py       # Base test classes
│       ├── mocks.py              # Common mocks
│       └── utils.py              # Test utilities
├── scripts/
│   └── testing/                  # Test runner scripts
│       ├── __init__.py
│       ├── run_tests.py          # CLI-based test runner
│       └── run_tests.py.old      # Legacy test runner (deprecated)
└── examples/                     # Example usage (not formal tests)
    ├── query_example.py
    ├── retrieval_example.py
    ├── streaming_example.py
    └── telemetry_example.py
```

This hierarchical structure provides:
1. Better organization of tests by type and component
2. Clear separation between mock tests, integration tests, and API tests
3. Improved discoverability and maintainability
4. Support for both backwards compatibility and new test patterns

## Test Types

### Mock Tests

Mock tests use mocked components to enable testing without external dependencies, particularly API keys. These tests are crucial for CI/CD pipelines and quick validation during development.

**Key Features**:
- No API keys required
- Fast execution
- Tests core logic without external dependencies
- Good for CI/CD pipelines

**Example in `test_mock.py`**:
```python
@mock.patch("atlas.providers.anthropic.Anthropic")
def test_agent_process_message(self, mock_anthropic):
    # Set up mock response
    mock_client = mock.MagicMock()
    mock_client.messages.create.return_value = mock.MagicMock(
        content=[{"text": "This is a mock response."}]
    )
    mock_anthropic.return_value = mock_client

    # Test agent with mock
    agent = AtlasAgent(provider_name="anthropic")
    response = agent.process_message("Test query")

    # Assert the response and that the mock was called
    self.assertEqual("This is a mock response.", response)
    mock_client.messages.create.assert_called_once()
```

### Unit Tests

Unit tests focus on testing individual components in isolation. They verify that each component meets its specifications.

**Key Features**:
- Test individual functions and classes
- Focus on specific behavior
- Fast execution
- Good for catching regression issues

**Example in `test_env.py`**:
```python
def test_get_string(self):
    # Set test environment variable
    os.environ["TEST_STRING"] = "test_value"

    # Test get_string function
    result = env.get_string("TEST_STRING")
    self.assertEqual("test_value", result)

    # Test with default value for missing variable
    result = env.get_string("MISSING_VAR", default="default_value")
    self.assertEqual("default_value", result)
```

### API Tests

API tests verify integration with external services. These tests require valid API keys and may incur costs.

**Key Features**:
- Test actual API integration
- Verify real responses
- Require valid API keys
- May incur costs

**Example in `test_api.py`**:
```python
def test_process_message(self):
    """Test the process_message method with real API."""
    agent = AtlasAgent(
        provider_name="anthropic",
        model_name="claude-3-7-sonnet-20250219"
    )
    query = self.query or "What is the capital of France?"
    response = agent.process_message(query)

    # Verify response is not empty and looks reasonable
    self.assertIsNotNone(response)
    self.assertGreater(len(response), 10)
```

### Integration Tests

Integration tests verify that different components work together correctly.

**Key Features**:
- Test component interactions
- Verify workflow correctness
- More complex test scenarios
- May require API keys depending on the test

## Running Tests

### Using the CLI-based Test Runner

The recommended way to run tests is using the `run_tests.py` script, which uses explicit CLI flags instead of environment variables:

```bash
# Run all unit tests
uv run python -m atlas.scripts.testing.run_tests unit

# Run unit tests for a specific module
uv run python -m atlas.scripts.testing.run_tests unit --module core

# Run mock tests
uv run python -m atlas.scripts.testing.run_tests mock

# Run integration tests
uv run python -m atlas.scripts.testing.run_tests integration

# Run real API tests with confirmation
uv run python -m atlas.scripts.testing.run_tests api --confirm

# Run API tests for a specific provider
uv run python -m atlas.scripts.testing.run_tests api --provider openai --confirm

# Run expensive tests (GPT-4, Claude Opus, etc.)
uv run python -m atlas.scripts.testing.run_tests api --expensive --confirm

# Run multiple test types at once
uv run python -m atlas.scripts.testing.run_tests unit mock integration

# Run all tests (will prompt for confirmation before running API tests)
uv run python -m atlas.scripts.testing.run_tests all
```

### Test Runner Options

The new test runner accepts the following options:

```
positional arguments:
  test_types            Types of tests to run: unit, mock, integration, api, all

options:
  -h, --help            Show help message and exit
  -m, --module MODULE   Module to filter tests by (e.g., 'core', 'models')
  -p, --provider {openai,anthropic,ollama}
                        Provider to filter API tests by
  --confirm             Skip confirmation prompt for API tests
  --expensive           Run expensive API tests (GPT-4, Claude Opus, etc.)
  --cost-limit COST_LIMIT
                        Maximum cost limit for API tests (default: 0.1)
  --enforce-cost-limit  Enforce cost limit by failing tests that exceed it
```

### Legacy Test Runner (Deprecated)

The legacy test runner is still available as `run_tests.py.old` for backwards compatibility:

```bash
# Run all mock tests (no API key required)
uv run python atlas/scripts/testing/run_tests.py.old --test-type mock

# Run unit tests for a specific module
uv run python atlas/scripts/testing/run_tests.py.old --test-type unit --module models
```

### Using unittest Directly

You can also run tests directly using the unittest module:

```bash
# Run a specific test file
uv python -m unittest atlas/tests/test_models.py

# Run all tests
uv python -m unittest discover -s atlas/tests
```

## Writing Tests

Atlas provides standardized test helpers and base classes to make writing tests easier and more consistent. These are available in the `atlas.tests.helpers` module.

### Using Test Decorators

```python
from atlas.tests.helpers import unit_test, mock_test, api_test, integration_test

class TestComponent(unittest.TestCase):
    """Test cases for Component."""

    @unit_test
    def test_component_initialization(self):
        """Test component initialization."""
        component = Component()
        self.assertIsNotNone(component)

    @mock_test
    def test_with_mocked_dependency(self):
        """Test with a mocked dependency."""
        with mock.patch("atlas.module.Dependency") as mock_dep:
            mock_dep.return_value.method.return_value = "mock result"
            component = Component()
            result = component.process("test input")
            self.assertEqual("expected result", result)

    @api_test
    def test_with_real_api(self):
        """Test with real API calls."""
        component = Component(api_key="real-api-key")
        result = component.process("test input")
        self.assertIsNotNone(result)

    @integration_test
    def test_component_integration(self):
        """Test integration with other components."""
        component_a = ComponentA()
        component_b = ComponentB()
        result = component_a.process_with(component_b, "test input")
        self.assertIsNotNone(result)
```

### Using Base Test Classes

```python
from atlas.tests.helpers import (
    TestWithTokenTracking, ProviderTestBase,
    OpenAIProviderTestBase, IntegrationTestBase
)

class TestOpenAIProvider(OpenAIProviderTestBase):
    """Test OpenAI provider implementation."""

    provider_class = OpenAIProvider
    provider_name = "openai"
    default_model = "gpt-3.5-turbo"

    @mock_test
    def test_generate_mocked(self):
        """Test generate method with mocked API."""
        # The base class provides self.provider and mock helpers
        request = self._create_request("Test message")

        with mock.patch("atlas.providers.openai.OpenAI") as mock_openai:
            mock_openai.return_value.chat.completions.create.return_value = mock_completion
            response = self.provider.generate(request)

            self.assertIsNotNone(response)
            self.assertEqual(response.provider, self.provider_name)

    @api_test
    def test_generate_api(self):
        """Test generate method with real API."""
        # This test will only run if RUN_API_TESTS=true and RUN_OPENAI_TESTS=true
        request = self._create_request("Write a single word response", 5)
        response = self.provider.generate(request)

        # Track token usage for cost reporting
        self.track_usage(response)

        self.assertIsNotNone(response.content)
        self.assertLessEqual(response.usage.total_tokens, 20)
```

### Integration Test Template

```python
from atlas.tests.helpers import integration_test, IntegrationTestBase

class TestAgentToolIntegration(IntegrationTestBase):
    """Integration tests for Agent + Tool interactions."""

    def setUp(self):
        """Set up the test with components for integration testing."""
        super().setUp()

        # Create the components to test together
        self.agent = ToolCapableAgent()
        self.tool = CalculatorTool()

        # Register tools with the agent
        self.agent.register_tool(self.tool)

    @integration_test
    def test_agent_uses_tool(self):
        """Test that the agent correctly uses the tool."""
        # Configure response with tool calls
        response_content = """
        Let me calculate that.

        <tool_calls>
        <tool_call name="calculator">
        {"operation": "add", "a": 5, "b": 10}
        </tool_call>
        </tool_calls>
        """

        # Set up the test scenario
        self.mock_provider.generate.return_value = create_mock_response(response_content)

        # Process a request that should trigger tool usage
        request = ModelRequest(messages=[ModelMessage.user("What is 5 + 10?")])
        response = self.agent.process(request)

        # Verify the tool was used correctly
        self.assertIn("15", response.content)
```

## Testing Examples

Atlas includes example scripts in the `examples/` directory, which serve as practical demonstrations of how to use the framework. While these are not formal tests, they provide valuable insights into real-world usage patterns.

You can run examples with or without an API key using the `SKIP_API_KEY_CHECK` environment variable:

```bash
# Run with mock responses (no API key required)
SKIP_API_KEY_CHECK=true uv run python examples/query_example.py

# Run with real API (requires valid API key)
uv run python examples/query_example.py
```

## Testing with Different Providers

Atlas supports testing with different model providers:

```bash
# Test with Anthropic provider
uv run python atlas/scripts/debug/check_models.py --provider anthropic

# Test with OpenAI provider
uv run python atlas/scripts/debug/check_models.py --provider openai

# Test with Ollama provider
uv run python atlas/scripts/debug/check_models.py --provider ollama
```

## API Cost Tracking

When running tests with real API calls, Atlas tracks the cost to help monitor usage:

```
API Usage: 683 input tokens, 502 output tokens
Estimated Cost: $0.009579 (Input: $0.002049, Output: $0.007530)
```

This helps developers understand the cost implications of their tests.

## Best Practices

### For Test Design

1. **Test Isolation**: Each test should run independently without relying on other tests
2. **Descriptive Names**: Use clear, descriptive names for test methods (e.g., `test_retrieval_with_empty_database`)
3. **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification phases
4. **Cover Edge Cases**: Test boundary conditions and exceptional scenarios
5. **Mock External Dependencies**: Use mocks for external services like API calls
6. **Clean Setup/Teardown**: Properly initialize and clean up test resources

### For Test Implementation

1. **Use Helper Methods**: Create helper methods for common test operations
2. **Minimize Test Duplication**: Extract common test logic to helper methods
3. **Focused Assertions**: Use specific assertion methods (e.g., `assertEqual`, `assertTrue`)
4. **Meaningful Error Messages**: Include helpful messages with assertions
5. **Clear Test Data**: Use descriptive and minimal test data
6. **Test One Thing**: Each test method should focus on testing one specific behavior

## Continuous Integration

Atlas is designed to support continuous integration workflows:

1. **Mock Tests for CI**: The mock tests can run without API keys, making them ideal for CI pipelines
2. **API Tests for Release Validation**: API tests can be run before releases to verify integration
3. **Test Runner Integration**: The unified test runner makes it easy to integrate with CI systems

## Related Documentation

- [Query Workflow](../workflows/query.md) - How the query process works
- [Retrieval Workflow](../workflows/retrieval.md) - Details on the retrieval process
- [Getting Started Guide](./getting_started.md) - Basic usage tutorial
- [Example Usage](./examples/) - Example code for common tasks
