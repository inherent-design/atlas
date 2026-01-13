/**
 * Atlas System Identity - Runtime Template Loading
 *
 * Multi-agent orchestration framework and system prompt.
 * Template loaded from external .md file at runtime.
 */

import { loadTemplate } from '../../template-loader.js'

/**
 * Atlas system identity and multi-agent orchestration framework.
 * Loads from: src/prompts/templates/CLAUDE-SYSTEM-IDENTITY.md
 */
export function getClaudeSys(): string {
  return loadTemplate(
    'CLAUDE-SYSTEM-IDENTITY.md',
    '# ATLAS System Prompt (MOCK)\n\n**Version:** 2.1\n\nMock content for testing.'
  )
}
