"""
Test error handling patterns for model providers.

This module tests the standardized error handling patterns and error
classes from the atlas.core.errors module.
"""

import unittest
from unittest import mock
from typing import Dict, Any, List, Optional, Type, Callable

# Import decorators
from atlas.tests.helpers import unit_test

# Import error classes
from atlas.core.errors import (
    APIError,
    AuthenticationError,
    ValidationError,
    ErrorSeverity,
    AtlasError,
    safe_execute,
)

# Import models for testing provider error handling
from atlas.models import (
    ModelProvider,
    ModelRequest,
    ModelMessage,
)


class TestErrorClasses(unittest.TestCase):
    """Test the error hierarchy and behaviors."""
    
    @unit_test
    def test_api_error_creation(self):
        """Test creating APIError instances."""
        # Create a basic error
        error = APIError(message="Test error")
        
        # Check basic properties
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.severity, ErrorSeverity.ERROR)  # Default severity
        self.assertFalse(error.details.get("retry_possible", False))
        
        # Create with custom properties
        error = APIError(
            message="Test error",
            cause=ValueError("Original error"),
            severity=ErrorSeverity.WARNING,
            retry_possible=True,
            details={"key": "value"},
        )
        
        # Check custom properties
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.severity, ErrorSeverity.WARNING)
        self.assertTrue(error.details.get("retry_possible", False))
        self.assertEqual(error.details.get("key"), "value")
        self.assertIsInstance(error.cause, ValueError)
        
    @unit_test
    def test_authentication_error(self):
        """Test AuthenticationError behavior."""
        # Create an authentication error
        error = AuthenticationError(
            message="Authentication failed",
            provider="test",
            severity=ErrorSeverity.ERROR,
        )
        
        # Check properties
        self.assertEqual(error.message, "Authentication failed")
        self.assertEqual(error.details.get("provider"), "test")
        self.assertEqual(error.severity, ErrorSeverity.ERROR)
        
        # Check inheritance
        self.assertIsInstance(error, AtlasError)
        
    @unit_test
    def test_validation_error(self):
        """Test ValidationError behavior."""
        # Create a validation error
        error = ValidationError(
            message="Validation failed",
            severity=ErrorSeverity.WARNING,
        )
        
        # Check properties
        self.assertEqual(error.message, "Validation failed")
        self.assertEqual(error.severity, ErrorSeverity.WARNING)
        
        # Check inheritance
        self.assertIsInstance(error, AtlasError)
        
    @unit_test
    def test_error_logging(self):
        """Test error logging functionality."""
        # Create an error
        error = APIError(message="Test error for logging")
        
        # Call the log method - it shouldn't raise exceptions
        try:
            error.log()
        except Exception as e:
            self.fail(f"Error logging should not raise exceptions: {e}")
            
        # Test with a cause
        error = APIError(
            message="Test error with cause",
            cause=ValueError("Original error")
        )
        
        try:
            error.log()
        except Exception as e:
            self.fail(f"Error logging with cause should not raise exceptions: {e}")


class TestSafeExecuteWrapper(unittest.TestCase):
    """Test the safe_execute wrapper function."""

    @unit_test
    def test_successful_execution(self):
        """Test safe_execute with successful execution."""
        def test_func():
            return "success"

        result = safe_execute(
            test_func,
            default="default",
            error_msg="Error message",
            error_cls=APIError,
        )
        
        self.assertEqual(result, "success")

    @unit_test
    def test_exception_handling(self):
        """Test safe_execute with exception handling."""
        def test_func():
            raise ValueError("Test error")

        # Test with default error handler
        with self.assertRaises(APIError) as context:
            safe_execute(
                test_func,
                default=None,
                error_msg="Test failed",
                error_cls=APIError,
            )
        
        self.assertIn("test failed", str(context.exception).lower())
        
        # Verify the cause is properly set
        self.assertIsInstance(context.exception.cause, ValueError)
        self.assertEqual(str(context.exception.cause), "Test error")
        
    @unit_test
    def test_default_return(self):
        """Test safe_execute with default return value."""
        def test_func():
            raise ValueError("Test error")

        # With log_error=False
        result = safe_execute(
            test_func,
            default="default_value",
            error_msg="Test failed",
            error_cls=APIError,
            log_error=False,
        )
        
        self.assertEqual(result, "default_value")
        
        # With log_error=True
        result = safe_execute(
            test_func,
            default="default_value",
            error_msg="Test failed",
            error_cls=APIError,
            log_error=True,
        )
        
        self.assertEqual(result, "default_value")

    @unit_test
    def test_custom_error_class(self):
        """Test safe_execute with custom error class."""
        def test_func():
            raise ValueError("Test error")

        # Test with AuthenticationError
        with self.assertRaises(AuthenticationError) as context:
            safe_execute(
                test_func,
                default=None,
                error_msg="Authentication failed",
                error_cls=AuthenticationError,
                provider="test_provider"
            )
        
        self.assertIn("authentication failed", str(context.exception).lower())
        self.assertEqual(context.exception.details.get("provider"), "test_provider")
        
        # Test with ValidationError
        with self.assertRaises(ValidationError) as context:
            safe_execute(
                test_func,
                default=None,
                error_msg="Validation failed",
                error_cls=ValidationError,
            )
        
        self.assertIn("validation failed", str(context.exception).lower())


class TestErrorHandlingIntegration(unittest.TestCase):
    """Test how errors integrate with provider functions."""
    
    @unit_test
    def test_error_conversion(self):
        """Test converting various errors to standardized Atlas errors."""
        # Test converting a generic exception
        try:
            raise ValueError("Test value error")
        except Exception as e:
            api_error = APIError.from_exception(e, "Operation failed")
        
        self.assertIsInstance(api_error, APIError)
        self.assertEqual(api_error.message, "Operation failed")
        self.assertIsInstance(api_error.cause, ValueError)
        
        # Test converting a more specific error
        try:
            raise ConnectionError("Connection failed")
        except Exception as e:
            api_error = APIError.from_exception(
                e, 
                "API call failed",
                details={"provider": "test", "retryable": True}
            )
        
        self.assertIsInstance(api_error, APIError)
        self.assertEqual(api_error.message, "API call failed")
        self.assertEqual(api_error.details.get("provider"), "test")
        self.assertEqual(api_error.details.get("retryable"), True)
        self.assertIsInstance(api_error.cause, ConnectionError)
    
    @unit_test
    def test_error_propagation(self):
        """Test that errors are properly propagated through the call stack."""
        # Create a function that might fail
        def risky_operation():
            raise ValueError("Something went wrong")
        
        # Create a function that uses safe_execute
        def safe_operation():
            return safe_execute(
                risky_operation,
                default=None,
                error_msg="Operation failed",
                error_cls=APIError,
                log_error=False,
            )
        
        # Create a function that handles the error
        def handler():
            try:
                return safe_operation()
            except APIError as e:
                # Convert to a different error type
                raise ValidationError(
                    message=f"Validation error due to: {e.message}",
                    cause=e
                )
        
        # Test the propagation
        with self.assertRaises(ValidationError) as context:
            handler()
        
        self.assertIn("validation error", str(context.exception).lower())
        self.assertIn("operation failed", str(context.exception).lower())
        self.assertIsInstance(context.exception.cause, APIError)
        self.assertIsInstance(context.exception.cause.cause, ValueError)


if __name__ == "__main__":
    unittest.main()