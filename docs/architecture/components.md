# Atlas Components

Atlas is built using a modular component architecture that enables flexible configuration and extension. This document provides an overview of the major components and their relationships.

## Component Diagram

The following diagram shows the main components of Atlas and how they interact:

```mermaid
graph TD
    %% Agent Components
    subgraph "Agent Components"
        BaseAgent[AtlasAgent]
        Controller[ControllerAgent]
        Workers[Worker Agents]
        Controller --> BaseAgent
        Workers --> BaseAgent
    end

    %% Knowledge Components
    subgraph "Knowledge Components"
        KB[KnowledgeBase]
        DocProc[DocumentProcessor]
        KB --> ChromaDB[(ChromaDB)]
        DocProc --> KB
    end

    %% Model Components
    subgraph "Model Provider Components"
        ModelFactory[ModelFactory]
        ModelProvider[ModelProvider]
        Anthropic[AnthropicProvider]
        OpenAI[OpenAIProvider]
        Ollama[OllamaProvider]
        ModelFactory --> ModelProvider
        Anthropic --> ModelProvider
        OpenAI --> ModelProvider
        Ollama --> ModelProvider
    end

    %% Graph Components
    subgraph "Graph Components"
        StateGraph[StateGraph]
        Edge[Edge]
        Node[Node]
        StateGraph --> Edge
        StateGraph --> Node
    end

    %% Core Components
    subgraph "Core Components"
        Config[Config]
        Telemetry[Telemetry]
        Error[Error Handling]
    end

    %% Connections between components
    BaseAgent --> KB
    BaseAgent --> ModelProvider
    Controller --> StateGraph
    Controller --> Workers

    %% Core connections
    Config --> BaseAgent
    Config --> KB
    Config --> ModelProvider
    Config --> StateGraph

    Telemetry --> BaseAgent
    Telemetry --> KB
    Telemetry --> ModelProvider
    Telemetry --> StateGraph
```

## Component Relationships

### Agent Components

The agent components form the primary interface with users and orchestrate the entire system:

- **AtlasAgent**: Base agent class that provides core functionality
  - Manages conversation history
  - Interacts with language model providers
  - Retrieves knowledge from the database
  - Formats prompts and processes responses

- **ControllerAgent**: Extends AtlasAgent for multi-agent orchestration
  - Manages worker agents
  - Coordinates parallel tasks
  - Aggregates results from workers
  - Implements complex workflows

- **WorkerAgent**: Specialized agents for specific tasks
  - **AnalysisWorker**: Analyzes queries and identifies information needs
  - **RetrievalWorker**: Focuses on efficient document retrieval
  - **DraftWorker**: Specializes in generating draft responses

```mermaid
classDiagram
    class AtlasAgent {
        +messages: List
        +knowledge_base: KnowledgeBase
        +provider: ModelProvider
        +system_prompt: str
        +query_knowledge_base(query)
        +format_knowledge_context(documents)
        +process_message(message)
        +process_message_streaming(message, callback)
        +reset_conversation()
    }

    class ControllerAgent {
        +workers: Dict
        +worker_results: Dict
        +workflow_type: str
        +process_message(message)
        +create_workers(worker_count)
        +collect_results()
    }

    class WorkerAgent {
        +worker_type: str
        +process_task(task)
        +generate_response(task, context)
    }

    AtlasAgent <|-- ControllerAgent
    AtlasAgent <|-- WorkerAgent
```

### Knowledge Components

The knowledge components manage document storage and retrieval:

- **KnowledgeBase**: Main interface for knowledge retrieval
  - Manages ChromaDB connection
  - Provides document search functionality
  - Handles relevance scoring

- **DocumentProcessor**: Handles document ingestion
  - Splits documents into appropriate chunks
  - Manages metadata and source tracking
  - Creates embeddings for documents

```mermaid
classDiagram
    class KnowledgeBase {
        +client: ChromaClient
        +collection: Collection
        +collection_name: str
        +db_path: str
        +retrieve(query)
        +add_documents(documents)
        +get_collection_stats()
    }

    class DocumentProcessor {
        +process_document(document)
        +chunk_document(document)
        +create_embeddings(chunks)
        +add_metadata(chunks, metadata)
    }

    DocumentProcessor --> KnowledgeBase: adds documents to
```

### Model Provider Components

The model provider components abstract interactions with language model APIs:

- **ModelProvider**: Base interface for all providers
  - **AnthropicProvider**: Implementation for Anthropic Claude models
  - **OpenAIProvider**: Implementation for OpenAI GPT models
  - **OllamaProvider**: Implementation for local Ollama models

- **ModelFactory**: Creates appropriate provider instances
  - Handles provider detection and selection
  - Manages provider registration
  - Implements fallback logic

```mermaid
classDiagram
    class ModelProvider {
        +name: str
        +model_name: str
        +max_tokens: int
        +generate(request)
        +stream(request)
        +validate_api_key()
    }

    class AnthropicProvider {
        +client: AnthropicClient
        +convert_to_anthropic_messages(messages)
        +create_completion(messages)
        +create_streaming_completion(messages)
    }

    class OpenAIProvider {
        +client: OpenAIClient
        +convert_to_openai_messages(messages)
        +create_completion(messages)
        +create_streaming_completion(messages)
    }

    class OllamaProvider {
        +base_url: str
        +convert_to_ollama_messages(messages)
        +create_completion(messages)
        +create_streaming_completion(messages)
    }

    class ModelFactory {
        +create_provider(provider_name, model_name, max_tokens)
        +discover_providers()
        +get_provider_class(provider_name)
    }

    ModelProvider <|-- AnthropicProvider
    ModelProvider <|-- OpenAIProvider
    ModelProvider <|-- OllamaProvider
    ModelFactory --> ModelProvider: creates
```

### Graph Components

The graph components enable complex workflow definition:

- **StateGraph**: LangGraph integration for state management
  - Defines workflow steps and transitions
  - Manages state during workflow execution

- **Edge**: Defines transitions between graph nodes
  - Implements conditional routing
  - Provides workflow branching logic

- **Node**: Defines individual operations in the workflow
  - Implements state transformations
  - Encapsulates agent and system functions

```mermaid
classDiagram
    class StateGraph {
        +nodes: Dict
        +edges: List
        +add_node(name, function)
        +add_edge(start, end, condition)
        +compile()
        +run(state)
    }

    class Edge {
        +start_node: str
        +end_node: str
        +condition: function
        +evaluate(state)
    }

    class Node {
        +name: str
        +function: function
        +process(state)
    }

    StateGraph --> Edge: contains
    StateGraph --> Node: contains
```

### Core Components

The core components provide foundational capabilities:

- **Config**: Configuration management
  - Environment variable integration
  - Default value handling
  - Configuration validation

- **Telemetry**: Performance monitoring
  - Operation tracing
  - Error tracking
  - Performance metrics

- **Error**: Standardized error handling
  - Custom error types
  - Error recovery mechanisms
  - Graceful degradation

```mermaid
classDiagram
    class AtlasConfig {
        +collection_name: str
        +db_path: str
        +model_name: str
        +max_tokens: int
        +from_env()
        +validate()
    }

    class Telemetry {
        +initialize_telemetry()
        +traced(name, attributes)
        +shutdown_telemetry()
        +enable_telemetry()
        +disable_telemetry()
    }

    class ErrorHandling {
        +APIError
        +ConfigError
        +KnowledgeBaseError
        +safe_execute(func, default)
    }
```

## Component Dependencies

The following table shows the key dependencies between components:

| Component       | Dependencies                         |
| --------------- | ------------------------------------ |
| AtlasAgent      | ModelProvider, KnowledgeBase, Config |
| ControllerAgent | AtlasAgent, WorkerAgent, StateGraph  |
| WorkerAgent     | AtlasAgent, KnowledgeBase            |
| KnowledgeBase   | ChromaDB, Config                     |
| ModelProvider   | Config, Telemetry                    |
| StateGraph      | Node, Edge, Config                   |

## Next Steps

- See [Agents](../components/agents/controller.md) for detailed agent documentation
- See [Knowledge](../components/knowledge/) for knowledge system details
- See [Models](../components/models/) for model provider information
- See [Graph](../components/graph/) for workflow documentation
