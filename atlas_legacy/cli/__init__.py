"""
CLI module for Atlas.

This module provides reusable CLI argument parsing and configuration
components for use in the main Atlas CLI and example applications,
including both a traditional command-line interface and a rich
textual user interface.
"""

from atlas.cli.config import create_provider_options_from_args
from atlas.cli.parser import create_parser, parse_cli_args

# Conditionally import Textual UI components if dependencies are available
try:
    from atlas.cli.textual import run_atlas_ui

    HAS_TEXTUAL = True
except ImportError:
    HAS_TEXTUAL = False
    run_atlas_ui = None

__all__ = [
    "create_parser",
    "create_provider_options_from_args",
    "parse_cli_args",
]

if HAS_TEXTUAL:
    __all__.append("run_atlas_ui")
