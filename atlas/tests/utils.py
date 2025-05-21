"""
Utility functions and classes for tests.

This module provides common test utilities used across
multiple test files for the Atlas framework.
"""

import inspect
import re
from typing import Any, Callable, Dict, List, Type, TypeVar

T = TypeVar("T")


def assert_implements_protocol(obj: Any, protocol_type: Type[T]) -> None:
    """
    Assert that an object correctly implements a protocol.
    
    Args:
        obj: The object to check
        protocol_type: The protocol type to check against
    
    Raises:
        AssertionError: If the object does not implement the protocol correctly
    """
    # Get all required methods and properties from the protocol
    protocol_members = []
    for name, member in inspect.getmembers(protocol_type):
        if not name.startswith("_") or name in ("__call__",):
            protocol_members.append(name)
    
    # Check that the object implements all required members
    for name in protocol_members:
        assert hasattr(obj, name), f"Object does not implement '{name}' required by protocol"


def assert_type_annotations_match(func: Callable, expected_annotations: Dict[str, Any]) -> None:
    """
    Assert that a function's type annotations match the expected ones.
    
    Args:
        func: The function to check
        expected_annotations: Dictionary of parameter names to expected types
        
    Raises:
        AssertionError: If annotations don't match expectations
    """
    annotations = getattr(func, "__annotations__", {})
    
    for param, expected_type in expected_annotations.items():
        assert param in annotations, f"Parameter '{param}' not found in function annotations"
        assert annotations[param] == expected_type, (
            f"Type mismatch for parameter '{param}': "
            f"expected {expected_type}, got {annotations[param]}"
        )


def camel_to_snake(name: str) -> str:
    """
    Convert CamelCase to snake_case.
    
    Args:
        name: The CamelCase string
        
    Returns:
        The snake_case version of the string
    """
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def assert_attributes_match(obj: Any, expected_attrs: Dict[str, Any]) -> None:
    """
    Assert that an object's attributes match the expected values.
    
    Args:
        obj: The object to check
        expected_attrs: Dictionary of attribute names to expected values
        
    Raises:
        AssertionError: If attributes don't match expectations
    """
    for attr, expected_value in expected_attrs.items():
        assert hasattr(obj, attr), f"Object does not have attribute '{attr}'"
        assert getattr(obj, attr) == expected_value, (
            f"Attribute '{attr}' has incorrect value: "
            f"expected {expected_value}, got {getattr(obj, attr)}"
        )


def get_type_parameters(obj: Any) -> List[Type]:
    """
    Get the type parameters of a generic class.
    
    Args:
        obj: The generic object
        
    Returns:
        A list of type parameters
    """
    try:
        return list(obj.__parameters__)
    except (AttributeError, TypeError):
        # Fall back to getting __orig_class__ if available (for typed instances)
        orig_class = getattr(obj, "__orig_class__", None)
        if orig_class is not None:
            return list(orig_class.__args__)
        return []