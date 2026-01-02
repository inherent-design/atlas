# Component Diagram Template

This template provides guidelines for creating consistent component relationship diagrams in Atlas documentation.

## Purpose

Component diagrams visualize the high-level components of a system and their relationships. They help readers understand the system's structure, dependencies, and organization.

## Template Structure

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│                      [System Name/Title]                       │
│                                                                │
├────────────────┐   ┌─────────────────┐   ┌──────────────────┐  │
│                │   │                 │   │                  │  │
│  [Component A] ├───┤  [Component B]  ├───┤  [Component C]   │  │
│                │   │                 │   │                  │  │
└────────┬───────┘   └────────┬────────┘   └──────────────────┘  │
         │                    │                                   │
         │                    │                                   │
┌────────┴───────┐   ┌────────┴────────┐                         │
│                │   │                 │                         │
│  [Component D] │   │  [Component E]  │                         │
│                │   │                 │                         │
└────────────────┘   └─────────────────┘                         │
│                                                                │
│                   [External System]                            │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

## Color Coding

Follow the standard Atlas color palette:

- Core components: Deep Blue (#0A2463)
- Supporting components: Medium Blue (#3E92CC)
- External systems: Gray (#8D99AE)
- Data stores: Dark Teal (#247BA0)
- User interfaces: Light Blue (#8AC4FF)

## Relationship Types

| Relationship | Symbol | Meaning |
|--------------|--------|---------|
| Solid line with arrow | ──→ | Dependency/Usage |
| Dashed line with arrow | ┈┈→ | Interface implementation |
| Double line | ═══ | Composition |
| Solid line with diamond | ◆── | Aggregation |

## Labels and Annotations

- Each component should have a clear, concise name
- Optional brief description (1-2 words) can be included below the name
- Relationship lines can include brief action verbs (e.g., "uses", "creates", "transforms")
- Include a legend for non-standard symbols
- Add a title that clearly identifies the system or subsystem being diagrammed

## Example Component Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Authentication System                          │
│                                                                      │
│  ┌──────────────┐        uses         ┌──────────────────────────┐   │
│  │              │◀───────────────────▶│                          │   │
│  │ Auth Service │                     │ User Management Service  │   │
│  │              │─────────────────────│                          │   │
│  └──────┬───────┘     validates       └──────────────┬───────────┘   │
│         │                                            │               │
│         │ authenticates                              │ manages       │
│         ▼                                            ▼               │
│  ┌──────────────┐                          ┌──────────────────────┐  │
│  │              │                          │                      │  │
│  │ JWT Provider │                          │     User Store       │  │
│  │              │                          │                      │  │
│  └──────────────┘                          └──────────────────────┘  │
│                                                                      │
│  ┌─────────────────────┐              ┌──────────────────────────┐   │
│  │                     │              │                          │   │
│  │ External OAuth      │◀────────────▶│ Authorization Service    │   │
│  │ Provider            │  federates   │                          │   │
│  └─────────────────────┘              └──────────────────────────┘   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## Best Practices

1. Keep components to 7±2 for readability
2. Group related components visually
3. Use consistent sizing and spacing
4. Emphasize important relationships
5. Include a clear system boundary
6. Add directional indicators on relationships
7. Maintain a clear visual hierarchy

## Diagram Metadata

Include the following metadata with each diagram:

- **Title**: Brief description of the system represented
- **Version**: Diagram version number
- **Date**: Last updated date
- **Author**: Creator of the diagram
- **Status**: Draft, Review, Approved, etc.

## Integration with Documentation

When incorporating component diagrams into documentation:

1. Introduce the diagram with a brief paragraph explaining its purpose
2. Refer to specific components by name in the text
3. Explain key relationships that might not be immediately obvious
4. Connect the diagram to both higher-level architecture and lower-level implementation details
5. Follow the diagram with more detailed explanations of critical components
