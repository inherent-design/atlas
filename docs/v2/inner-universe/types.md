---
title: Types
---

# Inner Universe Core Type Definitions

This document defines the core data types for the Inner Universe persistence layer, providing bare minimum definitions required to interface with SpacetimeDB.

## Primitive Types

Inner Universe leverages SpacetimeDB's built-in type system which maps to the following Rust types:

| SpacetimeDB Type  | Rust Type        | Description                                  |
| ----------------- | ---------------- | -------------------------------------------- |
| `bool`            | `bool`           | Boolean value (true/false)                   |
| `u8`              | `u8`             | 8-bit unsigned integer                       |
| `i8`              | `i8`             | 8-bit signed integer                         |
| `u16`             | `u16`            | 16-bit unsigned integer                      |
| `i16`             | `i16`            | 16-bit signed integer                        |
| `u32`             | `u32`            | 32-bit unsigned integer                      |
| `i32`             | `i32`            | 32-bit signed integer                        |
| `u64`             | `u64`            | 64-bit unsigned integer                      |
| `i64`             | `i64`            | 64-bit signed integer                        |
| `f32`             | `f32`            | 32-bit floating point                        |
| `f64`             | `f64`            | 64-bit floating point                        |
| `string`          | `String`         | UTF-8 string                                 |
| `bytes`           | `Vec<u8>`        | Byte array                                   |
| `array<T>`        | `Vec<T>`         | Variable-length array                        |
| `map<K, V>`       | `BTreeMap<K, V>` | Map with keys of type K and values of type V |
| `option<T>`       | `Option<T>`      | Optional value of type T                     |
| `albumlabel{...}` | Custom struct    | User-defined struct                          |

## Core Identity Types

```rust
// Identity uniquely identifies a client/user
use spacetimedb::Identity;

// Timestamp represents a point in time (milliseconds since UNIX epoch)
use spacetimedb::Timestamp;
```

## Entity System Types

```rust
// Unique identifier for entities, relations, and other resources
#[spacetimedb_derive::spacetimedb_type]
pub struct ResourceId(String);

// Metadata associated with an entity
#[spacetimedb_derive::spacetimedb_type]
pub struct EntityMetadata {
    // Basic properties
    pub name: Option<String>,
    pub description: Option<String>,
    pub tags: Vec<String>,

    // Type-specific properties stored as JSON-like data
    pub properties: Map<String, Value>
}

// Metadata associated with a relation
#[spacetimedb_derive::spacetimedb_type]
pub struct RelationMetadata {
    pub description: Option<String>,
    pub strength: f32,  // 0.0 to 1.0 indicating relationship strength
    pub bidirectional: bool,
    pub tags: Vec<String>,

    // Relation-specific properties stored as JSON-like data
    pub properties: Map<String, Value>
}

// Value represents different data types in a property bag
#[spacetimedb_derive::spacetimedb_type]
pub enum Value {
    Null,
    Bool(bool),
    Integer(i64),
    Float(f64),
    String(String),
    Array(Vec<Value>),
    Object(Map<String, Value>)
}
```

## Event System Types

```rust
// Event data for different event types
#[spacetimedb_derive::spacetimedb_type]
pub enum EventData {
    EntityCreated(EntityCreatedData),
    EntityUpdated(EntityUpdatedData),
    EntityDeleted(EntityDeletedData),
    RelationCreated(RelationCreatedData),
    RelationUpdated(RelationUpdatedData),
    RelationDeleted(RelationDeletedData),
    StateVersionCommitted(VersionCommitData),
    DeltaRecorded(DeltaRecordedData),
    ClientConnected(ClientConnectedData),
    ClientDisconnected(ClientDisconnectedData),
    Custom(Map<String, Value>)
}

#[spacetimedb_derive::spacetimedb_type]
pub struct EntityCreatedData {
    pub entity_id: String,
    pub entity_type: String,
    pub metadata: EntityMetadata
}

#[spacetimedb_derive::spacetimedb_type]
pub struct EntityUpdatedData {
    pub entity_id: String,
    pub changed_fields: Vec<String>,
    pub old_metadata: Option<EntityMetadata>,
    pub new_metadata: EntityMetadata
}

#[spacetimedb_derive::spacetimedb_type]
pub struct EntityDeletedData {
    pub entity_id: String,
    pub entity_type: String
}

#[spacetimedb_derive::spacetimedb_type]
pub struct RelationCreatedData {
    pub relation_id: String,
    pub from_entity: String,
    pub to_entity: String,
    pub relation_type: String,
    pub metadata: RelationMetadata
}

#[spacetimedb_derive::spacetimedb_type]
pub struct RelationUpdatedData {
    pub relation_id: String,
    pub changed_fields: Vec<String>,
    pub old_metadata: Option<RelationMetadata>,
    pub new_metadata: RelationMetadata
}

#[spacetimedb_derive::spacetimedb_type]
pub struct RelationDeletedData {
    pub relation_id: String,
    pub relation_type: String
}

#[spacetimedb_derive::spacetimedb_type]
pub struct VersionCommitData {
    pub version_id: String,
    pub parent_version_id: Option<String>,
    pub description: String,
    pub data_hash: String
}

#[spacetimedb_derive::spacetimedb_type]
pub struct DeltaRecordedData {
    pub delta_id: String,
    pub state_version_id: String,
    pub operations_count: usize,
    pub metadata: DeltaMetadata
}

#[spacetimedb_derive::spacetimedb_type]
pub struct ClientConnectedData {
    pub identity: Identity
}

#[spacetimedb_derive::spacetimedb_type]
pub struct ClientDisconnectedData {
    pub identity: Identity
}
```

## State Management Types

```rust
// Metadata for a delta record
#[spacetimedb_derive::spacetimedb_type]
pub struct DeltaMetadata {
    pub description: String,
    pub author: Option<String>,
    pub tags: Vec<String>,
    pub parent_delta_id: Option<String>
}

// A single operation in a delta
#[spacetimedb_derive::spacetimedb_type]
pub enum DeltaOperation {
    Set {
        path: String,
        value: Value
    },
    Delete {
        path: String
    },
    Insert {
        path: String,
        index: Option<usize>,
        value: Value
    },
    Remove {
        path: String,
        index: usize
    },
    Patch {
        path: String,
        patch: Map<String, Value>
    }
}

// Query filters for retrieving data
#[spacetimedb_derive::spacetimedb_type]
pub struct QueryFilter {
    pub field: String,
    pub operator: FilterOperator,
    pub value: Value
}

#[spacetimedb_derive::spacetimedb_type]
pub enum FilterOperator {
    Equals,
    NotEquals,
    GreaterThan,
    LessThan,
    GreaterOrEqual,
    LessOrEqual,
    Contains,
    StartsWith,
    EndsWith,
    In,
    NotIn
}
```

## Utility Types

```rust
// Configuration for the Inner Universe module
#[spacetimedb_derive::spacetimedb_type]
pub struct ModuleConfig {
    pub name: String,
    pub version: String,
    pub cache_size_mb: u32,
    pub log_level: LogLevel,
    pub features: Vec<FeatureFlag>
}

#[spacetimedb_derive::spacetimedb_type]
pub enum LogLevel {
    Error,
    Warn,
    Info,
    Debug,
    Trace
}

#[spacetimedb_derive::spacetimedb_type]
pub enum FeatureFlag {
    EnableStateVersioning,
    EnableAuditLog,
    EnableMetrics,
    EnableCaching,
    EnableDistribution
}

// Results and status responses
#[spacetimedb_derive::spacetimedb_type]
pub struct OperationResult {
    pub success: bool,
    pub message: Option<String>,
    pub data: Option<Value>
}

#[spacetimedb_derive::spacetimedb_type]
pub struct SystemStatus {
    pub status: SystemState,
    pub version: String,
    pub uptime_seconds: u64,
    pub entity_count: u64,
    pub relation_count: u64,
    pub event_count: u64,
    pub connected_clients: u32
}

#[spacetimedb_derive::spacetimedb_type]
pub enum SystemState {
    Starting,
    Running,
    Degraded,
    Maintenance,
    ShuttingDown
}
```

## Integration Types for Python Client

The following types will be used in the Python client to interact with the Rust module:

```python
# Python equivalents of the Rust types
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

# Basic types
ResourceId = str
Identity = str
Timestamp = int  # milliseconds since epoch

# Simple value type
class Value:
    @staticmethod
    def null():
        return {"type": "null", "value": None}

    @staticmethod
    def bool(value: bool):
        return {"type": "bool", "value": value}

    @staticmethod
    def integer(value: int):
        return {"type": "integer", "value": value}

    @staticmethod
    def float(value: float):
        return {"type": "float", "value": value}

    @staticmethod
    def string(value: str):
        return {"type": "string", "value": value}

    @staticmethod
    def array(values: List[Any]):
        return {"type": "array", "value": values}

    @staticmethod
    def object(obj: Dict[str, Any]):
        return {"type": "object", "value": obj}

    @staticmethod
    def from_native(value: Any):
        """Convert Python native types to Value objects"""
        if value is None:
            return Value.null()
        elif isinstance(value, bool):
            return Value.bool(value)
        elif isinstance(value, int):
            return Value.integer(value)
        elif isinstance(value, float):
            return Value.float(value)
        elif isinstance(value, str):
            return Value.string(value)
        elif isinstance(value, list):
            return Value.array([Value.from_native(v) for v in value])
        elif isinstance(value, dict):
            return Value.object({k: Value.from_native(v) for k, v in value.items()})
        else:
            raise TypeError(f"Cannot convert {type(value)} to Value")

@dataclass
class EntityMetadata:
    name: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = None
    properties: Dict[str, Any] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.properties is None:
            self.properties = {}

@dataclass
class RelationMetadata:
    description: Optional[str] = None
    strength: float = 1.0
    bidirectional: bool = False
    tags: List[str] = None
    properties: Dict[str, Any] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.properties is None:
            self.properties = {}

# Enum for filter operations
class FilterOperator(Enum):
    EQUALS = "Equals"
    NOT_EQUALS = "NotEquals"
    GREATER_THAN = "GreaterThan"
    LESS_THAN = "LessThan"
    GREATER_OR_EQUAL = "GreaterOrEqual"
    LESS_OR_EQUAL = "LessOrEqual"
    CONTAINS = "Contains"
    STARTS_WITH = "StartsWith"
    ENDS_WITH = "EndsWith"
    IN = "In"
    NOT_IN = "NotIn"

@dataclass
class QueryFilter:
    field: str
    operator: FilterOperator
    value: Any
```

## Python Client Interface Signatures

```python
class InnerUniverseClient:
    """Client interface for the Inner Universe persistence layer"""

    async def connect(self, address: str, port: int):
        """Connect to the SpacetimeDB instance"""
        pass

    async def disconnect(self):
        """Disconnect from the SpacetimeDB instance"""
        pass

    # Entity operations
    async def create_entity(self, entity_type: str, metadata: EntityMetadata) -> str:
        """Create a new entity in the persistence layer"""
        pass

    async def get_entity(self, entity_id: str) -> dict:
        """Retrieve an entity by ID"""
        pass

    async def update_entity(self, entity_id: str, metadata: EntityMetadata) -> bool:
        """Update an existing entity"""
        pass

    async def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity by ID"""
        pass

    async def query_entities(self,
                           entity_type: Optional[str] = None,
                           filters: List[QueryFilter] = None,
                           limit: int = 100,
                           offset: int = 0) -> List[dict]:
        """Query entities with optional filters"""
        pass

    # Relation operations
    async def create_relation(self,
                             from_entity: str,
                             to_entity: str,
                             relation_type: str,
                             metadata: RelationMetadata) -> str:
        """Create a new relation between entities"""
        pass

    async def get_relation(self, relation_id: str) -> dict:
        """Retrieve a relation by ID"""
        pass

    async def update_relation(self, relation_id: str, metadata: RelationMetadata) -> bool:
        """Update an existing relation"""
        pass

    async def delete_relation(self, relation_id: str) -> bool:
        """Delete a relation by ID"""
        pass

    # State operations
    async def commit_state_version(self,
                                  parent_version_id: Optional[str],
                                  description: str,
                                  data_hash: str) -> str:
        """Commit a new state version"""
        pass

    async def record_delta(self,
                          state_version_id: str,
                          operations: List[dict],
                          metadata: dict) -> str:
        """Record a delta for a state version"""
        pass

    async def get_state_version(self, version_id: str) -> dict:
        """Retrieve a state version by ID"""
        pass

    async def get_version_history(self, limit: int = 10) -> List[dict]:
        """Get recent state version history"""
        pass

    # Event operations
    async def publish_event(self,
                           event_type: str,
                           source: Optional[str],
                           data: dict) -> str:
        """Publish an event to the event log"""
        pass

    async def get_events(self,
                        event_type: Optional[str] = None,
                        start_time: Optional[int] = None,
                        end_time: Optional[int] = None,
                        limit: int = 100) -> List[dict]:
        """Get events from the event log"""
        pass

    # Subscription methods
    def subscribe_entity_changes(self, callback: callable):
        """Subscribe to entity table changes"""
        pass

    def subscribe_relation_changes(self, callback: callable):
        """Subscribe to relation table changes"""
        pass

    def subscribe_state_version_changes(self, callback: callable):
        """Subscribe to state_version table changes"""
        pass

    def subscribe_event_log_changes(self, callback: callable):
        """Subscribe to event_log table changes"""
        pass

    # System operations
    async def get_system_status(self) -> dict:
        """Get the current system status"""
        pass

    async def apply_configuration(self, config: dict) -> bool:
        """Apply configuration settings to the module"""
        pass
```
