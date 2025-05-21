"""
Schema definitions for Atlas components.

This module provides a hierarchical system of schemas:

1. Base Schemas: Foundation schema classes with common functionality
    - Located in schemas/base.py
    - Provides AtlasSchema base class, EnumField, JsonField, etc.

2. Schema Definitions: Pure data validation schemas without implementation bindings
    - Located in schemas/definitions/*.py
    - Pure schema structures with validation rules
    - No reference to implementation classes (avoids circular imports)
    - Example: schemas/definitions/services.py

3. Implementation Schemas: Extend definitions with implementation-specific logic
    - Located in the root schemas/ directory
    - Import and extend the pure definitions
    - Add post_load methods that convert validated data to implementation objects
    - Example: schemas/services.py extends schemas/definitions/services.py

Usage:
1. For validation only: Import schemas from definitions
   ```python
   from atlas.schemas.definitions.services import service_schema
   validated_data = service_schema.load(input_data)
   ```

2. For validation and object creation: Import from implementation schemas
   ```python
   from atlas.schemas.services import service_schema
   service_obj = service_schema.load(input_data)
   ```

3. For implementation classes/protocols: Import directly from implementation schemas
   ```python
   from atlas.schemas.services import BufferProtocol
   ```

This architecture allows for clear separation between validation rules and
implementation details, avoiding circular import issues while maintaining
a clean organization.
"""
