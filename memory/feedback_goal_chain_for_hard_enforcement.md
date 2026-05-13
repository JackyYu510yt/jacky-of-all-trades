---
name: goal-chain-for-hard-enforcement
description: /auto alone is prose discipline; chain with /goal for harness-enforced autonomy on non-trivial runs
metadata: 
  node_type: memory
  type: feedback
  originSessionId: cb6ea408-6728-4f2b-9bf9-52451451dcbd
---

For non-trivial unattended runs, recommend invoking `/goal <observable condition>` together with `/auto <task>` — either order. /goal installs a session-scoped Stop hook; Haiku evaluates the condition after every turn and forces another turn until "yes". /auto contributes runbook, approach rotation, log, fix mode.

**Why:** The user kept hitting mid-run blockers under `/auto` alone. The root cause is structural, not a missing invariant: /auto is just prose in `SKILL.md` — text the model reads. There is no harness enforcement. The model can emit a stop turn whenever it judges the work done. /goal is a real Stop hook with a separate evaluator. See [[feedback_auto_no_phase_gates]] and [[feedback_startup_gate_autonomous_engine]] — those rules are necessary but not sufficient on their own.

**How to apply:**

- If the user invokes `/auto <task>` for anything non-trivial (>3 steps, long-running, unattended, build pipeline), suggest chaining `/goal <condition>` in the same turn — or do it for them if the success condition is already explicit in the invocation.
- The /goal condition must be observable from transcript alone — exit code, test pass, file existence + size, metric threshold. "Looks fixed" fails. Same bar as Phase 0's success-condition rule.
- /goal Phase 0 source priority is now 0 in `/auto`'s scan list (above `./auto-*/GOAL.md`). If /goal is active, treat its condition as frozen and skip the activation gate.
- /goal requires trust dialog accepted and hooks enabled (`disableAllHooks` off, `allowManagedHooksOnly` off). If unavailable, /auto falls back to prose discipline and should surface that.
- Docs: https://code.claude.com/docs/en/goal
