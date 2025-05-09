#!/usr/bin/env python3
"""
Atlas: Advanced Multi-Modal Learning & Guidance Framework
Main entry point for the Atlas module.
"""

import os
import sys
import argparse

# Type imports removed as they are unused
from dotenv import load_dotenv

# Set tokenizers parallelism to false to avoid warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Load environment variables from .env file
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
    quiet_loggers=["chromadb", "uvicorn", "httpx", "opentelemetry"]
)

from atlas.agents.base import AtlasAgent
# Import DocumentProcessor at module level to standardize imports
from atlas.knowledge.ingest import DocumentProcessor


def parse_args():
    """Parse command-line arguments with dimensional contexts."""
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

    # Model provider options for common parser
    model_group = common_parser.add_argument_group("Model Provider Options")
    model_group.add_argument(
        "--provider",
        type=str,
        choices=["anthropic", "openai", "ollama"],
        default="anthropic",
        help="Model provider to use",
    )
    model_group.add_argument(
        "--model",
        type=str,
        help="Model to use (provider-specific, defaults to provider's latest model)"
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
    model_group.add_argument(
        "--base-url",
        type=str,
        help="Base URL for API (used primarily with Ollama, default: http://localhost:11434)",
    )

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

    return parser.parse_args()


def check_environment(provider="anthropic"):
    """Check for required environment variables based on provider.

    Args:
        provider: The model provider to use (anthropic, openai, ollama)

    Returns:
        Boolean indicating if the required environment variables are set.
    """
    if provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY environment variable is not set.")
            logger.error("Please set it before running Atlas with Anthropic provider.")
            logger.error("Example: export ANTHROPIC_API_KEY=your_api_key_here")
            return False
    elif provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable is not set.")
            logger.error("Please set it before running Atlas with OpenAI provider.")
            logger.error("Example: export OPENAI_API_KEY=your_api_key_here")
            return False
    elif provider == "ollama":
        # No API key required for Ollama, but we should check if it's running
        try:
            import requests

            response = requests.get("http://localhost:11434/api/version", timeout=1)
            if response.status_code != 200:
                logger.warning(
                    "Ollama server doesn't appear to be running at http://localhost:11434"
                )
                logger.warning("Please start Ollama before running Atlas with Ollama provider.")
                logger.warning("Example: ollama serve")
                logger.warning("Continuing anyway, but expect connection errors...")
        except (requests.RequestException, ImportError) as e:
            logger.warning(
                f"Could not connect to Ollama server at http://localhost:11434 - {str(e)}"
            )
            logger.warning("Please make sure Ollama is installed and running.")
            logger.warning("Example: ollama serve")
            logger.warning("Continuing anyway, but expect connection errors...")

    return True


def ingest_documents(args):
    """Ingest documents from the specified directory."""
    # Import config and needed components
    from atlas.core.config import AtlasConfig
    from atlas.knowledge.ingest import DocumentProcessor, live_ingest_directory

    # Create config with command line parameters
    config = AtlasConfig(collection_name=args.collection, db_path=args.db_path)

    # Get db_path from config
    db_path = config.db_path

    # Set up embedding and other parameters
    anthropic_api_key = None
    if args.provider == "anthropic" and args.embedding == "anthropic":
        # If we're using Anthropic for embeddings, get the API key
        from atlas.core import env
        anthropic_api_key = env.get_api_key("anthropic")
        if not anthropic_api_key:
            logger.error("Anthropic API key required for Anthropic embeddings")
            return False

    # Check embedding strategy
    embedding_strategy = args.embedding if hasattr(args, 'embedding') else "default"
    enable_deduplication = not getattr(args, 'no_dedup', False)
    watch_mode = getattr(args, 'watch', False)

    # Process directory or default directories
    if not args.directory:
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
            collection_name=args.collection, 
            db_path=db_path,
            enable_deduplication=enable_deduplication,
            embedding_strategy=embedding_strategy
        )

        for dir_path in default_dirs:
            if os.path.exists(dir_path):
                logger.info(f"Ingesting documents from {dir_path}")
                processor.process_directory(dir_path, recursive=getattr(args, 'recursive', True))
            else:
                logger.warning(f"Directory not found: {dir_path}")
    else:
        logger.info(f"Ingesting documents from {args.directory}")
        logger.info(f"Using ChromaDB at: {db_path}")
        logger.info(f"Embedding strategy: {embedding_strategy}")
        
        # If watch mode is enabled, use live ingestion
        if watch_mode:
            try:
                logger.info("Starting live ingestion (watch mode)")
                processor = live_ingest_directory(
                    directory=args.directory,
                    collection_name=args.collection,
                    db_path=db_path,
                    recursive=getattr(args, 'recursive', True),
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
                collection_name=args.collection, 
                db_path=db_path,
                enable_deduplication=enable_deduplication,
                embedding_strategy=embedding_strategy
            )
            
            processor.process_directory(args.directory, recursive=getattr(args, 'recursive', True))

    return True


def run_cli_mode(args):
    """Run Atlas in interactive CLI mode."""
    logger.info("\nAtlas CLI Mode")
    logger.info("-------------")

    # Import config and agent
    from atlas.core.config import AtlasConfig
    from atlas.providers.factory import discover_providers

    # Create config with command line parameters
    config = AtlasConfig(
        collection_name=args.collection,
        db_path=args.db_path,
        model_name=args.model,
        max_tokens=args.max_tokens,
    )

    # Get additional provider params
    provider_params = {}
    if args.base_url and args.provider == "ollama":
        provider_params["base_url"] = args.base_url

    # Determine which model to use
    model_name = args.model
    if not model_name:
        # If no model specified, get the default model for the provider
        available_providers = discover_providers()
        if args.provider in available_providers and available_providers[args.provider]:
            model_name = available_providers[args.provider][0]
            logger.info(f"No model specified, using default model: {model_name}")

    # Initialize agent
    logger.info(f"Using {args.provider} provider with model: {model_name or 'default'}")
    agent = AtlasAgent(
        system_prompt_file=args.system_prompt,
        collection_name=args.collection,
        config=config,
        provider_name=args.provider,
        model_name=model_name,
        **provider_params,
    )

    logger.info("Atlas is ready. Type 'exit' or 'quit' to end the session.")
    logger.info("---------------------------------------------------")

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
            response = agent.process_message(user_input)

            # Display the response
            print(f"\nAtlas: {response}")
        except KeyboardInterrupt:
            print("\nSession interrupted. Goodbye!")
            break
        except EOFError:
            print("\nEOF detected. Exiting gracefully.")
            break
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
            print("Let's continue with a fresh conversation.")
            # Reinitialize agent
            provider_params = {}
            if args.base_url and args.provider == "ollama":
                provider_params["base_url"] = args.base_url
            agent = AtlasAgent(
                system_prompt_file=args.system_prompt,
                collection_name=args.collection,
                config=config,
                provider_name=args.provider,
                model_name=model_name,
                **provider_params,
            )


def run_query_mode(args):
    """Run Atlas in query mode (single query, non-interactive)."""
    # Import and use config
    from atlas.core.config import AtlasConfig

    # Create config with command line parameters
    config = AtlasConfig(
        collection_name=args.collection,
        db_path=args.db_path,
        model_name=args.model,
        max_tokens=args.max_tokens,
    )

    print(f"Processing query: {args.query}")

    # Get additional provider params
    provider_params = {}
    if args.base_url and args.provider == "ollama":
        provider_params["base_url"] = args.base_url

    # Initialize agent
    print(f"Using {args.provider} provider with model: {args.model or 'default'}")
    agent = AtlasAgent(
        system_prompt_file=args.system_prompt,
        collection_name=args.collection,
        config=config,
        provider_name=args.provider,
        model_name=args.model,
        **provider_params,
    )

    response = agent.process_message(args.query)
    print(f"Response: {response}")
    return True


def run_controller_mode(args):
    """Run Atlas in controller mode (experimental)."""
    print("\nAtlas Controller Mode (Experimental)")
    print("-----------------------------------")
    
    if not getattr(args, 'experimental', False):
        print("ERROR: Controller mode is experimental. Use --experimental flag to acknowledge.")
        return False

    try:
        # Import here to avoid circular imports
        from atlas.orchestration.coordinator import AgentCoordinator

        # Initialize coordinator with parallel processing if enabled
        coordinator = AgentCoordinator(
            system_prompt_file=args.system_prompt,
            collection_name=args.collection,
            worker_count=args.workers,
        )

        print(f"Controller initialized with {args.workers} workers.")
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
                print(f"\nUnexpected error in controller mode: {str(e)}")
                print("Let's continue with a fresh conversation.")
                coordinator = AgentCoordinator(
                    system_prompt_file=args.system_prompt,
                    collection_name=args.collection,
                    worker_count=args.workers,
                )

        return True
    except Exception as e:
        print(f"Error initializing controller mode: {str(e)}")
        print("Falling back to CLI mode...")
        return run_cli_mode(args)


def run_worker_mode(args):
    """Run Atlas in worker mode (experimental)."""
    print("\nAtlas Worker Mode (Experimental)")
    print("--------------------------------")
    
    if not getattr(args, 'experimental', False):
        print("ERROR: Worker mode is experimental. Use --experimental flag to acknowledge.")
        return False

    try:
        # Import here to avoid circular imports
        from atlas.agents.worker import RetrievalWorker, AnalysisWorker, DraftWorker

        # Get worker type from args
        worker_type = getattr(args, 'worker_type', 'retrieval')
        
        print(f"Initializing {worker_type} worker...")

        # Import Union type for type annotation
        from typing import Union

        # Create appropriate worker type
        # Use a variable with the right type annotation
        worker: Union[AnalysisWorker, DraftWorker, RetrievalWorker]

        if worker_type == "analysis":
            analysis_worker = AnalysisWorker(
                system_prompt_file=args.system_prompt, 
                collection_name=args.collection,
                provider_name=args.provider,
                model_name=args.model
            )
            worker = analysis_worker
            worker_desc = "Analysis Worker: Specializes in query analysis and information needs identification"
        elif worker_type == "draft":
            draft_worker = DraftWorker(
                system_prompt_file=args.system_prompt, 
                collection_name=args.collection,
                provider_name=args.provider,
                model_name=args.model
            )
            worker = draft_worker
            worker_desc = "Draft Worker: Specializes in generating draft responses"
        else:  # Default to retrieval worker
            retrieval_worker = RetrievalWorker(
                system_prompt_file=args.system_prompt, 
                collection_name=args.collection,
                provider_name=args.provider,
                model_name=args.model
            )
            worker = retrieval_worker
            worker_desc = (
                "Retrieval Worker: Specializes in document retrieval and summarization"
            )

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
                print(f"\nError processing task: {str(e)}")

        return True
    except Exception as e:
        print(f"Error initializing worker mode: {str(e)}")
        print("Falling back to CLI mode...")
        return run_cli_mode(args)


def list_available_models(provider_name):
    """List available models for the specified provider and exit.

    Args:
        provider_name: The name of the provider to list models for.
    """
    from atlas.providers.factory import create_provider
    
    try:
        # Create provider instance without specifying model
        provider = create_provider(provider_name=provider_name)
        
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
                "GPT-4 Models": [m for m in models if "gpt-4" in m and "gpt-4o" not in m and "gpt-4.1" not in m],
                "GPT-3.5 Models": [m for m in models if "gpt-3.5" in m],
                "Other Models": [m for m in models if not any(x in m for x in ["gpt-4o", "gpt-4.1", "gpt-4", "gpt-3.5"])],
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
        print(f"\nError listing models for {provider_name}: {str(e)}")
        print("Make sure you have the appropriate API key set in your environment.")
        print(f"For {provider_name}, set the environment variable: {provider_name.upper()}_API_KEY\n")
        return False


def main():
    """Main entry point for Atlas."""
    args = parse_args()

    # Check if user wants to list available models
    if hasattr(args, 'models') and args.models:
        # Check environment first for the API key
        if not check_environment(args.provider):
            sys.exit(1)
            
        success = list_available_models(args.provider)
        sys.exit(0 if success else 1)

    # For ingest mode, we only need to check the API key if using Anthropic embeddings
    if args.mode == "ingest" and hasattr(args, 'embedding') and args.embedding == "anthropic":
        if args.provider != "anthropic":
            logger.warning("Setting provider to 'anthropic' since Anthropic embeddings were requested")
            args.provider = "anthropic"
        
        if not check_environment("anthropic"):
            logger.error("Anthropic API key is required for Anthropic embeddings")
            sys.exit(1)
    # For other modes, check environment based on selected provider
    elif args.mode != "ingest" and not check_environment(args.provider):
        sys.exit(1)

    # Run the appropriate mode
    success = True
    if args.mode == "cli":
        run_cli_mode(args)
    elif args.mode == "ingest":
        success = ingest_documents(args)
    elif args.mode == "query":
        success = run_query_mode(args)
    elif args.mode == "controller":
        success = run_controller_mode(args)
    elif args.mode == "worker":
        success = run_worker_mode(args)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
