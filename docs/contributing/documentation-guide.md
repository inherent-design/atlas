---
title: Documentation Guide
---

# Documentation Guide

This comprehensive guide outlines standards and best practices for creating high-quality documentation for the Atlas project. It covers writing standards, content structure, visual elements, and specific VitePress features.

## Documentation Standards

### Document Structure

#### Required Sections

Every documentation page should include:

1. **Title**: Clear, descriptive H1 heading
2. **Introduction**: Brief overview of the topic (1-3 sentences)
3. **Body**: Detailed content organized by headings
4. **Related Information**: Links to related documentation (when applicable)

#### Optional Sections

Depending on the content type, consider including:

- **Prerequisites**: Requirements before using the feature
- **Examples**: Practical code examples demonstrating usage
- **Troubleshooting**: Common issues and solutions
- **API Reference**: Method signatures and parameter details
- **Implementation Notes**: Technical details for developers

### Content Organization

#### Heading Hierarchy

- Use clear, descriptive headings that follow a logical hierarchy
- Maintain a consistent heading structure throughout your document
- Avoid skipping heading levels (e.g., don't go from H2 to H4)
- Keep headings concise (typically under 80 characters)

#### Perspective Fluidity

Our documentation follows the Trimodal Methodology Framework, combining three perspectives:

1. **Top-Down Design**: Start with the conceptual overview
2. **Bottom-Up Implementation**: Provide concrete details and examples
3. **Holistic Integration**: Explain how components work together

Structure your documentation to flow between these perspectives as appropriate, signaling transitions clearly.

#### Progressive Disclosure

Present information in order of importance:

1. Essential concepts first
2. Common usage patterns next
3. Advanced features and edge cases last

This allows readers to gain useful knowledge quickly while providing paths to deeper understanding.

### Content Flow and Engagement

#### Narrative Techniques

Maintain engagement through:

- **Question Headings**: Frame sections as answers to questions
- **Problem-Solution Format**: Present common challenges and their solutions
- **Scenario-Based Examples**: Show features in realistic contexts
- **Compare and Contrast**: Highlight differences between related concepts

#### Chunking Information

- Break content into digestible sections
- Group related information under appropriate headings
- Use lists and tables for structured information
- Limit paragraphs to 3-5 sentences

## Writing Style

### Voice and Tone

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

### Active Voice and Present Tense

Use active voice for clarity and directness:

| ✅ Active Voice                                         | ❌ Passive Voice                                          |
| ------------------------------------------------------ | -------------------------------------------------------- |
| The provider sends the request to the API.             | The request is sent to the API by the provider.          |
| You should configure API keys before using providers.  | API keys should be configured before providers are used. |

Use present tense for most documentation:

| ✅ Present Tense                            | ❌ Other Tenses                                 |
| ------------------------------------------ | ---------------------------------------------- |
| The provider returns a response object.    | The provider will return a response object.    |
| This method processes the input text.      | This method will process the input text.       |

### Clarity and Conciseness

- Use simple, direct language
- Avoid unnecessary words
- Break long sentences into shorter ones
- Use specific, concrete terms over vague ones

### Terminology Standards

Use consistent terminology throughout documentation:

| Term           | Definition                               | Notes                                 |
| -------------- | ---------------------------------------- | ------------------------------------- |
| Provider       | Implementation of an LLM API integration | Not "model", "backend", or "service"  |
| Agent          | AI entity that performs tasks            | Not "assistant", "bot", or "AI"       |
| Generate       | Create model output                      | Not "predict", "create", or "produce" |
| Knowledge Base | Stored embeddings and document content   | Not "database", "store", or "index"   |
| Retrieve       | Find relevant documents                  | Not "search", "query", or "lookup"    |

### Inclusive Language

#### Gender-Neutral Language

- Use gender-neutral terms (they/them/their) or plurals
- Avoid gendered terms like "guys," "mankind," or "manpower"
- Use role descriptions rather than gendered terms

#### Cultural Sensitivity

- Avoid culturally specific metaphors or idioms
- Use examples that work across cultures
- Be mindful of regional differences in technical terminology

#### Accessibility-Aware Language

- Focus on people, not disabilities
- Avoid ableist terms and metaphors
- Use neutral, respectful terminology

## Custom Containers

VitePress provides custom containers that help highlight and organize content. Use these strategically to enhance documentation clarity.

### Available Containers

1. **Info** (ℹ️): For neutral information and general notes
2. **Tip** (💡): For best practices, helpful advice, and efficiency gains
3. **Warning** (⚠️): For potential pitfalls, version compatibility issues, or important cautions
4. **Danger** (🔥): For critical warnings about breaking changes, security risks, or data loss potentials
5. **Details** (▶️): For collapsible content containing additional information or verbose examples

### Container Syntax

The basic syntax for VitePress custom containers is:

```md
::: [container-type] [optional title]
Content goes here
:::
```

### Container Usage Guidelines

#### General Guidelines

- Limit pages to 2-3 containers for standard pages
- Space containers throughout the document (avoid clustering)
- Never nest containers within each other
- Keep container content concise (typically 1-3 paragraphs)

#### Info Container

::: info When to Use Info Containers
Use info containers for general notes and neutral information that users should be aware of.
:::

**Appropriate Content:**
- General information about features or components
- Clarifications or additional context
- Notes about limitations or requirements

**Example:**
```md
::: info Provider Configuration
All providers require configuration before use. See the provider-specific documentation for details on required parameters.
:::
```

#### Tip Container

::: tip When to Use Tip Containers
Use tip containers for best practices, efficiency improvements, and helpful shortcuts that enhance the user experience.
:::

**Appropriate Content:**
- Best practices and recommended approaches
- Performance optimizations
- Alternative approaches that might be simpler in certain contexts

#### Warning Container

::: warning When to Use Warning Containers
Use warning containers for important cautions that users should be aware of before proceeding.
:::

**Appropriate Content:**
- Potential pitfalls in implementation
- Version compatibility issues
- Performance implications
- Deprecation notices

#### Danger Container

::: danger When to Use Danger Containers
Use danger containers ONLY for critical warnings that could result in security vulnerabilities, data loss, or breaking changes.
:::

**Appropriate Content:**
- Security vulnerabilities
- Potential data loss scenarios
- Breaking changes that require significant migration effort
- Authentication and authorization risks

#### Details Container

::: details When to Use Details Containers
Use details containers for additional information that might be useful but isn't essential for understanding the main content.
:::

**Appropriate Content:**
- Verbose code examples
- In-depth explanations of complex concepts
- Alternative implementation approaches
- Advanced configuration options

### Container with Custom Title

```md
::: tip BEST PRACTICE
This is a tip with a custom title.
:::
```

### Details Container with Attributes

```md
::: details Click me to see more {open}
This content is expanded by default.
:::
```

## Timeline Components

The Atlas documentation uses the VitePress Markdown Timeline component to visualize chronological sequences and processes.

### When to Use Timelines

::: warning Limited Application
Timelines should be used sparingly throughout the documentation as they add significant visual weight and computational overhead.
:::

#### Appropriate Use Cases

- **Chronological Development**: Showing project evolution over time
- **Release Planning**: Visualizing upcoming release schedules
- **Complex Workflows**: Illustrating multi-step processes with timing considerations
- **Implementation Phases**: Showing phase transitions with key deliverables
- **Historical Context**: Providing background on major changes or decisions

#### Inappropriate Use Cases

- Simple sequential steps that don't have a strong temporal component
- Feature comparisons or option descriptions
- API documentation or method signatures
- Navigation or table of contents replacements

### Timeline Syntax

::: warning Important Syntax Concept
Each `::: timeline <date/label>` block represents **one event** in a timeline. Sequential timeline blocks automatically combine to form a **single timeline** with multiple events.
:::

The basic syntax for each timeline event is:

```md
::: timeline [Date or Event Label]
- **[Optional Bold Items]**: Important details
- Additional bullet points
- More information
:::
```

### Timeline Implementation Examples

#### Product Roadmap Timeline

```md
::: timeline April 2025
- **Project Inception**: Initial architecture design and project planning
- System architecture definition
- Component interaction patterns
:::

::: timeline May 10-17, 2025
- **Provider System Enhancement**: Implementation of enhanced streaming infrastructure
- Streaming controls implementation
- Provider lifecycle management
:::

::: timeline May 18-24, 2025
- **Agent-Provider Integration**: Optimized agent-provider interface
- Agent streaming controls
- Provider capability utilization
:::
```

This creates ONE timeline with THREE events.

### Timeline Design Guidelines

1. **Entry Conciseness**: Keep entries brief (1-2 sentences per node)
2. **Consistent Format**: Maintain parallel structure across entries
3. **Timeline Length**: Limit timelines to 5-12 entries for readability
4. **Visual Balance**: Space primary/highlighted entries throughout the timeline

## Visual Elements and Formatting

### Text Formatting

| Element         | Formatting            | Example                                                    |
| --------------- | --------------------- | ---------------------------------------------------------- |
| Code            | Backticks             | Use `AnthropicProvider` for Claude models.                 |
| File paths      | Backticks             | Save the file to `/path/to/atlas/config.yaml`.             |
| Commands        | Backticks             | Run `python -m atlas` to start the CLI.                    |
| UI elements     | Bold                  | Click the **Generate** button.                             |
| Emphasis        | Italic                | This is *required* for all deployments.                    |
| New terms       | Bold on first mention | **Vector embeddings** represent text as numerical vectors. |

### Lists

- Use bulleted lists for unordered items
- Use numbered lists for sequential steps
- Keep list items parallel in structure
- Capitalize the first word of each list item
- Use semicolons for complex list items and periods for complete sentences

### Tables

- Use tables for structured, comparable information
- Include clear column headers
- Maintain consistent formatting within tables
- Provide context or introduction before tables

### Links

- Use descriptive link text that makes sense out of context
- Avoid generic phrases like "click here" or "read more"
- Use relative links for internal documentation
- Include the full URL for external resources when appropriate

### Images and Diagrams

- Include diagrams for complex systems or workflows
- Use consistent visual styles across diagrams
- Provide alt text for accessibility
- Keep diagrams simple and focused on key concepts
- Crop images to focus on relevant details
- Optimize image sizes for web viewing

## Content Quality Checklist

Before submitting documentation, verify:

1. **Accuracy**: Information is technically correct
2. **Clarity**: Language is clear and unambiguous
3. **Consistency**: Terminology and formatting are consistent
4. **Completeness**: All necessary information is included
5. **Style Compliance**: Content follows this style guide
6. **Inclusivity**: Language is respectful and inclusive
7. **Examples**: Code examples follow standards and work correctly
8. **Links**: All links point to correct destinations
9. **Visual Balance**: Containers and visual elements are used appropriately
10. **Accessibility**: Content is accessible to all users

## Example Documentation Structure

Here's an example structure for a component documentation page:

```md
# Component Name

Brief introduction to the component and its purpose.

## Overview

Conceptual explanation of what the component does and why it exists.

::: tip Best Practice
Include a tip for optimal usage of this component.
:::

## Basic Usage

```python
# Simple example code
```

Step-by-step explanation of the basic usage pattern.

## Key Features

### Feature One

Explanation and examples of feature one.

### Feature Two

Explanation and examples of feature two.

::: warning Compatibility
Note any compatibility considerations for this feature.
:::

## Advanced Usage

More complex examples and usage patterns.

::: details Advanced Configuration Example
```python
# Detailed implementation example
```
:::

## API Reference

Detailed method signatures and parameter descriptions.

## Related Components

Links to related documentation.
```

By following this comprehensive documentation guide, you'll create clear, consistent, and helpful documentation that enhances the Atlas user experience while maintaining high quality standards across all content.