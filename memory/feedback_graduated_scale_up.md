---
name: feedback_graduated_scale_up
description: "Prove work on a little before committing to the whole — smoke (1) → batch (small) → full, each rung a verify gate; conditional on the task having volume"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e6363a73-2f90-4170-84ec-7d9e243c8ed7
---

Build a strong foundation by climbing in rungs: **smoke (1 item) → batch (small set) → full set**, where each rung is a verify gate and the next does not start until the prior rung's output is checked.

**Why:** a bad foundation gets paid for early and cheap (on item 1, in seconds) instead of at hour two of a full run. Verifying each level before stacking the next is what makes "done" hold.

**How to apply:**
- `/spec` writes the *requirement* — when a project has volume, its success criteria must be graduated and scale-proof (smoke/batch/full rungs), not "works once". Any executor that reads the spec inherits the ladder.
- `/auto` executes the *ramp* — a step that processes many items or is a long unattended run is split into smoke→batch→full rungs in the runbook.
- **Conditional, not always-on (KISS):** only fires when there's real volume (batch, many items, long unattended run). Skip for renames, config tweaks, one-shot single-item tasks — don't fabricate a `1 → 10 → all` ladder for a task that only ever runs once.
- Every rung uses REAL inputs (P1 test-at-scale) — a ramp on toy fixtures proves nothing.

Encoded directly in the `/auto` ("Graduated Scale-Up" section) and `/spec` (INIT success-criteria step) skill files on 2026-06-17. Relates to [[feedback_kiss_optimization]] and [[feedback_structural_fix_vs_patch]].
