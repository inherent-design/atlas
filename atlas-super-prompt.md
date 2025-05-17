# Atlas Development Super-Prompt

## Project Context

Atlas is an advanced multi-modal agent framework currently in accelerated development for a June 30, 2025 deadline, with commercial launch planned for July 2025. The project follows a clean break philosophy, prioritizing best-in-class API design over backward compatibility.

## Current Status (May 16, 2025)

The provider system has been restructured with implementations moved to a dedicated directory and schema validation integrated for all provider implementations (Anthropic, OpenAI, Ollama, and Mock). The next priorities are:

1. **Streaming Infrastructure Enhancement** with schema validation and thread-safety
2. **Core Services Layer Implementation** with thread-safe buffer system and event system
3. **Knowledge System Refinement** with hybrid search capabilities

## Key Implementation Tasks

### 1. Stream Handler Schema Migration (High Priority) - Target: May 18, 2025

The streaming system needs to be enhanced with schema validation for consistent and robust interfaces.

**Required Components:**
- Schema validation for stream handlers and controls
- Validation for stream state transitions
- Thread-safe buffer implementation with flow control
- Schema-validated stream control operations (pause/resume/cancel)

**Implementation Strategy:**
1. Create `atlas/schemas/streaming.py` with new schema definitions:
   - `StreamStateSchema` - for validating stream state transitions
   - `StreamControlSchema` - for stream control interface validation
   - `StreamHandlerSchema` - for core handler validation
   - `StreamBufferConfigSchema` - for buffer configuration validation

2. Update `StreamHandler` and `EnhancedStreamHandler` classes to use schema validation
3. Implement validation decorators for stream operation methods
4. Update all provider implementations to use the validated streaming interfaces
5. Add comprehensive error mapping for streaming validation errors

**Key Files to Modify:**
- `atlas/schemas/streaming.py` (create)
- `atlas/providers/streaming/base.py` (update)
- `atlas/providers/streaming/control.py` (update)
- `atlas/providers/streaming/buffer.py` (update)
- `atlas/providers/implementations/*.py` (update stream implementations)

### 2. Core Services Implementation (High Priority) - Target: May 20-25, 2025

The core services layer will provide foundational abstractions for boundary interfaces, buffer systems, event communication, state management, and resource lifecycle.

**Required Components:**
- System boundary interfaces for validation at API boundaries
- Thread-safe buffer implementation with flow control
- Event system with subscription management
- State management with versioning
- Resource lifecycle management with dependency tracking

**Implementation Strategy:**
1. Create core services module structure:
   - `atlas/core/services/__init__.py`
   - `atlas/core/services/types.py` - Type system for services
   - `atlas/core/services/boundaries.py` - Boundary validation
   - `atlas/core/services/buffer.py` - Generic buffer system
   - `atlas/core/services/events.py` - Event system
   - `atlas/core/services/state.py` - State management
   - `atlas/core/services/resources.py` - Resource lifecycle

2. Define TypeVars and generic types for core services
3. Implement boundary interface with validation results
4. Create thread-safe buffer implementation with rate limiting and batching
5. Implement event bus with subscription and filtering
6. Create state machine with versioned container and transitions
7. Implement resource manager with dependency tracking and cleanup

**Key Implementation Pattern:**
```python
# Example Boundary Interface Pattern

from typing import Generic, TypeVar, Protocol, Dict, Any, Union
from enum import Enum
from dataclasses import dataclass

T = TypeVar('T')
U = TypeVar('U')

class ValidationStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    UNKNOWN = "unknown"

@dataclass
class ValidationResult(Generic[T]):
    status: ValidationStatus
    value: Optional[T] = None
    errors: Dict[str, str] = field(default_factory=dict)
    
class Boundary(Protocol[T, U]):
    def validate(self, data: Any) -> ValidationResult[T]:
        """Validate incoming data against the boundary."""
        ...
    
    def process(self, validated_data: T) -> U:
        """Process validated data to produce output."""
        ...
    
    def handle_error(self, error: ValidationResult[T]) -> None:
        """Handle validation error."""
        ...
```

### 3. Hybrid Knowledge System (Medium Priority) - Target: May 25, 2025

The knowledge system needs to be enhanced with hybrid search capabilities, combining vector and keyword search.

**Required Components:**
- Comprehensive hybrid search implementation
- Schema validation for search parameters
- Configurable weighting for semantic and keyword scores
- Advanced document chunking strategies
- Knowledge caching system

**Implementation Strategy:**
1. Finalize hybrid search implementation in `atlas/knowledge/hybrid_search.py`
2. Add schema validation for search parameters in `atlas/schemas/knowledge.py`
3. Implement configurable weighting between semantic and keyword scores
4. Create document chunking enhancements in `atlas/knowledge/chunking.py`
5. Develop knowledge caching system in `atlas/knowledge/caching.py`

**Implementation Pattern for Schema Validation:**
```python
# Example knowledge schema validation pattern

from atlas.schemas.base import AtlasSchema
from marshmallow import fields, validates, validates_schema, ValidationError

class HybridSearchSettingsSchema(AtlasSchema):
    semantic_weight = fields.Float(required=False, default=0.7)
    keyword_weight = fields.Float(required=False, default=0.3)
    merge_strategy = fields.String(
        required=False, 
        default="weighted_score",
        validate=validate.OneOf(
            ["weighted_score", "score_add", "score_multiply", "rank_fusion"]
        )
    )
    
    @validates("semantic_weight")
    def validate_semantic_weight(self, value):
        if value < 0 or value > 1:
            raise ValidationError("Semantic weight must be between 0 and 1")
    
    @validates("keyword_weight")
    def validate_keyword_weight(self, value):
        if value < 0 or value > 1:
            raise ValidationError("Keyword weight must be between 0 and 1")
    
    @validates_schema
    def validate_weights(self, data, **kwargs):
        if "semantic_weight" in data and "keyword_weight" in data:
            total = data["semantic_weight"] + data["keyword_weight"]
            if total <= 0:
                raise ValidationError("Sum of weights must be positive")
```

## Schema Validation Architecture

Atlas has established a schema validation system using Marshmallow with the following key components:

### 1. Base Schema Classes
- `AtlasSchema` - Base schema for all Atlas schemas
- `EnumField` - Field for enum values
- `JsonField` - Field for JSON data

### 2. Schema Organization
To resolve circular imports, schemas are organized in a two-level architecture:
- `schemas/definitions/` - Pure schema definitions without post_load
- `schemas/*.py` - Schema implementations with object creation

### 3. Validation Decorators
- `validate_with_schema` - For function return validation
- `validate_args` - For function parameter validation
- `validate_class_init` - For class init validation
- `create_schema_validated` - For creating schema-validated classes

### 4. Interface Example
```python
# Example schema validation implementation

from atlas.schemas.base import AtlasSchema
from atlas.schemas.validation import validate_with_schema, create_schema_validated

# Define the schema
class StreamStateSchema(AtlasSchema):
    value = fields.String(required=True)
    
    @validates("value")
    def validate_state(self, value):
        valid_states = [
            "initializing", "active", "paused", 
            "cancelled", "completed", "error"
        ]
        if value not in valid_states:
            raise ValidationError(f"Invalid state: {value}. Must be one of: {valid_states}")
    
    @post_load
    def make_object(self, data, **kwargs):
        # Convert to enum
        from atlas.providers.streaming.control import StreamState
        return StreamState(data["value"])

# Schema instance for convenient use
stream_state_schema = StreamStateSchema()

# Decorate a class for validation
@create_schema_validated(my_schema)
class ValidatedClass:
    def __init__(self, field1, field2, **kwargs):
        self.field1 = field1
        self.field2 = field2
        # Additional initialization
```

## Streaming Infrastructure Reference

The streaming system in Atlas provides enhanced control for LLM response streams with the following key components:

### 1. Stream Control Interface
The `StreamControl` interface defines operations for controlling streams:
- `pause()` - Temporarily pause the stream
- `resume()` - Resume a paused stream
- `cancel()` - Cancel the stream entirely
- `register_state_change_callback()` - Add callback for state changes
- `register_content_callback()` - Add callback for new content

### 2. Stream Buffer System
The buffer system manages content flow with thread safety:
- `StreamBuffer` - Thread-safe buffer for content
- `RateLimitedBuffer` - Buffer with rate limiting
- `BatchingBuffer` - Buffer with content batching

### 3. Stream Handler Implementation
The handler processes provider-specific streams:
- `StreamHandler` - Base handler interface
- `EnhancedStreamHandler` - Handler with advanced controls
- `StringStreamHandler` - Simple string-based implementation

## Core Services Architecture

The planned core services layer provides foundational capabilities:

### 1. Boundary System
- Validates data crossing system boundaries
- Maps schema errors to domain-specific errors
- Provides consistent error reporting

### 2. Buffer System
- Thread-safe content buffering
- Rate limiting and flow control
- Resource cleanup and monitoring

### 3. Event System
- Publisher/subscriber model for events
- Event filtering and routing
- Event history tracking

### 4. State Management
- Versioned state container
- Validated state transitions
- State projection capabilities

### 5. Resource Management
- Resource lifecycle with initialization and cleanup
- Dependency tracking between resources
- Connection pooling and reuse

## Knowledge System Architecture

The knowledge system provides document storage and retrieval:

### 1. Document Storage
- Document chunking with metadata
- Schema validation for documents and chunks
- Document version tracking

### 2. Retrieval System
- Vector-based semantic search
- Keyword-based BM25 search
- Hybrid search with configurable weights
- Result merging strategies

### 3. Caching System
- Document and query caching
- Invalidation strategies
- Metrics and observability

## Example Structure

The following examples should be created to demonstrate new functionality:

1. `examples/07_enhanced_streaming.py` - Demonstrates stream control
2. `examples/12_hybrid_retrieval.py` - Shows hybrid search capabilities
3. `examples/13_advanced_chunking.py` - Illustrates chunking strategies
4. `examples/14_knowledge_caching.py` - Demonstrates caching
5. `examples/17_boundary_validation.py` - Shows boundary validation

## Implementation Guidelines

1. **Schema First Approach**
   - Define schemas before implementing classes
   - Use schema validation for all API boundaries
   - Map validation errors to domain-specific errors

2. **Thread Safety**
   - Use proper locking for shared state
   - Implement thread-safe operations for all services
   - Ensure proper resource cleanup

3. **Testing Strategy**
   - Create unit tests for each component
   - Test boundary conditions and error cases
   - Verify thread safety with concurrent tests

4. **Documentation**
   - Add comprehensive docstrings
   - Create example scripts for new functionality
   - Update architecture documentation

## Timeline

- **May 17-19, 2025**: Stream handler schema validation
- **May 20-22, 2025**: Core services layer foundation
- **May 23-25, 2025**: Hybrid knowledge system enhancements
- **May 26-31, 2025**: Testing and documentation
- **June 1-7, 2025**: Multi-agent orchestration
- **June 8-14, 2025**: Enterprise features
- **June 15-30, 2025**: Final stabilization
- **July 2025**: Commercial launch