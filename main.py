#!/usr/bin/env python3
"""
Atlas: Advanced Multi-Modal Learning & Guidance Framework
Main entry point for the Atlas module.
"""

import os
import sys
import argparse
from typing import Optional

# Ensure atlas package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from atlas.agents.base import AtlasAgent
from atlas.knowledge.ingest import DocumentProcessor


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Atlas: Advanced Multi-Modal Learning & Guidance Framework",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Core arguments
    parser.add_argument(
        "-m", "--mode", 
        choices=["cli", "ingest", "query", "worker", "controller"],
        default="cli",
        help="Operation mode for Atlas"
    )
    
    # System prompt and knowledge base
    parser.add_argument(
        "-s", "--system-prompt", 
        type=str, 
        help="Path to system prompt file"
    )
    parser.add_argument(
        "-c", "--collection", 
        type=str, 
        default="atlas_knowledge_base",
        help="Name of the ChromaDB collection to use"
    )
    parser.add_argument(
        "--db-path", 
        type=str, 
        help="Path to ChromaDB database directory"
    )
    
    # Ingestion options
    parser.add_argument(
        "-d", "--directory", 
        type=str, 
        help="Directory to ingest documents from"
    )
    parser.add_argument(
        "-r", "--recursive", 
        action="store_true", 
        help="Recursively process directories"
    )
    
    # LangGraph options
    parser.add_argument(
        "--parallel", 
        action="store_true", 
        help="Enable parallel processing with LangGraph"
    )
    parser.add_argument(
        "--workers", 
        type=int, 
        default=3,
        help="Number of worker agents to spawn in controller mode"
    )
    parser.add_argument(
        "--workflow", 
        choices=["rag", "advanced", "custom", "retrieval", "analysis", "draft"],
        default="rag",
        help="LangGraph workflow to use or worker type in worker mode"
    )
    
    # Model options
    parser.add_argument(
        "--model", 
        type=str, 
        default="claude-3-sonnet-20240229",
        help="Claude model to use"
    )
    parser.add_argument(
        "--max-tokens", 
        type=int, 
        default=2000,
        help="Maximum tokens in model responses"
    )
    
    # Query options
    parser.add_argument(
        "-q", "--query", 
        type=str, 
        help="Single query to process (query mode only)"
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
    config = AtlasConfig(
        collection_name=args.collection,
        db_path=args.db_path
    )
    
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
        
        print(f"No directory specified. Using default directories:")
        for dir_path in default_dirs:
            print(f"  - {dir_path}")
        
        print(f"Using ChromaDB at: {db_path}")
        processor = DocumentProcessor(
            collection_name=args.collection,
            db_path=db_path
        )
        
        for dir_path in default_dirs:
            if os.path.exists(dir_path):
                print(f"\nIngesting documents from {dir_path}")
                processor.process_directory(dir_path)
            else:
                print(f"Directory not found: {dir_path}")
    else:
        print(f"Ingesting documents from {args.directory}")
        print(f"Using ChromaDB at: {db_path}")
        
        processor = DocumentProcessor(
            collection_name=args.collection,
            db_path=db_path
        )
        
        processor.process_directory(args.directory)
    
    return True


def run_cli_mode(args):
    """Run Atlas in interactive CLI mode."""
    print("\nAtlas CLI Mode")
    print("-------------")
    
    # Import and use config
    from atlas.core.config import AtlasConfig
    
    # Create config with command line parameters
    config = AtlasConfig(
        collection_name=args.collection,
        db_path=args.db_path,
        model_name=args.model,
        max_tokens=args.max_tokens
    )
    
    # Initialize agent
    agent = AtlasAgent(
        system_prompt_file=args.system_prompt, 
        collection_name=args.collection,
        config=config
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
                system_prompt_file=args.system_prompt, 
                collection_name=args.collection,
                config=config
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
        max_tokens=args.max_tokens
    )
    
    print(f"Processing query: {args.query}")
    
    agent = AtlasAgent(
        system_prompt_file=args.system_prompt, 
        collection_name=args.collection,
        config=config
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
            worker_count=args.workers
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
                    worker_count=args.workers
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
        
        # Create appropriate worker type
        if worker_type == "analysis":
            worker = AnalysisWorker(
                system_prompt_file=args.system_prompt,
                collection_name=args.collection
            )
            worker_desc = "Analysis Worker: Specializes in query analysis and information needs identification"
        elif worker_type == "draft":
            worker = DraftWorker(
                system_prompt_file=args.system_prompt,
                collection_name=args.collection
            )
            worker_desc = "Draft Worker: Specializes in generating draft responses"
        else:  # Default to retrieval worker
            worker = RetrievalWorker(
                system_prompt_file=args.system_prompt,
                collection_name=args.collection
            )
            worker_desc = "Retrieval Worker: Specializes in document retrieval and summarization"
        
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
                task = {
                    "task_id": "cli_task",
                    "query": user_input
                }
                
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