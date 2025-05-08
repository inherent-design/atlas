"""
Logging configuration for Atlas.

This module provides centralized configuration for logging throughout
the Atlas framework, with special handling for noisy dependencies.
"""

import logging
import os
import sys
from typing import Optional, Dict, Any, List

try:
    import structlog
    import rich.logging
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False

from atlas.core import env


def configure_logging(
    level: Optional[str] = None,
    format_string: Optional[str] = None,
    enable_rich: bool = True,
    quiet_loggers: Optional[List[str]] = None,
) -> None:
    """Configure logging for Atlas and its dependencies.

    Args:
        level: Logging level (default: from ATLAS_LOG_LEVEL or INFO)
        format_string: Format string for logging (default: standard format)
        enable_rich: Whether to use rich for console output
        quiet_loggers: List of loggers to silence (only showing errors or higher)
    """
    # Determine log level (priority: argument > env var > default)
    if level is None:
        level = env.get_string("ATLAS_LOG_LEVEL", "INFO").upper()

    numeric_level = getattr(logging, level, logging.INFO)

    # Default quiet loggers if not specified
    if quiet_loggers is None:
        quiet_loggers = [
            "chromadb",            # Very noisy by default
            "uvicorn",             # Underlying ChromaDB server
            "httpx",               # HTTP client used by many dependencies
            "opentelemetry",       # OTEL is very verbose
        ]

    # Default format string
    if format_string is None:
        format_string = "%(levelname)s | %(name)s | %(message)s"

    # Configure the root logger
    if STRUCTLOG_AVAILABLE and enable_rich:
        # Use structlog with rich for prettier console output
        rich_handler = rich.logging.RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_time=True,
            level=numeric_level,
        )
        handlers = [rich_handler]
    else:
        # Standard logging configuration
        handlers = [logging.StreamHandler(sys.stdout)]

    # Configure the root logger
    logging.basicConfig(
        level=numeric_level,
        format=format_string,
        handlers=handlers,
        force=True,  # Override any existing configuration
    )

    # Silence noisy loggers (only show ERROR or higher)
    for logger_name in quiet_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.ERROR)

    # Set up structlog if available
    if STRUCTLOG_AVAILABLE:
        configure_structlog()
        
    # Log configuration details
    root_logger = logging.getLogger()
    root_logger.debug(f"Logging configured at level {level}")
    root_logger.debug(f"Silenced loggers (ERROR level only): {', '.join(quiet_loggers)}")


def configure_structlog() -> None:
    """Configure structlog for structured logging."""
    if not STRUCTLOG_AVAILABLE:
        return

    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.

    This is a wrapper around logging.getLogger that ensures logging is configured.

    Args:
        name: Name of the logger.

    Returns:
        Logger instance.
    """
    # Ensure logging is configured
    if logging.getLogger().level == logging.NOTSET:
        configure_logging()
    
    return logging.getLogger(name)


def get_structlog_logger(name: str) -> Any:
    """Get a structlog logger with the given name.

    Args:
        name: Name of the logger.

    Returns:
        structlog.BoundLogger instance or standard logger if structlog not available.
    """
    if not STRUCTLOG_AVAILABLE:
        return get_logger(name)
    
    # Ensure logging is configured
    if logging.getLogger().level == logging.NOTSET:
        configure_logging()
    
    return structlog.get_logger(name)