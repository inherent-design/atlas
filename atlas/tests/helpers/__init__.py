"""
Atlas Test Helpers

This package provides standardized test helpers, utilities, and base classes for
Atlas tests. It helps create more consistent, maintainable, and resilient tests.
"""

# Import decorators
from atlas.tests.helpers.decorators import (
    unit_test, mock_test, integration_test, api_test, expensive_test,
    openai_test, anthropic_test, ollama_test,
    todo_test, flaky_test
)

# Import base classes
from atlas.tests.helpers.base_classes import (
    TestWithTokenTracking, ProviderTestBase,
    OpenAIProviderTestBase, AnthropicProviderTestBase, OllamaProviderTestBase,
    AgentTestBase, ToolTestBase, IntegrationTestBase
)

# Import mock utilities
from atlas.tests.helpers.mocks import (
    create_mock_message, create_mock_request, create_mock_response,
    create_mock_streaming_response, MockProvider,
    mock_openai_response, mock_anthropic_response, mock_ollama_response,
    mock_streaming_ollama_response,
    mock_openai_api, mock_anthropic_api, mock_ollama_api
)

# Import test utilities
from atlas.tests.helpers.utils import (
    create_example_test_case, generate_example_tests, create_integration_test,
    assert_response_contains_any, assert_response_contains_all, assert_response_is_similar,
    load_fixture, get_response_fixture, get_document_fixture, get_tool_fixture
)

__all__ = [
    # Decorators
    'unit_test', 'mock_test', 'integration_test', 'api_test', 'expensive_test',
    'openai_test', 'anthropic_test', 'ollama_test',
    'todo_test', 'flaky_test',
    
    # Base classes
    'TestWithTokenTracking', 'ProviderTestBase',
    'OpenAIProviderTestBase', 'AnthropicProviderTestBase', 'OllamaProviderTestBase',
    'AgentTestBase', 'ToolTestBase', 'IntegrationTestBase',
    
    # Mock utilities
    'create_mock_message', 'create_mock_request', 'create_mock_response',
    'create_mock_streaming_response', 'MockProvider',
    'mock_openai_response', 'mock_anthropic_response', 'mock_ollama_response',
    'mock_streaming_ollama_response',
    'mock_openai_api', 'mock_anthropic_api', 'mock_ollama_api',
    
    # Test utilities
    'create_example_test_case', 'generate_example_tests', 'create_integration_test',
    'assert_response_contains_any', 'assert_response_contains_all', 'assert_response_is_similar',
    'load_fixture', 'get_response_fixture', 'get_document_fixture', 'get_tool_fixture'
]