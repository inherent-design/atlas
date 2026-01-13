/**
 * Daemon state management
 *
 * Manages ephemeral state for:
 * - Concurrent ingestion tasks
 * - Global consolidation lock (in-memory)
 * - Auto-watch path registry
 */

import { v4 as uuid } from 'uuid'
import type { IngestionTask } from './protocol.js'

export interface ConsolidationLock {
  locked: boolean
  taskId?: string
  startedAt?: Date
}

/**
 * Daemon state manager
 *
 * All state is in-memory and ephemeral (resets on daemon restart).
 * This is intentional - daemon state is operational, not persistent.
 */
export class DaemonState {
  // Concurrent ingestion tasks (ephemeral)
  private ingestionTasks: Map<string, IngestionTask> = new Map()

  // Global consolidation lock (in-memory)
  private consolidationLock: ConsolidationLock = { locked: false }

  // Auto-watch path registrations (cwd → taskId)
  private autoWatchPaths: Map<string, string> = new Map()

  /**
   * Create new ingestion task
   */
  createIngestionTask(paths: string[], watching: boolean): string {
    const taskId = uuid()
    const task: IngestionTask = {
      id: taskId,
      paths,
      status: 'running',
      watching,
      filesProcessed: 0,
      chunksStored: 0,
      errors: [],
      startedAt: new Date().toISOString(),
    }
    this.ingestionTasks.set(taskId, task)
    return taskId
  }

  /**
   * Get task by ID
   */
  getIngestionTask(taskId: string): IngestionTask | undefined {
    return this.ingestionTasks.get(taskId)
  }

  /**
   * Get all ingestion tasks
   */
  getAllIngestionTasks(): IngestionTask[] {
    return Array.from(this.ingestionTasks.values())
  }

  /**
   * Update task
   */
  updateIngestionTask(taskId: string, updates: Partial<IngestionTask>): void {
    const task = this.ingestionTasks.get(taskId)
    if (task) {
      Object.assign(task, updates)
    }
  }

  /**
   * Try to acquire consolidation lock
   */
  acquireConsolidationLock(taskId: string): boolean {
    if (this.consolidationLock.locked) {
      return false
    }
    this.consolidationLock = {
      locked: true,
      taskId,
      startedAt: new Date(),
    }
    return true
  }

  /**
   * Release consolidation lock
   */
  releaseConsolidationLock(): void {
    this.consolidationLock = { locked: false }
  }

  /**
   * Get consolidation lock state
   */
  getConsolidationLock(): ConsolidationLock {
    return { ...this.consolidationLock }
  }

  /**
   * Register auto-watch path
   */
  registerAutoWatch(path: string, taskId: string): void {
    this.autoWatchPaths.set(path, taskId)
  }

  /**
   * Check if path is auto-watched
   */
  isAutoWatched(path: string): boolean {
    return this.autoWatchPaths.has(path)
  }

  /**
   * Get auto-watch task ID for path
   */
  getAutoWatchTaskId(path: string): string | undefined {
    return this.autoWatchPaths.get(path)
  }
}

// Singleton instance
export const daemonState = new DaemonState()
