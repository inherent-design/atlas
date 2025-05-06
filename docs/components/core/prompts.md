# Prompt System

This document describes the prompt management system in Atlas, which handles the loading, customization, and usage of system prompts across different agents.

## Overview

The prompt system in Atlas provides:

1. **Default System Prompts**: Pre-defined prompts that establish the Atlas identity and capabilities
2. **Custom Prompt Loading**: Ability to load custom prompts from files
3. **Error Handling**: Graceful fallback to defaults if custom prompts cannot be loaded
4. **Prompt Augmentation**: Runtime enhancement of prompts with knowledge context
5. **Integration with Agents**: Seamless use across different agent types

The prompt system is designed to:

- **Maintain Consistency**: Ensure all agents maintain the Atlas identity
- **Allow Customization**: Support specialized prompts for different agent roles
- **Handle Failures Gracefully**: Provide fallback mechanisms when errors occur
- **Support Dynamic Content**: Enable context-specific prompt enhancement

## Core Components

### Default System Prompt

The `DEFAULT_SYSTEM_PROMPT` constant defines the standard Atlas identity and behavior:

```python
from atlas.core.prompts import DEFAULT_SYSTEM_PROMPT

# The default system prompt includes:
# - Atlas identity definition
# - Knowledge context description
# - Capabilities outline
# - Approach guidelines
# - Important behavioral instructions
```

The default prompt establishes Atlas as a guide focused on organic and adaptive learning, helping users explore ideas and solve problems through collaborative conversation.

### Prompt Loading Function

The `load_system_prompt` function handles loading system prompts:

```python
from atlas.core.prompts import load_system_prompt

# Load default prompt
system_prompt = load_system_prompt()

# Load custom prompt from file
custom_prompt = load_system_prompt("/path/to/custom_prompt.md")
```

#### Parameters

| Parameter   | Type            | Description                                  |
| ----------- | --------------- | -------------------------------------------- |
| `file_path` | `Optional[str]` | Optional path to a custom system prompt file |

#### Returns

- `str`: The loaded prompt text (either custom or default)

#### Behavior

1. If no file path is provided, returns the default prompt
2. If a file path is provided:
   - Checks if the file exists (falls back to default if not)
   - Attempts to read the file content
   - Validates that the file is not empty
   - Returns the custom prompt if successful
   - Falls back to the default prompt if any errors occur

#### Error Handling

The function uses `safe_execute` to capture and handle errors:

```python
# Safe execution with graceful fallback
custom_prompt = safe_execute(
    read_prompt_file,
    default=DEFAULT_SYSTEM_PROMPT,
    error_msg=f"Failed to read system prompt from {file_path}",
    error_cls=ConfigurationError,
    log_error=True,
)
```

If the file cannot be read or is empty, appropriate error messages are logged, and the default prompt is used instead.

## Integration with Agents

### Base Agent Integration

The prompt system is integrated with the `AtlasAgent` class:

```python
from atlas.agents.base import AtlasAgent

# Create agent with default prompt
agent = AtlasAgent()

# Create agent with custom prompt
agent = AtlasAgent(system_prompt_file="/path/to/custom_prompt.md")
```

During agent initialization, the prompt is loaded:

```python
def __init__(self, system_prompt_file: Optional[str] = None, ...):
    # Load the system prompt
    self.system_prompt = load_system_prompt(system_prompt_file)
    ...
```

### Dynamic Prompt Enhancement

In the process_message methods, the default prompt is enhanced with retrieved knowledge:

```python
# Create system message with context
system_msg = self.system_prompt
if documents:
    context_text = self.format_knowledge_context(documents)
    system_msg = system_msg + context_text
```

The enhanced prompt includes:

1. The base system prompt (default or custom)
2. A "Relevant Knowledge" section with retrieved documents
3. Document metadata including source information

This enriched prompt provides the model with context-specific information for generating more informed responses.

## Custom Prompt Creation

### Custom Prompt Format

Custom prompts should follow these guidelines:

1. **Identity Definition**: Clearly establish the Atlas identity
2. **Capabilities Description**: Outline what Atlas can do
3. **Behavioral Guidelines**: Specify how Atlas should interact with users
4. **Knowledge Framework**: Reference to knowledge resources
5. **Interaction Patterns**: Define conversational approach

Example custom prompt structure:

```markdown
# Atlas: [Specialized Role]

You are Atlas, [specialized role description].

## Your Knowledge Context

[Description of specialized knowledge areas]

## Your Capabilities

1. [Capability 1]
2. [Capability 2]
...

## Your Approach

[Interaction guidelines and approach]

## Important Guidelines

- [Guideline 1]
- [Guideline 2]
...
```

### Specialization Examples

Custom prompts can be created for specific agent roles:

**Retrieval Worker Prompt:**
```markdown
# Atlas: Knowledge Retrieval Specialist

You are Atlas, specialized in knowledge retrieval and document analysis.

## Your Knowledge Context

You have access to a rich knowledge base containing project documentation.

## Your Capabilities

1. Analyze user queries to identify key information needs
2. Retrieve the most relevant documents from the knowledge base
3. Extract and synthesize information across multiple documents
4. Identify connections between different information sources
5. Provide concise summaries of retrieved information

## Your Approach

1. Carefully analyze the query to understand the true information need
2. Use semantic search to identify the most relevant documents
3. Extract key information from each document
4. Synthesize information across documents to create a comprehensive answer
5. Present information in a clear, structured format

## Important Guidelines

- Focus on relevance and accuracy of retrieved information
- Maintain factual consistency across documents
- Acknowledge when information might be incomplete or uncertain
- Always provide source attribution for retrieved information
- Never identify yourself as an AI or language model
```

## CLI Integration

The prompt system is integrated with the Atlas CLI:

```
python main.py -s /path/to/custom_prompt.md
```

The CLI parser includes a `--system-prompt` argument:

```python
parser.add_argument(
    "-s", "--system-prompt", type=str, help="Path to system prompt file"
)
```

This allows users to easily specify custom prompts when launching Atlas in any mode.

## Prompt Management Best Practices

1. **Use Version Control**: Store custom prompts in version control to track changes
   ```bash
   # Example directory structure
   prompts/
   ├── base.md             # Base Atlas prompt
   ├── retrieval_worker.md # Specialized for retrieval
   ├── analysis_worker.md  # Specialized for analysis
   └── draft_worker.md     # Specialized for drafting
   ```

2. **Maintain Identity Consistency**: Always preserve the core Atlas identity
   ```markdown
   # Always include in custom prompts
   You are Atlas, an AI guide dedicated to organic and adaptive learning...

   # Never include phrases like
   You are an AI assistant...
   ```

3. **Test Custom Prompts**: Verify behavior before deploying
   ```bash
   # Test a custom prompt
   python main.py -m query -s /path/to/test_prompt.md -q "Test query"
   ```

4. **Document Prompt Purpose**: Include metadata in prompt files
   ```markdown
   <!--
   Prompt: Analysis Worker
   Version: 1.2
   Last Updated: 2025-04-01
   Purpose: Specialized in deep analysis of user queries and content
   -->

   # Atlas: Analysis Specialist
   ...
   ```

5. **Incremental Changes**: Make small, focused changes to prompts
   ```markdown
   <!--
   Changes from v1.1:
   - Enhanced query refinement capabilities
   - Added guidance for handling ambiguous queries
   - Improved instruction for source citation
   -->
   ```

## Example: Creating a Custom Agent with Custom Prompt

```python
from atlas.agents.base import AtlasAgent
from atlas.core.config import AtlasConfig

# Define configuration
config = AtlasConfig(
    model_name="claude-3-opus-20240229",
    max_tokens=4000
)

# Create agent with custom prompt
agent = AtlasAgent(
    system_prompt_file="prompts/research_assistant.md",
    config=config,
    provider_name="anthropic"
)

# Process messages with enhanced research capabilities
response = agent.process_message("Analyze the impact of distributed ledger technology on supply chain management")
```

## Integration with Multi-Agent Systems

In multi-agent orchestration, different agents can use specialized prompts:

```python
from atlas.orchestration.coordinator import AgentCoordinator
from atlas.agents.worker import RetrievalWorker, AnalysisWorker, DraftWorker

# Create coordinator with base prompt
coordinator = AgentCoordinator(system_prompt_file="prompts/coordinator.md")

# Create specialized workers with different prompts
retrieval_worker = RetrievalWorker(system_prompt_file="prompts/retrieval.md")
analysis_worker = AnalysisWorker(system_prompt_file="prompts/analysis.md")
draft_worker = DraftWorker(system_prompt_file="prompts/drafting.md")
```

This approach allows each agent to have specialized instructions while maintaining a coherent system.

## Related Documentation

- [Agents Documentation](../../components/agents/controller.md) - Information about agent types and interactions
- [Configuration System](config.md) - Documentation for the configuration system
- [Model Providers](../models/) - Documentation for model providers
- [Error System](errors.md) - Information about error handling
