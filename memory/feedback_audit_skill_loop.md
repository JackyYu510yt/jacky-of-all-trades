---
name: feedback_audit_skill_loop
description: Before executing a non-trivial plan or change, invoke the /audit skill (independent AUDITOR subagent) — replaces the retired Codex external-audit hand-off
type: feedback
originSessionId: e603725b-6687-40da-af59-af62bed45597
---
Before executing a non-trivial plan or change, invoke the `/audit` skill instead of routing the plan to Codex. `/audit` spawns an independent AUDITOR subagent — a fresh reviewer that re-derives risk from the actual files, not the context that proposed the change — and returns a go / revise / stop verdict.

**Why:** On 2026-06-08 the user retired the Codex external-audit habit in favor of the in-session `/audit` skill. Same goal — catch blind spots, missing self-healing paths, simpler alternatives, scope creep, destructive/irreversible actions — but no external paste or round-trip; the review is a built-in gate.

**How to apply:**

- When finalizing a non-trivial new script/project plan, OR before executing a multi-file / destructive / irreversible change, invoke `/audit` before acting.

- Treat the audit verdict as a gate: integrate findings, resolve any stop verdict, then execute. Don't proceed past a stop without resolving it.

- This supersedes the old Codex plan-audit hand-off. Trigger is the same (non-trivial plan/change); the reviewer is now the `/audit` subagent.

- Codex/Gemini/Copilot CLIs remain available as general delegation tools — only the *plan-audit* step moved to `/audit`. Relates to [[feedback_kiss_optimization]] (build enough, then strip) — the audit is where overbuild and scope creep get caught.
