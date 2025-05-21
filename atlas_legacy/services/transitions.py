"""
State transition validators and transition rule system.

This module provides a comprehensive system for validating state transitions,
including predefined validators, composite validators, and a rule-based transition
system for defining valid state transitions between different states.
"""

from collections.abc import Callable
from typing import Any, TypeAlias

from atlas.core.errors import AtlasError, ErrorCategory, ErrorSeverity
from atlas.core.logging import get_logger

# Type aliases for improved clarity
StateData: TypeAlias = dict[str, Any]
TransitionValidator: TypeAlias = Callable[[dict[str, Any], dict[str, Any]], bool]
TransitionRule: TypeAlias = dict[str, Any]
ValidationResult: TypeAlias = tuple[bool, str | None]

# Create a logger for this module
logger = get_logger(__name__)


class TransitionError(AtlasError):
    """Error related to transition validation."""

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


class ValidatorResult:
    """Container for validation results with explanation."""

    def __init__(self, is_valid: bool, reason: str | None = None):
        """Initialize validation result.

        Args:
            is_valid: Whether the validation passed.
            reason: Optional explanation for the result.
        """
        self.is_valid = is_valid
        self.reason = reason

    def __bool__(self) -> bool:
        """Boolean representation of result.

        Returns:
            True if validation passed, False otherwise.
        """
        return self.is_valid


class StateTransitionValidator:
    """Validator for state transitions with composite logic support."""

    def __init__(
        self,
        name: str,
        validator_func: TransitionValidator | None = None,
        description: str | None = None,
    ):
        """Initialize a state transition validator.

        Args:
            name: Unique name for this validator.
            validator_func: Optional validation function.
            description: Optional description of this validator.
        """
        self.name = name
        self.validator_func = validator_func
        self.description = description or f"Validator {name}"

    def validate(self, from_state: dict[str, Any], to_state: dict[str, Any]) -> ValidatorResult:
        """Validate a state transition.

        Args:
            from_state: The original state.
            to_state: The target state.

        Returns:
            ValidatorResult containing validation result and reason.
        """
        if self.validator_func is None:
            return ValidatorResult(True, f"No validation function defined for {self.name}")

        try:
            is_valid = self.validator_func(from_state, to_state)
            return ValidatorResult(
                is_valid, f"Validation {'succeeded' if is_valid else 'failed'} for {self.name}"
            )
        except Exception as e:
            logger.error(f"Error in validator {self.name}: {e}", exc_info=True)
            return ValidatorResult(False, f"Validator {self.name} raised an exception: {e}")

    def __and__(self, other: "StateTransitionValidator") -> "CompositeValidator":
        """Create an AND validator with another validator.

        Args:
            other: Another validator to combine with this one using AND logic.

        Returns:
            A composite validator that passes only if both validators pass.
        """
        return CompositeValidator(
            name=f"{self.name}_AND_{other.name}", validators=[self, other], operator="AND"
        )

    def __or__(self, other: "StateTransitionValidator") -> "CompositeValidator":
        """Create an OR validator with another validator.

        Args:
            other: Another validator to combine with this one using OR logic.

        Returns:
            A composite validator that passes if either validator passes.
        """
        return CompositeValidator(
            name=f"{self.name}_OR_{other.name}", validators=[self, other], operator="OR"
        )

    def __invert__(self) -> "NotValidator":
        """Create a NOT validator that inverts this validator's result.

        Returns:
            A validator that passes if this validator fails.
        """
        return NotValidator(self)


class CompositeValidator(StateTransitionValidator):
    """Validator that combines multiple validators with logical operations."""

    def __init__(
        self,
        name: str,
        validators: list[StateTransitionValidator],
        operator: str = "AND",
        description: str | None = None,
    ):
        """Initialize a composite validator.

        Args:
            name: Unique name for this validator.
            validators: List of validators to combine.
            operator: Logical operator to apply ("AND" or "OR").
            description: Optional description of this validator.
        """
        super().__init__(name=name, description=description)
        self.validators = validators
        self.operator = operator.upper()

        if self.operator not in ["AND", "OR"]:
            raise ValueError(f"Invalid operator {operator}, must be 'AND' or 'OR'")

    def validate(self, from_state: dict[str, Any], to_state: dict[str, Any]) -> ValidatorResult:
        """Validate a state transition using composite logic.

        Args:
            from_state: The original state.
            to_state: The target state.

        Returns:
            ValidatorResult containing validation result and reason.
        """
        results = []
        reasons = []

        for validator in self.validators:
            result = validator.validate(from_state, to_state)
            results.append(result.is_valid)
            reasons.append(result.reason)

        if self.operator == "AND":
            is_valid = all(results)
            reason = "\n".join(reasons)
            return ValidatorResult(is_valid, reason)
        else:  # OR
            is_valid = any(results)
            reason = "\n".join(reasons)
            return ValidatorResult(is_valid, reason)


class NotValidator(StateTransitionValidator):
    """Validator that inverts the result of another validator."""

    def __init__(self, validator: StateTransitionValidator):
        """Initialize a NOT validator.

        Args:
            validator: The validator to invert.
        """
        super().__init__(
            name=f"NOT_{validator.name}", description=f"Inverted validator for {validator.name}"
        )
        self.validator = validator

    def validate(self, from_state: dict[str, Any], to_state: dict[str, Any]) -> ValidatorResult:
        """Validate a state transition by inverting another validator's result.

        Args:
            from_state: The original state.
            to_state: The target state.

        Returns:
            ValidatorResult containing the inverted validation result.
        """
        result = self.validator.validate(from_state, to_state)
        return ValidatorResult(
            not result.is_valid, f"Inverted result of {self.validator.name}: {result.reason}"
        )


# Built-in validators
def create_always_valid_validator() -> StateTransitionValidator:
    """Create a validator that always passes.

    Returns:
        A validator that always returns True.
    """
    return StateTransitionValidator(
        name="always_valid",
        validator_func=lambda from_state, to_state: True,
        description="Validator that always passes",
    )


def create_incremental_version_validator() -> StateTransitionValidator:
    """Create a validator that ensures version increments by exactly 1.

    Returns:
        A validator for version increments.
    """

    def validator(from_state: dict[str, Any], to_state: dict[str, Any]) -> bool:
        from_version = from_state.get("version", 0)
        to_version = to_state.get("version", 0)
        return to_version == from_version + 1

    return StateTransitionValidator(
        name="incremental_version",
        validator_func=validator,
        description="Validator that ensures version increments by exactly 1",
    )


def create_non_empty_data_validator() -> StateTransitionValidator:
    """Create a validator that ensures state data is not empty.

    Returns:
        A validator that checks for non-empty data.
    """

    def validator(from_state: dict[str, Any], to_state: dict[str, Any]) -> bool:
        return bool(to_state.get("data", {}))

    return StateTransitionValidator(
        name="non_empty_data",
        validator_func=validator,
        description="Validator that ensures state data is not empty",
    )


def create_field_exists_validator(field_name: str) -> StateTransitionValidator:
    """Create a validator that ensures a specific field exists in the state.

    Args:
        field_name: The name of the field that must exist.

    Returns:
        A validator that checks for field existence.
    """

    def validator(from_state: dict[str, Any], to_state: dict[str, Any]) -> bool:
        return field_name in to_state.get("data", {})

    return StateTransitionValidator(
        name=f"field_exists_{field_name}",
        validator_func=validator,
        description=f"Validator that ensures field '{field_name}' exists in state",
    )


def create_fields_unchanged_validator(*field_names: str) -> StateTransitionValidator:
    """Create a validator that ensures specified fields don't change.

    Args:
        *field_names: Names of fields that should remain unchanged.

    Returns:
        A validator that checks for unchanged fields.
    """

    def validator(from_state: dict[str, Any], to_state: dict[str, Any]) -> bool:
        from_data = from_state.get("data", {})
        to_data = to_state.get("data", {})

        for field in field_names:
            if field in from_data and field in to_data:
                if from_data[field] != to_data[field]:
                    return False

        return True

    field_list = "_".join(str(name) for name in field_names)

    return StateTransitionValidator(
        name=f"fields_unchanged_{field_list}",
        validator_func=validator,
        description=f"Validator that ensures fields {field_names} remain unchanged",
    )


def create_field_changed_validator(field_name: str) -> StateTransitionValidator:
    """Create a validator that ensures a field has changed.

    Args:
        field_name: The name of the field that must change.

    Returns:
        A validator that checks if a field has changed.
    """

    def validator(from_state: dict[str, Any], to_state: dict[str, Any]) -> bool:
        from_data = from_state.get("data", {})
        to_data = to_state.get("data", {})

        # Field must exist in both states and be different
        return (
            field_name in from_data
            and field_name in to_data
            and from_data[field_name] != to_data[field_name]
        )

    return StateTransitionValidator(
        name=f"field_changed_{field_name}",
        validator_func=validator,
        description=f"Validator that ensures field '{field_name}' has changed",
    )


def create_state_transition_validator(
    name: str, validator_func: TransitionValidator
) -> StateTransitionValidator:
    """Create a custom validator with the given name and validation function.

    Args:
        name: Unique name for the validator.
        validator_func: Function that performs the validation.

    Returns:
        A configured validator with the custom logic.
    """
    return StateTransitionValidator(
        name=name, validator_func=validator_func, description=f"Custom validator {name}"
    )


class TransitionRegistry:
    """Registry for state transition validators and rules."""

    def __init__(self):
        """Initialize the transition registry."""
        self._validators: dict[str, StateTransitionValidator] = {}
        self._transition_rules: dict[str, dict[str, list[StateTransitionValidator]]] = {}

        # Register built-in validators
        self.register_validator(create_always_valid_validator())
        self.register_validator(create_incremental_version_validator())
        self.register_validator(create_non_empty_data_validator())

    def register_validator(self, validator: StateTransitionValidator) -> None:
        """Register a validator in the registry.

        Args:
            validator: The validator to register.

        Raises:
            TransitionError: If a validator with the same name already exists.
        """
        if validator.name in self._validators:
            raise TransitionError(message=f"Validator {validator.name} already registered")

        self._validators[validator.name] = validator
        logger.debug(f"Registered validator: {validator.name}")

    def get_validator(self, name: str) -> StateTransitionValidator | None:
        """Get a validator by name.

        Args:
            name: The name of the validator to retrieve.

        Returns:
            The validator if found, None otherwise.
        """
        return self._validators.get(name)

    def register_transition_rule(
        self, from_state: str, to_state: str, validator: str | StateTransitionValidator
    ) -> None:
        """Register a transition rule between two states.

        Args:
            from_state: The source state name.
            to_state: The target state name.
            validator: The validator to use for this transition (name or instance).

        Raises:
            TransitionError: If the validator doesn't exist.
        """
        # Get validator instance
        if isinstance(validator, str):
            validator_instance = self.get_validator(validator)
            if not validator_instance:
                raise TransitionError(message=f"Validator {validator} not found in registry")
        else:
            validator_instance = validator
            # Auto-register if not already registered
            if validator_instance.name not in self._validators:
                self.register_validator(validator_instance)

        # Initialize state transitions if needed
        if from_state not in self._transition_rules:
            self._transition_rules[from_state] = {}

        if to_state not in self._transition_rules[from_state]:
            self._transition_rules[from_state][to_state] = []

        # Add validator to this transition
        self._transition_rules[from_state][to_state].append(validator_instance)

        logger.debug(
            f"Registered transition rule: {from_state} -> {to_state} "
            f"with validator {validator_instance.name}"
        )

    def get_transition_validators(
        self, from_state: str, to_state: str
    ) -> list[StateTransitionValidator]:
        """Get validators for a specific transition.

        Args:
            from_state: The source state name.
            to_state: The target state name.

        Returns:
            List of validators for this transition.
        """
        if from_state in self._transition_rules and to_state in self._transition_rules[from_state]:
            return self._transition_rules[from_state][to_state]
        else:
            # If wildcard rules exist, return those
            wildcard_validators = []

            # Check for "any -> specific" rules
            if "*" in self._transition_rules and to_state in self._transition_rules["*"]:
                wildcard_validators.extend(self._transition_rules["*"][to_state])

            # Check for "specific -> any" rules
            if from_state in self._transition_rules and "*" in self._transition_rules[from_state]:
                wildcard_validators.extend(self._transition_rules[from_state]["*"])

            # Check for "any -> any" rules
            if "*" in self._transition_rules and "*" in self._transition_rules["*"]:
                wildcard_validators.extend(self._transition_rules["*"]["*"])

            return wildcard_validators

    def validate_transition(
        self,
        from_state_name: str,
        to_state_name: str,
        from_state: dict[str, Any],
        to_state: dict[str, Any],
    ) -> tuple[bool, str]:
        """Validate a state transition using registered rules.

        Args:
            from_state_name: The source state name.
            to_state_name: The target state name.
            from_state: The source state data.
            to_state: The target state data.

        Returns:
            Tuple of (is_valid, reason).
        """
        validators = self.get_transition_validators(from_state_name, to_state_name)

        if not validators:
            # No rules specified, use the default increment validator
            increment_validator = self.get_validator("incremental_version")
            if increment_validator:
                result = increment_validator.validate(from_state, to_state)
                return result.is_valid, result.reason
            else:
                # If even the default validator is missing, allow the transition
                return True, "No transition rules found, allowing by default"

        # Apply all validators
        all_valid = True
        reasons = []

        for validator in validators:
            result = validator.validate(from_state, to_state)
            if not result.is_valid:
                all_valid = False
                reasons.append(result.reason)

        if not all_valid:
            return False, "\n".join(reasons)
        else:
            return True, "All validators passed"

    def get_allowed_transitions(self, from_state: str) -> set[str]:
        """Get all allowed transition target states from a source state.

        Args:
            from_state: The source state name.

        Returns:
            Set of allowed target state names.
        """
        allowed: set[str] = set()

        # Add specific transitions for this state
        if from_state in self._transition_rules:
            allowed.update(self._transition_rules[from_state].keys())

        # Add wildcard transitions
        if "*" in self._transition_rules:
            allowed.update(self._transition_rules["*"].keys())

        # Remove the wildcard itself if present
        if "*" in allowed:
            allowed.remove("*")

        return allowed


# Create the global transition registry
def create_transition_registry() -> TransitionRegistry:
    """Create and initialize the global transition registry.

    Returns:
        Initialized transition registry with default validators.
    """
    registry = TransitionRegistry()

    # Add additional built-in validators
    registry.register_validator(create_field_exists_validator("status"))
    registry.register_validator(create_field_exists_validator("metadata"))

    # Create some common transitions
    # For example, status transitions
    registry.register_transition_rule("initializing", "running", "incremental_version")
    registry.register_transition_rule("running", "paused", "incremental_version")
    registry.register_transition_rule("paused", "running", "incremental_version")
    registry.register_transition_rule("running", "stopped", "incremental_version")

    # Allow any status to transition to error
    registry.register_transition_rule("*", "error", "incremental_version")

    return registry


# Global registry instance
_transition_registry = None


def get_transition_registry() -> TransitionRegistry:
    """Get the global transition registry, creating it if needed.

    Returns:
        The global transition registry.
    """
    global _transition_registry

    if _transition_registry is None:
        _transition_registry = create_transition_registry()

    return _transition_registry
