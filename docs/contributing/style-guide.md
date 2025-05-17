---
title: Writing Style
---

# Writing Style Guide

This style guide establishes consistent writing standards across Atlas documentation. Following these guidelines ensures our documentation maintains a cohesive voice and delivers information effectively.

## Voice and Tone

### Core Attributes

Atlas documentation maintains these attributes:

- **Clear**: Straightforward, unambiguous language
- **Confident**: Authoritative without being dogmatic
- **Conversational**: Natural, human-readable language
- **Practical**: Focused on real-world application
- **Respectful**: Assumes reader competence without condescension

### Person and Point of View

- Use **second person** ("you") to address the reader directly
- Use **first person plural** ("we") when referring to the Atlas development team
- Avoid first person singular ("I") in documentation

### Examples

| ✅ Preferred                                                          | ❌ Avoid                                                                  |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| You can configure the provider using environment variables.          | The user can configure the provider using environment variables.         |
| We recommend using provider groups for production deployments.       | I recommend using provider groups for production deployments.            |
| Atlas handles all model interactions through the provider interface. | Atlas will handle all model interactions through the provider interface. |

## Language and Style

### Active Voice

Use active voice for clarity and directness:

| ✅ Active Voice                                         | ❌ Passive Voice                                          |
| ------------------------------------------------------ | -------------------------------------------------------- |
| The provider sends the request to the API.             | The request is sent to the API by the provider.          |
| You should configure API keys before using providers.  | API keys should be configured before providers are used. |
| Atlas generates responses using the selected provider. | Responses are generated using the selected provider.     |

### Present Tense

Use present tense for most documentation:

| ✅ Present Tense                            | ❌ Other Tenses                                 |
| ------------------------------------------ | ---------------------------------------------- |
| The provider returns a response object.    | The provider will return a response object.    |
| This method processes the input text.      | This method will process the input text.       |
| The agent communicates with worker agents. | The agent has communicated with worker agents. |

### Clarity and Conciseness

- Use simple, direct language
- Avoid unnecessary words
- Break long sentences into shorter ones
- Use specific, concrete terms over vague ones

| ✅ Clear and Concise                                         | ❌ Wordy or Vague                                                                                                                                      |
| ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Configure the provider with your API key.                   | It is necessary for you to undertake the task of configuring the provider with your specific API key credentials.                                     |
| Atlas retrieves relevant documents from the knowledge base. | Atlas utilizes various methodologies to engage in the process of retrieving documents that may be considered relevant from the knowledge base system. |
| Set `max_tokens` to limit response length.                  | In the event that you wish to impose limitations on the length of responses, you can proceed to set the `max_tokens` parameter.                       |

## Terminology Standards

### Consistent Terms

Use consistent terminology throughout documentation:

| Term           | Definition                               | Notes                                 |
| -------------- | ---------------------------------------- | ------------------------------------- |
| Provider       | Implementation of an LLM API integration | Not "model", "backend", or "service"  |
| Agent          | AI entity that performs tasks            | Not "assistant", "bot", or "AI"       |
| Generate       | Create model output                      | Not "predict", "create", or "produce" |
| Knowledge Base | Stored embeddings and document content   | Not "database", "store", or "index"   |
| Retrieve       | Find relevant documents                  | Not "search", "query", or "lookup"    |

### Technical Accuracy

- Use precise technical terms correctly
- Define specialized terms on first use
- Maintain consistent capitalization of product names

### Abbreviations and Acronyms

- Spell out abbreviations on first use with acronym in parentheses
- Use commonly understood abbreviations without explanation (API, JSON)
- Avoid creating new abbreviations

## Formatting Conventions

### Text Formatting

| Element         | Formatting            | Example                                                    |
| --------------- | --------------------- | ---------------------------------------------------------- |
| Code            | Backticks             | Use `AnthropicProvider` for Claude models.                 |
| File paths      | Backticks             | Save the file to `/path/to/atlas/config.yaml`.             |
| Commands        | Backticks             | Run `python -m atlas` to start the CLI.                    |
| UI elements     | Bold                  | Click the **Generate** button.                             |
| Emphasis        | Italic                | This is *required* for all deployments.                    |
| Book/doc titles | Italic                | Refer to the *Atlas API Reference*.                        |
| New terms       | Bold on first mention | **Vector embeddings** represent text as numerical vectors. |

### Lists

- Use bulleted lists for unordered items
- Use numbered lists for sequential steps
- Keep list items parallel in structure
- Capitalize the first word of each list item
- Use semicolons for complex list items and periods for complete sentences

### Links

- Use descriptive link text that makes sense out of context
- Avoid generic phrases like "click here" or "read more"
- Use relative links for internal documentation
- Include the full URL for external resources when appropriate

| ✅ Good Link Text                                                                      | ❌ Poor Link Text                                        |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| See the [Provider Configuration Guide](../v2/nerv/patterns/index.md) for details.     | Click [here](../v2/nerv/patterns/index.md) for details. |
| Learn about [Streaming in the Inner Universe](../v2/inner-universe/implementation.md) | [Read more](#).                                         |

## Content Structure

### Headings

- Use sentence case for headings (capitalize only the first word and proper nouns)
- Make headings descriptive and concise
- Maintain a logical heading hierarchy (H1 > H2 > H3)
- Avoid skipping heading levels

### Paragraphs

- Keep paragraphs focused on a single idea
- Limit paragraphs to 3-5 sentences
- Use transitional phrases between paragraphs
- Start with the most important information

### Code Blocks

- Add language identifiers to code blocks
- Keep examples concise and focused
- Use comments to explain complex operations
- Follow the [Code Examples Standards](./code-examples.md)

## Atlas-Specific Conventions

### Feature References

- Use exact feature names as they appear in the API
- Capitalize proper product names (Atlas, Anthropic, OpenAI)
- Use lowercase for general concepts (providers, agents, knowledge base)

### Version References

- Use version numbers when discussing version-specific features
- Format versions consistently as X.Y.Z (e.g., 1.0.0)
- Note when features were introduced or deprecated

### Environment References

- Use the exact environment variable names
- Format environment variables in all caps with underscores
- Note default values when referencing configuration options

## Inclusive Language

### Gender-Neutral Language

- Use gender-neutral terms (they/them/their) or plurals
- Avoid gendered terms like "guys," "mankind," or "manpower"
- Use role descriptions rather than gendered terms

| ✅ Inclusive                                    | ❌ Non-inclusive                                   |
| ---------------------------------------------- | ------------------------------------------------- |
| The developer can configure their environment. | The developer can configure his environment.      |
| Team members should update their API keys.     | Each programmer should update his or her API key. |
| Staff, team, workforce                         | Manpower                                          |

### Cultural Sensitivity

- Avoid culturally specific metaphors or idioms
- Use examples that work across cultures
- Be mindful of regional differences in technical terminology

### Accessibility-Aware Language

- Focus on people, not disabilities
- Avoid ableist terms and metaphors
- Use neutral, respectful terminology

| ✅ Preferred                            | ❌ Avoid      |
| -------------------------------------- | ------------ |
| Users who navigate with screen readers | Blind users  |
| Verify or check                        | Sanity check |
| Easy to use                            | Dummy-proof  |

## Documentation Review Checklist

Before submitting documentation, verify:

1. **Accuracy**: Information is technically correct
2. **Clarity**: Language is clear and unambiguous
3. **Consistency**: Terminology and formatting are consistent
4. **Completeness**: All necessary information is included
5. **Style Compliance**: Content follows this style guide
6. **Inclusivity**: Language is respectful and inclusive
7. **Examples**: Code examples follow standards and work correctly
8. **Links**: All links point to correct destinations

## Examples of Atlas Documentation Style

### Conceptual Explanation Example

```md
# Provider System

The provider system manages interactions with language model APIs. Each provider implements a standard interface, allowing Atlas to work with multiple AI services seamlessly.

Atlas supports these provider types:

- **AnthropicProvider**: Integrates with Claude models
- **OpenAIProvider**: Connects to GPT models
- **OllamaProvider**: Works with locally hosted models
- **MockProvider**: Simulates responses for testing

You can configure providers using environment variables or explicit parameters:

```python
from atlas.providers import AnthropicProvider

# Configure with environment variables
provider = AnthropicProvider()

# Or with explicit parameters
provider = AnthropicProvider(
    model_name="claude-3-7-sonnet-20250219",
    max_tokens=2000
)
```

When designing systems with multiple model options, consider implementing provider groups for enhanced reliability.
```

### Procedural Guide Example

```md
# Setting Up Environment Variables

Before using Atlas with external providers, you need to configure API keys as environment variables.

## Required Environment Variables

Different providers require specific environment variables:

- **Anthropic**: `ANTHROPIC_API_KEY`
- **OpenAI**: `OPENAI_API_KEY`
- **Ollama**: `OLLAMA_BASE_URL` (defaults to http://localhost:11434)

## Configuration Steps

1. Obtain API keys from the respective provider portals.
2. Set environment variables in your system.
3. Verify configuration using the diagnostics tool.

### Setting Environment Variables

```bash
# On Linux/macOS
export ANTHROPIC_API_KEY="your-api-key"

# On Windows (CMD)
set ANTHROPIC_API_KEY=your-api-key

# On Windows (PowerShell)
$env:ANTHROPIC_API_KEY="your-api-key"
```

### Verifying Configuration

Run the configuration check script to verify your environment:

```bash
python -m atlas.scripts.debug.check_config
```

This displays all detected configuration values and highlights any missing required variables.
```

By following these style guidelines, we maintain a consistent, professional voice throughout Atlas documentation, enhancing readability and user comprehension.
