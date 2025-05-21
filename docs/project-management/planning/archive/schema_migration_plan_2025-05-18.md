---
title: Schema Migration
---

# Schema Validation Migration Plan - May 18, 2025

## Overview

This document outlines the plan to migrate Atlas from legacy typing approaches (TypedDict, dataclasses) to consistent Marshmallow schema validation throughout the codebase. This migration will significantly enhance runtime type safety, improve API consistency, and enable better error handling.

## Current State Assessment

### Schema Implementation

The Atlas project has a well-designed schema validation system in the `/atlas/schemas/` directory:

- **Base Module**: `base.py` defines `AtlasSchema` and common fields
- **Schema Modules**: Organized by domain (messages, providers, options, etc.)
- **Validation Utilities**: Decorator-based validation for functions and classes
- **Schema Registry**: Exported schema instances for convenient use

### Legacy Typing

Several core components still use legacy typing approaches:

1. **Dataclasses**:
   - `providers/messages.py`: `ModelMessage`, `MessageContent`, `TokenUsage`, etc.
   - `providers/options.py`: `ProviderOptions`
   - `knowledge/chunking.py`: `DocumentChunk`
   - `tools/base.py`: Tool-related classes

2. **TypedDict**:
   - `core/types.py`: Contains extensive TypedDict definitions
   - `schemas/types.py`: Some TypedDict-based types
   - `graph/state.py`: Uses TypedDict for state representation

3. **Mixed Implementations**:
   - Some components like `providers/messages.py` already use schema validation for some operations but still rely on dataclasses for the base implementation

## Implementation Strategy

### 1. Migration Approach

We will use a **staged migration** following these principles:

1. **Schema-First**: Define or update schemas first, then implement schema-validated classes
2. **Backward Compatibility**: Maintain API compatibility during transition
3. **Outside-In**: Start with external API boundaries, then migrate internal components
4. **Test-Driven**: Add validation tests for each migrated component

### 2. Core Infrastructure

1. **Create SchemaValidated Wrappers**:
   - Ensure `create_schema_validated` decorator is robust
   - Add conversion utilities between schema types and domain objects

2. **Update Schema Base Classes**:
   - Enhance `AtlasSchema` with improved error reporting
   - Add nested validation support for complex structures

### 3. Migration Sequence

#### Phase 1: Core Data Types (May 12-14, 2025)

1. **Core Message Types**:
   - Migrate `providers/messages.py` first:
     - Update `ModelMessage`, `MessageContent`, `TextContent`, etc.
     - Replace duplicate `ModelRole` with schema-validated version
     - Add validation decorators to factory methods

2. **Provider Options**:
   - Migrate `providers/options.py`:
     - Convert `ProviderOptions` to schema-validated class
     - Update capability handling to use schema validation
     - Ensure environment variable integration works correctly

#### Phase 2: Knowledge and Tools (May 15-16, 2025)

1. **Knowledge Components**:
   - Migrate `knowledge/chunking.py`:
     - Convert `DocumentChunk` to schema-validated class
     - Ensure chunking strategies use validation
     - Add validation to retrieval filter structures

2. **Tool Definitions**:
   - Migrate `tools/base.py`:
     - Update tool registration to use schema validation
     - Convert tool parameter validation to use schemas
     - Ensure tool execution validates inputs/outputs

#### Phase 3: Core Types and State (May 17-19, 2025)

1. **Core TypedDict Migration**:
   - Migrate `core/types.py`:
     - Move TypedDict definitions to appropriate schema modules
     - Replace with imports from schema modules
     - Update Protocol definitions to use schema types

2. **Graph State Validation**:
   - Update `graph/state.py`:
     - Add schema validation for state transitions
     - Ensure LangGraph compatibility is maintained

#### Phase 4: Finalization (May 20-21, 2025)

1. **API Boundary Validation**:
   - Add validation decorators to public methods
   - Ensure consistent error handling across API boundaries

2. **Update Documentation and Examples**:
   - Update documentation to reflect schema approach
   - Create examples demonstrating validation usage
   - Add tutorials for schema extension

## Implementation Details

### 1. Schema-Validated Class Migration Pattern

For each class to migrate, we will:

1. **Define/Update Schema**:
   ```python
   class MessageSchema(AtlasSchema):
       role = EnumField(MessageRole, required=True)
       content = fields.Raw(required=True)
       name = fields.String(required=False)

       @post_load
       def make_object(self, data: Dict[str, Any], **kwargs) -> Message:
           return Message(**data)
   ```

2. **Create Schema-Validated Class**:
   ```python
   @create_schema_validated(lambda: message_schema)
   class Message:
       def __init__(self, role: MessageRole, content: Any, name: Optional[str] = None):
           self.role = role
           self.content = content
           self.name = name
   ```

3. **Add Factory Methods**:
   ```python
   @classmethod
   def from_dict(cls, data: Dict[str, Any]) -> "Message":
       return message_schema.load(data)

   def to_dict(self) -> Dict[str, Any]:
       return message_schema.dump(self)
   ```

### 2. TypedDict Migration Pattern

For TypedDict definitions:

1. **Move TypedDict to Schema Type Module**:
   ```python
   # Before (in core/types.py)
   class MessageDict(TypedDict, total=False):
       role: str
       content: Union[str, List[MessageContentItem], MessageContentItem]
       name: NotRequired[str]

   # After (in schemas/types.py)
   class MessageDict(ValidatedDict):
       role: str
       content: Union[str, List[ContentDict], ContentDict]
       name: NotRequired[str]
   ```

2. **Update Imports**:
   ```python
   # Before
   from atlas.core.types import MessageDict

   # After
   from atlas.schemas.types import MessageDict
   ```

### 3. API Validation Pattern

For API boundaries:

1. **Function Parameter Validation**:
   ```python
   @validate_args({
       "request": model_request_schema
   })
   def process_request(request: Dict[str, Any]) -> Dict[str, Any]:
       # Implementation with validated request
   ```

2. **Return Value Validation**:
   ```python
   @validate_with_schema(model_response_schema)
   def generate_response(prompt: str) -> Dict[str, Any]:
       # Implementation with validated return value
   ```

3. **Class Initialization Validation**:
   ```python
   @validate_class_init({
       "options": provider_options_schema
   })
   class Provider:
       def __init__(self, options: Dict[str, Any]):
           # Implementation with validated options
   ```

## Compatibility Considerations

1. **Backward Compatibility**:
   - Maintain existing public API signatures
   - Add deprecation warnings for legacy methods
   - Provide transition helpers for common patterns

2. **Performance**:
   - Monitor validation overhead in critical paths
   - Add caching for frequently validated structures
   - Consider selective validation for high-performance code paths

3. **Error Handling**:
   - Ensure consistent error messages
   - Map validation errors to appropriate domain errors
   - Maintain debugging context in error chains

## Testing Strategy

1. **Unit Tests**:
   - Add validation-specific test cases
   - Test boundary conditions and edge cases
   - Ensure error messages are helpful

2. **Integration Tests**:
   - Verify validation across component boundaries
   - Test error propagation and handling
   - Ensure LangGraph integration works correctly

3. **Performance Tests**:
   - Measure validation overhead
   - Verify caching mechanisms work
   - Ensure no regression in critical paths

## Timeline

| Phase                 | Tasks                              | Start Date   | End Date     |
| --------------------- | ---------------------------------- | ------------ | ------------ |
| 1: Core Data Types    | Migrate messages.py, options.py    | May 12, 2025 | May 14, 2025 |
| 2: Knowledge & Tools  | Migrate chunking.py, tools/base.py | May 15, 2025 | May 16, 2025 |
| 3: Core Types & State | Migrate types.py, graph/state.py   | May 17, 2025 | May 19, 2025 |
| 4: Finalization       | API boundaries, docs, examples     | May 20, 2025 | May 21, 2025 |

## Success Criteria

1. **Technical**:
   - All core data structures use schema validation
   - Consistent error handling across API boundaries
   - No TypedDict definitions outside of schema modules
   - All public methods validate inputs and outputs

2. **User Experience**:
   - Clear, helpful error messages
   - Improved API consistency
   - Strong type hints for IDE support
   - Detailed validation errors for debugging

3. **Development Experience**:
   - Simpler type safety mechanisms
   - Consistent validation approach
   - Better tooling for extension and customization
   - Clearer code organization

## Conclusion

This migration will significantly enhance Atlas's type safety and validation capabilities while maintaining backward compatibility. The staged approach allows for careful testing and validation at each step, ensuring a smooth transition with minimal disruption.
