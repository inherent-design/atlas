# Atlas Documentation Planning

This document outlines the planning and tracking system for Atlas documentation, including the documentation structure, completed tasks, and ongoing plans for documentation improvement.

## Current Status

```
✅ Documentation system with 60+ completed files
✅ Next focus: Multi-agent orchestration, MCP integration, and tool systems
```

## Documentation Structure

```
docs/
├── architecture/             # Top-down design ✅
│   ├── components.md         # Component relationships ✅
│   ├── data_flow.md          # Data flow patterns ✅
│   ├── design_principles.md  # Design patterns & principles ✅
│   ├── index.md              # Architecture section index/overview ✅
│   ├── module_interaction.md # Module interaction and integration ✅
│   └── system_requirements.md # Dependencies & requirements ✅
├── components/               # Bottom-up implementation
│   ├── agents/               # Agent components ✅
│   │   ├── controller.md     # Controller agent ✅
│   │   ├── index.md          # Agents overview ⏳
│   │   ├── messaging.md      # NEW - Agent messaging system ⏳
│   │   ├── specialized.md    # NEW - Specialized agent types ⏳
│   │   └── workers.md        # Worker agents ✅
│   ├── core/                 # Core components ✅
│   │   ├── config.md         # Configuration ✅
│   │   ├── env.md            # Environment variables ✅
│   │   ├── errors.md         # Error handling ✅
│   │   ├── prompts.md        # Prompt system ✅
│   │   └── telemetry.md      # Telemetry and tracing ✅
│   ├── graph/                # Graph components ✅
│   │   ├── edges.md          # Graph edges ✅
│   │   ├── index.md          # Graph section index/overview ✅
│   │   ├── nodes.md          # Graph nodes ✅
│   │   └── state.md          # State management ✅
│   ├── knowledge/            # Knowledge components ✅
│   │   ├── index.md          # Knowledge section index/overview ✅
│   │   ├── ingestion.md      # Document ingestion ✅
│   │   └── retrieval.md      # Retrieval functionality ✅
│   ├── models/               # Model providers ✅
│   │   ├── anthropic.md      # Anthropic integration ✅
│   │   ├── index.md          # Models section index/overview ✅
│   │   ├── mock.md           # Mock provider for testing ✅
│   │   ├── ollama.md         # Ollama integration ✅
│   │   └── openai.md         # OpenAI integration ✅
│   ├── tools/                # NEW - Tools components ⏳
│   │   ├── core.md           # NEW - Tool core concepts ⏳
│   │   ├── index.md          # NEW - Tools overview ⏳
│   │   ├── mcp.md            # NEW - MCP integration ⏳
│   │   └── standard.md       # NEW - Standard tool documentation ⏳
│   └── orchestration/        # NEW - Orchestration components ⏳
│       ├── index.md          # NEW - Orchestration overview ⏳
│       ├── messaging.md      # NEW - Messaging system ⏳
│       └── workflows.md      # NEW - Workflow patterns ⏳
├── guides/                   # Developer guides ✅
│   ├── configuration.md      # Configuration guide ✅
│   ├── examples/             # Code examples ✅
│   │   ├── advanced_examples.md  # Advanced usage patterns ✅
│   │   ├── hybrid_retrieval_example.md  # Hybrid search example ✅
│   │   ├── index.md          # Examples index/overview (formerly README.md) ✅
│   │   ├── multi_agent_example.md # Multi-agent workflows ✅
│   │   ├── query_example.md  # Query client usage ✅
│   │   ├── retrieval_example.md # Document retrieval ✅
│   │   └── streaming_example.md # Streaming responses ✅
│   ├── getting_started.md    # Getting started guide ✅
│   ├── testing.md            # Testing guide ✅
│   └── type_checking.md      # Type checking guide ✅
├── index.md                  # Main documentation landing page ✅
├── project-management/       # Project management documents ✅
│   ├── planning/             # Planning documents ✅
│   │   └── docs_planning.md  # Documentation planning ✅
│   ├── roadmap/              # Project roadmaps ✅
│   │   └── mvp_strategy.md   # MVP implementation strategy ✅
│   └── tracking/             # Progress tracking ✅
│       └── todo.md           # Todo list and progress tracking ✅
├── reference/                # Reference documentation ✅
│   ├── api.md                # API reference ✅
│   ├── cli.md                # CLI options ✅
│   ├── env_variables.md      # Environment variables ✅
│   └── faq.md                # FAQ ✅
└── workflows/                # Holistic integration ✅
    ├── custom_workflows.md   # Creating custom workflows ✅
    ├── multi_agent.md        # Multi-agent workflows ✅
    ├── query.md              # Query workflow ✅
    ├── retrieval.md          # Retrieval workflow ✅
    ├── tool_workflows.md     # NEW - Tool-based workflow examples ⏳
    └── specialized_agents.md # NEW - Working with specialized agents ⏳
```

## Completed Documentation Tasks

- [x] Core system components (config, env, errors, prompts)
- [x] Knowledge system (overview, ingestion, retrieval)
- [x] Graph system (state, nodes, edges)  
- [x] Model providers (base, anthropic, openai, ollama)
- [x] Workflow documentation (query, retrieval, multi-agent)
- [x] User guides (getting started, configuration, testing)
- [x] Reference documentation (API, CLI, env variables)

## Current Documentation Focus

- [ ] **Multi-Agent System Documentation**
  - Structured messaging and routing
  - Specialized agent implementations
  - Tool capability integration
  - Agent communication patterns

- [ ] **MCP Integration Documentation**
  - Model Context Protocol implementation
  - Tool schema and representation
  - Permission and capability management
  - Integration with existing agent system

- [ ] **Workflow Enhancements Documentation**
  - Task delegation and coordination
  - Workflow patterns for common scenarios
  - Parallel processing capabilities
  - Observability and monitoring

## Content Migration Tracking

| Source Document    | Target Location(s)                               | Status     |
| ------------------ | ------------------------------------------------ | ---------- |
| CHROMADB_VIEWER.md | guides/examples/chromadb_viewer.md               | Deprecated |
| ENV_VARIABLES.md   | reference/env_variables.md                       | Complete ✅ |
| MODELS.md          | components/models/index.md                       | Complete ✅ |
| MODEL_PROVIDERS.MD | components/models/{anthropic,openai,ollama}.md   | Complete ✅ |
| MVP_STRATEGY.md    | project-management/roadmap/mvp_strategy.md       | Complete ✅ |
| TESTING.md         | guides/testing.md                                | Complete ✅ |
| TODO.md            | project-management/tracking/todo.md              | Complete ✅ |
| TYPE_CHECKING.md   | guides/type_checking.md                          | Complete ✅ |
| cli/README.md      | reference/cli.md                                 | Complete ✅ |
| DOCS_TODO.md       | project-management/planning/docs_planning.md     | Complete ✅ |
| index.md           | index.md (new structure)                         | Complete ✅ |
| README.md files    | Converted to index.md files for directory routes | Complete ✅ |

## Documentation Principles

### Trimodal Documentation Approach

The Atlas documentation follows a Trimodal approach that provides comprehensive coverage from multiple perspectives:

1. **Top-Down Design** (Architecture)
   - High-level architecture and design principles
   - System requirements and dependencies
   - Component relationships and patterns
   - Data flow diagrams and system interaction maps

2. **Bottom-Up Implementation** (Components)
   - Detailed component functionality and interfaces
   - Implementation details and patterns
   - API references and usage examples
   - Configuration options and customization

3. **Holistic Integration** (Workflows)
   - End-to-end workflow documentation
   - Integration patterns and best practices
   - Cross-cutting concerns and considerations
   - User journey and experience documentation

### Documentation Standards

All Atlas documentation adheres to the following standards:

1. **Structure and Organization**
   - Clear hierarchical structure with logical grouping
   - Consistent file naming and organization
   - Standardized table of contents and navigation
   - Proper cross-referencing between related documents
   - Index files (`index.md`) used for directory-level routes

2. **Content Quality**
   - Comprehensive coverage of all critical functionality
   - Clear, concise explanations with appropriate detail
   - Practical code examples that demonstrate usage
   - Consistent terminology and language throughout

3. **Formatting and Style**
   - Consistent Markdown formatting and styling
   - Proper use of headings, lists, tables, and code blocks
   - Diagrams and visual aids where appropriate
   - Clear distinction between different types of information

4. **Linking Practices**
   - Two different linking styles used for different contexts:
     
     a) **Regular Content Links** (for local Markdown compatibility):
     - Include `.md` extensions for all file links (e.g., `[Link Text](./path/to/file.md)`)
     - Use directory paths without trailing `index.md` for directory index files (e.g., `[Link Text](./directory/)`)
     - Links to sibling files use `./filename.md` format
     - Links to parent directory files use `../filename.md` format
     - Relative paths preferred for all internal documentation links

     b) **VitePress Frontmatter Links** (hero sections, config files):
     - Omit `.md` extensions in VitePress-specific sections (e.g., `/guides/getting_started`)
     - Use directory paths with trailing slash for index pages (e.g., `/directory/`) 
     - Use absolute paths for root-relative references in VitePress config

   - Links checked and verified during the build process

5. **Maintenance Process**
   - Regular reviews and updates alongside code changes
   - Version control for documentation aligned with code
   - Deprecation notices for outdated information
   - Collaborative editing and review process

6. **Diagram Standards**
   - Mermaid diagrams used for all technical diagrams
   - No inline styling in diagrams (rely on VitePress theme styling)
   - Consistent diagram types for similar content
   - Simple, focused diagrams that illustrate key concepts

## Documentation Update Tasks

### Completed Documentation Updates

1. **Core Components**
   - [x] Provider implementations and token usage
   - [x] Knowledge system and hybrid retrieval
   - [x] Settings interfaces for configuration
   - [x] Testing systems and mock providers

2. **Examples and Guides**
   - [x] Multi-provider streaming examples
   - [x] Hybrid retrieval documentation
   - [x] Command-line interface updates
   - [x] Error handling and troubleshooting

## New Documentation Tasks

1. **Multi-Agent Orchestration Documentation**
   - [ ] Create new file: `components/agents/messaging.md`
     - [ ] Document StructuredMessage class and interface
     - [ ] Explain message metadata and serialization
     - [ ] Show message routing and delivery patterns
     - [ ] Document integration with LangGraph workflows
   - [ ] Update `workflows/multi_agent.md`
     - [ ] Add section on message passing protocols
     - [ ] Document message handling between agents
     - [ ] Include diagram of message flow patterns
   - [ ] Create new file: `components/orchestration/workflows.md`
     - [ ] Document workflow patterns for agent coordination
     - [ ] Explain parallel task execution
     - [ ] Detail task delegation and result aggregation
     - [ ] Show configuration for workflow optimization

2. **MCP Integration Documentation**
   - [ ] Create new file: `components/tools/mcp.md`
     - [ ] Document Model Context Protocol implementation
     - [ ] Explain tool representation and execution
     - [ ] Show integration with LLM providers
     - [ ] Provide examples of MCP tool usage
   - [ ] Create new file: `components/tools/index.md`
     - [ ] Overview of tool system architecture
     - [ ] Document tool registry and discovery mechanisms
     - [ ] Explain tool permissions and access control
     - [ ] Show integration with agent workflows

3. **Specialized Agent Documentation**
   - [ ] Create new file: `components/agents/specialized.md`
     - [ ] Document specialized worker agent implementations
     - [ ] Explain tool capability integration
     - [ ] Show agent toolkit usage patterns
     - [ ] Document agent capability discovery and advertising
   - [ ] Create new file: `components/tools/standard.md`
     - [ ] Document standard tool implementations
     - [ ] Explain tool interface requirements
     - [ ] Show tool registration process
     - [ ] Provide examples of creating custom tools

## New Documentation Example: Structured Messaging

The following example demonstrates the kind of documentation planned for the new messaging system:

```python
# Example of StructuredMessage usage
from atlas.agents.messaging import StructuredMessage, MessageType

# Create a structured message with tool calls
message = StructuredMessage(
    content="Please analyze this document", 
    metadata={
        "priority": "high",
        "sender": "controller_agent",
        "task_id": "doc_analysis_123"
    },
    tool_calls=[{
        "name": "knowledge_retrieval",
        "arguments": {
            "query": "document structure patterns",
            "max_results": 3
        }
    }]
)

# Message can be serialized for transport
serialized = message.to_dict()

# And reconstructed by the receiving agent
received = StructuredMessage.from_dict(serialized)
```

## Next Documentation Tasks

1. **Create Tool System Documentation**: Document the new tool system architecture, standards, and integration patterns
2. **Develop Agent Messaging Docs**: Document the structured messaging system for agent communication
3. **Update Workflow Documentation**: Enhance existing workflow docs with new orchestration capabilities

## Documentation Review Process

To maintain high-quality documentation, all documentation changes go through the following review process:

1. **Technical Accuracy Review**
   - Verification of technical content by subject matter experts
   - Validation of code examples and functionality descriptions
   - Confirmation of API references and parameter descriptions

2. **Usability and Clarity Review**
   - Assessment of readability and understandability
   - Evaluation of organization and structure
   - Review of examples for practicality and relevance

3. **Consistency and Standards Review**
   - Verification of adherence to documentation standards
   - Check for consistent terminology and formatting
   - Validation of proper cross-referencing and linking

4. **Final Integration Review**
   - Verification of proper placement within documentation structure
   - Check for seamless integration with existing content
   - Validation of navigation and discovery paths