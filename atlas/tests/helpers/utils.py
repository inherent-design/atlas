"""
Test utilities for Atlas tests.

This module provides utility functions for creating test cases, running tests,
and other test-related operations.
"""

import os
import json
import inspect
import unittest
from typing import Dict, Any, List, Optional, Type, Callable, TypeVar, Union, Tuple

# Type variables
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


# Example-based test utilities
def create_example_test_case(name: str, inputs: Dict[str, Any], expected_outputs: Dict[str, Any], 
                           test_func: Callable[[Dict[str, Any], Dict[str, Any]], None]):
    """Create a test case from examples.
    
    Args:
        name: The name of the test case.
        inputs: Dictionary of test inputs.
        expected_outputs: Dictionary of expected outputs.
        test_func: Function that performs the test.
        
    Returns:
        A test function.
    """
    def example_test_func(self):
        return test_func(self, inputs=inputs, expected_outputs=expected_outputs)
    
    example_test_func.__name__ = f"test_{name}"
    example_test_func.__doc__ = f"Test case for: {name}"
    return example_test_func


def generate_example_tests(test_class: Type[unittest.TestCase], examples: List[Dict[str, Any]], 
                          test_func: Callable[[Any, Dict[str, Any], Dict[str, Any]], None]):
    """Generate test methods from examples.
    
    Args:
        test_class: The test class to add methods to.
        examples: List of example dictionaries with 'name', 'inputs', and 'expected_outputs'.
        test_func: Function that performs the test.
    """
    for example in examples:
        test_method = create_example_test_case(
            example['name'],
            example['inputs'],
            example['expected_outputs'],
            test_func
        )
        setattr(test_class, test_method.__name__, test_method)


# Integration test utilities
def create_integration_test(components: List[Any], test_func: Callable):
    """Create an integration test connecting multiple components.
    
    Args:
        components: List of component instances to connect.
        test_func: Function that performs the test.
        
    Returns:
        A test function.
    """
    from atlas.tests.helpers.decorators import integration_test
    
    @integration_test
    def integration_test_func(self, *args, **kwargs):
        return test_func(self, components=components, *args, **kwargs)
    
    return integration_test_func


# Custom assertions
def assert_response_contains_any(test_case: unittest.TestCase, response: str, 
                               possible_contents: List[str], case_sensitive: bool = False):
    """Assert that a response contains any of the possible content strings.
    
    Args:
        test_case: The test case instance.
        response: The response string.
        possible_contents: List of possible content strings.
        case_sensitive: Whether the comparison should be case-sensitive.
    
    Raises:
        AssertionError: If the response doesn't contain any of the possible contents.
    """
    if not case_sensitive:
        response = response.lower()
        possible_contents = [content.lower() for content in possible_contents]
    
    for content in possible_contents:
        if content in response:
            return
    
    test_case.fail(f"Response does not contain any of the expected contents: {possible_contents}")


def assert_response_contains_all(test_case: unittest.TestCase, response: str, 
                               required_contents: List[str], case_sensitive: bool = False):
    """Assert that a response contains all of the required content strings.
    
    Args:
        test_case: The test case instance.
        response: The response string.
        required_contents: List of required content strings.
        case_sensitive: Whether the comparison should be case-sensitive.
    
    Raises:
        AssertionError: If the response doesn't contain all of the required contents.
    """
    if not case_sensitive:
        response = response.lower()
        required_contents = [content.lower() for content in required_contents]
    
    missing_contents = []
    for content in required_contents:
        if content not in response:
            missing_contents.append(content)
    
    if missing_contents:
        test_case.fail(f"Response is missing the following required contents: {missing_contents}")


def assert_response_is_similar(test_case: unittest.TestCase, actual: str, expected: str, 
                             threshold: float = 0.7):
    """Assert that a response is similar to the expected response.
    
    This uses a simple similarity metric based on word overlap.
    
    Args:
        test_case: The test case instance.
        actual: The actual response string.
        expected: The expected response string.
        threshold: The minimum similarity threshold (0.0 to 1.0).
    
    Raises:
        AssertionError: If the similarity is below the threshold.
    """
    actual_words = set(actual.lower().split())
    expected_words = set(expected.lower().split())
    
    if not expected_words:
        test_case.fail("Expected response is empty")
    
    overlap = len(actual_words.intersection(expected_words))
    similarity = overlap / len(expected_words)
    
    if similarity < threshold:
        test_case.fail(
            f"Response similarity {similarity:.2f} is below threshold {threshold:.2f}\n"
            f"Actual: {actual}\n"
            f"Expected: {expected}"
        )


# Fixture loading utilities
def load_fixture(fixture_path: str) -> Any:
    """Load a fixture file.
    
    Args:
        fixture_path: The path to the fixture file, relative to the fixtures directory.
        
    Returns:
        The loaded fixture data.
    
    Raises:
        FileNotFoundError: If the fixture file doesn't exist.
    """
    base_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "fixtures"
    )
    full_path = os.path.join(base_path, fixture_path)
    
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Fixture file not found: {full_path}")
    
    with open(full_path, 'r') as f:
        if full_path.endswith('.json'):
            return json.load(f)
        else:
            return f.read()


def get_response_fixture(provider: str, filename: str) -> Dict[str, Any]:
    """Load a response fixture for a specific provider.
    
    Args:
        provider: The provider name (e.g., 'openai', 'anthropic', 'ollama').
        filename: The fixture filename.
        
    Returns:
        The loaded response fixture data.
    """
    return load_fixture(os.path.join("responses", provider, filename))


def get_document_fixture(filename: str) -> str:
    """Load a document fixture.
    
    Args:
        filename: The fixture filename.
        
    Returns:
        The loaded document fixture data.
    """
    return load_fixture(os.path.join("documents", filename))


def get_tool_fixture(filename: str) -> Dict[str, Any]:
    """Load a tool fixture.
    
    Args:
        filename: The fixture filename.
        
    Returns:
        The loaded tool fixture data.
    """
    return load_fixture(os.path.join("tools", filename))