"""
Validation utilities for Atlas.

This module provides reusable utilities and decorators for schema-based
validation throughout the Atlas system, ensuring that data is properly
validated at API boundaries and during transitions between components.
"""

import functools
import inspect
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union, cast, get_type_hints

from marshmallow import Schema, ValidationError

# Type variables for function signatures
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')
S = TypeVar('S', bound=Schema)


def validate_with_schema(schema: Schema, field_name: Optional[str] = None):
    """Decorator to validate data with a schema.
    
    This decorator ensures that an object (either a parameter or a return value)
    is properly validated using the specified schema.
    
    Args:
        schema: The schema to use for validation.
        field_name: Optional parameter name to validate. If None, validates return value.
        
    Returns:
        Decorator function.
    
    Example:
        ```python
        @validate_with_schema(some_schema, field_name="config")
        def configure(self, config: Dict[str, Any]) -> None:
            # config is guaranteed to be valid
            ...
        
        @validate_with_schema(response_schema)
        def get_response(self) -> Dict[str, Any]:
            # return value will be validated
            ...
        ```
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if field_name is not None:
                # Validate a parameter
                if field_name in kwargs:
                    try:
                        validated_value = schema.load(kwargs[field_name])
                        kwargs[field_name] = validated_value
                    except ValidationError as e:
                        func_name = func.__name__
                        raise ValidationError(
                            f"Invalid {field_name} for {func_name}: {e.messages}",
                            field_name=field_name
                        )
                # No early return here as we still need to call the function
            
            # Call the original function
            result = func(*args, **kwargs)
            
            if field_name is None:
                # Validate the return value
                try:
                    return schema.load(result)
                except ValidationError as e:
                    func_name = func.__name__
                    raise ValidationError(
                        f"Invalid return value from {func_name}: {e.messages}"
                    )
            
            return result
        
        return cast(F, wrapper)
    
    return decorator


def validate_args(schema_map: Dict[str, Schema]):
    """Decorator to validate multiple function arguments against schemas.
    
    This decorator validates multiple function arguments against their
    respective schemas.
    
    Args:
        schema_map: A dictionary mapping parameter names to schemas.
        
    Returns:
        Decorator function.
    
    Example:
        ```python
        @validate_args({
            "config": config_schema,
            "options": options_schema
        })
        def configure(self, config: Dict[str, Any], options: Dict[str, Any]) -> None:
            # Both config and options are guaranteed to be valid
            ...
        ```
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get the function signature to match positional args to param names
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate each argument in the schema_map
            for param_name, schema in schema_map.items():
                if param_name in bound_args.arguments:
                    arg_value = bound_args.arguments[param_name]
                    try:
                        validated_value = schema.load(arg_value)
                        bound_args.arguments[param_name] = validated_value
                    except ValidationError as e:
                        func_name = func.__name__
                        raise ValidationError(
                            f"Invalid {param_name} for {func_name}: {e.messages}",
                            field_name=param_name
                        )
            
            # Call the function with validated arguments
            return func(*bound_args.args, **bound_args.kwargs)
        
        return cast(F, wrapper)
    
    return decorator


def validate_class_init(schema_map: Dict[str, Schema]):
    """Class decorator to validate __init__ arguments against schemas.
    
    This decorator ensures that arguments passed to a class's __init__
    method are properly validated using the specified schemas.
    
    Args:
        schema_map: A dictionary mapping parameter names to schemas.
        
    Returns:
        Class decorator function.
    
    Example:
        ```python
        @validate_class_init({
            "options": options_schema,
            "config": config_schema
        })
        class SomeClass:
            def __init__(self, options: Dict[str, Any], config: Dict[str, Any], **kwargs):
                # options and config are guaranteed to be valid
                ...
        ```
    """
    def decorator(cls: Type[Any]) -> Type[Any]:
        # Store the original __init__ method
        original_init = cls.__init__
        
        # Define a new __init__ method that validates arguments
        def __init__(self: Any, *args: Any, **kwargs: Any) -> None:
            # Get the signature of the original __init__
            sig = inspect.signature(original_init)
            bound_args = sig.bind(self, *args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate each argument in the schema_map
            for param_name, schema in schema_map.items():
                if param_name in bound_args.arguments:
                    arg_value = bound_args.arguments[param_name]
                    try:
                        validated_value = schema.load(arg_value)
                        bound_args.arguments[param_name] = validated_value
                    except ValidationError as e:
                        class_name = cls.__name__
                        raise ValidationError(
                            f"Invalid {param_name} for {class_name}.__init__: {e.messages}",
                            field_name=param_name
                        )
            
            # Call the original __init__ method with validated arguments
            original_args = bound_args.args[1:]  # Remove 'self'
            original_kwargs = {k: v for k, v in bound_args.kwargs.items()}
            original_init(self, *original_args, **original_kwargs)
        
        # Replace the __init__ method
        cls.__init__ = __init__  # type: ignore
        
        return cls
    
    return decorator


def create_schema_validated(schema: Union[Schema, Callable[[], Schema]]) -> Callable[[Type[T]], Type[T]]:
    """Factory for creating validated classes with schema integration.
    
    This decorator adds schema validation capabilities to a class, ensuring
    that instances are created with validated data.
    
    Args:
        schema: A schema instance or a function that returns a schema instance.
        
    Returns:
        Class decorator function.
    
    Example:
        ```python
        @create_schema_validated(message_schema)
        class Message:
            def __init__(self, content: str, **kwargs):
                self.content = content
                for key, value in kwargs.items():
                    setattr(self, key, value)
        ```
    """
    def get_schema() -> Schema:
        """Get the schema instance."""
        if callable(schema) and not isinstance(schema, Schema):
            return schema()
        return schema  # type: ignore
    
    def decorator(cls: Type[T]) -> Type[T]:
        # Store the original __init__ method
        original_init = cls.__init__
        
        # Add classmethod to create instances from dict
        @classmethod
        def from_dict(cls_: Type[T], data: Dict[str, Any]) -> T:
            """Create an instance from a dictionary.
            
            Args:
                data: The dictionary to convert.
                
            Returns:
                An instance of the class.
                
            Raises:
                ValidationError: If validation fails.
            """
            # If data is already an instance of the class, return it directly
            if isinstance(data, cls_):
                return data
                
            validated_data = get_schema().load(data)
            
            # Check if the class already has a proper constructor
            if hasattr(cls_, "__init__") and cls_.__init__ is not object.__init__:
                # Use the class constructor
                return cls_(**validated_data)
            else:
                # Create instance directly
                instance = cls_.__new__(cls_)
                for key, value in validated_data.items():
                    setattr(instance, key, value)
                return instance
        
        # Add method to convert to dict
        def to_dict(self: T) -> Dict[str, Any]:
            """Convert the instance to a dictionary.
            
            Returns:
                The dictionary representation.
            """
            return get_schema().dump(self)
        
        # Add class attribute for schema access
        schema_ = get_schema()
        
        # Define new __init__ method - only if it doesn't override a custom __init__
        if original_init is object.__init__:
            # No custom __init__, use generic initialization
            def __init__(self: Any, **kwargs: Any) -> None:
                """Initialize with validated data."""
                # Validate data against schema
                try:
                    validated_data = get_schema().load(kwargs)
                    
                    # Set attributes from validated data
                    for key, value in validated_data.items():
                        setattr(self, key, value)
                except ValidationError as e:
                    class_name = cls.__name__
                    raise ValidationError(
                        f"Invalid data for {class_name}: {e.messages}"
                    )
                
            # Replace __init__ with our generic version
            cls.__init__ = __init__  # type: ignore
        else:
            # Class has a custom __init__, add validation wrapper
            def __init_with_validation(self: Any, *args: Any, **kwargs: Any) -> None:
                """Initialize with validation."""
                # Get the signature of the original __init__
                sig = inspect.signature(original_init)
                
                try:
                    # Bind arguments to signature parameters
                    bound_args = sig.bind(self, *args, **kwargs)
                    bound_args.apply_defaults()
                    
                    # Extract kwargs for validation
                    kwargs_to_validate = {k: v for k, v in bound_args.kwargs.items()}
                    
                    # Validate kwargs against schema
                    validated_data = get_schema().load(kwargs_to_validate)
                    
                    # Update kwargs with validated data
                    for k, v in validated_data.items():
                        bound_args.kwargs[k] = v
                    
                    # Call original __init__ with validated data
                    original_args = bound_args.args[1:]  # Remove 'self'
                    original_kwargs = {k: v for k, v in bound_args.kwargs.items()}
                    original_init(self, *original_args, **original_kwargs)
                
                except ValidationError as e:
                    class_name = cls.__name__
                    raise ValidationError(
                        f"Invalid data for {class_name}: {e.messages}"
                    )
                except Exception as e:
                    # Fallback for binding errors
                    class_name = cls.__name__
                    if "takes 1 positional argument but" in str(e) and original_init is object.__init__:
                        # Handle object.__init__() error by directly setting attributes
                        for key, value in kwargs.items():
                            setattr(self, key, value)
                    else:
                        # Re-raise for other errors
                        raise
            
            # Replace __init__ with our validation wrapper
            cls.__init__ = __init_with_validation  # type: ignore
        
        # Add methods and attributes to the class
        cls.from_dict = from_dict
        cls.to_dict = to_dict
        cls.schema = schema_
        
        return cls
    
    return decorator


# Export utility functions
__all__ = [
    'validate_with_schema',
    'validate_args',
    'validate_class_init',
    'create_schema_validated'
]