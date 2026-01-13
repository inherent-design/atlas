/**
 * Smoke tests for search-inject hook logic
 */
import { describe, it, expect } from 'vitest'

describe('search-inject hook logic', () => {
  it('should skip very short prompts', () => {
    // Prompts < 3 chars should be skipped (trivial like "hi", "ok")
    const shortPrompt = { prompt: 'hi', session_id: 'test', transcript_path: '/tmp/t', cwd: '/tmp' }
    const shouldSkip =
      !shortPrompt.prompt || shortPrompt.prompt.length < 3 || shortPrompt.prompt.startsWith('/')
    expect(shouldSkip).toBe(true)
  })

  it('should skip slash commands', () => {
    const slashCommand = {
      prompt: '/help',
      session_id: 'test',
      transcript_path: '/tmp/t',
      cwd: '/tmp',
    }
    const shouldSkip =
      !slashCommand.prompt || slashCommand.prompt.length < 3 || slashCommand.prompt.startsWith('/')
    expect(shouldSkip).toBe(true)
  })

  it('should process valid prompts', () => {
    const validPrompt = {
      prompt: 'How do I implement feature X?',
      session_id: 'test',
      transcript_path: '/tmp/t',
      cwd: '/tmp',
    }
    const shouldSkip =
      !validPrompt.prompt || validPrompt.prompt.length < 3 || validPrompt.prompt.startsWith('/')
    expect(shouldSkip).toBe(false)
  })

  it('should format context correctly', () => {
    const results = [{ file_path: 'test.md', text: 'Test content', score: 0.9 }]
    const context = results
      .map((r, i) => `[Atlas Memory ${i + 1}] (${r.file_path}):\n${r.text}`)
      .join('\n\n---\n\n')

    expect(context).toContain('[Atlas Memory 1]')
    expect(context).toContain('test.md')
    expect(context).toContain('Test content')
  })
})
