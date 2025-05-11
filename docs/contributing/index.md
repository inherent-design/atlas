# Contributing to Atlas Documentation

This section outlines the guidelines and standards for contributing to the Atlas project documentation. Our documentation follows the structure of the [Trimodal Methodology Framework](../project-management/planning/architecture_planning.md), combining top-down design, bottom-up implementation, and holistic system integration perspectives.

## Core Documentation Principles

1. **Clarity and Precision**: Use clear, concise language appropriate to the context. Provide specific examples for abstract concepts and define specialized terminology.

2. **Adaptive Perspective**: Present information from multiple perspectives (user, developer, designer) to accommodate different knowledge levels and usage patterns.

3. **Progressive Disclosure**: Start with essential concepts before diving into complexities. Layer information so readers can explore details as needed.

4. **Consistency**: Maintain consistent terminology, formatting, and structure across all documentation.

5. **Example-Driven**: Provide concrete, runnable examples for all major features and concepts.

## Documentation Structure

Our documentation is organized into these main sections:

1. **[Architecture](../architecture/)**: High-level system design (Top-Down)
2. **[Components](../components/providers/)**: Individual module documentation (Bottom-Up)
3. **[Workflows](../workflows/query.md)**: Cross-component integration (Holistic)
4. **[Guides](../guides/getting_started.md)**: Task-oriented tutorials and guides
5. **[Reference](../reference/api.md)**: API references and configuration details
6. **[Project Management](../project-management/)**: Roadmaps, tracking, and planning

## Contribution Guides

These guides provide detailed standards and best practices for specific aspects of our documentation:

1. **[Documentation Standards](./documentation-standards.md)**: Overall guidelines for documentation content
2. **[Content Containers](./content-containers.md)**: Using VitePress custom containers for callouts
   - Info, tip, warning, danger, and details containers
   - GitHub-flavored alert syntax
   - When and how to use visual emphasis effectively
3. **[Timelines](./timelines.md)**: Guidelines for creating timeline components
   - Chronological process visualization
   - Implementation syntax and examples
   - Limited to 5-7 instances across documentation
4. **[Code Examples](./code-examples.md)**: Standards for code samples and snippets
5. **[Style Guide](./style-guide.md)**: Writing style, terminology, and voice guidelines

::: warning Component Usage
Remember to use [custom containers](./content-containers.md) and [timeline components](./timelines.md) sparingly throughout the documentation. These visual elements add significant weight and should only be used when they genuinely enhance understanding.
:::

## Contribution Process

1. **Plan**: Determine where your content fits in the documentation structure
2. **Draft**: Create your content following the appropriate guidelines
3. **Review**: Ensure content meets our standards for quality and clarity
4. **Submit**: Create a pull request with your changes
5. **Iterate**: Address feedback and refine your contribution

## Getting Help

If you're unsure about how to contribute or have questions about documentation standards, please [create an issue](https://github.com/inherent-design/atlas/issues/new) with the "documentation" label.

::: tip When to Update Documentation
Documentation should be updated:
- When introducing new features or components
- When changing existing functionality
- When fixing bugs that affect documented behavior
- When clarifying confusing or ambiguous documentation
:::