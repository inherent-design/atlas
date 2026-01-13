/**
 * Work coordinator - orchestrate multi-agent workflows
 *
 * Handles:
 * - Sequence execution (ordered)
 * - Parallel execution (concurrent)
 * - Conditional branching
 * - Loop execution (count, condition, infinite, adaptive)
 * - Context passing between nodes
 * - Error handling and retries
 */

import { createLogger, startTimer } from '../../shared/logger.js'
import { executeAgent } from './executor.js'
import type {
  WorkNode,
  WorkContext,
  WorkResult,
  AgentNode,
  SequenceNode,
  ParallelNode,
  ConditionalNode,
  LoopNode,
  AgentResult,
} from './types.js'

const log = createLogger('agents:coordinator')

/**
 * Execute a work graph
 */
export async function executeWork(
  node: WorkNode,
  context: WorkContext = { agents: [], variables: {}, project: 'default' }
): Promise<WorkResult> {
  const startTime = Date.now()
  const endTimer = startTimer('work:execute')

  log.info('Executing work graph', {
    nodeType: node.type,
    nodeId: node.id,
    project: context.project,
  })

  try {
    const results = await executeNode(node, context)

    const took = Date.now() - startTime
    endTimer()

    // Determine overall status based on agent results
    const allSuccess = results.agents.every((a) => a.status === 'success')
    const anyError = results.agents.some((a) => a.status === 'error')
    const anyMaxTurns = results.agents.some((a) => a.status === 'max_turns')

    const status: 'success' | 'error' | 'partial' = allSuccess
      ? 'success'
      : anyError || anyMaxTurns
        ? 'partial'
        : 'success'

    log.info('Work graph completed', {
      nodeType: node.type,
      agents: results.agents.length,
      status,
      took,
    })

    return {
      agents: results.agents,
      took,
      status,
    }
  } catch (error) {
    const took = Date.now() - startTime
    endTimer()

    log.error('Work graph failed', {
      nodeType: node.type,
      error: (error as Error).message,
    })

    return {
      agents: context.agents,
      took,
      status: 'error',
      error: (error as Error).message,
    }
  }
}

/**
 * Execute a single work node (recursive)
 */
async function executeNode(node: WorkNode, context: WorkContext): Promise<WorkContext> {
  log.debug('Executing node', { type: node.type, id: node.id })

  switch (node.type) {
    case 'agent':
      return await executeAgentNode(node, context)
    case 'sequence':
      return await executeSequenceNode(node, context)
    case 'parallel':
      return await executeParallelNode(node, context)
    case 'conditional':
      return await executeConditionalNode(node, context)
    case 'loop':
      return await executeLoopNode(node, context)
    default:
      throw new Error(`Unknown node type: ${(node as any).type}`)
  }
}

/**
 * Execute agent node
 */
async function executeAgentNode(node: AgentNode, context: WorkContext): Promise<WorkContext> {
  log.debug('Executing agent node', { role: node.config.role })

  // Merge project and emit from context if not specified
  const config = {
    ...node.config,
    project: node.config.project ?? context.project,
    emit: node.config.emit ?? (context.variables._emit as ((event: any) => void) | undefined),
  }

  const result = await executeAgent(config)

  // Add result to context
  return {
    ...context,
    agents: [...context.agents, result],
    variables: {
      ...context.variables,
      [`${node.id || node.config.role}_output`]: result.output,
      [`${node.id || node.config.role}_status`]: result.status,
    },
  }
}

/**
 * Execute sequence node (children in order)
 */
async function executeSequenceNode(node: SequenceNode, context: WorkContext): Promise<WorkContext> {
  log.debug('Executing sequence node', {
    children: node.children.length,
    passContext: node.passContext,
  })

  let currentContext = context

  for (let i = 0; i < node.children.length; i++) {
    const child = node.children[i]!

    log.debug('Executing sequence child', {
      index: i,
      total: node.children.length,
      type: child.type,
    })

    // Execute child with current context
    currentContext = await executeNode(child, currentContext)

    // If passContext enabled, add previous agent outputs to next agent's context
    if (node.passContext && i < node.children.length - 1) {
      const nextChild = node.children[i + 1]
      if (nextChild?.type === 'agent') {
        // Get outputs from all previous agents in this sequence
        const previousOutputs = currentContext.agents
          .slice(context.agents.length) // Only agents from this sequence
          .map((a) => `[${a.role.toUpperCase()}]\n${a.output}`)

        // Add to next agent's context
        nextChild.config.context = [...(nextChild.config.context || []), ...previousOutputs]
      }
    }
  }

  return currentContext
}

/**
 * Execute parallel node (children concurrently)
 */
async function executeParallelNode(node: ParallelNode, context: WorkContext): Promise<WorkContext> {
  const maxConcurrency = node.maxConcurrency ?? node.children.length

  log.debug('Executing parallel node', {
    children: node.children.length,
    maxConcurrency,
  })

  // Execute children in batches
  const results: WorkContext[] = []

  for (let i = 0; i < node.children.length; i += maxConcurrency) {
    const batch = node.children.slice(i, i + maxConcurrency)

    log.debug('Executing parallel batch', {
      batchIndex: i / maxConcurrency,
      batchSize: batch.length,
    })

    const batchResults = await Promise.all(
      batch.map((child) => executeNode(child, { ...context })) // Clone context for each
    )

    results.push(...batchResults)
  }

  // Merge all results into single context
  const mergedContext: WorkContext = {
    ...context,
    agents: [...context.agents],
    variables: { ...context.variables },
  }

  for (const result of results) {
    mergedContext.agents.push(...result.agents.slice(context.agents.length))
    Object.assign(mergedContext.variables, result.variables)
  }

  return mergedContext
}

/**
 * Execute conditional node (branch based on condition)
 */
async function executeConditionalNode(
  node: ConditionalNode,
  context: WorkContext
): Promise<WorkContext> {
  log.debug('Executing conditional node', { condition: node.condition })

  // Evaluate condition
  const conditionContext = { ...context.variables, ...(node.conditionContext || {}) }

  let conditionResult: boolean
  try {
    // Create safe evaluation context
    const evalContext = {
      context: conditionContext,
      agents: context.agents,
    }

    // Evaluate condition as JavaScript expression
    // eslint-disable-next-line no-new-func
    const fn = new Function('ctx', `with(ctx) { return ${node.condition} }`)
    conditionResult = fn(evalContext)

    log.debug('Condition evaluated', {
      condition: node.condition,
      result: conditionResult,
    })
  } catch (error) {
    log.error('Condition evaluation failed', {
      condition: node.condition,
      error: (error as Error).message,
    })
    throw new Error(`Condition evaluation failed: ${(error as Error).message}`)
  }

  // Execute appropriate branch
  if (conditionResult) {
    log.debug('Executing then branch')
    return await executeNode(node.then, context)
  } else if (node.else) {
    log.debug('Executing else branch')
    return await executeNode(node.else, context)
  } else {
    log.debug('Condition false, no else branch')
    return context
  }
}

/**
 * Execute loop node
 */
async function executeLoopNode(node: LoopNode, context: WorkContext): Promise<WorkContext> {
  log.debug('Executing loop node', {
    loopType: node.loopType,
    iterations: node.iterations,
  })

  switch (node.loopType) {
    case 'count':
      return await executeCountLoop(node, context)
    case 'condition':
      return await executeConditionLoop(node, context)
    case 'infinite':
      return await executeInfiniteLoop(node, context)
    case 'adaptive':
      return await executeAdaptiveLoop(node, context)
    default:
      throw new Error(`Unknown loop type: ${node.loopType}`)
  }
}

/**
 * Execute count-based loop (fixed iterations)
 */
async function executeCountLoop(node: LoopNode, context: WorkContext): Promise<WorkContext> {
  const iterations = node.iterations ?? 1

  log.debug('Executing count loop', { iterations })

  let currentContext = context

  for (let i = 0; i < iterations; i++) {
    log.debug('Loop iteration', { current: i + 1, total: iterations })

    // Update loop context with iteration info
    const loopContext = {
      ...currentContext,
      variables: {
        ...currentContext.variables,
        ...node.loopContext,
        loop_iteration: i,
        loop_total: iterations,
      },
    }

    currentContext = await executeNode(node.child, loopContext)
  }

  return currentContext
}

/**
 * Execute condition-based loop (while condition true)
 */
async function executeConditionLoop(node: LoopNode, context: WorkContext): Promise<WorkContext> {
  if (!node.continueWhile) {
    throw new Error('Condition loop requires continueWhile expression')
  }

  log.debug('Executing condition loop', { condition: node.continueWhile })

  let currentContext = context
  let iteration = 0
  const MAX_ITERATIONS = 100 // Safety limit

  while (iteration < MAX_ITERATIONS) {
    // Evaluate condition
    const conditionContext = { ...currentContext.variables, ...node.loopContext }

    let shouldContinue: boolean
    try {
      const evalContext = {
        context: conditionContext,
        agents: currentContext.agents,
      }

      // eslint-disable-next-line no-new-func
      const fn = new Function('ctx', `with(ctx) { return ${node.continueWhile} }`)
      shouldContinue = fn(evalContext)

      log.debug('Loop condition evaluated', {
        iteration,
        condition: node.continueWhile,
        result: shouldContinue,
      })
    } catch (error) {
      log.error('Loop condition evaluation failed', {
        condition: node.continueWhile,
        error: (error as Error).message,
      })
      break
    }

    if (!shouldContinue) {
      log.debug('Loop condition false, exiting')
      break
    }

    // Execute child
    const loopContext = {
      ...currentContext,
      variables: {
        ...currentContext.variables,
        ...node.loopContext,
        loop_iteration: iteration,
      },
    }

    currentContext = await executeNode(node.child, loopContext)
    iteration++
  }

  if (iteration >= MAX_ITERATIONS) {
    log.warn('Loop reached max iterations limit', { max: MAX_ITERATIONS })
  }

  return currentContext
}

/**
 * Execute infinite loop (manual control)
 */
async function executeInfiniteLoop(node: LoopNode, context: WorkContext): Promise<WorkContext> {
  log.debug('Executing infinite loop')

  // Infinite loops should have external stop mechanism
  // For now, treat as single iteration with warning
  log.warn('Infinite loop executed as single iteration (external control not yet implemented)')

  return await executeNode(node.child, {
    ...context,
    variables: {
      ...context.variables,
      ...node.loopContext,
    },
  })
}

/**
 * Execute adaptive loop (agent decides when to stop)
 */
async function executeAdaptiveLoop(node: LoopNode, context: WorkContext): Promise<WorkContext> {
  const maxIterations = node.adaptiveConfig?.maxIterations ?? 10
  const evaluatorRole = node.adaptiveConfig?.evaluatorRole ?? 'meta'

  log.debug('Executing adaptive loop', {
    maxIterations,
    evaluatorRole,
  })

  let currentContext = context
  let iteration = 0

  while (iteration < maxIterations) {
    log.debug('Adaptive loop iteration', { current: iteration + 1, max: maxIterations })

    // Execute child
    const loopContext = {
      ...currentContext,
      variables: {
        ...currentContext.variables,
        ...node.loopContext,
        loop_iteration: iteration,
        loop_max: maxIterations,
      },
    }

    currentContext = await executeNode(node.child, loopContext)

    // Check if we should continue (agent decides)
    // Look for "continue_loop" variable in context
    const shouldContinue = currentContext.variables.continue_loop as boolean | undefined

    if (shouldContinue === false) {
      log.debug('Adaptive loop agent signaled stop')
      break
    }

    iteration++
  }

  if (iteration >= maxIterations) {
    log.warn('Adaptive loop reached max iterations', { max: maxIterations })
  }

  return currentContext
}

/**
 * Build work context from agent results (helper)
 */
export function buildWorkContext(
  agents: AgentResult[],
  project: string = 'default',
  variables: Record<string, unknown> = {},
  emit?: (event: any) => void
): WorkContext {
  const contextVariables = emit ? { ...variables, _emit: emit } : variables
  return {
    agents,
    variables: contextVariables,
    project,
  }
}
