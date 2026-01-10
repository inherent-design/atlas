/**
 * Agent orchestration system - Public API
 *
 * Multi-agent execution runtime with:
 * - Single agent executor (multi-turn with tools + RAG)
 * - Work coordinator (sequence, parallel, conditional, loop)
 * - Predefined strategies (observe, research, validate-claim, etc.)
 */

// Core execution
export { executeAgent } from './executor'
export { executeWork, buildWorkContext } from './coordinator'

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
} from './types'

export { AGENT_TOOLS } from './types'

// Prompts (migrated to unified registry)
export { buildAgentPrompt, buildArtifactPath, buildFrontmatter } from '../../prompts/builders'

// Strategies
export {
  observe,
  research,
  validateClaim,
  extractLearning,
  meta,
  deepDive,
  parallelExplore,
  iterativeRefinement,
  conditionalPath,
} from './strategies'
