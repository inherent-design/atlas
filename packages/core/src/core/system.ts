/**
 * System Monitoring and Capacity Assessment
 *
 * Cross-platform resource monitoring using native commands (no systeminformation).
 * Enables intelligent workload scheduling based on CPU/memory pressure.
 *
 * Platform support:
 * - macOS: memory_pressure, sysctl, vm.loadavg
 * - Linux: /proc/meminfo, /proc/loadavg, nproc
 * - Windows: TODO (fails open for now)
 */

import { createLogger } from '../shared/logger'

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

/** Raw memory stats from platform-specific parsing */
interface MemoryStats {
  total: number // bytes
  available: number // bytes
  used: number // bytes
  swapTotal: number // bytes
  swapUsed: number // bytes
  freePercent?: number // macOS memory_pressure gives this directly
}

/** Raw CPU stats */
interface CPUStats {
  loadAvg1m: number
  loadAvg5m: number
  loadAvg15m: number
  cpuCount: number
}

// Simple TTL cache to avoid hammering shell on rapid calls
let cachedCapacity: { data: SystemCapacity; timestamp: number } | null = null
const CACHE_TTL_MS = 1000 // 1 second

/**
 * Reset capacity cache for testing.
 * Enables deterministic cache testing without real delays.
 * @internal Test-only export
 */
export function _resetCapacityCache(): void {
  cachedCapacity = null
}

/**
 * Run a shell command and return stdout
 */
function runCommand(cmd: string[]): string | null {
  try {
    const proc = Bun.spawnSync(cmd, { stdout: 'pipe', stderr: 'pipe' })
    if (proc.success) {
      return proc.stdout.toString().trim()
    }
    log.trace('Command failed', { cmd: cmd.join(' '), stderr: proc.stderr.toString() })
    return null
  } catch (error) {
    log.trace('Command error', { cmd: cmd.join(' '), error: (error as Error).message })
    return null
  }
}

/**
 * Parse macOS memory stats from memory_pressure and sysctl
 */
function parseMacOSMemory(): MemoryStats | null {
  // Get total memory from sysctl
  const memSizeStr = runCommand(['sysctl', '-n', 'hw.memsize'])
  if (!memSizeStr) return null
  const total = parseInt(memSizeStr, 10)

  // Get memory pressure (includes free percentage)
  const pressureOutput = runCommand(['memory_pressure'])
  if (!pressureOutput) {
    // Fallback: use vm_stat if memory_pressure unavailable
    return parseMacOSVmStat(total)
  }

  // Parse "System-wide memory free percentage: XX%"
  const freeMatch = pressureOutput.match(/System-wide memory free percentage:\s*(\d+)%/)
  const freePercent = freeMatch?.[1] ? parseInt(freeMatch[1], 10) : null

  if (freePercent === null) {
    return parseMacOSVmStat(total)
  }

  const available = Math.floor(total * (freePercent / 100))
  const used = total - available

  // macOS typically has no swap or minimal swap
  // Parse swap from memory_pressure output if present
  const swapInMatch = pressureOutput.match(/Swapins:\s*(\d+)/)
  const swapOutMatch = pressureOutput.match(/Swapouts:\s*(\d+)/)
  const hasSwapActivity =
    (swapInMatch?.[1] && parseInt(swapInMatch[1], 10) > 0) ||
    (swapOutMatch?.[1] && parseInt(swapOutMatch[1], 10) > 0)

  return {
    total,
    available,
    used,
    swapTotal: 0, // macOS doesn't expose swap size easily
    swapUsed: hasSwapActivity ? 1 : 0, // Binary indicator
    freePercent,
  }
}

/**
 * Fallback: parse macOS vm_stat for memory stats
 */
function parseMacOSVmStat(total: number): MemoryStats | null {
  const vmStatOutput = runCommand(['vm_stat'])
  if (!vmStatOutput) return null

  // Parse page size
  const pageSizeMatch = vmStatOutput.match(/page size of (\d+) bytes/)
  const pageSize = pageSizeMatch?.[1] ? parseInt(pageSizeMatch[1], 10) : 16384

  // Parse page counts
  const parsePages = (key: string): number => {
    const match = vmStatOutput.match(new RegExp(`${key}:\\s*([\\d.]+)`))
    return match?.[1] ? Math.floor(parseFloat(match[1])) : 0
  }

  const pagesFree = parsePages('Pages free')
  const pagesActive = parsePages('Pages active')
  const pagesInactive = parsePages('Pages inactive')
  const pagesSpeculative = parsePages('Pages speculative')
  const pagesWired = parsePages('Pages wired down')
  const pagesPurgeable = parsePages('Pages purgeable')

  // Available = free + inactive + purgeable (roughly)
  const availablePages = pagesFree + pagesInactive + pagesPurgeable
  const usedPages = pagesActive + pagesWired

  return {
    total,
    available: availablePages * pageSize,
    used: usedPages * pageSize,
    swapTotal: 0,
    swapUsed: 0,
  }
}

/**
 * Parse macOS CPU stats from sysctl
 */
function parseMacOSCPU(): CPUStats | null {
  const loadAvgStr = runCommand(['sysctl', '-n', 'vm.loadavg'])
  const cpuCountStr = runCommand(['sysctl', '-n', 'hw.ncpu'])

  if (!loadAvgStr || !cpuCountStr) return null

  // Format: "{ 1.26 2.13 3.33 }"
  const loadMatch = loadAvgStr.match(/\{\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\}/)
  if (!loadMatch?.[1] || !loadMatch?.[2] || !loadMatch?.[3]) return null

  return {
    loadAvg1m: parseFloat(loadMatch[1]),
    loadAvg5m: parseFloat(loadMatch[2]),
    loadAvg15m: parseFloat(loadMatch[3]),
    cpuCount: parseInt(cpuCountStr, 10),
  }
}

/**
 * Parse Linux memory stats from /proc/meminfo
 */
function parseLinuxMemory(): MemoryStats | null {
  const meminfo = runCommand(['cat', '/proc/meminfo'])
  if (!meminfo) return null

  const parseKB = (key: string): number => {
    const match = meminfo.match(new RegExp(`${key}:\\s*(\\d+)\\s*kB`))
    return match?.[1] ? parseInt(match[1], 10) * 1024 : 0 // Convert to bytes
  }

  const total = parseKB('MemTotal')
  const available = parseKB('MemAvailable')
  const free = parseKB('MemFree')
  const swapTotal = parseKB('SwapTotal')
  const swapFree = parseKB('SwapFree')

  return {
    total,
    available: available || free, // MemAvailable is better but may not exist on old kernels
    used: total - (available || free),
    swapTotal,
    swapUsed: swapTotal - swapFree,
  }
}

/**
 * Parse Linux CPU stats from /proc/loadavg and nproc
 */
function parseLinuxCPU(): CPUStats | null {
  const loadavg = runCommand(['cat', '/proc/loadavg'])
  const cpuCountStr = runCommand(['nproc'])

  if (!loadavg || !cpuCountStr) return null

  // Format: "0.05 0.09 0.08 1/591 1005398"
  const parts = loadavg.split(' ')
  if (parts.length < 3 || !parts[0] || !parts[1] || !parts[2]) return null

  return {
    loadAvg1m: parseFloat(parts[0]),
    loadAvg5m: parseFloat(parts[1]),
    loadAvg15m: parseFloat(parts[2]),
    cpuCount: parseInt(cpuCountStr, 10),
  }
}

/**
 * Get platform-specific memory and CPU stats
 */
function getPlatformStats(): { memory: MemoryStats; cpu: CPUStats } | null {
  const platform = process.platform

  if (platform === 'darwin') {
    const memory = parseMacOSMemory()
    const cpu = parseMacOSCPU()
    if (memory && cpu) return { memory, cpu }
  } else if (platform === 'linux') {
    const memory = parseLinuxMemory()
    const cpu = parseLinuxCPU()
    if (memory && cpu) return { memory, cpu }
  } else {
    // TODO: Windows support - use wmic or Get-WmiObject
    log.warn('Unsupported platform for system monitoring', { platform })
  }

  return null
}

/**
 * Calculate CPU utilization from load average
 * Load average / CPU count gives rough utilization (>1 means overloaded)
 */
function calculateCPUUtilization(loadAvg1m: number, cpuCount: number): number {
  // Normalize load to percentage (load of cpuCount = 100%)
  return Math.min(100, (loadAvg1m / cpuCount) * 100)
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
  // Check cache first
  if (cachedCapacity && Date.now() - cachedCapacity.timestamp < CACHE_TTL_MS) {
    log.trace('Using cached system capacity')
    return cachedCapacity.data
  }

  try {
    const stats = getPlatformStats()

    if (!stats) {
      // Fail open: allow worker spawn if monitoring unavailable
      log.debug('Platform stats unavailable, failing open')
      return failOpenCapacity()
    }

    const { memory, cpu } = stats

    const memRatio = memory.used / memory.total
    const availRatio = memory.available / memory.total
    const swapRatio = memory.swapTotal > 0 ? memory.swapUsed / memory.swapTotal : 0
    const cpuUtilization = calculateCPUUtilization(cpu.loadAvg1m, cpu.cpuCount)

    // Pressure classification
    // macOS memory_pressure gives us freePercent directly which is more accurate
    let pressureLevel: PressureLevel = 'nominal'
    if (memory.freePercent !== undefined) {
      // Use macOS memory_pressure classification
      if (memory.freePercent < 20) pressureLevel = 'warning'
      if (memory.freePercent < 5) pressureLevel = 'critical'
    } else {
      // Linux-style classification
      if (swapRatio > 0.5 || memRatio > 0.85) pressureLevel = 'warning'
      if (swapRatio > 0.75 || memRatio > 0.95) pressureLevel = 'critical'
    }

    const canSpawnWorker =
      cpuUtilization < 70 && availRatio > 0.15 && swapRatio < 0.4 && pressureLevel !== 'critical'

    const capacity: SystemCapacity = {
      canSpawnWorker,
      cpuUtilization,
      memoryUtilization: memRatio * 100,
      pressureLevel,
      details: {
        availableMemory: memory.available,
        swapUsage: memory.swapUsed,
        currentLoad: cpu.loadAvg1m,
        totalMemory: memory.total,
        usedMemory: memory.used,
      },
    }

    // Log at TRACE for raw values, DEBUG only for notable pressure
    if (pressureLevel !== 'nominal') {
      log.debug('System capacity assessed', {
        canSpawnWorker,
        pressureLevel,
        cpuUtilization: capacity.cpuUtilization.toFixed(1),
        memoryUtilization: capacity.memoryUtilization.toFixed(1),
        availableMemoryGB: (memory.available / 1024 / 1024 / 1024).toFixed(2),
      })
    } else {
      log.trace('System capacity assessed', {
        canSpawnWorker,
        pressureLevel,
        cpuUtilization: capacity.cpuUtilization.toFixed(1),
        memoryUtilization: capacity.memoryUtilization.toFixed(1),
      })
    }

    // Cache result
    cachedCapacity = { data: capacity, timestamp: Date.now() }

    return capacity
  } catch (error) {
    log.error('Failed to assess system capacity', error as Error)
    return failOpenCapacity()
  }
}

/**
 * Return a fail-open capacity (allows workers when monitoring fails)
 */
function failOpenCapacity(): SystemCapacity {
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
      const reduced = Math.min(maxWorkers, Math.max(minWorkers, Math.floor(staticLimit * 0.5)))
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
