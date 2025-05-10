"""
CLI argument parsing for Atlas.

This module provides utilities for creating and configuring the Atlas CLI
command-line argument parser.
"""

import argparse
from typing import Optional, List, Dict, Any


def create_parser() -> argparse.ArgumentParser:
    """Create the Atlas CLI argument parser.
    
    Returns:
        Configured argparse.ArgumentParser instance
    """
    # Create main parser
    parser = argparse.ArgumentParser(
        description="Atlas: Advanced Multi-Modal Learning & Guidance Framework",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Create subparsers for different modes
    mode_subparsers = parser.add_subparsers(
        dest="mode",
        title="operation modes",
        description="Select an operation mode for Atlas",
        help="Mode of operation",
        required=True,
    )

    # Common parser for shared arguments
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "-s", "--system-prompt", type=str, help="Path to system prompt file"
    )
    common_parser.add_argument(
        "-c",
        "--collection",
        type=str,
        default="atlas_knowledge_base",
        help="Name of the ChromaDB collection to use",
    )
    common_parser.add_argument(
        "--db-path", type=str, help="Path to ChromaDB database directory"
    )

    # Add provider group to common parser
    add_provider_group(common_parser)

    # CLI mode subparser
    cli_parser = mode_subparsers.add_parser(
        "cli",
        parents=[common_parser],
        help="Interactive CLI mode",
        description="Run Atlas in interactive CLI mode with conversation history",
    )

    # Query mode subparser
    query_parser = mode_subparsers.add_parser(
        "query",
        parents=[common_parser],
        help="Process a single query",
        description="Run Atlas in query mode to process a single query (non-interactive)",
    )
    query_parser.add_argument(
        "-q", "--query", type=str, required=True, help="Single query to process"
    )

    # Ingest mode subparser
    ingest_parser = mode_subparsers.add_parser(
        "ingest",
        parents=[common_parser],
        help="Ingest documents",
        description="Run Atlas in document ingestion mode to process files into the knowledge base",
    )
    ingest_parser.add_argument(
        "-d", "--directory", type=str, help="Directory to ingest documents from"
    )
    ingest_parser.add_argument(
        "-r", "--recursive", action="store_true", help="Recursively process directories"
    )
    ingest_parser.add_argument(
        "--embedding", 
        type=str,
        choices=["default", "anthropic", "hybrid"],
        default="default",
        help="Embedding strategy to use (default uses ChromaDB's built-in, anthropic uses Anthropic's API)"
    )
    ingest_parser.add_argument(
        "--no-dedup",
        action="store_true",
        help="Disable content deduplication during ingestion"
    )
    ingest_parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch directory for changes and ingest new/modified files automatically"
    )

    # Controller mode subparser (experimental)
    controller_parser = mode_subparsers.add_parser(
        "controller",
        parents=[common_parser],
        help="[Experimental] Multi-agent controller mode",
        description="Run Atlas in controller mode to coordinate multiple worker agents (experimental feature)",
    )
    controller_parser.add_argument(
        "--parallel",
        action="store_true",
        help="Enable parallel processing with LangGraph",
    )
    controller_parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Number of worker agents to spawn",
    )
    controller_parser.add_argument(
        "--workflow",
        choices=["rag", "advanced", "custom"],
        default="rag",
        help="LangGraph workflow to use",
    )
    controller_parser.add_argument(
        "--experimental",
        action="store_true",
        help="Acknowledge this is an experimental feature",
        required=True,
    )

    # Worker mode subparser (experimental)
    worker_parser = mode_subparsers.add_parser(
        "worker",
        parents=[common_parser],
        help="[Experimental] Worker agent mode",
        description="Run Atlas in worker mode as a specialized agent (experimental feature)",
    )
    worker_parser.add_argument(
        "--worker-type",
        choices=["retrieval", "analysis", "draft"],
        default="retrieval",
        help="Worker type to use",
    )
    worker_parser.add_argument(
        "--experimental",
        action="store_true",
        help="Acknowledge this is an experimental feature",
        required=True,
    )

    return parser


def add_provider_group(parser: argparse.ArgumentParser) -> None:
    """Add provider-related arguments to a parser.
    
    Args:
        parser: Parser to add provider group to
    """
    # Model provider options
    model_group = parser.add_argument_group("Model Provider Options")
    model_group.add_argument(
        "--provider",
        type=str,
        choices=["anthropic", "openai", "ollama", "mock"],
        default="anthropic",
        help="Model provider to use (auto-detected if only model is specified)",
    )
    model_group.add_argument(
        "--model",
        type=str,
        help="Model to use (provider-specific, e.g., claude-3-opus-20240229, gpt-4o, llama3). "
             "If provided without --provider, the provider will be auto-detected"
    )
    model_group.add_argument(
        "--capability",
        type=str,
        choices=["inexpensive", "efficient", "premium", "vision", "standard"],
        default="inexpensive",
        help="Model capability to use when no specific model is provided (default: inexpensive)",
    )
    model_group.add_argument(
        "--models",
        action="store_true",
        help="List available models for the specified provider and exit",
    )
    model_group.add_argument(
        "--max-tokens", 
        type=int, 
        default=2000,
        help="Maximum tokens in model responses"
    )

    # Ollama-specific options
    ollama_group = parser.add_argument_group("Ollama Provider Options")
    ollama_group.add_argument(
        "--ollama-api-endpoint",
        type=str,
        help="Ollama API endpoint URL (default: http://localhost:11434/api)",
    )
    ollama_group.add_argument(
        "--ollama-connect-timeout",
        type=float,
        help="Connection timeout for Ollama server in seconds (default: 2)",
    )
    ollama_group.add_argument(
        "--ollama-request-timeout",
        type=float,
        help="Request timeout for Ollama API calls in seconds (default: 60)",
    )


def parse_cli_args(args: Optional[List[str]] = None) -> Dict[str, Any]:
    """Parse command-line arguments.
    
    Args:
        args: Command-line arguments to parse, or None to use sys.argv
        
    Returns:
        Dictionary of parsed arguments
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    # Convert to dictionary
    return vars(parsed_args)