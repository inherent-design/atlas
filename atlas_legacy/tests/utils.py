"""
Utility functions and fixtures for Atlas tests.

This module provides common test utilities, fixtures, and helper functions
that can be used across multiple test modules.
"""

import uuid
from unittest.mock import MagicMock

import pytest


def generate_uuid() -> str:
    """Generate a random UUID string.

    Returns:
        A random UUID as a string.
    """
    return str(uuid.uuid4())


@pytest.fixture
def mock_command():
    """Create a mock command object.

    Returns:
        A MagicMock configured to behave like a Command.
    """
    command = MagicMock()
    command.execute.return_value = "mock_result"
    command.is_undoable = True
    command.command_id = generate_uuid()
    command.name = "MockCommand"
    command.parameters = {}
    command.target_service = "test-service"
    command.metadata = {}
    return command


@pytest.fixture
def mock_failing_command():
    """Create a mock command that fails when executed.

    Returns:
        A MagicMock configured to raise an exception when executed.
    """
    command = MagicMock()
    command.execute.side_effect = ValueError("Command execution failed")
    command.is_undoable = False
    command.command_id = generate_uuid()
    command.name = "FailingCommand"
    command.parameters = {}
    command.target_service = "test-service"
    command.metadata = {}
    return command


@pytest.fixture
def capture_logs(caplog):
    """Configure caplog for consistent log capture.

    Args:
        caplog: The pytest caplog fixture.

    Returns:
        The configured caplog fixture.
    """
    caplog.set_level("DEBUG")
    return caplog


class CommandTestHelper:
    """Helper class for command-related tests."""

    @staticmethod
    def create_test_function(return_value="test_result"):
        """Create a test function with configurable return value.

        Args:
            return_value: The value the function should return.

        Returns:
            A callable function.
        """

        def test_func(*args, **kwargs):
            return return_value

        # Set name for better function identification
        test_func.__name__ = "test_func"

        return test_func

    @staticmethod
    def create_failing_function(error_message="Function error"):
        """Create a function that raises an exception.

        Args:
            error_message: The error message to include.

        Returns:
            A callable function that raises a ValueError.
        """

        def failing_func(*args, **kwargs):
            raise ValueError(error_message)

        # Set name for better function identification
        failing_func.__name__ = "failing_func"

        return failing_func


# Add more utility functions and fixtures as needed
