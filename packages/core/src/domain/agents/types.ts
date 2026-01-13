/**
 * Agent orchestration types
 *
 * Defines types for multi-agent work execution:
 * - Agent roles (observer, connector, explainer, challenger, integrator, meta)
 * - Work nodes (agent, sequence, parallel, conditional, loop)
 * - Execution context and results
 */

import type { z } from 'zod'
import type { ToolDefinition as BaseToolDefinition } from '../../services/llm/message.js'
import type { AgentRole } from '../../prompts/types.js'

// ============================================
// Agent Roles
// ============================================

/**
 * Agent role types matching INTERSTITIA philosophy
 * Imported from prompts layer (single source of truth)
 */
export type { AgentRole }

/**
 * Agent configuration
 */
export interface AgentConfig {
  /** Agent role (determines system prompt) */
  role: AgentRole
  /** Task instruction for this agent */
  task: string
  /** Context to provide to agent (from RAG or previous agents) */
  context?: string[]
  /** Max turns for this agent (default: 5) */
  maxTurns?: number
  /** Temperature (default: 0.7) */
  temperature?: number
  /** Max tokens per turn (default: 4000) */
  maxTokens?: number
  /** QNTM keys to search for RAG context */
  qntmKeys?: string[]
  /** Consolidation level filter for RAG (0=raw, 1=dedup, 2=topic, 3=domain, 4=meta) */
  consolidationLevel?: 0 | 1 | 2 | 3 | 4
  /** Project name for artifact output paths */
  project?: string
  /** Whether to write artifacts to disk (default: true) */
  writeArtifacts?: boolean
  /** Event emitter for broadcasting execution events */
  emit?: (event: any) => void
}

// ============================================
// Tool Execution
// ============================================

/**
 * Tool call from LLM
 */
export interface ToolCall {
  id: string
  name: string
  input: Record<string, unknown>
}

/**
 * Tool execution result
 */
export interface ToolResult {
  id: string
  name: string
  output: string
  error?: string
}

// ============================================
// Agent Execution
// ============================================

/**
 * Agent turn in conversation
 */
export interface AgentTurn {
  /** Turn number */
  turn: number
  /** User/system message to agent */
  input?: string
  /** Agent's response */
  output: string
  /** Tools called by agent */
  toolCalls?: ToolCall[]
  /** Tool execution results */
  toolResults?: ToolResult[]
  /** Thinking trace (if available) */
  thinking?: string
  /** Token usage for this turn */
  usage?: {
    inputTokens: number
    outputTokens: number
    thinkingTokens?: number
  }
}

/**
 * Result from single agent execution
 */
export interface AgentResult {
  /** Agent role */
  role: AgentRole
  /** Task that was executed */
  task: string
  /** All conversation turns */
  turns: AgentTurn[]
  /** Final output from last turn */
  output: string
  /** Artifacts written to disk */
  artifacts: string[]
  /** Total token usage */
  usage: {
    inputTokens: number
    outputTokens: number
    thinkingTokens?: number
  }
  /** Execution status */
  status: 'success' | 'error' | 'max_turns'
  /** Error message if failed */
  error?: string
  /** Execution time in ms */
  took: number
}

// ============================================
// Work Graph
// ============================================

/**
 * Work node types
 */
export type WorkNodeType = 'agent' | 'sequence' | 'parallel' | 'conditional' | 'loop'

/**
 * Base work node
 */
export interface BaseWorkNode {
  type: WorkNodeType
  /** Optional node ID for referencing */
  id?: string
}

/**
 * Agent work node - execute single agent
 */
export interface AgentNode extends BaseWorkNode {
  type: 'agent'
  config: AgentConfig
}

/**
 * Sequence work node - execute children in order
 */
export interface SequenceNode extends BaseWorkNode {
  type: 'sequence'
  children: WorkNode[]
  /** Pass context from each node to next */
  passContext?: boolean
}

/**
 * Parallel work node - execute children concurrently
 */
export interface ParallelNode extends BaseWorkNode {
  type: 'parallel'
  children: WorkNode[]
  /** Max concurrent executions (default: all) */
  maxConcurrency?: number
}

/**
 * Conditional work node - execute based on predicate
 */
export interface ConditionalNode extends BaseWorkNode {
  type: 'conditional'
  /** Condition to evaluate (JavaScript expression) */
  condition: string
  /** Execute if condition true */
  then: WorkNode
  /** Execute if condition false */
  else?: WorkNode
  /** Context available to condition (from previous nodes) */
  conditionContext?: Record<string, unknown>
}

/**
 * Loop types
 */
export type LoopType = 'count' | 'condition' | 'infinite' | 'adaptive'

/**
 * Loop work node - execute child repeatedly
 */
export interface LoopNode extends BaseWorkNode {
  type: 'loop'
  loopType: LoopType
  child: WorkNode
  /** For count loops: number of iterations */
  iterations?: number
  /** For condition loops: continue while this is true */
  continueWhile?: string
  /** For adaptive loops: agent decides when to stop (exit condition in task) */
  adaptiveConfig?: {
    /** Agent role to evaluate loop continuation */
    evaluatorRole?: AgentRole
    /** Max iterations before forced exit */
    maxIterations?: number
  }
  /** Context passed to each iteration */
  loopContext?: Record<string, unknown>
}

/**
 * Union type for all work nodes
 */
export type WorkNode = AgentNode | SequenceNode | ParallelNode | ConditionalNode | LoopNode

// ============================================
// Work Execution
// ============================================

/**
 * Work execution context (passed between nodes)
 */
export interface WorkContext {
  /** Results from previous agent executions */
  agents: AgentResult[]
  /** Shared variables accessible to all nodes */
  variables: Record<string, unknown>
  /** Project name for artifact paths */
  project: string
}

/**
 * Work execution result
 */
export interface WorkResult {
  /** All agent results in execution order */
  agents: AgentResult[]
  /** Total execution time in ms */
  took: number
  /** Status */
  status: 'success' | 'error' | 'partial'
  /** Error if failed */
  error?: string
}

// ============================================
// Tool Definitions
// ============================================

/**
 * Tool definition for agent use (extends base with stricter schema)
 */
export interface ToolDefinition extends BaseToolDefinition {
  inputSchema: {
    type: 'object'
    properties: Record<string, unknown>
    required?: string[]
  }
}

/**
 * Available tools for agents
 */
export const AGENT_TOOLS: ToolDefinition[] = [
  {
    name: 'bash',
    description:
      'Execute bash commands. Returns stdout/stderr. Use for running tests, checking files, git operations, etc.',
    inputSchema: {
      type: 'object',
      properties: {
        command: {
          type: 'string',
          description: 'The bash command to execute',
        },
        timeout: {
          type: 'number',
          description: 'Timeout in milliseconds (max 600000)',
        },
      },
      required: ['command'],
    },
  },
  {
    name: 'read',
    description:
      'Read file contents from filesystem. Use for examining code, configs, documentation.',
    inputSchema: {
      type: 'object',
      properties: {
        file_path: {
          type: 'string',
          description: 'Absolute path to file to read',
        },
        offset: {
          type: 'number',
          description: 'Line number to start reading from (optional)',
        },
        limit: {
          type: 'number',
          description: 'Number of lines to read (optional)',
        },
      },
      required: ['file_path'],
    },
  },
  {
    name: 'write',
    description:
      'Write content to file (creates or overwrites). Use for creating new files or completely replacing existing ones.',
    inputSchema: {
      type: 'object',
      properties: {
        file_path: {
          type: 'string',
          description: 'Absolute path to file to write',
        },
        content: {
          type: 'string',
          description: 'Content to write to file',
        },
      },
      required: ['file_path', 'content'],
    },
  },
  {
    name: 'grep',
    description:
      'Search for patterns in files using ripgrep. Use for finding code, text, or patterns across codebase.',
    inputSchema: {
      type: 'object',
      properties: {
        pattern: {
          type: 'string',
          description: 'Regular expression pattern to search for',
        },
        path: {
          type: 'string',
          description: 'Directory or file to search in (optional, defaults to cwd)',
        },
        glob: {
          type: 'string',
          description: 'Glob pattern to filter files (e.g., "*.ts")',
        },
        output_mode: {
          type: 'string',
          enum: ['content', 'files_with_matches', 'count'],
          description: 'Output mode (default: files_with_matches)',
        },
      },
      required: ['pattern'],
    },
  },
  {
    name: 'glob',
    description: 'Find files matching glob pattern. Use for discovering files by name/extension.',
    inputSchema: {
      type: 'object',
      properties: {
        pattern: {
          type: 'string',
          description: 'Glob pattern (e.g., "**/*.ts", "src/**/*.test.ts")',
        },
        path: {
          type: 'string',
          description: 'Directory to search in (optional, defaults to cwd)',
        },
      },
      required: ['pattern'],
    },
  },
]
