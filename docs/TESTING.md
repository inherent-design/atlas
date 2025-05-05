# Testing in Atlas

This document describes the testing approach used in the Atlas project, including directory structure, test types, and how to run tests.

## Testing Directory Structure

Atlas uses a standardized approach to testing:

- **`atlas/tests/`**: Contains all unit tests and integration tests
  - Test files are named with a `test_` prefix (e.g., `test_models.py`, `test_env.py`)
  - Each test file focuses on testing a specific module or component
  - Tests use the Python `unittest` framework
  - Mock tests that don't require API keys are available for CI/CD

- **`atlas/scripts/testing/`**: Contains utility scripts for running tests and test-related tasks
  - `run_tests.py`: Script for running all tests or specific test types
  - `test_providers.py`: Script for testing different model providers
  - `test_query.py`: Script for testing individual queries

## Test Types

### Unit Tests

Unit tests focus on testing individual components in isolation. They are located in the `atlas/tests/` directory and follow the naming pattern `test_*.py`.

Examples:
- `test_models.py`: Tests for the models module
- `test_env.py`: Tests for the environment variable handling module

Unit tests use the `unittest` framework and should be designed to run quickly without external dependencies when possible.

### Integration Tests

Integration tests verify that different components work together correctly. These are also located in the `atlas/tests/` directory.

Examples:
- `test_api.py`: Tests the API integration
- `test_minimal.py`: Tests minimal functionality with real components

### Mock Tests

Mock tests use mocked components to test functionality without requiring external services or API keys. This is particularly useful for CI/CD pipelines.

Examples:
- `test_mock.py`: Mock tests with no API dependencies
- Mock provider implementations in `test_models.py`

## Running Tests

### Using the Test Runner Script

The recommended way to run tests is using the `run_tests.py` script:

```bash
# Run all tests
uv run python atlas/scripts/testing/run_tests.py

# Run only the models tests
uv run python atlas/scripts/testing/run_tests.py --module models

# Run only the mock tests
uv run python atlas/scripts/testing/run_tests.py --type mock
```

### Using unittest Directly

You can also run tests directly using the unittest module:

```bash
# Run a specific test file
uv run python -m unittest atlas/tests/test_models.py

# Run all tests
uv run python -m unittest discover -s atlas/tests
```

### Running Provider Tests

To test specific model providers:

```bash
# Test with Anthropic provider
uv run python atlas/scripts/testing/test_providers.py --provider anthropic

# Test with OpenAI provider
uv run python atlas/scripts/testing/test_providers.py --provider openai

# Test with Ollama provider
uv run python atlas/scripts/testing/test_providers.py --provider ollama
```

## Writing Tests

### Unit Test Template

```python
"""
Unit tests for [module name].

This module provides tests for [brief description].
"""

import unittest
from unittest import mock

from atlas.[module] import [functions, classes]

class Test[ModuleName](unittest.TestCase):
    """Test cases for [module name]."""

    def setUp(self):
        """Set up test environment."""
        # Set up test environment, create test data, etc.
        pass

    def tearDown(self):
        """Clean up after tests."""
        # Clean up after tests
        pass

    def test_[functionality](self):
        """Test [specific functionality]."""
        # Test implementation
        self.assertEqual(expected, actual)

if __name__ == "__main__":
    unittest.main()
```

### Mock Test Template

```python
"""
Mock tests for [module name].

This module provides tests for [brief description] using mocks.
"""

import unittest
from unittest import mock

from atlas.[module] import [functions, classes]

# Define mock classes
class Mock[ClassName]:
    """Mock implementation of [ClassName]."""
    def method(self):
        return "mock result"

class Test[ModuleName]WithMocks(unittest.TestCase):
    """Test cases for [module name] using mocks."""

    @mock.patch("atlas.[module].[dependency]")
    def test_[functionality](self, mock_dependency):
        """Test [specific functionality] with mocks."""
        # Set up mock behavior
        mock_dependency.return_value = "mock value"
        
        # Test implementation
        result = function_under_test()
        self.assertEqual("expected result", result)
        mock_dependency.assert_called_once_with(expected_args)

if __name__ == "__main__":
    unittest.main()
```

## Test Coverage

We aim for high test coverage, especially for critical components. When writing tests, consider:

1. **Happy path**: Test normal operation with valid inputs
2. **Edge cases**: Test boundary conditions and special cases
3. **Error handling**: Test how the code handles errors and invalid inputs
4. **Resource cleanup**: Test that resources are properly cleaned up

## CI/CD Integration

The test suite is designed to work with CI/CD pipelines. The mock tests can run without API keys, making them suitable for automated testing in CI/CD environments.

## Best Practices

1. **Isolation**: Tests should be isolated and not depend on each other's state
2. **Mocking**: Use mocks for external dependencies to keep tests fast and reliable
3. **Clarity**: Test names should clearly describe what is being tested
4. **Coverage**: Aim to test all code paths, including error handling
5. **Speed**: Tests should run quickly to encourage frequent testing
6. **Documentation**: Document any non-obvious test setup or assertions
7. **Environment**: Tests should clean up after themselves and not leave side effects