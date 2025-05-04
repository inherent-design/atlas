#!/usr/bin/env python3
"""
Test script for the Atlas framework.

This script tests different aspects of the Atlas framework implementation.
"""

import os
import sys
import argparse

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from atlas.core.config import AtlasConfig
from atlas.core.prompts import load_system_prompt
from atlas.agents.base import AtlasAgent
from atlas.agents.controller import ControllerAgent
from atlas.agents.worker import WorkerAgent, RetrievalWorker, AnalysisWorker, DraftWorker
from atlas.knowledge.ingest import DocumentProcessor
from atlas.knowledge.retrieval import KnowledgeBase
from atlas.orchestration.coordinator import AgentCoordinator
from atlas.graph.workflows import run_rag_workflow, run_controller_workflow


def test_base_agent(args):
    """Test the base Atlas agent."""
    print("\n=== Testing Base Agent ===\n")
    
    # Initialize agent
    agent = AtlasAgent(system_prompt_file=args.system_prompt)
    
    # Process a test message
    if args.query:
        query = args.query
    else:
        query = "What is the trimodal methodology in Atlas?"
    
    print(f"Query: {query}\n")
    response = agent.process_message(query)
    print(f"Response: {response}\n")


def test_controller_agent(args):
    """Test the controller agent with workers."""
    print("\n=== Testing Controller Agent ===\n")
    
    # Initialize controller
    controller = ControllerAgent(
        system_prompt_file=args.system_prompt,
        worker_count=3
    )
    
    # Process a test message
    if args.query:
        query = args.query
    else:
        query = "Explain the knowledge graph structure in Atlas."
    
    print(f"Query: {query}\n")
    response = controller.process_message(query)
    print(f"Response: {response}\n")
    
    # Get worker results
    worker_results = controller.get_worker_results()
    print("Worker Results:")
    for i, result in enumerate(worker_results):
        print(f"Worker {i+1}: {result['worker_id']}")


def test_coordinator(args):
    """Test the agent coordinator."""
    print("\n=== Testing Agent Coordinator ===\n")
    
    # Initialize coordinator
    coordinator = AgentCoordinator(
        system_prompt_file=args.system_prompt,
        worker_count=3
    )
    
    # Process a test message
    if args.query:
        query = args.query
    else:
        query = "How does Atlas implement perspective frameworks?"
    
    print(f"Query: {query}\n")
    response = coordinator.process_message(query)
    print(f"Response: {response}\n")


def test_workflows(args):
    """Test LangGraph workflows."""
    print("\n=== Testing LangGraph Workflows ===\n")
    
    # Create config
    config = AtlasConfig(
        collection_name="atlas_knowledge_base"
    )
    
    # Test RAG workflow
    print("Testing RAG workflow...")
    if args.query:
        query = args.query
    else:
        query = "What are the communication principles in Atlas?"
    
    print(f"Query: {query}\n")
    
    # Run the workflow
    rag_result = run_rag_workflow(
        query=query,
        system_prompt_file=args.system_prompt,
        config=config
    )
    
    # Extract response
    response = ""
    for msg in reversed(rag_result.messages):
        if msg["role"] == "assistant":
            response = msg["content"]
            break
    
    print(f"RAG Response: {response}\n")
    
    # Test controller workflow
    print("Testing controller workflow...")
    controller_result = run_controller_workflow(
        query=query,
        system_prompt_file=args.system_prompt,
        config=config
    )
    
    # Extract response
    response = ""
    for msg in reversed(controller_result.messages):
        if msg["role"] == "assistant":
            response = msg["content"]
            break
    
    print(f"Controller Response: {response}\n")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Test the Atlas framework")
    
    # Test options
    parser.add_argument(
        "-t", "--test", 
        choices=["base", "controller", "coordinator", "workflows", "all"],
        default="all",
        help="Test to run"
    )
    
    # General options
    parser.add_argument(
        "-s", "--system-prompt", 
        type=str, 
        help="Path to system prompt file"
    )
    parser.add_argument(
        "-q", "--query", 
        type=str, 
        help="Query to test with"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for testing."""
    args = parse_args()
    
    # Check for environment variables
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
        print("Please set it before running tests.")
        print("Example: export ANTHROPIC_API_KEY=your_api_key_here")
        sys.exit(1)
    
    # Run tests
    if args.test == "base" or args.test == "all":
        test_base_agent(args)
    
    if args.test == "controller" or args.test == "all":
        test_controller_agent(args)
    
    if args.test == "coordinator" or args.test == "all":
        test_coordinator(args)
    
    if args.test == "workflows" or args.test == "all":
        test_workflows(args)


if __name__ == "__main__":
    main()