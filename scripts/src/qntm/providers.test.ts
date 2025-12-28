/**
 * Unit tests for QNTM provider abstraction
 */

import { beforeEach, describe, expect, mock, test } from 'bun:test'
import type { QNTMGenerationInput } from '.'
import { checkOllamaAvailable, detectProvider, generateQNTMKeysWithProvider } from './providers'

describe('qntm-providers', () => {
  describe('generateQNTMKeysWithProvider', () => {
    const mockInput: QNTMGenerationInput = {
      chunk: 'This is a test chunk about memory consolidation patterns.',
      existingKeys: ['@existing ~ key'],
      context: {
        fileName: 'test.md',
        chunkIndex: 0,
        totalChunks: 1,
      },
    }

    describe('anthropic provider', () => {
      test('generates keys via Claude API', async () => {
        // Mock Bun.spawn for claude CLI
        const originalSpawn = Bun.spawn
        const mockStdout = new ReadableStream({
          start(controller) {
            // Claude CLI wraps response in {result: "..."} and wraps JSON in markdown code fences
            const jsonContent = JSON.stringify({
              keys: ['@memory ~ consolidation', '@patterns ~ neural'],
              reasoning: 'Test reasoning',
            })
            const wrapper = JSON.stringify({
              result: '```json\n' + jsonContent + '\n```',
            })
            controller.enqueue(new TextEncoder().encode(wrapper))
            controller.close()
          },
        })

        const mockStdin = {
          write: mock(() => {}),
          end: mock(() => {}),
        }

        ;(Bun as any).spawn = mock(() => ({
          stdin: mockStdin,
          stdout: mockStdout,
        }))

        try {
          const result = await generateQNTMKeysWithProvider(mockInput, {
            provider: 'anthropic',
            model: 'haiku',
          })

          expect(result.keys).toHaveLength(2)
          expect(result.keys).toContain('@memory ~ consolidation')
          expect(result.reasoning).toBe('Test reasoning')
        } finally {
          ;(Bun as any).spawn = originalSpawn
        }
      })

      test('includes existing keys in prompt', async () => {
        const originalSpawn = Bun.spawn
        let capturedPrompt = ''

        const mockStdout = new ReadableStream({
          start(controller) {
            // Claude CLI wraps response with markdown code fences
            const jsonContent = JSON.stringify({ keys: ['@test'], reasoning: 'test' })
            const wrapper = JSON.stringify({
              result: '```json\n' + jsonContent + '\n```',
            })
            controller.enqueue(new TextEncoder().encode(wrapper))
            controller.close()
          },
        })

        const mockStdin = {
          write: mock((data: any) => {
            capturedPrompt = data
          }),
          end: mock(() => {}),
        }

        ;(Bun as any).spawn = mock(() => ({
          stdin: mockStdin,
          stdout: mockStdout,
        }))

        try {
          await generateQNTMKeysWithProvider(mockInput, {
            provider: 'anthropic',
            model: 'haiku',
          })

          expect(capturedPrompt).toContain('@existing ~ key')
        } finally {
          ;(Bun as any).spawn = originalSpawn
        }
      })
    })

    describe('ollama provider', () => {
      test('generates keys via Ollama API', async () => {
        // Mock fetch for Ollama
        const originalFetch = global.fetch
        global.fetch = mock(async () => {
          return new Response(
            JSON.stringify({
              response: JSON.stringify({
                keys: ['@memory ~ consolidation', '@patterns ~ neural'],
                reasoning: 'Ollama reasoning',
              }),
            }),
            { status: 200 }
          )
        }) as any

        try {
          const result = await generateQNTMKeysWithProvider(mockInput, {
            provider: 'ollama',
            model: 'qwen2.5:7b',
            ollamaHost: 'http://localhost:11434',
          })

          expect(result.keys).toHaveLength(2)
          expect(result.keys).toContain('@memory ~ consolidation')
          expect(result.reasoning).toBe('Ollama reasoning')

          // Verify API call
          expect(global.fetch).toHaveBeenCalledWith(
            'http://localhost:11434/api/generate',
            expect.objectContaining({
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
            })
          )
        } finally {
          global.fetch = originalFetch
        }
      })

      test('uses correct Ollama request format', async () => {
        const originalFetch = global.fetch
        let capturedBody: any

        global.fetch = mock(async (_url: any, options: any) => {
          capturedBody = JSON.parse(options.body)
          return new Response(
            JSON.stringify({
              response: JSON.stringify({ keys: ['@test'], reasoning: 'test' }),
            }),
            { status: 200 }
          )
        }) as any

        try {
          await generateQNTMKeysWithProvider(mockInput, {
            provider: 'ollama',
            model: 'qwen2.5:7b',
          })

          expect(capturedBody.model).toBe('qwen2.5:7b')
          expect(capturedBody.format).toBe('json')
          expect(capturedBody.stream).toBe(false)
          expect(capturedBody.options.temperature).toBe(0.1)
        } finally {
          global.fetch = originalFetch
        }
      })

      test('handles Ollama API errors', async () => {
        const originalFetch = global.fetch
        global.fetch = mock(async () => {
          return new Response('Server error', { status: 500, statusText: 'Internal Server Error' })
        }) as any

        try {
          await expect(
            generateQNTMKeysWithProvider(mockInput, {
              provider: 'ollama',
              model: 'qwen2.5:7b',
            })
          ).rejects.toThrow('Failed to pull')
        } finally {
          global.fetch = originalFetch
        }
      })
    })

    test('throws on unknown provider', async () => {
      await expect(
        generateQNTMKeysWithProvider(mockInput, {
          provider: 'invalid' as any,
        })
      ).rejects.toThrow('Unknown provider: invalid')
    })

    test('includes context in prompt when provided', async () => {
      const originalFetch = global.fetch
      let capturedPrompt = ''

      global.fetch = mock(async (_url: any, options: any) => {
        const body = JSON.parse(options.body)
        capturedPrompt = body.prompt
        return new Response(
          JSON.stringify({
            response: JSON.stringify({ keys: ['@test'], reasoning: 'test' }),
          }),
          { status: 200 }
        )
      }) as any

      try {
        await generateQNTMKeysWithProvider(mockInput, {
          provider: 'ollama',
          model: 'qwen2.5:7b',
        })

        expect(capturedPrompt).toContain('test.md')
        expect(capturedPrompt).toContain('chunk 0/1')
      } finally {
        global.fetch = originalFetch
      }
    })
  })

  describe('checkOllamaAvailable', () => {
    test('returns true when Ollama is available', async () => {
      const originalFetch = global.fetch
      global.fetch = mock(async () => {
        return new Response(JSON.stringify({ models: [] }), { status: 200 })
      }) as any

      try {
        const available = await checkOllamaAvailable('http://localhost:11434')
        expect(available).toBe(true)
      } finally {
        global.fetch = originalFetch
      }
    })

    test('returns false when Ollama is unavailable', async () => {
      const originalFetch = global.fetch
      global.fetch = mock(async () => {
        throw new Error('Connection refused')
      }) as any

      try {
        const available = await checkOllamaAvailable('http://localhost:11434')
        expect(available).toBe(false)
      } finally {
        global.fetch = originalFetch
      }
    })

    test('returns false on timeout', async () => {
      const originalFetch = global.fetch
      global.fetch = mock(async (_url: any, options: any) => {
        // Simulate timeout by checking signal
        if (options?.signal) {
          await new Promise((resolve, reject) => {
            options.signal.addEventListener('abort', () => {
              reject(new Error('AbortError'))
            })
            setTimeout(resolve, 3000) // Longer than 2s timeout
          })
        }
        return new Response('{}', { status: 200 })
      }) as any

      try {
        const available = await checkOllamaAvailable('http://localhost:11434')
        expect(available).toBe(false)
      } finally {
        global.fetch = originalFetch
      }
    })

    test('uses correct API endpoint', async () => {
      const originalFetch = global.fetch
      let capturedUrl = ''

      global.fetch = mock(async (url: any) => {
        capturedUrl = url
        return new Response('{}', { status: 200 })
      }) as any

      try {
        await checkOllamaAvailable('http://custom-host:9999')
        expect(capturedUrl).toBe('http://custom-host:9999/api/tags')
      } finally {
        global.fetch = originalFetch
      }
    })
  })

  describe('detectProvider', () => {
    beforeEach(() => {
      // Clear environment
      delete process.env.ANTHROPIC_API_KEY
    })

    test('detects Ollama when available', async () => {
      const originalFetch = global.fetch
      global.fetch = mock(async () => new Response('{}', { status: 200 })) as any

      try {
        const provider = await detectProvider()
        expect(provider).toBe('ollama')
      } finally {
        global.fetch = originalFetch
      }
    })

    test('falls back to Claude when Ollama unavailable but API key set', async () => {
      const originalFetch = global.fetch
      global.fetch = mock(async () => {
        throw new Error('Connection refused')
      }) as any

      process.env.ANTHROPIC_API_KEY = 'test-key'

      try {
        const provider = await detectProvider()
        expect(provider).toBe('anthropic')
      } finally {
        global.fetch = originalFetch
        delete process.env.ANTHROPIC_API_KEY
      }
    })

    test('defaults to ollama when nothing available', async () => {
      const originalFetch = global.fetch
      global.fetch = mock(async () => {
        throw new Error('Connection refused')
      }) as any

      try {
        const provider = await detectProvider()
        expect(provider).toBe('ollama')
      } finally {
        global.fetch = originalFetch
      }
    })
  })
})
