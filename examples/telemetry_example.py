"""
Example of using Atlas with custom telemetry configuration.

This script demonstrates how to initialize the Atlas client with 
custom telemetry settings, including sending to a specific OTLP endpoint.
"""

import os
import sys
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from atlas import create_query_client
from atlas.core.telemetry import initialize_telemetry, enable_telemetry

def print_streaming(delta: str, full_text: str) -> None:
    """Print streaming output character by character."""
    for char in delta:
        print(char, end="", flush=True)
        time.sleep(0.01)  # Small delay to simulate typing

def main():
    """Run a query with custom telemetry configuration."""
    print("Initializing Atlas with custom telemetry settings...")
    
    # Set environment variables for telemetry
    os.environ["ATLAS_ENABLE_TELEMETRY"] = "true"
    os.environ["ATLAS_TELEMETRY_CONSOLE_EXPORT"] = "true"  # To see telemetry in console
    
    # Initialize telemetry with custom settings
    # Replace with your actual OTLP endpoint if you have one
    initialize_telemetry(
        service_name="atlas-custom",
        service_version="0.1.0",
        enable_console_exporter=True,  # For debugging - shows spans in console
        enable_otlp_exporter=True,     # Enable OTLP exporter
        otlp_endpoint="http://localhost:4317",  # Default OTLP endpoint
        sampling_ratio=1.0,            # Capture all telemetry
        force_enable=True              # Force enable even if env vars say otherwise
    )
    
    # Create a client - using SKIP_API_KEY_CHECK for testing
    # Remove this for production use with real API key
    os.environ["SKIP_API_KEY_CHECK"] = "true"
    client = create_query_client()
    
    # Run a simple query
    query = "What is the trimodal methodology in Atlas?"
    print(f"\nRunning query: {query}\n")
    
    try:
        print("Streaming Response with telemetry enabled:")
        result = client.query_streaming(query, print_streaming)
        print("\n\nStreaming completed with result length:", len(result))
    except Exception as e:
        print(f"\nError in streaming: {e}")
        
        print("\nFalling back to regular query...")
        result = client.query(query)
        print(f"Regular query result:\n{result}")
    
    print("\nTelemetry example completed!")
    print("Note: If you had a real OTLP collector running, telemetry would be sent there")

if __name__ == "__main__":
    main()