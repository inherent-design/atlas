/**
 * Tokenization Service
 *
 * Provides accurate token counting for Voyage AI models using
 * HuggingFace transformers.js tokenizers.
 *
 * Used for:
 * - Pre-validating documents against 32K context window
 * - Splitting large documents into sub-documents
 */

import { AutoTokenizer, type PreTrainedTokenizer } from '@huggingface/transformers'
import { createLogger } from '../../shared/logger'
import { createSingleton } from '../../shared/utils'

const log = createLogger('tokenization')

// Voyage models use this tokenizer (from HuggingFace hub)
const VOYAGE_TOKENIZER_MODEL = 'voyageai/voyage-3'

// Context window limits
export const VOYAGE_CONTEXT_WINDOW = 32000
export const VOYAGE_SAFE_LIMIT = 28000 // Safety margin for splitting

/**
 * Lazy-loaded tokenizer singleton
 */
let tokenizer: PreTrainedTokenizer | null = null
let tokenizerLoading: Promise<PreTrainedTokenizer> | null = null

async function loadTokenizer(): Promise<PreTrainedTokenizer> {
  if (tokenizer) return tokenizer

  if (tokenizerLoading) return tokenizerLoading

  tokenizerLoading = (async () => {
    log.debug('Loading Voyage tokenizer', { model: VOYAGE_TOKENIZER_MODEL })
    const t = await AutoTokenizer.from_pretrained(VOYAGE_TOKENIZER_MODEL)
    tokenizer = t
    log.info('Voyage tokenizer loaded', { model: VOYAGE_TOKENIZER_MODEL })
    return t
  })()

  return tokenizerLoading
}

/**
 * Count tokens in a single text string
 */
export async function countTokens(text: string): Promise<number> {
  const t = await loadTokenizer()
  const encoded = await t.encode(text)
  return encoded.length
}

/**
 * Count total tokens across multiple chunks
 */
export async function countTotalTokens(chunks: string[]): Promise<number> {
  const t = await loadTokenizer()
  let total = 0
  for (const chunk of chunks) {
    const encoded = await t.encode(chunk)
    total += encoded.length
  }
  return total
}

/**
 * Fast token estimation (chars / 4)
 * Use when exact count not needed and speed matters
 */
export function estimateTokens(text: string): number {
  return Math.ceil(text.length / 4)
}

/**
 * Fast total token estimation for chunks
 */
export function estimateTotalTokens(chunks: string[]): number {
  return chunks.reduce((sum, chunk) => sum + estimateTokens(chunk), 0)
}

/**
 * Split chunks into sub-documents that fit within token limit.
 *
 * Uses accurate token counting for precise splitting.
 * Each sub-document is guaranteed to be under maxTokens.
 *
 * @param chunks - Array of text chunks from a single document
 * @param maxTokens - Maximum tokens per sub-document (default: 28000)
 * @returns Array of sub-documents, each containing a subset of chunks
 */
export async function splitIntoDocuments(
  chunks: string[],
  maxTokens: number = VOYAGE_SAFE_LIMIT
): Promise<string[][]> {
  const t = await loadTokenizer()
  const documents: string[][] = []
  let currentDoc: string[] = []
  let currentTokens = 0

  for (const chunk of chunks) {
    const encoded = await t.encode(chunk)
    const chunkTokens = encoded.length

    // If adding this chunk exceeds limit, start new document
    if (currentTokens + chunkTokens > maxTokens && currentDoc.length > 0) {
      documents.push(currentDoc)
      currentDoc = []
      currentTokens = 0
    }

    currentDoc.push(chunk)
    currentTokens += chunkTokens
  }

  // Don't forget the last document
  if (currentDoc.length > 0) {
    documents.push(currentDoc)
  }

  log.debug('Split document into sub-documents', {
    originalChunks: chunks.length,
    subDocuments: documents.length,
    maxTokens,
  })

  return documents
}

/**
 * Fast split using token estimation (chars / 4)
 *
 * Use when:
 * - Processing many files and speed matters
 * - Exact boundaries not critical (has safety margin built in)
 */
export function splitIntoDocumentsFast(
  chunks: string[],
  maxTokens: number = VOYAGE_SAFE_LIMIT
): string[][] {
  const documents: string[][] = []
  let currentDoc: string[] = []
  let currentTokens = 0

  for (const chunk of chunks) {
    const chunkTokens = estimateTokens(chunk)

    if (currentTokens + chunkTokens > maxTokens && currentDoc.length > 0) {
      documents.push(currentDoc)
      currentDoc = []
      currentTokens = 0
    }

    currentDoc.push(chunk)
    currentTokens += chunkTokens
  }

  if (currentDoc.length > 0) {
    documents.push(currentDoc)
  }

  return documents
}

/**
 * Check if a document exceeds the context window
 */
export async function exceedsContextWindow(
  chunks: string[],
  limit: number = VOYAGE_CONTEXT_WINDOW
): Promise<boolean> {
  const total = await countTotalTokens(chunks)
  return total > limit
}

/**
 * Fast check using estimation
 */
export function exceedsContextWindowFast(
  chunks: string[],
  limit: number = VOYAGE_CONTEXT_WINDOW
): boolean {
  return estimateTotalTokens(chunks) > limit
}
