"""
CLI parser configuration for Atlas.

This module contains the command-line argument parsing configuration for the Atlas CLI.
"""

import argparse
import os
from typing import Any

from atlas.core.env import get_available_providers


def add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add common arguments to a parser.

    Args:
        parser: The parser to add arguments to
    """
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the log level",
    )


def add_provider_args(parser: argparse.ArgumentParser) -> None:
    """Add provider-related arguments to a parser.

    Args:
        parser: The parser to add arguments to
    """
    # Get available providers
    available_providers_dict = get_available_providers()

    # Convert to list for command-line choices
    available_providers = list(available_providers_dict.keys())

    # Ensure 'mock' is always included in available providers for CLI
    if "mock" not in available_providers:
        available_providers.append("mock")

    parser.add_argument(
        "--provider",
        type=str,
        default="mock",
        choices=available_providers,
        help="The provider to use for queries",
    )

    parser.add_argument(
        "--models",
        action="store_true",
        help="List available models for the specified provider",
    )

    parser.add_argument(
        "--model",
        type=str,
        help="The model to use",
    )

    parser.add_argument(
        "--capability",
        type=str,
        default="standard",
        choices=["efficient", "standard", "premium", "vision"],
        help="The capability level required",
    )


def add_query_args(parser: argparse.ArgumentParser) -> None:
    """Add query-related arguments to a parser.

    Args:
        parser: The parser to add arguments to
    """
    parser.add_argument(
        "-q",
        "--query",
        type=str,
        help="The query to run",
    )

    parser.add_argument(
        "--stream",
        action="store_true",
        help="Stream the response",
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        default=2000,
        help="Maximum number of tokens to generate",
    )


def add_knowledge_args(parser: argparse.ArgumentParser) -> None:
    """Add knowledge-related arguments to a parser.

    Args:
        parser: The parser to add arguments to
    """
    parser.add_argument(
        "-kb",
        "--knowledge-base",
        type=str,
        help="The knowledge base to use",
    )

    parser.add_argument(
        "--db-path",
        type=str,
        default=os.path.expanduser("~/.atlas/chroma"),
        help="Path to the vector database",
    )


def add_cli_args(parser: argparse.ArgumentParser) -> None:
    """Add CLI-specific arguments to a parser.

    Args:
        parser: The parser to add arguments to
    """
    # Mode selection
    parser.add_argument(
        "--mode",
        type=str,
        default="cli",
        choices=["cli", "query", "ingest", "controller", "worker"],
        help="Operation mode to run",
    )

    # Query mode args
    add_provider_args(parser)
    add_query_args(parser)
    add_knowledge_args(parser)

    # Ingest mode args
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        help="Directory containing documents to ingest",
    )

    parser.add_argument(
        "--collection",
        type=str,
        default="atlas_knowledge_base",
        help="Collection name for the vector database",
    )

    parser.add_argument(
        "--recursive",
        action="store_true",
        default=True,
        help="Recursively process directories during ingestion",
    )

    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch directory for changes during ingestion",
    )

    parser.add_argument(
        "--embedding",
        type=str,
        default="default",
        help="Embedding strategy for document ingestion",
    )

    parser.add_argument(
        "--no-dedup",
        action="store_true",
        help="Disable deduplication during ingestion",
    )

    # Controller and worker mode args
    parser.add_argument(
        "--experimental",
        action="store_true",
        help="Enable experimental features",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Number of worker agents for controller mode",
    )

    parser.add_argument(
        "--worker-type",
        type=str,
        default="retrieval",
        choices=["retrieval", "analysis", "draft"],
        help="Worker type for worker mode",
    )

    # Tool execution mode args
    parser.add_argument(
        "--tool-name",
        type=str,
        help="Name of the tool to execute",
    )

    parser.add_argument(
        "--tool-args",
        type=str,
        help="JSON string of arguments for the tool",
    )

    # System prompt selection
    parser.add_argument(
        "--system-prompt",
        type=str,
        help="Path to system prompt file",
    )

    return parser


def create_parser() -> argparse.ArgumentParser:
    """Create an argument parser for the Atlas CLI.

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Atlas - Advanced LLM Agent System",
    )

    # Add common arguments
    add_common_args(parser)

    # Add CLI arguments
    add_cli_args(parser)

    return parser


def parse_cli_args(args: list | None = None) -> dict[str, Any]:
    """Parse command-line arguments.

    Args:
        args: Optional list of arguments to parse

    Returns:
        Dictionary of parsed arguments
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    # Convert to dictionary
    return vars(parsed_args)
