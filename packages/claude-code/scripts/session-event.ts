#!/usr/bin/env bun
/**
 * PreCompact/SessionEnd hook: Send session event to Atlas daemon
 *
 * Input (stdin): { session_id, transcript_path, hook_event_name, trigger?, reason?, cwd }
 * Output: None (fire and forget to daemon)
 *
 * Uses AtlasConnection directly to communicate with daemon via Unix socket.
 */

import { AtlasConnection, isDaemonRunning } from '@inherent.design/atlas-core'

interface HookInput {
  session_id: string
  transcript_path: string
  hook_event_name: 'PreCompact' | 'SessionEnd'
  trigger?: 'manual' | 'auto'
  reason?: string
  cwd: string
}

async function main() {
  // Read input from stdin using Bun's native API
  let input: HookInput
  try {
    const data = await Bun.readableStreamToText(Bun.stdin.stream())
    input = JSON.parse(data)
  } catch {
    // Invalid input, exit silently
    process.exit(0)
  }

  // Check if daemon is running before attempting connection
  if (!isDaemonRunning()) {
    // Daemon not running, exit silently (don't block Claude Code)
    process.exit(0)
  }

  // Map hook event to daemon event type
  const eventType =
    input.hook_event_name === 'PreCompact' ? 'session.compacting' : 'session.ended'

  try {
    // Connect to daemon and send event
    const connection = new AtlasConnection()
    await connection.connect()

    await connection.request('atlas.session_event' as any, {
      type: eventType,
      data: {
        sessionId: input.session_id,
        transcriptPath: input.transcript_path,
        trigger: input.trigger,
        reason: input.reason,
        cwd: input.cwd,
      },
    })

    connection.disconnect()
  } catch {
    // Silently fail - don't block session operations
    // Daemon might have stopped between check and connect
  }

  process.exit(0)
}

main()
