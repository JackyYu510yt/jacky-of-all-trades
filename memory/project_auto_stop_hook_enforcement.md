---
name: auto-stop-hook-enforcement
description: /auto runs are harness-enforced via auto-stop-block.py Stop hook; runbook Status DONE/STUCK is the only way to release
metadata: 
  node_type: memory
  type: project
  originSessionId: cb6ea408-6728-4f2b-9bf9-52451451dcbd
---

`/auto` autonomy is enforced by a Stop hook at `~/.claude/hooks/auto-stop-block.py`, wired into `~/.claude/settings.json`. The hook runs on every Stop event and:

- Reads the session marker `./auto-runs/.session-<session_id>` (contains this chat's slug), then resolves to `./auto-runs/<slug>/runbook.txt` (Patterns 1 & 2) or `./auto-runs/<slug>/RUNBOOK.md` (Pattern 3). All /auto artifacts now live under one per-run folder `./auto-runs/<slug>/` — see [[auto-runs-folder-layout]].
- No marker / no runbook → exits 0 (dormant; normal stop behavior).
- Runbook exists AND its Status line is not DONE/STUCK AND no `auto-runs/<slug>/VERDICT_DONE|VERDICT_STUCK` sibling → exits 2 with a stderr reason that forces the model to continue.
- Fails open on any unexpected error so a broken hook never traps the user.

**Why:** /auto-the-skill alone is prose — the model can ignore it and emit a stop turn anyway. The user kept hitting mid-run blockers despite Hard Invariant #1. /goal works because it's harness-enforced; a Stop hook gives /auto the same enforcement without requiring the user to type /goal every time.

**How to apply:**

- When the user invokes /auto, expect the hook to block any premature stop. The release path is: the model writes `Status: DONE` or `Status: STUCK` to the runbook (Patterns 1 & 2) or touches `auto-runs/<slug>/VERDICT_DONE|VERDICT_STUCK` (Pattern 3). This is already what the /auto skill mandates for terminal verdicts.
- Outside /auto runs (no session marker) the hook is dormant — no impact on normal sessions.
- User escape: `rm ./auto-runs/.session-<session_id>` (or delete the whole `./auto-runs/` folder), edit the Status line to STUCK, or hard-exit the session. The hook does not block process exit.
- The `/goal` slash command is the user-typed equivalent and remains available as a complementary tool — useful when the user wants harness enforcement without creating a runbook. Docs: https://code.claude.com/docs/en/goal
- Related: [[feedback_auto_no_phase_gates]], [[feedback_startup_gate_autonomous_engine]] — prose-level rules that the Stop hook now backs with real enforcement.
