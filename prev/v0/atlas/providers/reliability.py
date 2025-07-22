"""
Reliability mechanisms for Atlas providers.

This module provides retry logic, circuit breakers, and other reliability
mechanisms to improve robustness when working with LLM providers.
"""

import logging
import random
import threading
import time
from collections.abc import Callable
from typing import Any, TypeVar

from atlas.core.errors import ErrorSeverity
from atlas.core.telemetry import traced
from atlas.providers.errors import (
    ProviderConnectionError,
    ProviderError,
    ProviderRateLimitError,
    ProviderServerError,
    ProviderTimeoutError,
)

logger = logging.getLogger(__name__)

# Type variable for generic function return type
T = TypeVar("T")


class ProviderRetryConfig:
    """Configuration for provider retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0,
        jitter_factor: float = 0.1,
        retryable_errors: list[type[Exception]] | None = None,
        retryable_status_codes: list[int] | None = None,
        retry_on_timeout: bool = True,
        retry_error_severities: list[ErrorSeverity] | None = None,
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
            retry_on_timeout: Whether to retry on timeout errors
            retry_error_severities: List of error severities that should trigger a retry
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.jitter_factor = jitter_factor
        self.retryable_errors = retryable_errors or [
            ProviderRateLimitError,
            ProviderServerError,
            ProviderTimeoutError,
            ProviderConnectionError,
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
        self.retry_on_timeout = retry_on_timeout
        self.retry_error_severities = retry_error_severities or [
            ErrorSeverity.WARNING,
            ErrorSeverity.INFO,
        ]


class ProviderCircuitBreaker:
    """Circuit breaker to prevent repeated API calls to failing services."""

    # State constants
    STATE_CLOSED = "CLOSED"  # Normal operation, requests pass through
    STATE_OPEN = "OPEN"  # Failing state, requests are blocked
    STATE_HALF_OPEN = "HALF_OPEN"  # Testing state, limited requests allowed

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        test_requests: int = 1,
        reset_timeout: float = 300.0,
        error_types: list[type[Exception]] | None = None,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of consecutive failures that trips the breaker
            recovery_timeout: Time in seconds before attempting recovery
            test_requests: Number of test requests allowed when half-open
            reset_timeout: Time in seconds before automatically resetting if no activity
            error_types: List of exception types that count as failures
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.test_requests = test_requests
        self.reset_timeout = reset_timeout

        # Tracked errors (defaults to ProviderError and its subclasses)
        self.error_types = error_types or [ProviderError]

        # State fields
        self._state = self.STATE_CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._last_activity_time = time.time()
        self._test_requests_remaining = 0

        # Thread safety
        self._lock = threading.RLock()

    @property
    def state(self) -> str:
        """Get the current state of the circuit breaker."""
        with self._lock:
            return self._state

    @property
    def failure_count(self) -> int:
        """Get the current failure count."""
        with self._lock:
            return self._failure_count

    @property
    def last_failure_time(self) -> float:
        """Get the timestamp of the last failure."""
        with self._lock:
            return self._last_failure_time

    @property
    def idle_time(self) -> float:
        """Get the time since the last activity in seconds."""
        with self._lock:
            return time.time() - self._last_activity_time

    @traced(name="circuitBreaker_record_success")
    def record_success(self) -> None:
        """Record a successful operation."""
        with self._lock:
            self._last_activity_time = time.time()

            if self._state == self.STATE_HALF_OPEN:
                # If successful in half-open state, reset to closed
                self._state = self.STATE_CLOSED
                self._failure_count = 0
                self._test_requests_remaining = 0
                logger.info("Circuit breaker reset to closed state after successful test request")
            elif self._state == self.STATE_CLOSED:
                # In closed state, reset failure count on success
                self._failure_count = 0

    @traced(name="circuitBreaker_record_failure")
    def record_failure(self, error: Exception | None = None) -> None:
        """
        Record a failed operation.

        Args:
            error: The exception that caused the failure, if any.
        """
        with self._lock:
            now = time.time()
            self._last_activity_time = now
            self._last_failure_time = now

            # Check if this error type counts as a failure
            if error and not self._is_tracked_error(error):
                return

            if self._state == self.STATE_HALF_OPEN:
                # If failed in half-open state, go back to open
                self._state = self.STATE_OPEN
                self._test_requests_remaining = 0
                logger.warning("Circuit breaker returning to open state after test request failure")
            elif self._state == self.STATE_CLOSED:
                # In closed state, increment failure count
                self._failure_count += 1

                if self._failure_count >= self.failure_threshold:
                    logger.warning(
                        f"Circuit breaker tripped after {self._failure_count} consecutive failures"
                    )
                    self._state = self.STATE_OPEN

    @traced(name="circuitBreaker_allow_request")
    def allow_request(self) -> bool:
        """
        Check if a request should be allowed through the circuit breaker.

        Returns:
            True if request is allowed, False otherwise
        """
        with self._lock:
            now = time.time()
            self._last_activity_time = now

            # Check for auto-reset if idle for too long
            if (
                self._state != self.STATE_CLOSED
                and (now - self._last_activity_time) > self.reset_timeout
            ):
                logger.info(f"Circuit breaker auto-reset after {self.reset_timeout}s of inactivity")
                self._state = self.STATE_CLOSED
                self._failure_count = 0
                return True

            if self._state == self.STATE_OPEN:
                # Check if recovery timeout has elapsed
                if now - self._last_failure_time >= self.recovery_timeout:
                    logger.info("Circuit breaker entering half-open state after recovery timeout")
                    self._state = self.STATE_HALF_OPEN
                    self._test_requests_remaining = self.test_requests
                else:
                    logger.debug(
                        f"Circuit breaker blocking request in open state (recovery in {self.recovery_timeout - (now - self._last_failure_time):.1f}s)"
                    )
                    return False

            if self._state == self.STATE_HALF_OPEN:
                # Only allow a limited number of test requests
                if self._test_requests_remaining > 0:
                    self._test_requests_remaining -= 1
                    logger.debug(
                        f"Circuit breaker allowing test request ({self._test_requests_remaining} remaining)"
                    )
                    return True
                logger.debug(
                    "Circuit breaker blocking request in half-open state (no test requests remaining)"
                )
                return False

            # In closed state, always allow
            return True

    def _is_tracked_error(self, error: Exception) -> bool:
        """
        Check if an error is one that should be tracked by the circuit breaker.

        Args:
            error: The exception to check

        Returns:
            True if the error should be tracked, False otherwise
        """
        return any(isinstance(error, err_type) for err_type in self.error_types)

    def reset(self) -> None:
        """
        Reset the circuit breaker to closed state.

        This can be useful for manually resetting after configuration changes
        or for testing.
        """
        with self._lock:
            self._state = self.STATE_CLOSED
            self._failure_count = 0
            self._test_requests_remaining = 0
            self._last_activity_time = time.time()
            logger.info("Circuit breaker manually reset to closed state")


class ProviderReliabilityManager:
    """
    Manager for provider reliability mechanisms.

    This class combines retry configuration and circuit breaker into a single
    utility that can be used to improve the reliability of provider operations.
    """

    def __init__(
        self,
        retry_config: ProviderRetryConfig | None = None,
        circuit_breaker: ProviderCircuitBreaker | None = None,
    ):
        """
        Initialize the reliability manager.

        Args:
            retry_config: Custom retry configuration, or None to use the default
            circuit_breaker: Custom circuit breaker, or None to use the default
        """
        self.retry_config = retry_config or ProviderRetryConfig()
        self.circuit_breaker = circuit_breaker or ProviderCircuitBreaker()

    @traced(name="reliabilityManager_execute")
    def execute_with_reliability(
        self,
        func: Callable[..., T],
        *args: Any,
        error_handler: Callable[[Exception], Exception | None] | None = None,
        provider_name: str = "unknown",
        default_value: T | None = None,
        **kwargs: Any,
    ) -> T:
        """
        Execute a function with retry logic and circuit breaker protection.

        This utility wraps function execution with:
        1. Circuit breaker protection to prevent overloading failing services
        2. Exponential backoff retry for transient errors
        3. Consistent error handling and logging

        Args:
            func: The function to execute
            *args: Arguments to pass to the function
            error_handler: Optional function to process errors before retrying
            provider_name: Name of the provider for error reporting
            default_value: Value to return if all retries fail and no error is raised
            **kwargs: Keyword arguments to pass to the function

        Returns:
            The result of the function call

        Raises:
            Exception: If the function call fails after all retries and no default_value
                      is provided
        """
        # First check the circuit breaker
        if not self.circuit_breaker.allow_request():
            logger.warning(f"{provider_name} provider circuit breaker is open, request blocked")
            if default_value is not None:
                return default_value
            raise ProviderError(
                message=f"{provider_name} provider circuit breaker is open, request blocked",
                severity=ErrorSeverity.WARNING,
                retry_possible=False,
                provider=provider_name,
            )

        retry_count = 0
        max_retries = self.retry_config.max_retries
        last_error: Exception | None = None

        while True:
            try:
                # Execute the function
                result = func(*args, **kwargs)
                # Record successful execution in circuit breaker
                self.circuit_breaker.record_success()
                return result

            except Exception as error:
                last_error = error

                # Allow custom error handling/transformation before retry logic
                if error_handler:
                    try:
                        transformed_error = error_handler(error)
                        if transformed_error:
                            last_error = transformed_error
                    except Exception as handler_error:
                        logger.warning(f"Error in custom error handler: {handler_error}")

                # Record failure in circuit breaker regardless of whether we'll retry
                self.circuit_breaker.record_failure(last_error)

                # Check if we should retry
                if retry_count < max_retries and self._should_retry(last_error):
                    retry_count += 1
                    delay = self._calculate_retry_delay(retry_count)

                    logger.warning(
                        f"Retryable error from {provider_name} provider: {type(last_error).__name__}. "
                        f"Retrying in {delay:.2f}s ({retry_count}/{max_retries})"
                    )
                    time.sleep(delay)
                    continue

                # If we have a default value, return it instead of raising the error
                if default_value is not None:
                    logger.error(
                        f"Error from {provider_name} provider after {retry_count} retries: {last_error}. "
                        f"Returning default value."
                    )
                    return default_value

                # Otherwise, raise the last error
                raise last_error

    def _should_retry(self, error: Exception) -> bool:
        """
        Determine if an error should trigger a retry attempt.

        Args:
            error: The exception that was raised

        Returns:
            True if the error should trigger a retry, False otherwise
        """
        # Check if the error explicitly indicates it's retryable
        if hasattr(error, "retry_possible") and error.retry_possible:
            return True

        # Check retry based on error severity for provider errors
        if hasattr(error, "severity") and self.retry_config.retry_error_severities:
            severity = error.severity
            if severity in self.retry_config.retry_error_severities:
                return True

        # Check if it's a ProviderError with a status code we should retry
        if isinstance(error, ProviderError) and hasattr(error, "details"):
            status_code = error.details.get("status_code")
            if status_code and status_code in self.retry_config.retryable_status_codes:
                return True

        # Check for timeout errors if configured to retry them
        if self.retry_config.retry_on_timeout and isinstance(
            error, (ProviderTimeoutError, TimeoutError)
        ):
            return True

        # Check if it's a type of error we should retry
        for error_type in self.retry_config.retryable_errors:
            if isinstance(error, error_type):
                return True

        return False

    def _calculate_retry_delay(self, retry_count: int) -> float:
        """
        Calculate the delay before the next retry with exponential backoff and jitter.

        Args:
            retry_count: Current retry attempt count (starting at 1 for first retry)

        Returns:
            Delay time in seconds
        """
        # For first retry (retry_count=1), use initial_delay
        # For subsequent retries, apply exponential backoff
        if retry_count <= 1:
            delay = self.retry_config.initial_delay
        else:
            # Apply the backoff factor to the previous delay
            retry_exp = retry_count - 1
            delay = self.retry_config.initial_delay * (self.retry_config.backoff_factor**retry_exp)

        # Apply maximum delay cap
        delay = min(delay, self.retry_config.max_delay)

        # Add jitter to prevent thundering herd problem
        jitter = delay * self.retry_config.jitter_factor * random.random()
        delay = delay + jitter

        return delay
