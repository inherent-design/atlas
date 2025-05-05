import { DefaultTheme } from "vitepress";

// Utility function to create a TODO item
const todoItem = (text: string, link: string): DefaultTheme.SidebarItem => ({
  text: `⏳ ${text}`,
  link,
});

// Complete sidebar configuration based on documentation structure
export const sidebar: DefaultTheme.Sidebar = [
  {
    text: "Models",
    link: "/models",
  },
  {
    text: "Environment Variables",
    link: "/env_variables",
  },
  {
    text: "Testing",
    link: "/testing",
  },
  {
    text: "Chroma DB Viewer",
    link: "/chromadb_viewer",
  },
];
