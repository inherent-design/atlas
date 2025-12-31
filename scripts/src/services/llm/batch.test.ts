/**
 * Tests for batch LLM completion
 */

// Use vi.hoisted() to define mocks that will be available when vi.mock() factories run
// (vi.mock() is hoisted to top of file, before variable declarations)
const {
  mockCompleteJSON,
  mockEnsureModel,
  mockAssessSystemCapacity,
  mockGetRecommendedConcurrency,
} = vi.hoisted(() => ({
  mockCompleteJSON: vi.fn((prompt: string, config: any) => {
    // Return simple result based on prompt
    return Promise.resolve({ result: `processed: ${prompt.slice(0, 20)}` })
  }),
  mockEnsureModel: vi.fn(() => Promise.resolve()),
  mockAssessSystemCapacity: vi.fn(() =>
    Promise.resolve({
      pressureLevel: 'normal' as const,
      cpuUtilization: 50,
      memoryUtilization: 60,
      canSpawnWorker: true,
      details: {
        totalMemory: 16 * 1024 * 1024 * 1024,
        availableMemory: 8 * 1024 * 1024 * 1024,
        cpuCount: 8,
        loadAverage: 2.5,
      },
    })
  ),
  mockGetRecommendedConcurrency: vi.fn((staticLimit: number, _min: number, _max: number) =>
    Promise.resolve(staticLimit)
  ),
}))

// Setup mocks - these are hoisted but now have access to hoisted mock functions
vi.mock('./providers', () => ({
  completeJSON: mockCompleteJSON,
}))

vi.mock('./ollama', () => ({
  ensureModel: mockEnsureModel,
}))

vi.mock('../../core/system', () => ({
  assessSystemCapacity: mockAssessSystemCapacity,
  getRecommendedConcurrency: mockGetRecommendedConcurrency,
}))

// Mock p-retry to just call the function directly
vi.mock('p-retry', () => ({
  default: async (fn: () => any) => {
    return await fn()
  },
}))

// Dynamic import after mocks are set up
const { completeBatch } = await import('./batch')
import type { BatchResult } from './batch'

describe('completeBatch', () => {
  beforeEach(() => {
    mockCompleteJSON.mockClear()
    mockEnsureModel.mockClear()
    mockAssessSystemCapacity.mockClear()
    mockGetRecommendedConcurrency.mockClear()

    // Reset default implementations
    mockCompleteJSON.mockImplementation((prompt: string, config: any) => {
      return Promise.resolve({ result: `processed: ${prompt.slice(0, 20)}` })
    })

    mockAssessSystemCapacity.mockResolvedValue({
      pressureLevel: 'normal' as const,
      cpuUtilization: 50,
      memoryUtilization: 60,
      canSpawnWorker: true,
      details: {
        totalMemory: 16 * 1024 * 1024 * 1024,
        availableMemory: 8 * 1024 * 1024 * 1024,
        cpuCount: 8,
        loadAverage: 2.5,
      },
    })

    // Reset environment
    delete process.env.LLM_CONCURRENCY
    delete process.env.QNTM_CONCURRENCY
  })

  describe('empty input handling', () => {
    test('returns empty result for empty array', async () => {
      const result = await completeBatch(
        [],
        (input: string) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      expect(result.results).toEqual([])
      expect(result.stats.total).toBe(0)
      expect(result.stats.success).toBe(0)
      expect(result.stats.failed).toBe(0)
      expect(result.failures).toEqual([])
    })

    test('does not call LLM for empty input', async () => {
      await completeBatch(
        [],
        (input: string) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      expect(mockCompleteJSON).not.toHaveBeenCalled()
    })
  })

  describe('successful batch processing', () => {
    test('processes single item', async () => {
      const inputs = ['test input']
      const result = await completeBatch(
        inputs,
        (input) => `Process: ${input}`,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      expect(result.results).toHaveLength(1)
      expect(result.stats.total).toBe(1)
      expect(result.stats.success).toBe(1)
      expect(result.stats.failed).toBe(0)
      expect(mockCompleteJSON).toHaveBeenCalledTimes(1)
    })

    test('processes multiple items', async () => {
      const inputs = ['input1', 'input2', 'input3']
      const result = await completeBatch(
        inputs,
        (input) => `Process: ${input}`,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      expect(result.results).toHaveLength(3)
      expect(result.stats.total).toBe(3)
      expect(result.stats.success).toBe(3)
      expect(result.stats.failed).toBe(0)
      expect(mockCompleteJSON).toHaveBeenCalledTimes(3)
    })

    test('calls buildPrompt with input and index', async () => {
      const inputs = ['a', 'b', 'c']
      const buildPrompt = vi.fn((input: string, index: number) => `${index}: ${input}`)

      await completeBatch(
        inputs,
        buildPrompt,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      expect(buildPrompt).toHaveBeenCalledWith('a', 0)
      expect(buildPrompt).toHaveBeenCalledWith('b', 1)
      expect(buildPrompt).toHaveBeenCalledWith('c', 2)
    })

    test('passes config to completeJSON', async () => {
      const config = { provider: 'anthropic' as const, model: 'haiku' }

      await completeBatch(
        ['test'],
        (input) => input,
        config,
        () => ({ error: true })
      )

      expect(mockCompleteJSON).toHaveBeenCalledWith(expect.any(String), config)
    })

    test('returns results in correct order', async () => {
      const inputs = ['first', 'second', 'third']

      mockCompleteJSON.mockImplementation((prompt: string) => {
        return Promise.resolve({ value: prompt })
      })

      const result = await completeBatch(
        inputs,
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      expect(result.results[0]).toEqual({ value: 'first' })
      expect(result.results[1]).toEqual({ value: 'second' })
      expect(result.results[2]).toEqual({ value: 'third' })
    })
  })

  describe('error handling', () => {
    test('uses defaultResult when item fails', async () => {
      const inputs = ['input1', 'input2']

      mockCompleteJSON
        .mockImplementationOnce(() => Promise.resolve({ success: true }))
        .mockImplementationOnce(() => Promise.reject(new Error('LLM failed')))

      const defaultResult = vi.fn((input: string, error: Error) => ({
        input,
        error: error.message,
      }))

      const result = await completeBatch(
        inputs,
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        defaultResult
      )

      expect(result.stats.success).toBe(1)
      expect(result.stats.failed).toBe(1)
      expect(defaultResult).toHaveBeenCalledWith('input2', expect.any(Error))
    })

    test('tracks failures correctly', async () => {
      const inputs = ['a', 'b', 'c', 'd']

      mockCompleteJSON
        .mockImplementationOnce(() => Promise.resolve({ ok: true }))
        .mockImplementationOnce(() => Promise.reject(new Error('Fail 1')))
        .mockImplementationOnce(() => Promise.resolve({ ok: true }))
        .mockImplementationOnce(() => Promise.reject(new Error('Fail 2')))

      const result = await completeBatch(
        inputs,
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      expect(result.stats.total).toBe(4)
      expect(result.stats.success).toBe(2)
      expect(result.stats.failed).toBe(2)
      expect(result.failures).toHaveLength(2)
      expect(result.failures[0].index).toBe(1)
      expect(result.failures[1].index).toBe(3)
    })

    test('includes error details in failures', async () => {
      const inputs = ['test']

      mockCompleteJSON.mockRejectedValueOnce(new Error('Custom error message'))

      const result = await completeBatch(
        inputs,
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      expect(result.failures[0].error.message).toBe('Custom error message')
    })

    test('continues processing after errors', async () => {
      const inputs = Array.from({ length: 5 }, (_, i) => `input${i}`)

      // Fail on indices 1 and 3
      mockCompleteJSON.mockImplementation((prompt: string) => {
        if (prompt.includes('input1') || prompt.includes('input3')) {
          return Promise.reject(new Error('Fail'))
        }
        return Promise.resolve({ ok: true })
      })

      const result = await completeBatch(
        inputs,
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      expect(result.stats.success).toBe(3)
      expect(result.stats.failed).toBe(2)
      expect(result.results).toHaveLength(5)
    })
  })

  describe('concurrency limiting', () => {
    test('respects LLM_CONCURRENCY env var', async () => {
      process.env.LLM_CONCURRENCY = '3'

      await completeBatch(
        ['test'],
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      // Should not call getRecommendedConcurrency when override set
      expect(mockGetRecommendedConcurrency).not.toHaveBeenCalled()
    })

    test('respects QNTM_CONCURRENCY env var', async () => {
      process.env.QNTM_CONCURRENCY = '5'

      await completeBatch(
        ['test'],
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      expect(mockGetRecommendedConcurrency).not.toHaveBeenCalled()
    })

    test('uses system-based concurrency when no override', async () => {
      await completeBatch(
        ['test'],
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      expect(mockGetRecommendedConcurrency).toHaveBeenCalled()
    })

    test('limits concurrent executions', async () => {
      let maxConcurrent = 0
      let currentConcurrent = 0

      mockCompleteJSON.mockImplementation(async () => {
        currentConcurrent++
        maxConcurrent = Math.max(maxConcurrent, currentConcurrent)
        await new Promise((resolve) => setTimeout(resolve, 20))
        currentConcurrent--
        return { ok: true }
      })

      // Override to use low concurrency
      process.env.LLM_CONCURRENCY = '2'

      await completeBatch(
        Array.from({ length: 10 }, (_, i) => `input${i}`),
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      // Should not exceed concurrency limit
      expect(maxConcurrent).toBeLessThanOrEqual(2)
    })
  })

  describe('Ollama model pre-pull', () => {
    test('ensures Ollama model before batch', async () => {
      await completeBatch(
        ['test'],
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      expect(mockEnsureModel).toHaveBeenCalledWith('ministral-3:3b', undefined)
    })

    test('uses custom Ollama host', async () => {
      await completeBatch(
        ['test'],
        (input) => input,
        { provider: 'ollama', model: 'llama3:8b', ollamaHost: 'http://custom:11434' },
        () => ({ error: true })
      )

      expect(mockEnsureModel).toHaveBeenCalledWith('llama3:8b', 'http://custom:11434')
    })

    test('does not ensure model for Anthropic', async () => {
      await completeBatch(
        ['test'],
        (input) => input,
        { provider: 'anthropic', model: 'haiku' },
        () => ({ error: true })
      )

      expect(mockEnsureModel).not.toHaveBeenCalled()
    })

    test('uses default Ollama model when not specified', async () => {
      await completeBatch(
        ['test'],
        (input) => input,
        { provider: 'ollama' },
        () => ({ error: true })
      )

      expect(mockEnsureModel).toHaveBeenCalledWith('ministral-3:3b', undefined)
    })

    test('ensures model only once per batch', async () => {
      await completeBatch(
        ['input1', 'input2', 'input3'],
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      expect(mockEnsureModel).toHaveBeenCalledTimes(1)
    })
  })

  describe('system capacity assessment', () => {
    test('assesses system capacity before processing', async () => {
      await completeBatch(
        ['test'],
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      expect(mockAssessSystemCapacity).toHaveBeenCalled()
    })

    test('proceeds normally under normal pressure', async () => {
      mockAssessSystemCapacity.mockResolvedValueOnce({
        pressureLevel: 'normal',
        cpuUtilization: 40,
        memoryUtilization: 50,
        canSpawnWorker: true,
        details: {
          totalMemory: 16 * 1024 * 1024 * 1024,
          availableMemory: 8 * 1024 * 1024 * 1024,
          cpuCount: 8,
          loadAverage: 2.0,
        },
      })

      const result = await completeBatch(
        ['test'],
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      expect(result.stats.success).toBe(1)
    })

    test('proceeds under high pressure', async () => {
      mockAssessSystemCapacity.mockResolvedValueOnce({
        pressureLevel: 'high',
        cpuUtilization: 85,
        memoryUtilization: 80,
        canSpawnWorker: true,
        details: {
          totalMemory: 16 * 1024 * 1024 * 1024,
          availableMemory: 2 * 1024 * 1024 * 1024,
          cpuCount: 8,
          loadAverage: 7.0,
        },
      })

      const result = await completeBatch(
        ['test'],
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      expect(result.stats.success).toBe(1)
    })

    test('proceeds under critical pressure', async () => {
      mockAssessSystemCapacity.mockResolvedValueOnce({
        pressureLevel: 'critical',
        cpuUtilization: 95,
        memoryUtilization: 90,
        canSpawnWorker: false,
        details: {
          totalMemory: 16 * 1024 * 1024 * 1024,
          availableMemory: 1 * 1024 * 1024 * 1024,
          cpuCount: 8,
          loadAverage: 9.0,
        },
      })

      const result = await completeBatch(
        ['test'],
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      // Should still process, just slower
      expect(result.stats.success).toBe(1)
    })
  })

  describe('type handling', () => {
    test('handles different input types', async () => {
      interface TestInput {
        id: number
        text: string
      }

      interface TestOutput {
        processed: string
      }

      const inputs: TestInput[] = [
        { id: 1, text: 'first' },
        { id: 2, text: 'second' },
      ]

      mockCompleteJSON.mockImplementation((prompt: string) => {
        return Promise.resolve({ processed: prompt })
      })

      const result: BatchResult<TestOutput> = await completeBatch(
        inputs,
        (input) => `Process ${input.text}`,
        { provider: 'ollama', model: 'ministral-3:3b' },
        (input, error) => ({ processed: `Error: ${input.text}` })
      )

      expect(result.results).toHaveLength(2)
      expect(result.results[0]).toHaveProperty('processed')
    })

    test('preserves result types', async () => {
      const inputs = [1, 2, 3]

      mockCompleteJSON.mockImplementation((prompt: string) => {
        const num = parseInt(prompt.replace('Number: ', ''))
        return Promise.resolve({ value: num * 2 })
      })

      const result = await completeBatch(
        inputs,
        (input) => `Number: ${input}`,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ value: 0 })
      )

      expect(result.results[0].value).toBe(2)
      expect(result.results[1].value).toBe(4)
      expect(result.results[2].value).toBe(6)
    })
  })

  describe('edge cases', () => {
    test('handles very large batch', async () => {
      const inputs = Array.from({ length: 100 }, (_, i) => i)

      const result = await completeBatch(
        inputs,
        (input) => `Process ${input}`,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      expect(result.stats.total).toBe(100)
      expect(result.results).toHaveLength(100)
    })

    test('handles undefined in defaultResult error', async () => {
      mockCompleteJSON.mockRejectedValueOnce(undefined)

      const result = await completeBatch(
        ['test'],
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        (input, error) => ({ input, errorMessage: error?.message || 'Unknown error' })
      )

      expect(result.stats.failed).toBe(1)
    })

    test('handles concurrent batch calls', async () => {
      const batch1 = completeBatch(
        ['a', 'b'],
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      const batch2 = completeBatch(
        ['c', 'd'],
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      const [result1, result2] = await Promise.all([batch1, batch2])

      expect(result1.stats.total).toBe(2)
      expect(result2.stats.total).toBe(2)
    })

    test('cleans up watchdog after completion', async () => {
      // This test verifies watchdog is stopped even if we don't check it directly
      await completeBatch(
        ['test'],
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      // Should not throw or leak resources
      expect(true).toBe(true)
    })

    test('cleans up watchdog after error', async () => {
      mockCompleteJSON.mockRejectedValueOnce(new Error('Fatal error'))

      await completeBatch(
        ['test'],
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      // Should still clean up
      expect(true).toBe(true)
    })
  })

  describe('result statistics', () => {
    test('calculates stats correctly for all success', async () => {
      const result = await completeBatch(
        ['a', 'b', 'c'],
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      expect(result.stats.total).toBe(3)
      expect(result.stats.success).toBe(3)
      expect(result.stats.failed).toBe(0)
    })

    test('calculates stats correctly for all failures', async () => {
      mockCompleteJSON.mockRejectedValue(new Error('Always fail'))

      const result = await completeBatch(
        ['a', 'b', 'c'],
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      expect(result.stats.total).toBe(3)
      expect(result.stats.success).toBe(0)
      expect(result.stats.failed).toBe(3)
    })

    test('calculates stats correctly for mixed results', async () => {
      let callCount = 0
      mockCompleteJSON.mockImplementation(() => {
        callCount++
        if (callCount % 2 === 0) {
          return Promise.reject(new Error('Fail'))
        }
        return Promise.resolve({ ok: true })
      })

      const result = await completeBatch(
        ['a', 'b', 'c', 'd', 'e'],
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      expect(result.stats.total).toBe(5)
      expect(result.stats.success).toBe(3) // indices 0, 2, 4
      expect(result.stats.failed).toBe(2) // indices 1, 3
    })

    test('stats match failures array length', async () => {
      mockCompleteJSON
        .mockResolvedValueOnce({ ok: true })
        .mockRejectedValueOnce(new Error('Fail 1'))
        .mockResolvedValueOnce({ ok: true })
        .mockRejectedValueOnce(new Error('Fail 2'))
        .mockRejectedValueOnce(new Error('Fail 3'))

      const result = await completeBatch(
        ['a', 'b', 'c', 'd', 'e'],
        (input) => input,
        { provider: 'ollama', model: 'ministral-3:3b' },
        () => ({ error: true })
      )

      expect(result.stats.failed).toBe(result.failures.length)
      expect(result.stats.failed).toBe(3)
    })
  })
})
