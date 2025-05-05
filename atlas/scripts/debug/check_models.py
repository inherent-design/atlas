#!/usr/bin/env python3
"""
Utility to check available model providers and their models.
"""

import os
import argparse
from dotenv import load_dotenv


def check_anthropic_models():
    """Check available Anthropic models."""
    try:
        from anthropic import Anthropic
        
        # Get API key from environment
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("ANTHROPIC_API_KEY environment variable is not set")
            return False
        
        # Initialize client
        client = Anthropic(api_key=api_key)
        
        # Try to list available models if possible, or use a well-known model that should work
        try:
            if hasattr(client, 'models') and callable(getattr(client, 'models').list):
                models = client.models.list()
                print("Available Anthropic models:")
                for model in models.data:
                    print(f"- {model.id}")
            else:
                print("Model listing not available in this version of the Anthropic SDK")
                print("Trying a test call with a well-known model...")
                
                # Test with Claude 3 Haiku
                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=10,
                    system="You are a helpful assistant.",
                    messages=[{"role": "user", "content": "Say hello"}]
                )
                print(f"Test successful with model: claude-3-haiku-20240307")
                print(f"Response: {response.content[0].text}")
                
                # List suggested models to try
                print("\nSuggested Anthropic models to try:")
                print("- claude-3-opus-20240229")
                print("- claude-3-sonnet-20240229")
                print("- claude-3-haiku-20240307")
                print("- claude-3-haiku-20240229")
            
            return True
        except Exception as e:
            print(f"Error checking Anthropic models: {str(e)}")
            return False
    
    except ImportError:
        print("Anthropic SDK not installed. Install with: pip install anthropic")
        return False


def check_openai_models():
    """Check available OpenAI models."""
    try:
        from openai import OpenAI
        
        # Get API key from environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("OPENAI_API_KEY environment variable is not set")
            return False
        
        # Initialize client
        client = OpenAI(api_key=api_key)
        
        try:
            # List models
            models = client.models.list()
            print("\nAvailable OpenAI models:")
            gpt_models = [model.id for model in models.data if model.id.startswith("gpt-")]
            for model_id in sorted(gpt_models):
                print(f"- {model_id}")
                
            return True
        except Exception as e:
            print(f"Error checking OpenAI models: {str(e)}")
            return False
    
    except ImportError:
        print("OpenAI SDK not installed. Install with: pip install openai")
        return False


def check_ollama_models():
    """Check available Ollama models."""
    try:
        import requests
        
        try:
            # Check if Ollama is running
            response = requests.get("http://localhost:11434/api/version", timeout=1)
            if response.status_code == 200:
                # List models
                try:
                    models_response = requests.get("http://localhost:11434/api/tags", timeout=1)
                    if models_response.status_code == 200:
                        data = models_response.json()
                        if "models" in data and data["models"]:
                            print("\nAvailable Ollama models:")
                            for model in data["models"]:
                                print(f"- {model['name']}")
                        else:
                            print("\nNo Ollama models found. Try pulling some models:")
                            print("  ollama pull llama3")
                            print("  ollama pull mistral")
                            print("  ollama pull gemma")
                    else:
                        print(f"\nFailed to list Ollama models: {models_response.status_code}")
                except Exception as e:
                    print(f"\nError listing Ollama models: {str(e)}")
                    
                return True
            else:
                print("\nOllama server is not responding correctly")
                return False
        except requests.RequestException:
            print("\nOllama server is not running at http://localhost:11434")
            print("Start Ollama with: ollama serve")
            return False
    
    except ImportError:
        print("Requests library not installed. Install with: pip install requests")
        return False


def main():
    """Check available LLM models for different providers."""
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Check available LLM models")
    parser.add_argument(
        "--provider", 
        choices=["all", "anthropic", "openai", "ollama"],
        default="all",
        help="Which provider to check"
    )
    args = parser.parse_args()
    
    if args.provider == "all" or args.provider == "anthropic":
        print("\n=== Checking Anthropic Models ===")
        check_anthropic_models()
    
    if args.provider == "all" or args.provider == "openai":
        print("\n=== Checking OpenAI Models ===")
        check_openai_models()
    
    if args.provider == "all" or args.provider == "ollama":
        print("\n=== Checking Ollama Models ===")
        check_ollama_models()


if __name__ == "__main__":
    main()