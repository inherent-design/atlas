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

from atlas.agents.base import AtlasAgent
from atlas.knowledge.ingest import DocumentProcessor


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Atlas: Advanced Multi-Modal Learning & Guidance Framework",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Core arguments
    parser.add_argument(
        "-m",
        "--mode",
        choices=["cli", "ingest", "query", "worker", "controller"],
        default="cli",
        help="Operation mode for Atlas",
    )

    # System prompt and knowledge base
    parser.add_argument(
        "-s", "--system-prompt", type=str, help="Path to system prompt file"
    )
    parser.add_argument(
        "-c",
        "--collection",
        type=str,
        default="atlas_knowledge_base",
        help="Name of the ChromaDB collection to use",
    )
    parser.add_argument(
        "--db-path", type=str, help="Path to ChromaDB database directory"
    )

    # Ingestion options
    parser.add_argument(
        "-d", "--directory", type=str, help="Directory to ingest documents from"
    )
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="Recursively process directories"
    )

    # LangGraph options
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Enable parallel processing with LangGraph",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Number of worker agents to spawn in controller mode",
    )
    parser.add_argument(
        "--workflow",
        choices=["rag", "advanced", "custom", "retrieval", "analysis", "draft"],
        default="rag",
        help="LangGraph workflow to use or worker type in worker mode",
    )

    # Model provider options
    parser.add_argument(
        "--provider",
        type=str,
        choices=["anthropic", "openai", "ollama"],
        default="anthropic",
        help="Model provider to use (anthropic, openai, ollama)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="claude-3-7-sonnet-20250219",
        help="Model to use (provider-specific, e.g., claude-3-opus-20240229, gpt-4o, llama3)",
    )
    parser.add_argument(
        "--max-tokens", type=int, default=2000, help="Maximum tokens in model responses"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        help="Base URL for API (used primarily with Ollama, default: http://localhost:11434)",
    )

    # Query options
    parser.add_argument(
        "-q", "--query", type=str, help="Single query to process (query mode only)"
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
            print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
            print("Please set it before running Atlas with Anthropic provider.")
            print("Example: export ANTHROPIC_API_KEY=your_api_key_here")
            return False
    elif provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("ERROR: OPENAI_API_KEY environment variable is not set.")
            print("Please set it before running Atlas with OpenAI provider.")
            print("Example: export OPENAI_API_KEY=your_api_key_here")
            return False
    elif provider == "ollama":
        # No API key required for Ollama, but we should check if it's running
        try:
            import requests

            response = requests.get("http://localhost:11434/api/version", timeout=1)
            if response.status_code != 200:
                print(
                    "WARNING: Ollama server doesn't appear to be running at http://localhost:11434"
                )
                print("Please start Ollama before running Atlas with Ollama provider.")
                print("Example: ollama serve")
                print("Continuing anyway, but expect connection errors...")
        except (requests.RequestException, ImportError) as e:
            print(
                f"WARNING: Could not connect to Ollama server at http://localhost:11434 - {str(e)}"
            )
            print("Please make sure Ollama is installed and running.")
            print("Example: ollama serve")
            print("Continuing anyway, but expect connection errors...")

    return True


def ingest_documents(args):
    """Ingest documents from the specified directory."""
    # Import config
    from atlas.core.config import AtlasConfig

    # Create config with command line parameters
    config = AtlasConfig(collection_name=args.collection, db_path=args.db_path)

    # Get db_path from config
    db_path = config.db_path

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

        print("No directory specified. Using default directories:")
        for dir_path in default_dirs:
            print(f"  - {dir_path}")

        print(f"Using ChromaDB at: {db_path}")
        processor = DocumentProcessor(collection_name=args.collection, db_path=db_path)

        for dir_path in default_dirs:
            if os.path.exists(dir_path):
                print(f"\nIngesting documents from {dir_path}")
                processor.process_directory(dir_path)
            else:
                print(f"Directory not found: {dir_path}")
    else:
        print(f"Ingesting documents from {args.directory}")
        print(f"Using ChromaDB at: {db_path}")

        processor = DocumentProcessor(collection_name=args.collection, db_path=db_path)

        processor.process_directory(args.directory)

    return True


def run_cli_mode(args):
    """Run Atlas in interactive CLI mode."""
    print("\nAtlas CLI Mode")
    print("-------------")

    # Import config and agent
    from atlas.core.config import AtlasConfig

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

    # Initialize agent
    print(f"Using {args.provider} provider with model: {args.model}")
    agent = AtlasAgent(
        system_prompt_file=args.system_prompt,
        collection_name=args.collection,
        config=config,
        provider_name=args.provider,
        model_name=args.model,
        **provider_params,
    )

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
                model_name=args.model,
                **provider_params,
            )


def run_query_mode(args):
    """Run Atlas in query mode (single query, non-interactive)."""
    if not args.query:
        print("ERROR: Query parameter (-q/--query) is required for query mode.")
        return False

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
    print(f"Using {args.provider} provider with model: {args.model}")
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
    """Run Atlas in controller mode."""
    print("\nAtlas Controller Mode")
    print("--------------------")

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
    """Run Atlas in worker mode."""
    print("\nAtlas Worker Mode")
    print("----------------")

    try:
        # Import here to avoid circular imports
        from atlas.agents.worker import RetrievalWorker, AnalysisWorker, DraftWorker

        # Default to retrieval worker if no specific type is given
        worker_type = "retrieval"
        if args.workflow and args.workflow in ["analysis", "draft"]:
            worker_type = args.workflow

        print(f"Initializing {worker_type} worker...")

        # Import Union type for type annotation
        from typing import Union

        # Create appropriate worker type
        # Use a variable with the right type annotation
        worker: Union[AnalysisWorker, DraftWorker, RetrievalWorker]

        if worker_type == "analysis":
            analysis_worker = AnalysisWorker(
                system_prompt_file=args.system_prompt, collection_name=args.collection
            )
            worker = analysis_worker
            worker_desc = "Analysis Worker: Specializes in query analysis and information needs identification"
        elif worker_type == "draft":
            draft_worker = DraftWorker(
                system_prompt_file=args.system_prompt, collection_name=args.collection
            )
            worker = draft_worker
            worker_desc = "Draft Worker: Specializes in generating draft responses"
        else:  # Default to retrieval worker
            retrieval_worker = RetrievalWorker(
                system_prompt_file=args.system_prompt, collection_name=args.collection
            )
            worker = retrieval_worker
            worker_desc = (
                "Retrieval Worker: Specializes in document retrieval and summarization"
            )

        print(f"Worker initialized: {worker_desc}")
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


def main():
    """Main entry point for Atlas."""
    args = parse_args()

    # Check environment based on selected provider
    if not check_environment(args.provider):
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
