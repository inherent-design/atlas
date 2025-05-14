# Perspective Shifting

## Overview

Perspective Shifting allows components to adapt their abstraction level dynamically based on the observer's needs. It creates different views or representations of the same underlying data tailored to specific contexts or roles.

## Key Concepts

- **Data Source**: The underlying raw data
- **Transformation Function**: Converts raw data to a specific view
- **Perspective**: Named view of the data with specific transformation
- **Context Awareness**: Adapting views based on runtime conditions
- **Abstraction Levels**: Varying detail levels for different consumers
- **Schema Definition**: Structured rules for transforming data between perspectives

## Benefits

- **Simplified Interfaces**: Present only relevant information for each use case
- **Progressive Disclosure**: Reveal complexity gradually as needed
- **Adaptable Views**: Transform data based on context
- **Separation of Concerns**: Keep raw data separate from presentation logic
- **Role-Based Access**: Provide appropriate information for different user roles
- **Validation Integration**: Combine data transformation with validation

## Implementation Considerations

- **Performance**: Cache frequently used perspectives
- **Consistency**: Ensure perspectives remain consistent during updates
- **Composition**: Support composition of multiple perspectives
- **Immutability**: Consider immutable data to simplify perspective management
- **Default Views**: Provide sensible default perspectives
- **Serialization Format**: Consider target formats (JSON, YAML, etc.)
- **Change Tracking**: Determine if transformations should track changes

## Core Interfaces

```
Projectable[S, P]
├── add_perspective(name, schema) -> None
├── view(perspective) -> P
├── get_available_perspectives() -> List[str]
└── update_data(data) -> None
```

## Implementation with Marshmallow Library

NERV implements the Perspective Shifting pattern using the [Marshmallow](https://marshmallow.readthedocs.io/) library, which provides schema-based data serialization, validation, and transformation:

### Core Library Components

| Component | Description | NERV Integration |
|-----------|-------------|-----------------|
| `Schema` base class | Defines field structure and processing rules | Extended for different perspectives |
| `fields` module | Type-specific field validators and formatters | Used for defining schema fields |
| `pre_load/post_load` decorators | Processing hooks during serialization | Custom transformations for perspectives |
| `only` parameter | Filters included fields | Used for field subset perspectives |
| `Meta` class | Schema configuration options | Used for perspective default settings |
| `ValidationError` class | Structured validation errors | Integrated with error handling |
| `SchemaOpts` class | Customizes schema behavior | Extended for perspective customization |
| `class_registry` | Manages nested schemas | Used for perspective composition |

### Core Schema Types

```python
from typing import Dict, List, Any, Type, Optional, Union
from marshmallow import Schema, fields, post_load, pre_dump, validates

class BasePerspective(Schema):
    """Base schema for all perspectives."""
    class Meta:
        # Common fields across all perspectives
        fields = ("id", "type", "created_at") 
        
    # Common field definitions
    id = fields.String(required=True)
    type = fields.String(required=True)
    created_at = fields.DateTime(required=True)

class UserPerspective(BasePerspective):
    """User-facing perspective with limited fields."""
    class Meta:
        # Fields included in user perspective
        fields = BasePerspective.Meta.fields + ("name", "description")
    
    # Additional fields
    name = fields.String(required=True)
    description = fields.String(required=False)
    
class DeveloperPerspective(BasePerspective):
    """Developer perspective with technical details."""
    class Meta:
        # Fields included in developer perspective
        fields = UserPerspective.Meta.fields + ("metadata", "debug_info")
    
    # Additional fields
    metadata = fields.Dict(required=False)
    debug_info = fields.Dict(required=False)
```

### Dynamic Perspective Management

The Marshmallow library enables dynamic perspective creation:

```python
class PerspectiveManager:
    """Manages dynamic perspectives with Marshmallow schemas."""
    
    def create_perspective(base_schema: Type[Schema], fields_subset: List[str], 
                           name: str) -> Type[Schema]:
        """Create a new perspective from an existing schema."""
        class DynamicPerspective(base_schema):
            class Meta:
                # Dynamically set included fields
                fields = fields_subset
        
        # Register for later use
        DynamicPerspective.__name__ = name
        return DynamicPerspective
```

### Marshmallow Integration with Atlas

The Perspective Shifting pattern implemented with Marshmallow integrates with multiple Atlas subsystems:

1. **Provider System**: Different views of provider capabilities
2. **Agent System**: Context-specific agent configurations
3. **Knowledge System**: Different document representation levels
4. **Configuration System**: Role-specific configuration views

## Performance Considerations

Marshmallow offers several performance optimization options:

1. **Field-Level Caching**:
   - Use Marshmallow's `fields.Pluck` for efficient access to nested data
   - Leverage `many=True` parameter for batch operations
   - Use `unknown=EXCLUDE` to avoid validation overhead for irrelevant fields

2. **Partial Loading**:
   - Use `partial=True` for schema validation with incomplete data
   - Leverage `only=['field1', 'field2']` for loading specific fields
   - Use `load_only=['internal_field']` to exclude internal fields from serialization

3. **Schema Reuse**:
   - Pre-instantiate commonly used schemas rather than creating instances per operation
   - Use schema registries for related schema families
   - Organize schemas in inheritance hierarchies to minimize duplication

## Pattern Variations

### Static Perspectives

Fixed set of predefined perspectives using Marshmallow schemas. Simple to implement and reason about.

```python
# Example static perspective definitions
user_schema = UserPerspective()
admin_schema = AdminPerspective()
developer_schema = DeveloperPerspective()

# Usage with static schemas
user_view = user_schema.dump(data)
admin_view = admin_schema.dump(data)
```

### Dynamic Perspectives

Perspectives can be added and removed at runtime using Marshmallow's dynamic schema capabilities.

```python
# Example dynamic perspective creation
minimal_fields = ["id", "name", "status"]
detailed_fields = minimal_fields + ["description", "metadata", "history"]

minimal_schema = perspective_manager.create_perspective(
    BaseSchema, minimal_fields, "MinimalView")
detailed_schema = perspective_manager.create_perspective(
    BaseSchema, detailed_fields, "DetailedView")
```

### Hierarchical Perspectives

Perspectives organized in a hierarchy using Marshmallow schema inheritance.

```python
# Base schema with common fields
class BaseSchema(Schema):
    id = fields.String()
    created_at = fields.DateTime()

# User perspective adds user-relevant fields
class UserSchema(BaseSchema):
    name = fields.String()
    description = fields.String()

# Admin perspective adds administrative fields
class AdminSchema(UserSchema):
    status = fields.String()
    permissions = fields.List(fields.String())

# Developer perspective adds technical details
class DeveloperSchema(AdminSchema):
    debug_info = fields.Dict()
    performance_metrics = fields.Dict()
```

## Integration with Other Patterns

- **Reactive Event Mesh**: Events can trigger perspective changes and schema validation
- **Temporal Versioning**: Perspectives can apply to different versioned states
- **State Projection**: Closely related pattern for projected state using immutable data
- **Effect System**: Perspective transformations can be modeled as explicit effects

## Related Patterns

- Strategy Pattern: Different serialization strategies
- Decorator Pattern: Enhancing schemas with additional behavior
- Adapter Pattern: Converting between different data representations
- View Model (MVVM): Similar to perspective concept in UI frameworks
- Lens Pattern (Functional Programming): Focused access to parts of data structures