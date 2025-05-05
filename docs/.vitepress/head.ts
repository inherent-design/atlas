import { HeadConfig } from "vitepress";

export const head: HeadConfig[] = [
  // ['link', { rel: 'icon', type: 'image/png', href: '/favicon.png' }],
  ["meta", { name: "theme-color", content: "#1e88e5" }],
  ["meta", { name: "og:type", content: "website" }],
  ["meta", { name: "og:site_name", content: "Atlas Docs" }],
  ["meta", { name: "og:url", content: "https://docs.inherent.design/atlas" }],
];
