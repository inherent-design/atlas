---
title: Implementation
---

# Inner Universe Implementation Guide

This document provides a comprehensive guide for implementing the SpacetimeDB persistence layer within the NERV architecture. The guide focuses on practical implementation steps, code examples, and best practices for integrating the two systems.

## Overview

The Inner Universe persistence layer provides durable storage for NERV components using SpacetimeDB, a WASM-powered database that supports both storage and computation. This implementation guide will cover:

1. Setting up the Python client to connect to SpacetimeDB
2. Mapping NERV components to SpacetimeDB tables and reducers
3. Implementing key operations for entity and relation management
4. Testing the integration
5. Handling errors
6. Optimizing performance

## Python Client Setup

### Installation Requirements

Start by installing the required dependencies for the Python client:

```bash
uv pip install spacetimedb-sdk asyncio typing-extensions
```

### Basic Client Configuration

Create a base configuration class for Inner Universe:

```python
# atlas/graph/persistence/config.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class InnerUniverseConfig:
    """Configuration for the Inner Universe persistence layer"""

    # SpacetimeDB connection settings
    address: str = "127.0.0.1"
    port: int = 3000

    # Module settings
    module_path: Optional[str] = None
    db_path: str = "./inner_universe_db"

    # Deployment settings
    build_module: bool = False
    module_dir: Optional[str] = None

    # Feature flags
    features: Dict[str, bool] = field(default_factory=lambda: {
        "enable_state_versioning": True,
        "enable_audit_log": True,
        "enable_metrics": False,
        "enable_caching": True
    })

    # Performance settings
    cache_size_mb: int = 256
    log_level: str = "info"

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format"""
        return {
            "spacetimedb_config": {
                "address": self.address,
                "port": self.port,
                "db_path": self.db_path,
                "log_level": self.log_level
            },
            "module_config": {
                "module_path": self.module_path,
                "module_dir": self.module_dir,
                "build_module": self.build_module
            },
            "server_config": {
                "cache_size_mb": self.cache_size_mb
            },
            "feature_flags": self.features
        }
```

### Client Implementation

Next, create the Inner Universe client that will interface with SpacetimeDB:

```python
# atlas/graph/persistence/inner_universe.py
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Union, TypeVar, Generic
from dataclasses import dataclass, asdict

from spacetimedb_sdk.client import SpacetimeDBClient
from spacetimedb_sdk.subscription import SubscriptionHandle

from atlas.graph.persistence.config import InnerUniverseConfig
from atlas.graph.persistence.types import (
    EntityMetadata, RelationMetadata, QueryFilter,
    FilterOperator, DeltaOperation, DeltaMetadata
)
from atlas.core.logging import get_logger

T = TypeVar('T')

class InnerUniverseClient:
    """Client for the Inner Universe persistence layer"""

    def __init__(self, config: InnerUniverseConfig):
        self.config = config
        self.client: Optional[SpacetimeDBClient] = None
        self.process = None
        self.logger = get_logger("inner_universe")
        self.subscriptions: List[SubscriptionHandle] = []

    async def connect(self) -> bool:
        """Connect to the SpacetimeDB instance"""
        try:
            self.logger.info(f"Connecting to SpacetimeDB at {self.config.address}:{self.config.port}")

            self.client = SpacetimeDBClient(
                address=self.config.address,
                port=self.config.port
            )

            await self.client.connect()
            self.logger.info("Connected to SpacetimeDB")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to SpacetimeDB: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from the SpacetimeDB instance"""
        if self.client:
            for subscription in self.subscriptions:
                self.client.unsubscribe(subscription)

            await self.client.disconnect()
            self.client = None
            self.logger.info("Disconnected from SpacetimeDB")

    # Entity operations
    async def create_entity(self, entity_type: str, metadata: EntityMetadata) -> str:
        """Create a new entity in the persistence layer"""
        if not self.client:
            raise RuntimeError("Client not connected")

        self.logger.debug(f"Creating entity of type {entity_type}")

        # Convert metadata to dictionary
        metadata_dict = asdict(metadata)

        # Call the reducer
        result = await self.client.call_reducer("create_entity", entity_type, metadata_dict)
        return result

    async def get_entity(self, entity_id: str) -> Dict[str, Any]:
        """Retrieve an entity by ID"""
        if not self.client:
            raise RuntimeError("Client not connected")

        self.logger.debug(f"Retrieving entity {entity_id}")

        # Query the entity table directly
        entities = await self.client.query(f"SELECT * FROM entity WHERE id = '{entity_id}'")

        if not entities:
            raise ValueError(f"Entity not found: {entity_id}")

        return entities[0]

    async def update_entity(self, entity_id: str, metadata: EntityMetadata) -> bool:
        """Update an existing entity"""
        if not self.client:
            raise RuntimeError("Client not connected")

        self.logger.debug(f"Updating entity {entity_id}")

        # Convert metadata to dictionary
        metadata_dict = asdict(metadata)

        # Call the reducer
        result = await self.client.call_reducer("update_entity", entity_id, metadata_dict)
        return result

    async def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity by ID"""
        if not self.client:
            raise RuntimeError("Client not connected")

        self.logger.debug(f"Deleting entity {entity_id}")

        # Call the reducer
        result = await self.client.call_reducer("delete_entity", entity_id)
        return result

    # Relation operations
    async def create_relation(
        self,
        from_entity: str,
        to_entity: str,
        relation_type: str,
        metadata: RelationMetadata
    ) -> str:
        """Create a new relation between entities"""
        if not self.client:
            raise RuntimeError("Client not connected")

        self.logger.debug(f"Creating relation {relation_type} from {from_entity} to {to_entity}")

        # Convert metadata to dictionary
        metadata_dict = asdict(metadata)

        # Call the reducer
        result = await self.client.call_reducer(
            "create_relation",
            from_entity,
            to_entity,
            relation_type,
            metadata_dict
        )
        return result

    # State version operations
    async def commit_state_version(
        self,
        parent_version_id: Optional[str],
        description: str,
        data_hash: str
    ) -> str:
        """Commit a new state version"""
        if not self.client:
            raise RuntimeError("Client not connected")

        self.logger.debug(f"Committing state version: {description}")

        # Call the reducer
        result = await self.client.call_reducer(
            "commit_state_version",
            parent_version_id,
            description,
            data_hash
        )
        return result

    async def record_delta(
        self,
        state_version_id: str,
        operations: List[DeltaOperation],
        metadata: DeltaMetadata
    ) -> str:
        """Record a delta for a state version"""
        if not self.client:
            raise RuntimeError("Client not connected")

        self.logger.debug(f"Recording delta for state version {state_version_id}")

        # Convert operations and metadata to dictionaries
        operations_dict = [asdict(op) for op in operations]
        metadata_dict = asdict(metadata)

        # Call the reducer
        result = await self.client.call_reducer(
            "record_delta",
            state_version_id,
            operations_dict,
            metadata_dict
        )
        return result

    # Event operations
    async def publish_event(
        self,
        event_type: str,
        source: Optional[str],
        data: Dict[str, Any]
    ) -> str:
        """Publish an event to the event log"""
        if not self.client:
            raise RuntimeError("Client not connected")

        self.logger.debug(f"Publishing event of type {event_type}")

        # Call the reducer
        result = await self.client.call_reducer("publish_event", event_type, source, data)
        return result

    # Subscription methods
    def subscribe_entity_changes(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Subscribe to entity table changes"""
        if not self.client:
            raise RuntimeError("Client not connected")

        def on_entity_update(changes):
            for change in changes:
                # Extract change type and entity data
                change_type = "INSERTED" if change.is_insertion() else "DELETED" if change.is_deletion() else "UPDATED"
                entity = change.row_after if change_type != "DELETED" else change.row_before

                # Call the callback
                callback(change_type, entity)

        # Subscribe to the entity table
        subscription = self.client.subscribe("entity", on_entity_update)
        self.subscriptions.append(subscription)

    # Query methods
    async def query_entities(
        self,
        entity_type: Optional[str] = None,
        filters: Optional[List[QueryFilter]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Query entities with optional filters"""
        if not self.client:
            raise RuntimeError("Client not connected")

        # Build query string
        query = "SELECT * FROM entity"
        conditions = []

        if entity_type:
            conditions.append(f"entity_type = '{entity_type}'")

        if filters:
            for filter_item in filters:
                # Convert filter operator to SQL operator
                op_str = self._filter_op_to_sql(filter_item.operator)

                # Format value based on type
                value_str = self._format_value_for_query(filter_item.value)

                conditions.append(f"{filter_item.field} {op_str} {value_str}")

        # Add WHERE clause if we have conditions
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Add limit and offset
        query += f" LIMIT {limit} OFFSET {offset}"

        self.logger.debug(f"Executing query: {query}")

        # Execute the query
        result = await self.client.query(query)
        return result

    # Helper methods
    def _filter_op_to_sql(self, op: FilterOperator) -> str:
        """Convert filter operator to SQL operator"""
        mapping = {
            FilterOperator.EQUALS: "=",
            FilterOperator.NOT_EQUALS: "!=",
            FilterOperator.GREATER_THAN: ">",
            FilterOperator.LESS_THAN: "<",
            FilterOperator.GREATER_OR_EQUAL: ">=",
            FilterOperator.LESS_OR_EQUAL: "<=",
            FilterOperator.CONTAINS: "LIKE",  # Approximate
            FilterOperator.STARTS_WITH: "LIKE",  # Approximate
            FilterOperator.ENDS_WITH: "LIKE",  # Approximate
            FilterOperator.IN: "IN",
            FilterOperator.NOT_IN: "NOT IN"
        }
        return mapping.get(op, "=")

    def _format_value_for_query(self, value: Any) -> str:
        """Format a value for use in a SQL query"""
        if value is None:
            return "NULL"
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # Escape single quotes
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        elif isinstance(value, list):
            # Format as array
            items = [self._format_value_for_query(item) for item in value]
            return f"({', '.join(items)})"
        else:
            # Fallback to string representation
            return f"'{value}'"
```

### Custom Type Definitions

Create type definitions for the Python client that map to the Rust types:

```python
# atlas/graph/persistence/types.py
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union


@dataclass
class EntityMetadata:
    """Metadata associated with an entity"""
    name: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RelationMetadata:
    """Metadata associated with a relation"""
    description: Optional[str] = None
    strength: float = 1.0
    bidirectional: bool = False
    tags: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)


class FilterOperator(Enum):
    """Query filter operators"""
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
    """Filter for database queries"""
    field: str
    operator: FilterOperator
    value: Any


@dataclass
class DeltaMetadata:
    """Metadata for a delta record"""
    description: str
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    parent_delta_id: Optional[str] = None


@dataclass
class DeltaOperation:
    """A single operation in a delta"""
    operation_type: str  # "Set", "Delete", "Insert", "Remove", "Patch"
    path: str
    value: Optional[Any] = None
    index: Optional[int] = None
    patch: Optional[Dict[str, Any]] = None
```

## SpacetimeDB Controller Implementation

Next, create the controller class that manages the SpacetimeDB process:

```python
# atlas/graph/persistence/controller.py
import asyncio
import os
import json
import tempfile
from typing import Dict, Any, Optional, List

from atlas.graph.persistence.config import InnerUniverseConfig
from atlas.graph.persistence.inner_universe import InnerUniverseClient
from atlas.core.logging import get_logger


class InnerUniverseController:
    """Controller for the Inner Universe persistence layer"""

    def __init__(self, config: InnerUniverseConfig):
        self.config = config
        self.process = None
        self.client: Optional[InnerUniverseClient] = None
        self.logger = get_logger("inner_universe_controller")

    async def start_deployment_mode(self) -> Dict[str, Any]:
        """Initialize and configure a new SpacetimeDB instance"""
        # Build module if needed
        if self.config.build_module and self.config.module_dir:
            await self._build_module()

        # Create a temporary config file
        config_file = await self._create_temp_config()

        # Launch SpacetimeDB in deployment mode
        cmd = [
            "spacetime", "deploy",
            "--module-path", self.config.module_path,
            "--db-path", self.config.db_path,
            "--config", config_file,
            "--log-level", self.config.log_level
        ]

        self.logger.info(f"Starting SpacetimeDB in deployment mode: {' '.join(cmd)}")

        # Start the process
        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Wait for deployment to complete
        stdout, stderr = await self.process.communicate()

        if self.process.returncode != 0:
            error_msg = stderr.decode()
            self.logger.error(f"Deployment failed: {error_msg}")
            raise RuntimeError(f"Deployment failed: {error_msg}")

        self.logger.info("SpacetimeDB deployment completed successfully")

        # Clean up temporary config file
        os.unlink(config_file)

        # Connect client
        self.client = InnerUniverseClient(self.config)
        await self.client.connect()

        return {
            "status": "deployed",
            "stdout": stdout.decode()
        }

    async def start_server_mode(self) -> InnerUniverseClient:
        """Start SpacetimeDB in server mode to handle ongoing requests"""
        # Launch SpacetimeDB in server mode
        cmd = [
            "spacetime", "run",
            "--db-path", self.config.db_path,
            "--address", self.config.address,
            "--port", str(self.config.port),
            "--log-level", self.config.log_level
        ]

        self.logger.info(f"Starting SpacetimeDB in server mode: {' '.join(cmd)}")

        # Start the process
        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Wait a bit for the server to start
        await asyncio.sleep(1)

        # Check if process is still running
        if self.process.returncode is not None:
            stderr = await self.process.stderr.read()
            error_msg = stderr.decode()
            self.logger.error(f"Server failed to start: {error_msg}")
            raise RuntimeError(f"Server failed to start: {error_msg}")

        # Connect client
        self.client = InnerUniverseClient(self.config)
        connected = await self.client.connect()

        if not connected:
            self.logger.error("Failed to connect to SpacetimeDB server")
            await self.stop()
            raise RuntimeError("Failed to connect to SpacetimeDB server")

        self.logger.info("SpacetimeDB server running and client connected")
        return self.client

    async def stop(self):
        """Stop the SpacetimeDB instance and disconnect client"""
        if self.client:
            await self.client.disconnect()
            self.client = None

        if self.process and self.process.returncode is None:
            self.process.terminate()
            await self.process.wait()
            self.logger.info("SpacetimeDB process terminated")

        self.process = None

    async def _build_module(self):
        """Build the Rust module to WebAssembly"""
        cmd = [
            "cargo", "build",
            "--release",
            "--target", "wasm32-unknown-unknown"
        ]

        self.logger.info(f"Building module: {' '.join(cmd)}")

        # Run in the module directory
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self.config.module_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode()
            self.logger.error(f"Module build failed: {error_msg}")
            raise RuntimeError(f"Module build failed: {error_msg}")

        self.logger.info("Module built successfully")

    async def _create_temp_config(self) -> str:
        """Create a temporary config file for SpacetimeDB deployment"""
        # Create a temporary file
        fd, path = tempfile.mkstemp(suffix=".json")

        # Write the config to the file
        with os.fdopen(fd, 'w') as f:
            json.dump(self.config.to_dict(), f)

        return path
```

## Mapping NERV Components to SpacetimeDB

### Entity-Relation Mapping

The following table shows how NERV components map to SpacetimeDB tables:

| NERV Component | SpacetimeDB Table(s)            | Description                                 |
| -------------- | ------------------------------- | ------------------------------------------- |
| Entity         | `entity`                        | Stores entities from NERV's knowledge graph |
| Relation       | `relation`                      | Stores relationships between entities       |
| Temporal       | `state_version`, `delta_record` | Stores versioned state and change history   |
| Event Bus      | `event_log`                     | Records events for synchronization          |

### Integration with EventBus

To integrate with NERV's EventBus, create a SpacetimeEventBus adapter:

```python
# atlas/graph/persistence/event_bus.py
from typing import Dict, Any, Optional, Callable, List
import asyncio

from atlas.agents.messaging.message import Message
from atlas.core.logging import get_logger
from atlas.graph.persistence.inner_universe import InnerUniverseClient


class SpacetimeEventBus:
    """Event bus adapter for SpacetimeDB integration"""

    def __init__(self, client: InnerUniverseClient):
        self.client = client
        self.logger = get_logger("spacetime_event_bus")
        self.handlers: Dict[str, List[Callable[[Message], None]]] = {}

    def register_handler(self, event_type: str, handler: Callable[[Message], None]) -> None:
        """Register a handler for a specific event type"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []

        self.handlers[event_type].append(handler)
        self.logger.debug(f"Registered handler for event type: {event_type}")

    async def publish(self, event_type: str, data: Dict[str, Any], source: Optional[str] = None) -> str:
        """Publish an event to the SpacetimeDB event log"""
        try:
            event_id = await self.client.publish_event(event_type, source, data)
            self.logger.debug(f"Published event {event_id} of type {event_type}")
            return event_id
        except Exception as e:
            self.logger.error(f"Failed to publish event: {e}")
            raise

    def subscribe_to_events(self) -> None:
        """Subscribe to events from the SpacetimeDB event log"""
        def on_event_change(change_type: str, event: Dict[str, Any]) -> None:
            if change_type != "INSERTED":
                return  # Only process new events

            # Convert to message format
            message = Message(
                id=event.get("event_id", ""),
                type=event.get("event_type", ""),
                source=event.get("source"),
                timestamp=event.get("timestamp", 0),
                data=event.get("data", {})
            )

            # Call registered handlers
            event_type = event.get("event_type", "")
            if event_type in self.handlers:
                for handler in self.handlers[event_type]:
                    asyncio.create_task(self._call_handler(handler, message))

        # Subscribe to event_log table changes
        self.client.subscribe_entity_changes(on_event_change)
        self.logger.info("Subscribed to event_log changes")

    async def _call_handler(self, handler: Callable[[Message], None], message: Message) -> None:
        """Call a handler with error handling"""
        try:
            handler(message)
        except Exception as e:
            self.logger.error(f"Error in event handler: {e}")
```

### Integration with TemporalStore

Next, create an adapter for NERV's TemporalStore:

```python
# atlas/graph/persistence/temporal_store.py
from typing import Dict, Any, Optional, List
import hashlib
import json

from atlas.core.logging import get_logger
from atlas.graph.persistence.inner_universe import InnerUniverseClient
from atlas.graph.persistence.types import DeltaMetadata, DeltaOperation


class SpacetimeTemporalStore:
    """TemporalStore adapter for SpacetimeDB integration"""

    def __init__(self, client: InnerUniverseClient):
        self.client = client
        self.logger = get_logger("spacetime_temporal_store")
        self.current_version_id: Optional[str] = None

    async def commit_version(self, state: Dict[str, Any], description: str) -> str:
        """Commit a new state version"""
        # Calculate hash of state for integrity checking
        state_json = json.dumps(state, sort_keys=True)
        data_hash = hashlib.sha256(state_json.encode()).hexdigest()

        # Commit the state version
        version_id = await self.client.commit_state_version(
            self.current_version_id,
            description,
            data_hash
        )

        # Update current version
        self.current_version_id = version_id

        self.logger.info(f"Committed state version {version_id}: {description}")

        return version_id

    async def record_state_delta(
        self,
        version_id: str,
        operations: List[Dict[str, Any]],
        description: str
    ) -> str:
        """Record a delta for a state version"""
        # Convert operations to DeltaOperation objects
        delta_operations = []
        for op in operations:
            op_type = op.get("type", "")
            path = op.get("path", "")

            if op_type == "set":
                delta_operations.append(DeltaOperation(
                    operation_type="Set",
                    path=path,
                    value=op.get("value")
                ))
            elif op_type == "delete":
                delta_operations.append(DeltaOperation(
                    operation_type="Delete",
                    path=path
                ))
            elif op_type == "insert":
                delta_operations.append(DeltaOperation(
                    operation_type="Insert",
                    path=path,
                    index=op.get("index"),
                    value=op.get("value")
                ))
            elif op_type == "remove":
                delta_operations.append(DeltaOperation(
                    operation_type="Remove",
                    path=path,
                    index=op.get("index", 0)
                ))
            elif op_type == "patch":
                delta_operations.append(DeltaOperation(
                    operation_type="Patch",
                    path=path,
                    patch=op.get("patch", {})
                ))

        # Create delta metadata
        metadata = DeltaMetadata(
            description=description,
            author=None,  # Could be populated from context
            tags=[]
        )

        # Record the delta
        delta_id = await self.client.record_delta(version_id, delta_operations, metadata)

        self.logger.info(f"Recorded delta {delta_id} for version {version_id}")

        return delta_id

    async def get_current_version(self) -> Optional[Dict[str, Any]]:
        """Get the current state version"""
        if not self.current_version_id:
            # Try to find the latest version
            versions = await self.client.query_entities(
                entity_type="state_version",
                limit=1,
                filters=[]  # No filters to get latest
            )

            if versions:
                self.current_version_id = versions[0].get("version_id")
            else:
                return None

        # Query the state version
        if self.current_version_id:
            versions = await self.client.query_entities(
                entity_type="state_version",
                filters=[{
                    "field": "version_id",
                    "operator": "EQUALS",
                    "value": self.current_version_id
                }]
            )

            if versions:
                return versions[0]

        return None
```

## Integration with NERV Core

### Persistence Manager

Create a central manager class to coordinate the SpacetimeDB integration:

```python
# atlas/graph/persistence/manager.py
from typing import Dict, Any, Optional, List
import asyncio

from atlas.core.logging import get_logger
from atlas.graph.persistence.config import InnerUniverseConfig
from atlas.graph.persistence.controller import InnerUniverseController
from atlas.graph.persistence.inner_universe import InnerUniverseClient
from atlas.graph.persistence.event_bus import SpacetimeEventBus
from atlas.graph.persistence.temporal_store import SpacetimeTemporalStore


class PersistenceManager:
    """Manager for the Inner Universe persistence layer"""

    def __init__(self, config: Optional[InnerUniverseConfig] = None):
        self.config = config or InnerUniverseConfig()
        self.controller = InnerUniverseController(self.config)
        self.client: Optional[InnerUniverseClient] = None
        self.event_bus: Optional[SpacetimeEventBus] = None
        self.temporal_store: Optional[SpacetimeTemporalStore] = None
        self.logger = get_logger("persistence_manager")
        self._initialized = False

    async def initialize(self, deploy: bool = False) -> bool:
        """Initialize the persistence layer"""
        try:
            if deploy:
                # Deploy in deployment mode
                await self.controller.start_deployment_mode()
            else:
                # Start in server mode
                self.client = await self.controller.start_server_mode()

                # Create adapters
                self.event_bus = SpacetimeEventBus(self.client)
                self.temporal_store = SpacetimeTemporalStore(self.client)

                # Subscribe to events
                self.event_bus.subscribe_to_events()

            self._initialized = True
            self.logger.info("Persistence manager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize persistence layer: {e}")
            await self.shutdown()
            return False

    async def shutdown(self) -> None:
        """Shutdown the persistence layer"""
        await self.controller.stop()
        self.client = None
        self.event_bus = None
        self.temporal_store = None
        self._initialized = False
        self.logger.info("Persistence manager shut down")

    def is_initialized(self) -> bool:
        """Check if the persistence layer is initialized"""
        return self._initialized

    # Entity operations
    async def create_entity(self, entity_type: str, metadata: Dict[str, Any]) -> str:
        """Create a new entity"""
        self._check_initialized()
        return await self.client.create_entity(entity_type, metadata)

    async def get_entity(self, entity_id: str) -> Dict[str, Any]:
        """Get an entity by ID"""
        self._check_initialized()
        return await self.client.get_entity(entity_id)

    async def update_entity(self, entity_id: str, metadata: Dict[str, Any]) -> bool:
        """Update an entity's metadata"""
        self._check_initialized()
        return await self.client.update_entity(entity_id, metadata)

    async def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity"""
        self._check_initialized()
        return await self.client.delete_entity(entity_id)

    # Relation operations
    async def create_relation(
        self,
        from_entity: str,
        to_entity: str,
        relation_type: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Create a new relation between entities"""
        self._check_initialized()
        return await self.client.create_relation(from_entity, to_entity, relation_type, metadata)

    # State version operations
    async def commit_version(self, state: Dict[str, Any], description: str) -> str:
        """Commit a new state version"""
        self._check_initialized()
        if not self.temporal_store:
            raise RuntimeError("TemporalStore not initialized")
        return await self.temporal_store.commit_version(state, description)

    # Event operations
    async def publish_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: Optional[str] = None
    ) -> str:
        """Publish an event"""
        self._check_initialized()
        if not self.event_bus:
            raise RuntimeError("EventBus not initialized")
        return await self.event_bus.publish(event_type, data, source)

    def _check_initialized(self) -> None:
        """Check if the persistence layer is initialized"""
        if not self._initialized or not self.client:
            raise RuntimeError("Persistence layer not initialized")
```

## Example Operations

### Entity Creation & Management

```python
# Example of using the persistence manager for entity operations
async def entity_example():
    # Create the persistence manager
    manager = PersistenceManager()

    # Initialize without deployment (assuming SpacetimeDB is already running)
    await manager.initialize()

    try:
        # Create a new entity
        entity_id = await manager.create_entity(
            entity_type="Person",
            metadata={
                "name": "John Doe",
                "description": "A test user",
                "tags": ["test", "example"],
                "properties": {
                    "age": 30,
                    "email": "john@example.com"
                }
            }
        )
        print(f"Created entity: {entity_id}")

        # Get the entity
        entity = await manager.get_entity(entity_id)
        print(f"Retrieved entity: {entity}")

        # Update the entity
        success = await manager.update_entity(
            entity_id=entity_id,
            metadata={
                "name": "John Doe",
                "description": "An updated test user",
                "tags": ["test", "example", "updated"],
                "properties": {
                    "age": 31,
                    "email": "john.doe@example.com"
                }
            }
        )
        print(f"Updated entity: {success}")

        # Create a related entity
        other_entity_id = await manager.create_entity(
            entity_type="Company",
            metadata={
                "name": "Acme Inc",
                "description": "A test company",
                "tags": ["test", "example"],
                "properties": {
                    "industry": "Technology"
                }
            }
        )
        print(f"Created related entity: {other_entity_id}")

        # Create a relation between entities
        relation_id = await manager.create_relation(
            from_entity=entity_id,
            to_entity=other_entity_id,
            relation_type="WORKS_FOR",
            metadata={
                "description": "Employment relationship",
                "strength": 0.9,
                "bidirectional": False,
                "tags": ["employment"],
                "properties": {
                    "start_date": "2023-01-01",
                    "position": "Software Engineer"
                }
            }
        )
        print(f"Created relation: {relation_id}")
    finally:
        # Shut down the persistence layer
        await manager.shutdown()
```

### State Versioning Example

```python
# Example of using the persistence manager for state versioning
async def versioning_example():
    # Create the persistence manager
    manager = PersistenceManager()

    # Initialize without deployment (assuming SpacetimeDB is already running)
    await manager.initialize()

    try:
        # Create initial state
        initial_state = {
            "version": "1.0.0",
            "settings": {
                "theme": "light",
                "notifications": True,
                "language": "en"
            },
            "data": {
                "items": [1, 2, 3],
                "count": 3
            }
        }

        # Commit initial state version
        version_id = await manager.commit_version(
            state=initial_state,
            description="Initial state version"
        )
        print(f"Committed initial state version: {version_id}")

        # Record a delta for adding an item
        add_operations = [
            {
                "type": "insert",
                "path": "data.items",
                "index": 3,
                "value": 4
            },
            {
                "type": "set",
                "path": "data.count",
                "value": 4
            }
        ]

        delta_id = await manager.temporal_store.record_delta(
            version_id=version_id,
            operations=add_operations,
            description="Added item 4"
        )
        print(f"Recorded delta: {delta_id}")

        # Update state with the changes
        updated_state = {
            "version": "1.0.0",
            "settings": {
                "theme": "light",
                "notifications": True,
                "language": "en"
            },
            "data": {
                "items": [1, 2, 3, 4],
                "count": 4
            }
        }

        # Commit updated state version
        new_version_id = await manager.commit_version(
            state=updated_state,
            description="Added item 4"
        )
        print(f"Committed updated state version: {new_version_id}")

        # Get current version
        current_version = await manager.temporal_store.get_current_version()
        print(f"Current version: {current_version}")
    finally:
        # Shut down the persistence layer
        await manager.shutdown()
```

### Event System Example

```python
# Example of using the persistence manager for events
async def event_example():
    # Create the persistence manager
    manager = PersistenceManager()

    # Initialize without deployment (assuming SpacetimeDB is already running)
    await manager.initialize()

    try:
        # Register event handler
        def handle_user_event(message):
            print(f"Received user event: {message.data}")

        manager.event_bus.register_handler("USER_ACTION", handle_user_event)

        # Publish an event
        event_id = await manager.publish_event(
            event_type="USER_ACTION",
            data={
                "action": "login",
                "user_id": "12345",
                "timestamp": 1633036800
            },
            source="auth_service"
        )
        print(f"Published event: {event_id}")

        # Wait for event processing
        await asyncio.sleep(1)
    finally:
        # Shut down the persistence layer
        await manager.shutdown()
```

## Testing the Integration

### Unit Testing Setup

Create test utilities for the SpacetimeDB integration:

```python
# atlas/tests/graph/persistence/conftest.py
import pytest
import asyncio
import tempfile
import os
import shutil

from atlas.graph.persistence.config import InnerUniverseConfig
from atlas.graph.persistence.controller import InnerUniverseController
from atlas.graph.persistence.manager import PersistenceManager


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def spacetime_config():
    """Create a temporary configuration for testing"""
    # Create a temporary directory for the database
    temp_dir = tempfile.mkdtemp()

    try:
        # Create configuration
        config = InnerUniverseConfig(
            address="127.0.0.1",
            port=3789,  # Use a different port for testing
            db_path=os.path.join(temp_dir, "test_db"),
            log_level="info",
            module_path="/path/to/test_module.wasm"  # Replace with the actual test module path
        )

        yield config
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)


@pytest.fixture(scope="session")
async def spacetime_controller(spacetime_config):
    """Create and start a SpacetimeDB controller"""
    controller = InnerUniverseController(spacetime_config)

    try:
        # Deploy the test database (skip if using a mock)
        # await controller.start_deployment_mode()

        # Start the server
        await controller.start_server_mode()

        yield controller
    finally:
        # Stop the controller
        await controller.stop()


@pytest.fixture(scope="function")
async def persistence_manager(spacetime_controller):
    """Create a persistence manager with an initialized client"""
    manager = PersistenceManager(spacetime_controller.config)

    # Use the existing client
    manager.client = spacetime_controller.client
    manager.event_bus = SpacetimeEventBus(manager.client)
    manager.temporal_store = SpacetimeTemporalStore(manager.client)
    manager._initialized = True

    yield manager
```

### Basic Test Implementation

Create basic tests for the persistence layer:

```python
# atlas/tests/graph/persistence/test_entities.py
import pytest

from atlas.graph.persistence.types import EntityMetadata, RelationMetadata


async def test_create_entity(persistence_manager):
    """Test creating an entity"""
    # Create test metadata
    metadata = EntityMetadata(
        name="Test Entity",
        description="A test entity",
        tags=["test", "entity"],
        properties={"test_prop": "test_value"}
    )

    # Create the entity
    entity_id = await persistence_manager.create_entity("TestType", metadata)

    # Verify the entity was created
    assert entity_id is not None
    assert isinstance(entity_id, str)

    # Get the entity
    entity = await persistence_manager.get_entity(entity_id)

    # Verify the entity data
    assert entity is not None
    assert entity["id"] == entity_id
    assert entity["entity_type"] == "TestType"
    assert entity["metadata"]["name"] == "Test Entity"
    assert "test" in entity["metadata"]["tags"]


async def test_create_and_update_entity(persistence_manager):
    """Test creating and updating an entity"""
    # Create initial metadata
    initial_metadata = EntityMetadata(
        name="Initial Name",
        description="Initial description",
        tags=["initial"],
        properties={"initial_prop": "initial_value"}
    )

    # Create the entity
    entity_id = await persistence_manager.create_entity("TestType", initial_metadata)

    # Updated metadata
    updated_metadata = EntityMetadata(
        name="Updated Name",
        description="Updated description",
        tags=["initial", "updated"],
        properties={"initial_prop": "initial_value", "new_prop": "new_value"}
    )

    # Update the entity
    result = await persistence_manager.update_entity(entity_id, updated_metadata)
    assert result is True

    # Get the updated entity
    updated_entity = await persistence_manager.get_entity(entity_id)

    # Verify the updates
    assert updated_entity["metadata"]["name"] == "Updated Name"
    assert updated_entity["metadata"]["description"] == "Updated description"
    assert "updated" in updated_entity["metadata"]["tags"]
    assert updated_entity["metadata"]["properties"]["new_prop"] == "new_value"


async def test_create_relation(persistence_manager):
    """Test creating a relation between entities"""
    # Create two entities
    entity1_id = await persistence_manager.create_entity(
        "TestType1",
        EntityMetadata(name="Entity 1")
    )

    entity2_id = await persistence_manager.create_entity(
        "TestType2",
        EntityMetadata(name="Entity 2")
    )

    # Create relation metadata
    relation_metadata = RelationMetadata(
        description="Test relation",
        strength=0.75,
        bidirectional=True,
        tags=["test_relation"],
        properties={"rel_prop": "rel_value"}
    )

    # Create the relation
    relation_id = await persistence_manager.create_relation(
        from_entity=entity1_id,
        to_entity=entity2_id,
        relation_type="TEST_RELATION",
        metadata=relation_metadata
    )

    # Verify the relation was created
    assert relation_id is not None
    assert isinstance(relation_id, str)
```

## Error Handling Patterns

Implement consistent error handling throughout the persistence layer:

```python
# atlas/graph/persistence/errors.py
class PersistenceError(Exception):
    """Base class for persistence layer errors"""
    pass


class ConnectionError(PersistenceError):
    """Error connecting to SpacetimeDB"""
    pass


class EntityNotFoundError(PersistenceError):
    """Entity not found in the database"""
    pass


class RelationNotFoundError(PersistenceError):
    """Relation not found in the database"""
    pass


class VersionNotFoundError(PersistenceError):
    """State version not found in the database"""
    pass


class AuthorizationError(PersistenceError):
    """Not authorized to perform the operation"""
    pass


class ValidationError(PersistenceError):
    """Input validation failed"""
    pass
```

Update the client to use these error types:

```python
# Example client method with improved error handling
async def get_entity(self, entity_id: str) -> Dict[str, Any]:
    """Retrieve an entity by ID"""
    if not self.client:
        raise ConnectionError("Client not connected")

    self.logger.debug(f"Retrieving entity {entity_id}")

    try:
        # Query the entity table directly
        entities = await self.client.query(f"SELECT * FROM entity WHERE id = '{entity_id}'")

        if not entities:
            raise EntityNotFoundError(f"Entity not found: {entity_id}")

        return entities[0]
    except Exception as e:
        if isinstance(e, EntityNotFoundError):
            raise
        else:
            self.logger.error(f"Error retrieving entity {entity_id}: {e}")
            raise PersistenceError(f"Error retrieving entity: {e}")
```

## Performance Optimization Strategies

### Connection Pooling

Implement connection pooling for SpacetimeDB clients:

```python
# atlas/graph/persistence/pool.py
import asyncio
from typing import Dict, List, Optional, Any, Callable
import time

from atlas.core.logging import get_logger
from atlas.graph.persistence.inner_universe import InnerUniverseClient
from atlas.graph.persistence.config import InnerUniverseConfig


class ClientPool:
    """Connection pool for SpacetimeDB clients"""

    def __init__(self, config: InnerUniverseConfig, min_size: int = 2, max_size: int = 10):
        self.config = config
        self.min_size = min_size
        self.max_size = max_size
        self.pool: List[InnerUniverseClient] = []
        self.in_use: Dict[InnerUniverseClient, float] = {}
        self.lock = asyncio.Lock()
        self.logger = get_logger("client_pool")

    async def initialize(self) -> None:
        """Initialize the connection pool"""
        async with self.lock:
            self.logger.info(f"Initializing client pool with min_size={self.min_size}")

            # Create initial connections
            for _ in range(self.min_size):
                client = InnerUniverseClient(self.config)
                await client.connect()
                self.pool.append(client)

            self.logger.info(f"Client pool initialized with {len(self.pool)} connections")

    async def acquire(self) -> InnerUniverseClient:
        """Acquire a client from the pool"""
        async with self.lock:
            # Try to get an available client
            if self.pool:
                client = self.pool.pop(0)
                self.in_use[client] = time.time()
                return client

            # If the pool is empty but we haven't reached max_size, create a new client
            if len(self.in_use) < self.max_size:
                client = InnerUniverseClient(self.config)
                await client.connect()
                self.in_use[client] = time.time()
                self.logger.debug(f"Created new client, pool size: {len(self.pool)}, in use: {len(self.in_use)}")
                return client

            # If we've reached max_size, wait for a client to be released
            self.logger.warning(f"Client pool exhausted (max_size={self.max_size}), waiting for release")

        # Wait outside the lock to prevent deadlock
        while True:
            await asyncio.sleep(0.1)

            async with self.lock:
                if self.pool:
                    client = self.pool.pop(0)
                    self.in_use[client] = time.time()
                    return client

    async def release(self, client: InnerUniverseClient) -> None:
        """Release a client back to the pool"""
        async with self.lock:
            if client in self.in_use:
                del self.in_use[client]
                self.pool.append(client)
                self.logger.debug(f"Released client to pool, pool size: {len(self.pool)}, in use: {len(self.in_use)}")
            else:
                self.logger.warning(f"Attempted to release a client that isn't in use")

    async def shutdown(self) -> None:
        """Shut down all clients in the pool"""
        async with self.lock:
            # Close all clients in the pool
            for client in self.pool:
                await client.disconnect()

            # Close all clients in use
            for client in list(self.in_use.keys()):
                await client.disconnect()

            self.pool.clear()
            self.in_use.clear()

            self.logger.info("Client pool shut down")
```

### Request Batching

Implement batching for operations:

```python
# atlas/graph/persistence/batch.py
from typing import Dict, List, Any, TypeVar, Generic
import asyncio

from atlas.core.logging import get_logger
from atlas.graph.persistence.inner_universe import InnerUniverseClient
from atlas.graph.persistence.types import EntityMetadata

T = TypeVar('T')


class BatchOperation(Generic[T]):
    """A batch operation with a future result"""

    def __init__(self):
        self.future: asyncio.Future[T] = asyncio.Future()


class EntityBatch:
    """Batch processor for entity operations"""

    def __init__(self, client: InnerUniverseClient, max_batch_size: int = 50, max_wait_ms: int = 100):
        self.client = client
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self.logger = get_logger("entity_batch")
        self.pending_operations: List[Dict[str, Any]] = []
        self.pending_futures: List[asyncio.Future] = []
        self.batch_task: Optional[asyncio.Task] = None
        self.lock = asyncio.Lock()

    async def create_entity(self, entity_type: str, metadata: EntityMetadata) -> str:
        """Queue an entity creation in the batch"""
        operation = BatchOperation[str]()

        async with self.lock:
            # Add to pending operations
            self.pending_operations.append({
                "type": "create_entity",
                "entity_type": entity_type,
                "metadata": metadata,
                "operation": operation
            })

            self.pending_futures.append(operation.future)

            # Start batch task if not running
            if not self.batch_task or self.batch_task.done():
                self.batch_task = asyncio.create_task(self._process_batch())

            # Process immediately if batch size reached
            if len(self.pending_operations) >= self.max_batch_size:
                self.batch_task.cancel()
                self.batch_task = asyncio.create_task(self._process_batch())

        # Wait for result
        return await operation.future

    async def _process_batch(self) -> None:
        """Process the current batch of operations"""
        try:
            # Wait for more operations or timeout
            try:
                await asyncio.sleep(self.max_wait_ms / 1000)
            except asyncio.CancelledError:
                # Batch size reached, process immediately
                pass

            async with self.lock:
                # Get the current batch
                operations = self.pending_operations.copy()
                futures = self.pending_futures.copy()

                # Clear pending lists
                self.pending_operations.clear()
                self.pending_futures.clear()

            if not operations:
                return

            self.logger.debug(f"Processing batch of {len(operations)} operations")

            # Group operations by type
            create_entities = []

            for op in operations:
                if op["type"] == "create_entity":
                    create_entities.append(op)

            # Process create_entity operations
            if create_entities:
                try:
                    # Call reducer for each operation
                    for op in create_entities:
                        entity_id = await self.client.create_entity(
                            op["entity_type"],
                            op["metadata"]
                        )
                        op["operation"].future.set_result(entity_id)
                except Exception as e:
                    # Set exception for all futures
                    for op in create_entities:
                        if not op["operation"].future.done():
                            op["operation"].future.set_exception(e)

            self.logger.debug(f"Batch processing completed")
        except Exception as e:
            self.logger.error(f"Error processing batch: {e}")

            # Set exception for all futures
            async with self.lock:
                for future in self.pending_futures:
                    if not future.done():
                        future.set_exception(e)

                self.pending_operations.clear()
                self.pending_futures.clear()
```

### Caching Layer

Implement a caching layer for frequently accessed data:

```python
# atlas/graph/persistence/cache.py
from typing import Dict, Any, Optional, List, Callable, TypeVar, Generic
import time
import asyncio

T = TypeVar('T')


class CacheEntry(Generic[T]):
    """An entry in the cache with expiration"""

    def __init__(self, value: T, ttl_seconds: float):
        self.value = value
        self.expires_at = time.time() + ttl_seconds

    def is_expired(self) -> bool:
        """Check if the entry is expired"""
        return time.time() > self.expires_at


class Cache(Generic[T]):
    """Simple in-memory cache with expiration"""

    def __init__(self, ttl_seconds: float = 300):
        self.ttl_seconds = ttl_seconds
        self.entries: Dict[str, CacheEntry[T]] = {}
        self.cleanup_task: Optional[asyncio.Task] = None

    def get(self, key: str) -> Optional[T]:
        """Get a value from the cache"""
        entry = self.entries.get(key)

        if entry is None or entry.is_expired():
            if entry is not None:
                del self.entries[key]
            return None

        return entry.value

    def set(self, key: str, value: T, ttl_seconds: Optional[float] = None) -> None:
        """Set a value in the cache with an optional custom TTL"""
        ttl = ttl_seconds if ttl_seconds is not None else self.ttl_seconds
        self.entries[key] = CacheEntry(value, ttl)

    def invalidate(self, key: str) -> None:
        """Remove a key from the cache"""
        if key in self.entries:
            del self.entries[key]

    def clear(self) -> None:
        """Clear all entries from the cache"""
        self.entries.clear()

    async def get_or_compute(self, key: str, compute_func: Callable[[], T]) -> T:
        """Get a value from the cache or compute it if not present"""
        value = self.get(key)

        if value is None:
            value = compute_func()
            self.set(key, value)

        return value

    async def cleanup(self) -> None:
        """Remove expired entries from the cache"""
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._cleanup_task())

    async def _cleanup_task(self) -> None:
        """Background task to clean up expired entries"""
        while True:
            # Check all entries
            keys_to_remove = []

            for key, entry in self.entries.items():
                if entry.is_expired():
                    keys_to_remove.append(key)

            # Remove expired entries
            for key in keys_to_remove:
                del self.entries[key]

            # Wait before next cleanup
            await asyncio.sleep(60)  # Clean up every minute
```

Add caching to the client:

```python
# Enhanced client method with caching
def get_entity_with_cache(self, entity_id: str) -> Dict[str, Any]:
    """Get an entity by ID with caching"""
    # Check cache first
    cache_key = f"entity:{entity_id}"
    cached_entity = self.cache.get(cache_key)

    if cached_entity:
        self.logger.debug(f"Cache hit for entity {entity_id}")
        return cached_entity

    # Not in cache, query from database
    entity = await self.get_entity(entity_id)

    # Store in cache
    self.cache.set(cache_key, entity)

    return entity
```

## Conclusion

This implementation guide provides a comprehensive approach to integrating SpacetimeDB with the NERV architecture. By following these patterns and examples, you can create a robust persistence layer that aligns with NERV's event-driven design, effect system, and state projection capabilities.

Key benefits of this integration include:

1. **Persistent Storage**: Durable storage for entities, relations, and events
2. **Real-time Synchronization**: Event-driven updates between clients
3. **Temporal State Management**: Support for versioned state and deltas
4. **Performance Optimization**: Connection pooling, batching, and caching
5. **Error Handling**: Robust error patterns and recovery mechanisms

Next steps for the integration include:

1. Implementing the full set of query capabilities
2. Adding transaction support for multi-step operations
3. Creating advanced analytics and reporting features
4. Implementing sharding for horizontal scaling
5. Adding monitoring and observability instrumentation
