---
name: feedback-plan-vocabulary-pyramid
description: Canonical plan vocabulary across all skills — MILESTONE (biggest) then PHASE then STEP; /auto writes a BOARD.md
metadata:
  type: feedback
---

The user's fixed vocabulary for breaking work into pieces, set 2026-08-27:
**MILESTONE ▸ PHASE ▸ STEP**. Milestone is the top of the chain because it is
the biggest; a phase lives inside a milestone, never the reverse. Canonical
definition lives in `/principles` → "Plan vocabulary"; `/auto`, `/spec`, and
`/supergoal` follow it.

**Why:** the user thinks of a milestone as the big waypoint and phases as the
chunks inside it. The skills previously ran the pyramid the other way
(PHASE ▸ MILESTONE ▸ STEP), so plans read backwards to them.

**How to apply:** never re-litigate the order. `/auto` groups every self-derived
runbook into 3–6 named phases under one milestone, each phase with its own
DONE-WHEN, and writes `./auto-runs/<slug>/BOARD.md` — a chronological board
reprinted in every report, where a phase goes green only with evidence on the
line. Watch the collision: `/auto` and `/prep` number their OWN procedure steps
"Phase 0 / Phase 8" — machinery, not the pyramid, never renamed. Legacy
`## Phases` SPEC.md files read with the two upper layers swapped in place.
Related: [[feedback-response-format]], [[feedback-confidence-risk-footer]].
