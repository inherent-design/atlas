"""
Test decorators for Atlas tests.

This module provides decorators for categorizing and controlling test execution
based on the test type and requirements.
"""

import os
import functools
import unittest
from typing import Callable, TypeVar, Any

# Type variable for function decorators
F = TypeVar('F', bound=Callable[..., Any])


# Basic Test Decorators
def unit_test(f: F) -> F:
    """Decorator for unit tests that don't require external dependencies.
    
    Unit tests are always run by default as they are fast and don't require
    external resources.
    
    Args:
        f: The test function to decorate.
        
    Returns:
        The decorated test function.
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    wrapper.__doc__ = f.__doc__ or ""
    wrapper.__doc__ += "\n\nThis is a unit test."
    setattr(wrapper, 'test_type', 'unit')
    return wrapper


def mock_test(f: F) -> F:
    """Decorator for tests that use mocked responses.
    
    Mock tests don't make real API calls and should always run unless explicitly
    disabled with SKIP_MOCK_TESTS=true.
    
    Args:
        f: The test function to decorate.
        
    Returns:
        The decorated test function.
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if os.environ.get("SKIP_MOCK_TESTS", "").lower() == "true":
            return unittest.skip("Mock tests disabled - set SKIP_MOCK_TESTS=false to enable")(f)(*args, **kwargs)
        return f(*args, **kwargs)
    wrapper.__doc__ = f.__doc__ or ""
    wrapper.__doc__ += "\n\nThis test uses mocked responses and does not make API calls."
    setattr(wrapper, 'test_type', 'mock')
    return wrapper


def integration_test(f: F) -> F:
    """Decorator for integration tests that connect multiple components.
    
    Integration tests verify that different components work together correctly.
    They are run only when RUN_INTEGRATION_TESTS=true is set.
    
    Args:
        f: The test function to decorate.
        
    Returns:
        The decorated test function.
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not os.environ.get("RUN_INTEGRATION_TESTS", "").lower() == "true":
            return unittest.skip("Integration tests disabled - set RUN_INTEGRATION_TESTS=true to enable")(f)(*args, **kwargs)
        return f(*args, **kwargs)
    wrapper.__doc__ = f.__doc__ or ""
    wrapper.__doc__ += "\n\nThis is an integration test that connects multiple components."
    setattr(wrapper, 'test_type', 'integration')
    return wrapper


def api_test(f: F) -> F:
    """Decorator for tests that make real API calls.
    
    API tests make real calls to external services and may incur costs.
    They are run only when RUN_API_TESTS=true is set.
    
    Args:
        f: The test function to decorate.
        
    Returns:
        The decorated test function.
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not os.environ.get("RUN_API_TESTS", "").lower() == "true":
            return unittest.skip("API tests disabled - set RUN_API_TESTS=true to enable")(f)(*args, **kwargs)
        return f(*args, **kwargs)
    wrapper.__doc__ = f.__doc__ or ""
    wrapper.__doc__ += "\n\nThis test makes real API calls and may incur costs."
    setattr(wrapper, 'test_type', 'api')
    return wrapper


def expensive_test(f: F) -> F:
    """Decorator for tests that make expensive API calls.
    
    Expensive tests make API calls that may incur significant costs.
    They are run only when RUN_EXPENSIVE_TESTS=true is set.
    
    Args:
        f: The test function to decorate.
        
    Returns:
        The decorated test function.
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not os.environ.get("RUN_EXPENSIVE_TESTS", "").lower() == "true":
            return unittest.skip("Expensive tests disabled - set RUN_EXPENSIVE_TESTS=true to enable")(f)(*args, **kwargs)
        return f(*args, **kwargs)
    wrapper.__doc__ = f.__doc__ or ""
    wrapper.__doc__ += "\n\nThis test makes expensive API calls and may incur significant costs."
    setattr(wrapper, 'test_type', 'expensive')
    return wrapper


# Provider-specific test decorators
def openai_test(f: F) -> F:
    """Decorator for tests that specifically use OpenAI API.
    
    These tests require an OpenAI API key and are run only when RUN_API_TESTS=true
    and RUN_OPENAI_TESTS=true are set.
    
    Args:
        f: The test function to decorate.
        
    Returns:
        The decorated test function.
    """
    @functools.wraps(f)
    @api_test
    def wrapper(*args, **kwargs):
        if not os.environ.get("RUN_OPENAI_TESTS", "").lower() == "true":
            return unittest.skip("OpenAI tests disabled - set RUN_OPENAI_TESTS=true to enable")(f)(*args, **kwargs)
        if not os.environ.get("OPENAI_API_KEY"):
            return unittest.skip("OpenAI API key not set - set OPENAI_API_KEY environment variable")(f)(*args, **kwargs)
        return f(*args, **kwargs)
    wrapper.__doc__ = f.__doc__ or ""
    wrapper.__doc__ += "\n\nThis test uses the OpenAI API and requires an API key."
    setattr(wrapper, 'test_type', 'api')
    setattr(wrapper, 'provider', 'openai')
    return wrapper


def anthropic_test(f: F) -> F:
    """Decorator for tests that specifically use Anthropic API.
    
    These tests require an Anthropic API key and are run only when RUN_API_TESTS=true
    and RUN_ANTHROPIC_TESTS=true are set.
    
    Args:
        f: The test function to decorate.
        
    Returns:
        The decorated test function.
    """
    @functools.wraps(f)
    @api_test
    def wrapper(*args, **kwargs):
        if not os.environ.get("RUN_ANTHROPIC_TESTS", "").lower() == "true":
            return unittest.skip("Anthropic tests disabled - set RUN_ANTHROPIC_TESTS=true to enable")(f)(*args, **kwargs)
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return unittest.skip("Anthropic API key not set - set ANTHROPIC_API_KEY environment variable")(f)(*args, **kwargs)
        return f(*args, **kwargs)
    wrapper.__doc__ = f.__doc__ or ""
    wrapper.__doc__ += "\n\nThis test uses the Anthropic API and requires an API key."
    setattr(wrapper, 'test_type', 'api')
    setattr(wrapper, 'provider', 'anthropic')
    return wrapper


def ollama_test(f: F) -> F:
    """Decorator for tests that specifically use Ollama API.
    
    These tests require Ollama to be running locally and are run only when 
    RUN_API_TESTS=true and RUN_OLLAMA_TESTS=true are set.
    
    Args:
        f: The test function to decorate.
        
    Returns:
        The decorated test function.
    """
    @functools.wraps(f)
    @api_test
    def wrapper(*args, **kwargs):
        if not os.environ.get("RUN_OLLAMA_TESTS", "").lower() == "true":
            return unittest.skip("Ollama tests disabled - set RUN_OLLAMA_TESTS=true to enable")(f)(*args, **kwargs)
        
        # Try to check if Ollama is running
        try:
            import requests
            response = requests.get("http://localhost:11434/api/version", timeout=1)
            if response.status_code != 200:
                return unittest.skip("Ollama server not running at http://localhost:11434")(f)(*args, **kwargs)
        except (ImportError, requests.RequestException):
            return unittest.skip("Ollama server not running or requests module not available")(f)(*args, **kwargs)
            
        return f(*args, **kwargs)
    wrapper.__doc__ = f.__doc__ or ""
    wrapper.__doc__ += "\n\nThis test uses the Ollama API and requires Ollama to be running locally."
    setattr(wrapper, 'test_type', 'api')
    setattr(wrapper, 'provider', 'ollama')
    return wrapper


# Utility decorators
def todo_test(reason: str):
    """Decorator for tests that are not yet implemented or need fixing.
    
    Args:
        reason: The reason why the test is marked as TODO.
        
    Returns:
        A decorator function.
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return unittest.skip(f"TODO: {reason}")(f)(*args, **kwargs)
        wrapper.__doc__ = f.__doc__ or ""
        wrapper.__doc__ += f"\n\nTODO: {reason}"
        return wrapper
    return decorator


def flaky_test(max_retries: int = 3):
    """Decorator for tests that may occasionally fail due to external factors.
    
    Args:
        max_retries: Maximum number of retry attempts.
        
    Returns:
        A decorator function.
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        # Re-raise the exception on the last attempt
                        raise
                    print(f"Test {f.__name__} failed on attempt {attempt + 1}, retrying...")
            return f(*args, **kwargs)  # This should never be reached
        wrapper.__doc__ = f.__doc__ or ""
        wrapper.__doc__ += f"\n\nThis test is marked as flaky and may be retried up to {max_retries} times."
        return wrapper
    return decorator