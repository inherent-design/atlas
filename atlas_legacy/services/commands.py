"""
Command pattern implementation with undo capability.

This module provides a command pattern implementation with undo/redo capability,
command queueing, and execution tracking. It is designed to be thread-safe and
support command composition.
"""

import copy
import inspect
import time
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from threading import RLock
from typing import Any, ClassVar, Generic, TypeAlias, TypeVar

from atlas.core.errors import AtlasError, ErrorCategory, ErrorSeverity
from atlas.core.logging import get_logger
from atlas.schemas.services import command_result_schema

# Type aliases for improved clarity
CommandId: TypeAlias = str
CommandName: TypeAlias = str
CommandParameters: TypeAlias = dict[str, Any]
CommandResult: TypeAlias = dict[str, Any]
ServiceName: TypeAlias = str
UndoFunction: TypeAlias = Callable[[], None]

# Generic type for command results
T = TypeVar("T")

# Create a logger for this module
logger = get_logger(__name__)


# Custom error classes for the command system
class CommandError(AtlasError):
    """Base class for command system errors."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        command_id: str | None = None,
        command_name: str | None = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            command_id: The ID of the command causing the error.
            command_name: The name of the command causing the error.
        """
        details = details or {}

        if command_id:
            details["command_id"] = command_id

        if command_name:
            details["command_name"] = command_name

        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.LOGIC,
            details=details,
            cause=cause,
        )


class CommandExecutionError(CommandError):
    """Error related to command execution."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        command_id: str | None = None,
        command_name: str | None = None,
        parameters: dict[str, Any] | None = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            command_id: The ID of the command causing the error.
            command_name: The name of the command causing the error.
            parameters: The parameters passed to the command.
        """
        details = details or {}

        if parameters:
            details["parameters"] = parameters

        super().__init__(
            message=message,
            details=details,
            cause=cause,
            severity=severity,
            command_id=command_id,
            command_name=command_name,
        )


class CommandUndoError(CommandError):
    """Error related to command undo operations."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        command_id: str | None = None,
        command_name: str | None = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            command_id: The ID of the command causing the error.
            command_name: The name of the command causing the error.
        """
        super().__init__(
            message=message,
            details=details,
            cause=cause,
            severity=severity,
            command_id=command_id,
            command_name=command_name,
        )


class Command(Generic[T], ABC):
    """Base class for all commands in the system."""

    def __init__(
        self,
        command_id: str | None = None,
        parameters: dict[str, Any] | None = None,
        target_service: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize a new command.

        Args:
            command_id: Optional unique identifier for this command.
            parameters: Optional parameters for the command.
            target_service: Optional target service for the command.
            metadata: Optional metadata for the command.
        """
        self.command_id = command_id or str(uuid.uuid4())
        self.parameters = parameters or {}
        self.target_service = target_service
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self._undo_func: UndoFunction | None = None

        # Avoid property access during init since subclasses may not have fully initialized
        command_name = self.__class__.__name__
        logger.debug(f"Created command {self.command_id} with name {command_name}")

    @property
    def name(self) -> str:
        """Get the name of the command.

        Returns:
            The name of the command.
        """
        return self.__class__.__name__

    @property
    def is_undoable(self) -> bool:
        """Check if this command can be undone.

        Returns:
            True if the command can be undone, False otherwise.
        """
        return self._undo_func is not None

    @abstractmethod
    def execute(self) -> T:
        """Execute the command.

        Returns:
            The result of the command execution.

        Raises:
            CommandExecutionError: If the command execution fails.
        """
        pass

    def undo(self) -> None:
        """Undo the command.

        Raises:
            CommandUndoError: If the command cannot be undone.
        """
        if not self.is_undoable:
            raise CommandUndoError(
                message=f"Command {self.name} is not undoable",
                command_id=self.command_id,
                command_name=self.name,
            )

        try:
            self._undo_func()
            logger.debug(f"Undid command {self.command_id}")
        except Exception as e:
            raise CommandUndoError(
                message=f"Failed to undo command {self.name}: {e}",
                cause=e,
                command_id=self.command_id,
                command_name=self.name,
            )

    def set_undo_func(self, func: UndoFunction) -> None:
        """Set the undo function for this command.

        Args:
            func: The function to call to undo this command.
        """
        self._undo_func = func

    def to_dict(self) -> dict[str, Any]:
        """Convert the command to a dictionary.

        Returns:
            Dictionary representation of the command.
        """
        return {
            "command_id": self.command_id,
            "name": self.name,
            "parameters": self.parameters,
            "target_service": self.target_service,
            "is_undoable": self.is_undoable,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


class FunctionCommand(Command[T]):
    """Command that executes a function with arguments."""

    def __init__(
        self,
        func: Callable[..., T],
        args: tuple = (),
        kwargs: dict[str, Any] | None = None,
        command_id: str | None = None,
        target_service: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize a new function command.

        Args:
            func: The function to execute.
            args: Positional arguments for the function.
            kwargs: Keyword arguments for the function.
            command_id: Optional unique identifier for this command.
            target_service: Optional target service for the command.
            metadata: Optional metadata for the command.
        """
        parameters = kwargs or {}

        # Add positional arguments to parameters
        for i, arg in enumerate(args):
            parameters[f"arg_{i}"] = arg

        super().__init__(
            command_id=command_id,
            parameters=parameters,
            target_service=target_service,
            metadata=metadata,
        )

        self._func = func
        self._args = args
        self._kwargs = kwargs or {}

        # Extract function name for better logging
        if hasattr(func, "__name__"):
            self.function_name = func.__name__
        else:
            self.function_name = "anonymous"

    @property
    def name(self) -> str:
        """Get the name of the command.

        Returns:
            The name of the command.
        """
        return f"FunctionCommand({self.function_name})"

    def execute(self) -> T:
        """Execute the function.

        Returns:
            The result of the function execution.

        Raises:
            CommandExecutionError: If the function execution fails.
        """
        try:
            result = self._func(*self._args, **self._kwargs)
            logger.debug(f"Executed function command {self.command_id} ({self.function_name})")
            return result
        except Exception as e:
            raise CommandExecutionError(
                message=f"Failed to execute function {self.function_name}: {e}",
                cause=e,
                command_id=self.command_id,
                command_name=self.name,
                parameters=self.parameters,
            )


class CompositeCommand(Command[list[Any]]):
    """Command that executes multiple commands in sequence."""

    def __init__(
        self,
        commands: list[Command],
        command_id: str | None = None,
        target_service: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize a new composite command.

        Args:
            commands: The commands to execute in sequence.
            command_id: Optional unique identifier for this command.
            target_service: Optional target service for the command.
            metadata: Optional metadata for the command.
        """
        super().__init__(
            command_id=command_id,
            parameters={"command_count": len(commands)},
            target_service=target_service,
            metadata=metadata,
        )

        self._commands = commands
        self._executed_commands: list[Command] = []

    @property
    def name(self) -> str:
        """Get the name of the command.

        Returns:
            The name of the command.
        """
        return f"CompositeCommand({len(self._commands)})"

    @property
    def is_undoable(self) -> bool:
        """Check if this command can be undone.

        Returns:
            True if all executed commands can be undone, False otherwise.
        """
        return all(cmd.is_undoable for cmd in self._executed_commands)

    def execute(self) -> list[Any]:
        """Execute all commands in sequence.

        Returns:
            A list of results from each command.

        Raises:
            CommandExecutionError: If any command execution fails.
        """
        results = []
        self._executed_commands = []

        for i, command in enumerate(self._commands):
            try:
                logger.debug(
                    f"Executing sub-command {i + 1}/{len(self._commands)} in composite command {self.command_id}"
                )
                result = command.execute()
                results.append(result)
                self._executed_commands.append(command)
            except Exception as e:
                # Roll back any executed commands
                self._rollback_executed()

                raise CommandExecutionError(
                    message=f"Failed to execute sub-command {i + 1}/{len(self._commands)} in composite command: {e}",
                    cause=e,
                    command_id=self.command_id,
                    command_name=self.name,
                )

        logger.debug(
            f"Executed composite command {self.command_id} with {len(self._commands)} sub-commands"
        )
        return results

    def undo(self) -> None:
        """Undo all executed commands in reverse order.

        Raises:
            CommandUndoError: If any command cannot be undone.
        """
        if not self.is_undoable:
            raise CommandUndoError(
                message=f"Composite command {self.command_id} is not fully undoable",
                command_id=self.command_id,
                command_name=self.name,
            )

        try:
            # Undo in reverse order
            for i, command in enumerate(reversed(self._executed_commands)):
                logger.debug(
                    f"Undoing sub-command {len(self._executed_commands) - i}/{len(self._executed_commands)} "
                    f"in composite command {self.command_id}"
                )
                command.undo()

            logger.debug(f"Undid composite command {self.command_id}")

        except Exception as e:
            raise CommandUndoError(
                message=f"Failed to undo composite command: {e}",
                cause=e,
                command_id=self.command_id,
                command_name=self.name,
            )

    def _rollback_executed(self) -> None:
        """Roll back any executed commands in case of failure.

        This method is called internally when a command fails to execute.
        It attempts to undo any commands that were successfully executed.
        """
        logger.debug(
            f"Rolling back {len(self._executed_commands)} executed commands in composite command {self.command_id}"
        )

        for i, command in enumerate(reversed(self._executed_commands)):
            try:
                if command.is_undoable:
                    logger.debug(
                        f"Rolling back sub-command {len(self._executed_commands) - i}/{len(self._executed_commands)}"
                    )
                    command.undo()
            except Exception as e:
                logger.error(
                    f"Error during rollback of sub-command "
                    f"{len(self._executed_commands) - i}/{len(self._executed_commands)}: {e}",
                    exc_info=True,
                )


class CommandExecutor:
    """Executes commands and maintains command history."""

    # Class constants
    MAX_HISTORY: ClassVar[int] = 100

    def __init__(self, max_history: int = MAX_HISTORY):
        """Initialize a new command executor.

        Args:
            max_history: Maximum number of commands to keep in history.
        """
        self._lock = RLock()
        self._max_history = max_history
        self._command_history: list[Command] = []
        self._result_history: list[dict[str, Any]] = []
        self._undo_stack: list[Command] = []
        self._redo_stack: list[Command] = []

        logger.debug(f"Created CommandExecutor with max_history={max_history}")

    def execute(self, command: Command[T]) -> T:
        """Execute a command and add it to history.

        Args:
            command: The command to execute.

        Returns:
            The result of the command execution.

        Raises:
            CommandExecutionError: If the command execution fails.
        """
        start_time = time.time()
        success = False
        error_message = None

        try:
            # Execute the command
            result = command.execute()
            success = True

            # Add to history if successful
            with self._lock:
                self._command_history.append(command)

                # Trim history if needed
                if len(self._command_history) > self._max_history:
                    self._command_history = self._command_history[-self._max_history :]

                # Clear redo stack when executing a new command
                self._redo_stack = []

                # Add to undo stack if undoable
                if command.is_undoable:
                    self._undo_stack.append(command)

            logger.debug(f"Executed command {command.command_id}")
            return result

        except Exception as e:
            success = False
            error_message = str(e)

            # Re-raise as CommandExecutionError
            if not isinstance(e, CommandExecutionError):
                raise CommandExecutionError(
                    message=f"Failed to execute command {command.name}: {e}",
                    cause=e,
                    command_id=command.command_id,
                    command_name=command.name,
                    parameters=command.parameters,
                )
            raise

        finally:
            # Record result in history regardless of success
            execution_time = time.time() - start_time

            try:
                # Create result record
                result_data = {
                    "result_id": str(uuid.uuid4()),
                    "command_id": command.command_id,
                    "success": success,
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat(),
                }

                if success:
                    # Try to add result data if serializable
                    try:
                        import json

                        # Test serialization - not used directly but checks if possible
                        json.dumps({"result": result})
                        result_data["data"] = {"result": result}
                    except (TypeError, ValueError):
                        # If serialization fails, just omit the data
                        result_data["data"] = {"result_type": str(type(result))}
                else:
                    # Add error information
                    result_data["error"] = error_message

                # Store result in history
                with self._lock:
                    validated_result = command_result_schema.load(result_data)
                    self._result_history.append(validated_result)

                    # Trim result history if needed
                    if len(self._result_history) > self._max_history:
                        self._result_history = self._result_history[-self._max_history :]

            except Exception as result_error:
                logger.error(f"Error recording command result: {result_error}", exc_info=True)

    def undo(self) -> CommandId | None:
        """Undo the last undoable command.

        Returns:
            The ID of the undone command, or None if no command to undo.

        Raises:
            CommandUndoError: If the command cannot be undone.
        """
        with self._lock:
            if not self._undo_stack:
                logger.debug("No commands to undo")
                return None

            command = self._undo_stack.pop()

        try:
            # Undo the command
            command.undo()

            # Add to redo stack
            with self._lock:
                self._redo_stack.append(command)

            logger.debug(f"Undid command {command.command_id}")
            return command.command_id

        except Exception as e:
            # Re-add to undo stack on failure
            with self._lock:
                self._undo_stack.append(command)

            # Re-raise as CommandUndoError
            if not isinstance(e, CommandUndoError):
                raise CommandUndoError(
                    message=f"Failed to undo command {command.name}: {e}",
                    cause=e,
                    command_id=command.command_id,
                    command_name=command.name,
                )
            raise

    def redo(self) -> CommandId | None:
        """Redo the last undone command.

        Returns:
            The ID of the redone command, or None if no command to redo.

        Raises:
            CommandExecutionError: If the command execution fails.
        """
        with self._lock:
            if not self._redo_stack:
                logger.debug("No commands to redo")
                return None

            command = self._redo_stack.pop()

        try:
            # Re-execute the command
            result = command.execute()

            # Add back to undo stack
            with self._lock:
                self._undo_stack.append(command)

                # Record result in history
                try:
                    result_data = {
                        "result_id": str(uuid.uuid4()),
                        "command_id": command.command_id,
                        "success": True,
                        "execution_time": 0.0,  # No timing for redo
                        "timestamp": datetime.now().isoformat(),
                    }

                    # Try to add result data if serializable
                    try:
                        import json

                        # Test serialization
                        json.dumps({"result": result})
                        result_data["data"] = {"result": result}
                    except (TypeError, ValueError):
                        # If serialization fails, just omit the data
                        result_data["data"] = {"result_type": str(type(result))}

                    # Store result in history
                    validated_result = command_result_schema.load(result_data)
                    self._result_history.append(validated_result)

                    # Trim result history if needed
                    if len(self._result_history) > self._max_history:
                        self._result_history = self._result_history[-self._max_history :]

                except Exception as result_error:
                    logger.error(f"Error recording redo result: {result_error}", exc_info=True)

            logger.debug(f"Redid command {command.command_id}")
            return command.command_id

        except Exception as e:
            # Re-add to redo stack on failure
            with self._lock:
                self._redo_stack.append(command)

            # Re-raise as CommandExecutionError
            if not isinstance(e, CommandExecutionError):
                raise CommandExecutionError(
                    message=f"Failed to redo command {command.name}: {e}",
                    cause=e,
                    command_id=command.command_id,
                    command_name=command.name,
                    parameters=command.parameters,
                )
            raise

    def clear_history(self) -> None:
        """Clear command history and stacks."""
        with self._lock:
            self._command_history = []
            self._result_history = []
            self._undo_stack = []
            self._redo_stack = []

            logger.debug("Cleared command history and stacks")

    def get_history(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Get command history.

        Args:
            limit: Maximum number of commands to return.

        Returns:
            List of command dictionaries, newest first.
        """
        with self._lock:
            history = [cmd.to_dict() for cmd in self._command_history]

            # Return newest first
            history.reverse()

            if limit:
                history = history[:limit]

            return history

    def get_results(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Get command result history.

        Args:
            limit: Maximum number of results to return.

        Returns:
            List of result dictionaries, newest first.
        """
        with self._lock:
            # Return newest first (already in reverse order)
            results = self._result_history.copy()
            results.reverse()

            if limit:
                results = results[:limit]

            return results

    def get_command_result(self, command_id: CommandId) -> dict[str, Any] | None:
        """Get the result of a specific command.

        Args:
            command_id: The ID of the command.

        Returns:
            The result dictionary, or None if not found.
        """
        with self._lock:
            for result in self._result_history:
                if result.get("command_id") == command_id:
                    return result

            return None

    def can_undo(self) -> bool:
        """Check if there are commands that can be undone.

        Returns:
            True if there are commands that can be undone, False otherwise.
        """
        with self._lock:
            return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if there are commands that can be redone.

        Returns:
            True if there are commands that can be redone, False otherwise.
        """
        with self._lock:
            return len(self._redo_stack) > 0

    def get_stats(self) -> dict[str, Any]:
        """Get command executor statistics.

        Returns:
            Dictionary of command executor statistics.
        """
        with self._lock:
            total_success = sum(1 for r in self._result_history if r.get("success", False))
            total_failure = len(self._result_history) - total_success

            return {
                "command_history_size": len(self._command_history),
                "result_history_size": len(self._result_history),
                "undo_stack_size": len(self._undo_stack),
                "redo_stack_size": len(self._redo_stack),
                "max_history": self._max_history,
                "total_success": total_success,
                "total_failure": total_failure,
                "success_rate": total_success / max(1, len(self._result_history)),
            }


def create_command_executor(max_history: int = CommandExecutor.MAX_HISTORY) -> CommandExecutor:
    """Create a new command executor.

    Args:
        max_history: Maximum number of commands to keep in history.

    Returns:
        A new CommandExecutor instance.
    """
    return CommandExecutor(max_history=max_history)


# Utility functions for creating commands


def create_function_command(
    func: Callable[..., T], *args: Any, **kwargs: Any
) -> FunctionCommand[T]:
    """Create a command that executes a function.

    Args:
        func: The function to execute.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.

    Returns:
        A FunctionCommand instance.
    """
    return FunctionCommand(func=func, args=args, kwargs=kwargs)


def create_composite_command(
    commands: list[Command], command_id: str | None = None
) -> CompositeCommand:
    """Create a command that executes multiple commands in sequence.

    Args:
        commands: The commands to execute in sequence.
        command_id: Optional unique identifier for this command.

    Returns:
        A CompositeCommand instance.
    """
    return CompositeCommand(commands=commands, command_id=command_id)


def undoable(executor: CommandExecutor):
    """Decorator to make a function undoable via the command system.

    Args:
        executor: The command executor to use.

    Returns:
        A decorator function.
    """

    def decorator(func):
        """Decorator to make a function undoable.

        Args:
            func: The function to decorate.

        Returns:
            The wrapped function.
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper to execute the function as a command.

            Args:
                *args: Arguments to pass to the function.
                **kwargs: Keyword arguments to pass to the function.

            Returns:
                The result of the function.
            """
            # Extract parameters for undo function
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())

            # Create parameter dict for undo function
            param_dict = {}

            # Add positional arguments
            for i, arg in enumerate(args):
                if i < len(param_names):
                    param_dict[param_names[i]] = arg

            # Add keyword arguments
            param_dict.update(kwargs)

            # Create state for undo
            orig_state = None

            # Find target object or module
            if args and hasattr(args[0], "__dict__"):
                # Instance method, capture original state
                target = args[0]
                orig_state = copy.deepcopy(target.__dict__)
            else:
                # Function or static method, try to find module state
                module = inspect.getmodule(func)
                if module:
                    orig_state = {
                        name: getattr(module, name)
                        for name in dir(module)
                        if not name.startswith("_") and not inspect.ismodule(getattr(module, name))
                    }

            # Create command
            command = create_function_command(func, *args, **kwargs)

            # Define undo function if we have original state
            if orig_state:

                def undo_func():
                    if args and hasattr(args[0], "__dict__"):
                        # Restore instance state
                        target = args[0]
                        target.__dict__.clear()
                        target.__dict__.update(orig_state)
                    else:
                        # Restore module state
                        module = inspect.getmodule(func)
                        if module:
                            for name, value in orig_state.items():
                                setattr(module, name, value)

                command.set_undo_func(undo_func)

            # Execute command via executor
            return executor.execute(command)

        return wrapper

    return decorator
