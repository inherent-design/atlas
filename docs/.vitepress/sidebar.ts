import { DefaultTheme } from "vitepress";

// Utility function to create a status-marked item
const _statusItem = (
  text: string,
  link: string,
  status: "done" | "progress" | "planned"
): DefaultTheme.SidebarItem => {
  const icons = {
    done: "✅",
    progress: "🚧",
    planned: "⏱️",
  };
  return {
    text: `${icons[status]} ${text}`,
    link,
  };
};

// Complete sidebar configuration based on documentation structure
export const sidebar: DefaultTheme.Sidebar = [
  {
    text: "Getting Started",
    items: [
      { text: "Introduction", link: "/" },
      { text: "Getting Started", link: "/guides/getting_started" },
      { text: "Configuration", link: "/guides/configuration" },
    ],
  },
  {
    text: "Architecture",
    collapsed: false,
    items: [
      { text: "Overview", link: "/architecture/" },
      { text: "Components", link: "/architecture/components" },
      { text: "Data Flow", link: "/architecture/data_flow" },
      { text: "Module Interaction", link: "/architecture/module_interaction" },
      { text: "Design Principles", link: "/architecture/design_principles" },
      {
        text: "System Requirements",
        link: "/architecture/system_requirements",
      },
    ],
  },
  {
    text: "Components",
    collapsed: true,
    items: [
      {
        text: "Core",
        collapsed: true,
        items: [
          { text: "Configuration", link: "/components/core/config" },
          { text: "Environment", link: "/components/core/env" },
          { text: "Error Handling", link: "/components/core/errors" },
          { text: "Prompts", link: "/components/core/prompts" },
          { text: "Telemetry", link: "/components/core/telemetry" },
        ],
      },
      {
        text: "Agents",
        collapsed: true,
        items: [
          { text: "Controller", link: "/components/agents/controller" },
          { text: "Workers", link: "/components/agents/workers" },
        ],
      },
      {
        text: "Graph",
        collapsed: true,
        items: [
          { text: "Overview", link: "/components/graph/" },
          { text: "Nodes", link: "/components/graph/nodes" },
          { text: "Edges", link: "/components/graph/edges" },
          { text: "State", link: "/components/graph/state" },
        ],
      },
      {
        text: "Knowledge",
        collapsed: true,
        items: [
          { text: "Overview", link: "/components/knowledge/" },
          { text: "Ingestion", link: "/components/knowledge/ingestion" },
          { text: "Retrieval", link: "/components/knowledge/retrieval" },
        ],
      },
      {
        text: "Models",
        collapsed: true,
        items: [
          { text: "Overview", link: "/components/models/" },
          { text: "Anthropic", link: "/components/models/anthropic" },
          { text: "OpenAI", link: "/components/models/openai" },
          { text: "Ollama", link: "/components/models/ollama" },
          { text: "Mock", link: "/components/models/mock" },
        ],
      },
    ],
  },
  {
    text: "Workflows",
    collapsed: false,
    items: [
      { text: "Query", link: "/workflows/query" },
      { text: "Retrieval", link: "/workflows/retrieval" },
      { text: "Multi-Agent", link: "/workflows/multi_agent" },
      { text: "Custom Workflows", link: "/workflows/custom_workflows" },
    ],
  },
  {
    text: "Guides",
    collapsed: false,
    items: [
      { text: "Testing", link: "/guides/testing" },
      { text: "Type Checking", link: "/guides/type_checking" },
      {
        text: "Examples",
        collapsed: true,
        items: [
          { text: "Overview", link: "/guides/examples/" },
          { text: "Query", link: "/guides/examples/query_example" },
          { text: "Retrieval", link: "/guides/examples/retrieval_example" },
          { text: "Streaming", link: "/guides/examples/streaming_example" },
          { text: "Multi-Agent", link: "/guides/examples/multi_agent_example" },
          { text: "Advanced", link: "/guides/examples/advanced_examples" },
        ],
      },
    ],
  },
  {
    text: "Reference",
    collapsed: true,
    items: [
      { text: "API Reference", link: "/reference/api" },
      { text: "CLI Options", link: "/reference/cli" },
      { text: "Environment Variables", link: "/reference/env_variables" },
      { text: "FAQ", link: "/reference/faq" },
    ],
  },
  {
    text: "Project Management",
    collapsed: true,
    items: [
      {
        text: "Planning",
        collapsed: true,
        items: [
          {
            text: "MVP Strategy",
            link: "/project-management/roadmap/mvp_strategy",
          },
          {
            text: "MVP Completion Strategy",
            link: "/project-management/planning/mvp_completion_strategy",
          },
          {
            text: "Open Source Strategy",
            link: "/project-management/planning/open_source_strategy",
          },
          {
            text: "Documentation Planning",
            link: "/project-management/planning/docs_planning",
          },
        ],
      },
      {
        text: "Business",
        collapsed: true,
        items: [
          {
            text: "Monetization Strategy",
            link: "/project-management/business/monetization_strategy",
          },
        ],
      },
      {
        text: "Legal",
        collapsed: true,
        items: [
          {
            text: "License Selection",
            link: "/project-management/legal/license_selection",
          },
        ],
      },
      {
        text: "Marketing",
        collapsed: true,
        items: [
          {
            text: "Project Overview",
            link: "/project-management/marketing/project_overview",
          },
          {
            text: "Press Release Template",
            link: "/project-management/marketing/press_release_template",
          },
          {
            text: "Pitch Deck Outline",
            link: "/project-management/marketing/pitch_deck_outline",
          },
        ],
      },
      {
        text: "Implementation Plan",
        link: "/project-management/tracking/todo",
      },
    ],
  },
];
