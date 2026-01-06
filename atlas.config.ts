import { defineConfig } from '@inherent.design/atlas-core'

export default defineConfig({
  backends: {
    'text-completion': 'claude-code:sonnet',
    'json-completion': 'claude-code:haiku',
    vision: 'claude-code:sonnet',
    'tool-use': 'claude-code:sonnet',
    streaming: 'claude-code:haiku',
  },
  daemon: {
    autoStart: {
      fileWatcher: true,
    },
  },
})
