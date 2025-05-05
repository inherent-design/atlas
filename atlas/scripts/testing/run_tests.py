#!/usr/bin/env python3
"""
Test runner for Atlas framework.

This script provides a unified interface for running all Atlas tests.
"""

import os
import sys
import argparse
import unittest


def run_mock_tests():
    """Run all mock tests."""
    print("=== Running Atlas Mock Tests ===")
    print("NOTE: Mock tests do not incur API costs as they use mocked responses.")
    
    # Import the mock test module
    from atlas.tests.test_mock import (
        TestConfig,
        TestSystemPrompt,
        TestAgent,
        TestControllerAgent,
        TestWorkerAgent,
        TestSpecializedWorkers,
        TestRagWorkflow,
        TestControllerWorkflow,
        setup_test_environment
    )
    
    # Set up the test environment
    setup_test_environment()
    
    # Create a test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(loader.loadTestsFromTestCase(TestConfig))
    suite.addTest(loader.loadTestsFromTestCase(TestSystemPrompt))
    suite.addTest(loader.loadTestsFromTestCase(TestAgent))
    suite.addTest(loader.loadTestsFromTestCase(TestControllerAgent))
    suite.addTest(loader.loadTestsFromTestCase(TestWorkerAgent))
    suite.addTest(loader.loadTestsFromTestCase(TestSpecializedWorkers))
    suite.addTest(loader.loadTestsFromTestCase(TestRagWorkflow))
    suite.addTest(loader.loadTestsFromTestCase(TestControllerWorkflow))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n=== {result.testsRun - len(result.errors) - len(result.failures)}/{result.testsRun} mock tests passed! ===")
    if result.skipped:
        print(f"Note: {len(result.skipped)} tests were skipped as expected during development.")
    
    return result.wasSuccessful()


def run_minimal_tests():
    """Run minimal tests."""
    print("=== Running Atlas Minimal Tests ===")
    
    # Import the minimal test module
    from atlas.tests.test_minimal import (
        TestConfig,
        TestSystemPrompt,
        setup_test_environment
    )
    
    # Set up the test environment
    setup_test_environment()
    
    # Create a test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(loader.loadTestsFromTestCase(TestConfig))
    suite.addTest(loader.loadTestsFromTestCase(TestSystemPrompt))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n=== {result.testsRun - len(result.errors) - len(result.failures)}/{result.testsRun} minimal tests passed! ===")
    
    return result.wasSuccessful()


def run_api_tests(test_name, system_prompt=None, query=None):
    """Run API tests.
    
    Args:
        test_name: Name of the test to run.
        system_prompt: Optional path to system prompt file.
        query: Optional query to test with.
    
    Returns:
        True if all tests passed, False otherwise.
    """
    print("=== Running Atlas API Tests ===")
    print("NOTE: These tests will make real API calls and incur costs.")
    
    # Check for environment variables
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
        print("Please set it before running API tests.")
        print("Example: export ANTHROPIC_API_KEY=your_api_key_here")
        return False
    
    # Import the API test module
    from atlas.tests.test_api import (
        TestBaseAgent,
        TestControllerAgent,
        TestCoordinator,
        TestWorkflows
    )
    
    # Create a test suite
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # Set common attributes for test classes
    for test_class in [TestBaseAgent, TestControllerAgent, TestCoordinator, TestWorkflows]:
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
    print(f"\n=== {result.testsRun - len(result.errors) - len(result.failures)}/{result.testsRun} API tests passed! ===")
    if result.skipped:
        print(f"Note: {len(result.skipped)} tests were skipped.")
    
    return result.wasSuccessful()


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run Atlas tests")
    
    # Test type
    parser.add_argument(
        "-t", 
        "--test-type",
        choices=["mock", "minimal", "api", "all"],
        default="mock",
        help="Type of tests to run (default: mock)"
    )
    
    # API test options
    parser.add_argument(
        "--api-test",
        choices=["base", "controller", "coordinator", "workflows", "all"],
        default="base",
        help="API test to run (default: base)"
    )
    
    # General options
    parser.add_argument(
        "-s", "--system-prompt", type=str, help="Path to system prompt file for API tests"
    )
    parser.add_argument(
        "-q", "--query", type=str, help="Query to test with for API tests"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for running tests."""
    args = parse_args()
    
    success = True
    
    if args.test_type in ["mock", "all"]:
        mock_success = run_mock_tests()
        success = success and mock_success
        print("\n")
    
    if args.test_type in ["minimal", "all"]:
        minimal_success = run_minimal_tests()
        success = success and minimal_success
        print("\n")
    
    if args.test_type in ["api", "all"]:
        api_success = run_api_tests(args.api_test, args.system_prompt, args.query)
        success = success and api_success
        print("\n")
    
    # Return appropriate exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()