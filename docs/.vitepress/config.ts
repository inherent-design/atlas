import MarkdownTaskLists from 'markdown-it-task-lists'
import { DefaultTheme, HeadConfig, defineConfig } from 'vitepress'
import timeline from 'vitepress-markdown-timeline'
import { withMermaid } from 'vitepress-plugin-mermaid'
import { withSidebar } from 'vitepress-sidebar'

const head: HeadConfig[] = [
  // ['link', { rel: 'icon', type: 'image/png', href: '/favicon.png' }],
  ['meta', { name: 'theme-color', content: '#1e88e5' }],
  ['meta', { name: 'og:type', content: 'website' }],
  ['meta', { name: 'og:site_name', content: 'Atlas Docs' }],
  ['meta', { name: 'og:url', content: 'https://docs.inherent.design/atlas' }],
]

const nav: DefaultTheme.NavItem[] = []

// https://vitepress.dev/reference/site-config
export default defineConfig(
  withSidebar(
    withMermaid({
      ignoreDeadLinks: ['http://localhost:11434'],
      lang: 'en-US',

      title: 'Atlas Docs',
      description: 'Official documentation for Atlas',

      head,

      lastUpdated: true,

      markdown: {
        typographer: true,

        config: (md) => {
          /**
           * Enable task lists
           */
          md.use(MarkdownTaskLists, {
            enabled: true,
            label: true,
          })

          /**
           * Enable timeline
           */
          md.use(timeline)
        },
      },

      vite: {
        build: {
          // Increase warning limit to prevent build errors while maintaining performance
          chunkSizeWarningLimit: 3200,
        },
        // Optimize dependency pre-bundling
        optimizeDeps: {
          exclude: ['vitepress-plugin-mermaid'],
        },
      },

      mermaid: {
        startOnLoad: false, // Defer loading until needed
        fontFamily: 'var(--vp-font-family-base)', // Use VitePress font
        altFontFamily: 'var(--vp-font-family-mono)', // Fallback

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
        class: 'mermaid',
      },

      themeConfig: {
        // https://vitepress.dev/reference/default-theme-config

        socialLinks: [
          {
            icon: 'github',
            link: 'https://github.com/inherent-design/atlas',
          },
        ],

        editLink: {
          pattern:
            'https://github.com/inherent-design/atlas/edit/main/docs/:path',
          text: 'Edit this page on GitHub',
        },

        footer: {
          message: 'Released under the MIT License.',
          copyright: 'Copyright © 2023-2025 inherent.design',
        },

        search: {
          provider: 'local',
          options: {
            detailedView: true,
            translations: {
              button: {
                buttonText: 'Search documentation',
                buttonAriaLabel: 'Search documentation',
              },
              modal: {
                displayDetails: 'Display detailed results',
                resetButtonTitle: 'Reset search',
                backButtonTitle: 'Close search',
                noResultsText: 'No results for',
                footer: {
                  navigateText: 'to navigate',
                  selectText: 'to select',
                  closeText: 'to close',
                },
              },
            },
          },
        },

        docFooter: {
          prev: 'Previous page',
          next: 'Next page',
        },

        outline: {
          level: 'deep',
          label: 'On this page',
        },

        lastUpdated: {
          text: 'Updated at',
          formatOptions: {
            dateStyle: 'medium',
            timeStyle: 'short',
          },
        },

        sidebarMenuLabel: 'Menu',
        darkModeSwitchLabel: 'Light or Dark',
        returnToTopLabel: 'Return to top',
      },
    }),
    {
      collapsed: true,
      collapseDepth: 1,

      rootGroupText: 'Menu',
      rootGroupLink: '/index.md',

      useTitleFromFileHeading: true,
      useTitleFromFrontmatter: true,
      useFolderLinkFromIndexFile: true,
      // useFolderTitleFromIndexFile: true,

      excludePattern: [],

      includeRootIndexFile: true,
      // includeFolderIndexFile: true,

      hyphenToSpace: true,
      underscoreToSpace: true,
      capitalizeFirst: true,
      capitalizeEachWords: true,

      // manualSortFileNameByPriority: ['index.md'],
      // sortFolderTo: 'bottom',
      sortMenusByFrontmatterOrder: true,
    }
  )
)
