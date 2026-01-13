/**
 * Agent orchestration system - Public API
 *
 * Multi-agent execution runtime with:
 * - Single agent executor (multi-turn with tools + RAG)
 * - Work coordinator (sequence, parallel, conditional, loop)
 */

// Core execution
export { executeAgent } from './executor.js'
export { executeWork, buildWorkContext } from './coordinator.js'

// Types
export type {
  AgentRole,
  AgentConfig,
  AgentResult,
  AgentTurn,
  ToolCall,
  ToolResult,
  WorkNode,
  WorkNodeType,
  AgentNode,
  SequenceNode,
  ParallelNode,
  ConditionalNode,
  LoopNode,
  LoopType,
  WorkContext,
  WorkResult,
  ToolDefinition,
} from './types.js'

export { AGENT_TOOLS } from './types.js'

// Strategies: All removed (2026-01-10) - zero usage confirmed by architecture audit
