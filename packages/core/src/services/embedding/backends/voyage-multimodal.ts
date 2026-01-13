/**
 * Voyage AI Multimodal Embedding Backend
 *
 * Implements EmbeddingBackend + CanEmbedMultimodal for Voyage AI multimodal models:
 * - VoyageMultimodalBackend (voyage-multimodal-3): image-embedding capability
 *
 * Supports:
 * - Images: PNG, JPEG, WEBP, GIF
 * - Input formats: base64-encoded data URLs
 * - 1024-dimensional vectors (same as text/code)
 */

import { VoyageAIClient } from 'voyageai'
import { VOYAGE_API_KEY } from '../../../shared/config.js'
import { createLogger } from '../../../shared/logger.js'
import { createSingleton } from '../../../shared/utils.js'
import { MULTIMODAL_MIME_TYPES } from '../types.js'
import type {
  EmbeddingBackend,
  EmbeddingCapability,
  CanEmbedMultimodal,
  MultimodalEmbeddingResult,
  MultimodalMimeType,
} from '../types.js'

const log = createLogger('embedding:voyage-multimodal')

// Singleton Voyage client
function createVoyageClient(): VoyageAIClient {
  if (!VOYAGE_API_KEY) {
    throw new Error('VOYAGE_API_KEY environment variable not set')
  }
  return new VoyageAIClient({ apiKey: VOYAGE_API_KEY })
}

const voyageSingleton = createSingleton(createVoyageClient, 'voyage')

/**
 * Convert Buffer to base64 data URL format required by Voyage API
 *
 * @param buffer - Image buffer
 * @param mimeType - MIME type (e.g., 'image/png')
 * @returns Base64 data URL in format: data:image/png;base64,<data>
 */
function bufferToDataURL(buffer: Buffer, mimeType: string): string {
  const base64 = buffer.toString('base64')
  return `data:${mimeType};base64,${base64}`
}

/**
 * Voyage Multimodal Backend (voyage-multimodal-3)
 *
 * Capabilities: multimodal-embedding
 * Use for: Images (PNG, JPEG, WEBP, GIF), PDFs with visual content
 */
export class VoyageMultimodalBackend implements EmbeddingBackend, CanEmbedMultimodal {
  readonly name = 'voyage:multimodal'
  readonly capabilities: ReadonlySet<EmbeddingCapability> = new Set(['multimodal-embedding'])
  readonly dimensions = 1024
  readonly maxTokens = 32000 // 32K token context
  readonly model = 'voyage-multimodal-3'
  readonly latency = 'moderate' as const
  readonly pricing = { input: 0.08, output: 0 } // Same pricing as text embeddings

  private client: VoyageAIClient

  constructor() {
    this.client = voyageSingleton.get()
  }

  async isAvailable(): Promise<boolean> {
    if (!VOYAGE_API_KEY) {
      return false
    }

    try {
      // Test with minimal request (single pixel image as base64)
      // 1x1 transparent PNG: 68 bytes
      const testImage =
        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='

      await this.client.multimodalEmbed({
        inputs: [{ content: [{ type: 'image_base64', imageBase64: testImage }] }],
        model: this.model,
      })
      return true
    } catch (error) {
      log.warn('Voyage multimodal availability check failed', { error: (error as Error).message })
      return false
    }
  }

  supports(cap: EmbeddingCapability): boolean {
    return this.capabilities.has(cap)
  }

  /**
   * Check if a MIME type is supported by this backend
   */
  supportsMimeType(mimeType: string): boolean {
    return (MULTIMODAL_MIME_TYPES as readonly string[]).includes(mimeType)
  }

  /**
   * Embed multimodal content (images)
   *
   * @param input - Image buffer
   * @param mimeType - MIME type (e.g., 'image/png', 'image/jpeg')
   * @returns Multimodal embedding result
   */
  async embedMultimodal(input: Buffer, mimeType: string): Promise<MultimodalEmbeddingResult> {
    if (!this.supportsMimeType(mimeType)) {
      throw new Error(
        `Unsupported MIME type: ${mimeType}. Supported: ${MULTIMODAL_MIME_TYPES.join(', ')}`
      )
    }

    // Convert buffer to data URL format
    const dataURL = bufferToDataURL(input, mimeType)

    log.debug('Voyage multimodal embed request', {
      model: this.model,
      mimeType,
      bufferSize: input.length,
    })

    const response = await this.client.multimodalEmbed({
      inputs: [
        {
          content: [
            {
              type: 'image_base64',
              imageBase64: dataURL,
            },
          ],
        },
      ],
      model: this.model,
      inputType: 'document', // Default to document type for indexing
    })

    const embedding = response.data?.[0]?.embedding
    if (!embedding) {
      throw new Error('No embedding returned from Voyage multimodal API')
    }

    log.debug('Voyage multimodal embed success', {
      model: this.model,
      dimensions: embedding.length,
      usage: response.usage,
    })

    return {
      embedding,
      model: this.model,
      strategy: 'multimodal',
      dimensions: this.dimensions,
      mimeType,
    }
  }
}
