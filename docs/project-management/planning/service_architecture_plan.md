---
title: Service Architecture Plan
---

# Service Architecture Plan

::: info CORE ARCHITECTURE DESIGN WITH FEATURE-FIRST APPROACH
This document outlines the service-oriented architecture design for Atlas v2, implementing principles from the [Clean Break Architecture Manifesto](./clean_break_manifest.md) and integrating the NERV (Neural Event-Reactive Virtualization) architecture with Inner Universe persistence. It focuses on architectural clarity, service separation, protocol-first design, and reactive event-driven patterns while prioritizing feature-driven vertical slices.
:::

::: tip Current Status (May 20, 2025)
- **Current Approach**: Vertical feature slices with focused architectural components
- **Current Progress**: NERV primitives and component patterns established
- **Current Focus**: Implementing core NERV components for Streaming Chat feature
- **Target Completion**: Iterative delivery of features with accompanying architecture components
:::

## 1. Feature-Driven Architecture Overview

### 1.1 Core Design Principles

The service architecture maintains these core NERV principles while adopting a vertical slice approach:

1. **Emergence Over Prescription**: Architecture emerges from interaction patterns
2. **Protocol-First Design**: All interfaces are defined first as protocols with clear contracts
3. **Type-Safe Foundations**: Strong typing throughout with centralized type variable system
4. **Reactive Event Mesh**: Components communicate through reactive event subscription
5. **Temporal State Awareness**: State history is maintained through versioned containers
6. **Perspective Shifting**: Different views of the same data for different contexts
7. **Explicit Effect Tracking**: Side effects are explicitly captured and managed
8. **Adaptive Component Composition**: Services discover what they need rather than explicit wiring

### 1.2 Vertical Architecture Slices

Rather than building complete horizontal layers, we will implement vertical slices that deliver complete functional features:

```
┌─────────────────────────────────────────────────────────────┐
│                      Public API Layer                       │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                    Component Layer                          │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐        │
│  │  Providers  │   │   Agents    │   │  Knowledge  │        │
│  └────┬────────┘   └────┬────────┘   └────┬────────┘        │
└───────┼─▲───────────────┼─▲───────────────┼─▲───────────────┘
        │ │               │ │               │ │
┌───────▼─┴───────────────▼─┴───────────────▼─┴───────────────┐
│                      Service Layer                          │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐        │
│  │    State    │   │   Command   │   │    Event    │        │
│  └─────────────┘   └─────────────┘   └─────────────┘        │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐        │
│  │    Buffer   │   │   Resource  │   │   Registry  │        │
│  └─────────────┘   └─────────────┘   └─────────────┘        │
└───────────┬─▲───────────────┬─▲───────────────┬─▲───────────┘
            │ │               │ │               │ │
┌───────────▼─┴───────────────▼─┴───────────────▼─┴───────────┐
│                NERV Components & Primitives                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐        │
│  │  EventBus   │   │TemporalStore│   │ EffectMonad │        │
│  └─────────────┘   └─────────────┘   └─────────────┘        │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐        │
│  │  StateProj. │   | AspectWeaver│   │  Container  │        │
│  └─────────────┘   └─────────────┘   └─────────────┘        │
└───────────┬─▲───────────────────────────────────────────────┘
            │ │
┌───────────▼─┴───────────────────────────────────────────────┐
│                  Inner Universe Layer                       │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐        │
│  │ Controller  │   │ SpacetimeDB │   │  Adapters   │        │
│  └─────────────┘   └─────────────┘   └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

For each feature slice, we will:
1. Implement only the necessary components from each layer
2. Build complete end-to-end functionality that users can test
3. Follow the clean break architecture principles within the feature scope
4. Enable incremental adoption and testing of the architecture

### 1.3 Key Architectural Components

#### Core NERV Components

1. **EventBus**: Reactive Event Mesh implementation for decoupled communication
2. **TemporalStore**: Historical state tracking with version history
3. **PerspectiveAware**: Context-specific views of data
4. **StateProjector**: Efficient state evolution with immutability
5. **EffectMonad**: Explicit side-effect tracking
6. **AspectWeaver**: Cross-cutting concerns management
7. **Container**: Dependency management system
8. **QuantumPartitioner**: Parallel execution with dependencies
9. **DiffSynchronizer**: Data reconciliation between systems

#### Inner Universe Integration

1. **Controller**: Central coordination for SpacetimeDB interaction
2. **Adapters**: Connect NERV components to SpacetimeDB
3. **Type Mapping**: Consistent mapping between Python and Rust types

#### Core Services

1. **Service Registry**: Central registry for service discovery
2. **Event System**: Event subscription and publication
3. **Buffer System**: Thread-safe data flow management
4. **State Container**: Versioned state management
5. **Command System**: Command pattern implementation
6. **Resource Manager**: Resource lifecycle management

## 2. Feature-Slice Implementation Approach

### 2.1 Streaming Chat Feature

The Streaming Chat feature slice will implement:

1. **EventBus Component**: For real-time event communication
2. **Buffer Service**: For streaming token management
3. **State Container**: For response tracking
4. **Provider Services**: For LLM integration

This feature demonstrates:
- Event-driven architecture
- Real-time data flow
- Thread safety
- Provider integration

### 2.2 Agent Delegation Feature

The Agent Delegation feature slice will implement:

1. **TemporalStore Component**: For agent state tracking
2. **Event System**: For agent communication
3. **Command System**: For task execution
4. **State Management**: For task tracking

This feature demonstrates:
- State transition management
- Complex event flows
- Command pattern usage
- Multi-agent coordination

### 2.3 Knowledge Retrieval Feature

The Knowledge Retrieval feature slice will implement:

1. **PerspectiveAware Component**: For context-specific views
2. **Inner Universe Integration**: For persistence
3. **Resource Management**: For vector stores
4. **Buffer System**: For chunking and embedding

This feature demonstrates:
- Persistence layer integration
- Resource lifecycle management
- Data transformation
- Information retrieval patterns

## 3. Component Implementation Strategy

### 3.1 EventBus and Event System

The EventBus serves as the communication backbone across components:

- **Implementation Approach**: Start with minimal functionality for Streaming Chat
- **Key Capabilities**: Event subscription, publication, filtering
- **Integration Points**: Provider streaming, user interface updates
- **Extensions**: Add middleware, history tracking for later features

### 3.2 Buffer System 

The Buffer System manages streaming data flow:

- **Implementation Approach**: Implement for token streaming first
- **Key Capabilities**: Thread-safe operations, flow control
- **Integration Points**: Provider streaming, user interface
- **Extensions**: Add batching, priority for later features

### 3.3 State Container

The State Container provides versioned state management:

- **Implementation Approach**: Start with simple response tracking
- **Key Capabilities**: State updates, version tracking
- **Integration Points**: UI state representation, event triggers
- **Extensions**: Add full history, branching for later features

### 3.4 Resource Management

Resource Management handles external dependencies:

- **Implementation Approach**: Start with provider connections
- **Key Capabilities**: Lifecycle management, cleanup
- **Integration Points**: Vector stores, external services
- **Extensions**: Add monitoring, pooling for later features

## 4. Implementation Roadmap and Dependencies

### 4.1 Streaming Chat Dependencies

For the Streaming Chat feature:

1. **NERV Components**:
   - EventBus - Essential
   - Buffer System - Essential
   - StateProjector - Essential
   - Container - Optional

2. **Service Implementations**:
   - Event System - Essential
   - Buffer Service - Essential
   - State Service - Essential
   - Provider Service - Essential

### 4.2 Agent Delegation Dependencies

For the Agent Delegation feature:

1. **NERV Components**:
   - EventBus - Essential (reuse from Streaming Chat)
   - TemporalStore - Essential
   - Container - Essential
   - EffectMonad - Optional

2. **Service Implementations**:
   - Event System - Essential (reuse from Streaming Chat)
   - Command Service - Essential
   - State Service - Essential (extend from Streaming Chat)
   - Registry Service - Essential

### 4.3 Knowledge Retrieval Dependencies

For the Knowledge Retrieval feature:

1. **NERV Components**:
   - PerspectiveAware - Essential
   - DiffSynchronizer - Essential
   - Inner Universe Controller - Essential

2. **Service Implementations**:
   - Resource Service - Essential
   - Persistence Service - Essential
   - Buffer Service - Essential (reuse from Streaming Chat)
   - Registry Service - Essential (reuse from Agent Delegation)

## 5. Natural Integration Zones

The architecture recognizes natural integration zones where different patterns blend together organically:

### 5.1 State-Event Continuum

Where state management and event systems naturally blend:

- Events trigger state transitions in TemporalStore
- State transitions publish events through EventBus
- State history aligns with event history
- Versioned state and event sequences provide natural correlation

### 5.2 Execution-Dependency Fabric

Where command execution and service dependencies naturally interweave:

- Command execution depends on service availability
- Service discovery influences command capabilities
- Effect tracking captures service interactions
- Command lifecycles align with resource lifecycles

### 5.3 Perspective-Synchronization Mesh

Where data transformation and data synchronization naturally overlap:

- Data projections influence synchronization strategies
- Schema definitions serve validation and mapping purposes
- Context-specific views inform synchronization priorities
- Transformation and reconciliation form natural feedback loops

## 6. Conclusion

This service architecture approach focuses on delivering vertical feature slices while maintaining the architectural integrity of the NERV system. By implementing only the necessary components for each feature, we can deliver value incrementally while still building toward the complete clean break architecture.

Key advantages of this approach:

1. **Faster Value Delivery**: Complete features delivered earlier
2. **Lower Implementation Risk**: Architecture validated through actual usage
3. **Better Resource Allocation**: Focus on components needed for current features
4. **Emergent Design**: Architecture emerges naturally from interaction patterns
5. **Adaptive Evolution**: Components evolve based on real-world usage

::: tip Next Steps
Focus on implementing the core components required for the Streaming Chat feature: EventBus, Buffer Service, and State Container. This will establish the foundation for immediate functional value while validating core architectural patterns.
:::