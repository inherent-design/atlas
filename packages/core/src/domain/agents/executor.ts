/**
 * Agent executor - single agent runtime
 *
 * Handles:
 * - Multi-turn LLM conversation
 * - Tool execution (Bash, Read, Write, Grep, Glob)
 * - RAG context injection from Qdrant
 * - Artifact writing to ~/.atlas/{role}/{type}/{project}/
 */

import { spawn } from 'child_process'
import { createLogger, startTimer } from '../../shared/logger.js'
import { getLLMBackendFor } from '../../services/llm/index.js'
import type { LLMBackend, CanUseTool, ToolUseResult } from '../../services/llm/types.js'
import { search } from '../search/index.js'
import type {
  AgentConfig,
  AgentResult,
  AgentTurn,
  ToolCall,
  ToolResult,
  AGENT_TOOLS,
} from './types.js'
import { buildAgentPrompt, buildArtifactPath } from '../../prompts/builders.js'
import type { ToolDefinition } from './types.js'
import { AGENT_TOOLS as TOOL_DEFINITIONS } from './types.js'

const log = createLogger('agents:executor')

/**
 * Helper to spawn process and collect stdout/stderr (Node.js equivalent of Bun.spawn)
 */
async function spawnAsync(
  args: string[]
): Promise<{ stdout: string; stderr: string; exitCode: number | null }> {
  if (args.length === 0) {
    throw new Error('spawnAsync requires at least one argument')
  }

  return new Promise((resolve, reject) => {
    const proc = spawn(args[0]!, args.slice(1), {
      stdio: ['inherit', 'pipe', 'pipe'],
    })

    let stdout = ''
    let stderr = ''

    proc.stdout?.on('data', (chunk: Buffer) => {
      stdout += chunk.toString()
    })

    proc.stderr?.on('data', (chunk: Buffer) => {
      stderr += chunk.toString()
    })

    proc.on('error', reject)

    proc.on('close', (code: number | null) => {
      resolve({ stdout, stderr, exitCode: code })
    })
  })
}

/**
 * Type guard: Check if backend supports tool use
 */
function isToolUseBackend(backend: LLMBackend): backend is LLMBackend & CanUseTool {
  return 'completeWithTools' in backend && typeof backend.completeWithTools === 'function'
}

/**
 * Execute a single agent with multi-turn conversation
 */
export async function executeAgent(config: AgentConfig): Promise<AgentResult> {
  const startTime = Date.now()
  const endTimer = startTimer(`agent:${config.role}`)

  log.info('Executing agent', {
    role: config.role,
    task: config.task.substring(0, 100),
    maxTurns: config.maxTurns ?? 5,
  })

  // Emit agent.started event
  config.emit?.({
    type: 'agent.started',
    data: {
      role: config.role,
      task: config.task.substring(0, 200),
      project: config.project || 'default',
      maxTurns: config.maxTurns ?? 5,
    },
  })

  const turns: AgentTurn[] = []
  const artifacts: string[] = []
  let totalUsage = {
    inputTokens: 0,
    outputTokens: 0,
    thinkingTokens: 0,
  }

  try {
    // Get LLM backend (prefer tool-use, fallback to text-completion)
    let backend = getLLMBackendFor('tool-use')

    // If no tool-use backend, check for text-completion with completeWithTools method
    if (!backend || !isToolUseBackend(backend)) {
      backend = getLLMBackendFor('text-completion')

      if (!backend) {
        throw new Error('No LLM backend available')
      }

      // Check if the text-completion backend supports tool use
      if (!isToolUseBackend(backend)) {
        throw new Error(
          'LLM backend does not support tool use. Available capabilities: ' +
            Array.from(backend.capabilities).join(', ')
        )
      }
    }

    // Gather RAG context if QNTM keys provided
    let ragContext: string[] = []
    if (config.qntmKeys && config.qntmKeys.length > 0) {
      log.debug('Gathering RAG context', { qntmKeys: config.qntmKeys })

      for (const key of config.qntmKeys) {
        const results = await search({
          query: key,
          qntmKey: key,
          limit: 5,
          consolidationLevel: config.consolidationLevel,
        })

        ragContext.push(
          ...results.map((r: any) => `[${r.file_path}]\n${r.text}\n(score: ${r.score.toFixed(3)})`)
        )
      }

      log.debug('RAG context gathered', { chunks: ragContext.length })
    }

    // Combine provided context with RAG context
    const fullContext = [...(config.context || []), ...ragContext]

    // Build initial system prompt
    const systemPrompt = await buildAgentPrompt(config.role, config.task, { context: fullContext })

    // Conversation history (for multi-turn)
    const messages: Array<{ role: 'user' | 'assistant'; content: string }> = [
      { role: 'user', content: systemPrompt },
    ]

    const maxTurns = config.maxTurns ?? 5
    let turnNumber = 0
    let continueConversation = true

    // Multi-turn conversation loop
    while (continueConversation && turnNumber < maxTurns) {
      turnNumber++

      log.debug('Agent turn starting', {
        role: config.role,
        turn: turnNumber,
        maxTurns,
      })

      // Emit agent.turn event
      config.emit?.({
        type: 'agent.turn',
        data: {
          role: config.role,
          turn: turnNumber,
          maxTurns,
        },
      })

      const turn: AgentTurn = {
        turn: turnNumber,
        output: '',
      }

      try {
        // Call LLM with tools (type-safe: backend is guaranteed to be CanUseTool by checks above)
        const response: ToolUseResult = await backend.completeWithTools(
          messages[messages.length - 1]!.content, // Last user message
          TOOL_DEFINITIONS,
          {
            temperature: config.temperature ?? 0.7,
            maxTokens: config.maxTokens ?? 4000,
          }
        )

        turn.output = response.text
        turn.usage = {
          inputTokens: response.usage?.inputTokens ?? 0,
          outputTokens: response.usage?.outputTokens ?? 0,
          thinkingTokens: response.usage?.thinkingTokens,
        }

        // Update total usage
        totalUsage.inputTokens += turn.usage.inputTokens
        totalUsage.outputTokens += turn.usage.outputTokens
        totalUsage.thinkingTokens =
          (totalUsage.thinkingTokens ?? 0) + (turn.usage.thinkingTokens ?? 0)

        // Add assistant response to history
        messages.push({ role: 'assistant', content: response.text })

        // Check if tools were called
        if (response.toolCalls && response.toolCalls.length > 0) {
          log.debug('Agent called tools', {
            role: config.role,
            turn: turnNumber,
            tools: response.toolCalls.map((t: any) => t.name),
          })

          turn.toolCalls = response.toolCalls

          // Emit tool call events
          for (const toolCall of response.toolCalls) {
            config.emit?.({
              type: 'agent.tool_called',
              data: {
                role: config.role,
                turn: turnNumber,
                toolName: toolCall.name,
                toolId: toolCall.id,
              },
            })
          }

          // Execute tools
          const toolResults: ToolResult[] = []

          for (const toolCall of response.toolCalls) {
            const result = await executeTool(toolCall)
            toolResults.push(result)
          }

          turn.toolResults = toolResults

          // Build tool results message for next turn
          const toolResultsMessage = toolResults
            .map((r) => {
              if (r.error) {
                return `[${r.name} (${r.id}) ERROR]\n${r.error}`
              }
              return `[${r.name} (${r.id}) RESULT]\n${r.output}`
            })
            .join('\n\n')

          messages.push({ role: 'user', content: toolResultsMessage })

          // Continue conversation (agent may need to process tool results)
          continueConversation = true
        } else {
          // No tools called - agent is done
          log.debug('Agent completed without tool calls', {
            role: config.role,
            turn: turnNumber,
          })
          continueConversation = false
        }
      } catch (error) {
        log.error('Agent turn failed', {
          role: config.role,
          turn: turnNumber,
          error: (error as Error).message,
        })

        // Emit error event
        config.emit?.({
          type: 'agent.error',
          data: {
            role: config.role,
            turn: turnNumber,
            error: (error as Error).message,
            phase: 'turn',
          },
        })

        turn.output = `[ERROR] ${(error as Error).message}`
        continueConversation = false
      }

      turns.push(turn)
    }

    // Write artifacts if enabled
    if (config.writeArtifacts !== false) {
      const project = config.project || 'default'
      const taskName = config.task
        .substring(0, 50)
        .replace(/[^a-z0-9]+/gi, '-')
        .toLowerCase()
      const artifactPath = buildArtifactPath(config.role, 'outputs', project, taskName)

      const artifactContent = buildArtifactContent(config, turns)

      // Ensure directory exists
      const fs = await import('fs/promises')
      const path = await import('path')
      await fs.mkdir(path.dirname(artifactPath), { recursive: true })

      await fs.writeFile(artifactPath, artifactContent, 'utf-8')

      artifacts.push(artifactPath)

      log.debug('Artifact written', { path: artifactPath })
    }

    const took = Date.now() - startTime
    endTimer()

    // Determine status
    let status: 'success' | 'error' | 'max_turns' = 'success'
    if (turnNumber >= maxTurns) {
      status = 'max_turns'
      log.warn('Agent reached max turns', {
        role: config.role,
        turns: turnNumber,
      })
    }

    const result: AgentResult = {
      role: config.role,
      task: config.task,
      turns,
      output: turns[turns.length - 1]?.output || '',
      artifacts,
      usage: totalUsage,
      status,
      took,
    }

    // Emit agent.completed event
    config.emit?.({
      type: 'agent.completed',
      data: {
        role: config.role,
        status,
        turns: turns.length,
        artifacts,
        took,
      },
    })

    log.info('Agent execution completed', {
      role: config.role,
      turns: turns.length,
      status,
      took,
    })

    return result
  } catch (error) {
    const took = Date.now() - startTime
    endTimer()

    log.error('Agent execution failed', {
      role: config.role,
      error: (error as Error).message,
    })

    // Emit error event
    config.emit?.({
      type: 'agent.error',
      data: {
        role: config.role,
        error: (error as Error).message,
        phase: 'init',
      },
    })

    return {
      role: config.role,
      task: config.task,
      turns,
      output: '',
      artifacts,
      usage: totalUsage,
      status: 'error',
      error: (error as Error).message,
      took,
    }
  }
}

/**
 * Execute a tool call
 */
async function executeTool(toolCall: ToolCall): Promise<ToolResult> {
  const { id, name, input } = toolCall

  log.debug('Executing tool', { name, id })

  try {
    switch (name) {
      case 'bash':
        return await executeBash(id, input)
      case 'read':
        return await executeRead(id, input)
      case 'write':
        return await executeWrite(id, input)
      case 'grep':
        return await executeGrep(id, input)
      case 'glob':
        return await executeGlob(id, input)
      default:
        return {
          id,
          name,
          output: '',
          error: `Unknown tool: ${name}`,
        }
    }
  } catch (error) {
    log.error('Tool execution failed', {
      name,
      id,
      error: (error as Error).message,
    })

    return {
      id,
      name,
      output: '',
      error: (error as Error).message,
    }
  }
}

/**
 * Execute bash command
 */
async function executeBash(id: string, input: Record<string, unknown>): Promise<ToolResult> {
  const command = input.command as string
  const timeout = (input.timeout as number) ?? 120000 // 2 min default

  if (!command) {
    return { id, name: 'bash', output: '', error: 'Missing command parameter' }
  }

  log.debug('Executing bash command', { command: command.substring(0, 100) })

  try {
    // Note: Node.js spawn timeout handled via AbortController in future improvement
    // For now, maintain similar behavior to Bun version
    const { stdout, stderr, exitCode } = await spawnAsync(['bash', '-c', command])

    const output = `[Exit code: ${exitCode}]\n\nSTDOUT:\n${stdout}\n\nSTDERR:\n${stderr}`

    return { id, name: 'bash', output }
  } catch (error) {
    return {
      id,
      name: 'bash',
      output: '',
      error: `Bash execution failed: ${(error as Error).message}`,
    }
  }
}

/**
 * Execute read file
 */
async function executeRead(id: string, input: Record<string, unknown>): Promise<ToolResult> {
  const filePath = input.file_path as string
  const offset = input.offset as number | undefined
  const limit = input.limit as number | undefined

  if (!filePath) {
    return { id, name: 'read', output: '', error: 'Missing file_path parameter' }
  }

  log.debug('Reading file', { filePath })

  try {
    const fs = await import('fs/promises')
    const content = await fs.readFile(filePath, 'utf-8')

    // Apply offset/limit if specified
    if (offset !== undefined || limit !== undefined) {
      const lines = content.split('\n')
      const startLine = offset ?? 0
      const endLine = limit ? startLine + limit : lines.length
      const selectedLines = lines.slice(startLine, endLine)

      // Add line numbers
      const numberedLines = selectedLines.map((line, i) => `${startLine + i + 1}: ${line}`)

      return {
        id,
        name: 'read',
        output: numberedLines.join('\n'),
      }
    }

    // Return full file with line numbers
    const lines = content.split('\n')
    const numberedLines = lines.map((line, i) => `${i + 1}: ${line}`)

    return {
      id,
      name: 'read',
      output: numberedLines.join('\n'),
    }
  } catch (error) {
    return {
      id,
      name: 'read',
      output: '',
      error: `Failed to read file: ${(error as Error).message}`,
    }
  }
}

/**
 * Execute write file
 */
async function executeWrite(id: string, input: Record<string, unknown>): Promise<ToolResult> {
  const filePath = input.file_path as string
  const content = input.content as string

  if (!filePath || content === undefined) {
    return {
      id,
      name: 'write',
      output: '',
      error: 'Missing file_path or content parameter',
    }
  }

  log.debug('Writing file', { filePath })

  try {
    const fs = await import('fs/promises')
    const path = await import('path')

    // Ensure directory exists
    await fs.mkdir(path.dirname(filePath), { recursive: true })

    await fs.writeFile(filePath, content, 'utf-8')

    return {
      id,
      name: 'write',
      output: `File written successfully: ${filePath}`,
    }
  } catch (error) {
    return {
      id,
      name: 'write',
      output: '',
      error: `Failed to write file: ${(error as Error).message}`,
    }
  }
}

/**
 * Execute grep search
 */
async function executeGrep(id: string, input: Record<string, unknown>): Promise<ToolResult> {
  const pattern = input.pattern as string
  const searchPath = (input.path as string) ?? process.cwd()
  const glob = input.glob as string | undefined
  const outputMode = (input.output_mode as string) ?? 'files_with_matches'

  if (!pattern) {
    return { id, name: 'grep', output: '', error: 'Missing pattern parameter' }
  }

  log.debug('Executing grep', { pattern, searchPath, glob, outputMode })

  try {
    const args = ['rg', pattern, searchPath]

    if (glob) {
      args.push('--glob', glob)
    }

    if (outputMode === 'files_with_matches') {
      args.push('-l')
    } else if (outputMode === 'count') {
      args.push('-c')
    }

    const { stdout, exitCode } = await spawnAsync(args)

    if (exitCode !== 0 && stdout.trim().length === 0) {
      return {
        id,
        name: 'grep',
        output: 'No matches found',
      }
    }

    return {
      id,
      name: 'grep',
      output: stdout || 'No matches found',
    }
  } catch (error) {
    return {
      id,
      name: 'grep',
      output: '',
      error: `Grep failed: ${(error as Error).message}`,
    }
  }
}

/**
 * Execute glob file search
 */
async function executeGlob(id: string, input: Record<string, unknown>): Promise<ToolResult> {
  const pattern = input.pattern as string
  const searchPath = (input.path as string) ?? process.cwd()

  if (!pattern) {
    return { id, name: 'glob', output: '', error: 'Missing pattern parameter' }
  }

  log.debug('Executing glob', { pattern, searchPath })

  try {
    // Use Node's fs + minimatch for glob pattern matching (no external dep needed)
    const { readdirSync, statSync } = await import('fs')
    const { join, relative } = await import('path')

    const files: string[] = []

    // Simple recursive glob implementation
    function walk(dir: string) {
      try {
        const entries = readdirSync(dir, { withFileTypes: true })
        for (const entry of entries) {
          const fullPath = join(dir, entry.name)
          if (entry.isDirectory()) {
            walk(fullPath)
          } else if (entry.isFile()) {
            // Check if path matches pattern (simple wildcard support)
            const relPath = relative(searchPath, fullPath)
            if (matchesPattern(relPath, pattern)) {
              files.push(relPath)
            }
          }
        }
      } catch (e) {
        // Skip dirs we can't read
      }
    }

    // Basic wildcard matching (supports *, **, .ext patterns)
    function matchesPattern(path: string, pattern: string): boolean {
      if (pattern === '*' || pattern === '**') return true
      if (pattern.startsWith('*.')) {
        return path.endsWith(pattern.slice(1))
      }
      if (pattern.includes('*')) {
        const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$')
        return regex.test(path)
      }
      return path === pattern
    }

    walk(searchPath)

    if (files.length === 0) {
      return {
        id,
        name: 'glob',
        output: 'No files found',
      }
    }

    return {
      id,
      name: 'glob',
      output: files.join('\n'),
    }
  } catch (error) {
    return {
      id,
      name: 'glob',
      output: '',
      error: `Glob failed: ${(error as Error).message}`,
    }
  }
}

/**
 * Build artifact content from agent execution
 */
function buildArtifactContent(config: AgentConfig, turns: AgentTurn[]): string {
  const timestamp = new Date().toISOString()

  let content = `# ${config.role.toUpperCase()} Agent Output\n\n`
  content += `**Generated**: ${timestamp}\n`
  content += `**Task**: ${config.task}\n\n`

  if (config.context && config.context.length > 0) {
    content += `## Context Provided\n\n${config.context.length} context items\n\n`
  }

  content += `## Execution Trace\n\n`

  for (const turn of turns) {
    content += `### Turn ${turn.turn}\n\n`

    if (turn.toolCalls && turn.toolCalls.length > 0) {
      content += `**Tools Called**: ${turn.toolCalls.map((t) => t.name).join(', ')}\n\n`

      for (let i = 0; i < turn.toolCalls.length; i++) {
        const call = turn.toolCalls[i]!
        const result = turn.toolResults?.[i]

        content += `#### Tool: ${call.name}\n\n`
        content += `**Input**:\n\`\`\`json\n${JSON.stringify(call.input, null, 2)}\n\`\`\`\n\n`

        if (result) {
          if (result.error) {
            content += `**Error**: ${result.error}\n\n`
          } else {
            content += `**Output**:\n\`\`\`\n${result.output.substring(0, 1000)}\n\`\`\`\n\n`
          }
        }
      }
    }

    content += `**Agent Response**:\n\n${turn.output}\n\n`

    if (turn.usage) {
      content += `**Tokens**: ${turn.usage.inputTokens} in / ${turn.usage.outputTokens} out`
      if (turn.usage.thinkingTokens) {
        content += ` / ${turn.usage.thinkingTokens} thinking`
      }
      content += `\n\n`
    }

    content += `---\n\n`
  }

  return content
}
