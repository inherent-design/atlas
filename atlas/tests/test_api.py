#!/usr/bin/env python3
"""
API integration test script for the Atlas framework.

This script tests different aspects of the Atlas framework implementation
with real API calls. It requires a valid ANTHROPIC_API_KEY environment variable.
For mock tests that don't require API keys, use test_mock.py instead.
"""

import os
import sys
import argparse
import unittest
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the Python path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from atlas.core.config import AtlasConfig
from atlas.agents.base import AtlasAgent
from atlas.agents.controller import ControllerAgent
from atlas.orchestration.coordinator import AgentCoordinator
from atlas.graph.workflows import run_rag_workflow, run_controller_workflow


class TestBaseAgent(unittest.TestCase):
    """Test the base Atlas agent."""

    def test_process_message(self):
        """Test the processing of a message."""
        # Skip if no API key is set
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self.skipTest("ANTHROPIC_API_KEY environment variable is not set.")

        # Initialize agent
        agent = AtlasAgent(system_prompt_file=self.system_prompt_file)

        # Process a test message
        query = self.query or "What is the trimodal methodology in Atlas?"

        print(f"Query: {query}\n")

        # Process message (usage tracking is now in the agent class)
        response = agent.process_message(query)

        # Basic assertions
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)

        print(f"Response: {response}\n")
        return response


class TestControllerAgent(unittest.TestCase):
    """Test the controller agent with workers."""

    def test_process_message(self):
        """Test the processing of a message."""
        # Skip if no API key is set
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self.skipTest("ANTHROPIC_API_KEY environment variable is not set.")

        # Initialize controller
        controller = ControllerAgent(
            system_prompt_file=self.system_prompt_file, worker_count=3
        )

        # Process a test message
        query = self.query or "Explain the knowledge graph structure in Atlas."

        print(f"Query: {query}\n")
        response = controller.process_message(query)

        # Basic assertions
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)

        print(f"Response: {response}\n")

        # Get worker results
        worker_results = controller.get_worker_results()
        self.assertIsNotNone(worker_results)

        print("Worker Results:")
        for i, result in enumerate(worker_results):
            self.assertIn("worker_id", result)
            print(f"Worker {i + 1}: {result['worker_id']}")

        return response


class TestCoordinator(unittest.TestCase):
    """Test the agent coordinator."""

    def test_process_message(self):
        """Test the processing of a message."""
        # Skip if no API key is set
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self.skipTest("ANTHROPIC_API_KEY environment variable is not set.")

        # Initialize coordinator
        coordinator = AgentCoordinator(
            system_prompt_file=self.system_prompt_file, worker_count=3
        )

        # Process a test message
        query = self.query or "How does Atlas implement perspective frameworks?"

        print(f"Query: {query}\n")
        response = coordinator.process_message(query)

        # Basic assertions
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)

        print(f"Response: {response}\n")
        return response


class TestWorkflows(unittest.TestCase):
    """Test LangGraph workflows."""

    def test_rag_workflow(self):
        """Test the RAG workflow."""
        # Skip if no API key is set
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self.skipTest("ANTHROPIC_API_KEY environment variable is not set.")

        # Create config
        config = AtlasConfig(collection_name="atlas_knowledge_base")

        # Test RAG workflow
        print("Testing RAG workflow...")
        query = self.query or "What are the communication principles in Atlas?"

        print(f"Query: {query}\n")

        # Run the workflow
        rag_result = run_rag_workflow(
            query=query, system_prompt_file=self.system_prompt_file, config=config
        )

        # Basic assertions
        self.assertIsNotNone(rag_result)
        self.assertTrue(hasattr(rag_result, "messages"))
        self.assertGreater(len(rag_result.messages), 0)

        # Extract response
        response = ""
        for msg in reversed(rag_result.messages):
            if msg["role"] == "assistant":
                response = msg["content"]
                break

        self.assertIsNotNone(response)
        self.assertGreater(len(response), 0)

        print(f"RAG Response: {response}\n")
        return response

    def test_controller_workflow(self):
        """Test the controller workflow."""
        # Skip if no API key is set
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self.skipTest("ANTHROPIC_API_KEY environment variable is not set.")

        # Create config
        config = AtlasConfig(collection_name="atlas_knowledge_base")

        # Test controller workflow
        print("Testing controller workflow...")
        query = self.query or "What are the communication principles in Atlas?"

        print(f"Query: {query}\n")

        # Run the workflow
        controller_result = run_controller_workflow(
            query=query, system_prompt_file=self.system_prompt_file, config=config
        )

        # Basic assertions
        self.assertIsNotNone(controller_result)
        self.assertTrue(hasattr(controller_result, "messages"))
        self.assertGreater(len(controller_result.messages), 0)

        # Extract response
        response = ""
        for msg in reversed(controller_result.messages):
            if msg["role"] == "assistant":
                response = msg["content"]
                break

        self.assertIsNotNone(response)
        self.assertGreater(len(response), 0)

        print(f"Controller Response: {response}\n")
        return response


def run_tests(
    test_name: str, system_prompt: Optional[str] = None, query: Optional[str] = None
):
    """Run the specified tests.

    Args:
        test_name: Name of the test to run.
        system_prompt: Optional path to system prompt file.
        query: Optional query to test with.
    """
    # Check for environment variables
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
        print("Please set it before running tests.")
        print("Example: export ANTHROPIC_API_KEY=your_api_key_here")
        print(
            "Alternatively, you can use test_mock.py which doesn't require an API key."
        )
        sys.exit(1)

    # Create and configure test suite
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    # Set common attributes for test classes
    for test_class in [
        TestBaseAgent,
        TestControllerAgent,
        TestCoordinator,
        TestWorkflows,
    ]:
        test_class.system_prompt_file = system_prompt
        test_class.query = query

    # Add appropriate tests to suite
    if test_name == "base" or test_name == "all":
        suite.addTest(loader.loadTestsFromTestCase(TestBaseAgent))

    if test_name == "controller" or test_name == "all":
        suite.addTest(loader.loadTestsFromTestCase(TestControllerAgent))

    if test_name == "coordinator" or test_name == "all":
        suite.addTest(loader.loadTestsFromTestCase(TestCoordinator))

    if test_name == "workflows" or test_name == "all":
        suite.addTest(loader.loadTestsFromTestCase(TestWorkflows))

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print(
        f"\n=== {result.testsRun - len(result.errors) - len(result.failures)}/{result.testsRun} tests passed! ==="
    )
    if result.skipped:
        print(f"Note: {len(result.skipped)} tests were skipped.")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Test the Atlas framework")

    # Test options
    parser.add_argument(
        "-t",
        "--test",
        choices=["base", "controller", "coordinator", "workflows", "all"],
        default="all",
        help="Test to run (default: all)",
    )

    # General options
    parser.add_argument(
        "-s", "--system-prompt", type=str, help="Path to system prompt file"
    )
    parser.add_argument("-q", "--query", type=str, help="Query to test with")

    return parser.parse_args()


def main():
    """Main entry point for testing."""
    args = parse_args()

    print("=== Running Atlas API Tests ===")
    print("NOTE: These tests will make real API calls and incur costs.")
    print("For cost-free mock tests, use test_mock.py instead.\n")

    # Run tests
    run_tests(args.test, args.system_prompt, args.query)


if __name__ == "__main__":
    main()
