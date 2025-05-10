"""
CLI module for Atlas.

This module provides reusable CLI argument parsing and configuration
components for use in the main Atlas CLI and example applications.
"""

from atlas.cli.parser import create_parser, parse_cli_args
from atlas.cli.config import create_provider_options_from_args

__all__ = [
    "create_parser",
    "parse_cli_args",
    "create_provider_options_from_args",
]