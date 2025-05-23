---
title: Contributing
---

# Contributing to Atlas Documentation

This section provides comprehensive guidelines for contributing to the Atlas project documentation. Our documentation follows the structure of the Trimodal Methodology Framework, combining top-down design, bottom-up implementation, and holistic system integration perspectives.

## Core Documentation Principles

1. **Clarity and Precision**: Use clear, concise language appropriate to the context. Provide specific examples for abstract concepts and define specialized terminology.

2. **Adaptive Perspective**: Present information from multiple perspectives (user, developer, designer) to accommodate different knowledge levels and usage patterns.

3. **Progressive Disclosure**: Start with essential concepts before diving into complexities. Layer information so readers can explore details as needed.

4. **Consistency**: Maintain consistent terminology, formatting, and structure across all documentation.

5. **Example-Driven**: Provide concrete, runnable examples for all major features and concepts.

## Documentation Structure

Our documentation is organized into these main sections:

1. **Architecture**: The system architecture is now documented in:
   - **[Architectural Patterns](../v2/nerv/patterns/)**: Core architectural patterns (Top-Down)
   - **[Components](../v2/nerv/components/)**: Core component implementation (Bottom-Up)
   - **[Composites](../v2/nerv/composites/)**: System integration components (Holistic)

2. **Implementation**: Implementation details are found in:
   - **[Implementation Guide](../v2/inner-universe/implementation.md)**: Implementation approach
   - **[Integration Guide](../v2/inner-universe/integration_guide.md)**: System integration
   - **[Type System](../v2/inner-universe/types.md)**: Type definitions

3. **Project Management**: Project planning and tracking:
   - **[Product Roadmap](../project-management/roadmap/product_roadmap.md)**: Development roadmap
   - **[Implementation Plan](../project-management/planning/feature_driven_architecture.md)**: Execution plan
   - **[Progress Tracking](../project-management/tracking/proposed_structure.md)**: Implementation status

4. **Reference**: Reference documentation:
   - **[Licensing](../reference/licensing.md)**: Licensing information

## Contribution Guides

These consolidated guides provide comprehensive standards and best practices for Atlas documentation:

### [Code Standards](./code-standards.md)
Complete guide to code quality, formatting, and type system usage including:
- **Code Examples**: Standards for creating clear, instructive code examples
- **Colored Diffs**: Using visual diffs to highlight code changes
- **Type System**: Comprehensive type system guidelines and best practices
- **Type Mappings**: Handling type conversions between different systems

### [Documentation Guide](./documentation-guide.md)
Comprehensive guide to writing high-quality documentation including:
- **Writing Standards**: Voice, tone, and style guidelines
- **Content Containers**: Using VitePress custom containers effectively
- **Timeline Components**: Creating chronological visualizations
- **Visual Elements**: Formatting, images, and accessibility

### [Implementation Guide](./implementation-guide.md)
Technical setup and implementation patterns including:
- **Development Environment**: Setting up and using the development environment
- **Schema Validation**: Using Marshmallow for runtime validation
- **Implementation Patterns**: Common patterns for providers, agents, and tools

::: tip Getting Started
New contributors should start with the [Implementation Guide](./implementation-guide.md) to set up their development environment, then refer to the [Code Standards](./code-standards.md) for coding guidelines and the [Documentation Guide](./documentation-guide.md) for writing documentation.
:::

## Contribution Process

1. **Plan**: Determine where your content fits in the documentation structure
2. **Setup**: Follow the [Implementation Guide](./implementation-guide.md) to set up your development environment
3. **Draft**: Create your content following the appropriate guidelines
4. **Review**: Ensure content meets our standards for quality and clarity
5. **Submit**: Create a pull request with your changes
6. **Iterate**: Address feedback and refine your contribution

## Key Guidelines Summary

### For Code Contributions
- Follow the type system guidelines in [Code Standards](./code-standards.md)
- Use proper schema validation as outlined in [Implementation Guide](./implementation-guide.md)
- Include comprehensive examples following [Code Standards](./code-standards.md)
- Run all quality checks: `uv run pytest`, `uv run mypy atlas`, `uv run ruff check .`

### For Documentation Contributions
- Follow the writing style in [Documentation Guide](./documentation-guide.md)
- Use custom containers appropriately (limit to 2-3 per page)
- Include practical code examples following [Code Standards](./code-standards.md)
- Test all links and code examples before submission

### For Visual Elements
- Use timeline components sparingly for chronological processes
- Apply colored diffs to highlight important code changes
- Follow accessibility guidelines for images and diagrams
- Maintain visual consistency across documentation

## Getting Help

If you're unsure about how to contribute or have questions about documentation standards, please [create an issue](https://github.com/inherent-design/atlas/issues/new) with the "documentation" label.

::: info Quality Focus
Atlas prioritizes high-quality, consistent documentation that serves both newcomers and experienced developers. All contributions should enhance clarity, maintain consistency, and provide practical value to users.
:::