# Streaming Example

This example demonstrates how to use Atlas with streaming responses to create a more interactive experience for users.

## Overview

Streaming responses allow you to display partial responses as they are generated, rather than waiting for the complete response. This provides several benefits:

1. **Improved User Experience**: Users see the response building immediately
2. **Faster Perceived Response Time**: No waiting for the complete generation
3. **Interactive Applications**: Enables more dynamic interfaces
4. **Progress Feedback**: Users know the system is working on their query

## Setup

First, import the necessary modules and create a query client:

```python
import logging
import os
import sys
import time

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import atlas package
from atlas import create_query_client

# Create a client
client = create_query_client()
```

## Creating a Streaming Callback

The streaming functionality requires a callback function that receives incremental text chunks:

```python
def print_streaming(delta: str, full_text: str) -> None:
    """Print streaming output character by character.

    Args:
        delta: The new text chunk that was just generated.
        full_text: The complete text generated so far.
    """
    # Print the delta without newline and flush immediately
    for char in delta:
        print(char, end="", flush=True)
        time.sleep(0.01)  # Small delay to simulate typing
```

This callback function receives two arguments:
- `delta`: The new text chunk that was just generated
- `full_text`: The complete text that has been generated so far

You can customize this function to fit your application's needs, such as:
- Updating a UI element
- Adding formatting or processing of the text
- Tracking response progress
- Adding animation effects

## Basic Streaming Query

The simplest way to use streaming is to send a query and provide a callback function:

```python
# Define a query
query = "What is the trimodal methodology in Atlas?"
print(f"Query: {query}")

print("Streaming Response:")
# Send the query with streaming enabled
result = client.query_streaming(query, print_streaming)

# The result contains the complete response after streaming finishes
print("\n\nTotal response length:", len(result))
```

## Error Handling

Always implement error handling to gracefully recover from streaming issues:

```python
try:
    print("Streaming Response:")
    # Try streaming response
    result = client.query_streaming(query, print_streaming)
    print("\n\nStreaming completed with result length:", len(result))
except Exception as e:
    print(f"\nError in streaming: {e}")

    print("\nFalling back to regular query...")
    # Fall back to regular query
    result = client.query(query)
    print(f"Regular query result:\n{result}")
```

## Advanced Streaming Callback

For more sophisticated applications, you can create a callback that provides richer functionality:

```python
class StreamingHandler:
    def __init__(self):
        self.start_time = time.time()
        self.tokens = 0
        self.words = 0
        
    def stream_callback(self, delta: str, full_text: str):
        # Update counters
        self.tokens += 1
        if delta.strip() and delta.strip() not in ",.;:!?":
            self.words += 1
            
        # Print the delta
        print(delta, end="", flush=True)
        
        # Optionally show progress stats every 20 tokens
        if self.tokens % 20 == 0:
            elapsed = time.time() - self.start_time
            tokens_per_second = self.tokens / elapsed
            print(f"\n[Generated {self.tokens} tokens at {tokens_per_second:.1f} tokens/sec]", end="", flush=True)

# Create handler and use its callback method
handler = StreamingHandler()
client.query_streaming(query, handler.stream_callback)
```

## Streaming with Context

You can combine streaming with document retrieval:

```python
# First retrieve context documents
documents = client.retrieve_only(query)
print(f"Retrieved {len(documents)} relevant documents")

# Show the most relevant document
if documents:
    print(f"Most relevant document: {documents[0]['metadata'].get('source', 'Unknown')}")
    
# Then stream the response
print("\nStreaming Response:")
result = client.query_streaming(query, print_streaming)
```

## Complete Example with Multiple Providers

Atlas supports streaming with multiple model providers. Here's a complete example demonstrating how to use streaming with different providers:

```python
import argparse
import logging
import os
import sys
import time
from typing import Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import atlas package
from atlas import create_query_client
from atlas.models.factory import create_provider
from atlas.models.base import ModelRequest, ModelMessage

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
        use_mock: If True, use mock mode without API key.
    """
    print("\n" + "="*50)
    print("DEMO 1: Streaming using Atlas Query Client")
    print("="*50)

    # Set environment for testing if needed
    if use_mock:
        os.environ["SKIP_API_KEY_CHECK"] = "true"
    
    # Create a client
    client = create_query_client()

    # Use a simple query
    query = "What is the trimodal methodology in Atlas?"
    print(f"Query: {query}")

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
        use_mock: If True, use mock mode without API key.
    """
    print("\n" + "="*50)
    print(f"DEMO 2: Direct Streaming with {provider_name.capitalize()} Provider")
    print("="*50)
    
    # Provider-specific configurations
    provider_configs = {
        "anthropic": {
            "default_model": "claude-3-7-sonnet-20250219",
            "max_tokens": 300,
        },
        "openai": {
            "default_model": "gpt-4.1",
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
    
    # Set environment for testing if needed
    if use_mock:
        os.environ["SKIP_API_KEY_CHECK"] = "true"
    
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
                       help="Use mock mode without API key")
    
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
```

## Command-Line Interface

The streaming example includes a command-line interface that allows you to test different providers and models:

```bash
# Run with the default mock provider (no API key required)
python examples/streaming_example.py

# Run with a specific provider
python examples/streaming_example.py --provider anthropic

# Run with a specific model
python examples/streaming_example.py --provider openai --model gpt-4.1

# Test all providers (requires API keys)
python examples/streaming_example.py --provider all

# Run in mock mode (no API key required)
python examples/streaming_example.py --provider anthropic --mock

# Only run the client demo
python examples/streaming_example.py --provider client
```

### Command-Line Arguments

| Argument | Description | Default |
| -------- | ----------- | ------- |
| `--provider`, `-p` | The provider to use (anthropic, openai, ollama, mock, all, client) | mock |
| `--model`, `-m` | Specific model to use (provider-dependent) | Provider default |
| `--mock` | Run in mock mode without API key | False |

Using the command-line interface makes it easy to test streaming functionality with different providers and models without changing the code.

## Performance Considerations

When using streaming in production applications:

1. **Network Reliability**: Ensure the connection can maintain a stream of data
2. **Resource Usage**: Streaming can require keeping connections open longer
3. **UI Responsiveness**: Ensure the UI doesn't block while processing streaming updates
4. **Timeout Handling**: Implement timeouts in case streaming hangs
5. **Token Tracking**: Monitor token usage during streaming to estimate costs and prevent excess usage

## Integration with Web Applications

Streaming works well with web frameworks that support server-sent events (SSE) or WebSockets:

```python
# Example with Flask and SSE
from flask import Flask, Response, render_template
import json

app = Flask(__name__)
client = create_query_client()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream', methods=['POST'])
def stream():
    query = request.json.get('query', '')
    
    def stream_generator():
        buffer = []
        
        def callback(delta, full_text):
            buffer.append(delta)
            if len(buffer) >= 5 or '\n' in delta:
                chunk = ''.join(buffer)
                yield f"data: {json.dumps({'text': chunk})}\n\n"
                buffer.clear()
        
        try:
            client.query_streaming(query, callback)
            if buffer:  # Send any remaining text
                yield f"data: {json.dumps({'text': ''.join(buffer)})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(stream_generator(), mimetype='text/event-stream')
```

## Related Documentation

- [Query Workflow](../../workflows/query.md) - Detailed information about the query workflow
- [Query Example](./query_example.md) - Basic query functionality
- [API Reference](../../reference/api.md) - Complete API documentation
- [Environment Variables](../../reference/env_variables.md) - Configuration options