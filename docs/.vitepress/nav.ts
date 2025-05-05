import { DefaultTheme } from "vitepress";

export const nav: DefaultTheme.NavItem[] = [
  {
    text: "Home",
    link: "/",
  },
  {
    text: "Development",
    items: [
      {
        text: "MVP Strategy",
        link: "/MVP_STRATEGY",
      },
      {
        text: "Implementation Plan",
        link: "/TODO",
      },
      {
        text: "Testing Guide",
        link: "/TESTING",
      },
    ],
  },
  {
    text: "Configuration",
    items: [
      {
        text: "Environment Variables",
        link: "/ENV_VARIABLES",
      },
      {
        text: "Models",
        link: "/MODELS",
      },
      {
        text: "Model Providers",
        link: "/MODEL_PROVIDERS",
      },
    ],
  },
  {
    text: "Tools",
    items: [
      {
        text: "ChromaDB Viewer",
        link: "/CHROMADB_VIEWER",
      },
    ],
  },
];
