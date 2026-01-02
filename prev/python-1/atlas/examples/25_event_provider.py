#!/usr/bin/env python
"""
Example demonstrating the event system integration with providers.

This example shows how to create providers with event tracking,
subscribe to provider events, and display event history.
"""

import time
from datetime import datetime
from typing import Any, Dict

from atlas.core.services.events import create_event_system, on_event
from atlas.core.services.middleware import HistoryMiddleware
from atlas.providers.factory import create_provider
from atlas.providers.messages import Message, MessageRole, ModelRequest


def format_event(event: Dict[str, Any]) -> str:
    """Format an event for display.

    Args:
        event: The event to format.

    Returns:
        A formatted string representation of the event.
    """
    event_type = event["event_type"]
    source = event["source"]
    timestamp = datetime.fromisoformat(event["timestamp"]).strftime("%H:%M:%S")

    if "latency" in event["data"]:
        latency = f"({event['data']['latency']:.2f}s)"
    else:
        latency = ""

    return f"[{timestamp}] {event_type} from {source} {latency}"


def main():
    """Main entry point for the example."""
    print("Event-Enabled Provider Example")
    print("-" * 60)

    # Create event system with history middleware
    event_system = create_event_system()
    history_middleware = HistoryMiddleware(max_history=100)
    event_system.add_middleware(history_middleware)

    # Define event handler
    @on_event(event_system, "provider.*")
    def handle_provider_event(event):
        """Handle provider events."""
        print(f"EVENT: {format_event(event)}")

    # Create provider with event system
    provider = create_provider(
        provider_name="mock",
        model_name="mock-standard",
        event_system=event_system,
        enable_events=True,
    )

    # Print provider info
    print(f"Created provider {provider.name} with model {provider.model_name}")
    print(f"Provider has events: {hasattr(provider, 'event_system')}")
    print("-" * 60)

    # Create a request
    messages = [Message(role=MessageRole.USER, content="Hello, how are you?")]
    request = ModelRequest(messages=messages)

    # Generate a response
    print("Generating a response...")
    response = provider.generate(request)
    print(f"Response: {response.content}")
    print("-" * 60)

    # Stream a response
    print("Streaming a response...")
    request = ModelRequest(
        messages=[Message(role=MessageRole.USER, content="Tell me a short story.")]
    )

    final_response, stream_handler = provider.stream(request)

    chunks = []
    while True:
        chunk = stream_handler.original_handler.get_next_chunk(timeout=1.0)
        if chunk is None:
            break
        chunks.append(chunk)
        print(f"Chunk: {chunk[:20]}...")

    print(f"Received {len(chunks)} chunks")
    print(f"Final response length: {len(final_response.content)}")
    print("-" * 60)

    # Wait for events to process
    time.sleep(0.5)

    # Print event history
    print("Event History:")
    for event in history_middleware.get_history():
        print(f"- {format_event(event)}")


if __name__ == "__main__":
    main()
