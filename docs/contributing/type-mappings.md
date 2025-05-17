---
title: Type Mapping
---

# Type Mapping Guide

This document provides guidance on handling type mappings between different components and systems within Atlas. It covers key concepts, techniques, and best practices for ensuring consistent type conversions and mapping patterns.

## Overview

Type mappings are crucial when data moves between different components, especially when crossing language or system boundaries. This guide addresses:

1. **Type Conversion Patterns**: Consistent approaches for converting between different type representations
2. **Serialization Strategies**: How to reliably serialize and deserialize complex data structures
3. **System Boundary Handling**: Techniques for maintaining type consistency across API boundaries
4. **Validation Approaches**: Ensuring type integrity during conversions

## Type Mapping Pattern

The recommended pattern for type mappings in Atlas follows a standardized approach:

```python
# Type converter class approach
class TypeConverter:
    """Handles conversions between different type representations."""

    @staticmethod
    def to_target_format(source_obj):
        """Convert from source format to target format."""
        # Conversion logic here
        pass

    @staticmethod
    def from_target_format(target_obj):
        """Convert from target format back to source format."""
        # Reverse conversion logic here
        pass
```

This bidirectional conversion pattern ensures data can be reliably transformed in both directions.

## Python to JSON Type Mapping

When converting between Python types and JSON:

| Python Type        | JSON Representation | Notes                                      |
| ------------------ | ------------------- | ------------------------------------------ |
| `str`              | String              | Direct mapping                             |
| `int`, `float`     | Number              | Direct mapping                             |
| `bool`             | Boolean             | Direct mapping                             |
| `None`             | null                | Direct mapping                             |
| `list`, `tuple`    | Array               | Elements are converted recursively         |
| `dict`             | Object              | Keys must be strings                       |
| `datetime`, `date` | String              | ISO format (YYYY-MM-DDTHH:MM:SS.sssZ)      |
| Custom classes     | Object              | Convert to dict with `__dict__` or schemas |
| `Enum`             | String/Number       | Use enum value                             |

### Implementation Example

```python
import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

def convert_to_json_safe(obj: Any) -> Any:
    """Convert a Python object to a JSON-compatible representation."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, (list, tuple)):
        return [convert_to_json_safe(item) for item in obj]
    elif isinstance(obj, dict):
        return {str(k): convert_to_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Enum):
        return obj.value
    elif hasattr(obj, "__dict__"):
        return convert_to_json_safe(obj.__dict__)
    else:
        return str(obj)  # Fallback to string representation
```

## Schema-Based Type Mapping

For complex objects, use schema-based mapping for more control:

```python
from marshmallow import Schema, fields, post_load

class UserData:
    def __init__(self, name: str, email: str, age: int, roles: List[str]):
        self.name = name
        self.email = email
        self.age = age
        self.roles = roles

class UserSchema(Schema):
    name = fields.Str(required=True)
    email = fields.Email(required=True)
    age = fields.Int(required=True)
    roles = fields.List(fields.Str(), required=True)

    @post_load
    def make_user(self, data, **kwargs):
        return UserData(**data)

# Usage
schema = UserSchema()
user_dict = {"name": "John", "email": "john@example.com", "age": 30, "roles": ["admin", "user"]}
user_obj = schema.load(user_dict)  # Convert dict to UserData
user_dict_again = schema.dump(user_obj)  # Convert UserData back to dict
```

## Type Registry Pattern

For systems with many different types, a type registry can help manage mappings:

```python
class TypeRegistry:
    """Registry of type converters between systems."""

    # Map of source type to converter functions
    TYPE_CONVERTERS = {}

    @classmethod
    def register(cls, source_type, converter):
        """Register a converter for a specific type."""
        cls.TYPE_CONVERTERS[source_type] = converter

    @classmethod
    def convert(cls, obj, target_system):
        """Convert an object to the target system's representation."""
        obj_type = type(obj)

        if obj_type not in cls.TYPE_CONVERTERS:
            raise ValueError(f"No converter registered for type {obj_type.__name__}")

        converter = cls.TYPE_CONVERTERS[obj_type]
        return converter(obj, target_system)
```

## Cross-System Type Mapping

For detailed guidance on mapping between Atlas's Python types and other systems like NERV/Inner Universe, see:

- [NERV-Inner Universe Type Mappings](../v2/inner-universe/type_mappings.md): Comprehensive mapping between Python types and Rust/SpacetimeDB types
- [Schema Migration Tasks](../project-management/tracking/schema_migration_tasks.md): Migration strategies for evolving type systems

## Validation During Type Mapping

Always validate data during type conversions:

```python
def convert_with_validation(source_obj, target_type):
    """Convert source object to target type with validation."""
    # First perform the conversion
    converted = perform_conversion(source_obj, target_type)

    # Then validate the result
    validation_errors = validate_object(converted, target_type)
    if validation_errors:
        raise ValueError(f"Conversion resulted in invalid data: {validation_errors}")

    return converted
```

## Best Practices for Type Mappings

1. **Bidirectional Conversion**: Implement both to/from conversion functions
2. **Validation**: Always validate data after conversion
3. **Error Handling**: Provide clear error messages for conversion failures
4. **Default Values**: Handle missing or null fields consistently
5. **Version Tolerance**: Design conversions to be tolerant of version differences
6. **Type Safety**: Use static typing for converter functions
7. **Documentation**: Document type mapping assumptions and constraints
8. **Testing**: Create tests for all type conversions, especially edge cases

## Real-World Examples from Atlas

### Provider Response Mapping

The Atlas provider system maps different provider-specific response formats to a standardized `ModelResponse`:

```python
# From atlas/providers/implementations/anthropic.py
def _map_response(self, response_obj: Any) -> ModelResponse:
    """Map the provider response to a standardized model response."""
    if not response_obj:
        raise ProviderError("Empty response received from Anthropic API")

    # Extract content from Anthropic's specific format
    content = response_obj.get("content", "")
    if isinstance(content, list) and len(content) > 0:
        content = content[0].get("text", "")

    # Convert Anthropic's token usage format to Atlas format
    usage = TokenUsage.create_direct(
        input_tokens=response_obj.get("usage", {}).get("input_tokens", 0),
        output_tokens=response_obj.get("usage", {}).get("output_tokens", 0)
    )

    # Create standardized model response
    return ModelResponse.create_direct(
        provider="anthropic",
        model=response_obj.get("model"),
        content=content,
        usage=usage,
        raw_response=response_obj
    )
```

### Event Data Conversion

For event-based systems, mapped types are important for ensuring consistency:

```python
# Example event data conversion
def convert_event_data(event):
    """Convert event data to compatible format."""
    event_type = event.get("type")

    # Event type-specific conversion
    if event_type == "entity_created":
        return {
            "entity_id": event["data"]["id"],
            "entity_type": event["data"]["type"],
            "metadata": convert_metadata(event["data"]["metadata"])
        }
    elif event_type == "relation_created":
        return {
            "from_entity": event["data"]["from"],
            "to_entity": event["data"]["to"],
            "relation_type": event["data"]["type"]
        }
    else:
        # Default handling
        return event["data"]
```

## References

- [Schema Validation Guide](./schema_validation.md)
- [Type System Guide](./types.md)
- [Type System Migration](./typing-issues.md)
- [NERV-Inner Universe Type Mappings](../v2/inner-universe/type_mappings.md)
- [Marshmallow Documentation](https://marshmallow.readthedocs.io/)
