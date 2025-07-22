---
title: Feature-Driven Architecture Plan
---

# Feature-Driven Architecture Plan

::: danger CLEAN BREAK WITH VERTICAL FEATURE SLICES
This document outlines our comprehensive strategy for implementing Atlas's clean break architecture through vertical feature slices. By focusing on delivering complete functional features rather than building horizontal layers, we can demonstrate value earlier while maintaining architectural integrity. Each feature slice implements only the necessary components from each layer, from type variables and protocols to services and user interfaces.
:::

::: tip Current Status (May 20, 2025)
- ✅ Defined the clean break architecture and NERV component strategy
- ✅ Established centralized type variable system with variance control
- ✅ Implemented runtime-checkable protocols for service interfaces
- ✅ Created domain-specific primitive definitions for service areas
- 🚧 Shifting implementation strategy to vertical feature slices
- 🚧 Implementing core components for Streaming Chat feature
- 🚧 Building event system and buffer components for streaming support
:::

## 1. Architectural Vision

Our architecture combines strong typing, protocol-first design, and reactive event-driven patterns while delivering value through vertical feature slices.

### 1.1 Core Design Principles

1. **Emergence Over Prescription**: Architecture emerges from interaction patterns
2. **Protocol-First Design**: All interfaces are defined as protocols with clear contracts
3. **Type-Safe Foundations**: Strong typing throughout with centralized type variable system
4. **Reactive Event Mesh**: Components communicate through reactive event subscription
5. **Temporal State Awareness**: State history is maintained through versioned containers
6. **Perspective Shifting**: Different views of the same data for different contexts
7. **Explicit Effect Tracking**: Side effects are explicitly captured and managed
8. **Adaptive Component Composition**: Services discover what they need rather than explicit wiring

### 1.2 Feature Slice Architecture

Rather than building complete horizontal layers, we implement vertical slices that deliver complete functional features:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        FEATURE SLICE ARCHITECTURE                         │
└───────────────────────────────────────────────────────────────────────────┘

┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│          │ │          │ │          │ │          │ │          │ │          │
│ Streaming│ │  Agent   │ │Knowledge │ │  Multi-  │ │ Workflow │ │ Command  │
│   Chat   │ │Delegation│ │Retrieval │ │ Provider │ │Execution │ │   CLI    │
│          │ │          │ │          │ │ Routing  │ │          │ │          │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
    ↑│↓          ↑│↓          ↑│↓          ↑│↓          ↑│↓          ↑│↓
┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐
│Components│ │Components│ │Components│ │Components│ │Components│ │Components│
│          │ │          │ │          │ │          │ │          │ │          │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
    ↑│↓          ↑│↓          ↑│↓          ↑│↓          ↑│↓          ↑│↓
┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐
│ Services │ │ Services │ │ Services │ │ Services │ │ Services │ │ Services │
│          │ │          │ │          │ │          │ │          │ │          │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
    ↑│↓          ↑│↓          ↑│↓          ↑│↓          ↑│↓          ↑│↓
┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐
│   NERV   │ │   NERV   │ │   NERV   │ │   NERV   │ │   NERV   │ │   NERV   │
│Components│ │Components│ │Components│ │Components│ │Components│ │Components│
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
    ↑│↓          ↑│↓          ↑│↓          ↑│↓          ↑│↓          ↑│↓
┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐
│  Inner   │ │  Inner   │ │  Inner   │ │  Inner   │ │  Inner   │ │  Inner   │
│ Universe │ │ Universe │ │ Universe │ │ Universe │ │ Universe │ │ Universe │
└──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘
```

Each feature slice:
1. Implements only the necessary components from each layer
2. Delivers complete end-to-end functionality for immediate testing
3. Follows clean break architecture principles within its scope
4. Enables incremental architecture adoption and validation

## 2. Feature Prioritization

### 2.1 Feature Priority Legend
- 🔴 **Primary Features** - Core functionality that must be delivered first
- 🟠 **Secondary Features** - Important functionality built on primary features
- 🟢 **Tertiary Features** - Additional functionality that enhances the system
- 🔵 **Future Features** - Planned for future releases

### 2.2 Key Feature Slices

1. **Streaming Chat** 🔴
   - Real-time streaming conversation with LLM providers
   - Includes provider integration, streaming buffer, response tracking
   - Demonstrates event-driven architecture and buffer system

2. **Agent Delegation** 🔴
   - Task delegation between multiple specialized agents
   - Includes agent messaging, state tracking, task coordination
   - Demonstrates event-driven communication and state management

3. **Knowledge Retrieval** 🔴
   - Document chunking, embedding, and semantic search
   - Includes vector storage, hybrid search, context integration
   - Demonstrates persistence layer and state projection

4. **Multi-Provider Routing** 🟠
   - Intelligent routing between different LLM providers
   - Includes capability matching, fallback strategies, cost optimization
   - Demonstrates registry pattern and effect tracking

5. **Workflow Execution** 🟠
   - Complex multi-step workflow orchestration
   - Includes parallel execution, dependency management, error handling
   - Demonstrates quantum partitioning and reactive event mesh

6. **Command CLI** 🟠
   - Textual-based rich terminal interface
   - Includes command parsing, execution, response formatting
   - Demonstrates command pattern and perspective shifting

## 3. Layered Architecture Components

Each feature implements components from these architectural layers:

### 3.1 Type Variables Layer

The type variables system provides a consistent foundation for type safety:

- **Centralized Definitions**: Single source of truth in `type_vars.py`
- **Variance Control**: Explicit covariant (`_co`) and contravariant (`_contra`) types
- **Domain-Specific Types**: Specialized types for different subsystems
- **Feature-Specific Types**: Types dedicated to specific feature requirements

Type variable categories include:
- General Purpose: `T`, `K`, `V`, `R`
- Service-Specific: `DataT`, `StateT`, `EventT`
- Variance-Specific: `T_co`, `DataT_co`, `T_contra`
- Container-Specific: `KeyT`, `ValueT`, `ItemT`
- Functional: `CallableT`, `InputT`, `OutputT`
- Feature-Specific: `ProviderT`, `AgentT`, `DocumentT`

### 3.2 Protocols Layer

The protocol system defines interfaces that services must implement:

- **Runtime Checkable**: All protocols are decorated with `@runtime_checkable`
- **Duck Typing**: Structural subtyping for flexibility
- **Type Guards**: Associated type guard functions
- **Protocol Hierarchy**: Logical inheritance relationships

### 3.3 Primitives Layer

The primitives system provides core interfaces and error types:

| Domain | Purpose | Key Primitives |
|--------|---------|---------------|
| buffer | Data flow control | BufferProtocol, FlowControlProtocol |
| commands | Command pattern | CommandProtocol, CommandProcessorProtocol |
| events | Event communication | EventBusProtocol, EventSubscriberProtocol |
| state | State containers | StateProtocol, VersionedStateProtocol |
| registry | Service registration | RegistryProtocol, DiscoveryProtocol |
| resources | Resource management | ResourceProtocol, LifecycleManagerProtocol |

### 3.4 Schema Layer

The schema system provides validation and serialization for data structures:

- **Type Verification**: Validate data against type definitions
- **Runtime Validation**: Check data structure at runtime
- **Serialization**: Convert between different data formats
- **Documentation**: Generate schema documentation

### 3.5 NERV Components

Core NERV components provide the foundation for services:

1. **EventBus**: Reactive Event Mesh implementation for decoupled communication
2. **TemporalStore**: Historical state tracking with version history
3. **PerspectiveAware**: Context-specific views of data
4. **StateProjector**: Efficient state evolution with immutability
5. **EffectMonad**: Explicit side-effect tracking
6. **QuantumPartitioner**: Parallel execution with dependencies
7. **Container**: Dependency management system
8. **AspectWeaver**: Cross-cutting concerns management
9. **DiffSynchronizer**: Data reconciliation between systems

### 3.6 Inner Universe Integration

The persistence layer provides durable storage and synchronization:

1. **Controller**: Central coordination for SpacetimeDB interaction
2. **Adapters**: Connect NERV components to SpacetimeDB
3. **Type Mapping**: Consistent mapping between Python and Rust types

## 4. Feature-Specific Implementation

### 4.1 Streaming Chat Feature

#### Type System Components
- **Type Variables**: Event, Stream, Token, Provider
- **Protocols**: EventBus, Buffer, StreamControl
- **Primitives**: events, buffer, state
- **Schemas**: StreamResponse, ProviderMessage

#### Implementation Components
1. **EventBus Component**: Real-time event communication
   - Event publication/subscription
   - Event filtering and routing
   - Thread-safe operation
   - Event context tracking

2. **Buffer Service**: Streaming token management
   - Thread-safe token queue
   - Backpressure control
   - Flow rate management
   - Token accumulation

3. **State Container**: Response tracking
   - Current stream state
   - Token history
   - Metadata tracking
   - Event triggers

4. **Provider Services**: LLM integration
   - Provider-specific adapters
   - Streaming support
   - Error handling
   - Retry policies

#### Implementation Roadmap
- **May 20-21**: Event & Buffer System
- **May 21-22**: Streaming Provider
- **May 22-23**: Provider Implementations & Example

### 4.2 Agent Delegation Feature

#### Type System Components
- **Type Variables**: Agent, Task, Message
- **Protocols**: StateContainer, Command, Messenger
- **Primitives**: commands, state, transitions
- **Schemas**: AgentTask, AgentMessage

#### Implementation Components
1. **TemporalStore Component**: Agent state tracking
   - State versioning
   - History tracking
   - State transition management
   - State serialization

2. **Command System**: Task execution
   - Command pattern implementation
   - Task execution tracking
   - Error handling
   - Result management

3. **Message Routing**: Agent communication
   - Structured message format
   - Message routing system
   - Delivery verification
   - Message context

#### Implementation Roadmap
- **May 23-24**: Agent State & Messaging
- **May 24-25**: Controller & Delegation
- **May 25-26**: Specialized Agents & Example

### 4.3 Knowledge Retrieval Feature

#### Type System Components
- **Type Variables**: Document, Embedding, Query
- **Protocols**: Resource, Persistence, Vector
- **Primitives**: resources, buffer, registry
- **Schemas**: Document, EmbeddingVector, QueryResult

#### Implementation Components
1. **PerspectiveAware Component**: Context-specific views
   - Schema-based transformations
   - Context-aware projections
   - View validation
   - Data filtering

2. **Resource Management**: Vector store handling
   - Resource lifecycle
   - Connection pooling
   - Resource monitoring
   - Error recovery

3. **Persistence Integration**: Document storage
   - ChromaDB integration
   - Vector storage
   - Metadata management
   - Query optimization

#### Implementation Roadmap
- **May 26-27**: Document Processing
- **May 27-28**: Vector Store & Retrieval
- **May 28-29**: Hybrid Search & Example

## 5. Component Reuse and Dependencies

### 5.1 Feature Slice Dependencies

Each feature builds upon components from previous features:

1. **Streaming Chat**:
   - **Required New**: EventBus, Buffer System, State Container
   - **Required External**: LLM Providers

2. **Agent Delegation**:
   - **Reused**: EventBus (from Streaming Chat)
   - **Required New**: TemporalStore, Command System
   - **Extended**: State Container (from Streaming Chat)

3. **Knowledge Retrieval**:
   - **Reused**: Buffer System (from Streaming Chat)
   - **Required New**: PerspectiveAware, Inner Universe Integration
   - **Extended**: Resource Management

### 5.2 Natural Integration Zones

The architecture recognizes areas where different patterns naturally blend:

#### State-Event Continuum
- Events trigger state transitions in TemporalStore
- State transitions publish events through EventBus
- State history aligns with event history
- Versioned state and event sequences provide natural correlation

#### Execution-Dependency Fabric
- Command execution depends on service availability
- Service discovery influences command capabilities
- Effect tracking captures service interactions
- Command lifecycles align with resource lifecycles

#### Perspective-Synchronization Mesh
- Data projections influence synchronization strategies
- Schema definitions serve validation and mapping purposes
- Context-specific views inform synchronization priorities
- Transformation and reconciliation form natural feedback loops

## 6. Testing Strategy

### 6.1 Test Organization

Tests are organized to mirror the project structure, with an emphasis on feature slices:

```
tests/
├── test_types.py            # Test type variable definitions
├── test_protocols.py        # Test protocol interfaces
├── features/                # Feature-specific tests
│   ├── streaming_chat/      # Streaming Chat tests
│   ├── agent_delegation/    # Agent Delegation tests
│   └── knowledge_retrieval/ # Knowledge Retrieval tests
├── primitives/              # Test all primitive interfaces
├── services/                # Test service implementations
└── integration/             # Test cross-component integration
```

### 6.2 Testing Approach

1. **Feature-Specific Testing**
   - Test entire feature slice functionality
   - Verify feature-specific components work together
   - Ensure end-to-end workflow operates correctly

2. **Type and Protocol Testing**
   - Verify type variable usage and variance correctness
   - Test protocol implementations with mock classes
   - Ensure type guards correctly identify implementations

3. **Service Testing**
   - Test compliance with primitive interfaces
   - Verify thread safety with concurrent operations
   - Test error handling and recovery mechanisms
   - Verify service integration through registries

4. **Integration Testing**
   - Test cross-service interactions
   - Verify event propagation between components
   - Test end-to-end workflows through multiple services
   - Measure performance under varying loads

## 7. Implementation Timeline

The implementation follows a phased approach, with each phase delivering complete feature slices:

::: timeline Phase 1: Streaming Chat & Agent Delegation
- **May 20-26, 2025** 🚧
- Implement streaming chat feature slice
- Build agent delegation feature slice
- Create examples demonstrating both features
- Implement core services: event, buffer, state
- Core NERV components: EventBus, StateProjector
:::

::: timeline Phase 2: Knowledge Retrieval & Provider Routing
- **May 26 - June 1, 2025** 🔄
- Implement knowledge retrieval feature slice
- Build multi-provider routing feature slice
- Create examples demonstrating both features
- Implement core services: registry, resources
- Core NERV components: TemporalStore, Container
:::

::: timeline Phase 3: Workflow & CLI
- **June 1-7, 2025** 🔲
- Implement workflow execution feature slice
- Build command CLI feature slice
- Create examples demonstrating both features
- Implement core services: commands, perspective
- Core NERV components: QuantumPartitioner, PerspectiveAware
:::

::: timeline Phase 4: Integration & Polish
- **June 7-14, 2025** 🔲
- Implement system-level integration
- Complete documentation
- Add comprehensive examples
- Final polish and cleanup
- Full performance optimization
:::

## 8. Advantages of Feature-Driven Approach

This feature-driven architecture approach offers several key advantages:

1. **Functional Value Earlier**: Complete features delivered incrementally
2. **Reduced Implementation Risk**: Architecture validated through actual usage
3. **Better Resource Allocation**: Focus on components needed for current features
4. **Clear Progress Metrics**: Feature completion provides tangible milestones
5. **Architectural Integrity**: Maintains clean break principles with practical delivery
6. **Faster Feedback Cycles**: Earlier user testing and validation
7. **Natural Evolution**: Architecture emerges from real usage patterns
8. **Flexible Prioritization**: Easily adapt focus as requirements evolve

## 9. Conclusion

The feature-driven architecture approach enables us to deliver immediate functional value while building toward our clean break architecture vision. By focusing on vertical feature slices, we can validate architectural patterns through practical implementation, evolve components based on real-world usage, and maintain a clear path to completion.

This approach combines the benefits of architectural integrity with pragmatic development, ensuring a robust foundation while delivering tangible results throughout the implementation timeline.

::: tip Next Steps
Our immediate focus is completing the Streaming Chat feature slice, starting with the EventBus, Buffer Service, and State Container. This will establish the foundation for real-time data flow while validating our core architectural patterns.
:::