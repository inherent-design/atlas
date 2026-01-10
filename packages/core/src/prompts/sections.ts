/**
 * Prompt Section Loaders
 *
 * Composable sections for dynamic prompt assembly.
 * Sections can be injected into prompts via {{SECTION_NAME}} placeholders.
 *
 * Content is now embedded statically (no runtime file I/O).
 * Lazy-loaded to avoid allocating large strings at module import time.
 */

export interface PromptSection {
  name: string
  loader: () => Promise<string> | string
  cache?: {
    content: string
    loadedAt: number
    ttl: number
  }
}

export const sections: Record<string, PromptSection> = {
  FILE_ORG_CONTEXT: {
    name: 'file-organization',
    loader: () => {
      // Lazy require to avoid loading content until actually needed
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const { getFileOrgContext } = require('./variants/base/file-organization')
      return getFileOrgContext()
    },
  },

  CLAUDE_SYS: {
    name: 'atlas-identity',
    loader: () => {
      // Lazy require to avoid loading content until actually needed
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const { getClaudeSys } = require('./variants/base/system-identity')
      return getClaudeSys()
    },
  },

  SIGNAL_SYSTEM: {
    name: 'signal-system',
    loader: () => {
      // Lazy require to avoid loading content until actually needed
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const { getSignalSystem } = require('./variants/base/signal-system')
      return getSignalSystem()
    },
  },
}

/**
 * Load a section by name.
 * Handles caching and error recovery.
 */
export async function loadSection(name: string): Promise<string> {
  const section = sections[name]
  if (!section) {
    console.warn(`[prompts] Section "${name}" not found`)
    return `[Section ${name} not found]`
  }

  // Check cache
  if (
    section.cache?.content &&
    Date.now() - section.cache.loadedAt < section.cache.ttl
  ) {
    return section.cache.content
  }

  try {
    // Load fresh
    const content = await Promise.resolve(section.loader())

    // Update cache
    if (section.cache) {
      section.cache.content = content
      section.cache.loadedAt = Date.now()
    }

    return content
  } catch (err) {
    console.error(`[prompts] Failed to load section "${name}":`, err)
    return `[Failed to load section ${name}]`
  }
}

