"""
Validation utilities for Atlas providers.

This module provides validation functions and decorators to ensure that
provider inputs and outputs are properly validated using schemas.
"""

import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast, get_type_hints

from marshmallow import Schema, ValidationError

from atlas.schemas.providers import model_request_schema, model_response_schema
from atlas.schemas.types import SchemaValidated
from atlas.providers.errors import ProviderValidationError
from atlas.providers.messages import ModelRequest, ModelResponse
from atlas.schemas.validation import validate_with_schema, validate_args, validate_class_init


# Type variables for function signatures
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')
SchemaType = TypeVar('SchemaType', bound=Schema)


def validate_request(func: F) -> F:
    """Decorator to validate request objects before processing.
    
    This decorator ensures that the request object passed to a provider
    method is properly validated against the ModelRequestSchema.
    
    Args:
        func: The function to decorate.
        
    Returns:
        The decorated function.
    
    Example:
        ```python
        @validate_request
        def generate(self, request: ModelRequest) -> ModelResponse:
            # request is guaranteed to be valid
            ...
        ```
    """
    @functools.wraps(func)
    def wrapper(self: Any, request: Any, *args: Any, **kwargs: Any) -> Any:
        # Skip validation if request is already validated
        if isinstance(request, SchemaValidated):
            return func(self, request.data, *args, **kwargs)
        
        try:
            # Handle case where request is already a ModelRequest
            if isinstance(request, ModelRequest):
                # No need to convert back to ModelRequest
                return func(self, request, *args, **kwargs)
            
            # Otherwise, validate the request (assuming it's a dict)
            validated_request = model_request_schema.load(request)
            
            # Convert to ModelRequest and call the function
            model_request = ModelRequest.from_dict(validated_request)
            return func(self, model_request, *args, **kwargs)
        except ValidationError as e:
            # Convert validation errors to provider errors
            provider_name = getattr(self, "name", "unknown")
            raise ProviderValidationError(
                f"Invalid request for provider {provider_name}: {e.messages}",
                provider=provider_name,
                details={"validation_errors": e.messages}
            )
    
    return cast(F, wrapper)


def validate_response(func: F) -> F:
    """Decorator to validate response objects after processing.
    
    This decorator ensures that the response object returned from a provider
    method is properly validated against the ModelResponseSchema.
    
    Args:
        func: The function to decorate.
        
    Returns:
        The decorated function.
    
    Example:
        ```python
        @validate_response
        def generate(self, request: ModelRequest) -> ModelResponse:
            # response will be validated before returning
            ...
        ```
    """
    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        # Call the original function
        response = func(self, *args, **kwargs)
        
        # Skip validation if response is already validated or not a ModelResponse
        if isinstance(response, SchemaValidated) or not isinstance(response, ModelResponse):
            return response
        
        try:
            # Validate the response
            validated_response = model_response_schema.load(response.to_dict())
            
            # Return a validated response
            return ModelResponse.from_dict(validated_response)
        except ValidationError as e:
            # Convert validation errors to provider errors
            provider_name = getattr(self, "name", "unknown")
            raise ProviderValidationError(
                f"Invalid response from provider {provider_name}: {e.messages}",
                provider=provider_name,
                details={"validation_errors": e.messages}
            )
    
    return cast(F, wrapper)


def validated_by(schema: Schema, field_name: Optional[str] = None) -> Callable[[F], F]:
    """Decorator factory to validate objects using a specific schema.
    
    This decorator ensures that an object (either a parameter or a return value)
    is properly validated using the specified schema.
    
    Args:
        schema: The schema to use for validation.
        field_name: Optional parameter name to validate. If None, validates return value.
        
    Returns:
        Decorator function.
    
    Example:
        ```python
        @validated_by(some_schema, field_name="config")
        def configure(self, config: Dict[str, Any]) -> None:
            # config is guaranteed to be valid
            ...
        
        @validated_by(response_schema)
        def get_response(self) -> Dict[str, Any]:
            # return value will be validated
            ...
        ```
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            if field_name is not None:
                # Validate a parameter
                if field_name in kwargs:
                    try:
                        validated_value = schema.load(kwargs[field_name])
                        kwargs[field_name] = validated_value
                    except ValidationError as e:
                        provider_name = getattr(self, "name", "unknown")
                        raise ProviderValidationError(
                            f"Invalid {field_name} for provider {provider_name}: {e.messages}",
                            provider=provider_name,
                            details={"validation_errors": e.messages}
                        )
                # No early return here as we still need to call the function
            
            # Call the original function
            result = func(self, *args, **kwargs)
            
            if field_name is None:
                # Validate the return value
                try:
                    return schema.load(result)
                except ValidationError as e:
                    provider_name = getattr(self, "name", "unknown")
                    raise ProviderValidationError(
                        f"Invalid return value from provider {provider_name}: {e.messages}",
                        provider=provider_name,
                        details={"validation_errors": e.messages}
                    )
            
            return result
        
        return cast(F, wrapper)
    
    return decorator


def validate_options(schema: Schema) -> Callable[[Type[Any]], Type[Any]]:
    """Class decorator to validate options during initialization.
    
    This decorator ensures that options passed to a class's __init__
    method are properly validated using the specified schema.
    
    Args:
        schema: The schema to use for validation.
        
    Returns:
        Class decorator function.
    
    Example:
        ```python
        @validate_options(provider_options_schema)
        class SomeProvider(ModelProvider):
            def __init__(self, options: Dict[str, Any], **kwargs):
                # options is guaranteed to be valid
                ...
        ```
    """
    def decorator(cls: Type[Any]) -> Type[Any]:
        # Store the original __init__ method
        original_init = cls.__init__
        
        # Define a new __init__ method that validates options
        def __init__(self: Any, *args: Any, **kwargs: Any) -> None:
            # Check if options are passed
            if "options" in kwargs:
                try:
                    # Validate options
                    validated_options = schema.load(kwargs["options"])
                    kwargs["options"] = validated_options
                except ValidationError as e:
                    provider_name = getattr(cls, "name", kwargs.get("name", "unknown"))
                    raise ProviderValidationError(
                        f"Invalid options for provider {provider_name}: {e.messages}",
                        provider=provider_name,
                        details={"validation_errors": e.messages}
                    )
            
            # Call the original __init__ method
            original_init(self, *args, **kwargs)
        
        # Replace the __init__ method
        cls.__init__ = __init__  # type: ignore
        
        return cls
    
    return decorator


def provider_schema_validated(schema_factory: Callable[[], SchemaType]) -> Callable[[Type[T]], Type[T]]:
    """Factory for creating schema-validated provider classes.
    
    This decorator adds schema validation capabilities to a provider class,
    ensuring that requests, responses, and options are properly validated.
    
    Args:
        schema_factory: A function that returns a schema instance.
        
    Returns:
        Class decorator function.
    
    Example:
        ```python
        @provider_schema_validated(lambda: ProviderSchema())
        class CustomProvider(ModelProvider):
            def __init__(self, name: str, model_name: str, **kwargs):
                self.name = name
                self.model_name = model_name
                # ...
        ```
    """
    def decorator(cls: Type[T]) -> Type[T]:
        # Store the original __init__ method
        original_init = cls.__init__
        
        # Add classmethod to create instances from dict
        @classmethod
        def from_dict(cls_: Type[T], data: Dict[str, Any]) -> T:
            """Create a provider instance from a dictionary.
            
            Args:
                data: The dictionary to convert.
                
            Returns:
                A provider instance.
                
            Raises:
                ValidationError: If validation fails.
            """
            schema = schema_factory()
            validated_data = schema.load(data)
            return cls_(**validated_data)
        
        # Add method to convert to dict
        def to_dict(self: T) -> Dict[str, Any]:
            """Convert the provider instance to a dictionary.
            
            Returns:
                The dictionary representation.
            """
            schema = schema_factory()
            return schema.dump(self)
        
        # Add class attribute for schema access
        schema_ = schema_factory()
        
        # Define new __init__ method
        def __init__(self: Any, *args: Any, **kwargs: Any) -> None:
            # Get the signature of the original __init__
            sig = inspect.signature(original_init)
            bound_args = sig.bind(self, *args, **kwargs)
            bound_args.apply_defaults()
            
            # Get all kwargs
            params = {**{name: value for name, value in zip(list(sig.parameters.keys())[1:], args)},
                     **kwargs}
            
            # Validate against schema
            try:
                schema = schema_factory()
                validated_data = schema.load(params)
                
                # Update kwargs with validated data
                for k, v in validated_data.items():
                    if k in bound_args.kwargs:
                        bound_args.kwargs[k] = v
            except ValidationError as e:
                provider_name = params.get("name", cls.__name__)
                raise ProviderValidationError(
                    f"Invalid configuration for provider {provider_name}: {e.messages}",
                    provider=provider_name,
                    details={"validation_errors": e.messages}
                )
            
            # Call original __init__ with validated data
            original_args = bound_args.args[1:]  # Remove 'self'
            original_kwargs = {k: v for k, v in bound_args.kwargs.items()}
            original_init(self, *original_args, **original_kwargs)
        
        # Add methods and attributes to the class
        cls.from_dict = from_dict
        cls.to_dict = to_dict
        cls.schema = schema_
        cls.__init__ = __init__  # type: ignore
        
        return cls
    
    return decorator


def validate_stream_handler(func: F) -> F:
    """Decorator to validate streaming handlers and operations.
    
    This decorator ensures that streaming operations are properly
    validated, including stream initialization and event handling.
    
    Args:
        func: The function to decorate.
        
    Returns:
        The decorated function.
    
    Example:
        ```python
        @validate_stream_handler
        def stream(self, request: ModelRequest) -> StreamHandler:
            # Streaming setup and operations are validated
            ...
        ```
    """
    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        # Validate request if it's the first argument and a ModelRequest
        if args and isinstance(args[0], ModelRequest):
            request = args[0]
            try:
                validated_request = model_request_schema.load(request.to_dict())
                # Replace the first argument with the validated request
                args = (ModelRequest.from_dict(validated_request),) + args[1:]
            except ValidationError as e:
                provider_name = getattr(self, "name", "unknown")
                raise ProviderValidationError(
                    f"Invalid streaming request for provider {provider_name}: {e.messages}",
                    provider=provider_name,
                    details={"validation_errors": e.messages}
                )
        
        # Call the original function with validated arguments
        result = func(self, *args, **kwargs)
        
        # Validate that the result supports the streaming interface
        if hasattr(result, "get_iterator") and hasattr(result, "process_stream"):
            return result
        else:
            provider_name = getattr(self, "name", "unknown")
            raise ProviderValidationError(
                f"Invalid stream handler returned by provider {provider_name}",
                provider=provider_name,
                details={"error": "Stream handler must implement get_iterator and process_stream methods"}
            )
    
    return cast(F, wrapper)


def validate_capabilities(
    required_capabilities: List[str] = None,
    min_strengths: Dict[str, int] = None
) -> Callable[[F], F]:
    """Decorator to validate provider capabilities before operation.
    
    This decorator checks if a provider has the required capabilities
    with the minimum strength levels before executing the decorated function.
    
    Args:
        required_capabilities: List of capability names that must be present.
        min_strengths: Dictionary mapping capability names to minimum strength levels.
        
    Returns:
        Decorator function.
    
    Example:
        ```python
        @validate_capabilities(
            required_capabilities=["streaming", "vision"],
            min_strengths={"streaming": 2}
        )
        def process_image_stream(self, image, request):
            # Provider is guaranteed to have streaming and vision capabilities,
            # with streaming at strength level >= 2
            ...
        ```
    """
    required_capabilities = required_capabilities or []
    min_strengths = min_strengths or {}
    
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Skip validation if no requirements
            if not required_capabilities and not min_strengths:
                return func(self, *args, **kwargs)
            
            # Get provider capabilities
            capabilities = getattr(self, "capabilities", {})
            if not capabilities:
                provider_name = getattr(self, "name", "unknown")
                raise ProviderValidationError(
                    f"Provider {provider_name} does not define capabilities",
                    provider=provider_name,
                    details={"error": "No capabilities defined for provider"}
                )
            
            # Check required capabilities
            missing_capabilities = [cap for cap in required_capabilities if cap not in capabilities]
            if missing_capabilities:
                provider_name = getattr(self, "name", "unknown")
                raise ProviderValidationError(
                    f"Provider {provider_name} is missing required capabilities: {', '.join(missing_capabilities)}",
                    provider=provider_name,
                    details={"missing_capabilities": missing_capabilities}
                )
            
            # Check minimum strength levels
            insufficient_strengths = {
                cap: {"required": min_strength, "actual": capabilities.get(cap, 0)}
                for cap, min_strength in min_strengths.items()
                if capabilities.get(cap, 0) < min_strength
            }
            
            if insufficient_strengths:
                provider_name = getattr(self, "name", "unknown")
                raise ProviderValidationError(
                    f"Provider {provider_name} has insufficient capability strengths",
                    provider=provider_name,
                    details={"insufficient_strengths": insufficient_strengths}
                )
            
            # Call the original function
            return func(self, *args, **kwargs)
        
        return cast(F, wrapper)
    
    return decorator


# Export utility functions
__all__ = [
    'validate_request',
    'validate_response',
    'validated_by',
    'validate_options',
    'provider_schema_validated',
    'validate_stream_handler',
    'validate_capabilities'
]