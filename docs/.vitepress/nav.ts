import { DefaultTheme } from "vitepress";

export const nav: DefaultTheme.NavItem[] = [
  {
    text: "Home",
    link: "/",
  },
  {
    text: "Getting Started",
    link: "/guides/getting_started",
  },
  {
    text: "Architecture",
    items: [
      {
        text: "Overview",
        link: "/architecture/",
      },
      {
        text: "Components",
        link: "/architecture/components",
      },
      {
        text: "Data Flow",
        link: "/architecture/data_flow",
      },
      {
        text: "Design Principles",
        link: "/architecture/design_principles",
      },
    ],
  },
  {
    text: "Components",
    items: [
      {
        text: "Core",
        link: "/components/core/config",
      },
      {
        text: "Agents",
        link: "/components/agents/controller",
      },
      {
        text: "Graph",
        link: "/components/graph/",
      },
      {
        text: "Knowledge",
        link: "/components/knowledge/",
      },
      {
        text: "Models",
        link: "/components/models/",
      },
    ],
  },
  {
    text: "Workflows",
    items: [
      {
        text: "Query",
        link: "/workflows/query",
      },
      {
        text: "Retrieval",
        link: "/workflows/retrieval",
      },
      {
        text: "Multi-Agent",
        link: "/workflows/multi_agent",
      },
      {
        text: "Custom Workflows",
        link: "/workflows/custom_workflows",
      },
    ],
  },
  {
    text: "Guides",
    items: [
      {
        text: "Configuration",
        link: "/guides/configuration",
      },
      {
        text: "Testing",
        link: "/guides/testing",
      },
      {
        text: "Type Checking",
        link: "/guides/type_checking",
      },
      {
        text: "Examples",
        link: "/guides/examples/",
      },
    ],
  },
  {
    text: "Reference",
    items: [
      {
        text: "API Reference",
        link: "/reference/api",
      },
      {
        text: "CLI Options",
        link: "/reference/cli",
      },
      {
        text: "Environment Variables",
        link: "/reference/env_variables",
      },
      {
        text: "FAQ",
        link: "/reference/faq",
      },
    ],
  },
];