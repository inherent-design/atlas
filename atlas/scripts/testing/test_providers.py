#!/usr/bin/env python3
"""
Utility for testing different model providers with Atlas.

This script provides examples of using different model providers with Atlas.
"""

import os
import argparse
from dotenv import load_dotenv

from atlas.agents.multi_provider_base import MultiProviderAgent, list_available_providers
from atlas.core.config import AtlasConfig


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Test Atlas with different model providers",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Provider selection
    parser.add_argument(
        "--provider",
        type=str,
        default="anthropic",
        choices=["anthropic", "openai", "ollama"],
        help="Model provider to use",
    )
    
    # Model selection
    parser.add_argument(
        "--model",
        type=str,
        help="Specific model to use (defaults to provider's default)",
    )
    
    # Query options
    parser.add_argument(
        "-q", "--query",
        type=str,
        default="What is the trimodal methodology in Atlas?",
        help="Query to process",
    )
    
    # System prompt
    parser.add_argument(
        "-s", "--system-prompt",
        type=str,
        help="Path to system prompt file",
    )
    
    # Collection name
    parser.add_argument(
        "-c", "--collection",
        type=str,
        default="atlas_knowledge_base",
        help="Name of the ChromaDB collection to use",
    )
    
    # Interactive mode
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive mode",
    )
    
    # List providers
    parser.add_argument(
        "-l", "--list-providers",
        action="store_true",
        help="List available providers and models",
    )

    return parser.parse_args()


def main():
    """Main entry point for provider test script."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Parse arguments
    args = parse_args()
    
    # List available providers if requested
    if args.list_providers:
        providers = list_available_providers()
        return
    
    print(f"Testing Atlas with {args.provider} provider")
    if args.model:
        print(f"Using model: {args.model}")
    
    # Create agent with specified provider
    try:
        agent = MultiProviderAgent(
            system_prompt_file=args.system_prompt,
            collection_name=args.collection,
            provider_name=args.provider,
            model_name=args.model,
        )
        
        if args.interactive:
            # Interactive mode
            print("\nAtlas Multi-Provider Test (Interactive Mode)")
            print("-------------------------------------------")
            print(f"Using provider: {args.provider}")
            print("Type 'exit' or 'quit' to end the session")
            
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
        else:
            # Single query mode
            print(f"\nProcessing query: {args.query}")
            response = agent.process_message(args.query)
            print(f"\nResponse: {response}")
    
    except Exception as e:
        print(f"Error initializing agent: {str(e)}")
        
        # Check for missing API keys and provide guidance
        if args.provider == "anthropic" and not os.environ.get("ANTHROPIC_API_KEY"):
            print("\nMissing ANTHROPIC_API_KEY environment variable.")
            print("Set it with: export ANTHROPIC_API_KEY=your_key_here")
        elif args.provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
            print("\nMissing OPENAI_API_KEY environment variable.")
            print("Set it with: export OPENAI_API_KEY=your_key_here")
        elif args.provider == "ollama":
            print("\nMake sure Ollama is running locally.")
            print("Start it with: ollama serve")


if __name__ == "__main__":
    main()