# Atlas Documentation Planning

This document outlines the planning and tracking system for Atlas documentation, including the documentation structure, completed tasks, and ongoing plans for documentation improvement.

## Current Implementation Status

```
✅ Completed documentation     (59 files)
🔄 Updated documentation      (3 files - OpenAI provider, Anthropic provider, streaming example)
✅ All documentation updates complete
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
│   └── models/               # Model providers ✅
│       ├── anthropic.md      # Anthropic integration ✅
│       ├── index.md          # Models section index/overview ✅
│       ├── ollama.md         # Ollama integration ✅
│       └── openai.md         # OpenAI integration ✅
├── guides/                   # Developer guides ✅
│   ├── configuration.md      # Configuration guide ✅
│   ├── examples/             # Code examples ✅
│   │   ├── advanced_examples.md  # Advanced usage patterns ✅
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
    └── retrieval.md          # Retrieval workflow ✅
```

## Completed Documentation Tasks

- [x] Core system components (config, env, errors, prompts)
- [x] Knowledge system (overview, ingestion, retrieval)
- [x] Graph system (state, nodes, edges)  
- [x] Model providers (base, anthropic, openai, ollama)
- [x] Workflow documentation (query, retrieval, multi-agent)
- [x] User guides (getting started, configuration, testing)
- [x] Reference documentation (API, CLI, env variables)

## Recent Implementation Changes

- [x] **Provider Implementations**
  - OpenAI and Ollama providers with streaming support
  - Token usage tracking and cost calculation
  - Enhanced error handling and API key validation
  - Updated pricing for all providers

- [x] **Token Usage System**
  - TokenUsage and CostEstimate classes with to_dict() methods
  - Cost formatting with precision based on magnitude
  - Provider-specific cost calculation implementations
  - Comprehensive token tracking tests

- [x] **Streaming Functionality**
  - Stream handler implementation for all providers
  - Callback-based streaming for interactive UIs
  - Token and cost tracking during streaming
  - Command-line argument support in examples

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

### Provider Implementation Updates

1. **Update Model Provider Documentation**
   - [x] Update pricing information to match latest implementations (high priority)
     - [x] Update OpenAI pricing in openai.md with GPT-4.1, GPT-4.1-mini, and GPT-4.1-nano models
     - [x] Update GPT-4o pricing from $15.00/M to $20.00/M for output tokens
     - [x] Add o-series models (o3, o4-mini) documentation and pricing
     - [x] Update Anthropic pricing with Claude 3.5 Haiku ($0.80/M input, $4.0/M output)
   - [x] Update model lists and defaults in provider documentation
     - [x] Change OpenAI default model from GPT-4o to GPT-4.1 in examples
     - [x] Add GPT-4o-mini to model list and examples
     - [x] Add Claude 3.5 Haiku to Anthropic model list and examples
   - [x] Update code examples to use latest models and APIs
     - [x] Update streaming examples with latest implementation patterns
     - [x] Add command-line argument documentation for streaming_example.py
     - [x] Include token tracking and cost calculation examples

2. **Update Token Usage Documentation**
   - [x] Document the TokenUsage class and to_dict() method (OpenAI provider)
   - [x] Document the CostEstimate class and to_dict() method (OpenAI provider)
   - [x] Add examples of token usage tracking across different providers (OpenAI example)
   - [x] Document cost estimation formatting for different magnitudes
   - [x] Add troubleshooting section for token tracking issues

3. **Update Streaming Documentation**
   - [x] Add multi-provider streaming examples
   - [x] Document the streaming_example.py command-line interface
   - [x] Add token tracking during streaming examples
   - [x] Update stream_with_callback documentation with latest patterns
   - [x] Document streaming error handling and recovery strategies

4. **Testing Documentation Updates**
   - [ ] Document mock provider usage for testing without API keys
   - [ ] Document token usage testing patterns and tools
   - [ ] Add examples of testing streaming functionality
   - [ ] Document the token_usage test module structure and usage
   - [ ] Add troubleshooting guide for common testing issues

## Future Documentation Enhancements

1. **Interactive Documentation**
   - Add interactive code examples and playgrounds
   - Create interactive diagrams for complex concepts
   - Implement live API testing capabilities

2. **Visual Enhancements**
   - Add more diagrams and visual representations
   - Create workflow visualizations for common patterns
   - Implement consistent visual design system

3. **User Experience Improvements**
   - Enhance search functionality for documentation
   - Implement difficulty level indicators for different sections
   - Create guided learning paths for different user types

4. **Content Expansion**
   - Add more practical examples and use cases
   - Create troubleshooting guides and FAQs
   - Develop case studies of real-world implementations
   - Add performance benchmarks and optimization guides

5. **Community Integration**
   - Add contributor guidelines and documentation standards
   - Implement feedback mechanisms for documentation
   - Create community contribution process for examples

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