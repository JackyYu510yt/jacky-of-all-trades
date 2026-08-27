---
name: measure-the-bottleneck-first
description: "Before auditing or fixing a subsystem, measure whether it is the actual constraint on the user's goal number — a week of correct fixes to the wrong layer is the failure mode"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9438c703-ffb0-43e7-907e-36d70f4b7724
  modified: 2026-08-27T02:41:10.870Z
---

Before spending a session auditing or fixing a subsystem, **measure whether that subsystem is what
is actually blocking the user's goal number.** Ask "what is the output today vs the target, and where
does it stop?" FIRST — from receipts on disk, not logs.

**Why:** 2026-08-26. The user said: *"the past week I've been working on this and I've thought it's
fixed, start up production, and we're nowhere near my goals."* A full image-lane audit ran, found real
defects, verified 3 fixes to 34 discriminating cases — and only at the very end, when the user asked
"how do you know with 100% certainty this is right", did a 2-minute measurement show the pipeline was
looping in the **voiceover** stage and had not reached the image stage at all in ~3 hours. The audit
was correct and the fixes were correct; they were not the constraint. The spec that scoped the audit
never asked whether the image lane was the bottleneck either.

**How to apply:**
- Open with the goal number vs the actual, from the artifact layer (files on disk with mtimes, ledger
  receipts), never from a log line or a health file — those are exactly what go stale.
- Then find the FIRST stage that isn't advancing. Fix there.
- Per-hour beats per-day: an aggregate hides a 92,208-attempt hour next to twenty idle ones.
- Say plainly when a verified fix is **not** proven to move the goal number. "Correct" and
  "the thing that was blocking you" are different claims and must be reported separately
  (this is [[feedback-completed-means-delivered]] / P12 applied to diagnosis, not just delivery).

Related: [[feedback-pin-the-fix]], [[feedback-discriminating-tests]], [[feedback-evidence-first-error-recon]]
