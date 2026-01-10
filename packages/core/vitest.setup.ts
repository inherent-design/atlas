/**
 * Vitest global setup
 * Runs once before all test files
 */

// Suppress MaxListenersExceededWarning from Vitest fork pool
// Each forked test process adds exit listeners, which can exceed Node's default limit of 10
process.setMaxListeners(20)
