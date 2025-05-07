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
        text: "Module Interaction",
        link: "/architecture/module_interaction",
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
      {
        text: "Tools",
        link: "/components/tools/",
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
  {
    text: "Project",
    items: [
      {
        text: "Planning",
        items: [
          {
            text: "MVP Strategy",
            link: "/project-management/roadmap/mvp_strategy",
          },
          {
            text: "MVP Completion",
            link: "/project-management/planning/mvp_completion_strategy",
          },
          {
            text: "Open Source Strategy",
            link: "/project-management/planning/open_source_strategy",
          },
        ],
      },
      {
        text: "Business & Marketing",
        items: [
          {
            text: "Monetization Strategy",
            link: "/project-management/business/monetization_strategy",
          },
          {
            text: "Project Overview",
            link: "/project-management/marketing/project_overview",
          },
        ],
      },
    ],
  },
];