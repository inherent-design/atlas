---

title: Events

---


# Event Bus Architecture and Event Flow

## Event Bus Architecture

The event bus is the central nervous system connecting all components. This visualization shows how different modules connect through the event bus.

```mermaid
graph
    subgraph "Atlas Core"
        EB[Event Bus]

        subgraph "Providers"
            P1[Provider Registry]
            P2[Provider Group]
            P3[Provider Implementations]
        end

        subgraph "Agents"
            A1[Agent Controller]
            A2[Agent Workers]
            A3[Agent Registry]
        end

        subgraph "Knowledge"
            K1[Document Store]
            K2[Retrieval System]
            K3[Embeddings]
        end

        subgraph "Tools"
            T1[Tool Registry]
            T2[Tool Implementations]
        end

        subgraph "Orchestration"
            O1[Workflow Engine]
            O2[Scheduler]
        end

        subgraph "Core Services"
            CS1[State Management]
            CS2[Command Processor]
            CS3[Telemetry]
        end
    end

    %% Connections to Event Bus
    P1 --- EB
    P2 --- EB
    P3 --- EB
    A1 --- EB
    A2 --- EB
    A3 --- EB
    K1 --- EB
    K2 --- EB
    K3 --- EB
    T1 --- EB
    T2 --- EB
    O1 --- EB
    O2 --- EB
    CS1 --- EB
    CS2 --- EB
    CS3 --- EB
```

## Event Flow Visualization

This diagram shows how events flow through the system during a typical operation.

```mermaid
sequenceDiagram
    participant User
    participant Agent as Agent Controller
    participant Provider as Provider Group
    participant Knowledge as Knowledge System
    participant EventBus as Event Bus

    User->>Agent: Submit Query
    Agent->>EventBus: Publish QueryReceived
    EventBus->>Knowledge: Notify QueryReceived
    Knowledge->>EventBus: Publish RetrievalResults
    EventBus->>Agent: Notify RetrievalResults
    Agent->>EventBus: Publish ProviderRequest
    EventBus->>Provider: Notify ProviderRequest
    Provider->>EventBus: Publish StreamStarted
    EventBus->>Agent: Notify StreamStarted

    loop Streaming
        Provider->>EventBus: Publish StreamChunk
        EventBus->>Agent: Notify StreamChunk
        EventBus->>User: Stream Partial Result
    end

    Provider->>EventBus: Publish StreamCompleted
    EventBus->>Agent: Notify StreamCompleted
    Agent->>EventBus: Publish ResponseComplete
    EventBus->>User: Deliver Complete Response
```

## Component Interaction Sequence

### Network Boundary Interaction Example

```
┌────────┐          ┌───────────────┐       ┌───────────────┐       ┌─────────────┐
│ Client │          │ NetworkBoundr.│       │ BusinessLogic │       │ Repository  │
└───┬────┘          └───────┬───────┘       └───────┬───────┘       └──────┬──────┘
    │                        │                      │                      │
    │  RawApiRequest         │                      │                      │
    │─────────────────────────>                     │                      │
    │                        │                      │                      │
    │                        │  Validate            │                      │
    │                        │──────┐               │                      │
    │                        │      │               │                      │
    │                        │<─────┘               │                      │
    │                        │                      │                      │
    │                        │  ValidatedRequest    │                      │
    │                        │─────────────────────>│                      │
    │                        │                      │                      │
    │                        │                      │  DatabaseQuery       │
    │                        │                      │─────────────────────>│
    │                        │                      │                      │
    │                        │                      │  QueryResult         │
    │                        │                      │<─────────────────────│
    │                        │                      │                      │
    │                        │  DomainObject        │                      │
    │                        │<─────────────────────│                      │
    │                        │                      │                      │
    │                        │  Transform           │                      │
    │                        │──────┐               │                      │
    │                        │      │               │                      │
    │                        │<─────┘               │                      │
    │                        │                      │                      │
    │  ApiResponse           │                      │                      │
    │<─────────────────────────                     │                      │
    │                        │                      │                      │
```

## Event Types

The system defines various event types to classify different kinds of events. These event types help with event routing, filtering, and handling:

```python
class EventType(Enum):
    """Core event types in the system."""
    # System lifecycle events
    SYSTEM_INIT = auto()
    SYSTEM_SHUTDOWN = auto()

    # Provider events
    PROVIDER_CREATED = auto()
    PROVIDER_CONNECTED = auto()
    PROVIDER_DISCONNECTED = auto()
    PROVIDER_ERROR = auto()

    # Agent events
    AGENT_CREATED = auto()
    AGENT_STARTED = auto()
    AGENT_STOPPED = auto()
    AGENT_ERROR = auto()

    # Stream events
    STREAM_STARTED = auto()
    STREAM_CHUNK = auto()
    STREAM_PAUSED = auto()
    STREAM_RESUMED = auto()
    STREAM_COMPLETED = auto()
    STREAM_ERROR = auto()

    # Workflow events
    WORKFLOW_STARTED = auto()
    WORKFLOW_NODE_ENTERED = auto()
    WORKFLOW_NODE_EXITED = auto()
    WORKFLOW_COMPLETED = auto()
    WORKFLOW_ERROR = auto()

    # Knowledge events
    DOCUMENT_ADDED = auto()
    DOCUMENT_PROCESSED = auto()
    RETRIEVAL_STARTED = auto()
    RETRIEVAL_COMPLETED = auto()

    # Command events
    COMMAND_EXECUTED = auto()
    COMMAND_REVERTED = auto()
    COMMAND_FAILED = auto()
```
