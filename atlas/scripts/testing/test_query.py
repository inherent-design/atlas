#!/usr/bin/env python3
"""
Utility to run a single query against the Atlas agent for testing.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Set tokenizers parallelism to false to avoid warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Load environment variables from .env file
load_dotenv()

from atlas.core.config import AtlasConfig


def test_with_base_agent(query, provider="anthropic", model=None):
    """Test with the base Atlas agent.
    
    Args:
        query: The query to process.
        provider: The model provider to use.
        model: Optional specific model to use.
    """
    from atlas.agents.base import AtlasAgent
    
    # Check API key based on provider
    if provider == "anthropic" and not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
        return False
    elif provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set.")
        return False
    
    # Create configuration
    config = AtlasConfig(
        collection_name="atlas_knowledge_base",
        model_name=model or "claude-3-5-sonnet-20240620"
    )
    
    # Initialize agent
    print(f"Initializing agent with provider: {provider}")
    agent = AtlasAgent(config=config)
    
    print(f"\nQuery: {query}")
    
    # Process query
    response = agent.process_message(query)
    
    print(f"\nResponse: {response}")
    return True


def test_with_multi_provider_agent(query, provider="anthropic", model=None):
    """Test with the multi-provider Atlas agent.
    
    Args:
        query: The query to process.
        provider: The model provider to use.
        model: Optional specific model to use.
    """
    try:
        from atlas.agents.multi_provider_base import MultiProviderAgent, list_available_providers
        
        # Check API key based on provider
        if provider == "anthropic" and not os.environ.get("ANTHROPIC_API_KEY"):
            print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
            return False
        elif provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
            print("ERROR: OPENAI_API_KEY environment variable is not set.")
            return False
        elif provider == "ollama":
            # For Ollama, check if the service is running
            try:
                import requests
                response = requests.get("http://localhost:11434/api/version", timeout=1)
                if response.status_code != 200:
                    print("WARNING: Ollama server doesn't appear to be running at http://localhost:11434")
                    print("Please start Ollama before testing.")
                    return False
            except:
                print("WARNING: Couldn't connect to Ollama server at http://localhost:11434")
                print("Please make sure Ollama is installed and running.")
                return False
        
        # Get default model if not specified
        if not model:
            if provider == "anthropic":
                model = "claude-3-5-sonnet-20240620"
            elif provider == "openai":
                model = "gpt-4o"
            elif provider == "ollama":
                model = "llama3"
        
        # Create configuration
        config = AtlasConfig(collection_name="atlas_knowledge_base")
        
        # Initialize agent
        print(f"Initializing multi-provider agent with provider: {provider}, model: {model}")
        agent = MultiProviderAgent(
            config=config,
            provider_name=provider,
            model_name=model
        )
        
        print(f"\nQuery: {query}")
        
        # Process query
        response = agent.process_message(query)
        
        print(f"\nResponse: {response}")
        return True
    
    except ImportError as e:
        print(f"Error importing multi-provider agent: {e}")
        print("Falling back to base agent...")
        return test_with_base_agent(query, provider, model)


def main():
    """Run a test query against Atlas."""
    parser = argparse.ArgumentParser(description="Test Atlas with a single query")
    
    parser.add_argument(
        "-q", "--query", 
        type=str, 
        default="What is the trimodal methodology in Atlas?", 
        help="Query to process"
    )
    
    parser.add_argument(
        "-p", "--provider",
        choices=["anthropic", "openai", "ollama"],
        default="anthropic",
        help="Model provider to use"
    )
    
    parser.add_argument(
        "-m", "--model",
        type=str,
        help="Specific model to use"
    )
    
    parser.add_argument(
        "--multi-provider",
        action="store_true",
        help="Use multi-provider agent implementation"
    )
    
    args = parser.parse_args()
    
    print("=== Atlas Query Test ===")
    
    if args.multi_provider:
        success = test_with_multi_provider_agent(args.query, args.provider, args.model)
    else:
        success = test_with_base_agent(args.query, args.provider, args.model)
    
    if success:
        print("\nTest completed successfully.")
    else:
        print("\nTest failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()