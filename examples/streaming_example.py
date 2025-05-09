"""
Example of streaming responses from Atlas using different model providers.

This script demonstrates how to use streaming functionality with different model providers:
- Anthropic (Claude)
- OpenAI
- Ollama
- Mock (for testing)

Streaming creates a more interactive experience by showing incremental responses.
"""

import argparse
import logging
import os
import sys
import time
from typing import Optional, Dict, Any, Callable

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import atlas package
from atlas import create_query_client
from atlas.providers.factory import create_provider
from atlas.providers.base import ModelRequest, ModelMessage


def print_streaming(delta: str, full_text: str) -> None:
    """Print streaming output character by character.

    Args:
        delta: The new text chunk.
        full_text: The complete text so far.
    """
    # Print the delta without newline and flush immediately
    for char in delta:
        print(char, end="", flush=True)
        time.sleep(0.005)  # Small delay to simulate typing


def demonstrate_client_streaming(use_mock: bool = False) -> None:
    """Demonstrate streaming using the Atlas query client.
    
    Args:
        use_mock: If True, use mock provider without API key.
    """
    print("\n" + "="*50)
    print("DEMO 1: Streaming using Atlas Query Client")
    print("="*50)
    
    # Create a client with the appropriate provider
    provider_name = "mock" if use_mock else "anthropic"
    client = create_query_client(provider_name=provider_name)

    # Use a simple query
    query = "What is the trimodal methodology in Atlas?"
    print(f"Query: {query} (using {provider_name} provider)")

    try:
        print("\nStreaming Response:")
        # Try streaming response
        result = client.query_streaming(query, print_streaming)
        print("\n\nStreaming completed with result length:", len(result))
        
        # Display token usage and cost information
        if hasattr(client, "last_response") and client.last_response:
            if hasattr(client.last_response, "usage") and client.last_response.usage:
                usage = client.last_response.usage
                print(f"\nToken Usage: {usage.input_tokens} input, {usage.output_tokens} output tokens")
            
            if hasattr(client.last_response, "cost") and client.last_response.cost:
                print(f"Estimated Cost: {client.last_response.cost}")
    except Exception as e:
        print(f"\nError in streaming: {e}")

        print("\nFalling back to regular query...")
        # Try regular query
        result = client.query(query)
        print(f"Regular query result:\n{result}")


def demonstrate_provider_streaming(provider_name: str, model_name: Optional[str] = None, use_mock: bool = False) -> None:
    """Demonstrate streaming directly with a specific provider.
    
    Args:
        provider_name: The name of the provider to use ("anthropic", "openai", "ollama", or "mock").
        model_name: Optional model name to use.
        use_mock: If True, override provider_name with "mock".
    """
    # Override provider if use_mock is True
    if use_mock:
        provider_name = "mock"
        
    print("\n" + "="*50)
    print(f"DEMO 2: Direct Streaming with {provider_name.capitalize()} Provider")
    print("="*50)
    
    # Provider-specific configurations
    provider_configs: Dict[str, Dict[str, Any]] = {
        "anthropic": {
            "default_model": "claude-3-7-sonnet-20250219",
            "max_tokens": 300,
        },
        "openai": {
            "default_model": "gpt-4o",
            "max_tokens": 300,
        },
        "ollama": {
            "default_model": "llama3",
            "max_tokens": 300,
        },
        "mock": {
            "default_model": "mock-standard",
            "max_tokens": 300,
            "delay_ms": 50,  # Faster output for demo purposes
        }
    }
    
    # Get configuration for the selected provider
    config = provider_configs.get(provider_name, {})
    
    # Create the provider
    try:
        provider = create_provider(
            provider_name, 
            model_name=model_name or config.get("default_model"),
            max_tokens=config.get("max_tokens", 300),
            # Add any provider-specific parameters
            **{k: v for k, v in config.items() if k not in ["default_model", "max_tokens"]}
        )
    except Exception as e:
        print(f"Error creating provider {provider_name}: {e}")
        return
    
    # Create a simple request
    request = ModelRequest(
        messages=[ModelMessage.user("What is the trimodal methodology in Atlas?")],
        max_tokens=config.get("max_tokens", 300),
    )
    
    print(f"Using model: {provider.model_name}")
    print("Query: What is the trimodal methodology in Atlas?")
    
    # Define a custom streaming callback
    def stream_callback(delta: str, response: Any) -> None:
        """Custom callback for streaming."""
        print_streaming(delta, response.content)
        
        # Update progress info every few tokens
        if delta.endswith(".") or delta.endswith("?") or delta.endswith("!"):
            tokens_so_far = response.usage.output_tokens if hasattr(response.usage, "output_tokens") else "unknown"
            print(f"\n[Progress: {tokens_so_far} tokens generated so far...]", end="\r")
    
    try:
        print("\nStreaming Response:")
        # Stream with callback
        final_response = provider.stream_with_callback(request, stream_callback)
        
        # Print final statistics
        print("\n\nStreaming completed!")
        print(f"Model: {final_response.model}")
        print(f"Provider: {final_response.provider}")
        print(f"Content length: {len(final_response.content)} characters")
        print(f"Tokens: {final_response.usage.input_tokens} input, {final_response.usage.output_tokens} output")
        print(f"Estimated cost: {final_response.cost}")
        print(f"Finish reason: {final_response.finish_reason}")
    except Exception as e:
        print(f"\nError in streaming: {e}")


def main():
    """Parse arguments and run the appropriate demo."""
    parser = argparse.ArgumentParser(description="Demonstrate streaming with different providers.")
    parser.add_argument("--provider", "-p", type=str, default="mock",
                       choices=["anthropic", "openai", "ollama", "mock", "all", "client"],
                       help="The provider to demonstrate (default: mock)")
    parser.add_argument("--model", "-m", type=str, default=None,
                       help="The model to use (default: provider-specific)")
    parser.add_argument("--mock", action="store_true",
                       help="Override provider selection and use mock provider (no API key required)")
    
    args = parser.parse_args()
    
    if args.provider == "client":
        # Just demonstrate the Atlas client
        demonstrate_client_streaming(args.mock)
    elif args.provider == "all":
        # Demonstrate all providers
        demonstrate_client_streaming(args.mock)
        for provider in ["mock", "anthropic", "openai", "ollama"]:
            try:
                demonstrate_provider_streaming(provider, args.model, args.mock)
            except Exception as e:
                print(f"Error demonstrating {provider}: {e}")
    else:
        # Demonstrate a specific provider
        demonstrate_provider_streaming(args.provider, args.model, args.mock)


if __name__ == "__main__":
    main()
