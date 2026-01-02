/**
 * LLM Service Types
 *
 * Capability interfaces for LLM backends.
 * Each capability is a mixin interface that backends can implement.
 *
 * Backend implementations:
 * - AnthropicBackend (Claude Opus/Sonnet/Haiku): All capabilities
 * - OllamaLLMBackend (ministral, llama, etc.): text-completion, json-completion
 */

import type { BackendDescriptor, LLMCapability, LatencyClass, PricingInfo } from '../../shared/capabilities'

// ============================================
// Result Types
// ============================================

/**
 * Token usage information
 */
export interface TokenUsage {
  /** Tokens in the input prompt */
  inputTokens: number
  /** Tokens in the output completion */
  outputTokens: number
  /** Tokens used for extended thinking (if applicable) */
  thinkingTokens?: number
  /** Tokens from cache hit (if applicable) */
  cachedTokens?: number
}

/**
 * Result from a completion operation
 */
export interface CompletionResult {
  /** The generated text */
  text: string
  /** Token usage statistics */
  usage?: TokenUsage
  /** Model that generated this result */
  model: string
  /** Stop reason (e.g., 'end_turn', 'max_tokens', 'tool_use') */
  stopReason?: string
}

/**
 * Result from extended thinking operation
 */
export interface ThinkingResult extends CompletionResult {
  /** The thinking/reasoning trace (if exposed) */
  thinking?: string
  /** Summary of the thinking process */
  thinkingSummary?: string
}

/**
 * Tool/function definition for tool use
 */
export interface ToolDefinition {
  name: string
  description: string
  inputSchema: Record<string, unknown>
}

/**
 * Tool use result
 */
export interface ToolUseResult extends CompletionResult {
  /** Tools that were called */
  toolCalls: Array<{
    id: string
    name: string
    input: Record<string, unknown>
  }>
}

/**
 * Image input for vision capability
 */
export interface ImageInput {
  /** Base64-encoded image data */
  data: string
  /** MIME type (e.g., 'image/png', 'image/jpeg') */
  mimeType: string
}

// ============================================
// Backend Descriptor
// ============================================

/**
 * LLM backend descriptor.
 * Extends base descriptor with LLM-specific metadata.
 */
export interface LLMBackend extends BackendDescriptor<LLMCapability> {
  /** Model identifier (e.g., 'claude-sonnet-4-5-20250929') */
  readonly modelId: string

  /** Maximum context window in tokens */
  readonly contextWindow: number

  /** Maximum output tokens */
  readonly maxOutputTokens: number

  /** Relative latency classification */
  readonly latency: LatencyClass

  /** Pricing information (if metered) */
  readonly pricing?: PricingInfo
}

// ============================================
// Capability Interfaces (Mixins)
// ============================================

/**
 * Basic text completion capability.
 * All LLM backends implement this.
 */
export interface CanComplete {
  /**
   * Generate a completion for a prompt.
   *
   * @param prompt - The input prompt
   * @param options - Completion options
   * @returns Completion result
   */
  complete(prompt: string, options?: CompletionOptions): Promise<CompletionResult>
}

/**
 * JSON/structured output capability.
 * Guarantees well-formed JSON output.
 */
export interface CanCompleteJSON {
  /**
   * Generate a JSON completion.
   *
   * @param prompt - The input prompt (should instruct JSON format)
   * @param options - Completion options
   * @returns Parsed JSON result
   */
  completeJSON<T>(prompt: string, options?: CompletionOptions): Promise<T>
}

/**
 * Extended thinking capability.
 * Model can reason step-by-step with thinking budget.
 */
export interface CanThink {
  /**
   * Generate a completion with extended thinking.
   *
   * @param prompt - The input prompt
   * @param options - Thinking options including budget
   * @returns Completion with thinking trace
   */
  think(prompt: string, options?: ThinkingOptions): Promise<ThinkingResult>
}

/**
 * Vision/image understanding capability.
 */
export interface CanSeeImages {
  /**
   * Generate a completion with image input.
   *
   * @param prompt - Text prompt
   * @param images - Array of images to analyze
   * @param options - Completion options
   * @returns Completion result
   */
  completeWithImages(
    prompt: string,
    images: ImageInput[],
    options?: CompletionOptions
  ): Promise<CompletionResult>
}

/**
 * Tool/function calling capability.
 */
export interface CanUseTool {
  /**
   * Generate a completion with tool definitions.
   *
   * @param prompt - The input prompt
   * @param tools - Available tools
   * @param options - Completion options
   * @returns Result with tool calls
   */
  completeWithTools(
    prompt: string,
    tools: ToolDefinition[],
    options?: CompletionOptions
  ): Promise<ToolUseResult>
}

/**
 * Streaming output capability.
 */
export interface CanStream {
  /**
   * Stream a completion token by token.
   *
   * @param prompt - The input prompt
   * @param options - Completion options
   * @returns Async iterator of text chunks
   */
  stream(prompt: string, options?: CompletionOptions): AsyncIterable<string>
}

// ============================================
// Capability Map (for type narrowing)
// ============================================

/**
 * Maps capability strings to their interface types.
 * Used for type-safe capability checking.
 */
export type LLMCapabilityMap = {
  'text-completion': CanComplete
  'json-completion': CanCompleteJSON
  'extended-thinking': CanThink
  vision: CanSeeImages
  'tool-use': CanUseTool
  streaming: CanStream
  'long-context': object // No additional methods, just metadata
}

// ============================================
// Options Types
// ============================================

/**
 * Options for completion operations
 */
export interface CompletionOptions {
  /** Sampling temperature (0.0-1.0) */
  temperature?: number
  /** Maximum tokens to generate */
  maxTokens?: number
  /** Stop sequences */
  stopSequences?: string[]
  /** Top-p nucleus sampling */
  topP?: number
  /** Top-k sampling */
  topK?: number
}

/**
 * Options for extended thinking
 */
export interface ThinkingOptions extends CompletionOptions {
  /** Maximum thinking tokens budget */
  thinkingBudget?: number
  /** Whether to include thinking trace in response */
  includeThinking?: boolean
}

// ============================================
// Configuration Types
// ============================================

/**
 * Configuration for initializing an LLM backend
 */
export interface LLMBackendConfig {
  /** Model identifier or alias */
  model: string
  /** API key (if required) */
  apiKey?: string
  /** Base URL for API (for self-hosted) */
  baseUrl?: string
  /** Request timeout in milliseconds */
  timeout?: number
  /** Default temperature */
  defaultTemperature?: number
  /** Default max tokens */
  defaultMaxTokens?: number
}

// ============================================
// Claude Model Specifications
// ============================================

/**
 * Claude model family identifiers
 */
export type ClaudeModelFamily = 'opus' | 'sonnet' | 'haiku'

/**
 * Claude model specifications (from Anthropic docs, Dec 2025)
 */
export const CLAUDE_MODELS = {
  'opus-4.5': {
    id: 'claude-opus-4-5-20251101',
    alias: 'claude-opus-4-5',
    family: 'opus' as const,
    contextWindow: 200_000,
    maxOutputTokens: 64_000,
    pricing: { input: 5, output: 25 },
    latency: 'moderate' as const,
    knowledgeCutoff: '2025-05',
    capabilities: new Set<LLMCapability>([
      'text-completion',
      'json-completion',
      'extended-thinking',
      'vision',
      'tool-use',
      'streaming',
    ]),
  },
  'sonnet-4.5': {
    id: 'claude-sonnet-4-5-20250929',
    alias: 'claude-sonnet-4-5',
    family: 'sonnet' as const,
    contextWindow: 1_000_000, // With beta header
    maxOutputTokens: 64_000,
    pricing: { input: 3, output: 15 },
    latency: 'fast' as const,
    knowledgeCutoff: '2025-01',
    capabilities: new Set<LLMCapability>([
      'text-completion',
      'json-completion',
      'extended-thinking',
      'vision',
      'tool-use',
      'streaming',
      'long-context',
    ]),
  },
  'haiku-4.5': {
    id: 'claude-haiku-4-5-20251001',
    alias: 'claude-haiku-4-5',
    family: 'haiku' as const,
    contextWindow: 200_000,
    maxOutputTokens: 64_000,
    pricing: { input: 1, output: 5 },
    latency: 'fastest' as const,
    knowledgeCutoff: '2025-02',
    capabilities: new Set<LLMCapability>([
      'text-completion',
      'json-completion',
      'extended-thinking',
      'vision',
      'tool-use',
      'streaming',
    ]),
  },
  // Legacy models (still available)
  'sonnet-4': {
    id: 'claude-sonnet-4-20250514',
    alias: 'claude-sonnet-4-0',
    family: 'sonnet' as const,
    contextWindow: 200_000,
    maxOutputTokens: 64_000,
    pricing: { input: 3, output: 15 },
    latency: 'fast' as const,
    knowledgeCutoff: '2025-01',
    capabilities: new Set<LLMCapability>([
      'text-completion',
      'json-completion',
      'extended-thinking',
      'vision',
      'tool-use',
      'streaming',
    ]),
  },
  'haiku-3': {
    id: 'claude-3-haiku-20240307',
    alias: undefined,
    family: 'haiku' as const,
    contextWindow: 200_000,
    maxOutputTokens: 4_000,
    pricing: { input: 0.25, output: 1.25 },
    latency: 'fastest' as const,
    knowledgeCutoff: '2023-08',
    capabilities: new Set<LLMCapability>(['text-completion', 'json-completion', 'vision', 'tool-use', 'streaming']),
  },
} as const

export type ClaudeModelKey = keyof typeof CLAUDE_MODELS

// ============================================
// Ollama Model Types
// ============================================

/**
 * Ollama model info from /api/tags (list models)
 */
export interface OllamaModelInfo {
  name: string
  model: string
  modified_at: string
  size: number
  digest: string
  details: {
    parent_model?: string
    format?: string
    family?: string
    families?: string[]
    parameter_size?: string
    quantization_level?: string
  }
}

/**
 * Ollama model details from /api/show (single model)
 * This endpoint returns capabilities!
 */
export interface OllamaModelDetails {
  parameters: string
  license: string
  modified_at: string
  template: string
  /** Capabilities reported by Ollama (e.g., ['completion', 'vision']) */
  capabilities: OllamaCapability[]
  details: {
    format?: string
    family?: string
    families?: string[]
    parameter_size?: string
    quantization_level?: string
  }
  model_info?: Record<string, unknown>
}

/**
 * Ollama capability strings as reported by /api/show
 */
export type OllamaCapability =
  | 'completion' // Text generation
  | 'vision' // Image understanding
  | 'embedding' // Vector embeddings
  | 'tools' // Tool/function calling

/**
 * Map Ollama's capability strings to our LLMCapability type
 */
export function mapOllamaCapabilities(ollamaCaps: OllamaCapability[]): Set<LLMCapability> {
  const caps = new Set<LLMCapability>()

  for (const cap of ollamaCaps) {
    switch (cap) {
      case 'completion':
        caps.add('text-completion')
        caps.add('json-completion') // All completion models support JSON format
        caps.add('streaming') // All Ollama models support streaming
        break
      case 'vision':
        caps.add('vision')
        break
      case 'tools':
        caps.add('tool-use')
        break
      // 'embedding' is handled by embedding service, not LLM
    }
  }

  return caps
}

/**
 * Models known to support extended thinking via `think` parameter
 */
export const OLLAMA_THINKING_MODELS = [
  'qwen3',
  'deepseek-r1',
  'deepseek-v3',
  'gpt-oss',
] as const

/**
 * Check if an Ollama model supports thinking
 * (Not reported in capabilities, must check model name)
 */
export function ollamaSupportsThinking(modelName: string): boolean {
  const lower = modelName.toLowerCase()
  return OLLAMA_THINKING_MODELS.some((m) => lower.includes(m))
}

/**
 * Known Ollama embedding model dimensions.
 * Used as fallback when model doesn't report dimensions.
 * NOT exhaustive - Ollama models are discovered dynamically via /api/tags.
 */
export const OLLAMA_EMBEDDING_DIMENSIONS: Record<string, number> = {
  'embeddinggemma': 768,
  'qwen3-embedding': 1024,
  'all-minilm': 384,
  'nomic-embed-text': 768,
  'mxbai-embed-large': 1024,
}

/**
 * Get embedding dimensions for an Ollama model.
 * Returns undefined if unknown (caller should query the model or use default).
 */
export function getOllamaEmbeddingDimensions(modelName: string): number | undefined {
  const lower = modelName.toLowerCase()
  for (const [key, dims] of Object.entries(OLLAMA_EMBEDDING_DIMENSIONS)) {
    if (lower.includes(key)) return dims
  }
  return undefined
}

// ============================================
// Ollama Dynamic Discovery
// ============================================

/**
 * Ollama backend configuration.
 * Models are discovered dynamically, not hardcoded.
 */
export interface OllamaConfig {
  /** Ollama server URL (default: http://localhost:11434) */
  host: string
  /** Request timeout in milliseconds */
  timeout?: number
}

/**
 * Result of discovering an Ollama model's capabilities.
 * Combines /api/show response with our capability mapping.
 */
export interface OllamaDiscoveredModel {
  /** Model name as reported by Ollama */
  name: string
  /** Model family (e.g., 'llama', 'qwen', 'mistral') */
  family?: string
  /** Parameter size (e.g., '7B', '70B') */
  parameterSize?: string
  /** Quantization level (e.g., 'Q4_K_M') */
  quantization?: string
  /** Raw capabilities from Ollama */
  ollamaCapabilities: OllamaCapability[]
  /** Mapped to our LLMCapability type */
  capabilities: Set<LLMCapability>
  /** Whether this model supports embeddings */
  isEmbeddingModel: boolean
  /** Embedding dimensions (if embedding model) */
  embeddingDimensions?: number
}
