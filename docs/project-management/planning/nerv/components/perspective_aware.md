---
title: Perspective-Aware
---

# PerspectiveAware Implementation

## Overview

The PerspectiveAware class implements the Perspective Shifting pattern, providing multiple views of the same underlying data based on context, abstraction level, or user role.

## Architectural Role

PerspectiveAware empowers components to adapt their data presentation:

- **Configuration**: Different views for different user roles
- **API Responses**: Context-appropriate data representations
- **Knowledge System**: Domain-specific views of the same knowledge
- **Telemetry**: Different aggregation levels for monitoring
- **Documentation**: Adapting to user expertise levels
- **Validation**: Combined schema validation and transformation

## Implementation Details

The PerspectiveAware implementation features:

1. **Thread-safe perspective management** using read-write locks
2. **Dynamic perspective registration** at runtime
3. **Default perspective fallback** for unrecognized requests
4. **Perspective metadata** for discovery and selection
5. **Update safety** to maintain perspective consistency
6. **Schema validation** integrated with transformations
7. **Nested perspectives** for complex object hierarchies

## Implementation Library: Marshmallow

The PerspectiveAware component is implemented using the [Marshmallow](https://marshmallow.readthedocs.io/) library, which provides structured data serialization, validation, and transformation:

### Core Library Integration

| Marshmallow Feature | Usage in PerspectiveAware | Integration Details |
|---------------------|---------------------------|---------------------|
| `Schema` class | Define perspective schemas | Core building block for all perspectives |
| Field declarations | Define specific field types | Strongly-typed perspective fields |
| `Meta` class options | Configure perspective behavior | Control perspective display and validation rules |
| `only`/`exclude` parameters | Create field subsets | Dynamic perspective field selection |
| Post-processing hooks | Custom perspective transformations | Advanced perspective logic |
| Nested schemas | Hierarchical perspective composition | Complex nested object transformations |
| Custom field types | Specialized data handling | Domain-specific perspective fields |
| Validation errors | Structured validation issues | Actionable error reporting |

### Core Implementation Structure

```python
from typing import Dict, Any, List, Type, Optional, Generic, TypeVar
from threading import RLock
from marshmallow import Schema, fields, post_load, pre_dump, ValidationError

T = TypeVar('T')  # Source data type
P = TypeVar('P')  # Perspective result type

class PerspectiveAware(Generic[T, P]):
    """Thread-safe container for multiple data perspectives.
    
    Provides different views of the same underlying data using
    Marshmallow schemas for transformation and validation.
    """
    
    def __init__(self, data: T, default_perspective: str = "default"):
        """Initialize with source data and default perspective name."""
        self._data = data
        self._default_perspective = default_perspective
        self._perspectives: Dict[str, Schema] = {}
        self._perspective_metadata: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()
        
    def add_perspective(self, name: str, schema: Type[Schema], 
                        metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register a new perspective schema with optional metadata."""
        with self._lock:
            self._perspectives[name] = schema()
            self._perspective_metadata[name] = metadata or {}
            
    def view(self, perspective: Optional[str] = None) -> P:
        """Get data through the specified perspective."""
        perspective = perspective or self._default_perspective
        
        with self._lock:
            if perspective not in self._perspectives:
                perspective = self._default_perspective
                
            schema = self._perspectives[perspective]
            return schema.dump(self._data)
            
    def get_available_perspectives(self) -> List[str]:
        """Get list of all registered perspective names."""
        with self._lock:
            return list(self._perspectives.keys())
            
    def update_data(self, data: T) -> None:
        """Update the underlying source data."""
        with self._lock:
            self._data = data
```

### Schema Definition Patterns

The Marshmallow library enables sophisticated schema designs:

```python
from marshmallow import Schema, fields, validate, validates, ValidationError

# Base perspective with common fields
class BasePerspective(Schema):
    """Base schema with common fields across perspectives."""
    id = fields.String(required=True)
    name = fields.String(required=True)
    created_at = fields.DateTime(required=True)
    
    class Meta:
        """Configuration for the schema's behavior."""
        ordered = True          # Preserve field order
        unknown = "exclude"     # Ignore unknown fields
        
# Public perspective with limited fields
class PublicPerspective(BasePerspective):
    """Public-facing perspective with minimal information."""
    description = fields.String()
    
    class Meta(BasePerspective.Meta):
        """Control which fields are included."""
        fields = ("id", "name", "description")
        
# User perspective with more fields        
class UserPerspective(BasePerspective):
    """User-facing perspective with personal information."""
    email = fields.Email()
    preferences = fields.Dict()
    
    @validates("preferences")
    def validate_preferences(self, preferences):
        """Custom validation for preferences."""
        if "theme" in preferences and preferences["theme"] not in ["light", "dark", "system"]:
            raise ValidationError("Invalid theme setting")
            
    @post_load
    def format_data(self, data, **kwargs):
        """Post-processing after schema load."""
        if "email" in data:
            # Normalize email to lowercase
            data["email"] = data["email"].lower()
        return data
        
# Admin perspective with all details
class AdminPerspective(UserPerspective):
    """Admin perspective with complete access."""
    role = fields.String(validate=validate.OneOf(["user", "moderator", "admin"]))
    internal_data = fields.Dict()
    
    class Meta(BasePerspective.Meta):
        """Include all fields."""
        additional = ("email", "preferences", "role", "internal_data", 
                      "created_at", "updated_at")
        
# Analytics perspective with aggregated metrics
class AnalyticsPerspective(BasePerspective):
    """Analytics perspective with usage statistics."""
    activity_count = fields.Integer()
    last_active = fields.DateTime()
    
    @pre_dump
    def compute_metrics(self, data, **kwargs):
        """Pre-processing to compute analytics before serialization."""
        result = {**data}
        if hasattr(data, "activity"):
            result["activity_count"] = len(data.activity)
            result["last_active"] = max(a.timestamp for a in data.activity) if data.activity else None
        return result
```

## Key Components

- **Underlying Data**: The raw source data stored internally
- **Schema Classes**: Marshmallow schemas defining structure and validation
- **Schema Registry**: Collection of named schemas for different perspectives
- **Default Perspective**: Fallback schema when no perspective is specified
- **Transformation Hooks**: Custom pre/post processing functions
- **Validation Rules**: Field-level and schema-level validation

## Performance Considerations

### Schema Efficiency

- **Schema Reuse**: Pre-instantiate schemas rather than creating on demand
- **Field Selection**: Use `only` parameter to select specific fields when possible
- **Partial Loading**: Use `partial=True` for validation with incomplete data

```python
# Performance optimization with field selection
def get_optimized_view(self, perspective, fields=None):
    """Get data with optional field filtering for performance."""
    with self._lock:
        schema = self._perspectives[perspective]
        # Only serialize requested fields
        if fields:
            return schema.dump(self._data, only=fields)
        return schema.dump(self._data)
```

### Caching Strategy

- **View Caching**: Cache frequent perspective results
- **Selective Invalidation**: Clear caches on specific field updates
- **TTL Control**: Time-based cache invalidation for perspectives

```python
# Implement perspective result caching
def view_with_cache(self, perspective, max_age_seconds=60):
    """Get data with caching for frequently used perspectives."""
    current_time = time.time()
    cache_key = f"{perspective}_{id(self._data)}"
    
    # Check cache first
    if cache_key in self._cache:
        cached_at, result = self._cache[cache_key]
        if current_time - cached_at < max_age_seconds:
            return result
    
    # Cache miss - generate and store in cache
    result = self.view(perspective)
    self._cache[cache_key] = (current_time, result)
    return result
```

### Memory Management

- **Lazy Transformation**: Transform perspectives only when needed
- **Field Exclusion**: Avoid serializing large fields when unnecessary
- **Reference Preservation**: Avoid unnecessary copies of immutable data

## Integration with Atlas

PerspectiveAware with Marshmallow is used throughout Atlas:

### Provider System Integration

```python
# Provider capability schemas with different perspectives
class ProviderCapabilitySchema(Schema):
    """Base schema for provider capabilities."""
    provider_id = fields.String(required=True)
    models = fields.List(fields.String())
    features = fields.Dict()
    
# Client perspective - limited to essential info
class ClientCapabilitySchema(ProviderCapabilitySchema):
    """Client-focused view of provider capabilities."""
    class Meta:
        fields = ("provider_id", "models", "features.streaming", 
                  "features.vision", "features.tools")
    
# System perspective - complete information
class SystemCapabilitySchema(ProviderCapabilitySchema):
    """System-level view with complete provider information."""
    # All fields included by default
    api_details = fields.Dict()
    rate_limits = fields.Dict()
    
# Usage in provider registry
provider_registry.add_perspective(
    "client",
    ClientCapabilitySchema,
    {"description": "Client-facing provider information"}
)

provider_registry.add_perspective(
    "system",
    SystemCapabilitySchema,
    {"description": "Complete provider capability information"}
)
```

### Knowledge Document Integration

```python
# Document schemas with different perspectives
class DocumentSchema(Schema):
    """Base schema for knowledge documents."""
    id = fields.String(required=True)
    title = fields.String(required=True)
    content = fields.String(required=True)
    metadata = fields.Dict()
    
# Search result perspective - focused on relevance
class SearchResultSchema(DocumentSchema):
    """Search-optimized document view."""
    class Meta:
        fields = ("id", "title", "snippet", "relevance_score")
        
    snippet = fields.String()
    relevance_score = fields.Float()
    
    @pre_dump
    def generate_snippet(self, data, **kwargs):
        """Generate a search snippet from the document content."""
        if not hasattr(data, "snippet"):
            data = {**data}
            data["snippet"] = generate_snippet(data["content"], max_length=200)
        return data
    
# Detailed document perspective
class DetailedDocumentSchema(DocumentSchema):
    """Complete document with all details."""
    # Uses all fields with additional processing
    chunks = fields.List(fields.Dict())
    embeddings = fields.Dict()
    
    @post_load
    def format_content(self, data, **kwargs):
        """Format content for display."""
        data["content_html"] = markdown_to_html(data["content"])
        return data
```

### Configuration System Integration

```python
# Configuration schemas with different access levels
class ConfigSchema(Schema):
    """Base configuration schema."""
    version = fields.String()
    environment = fields.String()
    settings = fields.Dict()
    
# User settings perspective
class UserConfigSchema(ConfigSchema):
    """User-accessible configuration settings."""
    class Meta:
        fields = ("version", "settings.ui", "settings.preferences")
        
# Admin settings perspective
class AdminConfigSchema(ConfigSchema):
    """Administrator configuration settings."""
    # Additional fields for admins
    api_keys = fields.Dict()
    service_endpoints = fields.Dict()
    
    @validates("settings")
    def validate_admin_settings(self, settings):
        """Validate admin-specific settings."""
        if "security" in settings and "log_level" in settings["security"]:
            if settings["security"]["log_level"] not in ["INFO", "DEBUG", "WARNING", "ERROR"]:
                raise ValidationError("Invalid log level")
```

## Usage Patterns

### Basic Multiple Views

Use the Marshmallow schemas to define different perspectives:

```python
# Define the perspective-aware container with source data
user_data = get_user_from_database(user_id)
user_perspectives = PerspectiveAware(user_data)

# Add different perspectives using Marshmallow schemas
user_perspectives.add_perspective("public", PublicUserSchema)
user_perspectives.add_perspective("profile", ProfileUserSchema)
user_perspectives.add_perspective("admin", AdminUserSchema)

# Get data from specific perspective
public_view = user_perspectives.view("public")
profile_view = user_perspectives.view("profile")
```

### Dynamic Field Selection

Create perspectives with dynamic field selection:

```python
# Base schema with all possible fields
class UserSchema(Schema):
    id = fields.String(required=True)
    username = fields.String(required=True)
    email = fields.Email()
    profile = fields.Nested(ProfileSchema)
    settings = fields.Dict()
    history = fields.List(fields.Nested(ActivitySchema))
    
# Create dynamic perspectives based on needed fields
def create_custom_perspective(field_set_name):
    """Create a custom perspective based on predefined field sets."""
    field_sets = {
        "minimal": ["id", "username"],
        "contact": ["id", "username", "email"],
        "full_profile": ["id", "username", "email", "profile"],
        "complete": None  # All fields
    }
    
    class CustomSchema(UserSchema):
        class Meta:
            fields = field_sets[field_set_name]
            
    return CustomSchema

# Add dynamic perspectives
for perspective in ["minimal", "contact", "full_profile", "complete"]:
    user_perspectives.add_perspective(
        perspective, 
        create_custom_perspective(perspective)
    )
```

### Validation-Integrated Perspectives

Combine validation with perspectives:

```python
# Schema with validation rules
class DocumentEditSchema(Schema):
    """Document schema with edit validation."""
    title = fields.String(required=True, validate=validate.Length(min=3, max=100))
    content = fields.String(required=True)
    tags = fields.List(fields.String(), validate=validate.Length(max=10))
    
    @validates("content")
    def validate_content(self, content):
        """Validate content meets minimum requirements."""
        if len(content.strip()) < 50:
            raise ValidationError("Content must be at least 50 characters")
            
# Use for validation during update
def update_document(doc_id, updates):
    """Update document with validation."""
    document = get_document(doc_id)
    doc_perspectives = PerspectiveAware(document)
    doc_perspectives.add_perspective("edit", DocumentEditSchema)
    
    try:
        # Validate updates against edit schema
        schema = DocumentEditSchema()
        validated_data = schema.load(updates)
        
        # Apply validated updates
        update_document_in_db(doc_id, validated_data)
        return True, None
    except ValidationError as err:
        return False, err.messages
```

### Inheritance-Based Perspectives

Build perspective hierarchies:

```python
# Base perspective with essential fields
class BasePerspective(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)

# User perspective adds user fields
class UserPerspective(BasePerspective):
    email = fields.Email()
    preferences = fields.Dict()

# Moderator perspective adds moderation fields
class ModeratorPerspective(UserPerspective):
    moderation_actions = fields.List(fields.Dict())
    pending_items = fields.Integer()

# Admin perspective adds system fields
class AdminPerspective(ModeratorPerspective):
    system_access = fields.Dict()
    analytics = fields.Dict()
```

## Relationship to Patterns

Implements:
- **[Perspective Shifting](../patterns/perspective_shifting.md)**: Primary implementation using Marshmallow schemas

Supports:
- **[Reactive Event Mesh](../patterns/reactive_event_mesh.md)**: Can emit events on perspective changes
- **[Temporal Versioning](../patterns/temporal_versioning.md)**: Can maintain perspective history with versioned schemas
- **[State Projection](../patterns/state_projection.md)**: Complementary approach for state views
- **[Effect System](../patterns/effect_system.md)**: Perspective transformations can be modeled as explicit effects