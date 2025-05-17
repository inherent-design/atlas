#!/usr/bin/env python3
"""
Run all schema validation tests.

This script runs all schema validation tests in the Atlas project and
provides a summary of the results. It's a convenient way to verify that
the schema validation system is working correctly.
"""

import unittest
import time
import sys
from typing import List, Tuple


def run_schema_tests() -> Tuple[int, int, List[str]]:
    """
    Run all schema validation tests and return results.
    
    Returns:
        Tuple containing (passed_tests, total_tests, failed_test_names)
    """
    # Create test suite for all schema tests
    test_suite = unittest.TestLoader().discover(
        start_dir="atlas/tests",
        pattern="test_schema_*.py"
    )
    
    # Create a test result object to collect results
    test_result = unittest.TestResult()
    
    # Run the tests
    test_suite.run(test_result)
    
    # Collect failed test names
    failed_tests = []
    for test, error in test_result.errors:
        failed_tests.append(f"{test.id()} - Error: {error}")
    for test, failure in test_result.failures:
        failed_tests.append(f"{test.id()} - Failure: {failure}")
    
    # Return pass count, total count, and failed test names
    return (
        test_result.testsRun - len(test_result.errors) - len(test_result.failures),
        test_result.testsRun,
        failed_tests
    )


def main() -> int:
    """
    Run schema tests and print results.
    
    Returns:
        Exit code (0 for success, 1 for failures)
    """
    print("Running Atlas Schema Validation Tests...")
    print("=======================================")
    
    start_time = time.time()
    passed, total, failed_tests = run_schema_tests()
    end_time = time.time()
    
    # Print results
    print(f"\nResults: {passed}/{total} tests passed")
    print(f"Time taken: {end_time - start_time:.2f} seconds")
    
    # Print failed tests if any
    if failed_tests:
        print("\nFailed tests:")
        for test in failed_tests:
            print(f"- {test}")
        return 1
    else:
        print("\nAll tests passed successfully!")
        return 0


if __name__ == "__main__":
    sys.exit(main())