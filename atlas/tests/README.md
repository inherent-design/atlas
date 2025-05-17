# Atlas Tests

This directory contains tests for the Atlas codebase. These tests are organized by component and functionality.

## Test Organization

- **Unit Tests**: Tests for individual components and functions
- **Integration Tests**: Tests for interactions between multiple components
- **Functional Tests**: Tests for end-to-end functionality
- **Schema Validation Tests**: Tests for schema validation and serialization/deserialization

## Running Tests

To run all tests:

```bash
uv run pytest
```

To run a specific test:

```bash
uv run pytest atlas/tests/test_schema_message_validation.py
```

To run tests with verbose output:

```bash
uv run pytest -v
```

## Test Files

### Schema Validation Tests

- `test_schema_message_validation.py`: Tests for message content and model message schema validation
- `test_schema_response_validation.py`: Tests for response-related classes (TokenUsage, CostEstimate, ModelResponse)
- `test_schema_validation_decorators.py`: Tests for validation decorators and utilities

You can run all schema tests with:

```bash
uv run python atlas/tests/run_schema_tests.py
```

## Test Helpers

The tests use various helpers and fixtures to make testing easier and more consistent. These include:

- Mock implementations of providers and components
- Common test fixtures for reuse across tests
- Utilities for creating test data