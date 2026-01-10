/**
 * Predefined work strategies
 *
 * Common multi-agent patterns ready to use:
 * - observe: Single observer agent
 * - research: Observer → Connector → Integrator
 * - validate-claim: Parallel observers → Challenger → Integrator
 * - extract-learning: Explainer → Challenger (loop) → Integrator
 */

import { createLogger } from '../../shared/logger'
import type { WorkNode, AgentNode, SequenceNode, ParallelNode, LoopNode } from './types'

const log = createLogger('agents:strategies')

/**
 * Single observer strategy
 * Use for data gathering tasks
 */
export function observe(task: string, project?: string): AgentNode {
  log.debug('Building observe strategy', { project })
  return {
    type: 'agent',
    id: 'observer',
    config: {
      role: 'observer',
      task,
      project,
    },
  }
}

/**
 * Research strategy: Observer → Connector → Integrator
 * Use for exploring and understanding a domain
 */
export function research(
  observationTask: string,
  integrationTask: string,
  project?: string
): SequenceNode {
  log.debug('Building research strategy', { project })
  return {
    type: 'sequence',
    passContext: true,
    children: [
      {
        type: 'agent',
        id: 'observer',
        config: {
          role: 'observer',
          task: observationTask,
          project,
        },
      },
      {
        type: 'agent',
        id: 'connector',
        config: {
          role: 'connector',
          task: 'Analyze the observations and identify patterns, clusters, and relationships.',
          project,
        },
      },
      {
        type: 'agent',
        id: 'integrator',
        config: {
          role: 'integrator',
          task: integrationTask,
          project,
        },
      },
    ],
  }
}

/**
 * Validate claim strategy: Parallel observers → Challenger → Integrator
 * Use for verifying claims with multiple independent observations
 */
export function validateClaim(
  claim: string,
  observationTasks: string[],
  integrationTask: string,
  project?: string
): SequenceNode {
  log.debug('Building validateClaim strategy', { taskCount: observationTasks.length, project })
  // Create parallel observers
  const parallelObservers: ParallelNode = {
    type: 'parallel',
    children: observationTasks.map((task, i) => ({
      type: 'agent',
      id: `observer_${i}`,
      config: {
        role: 'observer',
        task,
        project,
      },
    })),
  }

  // Create explainer to generate hypotheses about the claim
  const explainer: AgentNode = {
    type: 'agent',
    id: 'explainer',
    config: {
      role: 'explainer',
      task: `Generate 2-3 competing hypotheses about this claim: "${claim}"\n\nBased on the observations gathered, propose testable explanations.`,
      project,
    },
  }

  // Create challenger to validate hypotheses
  const challenger: AgentNode = {
    type: 'agent',
    id: 'challenger',
    config: {
      role: 'challenger',
      task: 'Test each hypothesis systematically. Use tools to gather evidence for or against each prediction.',
      project,
    },
  }

  // Create integrator to synthesize findings
  const integrator: AgentNode = {
    type: 'agent',
    id: 'integrator',
    config: {
      role: 'integrator',
      task: integrationTask,
      project,
    },
  }

  return {
    type: 'sequence',
    passContext: true,
    children: [parallelObservers, explainer, challenger, integrator],
  }
}

/**
 * Extract learning strategy: Explainer → Challenger (loop until validated)
 * Use for iteratively testing and refining understanding
 */
export function extractLearning(
  domain: string,
  observations: string[],
  project?: string,
  maxIterations: number = 3
): SequenceNode {
  // Create explainer with observations as context
  const explainer: AgentNode = {
    type: 'agent',
    id: 'explainer',
    config: {
      role: 'explainer',
      task: `Generate competing hypotheses about: ${domain}\n\nPropose testable explanations with falsifiable predictions.`,
      context: observations,
      project,
    },
  }

  // Create challenger in adaptive loop
  const challengerLoop: LoopNode = {
    type: 'loop',
    loopType: 'adaptive',
    adaptiveConfig: {
      evaluatorRole: 'challenger',
      maxIterations,
    },
    child: {
      type: 'agent',
      id: 'challenger',
      config: {
        role: 'challenger',
        task: `Test hypotheses systematically. If all predictions are validated, set continue_loop=false in your response. If some are refuted, continue testing refined hypotheses.`,
        project,
      },
    },
  }

  // Create integrator to synthesize validated learnings
  const integrator: AgentNode = {
    type: 'agent',
    id: 'integrator',
    config: {
      role: 'integrator',
      task: `Synthesize validated hypotheses into actionable insights about ${domain}.`,
      project,
    },
  }

  return {
    type: 'sequence',
    passContext: true,
    children: [explainer, challengerLoop, integrator],
  }
}

/**
 * Meta strategy: Let meta agent design the workflow
 * Use for complex tasks where optimal agent topology is unclear
 */
export function meta(task: string, project?: string): AgentNode {
  return {
    type: 'agent',
    id: 'meta',
    config: {
      role: 'meta',
      task: `Design and execute a multi-agent workflow for: ${task}\n\nAnalyze the task, determine optimal agent sequence, and coordinate execution.`,
      project,
    },
  }
}

/**
 * Deep dive strategy: Observe → Connector → Explainer → Challenger → Integrator
 * Full research pipeline with validation
 */
export function deepDive(
  topic: string,
  explorationTask: string,
  integrationTask: string,
  project?: string
): SequenceNode {
  return {
    type: 'sequence',
    passContext: true,
    children: [
      {
        type: 'agent',
        id: 'observer',
        config: {
          role: 'observer',
          task: explorationTask,
          project,
        },
      },
      {
        type: 'agent',
        id: 'connector',
        config: {
          role: 'connector',
          task: 'Identify patterns and relationships in the observations.',
          project,
        },
      },
      {
        type: 'agent',
        id: 'explainer',
        config: {
          role: 'explainer',
          task: `Generate competing hypotheses about ${topic} based on the patterns identified.`,
          project,
        },
      },
      {
        type: 'agent',
        id: 'challenger',
        config: {
          role: 'challenger',
          task: 'Systematically test each hypothesis. Use tools to gather evidence.',
          project,
        },
      },
      {
        type: 'agent',
        id: 'integrator',
        config: {
          role: 'integrator',
          task: integrationTask,
          project,
        },
      },
    ],
  }
}

/**
 * Parallel exploration strategy: Multiple observers with different angles
 * Use when you want diverse perspectives on same topic
 */
export function parallelExplore(
  tasks: Array<{ role: 'observer' | 'explainer'; task: string }>,
  synthesisTask: string,
  project?: string
): SequenceNode {
  const parallelAgents: ParallelNode = {
    type: 'parallel',
    children: tasks.map((t, i) => ({
      type: 'agent',
      id: `${t.role}_${i}`,
      config: {
        role: t.role,
        task: t.task,
        project,
      },
    })),
  }

  const synthesizer: AgentNode = {
    type: 'agent',
    id: 'integrator',
    config: {
      role: 'integrator',
      task: synthesisTask,
      project,
    },
  }

  return {
    type: 'sequence',
    passContext: true,
    children: [parallelAgents, synthesizer],
  }
}

/**
 * Iterative refinement: Integrate → Challenge → Integrate (loop)
 * Use for building something that needs validation rounds
 */
export function iterativeRefinement(
  buildTask: string,
  validationTask: string,
  project?: string,
  maxIterations: number = 3
): LoopNode {
  return {
    type: 'loop',
    loopType: 'count',
    iterations: maxIterations,
    child: {
      type: 'sequence',
      passContext: true,
      children: [
        {
          type: 'agent',
          id: 'integrator',
          config: {
            role: 'integrator',
            task: buildTask,
            project,
          },
        },
        {
          type: 'agent',
          id: 'challenger',
          config: {
            role: 'challenger',
            task: validationTask,
            project,
          },
        },
      ],
    },
  }
}

/**
 * Conditional branch: Observe, then decide path
 * Use when workflow depends on observations
 */
export function conditionalPath(
  observationTask: string,
  condition: string,
  thenTask: string,
  elseTask: string,
  project?: string
): SequenceNode {
  return {
    type: 'sequence',
    passContext: true,
    children: [
      {
        type: 'agent',
        id: 'observer',
        config: {
          role: 'observer',
          task: observationTask,
          project,
        },
      },
      {
        type: 'conditional',
        condition,
        conditionContext: {},
        then: {
          type: 'agent',
          id: 'then_integrator',
          config: {
            role: 'integrator',
            task: thenTask,
            project,
          },
        },
        else: {
          type: 'agent',
          id: 'else_integrator',
          config: {
            role: 'integrator',
            task: elseTask,
            project,
          },
        },
      },
    ],
  }
}
