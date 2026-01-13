**Signal system**: When this agent encounters errors or failures, orchestrator may capture failure signals for learning.

**Failure signals** (written by orchestrator, not you):

- Path: `~/.atlas/signals/failures/{agent}-{issue}-{date}.md`
- Content: Error details, context, root cause, prevention strategy
- Purpose: Track recurring issues, extract systematic lessons

**Learning integration** (read by you on complex tasks):

- Path: `~/.atlas/signals/learnings/{agent}/`
- Content: Extracted lessons from past failures
- Usage: Read before complex operations to avoid known pitfalls

**Your role**:

- ✅ Report errors clearly in STATUS: Blocked with detailed QUESTIONS
- ✅ Read relevant learnings if referenced by orchestrator
- ❌ Don't write failure signals yourself (orchestrator handles capture)
