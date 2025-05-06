"""
Atlas agent implementation using LangGraph.

This module defines the main Atlas agent workflow and capabilities.
"""

import os
import sys
from typing import Dict, List, Any, Optional

from anthropic import Anthropic

from atlas.tools.knowledge_retrieval import retrieve_knowledge


# Default system prompt
DEFAULT_SYSTEM_PROMPT = """# **Atlas: Advanced Multi-Modal Learning & Guidance Framework**

You are Atlas, an AI guide dedicated to organic and adaptive learning, helping users explore ideas and solve problems through collaborative conversation.

## Your Knowledge Context

You have access to a rich knowledge base containing the Atlas framework documentation. This includes:
- Core Identity & Mission
- Trimodal Methodology Framework
- Knowledge Framework
- Communication Principles
- Task Capabilities
- Implementation Templates

Use this knowledge to provide helpful, accurate responses based on the Atlas framework.

## Your Capabilities

1. Answer questions about the Atlas framework and its components
2. Explain concepts related to knowledge management, documentation, and AI assistance
3. Provide guidance on implementing Atlas principles in various contexts
4. Suggest relevant Atlas templates or frameworks for specific user needs
5. Maintain consistent understanding of the Atlas identity and methodology

## Your Approach

1. First analyze what the user is asking and what they need
2. Then look at the provided context documents to inform your response
3. Integrate relevant information from the documents to craft a helpful answer
4. When information might be missing, acknowledge limits while providing the best available guidance
5. Always maintain the Atlas identity, never identifying yourself as an AI or Claude

## Important Guidelines

- NEVER identify yourself as an AI, language model, or algorithm
- DO NOT use phrases like "Based on my training data..." or "As an AI..."
- Focus on being helpful while maintaining the Atlas persona
- When uncertain, maintain appropriate epistemic humility without revealing limitations related to being AI
- Keep responses clear, concise, and directly relevant to the user's needs
"""


def load_system_prompt(file_path: Optional[str] = None) -> str:
    """Load the system prompt from a file or use the default.

    Args:
        file_path: Optional path to a system prompt file.

    Returns:
        The system prompt string.
    """
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                custom_prompt = f.read()
                print(f"Loaded custom system prompt from {file_path}")
                return custom_prompt
        except Exception as e:
            print(f"Error loading system prompt from {file_path}: {str(e)}")
            print("Using default system prompt instead.")

    return DEFAULT_SYSTEM_PROMPT


class AtlasAgent:
    """Atlas agent for interacting with users."""

    def __init__(
        self,
        system_prompt_file: Optional[str] = None,
        collection_name: str = "atlas_knowledge_base",
    ):
        """Initialize the Atlas agent.

        Args:
            system_prompt_file: Optional path to a file containing the system prompt.
            collection_name: Name of the Chroma collection to use.
        """
        # Load the system prompt
        self.system_prompt = load_system_prompt(system_prompt_file)
        self.collection_name = collection_name

        # Initialize the Anthropic client
        self.anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

        # Initialize conversation history
        self.messages: List[Dict[str, str]] = []

    def query_knowledge_base(self, query: str) -> List[Dict[str, Any]]:
        """Query the knowledge base for relevant information.

        Args:
            query: The query string.

        Returns:
            A list of relevant documents.
        """
        # Create a fake state to use with retrieve_knowledge
        state = {"messages": [{"role": "user", "content": query}]}

        # Call retrieve_knowledge directly
        updated_state = retrieve_knowledge(
            state, query=query, collection_name=self.collection_name
        )

        # Return the documents with proper typing
        documents: List[Dict[str, Any]] = updated_state.get("context", {}).get(
            "documents", []
        )
        return documents

    def process_message(self, message: str) -> str:
        """Process a user message and return the agent's response.

        Args:
            message: The user's message.

        Returns:
            The agent's response.
        """
        try:
            # Add user message to history
            self.messages.append({"role": "user", "content": message})

            # Retrieve relevant documents from the knowledge base
            print(
                f"Querying knowledge base for: {message[:50]}{'...' if len(message) > 50 else ''}"
            )
            documents = self.query_knowledge_base(message)
            print(f"Retrieved {len(documents)} relevant documents")

            if documents:
                # Print top documents for debugging
                print("Top relevant documents:")
                for i, doc in enumerate(documents[:3]):
                    source = doc["metadata"].get("source", "Unknown")
                    score = doc["relevance_score"]
                    print(f"  {i + 1}. {source} (score: {score:.4f})")

            # Create system message with context
            system_msg = self.system_prompt
            if documents:
                context_text = "\n\n## Relevant Knowledge\n\n"
                for i, doc in enumerate(
                    documents[:3]
                ):  # Limit to top 3 most relevant docs
                    source = doc["metadata"].get("source", "Unknown")
                    content = doc["content"]
                    context_text += f"### Document {i + 1}: {source}\n{content}\n\n"

                system_msg = system_msg + context_text

            # Generate response using Claude
            response = self.anthropic_client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=2000,
                system=system_msg,
                messages=self.messages,
            )

            # Extract response text with explicit typing
            assistant_message: str = response.content[0].text

            # Add assistant response to history
            self.messages.append({"role": "assistant", "content": assistant_message})

            return assistant_message

        except Exception as e:
            print(f"Error processing message: {str(e)}")
            print(f"Error details: {sys.exc_info()}")
            return "I'm sorry, I encountered an error processing your request. Please try again."


def parse_args():
    """Parse command-line arguments."""
    import argparse

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

    # Model options
    parser.add_argument(
        "--model",
        type=str,
        default="claude-3-7-sonnet-20250219",
        help="Claude model to use",
    )
    parser.add_argument(
        "--max-tokens", type=int, default=2000, help="Maximum tokens in model responses"
    )

    # Query options
    parser.add_argument(
        "-q", "--query", type=str, help="Single query to process (query mode only)"
    )

    return parser.parse_args()


def check_environment():
    """Check for required environment variables."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
        print("Please set it before running Atlas.")
        print("Example: export ANTHROPIC_API_KEY=your_api_key_here")
        return False
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
        from atlas.knowledge.ingest import DocumentProcessor

        processor = DocumentProcessor(collection_name=args.collection, db_path=db_path)

        for dir_path in default_dirs:
            if os.path.exists(dir_path):
                print(f"\nIngesting documents from {dir_path}")
                processor.process_directory(dir_path, recursive=args.recursive)
            else:
                print(f"Directory not found: {dir_path}")
    else:
        print(f"Ingesting documents from {args.directory}")
        print(f"Using ChromaDB at: {db_path}")

        from atlas.knowledge.ingest import DocumentProcessor

        processor = DocumentProcessor(collection_name=args.collection, db_path=db_path)

        processor.process_directory(args.directory, recursive=args.recursive)

    return True


def run_cli_mode(args):
    """Run Atlas in interactive CLI mode."""
    print("\nAtlas CLI Mode")
    print("-------------")

    # Initialize agent with collection name
    agent = AtlasAgent(
        system_prompt_file=args.system_prompt, collection_name=args.collection
    )

    print("Atlas is ready. Type 'exit' or 'quit' to end the session.")
    print("---------------------------------------------------")

    while True:
        # Get user input
        try:
            user_input = input("\nYou: ")

            # Check for exit command
            if user_input.lower() in ["exit", "quit"]:
                print("\nGoodbye!")
                break

            # Process the message and get response
            response = agent.process_message(user_input)

            # Display the response
            print(f"\nAtlas: {response}")
        except KeyboardInterrupt:
            print("\nSession interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
            print("Let's continue with a fresh conversation.")
            agent = AtlasAgent(
                system_prompt_file=args.system_prompt, collection_name=args.collection
            )


def run_query_mode(args):
    """Run Atlas in query mode (single query, non-interactive)."""
    if not args.query:
        print("ERROR: Query parameter (-q/--query) is required for query mode.")
        return False

    # Process the query

    print(f"Processing query: {args.query}")

    agent = AtlasAgent(
        system_prompt_file=args.system_prompt, collection_name=args.collection
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
        from atlas.core.config import AtlasConfig

        # Create config with command line parameters
        config = AtlasConfig(
            collection_name=args.collection,
            db_path=args.db_path,
            model_name=args.model,
            max_tokens=args.max_tokens,
            parallel_enabled=args.parallel,
            worker_count=args.workers,
        )

        # Initialize coordinator with parallel processing if enabled
        coordinator = AgentCoordinator(
            system_prompt_file=args.system_prompt,
            collection_name=args.collection,
            config=config,
            worker_count=args.workers,
        )

        print(f"Controller initialized with {args.workers} workers.")
        print("Atlas is ready. Type 'exit' or 'quit' to end the session.")
        print("---------------------------------------------------")

        while True:
            # Get user input
            try:
                user_input = input("\nYou: ")

                # Check for exit command
                if user_input.lower() in ["exit", "quit"]:
                    print("\nGoodbye!")
                    break

                # Process the message and get response
                response = coordinator.process_message(user_input)

                # Display the response
                print(f"\nAtlas: {response}")
            except KeyboardInterrupt:
                print("\nSession interrupted. Goodbye!")
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
        from atlas.core.config import AtlasConfig

        # Create config with command line parameters
        config = AtlasConfig(
            collection_name=args.collection,
            db_path=args.db_path,
            model_name=args.model,
            max_tokens=args.max_tokens,
        )

        # Default to retrieval worker if no specific type is given
        worker_type = "retrieval"
        if args.workflow and args.workflow in ["analysis", "draft"]:
            worker_type = args.workflow

        print(f"Initializing {worker_type} worker...")

        # Import Union type for type annotation
        from typing import Union

        # Create appropriate worker type with explicit type annotation
        worker: Union[AnalysisWorker, DraftWorker, RetrievalWorker]

        if worker_type == "analysis":
            analysis_worker = AnalysisWorker(
                system_prompt_file=args.system_prompt,
                collection_name=args.collection,
                config=config,
            )
            worker = analysis_worker
            worker_desc = "Analysis Worker: Specializes in query analysis and information needs identification"
        elif worker_type == "draft":
            draft_worker = DraftWorker(
                system_prompt_file=args.system_prompt,
                collection_name=args.collection,
                config=config,
            )
            worker = draft_worker
            worker_desc = "Draft Worker: Specializes in generating draft responses"
        else:  # Default to retrieval worker
            retrieval_worker = RetrievalWorker(
                system_prompt_file=args.system_prompt,
                collection_name=args.collection,
                config=config,
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
                user_input = input("\nTask: ")

                # Check for exit command
                if user_input.lower() in ["exit", "quit"]:
                    print("\nWorker shutting down. Goodbye!")
                    break

                # Create a simple task and process it
                task = {"task_id": "cli_task", "query": user_input}

                result = worker.process_task(task)
                print(f"\nResult: {result.get('result', 'No result')}")

            except KeyboardInterrupt:
                print("\nWorker interrupted. Shutting down!")
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

    # Check environment
    if not check_environment():
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
