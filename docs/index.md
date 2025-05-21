---

title: Atlas

layout: home

hero:
  name: Atlas
  text: Documentation
  tagline: Advanced Multi-Modal Learning & Guidance Framework
  actions:
    - theme: brand
      text: Learn More
      link: /v2/nerv/
    - theme: alt
      text: Reference
      link: /api
    - theme: alt
      text: Project Status
      link: /project-management/tracking/proposed_structure
    - theme: alt
      text: Contributing
      link: /contributing

features:
  - icon: 🤖
    title: Multi-Agent Architecture
    details: Controller-worker pattern enabling parallel processing and agent specialization
  - icon: 🔄
    title: LangGraph Integration
    details: Graph-based workflows for complex agent behaviors with state management
  - icon: 🧠
    title: Knowledge Persistence
    details: Maintains context across sessions using ChromaDB vector storage
  - icon: 📚
    title: Documentation Indexing
    details: Automatically processes and indexes documentation with gitignore-aware filtering
  - icon: 🔍
    title: Intelligent Retrieval
    details: Retrieves relevant context based on user queries with semantic search
  - icon: 🧩
    title: Multi-Provider Support
    details: Compatible with Anthropic, OpenAI, and Ollama model providers
---

## Atlas

Atlas is a comprehensive meta-framework for knowledge representation, documentation, and adaptive guidance systems. It integrates advanced graph-based knowledge structures with a controller-worker architecture and LangGraph implementation.

### Key Features

- **Multi-Agent Architecture**: Controller-worker pattern for parallel processing and specialization
- **LangGraph Integration**: Graph-based workflows for complex agent behaviors
- **Knowledge Persistence**: Maintains context across sessions using ChromaDB vector storage
- **Documentation Indexing**: Automatically processes and indexes documentation with gitignore-aware filtering
- **Intelligent Retrieval**: Retrieves relevant context based on user queries
- **Consistent Identity**: Maintains the Atlas identity and principles in all interactions

### Documentation Sections

#### Architecture (Top-Down Design)
- **[Architecture Overview](./v2/nerv/)**: High-level system architecture
- **[Component Patterns](./v2/nerv/patterns/)**: Core architectural patterns
- **[Component Implementation](./v2/nerv/components/)**: Component implementations
- **[Integration Guide](./v2/inner-universe/integration_guide.md)**: System integration guide

#### Components (Bottom-Up Implementation)
- **[Primitives](./v2/nerv/primitives/)**: Core building blocks of the system
- **[Composites](./v2/nerv/composites/)**: Combined component patterns
- **[Implementation](./v2/inner-universe/implementation.md)**: Implementation details
- **[Type System](./v2/inner-universe/types.md)**: Type definitions and mappings
- **[Schema](./v2/inner-universe/schema.md)**: Data schema definitions

#### System Integration (Holistic Integration)
- **[Event-Driven Architecture](./v2/nerv/composites/event_driven_architecture.md)**: Event-based communication system
- **[Parallel Workflow Engine](./v2/nerv/composites/parallel_workflow_engine.md)**: Multi-step workflow orchestration
- **[Adaptive State Management](./v2/nerv/composites/adaptive_state_management.md)**: Dynamic state handling
- **[Implementation Strategy](./v2/inner-universe/implementation.md)**: Implementation approach and details

#### Developer Guides
- **[Testing Strategy](./v2/inner-universe/testing_strategy.md)**: Testing approach and tools
- **[Deployment](./v2/inner-universe/deployment.md)**: Deployment guidelines
- **[Migration Guide](./v2/inner-universe/migration_guide.md)**: Migrating to the current architecture
- **[Type Mappings](./v2/inner-universe/type_mappings.md)**: Type reference for implementation
- **[Examples](https://github.com/inherent-design/atlas/tree/main/examples)**: Practical demonstrations of Atlas functionality

#### Project Management
- **[Product Roadmap](./project-management/roadmap/product_roadmap.md)**: Comprehensive development roadmap
- **[Implementation Plan](./project-management/planning/schema_service_plan.md)**: Core services implementation plan
- **[Progress Tracking](./project-management/tracking/proposed_structure.md)**: Current implementation status
- **[Project Overview](./project-management/index.md)**: Project management documentation

#### Reference
- **[Licensing](./reference/licensing.md)**: Licensing information
- **[Pattern Cheatsheet](./v2/nerv/types/cheatsheet.md)**: Quick reference for patterns and components
- **[Architecture Diagrams](./v2/nerv/types/diagrams.md)**: Visual architecture representations
- **[Implementation Approach](./v2/inner-universe/index.md)**: Implementation overview and approach

#### Contributing
- **[Contribution Guide](./contributing/)**: Guidelines for contributing to Atlas
- **[Documentation Standards](./contributing/documentation-standards.md)**: Standards for writing documentation
- **[Content Containers](./contributing/content-containers.md)**: Guidelines for using custom containers
- **[Code Examples](./contributing/code-examples.md)**: Standards for code samples and examples
