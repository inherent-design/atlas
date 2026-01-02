---
title: Core Services
---

# Core Services Integration Plan - May 19, 2025

::: danger SUPERSEDED BY CLEAN BREAK APPROACH
This integration plan has been **superseded** by the [Clean Break Architecture Manifesto](../clean_break_manifest.md) which advocates for a more fundamental redesign rather than progressive integration.
:::

::: warning REVISED APPROACH NEEDED
Our initial integration approach attempted to layer services onto existing architecture. After evaluation, we've determined that a more thorough redesign is needed to fully leverage the service architecture's benefits. See the [Clean Break Architecture Manifesto](../clean_break_manifest.md) for the new direction.
:::

::: tip Original Status
- **Date**: May 17, 2025
- **Previous Approach**: Progressive integration of core services
- **Current Direction**: Clean break architecture redesign
- **New Target Completion**: June 10, 2025 (extended timeline for complete redesign)
:::

## 1. Original Integration Overview (SUPERSEDED)

The Core Services Layer provides fundamental infrastructure services that can significantly enhance the capabilities of our existing systems. Our initial integration strategy followed these principles:

1. **Non-disruptive Integration**: Add capabilities without breaking existing functionality
2. **Progressive Adoption**: Integrate gradually, starting with high-value use cases
3. **Clean Architecture**: Maintain clear boundaries between components
4. **Performance Focus**: Ensure integrations do not negatively impact performance
5. **Testability**: Ensure all integrations are covered by comprehensive tests

## 2. Provider System Integration

### 2.1 Event-Enabled Provider System

The event system offers powerful capabilities for tracking provider operations, enabling:

- More detailed telemetry
- Improved error tracking
- Better debugging capabilities
- Performance monitoring

### 2.2 Implementation Strategy

```python
# Step 1: Create an EventEnabledProvider mixin class
class EventEnabledProvider:
    """Mixin class that adds event system capabilities to providers."""

    def __init__(self, event_system: EventSystem = None, **kwargs):
        """Initialize with an event system.

        Args:
            event_system: Event system to use for publishing events.
            **kwargs: Additional keyword arguments.
        """
        self.event_system = event_system or create_event_system()

        # Add middleware for event tracking
        self.event_system.add_middleware(create_logging_middleware())
        self.event_system.add_middleware(create_timing_middleware())

        # Initialize event history if needed
        self.history_middleware = HistoryMiddleware(max_history=100)
        self.event_system.add_middleware(self.history_middleware)

    def publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish an event with the provider as the source.

        Args:
            event_type: Type of event to publish.
            data: Event data.
        """
        if self.event_system:
            # Use provider name as source if available
            source = getattr(self, "name", "unknown_provider")
            self.event_system.publish(
                event_type=event_type,
                data=data,
                source=f"provider.{source}"
            )
```

### 2.3 Provider Integration Points

1. **Provider Factory**
   - Inject event system during provider creation
   - Enable configuration of event system through options

2. **Provider Base Class**
   - Add event hooks for key operations (generate, stream, validate)
   - Publish events for request validation, generation start/end, token counts

3. **ProviderGroup**
   - Track fallback behavior with events
   - Monitor selection criteria and decisions

### 2.4 Event Types

Standard event types for the provider system:

| Event Type                  | Description                  | Data Fields                             |
| --------------------------- | ---------------------------- | --------------------------------------- |
| `provider.generate.start`   | Generation request initiated | request, model, options                 |
| `provider.generate.end`     | Generation completed         | request, response, tokens, latency      |
| `provider.generate.error`   | Generation error             | request, error, retry_count             |
| `provider.stream.start`     | Stream started               | request, model, options                 |
| `provider.stream.chunk`     | Stream chunk received        | chunk_size, content                     |
| `provider.stream.end`       | Stream completed             | total_chunks, tokens, latency           |
| `provider.stream.error`     | Stream error                 | request, error, partial_content         |
| `provider.validate.failure` | Validation failure           | request, validation_errors              |
| `provider.fallback`         | Provider fallback occurred   | original_provider, new_provider, reason |

## 3. Agent System Integration

### 3.1 Event-Aware Agent System

The agent system can benefit significantly from event-driven architecture:

- Track agent lifecycle and state transitions
- Monitor agent communications and task execution
- Implement event-based agent coordination
- Enable debugging of complex agent workflows

### 3.2 Implementation Strategy

```python
# Step 1: Create a BaseEventAgent class that uses the event system
class BaseEventAgent(Agent):
    """Base class for agents with event system integration."""

    def __init__(self, event_system: EventSystem = None, **kwargs):
        """Initialize the agent with an event system.

        Args:
            event_system: Event system to use for publishing events.
            **kwargs: Additional arguments passed to the parent class.
        """
        super().__init__(**kwargs)
        self.event_system = event_system or create_event_system()

        # Subscribe to relevant events if needed
        self.subscription_ids = []

        # Add middleware
        self.event_system.add_middleware(create_timing_middleware())

        # Initialize event tracking
        self._task_start_times = {}

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task with event tracking.

        Args:
            task: The task to execute.

        Returns:
            The task result.
        """
        task_id = task.get("task_id", str(uuid.uuid4()))

        # Track task start
        self._task_start_times[task_id] = time.time()
        self.event_system.publish(
            event_type="agent.task.start",
            data={
                "task_id": task_id,
                "task_type": task.get("task_type", "unknown"),
                "agent_id": self.agent_id,
                "agent_type": self.__class__.__name__
            }
        )

        try:
            # Execute task
            result = super().execute_task(task)

            # Track task completion
            elapsed = time.time() - self._task_start_times.get(task_id, time.time())
            self.event_system.publish(
                event_type="agent.task.complete",
                data={
                    "task_id": task_id,
                    "success": True,
                    "execution_time": elapsed,
                    "agent_id": self.agent_id,
                    "result_size": len(str(result)) if result else 0
                }
            )

            return result

        except Exception as e:
            # Track task failure
            elapsed = time.time() - self._task_start_times.get(task_id, time.time())
            self.event_system.publish(
                event_type="agent.task.error",
                data={
                    "task_id": task_id,
                    "success": False,
                    "execution_time": elapsed,
                    "agent_id": self.agent_id,
                    "error": str(e),
                    "error_type": e.__class__.__name__
                }
            )
            raise
```

### 3.3 Agent Integration Points

1. **AgentController**
   - Track agent creation, registration, and task assignment
   - Monitor controller state transitions

2. **WorkerAgent**
   - Log task execution start/end
   - Track worker status and availability

3. **TaskAwareAgent**
   - Monitor task awareness decisions
   - Track provider selection based on task

4. **ToolAgent**
   - Track tool usage and results
   - Monitor tool chaining operations

### 3.4 Event Types

Standard event types for the agent system:

| Event Type            | Description                 | Data Fields                        |
| --------------------- | --------------------------- | ---------------------------------- |
| `agent.created`       | Agent created               | agent_id, agent_type, capabilities |
| `agent.task.start`    | Task execution started      | task_id, task_type, agent_id       |
| `agent.task.complete` | Task execution completed    | task_id, success, execution_time   |
| `agent.task.error`    | Task execution error        | task_id, error, error_type         |
| `agent.message.sent`  | Message sent between agents | from_agent, to_agent, message_type |
| `agent.state.change`  | Agent state changed         | agent_id, old_state, new_state     |
| `agent.tool.use`      | Tool usage by agent         | tool_name, inputs, agent_id        |
| `agent.tool.result`   | Tool result received        | tool_name, success, execution_time |

## 4. Knowledge System Integration

### 4.1 Event-Driven Knowledge System

The knowledge system can leverage events for:

- Tracking document ingestion
- Monitoring query performance
- Improving cache hit rates
- Diagnosing retrieval issues

### 4.2 Implementation Strategy

```python
# Step 1: Create an EventAwareKnowledgeBase class
class EventAwareKnowledgeBase:
    """Mixin class that adds event capabilities to knowledge base."""

    def __init__(self, event_system: EventSystem = None, **kwargs):
        """Initialize with an event system.

        Args:
            event_system: Event system to use for publishing events.
            **kwargs: Additional keyword arguments.
        """
        self.event_system = event_system or create_event_system()

        # Add middleware for detailed logging
        self.event_system.add_middleware(create_logging_middleware())

        # Add history middleware for debugging
        self.history_middleware = HistoryMiddleware(max_history=50)
        self.event_system.add_middleware(self.history_middleware)

        # Add timing middleware for performance tracking
        self.event_system.add_middleware(create_timing_middleware())

    def publish_kb_event(self, event_type: str, data: Dict[str, Any]):
        """Publish a knowledge base event.

        Args:
            event_type: Type of event to publish.
            data: Event data.
        """
        if self.event_system:
            collection_name = getattr(self, "collection_name", "unknown")
            self.event_system.publish(
                event_type=event_type,
                data=data,
                source=f"knowledge.{collection_name}"
            )
```

### 4.3 Knowledge System Integration Points

1. **Document Ingestion**
   - Track document processing steps
   - Monitor chunking operations
   - Measure embedding generation time

2. **Document Retrieval**
   - Track query execution
   - Monitor search latency
   - Record result counts and relevance scores

3. **Hybrid Search**
   - Monitor keyword vs. semantic search balance
   - Track search strategy selection

### 4.4 Event Types

Standard event types for the knowledge system:

| Event Type                           | Description                  | Data Fields                        |
| ------------------------------------ | ---------------------------- | ---------------------------------- |
| `knowledge.document.ingest.start`    | Document ingestion started   | document_id, mime_type, size       |
| `knowledge.document.ingest.complete` | Document ingestion completed | document_id, chunks, duration      |
| `knowledge.document.chunk`           | Document chunking            | document_id, chunk_count, strategy |
| `knowledge.embedding.generate`       | Embedding generation         | vector_count, dimensions, model    |
| `knowledge.query.start`              | Query started                | query_text, filters, strategy      |
| `knowledge.query.complete`           | Query completed              | results_count, duration, strategy  |
| `knowledge.query.semantic`           | Semantic search              | query_embedding, top_k, duration   |
| `knowledge.query.keyword`            | Keyword search               | query_terms, matches, duration     |

## 5. Integration Examples

### 5.1 Provider with Events Example

```python
# examples/30_provider_with_events.py
from atlas.core.services.events import EventSystem, create_event_system
from atlas.core.services.middleware import create_logging_middleware, HistoryMiddleware
from atlas.providers.base import Provider

# Create event system with middleware
event_system = create_event_system()
event_system.add_middleware(create_logging_middleware())
history = HistoryMiddleware(max_history=100)
event_system.add_middleware(history)

# Create provider with event system
provider = Provider.create(
    provider_name="anthropic",
    model_name="claude-3-sonnet-20240229",
    event_system=event_system
)

# Subscribe to events
event_system.subscribe(
    event_type="provider.*",
    callback=lambda event: print(f"Provider event: {event['event_type']}")
)

# Generate response
response = provider.generate({"messages": [{"role": "user", "content": "Hello"}]})

# Print event history
print("\nEvent History:")
for event in history.get_history():
    print(f"- {event['event_type']} ({event['metadata'].get('processing_time_ms', 0):.2f}ms)")

# Get provider stats from events
start_events = [e for e in history.get_history() if e["event_type"] == "provider.generate.start"]
end_events = [e for e in history.get_history() if e["event_type"] == "provider.generate.end"]
print(f"\nGeneration Count: {len(end_events)}")
print(f"Average Tokens: {sum(e['data'].get('token_count', 0) for e in end_events) / max(1, len(end_events)):.1f}")
print(f"Average Latency: {sum(e['data'].get('latency', 0) for e in end_events) / max(1, len(end_events)):.2f}s")
```

### 5.2 Agent with Events Example

```python
# examples/31_agent_with_events.py
from atlas.core.services.events import EventSystem, create_event_system
from atlas.core.services.middleware import create_timing_middleware, HistoryMiddleware
from atlas.agents.base import Agent

# Create event system with middleware
event_system = create_event_system()
event_system.add_middleware(create_timing_middleware())
history = HistoryMiddleware(max_history=100)
event_system.add_middleware(history)

# Create agent with event system
agent = Agent.create(
    agent_type="task_aware",
    event_system=event_system
)

# Subscribe to events
event_system.subscribe(
    event_type="agent.task.*",
    callback=lambda event: print(f"Agent task event: {event['event_type']}")
)

# Execute task
result = agent.execute_task({
    "task_id": "task_123",
    "task_type": "summarize",
    "content": "This is a test document that should be summarized."
})

# Print event history
print("\nEvent History:")
for event in history.get_history():
    print(f"- {event['event_type']} ({event['metadata'].get('processing_time_ms', 0):.2f}ms)")

# Calculate task metrics
task_events = [e for e in history.get_history() if e["event_type"].startswith("agent.task")]
start_events = [e for e in task_events if e["event_type"] == "agent.task.start"]
complete_events = [e for e in task_events if e["event_type"] == "agent.task.complete"]

print(f"\nTasks Started: {len(start_events)}")
print(f"Tasks Completed: {len(complete_events)}")
if complete_events:
    avg_time = sum(e['data'].get('execution_time', 0) for e in complete_events) / len(complete_events)
    print(f"Average Execution Time: {avg_time:.2f}s")
```

## 6. Strategy for Full Integration

### 6.1 Service Registry Implementation

To facilitate system-wide access to core services, we'll implement a service registry:

```python
# Service registry for centralized access
class ServiceRegistry:
    """Registry for core services."""

    _instance = None

    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = ServiceRegistry()
        return cls._instance

    def __init__(self):
        """Initialize the registry."""
        self._services = {}
        self._lock = threading.RLock()

    def register(self, service_type: str, service: Any):
        """Register a service.

        Args:
            service_type: Type of service.
            service: Service instance.
        """
        with self._lock:
            self._services[service_type] = service

    def get(self, service_type: str) -> Any:
        """Get a registered service.

        Args:
            service_type: Type of service.

        Returns:
            The registered service or None.
        """
        with self._lock:
            return self._services.get(service_type)

    def has(self, service_type: str) -> bool:
        """Check if a service is registered.

        Args:
            service_type: Type of service.

        Returns:
            True if the service is registered, False otherwise.
        """
        with self._lock:
            return service_type in self._services
```

### 6.2 Service Types

Standard service types for the registry:

| Service Type     | Description                         | Implementation    |
| ---------------- | ----------------------------------- | ----------------- |
| `event_system`   | Event system with publish-subscribe | `EventSystem`     |
| `buffer_system`  | Buffer system for data flow         | `MemoryBuffer`    |
| `command_system` | Command pattern execution           | `CommandExecutor` |
| `state_system`   | State management with versioning    | `StateContainer`  |

### 6.3 Integration Phasing

We'll integrate core services in phases:

1. **Phase 1 (May 20-21)**
   - Create service registry
   - Integrate event system with providers
   - Add basic events to key provider operations

2. **Phase 2 (May 21-22)**
   - Integrate event system with agents
   - Implement agent lifecycle events
   - Add task execution tracking

3. **Phase 3 (May 22-23)**
   - Integrate event system with knowledge base
   - Implement document processing events
   - Add query execution tracking

4. **Phase 4 (May 23-24)**
   - System-wide event coordination
   - Add buffer system to streaming operations
   - Implement command pattern for core operations

## 7. Performance Considerations

### 7.1 Event Filtering

Implement filter middleware to control event volume:

```python
# Example global filter for non-critical events
def global_event_filter(event):
    """Filter out high-volume non-critical events in production."""
    if os.environ.get("ATLAS_ENV") == "production":
        # Only allow critical events in production
        if event["event_type"] in [
            "provider.generate.error",
            "agent.task.error",
            "knowledge.query.error"
        ]:
            return True

        # Allow start/end events but not intermediate ones
        return not event["event_type"].endswith(".progress")
    return True

# Add filter to event system
event_system.add_middleware(create_filter_middleware(global_event_filter))
```

### 7.2 Middleware Optimization

Configure middleware for optimal performance:

```python
# Configure middleware based on environment
def configure_middleware(event_system, env="development"):
    """Configure middleware based on environment."""
    if env == "development":
        # Development: full logging and history
        event_system.add_middleware(create_logging_middleware(), priority=100)
        event_system.add_middleware(create_timing_middleware(), priority=90)
        event_system.add_middleware(HistoryMiddleware(max_history=1000), priority=80)
    elif env == "testing":
        # Testing: timing only
        event_system.add_middleware(create_timing_middleware(), priority=100)
        event_system.add_middleware(HistoryMiddleware(max_history=100), priority=90)
    elif env == "production":
        # Production: minimal overhead
        event_system.add_middleware(create_filter_middleware(global_event_filter), priority=100)
        event_system.add_middleware(create_timing_middleware(), priority=90)
```

## 8. Unit Testing Strategy

### 8.1 Test Coverage Requirements

- Each integration point must have dedicated tests
- Verify correct event publishing for key operations
- Test event subscription and callback behavior
- Validate middleware pipeline functionality
- Ensure thread safety under concurrent usage

### 8.2 Example Tests

```python
# Example test for provider with events
def test_provider_with_events():
    """Test provider integration with event system."""
    # Create event system with history middleware
    event_system = create_event_system()
    history = HistoryMiddleware()
    event_system.add_middleware(history)

    # Create mock provider with event system
    provider = MockProvider(
        model_name="mock-model",
        event_system=event_system
    )

    # Generate response
    provider.generate({"messages": [{"role": "user", "content": "Hello"}]})

    # Verify events were published
    events = history.get_history()
    event_types = [event["event_type"] for event in events]

    # Check essential events were published
    assert "provider.generate.start" in event_types
    assert "provider.generate.end" in event_types

    # Check event data
    end_event = next(e for e in events if e["event_type"] == "provider.generate.end")
    assert "token_count" in end_event["data"]
    assert "latency" in end_event["data"]
    assert end_event["source"].startswith("provider.")
```

## 9. Next Steps

### 9.1 Immediate Actions

1. **Create Integration Branches**
   - `feature/provider-events`: Provider system integration
   - `feature/agent-events`: Agent system integration
   - `feature/knowledge-events`: Knowledge system integration

2. **Implement Core Testing**
   - Create test fixtures for event-integrated components
   - Develop standard test patterns for event verification

3. **Update Documentation**
   - Add integration documentation to component READMEs
   - Create examples demonstrating event-driven architecture

### 9.2 Completion Criteria

Before considering the integration complete, ensure:

1. All core operations emit appropriate events
2. Event history works for debugging purposes
3. Performance impact is minimal in production
4. Documentation clearly explains event types and usage
5. Examples demonstrate the value of event-based patterns

## 10. Conclusion

The integration of core services into the existing Atlas systems represents a significant enhancement to our architecture. It will enable more robust telemetry, improved debugging, and better state management throughout the system. This plan establishes a clear path forward for this integration while maintaining our focus on performance, clean architecture, and reliable testing.

::: tip Next Steps
Once this integration is complete, we'll focus on leveraging these capabilities for the Textual CLI implementation.
:::
