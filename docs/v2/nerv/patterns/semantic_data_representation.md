# Semantic Data Representation Across Multiple Perspectives

*Research on k-v strategies for flattening data relationships and programmatic transformation patterns*

## Overview

This document outlines strategies for representing the same underlying data across multiple perspectives while preserving semantic meaning. The patterns described here build upon NERV's `PerspectiveAware`, `StateProjector`, and `EventBus` components to enable efficient data transformation pipelines for different storage systems.

## Core Challenge

Modern distributed systems need to represent the same canonical data in multiple formats optimized for different access patterns:

- **Time-series data** for analytics and trend analysis
- **Full-text search** for discovery and retrieval  
- **Key-value strategies** for fast lookups and caching
- **Graph relationships** for understanding connections

## Key-Value Flattening Strategies

### 1. Path-Based Keys

The most common approach where keys represent traversal paths from entity root to specific attributes. Excellent for preserving hierarchy while enabling efficient lookups.

**Syntax Pattern:** `entity_type:id:attribute:sub_attribute`

**Examples:**
- `user:123:profile:name` → `"John Doe"`
- `user:123:posts:post_abc:title` → `"My First Post"`

### 2. Semantic Hashing / Composite Keys

Encodes multiple facets of data into the key structure, enabling different perspectives of the same entity. Aligns with NERV's "Semantic Hashes" concept.

**Syntax Pattern:** `perspective:entity_type:id:field`

**Examples:**
- `public:user:123:name` → `"John Doe"`
- `internal:user:123:email` → `"john.doe@example.com"`

### 3. Relationship Indexing

Uses Redis Sets or Sorted Sets to represent graph edges and maintain relationship information.

**Syntax Pattern:** `entity_type:id:relation_type`

**Examples:**
- `user:123:friends` → `SADD user:123:friends user:456 user:789`
- `user:123:logins` → `ZADD user:123:logins 1672531200 "2023-01-01T00:00:00Z"`

## Programmatic Transformation Pipeline

### Architecture Components

1. **Source of Truth**: Inner Universe database holding normalized, relational graph data
2. **Event Trigger**: Changes emit events on EventBus (e.g., `ENTITY_UPDATED`)
3. **Transformation Engine**: Service subscribing to these events
4. **Projectors**: Target-specific transformation classes for each storage system

### Flattening Implementation

```python
def flatten_for_kv(entity: dict, perspective: str = "default") -> dict:
    """
    Flattens a nested entity dictionary into key-value map for Redis.
    
    Preserves semantic meaning through hierarchical key structure.
    """
    flat_kv = {}
    entity_type = entity.get("entity_type", "unknown")
    entity_id = entity.get("id")

    if not entity_id:
        raise ValueError("Entity must have an 'id'")

    def recurse(obj, path_prefix):
        if isinstance(obj, dict):
            for k, v in obj.items():
                recurse(v, f"{path_prefix}:{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                recurse(item, f"{path_prefix}:{i}")
        else:
            # Final value, create the key-value pair
            flat_kv[path_prefix] = str(obj)

    # Build hierarchical keys preserving semantic structure
    base_key = f"{perspective}:{entity_type}:{entity_id}"
    recurse(entity.get("metadata", {}), base_key)

    # Add top-level fields
    flat_kv[f"{base_key}:entity_type"] = entity_type
    flat_kv[f"{base_key}:created_at"] = str(entity.get("created_at"))
    flat_kv[f"{base_key}:updated_at"] = str(entity.get("updated_at"))

    return flat_kv
```

### Projector Pattern Implementation

```python
from abc import ABC, abstractmethod
import json

class BaseProjector(ABC):
    """Abstract base for all storage-specific projectors."""
    
    @abstractmethod
    def project(self, entity: dict) -> dict:
        """Transforms canonical entity into target format."""
        pass

class ElasticsearchProjector(BaseProjector):
    """Projects entity for full-text search optimization."""
    
    def project(self, entity: dict) -> dict:
        return {
            "entity_id": entity["id"],
            "type": entity["entity_type"],
            "created": entity["created_at"],
            "updated": entity["updated_at"],
            "content": f"{entity['metadata'].get('name', '')} {entity['metadata'].get('description', '')}",
            "tags": entity["metadata"].get("tags", []),
            "author": entity["metadata"].get("properties", {}).get("author"),
            "raw_metadata": json.dumps(entity["metadata"])
        }

class KeyValueProjector(BaseProjector):
    """Projects entity into flattened key-value format."""
    
    def project(self, entity: dict) -> dict:
        return flatten_for_kv(entity, perspective="cache")

class TimeseriesProjector(BaseProjector):
    """Projects entity to extract time-series data points."""
    
    def project(self, entity: dict) -> dict:
        points = []
        if "logins" in entity.get("metadata", {}).get("properties", {}):
            points.append({
                "measurement": "logins",
                "tags": {"user_id": entity["id"], "type": entity["entity_type"]},
                "time": entity["updated_at"],
                "fields": {
                    "count": entity["metadata"]["properties"]["logins"]
                }
            })
        return {"points": points}
```

### Transformation Engine

```python
class TransformationEngine:
    """Orchestrates data projection across multiple storage targets."""
    
    def __init__(self):
        self.projectors = {
            "elasticsearch": ElasticsearchProjector(),
            "redis": KeyValueProjector(),
            "clickhouse": TimeseriesProjector(),
        }

    def on_entity_updated(self, entity: dict):
        """EventBus subscriber for entity update events."""
        for name, projector in self.projectors.items():
            projection = projector.project(entity)
            # Send projection to target storage system
            self._send_to_target(name, projection)
    
    def _send_to_target(self, target: str, data: dict):
        """Dispatch data to appropriate storage system."""
        # Implementation would vary by target:
        # redis_client.mset(data)
        # es_client.index(data)
        # clickhouse_client.insert(data)
        pass
```

## Denormalization Trade-offs Matrix

| Strategy | Target System | Read Performance | Write Performance | Storage Cost | Data Consistency | Query Flexibility |
|----------|---------------|------------------|-------------------|--------------|------------------|-------------------|
| **Normalized (Source of Truth)** | SpacetimeDB | Low (joins/traversals) | **High** (single write) | **Low** | **High** (ACID) | **High** (graph queries) |
| **Fully Denormalized Document** | Elasticsearch, MongoDB | **High** (single doc fetch) | Low (complex updates) | High (duplication) | Eventual | Medium (doc structure limits) |
| **Flattened Key-Value** | Redis, Memcached | **Highest** (direct key lookup) | Medium (multiple keys) | High (extreme duplication) | Eventual | **Low** (key-based only) |
| **Wide-Column / Time-Series** | ClickHouse, InfluxDB | **High** (for aggregations) | High (append optimized) | Medium | Eventual | Medium (time-series optimized) |

## Consistency Across Representations

### Event-Driven Consistency Architecture

1. **Single Source of Truth**: All writes go only to Inner Universe database
2. **Persistent Event Log**: Every write generates immutable event in EventLog
3. **Publish/Subscribe**: EventBus broadcasts to all interested projectors
4. **Idempotent Subscribers**: Projectors handle duplicate events gracefully
5. **Failure Recovery**: Dead-letter queues and event replay capabilities

### Implementation Pattern

```python
class EventDrivenConsistency:
    """Maintains consistency across multiple data representations."""
    
    def __init__(self, event_bus, transformation_engine):
        self.event_bus = event_bus
        self.transformation_engine = transformation_engine
        
        # Subscribe to entity change events
        self.event_bus.subscribe("ENTITY_UPDATED", self.on_entity_updated)
        self.event_bus.subscribe("ENTITY_DELETED", self.on_entity_deleted)
    
    def update_entity(self, entity_id: str, changes: dict):
        """Transactional update with event generation."""
        # 1. Update source of truth in transaction
        with db.transaction():
            updated_entity = db.update_entity(entity_id, changes)
            event_log.persist({
                "type": "ENTITY_UPDATED",
                "entity_id": entity_id,
                "data": updated_entity,
                "timestamp": time.time()
            })
        
        # 2. Publish event after successful commit
        self.event_bus.publish({
            "type": "ENTITY_UPDATED",
            "data": updated_entity
        })
    
    def on_entity_updated(self, event_data):
        """Handle entity update events."""
        try:
            self.transformation_engine.on_entity_updated(event_data)
        except Exception as e:
            # Move to dead-letter queue for manual inspection
            self.dead_letter_queue.add(event_data)
            logger.error(f"Failed to process entity update: {e}")
```

## Performance Characteristics

### Storage-Specific Optimizations

**Redis (Key-Value)**:
- Use weak references to prevent memory leaks
- Implement partitioned keys for high-volume data
- Optimize key patterns for range queries

**Elasticsearch (Full-Text Search)**:
- Cache schema instances and transformations
- Use partial serialization for large documents
- Implement lazy field resolution for nested objects

**ClickHouse (Time-Series)**:
- Batch writes for optimal throughput
- Partition by time ranges for query performance
- Use materialized views for common aggregations

**PostgreSQL (Source of Truth)**:
- Implement connection pooling for concurrent access
- Use read replicas for analytical workloads
- Optimize indexes for common query patterns

## Integration with NERV Components

### PerspectiveAware Integration

```python
class SemanticDataRepresentation(PerspectiveAware):
    """Integrates semantic representation with NERV perspective system."""
    
    def __init__(self):
        super().__init__()
        self.projectors = self._initialize_projectors()
    
    def get_perspective_data(self, entity_id: str, perspective: str) -> dict:
        """Return data optimized for specific perspective."""
        canonical_entity = self.inner_universe.get_entity(entity_id)
        
        if perspective in self.projectors:
            return self.projectors[perspective].project(canonical_entity)
        
        return canonical_entity
    
    def update_all_perspectives(self, entity: dict):
        """Update all perspective representations of entity."""
        for perspective_name, projector in self.projectors.items():
            projected_data = projector.project(entity)
            self._store_perspective(perspective_name, entity["id"], projected_data)
```

### StateProjector Integration

```python
class SemanticStateProjector(StateProjector):
    """Projects semantic state changes across storage systems."""
    
    def project_state_change(self, old_state: dict, new_state: dict) -> dict:
        """Project state delta across all representations."""
        delta = self.compute_delta(old_state, new_state)
        
        projections = {}
        for target, projector in self.projectors.items():
            projections[target] = {
                "old": projector.project(old_state) if old_state else None,
                "new": projector.project(new_state),
                "delta": projector.project(delta)
            }
        
        return projections
```

## Future Considerations

### Adaptive Projection

- **Usage-Based Optimization**: Adjust projection strategies based on access patterns
- **Lazy Projection**: Generate projections on-demand for infrequently accessed data
- **Smart Caching**: Cache projections with intelligent invalidation strategies

### Schema Evolution

- **Versioned Projectors**: Support multiple projection versions during schema migrations
- **Backward Compatibility**: Maintain old projection formats during transition periods
- **Progressive Enhancement**: Gradually improve projections without breaking existing consumers

## Conclusion

Semantic data representation across multiple perspectives requires careful balance of performance, consistency, and complexity. The patterns outlined here provide a foundation for building systems that can efficiently serve different access patterns while maintaining data integrity through event-driven consistency mechanisms.

The key insight is that effective data flattening preserves semantic meaning through intelligent key design while leveraging NERV's architectural components for robust, scalable implementation.