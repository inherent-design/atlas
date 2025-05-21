"""
Example demonstrating integration of Core Services with Knowledge System.

This example shows how to use the event system with knowledge retrieval operations,
allowing you to track and analyze performance, monitor operations, and collect
diagnostic information about knowledge retrieval.
"""

import argparse
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from atlas.core.services.events import EventSystem, create_event_system
from atlas.core.services.middleware import HistoryMiddleware, create_logging_middleware
from atlas.knowledge.events import (
    EventEnabledKnowledgeBase,
    create_event_enabled_knowledge_base,
    retrieve_knowledge_with_events,
)
from atlas.knowledge.retrieval import KnowledgeBase
from atlas.knowledge.settings import RetrievalSettings
from examples.common import print_header, print_json, print_section, setup_logging


def event_callback(event: Dict[str, Any]) -> None:
    """Handle knowledge events for demonstration.

    Args:
        event: The event data to handle.
    """
    # Extract basic event info
    event_type = event.get("event_type", "unknown")
    timestamp = event.get("timestamp", datetime.now().isoformat())
    event_data = event.get("data", {})

    # Format timestamp
    try:
        dt = datetime.fromisoformat(timestamp)
        formatted_time = dt.strftime("%H:%M:%S.%f")[:-3]
    except:
        formatted_time = timestamp

    # Print different information based on event type
    if event_type.endswith(".start"):
        print(f"[{formatted_time}] 🚀 Started: {event_type}")

        # For retrieval operations, print the query
        if "retrieve" in event_type:
            query = event_data.get("query", "")
            print(f"  Query: {query[:50]}{'...' if len(query) > 50 else ''}")

    elif event_type.endswith(".end"):
        duration = event_data.get("duration_seconds", 0) * 1000  # Convert to ms
        result_count = event_data.get("result_count", 0)
        print(
            f"[{formatted_time}] ✅ Completed: {event_type} in {duration:.2f}ms with {result_count} results"
        )

        # Print result summary for retrieval operations
        if "retrieve" in event_type and "result_summary" in event_data:
            print("\n  Top results:")
            for i, result in enumerate(event_data["result_summary"]):
                score = result.get("relevance_score", 0)
                source = result.get("source", "unknown")
                content = result.get("content_preview", "")
                print(f"  {i+1}. [{score:.4f}] {source}")
                print(f"     {content}")
            print()

    elif event_type.endswith(".error"):
        error_type = event_data.get("error_type", "Unknown")
        error_msg = event_data.get("error", "No error message")
        print(f"[{formatted_time}] ❌ Error: {event_type}")
        print(f"  {error_type}: {error_msg}")

    elif "cache" in event_type:
        hits = event_data.get("cache_hits", 0)
        misses = event_data.get("cache_misses", 0)
        ratio = event_data.get("hit_ratio", 0) * 100
        print(f"[{formatted_time}] 💾 Cache: {event_type}")
        print(f"  Hits: {hits}, Misses: {misses}, Ratio: {ratio:.1f}%")


def demonstrate_knowledge_events():
    """Demonstrate event integration with knowledge system."""
    print_header("Knowledge System Event Integration")

    # Create event system with history tracking
    event_system = create_event_system()
    history_middleware = HistoryMiddleware(max_history=100)
    event_system.add_middleware(history_middleware)
    event_system.add_middleware(create_logging_middleware())

    # Subscribe to knowledge events
    event_system.subscribe(event_type="knowledge.*", callback=event_callback)

    print_section("Creating Event-Enabled Knowledge Base")

    # Method 1: Create using mixin class directly
    class CustomKnowledgeBase(EventEnabledKnowledgeBase, KnowledgeBase):
        """Custom knowledge base with event system integration."""

        pass

    # Method 2: Create using factory function
    EventEnabledKB = create_event_enabled_knowledge_base()

    # Create instance
    kb = EventEnabledKB(event_system=event_system)
    print(f"Created {kb.__class__.__name__}\n")

    # Set up sample queries
    queries = [
        "How does Atlas handle multi-agent workflows?",
        "What is ChromaDB and how is it used in Atlas?",
        "What providers are supported by Atlas?",
        "How does the event system work?",
        "What are state transitions and validators?",
    ]

    print_section("Basic Knowledge Retrieval with Events")
    for query in queries[:2]:
        print(f"\nRetrieving for query: {query}")
        results = kb.retrieve(query, n_results=3)
        print(f"Found {len(results)} results\n")
        time.sleep(1)  # Just to separate events in output

    print_section("Hybrid Retrieval with Events")
    query = queries[2]
    print(f"\nPerforming hybrid retrieval for: {query}")
    results = kb.retrieve_hybrid(query=query, n_results=3, semantic_weight=0.6, keyword_weight=0.4)
    print(f"Found {len(results)} results\n")

    print_section("Metadata Search with Events")
    print("\nSearching for version information:")
    versions = kb.get_versions()
    print(f"Found {len(versions)} versions\n")

    # Simulate cache hit and miss
    print_section("Cache Tracking")
    print("\nSimulating cache behavior:")
    kb.track_cache_miss("What is the purpose of Atlas?")
    kb.track_cache_hit("How does Atlas handle multi-agent workflows?")
    kb.track_cache_hit("What providers are supported by Atlas?")
    kb.track_cache_miss("How do I contribute to Atlas?")
    print()

    # Print metrics
    print_section("Knowledge Base Metrics")
    metrics = kb.get_knowledge_metrics()
    print_json(metrics)

    # Print event history
    print_section("Event History")
    events = kb.get_event_history(limit=10)
    print(f"Most recent {len(events)} events:\n")
    for event in events:
        event_type = event.get("event_type", "unknown")
        timestamp = event.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime("%H:%M:%S.%f")[:-3]
        except:
            formatted_time = timestamp

        print(f"[{formatted_time}] {event_type}")

    print("\nKnowledge system event integration demonstration complete.")


def demonstrate_langgraph_integration():
    """Demonstrate langgraph integration with knowledge events."""
    print_header("LangGraph Integration with Knowledge Events")

    # Create event system
    event_system = create_event_system()
    event_system.subscribe(event_type="agent.knowledge.*", callback=event_callback)

    # Create a simple state for demonstration
    state = {"messages": [{"role": "user", "content": "How does the Atlas event system work?"}]}

    print_section("Using retrieve_knowledge_with_events")
    print("Processing state with user query about event system...")

    # Use the event-enabled knowledge retrieval function
    updated_state = retrieve_knowledge_with_events(
        state=state, settings=RetrievalSettings(num_results=3), event_system=event_system
    )

    # Display the retrieved documents
    documents = updated_state.get("context", {}).get("documents", [])
    print(f"\nRetrieved {len(documents)} documents for the query")

    if documents:
        print("\nTop document preview:")
        doc = documents[0]
        source = doc.get("metadata", {}).get("source", "unknown")
        score = doc.get("relevance_score", 0)
        content = doc.get("content", "")[:200] + "..."
        print(f"Source: {source}")
        print(f"Score: {score:.4f}")
        print(f"Content: {content}")

    print("\nLangGraph integration demonstration complete.")


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Atlas Knowledge System Event Integration Example")
    parser.add_argument(
        "--langgraph", action="store_true", help="Demonstrate LangGraph integration"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    # Setup logging
    setup_logging(debug=args.debug)

    # Run appropriate demonstration
    if args.langgraph:
        demonstrate_langgraph_integration()
    else:
        demonstrate_knowledge_events()
