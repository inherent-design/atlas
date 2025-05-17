"""
Error handling for Atlas providers.

This module defines provider-specific error classes and categorization
to enable consistent error handling across different providers.
"""

from typing import Dict, List, Any, Optional
from atlas.core.errors import APIError, AuthenticationError, ValidationError, ErrorSeverity


class ProviderError(APIError):
    """Base class for provider-specific errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        provider: Optional[str] = None,
        retry_possible: bool = False,
    ):
        """Initialize the error.
        
        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            provider: The provider that caused the error.
            retry_possible: Whether the operation can be retried.
        """
        details = details or {}
        if provider:
            details["provider"] = provider
            
        super().__init__(
            message=message,
            severity=severity,
            details=details,
            cause=cause,
            retry_possible=retry_possible,
        )


class ProviderAuthenticationError(AuthenticationError, ProviderError):
    """Error related to provider authentication."""
    
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
            provider: The provider that caused the error.
        """
        details = details or {}
        if provider:
            details["provider"] = provider
            
        super().__init__(
            message=message,
            cause=cause,
            severity=severity,
            provider=provider,
            details=details
        )


class ProviderRateLimitError(ProviderError):
    """Error related to provider rate limiting."""
    
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
            provider: The provider that caused the error.
            retry_after: Suggested time to wait before retrying (seconds).
        """
        details = details or {}
        if retry_after is not None:
            details["retry_after"] = retry_after
            
        super().__init__(
            message=message,
            details=details,
            cause=cause,
            severity=severity,
            provider=provider,
            retry_possible=True,  # Rate limit errors are always retryable
        )


class ProviderServerError(ProviderError):
    """Error related to provider server issues."""
    
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
            provider: The provider that caused the error.
        """
        super().__init__(
            message=message,
            details=details,
            cause=cause,
            severity=severity,
            provider=provider,
            retry_possible=True,  # Server errors are typically transient and retryable
        )


class ProviderTimeoutError(ProviderError):
    """Error related to provider timeouts."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        severity: ErrorSeverity = ErrorSeverity.WARNING,
        provider: Optional[str] = None,
    ):
        """Initialize the error.
        
        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            provider: The provider that caused the error.
        """
        super().__init__(
            message=message,
            details=details,
            cause=cause,
            severity=severity,
            provider=provider,
            retry_possible=True,  # Timeout errors are retryable
        )


class ProviderStreamError(ProviderError):
    """Error related to streaming operations."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        provider: Optional[str] = None,
        can_resume: bool = False,
    ):
        """Initialize the error.
        
        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            provider: The provider that caused the error.
            can_resume: Whether the stream can be resumed after this error.
        """
        details = details or {}
        details["can_resume"] = can_resume
        
        super().__init__(
            message=message,
            details=details,
            cause=cause,
            severity=severity,
            provider=provider,
            retry_possible=can_resume,  # Only retryable if can_resume is True
        )


class ProviderValidationError(ValidationError):
    """Error related to provider request validation."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        provider: Optional[str] = None,
        field_errors: Optional[Dict[str, List[str]]] = None,
    ):
        """Initialize the error.
        
        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            provider: The provider that caused the error.
            field_errors: Mapping of field names to error messages.
        """
        details = details or {}
        if provider:
            details["provider"] = provider
            
        super().__init__(
            message=message,
            details=details,
            cause=cause,
            severity=severity,
            field_errors=field_errors,
        )


class ProviderConfigError(ProviderValidationError):
    """Error related to provider configuration validation."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        provider: Optional[str] = None,
        field_errors: Optional[Dict[str, List[str]]] = None,
    ):
        """Initialize the error.
        
        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            provider: The provider that caused the error.
            field_errors: Mapping of field names to error messages.
        """
        super().__init__(
            message=message,
            details=details,
            cause=cause,
            severity=severity,
            provider=provider,
            field_errors=field_errors,
        )


class ProviderConnectionError(ProviderError):
    """Error related to provider connection issues."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        severity: ErrorSeverity = ErrorSeverity.WARNING,
        provider: Optional[str] = None,
    ):
        """Initialize the error.
        
        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            provider: The provider that caused the error.
        """
        super().__init__(
            message=message,
            details=details,
            cause=cause,
            severity=severity,
            provider=provider,
            retry_possible=True,  # Connection errors are usually retryable
        )


class ProviderNetworkError(ProviderError):
    """Error related to provider network issues."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        severity: ErrorSeverity = ErrorSeverity.WARNING,
        provider: Optional[str] = None,
    ):
        """Initialize the error.
        
        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            provider: The provider that caused the error.
        """
        super().__init__(
            message=message,
            details=details,
            cause=cause,
            severity=severity,
            provider=provider,
            retry_possible=True,  # Network errors are usually retryable
        )


class ProviderUnavailableError(ProviderError):
    """Error when a provider is temporarily unavailable."""
    
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
            provider: The provider that caused the error.
        """
        super().__init__(
            message=message,
            details=details,
            cause=cause,
            severity=severity,
            provider=provider,
            retry_possible=True,  # Unavailable errors may be retryable later
        )


class ProviderNotSupportedError(ProviderError):
    """Error for unsupported provider operations."""
    
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
            provider: The provider that caused the error.
        """
        super().__init__(
            message=message,
            details=details,
            cause=cause,
            severity=severity,
            provider=provider,
            retry_possible=False,  # Not supported errors are not retryable
        )


class ProviderQuotaExceededError(ProviderError):
    """Error for exceeded provider quotas."""
    
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
            provider: The provider that caused the error.
        """
        super().__init__(
            message=message,
            details=details,
            cause=cause,
            severity=severity,
            provider=provider,
            retry_possible=False,  # Quota errors are not retryable without intervention
        )


# Error conversion utilities

def convert_provider_error(
    error: Exception,
    provider_name: str,
    retry_possible: bool = False,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
) -> ProviderError:
    """Convert a generic exception to a provider-specific error.
    
    Args:
        error: The original exception.
        provider_name: The name of the provider.
        retry_possible: Whether the operation can be retried.
        severity: The severity level of the error.
        
    Returns:
        A ProviderError instance.
    """
    # Check if it's already a provider error
    if isinstance(error, ProviderError):
        return error
        
    # Create a new provider error with the original as cause
    return ProviderError(
        message=f"Error in provider {provider_name}: {str(error)}",
        cause=error,
        provider=provider_name,
        retry_possible=retry_possible,
        severity=severity,
    )


def categorize_http_error(
    status_code: int,
    error: Exception,
    provider_name: str,
    error_message: Optional[str] = None,
) -> ProviderError:
    """Categorize an HTTP error based on status code.
    
    Args:
        status_code: The HTTP status code.
        error: The original exception.
        provider_name: The name of the provider.
        error_message: Optional custom error message.
        
    Returns:
        A categorized ProviderError instance.
    """
    message = error_message or f"Provider {provider_name} returned HTTP {status_code}"
    details = {"status_code": status_code}
    
    # 4xx errors
    if 400 <= status_code < 500:
        if status_code == 401:
            return ProviderAuthenticationError(
                message=f"Authentication error with provider {provider_name}: {message}",
                cause=error,
                provider=provider_name,
                details=details,
            )
        elif status_code == 403:
            return ProviderAuthenticationError(
                message=f"Authorization error with provider {provider_name}: {message}",
                cause=error,
                provider=provider_name,
                details=details,
            )
        elif status_code == 429:
            return ProviderRateLimitError(
                message=f"Rate limit exceeded with provider {provider_name}: {message}",
                cause=error,
                provider=provider_name,
                details=details,
            )
        else:
            # Other 4xx errors are generally not retryable
            return ProviderError(
                message=message,
                cause=error,
                provider=provider_name,
                retry_possible=False,
                details=details,
            )
    
    # 5xx errors
    elif 500 <= status_code < 600:
        return ProviderServerError(
            message=f"Server error from provider {provider_name}: {message}",
            cause=error,
            provider=provider_name,
            details=details,
        )
    
    # Unknown status codes
    else:
        return ProviderError(
            message=message,
            cause=error,
            provider=provider_name,
            retry_possible=False,
            details=details,
        )