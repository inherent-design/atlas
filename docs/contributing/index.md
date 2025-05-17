---
title: Contributing
---

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
   - **[Implementation Plan](../project-management/planning/accelerated_implementation_plan.md)**: Execution plan
   - **[Progress Tracking](../project-management/tracking/todo.md)**: Implementation status

4. **Reference**: Reference documentation:
   - **[Licensing](../reference/licensing.md)**: Licensing information

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
4. **[Code Examples](./code-examples.md)**: Standards for code samples and snippets
5. **[Style Guide](./style-guide.md)**: Writing style, terminology, and voice guidelines

### Type System and Schema Validation

The following guides provide information about Atlas's type system and schema validation approach:

1. **[Type System Guide](./types.md)**: Comprehensive overview of Atlas's type system
   - Static typing with Protocol and TypedDict
   - Generic typing and type narrowing
   - Best practices for type safety
2. **[Schema Validation](./schema-validation.md)**: How to use Marshmallow schema validation
   - Basic schema usage and examples
   - Validation decorators and patterns
   - Migration notes for Marshmallow 4.0.0
3. **[Type Mapping Guide](./type-mappings.md)**: Handling type conversions between systems
   - Type conversion patterns and strategies
   - Serialization and deserialization techniques
   - System boundary handling
   - Integration with NERV/Inner Universe types

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
