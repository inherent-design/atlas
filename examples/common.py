"""
Common utilities for Atlas examples.

This module provides shared functionality for Atlas examples, including:
- Consistent logging configuration
- Common CLI argument parsing
- Utilities for example setup and execution
- Database path and collection management
- Test data ingestion verification

All examples should use these utilities for consistent behavior and appearance.
"""

import os
import sys
import argparse
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Tuple

# Add parent directory to path so we can import atlas from the development directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import Atlas utilities
from atlas.core import logging, env
from atlas.providers import ProviderOptions
from atlas.providers.resolver import resolve_provider_options, create_provider_from_options
from atlas.cli.config import create_provider_options_from_args


# Default example database and collection
EXAMPLE_DB_PATH = os.path.join(os.path.dirname(__file__), "example_data", "db")
EXAMPLE_COLLECTION = "atlas_examples"
EXAMPLE_DOCS_PATH = os.path.join(os.path.dirname(__file__), "..", "docs")
DATA_MARKER_FILE = os.path.join(EXAMPLE_DB_PATH, ".data_ingested")


def get_example_db_path() -> str:
    """Get the path to the example database.
    
    This uses a separate database for examples to avoid conflicts with the main Atlas database.
    
    Returns:
        Path to the example database
    """
    # Create directory if it doesn't exist
    os.makedirs(EXAMPLE_DB_PATH, exist_ok=True)
    return EXAMPLE_DB_PATH


def get_example_collection() -> str:
    """Get the name of the example collection.
    
    Returns:
        Name of the example collection
    """
    return EXAMPLE_COLLECTION


def configure_example_logging(quiet_loggers: Optional[List[str]] = None) -> None:
    """Configure logging for examples using Atlas's centralized logging system.
    
    Args:
        quiet_loggers: Additional loggers to silence beyond the defaults
    """
    # Default quiet loggers for examples
    default_quiet = ["chromadb", "uvicorn", "httpx", "opentelemetry"]
    
    # Add any additional loggers to quiet
    if quiet_loggers:
        default_quiet.extend(quiet_loggers)
    
    # Set up logging with centralized configuration - same as in main.py
    logging.configure_logging(
        level=os.environ.get("ATLAS_LOG_LEVEL", "INFO"),
        enable_rich=True,
        quiet_loggers=default_quiet
    )


def get_base_argument_parser(description: str) -> argparse.ArgumentParser:
    """Create base argument parser with standard Atlas options.
    
    Args:
        description: Description of the example
        
    Returns:
        ArgumentParser with standard Atlas options
    """
    parser = argparse.ArgumentParser(description=description)
    
    # Provider selection options (same as in CLI)
    parser.add_argument(
        "--provider", 
        type=str, 
        help="Model provider to use (e.g., anthropic, openai, ollama, mock)"
    )
    parser.add_argument(
        "--model", 
        type=str, 
        help="Specific model to use (auto-detects provider if not specified)"
    )
    parser.add_argument(
        "--capability", 
        type=str, 
        choices=["inexpensive", "efficient", "premium", "vision", "standard"],
        default="inexpensive",
        help="Model capability to use (used when model not specified)"
    )
    
    # Database and collection options
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,  # Will be set to example DB path if not specified
        help="Path to the database (default: example database)"
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=None,  # Will be set to example collection if not specified
        help="Name of the collection to use (default: example collection)"
    )
    parser.add_argument(
        "--use-system-db",
        action="store_true",
        help="Use the system database path instead of the example database"
    )
    
    # Additional common options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging"
    )
    
    return parser


def setup_example(description: str, setup_func: Optional[Callable] = None) -> argparse.Namespace:
    """Set up an example with standard configuration.
    
    This function:
    1. Configures logging
    2. Creates and parses arguments
    3. Runs any example-specific setup
    4. Prints a header for the example
    5. Sets up database paths
    
    Args:
        description: Description of the example
        setup_func: Optional function to run for example-specific setup
        
    Returns:
        Parsed arguments
    """
    # Configure logging
    configure_example_logging()
    logger = logging.get_logger(__name__)
    
    # Create and parse arguments
    parser = get_base_argument_parser(description)
    
    # Allow the setup function to add arguments
    if setup_func:
        setup_func(parser)
    
    args = parser.parse_args()
    
    # Adjust log level if verbose flag is set
    if args.verbose:
        os.environ["ATLAS_LOG_LEVEL"] = "DEBUG"
        logging.configure_logging(level="DEBUG")
        logger.debug("Debug logging enabled")
    
    # Set up database paths if not specified
    if not args.db_path:
        if args.use_system_db:
            # Use system database path from environment or default
            args.db_path = env.get_string("ATLAS_DB_PATH")
            if not args.db_path:
                home_dir = os.path.expanduser("~")
                args.db_path = os.path.join(home_dir, "atlas_chroma_db")
            logger.debug(f"Using system database path: {args.db_path}")
        else:
            # Use example database path
            args.db_path = get_example_db_path()
            logger.debug(f"Using example database path: {args.db_path}")
    
    # Set up collection name if not specified
    if not args.collection:
        if args.use_system_db:
            # Use system collection from environment or default
            args.collection = env.get_string("ATLAS_COLLECTION_NAME", "atlas_knowledge_base")
            logger.debug(f"Using system collection: {args.collection}")
        else:
            # Use example collection
            args.collection = get_example_collection()
            logger.debug(f"Using example collection: {args.collection}")
    
    # Print header
    print("\n" + "="*50)
    print(f"     {description}")
    print("="*50 + "\n")
    
    return args


def ensure_example_data(args: argparse.Namespace, force_ingestion: bool = False) -> Tuple[bool, int]:
    """Ensure example data is present in the database.
    
    This function:
    1. Checks if data has been ingested
    2. If not, ingests example data
    3. Verifies document count
    
    Args:
        args: Parsed arguments
        force_ingestion: Whether to force ingestion even if data marker exists
        
    Returns:
        (was_data_ingested, document_count)
    """
    logger = logging.get_logger(__name__)
    
    # Create marker file directory if needed
    os.makedirs(os.path.dirname(DATA_MARKER_FILE), exist_ok=True)
    
    # Import here to avoid circular imports
    from atlas.knowledge.retrieval import KnowledgeBase
    from atlas.knowledge.ingest import DocumentProcessor
    
    # Check if we're using the example database and collection
    is_using_example_data = (
        not args.use_system_db and
        (args.db_path == get_example_db_path() or args.db_path is None) and
        (args.collection == get_example_collection() or args.collection is None)
    )
    
    if not is_using_example_data:
        # Using custom database/collection, don't manage example data
        logger.debug("Using custom database or collection, skipping example data management")
        try:
            kb = KnowledgeBase(
                collection_name=args.collection,
                db_path=args.db_path
            )
            return False, kb.collection.count()
        except Exception as e:
            logger.error(f"Error checking document count: {e}")
            return False, 0
    
    # Initialize knowledge base for document count
    try:
        kb = KnowledgeBase(
            collection_name=args.collection,
            db_path=args.db_path
        )
        document_count = kb.collection.count()
    except Exception as e:
        logger.error(f"Error checking document count: {e}")
        document_count = 0
    
    # Check if data has been ingested and there are documents
    data_ingested = os.path.exists(DATA_MARKER_FILE)
    
    if data_ingested and document_count > 0 and not force_ingestion:
        logger.info(f"Example data already ingested ({document_count} documents)")
        return False, document_count
    
    # Ingestion needed
    logger.info("Ingesting example data...")
    print("\nIngesting example data...")
    
    # Ensure example docs path exists
    if not os.path.exists(EXAMPLE_DOCS_PATH):
        logger.error(f"Example docs path not found: {EXAMPLE_DOCS_PATH}")
        return False, 0
    
    # Get list of files to ingest
    processor = DocumentProcessor(
        collection_name=args.collection,
        db_path=args.db_path
    )
    
    # Process example docs (use docs directory by default)
    num_processed = processor.process_directory(EXAMPLE_DOCS_PATH, recursive=True)
    
    # Check if ingestion was successful
    if num_processed > 0:
        # Create marker file to indicate data has been ingested
        with open(DATA_MARKER_FILE, 'w') as f:
            f.write(f"Data ingested at {os.path.basename(EXAMPLE_DOCS_PATH)} with {num_processed} files")
        
        logger.info(f"Ingestion complete: {num_processed} files processed")
        print(f"Ingestion complete: {num_processed} files processed")
        
        # Verify document count
        document_count = processor.collection.count()
        print(f"Documents in database: {document_count}")
        
        return True, document_count
    else:
        logger.error("No files processed during ingestion")
        return False, 0


def create_provider_from_args(args: argparse.Namespace) -> Any:
    """Create a provider from command line arguments.
    
    Args:
        args: Command line arguments
        
    Returns:
        ModelProvider instance
    """
    # Create options from args (using same method as CLI)
    options = create_provider_options_from_args(args)
    
    # Resolve options
    resolved = resolve_provider_options(options)
    
    # Create and return provider
    return create_provider_from_options(resolved)


def print_example_footer() -> None:
    """Print a footer for the example."""
    print("\n" + "="*50)
    print("          Example Complete")
    print("="*50 + "\n")


def handle_example_error(logger, error: Exception, message: str, user_message: str = None, exit_code: int = None) -> None:
    """Handle errors in examples consistently.

    This function:
    1. Logs the error with stack trace
    2. Prints a user-friendly message
    3. Optionally exits with specified code

    Args:
        logger: The logger instance to use
        error: The exception that occurred
        message: Error message for the log
        user_message: Optional additional message to display to the user
        exit_code: If provided, call sys.exit with this code
    """
    import sys

    # Log the error with full traceback
    logger.exception(f"{message}: {error}")

    # Print user-facing error message
    print(f"Error: {message}: {error}")

    # Print additional information if provided
    if user_message:
        print(user_message)

    # Exit if requested
    if exit_code is not None:
        sys.exit(exit_code)


def print_section(title: str) -> None:
    """Print a section heading with consistent formatting.

    Used to visually separate different sections in example output.

    Args:
        title: The title of the section
    """
    print("\n" + "-"*50)
    print(title)
    print("-"*50)


def highlight(text: str, color: str = "yellow") -> str:
    """Highlight text in the terminal with ANSI color codes.

    Args:
        text: The text to highlight
        color: Color name (red, green, yellow, blue, purple, cyan)

    Returns:
        Text with ANSI color codes
    """
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "end": "\033[0m"
    }
    return f"{colors.get(color, colors['yellow'])}{text}{colors['end']}"


def create_providers_for_examples(provider_names: Optional[List[str]] = None,
                                 ensure_mock: bool = True,
                                 min_providers: int = 1) -> List[Any]:
    """Create provider instances for examples.

    This function creates a list of provider instances based on available providers,
    ensuring that at least the specified minimum number of providers are returned.
    If fewer providers are available than the minimum, mock providers are added.

    Args:
        provider_names: Optional list of specific provider names to include
        ensure_mock: Whether to always include a mock provider for testing
        min_providers: Minimum number of providers to return

    Returns:
        List of provider instances
    """
    from atlas.providers import create_provider, discover_providers, ModelProvider

    # Import here to avoid circular imports
    logger = logging.get_logger(__name__)

    # Discover available providers
    available = discover_providers()

    # If specific providers are requested, filter available providers
    if provider_names:
        # Convert to list if it's a comma-separated string
        if isinstance(provider_names, str):
            provider_names = [p.strip() for p in provider_names.split(",")]

        # Filter available providers
        available = {k: v for k, v in available.items() if k in provider_names}

    # Start with mock provider if requested or if we need to ensure minimum providers
    providers = []

    if ensure_mock or (len(available) < min_providers and "mock" in available):
        mock_provider = create_provider(provider_name="mock", model_name="mock-standard")
        providers.append(mock_provider)
        logger.info(f"Added mock provider with model: {mock_provider.model_name}")

    # Add other available providers
    for provider_name, models in available.items():
        if provider_name != "mock" or (provider_name == "mock" and not any(p.name == "mock" for p in providers)):
            try:
                provider = create_provider(provider_name=provider_name)
                providers.append(provider)
                logger.info(f"Added {provider_name} provider with model: {provider.model_name}")
            except Exception as e:
                logger.warning(f"{provider_name} provider not added: {e}")

    # Add more mock providers if needed to reach minimum
    if len(providers) < min_providers:
        # Add mock-advanced if we already have mock-standard
        if len(providers) == 1 and providers[0].name == "mock" and providers[0].model_name == "mock-standard":
            provider = create_provider(provider_name="mock", model_name="mock-advanced")
        else:
            provider = create_provider(provider_name="mock", model_name="mock-standard")

        providers.append(provider)
        logger.info(f"Added mock provider with model: {provider.model_name}")

    return providers


def create_provider_group_for_examples(provider_names: Optional[List[str]] = None,
                                      selection_strategy: str = "failover",
                                      name: str = "example_provider_group",
                                      min_providers: int = 2) -> Any:
    """Create a provider group for examples.

    Args:
        provider_names: Optional list of specific provider names to include
        selection_strategy: Strategy for selecting providers (failover, round_robin, etc.)
        name: Name for the provider group
        min_providers: Minimum number of providers to include in the group

    Returns:
        ProviderGroup instance
    """
    from atlas.providers import create_provider_group

    # Create provider instances
    providers = create_providers_for_examples(
        provider_names=provider_names,
        ensure_mock=True,
        min_providers=min_providers
    )

    # Create provider group with the specified strategy
    return create_provider_group(
        providers=providers,
        selection_strategy=selection_strategy,
        name=name
    )