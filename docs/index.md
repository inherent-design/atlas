---
title: Home
layout: home

hero:
  name: Atlas
  text: Documentation
  tagline: Advanced Multi-Modal Learning & Guidance Framework
  actions:
    - theme: brand
      text: Getting Started
      link: /guides/getting_started
    - theme: alt
      text: Architecture
      link: /architecture/
    - theme: alt
      text: Components
      link: /components/providers/

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
- **[Architecture Overview](./architecture/)**: High-level system architecture
- **[Component Relationships](./architecture/components.md)**: How components interact
- **[Data Flow](./architecture/data_flow.md)**: Data pathways through the system
- **[Design Principles](./architecture/design_principles.md)**: Core design patterns and principles

#### Components (Bottom-Up Implementation)
- **[Core Components](./components/core/config.md)**: Configuration, environment, errors, and prompts
- **[Agent System](./components/agents/controller.md)**: Agent implementation and registry
- **[Knowledge System](./components/knowledge/)**: Document processing and retrieval
- **[Graph System](./components/graph/)**: State management and workflow construction
- **[Providers](./components/providers/)**: Integration with different LLM providers

#### Workflows (Holistic Integration)
- **[Query Workflow](./workflows/query.md)**: Standard query-response flow
- **[Retrieval Workflow](./workflows/retrieval.md)**: Knowledge retrieval process
- **[Multi-Agent Workflow](./workflows/multi_agent.md)**: Controller-worker coordination
- **[Custom Workflows](./workflows/custom_workflows.md)**: Creating specialized workflows

#### Developer Guides
- **[Getting Started](./guides/getting_started.md)**: Quick start for new developers
- **[Configuration](./guides/configuration.md)**: Configuring Atlas for your needs
- **[Testing](./guides/testing.md)** 🚧: Testing strategies and tools (planned architecture)
- **[Type Checking](./guides/type_checking.md)**: Type safety and validation
- **[Examples](https://github.com/inherent-design/atlas/tree/main/examples)**: Practical demonstrations of Atlas functionality

#### Project Management
- **[MVP Strategy](./project-management/roadmap/mvp_strategy.md)**: Implementation approach for MVP
- **[Progress Tracking](./project-management/tracking/todo.md)**: Current implementation status
- **[Documentation Planning](./project-management/planning/implementation_planning.md)**: Implementation and documentation plans

#### Reference
- **[API Reference](./reference/api.md)**: Core API documentation
- **[CLI Options](./reference/cli.md)**: Command-line interface guide
- **[Environment Variables](./reference/env_variables.md)**: Available configuration options
- **[FAQ](./reference/faq.md)**: Frequently asked questions
