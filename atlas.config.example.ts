/**
 * Example Atlas Configuration
 *
 * Copy this file to atlas.config.ts and customize for your setup.
 * Place in the directory where you run `atlas` commands.
 */

import { defineConfig } from '@inherent.design/atlas-core'

export default defineConfig({
  backends: {
    // Embedding backends (Voyage AI - requires VOYAGE_API_KEY)
    'text-embedding': 'voyage:voyage-3-large',
    'code-embedding': 'voyage:voyage-code-3',
    'contextualized-embedding': 'voyage:voyage-context-3',

    // LLM backends (choose one)
    'text-completion': 'ollama:ministral-3:3b', // Local Ollama
    'json-completion': 'ollama:ministral-3:3b',
    'qntm-generation': 'ollama:ministral-3:3b',

    // Or use Claude Code CLI:
    // 'text-completion': 'claude-code:haiku',
    // 'json-completion': 'claude-code:haiku',
    // 'qntm-generation': 'claude-code:haiku',

    // Reranking (Voyage AI)
    reranking: 'voyage:rerank-2.5',
  },

  logging: {
    // Global log level
    level: 'info',

    // Module-specific overrides
    // modules: 'ingest:debug,qntm/*:trace',
  },
})
