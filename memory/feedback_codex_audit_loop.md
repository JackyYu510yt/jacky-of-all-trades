---
name: feedback_codex_audit_loop
description: User routes plans through Codex (OpenAI) for external audit before execution — expect a feedback loop, not single-shot approval
type: feedback
originSessionId: e603725b-6687-40da-af59-af62bed45597
---
When producing a plan for a non-trivial new script or project, the user often hands the plan off to Codex for an external audit before executing it. Expect a multi-turn loop: plan → Codex feedback → integrate → re-review → execute.

**Why:** User explicitly described this workflow while creating the `prep` skill. The Codex audit catches blind spots, missing self-healing paths, and simpler alternatives. Treat external review as a built-in step, not overhead.

**How to apply:**
- When finalizing a plan for something new and non-trivial, prepare it in a format easily pasted into another agent: clear sections (goal, summary, functions, data flow, self-healing, open questions), self-contained, no project-internal shorthand.
- When the user returns with Codex feedback, integrate each item one at a time: restate → ask Accept/Reject/Modify → update plan with a traceable marker like `> [Codex]`.
- Do not proceed to execution until the user explicitly says they are satisfied with the audited plan.
- This applies beyond the `prep` skill — any time the user plans something substantial, default to producing plan text in an audit-ready shape.
