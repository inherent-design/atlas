"""
Error handling for Atlas.

This module provides standardized error handling across Atlas components.
"""

import traceback
import logging
from typing import Dict, Any, Optional, Type, List, Callable, TypeVar
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ErrorSeverity(str, Enum):
    """Severity levels for errors."""

    # Informational, not impacting operation
    INFO = "info"

    # Minor issue that can be worked around
    WARNING = "warning"

    # Issue that prevents operation but might be recoverable
    ERROR = "error"

    # Critical issue that cannot be recovered from
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Categories of errors across the application."""

    # Environmental issues (file access, network, etc.)
    ENVIRONMENT = "environment"

    # Configuration problems
    CONFIGURATION = "configuration"

    # Input validation errors
    VALIDATION = "validation"

    # API/external service errors
    API = "api"

    # Authentication/authorization errors
    AUTH = "auth"

    # Data processing errors
    DATA = "data"

    # Core algorithm/logic errors
    LOGIC = "logic"

    # Resource constraints (memory, CPU, etc.)
    RESOURCE = "resource"

    # Unknown/uncategorized errors
    UNKNOWN = "unknown"


class AtlasError(Exception):
    """Base class for all Atlas exceptions."""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            severity: Severity level of the error.
            category: Category of the error.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
        """
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.category = category
        self.details = details or {}
        self.cause = cause

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary.

        Returns:
            Dictionary representation of the error.
        """
        result = {
            "message": self.message,
            "severity": self.severity,
            "category": self.category,
            "type": type(self).__name__,
        }

        if self.details:
            # Convert details dict to result
            for key, value in self.details.items():
                result[key] = value

        if self.cause:
            result["cause"] = str(self.cause)

        return result

    def log(self, log_level: Optional[int] = None):
        """Log the error with appropriate level.

        Args:
            log_level: Optional override for log level.
        """
        if log_level is None:
            # Map severity to log level
            if self.severity == ErrorSeverity.INFO:
                log_level = logging.INFO
            elif self.severity == ErrorSeverity.WARNING:
                log_level = logging.WARNING
            elif self.severity == ErrorSeverity.ERROR:
                log_level = logging.ERROR
            else:  # CRITICAL
                log_level = logging.CRITICAL

        # Create log message
        log_msg = f"{type(self).__name__}: {self.message}"

        # Include traceback for ERROR and CRITICAL
        if log_level >= logging.ERROR and self.cause:
            logger.log(log_level, log_msg, exc_info=self.cause)
        else:
            logger.log(log_level, log_msg)


# Specific error types


class ConfigurationError(AtlasError):
    """Error related to configuration issues."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
        """
        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.CONFIGURATION,
            details=details,
            cause=cause,
        )


class APIError(AtlasError):
    """Error related to API calls."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        retry_possible: bool = False,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            retry_possible: Whether the operation can be retried.
        """
        details = details or {}
        details["retry_possible"] = retry_possible

        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.API,
            details=details,
            cause=cause,
        )
        
    @classmethod
    def from_exception(
        cls,
        exception: Exception,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        retry_possible: bool = False,
    ) -> 'APIError':
        """Create an APIError from an existing exception.
        
        Args:
            exception: The exception to convert.
            message: The error message.
            details: Optional detailed information about the error.
            severity: Severity level of the error.
            retry_possible: Whether the operation can be retried.
            
        Returns:
            A new APIError instance.
        """
        return cls(
            message=message,
            details=details,
            cause=exception,
            severity=severity,
            retry_possible=retry_possible,
        )


class ValidationError(AtlasError):
    """Error related to input validation."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        severity: ErrorSeverity = ErrorSeverity.WARNING,
        field_errors: Optional[Dict[str, List[str]]] = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            field_errors: Mapping of field names to error messages.
        """
        details = details or {}
        if field_errors:
            details["field_errors"] = field_errors

        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.VALIDATION,
            details=details,
            cause=cause,
        )


class AuthenticationError(AtlasError):
    """Error related to authentication."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        provider: Optional[str] = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            provider: The authentication provider that caused the error.
        """
        details = details or {}
        if provider:
            details["provider"] = provider

        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.AUTH,
            details=details,
            cause=cause,
        )


class ResourceError(AtlasError):
    """Error related to resource constraints."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        resource_type: Optional[str] = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            resource_type: The type of resource that caused the error.
        """
        details = details or {}
        if resource_type:
            details["resource_type"] = resource_type

        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.RESOURCE,
            details=details,
            cause=cause,
        )


class RateLimitError(APIError):
    """Error related to rate limiting in API calls."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        severity: ErrorSeverity = ErrorSeverity.WARNING,
        provider: Optional[str] = None,
        retry_after: Optional[float] = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            provider: The provider that imposed the rate limit.
            retry_after: Suggested time to wait before retrying (seconds).
        """
        details = details or {}
        if provider:
            details["provider"] = provider
        if retry_after is not None:
            details["retry_after"] = retry_after

        super().__init__(
            message=message,
            severity=severity,
            details=details,
            cause=cause,
            retry_possible=True,  # Rate limit errors are always retryable
        )


# Error handling utilities


def safe_execute(
    func: Callable[..., T],
    default: Optional[T] = None,
    error_handler: Optional[Callable[[Exception], Optional[T]]] = None,
    log_error: bool = True,
    error_cls: Type[AtlasError] = AtlasError,
    error_msg: str = "Error executing function",
    *args: Any,
    **kwargs: Any,
) -> T:
    """Execute a function safely, handling exceptions.

    Args:
        func: The function to execute.
        default: Default value to return if function fails.
        error_handler: Optional function to handle the exception.
        log_error: Whether to log the error.
        error_cls: The error class to use when creating an error.
        error_msg: The error message to use.
        *args: Arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        The result of the function or the default value if an exception occurs.
    """
    # Extract error constructor kwargs from kwargs (any keys that don't match function parameters)
    import inspect
    
    func_signature = inspect.signature(func)
    func_params = set(func_signature.parameters.keys())
    
    # Separate kwargs into function kwargs and error kwargs
    error_kwargs = {}
    function_kwargs = {}
    
    for key, value in kwargs.items():
        if key in func_params:
            function_kwargs[key] = value
        else:
            error_kwargs[key] = value
    
    try:
        return func(*args, **function_kwargs)
    except Exception as e:
        # Create and log the error
        error = error_cls(message=error_msg, cause=e, **error_kwargs)

        if log_error:
            error.log()

        # Call error handler if provided
        if error_handler:
            try:
                handler_result = error_handler(e)
                if handler_result is not None:
                    return handler_result
            except Exception as handler_error:
                logger.error(f"Error in error handler: {str(handler_error)}")

        # Return default value
        if default is None:
            raise error  # Re-raise the error if no default is provided
        return default


def get_error_message(exception: Exception, include_traceback: bool = False) -> str:
    """Get a formatted error message from an exception.

    Args:
        exception: The exception to format.
        include_traceback: Whether to include the traceback.

    Returns:
        Formatted error message.
    """
    if isinstance(exception, AtlasError):
        base_msg = exception.message
    else:
        base_msg = str(exception)

    if include_traceback:
        tb = traceback.format_exception(
            type(exception), exception, exception.__traceback__
        )
        return f"{base_msg}\n\n{''.join(tb)}"

    return base_msg


def convert_exception(
    exception: Exception,
    error_cls: Type[AtlasError] = AtlasError,
    message: Optional[str] = None,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    details: Optional[Dict[str, Any]] = None,
) -> AtlasError:
    """Convert a standard exception to an AtlasError.

    Args:
        exception: The exception to convert.
        error_cls: AtlasError subclass to use.
        message: Optional message to use (falls back to str(exception)).
        severity: Severity level of the error.
        category: Category of the error.
        details: Optional detailed information about the error.

    Returns:
        AtlasError instance.
    """
    if isinstance(exception, error_cls):
        return exception

    msg = message if message is not None else str(exception)
    return error_cls(
        message=msg,
        severity=severity,
        category=category,
        details=details,
        cause=exception,
    )
