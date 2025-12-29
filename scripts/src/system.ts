/**
 * System Monitoring and Capacity Assessment
 *
 * Cross-platform resource monitoring using systeminformation + bun-webgpu.
 * Enables intelligent workload scheduling based on CPU/memory pressure.
 */

import si from 'systeminformation'
import { createLogger } from './logger'

const log = createLogger('system')

export type PressureLevel = 'nominal' | 'warning' | 'critical'

export interface SystemCapacity {
  canSpawnWorker: boolean
  cpuUtilization: number
  memoryUtilization: number
  pressureLevel: PressureLevel
  details: {
    availableMemory: number
    swapUsage: number
    currentLoad: number
    totalMemory: number
    usedMemory: number
  }
}

export interface GPUCapability {
  available: boolean
  maxBufferSize?: number
  maxTextureDimension2D?: number
  vendor?: string
  error?: string
}

/**
 * Assess current system capacity for spawning workers
 *
 * Based on:
 * - CPU load (< 70% for nominal)
 * - Available memory (> 15% free)
 * - Swap usage (< 40% for nominal)
 * - Memory pressure classification
 */
export async function assessSystemCapacity(): Promise<SystemCapacity> {
  try {
    const [mem, cpu] = await Promise.all([si.mem(), si.currentLoad()])

    log.trace('Raw system stats', {
      memTotal: mem.total,
      memUsed: mem.used,
      memAvailable: mem.available,
      swapTotal: mem.swaptotal,
      swapUsed: mem.swapused,
      cpuLoad: cpu.currentLoad,
    })

    const memRatio = mem.used / mem.total
    const availRatio = mem.available / mem.total
    const swapRatio = mem.swaptotal > 0 ? mem.swapused / mem.swaptotal : 0

    // Pressure classification (matches macOS/Linux kernel semantics)
    let pressureLevel: PressureLevel = 'nominal'
    if (swapRatio > 0.5 || memRatio > 0.85) pressureLevel = 'warning'
    if (swapRatio > 0.75 || memRatio > 0.95) pressureLevel = 'critical'

    const canSpawnWorker =
      cpu.currentLoad < 70 && availRatio > 0.15 && swapRatio < 0.4 && pressureLevel !== 'critical'

    const capacity: SystemCapacity = {
      canSpawnWorker,
      cpuUtilization: cpu.currentLoad,
      memoryUtilization: memRatio * 100,
      pressureLevel,
      details: {
        availableMemory: mem.available,
        swapUsage: mem.swapused,
        currentLoad: cpu.currentLoad,
        totalMemory: mem.total,
        usedMemory: mem.used,
      },
    }

    log.debug('System capacity assessed', {
      canSpawnWorker,
      pressureLevel,
      cpuUtilization: capacity.cpuUtilization.toFixed(1),
      memoryUtilization: capacity.memoryUtilization.toFixed(1),
      availableMemoryGB: (mem.available / 1024 / 1024 / 1024).toFixed(2),
    })

    return capacity
  } catch (error) {
    log.error('Failed to assess system capacity', error as Error)
    // Fail open: allow worker spawn if monitoring fails
    return {
      canSpawnWorker: true,
      cpuUtilization: 0,
      memoryUtilization: 0,
      pressureLevel: 'nominal',
      details: {
        availableMemory: 0,
        swapUsage: 0,
        currentLoad: 0,
        totalMemory: 0,
        usedMemory: 0,
      },
    }
  }
}

/**
 * Get GPU capabilities via WebGPU (cross-vendor)
 *
 * NOTE: Requires GPU initialization, heavier than system stats.
 * Use sparingly for capability detection, not pressure monitoring.
 */
export async function getGPUCapabilities(): Promise<GPUCapability> {
  try {
    // Dynamically import bun-webgpu to avoid loading if not needed
    const { setupGlobals } = await import('bun-webgpu')
    setupGlobals()

    log.trace('Requesting WebGPU adapter')

    const adapter = await (navigator as any).gpu?.requestAdapter()
    if (!adapter) {
      log.debug('No WebGPU adapter available')
      return { available: false, error: 'No GPU adapter found' }
    }

    const limits = adapter.limits

    log.debug('WebGPU adapter detected', {
      maxBufferSize: limits.maxBufferSize,
      maxTextureDimension2D: limits.maxTextureDimension2D,
    })

    return {
      available: true,
      maxBufferSize: limits.maxBufferSize,
      maxTextureDimension2D: limits.maxTextureDimension2D,
      vendor: 'unknown', // WebGPU doesn't expose vendor for fingerprinting
    }
  } catch (error) {
    log.warn('GPU capability detection failed', { error: (error as Error).message })
    return { available: false, error: (error as Error).message }
  }
}

/**
 * Get concurrency limit based on system pressure
 *
 * Dynamically adjusts worker count based on available resources.
 * Falls back to static calculation if monitoring fails.
 */
export async function getRecommendedConcurrency(
  staticLimit: number,
  minWorkers = 1,
  maxWorkers = 10
): Promise<number> {
  try {
    const capacity = await assessSystemCapacity()

    if (capacity.pressureLevel === 'critical') {
      log.warn('Critical system pressure, limiting to minimum workers', { minWorkers })
      return minWorkers
    }

    if (capacity.pressureLevel === 'warning') {
      const reduced = Math.max(minWorkers, Math.floor(staticLimit * 0.5))
      log.info('System pressure warning, reducing concurrency', {
        from: staticLimit,
        to: reduced,
      })
      return reduced
    }

    // Nominal pressure: use static limit
    const capped = Math.min(staticLimit, maxWorkers)
    log.debug('Nominal system pressure, using static concurrency', { concurrency: capped })
    return capped
  } catch (error) {
    log.error('Failed to get recommended concurrency, using static limit', error as Error)
    return Math.min(staticLimit, maxWorkers)
  }
}
