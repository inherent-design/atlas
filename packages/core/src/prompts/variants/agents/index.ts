/**
 * Agent Prompt Variants Index
 *
 * Exports all agent prompts (both 3-role and 6-role models).
 */

// 6-role model agents
export { observerPrompt } from './observer.js'
export { connectorPrompt } from './connector.js'
export { explainerPrompt } from './explainer.js'
export { challengerPrompt } from './challenger.js'
export { integrator6RolePrompt } from './integrator-6role.js'
export { metaPrompt } from './meta.js'

// 3-role model agents
export { sensorPrompt } from './sensor.js'
export { reasonerPrompt } from './reasoner.js'
export { integratorPrompt } from './integrator-3role.js'
