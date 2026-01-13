/**
 * LLM Message Adapters
 *
 * Exports all provider-specific message adapters for converting
 * between unified message format and native provider formats.
 *
 * @internal - Legacy adapter exports. Prefer using backends through registry.
 */

export { AnthropicAdapter } from './anthropic.js'
export { OllamaAdapter } from './ollama.js'
export type { OllamaMessage, OllamaChatRequest, OllamaChatResponse } from './ollama.js'
export { ClaudeCodeAdapter } from './claude-code.js'
export type { ClaudeCodeResponse } from './claude-code.js'
