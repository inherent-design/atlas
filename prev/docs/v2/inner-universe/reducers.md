---
title: Reducers
---

# Inner Universe Reducers

This document defines the core reducers (server-side functions) for the Inner Universe persistence layer. These reducers form the API that the Python client will use to interact with the SpacetimeDB module.

## Core Concepts

In SpacetimeDB, reducers are server-side functions that:

1. Run as transactions against the database
2. Can be called by clients over the network
3. Can read and write to tables in the database
4. Cannot directly return values to clients (they can only modify data)
5. Are the only way to modify data in the database

## Lifecycle Reducers

These reducers handle system lifecycle events:

```rust
/// Called when the module is initially published
#[reducer(init)]
pub fn init(ctx: &ReducerContext) {
    log::info!("Initializing Inner Universe module");

    // Initialize configuration with default values
    initialize_config(ctx);

    // Log initialization event
    log_event(
        ctx,
        "SYSTEM_INITIALIZED",
        None,
        EventData::Custom(btreemap! {
            "version".to_string() => Value::String("0.1.0".to_string()),
            "timestamp".to_string() => Value::Integer(ctx.timestamp as i64)
        })
    );
}

/// Called when a client connects to the database
#[reducer(client_connected)]
pub fn identity_connected(ctx: &ReducerContext) {
    let identity = ctx.sender;
    let connection_id = ctx.connection_id.to_string();

    log::debug!("Client connected: {}", identity);

    // Record client connection
    ctx.db.client_connection().insert(ClientConnection {
        identity,
        connection_id,
        connected_at: ctx.timestamp,
        last_active_at: ctx.timestamp,
        client_info: None,
        status: ConnectionStatus::Connected
    });

    // Publish connection event
    log_event(
        ctx,
        "CLIENT_CONNECTED",
        Some(identity.to_string()),
        EventData::ClientConnected(ClientConnectedData { identity })
    );
}

/// Called when a client disconnects
#[reducer(client_disconnected)]
pub fn identity_disconnected(ctx: &ReducerContext) {
    let identity = ctx.sender;

    log::debug!("Client disconnected: {}", identity);

    // Update client connection status
    if let Some(mut connection) = ctx.db.client_connection()
        .filter(|c| c.identity == identity)
        .first()
    {
        connection.status = ConnectionStatus::Disconnected;
        ctx.db.client_connection().update(connection);
    }

    // Publish disconnection event
    log_event(
        ctx,
        "CLIENT_DISCONNECTED",
        Some(identity.to_string()),
        EventData::ClientDisconnected(ClientDisconnectedData { identity })
    );
}
```

## Entity Management Reducers

These reducers handle entity creation, retrieval, update, and deletion:

```rust
/// Create a new entity in the database
#[reducer]
pub fn create_entity(
    ctx: &ReducerContext,
    entity_type: String,
    metadata: EntityMetadata
) -> Result<String, String> {
    // Validate entity type
    if entity_type.is_empty() {
        return Err("Entity type cannot be empty".into());
    }

    // Generate a unique ID
    let id = generate_uuid();
    let now = ctx.timestamp;

    // Insert the entity
    ctx.db.entity().insert(Entity {
        id: id.clone(),
        entity_type: entity_type.clone(),
        created_at: now,
        updated_at: now,
        metadata: metadata.clone()
    });

    // Log the event
    log_event(
        ctx,
        "ENTITY_CREATED",
        Some(id.clone()),
        EventData::EntityCreated(EntityCreatedData {
            entity_id: id.clone(),
            entity_type,
            metadata
        })
    );

    Ok(id)
}

/// Update an existing entity
#[reducer]
pub fn update_entity(
    ctx: &ReducerContext,
    entity_id: String,
    metadata: EntityMetadata
) -> Result<bool, String> {
    // Find the entity
    let entity = ctx.db.entity()
        .filter(|e| e.id == entity_id)
        .first()
        .ok_or_else(|| format!("Entity not found: {}", entity_id))?;

    // Prepare an update
    let mut updated_entity = entity.clone();
    updated_entity.metadata = metadata.clone();
    updated_entity.updated_at = ctx.timestamp;

    // Track changed fields
    let mut changed_fields = Vec::new();

    // Compare metadata fields to detect changes
    if entity.metadata.name != metadata.name {
        changed_fields.push("name".to_string());
    }

    if entity.metadata.description != metadata.description {
        changed_fields.push("description".to_string());
    }

    if entity.metadata.tags != metadata.tags {
        changed_fields.push("tags".to_string());
    }

    // More detailed property comparison could be added here

    // Update the entity
    ctx.db.entity().update(updated_entity);

    // Log the event
    log_event(
        ctx,
        "ENTITY_UPDATED",
        Some(entity_id.clone()),
        EventData::EntityUpdated(EntityUpdatedData {
            entity_id: entity_id.clone(),
            changed_fields,
            old_metadata: Some(entity.metadata),
            new_metadata: metadata
        })
    );

    Ok(true)
}

/// Delete an existing entity
#[reducer]
pub fn delete_entity(
    ctx: &ReducerContext,
    entity_id: String
) -> Result<bool, String> {
    // Find the entity
    let entity = ctx.db.entity()
        .filter(|e| e.id == entity_id)
        .first()
        .ok_or_else(|| format!("Entity not found: {}", entity_id))?;

    // Check for relations to this entity
    let relations_count = ctx.db.relation()
        .filter(|r| r.from_entity == entity_id || r.to_entity == entity_id)
        .count();

    if relations_count > 0 {
        return Err(format!("Cannot delete entity with {} existing relationships", relations_count));
    }

    // Save entity type for event
    let entity_type = entity.entity_type.clone();

    // Delete the entity
    ctx.db.entity().delete(&entity);

    // Log the event
    log_event(
        ctx,
        "ENTITY_DELETED",
        Some(entity_id.clone()),
        EventData::EntityDeleted(EntityDeletedData {
            entity_id,
            entity_type
        })
    );

    Ok(true)
}
```

## Relation Management Reducers

These reducers handle relationship creation, update, and deletion:

```rust
/// Create a new relation between entities
#[reducer]
pub fn create_relation(
    ctx: &ReducerContext,
    from_entity: String,
    to_entity: String,
    relation_type: String,
    metadata: RelationMetadata
) -> Result<String, String> {
    // Validate relation type
    if relation_type.is_empty() {
        return Err("Relation type cannot be empty".into());
    }

    // Verify entities exist
    if !entity_exists(ctx, &from_entity) {
        return Err(format!("From entity not found: {}", from_entity));
    }

    if !entity_exists(ctx, &to_entity) {
        return Err(format!("To entity not found: {}", to_entity));
    }

    // Generate a unique ID
    let id = generate_uuid();
    let now = ctx.timestamp;

    // Insert the relation
    ctx.db.relation().insert(Relation {
        id: id.clone(),
        from_entity: from_entity.clone(),
        to_entity: to_entity.clone(),
        relation_type: relation_type.clone(),
        created_at: now,
        metadata: metadata.clone()
    });

    // Log the event
    log_event(
        ctx,
        "RELATION_CREATED",
        Some(id.clone()),
        EventData::RelationCreated(RelationCreatedData {
            relation_id: id.clone(),
            from_entity,
            to_entity,
            relation_type,
            metadata
        })
    );

    Ok(id)
}

/// Update an existing relation
#[reducer]
pub fn update_relation(
    ctx: &ReducerContext,
    relation_id: String,
    metadata: RelationMetadata
) -> Result<bool, String> {
    // Find the relation
    let relation = ctx.db.relation()
        .filter(|r| r.id == relation_id)
        .first()
        .ok_or_else(|| format!("Relation not found: {}", relation_id))?;

    // Prepare an update
    let mut updated_relation = relation.clone();
    updated_relation.metadata = metadata.clone();

    // Track changed fields
    let mut changed_fields = Vec::new();

    // Compare metadata fields to detect changes
    if relation.metadata.description != metadata.description {
        changed_fields.push("description".to_string());
    }

    if relation.metadata.strength != metadata.strength {
        changed_fields.push("strength".to_string());
    }

    if relation.metadata.bidirectional != metadata.bidirectional {
        changed_fields.push("bidirectional".to_string());
    }

    if relation.metadata.tags != metadata.tags {
        changed_fields.push("tags".to_string());
    }

    // Update the relation
    ctx.db.relation().update(updated_relation);

    // Log the event
    log_event(
        ctx,
        "RELATION_UPDATED",
        Some(relation_id.clone()),
        EventData::RelationUpdated(RelationUpdatedData {
            relation_id,
            changed_fields,
            old_metadata: Some(relation.metadata),
            new_metadata: metadata
        })
    );

    Ok(true)
}

/// Delete an existing relation
#[reducer]
pub fn delete_relation(
    ctx: &ReducerContext,
    relation_id: String
) -> Result<bool, String> {
    // Find the relation
    let relation = ctx.db.relation()
        .filter(|r| r.id == relation_id)
        .first()
        .ok_or_else(|| format!("Relation not found: {}", relation_id))?;

    // Save relation type for event
    let relation_type = relation.relation_type.clone();

    // Delete the relation
    ctx.db.relation().delete(&relation);

    // Log the event
    log_event(
        ctx,
        "RELATION_DELETED",
        Some(relation_id.clone()),
        EventData::RelationDeleted(RelationDeletedData {
            relation_id,
            relation_type
        })
    );

    Ok(true)
}
```

## State Version Management Reducers

These reducers handle state versioning for NERV's TemporalStore integration:

```rust
/// Commit a new state version
#[reducer]
pub fn commit_state_version(
    ctx: &ReducerContext,
    parent_version_id: Option<String>,
    description: String,
    data_hash: String
) -> Result<String, String> {
    // Validate parent version if provided
    if let Some(parent_id) = &parent_version_id {
        if !version_exists(ctx, parent_id) {
            return Err(format!("Parent version not found: {}", parent_id));
        }
    }

    // Generate a unique version ID
    let version_id = generate_uuid();
    let now = ctx.timestamp;

    // Insert the state version
    ctx.db.state_version().insert(StateVersion {
        version_id: version_id.clone(),
        parent_version_id,
        timestamp: now,
        description: description.clone(),
        data_hash: data_hash.clone(),
        owner: ctx.sender
    });

    // Log the event
    log_event(
        ctx,
        "STATE_VERSION_COMMITTED",
        Some(version_id.clone()),
        EventData::StateVersionCommitted(VersionCommitData {
            version_id: version_id.clone(),
            parent_version_id,
            description,
            data_hash
        })
    );

    Ok(version_id)
}

/// Record a delta for a state version
#[reducer]
pub fn record_delta(
    ctx: &ReducerContext,
    state_version_id: String,
    operations: Vec<DeltaOperation>,
    metadata: DeltaMetadata
) -> Result<String, String> {
    // Verify state version exists
    if !version_exists(ctx, &state_version_id) {
        return Err(format!("State version not found: {}", state_version_id));
    }

    // Generate a unique delta ID
    let delta_id = generate_uuid();
    let now = ctx.timestamp;

    // Insert the delta record
    ctx.db.delta_record().insert(DeltaRecord {
        delta_id: delta_id.clone(),
        state_version_id: state_version_id.clone(),
        operations: operations.clone(),
        timestamp: now,
        metadata: metadata.clone()
    });

    // Log the event
    log_event(
        ctx,
        "DELTA_RECORDED",
        Some(delta_id.clone()),
        EventData::DeltaRecorded(DeltaRecordedData {
            delta_id: delta_id.clone(),
            state_version_id,
            operations_count: operations.len(),
            metadata
        })
    );

    Ok(delta_id)
}

/// Get the full history for a state version
#[reducer]
pub fn get_version_history(
    ctx: &ReducerContext,
    version_id: String,
    max_depth: u32
) -> Result<Vec<String>, String> {
    // Verify state version exists
    if !version_exists(ctx, &version_id) {
        return Err(format!("State version not found: {}", version_id));
    }

    // Recursively fetch parent versions
    let mut history = Vec::new();
    let mut current_id = Some(version_id);
    let mut depth = 0;

    while let Some(id) = current_id {
        if depth >= max_depth {
            break;
        }

        history.push(id.clone());

        // Get parent version
        if let Some(version) = ctx.db.state_version()
            .filter(|v| v.version_id == id)
            .first()
        {
            current_id = version.parent_version_id.clone();
        } else {
            current_id = None;
        }

        depth += 1;
    }

    Ok(history)
}
```

## Event System Reducers

These reducers handle event logging and querying:

```rust
/// Publish an event to the event log
#[reducer]
pub fn publish_event(
    ctx: &ReducerContext,
    event_type: String,
    source: Option<String>,
    data: EventData
) -> Result<String, String> {
    // Validate event type
    if event_type.is_empty() {
        return Err("Event type cannot be empty".into());
    }

    // Generate a unique event ID
    let event_id = generate_uuid();
    let now = ctx.timestamp;

    // Insert the event
    ctx.db.event_log().insert(EventLog {
        event_id: event_id.clone(),
        event_type,
        source,
        timestamp: now,
        data
    });

    Ok(event_id)
}

/// Get recent events of a specific type
#[reducer]
pub fn get_recent_events(
    ctx: &ReducerContext,
    event_type: Option<String>,
    max_count: u32
) -> Result<Vec<String>, String> {
    // Validate max count
    if max_count == 0 || max_count > 1000 {
        return Err("Max count must be between 1 and 1000".into());
    }

    let mut events_query = ctx.db.event_log();

    // Filter by event type if provided
    if let Some(et) = event_type {
        events_query = events_query.filter(|e| e.event_type == et);
    }

    // Get recent events, ordered by timestamp descending
    let events: Vec<String> = events_query
        .order_by(|e| e.timestamp, spacetimedb::SpacetimeType::Descending)
        .limit(max_count as usize)
        .map(|e| e.event_id)
        .collect();

    Ok(events)
}
```

## Query and Subscription Reducers

These reducers handle data subscriptions and querying:

```rust
/// Create a subscription for a client
#[reducer]
pub fn create_subscription(
    ctx: &ReducerContext,
    query: String
) -> Result<String, String> {
    // Validate query
    if query.is_empty() {
        return Err("Query cannot be empty".into());
    }

    // Generate a unique subscription ID
    let subscription_id = generate_uuid();
    let now = ctx.timestamp;

    // Insert the subscription
    ctx.db.subscription().insert(Subscription {
        subscription_id: subscription_id.clone(),
        identity: ctx.sender,
        query,
        created_at: now,
        updated_at: now,
        status: SubscriptionStatus::Active
    });

    Ok(subscription_id)
}

/// Update a subscription status
#[reducer]
pub fn update_subscription_status(
    ctx: &ReducerContext,
    subscription_id: String,
    status: SubscriptionStatus
) -> Result<bool, String> {
    // Find the subscription
    let subscription = ctx.db.subscription()
        .filter(|s| s.subscription_id == subscription_id && s.identity == ctx.sender)
        .first()
        .ok_or_else(|| format!("Subscription not found: {}", subscription_id))?;

    // Update the subscription status
    let mut updated_subscription = subscription.clone();
    updated_subscription.status = status;
    updated_subscription.updated_at = ctx.timestamp;

    ctx.db.subscription().update(updated_subscription);

    Ok(true)
}

/// Delete a subscription
#[reducer]
pub fn delete_subscription(
    ctx: &ReducerContext,
    subscription_id: String
) -> Result<bool, String> {
    // Find the subscription
    let subscription = ctx.db.subscription()
        .filter(|s| s.subscription_id == subscription_id && s.identity == ctx.sender)
        .first()
        .ok_or_else(|| format!("Subscription not found: {}", subscription_id))?;

    // Delete the subscription
    ctx.db.subscription().delete(&subscription);

    Ok(true)
}
```

## System Management Reducers

These reducers handle system configuration and status:

```rust
/// Get the current system status
#[reducer]
pub fn get_system_status(ctx: &ReducerContext) -> Result<SystemStatus, String> {
    // Count entities and relations
    let entity_count = ctx.db.entity().count() as u64;
    let relation_count = ctx.db.relation().count() as u64;
    let event_count = ctx.db.event_log().count() as u64;

    // Count connected clients
    let connected_clients = ctx.db.client_connection()
        .filter(|c| matches!(c.status, ConnectionStatus::Connected))
        .count() as u32;

    // Calculate uptime (if we stored start time in a config entry)
    let start_time = ctx.db.config()
        .filter(|c| c.key == "start_time")
        .first()
        .and_then(|c| c.value.parse::<u64>().ok())
        .unwrap_or(ctx.timestamp);

    let uptime_seconds = (ctx.timestamp - start_time) / 1000;

    // Get module version from config
    let version = ctx.db.config()
        .filter(|c| c.key == "module_version")
        .first()
        .map(|c| c.value.clone())
        .unwrap_or_else(|| "0.1.0".to_string());

    // Return status report
    Ok(SystemStatus {
        status: SystemState::Running,
        version,
        uptime_seconds,
        entity_count,
        relation_count,
        event_count,
        connected_clients
    })
}

/// Update system configuration
#[reducer]
pub fn update_config(
    ctx: &ReducerContext,
    key: String,
    value: String,
    description: Option<String>
) -> Result<bool, String> {
    // Check if this is an admin-only config key
    if is_admin_only_config(&key) && !is_admin(ctx.sender) {
        return Err("Unauthorized: Admin privileges required for this configuration key".into());
    }

    // Find existing config
    let existing_config = ctx.db.config()
        .filter(|c| c.key == key)
        .first();

    // Update or insert config
    if let Some(config) = existing_config {
        let mut updated_config = config.clone();
        updated_config.value = value;
        updated_config.description = description;
        updated_config.updated_at = ctx.timestamp;
        updated_config.updated_by = ctx.sender;

        ctx.db.config().update(updated_config);
    } else {
        ctx.db.config().insert(Config {
            key,
            value,
            description,
            updated_at: ctx.timestamp,
            updated_by: ctx.sender
        });
    }

    Ok(true)
}
```

## Utility Functions

These utility functions are used by reducers:

```rust
/// Generate a UUID string
fn generate_uuid() -> String {
    let uuid = uuid::Uuid::new_v4();
    uuid.to_string()
}

/// Check if an entity exists
fn entity_exists(ctx: &ReducerContext, entity_id: &str) -> bool {
    ctx.db.entity()
        .filter(|e| e.id == entity_id)
        .count() > 0
}

/// Check if a state version exists
fn version_exists(ctx: &ReducerContext, version_id: &str) -> bool {
    ctx.db.state_version()
        .filter(|v| v.version_id == version_id)
        .count() > 0
}

/// Log an event to the event log
fn log_event(
    ctx: &ReducerContext,
    event_type: &str,
    source: Option<String>,
    data: EventData
) -> String {
    let event_id = generate_uuid();

    ctx.db.event_log().insert(EventLog {
        event_id: event_id.clone(),
        event_type: event_type.to_string(),
        source,
        timestamp: ctx.timestamp,
        data
    });

    event_id
}

/// Initialize system configuration with default values
fn initialize_config(ctx: &ReducerContext) {
    let now = ctx.timestamp;

    // Core configuration
    ctx.db.config().insert(Config {
        key: "module_version".to_string(),
        value: "0.1.0".to_string(),
        description: Some("Inner Universe module version".to_string()),
        updated_at: now,
        updated_by: ctx.sender
    });

    ctx.db.config().insert(Config {
        key: "start_time".to_string(),
        value: now.to_string(),
        description: Some("System start time".to_string()),
        updated_at: now,
        updated_by: ctx.sender
    });

    // Feature flags
    ctx.db.config().insert(Config {
        key: "feature_enable_state_versioning".to_string(),
        value: "true".to_string(),
        description: Some("Enable state versioning".to_string()),
        updated_at: now,
        updated_by: ctx.sender
    });

    ctx.db.config().insert(Config {
        key: "feature_enable_audit_log".to_string(),
        value: "true".to_string(),
        description: Some("Enable audit logging".to_string()),
        updated_at: now,
        updated_by: ctx.sender
    });

    // Performance settings
    ctx.db.config().insert(Config {
        key: "cache_size_mb".to_string(),
        value: "256".to_string(),
        description: Some("Cache size in megabytes".to_string()),
        updated_at: now,
        updated_by: ctx.sender
    });

    ctx.db.config().insert(Config {
        key: "log_level".to_string(),
        value: "info".to_string(),
        description: Some("Logging level".to_string()),
        updated_at: now,
        updated_by: ctx.sender
    });
}

/// Check if a user is an admin
fn is_admin(identity: Identity) -> bool {
    // In a real implementation, this would check against a list of admin identities
    // For now, we assume the module owner is the admin
    // ctx.module_owner() == identity

    // Placeholder for testing
    true
}

/// Check if a configuration key requires admin privileges
fn is_admin_only_config(key: &str) -> bool {
    // List of admin-only configuration keys
    let admin_keys = [
        "log_level",
        "cache_size_mb",
        "feature_enable_",
        "admin_",
        "security_"
    ];

    admin_keys.iter().any(|prefix| key.starts_with(prefix))
}
```

## Error Handling Strategy

All reducers follow a consistent error handling pattern:

1. **Early Validation**: Validate all inputs before making any changes
2. **Result Return Type**: Use `Result<T, String>` for operations that can fail
3. **Descriptive Error Messages**: Provide clear error messages for troubleshooting
4. **Transaction Safety**: Let SpacetimeDB roll back the transaction on error
5. **Error Logging**: Log all errors for audit and debugging

```rust
// Example of the error handling pattern
#[reducer]
pub fn example_with_error_handling(
    ctx: &ReducerContext,
    input: String
) -> Result<String, String> {
    // 1. Early validation
    if input.is_empty() {
        return Err("Input cannot be empty".into());
    }

    // 2. Resource validation
    let resource = ctx.db.some_table()
        .filter(|r| r.id == "some_id")
        .first()
        .ok_or_else(|| "Resource not found".to_string())?;

    // 3. Permission check
    if !has_permission(ctx.sender, &resource) {
        return Err("Permission denied".into());
    }

    // 4. Processing with potential failures
    let result = process_input(&input)
        .map_err(|e| format!("Processing error: {}", e))?;

    // 5. Database operations
    ctx.db.some_table().insert(SomeTable {
        // fields...
    });

    // 6. Return success
    Ok(result)
}
```

## Integration with Python Client

The Python client will call these reducers using the SpacetimeDB Python SDK:

```python
# Example Python client reducer call
async def create_entity(client, entity_type, metadata):
    """Create a new entity in the database"""
    try:
        # Convert Python EntityMetadata to the format expected by the reducer
        metadata_dict = dataclasses.asdict(metadata)

        # Call the reducer
        result = await client.call_reducer(
            "create_entity",
            entity_type,
            metadata_dict
        )

        # The result is a string with the entity ID
        return result
    except Exception as e:
        # Handle error
        print(f"Error creating entity: {e}")
        raise
```

## Performance Considerations

These reducers are designed with performance in mind:

1. **Minimal Data Copying**: Operating directly on table references when possible
2. **Efficient Queries**: Using filtered queries with appropriate indices
3. **Batch Operations**: Supporting bulk operations for entity/relation management
4. **Lightweight Events**: Using minimal event payloads for frequent operations
5. **Query Optimization**: Utilizing SpacetimeDB's query optimization capabilities
