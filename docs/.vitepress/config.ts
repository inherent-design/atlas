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

    mermaidPlugin: {
      class: "mermaid",
      // Optimize mermaid initialization and rendering
      mermaidConfig: {
        startOnLoad: false, // Defer loading until needed
        fontFamily: "var(--vp-font-family-base)", // Use VitePress font
        altFontFamily: "var(--vp-font-family-mono)", // Fallback
        
        // Global theme settings configured with CSS variables
        theme: 'base',
        themeVariables: {
          // Core appearance
          primaryColor: 'var(--mermaid-primary-color)',
          primaryBorderColor: 'var(--mermaid-primary-border)',
          primaryTextColor: 'var(--mermaid-text-color)',
          secondaryColor: 'var(--mermaid-info-color)',
          secondaryBorderColor: 'var(--mermaid-info-border)',
          tertiaryColor: 'var(--mermaid-success-color)',
          tertiaryBorderColor: 'var(--mermaid-success-border)',
          
          // Lines and labels
          lineColor: 'var(--mermaid-edge-color)',
          textColor: 'var(--mermaid-text-color)',
          mainBkg: 'var(--mermaid-node-bg)',
          nodeBorder: 'var(--mermaid-node-border)',
          edgeLabelBackground: 'var(--mermaid-label-bg)',
          
          // Fonts
          fontSize: '14px',
          fontFamily: 'var(--vp-font-family-base)',
          
          // Diagram-specific elements
          labelColor: 'var(--mermaid-text-color)',
          labelTextColor: 'var(--mermaid-text-color)',
          classText: 'var(--mermaid-text-color)',
          noteTextColor: 'var(--mermaid-text-color)',
          loopTextColor: 'var(--mermaid-text-color)',
        },
        
        // Diagram-specific settings
        flowchart: {
          useMaxWidth: true, // Better responsive behavior
          htmlLabels: true,
          curve: 'cardinal', // More efficient curve rendering
          nodeSpacing: 50,
          rankSpacing: 60,
          labelBackground: 'var(--mermaid-label-bg)',
          edgeLabelBackground: 'var(--mermaid-label-bg)',
          diagramPadding: 8,
          messageFontSize: 12,
          labelFontSize: '12px',
          edgeFontSize: '12px',
        },
        sequence: {
          useMaxWidth: true,
          diagramMarginX: 50,
          diagramMarginY: 10,
          actorFontSize: 14,
          noteFontSize: 14,
          messageFontSize: 14,
        },
        classDiagram: {
          useMaxWidth: true,
          diagramPadding: 20,
        },
        entityRelationshipDiagram: {
          useMaxWidth: true,
          diagramPadding: 20,
        },
        gantt: {
          useMaxWidth: true,
          leftPadding: 75,
          rightPadding: 30,
          topPadding: 30,
          bottomPadding: 30,
        },
      },
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
