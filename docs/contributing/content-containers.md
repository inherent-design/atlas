---
title: Custom Container
---

# Custom Container Usage Guide

VitePress provides custom containers that help highlight and organize content. This guide outlines when and how to use these containers in Atlas documentation.

## Available Containers

VitePress supports these built-in custom containers:

1. **Info** (ℹ️): For neutral information and general notes
2. **Tip** (💡): For best practices, helpful advice, and efficiency gains
3. **Warning** (⚠️): For potential pitfalls, version compatibility issues, or important cautions
4. **Danger** (🔥): For critical warnings about breaking changes, security risks, or data loss potentials
5. **Details** (▶️): For collapsible content containing additional information or verbose examples

VitePress also supports [GitHub-flavored alerts](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#alerts) with the following types:
- **NOTE**: Highlights information users should consider, even when skimming
- **TIP**: Optional information to help users be more successful
- **IMPORTANT**: Crucial information necessary for users to succeed
- **WARNING**: Critical content demanding immediate user attention due to potential risks
- **CAUTION**: Negative potential consequences of an action

## General Guidelines

### When to Use Containers

Custom containers should be used strategically to:

- Highlight information that requires visual separation from main content
- Call attention to critical information that might otherwise be missed
- Provide supplementary details that not all readers need

### Container Limits

To avoid visual overload:

- Limit pages to 2-3 containers for standard pages
- Space containers throughout the document (avoid clustering)
- Never nest containers within each other
- Keep container content concise (typically 1-3 paragraphs)

## Container Syntax

### Basic Container Syntax

The basic syntax for VitePress custom containers is:

```md
::: [container-type] [optional title]
Content goes here
:::
```

Available container types are: `info`, `tip`, `warning`, `danger`, and `details`.

### Container with Custom Title

You can specify a custom title for any container:

```md
::: tip BEST PRACTICE
This is a tip with a custom title.
:::
```

### Details Container with Attributes

The details container supports the `open` attribute to make it expanded by default:

```md
::: details Click me to see more {open}
This content is expanded by default.
:::
```

### GitHub-Flavored Alert Syntax

GitHub-flavored alerts use a different syntax:

```md
> [!NOTE]
> This is a note using GitHub-flavored alert syntax.

> [!WARNING]
> This is a warning using GitHub-flavored alert syntax.
```

## Container-Specific Guidelines

### Info Container

::: info When to Use Info Containers
Use info containers for general notes and neutral information that users should be aware of.
:::

**Appropriate Content:**
- General information about features or components
- Clarifications or additional context
- Notes about limitations or requirements
- General explanations that need visual emphasis

**Example:**
```md
::: info Provider Configuration
All providers require configuration before use. See the provider-specific documentation for details on required parameters.
:::
```

### Tip Container

::: tip When to Use Tip Containers
Use tip containers for best practices, efficiency improvements, and helpful shortcuts that enhance the user experience but aren't essential for basic functionality.
:::

**Appropriate Content:**
- Best practices and recommended approaches
- Performance optimizations
- Keyboard shortcuts and time-saving techniques
- Alternative approaches that might be simpler in certain contexts

**Example:**
```md
::: tip Provider Selection Strategy
For production deployments, we recommend using provider groups with the failover strategy to ensure resilience against API failures.
:::
```

### Warning Container

::: warning When to Use Warning Containers
Use warning containers for important cautions that users should be aware of before proceeding, but that don't represent critical dangers.
:::

**Appropriate Content:**
- Potential pitfalls in implementation
- Version compatibility issues
- Performance implications
- Common mistakes and how to avoid them
- Deprecation notices

**Example:**
```md
::: warning Provider Compatibility
The enhanced streaming interface is not backward compatible with Atlas versions prior to 0.5. If you need to maintain compatibility, use the standard streaming approach.
:::
```

### Danger Container

::: danger When to Use Danger Containers
Use danger containers ONLY for critical warnings that could result in security vulnerabilities, data loss, or breaking changes that significantly impact systems.
:::

**Appropriate Content:**
- Security vulnerabilities
- Potential data loss scenarios
- Breaking changes that require significant migration effort
- Operations that can't be undone
- Authentication and authorization risks

**Example:**
```md
::: danger API Key Security
Never store API keys directly in your configuration files or commit them to version control. Use environment variables or secure vaults as described in the security guide.
:::
```

### Details Container

::: details When to Use Details Containers
Use details containers for additional information that might be useful but isn't essential for understanding the main content. These are collapsible by default.
:::

**Appropriate Content:**
- Verbose code examples
- In-depth explanations of complex concepts
- Alternative implementation approaches
- Historical context or background information
- Advanced configuration options

**Example:**
```md
::: details Advanced Configuration Example
```python
# This example shows complex configuration with annotations
provider_group = ProviderGroup(
    providers=[
        AnthropicProvider(model_name="claude-3-7-sonnet-20250219"),
        OpenAIProvider(model_name="gpt-4-turbo"),
    ],
    selection_strategy=ProviderSelectionStrategy.failover,
    name="advanced_provider_group",
)
```
:::
```

## Content Placement Strategies

### Strategic Container Placement

Place containers at these key points in the document:

1. **After Introduction**: Place critical warnings or setup requirements early
2. **Before Complex Implementation**: Add warnings before sections with potential pitfalls
3. **After Feature Explanations**: Add tips for optimizing feature usage
4. **At Section Transitions**: Add details containers for deeper dives into concepts

### Container Content Flow

Structure container content to:

1. Start with the most important information
2. Provide clear, concise explanations
3. Include actionable guidance when possible
4. Link to detailed documentation for complex topics

## Examples in Context

Here's how containers might be used in a complete documentation page:

```md
# Provider System

The Provider System manages integrations with external LLM providers.

::: tip Provider Auto-Detection
Atlas can automatically detect the appropriate provider based on the model name.
For example, models starting with "claude" will use the AnthropicProvider.
:::

## Basic Usage

Standard code example and explanation...

::: warning Environment Variables
Provider API keys must be set as environment variables before using providers.
If keys aren't configured, operations will fail with AuthenticationError.
:::

## Advanced Configuration

Advanced configuration details...

::: details Provider Selection Implementation
```python
# Detailed code example showing provider selection internals
```
:::

## Security Considerations

::: danger API Key Protection
Never log or expose API keys in your application. Atlas provides secure methods
for handling credentials described in the Security Best Practices guide.
:::
```

## Common Mistakes to Avoid

1. **Overuse**: Don't use containers for standard content that doesn't need highlighting
2. **Inconsistency**: Maintain consistent usage patterns across documentation
3. **Redundancy**: Don't repeat the same information in multiple containers
4. **Length**: Don't place lengthy content in containers; keep them focused
5. **Misaligned Severity**: Use the appropriate container type for the importance level

## Container Accessibility

To ensure containers are accessible:

- Don't rely solely on color to convey information
- Make sure container content makes sense in context
- Keep details container summaries descriptive
- Avoid using containers for critical navigation or essential instructions

By following these guidelines, you'll enhance documentation clarity while avoiding visual clutter or misaligned emphasis.
