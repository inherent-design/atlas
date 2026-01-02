/**
 * Shim for Bun runtime APIs in Vitest environment
 * Provides minimal compatibility for code that imports from 'bun' and 'bun-webgpu'
 */

import picomatch from 'picomatch'

/**
 * Stub for bun-webgpu setupGlobals
 * GPU detection is not needed in tests
 */
export function setupGlobals() {
  // No-op in test environment
}

/**
 * Minimal Glob implementation using picomatch
 * Compatible with Bun.Glob API used in logger.ts
 */
export class Glob {
  private matcher: (str: string) => boolean

  constructor(pattern: string) {
    // Convert glob pattern to picomatch matcher
    this.matcher = picomatch(pattern)
  }

  match(value: string): boolean {
    return this.matcher(value)
  }
}

/**
 * Make Bun global available for test code that uses Bun.spawnSync
 * This allows tests to spy on Bun.spawnSync even though we're not running in Bun
 */
if (typeof globalThis.Bun === 'undefined') {
  ;(globalThis as any).Bun = {
    spawnSync: (cmd: string[]) => ({
      success: false,
      stdout: Buffer.from(''),
      stderr: Buffer.from('not implemented in test shim'),
    }),
    // Async spawn stub - returns a mock process object
    spawn: (cmd: string[], options?: any) => {
      const { Readable, Writable } = require('stream')

      // Create mock stdin that accepts writes
      const mockStdin = new Writable({
        write(chunk: any, encoding: any, callback: () => void) {
          callback()
        },
      })
      mockStdin.end = () => {}

      // Create mock stdout/stderr that return empty
      const mockStdout = Readable.from([Buffer.from('')])
      const mockStderr = Readable.from([Buffer.from('')])

      return {
        stdin: mockStdin,
        stdout: mockStdout,
        stderr: mockStderr,
        exited: Promise.resolve(0),
        kill: () => {},
      }
    },
  }
}
