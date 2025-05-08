# Atlas Test Suite

This directory contains all tests for the Atlas project. Tests are organized in several categories to ensure comprehensive coverage while managing API costs.

## Test Categories

1. **Unit Tests**: Tests for individual components without external dependencies
2. **Mock Tests**: Tests that use the MockProvider to avoid API calls
3. **Minimal Tests**: Core functionality tests for essential components
4. **API Tests**: Integration tests for Atlas workflows (uses API calls)
5. **Real API Tests**: Tests that directly verify provider implementations using actual API calls

## Running Tests

Atlas includes a unified test runner that can execute different test categories.

### Basic Usage

```bash
# Run mock tests (default, no API costs)
python -m atlas.scripts.testing.run_tests

# Run unit tests
python -m atlas.scripts.testing.run_tests -t unit

# Run minimal tests
python -m atlas.scripts.testing.run_tests -t minimal

# Run a specific module's tests
python -m atlas.scripts.testing.run_tests -t unit -m models
```

### Running Real API Tests

Real API tests make actual calls to provider APIs and may incur costs. These tests are skipped by default and must be explicitly enabled:

```bash
# Set required environment variables
export RUN_API_TESTS=true

# Run basic API tests (uses cheaper models)
python -m atlas.scripts.testing.run_tests -t real_api

# Run all tests including expensive models (GPT-4, Claude Opus)
export RUN_EXPENSIVE_TESTS=true
python -m atlas.scripts.testing.run_tests -t real_api
```

### Provider API Keys

To run real API tests, you need to set the appropriate API keys:

```bash
# For OpenAI tests
export OPENAI_API_KEY=your_api_key_here

# For Anthropic tests
export ANTHROPIC_API_KEY=your_api_key_here

# For Ollama tests, ensure Ollama is running locally
# No API key is required, but the Ollama server must be accessible
```

## Test Structure

- **`test_*.py`**: Unit tests for specific modules
- **`test_mock.py`**: Mock tests that don't require API keys
- **`test_minimal.py`**: Minimal tests for core functionality
- **`test_api.py`**: Integration tests that require API keys
- **`real_api_tests.py`**: Tests that verify actual provider implementations

## Cost Control

The real API tests are designed with cost control in mind:

1. **Tiered Testing**:
   - Most tests use cheaper models (GPT-3.5-Turbo, Claude Haiku)
   - Tests for expensive models require additional opt-in (`RUN_EXPENSIVE_TESTS=true`)

2. **Token Limits**:
   - All tests use minimal token limits (typically 5-10 tokens)
   - Assertions verify that token usage stays below specified thresholds

3. **Simple Prompts**:
   - Tests use simple, short prompts to minimize token usage
   - Streaming tests use the same minimal prompts

## Test Fixtures

Common test utilities are available in `helpers.py`, including:

- Mock response fixtures
- Test environment setup
- Helper functions for working with providers

## Adding New Tests

1. **Unit Tests**: Add to the appropriate test file or create a new one
2. **Real API Tests**: Add to `real_api_tests.py`, using the `api_test` decorator
3. **Expensive Tests**: Use the `expensive_test` decorator for tests that use costly models

When adding real API tests, always:
- Keep token usage to a minimum
- Use cheaper models when possible
- Add appropriate skipping logic for missing API keys
- Track and report token usage