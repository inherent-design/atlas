"""
Stream control interface for Atlas providers.

This module provides interfaces and implementations for controlling streaming
responses, including pause, resume, and cancel operations.
"""

import abc
import enum
import logging
import threading
from collections.abc import Callable
from typing import Any, cast

from atlas.core.errors import ErrorSeverity

# Import types
from atlas.core.types import StreamControlProtocol
from atlas.providers.errors import ProviderStreamError
from atlas.schemas.streaming import (
    stream_metrics_schema,
    stream_state_schema,
    validate_streaming_config,
)

logger = logging.getLogger(__name__)


class StreamState(str, enum.Enum):
    """Possible states of a stream."""

    INITIALIZING = "initializing"  # Stream is being set up but not started
    ACTIVE = "active"  # Stream is actively producing content
    PAUSED = "paused"  # Stream is temporarily paused
    CANCELLED = "cancelled"  # Stream was explicitly cancelled
    COMPLETED = "completed"  # Stream has naturally completed
    ERROR = "error"  # Stream encountered an error


class StreamControl(abc.ABC, StreamControlProtocol):
    """Interface for controlling a streaming response.

    This interface provides methods for controlling streaming response flow,
    including pause, resume, and cancel operations. It also provides information
    about the stream's current state and capabilities.
    """

    @property
    @abc.abstractmethod
    def state(self) -> StreamState:
        """Get the current state of the stream."""
        pass

    @property
    @abc.abstractmethod
    def can_pause(self) -> bool:
        """Whether this stream supports pausing."""
        pass

    @property
    @abc.abstractmethod
    def can_resume(self) -> bool:
        """Whether this stream can be resumed from a paused state."""
        pass

    @property
    @abc.abstractmethod
    def can_cancel(self) -> bool:
        """Whether this stream supports cancellation."""
        pass

    @abc.abstractmethod
    def pause(self) -> bool:
        """
        Pause the stream if supported.

        Returns:
            bool: True if the stream was paused, False otherwise.

        Raises:
            ProviderStreamError: If the pause operation fails.
        """
        pass

    @abc.abstractmethod
    def resume(self) -> bool:
        """
        Resume the stream if paused.

        Returns:
            bool: True if the stream was resumed, False otherwise.

        Raises:
            ProviderStreamError: If the resume operation fails.
        """
        pass

    @abc.abstractmethod
    def cancel(self) -> bool:
        """
        Cancel the stream if supported.

        Returns:
            bool: True if the stream was cancelled, False otherwise.

        Raises:
            ProviderStreamError: If the cancel operation fails.
        """
        pass

    @abc.abstractmethod
    def register_state_change_callback(self, callback: Callable[[StreamState], None]) -> None:
        """
        Register a callback to be called when the stream state changes.

        Args:
            callback: Function to call with the new state.
        """
        pass

    @abc.abstractmethod
    def register_content_callback(self, callback: Callable[[str, Any], None]) -> None:
        """
        Register a callback to be called when new content is available.

        Args:
            callback: Function to call with new content and updated response.
        """
        pass

    @abc.abstractmethod
    def get_metrics(self) -> dict[str, Any]:
        """
        Get stream performance metrics.

        Returns:
            Dict containing stream metrics such as tokens processed,
            throughput, latency, etc.
        """
        pass


class StreamControlBase(StreamControl):
    """Base implementation of StreamControl interface.

    This class provides a foundation for implementing stream control
    capabilities with state management and callback registration.
    """

    @validate_streaming_config
    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the stream control base.

        Args:
            config: Optional configuration dictionary that will be validated using schema.
        """
        from atlas.schemas.streaming import stream_control_schema, stream_metrics_schema

        self._state_lock = threading.RLock()

        # Default initialization
        self._state = StreamState.INITIALIZING
        self._state_callbacks = []
        self._content_callbacks = []
        self._metrics: dict[str, Any] = {
            "start_time": None,
            "end_time": None,
            "tokens_processed": 0,
            "chars_processed": 0,
            "chunks_processed": 0,
            "avg_token_per_sec": 0.0,
            "total_tokens": 0,
        }
        self._metrics_lock = threading.Lock()

        # Convert to a config dict if None
        if config is None:
            config = {
                "state": self._state.value,
                "can_pause": False,
                "can_resume": False,
                "can_cancel": False,
                "metrics": dict(self._metrics),
            }

        # Validate the config if not already validated
        if not getattr(config, "_validated", False):
            try:
                # Validate config using control schema
                control_config = {
                    "state": config.get("state", self._state.value),
                    "can_pause": config.get("can_pause", False),
                    "can_resume": config.get("can_resume", False),
                    "can_cancel": config.get("can_cancel", False),
                }
                validated_control = stream_control_schema.load(control_config)
                # Mark as validated
                validated_control._validated = True

                # Update config with validated control values
                config.update(validated_control)
            except Exception as e:
                logger.warning(f"Invalid control configuration: {e}")
                # Continue with default values

        # Apply configuration if provided
        if config is not None:
            # Set initial state if specified
            if "state" in config:
                state_value = config["state"]
                # If already a StreamState enum, use it directly
                if isinstance(state_value, StreamState):
                    self._state = state_value
                else:
                    # Validate and convert state
                    try:
                        # Use schema to convert and validate
                        validated_state = stream_state_schema.load({"value": state_value})
                        self._state = validated_state
                    except Exception as e:
                        # Default to initializing if invalid
                        logger.warning(
                            f"Invalid initial state: {state_value}, using default. Error: {e}"
                        )

            # Set initial metrics if specified
            if "metrics" in config:
                try:
                    # Validate metrics using schema
                    validated_metrics = stream_metrics_schema.load(config["metrics"])
                    self._metrics.update(validated_metrics)
                except Exception as e:
                    logger.warning(f"Invalid metrics configuration: {e}")
                    # Continue with default metrics

    @property
    def state(self) -> StreamState:
        """Get the current state of the stream."""
        with self._state_lock:
            return self._state

    @property
    def can_pause(self) -> bool:
        """Whether this stream supports pausing."""
        # Default implementation supports pausing if active
        with self._state_lock:
            return self._state == StreamState.ACTIVE

    @property
    def can_resume(self) -> bool:
        """Whether this stream can be resumed from a paused state."""
        # Default implementation supports resuming if paused
        with self._state_lock:
            return self._state == StreamState.PAUSED

    @property
    def can_cancel(self) -> bool:
        """Whether this stream supports cancellation."""
        # Default implementation supports cancellation if active or paused
        with self._state_lock:
            return self._state in (StreamState.ACTIVE, StreamState.PAUSED)

    def _set_state(self, new_state: StreamState) -> None:
        """
        Set the stream state and notify callbacks.

        Args:
            new_state: The new state.
        """
        from atlas.schemas.streaming import stream_state_transition_schema

        with self._state_lock:
            if self._state == new_state:
                return

            old_state = self._state

            # Determine trigger based on state transition
            trigger = None
            if old_state == StreamState.INITIALIZING and new_state == StreamState.ACTIVE:
                trigger = "start"
            elif old_state == StreamState.ACTIVE and new_state == StreamState.PAUSED:
                trigger = "pause"
            elif old_state == StreamState.PAUSED and new_state == StreamState.ACTIVE:
                trigger = "resume"
            elif (old_state == StreamState.ACTIVE and new_state == StreamState.CANCELLED) or (
                old_state == StreamState.PAUSED and new_state == StreamState.CANCELLED
            ):
                trigger = "cancel"
            elif old_state == StreamState.ACTIVE and new_state == StreamState.COMPLETED:
                trigger = "complete"
            elif (
                (old_state == StreamState.ACTIVE and new_state == StreamState.ERROR)
                or (old_state == StreamState.PAUSED and new_state == StreamState.ERROR)
                or (old_state == StreamState.INITIALIZING and new_state == StreamState.ERROR)
            ):
                trigger = "error"
            elif (
                old_state in [StreamState.CANCELLED, StreamState.COMPLETED, StreamState.ERROR]
                and new_state == StreamState.INITIALIZING
            ):
                trigger = "reset"
            else:
                # Log a warning for invalid transitions but allow them anyway for compatibility
                logger.warning(f"Invalid state transition: {old_state} -> {new_state}")
                trigger = "unknown"

            # Validate the transition if we found a trigger
            if trigger and trigger != "unknown":
                try:
                    # Create transition data
                    transition = {
                        "from_state": old_state.value,
                        "to_state": new_state.value,
                        "trigger": trigger,
                    }

                    # Validate transition
                    stream_state_transition_schema.load(transition)
                except Exception as e:
                    logger.warning(
                        f"Invalid state transition: {old_state} -> {new_state}. Error: {e}"
                    )
                    # Continue with the transition anyway for compatibility

            # Update state
            self._state = new_state

        # Notify callbacks outside the lock to prevent deadlocks
        for callback in self._state_callbacks:
            try:
                callback(new_state)
            except Exception as e:
                logger.error(f"Error in state change callback: {e}", exc_info=True)

        logger.debug(f"Stream state changed: {old_state} -> {new_state}")

    def register_state_change_callback(self, callback: Callable[[StreamState], None]) -> None:
        """
        Register a callback to be called when the stream state changes.

        Args:
            callback: Function to call with the new state.
        """
        with self._state_lock:
            self._state_callbacks.append(callback)
            # Immediately call with current state to initialize
            current_state = self._state

        try:
            callback(current_state)
        except Exception as e:
            logger.error(f"Error in initial state callback: {e}", exc_info=True)

    def register_content_callback(self, callback: Callable[[str, Any], None]) -> None:
        """
        Register a callback to be called when new content is available.

        Args:
            callback: Function to call with new content and updated response.
        """
        self._content_callbacks.append(callback)

    def pause(self) -> bool:
        """
        Pause the stream if supported.

        Returns:
            bool: True if the stream was paused, False otherwise.

        Raises:
            ProviderStreamError: If the pause operation fails.
        """
        from atlas.schemas.streaming import stream_operation_result_schema, validate_pause_operation

        with self._state_lock:
            current_state = self._state.value

            # Validate if the operation is allowed
            if not validate_pause_operation(current_state):
                logger.debug(f"Cannot pause stream in state {current_state}")
                return False

            # Check implementation-specific capability
            if not self.can_pause:
                logger.debug("Stream does not support pausing")
                return False

            try:
                # Provider-specific pause implementation
                if self._pause_provider_stream():
                    # Create operation result
                    result = {"success": True, "state": StreamState.PAUSED.value}

                    # Validate the result
                    validated_result = stream_operation_result_schema.load(result)

                    # Update state
                    self._set_state(StreamState.PAUSED)
                    return True
                return False
            except Exception as e:
                error = ProviderStreamError(
                    message=f"Failed to pause stream: {e}",
                    cause=e,
                    severity=ErrorSeverity.WARNING,
                    can_resume=True,
                )
                logger.error(str(error), exc_info=True)
                raise error

    def resume(self) -> bool:
        """
        Resume the stream if paused.

        Returns:
            bool: True if the stream was resumed, False otherwise.

        Raises:
            ProviderStreamError: If the resume operation fails.
        """
        from atlas.schemas.streaming import (
            stream_operation_result_schema,
            validate_resume_operation,
        )

        with self._state_lock:
            current_state = self._state.value

            # Validate if the operation is allowed
            if not validate_resume_operation(current_state):
                logger.debug(f"Cannot resume stream in state {current_state}")
                return False

            # Check implementation-specific capability
            if not self.can_resume:
                logger.debug("Stream does not support resuming")
                return False

            try:
                # Provider-specific resume implementation
                if self._resume_provider_stream():
                    # Create operation result
                    result = {"success": True, "state": StreamState.ACTIVE.value}

                    # Validate the result
                    validated_result = stream_operation_result_schema.load(result)

                    # Update state
                    self._set_state(StreamState.ACTIVE)
                    return True
                return False
            except Exception as e:
                error = ProviderStreamError(
                    message=f"Failed to resume stream: {e}",
                    cause=e,
                    severity=ErrorSeverity.WARNING,
                    can_resume=False,
                )
                logger.error(str(error), exc_info=True)
                raise error

    def cancel(self) -> bool:
        """
        Cancel the stream if supported.

        Returns:
            bool: True if the stream was cancelled, False otherwise.

        Raises:
            ProviderStreamError: If the cancel operation fails.
        """
        from atlas.schemas.streaming import (
            stream_operation_result_schema,
            validate_cancel_operation,
        )

        with self._state_lock:
            current_state = self._state.value

            # Validate if the operation is allowed
            if not validate_cancel_operation(current_state):
                logger.debug(f"Cannot cancel stream in state {current_state}")
                return False

            # Check implementation-specific capability
            if not self.can_cancel:
                logger.debug("Stream does not support cancellation")
                return False

            try:
                # Provider-specific cancel implementation
                if self._cancel_provider_stream():
                    # Create operation result
                    result = {"success": True, "state": StreamState.CANCELLED.value}

                    # Validate the result
                    validated_result = stream_operation_result_schema.load(result)

                    # Update state
                    self._set_state(StreamState.CANCELLED)
                    return True
                return False
            except Exception as e:
                error = ProviderStreamError(
                    message=f"Failed to cancel stream: {e}",
                    cause=e,
                    severity=ErrorSeverity.WARNING,
                    can_resume=False,
                )
                logger.error(str(error), exc_info=True)
                raise error

    def _pause_provider_stream(self) -> bool:
        """
        Provider-specific implementation to pause the stream.

        Returns:
            bool: True if the stream was paused, False otherwise.
        """
        # Default implementation always succeeds
        return True

    def _resume_provider_stream(self) -> bool:
        """
        Provider-specific implementation to resume the stream.

        Returns:
            bool: True if the stream was resumed, False otherwise.
        """
        # Default implementation always succeeds
        return True

    def _cancel_provider_stream(self) -> bool:
        """
        Provider-specific implementation to cancel the stream.

        Returns:
            bool: True if the stream was cancelled, False otherwise.
        """
        # Default implementation always succeeds
        return True

    def get_metrics(self) -> dict[str, Any]:
        """
        Get stream performance metrics.

        Returns:
            Dict containing stream metrics such as tokens processed,
            throughput, latency, etc.
        """
        with self._metrics_lock:
            # Make a copy to avoid thread safety issues
            metrics_copy = dict(self._metrics)

            try:
                # Validate metrics using schema before returning
                validated_metrics = stream_metrics_schema.validate_data(metrics_copy)
                return validated_metrics
            except Exception as e:
                # Log warning but still return the metrics
                logger.warning(f"Metrics validation failed: {e}")
                return metrics_copy

    def _update_metrics(self, delta: str) -> None:
        """
        Update the metrics with new content.

        Args:
            delta: The new content.
        """
        import time

        with self._metrics_lock:
            # Initialize metrics with default values if they're None
            if self._metrics["start_time"] is None:
                self._metrics["start_time"] = time.time()

            if self._metrics["chunks_processed"] is None:
                self._metrics["chunks_processed"] = 0

            if self._metrics["chars_processed"] is None:
                self._metrics["chars_processed"] = 0

            if self._metrics["tokens_processed"] is None:
                self._metrics["tokens_processed"] = 0

            # Get the current time for calculations
            current_time = time.time()

            # Update metrics (with safe type handling)
            chunks_processed = self._metrics["chunks_processed"]
            chars_processed = self._metrics["chars_processed"]
            tokens_processed = self._metrics["tokens_processed"]

            # Perform operations on the local variables
            chunks_processed += 1
            chars_processed += len(delta)

            # Estimate tokens (can be improved with actual tokenization)
            estimated_tokens = len(delta) / 4  # Rough estimate
            tokens_processed += estimated_tokens

            # Store updated values back
            self._metrics["chunks_processed"] = chunks_processed
            self._metrics["chars_processed"] = chars_processed
            self._metrics["tokens_processed"] = tokens_processed

            # Calculate rate safely
            start_time = cast(float, self._metrics["start_time"])  # Cast to ensure type safety
            elapsed = current_time - start_time
            if elapsed > 0:
                self._metrics["avg_token_per_sec"] = tokens_processed / elapsed
