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

## Complete Example

Here's a complete example demonstrating streaming functionality:

```python
import logging
import os
import sys
import time

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import atlas package
from atlas import create_query_client


def print_streaming(delta: str, full_text: str) -> None:
    """Print streaming output character by character.

    Args:
        delta: The new text chunk.
        full_text: The complete text so far.
    """
    # Print the delta without newline and flush immediately
    for char in delta:
        print(char, end="", flush=True)
        time.sleep(0.01)  # Small delay to simulate typing


def main():
    """Run a streaming test."""
    print("Testing Atlas streaming query...")

    # Create a client with SKIP_API_KEY_CHECK enabled for testing
    os.environ["SKIP_API_KEY_CHECK"] = "true"
    client = create_query_client()

    # Use a simple query
    query = "What is the trimodal methodology in Atlas?"
    print(f"Query: {query}")

    try:
        print("Streaming Response:")
        # Try streaming response
        result = client.query_streaming(query, print_streaming)
        print("\n\nStreaming completed with result length:", len(result))
    except Exception as e:
        print(f"\nError in streaming: {e}")

        print("\nFalling back to regular query...")
        # Try regular query
        result = client.query(query)
        print(f"Regular query result:\n{result}")

    print("\nTest completed!")


if __name__ == "__main__":
    main()
```

## Performance Considerations

When using streaming in production applications:

1. **Network Reliability**: Ensure the connection can maintain a stream of data
2. **Resource Usage**: Streaming can require keeping connections open longer
3. **UI Responsiveness**: Ensure the UI doesn't block while processing streaming updates
4. **Timeout Handling**: Implement timeouts in case streaming hangs

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