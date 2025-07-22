"""
Pytest configuration file for Atlas tests.

This file contains global pytest fixtures and configuration that apply to all tests.
"""

import logging
from collections.abc import Generator

import pytest


@pytest.fixture(autouse=True)
def suppress_logs() -> Generator[None]:
    """Suppress log output during test execution to reduce noise.

    This fixture runs automatically for all tests. It temporarily
    raises the logging level to ERROR to avoid printing debugging
    and info messages during test runs.

    It restores the previous log level after the test completes.
    """
    # Save previous log levels
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    previous_levels = {logger: logger.level for logger in loggers}
    root_level = logging.root.level

    # Set all loggers to ERROR level to suppress output
    for logger in loggers:
        logger.setLevel(logging.ERROR)
    logging.root.setLevel(logging.ERROR)

    try:
        # Run the test
        yield
    finally:
        # Restore previous log levels
        for logger, level in previous_levels.items():
            logger.setLevel(level)
        logging.root.setLevel(root_level)


@pytest.fixture
def log_level(request):
    """Set a specific log level for tests that need it.

    Usage:
        @pytest.mark.parametrize('log_level', ['DEBUG'], indirect=True)
        def test_with_debug_logs():
            # This test will have logs at DEBUG level
            ...
    """
    level = getattr(logging, request.param) if hasattr(request, "param") else logging.INFO
    prev_level = logging.root.level
    logging.root.setLevel(level)

    try:
        yield level
    finally:
        logging.root.setLevel(prev_level)
