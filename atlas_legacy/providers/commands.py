"""
Provider command implementations.

This module provides command classes for provider operations. These commands
encapsulate the logic for generating responses, streaming, validating requests,
and cancellation operations.
"""

import threading
import time
import uuid
from abc import abstractmethod
from typing import Any

from atlas.core.errors import AtlasError, ErrorCategory, ErrorSeverity
from atlas.core.logging import get_logger
from atlas.core.services.buffer import create_buffer
from atlas.core.services.commands import Command
from atlas.core.services.events import EventSystem

# Create a logger for this module
logger = get_logger(__name__)


class ProviderCommandError(AtlasError):
    """Error during provider command execution."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        command_id: str | None = None,
        provider_type: str | None = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            command_id: The ID of the command causing the error.
            provider_type: The provider type.
        """
        details = details or {}

        if command_id:
            details["command_id"] = command_id

        if provider_type:
            details["provider_type"] = provider_type

        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.OPERATION,
            details=details,
            cause=cause,
        )


class ProviderCommand(Command):
    """Base class for provider commands."""

    def __init__(self, provider: Any, state_container: Any, event_system: EventSystem, **kwargs):
        """Initialize the provider command.

        Args:
            provider: The provider instance.
            state_container: The provider's state container.
            event_system: The event system service.
            **kwargs: Command-specific parameters.
        """
        self.command_id = str(uuid.uuid4())
        self.provider = provider
        self.state = state_container
        self.event_system = event_system
        self.kwargs = kwargs
        self.completed = False
        self.result = None
        self.error = None

        logger.debug(f"Created {self.__class__.__name__} for provider {provider.provider_type}")

    @abstractmethod
    def execute(self) -> Any:
        """Execute the command and return the result."""
        pass

    def undo(self) -> bool:
        """Undo the command if possible.

        Returns:
            True if the command was undone, False otherwise.
        """
        if not self.is_undoable or not self.completed:
            return False

        return self._do_undo()

    def _do_undo(self) -> bool:
        """Perform the actual undo operation.

        This method should be overridden by subclasses that support undo.

        Returns:
            True if the command was undone, False otherwise.
        """
        return False

    @property
    def is_undoable(self) -> bool:
        """Check if this command can be undone.

        Returns:
            True if the command can be undone, False otherwise.
        """
        return False

    def _update_state(self, updates: dict[str, Any]) -> None:
        """Update the provider state.

        Args:
            updates: The state updates to apply.
        """
        self.state.update(updates)

    def _publish_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Publish an event.

        Args:
            event_type: The type of event to publish.
            data: The event data.
        """
        event_data = {
            "provider_type": self.provider.provider_type,
            "model_name": self.provider.model_name,
            "command_id": self.command_id,
            **data,
        }

        self.event_system.publish(f"provider.{event_type}", event_data)

    def _handle_error(self, error: Exception) -> None:
        """Handle an error that occurred during command execution.

        Args:
            error: The error that occurred.

        Raises:
            ProviderCommandError: The wrapped error.
        """
        self.error = error

        # Update state with error information
        self._update_state({"last_error": str(error), "status": "error"})

        # Publish error event
        self._publish_event(
            "error",
            {
                "error": str(error),
                "error_type": type(error).__name__,
                "command_type": self.__class__.__name__,
            },
        )

        # Convert to ProviderCommandError
        raise ProviderCommandError(
            message=f"Command execution failed: {error}",
            cause=error,
            command_id=self.command_id,
            provider_type=self.provider.provider_type,
        )


class GenerateCommand(ProviderCommand):
    """Command for generating a response."""

    def execute(self) -> dict[str, Any]:
        """Execute the generate command.

        Returns:
            The generation response.

        Raises:
            ProviderCommandError: If the command execution fails.
        """
        try:
            # Get the request from kwargs
            request = self.kwargs.get("request")
            if not request:
                raise ValueError("Missing required parameter: request")

            # Update state to indicate request is being processed
            self._update_state(
                {
                    "active_requests": self.state.data.get("active_requests", 0) + 1,
                    "total_requests": self.state.data.get("total_requests", 0) + 1,
                    "status": "generating",
                }
            )

            # Publish event for request start
            self._publish_event("generate.start", {"request": request})

            # Start execution timing
            start_time = time.time()

            # Call the provider's implementation to get the response
            # This will typically call the provider-specific implementation
            response = self.provider._generate_implementation(request)

            # Calculate execution time
            execution_time = time.time() - start_time

            # Update state to reflect completion
            token_count = response.get("usage", {}).get("total_tokens", 0)
            self._update_state(
                {
                    "active_requests": max(0, self.state.data.get("active_requests", 0) - 1),
                    "total_tokens": self.state.data.get("total_tokens", 0) + token_count,
                    "status": "ready",
                }
            )

            # Publish event for request completion
            self._publish_event(
                "generate.end",
                {
                    "request": request,
                    "response": response,
                    "token_count": token_count,
                    "execution_time": execution_time,
                },
            )

            # Store the result and mark as completed
            self.result = response
            self.completed = True

            return response

        except Exception as e:
            logger.error(
                f"Error in GenerateCommand for {self.provider.provider_type}: {e}", exc_info=True
            )
            self._handle_error(e)


class StreamCommand(ProviderCommand):
    """Command for streaming a response."""

    def execute(self) -> Any:
        """Execute the stream command.

        Returns:
            A streamable object that yields response chunks.

        Raises:
            ProviderCommandError: If the command execution fails.
        """
        try:
            # Get the request from kwargs
            request = self.kwargs.get("request")
            if not request:
                raise ValueError("Missing required parameter: request")

            # Create a buffer for this stream
            buffer_id = f"{self.provider.provider_type}_{self.command_id}"
            stream_buffer = create_buffer(
                {
                    "buffer_type": "memory",
                    "max_size": 1024 * 10,  # 10KB buffer
                }
            )

            # Update state to indicate streaming is active
            self._update_state(
                {
                    "active_requests": self.state.data.get("active_requests", 0) + 1,
                    "total_requests": self.state.data.get("total_requests", 0) + 1,
                    "is_streaming": True,
                    "status": "streaming",
                }
            )

            # Publish event for stream start
            self._publish_event("stream.start", {"request": request, "buffer_id": buffer_id})

            # Begin streaming in a separate thread
            self._start_streaming_thread(request, stream_buffer)

            # Return the buffer (or a wrapper around it)
            self.result = stream_buffer
            self.completed = True

            return stream_buffer

        except Exception as e:
            logger.error(
                f"Error in StreamCommand for {self.provider.provider_type}: {e}", exc_info=True
            )
            self._handle_error(e)

    def _start_streaming_thread(self, request: dict[str, Any], buffer: Any) -> None:
        """Start a thread to handle the streaming process.

        Args:
            request: The generation request.
            buffer: The buffer to stream results into.
        """

        def stream_worker():
            try:
                # Start execution timing
                start_time = time.time()

                # Call the provider's implementation to get the streaming iterator
                # This will typically call the provider-specific implementation
                stream_iter = self.provider._stream_implementation(request)

                token_count = 0

                # Process stream items
                for item in stream_iter:
                    # Push the item to the buffer
                    buffer.push(item)

                    # Update token count if available
                    if "usage" in item and "total_tokens" in item["usage"]:
                        token_count = item["usage"]["total_tokens"]

                    # Publish event for chunk received
                    self._publish_event(
                        "stream.chunk",
                        {
                            "chunk": item,
                            "buffer_id": buffer.buffer_id if hasattr(buffer, "buffer_id") else None,
                        },
                    )

                # Calculate execution time
                execution_time = time.time() - start_time

                # Mark the buffer as complete
                if hasattr(buffer, "complete"):
                    buffer.complete()

                # Update state to reflect completion
                self._update_state(
                    {
                        "active_requests": max(0, self.state.data.get("active_requests", 0) - 1),
                        "total_tokens": self.state.data.get("total_tokens", 0) + token_count,
                        "is_streaming": False,
                        "status": "ready",
                    }
                )

                # Publish event for stream completion
                self._publish_event(
                    "stream.end",
                    {
                        "request": request,
                        "buffer_id": buffer.buffer_id if hasattr(buffer, "buffer_id") else None,
                        "token_count": token_count,
                        "execution_time": execution_time,
                    },
                )

            except Exception as e:
                logger.error(
                    f"Error in streaming thread for {self.provider.provider_type}: {e}",
                    exc_info=True,
                )

                # Mark buffer as failed if possible
                if hasattr(buffer, "fail"):
                    buffer.fail(str(e))

                # Update state with error information
                self._update_state(
                    {
                        "active_requests": max(0, self.state.data.get("active_requests", 0) - 1),
                        "is_streaming": False,
                        "last_error": str(e),
                        "status": "error",
                    }
                )

                # Publish error event
                self._publish_event(
                    "error",
                    {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "is_streaming": True,
                        "buffer_id": buffer.buffer_id if hasattr(buffer, "buffer_id") else None,
                    },
                )

        # Create and start the thread
        thread = threading.Thread(target=stream_worker)
        thread.daemon = True
        thread.start()


class ValidateCommand(ProviderCommand):
    """Command for validating a request."""

    def execute(self) -> bool:
        """Execute the validate command.

        Returns:
            True if the request is valid, False otherwise.

        Raises:
            ProviderCommandError: If the command execution fails.
        """
        try:
            # Get the request from kwargs
            request = self.kwargs.get("request")
            if not request:
                raise ValueError("Missing required parameter: request")

            # Start execution timing
            start_time = time.time()

            # Call the provider's implementation to validate the request
            # This will typically call the provider-specific implementation
            valid = self.provider._validate_implementation(request)

            # Calculate execution time
            execution_time = time.time() - start_time

            # Publish event for validation result
            self._publish_event(
                "validate", {"request": request, "valid": valid, "execution_time": execution_time}
            )

            # Store the result and mark as completed
            self.result = valid
            self.completed = True

            return valid

        except Exception as e:
            logger.error(
                f"Error in ValidateCommand for {self.provider.provider_type}: {e}", exc_info=True
            )
            self._handle_error(e)


class CancelCommand(ProviderCommand):
    """Command for cancelling a request."""

    def execute(self) -> bool:
        """Execute the cancel command.

        Returns:
            True if the request was cancelled, False otherwise.

        Raises:
            ProviderCommandError: If the command execution fails.
        """
        try:
            # Get the request ID from kwargs
            request_id = self.kwargs.get("request_id")
            if not request_id:
                raise ValueError("Missing required parameter: request_id")

            # Update state to indicate cancellation attempt
            self._update_state({"status": "cancelling"})

            # Publish event for cancellation attempt
            self._publish_event("cancel.attempt", {"request_id": request_id})

            # Start execution timing
            start_time = time.time()

            # Call the provider's implementation to cancel the request
            # This will typically call the provider-specific implementation
            success = self.provider._cancel_implementation(request_id)

            # Calculate execution time
            execution_time = time.time() - start_time

            # Update state based on cancellation result
            if success:
                self._update_state(
                    {
                        "active_requests": max(0, self.state.data.get("active_requests", 0) - 1),
                        "is_streaming": False,
                        "status": "ready",
                    }
                )
            else:
                self._update_state({"status": "ready"})

            # Publish event for cancellation result
            self._publish_event(
                "cancel.result",
                {"request_id": request_id, "success": success, "execution_time": execution_time},
            )

            # Store the result and mark as completed
            self.result = success
            self.completed = True

            return success

        except Exception as e:
            logger.error(
                f"Error in CancelCommand for {self.provider.provider_type}: {e}", exc_info=True
            )
            self._handle_error(e)
