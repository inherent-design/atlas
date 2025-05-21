"""
Test configuration and fixtures for Atlas tests.

This module provides common fixtures and test configuration
used across multiple test files for the Atlas framework.
"""

import contextlib
import logging
import os
import sys
from typing import Any, AsyncGenerator, Generator

import pytest

# Add project root to path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from atlas.core.errors import AtlasError, ErrorCategory, ErrorSeverity

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Silence some noisy loggers during tests
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


@pytest.fixture
def temp_env() -> Generator[None, None, None]:
    """Create a temporary environment for testing.

    This fixture allows setting temporary environment variables for the duration of a test
    and restores the original environment when the test completes.
    """
    old_environ = dict(os.environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_environ)


@pytest.fixture
def mock_error() -> AtlasError:
    """Create a mock AtlasError for testing."""
    return AtlasError(
        message="Test error",
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.UNKNOWN,
        details={"test": "value"},
    )


@contextlib.contextmanager
def assert_raises_atlas_error(
    error_type: type[AtlasError],
    message_contains: str | None = None,
    severity: ErrorSeverity | None = None,
    category: ErrorCategory | None = None,
) -> Generator[None, None, None]:
    """Assert that a specific Atlas error is raised with expected attributes.

    Args:
        error_type: The expected error type
        message_contains: Optional substring expected in the error message
        severity: Optional expected error severity
        category: Optional expected error category

    Raises:
        AssertionError: If the expected error wasn't raised or didn't match expectations
    """
    try:
        yield
        pytest.fail(f"Expected {error_type.__name__} to be raised, but no exception was raised")
    except error_type as e:
        if message_contains is not None and message_contains not in e.message:
            pytest.fail(
                f"Expected error message to contain '{message_contains}', but got '{e.message}'"
            )
        if severity is not None and e.severity != severity:
            pytest.fail(f"Expected error severity {severity}, but got {e.severity}")
        if category is not None and e.category != category:
            pytest.fail(f"Expected error category {category}, but got {e.category}")
    except Exception as e:
        pytest.fail(f"Expected {error_type.__name__} to be raised, but got {type(e).__name__}")


@pytest.fixture
def raises_atlas_error() -> Any:
    """Fixture that provides the assert_raises_atlas_error context manager."""
    return assert_raises_atlas_error


@pytest.fixture
async def async_temp_env() -> AsyncGenerator[None, None]:
    """Create a temporary environment for async testing."""
    old_environ = dict(os.environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_environ)
