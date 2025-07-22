"""
Validation decorators for Atlas core services.

This module contains decorators that can be used to validate service inputs.
These decorators help ensure data consistency and proper error handling.
"""

from functools import wraps
from typing import Any, Callable, TypeVar, cast

from atlas.core.errors import ConfigurationError

F = TypeVar("F", bound=Callable[..., Any])

def validate_with_schema(
    schema_name: str, arg_names: list[str] = None
) -> Callable[[F], F]:
    """Create a decorator that validates arguments using a schema.
    
    Args:
        schema_name: Name of the schema to use for validation.
        arg_names: List of argument names to validate. If None, defaults to
            ["config", "configuration", "settings"].
            
    Returns:
        A decorator function.
    """
    
    def decorator(func: F) -> F:
        """Decorator that validates arguments using a schema.
        
        Args:
            func: The function to decorate.
            
        Returns:
            The decorated function.
        """
        
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function that validates arguments using a schema.
            
            Args:
                *args: Function arguments.
                **kwargs: Function keyword arguments.
                
            Returns:
                The result of the decorated function.
                
            Raises:
                ConfigurationError: If validation fails.
            """
            try:
                # Import here to avoid circular imports
                import atlas.schemas.services as schemas
                
                # Get schema
                schema = getattr(schemas, f"{schema_name}_schema")
                
                # Get argument names to validate
                names_to_validate = arg_names or ["config", "configuration", "settings"]
                
                # Validate arguments
                for arg_name in names_to_validate:
                    if arg_name in kwargs and kwargs[arg_name] is not None:
                        # Skip if not a dict
                        if not isinstance(kwargs[arg_name], dict):
                            continue
                            
                        # Validate
                        kwargs[arg_name] = schema.load(kwargs[arg_name])
                
                # Call original function
                return func(*args, **kwargs)
                
            except Exception as e:
                # Convert to configuration error
                raise ConfigurationError(
                    message=f"Invalid {schema_name} configuration: {e}",
                    cause=e,
                )
                
        return cast(F, wrapper)
        
    return decorator


# Specific decorators for common validations
validate_service_config = validate_with_schema("service", ["config", "service_config"])
validate_buffer_config = validate_with_schema("buffer_config", ["config", "buffer_config"])
validate_command = validate_with_schema("command", ["command"])
validate_event_data = validate_with_schema("event", ["data", "event_data"])
validate_resource_config = validate_with_schema("resource", ["config", "resource_config"])
validate_state_data = validate_with_schema("state", ["data", "state_data"])