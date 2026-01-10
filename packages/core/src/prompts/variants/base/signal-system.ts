/**
 * Signal System Guidance - Runtime Template Loading
 *
 * Template for signal-based learning system guidance.
 * Template loaded from external .md file at runtime.
 */

import { loadTemplate } from '../../template-loader'

/**
 * Signal system guidance template (loaded from external file).
 * Loads from: src/prompts/templates/SIGNAL-SYSTEM-TEMPLATE.md
 */
export function getSignalSystem(): string {
  return loadTemplate(
    'SIGNAL-SYSTEM-TEMPLATE.md',
    '**Signal system** (MOCK): Mock content for testing.'
  )
}
