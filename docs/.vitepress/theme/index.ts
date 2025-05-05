import type { EnhanceAppContext } from 'vitepress'
import DefaultTheme from 'vitepress/theme'

import 'vitepress-markdown-timeline/dist/theme/index.css'
import './custom.css'

export default {
  ...DefaultTheme,
  enhanceApp({ app, router, siteData }: EnhanceAppContext) {
    DefaultTheme.enhanceApp?.({ app, router, siteData })
  },
}
