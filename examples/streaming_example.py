"""
Example of streaming responses from the Atlas query client.

This script demonstrates how to use the streaming functionality to get
incremental responses from the language model, which creates a more
interactive experience for the user.
"""

import sys
import os
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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