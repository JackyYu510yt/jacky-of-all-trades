---
name: feedback_audit_error_path_ordering
description: "Audit the recovery/error path as a path with its own ordering & state — not just the happy path's mental model"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 30783ab6-d785-4b9f-bbca-e65c7bd55b33
---

When reviewing a skill, script, or design, the user (and Claude) tend to audit the *successful* path's mental model and skip the *failure* path — yet most problems happen exactly when errors occur. The sharp form: recovery paths (retry, approach-rotation, resume, rollback, re-open-after-review) are **re-entries over partial state**, and their *ordering* (undo partial effects → re-assert the precondition → invalidate downstream consumers) goes unchecked even when the happy-path order was carefully verified.

**Why:** the happy path only moves forward through clean states; a recovery path moves *backward into* a step that already ran, where leftover state/order gets silently thrown away. A field can be defined in a schema and invoked at no recovery door (the orphaned `/auto` `rollback:` field), and a happy-path audit will never catch it.

**How to apply:** for any non-trivial review, enumerate each error/recovery path explicitly and trace it as a path with its own steps. Ask at every re-entry point: does it restore the precondition before retrying, undo the prior attempt's residue, and invalidate downstream work that consumed now-stale output? Watch for *assumed* recovery doors that don't actually exist in the code (the proposed `/auto` "park re-entry" door — caught by independent /audit). Codified in `/auto`'s "Re-entry hygiene" subsection + Hard Invariant #12, and in `/spec` as the unattended/self-healing success-criteria dimension + the per-phase `RECOVERS-BY` field (failure mode + ordered recovery: roll back → re-assert precondition → invalidate downstream → resume). /spec is the planning-time twin: design the error path at the bar so any executor inherits it (2026-06-30).

Related: [[feedback_evidence_first_error_recon]], [[feedback_structural_fix_vs_patch]], [[feedback_pin_the_fix]], [[feedback_audit_skill_loop]].
