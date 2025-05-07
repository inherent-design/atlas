# Atlas Architecture Planning

This document outlines the architectural planning for Atlas, including module organization, implementation strategies, and development principles.

## System Architecture Overview

The Atlas architecture follows a modular design with clear separation of concerns:

- **Core Components**: Base functionality, configuration, and error handling
- **Agents**: Specialized entities that perform specific tasks
- **Knowledge System**: Document storage, retrieval, and query processing
- **Models**: LLM provider integrations and abstraction layer
- **Graph**: State management and flow control
- **Tools**: Capability extensions for agents
- **Orchestration**: Coordination of multi-agent systems

## Proposed File Structure

```
atlas/
├── agents/
│   ├── __init__.py
│   ├── base.py             # Keep - extend with tool capabilities
│   ├── controller.py       # Keep - enhance with message routing
│   ├── registry.py         # Keep - extend for capability discovery
│   ├── worker.py           # Keep - extend for specialized workers
│   ├── messaging/          # NEW directory for agent communication
│   │   ├── __init__.py
│   │   ├── message.py      # NEW - StructuredMessage implementation
│   │   ├── routing.py      # NEW - Message routing and delivery
│   │   └── serialization.py # NEW - Message serialization/deserialization
│   └── specialized/        # NEW directory for specialized agents
│       ├── __init__.py
│       ├── knowledge_agent.py # NEW - Specialized for knowledge operations
│       ├── tool_agent.py   # NEW - Tool-capable agent base class
│       └── research_agent.py # NEW - Research-focused agent
├── tools/                  # NEW top-level directory for tools
│   ├── __init__.py
│   ├── base.py             # NEW - Tool interface definition
│   ├── registry.py         # NEW - Tool registration and discovery
│   ├── permissions.py      # NEW - Tool access control
│   ├── standard/           # NEW - Standard built-in tools
│   │   ├── __init__.py
│   │   ├── knowledge_tools.py # NEW - Knowledge base interaction tools
│   │   ├── web_tools.py    # NEW - Web interaction tools
│   │   └── utility_tools.py # NEW - Utility functions as tools
│   └── mcp/                # NEW - MCP integration
│       ├── __init__.py
│       ├── adapter.py      # NEW - MCP protocol adapter
│       ├── converter.py    # NEW - Convert MCP tools to Atlas tools
│       └── registry.py     # NEW - MCP tool registration
└── orchestration/          # ENHANCE existing directory
    ├── __init__.py
    ├── coordinator.py      # Enhance for tool orchestration
    ├── parallel.py         # Keep
    ├── scheduler.py        # Keep
    ├── messaging/          # NEW - Messaging infrastructure
    │   ├── __init__.py
    │   ├── broker.py       # NEW - Message broker implementation
    │   └── queue.py        # NEW - Message queue implementation
    └── workflow/           # NEW - Workflow definitions
        ├── __init__.py
        ├── patterns.py     # NEW - Common workflow patterns
        └── templates.py    # NEW - Workflow templates
```

## Implementation Approach

### 1. Multi-Agent System Architecture

The multi-agent system follows a controller-worker pattern where:

- **Controller Agent**: Coordinates task distribution and result aggregation
- **Worker Agents**: Perform specialized tasks with domain expertise
- **Structured Messaging**: Enables rich communication between agents
- **Tool System**: Extends agent capabilities with external functions

Implementation details:

```python
class StructuredMessage:
    """Structured message format for agent communication with tool capability."""
    
    def __init__(self, content, metadata=None, task_id=None, tool_calls=None):
        self.content = content
        self.metadata = metadata or {}
        self.task_id = task_id or str(uuid.uuid4())
        self.timestamp = time.time()
        self.tool_calls = tool_calls or []
        self.source_agent = None
        self.target_agent = None
    
    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            "content": self.content,
            "metadata": self.metadata,
            "task_id": self.task_id,
            "timestamp": self.timestamp,
            "tool_calls": self.tool_calls,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent
        }
        
    @classmethod
    def from_dict(cls, data):
        """Create message from dictionary."""
        msg = cls(
            content=data["content"],
            metadata=data["metadata"],
            task_id=data["task_id"],
            tool_calls=data["tool_calls"]
        )
        msg.timestamp = data["timestamp"]
        msg.source_agent = data["source_agent"]
        msg.target_agent = data["target_agent"]
        return msg
```

### 2. Tool System Architecture

The tool system provides a standardized way to extend agent capabilities:

```python
class AgentToolkit:
    """Registry for tools that agents can use."""
    
    def __init__(self):
        self.tools = {}
        self.permissions = {}
    
    def register_tool(self, name, function, description, schema):
        """Register a tool function with its schema."""
        self.tools[name] = {
            "function": function,
            "description": description,
            "schema": schema
        }
    
    def get_tool_descriptions(self, agent_id):
        """Get tool descriptions available to an agent."""
        return {
            name: tool["description"] 
            for name, tool in self.tools.items()
            if self.has_permission(agent_id, name)
        }
        
    def execute_tool(self, agent_id, tool_name, arguments):
        """Execute a tool if agent has permission."""
        if not self.has_permission(agent_id, tool_name):
            raise PermissionError(f"Agent {agent_id} doesn't have permission to use {tool_name}")
            
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found in registry")
            
        tool = self.tools[tool_name]
        return tool["function"](**arguments)
        
    def has_permission(self, agent_id, tool_name):
        """Check if agent has permission to use tool."""
        if agent_id not in self.permissions:
            return False
            
        if "*" in self.permissions[agent_id]:
            return True
            
        return tool_name in self.permissions[agent_id]
```

### 3. Specialized Agent Architecture

Tool-capable agents extend the base worker agent with tool functionality:

```python
class ToolCapableAgent(WorkerAgent):
    """Worker agent with tool execution capabilities."""
    
    def __init__(self, name, model_provider, toolkit=None):
        super().__init__(name, model_provider)
        self.toolkit = toolkit or AgentToolkit()
        self.capabilities = []
        
    def register_capability(self, capability):
        """Register a capability this agent provides."""
        self.capabilities.append(capability)
        
    def handle_message(self, message):
        """Process incoming message and execute any tool calls."""
        # Handle basic message content
        response_content = self._process_content(message.content)
        
        # Handle any tool calls in the message
        tool_results = []
        for tool_call in message.tool_calls:
            result = self.toolkit.execute_tool(
                self.id,
                tool_call["name"],
                tool_call["arguments"]
            )
            tool_results.append({
                "name": tool_call["name"],
                "result": result
            })
            
        # Create response message
        response = StructuredMessage(
            content=response_content,
            metadata={"type": "response", "in_reply_to": message.task_id},
            task_id=str(uuid.uuid4()),
            tool_results=tool_results
        )
        response.source_agent = self.id
        response.target_agent = message.source_agent
        
        return response
```

## Implementation Status by Module

### Models Module

**Completed:**
- ✅ Base provider interface with standardized types
- ✅ Factory pattern with registration mechanism
- ✅ Provider auto-detection from environment
- ✅ Environment variable integration with env module
- ✅ Unit tests for provider functionality
- ✅ Streaming implementation for all providers (Anthropic, OpenAI, Ollama)
- ✅ Enhanced API key validation
- ✅ Comprehensive error handling with standardized error types
- ✅ Token usage tracking and cost calculation
- ✅ Mock provider implementation for testing without API keys

**Planned:**
- ⏱️ Connection pooling for improved performance
- ⏱️ Provider health monitoring
- ⏱️ Advanced error handling with retries
- ⏱️ Cost optimization strategies

### Knowledge System

**Completed:**
- ✅ Enhanced document chunking with semantic boundaries
  - ✅ Document type detection (Markdown, code, general text)
  - ✅ Specialized chunking strategies for different document types
  - ✅ Code chunking based on function/class definitions
  - ✅ Markdown chunking with frontmatter preservation
- ✅ Content deduplication system
  - ✅ Content hashing with normalization
  - ✅ Duplicate detection and reference tracking
  - ✅ Configurable deduplication options
- ✅ Real-time directory ingestion
  - ✅ Directory watching with watchdog integration
  - ✅ File change detection and processing
  - ✅ Cooldown mechanisms to prevent duplicate processing
  - ✅ Enhanced progress indicators for ingestion and embedding
  - ✅ Performance metrics and timing information
- ✅ Enhanced retrieval with filtering
  - ✅ Metadata-based filtering with complex queries
  - ✅ RetrievalFilter class for filter composition
  - ✅ RetrievalResult with relevance scoring
  - ✅ Reranking capabilities for better relevance
- ✅ Hybrid retrieval implementation
  - ✅ Combined semantic and keyword search
  - ✅ Weighted result combination
  - ✅ Configurable search parameters
- ✅ Customizable embedding strategies
  - ✅ Abstract embedding strategy interface
  - ✅ Provider-specific implementations (Anthropic, ChromaDB)
  - ✅ Strategy factory for easy instantiation
  - ✅ Hybrid embedding approach support
- ✅ Enhanced document identification
  - ✅ Simplified document ID format (parent_dir/filename.md)
  - ✅ Consistent metadata with both full paths and simplified IDs
  - ✅ Improved readability for debugging and document inspection

**Planned:**
- ⏱️ Query caching for performance optimization
- ⏱️ Performance telemetry for knowledge operations
- ⏱️ Support for multimedia document types
- ⏱️ Advanced relevance feedback mechanisms

## Acceleration Pathways

These pathways represent specialized areas of functionality that can be accelerated in parallel with the MVP approach, depending on specific user priorities and resource availability.

### Enhanced Knowledge Retrieval 🧠 [Accel] ✅

- ✅ Implement advanced embedding with multi-provider support
- ✅ Create sophisticated chunking with overlap strategies
- ✅ Enhance retrieval with hybrid search (keywords + semantic)
- ✅ Add document metadata filtering and faceted search
- [ ] Implement caching layers for improved performance

### Multi-Agent Intelligence 🤖 [Accel]

- [x] Build basic agent registry with registration mechanism
- [x] Implement basic workflow routing through graph edges
- [x] Implement structured message format for cross-agent communication
- [x] Build tool-capable specialized worker agents
- [x] Implement tool registration and permission management
- [ ] Create MCP (Model Context Protocol) integration layer
- [ ] Add support for external tool registration
- [ ] Implement agent capability advertising and discovery
- [ ] Create agent state preservation and context management
- [ ] Add dynamic agent allocation based on task requirements
- [ ] Implement feedback and observability mechanisms

### Provider Flexibility & Performance ⚡ [Accel]

- [x] Complete streaming implementation for Anthropic provider
- [x] Complete full implementations for all providers
  - [x] OpenAI Provider Implementation
    - [x] Proper API key validation with test API call
    - [x] Complete streaming implementation with StreamHandler
    - [x] Error handling using standardized error types
    - [x] Token usage and cost calculation
    - [x] Add support for stream_with_callback()
  - [x] Ollama Provider Implementation
    - [x] Enhanced server availability validation
    - [x] Complete streaming implementation with StreamHandler
    - [x] Error handling using standardized error types
    - [x] Token usage estimation improvements
    - [x] Add support for stream_with_callback()
- [x] Implement basic API key validation for providers
- [x] Implement sophisticated streaming with token tracking for all providers
- [ ] Add connection pooling and performance optimizations
- [ ] Create provider switching based on cost/performance needs
- [ ] Implement fallback mechanisms between providers

## Development Principles

1. **Clean Break Philosophy**: Prioritize building high-quality, robust APIs over maintaining backward compatibility with legacy code.
2. **Parallel Development**: Build new implementations alongside existing code until ready for complete cutover.
3. **Test-Driven Development**: Create comprehensive tests alongside or before implementation.
4. **Complete Documentation**: Provide thorough documentation for all new components with clear examples.
5. **Robust Error Handling**: Implement consistent, informative error handling throughout all components.
6. **Type Safety**: Use comprehensive type hints and validation for better code quality and reliability.
7. **Consistent Environment Configuration**: Maintain a clear precedence model for configuration (CLI args > env vars > defaults).
8. **Modular Design**: Create loosely coupled components that can be used independently.
9. **Documentation-Driven Implementation**: Use documentation to guide implementation while resolving any discrepancies:
   - Start with thoroughly documenting the expected behavior and interfaces
   - When discrepancies arise between documentation and implementation needs:
     - Favor the approach that provides better API design, performance, and maintainability
     - Update documentation to match implementation decisions when technical requirements necessitate changes
     - Preserve the original design intent while adapting to technical realities
   - Keep both implementation and documentation in sync throughout development