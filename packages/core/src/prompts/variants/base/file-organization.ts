/**
 * File Organization Guidance - Runtime Template Loading
 *
 * Agent file organization guide for .atlas/ directory structure.
 * Template loaded from external .md file at runtime.
 */

import { loadTemplate } from '../../template-loader'

/**
 * File organization guidance for agents.
 * Loads from: src/prompts/templates/AGENT-FILE-ORGANIZATION-GUIDE.md
 */
export function getFileOrgContext(): string {
  return loadTemplate(
    'AGENT-FILE-ORGANIZATION-GUIDE.md',
    '# Agent File Organization Guide (MOCK)\n\n**Version:** 1.0\n\nMock content for testing.'
  )
}
