# Testing Guide

This guide provides a comprehensive overview of the testing approaches and practices for the Atlas framework.

## Testing Philosophy

Atlas follows a robust testing philosophy that includes:

1. **Comprehensive Test Coverage**: Testing all critical components with both unit and integration tests
2. **Mock-First Testing**: Using mocks to enable testing without requiring API keys
3. **Test Isolation**: Ensuring tests are independent and don't rely on shared state
4. **Continuous Validation**: Running tests frequently during development

## Testing Directory Structure

The Atlas testing infrastructure is organized across several directories:

```
atlas/
├── tests/                        # Core test modules
│   ├── __init__.py
│   ├── helpers.py                # Test helpers and utilities
│   ├── test_api.py               # API integration tests (requires API key)
│   ├── test_env.py               # Environment variable tests
│   ├── test_minimal.py           # Minimal functionality tests
│   ├── test_mock.py              # Mock tests (no API key required)
│   └── test_models.py            # Model provider tests
├── scripts/
│   └── testing/                  # Test runner scripts
│       ├── __init__.py
│       └── run_tests.py          # Unified test runner
└── examples/                     # Example usage (not formal tests)
    ├── query_example.py
    ├── retrieval_example.py
    ├── streaming_example.py
    └── telemetry_example.py
```

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
@mock.patch("atlas.models.anthropic.Anthropic")
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

### Using the Unified Test Runner

The recommended way to run tests is using the `run_tests.py` script:

```bash
# Run all mock tests (no API key required)
uv run python atlas/scripts/testing/run_tests.py --test-type mock

# Run unit tests for a specific module
uv run python atlas/scripts/testing/run_tests.py --test-type unit --module models

# Run minimal tests (basic functionality verification)
uv run python atlas/scripts/testing/run_tests.py --test-type minimal

# Run API tests for the base agent (requires API key)
uv run python atlas/scripts/testing/run_tests.py --test-type api --api-test base

# Run API tests with a custom query
uv run python atlas/scripts/testing/run_tests.py --test-type api --api-test base --query "Your query here"

# Run all tests (both mock and real tests)
uv run python atlas/scripts/testing/run_tests.py --test-type all
```

### Test Runner Options

The test runner accepts the following options:

```
-h, --help        Show help message and exit
-t, --test-type   Type of tests to run: unit, mock, minimal, api, or all (default: mock)
-m, --module      Module to test for unit tests (e.g., 'models', 'env')
--api-test        API test to run: base, controller, coordinator, workflows, or all (default: base)
-s, --system-prompt  Path to system prompt file for API tests
-q, --query       Query to test with for API tests
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

### Unit Test Template

```python
import unittest
from unittest import mock

from atlas.module import Component

class TestComponent(unittest.TestCase):
    """Test cases for Component."""

    def setUp(self):
        """Set up test environment."""
        # Initialize test data and resources
        self.component = Component()

    def tearDown(self):
        """Clean up after tests."""
        # Clean up any resources or test state
        pass

    def test_functionality(self):
        """Test specific functionality."""
        # Arrange
        input_data = "test input"
        expected_output = "expected result"

        # Act
        actual_output = self.component.process(input_data)

        # Assert
        self.assertEqual(expected_output, actual_output)
```

### Mock Test Template

```python
import unittest
from unittest import mock

from atlas.module import Component

class TestComponentWithMocks(unittest.TestCase):
    """Test cases for Component using mocks."""

    @mock.patch("atlas.module.Dependency")
    def test_functionality_with_mock(self, mock_dependency):
        """Test functionality with mocked dependency."""
        # Set up mock behavior
        mock_instance = mock.MagicMock()
        mock_instance.method.return_value = "mock result"
        mock_dependency.return_value = mock_instance

        # Create component with mocked dependency
        component = Component()

        # Act
        result = component.process("test input")

        # Assert
        self.assertEqual("expected result", result)
        mock_instance.method.assert_called_once_with("test input")
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
