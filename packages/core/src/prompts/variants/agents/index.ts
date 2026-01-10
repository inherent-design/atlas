/**
 * Agent Prompt Variants Index
 *
 * Exports all agent prompts (both 3-role and 6-role models).
 */

// 6-role model agents
export { observerPrompt } from './observer'
export { connectorPrompt } from './connector'
export { explainerPrompt } from './explainer'
export { challengerPrompt } from './challenger'
export { integrator6RolePrompt } from './integrator-6role'
export { metaPrompt } from './meta'

// 3-role model agents
export { sensorPrompt } from './sensor'
export { reasonerPrompt } from './reasoner'
export { integratorPrompt } from './integrator-3role'
