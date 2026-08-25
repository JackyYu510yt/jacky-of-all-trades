---
name: guardian-trigger-gap
description: "/auto pasted mid-message doesn't load the skill — global CLAUDE.md rule now forces Skill(auto); first field run gemini-fallback-live-023001"
metadata: 
  node_type: memory
  type: project
  originSessionId: d677690e-3805-4a13-b34a-5f52fd9c1443
  modified: 2026-08-16T09:34:18.606Z
---

2026-08-16: First real-world Goal-Guardian field test (Jacky Rush session,
run `gemini-fallback-live-023001`) exposed a trigger gap: `/auto` embedded in
PASTED text is not parsed as a slash command, so the harness never injects
SKILL.md — Claude improvises pre-guardian behavior from stale memory (no
contract, no cron). Decisive evidence: it ran `Skill(auto)` only after the
user's manual nudge, proving the skill wasn't loaded at invocation.

**Fix (structural):** created `~/.claude/CLAUDE.md` (user-level, all
projects) mandating `Skill(auto)` invocation whenever /auto or its trigger
phrases appear anywhere in a message without the skill loaded this turn.

Once loaded, the guardian behaved to spec: contract pinned, one 15-min cron
(46cf98b4), RedTeam pending, checkpoint status, session-only honesty note.
Pre-registered field-test predictions live in
`Skills/guardian-field-test-predictions.md` (P1-P9; P1/P2 already confirmed;
P0 trigger-gap logged as the first finding). Related: [[feedback_structural_fix_vs_patch]].
