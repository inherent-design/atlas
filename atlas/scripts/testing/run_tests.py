#!/usr/bin/env python3
"""
Test runner for Atlas framework.

This script provides a unified interface for running all Atlas tests.
Tests are organized in the atlas/tests/ directory with consistent naming:
- test_*.py: Unit tests for specific modules
- test_mock.py: Mock tests that don't require API keys
- test_api.py: Integration tests that require API keys
"""

import os
import sys
import argparse
import unittest
import importlib
import glob
from pathlib import Path


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
        setup_test_environment,
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
    print(
        f"\n=== {result.testsRun - len(result.errors) - len(result.failures)}/{result.testsRun} mock tests passed! ==="
    )
    if result.skipped:
        print(
            f"Note: {len(result.skipped)} tests were skipped as expected during development."
        )

    return result.wasSuccessful()


def run_minimal_tests():
    """Run minimal tests."""
    print("=== Running Atlas Minimal Tests ===")

    # Import the minimal test module
    from atlas.tests.test_minimal import (
        TestConfig,
        TestSystemPrompt,
        setup_test_environment,
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
    print(
        f"\n=== {result.testsRun - len(result.errors) - len(result.failures)}/{result.testsRun} minimal tests passed! ==="
    )

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
        TestWorkflows,
    )

    # Create a test suite
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
        f"\n=== {result.testsRun - len(result.errors) - len(result.failures)}/{result.testsRun} API tests passed! ==="
    )
    if result.skipped:
        print(f"Note: {len(result.skipped)} tests were skipped.")

    return result.wasSuccessful()


def run_unit_tests(module_name=None):
    """Run unit tests for a specific module or all modules.

    Args:
        module_name: Optional name of the module to test (e.g., 'models', 'env').
                    If None, all unit tests are run.

    Returns:
        True if all tests passed, False otherwise.
    """
    if module_name:
        print(f"=== Running Unit Tests for {module_name} module ===")
    else:
        print("=== Running All Unit Tests ===")

    # Get project root directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    tests_dir = os.path.join(project_root, "atlas/tests")

    # Find test files
    test_files = []
    if module_name:
        # Look for a specific test file
        pattern = f"test_{module_name}*.py"
        test_files = glob.glob(os.path.join(tests_dir, pattern))
        if not test_files:
            print(f"No test file found matching {pattern}")
            return False
    else:
        # Find all test files except test_mock.py and test_api.py
        all_test_files = glob.glob(os.path.join(tests_dir, "test_*.py"))
        test_files = [
            file
            for file in all_test_files
            if not (file.endswith("test_mock.py") or file.endswith("test_api.py"))
        ]

    # Import and run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for test_file in test_files:
        test_module_name = os.path.basename(test_file)[:-3]  # Remove .py
        module_path = f"atlas.tests.{test_module_name}"
        try:
            test_module = importlib.import_module(module_path)
            module_tests = loader.loadTestsFromModule(test_module)
            suite.addTests(module_tests)
            print(f"Added tests from {test_module_name}")
        except ImportError as e:
            print(f"Error importing {module_path}: {e}")

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print(
        f"\n=== {result.testsRun - len(result.errors) - len(result.failures)}/{result.testsRun} unit tests passed! ==="
    )
    if result.skipped:
        print(f"Note: {len(result.skipped)} tests were skipped.")

    return result.wasSuccessful()


def run_real_api_tests():
    """Run real API tests that make actual provider API calls.
    
    These tests are controlled by environment variables:
    - RUN_API_TESTS=true: Enables real API tests
    - RUN_EXPENSIVE_TESTS=true: Enables expensive API tests (GPT-4, Claude Opus, etc.)
    
    Returns:
        True if all tests passed, False otherwise.
    """
    print("=== Running Real Provider API Tests ===")
    print("NOTE: These tests make actual API calls and may incur costs.")
    
    # Check environment variable
    if not os.environ.get("RUN_API_TESTS"):
        print("ERROR: RUN_API_TESTS environment variable is not set.")
        print("Please set it before running real API tests.")
        print("Example: export RUN_API_TESTS=true python -m atlas.scripts.testing.run_tests -t real_api")
        return False
    
    # Import the real API test module
    try:
        from atlas.tests.real_api_tests import (
            TestOpenAIRealAPI,
            TestOllamaRealAPI,
            TestAnthropicRealAPI,
        )
    except ImportError as e:
        print(f"Error importing real_api_tests module: {e}")
        return False
    
    # Create a test suite
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # Add test cases
    suite.addTest(loader.loadTestsFromTestCase(TestOpenAIRealAPI))
    suite.addTest(loader.loadTestsFromTestCase(TestOllamaRealAPI))
    suite.addTest(loader.loadTestsFromTestCase(TestAnthropicRealAPI))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(
        f"\n=== {result.testsRun - len(result.errors) - len(result.failures)}/{result.testsRun} real API tests passed! ==="
    )
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
        choices=["unit", "mock", "minimal", "api", "real_api", "all"],
        default="mock",
        help="Type of tests to run (default: mock)",
    )

    # Module to test
    parser.add_argument(
        "-m", "--module", type=str, help="Module to test (e.g., 'models', 'env')"
    )

    # API test options
    parser.add_argument(
        "--api-test",
        choices=["base", "controller", "coordinator", "workflows", "all"],
        default="base",
        help="API test to run (default: base)",
    )

    # General options
    parser.add_argument(
        "-s",
        "--system-prompt",
        type=str,
        help="Path to system prompt file for API tests",
    )
    parser.add_argument(
        "-q", "--query", type=str, help="Query to test with for API tests"
    )

    return parser.parse_args()


def main():
    """Main entry point for running tests."""
    args = parse_args()

    success = True

    if args.test_type in ["unit", "all"]:
        unit_success = run_unit_tests(args.module)
        success = success and unit_success
        print("\n")

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
        
    if args.test_type in ["real_api", "all"]:
        real_api_success = run_real_api_tests()
        success = success and real_api_success
        print("\n")

    # Return appropriate exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
