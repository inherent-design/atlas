# Schema Validation Architecture

The Atlas framework implements a comprehensive schema validation system based on Marshmallow to ensure data integrity and type safety across the codebase. This document explains the architecture of this system, key components, and how to extend it.

## Overview

The schema validation system uses a layered approach to avoid circular imports while providing comprehensive validation:

1. **Pure Schema Definitions**: Base schemas that define structure and validation rules without implementation dependencies
2. **Proxy Schema Classes**: Schemas that extend the base definitions and handle conversion to implementation classes
3. **Schema-Validated Classes**: Implementation classes decorated with validation capabilities

## Directory Structure

```
atlas/
  schemas/
    __init__.py
    base.py              # Base schema utilities and field types
    validation.py        # Schema validation decorators and utilities
    messages.py          # Schema implementations for message classes
    providers.py         # Schema implementations for provider-related classes
    options.py           # Schema implementations for provider options
    definitions/         # Pure schema definitions
      __init__.py
      messages.py        # Message type schemas
      options.py         # Provider options schemas
      providers.py       # Provider schemas
```

## Schema Validation Layers

### 1. Pure Schema Definitions

Located in the `atlas/schemas/definitions/` directory, these schemas define structure and validation rules without referencing implementation classes, avoiding circular imports:

```python
# Example from atlas/schemas/definitions/messages.py
class TextContentSchema(AtlasSchema):
    """Schema for text content in messages."""
    
    type = fields.Constant("text", required=True)
    text = fields.String(required=True)
```

### 2. Proxy Schema Classes

Located in the main `atlas/schemas/` directory, these extend the base definitions with post-load methods that convert validated data into implementation classes:

```python
# Example from atlas/schemas/messages.py
class TextContentSchema(base_text_content_schema.__class__):
    """Schema for text content in messages with implementation conversion."""
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Any:
        """Convert loaded data into a TextContent object."""
        # Import here to avoid circular imports
        from atlas.providers.messages import MessageContent
        return MessageContent.__new__(
            MessageContent,
            type="text",
            text=data["text"]
        )
```

### 3. Schema-Validated Classes

Implementation classes decorated with `@create_schema_validated` to gain validation capabilities:

```python
# Example from atlas/providers/messages.py
@create_schema_validated(message_content_schema)
class MessageContent:
    """Content of a message, which can be text or other media."""
    type: str
    text: Optional[str] = None
    image_url: Optional[Dict[str, Any]] = None
```

## Key Components

### 1. Base Utilities (`atlas/schemas/base.py`)

- `AtlasSchema`: Base class for all schemas, providing common utilities
- `EnumField`: Custom field for enum validation
- `JsonField`: Custom field for JSON handling

### 2. Validation Decorators (`atlas/schemas/validation.py`)

- `create_schema_validated()`: Primary decorator to add schema validation to classes
- `validate_with_schema()`: Function decorator for validating arguments or return values
- `validate_args()`: Decorator for validating multiple function arguments
- `validate_class_init()`: Decorator for validating class initialization parameters

### 3. Schema Implementations

Each schema implementation module (e.g., `messages.py`, `options.py`) contains:

1. Schema implementations extending the base definitions
2. Post-load methods for conversion to implementation classes
3. Utility functions for validation

## Usage Examples

### Creating a Schema-Validated Class

```python
from atlas.schemas.validation import create_schema_validated
from atlas.schemas.messages import message_content_schema

@create_schema_validated(message_content_schema)
class MessageContent:
    """Content of a message, which can be text or other media."""
    
    type: str
    text: Optional[str] = None
    image_url: Optional[Dict[str, Any]] = None
    
    @classmethod
    def create_text(cls, text: str) -> "MessageContent":
        """Create a text content message."""
        return cls(type="text", text=text)
```

### Validating Function Arguments

```python
from atlas.schemas.validation import validate_args
from atlas.schemas.providers import model_request_schema, model_response_schema

@validate_args({
    "request": model_request_schema,
    "response": model_response_schema
})
def process_request_response(request, response):
    # Both request and response are guaranteed to be valid
    pass
```

## Schema Migration Strategy

When migrating existing classes to use schema validation:

1. Create pure schema definitions in the `definitions/` directory
2. Create schema classes with post_load methods in the main schemas directory
3. Apply the `@create_schema_validated` decorator to implementation classes
4. Update the constructors or ensure compatibility with the schema

## Handling Circular Imports

The layered approach solves circular import problems:

1. Implementation classes import schemas
2. Schemas import definitions (no circular dependency)
3. Post-load methods use delayed imports for implementation classes

## Testing Schema Validation

The test suite includes comprehensive tests for schema validation:

- `test_schema_message_validation.py`: Tests for message-related schemas
- `test_schema_response_validation.py`: Tests for response-related schemas
- `test_schema_options_validation.py`: Tests for provider options schemas
- `test_schema_validation_decorators.py`: Tests for schema validation decorators

Run all schema tests with:

```bash
uv run python -m atlas.tests.run_schema_tests
```

## Extending the Schema System

To extend the schema validation system for a new component:

1. Create a pure schema definition in `definitions/your_component.py`
2. Create a schema implementation in `schemas/your_component.py`
3. Add post_load methods to convert to implementation classes
4. Apply the `@create_schema_validated` decorator to implementation classes
5. Add tests in `tests/test_schema_your_component.py`