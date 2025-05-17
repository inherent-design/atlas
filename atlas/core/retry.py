"""
Retry mechanism with exponential backoff for transient API failures.

This module provides utilities for implementing robust retry logic with
exponential backoff, jitter, and configurable parameters. It's designed
to handle transient failures in API calls to LLM providers.
"""

import logging
import random
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast
from dataclasses import dataclass

from atlas.core.errors import APIError, RateLimitError

logger = logging.getLogger(__name__)

# Type variable for generic function return type
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class RetryPolicy:
    """Policy for retry behavior.
    
    Contains configuration for retry attempts, including delays and backoff factors.
    """
    enabled: bool = True
    max_retries: int = 3
    min_delay: float = 0.5
    max_delay: float = 30.0
    backoff_factor: float = 2.0
    jitter: float = 0.1


@dataclass
class RetryState:
    """State tracking for retry operations.
    
    Tracks the current retry attempt and holds the retry policy.
    """
    attempt: int = 0
    max_retries: int = 3
    retry_policy: Optional[RetryPolicy] = None
    last_error: Optional[Exception] = None
    
    def __post_init__(self):
        if self.retry_policy is None:
            self.retry_policy = RetryPolicy()
        # Ensure self.retry_policy is not None after initialization
        assert self.retry_policy is not None


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0,
        jitter_factor: float = 0.1,
        retryable_errors: Optional[List[Type[Exception]]] = None,
        retryable_status_codes: Optional[List[int]] = None,
    ):
        """
        Initialize retry configuration.

        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before first retry
            backoff_factor: Multiplier for subsequent retry delays
            max_delay: Maximum delay in seconds between retries
            jitter_factor: Random factor to add jitter to delay (0.0 to 1.0)
            retryable_errors: List of exception types that should trigger a retry
            retryable_status_codes: List of HTTP status codes that should trigger a retry
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.jitter_factor = jitter_factor
        self.retryable_errors = retryable_errors or [
            RateLimitError,
            TimeoutError,
            ConnectionError,
        ]
        self.retryable_status_codes = retryable_status_codes or [
            429,  # Too Many Requests
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable
            504,  # Gateway Timeout
        ]


def is_retryable_error(
    error: Exception, config: RetryConfig, retry_count: int
) -> bool:
    """
    Determine if an error should trigger a retry attempt.

    Args:
        error: The exception that was raised
        config: Retry configuration
        retry_count: Current retry attempt count

    Returns:
        True if the error should trigger a retry, False otherwise
    """
    # If we've hit the max retries, don't retry
    if retry_count >= config.max_retries:
        return False

    # Check if the error explicitly indicates it's retryable
    if hasattr(error, "retry_possible") and getattr(error, "retry_possible"):
        return True

    # Check if it's an APIError with a status code we should retry
    if isinstance(error, APIError) and hasattr(error, "details"):
        status_code = error.details.get("status_code")
        if status_code in config.retryable_status_codes:
            return True

    # Check if it's a type of error we should retry
    for error_type in config.retryable_errors:
        if isinstance(error, error_type):
            return True

    return False


def calculate_delay(retry_count: int, config: RetryConfig) -> float:
    """
    Calculate the delay before the next retry with exponential backoff and jitter.

    Args:
        retry_count: Current retry attempt count (starting at 1 for first retry)
        config: Retry configuration

    Returns:
        Delay time in seconds
    """
    # For first retry (retry_count=1), use initial_delay
    # For subsequent retries, apply exponential backoff
    if retry_count <= 1:
        delay = config.initial_delay
    else:
        # We apply the backoff factor to the previous delay
        # retry_count=2 means (initial_delay * backoff_factor^1)
        retry_exp = retry_count - 1
        delay = config.initial_delay * (config.backoff_factor ** retry_exp)

    # Apply maximum delay cap
    delay = min(delay, config.max_delay)

    # Add jitter to prevent thundering herd problem
    # This adds a random component of up to jitter_factor of the delay
    jitter = delay * config.jitter_factor * random.random()
    delay = delay + jitter

    return delay


def calculate_retry_delay(state: RetryState) -> float:
    """
    Calculate the delay for a retry operation based on the retry state and policy.
    
    Args:
        state: Current retry state
        
    Returns:
        Delay time in seconds
    """
    # We know policy is not None because of the __post_init__ assert
    policy = state.retry_policy
    assert policy is not None, "RetryPolicy should not be None after initialization"
    
    if not policy.enabled or state.attempt > state.max_retries:
        return 0
    
    # Calculate base delay with exponential backoff
    if state.attempt <= 1:
        base_delay = policy.min_delay
    else:
        # We apply the backoff factor to calculate the exponential delay
        # attempt=2 means (min_delay * backoff_factor^1)
        backoff_exponent = state.attempt - 1
        base_delay = policy.min_delay * (policy.backoff_factor ** backoff_exponent)
    
    # Apply maximum delay cap
    delay = min(base_delay, policy.max_delay)
    
    # Add jitter to prevent thundering herd problem
    jitter_amount = delay * policy.jitter
    # This adds a random component of up to jitter amount
    delay = delay + (jitter_amount * random.random())
    
    return delay


def with_retry(config: Optional[RetryConfig] = None) -> Callable[[F], F]:
    """
    Decorator to add retry logic to a function.

    Args:
        config: Retry configuration, uses default if None

    Returns:
        Decorated function with retry logic
    """
    retry_config = config or RetryConfig()

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            retry_count = 0
            last_error = None

            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as error:
                    last_error = error
                    if is_retryable_error(error, retry_config, retry_count):
                        retry_count += 1
                        delay = calculate_delay(retry_count, retry_config)

                        error_type = type(error).__name__
                        if hasattr(error, "status_code"):
                            status_info = f" (Status: {getattr(error, 'status_code')})"
                        else:
                            status_info = ""

                        logger.warning(
                            f"Retryable error occurred: {error_type}{status_info}. "
                            f"Retrying in {delay:.2f}s ({retry_count}/{retry_config.max_retries})"
                        )
                        time.sleep(delay)
                    else:
                        # Not retryable or max retries reached, raise the last error
                        logger.debug(
                            f"Not retrying after error: {type(last_error).__name__}. "
                            f"Max retries reached or non-retryable error."
                        )
                        raise

        return cast(F, wrapper)

    return decorator


class CircuitBreakerState:
    """Circuit breaker state tracking."""

    CLOSED = "CLOSED"  # Normal operation, requests pass through
    OPEN = "OPEN"  # Failing state, requests are blocked
    HALF_OPEN = "HALF_OPEN"  # Testing state, limited requests allowed


# Export the states as class constants for easier access
CIRCUIT_CLOSED = CircuitBreakerState.CLOSED
CIRCUIT_OPEN = CircuitBreakerState.OPEN
CIRCUIT_HALF_OPEN = CircuitBreakerState.HALF_OPEN


class CircuitBreaker:
    """
    Circuit breaker implementation to prevent repeated API calls to failing services.
    
    The circuit breaker pattern helps prevent cascading failures by automatically
    stopping requests to a failing service temporarily, giving it time to recover.
    """
    
    # State constants for easier access
    CLOSED = CircuitBreakerState.CLOSED
    OPEN = CircuitBreakerState.OPEN
    HALF_OPEN = CircuitBreakerState.HALF_OPEN

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        test_requests: int = 1,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of consecutive failures that trips the breaker
            recovery_timeout: Time in seconds before attempting recovery
            test_requests: Number of test requests allowed when half-open
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.test_requests = test_requests
        
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.test_requests_remaining = 0
    
    def record_success(self) -> None:
        """Record a successful operation."""
        if self.state == self.HALF_OPEN:
            # If successful in half-open state, reset to closed
            self.state = self.CLOSED
            self.failure_count = 0
            self.test_requests_remaining = 0
        elif self.state == self.CLOSED:
            # In closed state, reset failure count on success
            self.failure_count = 0
    
    def record_failure(self) -> None:
        """Record a failed operation."""
        now = time.time()
        self.last_failure_time = now
        
        if self.state == self.HALF_OPEN:
            # If failed in half-open state, go back to open
            self.state = self.OPEN
            self.test_requests_remaining = 0
        elif self.state == self.CLOSED:
            # In closed state, increment failure count
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                logger.warning(
                    f"Circuit breaker tripped after {self.failure_count} consecutive failures"
                )
                self.state = self.OPEN
    
    def allow_request(self) -> bool:
        """
        Check if a request should be allowed through the circuit breaker.
        
        Returns:
            True if request is allowed, False otherwise
        """
        now = time.time()
        
        if self.state == self.OPEN:
            # Check if recovery timeout has elapsed
            if now - self.last_failure_time >= self.recovery_timeout:
                logger.info("Circuit breaker entering half-open state after recovery timeout")
                self.state = self.HALF_OPEN
                self.test_requests_remaining = self.test_requests
            else:
                return False
        
        if self.state == self.HALF_OPEN:
            # Only allow a limited number of test requests
            if self.test_requests_remaining > 0:
                self.test_requests_remaining -= 1
                return True
            return False
        
        # In closed state, always allow
        return True


def with_circuit_breaker(
    circuit_breaker: CircuitBreaker,
) -> Callable[[F], F]:
    """
    Decorator to add circuit breaker logic to a function.
    
    Args:
        circuit_breaker: CircuitBreaker instance to use
        
    Returns:
        Decorated function with circuit breaker logic
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not circuit_breaker.allow_request():
                from atlas.core.errors import ErrorSeverity
                raise APIError(
                    message="Circuit breaker open, request blocked",
                    severity=ErrorSeverity.WARNING,
                    retry_possible=False,
                )
            
            try:
                result = func(*args, **kwargs)
                circuit_breaker.record_success()
                return result
            except Exception as e:
                circuit_breaker.record_failure()
                raise
                
        return cast(F, wrapper)
    
    return decorator