import { DefaultTheme } from "vitepress";

// Utility function to create a status-marked item
const statusItem = (text: string, link: string, status: "done" | "progress" | "planned"): DefaultTheme.SidebarItem => {
  const icons = {
    done: "✅",
    progress: "🚧",
    planned: "⏱️"
  };
  return {
    text: `${icons[status]} ${text}`,
    link
  };
};

// Complete sidebar configuration based on documentation structure
export const sidebar: DefaultTheme.Sidebar = [
  {
    text: "Getting Started",
    items: [
      { text: "Overview", link: "/" },
      statusItem("MVP Strategy", "/MVP_STRATEGY", "done"),
      statusItem("Implementation Plan", "/TODO", "done"),
    ]
  },
  {
    text: "Development",
    items: [
      statusItem("Testing Guide", "/TESTING", "done"),
      statusItem("Environment Variables", "/ENV_VARIABLES", "done"),
      statusItem("CLI Tools", "/cli/README", "done"),
    ]
  },
  {
    text: "Configuration",
    items: [
      statusItem("Models", "/MODELS", "done"),
      statusItem("Model Providers", "/MODEL_PROVIDERS", "done"),
    ]
  },
  {
    text: "Tools & Utilities",
    items: [
      statusItem("ChromaDB Viewer", "/CHROMADB_VIEWER", "done"),
    ]
  },
];
