import MarkdownTaskLists from "markdown-it-task-lists";
import { defineConfig } from "vitepress";
import timeline from "vitepress-markdown-timeline";
import { withMermaid } from "vitepress-plugin-mermaid";
import { head } from "./head";
import { nav } from "./nav";
import { sidebar } from "./sidebar";

// https://vitepress.dev/reference/site-config
export default defineConfig(
  withMermaid({
    lang: "en-US",

    title: "Atlas Docs",
    description: "Official documentation for Atlas",

    head,
    base: "/atlas",

    lastUpdated: true,

    themeConfig: {
      // https://vitepress.dev/reference/default-theme-config

      socialLinks: [
        {
          icon: "github",
          link: "https://github.com/inherent-design/inherent.design",
        },
      ],

      editLink: {
        pattern:
          "https://github.com/inherent-design/inherent.design/edit/main/docs/:path",
        text: "Edit this page on GitHub",
      },

      footer: {
        message: "Released under the MIT License.",
        copyright: "Copyright © 2023-2025 inherent.design",
      },

      search: {
        provider: "local",
        options: {
          detailedView: true,
          translations: {
            button: {
              buttonText: "Search documentation",
              buttonAriaLabel: "Search documentation",
            },
            modal: {
              displayDetails: "Display detailed results",
              resetButtonTitle: "Reset search",
              backButtonTitle: "Close search",
              noResultsText: "No results for",
              footer: {
                navigateText: "to navigate",
                selectText: "to select",
                closeText: "to close",
              },
            },
          },
        },
      },

      docFooter: {
        prev: "Previous page",
        next: "Next page",
      },

      outline: {
        level: "deep",
        label: "On this page",
      },

      lastUpdated: {
        text: "Updated at",
        formatOptions: {
          dateStyle: "medium",
          timeStyle: "short",
        },
      },

      sidebarMenuLabel: "Menu",
      darkModeSwitchLabel: "Light or Dark",
      returnToTopLabel: "Return to top",

      nav,
      sidebar,
    },

    markdown: {
      typographer: true,

      config: (md) => {
        /**
         * Enable task lists
         */
        md.use(MarkdownTaskLists, {
          enabled: true,
          label: true,
        });

        /**
         * Enable timeline
         */
        md.use(timeline);
      },
    },

    mermaid: {
      startOnLoad: false, // Defer loading until needed
      fontFamily: "var(--vp-font-family-base)", // Use VitePress font
      altFontFamily: "var(--vp-font-family-mono)", // Fallback

      // Diagram-specific settings
      flowchart: {
        useMaxWidth: true, // Better responsive behavior
        htmlLabels: true,
        nodeSpacing: 50,
        rankSpacing: 60,
        diagramPadding: 8,
      },
      sequence: {
        useMaxWidth: true,
        diagramMarginX: 50,
        diagramMarginY: 10,
        actorFontSize: 14,
        noteFontSize: 14,
        messageFontSize: 14,
      },
      gantt: {
        useMaxWidth: true,
        leftPadding: 75,
        rightPadding: 30,
        topPadding: 30,
      },
    },

    mermaidPlugin: {
      class: "mermaid",
    },

    vite: {
      build: {
        // Increase warning limit to prevent build errors while maintaining performance
        chunkSizeWarningLimit: 1500,
      },
      // Optimize dependency pre-bundling
      optimizeDeps: {
        exclude: ["vitepress-plugin-mermaid"],
      },
    },
  })
);
