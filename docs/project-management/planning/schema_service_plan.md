---
title: Schema & Type System Architecture Plan
---

# Schema & Type System Architecture Plan

::: danger CLEAN BREAK ARCHITECTURE WITH VERTICAL FEATURES
This document outlines our comprehensive plan for implementing the clean break architecture approach with a focus on type variables, protocols, primitives, and schemas. This architecture prioritizes type safety, runtime verification, clear interfaces, and extensibility while delivering value through vertical feature slices.
:::

::: tip Current Status (May 20, 2025)
- ✅ Established centralized type variable system with variance control in `type_vars.py`
- ✅ Implemented runtime-checkable protocols for interfaces in `protocols.py`
- ✅ Created domain-specific primitive definitions in `primitives/*/types.py`
- ✅ Implemented domain-specific error hierarchies in `primitives/*/errors.py`
- ✅ Developed comprehensive test suite validating all primitive interfaces
- ✅ Resolved circular dependency issues between modules
- 🚧 Building schema validation system with type verification
- 🚧 Implementing feature-specific service components
:::

## 1. Feature-Driven Type System Architecture

### 1.1 Core Architecture Overview

The Atlas architecture follows a layered approach, with each layer building on the previous, while organizing implementation around vertical feature slices:

1. **Type Variables Layer**: Centralized type definitions with variance control
2. **Protocols Layer**: Runtime-checkable interface definitions
3. **Primitives Layer**: Domain-specific interfaces and errors
4. **Schema Layer**: Data structure validation and serialization
5. **Service Layer**: Implementations of primitive interfaces
6. **Component Layer**: Domain-specific components using core services

This layered architecture provides several benefits:
- **Type Safety**: Strong typing throughout with generic parameters
- **Runtime Verification**: Interface compliance checked at runtime
- **Clear Boundaries**: Well-defined interfaces between components
- **Testability**: Each layer can be tested in isolation
- **Extensibility**: New implementations can be added without changing interfaces
- **Incremental Delivery**: Vertical features with minimum necessary components

### 1.2 Vertical Feature Slices

Each vertical feature slice will implement the necessary components from each layer:

1. **Streaming Chat**:
   - Required Type Variables: Event, Stream, Token, Provider
   - Required Protocols: EventBus, Buffer, StreamControl
   - Required Primitives: events, buffer, state
   - Required Schemas: StreamResponse, ProviderMessage
   - Required Services: EventService, BufferService, StateService

2. **Agent Delegation**:
   - Required Type Variables: Agent, Task, Message
   - Required Protocols: StateContainer, Command, Messenger
   - Required Primitives: commands, state, transitions
   - Required Schemas: AgentTask, AgentMessage
   - Required Services: CommandService, StateService, RegistryService

3. **Knowledge Retrieval**:
   - Required Type Variables: Document, Embedding, Query
   - Required Protocols: Resource, Persistence, Vector
   - Required Primitives: resources, buffer, registry
   - Required Schemas: Document, EmbeddingVector, QueryResult
   - Required Services: ResourceService, PersistenceService, BufferService

## 2. Type System Architecture

### 2.1 Type Variables System

The type variables system provides a consistent foundation for type safety throughout the codebase:

- **Centralized Definitions**: Single source of truth in `type_vars.py`
- **Variance Control**: Explicit covariant (`_co`) and contravariant (`_contra`) types
- **Domain-Specific Types**: Specialized types for different subsystems
- **Circular Import Prevention**: Strategic module organization

### 2.2 Type Variables Organization

Our type variables are organized into logical categories:

| Category | Examples | Purpose |
|----------|----------|---------|
| General Purpose | `T`, `K`, `V`, `R` | Generic type parameters for polymorphic functions |
| Service-Specific | `DataT`, `StateT`, `EventT` | Specialized type parameters for services |
| Variance-Specific | `T_co`, `DataT_co`, `T_contra` | Type parameters with explicit variance |
| Container-Specific | `KeyT`, `ValueT`, `ItemT` | Type parameters for container types |
| Functional | `CallableT`, `InputT`, `OutputT` | Type parameters for functional operations |
| Feature-Specific | `ProviderT`, `AgentT`, `DocumentT` | Type parameters for domain components |

### 2.3 Protocol System

The protocol system defines interfaces that services and components must implement:

- **Runtime Checkable**: All protocols are decorated with `@runtime_checkable`
- **Duck Typing**: Protocols enable structural subtyping for flexibility
- **Type Guards**: Each protocol has associated type guard functions
- **Protocol Hierarchy**: Protocols form a logical inheritance hierarchy

### 2.4 Protocol Implementation for Features

Each feature requires specific protocols:

**Streaming Chat Protocols**:
- `EventBusProtocol`: Event subscription and publication
- `BufferProtocol`: Thread-safe buffer for streaming data
- `StreamControlProtocol`: Control streaming flow
- `ProviderProtocol`: Interface for LLM providers

**Agent Delegation Protocols**:
- `CommandProcessorProtocol`: Command execution and tracking
- `StateContainerProtocol`: Versioned state management
- `MessageRouterProtocol`: Message routing between agents
- `AgentRegistryProtocol`: Agent discovery and management

**Knowledge Retrieval Protocols**:
- `ResourceManagerProtocol`: External resource management
- `PersistenceProtocol`: Data persistence and retrieval
- `VectorStoreProtocol`: Vector storage and similarity search
- `EmbeddingProtocol`: Text to vector conversion

## 3. Primitives System Architecture

### 3.1 Purpose and Design

The primitives system defines core interfaces and types for all service components:

- **Domain-Specific Primitives**: Each service area has dedicated primitive definitions
- **Protocol-Based Definitions**: All interfaces defined as protocols first
- **Error Hierarchies**: Each domain has specific error class hierarchy
- **Type Safety**: Generic parameters ensure type consistency throughout

### 3.2 Primitive Domains

We've implemented primitive definitions for these core service areas:

| Domain | Purpose | Key Primitives |
|--------|---------|---------------|
| buffer | Data flow control | BufferProtocol, FlowControlProtocol |
| commands | Command pattern | CommandProtocol, CommandProcessorProtocol |
| component | Base components | ComponentProtocol, LifecycleProtocol |
| events | Event communication | EventBusProtocol, EventSubscriberProtocol |
| middleware | Pipeline processing | MiddlewareProtocol, PipelineProtocol |
| registry | Service registration | RegistryProtocol, DiscoveryProtocol |
| resources | Resource management | ResourceProtocol, LifecycleManagerProtocol |
| state | State containers | StateProtocol, VersionedStateProtocol |
| transitions | State transitions | TransitionProtocol, StateMachineProtocol |
| validation | Data validation | ValidatorProtocol, SchemaProtocol |

### 3.3 Feature-Specific Primitive Selection

Each feature will use only the necessary primitives:

**Streaming Chat**:
- `events`: For event-driven communication
- `buffer`: For token streaming
- `state`: For response tracking
- Relevant errors: BufferOverflowError, EventSubscriptionError

**Agent Delegation**:
- `events`: For communication between agents
- `commands`: For task execution
- `state`: For agent state tracking
- `transitions`: For state machine management
- Relevant errors: CommandExecutionError, StateMachineError

**Knowledge Retrieval**:
- `resources`: For vector store management
- `buffer`: For document chunking
- `registry`: For persistent store discovery
- Relevant errors: ResourceNotFoundError, VectorStoreError

## 4. Schema System Architecture

### 4.1 Purpose and Design

The schema system provides validation and serialization for data structures:

- **Type Verification**: Validate data against type definitions
- **Runtime Validation**: Check data structure at runtime
- **Serialization**: Convert between different data formats
- **Documentation**: Generate schema documentation

### 4.2 Schema Components

The schema system has these main components:

- **BaseSchema**: Foundation for all schema types
- **ServiceSchema**: For service configuration
- **EventSchema**: For event data
- **CommandSchema**: For command data
- **StateSchema**: For state data
- **ResourceSchema**: For resource data

### 4.3 Feature-Specific Schemas

**Streaming Chat Schemas**:
- `ProviderRequestSchema`: For provider requests
- `StreamResponseSchema`: For streaming responses
- `TokenSchema`: For individual tokens
- `StreamStateSchema`: For stream state tracking

**Agent Delegation Schemas**:
- `AgentTaskSchema`: For agent tasks
- `AgentMessageSchema`: For agent communication
- `TaskStateSchema`: For task state tracking
- `AgentCapabilitySchema`: For agent capabilities

**Knowledge Retrieval Schemas**:
- `DocumentSchema`: For document metadata
- `ChunkSchema`: For document chunks
- `EmbeddingSchema`: For vector embeddings
- `QueryResultSchema`: For search results

## 5. Service Implementation Plan

### 5.1 Core Service Architecture

Each service implements its corresponding primitive interface and follows a consistent pattern:

- **Thread-Safety**: All services use appropriate concurrency controls
- **Error Handling**: Comprehensive error handling and propagation
- **Event Publication**: Services publish events for monitoring
- **Factory Functions**: Standard factory functions for initialization

### 5.2 Feature-Driven Service Implementation

#### 5.2.1 Streaming Chat Services

Essential services for the Streaming Chat feature:

- **EventService**: Implement the EventBus primitive for event flow
- **BufferService**: Implement the Buffer primitive for streaming
- **StateService**: Implement the State primitive for tracking
- **ProviderService**: Implement provider integration

Implementation approach:
1. Start with minimal event system for basic publication/subscription
2. Add thread-safe buffer implementation with flow control
3. Implement simple state tracking for streaming responses
4. Connect to provider APIs with streaming support

#### 5.2.2 Agent Delegation Services

Essential services for the Agent Delegation feature:

- **CommandService**: Implement the Command primitive for tasks
- **StateService**: Extend the State primitive for agent state
- **RegistryService**: Implement the Registry primitive for agents
- **MessagingService**: Implement agent communication

Implementation approach:
1. Leverage existing event system for messaging
2. Add command pattern implementation for tasks
3. Extend state service with agent-specific tracking
4. Create registry for agent discovery and selection

#### 5.2.3 Knowledge Retrieval Services

Essential services for the Knowledge Retrieval feature:

- **ResourceService**: Implement the Resource primitive for vector stores
- **PersistenceService**: Implement persistence for documents
- **ChunkingService**: Implement document processing
- **EmbeddingService**: Implement vector embedding

Implementation approach:
1. Create resource management for vector stores
2. Implement document chunking and processing
3. Add vector embedding capabilities
4. Connect to persistence layer for storage

## 6. Implementation Roadmap

::: timeline Foundations: Type System & Protocols
- **May 19-21, 2025** ✅
- Implement centralized type variable system
- Create runtime-checkable protocols
- Implement primitive interfaces and errors
- Build test suite for type system validation
:::

::: timeline Streaming Chat Implementation
- **May 21-23, 2025** 🚧
- Implement EventBus for event communication
- Create Buffer service for streaming
- Add State service for response tracking
- Build Provider service with LLM integration
- Develop end-to-end streaming chat example
:::

::: timeline Agent Delegation Implementation
- **May 23-26, 2025** 🔄
- Implement Command service for tasks
- Extend State service for agent state
- Create Registry service for agent discovery
- Add Messaging service for communication
- Develop agent delegation example
:::

::: timeline Knowledge Retrieval Implementation
- **May 26-29, 2025** 🔄
- Implement Resource service for vector stores
- Create Persistence service for documents
- Add Chunking service for processing
- Build Embedding service for vectors
- Develop knowledge retrieval example
:::

::: timeline Integration and Refinement
- **May 29-31, 2025** 🔄
- Cross-feature integration testing
- Performance optimization for key services
- Documentation and examples
- Schema evolution support
:::

## 7. Testing Strategy

### 7.1 Test Organization

Tests are organized to mirror the project structure, ensuring comprehensive coverage:

```
tests/
├── test_types.py           # Test type variable definitions
├── test_protocols.py       # Test protocol interfaces
├── features/               # Feature-specific tests
│   ├── streaming_chat/     # Streaming Chat tests
│   ├── agent_delegation/   # Agent Delegation tests
│   └── knowledge_retrieval/# Knowledge Retrieval tests
├── primitives/             # Test all primitive interfaces
├── schemas/                # Test schema validation
├── services/               # Test service implementations
└── integration/            # Test cross-component integration
```

### 7.2 Testing Approach

1. **Type and Protocol Testing**
   - Test type variable declarations and usage
   - Verify protocol implementations with mock classes
   - Ensure type guards correctly identify implementations

2. **Feature-Specific Testing**
   - Test entire feature slice functionality
   - Verify feature-specific components work together
   - Ensure end-to-end workflow operates correctly

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

## 8. Conclusion

The schema and type system architecture provides a solid foundation for our feature-driven implementation approach. By focusing on vertical feature slices while maintaining architectural integrity, we ensure:

- **Faster Value Delivery**: Complete features delivered earlier
- **Lower Implementation Risk**: Architecture validated through actual usage
- **Better Resource Allocation**: Focus on components needed for current features
- **Architectural Consistency**: Clean, well-defined interfaces between components
- **Type Safety**: Strong typing throughout the system
- **Extensibility**: New features can be added without changing core interfaces

::: tip Next Steps
Focus on implementing the Streaming Chat feature slice first, starting with the EventBus, Buffer Service, and State Service to provide immediate functional value while establishing the foundation for future features.
:::