---
title: Schema Validation
---

# Schema Validation Guide

This guide explains how to use schema validation in Atlas, along with migration notes for marshmallow 4.0.0.

## Overview

Atlas uses marshmallow for schema validation to ensure that data structures conform to expected formats. This validation happens at API boundaries and provides several benefits:

- Type safety and validation
- Consistent serialization/deserialization
- Self-documenting data structures
- Improved error messages

## Using Schema Validation

### Basic Schema Usage

```python
from atlas.schemas.messages import text_content_schema

# Validate text content
content = {
    "type": "text", 
    "text": "This is a sample message"
}
validated_content = text_content_schema.load(content)
```

### Creating Custom Schemas

```python
from atlas.schemas.base import AtlasSchema
from marshmallow import fields

class MyCustomSchema(AtlasSchema):
    """Schema for my custom data structure."""
    
    id = fields.String(required=True)
    name = fields.String(required=True)
    value = fields.Integer(required=False, load_default=0)
    
my_schema = MyCustomSchema()
```

### Validation Decorators

Atlas provides several decorators for schema validation:

```python
from atlas.schemas.validation import validate_with_schema
from atlas.schemas.providers import model_request_schema

@validate_with_schema(model_request_schema)
def process_request(request):
    # request is guaranteed to be valid
    ...
```

## Migrating to Marshmallow 4.0.0

::: warning
In marshmallow 4.0.0, the `default` parameter for fields has been replaced by separate `load_default` and `dump_default` parameters.
:::

### Changes from Marshmallow 3.x

Marshmallow 4.0.0 introduces several breaking changes, with the most important being the replacement of the `default` parameter:

- **Old (3.x)**: `fields.Boolean(required=False, default=True)`
- **New (4.0.0)**: `fields.Boolean(required=False, load_default=True)`

The separation into `load_default` and `dump_default` provides more control over serialization and deserialization defaults:

- `load_default`: Default value when deserializing (loading) data
- `dump_default`: Default value when serializing (dumping) data

### Migration Examples

#### Before (Marshmallow 3.x)

```python
class DatabaseConfigSchema(AtlasSchema):
    provider = fields.String(required=True)
    persistent = fields.Boolean(required=False, default=True)
    options = fields.Dict(keys=fields.String(), values=fields.Raw(), required=False)
```

#### After (Marshmallow 4.0.0)

```python
class DatabaseConfigSchema(AtlasSchema):
    provider = fields.String(required=True)
    persistent = fields.Boolean(required=False, load_default=True)
    options = fields.Dict(keys=fields.String(), values=fields.Raw(), required=False)
```

### Other Considerations

1. For fields where you want different default values for loading and dumping:

```python
class UserSchema(AtlasSchema):
    active = fields.Boolean(load_default=False, dump_default=True)
```

2. For validators, make sure to add `**kwargs` to your method signatures:

```python
@validates("field_name")
def validate_field(self, value, **kwargs):
    # Validation logic
```

## Common Schema Types

Atlas provides many built-in schemas:

- `ModelMessageSchema`: For model messages
- `TokenUsageSchema`: For token usage tracking
- `ProviderOptionsSchema`: For provider options
- `AgentConfigSchema`: For agent configuration
- `RetrievalSettingsSchema`: For knowledge retrieval settings

## Example: Complete Schema Validation

For a complete example of schema validation, see the `examples/16_schema_validation.py` file, which demonstrates:

1. Basic schema validation for messages and data structures
2. Provider options validation
3. Using the SchemaValidated wrapper for guaranteed validation
4. Creating custom schemas for application-specific objects
5. Validating data at API boundaries
6. Mapping schema validation errors to provider-specific errors
7. Advanced validation decorators for functions and classes

## Migration from TypedDict

Atlas is in the process of migrating from TypedDict-based type annotations to schema-based validation. 
For details on this migration, see the [Schema Migration Tasks](../project-management/tracking/schema_migration_tasks.md).