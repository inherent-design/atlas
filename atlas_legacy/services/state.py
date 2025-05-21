"""
State management with versioning and transitions.

This module provides a state management system with versioning, history tracking
and controlled transitions. It is designed to be thread-safe and support
validation of state transitions.
"""

import copy
import uuid
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from threading import RLock
from typing import Any, ClassVar, TypeAlias

from atlas.core.errors import AtlasError, ErrorCategory, ErrorSeverity
from atlas.core.logging import get_logger
from atlas.schemas.services import state_schema

# Type aliases for improved clarity
StateId: TypeAlias = str
TransitionId: TypeAlias = str
TransitionValidator: TypeAlias = Callable[[dict[str, Any], dict[str, Any]], bool]
StateData: TypeAlias = dict[str, Any]
TransitionMetadata: TypeAlias = dict[str, Any]

# Create a logger for this module
logger = get_logger(__name__)


# Custom error classes for the state system
class StateError(AtlasError):
    """Base class for state management errors."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
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
            category=ErrorCategory.DATA,
            details=details,
            cause=cause,
        )


class StateTransitionError(StateError):
    """Error related to state transitions."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        from_state: dict[str, Any] | None = None,
        to_state: dict[str, Any] | None = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            from_state: The original state.
            to_state: The target state.
        """
        details = details or {}

        if from_state:
            details["from_state"] = from_state

        if to_state:
            details["to_state"] = to_state

        super().__init__(
            message=message,
            details=details,
            cause=cause,
            severity=severity,
        )


class StateAccessError(StateError):
    """Error related to state access."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
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
            details=details,
            cause=cause,
            severity=severity,
        )


class StateTransition:
    """Represents a transition between two states."""

    def __init__(
        self,
        transition_id: str,
        from_state: dict[str, Any],
        to_state: dict[str, Any],
        validator: TransitionValidator | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize a new state transition.

        Args:
            transition_id: Unique identifier for this transition.
            from_state: The original state.
            to_state: The target state.
            validator: Optional function to validate the transition.
            metadata: Optional metadata about the transition.
        """
        self.transition_id = transition_id
        self.from_state = from_state
        self.to_state = to_state
        self.validator = validator
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

        logger.debug(
            f"Created transition {transition_id} from version "
            f"{from_state.get('version', 0)} to {to_state.get('version', 0)}"
        )

    def is_valid(self) -> bool:
        """Check if this transition is valid.

        Returns:
            True if the transition is valid, False otherwise.
        """
        if self.validator:
            try:
                return self.validator(self.from_state, self.to_state)
            except Exception as e:
                logger.error(
                    f"Error validating transition {self.transition_id}: {e}", exc_info=True
                )
                return False

        # Default to valid if no validator
        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert the transition to a dictionary.

        Returns:
            Dictionary representation of the transition.
        """
        return {
            "transition_id": self.transition_id,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "validator": self.validator.__name__ if self.validator else "none",
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


# Built-in validators for common transition scenarios
def always_valid(from_state: dict[str, Any], to_state: dict[str, Any]) -> bool:
    """Validator that always allows transitions.

    Args:
        from_state: The original state.
        to_state: The target state.

    Returns:
        Always True.
    """
    return True


def incremental_version(from_state: dict[str, Any], to_state: dict[str, Any]) -> bool:
    """Validator that ensures version increases by exactly 1.

    Args:
        from_state: The original state.
        to_state: The target state.

    Returns:
        True if the version increases by 1, False otherwise.
    """
    from_version = from_state.get("version", 0)
    to_version = to_state.get("version", 0)
    return to_version == from_version + 1


def no_empty_data(from_state: dict[str, Any], to_state: dict[str, Any]) -> bool:
    """Validator that ensures the state data is not empty.

    Args:
        from_state: The original state.
        to_state: The target state.

    Returns:
        True if the state data is not empty, False otherwise.
    """
    return bool(to_state.get("data", {}))


def field_exists(field_name: str) -> TransitionValidator:
    """Create a validator that ensures a field exists in the state.

    Args:
        field_name: The name of the field to check.

    Returns:
        A validator function.
    """

    def validator(from_state: dict[str, Any], to_state: dict[str, Any]) -> bool:
        """Validator that ensures a field exists in the state.

        Args:
            from_state: The original state.
            to_state: The target state.

        Returns:
            True if the field exists, False otherwise.
        """
        return field_name in to_state.get("data", {})

    return validator


def fields_unchanged(*field_names: str) -> TransitionValidator:
    """Create a validator that ensures specified fields don't change.

    Args:
        *field_names: The names of fields that should not change.

    Returns:
        A validator function.
    """

    def validator(from_state: dict[str, Any], to_state: dict[str, Any]) -> bool:
        """Validator that ensures specified fields don't change.

        Args:
            from_state: The original state.
            to_state: The target state.

        Returns:
            True if the fields are unchanged, False otherwise.
        """
        from_data = from_state.get("data", {})
        to_data = to_state.get("data", {})

        for field in field_names:
            if field in from_data and field in to_data:
                if from_data[field] != to_data[field]:
                    return False

        return True

    return validator


class StateContainer:
    """Thread-safe container for state with versioning and history."""

    # Class constants
    MAX_HISTORY: ClassVar[int] = 100

    def __init__(self, initial_state: dict[str, Any] | None = None, max_history: int = MAX_HISTORY):
        """Initialize a new state container.

        Args:
            initial_state: Optional initial state data.
            max_history: Maximum number of historical states to keep.
        """
        self._lock = RLock()
        self._max_history = max_history
        self._history: list[dict[str, Any]] = []
        self._transitions: list[StateTransition] = []

        # Create initial state
        initial_data = initial_state or {}

        try:
            # Validate using schema
            state_data = state_schema.load(
                {
                    "version": 1,
                    "data": initial_data,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {},
                }
            )

            # Add to history
            with self._lock:
                self._history.append(state_data)

            logger.debug(f"Created StateContainer with initial data: {initial_data}")

        except Exception as e:
            raise StateError(message=f"Failed to create state container: {e}", cause=e)

    @property
    def current_state(self) -> dict[str, Any]:
        """Get the current state.

        Returns:
            The current state data.
        """
        with self._lock:
            return copy.deepcopy(self._history[-1])

    @property
    def version(self) -> int:
        """Get the current state version.

        Returns:
            The current state version.
        """
        with self._lock:
            return self._history[-1].get("version", 1)

    @property
    def data(self) -> dict[str, Any]:
        """Get the current state data.

        Returns:
            The current state data.
        """
        with self._lock:
            return copy.deepcopy(self._history[-1].get("data", {}))

    def get_state(self, version: int | None = None) -> dict[str, Any]:
        """Get a specific state version.

        Args:
            version: The version to retrieve, or None for current.

        Returns:
            The state data for the specified version.

        Raises:
            StateAccessError: If the version doesn't exist.
        """
        with self._lock:
            if version is None:
                return copy.deepcopy(self._history[-1])

            for state in self._history:
                if state.get("version") == version:
                    return copy.deepcopy(state)

            raise StateAccessError(message=f"State version {version} not found in history")

    def get_field(self, field_name: str) -> Any:
        """Get a specific field from the current state.

        Args:
            field_name: The name of the field to retrieve.

        Returns:
            The field value, or None if not found.
        """
        with self._lock:
            data = self._history[-1].get("data", {})
            return copy.deepcopy(data.get(field_name))

    def has_field(self, field_name: str) -> bool:
        """Check if a field exists in the current state.

        Args:
            field_name: The name of the field to check.

        Returns:
            True if the field exists, False otherwise.
        """
        with self._lock:
            data = self._history[-1].get("data", {})
            return field_name in data

    def update(
        self,
        new_data: dict[str, Any],
        validator: TransitionValidator | None = None,
        metadata: dict[str, Any] | None = None,
        merge: bool = True,
    ) -> dict[str, Any]:
        """Update the state with new data.

        Args:
            new_data: The new state data.
            validator: Optional function to validate the transition.
            metadata: Optional metadata about the transition.
            merge: If True, merge with existing data; if False, replace.

        Returns:
            The new state after the update.

        Raises:
            StateTransitionError: If the transition is invalid.
        """
        with self._lock:
            # Get current state
            current_state = self._history[-1]
            current_version = current_state.get("version", 1)
            current_data = current_state.get("data", {})

            # Prepare new state
            if merge:
                # Merge with existing data
                merged_data = copy.deepcopy(current_data)
                merged_data.update(new_data)
                new_state_data = merged_data
            else:
                # Replace existing data
                new_state_data = new_data

            # Create new state
            try:
                new_state = state_schema.load(
                    {
                        "version": current_version + 1,
                        "data": new_state_data,
                        "timestamp": datetime.now().isoformat(),
                        "metadata": metadata or {},
                    }
                )

                # Create transition
                transition = StateTransition(
                    transition_id=str(uuid.uuid4()),
                    from_state=current_state,
                    to_state=new_state,
                    validator=validator,
                    metadata=metadata,
                )

                # Validate transition
                if not transition.is_valid():
                    raise StateTransitionError(
                        message="Invalid state transition",
                        from_state=current_state,
                        to_state=new_state,
                    )

                # Apply transition
                self._history.append(new_state)
                self._transitions.append(transition)

                # Trim history if needed
                if len(self._history) > self._max_history:
                    self._history = self._history[-self._max_history :]

                logger.debug(
                    f"Updated state to version {new_state.get('version')} "
                    f"with transition {transition.transition_id}"
                )

                return copy.deepcopy(new_state)

            except StateTransitionError:
                # Re-raise transition errors
                raise

            except Exception as e:
                raise StateError(message=f"Failed to update state: {e}", cause=e)

    def update_field(
        self,
        field_name: str,
        value: Any,
        validator: TransitionValidator | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update a single field in the state.

        Args:
            field_name: The name of the field to update.
            value: The new value for the field.
            validator: Optional function to validate the transition.
            metadata: Optional metadata about the transition.

        Returns:
            The new state after the update.

        Raises:
            StateTransitionError: If the transition is invalid.
        """
        # Create a new data dictionary with just this field
        new_data = {field_name: value}

        # Update with merge=True to preserve other fields
        return self.update(new_data=new_data, validator=validator, metadata=metadata, merge=True)

    def rollback(self, version: int) -> dict[str, Any]:
        """Rollback to a previous version.

        Args:
            version: The version to rollback to.

        Returns:
            The state after rollback.

        Raises:
            StateAccessError: If the version doesn't exist.
            StateTransitionError: If the rollback is invalid.
        """
        with self._lock:
            # Find the target state
            target_state = None
            for state in self._history:
                if state.get("version") == version:
                    target_state = state
                    break

            if not target_state:
                raise StateAccessError(message=f"State version {version} not found in history")

            # Create a new state based on the target
            current_state = self._history[-1]
            current_version = current_state.get("version", 1)

            try:
                # Create rollback state with incremented version
                rollback_data = copy.deepcopy(target_state.get("data", {}))

                new_state = state_schema.load(
                    {
                        "version": current_version + 1,
                        "data": rollback_data,
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {
                            "rollback": True,
                            "rollback_from": current_version,
                            "rollback_to": version,
                        },
                    }
                )

                # Create transition
                transition = StateTransition(
                    transition_id=str(uuid.uuid4()),
                    from_state=current_state,
                    to_state=new_state,
                    validator=None,  # No validation for rollbacks
                    metadata={
                        "rollback": True,
                        "rollback_from": current_version,
                        "rollback_to": version,
                    },
                )

                # Apply transition
                self._history.append(new_state)
                self._transitions.append(transition)

                # Trim history if needed
                if len(self._history) > self._max_history:
                    self._history = self._history[-self._max_history :]

                logger.debug(
                    f"Rolled back state from version {current_version} to {version}, "
                    f"new version is {new_state.get('version')}"
                )

                return copy.deepcopy(new_state)

            except Exception as e:
                raise StateError(message=f"Failed to rollback state: {e}", cause=e)

    def get_history(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Get the state history.

        Args:
            limit: Maximum number of historical states to return.

        Returns:
            List of historical states, oldest first.
        """
        with self._lock:
            history = copy.deepcopy(self._history)

            if limit:
                history = history[-limit:]

            return history

    def get_transitions(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Get the transition history.

        Args:
            limit: Maximum number of transitions to return.

        Returns:
            List of transitions, oldest first.
        """
        with self._lock:
            transitions = [t.to_dict() for t in self._transitions]

            if limit:
                transitions = transitions[-limit:]

            return transitions

    def clear_history(self, keep_current: bool = True) -> None:
        """Clear the state history.

        Args:
            keep_current: If True, keep the current state.
        """
        with self._lock:
            if keep_current:
                current = self._history[-1]
                self._history = [current]
                self._transitions = []
            else:
                self._history = []
                self._transitions = []

            logger.debug("Cleared state history")

    def snapshot(self) -> dict[str, Any]:
        """Create a complete snapshot of the state container.

        Returns:
            Dictionary containing the complete state.
        """
        with self._lock:
            return {
                "current_state": copy.deepcopy(self._history[-1]),
                "history": copy.deepcopy(self._history),
                "transitions": [t.to_dict() for t in self._transitions],
                "max_history": self._max_history,
                "version_count": len(self._history),
                "transition_count": len(self._transitions),
            }

    def restore(self, snapshot: dict[str, Any]) -> None:
        """Restore state from a snapshot.

        Args:
            snapshot: A snapshot created by the snapshot method.

        Raises:
            StateError: If the snapshot is invalid.
        """
        try:
            # Validate snapshot
            if "current_state" not in snapshot or "history" not in snapshot:
                raise StateError(message="Invalid snapshot: missing required fields")

            # Create transitions from snapshot
            transitions = []
            for t_data in snapshot.get("transitions", []):
                if not isinstance(t_data, dict):
                    continue

                transition = StateTransition(
                    transition_id=t_data.get("transition_id", str(uuid.uuid4())),
                    from_state=t_data.get("from_state", {}),
                    to_state=t_data.get("to_state", {}),
                    validator=None,  # Can't restore validator functions
                    metadata=t_data.get("metadata", {}),
                )
                transitions.append(transition)

            # Apply snapshot
            with self._lock:
                self._history = snapshot.get("history", [])
                self._transitions = transitions
                self._max_history = snapshot.get("max_history", self.MAX_HISTORY)

            logger.debug(
                f"Restored state from snapshot with {len(self._history)} "
                f"historical states and {len(self._transitions)} transitions"
            )

        except Exception as e:
            raise StateError(message=f"Failed to restore state from snapshot: {e}", cause=e)


def create_state_container(
    initial_state: dict[str, Any] | None = None, max_history: int = StateContainer.MAX_HISTORY
) -> StateContainer:
    """Create a new state container.

    Args:
        initial_state: Optional initial state data.
        max_history: Maximum number of historical states to keep.

    Returns:
        A new StateContainer instance.
    """
    return StateContainer(initial_state=initial_state, max_history=max_history)


# State decorators
def track_state_changes(state_container: StateContainer, field_name: str | None = None):
    """Decorator to track changes to state from a function.

    Args:
        state_container: The state container to update.
        field_name: Optional specific field to update in the state.

    Returns:
        A decorator function.
    """

    def decorator(func):
        """Decorator to track changes to state from a function.

        Args:
            func: The function to decorate.

        Returns:
            The wrapped function.
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper to call the function and update state.

            Args:
                *args: Arguments to pass to the function.
                **kwargs: Keyword arguments to pass to the function.

            Returns:
                The result of the function.
            """
            result = func(*args, **kwargs)

            # Update state
            if field_name:
                # Update specific field
                state_container.update_field(
                    field_name=field_name,
                    value=result,
                    metadata={"function": func.__name__, "timestamp": datetime.now().isoformat()},
                )
            else:
                # Try to update with result if it's a dict
                if isinstance(result, dict):
                    state_container.update(
                        new_data=result,
                        metadata={
                            "function": func.__name__,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )
                else:
                    # Otherwise, update with a result field
                    state_container.update(
                        new_data={"result": result},
                        metadata={
                            "function": func.__name__,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )

            return result

        return wrapper

    return decorator


def require_state_field(
    state_container: StateContainer,
    field_name: str,
    validator: Callable[[Any], bool] | None = None,
    error_message: str | None = None,
):
    """Decorator to require a field in the state.

    Args:
        state_container: The state container to check.
        field_name: The name of the field to require.
        validator: Optional function to validate the field value.
        error_message: Optional custom error message.

    Returns:
        A decorator function.
    """

    def decorator(func):
        """Decorator to require a field in the state.

        Args:
            func: The function to decorate.

        Returns:
            The wrapped function.
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper to check state field and call the function.

            Args:
                *args: Arguments to pass to the function.
                **kwargs: Keyword arguments to pass to the function.

            Returns:
                The result of the function.

            Raises:
                StateAccessError: If the field is missing or invalid.
            """
            # Check if field exists
            if not state_container.has_field(field_name):
                msg = error_message or f"Required state field '{field_name}' is missing"
                raise StateAccessError(message=msg)

            # Validate field value if validator provided
            if validator:
                field_value = state_container.get_field(field_name)
                if not validator(field_value):
                    msg = error_message or f"State field '{field_name}' failed validation"
                    raise StateAccessError(message=msg)

            # Call function
            return func(*args, **kwargs)

        return wrapper

    return decorator
