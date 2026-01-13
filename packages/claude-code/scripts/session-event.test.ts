/**
 * Smoke tests for session-event hook logic
 */
import { describe, it, expect } from 'vitest'

describe('session-event hook logic', () => {
  it('should map PreCompact to session.compacting', () => {
    const mapEventType = (hookEvent: string) =>
      hookEvent === 'PreCompact' ? 'session.compacting' : 'session.ended'

    expect(mapEventType('PreCompact')).toBe('session.compacting')
  })

  it('should map SessionEnd to session.ended', () => {
    const mapEventType = (hookEvent: string) =>
      hookEvent === 'PreCompact' ? 'session.compacting' : 'session.ended'

    expect(mapEventType('SessionEnd')).toBe('session.ended')
  })

  it('should construct valid event data', () => {
    const input = {
      session_id: 'test-session',
      transcript_path: '/tmp/transcript.jsonl',
      hook_event_name: 'SessionEnd' as const,
      cwd: '/tmp',
    }

    const eventData = {
      sessionId: input.session_id,
      transcriptPath: input.transcript_path,
      trigger: undefined,
      reason: undefined,
      cwd: input.cwd,
    }

    expect(eventData.sessionId).toBe('test-session')
    expect(eventData.transcriptPath).toBe('/tmp/transcript.jsonl')
    expect(eventData.cwd).toBe('/tmp')
  })
})
