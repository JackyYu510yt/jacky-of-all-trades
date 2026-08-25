---
name: redteam-scenario-attack
description: "Dedicated RED-TEAM attacker subagent (10 hostile-scenario categories, HANDLED/DEGRADES/BREAKS/UNKNOWN verdicts) codified across /audit, /prep, /auto, /spec on 2026-08-13"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2bdc538f-dba4-4ca7-bd5a-24bc25ceb833
  modified: 2026-08-13T07:06:38.166Z
---

Reviews must not only check the plan as written — a dedicated RED-TEAM agent must invent hostile scenarios and walk each through the actual code/plan to an end-state verdict. Born from the user's yunwu-fallback question: "what about edge cases where the video is supposed to be finished by Claude but it runs out of usage?" — the AUDITOR never asked it.

**Why:** the AUDITOR (scope/assumptions/regressions) and the author share a blind spot: neither's success metric is *breaking* the design with concrete adversity. A brain with one job (attack) digs where a brain with six duties skims. User explicitly picked "Dedicated RED-TEAM agent" over an extra AUDITOR duty.

**How to apply:** canonical brief lives in `~/.claude/skills/audit/SKILL.md` under the heading "The brief handed to the RED-TEAM" (Phase 5.5) — /prep, /auto, /spec reference it by that heading string, never duplicate it. 10 categories: C1 mid-op death, C2 check-then-act race, C3 half-done re-entry, C4 flapping, C5 two actors, C6 boundaries, C7 time windows, C8 recovery-fails, C9 poison pill, C10 lying success. Verdicts: HANDLED (cite the line) / DEGRADES (name the cost) / BREAKS (name the end-state) / UNKNOWN (never guess). Wiring: /audit — dispatched in parallel with AUDITOR; any BREAKS caps verdict at NEEDS REVISION. /prep Phase 7 — parallel dispatch, `> [RED-TEAM]` callouts, works in autonomous mode too. /auto — RED-TEAM rider on the Terminal Refuter Gate; fires on the deliverable's NATURE (unattended/stateful) even when the refuter is skipped for a machine-checked goal; `RedTeam:` runbook field survives compaction; BREAKS = BLOCKER; shares the max-2-rounds bound. /spec — success criteria for unattended tools sweep the 10 categories; each load-bearing scenario becomes a RECOVERS-BY or ASSUME+PROBE line. Mandatory for unattended/long-running/stateful/concurrent changes; skippable for attended one-shots ONLY with an explicit `RED-TEAM: skipped` line. Related: [[audit-skill-loop]], [[audit-error-path-ordering]], [[discriminating-tests]].
