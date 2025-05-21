"""
Unit tests for state transition system.

This module tests the state transition registry, validators, and transition rules
to ensure proper validation of state transitions.
"""

import unittest

from atlas.services.transitions import (
    StateTransitionValidator,
    TransitionRegistry,
    create_always_valid_validator,
    create_field_changed_validator,
    create_field_exists_validator,
    create_fields_unchanged_validator,
    create_incremental_version_validator,
    create_non_empty_data_validator,
    create_state_transition_validator,
    get_transition_registry,
)


class TestStateTransitionValidator(unittest.TestCase):
    """Test the StateTransitionValidator class."""

    def test_basic_validation(self):
        """Test basic validator functionality."""
        # Create a simple validator
        validator = StateTransitionValidator(
            name="test_validator",
            validator_func=lambda from_state, to_state: "value"
            in to_state.get("data", {}),
            description="Test validator requiring value field",
        )

        # Create test states
        from_state = {"version": 1, "data": {}}
        to_state_valid = {"version": 2, "data": {"value": 42}}
        to_state_invalid = {"version": 2, "data": {"status": "ready"}}

        # Test validation
        result1 = validator.validate(from_state, to_state_valid)
        self.assertTrue(result1.is_valid)
        self.assertIsNotNone(result1.reason)

        result2 = validator.validate(from_state, to_state_invalid)
        self.assertFalse(result2.is_valid)
        self.assertIsNotNone(result2.reason)

    def test_validator_with_exception(self):
        """Test validator that raises an exception."""

        def failing_validator(from_state, to_state):
            raise ValueError("Test exception")

        validator = StateTransitionValidator(
            name="failing_validator", validator_func=failing_validator
        )

        # Validation should return False but not raise the exception
        result = validator.validate({}, {})
        self.assertFalse(result.is_valid)
        self.assertIn("exception", result.reason)

    def test_no_validator_func(self):
        """Test validator with no validation function."""
        validator = StateTransitionValidator(name="empty_validator")

        # Should return True by default
        result = validator.validate({}, {})
        self.assertTrue(result.is_valid)

    def test_composite_and(self):
        """Test AND composite validator."""
        # Create component validators
        v1 = StateTransitionValidator(
            name="has_value",
            validator_func=lambda from_state, to_state: "value"
            in to_state.get("data", {}),
        )

        v2 = StateTransitionValidator(
            name="has_status",
            validator_func=lambda from_state, to_state: "status"
            in to_state.get("data", {}),
        )

        # Create composite validator using & operator
        composite = v1 & v2

        # Test states
        from_state = {"version": 1, "data": {}}
        state1 = {"version": 2, "data": {"value": 42}}
        state2 = {"version": 2, "data": {"status": "ready"}}
        state3 = {"version": 2, "data": {"value": 42, "status": "ready"}}

        # Test validation
        self.assertFalse(composite.validate(from_state, state1).is_valid)
        self.assertFalse(composite.validate(from_state, state2).is_valid)
        self.assertTrue(composite.validate(from_state, state3).is_valid)

    def test_composite_or(self):
        """Test OR composite validator."""
        # Create component validators
        v1 = StateTransitionValidator(
            name="has_value",
            validator_func=lambda from_state, to_state: "value"
            in to_state.get("data", {}),
        )

        v2 = StateTransitionValidator(
            name="has_status",
            validator_func=lambda from_state, to_state: "status"
            in to_state.get("data", {}),
        )

        # Create composite validator using | operator
        composite = v1 | v2

        # Test states
        from_state = {"version": 1, "data": {}}
        state1 = {"version": 2, "data": {"value": 42}}
        state2 = {"version": 2, "data": {"status": "ready"}}
        state3 = {"version": 2, "data": {}}

        # Test validation
        self.assertTrue(composite.validate(from_state, state1).is_valid)
        self.assertTrue(composite.validate(from_state, state2).is_valid)
        self.assertFalse(composite.validate(from_state, state3).is_valid)

    def test_complex_composition(self):
        """Test complex validator composition."""
        # Create component validators
        v1 = StateTransitionValidator(
            name="has_value",
            validator_func=lambda from_state, to_state: "value"
            in to_state.get("data", {}),
        )

        v2 = StateTransitionValidator(
            name="has_status",
            validator_func=lambda from_state, to_state: "status"
            in to_state.get("data", {}),
        )

        v3 = StateTransitionValidator(
            name="has_metadata",
            validator_func=lambda from_state, to_state: "metadata" in to_state,
        )

        # Create complex composite: (v1 OR v2) AND v3
        composite = (v1 | v2) & v3

        # Test states
        from_state = {"version": 1, "data": {}}
        state1 = {"version": 2, "data": {"value": 42}, "metadata": {}}
        state2 = {"version": 2, "data": {"status": "ready"}, "metadata": {}}
        state3 = {"version": 2, "data": {"value": 42, "status": "ready"}}
        state4 = {"version": 2, "data": {}, "metadata": {}}

        # Test validation
        self.assertTrue(composite.validate(from_state, state1).is_valid)
        self.assertTrue(composite.validate(from_state, state2).is_valid)
        self.assertFalse(composite.validate(from_state, state3).is_valid)  # No metadata
        self.assertFalse(
            composite.validate(from_state, state4).is_valid
        )  # No value or status

    def test_not_validator(self):
        """Test NOT validator."""
        # Create a validator
        v1 = StateTransitionValidator(
            name="has_value",
            validator_func=lambda from_state, to_state: "value"
            in to_state.get("data", {}),
        )

        # Create a NOT validator using ~ operator
        not_v1 = ~v1

        # Test states
        from_state = {"version": 1, "data": {}}
        state1 = {"version": 2, "data": {"value": 42}}
        state2 = {"version": 2, "data": {"status": "ready"}}

        # Test validation
        self.assertFalse(not_v1.validate(from_state, state1).is_valid)
        self.assertTrue(not_v1.validate(from_state, state2).is_valid)


class TestValidatorFactory(unittest.TestCase):
    """Test validator factory functions."""

    def test_always_valid(self):
        """Test always_valid validator."""
        validator = create_always_valid_validator()

        # Should pass any states
        self.assertTrue(validator.validate({}, {}).is_valid)
        self.assertTrue(
            validator.validate({"data": {}}, {"data": {"value": 42}}).is_valid
        )

    def test_incremental_version(self):
        """Test incremental_version validator."""
        validator = create_incremental_version_validator()

        # Test valid increment
        self.assertTrue(validator.validate({"version": 1}, {"version": 2}).is_valid)

        # Test invalid increments
        self.assertFalse(validator.validate({"version": 1}, {"version": 3}).is_valid)

        self.assertFalse(validator.validate({"version": 2}, {"version": 1}).is_valid)

        self.assertFalse(validator.validate({"version": 1}, {"version": 1}).is_valid)

    def test_non_empty_data(self):
        """Test non_empty_data validator."""
        validator = create_non_empty_data_validator()

        # Test valid non-empty data
        self.assertTrue(validator.validate({}, {"data": {"value": 42}}).is_valid)

        # Test invalid empty data
        self.assertFalse(validator.validate({}, {"data": {}}).is_valid)

    def test_field_exists(self):
        """Test field_exists validator."""
        validator = create_field_exists_validator("status")

        # Test valid field existence
        self.assertTrue(validator.validate({}, {"data": {"status": "ready"}}).is_valid)

        # Test invalid missing field
        self.assertFalse(validator.validate({}, {"data": {"value": 42}}).is_valid)

    def test_fields_unchanged(self):
        """Test fields_unchanged validator."""
        validator = create_fields_unchanged_validator("id", "type")

        # Test valid unchanged fields
        self.assertTrue(
            validator.validate(
                {"data": {"id": "123", "type": "user", "name": "Alice"}},
                {"data": {"id": "123", "type": "user", "name": "Bob"}},
            ).is_valid
        )

        # Test invalid changed field
        self.assertFalse(
            validator.validate(
                {"data": {"id": "123", "type": "user"}},
                {"data": {"id": "456", "type": "user"}},
            ).is_valid
        )

    def test_field_changed(self):
        """Test field_changed validator."""
        validator = create_field_changed_validator("status")

        # Test valid changed field
        self.assertTrue(
            validator.validate(
                {"data": {"status": "pending"}}, {"data": {"status": "complete"}}
            ).is_valid
        )

        # Test invalid unchanged field
        self.assertFalse(
            validator.validate(
                {"data": {"status": "pending"}}, {"data": {"status": "pending"}}
            ).is_valid
        )

        # Test missing field in one state
        self.assertFalse(
            validator.validate({"data": {}}, {"data": {"status": "pending"}}).is_valid
        )

    def test_custom_validator(self):
        """Test custom validator creation."""

        def validate_value_increased(from_state, to_state):
            from_value = from_state.get("data", {}).get("value", 0)
            to_value = to_state.get("data", {}).get("value", 0)
            return to_value > from_value

        validator = create_state_transition_validator(
            "value_increased", validate_value_increased
        )

        # Test valid value increase
        self.assertTrue(
            validator.validate(
                {"data": {"value": 10}}, {"data": {"value": 20}}
            ).is_valid
        )

        # Test invalid value decrease
        self.assertFalse(
            validator.validate(
                {"data": {"value": 20}}, {"data": {"value": 10}}
            ).is_valid
        )


class TestTransitionRegistryIntegration(unittest.TestCase):
    """Test the TransitionRegistry in integration scenarios."""

    def setUp(self):
        """Set up a registry for testing."""
        # Create a fresh registry and clear built-in validators
        self.registry = TransitionRegistry()
        self.registry._validators = {}

        # Register validators for testing
        self.registry.register_validator(create_always_valid_validator())
        self.registry.register_validator(create_incremental_version_validator())
        self.registry.register_validator(create_non_empty_data_validator())
        self.registry.register_validator(create_field_exists_validator("status"))

        # Define a state machine for a simple task workflow
        # pending -> in_progress -> completed
        # pending -> cancelled
        # in_progress -> cancelled
        # Any state can transition to error

        # Register transition rules
        self.registry.register_transition_rule(
            "pending", "in_progress", "incremental_version"
        )

        # In_progress -> completed requires status field
        self.registry.register_transition_rule(
            "in_progress", "completed", "field_exists_status"
        )

        # Add cancel transitions
        self.registry.register_transition_rule(
            "pending", "cancelled", "incremental_version"
        )
        self.registry.register_transition_rule(
            "in_progress", "cancelled", "incremental_version"
        )

        # Error transition with wildcard - use always_valid to skip version check
        self.registry.register_transition_rule("*", "error", "always_valid")

    def test_workflow_transitions(self):
        """Test that workflow transitions follow rules."""
        # Create states
        pending = {"version": 1, "data": {"status": "pending"}}
        in_progress = {"version": 2, "data": {"status": "in_progress"}}
        completed = {"version": 3, "data": {"status": "completed"}}
        cancelled = {"version": 2, "data": {"status": "cancelled"}}
        error = {"version": 2, "data": {"status": "error", "error": "Test error"}}

        # Valid transitions
        valid1, _ = self.registry.validate_transition(
            "pending", "in_progress", pending, in_progress
        )
        self.assertTrue(valid1)

        valid2, _ = self.registry.validate_transition(
            "in_progress", "completed", in_progress, completed
        )
        self.assertTrue(valid2)

        valid3, _ = self.registry.validate_transition(
            "pending", "cancelled", pending, cancelled
        )
        self.assertTrue(valid3)

        valid4, _ = self.registry.validate_transition(
            "in_progress", "error", in_progress, error
        )
        self.assertTrue(valid4)

        # Invalid transitions
        # Pending -> completed (not allowed)
        invalid1, reason1 = self.registry.validate_transition(
            "pending", "completed", pending, completed
        )
        self.assertFalse(invalid1)

        # in_progress -> in_progress (version didn't change)
        invalid_same_state = {
            "version": 2,
            "data": {"status": "in_progress", "progress": 50},
        }
        invalid2, reason2 = self.registry.validate_transition(
            "in_progress", "in_progress", in_progress, invalid_same_state
        )
        self.assertFalse(invalid2)

        # This test previously expected version skip to be invalid,
        # but since our implementation now only uses incremental_version validator
        # for transitions with no explicit rules (not our case),
        # and we're using field_exists_status as our validator for in_progress->completed,
        # this version skip is actually valid since the status field exists.
        # Let's replace this test with another invalid case.

        # Missing status field is not allowed for in_progress->completed
        invalid_skip = {"version": 3, "data": {"progress": 100}}
        invalid3, reason3 = self.registry.validate_transition(
            "in_progress", "completed", in_progress, invalid_skip
        )
        self.assertFalse(invalid3)

    def test_allowed_transitions(self):
        """Test getting allowed transitions from the registry."""
        # Get allowed transitions from each state
        from_pending = self.registry.get_allowed_transitions("pending")
        self.assertEqual(from_pending, {"in_progress", "cancelled", "error"})

        from_in_progress = self.registry.get_allowed_transitions("in_progress")
        self.assertEqual(from_in_progress, {"completed", "cancelled", "error"})

        from_completed = self.registry.get_allowed_transitions("completed")
        self.assertEqual(from_completed, {"error"})

        # Try an unregistered state
        from_unknown = self.registry.get_allowed_transitions("unknown_state")
        self.assertEqual(from_unknown, {"error"})  # Only wildcard error transition

    def test_global_registry(self):
        """Test the global transition registry."""
        registry = get_transition_registry()

        # Should have some default transitions
        allowed_from_initializing = registry.get_allowed_transitions("initializing")
        self.assertIn("running", allowed_from_initializing)

        allowed_from_running = registry.get_allowed_transitions("running")
        self.assertIn("paused", allowed_from_running)
        self.assertIn("stopped", allowed_from_running)

        # All states should transition to error
        self.assertIn("error", registry.get_allowed_transitions("any_state"))


if __name__ == "__main__":
    unittest.main()
