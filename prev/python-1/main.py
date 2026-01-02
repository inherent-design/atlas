#!/usr/bin/env python3
"""
Atlas: Advanced Multi-Modal Learning & Guidance Framework
Main entry point for the Atlas module.
"""

import os
import sys
import time
from typing import Any

# Set tokenizers parallelism to false to avoid warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Ensure atlas package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging early
from atlas.core import logging

logger = logging.get_logger(__name__)

# Set up logging with appropriate settings
logging.configure_logging(
    level=os.environ.get("ATLAS_LOG_LEVEL", "INFO"),
    enable_rich=True,
    quiet_loggers=["chromadb", "uvicorn", "httpx", "opentelemetry"],
)

# Import CLI utilities
from atlas.agents.base import AtlasAgent
from atlas.cli.config import (
    create_atlas_config_from_args,
    create_provider_options_from_args,
)
from atlas.cli.parser import parse_cli_args
from atlas.core import env

# Import core components
from atlas.core.config import AtlasConfig
from atlas.knowledge.ingest import DocumentProcessor


def validate_provider_api_key(provider_name: str = "anthropic") -> bool:
    """Validate that the API key for the given provider is available.

    Args:
        provider_name: The model provider to validate (anthropic, openai, ollama, mock)

    Returns:
        Boolean indicating if the provider can be used (API key available or not needed).
    """
    # The mock provider doesn't need an API key
    if provider_name == "mock":
        logger.info("Using mock provider (no API key required)")
        return True

    # Import environment utilities
    from atlas.core import env

    # Ollama doesn't need an API key, just a running server
    if provider_name == "ollama":
        logger.warning("Ollama server doesn't appear to be running at http://localhost:11434")
        logger.warning("Please start Ollama before running Atlas with Ollama provider.")
        logger.warning("Example: ollama serve")
        logger.warning("Continuing anyway, but expect connection errors...")
        return True  # Still allow Ollama even if server is not running

    # Check if the provider is available
    provider_status = env.validate_provider_requirements([provider_name])

    if not provider_status.get(provider_name, False):
        # API key is required but not available
        env_var_name = f"{provider_name.upper()}_API_KEY"
        logger.error(f"{env_var_name} environment variable is not set.")
        logger.error(f"Please set it before running Atlas with {provider_name} provider.")
        logger.error(f"Example: export {env_var_name}=your_api_key_here")
        return False

    return True


def ingest_documents(args: dict[str, Any]) -> bool:
    """Ingest documents from the specified directory.

    Args:
        args: Command-line arguments as a dictionary

    Returns:
        True if ingestion was successful, False otherwise
    """
    # Create config with command line parameters
    config_dict = create_atlas_config_from_args(args)
    config = AtlasConfig(**config_dict)

    # Get db_path from config
    db_path = config.db_path

    # Set up embedding and other parameters
    anthropic_api_key = None
    if args.get("provider") == "anthropic" and args.get("embedding") == "anthropic":
        # If we're using Anthropic for embeddings, get the API key
        anthropic_api_key = env.get_api_key("anthropic")
        if not anthropic_api_key:
            logger.error("Anthropic API key required for Anthropic embeddings")
            return False

    # Check embedding strategy
    embedding_strategy = args.get("embedding", "default")
    enable_deduplication = not args.get("no_dedup", False)
    watch_mode = args.get("watch", False)

    # Process directory or default directories
    if not args.get("directory"):
        # Use default directories if none specified
        default_dirs = [
            "./src-markdown/prev/v1",
            "./src-markdown/prev/v2",
            "./src-markdown/prev/v3",
            "./src-markdown/prev/v4",
            "./src-markdown/prev/v5",
            "./src-markdown/quantum",
        ]

        logger.info("No directory specified. Using default directories:")
        for dir_path in default_dirs:
            logger.info(f"  - {dir_path}")

        logger.info(f"Using ChromaDB at: {db_path}")
        logger.info(f"Embedding strategy: {embedding_strategy}")

        processor = DocumentProcessor(
            anthropic_api_key=anthropic_api_key,
            collection_name=args.get("collection", "atlas_knowledge_base"),
            db_path=db_path,
            enable_deduplication=enable_deduplication,
            embedding_strategy=embedding_strategy,
        )

        for dir_path in default_dirs:
            if os.path.exists(dir_path):
                logger.info(f"Ingesting documents from {dir_path}")
                processor.process_directory(dir_path, recursive=args.get("recursive", True))
            else:
                logger.warning(f"Directory not found: {dir_path}")
    else:
        logger.info(f"Ingesting documents from {args['directory']}")
        logger.info(f"Using ChromaDB at: {db_path}")
        logger.info(f"Embedding strategy: {embedding_strategy}")

        # If watch mode is enabled, use live ingestion
        if watch_mode:
            try:
                from atlas.knowledge.ingest import live_ingest_directory

                logger.info("Starting live ingestion (watch mode)")
                processor = live_ingest_directory(
                    directory=args["directory"],
                    collection_name=args.get("collection", "atlas_knowledge_base"),
                    db_path=db_path,
                    recursive=args.get("recursive", True),
                    enable_deduplication=enable_deduplication,
                )

                # Keep process running until interrupted
                logger.info("Press Ctrl+C to stop watching...")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Stopping watchers...")
                    processor.stop_watching()
                    logger.info("Watching stopped")
            except Exception as e:
                logger.error(f"Error in watch mode: {e}")
                return False
        else:
            # Standard one-time processing
            processor = DocumentProcessor(
                anthropic_api_key=anthropic_api_key,
                collection_name=args.get("collection", "atlas_knowledge_base"),
                db_path=db_path,
                enable_deduplication=enable_deduplication,
                embedding_strategy=embedding_strategy,
            )

            processor.process_directory(args["directory"], recursive=args.get("recursive", True))

    return True


def run_cli_mode(args: dict[str, Any]) -> bool:
    """Run Atlas in interactive CLI mode.

    Args:
        args: Command-line arguments as a dictionary

    Returns:
        True if CLI mode ran successfully, False otherwise
    """
    logger.info("\nAtlas CLI Mode")
    logger.info("-------------")

    # Create provider options from CLI arguments
    from atlas.providers import create_provider_from_options

    provider_options = create_provider_options_from_args(args)

    # Create config
    config_dict = create_atlas_config_from_args(args)
    config = AtlasConfig(**config_dict)

    # Determine if streaming should be enabled
    use_streaming = args.get("stream", False)  # Default to non-streaming mode for stability

    try:
        # Create provider with auto-detection and resolution
        provider = create_provider_from_options(provider_options)

        # Log provider and model information
        logger.info(f"Using {provider.name} provider with model: {provider.model_name}")
        if args.get("capability") and not args.get("model"):
            logger.info(f"Model selected based on '{args['capability']}' capability")

        # Initialize agent with the provider
        agent = AtlasAgent(
            system_prompt_file=args.get("system_prompt"),
            collection_name=args.get("collection", "atlas_knowledge_base"),
            config=config,
            provider=provider,
        )
    except Exception as e:
        logger.error(f"Error initializing provider: {e}")
        logger.warning("Falling back to default configuration")

        # Fall back to default configuration
        try:
            # Create minimal provider options
            minimal_options = create_provider_options_from_args(
                {"provider": args.get("provider", "anthropic")}
            )
            provider = create_provider_from_options(minimal_options)

            agent = AtlasAgent(
                system_prompt_file=args.get("system_prompt"),
                collection_name=args.get("collection", "atlas_knowledge_base"),
                config=config,
                provider=provider,
            )
        except Exception as second_e:
            logger.error(f"Second error: {second_e}")
            logger.warning("Falling back to minimal configuration")

            # Last resort - use minimal configuration
            agent = AtlasAgent(
                system_prompt_file=args.get("system_prompt"),
                collection_name=args.get("collection", "atlas_knowledge_base"),
            )

    logger.info("Atlas is ready. Type 'exit' or 'quit' to end the session.")
    logger.info(f"Streaming mode is {'enabled' if use_streaming else 'disabled'}.")
    logger.info("Commands: '/stream on|off' to toggle streaming, '/clear' to reset conversation")
    logger.info("---------------------------------------------------")

    # We'll define the streaming callback inline instead to avoid scope issues

    while True:
        # Get user input
        try:
            # Try to avoid EOF issues with a more robust input approach
            print("\nYou: ", end="", flush=True)
            user_input = sys.stdin.readline().strip()

            # Check for exit command
            if user_input.lower() in ["exit", "quit"]:
                print("\nGoodbye!")
                break

            # Skip empty inputs
            if not user_input:
                continue

            # Handle special commands
            if user_input.startswith("/"):
                if user_input.startswith("/stream"):
                    parts = user_input.split()
                    if len(parts) > 1:
                        if parts[1].lower() in ["on", "true", "yes", "enable"]:
                            use_streaming = True
                            print("\nStreaming mode enabled.")
                        elif parts[1].lower() in ["off", "false", "no", "disable"]:
                            use_streaming = False
                            print("\nStreaming mode disabled.")
                        else:
                            print("\nInvalid option. Use '/stream on' or '/stream off'.")
                    else:
                        print(
                            f"\nStreaming is currently {'enabled' if use_streaming else 'disabled'}."
                        )
                    continue
                elif user_input == "/clear":
                    agent.reset_conversation()
                    print("\nConversation history cleared.")
                    continue
                else:
                    print(f"\nUnknown command: {user_input}")
                    continue

            # Process the message with or without streaming
            if use_streaming:
                print("\nAtlas: ", end="", flush=True)

                # Create a simpler streaming approach
                def simple_streaming_callback(delta, full_text):
                    print(delta, end="", flush=True)

                try:
                    # Just run with streaming without log modifications
                    response = agent.process_message_streaming(
                        user_input, simple_streaming_callback
                    )

                    # Add a new line after streaming
                    print("")

                except Exception as e:
                    # Fall back to non-streaming if any error occurs
                    logger.warning(f"Streaming error: {e}")
                    logger.warning("Falling back to non-streaming mode.")
                    use_streaming = False
                    # Process with regular mode
                    response = agent.process_message(user_input)
                    print(response)
            else:
                # Process message without streaming
                response = agent.process_message(user_input)
                print(f"\nAtlas: {response}")

        except KeyboardInterrupt:
            print("\nSession interrupted. Goodbye!")
            break
        except EOFError:
            print("\nEOF detected. Exiting gracefully.")
            break
        except Exception as e:
            print(f"\nUnexpected error: {e!s}")
            print("Let's continue with a fresh conversation.")
            # Reinitialize with minimal configuration
            agent = AtlasAgent(
                system_prompt_file=args.get("system_prompt"),
                collection_name=args.get("collection", "atlas_knowledge_base"),
            )

    return True


def run_query_mode(args: dict[str, Any]) -> bool:
    """Run Atlas in query mode (single query, non-interactive).

    Args:
        args: Command-line arguments as a dictionary

    Returns:
        True if query was processed successfully, False otherwise
    """
    # Create provider options from CLI arguments
    from atlas.providers import create_provider_from_options

    provider_options = create_provider_options_from_args(args)

    # Create config
    config_dict = create_atlas_config_from_args(args)
    config = AtlasConfig(**config_dict)

    print(f"Processing query: {args['query']}")

    try:
        # Create provider with auto-detection and resolution
        provider = create_provider_from_options(provider_options)

        # Log the provider and model information
        print(f"Using {provider.name} provider with model: {provider.model_name}")
        if args.get("capability") and not args.get("model"):
            print(f"Model selected based on '{args['capability']}' capability")

        # Initialize agent with the provider
        agent = AtlasAgent(
            system_prompt_file=args.get("system_prompt"),
            collection_name=args.get("collection", "atlas_knowledge_base"),
            config=config,
            provider=provider,
        )
    except Exception as e:
        print(f"Error initializing provider: {e}")
        print("Falling back to default configuration")

        try:
            # Create minimal provider options
            minimal_options = create_provider_options_from_args(
                {"provider": args.get("provider", "anthropic")}
            )
            provider = create_provider_from_options(minimal_options)

            agent = AtlasAgent(
                system_prompt_file=args.get("system_prompt"),
                collection_name=args.get("collection", "atlas_knowledge_base"),
                config=config,
                provider=provider,
            )
        except Exception as second_e:
            print(f"Second error: {second_e}")
            print("Falling back to minimal configuration")

            # Last resort - try minimal config
            agent = AtlasAgent(
                system_prompt_file=args.get("system_prompt"),
                collection_name=args.get("collection", "atlas_knowledge_base"),
            )

    response = agent.process_message(args["query"])
    print(f"Response: {response}")
    return True


def run_controller_mode(args: dict[str, Any]) -> bool:
    """Run Atlas in controller mode (experimental).

    Args:
        args: Command-line arguments as a dictionary

    Returns:
        True if controller mode ran successfully, False otherwise
    """
    print("\nAtlas Controller Mode (Experimental)")
    print("-----------------------------------")

    if not args.get("experimental", False):
        print("ERROR: Controller mode is experimental. Use --experimental flag to acknowledge.")
        return False

    try:
        # Import here to avoid circular imports
        from atlas.orchestration.coordinator import AgentCoordinator

        # Create provider options from CLI arguments
        from atlas.providers import create_provider_from_options

        provider_options = create_provider_options_from_args(args)

        # Try to create the provider for diagnostic purposes
        try:
            provider = create_provider_from_options(provider_options)
            print(f"Using {provider.name} provider with model: {provider.model_name}")
        except Exception as e:
            print(f"Warning: Could not initialize provider: {e}")
            print("Controller will use default provider")

        # Initialize coordinator with parallel processing if enabled
        coordinator = AgentCoordinator(
            system_prompt_file=args.get("system_prompt"),
            collection_name=args.get("collection", "atlas_knowledge_base"),
            worker_count=args.get("workers", 3),
        )

        print(f"Controller initialized with {args.get('workers', 3)} workers.")
        print("⚠️  NOTE: Controller mode is experimental and may not work as expected.")
        print("      The multi-agent architecture is still under development.")
        print("Atlas is ready. Type 'exit' or 'quit' to end the session.")
        print("---------------------------------------------------")

        while True:
            # Get user input
            try:
                # Try to avoid EOF issues with a more robust input approach
                print("\nYou: ", end="", flush=True)
                user_input = sys.stdin.readline().strip()

                # Check for exit command
                if user_input.lower() in ["exit", "quit"]:
                    print("\nGoodbye!")
                    break

                # Skip empty inputs
                if not user_input:
                    continue

                # Process the message and get response
                response = coordinator.process_message(user_input)

                # Display the response
                print(f"\nAtlas: {response}")
            except KeyboardInterrupt:
                print("\nSession interrupted. Goodbye!")
                break
            except EOFError:
                print("\nEOF detected. Exiting gracefully.")
                break
            except Exception as e:
                print(f"\nUnexpected error in controller mode: {e!s}")
                print("Let's continue with a fresh conversation.")
                coordinator = AgentCoordinator(
                    system_prompt_file=args.get("system_prompt"),
                    collection_name=args.get("collection", "atlas_knowledge_base"),
                    worker_count=args.get("workers", 3),
                )

        return True
    except Exception as e:
        print(f"Error initializing controller mode: {e!s}")
        print("Falling back to CLI mode...")
        return run_cli_mode(args)


def run_worker_mode(args: dict[str, Any]) -> bool:
    """Run Atlas in worker mode (experimental).

    Args:
        args: Command-line arguments as a dictionary

    Returns:
        True if worker mode ran successfully, False otherwise
    """
    print("\nAtlas Worker Mode (Experimental)")
    print("--------------------------------")

    if not args.get("experimental", False):
        print("ERROR: Worker mode is experimental. Use --experimental flag to acknowledge.")
        return False

    try:
        # Import here to avoid circular imports
        from atlas.agents.worker import AnalysisWorker, DraftWorker, RetrievalWorker

        # Create provider options from CLI arguments
        from atlas.providers import create_provider_from_options

        provider_options = create_provider_options_from_args(args)

        try:
            # Create provider with auto-detection and resolution
            provider = create_provider_from_options(provider_options)

            # Log the provider and model information
            print(f"Using {provider.name} provider with model: {provider.model_name}")
            if args.get("capability") and not args.get("model"):
                print(f"Model selected based on '{args['capability']}' capability")

        except Exception as e:
            print(f"Error creating provider: {e}")
            print("Continuing with original model/provider settings")
            provider = None

        # Get worker type from args
        worker_type = args.get("worker_type", "retrieval")

        print(f"Initializing {worker_type} worker...")

        # Import Union type for type annotation

        # Create appropriate worker type based on worker_type
        if worker_type == "analysis":
            if provider:
                worker = AnalysisWorker(
                    system_prompt_file=args.get("system_prompt"),
                    collection_name=args.get("collection", "atlas_knowledge_base"),
                    provider=provider,
                )
            else:
                worker = AnalysisWorker(
                    system_prompt_file=args.get("system_prompt"),
                    collection_name=args.get("collection", "atlas_knowledge_base"),
                    provider_name=args.get("provider", "anthropic"),
                    model_name=args.get("model"),
                )
            worker_desc = "Analysis Worker: Specializes in query analysis and information needs identification"
        elif worker_type == "draft":
            if provider:
                worker = DraftWorker(
                    system_prompt_file=args.get("system_prompt"),
                    collection_name=args.get("collection", "atlas_knowledge_base"),
                    provider=provider,
                )
            else:
                worker = DraftWorker(
                    system_prompt_file=args.get("system_prompt"),
                    collection_name=args.get("collection", "atlas_knowledge_base"),
                    provider_name=args.get("provider", "anthropic"),
                    model_name=args.get("model"),
                )
            worker_desc = "Draft Worker: Specializes in generating draft responses"
        else:  # Default to retrieval worker
            if provider:
                worker = RetrievalWorker(
                    system_prompt_file=args.get("system_prompt"),
                    collection_name=args.get("collection", "atlas_knowledge_base"),
                    provider=provider,
                )
            else:
                worker = RetrievalWorker(
                    system_prompt_file=args.get("system_prompt"),
                    collection_name=args.get("collection", "atlas_knowledge_base"),
                    provider_name=args.get("provider", "anthropic"),
                    model_name=args.get("model"),
                )
            worker_desc = "Retrieval Worker: Specializes in document retrieval and summarization"

        print(f"Worker initialized: {worker_desc}")
        print("⚠️  NOTE: Worker mode is experimental and may not work as expected.")
        print("Atlas worker is ready. Type 'exit' or 'quit' to end the session.")
        print("-----------------------------------------------------------")

        # Simple CLI loop for worker
        while True:
            try:
                # Try to avoid EOF issues with a more robust input approach
                print("\nTask: ", end="", flush=True)
                user_input = sys.stdin.readline().strip()

                # Check for exit command
                if user_input.lower() in ["exit", "quit"]:
                    print("\nWorker shutting down. Goodbye!")
                    break

                # Skip empty inputs
                if not user_input:
                    continue

                # Create a simple task and process it
                task = {"task_id": "cli_task", "query": user_input}

                result = worker.process_task(task)
                print(f"\nResult: {result.get('result', 'No result')}")

            except KeyboardInterrupt:
                print("\nWorker interrupted. Shutting down!")
                break
            except EOFError:
                print("\nEOF detected. Exiting gracefully.")
                break
            except Exception as e:
                print(f"\nError processing task: {e!s}")

        return True
    except Exception as e:
        print(f"Error initializing worker mode: {e!s}")
        print("Falling back to CLI mode...")
        return run_cli_mode(args)


def list_available_models(provider_name: str) -> bool:
    """List available models for the specified provider and exit.

    Args:
        provider_name: The name of the provider to list models for.

    Returns:
        True if models were listed successfully, False otherwise
    """
    from atlas.providers import ProviderOptions, create_provider_from_options

    try:
        # Create minimal provider options
        options = ProviderOptions(provider_name=provider_name)

        # Create provider instance
        provider = create_provider_from_options(options)

        # Get available models
        models = provider.get_available_models()

        print(f"\nAvailable models for {provider_name}:")
        print("=" * 50)

        # Group models by capabilities or versions if possible
        if provider_name == "anthropic":
            categories = {
                "Latest Models": [m for m in models if "3-7" in m or "3-5" in m],
                "Claude 3 Opus": [m for m in models if "opus" in m],
                "Claude 3 Sonnet": [m for m in models if "sonnet" in m],
                "Claude 3 Haiku": [m for m in models if "haiku" in m],
                "Legacy Models": [m for m in models if "claude-2" in m],
            }

            for category, model_list in categories.items():
                if model_list:
                    print(f"\n{category}:")
                    for model in model_list:
                        print(f"  - {model}")

        elif provider_name == "openai":
            categories = {
                "GPT-4o Models": [m for m in models if "gpt-4o" in m],
                "GPT-4.1 Models": [m for m in models if "gpt-4.1" in m],
                "GPT-4 Models": [
                    m for m in models if "gpt-4" in m and "gpt-4o" not in m and "gpt-4.1" not in m
                ],
                "GPT-3.5 Models": [m for m in models if "gpt-3.5" in m],
                "Other Models": [
                    m
                    for m in models
                    if not any(x in m for x in ["gpt-4o", "gpt-4.1", "gpt-4", "gpt-3.5"])
                ],
            }

            for category, model_list in categories.items():
                if model_list:
                    print(f"\n{category}:")
                    for model in model_list:
                        print(f"  - {model}")

        else:
            # For other providers, just list the models
            for model in models:
                print(f"  - {model}")

        print("\n")
        return True

    except Exception as e:
        print(f"\nError listing models for {provider_name}: {e!s}")
        print("Make sure you have the appropriate API key set in your environment.")
        print(
            f"For {provider_name}, set the environment variable: {provider_name.upper()}_API_KEY\n"
        )
        return False


def run_textual_mode(args: dict[str, Any]) -> bool:
    """Run Atlas in Textual UI mode.

    Args:
        args: Command-line arguments as a dictionary

    Returns:
        True if textual mode ran successfully, False otherwise
    """
    logger.error("Textual UI mode is no longer available")
    logger.info("Falling back to CLI mode...")
    return run_cli_mode(args)


def main():
    """Main entry point for Atlas."""
    # Parse command-line arguments
    args = parse_cli_args()

    # Handle model listing request
    if args.get("models"):
        provider_name = args.get("provider", "anthropic")

        # Validate API key availability (mock provider doesn't need validation)
        if provider_name != "mock" and not validate_provider_api_key(provider_name):
            sys.exit(1)

        success = list_available_models(provider_name)
        sys.exit(0 if success else 1)

    # Handle different operation modes
    if args.get("mode") == "ingest":
        # For ingest mode, validate API key only if using Anthropic embeddings
        if args.get("embedding") == "anthropic":
            if args.get("provider") != "anthropic":
                logger.warning(
                    "Setting provider to 'anthropic' since Anthropic embeddings were requested"
                )
                args["provider"] = "anthropic"

            if not validate_provider_api_key("anthropic"):
                logger.error("Anthropic API key is required for Anthropic embeddings")
                sys.exit(1)
    else:
        # For other modes, validate API key for the selected provider
        # Mock provider doesn't need API key validation
        provider_name = args.get("provider", "anthropic")
        if provider_name != "mock" and not validate_provider_api_key(provider_name):
            sys.exit(1)

    # Run the appropriate mode
    success = True
    mode = args.get("mode")

    if mode == "cli":
        success = run_cli_mode(args)
    elif mode == "textual":
        success = run_textual_mode(args)
    elif mode == "ingest":
        success = ingest_documents(args)
    elif mode == "query":
        success = run_query_mode(args)
    elif mode == "controller":
        success = run_controller_mode(args)
    elif mode == "worker":
        success = run_worker_mode(args)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
