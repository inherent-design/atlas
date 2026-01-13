/**
 * Generic Backend Registry
 *
 * Provides capability-indexed registration and lookup for any backend type.
 * Used by embedding, LLM, and reranker services.
 *
 * Features:
 * - Register backends by name
 * - Index by capabilities for fast lookup
 * - Query available backends (with health checks)
 * - Get backends by capability or name
 */

import type { BackendDescriptor } from './capabilities.js'
import { createLogger } from './logger.js'

const log = createLogger('registry')

/**
 * Generic registry for capability-based backend lookup.
 *
 * @template B - Backend type (must extend BackendDescriptor)
 *
 * @example
 * const llmRegistry = new BackendRegistry<LLMBackend>()
 * llmRegistry.register(new AnthropicBackend('haiku'))
 * llmRegistry.register(new OllamaLLMBackend('ministral'))
 *
 * const backend = llmRegistry.getFor('json-completion')
 * if (backend) await backend.completeJSON(prompt)
 */
export class BackendRegistry<B extends BackendDescriptor<string>> {
  private backends = new Map<string, B>()
  private capabilityIndex = new Map<string, Set<string>>()

  /**
   * Register a backend in the registry.
   * Automatically indexes by all advertised capabilities.
   *
   * @param backend - Backend to register
   * @throws If backend with same name already exists
   */
  register(backend: B): void {
    if (this.backends.has(backend.name)) {
      log.warn('Backend already registered, replacing', { name: backend.name })
    }

    this.backends.set(backend.name, backend)

    // Index by capabilities
    for (const cap of backend.capabilities) {
      if (!this.capabilityIndex.has(cap)) {
        this.capabilityIndex.set(cap, new Set())
      }
      this.capabilityIndex.get(cap)!.add(backend.name)
    }

    log.debug('Backend registered', {
      name: backend.name,
      capabilities: [...backend.capabilities],
    })
  }

  /**
   * Unregister a backend by name.
   * Removes from capability index as well.
   *
   * @param name - Backend name to remove
   * @returns true if backend was removed, false if not found
   */
  unregister(name: string): boolean {
    const backend = this.backends.get(name)
    if (!backend) return false

    // Remove from capability index
    for (const cap of backend.capabilities) {
      const names = this.capabilityIndex.get(cap)
      if (names) {
        names.delete(name)
        if (names.size === 0) {
          this.capabilityIndex.delete(cap)
        }
      }
    }

    this.backends.delete(name)
    log.debug('Backend unregistered', { name })
    return true
  }

  /**
   * Get a specific backend by name.
   *
   * @param name - Backend name (e.g., 'anthropic:haiku')
   * @returns Backend or undefined if not found
   */
  get(name: string): B | undefined {
    return this.backends.get(name)
  }

  /**
   * Get first backend that supports a capability.
   * Useful when you just need any backend that can do X.
   *
   * @param capability - Capability to look for
   * @returns First matching backend or undefined
   */
  getFor(capability: string): B | undefined {
    const names = this.capabilityIndex.get(capability)
    if (!names?.size) return undefined
    const firstName = [...names][0]!
    return this.backends.get(firstName)
  }

  /**
   * Get all backends that support a capability.
   * Useful for fallback chains or parallel execution.
   *
   * @param capability - Capability to look for
   * @returns Array of matching backends (may be empty)
   */
  getAllFor(capability: string): B[] {
    const names = this.capabilityIndex.get(capability) ?? new Set()
    return [...names].map((n) => this.backends.get(n)!).filter(Boolean)
  }

  /**
   * Get all registered backends.
   *
   * @returns Array of all backends
   */
  getAll(): B[] {
    return [...this.backends.values()]
  }

  /**
   * Get all currently available backends.
   * Calls isAvailable() on each backend (may involve network calls).
   *
   * @returns Array of available backends
   */
  async getAvailable(): Promise<B[]> {
    const available: B[] = []

    for (const backend of this.backends.values()) {
      try {
        if (await backend.isAvailable()) {
          available.push(backend)
        }
      } catch (error) {
        log.warn('Backend availability check failed', {
          name: backend.name,
          error: (error as Error).message,
        })
      }
    }

    return available
  }

  /**
   * Get first available backend that supports a capability.
   * Useful for automatic fallback when primary backend is down.
   *
   * @param capability - Capability to look for
   * @returns First available matching backend or undefined
   */
  async getAvailableFor(capability: string): Promise<B | undefined> {
    const backends = this.getAllFor(capability)

    for (const backend of backends) {
      try {
        if (await backend.isAvailable()) {
          return backend
        }
      } catch {
        // Continue to next backend
      }
    }

    return undefined
  }

  /**
   * Check if any backend supports a capability.
   *
   * @param capability - Capability to check
   * @returns true if at least one backend supports it
   */
  hasCapability(capability: string): boolean {
    return (this.capabilityIndex.get(capability)?.size ?? 0) > 0
  }

  /**
   * Get all registered capabilities across all backends.
   *
   * @returns Array of capability strings
   */
  getCapabilities(): string[] {
    return [...this.capabilityIndex.keys()]
  }

  /**
   * Get count of registered backends.
   */
  get size(): number {
    return this.backends.size
  }

  /**
   * Clear all registered backends.
   * Useful for testing.
   */
  clear(): void {
    this.backends.clear()
    this.capabilityIndex.clear()
    log.debug('Registry cleared')
  }
}
