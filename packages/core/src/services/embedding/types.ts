/**
 * Embedding Service Types
 *
 * Capability interfaces for embedding backends.
 * Each capability is a mixin interface that backends can implement.
 *
 * Backend implementations:
 * - VoyageSnippetBackend (voyage-3-large): text-embedding
 * - VoyageCodeBackend (voyage-code-3): text-embedding, code-embedding
 * - VoyageContextBackend (voyage-context-3): text-embedding, contextualized-embedding
 * - VoyageMultimodalBackend (voyage-multimodal-3.5): text-embedding, multimodal-embedding
 * - OllamaEmbeddingBackend (nomic-embed-text, etc.): text-embedding
 */

import type {
  BackendDescriptor,
  EmbeddingCapability,
  EmbeddingStrategy,
  LatencyClass,
  PricingInfo,
} from '../../shared/capabilities.js'

// Re-export for backend implementations
export type { EmbeddingCapability, EmbeddingStrategy } from '../../shared/capabilities.js'

// ============================================
// Result Types
// ============================================

/**
 * Result from an embedding operation
 */
export interface EmbeddingResult {
  /** The embedding vector */
  embedding: number[]
  /** Model used to generate this embedding */
  model: string
  /** Strategy used (snippet, contextualized, multimodal) */
  strategy: EmbeddingStrategy
  /** Vector dimensions */
  dimensions: number
}

/**
 * Result from a contextualized embedding operation.
 * Includes document and chunk indices for reassembly.
 */
export interface ContextualizedEmbeddingResult extends EmbeddingResult {
  /** Index of the document in the batch */
  documentIndex: number
  /** Index of the chunk within the document */
  chunkIndex: number
}

/**
 * Result from a multimodal embedding operation.
 * May include extracted text for transparency.
 */
export interface MultimodalEmbeddingResult extends EmbeddingResult {
  /** MIME type of the input */
  mimeType: string
  /** Extracted text (if applicable, for debugging) */
  extractedText?: string
}

/**
 * Unified batch embedding result.
 * Normalizes responses from different providers (Voyage, Ollama, OpenAI).
 *
 * Provider response mapping:
 * - Voyage: response.data[i].embedding → embeddings[i]
 * - Ollama: response.embeddings[i] → embeddings[i]
 * - OpenAI: response.data[i].embedding → embeddings[i]
 */
export interface BatchEmbeddingResult {
  /** Embedding vectors, one per input */
  embeddings: number[][]
  /** Model identifier that produced these embeddings */
  model: string
  /** Strategy used (snippet, contextualized, code) */
  strategy: EmbeddingStrategy
  /** Vector dimensions */
  dimensions: number
  /** Usage statistics (optional, provider-dependent) */
  usage?: {
    /** Number of input tokens processed */
    inputTokens: number
    /** Processing duration in milliseconds (Ollama) */
    durationMs?: number
  }
}

// ============================================
// Backend Descriptor
// ============================================

/**
 * Embedding backend descriptor.
 * Extends base descriptor with embedding-specific metadata.
 * Capabilities (embedText, embedCode, etc.) are optional and capability-specific.
 */
export interface EmbeddingBackend
  extends BackendDescriptor<EmbeddingCapability>, Partial<CanEmbedText>, Partial<CanEmbedCode> {
  /** Vector dimensions produced by this backend */
  readonly dimensions: number

  /** Maximum tokens per embedding request */
  readonly maxTokens: number

  /** Model identifier (e.g., 'voyage-3-large') */
  readonly model: string

  /** Relative latency classification */
  readonly latency: LatencyClass

  /** Pricing information (if metered) */
  readonly pricing?: PricingInfo

  /** Maximum batch size (optional, defaults to 32 if not specified) */
  readonly maxBatchSize?: number
}

// ============================================
// Capability Interfaces (Mixins)
// ============================================

/**
 * Basic text embedding capability.
 * Most backends implement this.
 */
export interface CanEmbedText {
  /**
   * Embed text content.
   *
   * @param input - Single string or array of strings
   * @returns Batch embedding result with all vectors
   */
  embedText(input: string | string[]): Promise<BatchEmbeddingResult>
}

/**
 * Code-optimized embedding capability.
 * Uses models trained on code structure and semantics.
 */
export interface CanEmbedCode {
  /**
   * Embed code content with code-optimized model.
   *
   * @param input - Single code string or array
   * @param language - Optional language hint (e.g., 'typescript', 'python')
   * @returns Batch embedding result with all vectors
   */
  embedCode(input: string | string[], language?: string): Promise<BatchEmbeddingResult>
}

/**
 * Contextualized embedding capability.
 * Embeds chunks with awareness of document context.
 *
 * @see https://docs.voyageai.com/docs/embeddings#voyage-context-3
 */
export interface CanEmbedContextualized {
  /**
   * Embed chunks with document context.
   *
   * Each chunk is embedded with awareness of its neighboring chunks
   * in the document, improving retrieval for context-dependent content.
   *
   * @param documents - Array of documents, each document is array of chunks
   * @returns 2D array: results[docIndex][chunkIndex]
   */
  embedContextualized(documents: string[][]): Promise<ContextualizedEmbeddingResult[][]>
}

/**
 * Multimodal embedding capability.
 * Handles PDFs, images, and other non-text content.
 */
export interface CanEmbedMultimodal {
  /**
   * Embed multimodal content (PDF, image, etc.)
   *
   * @param input - Buffer containing the file content
   * @param mimeType - MIME type of the content (e.g., 'application/pdf', 'image/png')
   * @returns Single embedding result
   */
  embedMultimodal(input: Buffer, mimeType: string): Promise<MultimodalEmbeddingResult>

  /**
   * Check if a MIME type is supported.
   *
   * @param mimeType - MIME type to check
   * @returns true if this backend can embed this content type
   */
  supportsMimeType(mimeType: string): boolean
}

// ============================================
// Capability Map (for type narrowing)
// ============================================

/**
 * Maps capability strings to their interface types.
 * Used for type-safe capability checking.
 *
 * @example
 * function embedWithCapability<C extends EmbeddingCapability>(
 *   backend: EmbeddingBackend & EmbeddingCapabilityMap[C],
 *   capability: C
 * ) { ... }
 */
export type EmbeddingCapabilityMap = {
  'text-embedding': CanEmbedText
  'code-embedding': CanEmbedCode
  'contextualized-embedding': CanEmbedContextualized
  'multimodal-embedding': CanEmbedMultimodal
}

// ============================================
// Configuration Types
// ============================================

/**
 * Options for embedding operations
 */
export interface EmbedOptions {
  /** Temperature for embedding model (if applicable) */
  temperature?: number
  /** Truncate input to fit max tokens instead of erroring */
  truncate?: boolean
  /** Output dimensions (for models that support flexible dimensions) */
  outputDimensions?: number
}

// ============================================
// File Type Detection
// ============================================

/**
 * File extensions that should use code-optimized embeddings
 */
export const CODE_EXTENSIONS = ['.ts', '.tsx', '.js', '.jsx', '.py', '.rs', '.go', '.sh'] as const

/**
 * File extensions for text-based content (documents, configs, data)
 * All get chunked and embedded as text.
 *
 * Includes:
 * - Documents: .md, .txt, .rst, .html (prose with semantic flow)
 * - Configs/Data: .json, .yaml, .yml, .toml, .csv (self-contained)
 */
export const TEXT_EXTENSIONS = [
  '.md',
  '.txt',
  '.rst',
  '.html',
  '.json',
  '.yaml',
  '.yml',
  '.toml',
  '.csv',
] as const

/**
 * File extensions that require multimodal embeddings
 */
export const MEDIA_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.webp'] as const

/**
 * MIME types supported by multimodal embedding
 */
export const MULTIMODAL_MIME_TYPES = [
  'application/pdf',
  'image/png',
  'image/jpeg',
  'image/gif',
  'image/webp',
] as const

export type MultimodalMimeType = (typeof MULTIMODAL_MIME_TYPES)[number]

/**
 * Get all file extensions that Atlas can embed.
 * Used by FileWatcher to filter watchable files.
 *
 * @returns Array of all embeddable file extensions
 */
export function getAllEmbeddableExtensions(): string[] {
  return [...TEXT_EXTENSIONS, ...CODE_EXTENSIONS, ...MEDIA_EXTENSIONS]
}

// ============================================
// Content Type Detection
// ============================================

/**
 * Content type classification based on file extension
 */
export type ContentType = 'text' | 'code' | 'media'

/**
 * Detect content type from file path.
 *
 * @param filePath - Path to file (uses extension)
 * @returns Content type classification
 */
export function detectContentType(filePath: string): ContentType {
  const ext = filePath.slice(filePath.lastIndexOf('.')).toLowerCase()

  if (CODE_EXTENSIONS.includes(ext as any)) return 'code'
  if (TEXT_EXTENSIONS.includes(ext as any)) return 'text'
  if (MEDIA_EXTENSIONS.includes(ext as any)) return 'media'

  return 'text' // Default to text for unknown extensions
}

/**
 * Determine which named vectors are required for a content type.
 *
 * @param contentType - Content type from detectContentType()
 * @returns Array of vector names that should be generated
 */
export function getRequiredVectors(contentType: ContentType): ('text' | 'code' | 'media')[] {
  switch (contentType) {
    case 'code':
      return ['text', 'code'] // Code files get both text and code vectors
    case 'text':
      return ['text'] // Text/documents get only text vector
    case 'media':
      return ['text', 'media'] // Media gets text (from extraction) + media vector
    default:
      return ['text']
  }
}
