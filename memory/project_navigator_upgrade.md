---
name: project-navigator-upgrade
description: 2026-08-24 Goal-Guardian gained the Navigator — every tick analyzes-then-recommends via a fresh subagent + DIGEST.md compact brief; blocker-review absorbed as its stuck-context intensity
metadata: 
  node_type: memory
  type: project
  originSessionId: 6780e265-126e-47e4-b381-47d217942786
  modified: 2026-08-24T16:37:34.431Z
---

2026-08-24: /auto's Goal-Guardian was upgraded with the **Navigator** (user-directed; plan `golden-gliding-lantern.md`; run `auto-runs/navigator-upgrade-091236/`).

What changed in `~/.claude/skills/auto/SKILL.md` (backup `SKILL.md.bak-pre-navigator-20260824-091236`):
- New tick step **4.6 NAVIGATOR** — EVERY guardian tick dispatches a fresh read-only subagent with GOAL.md + runbook + APPROACHES + PROGRESS + **DIGEST.md** + log tail; returns HAPPENED (disk-cited) / VERDICT / NEXT (one move) / DIGEST-DELTA.
- **4.6 executes nothing** — an approved NEXT-ACTION runs AS step 7 (substitutes for the next pending step); all gates/riders (success probe, FnReview, sweep, refuter, Round caps) unchanged. Booked to APPROACHES.md BEFORE execution; rejections consume no approach slots (compass carve-out); parked steps un-park only via step 8.
- **DIGEST.md** = per-run compact area (≤~25 lines, hard cap 40): significant findings / new implementations / errors / trajectory. CONTEXT, never EVIDENCE; blocker-review's packet stays digest-free.
- Blocker-review = the same Navigator shape carrying the stuck packet (name kept so cross-skill references in [[feedback-heavens-net]]-era docs, /prep, /spec, /repair still resolve).
- Degradation: uncited/dead Navigator → retry once → plain old ladder; guardian never depends on it.
- Surfacing: runbook `Navigator:` field + a Navigator line in every checkpoint report.

Process: user picked every-tick / execute+surface / compact-area via structured options; draft survived /audit round 1 (AUDITOR REVISE + RED-TEAM 4 BREAKS) → v2 → round-2 verifier (9/9 holes closed) → v3 one-liners → 15 edits applied; live smoke = the run's own tick 2 (DIGEST missing→skeleton path + first real Navigator dispatch, returned cited NEXT-ACTION).

Open leads: auto-log-hook did not append tool calls this session (model-discipline logging carried the run) — worth a separate /repair look; residuals N-2 (Navigator: line reaches blocker-review via runbook) and N-3 (rebuild list omits Navigator mirror) accepted in notes.md.
