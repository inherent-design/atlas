---
title: Doc. Standards
---

# Documentation Standards

This guide outlines the standards and best practices for writing documentation for the Atlas project. Following these guidelines ensures our documentation remains consistent, clear, and useful for all users.

## Document Structure

### Required Sections

Every documentation page should include:

1. **Title**: Clear, descriptive H1 heading
2. **Introduction**: Brief overview of the topic (1-3 sentences)
3. **Body**: Detailed content organized by headings
4. **Related Information**: Links to related documentation (when applicable)

### Optional Sections

Depending on the content type, consider including:

- **Prerequisites**: Requirements before using the feature
- **Examples**: Practical code examples demonstrating usage
- **Troubleshooting**: Common issues and solutions
- **API Reference**: Method signatures and parameter details
- **Implementation Notes**: Technical details for developers

## Content Organization

### Heading Hierarchy

- Use clear, descriptive headings that follow a logical hierarchy
- Maintain a consistent heading structure throughout your document
- Avoid skipping heading levels (e.g., don't go from H2 to H4)
- Keep headings concise (typically under 80 characters)

### Chunking Information

- Break content into digestible sections
- Group related information under appropriate headings
- Use lists and tables for structured information
- Limit paragraphs to 3-5 sentences

### Perspective Fluidity

Our documentation follows the Trimodal Methodology Framework, which combines three perspectives:

1. **Top-Down Design**: Start with the conceptual overview
2. **Bottom-Up Implementation**: Provide concrete details and examples
3. **Holistic Integration**: Explain how components work together

Structure your documentation to flow between these perspectives as appropriate, signaling transitions clearly.

## Content Flow and Engagement

### Progressive Disclosure

Present information in order of importance:

1. Essential concepts first
2. Common usage patterns next
3. Advanced features and edge cases last

This allows readers to gain useful knowledge quickly while providing paths to deeper understanding.

### Narrative Techniques

Maintain engagement through:

- **Question Headings**: Frame sections as answers to questions
- **Problem-Solution Format**: Present common challenges and their solutions
- **Scenario-Based Examples**: Show features in realistic contexts
- **Compare and Contrast**: Highlight differences between related concepts

### Code Examples

Include practical code examples for all feature documentation:

- Ensure examples are complete and runnable
- Include imports and setup steps
- Document inputs, outputs, and side effects
- Show both simple and complex use cases

See the [Code Examples Guide](./code-examples.md) for detailed standards.

## Content Elements

### Text Formatting

- Use **bold** for emphasis of important terms
- Use *italics* sparingly for secondary emphasis
- Use `code formatting` for code references, commands, and file paths
- Use blockquotes for extended quotations

### Lists

- Use bulleted lists for unordered items
- Use numbered lists for sequential steps or prioritized items
- Keep list items parallel in structure
- Limit nesting to 2-3 levels

### Tables

- Use tables for structured, comparable information
- Include clear column headers
- Maintain consistent formatting within tables
- Provide context or introduction before tables

### Custom Containers

Use custom containers to highlight important information:

```md
::: tip
Best practices and helpful advice
:::

::: warning
Important cautions or potential issues
:::

::: danger
Critical warnings about breaking changes or serious risks
:::

::: details
Additional information that might not be needed by all readers
:::
```

See the [Content Containers Guide](./content-containers.md) for detailed usage guidelines.

## Language and Style

### Voice and Tone

- Use a clear, conversational tone
- Write in active voice when possible
- Address the reader directly using "you"
- Avoid jargon and overly technical language without explanation

### Clarity and Precision

- Define technical terms when first introduced
- Use consistent terminology throughout
- Be specific rather than general
- Provide concrete examples for abstract concepts

### Internationalization Considerations

- Use simple, clear sentence structures
- Avoid idioms, colloquialisms, and cultural references
- Use inclusive language that works across cultures
- Ensure examples are globally relevant

## Visual Elements

### Diagrams

- Include diagrams for complex systems or workflows
- Use consistent visual styles across diagrams
- Provide alt text for accessibility
- Keep diagrams simple and focused on key concepts

### Images

- Use screenshots to illustrate UI elements
- Crop images to focus on relevant details
- Optimize image sizes for web viewing
- Include descriptive captions

## Final Checks

Before submitting documentation:

1. **Accuracy**: Verify all technical information is correct
2. **Completeness**: Ensure all necessary information is included
3. **Clarity**: Check that explanations are clear and concise
4. **Consistency**: Confirm terminology and formatting are consistent
5. **Examples**: Test all code examples to ensure they work
6. **Links**: Verify all links point to the correct destinations
7. **Spelling/Grammar**: Check for language errors

## Example Documentation Structure

Here's an example structure for a component documentation page:

```md
# Component Name

Brief introduction to the component and its purpose.

## Overview

Conceptual explanation of what the component does and why it exists.

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

## Advanced Usage

More complex examples and usage patterns.

## API Reference

Detailed method signatures and parameter descriptions.

## Related Components

Links to related documentation.
```
