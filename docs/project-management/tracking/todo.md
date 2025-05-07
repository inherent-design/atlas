# Atlas Project TODO

## At a Glance

**Completed:**
- ✅ Core infrastructure and provider implementations
- ✅ Knowledge system with hybrid retrieval and settings interface
- ✅ Documentation system with comprehensive coverage

**Current Focus:**
- 🔄 Multi-Agent Orchestration: Structured messaging and tool-capable agents
- 🔄 MCP Integration: Model Context Protocol for tool integration
- 🔄 Specialized Agents: Purpose-built agents with specific capabilities

**Implementation Priority:**
1. Structured message system for agent communication
2. Tool integration framework with MCP support
3. Specialized worker agents with tool capabilities

## Proposed File Structure Changes

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

## Implementation Tasks

1. **Multi-Agent System (High Priority)**
   - [ ] Implement StructuredMessage class with metadata and tool call support
   - [ ] Create specialized worker agent base class with tool capabilities
   - [ ] Develop AgentToolkit for tool registration and discovery
   - [ ] Add MCP integration adapter for external tools
   - [ ] Implement message routing and broker system
   - [ ] Create context preservation between agent interactions
   - [ ] Build task delegation and result aggregation system
   - [ ] Add parallel processing for independent agent tasks

2. **Tool System Implementation (High Priority)**
   - [ ] Create Tool base class with schema validation
   - [ ] Implement ToolRegistry for tool discovery
   - [ ] Add permission system for tool access control
   - [ ] Develop standard tool set for common operations
   - [ ] Create MCP adapter for external tool integration
   - [ ] Implement tool execution and result handling
   - [ ] Add tool capability advertising mechanism
   - [ ] Build tool call serialization and transport

3. **Workflow Enhancement (Medium Priority)**
   - [ ] Create workflow templates for common patterns
   - [ ] Implement advanced edge routing with tool awareness
   - [ ] Add workflow monitoring and observability
   - [ ] Build parallel execution coordinator
   - [ ] Create visualization system for workflow inspection

## MVP Implementation Strategy

The Atlas MVP follows a **Minimal Viable Pipeline** approach that creates a functioning end-to-end system with simplified implementations of all critical components. This ensures users can benefit from basic functionality across all key value areas before any single component is deeply optimized.

### Phase 1: Foundation Stabilization ✅

**Critical Path [P0]:** ✅ COMPLETED
- [x] Complete streaming implementation for Anthropic provider
- [x] Implement basic API key validation mechanism
- [x] Unify agent implementations (AtlasAgent and MultiProviderAgent)
- [x] Create minimal agent registry with registration mechanism
- [x] Create edges.py file with conditional routing
- [x] Enhance error handling across all core components
- [x] Create query-only version for other agentic clients
- [x] Standardize environment variable handling across components

**Important [P1]:**
- [x] Maintain backward compatibility for existing agent code
- [x] Add basic telemetry throughout agent operations
- [x] Implement simple factory methods for agent creation
- [x] Create examples demonstrating the query-only interface
- [x] Organize testing and examples for better structure
- [x] Add missing unit tests for provider functionality
- [x] Create simple mocked providers for testing

**Nice to Have [P2]:**
- [ ] Add connection pooling for improved performance
- [ ] Create health checks for provider status
- [ ] Add dynamic provider switching capability
- [ ] Implement advanced agent class discovery
- [ ] Create comprehensive telemetry dashboard

### Phase 2: Knowledge Enhancements ✅

**Critical Path [P0]:** ✅ COMPLETED
- [x] Verify and enhance document chunking strategies
  - [x] Implement adaptive chunking based on document structure
  - [x] Add overlap controls to maintain context across chunks
  - [x] Create content-aware boundaries that respect semantic units
  - [x] Support custom chunking strategies for different document types
- [x] Improve metadata handling for documents
  - [x] Add rich metadata extraction from document content
  - [x] Implement metadata-based filtering and sorting
  - [x] Create standardized metadata schema for cross-document queries
  - [x] Support custom metadata fields for specialized document types
- [x] Enhance retrieval with improved relevance scoring
  - [x] Implement hybrid retrieval combining semantic and lexical search
  - [x] Add re-ranking capabilities for better result ordering
  - [x] Create relevance feedback mechanisms
  - [x] Support configurable similarity thresholds
- [x] Add basic filtering capabilities for results
  - [x] Implement metadata-based filtering
  - [x] Add content-based filtering options
  - [x] Create filter combinations with boolean logic
  - [x] Support date range and numeric range filters

**Important [P1]:**
- [x] Implement basic validation of ingested content
  - [x] Add content quality checks for ingested documents
  - [x] Implement duplicate detection mechanisms
  - [x] Create content validation rules for different document types
- [x] Add better error handling for ingestion failures
  - [x] Implement granular error reporting for ingestion steps
  - [x] Create recovery mechanisms for partial ingestion failures
  - [x] Add retry logic for transient failures
- [ ] Create simple caching for frequent queries
  - [ ] Implement in-memory cache for frequent queries
  - [ ] Add cache invalidation based on document changes
  - [ ] Create configurable cache parameters
- [ ] Add telemetry for knowledge operations
  - [ ] Implement performance metrics for ingestion and retrieval
  - [ ] Add detailed logging for knowledge operations
  - [ ] Create dashboard for monitoring knowledge system performance
- [x] Implement document versioning support
  - [x] Add version tracking for documents
  - [x] Implement version-specific queries
  - [x] Create history tracking for document changes

**Nice to Have [P2]:**
- [ ] Add support for multimedia document types
- [ ] Implement hierarchical document structures
- [ ] Create document relevance feedback system
- ✅ Add hybrid semantic-keyword search
- ✅ Implement faceted filtering options

### Phase 3: Workflow Improvements 🔀

**Critical Path [P0]:**
- [x] Create basic Edge class with conditional routing
- [x] Implement simple edge factories for common patterns
- [ ] Improve message passing between agents
- [ ] Add structured message formats with metadata

**Important [P1]:**
- [ ] Add validation for edge connections
- [ ] Create examples of useful workflow patterns
- [ ] Implement better error handling for communication
- [ ] Create simple coordination patterns
- [ ] Add logging for workflow execution

**Nice to Have [P2]:**
- [ ] Implement advanced branching logic for complex workflows
- [ ] Create visualization tools for workflows
- [ ] Add dynamic workflow creation capabilities
- [ ] Implement workflow versioning and history
- [ ] Create parallel execution optimization

### Phase 4: Environment & Configuration ✅

**Critical Path [P0]:** ✅ COMPLETED
- [x] Refine environment variable handling with env.py module
- [x] Implement consistent configuration precedence (CLI > ENV > defaults)
- [x] Update core modules to respect environment variables
- [x] Document environment variables and their usage
- [x] Enhance error reporting for configuration issues

**Important [P1]:** ✅ COMPLETED
- [x] Add provider-specific environment variables
- [x] Create validation logic for environment variables
- [x] Implement development mode configuration
- [x] Create CLI tools registry documentation
- [x] Enhance environment variable documentation

### Phase 5: Documentation System ✅

**Critical Path [P0]:** ✅ COMPLETED
- [x] Create comprehensive documentation structure
- [x] Implement VitePress-based documentation site
- [x] Document all core components and their APIs
- [x] Create workflow documentation with examples
- [x] Ensure proper linking and navigation

**Important [P1]:** ✅ COMPLETED
- [x] Add diagrams for architecture and data flow
- [x] Create consistent documentation standards
- [x] Implement proper index.md files for all directories
- [x] Create comprehensive navigation and sidebar
- [x] Optimize diagrams without inline styling

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
- [ ] Implement structured message format for cross-agent communication
- [ ] Build tool-capable specialized worker agents
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

## Key Implementation Components

### 1. Structured Message System

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

### 2. Agent Toolkit for Tool Management

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

### 3. Specialized Worker Agent

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

## Models Module Implementation Status

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

**Completed Tests:**
- ✅ Comprehensive testing for all providers
  - ✅ Create mock provider implementation for testing
  - ✅ Implement unit tests for OpenAI provider streaming
  - ✅ Implement unit tests for Ollama provider streaming 
  - ✅ Add tests for provider error handling patterns
  - ✅ Create tests for token usage tracking and cost calculation
  - ✅ Update streaming example to demonstrate all providers
  - ✅ Update OpenAI pricing information to latest models (GPT-4.1, GPT-4.1 mini, GPT-4.1 nano, o3, o4-mini)

**Planned:**
- ⏱️ Connection pooling for improved performance
- ⏱️ Provider health monitoring
- ⏱️ Advanced error handling with retries
- ⏱️ Cost optimization strategies

## Knowledge System Implementation Status

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

## Documentation Status

**Completed:**
- ✅ VitePress documentation structure with proper navigation
- ✅ Complete documentation for all components (59 files)
- ✅ Comprehensive guides and tutorials
- ✅ Mermaid diagrams for architecture and data flow
- ✅ API references and code examples
- ✅ Index.md files for all directory routes
- ✅ Proper linking system and cross-references
- ✅ Diagram standards with clean Mermaid implementation

**Planned Enhancements:**
- ⏱️ Interactive code examples
- ⏱️ More visual diagrams and illustrations
- ⏱️ Advanced troubleshooting guides
- ⏱️ User journey documentation

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

See `project-management/roadmap/mvp_strategy.md` for a detailed explanation of the MVP approach, implementation timelines, and prioritization framework.