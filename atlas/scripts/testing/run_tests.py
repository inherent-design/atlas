#!/usr/bin/env python3
"""
Atlas Test Runner

This script provides a unified interface for running Atlas tests with explicit
CLI flags instead of environment variables. It supports different test types,
providers, and granular control over test execution.

Usage examples:
- Run unit tests: python -m atlas.scripts.testing.run_tests unit
- Run mock tests: python -m atlas.scripts.testing.run_tests mock
- Run integration tests: python -m atlas.scripts.testing.run_tests integration
- Run API tests: python -m atlas.scripts.testing.run_tests api --confirm
- Run specific provider API tests: python -m atlas.scripts.testing.run_tests api --provider openai --confirm
- Run multiple test types: python -m atlas.scripts.testing.run_tests unit mock integration
- Run all tests: python -m atlas.scripts.testing.run_tests all
"""

import os
import sys
import glob
import argparse
import unittest
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any


def discover_tests(directory: str, pattern: str = "test_*.py") -> List[str]:
    """Discover test files in a directory.
    
    Args:
        directory: Directory to search in.
        pattern: Pattern to match test files.
        
    Returns:
        List of discovered test file paths.
    """
    base_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "../../../atlas/tests"
    ))
    search_path = os.path.join(base_path, directory)
    
    # Check if the directory exists
    if not os.path.exists(search_path):
        return []
    
    # Find all test files matching the pattern
    return glob.glob(os.path.join(search_path, pattern))


def load_tests_from_file(file_path: str) -> unittest.TestSuite:
    """Load tests from a file into a test suite.
    
    Args:
        file_path: Path to the test file.
        
    Returns:
        Test suite containing the tests from the file.
    """
    # Convert file path to module path
    rel_path = os.path.relpath(
        file_path, 
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    )
    
    # Remove file extension and convert to module path
    module_path = rel_path.replace("/", ".").replace("\\", ".").replace(".py", "")
    
    # Load the module
    try:
        test_module = importlib.import_module(module_path)
        
        # Create test suite
        loader = unittest.TestLoader()
        return loader.loadTestsFromModule(test_module)
    except ImportError as e:
        print(f"Error importing {module_path}: {e}")
        return unittest.TestSuite()


def discover_and_load_tests(test_type: str, module: Optional[str] = None, 
                          provider: Optional[str] = None) -> unittest.TestSuite:
    """Discover and load tests of a specific type.
    
    Args:
        test_type: Type of tests to load ('unit', 'mock', 'integration', 'api').
        module: Optional module to filter tests by.
        provider: Optional provider to filter API tests by.
        
    Returns:
        Test suite containing the discovered tests.
    """
    suite = unittest.TestSuite()
    
    # Define directory based on test type
    if test_type == "unit":
        directory = "unit"
        if module:
            directory = f"unit/{module}"
    elif test_type == "mock":
        directory = "mock"
        if module:
            directory = f"mock/{module}"
    elif test_type == "integration":
        directory = "integration"
        if module:
            directory = f"integration/{module}"
    elif test_type == "api":
        directory = "api"
        if provider:
            directory = f"api/{provider}"
    else:
        print(f"Unknown test type: {test_type}")
        return suite
    
    # Check if we have tests in the new directory structure
    test_files = discover_tests(directory)
    
    # If no tests found in new structure, try the old structure
    if not test_files:
        print(f"No tests found in {directory}, trying legacy test files...")
        
        # For backwards compatibility
        if test_type == "unit":
            test_files = discover_tests("", "test_*.py")
            test_files = [f for f in test_files if not any(
                f.endswith(x) for x in [
                    "test_mock.py", "test_api.py", "test_minimal.py", 
                    "real_api_tests.py"
                ]
            )]
        elif test_type == "mock":
            test_files = discover_tests("", "test_mock.py")
        elif test_type == "integration":
            test_files = discover_tests("integration")
        elif test_type == "api":
            if provider == "openai":
                test_files = discover_tests("", "test_openai_provider.py")
            elif provider == "ollama":
                test_files = discover_tests("", "test_ollama_provider.py")
            elif provider == "anthropic":
                test_files = discover_tests("", "test_*anthropic*.py")
            else:
                test_files = discover_tests("", "real_api_tests.py")
    
    # Load tests from each file
    for file_path in test_files:
        file_suite = load_tests_from_file(file_path)
        suite.addTest(file_suite)
        print(f"Loaded tests from {os.path.basename(file_path)}")
    
    return suite


def run_tests(suite: unittest.TestSuite, test_type: str) -> Tuple[bool, Dict[str, int]]:
    """Run tests in a test suite.
    
    Args:
        suite: Test suite to run.
        test_type: Type of tests being run (for logging).
        
    Returns:
        Tuple of (success, stats) where success is True if all tests passed,
        and stats is a dictionary with test counts.
    """
    print(f"\n=== Running {test_type.upper()} Tests ===")
    
    # Special warnings for API tests
    if test_type == "api":
        print("NOTE: These tests make real API calls and may incur costs.")
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Collect stats
    stats = {
        "total": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "passed": result.testsRun - len(result.failures) - len(result.errors),
    }
    
    # Print summary
    print(f"\n=== {stats['passed']}/{stats['total']} {test_type} tests passed! ===")
    if stats['skipped'] > 0:
        print(f"Note: {stats['skipped']} tests were skipped.")
    
    return result.wasSuccessful(), stats


def set_test_environment(args: argparse.Namespace) -> None:
    """Set environment variables based on CLI arguments.
    
    Args:
        args: Parsed command-line arguments.
    """
    # Clear existing test environment variables
    for var in [
        "RUN_API_TESTS", "RUN_EXPENSIVE_TESTS", "RUN_INTEGRATION_TESTS",
        "RUN_OPENAI_TESTS", "RUN_ANTHROPIC_TESTS", "RUN_OLLAMA_TESTS",
        "ENFORCE_COST_LIMIT", "MAX_TEST_COST"
    ]:
        if var in os.environ:
            del os.environ[var]
    
    # Set new environment variables based on args
    if "api" in args.test_types:
        os.environ["RUN_API_TESTS"] = "true"
        
        # Provider-specific flags
        if args.provider:
            if "openai" in args.provider:
                os.environ["RUN_OPENAI_TESTS"] = "true"
            if "anthropic" in args.provider:
                os.environ["RUN_ANTHROPIC_TESTS"] = "true"
            if "ollama" in args.provider:
                os.environ["RUN_OLLAMA_TESTS"] = "true"
        else:
            # If no provider specified, enable all
            os.environ["RUN_OPENAI_TESTS"] = "true"
            os.environ["RUN_ANTHROPIC_TESTS"] = "true"
            os.environ["RUN_OLLAMA_TESTS"] = "true"
    
    if "integration" in args.test_types:
        os.environ["RUN_INTEGRATION_TESTS"] = "true"
    
    if args.expensive:
        os.environ["RUN_EXPENSIVE_TESTS"] = "true"
    
    # Cost control
    if args.cost_limit is not None:
        os.environ["MAX_TEST_COST"] = str(args.cost_limit)
        
    if args.enforce_cost_limit:
        os.environ["ENFORCE_COST_LIMIT"] = "true"


def confirm_api_tests(provider: Optional[str] = None, expensive: bool = False) -> bool:
    """Confirm running API tests with the user.
    
    Args:
        provider: Optional provider to filter API tests by.
        expensive: Whether expensive tests will be run.
        
    Returns:
        True if the user confirms, False otherwise.
    """
    provider_str = f" for {provider}" if provider else ""
    expense_str = " including EXPENSIVE tests" if expensive else ""
    
    print(f"\n⚠️  WARNING: You are about to run real API tests{provider_str}{expense_str}.")
    print("These tests will make actual API calls and may incur costs on your account.")
    
    # Check for required API keys
    if not provider or "openai" in provider:
        if not os.environ.get("OPENAI_API_KEY"):
            print("⚠️  OPENAI_API_KEY environment variable is not set.")
    
    if not provider or "anthropic" in provider:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("⚠️  ANTHROPIC_API_KEY environment variable is not set.")
    
    if not provider or "ollama" in provider:
        try:
            import requests
            try:
                response = requests.get("http://localhost:11434/api/version", timeout=1)
                if response.status_code != 200:
                    print("⚠️  Ollama server doesn't appear to be running at http://localhost:11434")
            except requests.RequestException:
                print("⚠️  Could not connect to Ollama server at http://localhost:11434")
        except ImportError:
            print("⚠️  'requests' package not installed, can't check Ollama server")
    
    try:
        response = input("\nDo you want to continue? (yes/no): ").strip().lower()
        return response in ("yes", "y")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return False


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Run Atlas tests with explicit CLI flags",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n")[2]  # Use usage examples from docstring
    )
    
    # Test types (positional)
    parser.add_argument(
        "test_types",
        nargs="+",
        choices=["unit", "mock", "integration", "api", "all"],
        help="Types of tests to run"
    )
    
    # Filter options
    parser.add_argument(
        "-m", "--module",
        type=str,
        help="Module to filter tests by (e.g., 'core', 'models')"
    )
    
    parser.add_argument(
        "-p", "--provider",
        choices=["openai", "anthropic", "ollama"],
        help="Provider to filter API tests by"
    )
    
    # API test options
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip confirmation prompt for API tests"
    )
    
    parser.add_argument(
        "--expensive",
        action="store_true",
        help="Run expensive API tests (GPT-4, Claude Opus, etc.)"
    )
    
    # Cost control
    parser.add_argument(
        "--cost-limit",
        type=float,
        help="Maximum cost limit for API tests (default: 0.1)"
    )
    
    parser.add_argument(
        "--enforce-cost-limit",
        action="store_true",
        help="Enforce cost limit by failing tests that exceed it"
    )
    
    return parser.parse_args()


def main() -> None:
    """Main entry point for running tests."""
    args = parse_args()
    
    # Handle 'all' test type
    if "all" in args.test_types:
        args.test_types = ["unit", "mock", "integration", "api"]
    
    # Confirm API tests if requested
    if "api" in args.test_types and not args.confirm:
        if not confirm_api_tests(args.provider, args.expensive):
            print("API tests cancelled.")
            if len(args.test_types) == 1:  # Only API tests were requested
                sys.exit(0)
            else:
                # Remove API tests and continue with others
                args.test_types.remove("api")
    
    # Set environment variables based on CLI flags
    set_test_environment(args)
    
    # Track results
    all_success = True
    total_stats = {
        "total": 0,
        "passed": 0,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
    }
    
    # Run each test type
    for test_type in args.test_types:
        # Skip API tests if they were cancelled
        if test_type == "api" and "api" not in args.test_types:
            continue
        
        # Discover and load tests
        suite = discover_and_load_tests(test_type, args.module, args.provider)
        
        # Skip if no tests were found
        if suite.countTestCases() == 0:
            print(f"\n=== No {test_type} tests found ===")
            continue
        
        # Run the tests
        success, stats = run_tests(suite, test_type)
        all_success = all_success and success
        
        # Update total stats
        for key in total_stats:
            total_stats[key] += stats.get(key, 0)
        
        print("\n")  # Add spacing between test types
    
    # Print overall summary
    print("=== Overall Test Results ===")
    print(f"Total Tests: {total_stats['total']}")
    print(f"Passed: {total_stats['passed']}")
    print(f"Failed: {total_stats['failures']}")
    print(f"Errors: {total_stats['errors']}")
    print(f"Skipped: {total_stats['skipped']}")
    print(f"Success Rate: {total_stats['passed'] / total_stats['total']:.2%}")
    
    # Return appropriate exit code
    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()