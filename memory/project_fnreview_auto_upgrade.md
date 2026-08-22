---
name: fnreview-auto-upgrade
description: 2026-08-22 — /auto gained FnReview (per-function completeness review); spec is function-review-SPEC.md v8 in the Skills folder; two lessons from the build (fix RUN ≠ fix MODE; stale-claim sweep)
metadata: 
  node_type: memory
  type: project
  originSessionId: ee50695d-1afd-4f48-ab4c-9d39197ba184
  modified: 2026-08-22T14:32:01.163Z
---

On 2026-08-22 /auto gained **FnReview** — an in-turn fresh-eyes reviewer dispatched when an AUTHOR function or any function-level fix passes its verify (5 principles + goal-trace + 4 "complete, not band-aid" items; bounded 2 rounds/step/guardian pass; content-hash stamps on the Functions block; open finding = DONE gate that forces the refuter even on machine-green goals). Canonical design: `C:\Users\Shadow\Desktop\Compiled Binaries\Skills\function-review-SPEC.md` (v8, approved after 1 AUDITOR + 1 RED-TEAM + 6 REFUTER rounds); wired into `~/.claude/skills/auto/SKILL.md` (backup `SKILL.md.bak-pre-fnreview-20260822-033619`). Runs: `auto-runs/function-review-spec-031538` (spec) + `auto-runs/fnreview-wire-041725` (wiring) in that folder.

**Why:** user wanted "guardian per function complete + reviewer that checks Heaven's principles and that it's a complete function or fix"; a cron is a clock not a trigger (one-cron rule), so it became an in-turn dispatch.

**How to apply:**
- Spread DECIDED 2026-08-22 (user: "lets add it to the other skills"): /prep Phase 8 AUDIT is executed by FnReview (+ fixed SAFE fns), /repair step 9 Audit is executed by FnReview with the fix packet (+ `FnReview (step 9):` line in the DONE report) — both pointer-shaped to /auto's canonical section; backups `prep/SKILL.md.bak-pre-fnreview-*`, `repair/SKILL.md.bak-pre-fnreview-*`. Still open: Option B (review every INLINE fn) on sweep evidence; single-reviewer rubber-stamp accepted as residual.
- Lesson 1 (keyed a BLOCKER): in /auto, **fix MODE** (entered only on a verify failure) ≠ a **fix RUN** (`/auto /repair`, "fix X" — NORMAL-mode steps). Any rule keyed to "fix" must say which; the spec uses a structural `fix-trigger` (fix mode OR rewrote a def that existed at run start).
- Lesson 2: when wiring a new rule into a long skill, a Scope satellite list says where to ADD the rule — also grep for the OLD claim it negates ("machine-checked → skipped", "verify pass → mark DONE"); four stale sentences survived until an AUDITOR diff caught them. Add a "stale-claim sweep" line to future spec Scope lists (the guardian spec had one).
- Not yet field-tested on a real build — first real /prep+/auto run should be watched for dispatch cost and the `VERIFIED (FnReview pending)` state behaving at resume.

Related: [[guardian-trigger-gap]], [[feedback-structural-fix-vs-patch]], [[feedback-heavens-net]].
