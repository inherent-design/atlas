/**
 * Shared Capability Types for Atlas Services
 *
 * Capability-first architecture: services advertise what they can do,
 * business logic queries capabilities before calling methods.
 *
 * This module provides:
 * - Service type classifications
 * - Capability enums per service type
 * - Base BackendDescriptor interface
 * - Type utilities for capability narrowing
 */

import type { ContentType } from './types.js'

// ============================================
// Service Types
// ============================================

/**
 * High-level service classifications in Atlas
 */
export type ServiceType = 'embedding' | 'llm' | 'reranker'

// ============================================
// Capability Enums
// ============================================

/**
 * Embedding service capabilities
 */
export type EmbeddingCapability =
  | 'text-embedding' // Basic text → vector
  | 'code-embedding' // Code-optimized embedding
  | 'contextualized-embedding' // Document-aware chunk embedding
  | 'multimodal-embedding' // PDF, image → vector

/**
 * LLM service capabilities
 *
 * Note: Task-specific uses (QNTM generation, consolidation) use 'json-completion'.
 * No separate capability needed - they're just JSON completion with specific prompts.
 */
export type LLMCapability =
  | 'text-completion' // Basic prompt → text
  | 'json-completion' // Structured output (JSON mode) - used for QNTM, consolidation
  | 'extended-thinking' // Chain-of-thought with budget
  | 'vision' // Image input processing
  | 'tool-use' // Function/tool calling
  | 'streaming' // Token-by-token output
  | 'long-context' // >200K token context

/**
 * Reranker service capabilities
 */
export type RerankerCapability =
  | 'text-reranking' // Query + docs → relevance scores
  | 'code-reranking' // Code-optimized reranking (Jina v2, Qwen3)
  | 'multilingual-reranking' // Cross-language reranking (Voyage-lite, Jina, Qwen3)

/**
 * Union of all capability types
 */
export type Capability = EmbeddingCapability | LLMCapability | RerankerCapability

// ============================================
// Backend Descriptor
// ============================================

/**
 * Base interface for all backend descriptors.
 *
 * Every backend (embedding, LLM, reranker) implements this to advertise:
 * - Identity (name)
 * - Capabilities (what it can do)
 * - Availability (is it currently usable)
 *
 * @template C - The capability type for this backend (e.g., LLMCapability)
 */
export interface BackendDescriptor<C extends string = string> {
  /** Unique identifier for this backend (e.g., 'anthropic:haiku', 'voyage:text') */
  readonly name: string

  /** Set of capabilities this backend provides */
  readonly capabilities: ReadonlySet<C>

  /**
   * Check if this backend is currently available.
   * May involve network calls (API health checks, model availability).
   */
  isAvailable(): Promise<boolean>

  /**
   * Type-safe capability check.
   * Use this before calling capability-specific methods.
   *
   * @example
   * if (backend.supports('json-completion')) {
   *   // TypeScript knows backend has completeJSON method
   *   await backend.completeJSON(prompt)
   * }
   */
  supports(cap: C): boolean
}

// ============================================
// Latency Classification
// ============================================

/**
 * Relative latency classification for backends.
 * Used for routing decisions (e.g., prefer faster for real-time).
 */
export type LatencyClass = 'fastest' | 'fast' | 'moderate' | 'slow'

// ============================================
// Pricing Information
// ============================================

/**
 * Pricing information for metered backends.
 * All prices in USD per million tokens.
 */
export interface PricingInfo {
  /** Cost per million input tokens */
  input: number
  /** Cost per million output tokens */
  output: number
  /** Optional: Cost for cached/prompt-cached tokens */
  cached?: number
}

// ============================================
// Content Type Classification
// ============================================

/**
 * Content type for routing to appropriate backend/vector
 * Re-exported from shared/types.ts for convenience
 */
export type { ContentType }

/**
 * Embedding strategy for content
 */
export type EmbeddingStrategy = 'snippet' | 'contextualized' | 'multimodal'

/**
 * Result of content classification (used for embedding routing)
 */
export interface ContentClassification {
  /** Primary content type */
  contentType: ContentType
  /** Recommended embedding strategy */
  strategy: EmbeddingStrategy
  /** Confidence in classification (0.0-1.0) */
  confidence: number
  /** Optional: Preferred capability to use */
  preferredCapability?: EmbeddingCapability
}

// ============================================
// Type Guards and Utilities
// ============================================

/**
 * Check if a capability is an embedding capability
 */
export function isEmbeddingCapability(cap: Capability): cap is EmbeddingCapability {
  return [
    'text-embedding',
    'code-embedding',
    'contextualized-embedding',
    'multimodal-embedding',
  ].includes(cap)
}

/**
 * Check if a capability is an LLM capability
 */
export function isLLMCapability(cap: Capability): cap is LLMCapability {
  return [
    'text-completion',
    'json-completion',
    'extended-thinking',
    'vision',
    'tool-use',
    'streaming',
    'long-context',
  ].includes(cap)
}

/**
 * Check if a capability is a reranker capability
 */
export function isRerankerCapability(cap: Capability): cap is RerankerCapability {
  return ['text-reranking', 'code-reranking', 'multilingual-reranking'].includes(cap)
}

/**
 * Get service type from capability
 */
export function getServiceType(cap: Capability): ServiceType {
  if (isEmbeddingCapability(cap)) return 'embedding'
  if (isLLMCapability(cap)) return 'llm'
  if (isRerankerCapability(cap)) return 'reranker'
  throw new Error(`Unknown capability: ${cap}`)
}
