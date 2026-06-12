---
name: feedback_evidence_first_error_recon
description: Evidence-first failure handling — never guess what an error means; act only on seen/captured/proven failures. Embodied in the /error-recon skill.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: aa19c651-ff43-403d-8306-e8070574fbad
---

Never act on what an error *seems* to mean — act only on empirical evidence that distinguishes what it *actually* means. A misclassified error is worse than no handling. Codified in the `/error-recon` skill at `~/.claude/skills/error-recon/SKILL.md`.

**Why:** Real scar tissue. Soft blocks (3-min waits) were once treated as daily hard caps, killing capacity for the day. An account-setup tool's umbrella "FAILED/cooked" label made healthy accounts look dead; a transitional URL was read as a verdict; hidden HTML was trusted over the visible page; 498 ledger rows were really 192 accounts. Every misread was a verdict from a proxy instead of primary evidence.

**How to apply:**
- Success is verified only from the real **output** (file on disk that opens, session that performs a real action) — never from a screen, label, or log line. Screen = witness for diagnosing failure; hidden text/logs = corroborate only.
- Spot a state with OR (any alternate form); assign its *meaning* only when two independent signals agree (AND). Single-signal verdicts must be justified.
- Settled-vs-passthrough is a timing question (re-check must outlast the step's normal time); recoverable-vs-permanent is set by a duration probe.
- No umbrella labels (1:1 state→ID), denominators before population claims, the map is the only interpreter, verbatim messages only.
- Tools ship a flight recorder: unmapped errors get captured (msg + log + screenshot) to feed the next recon.
- Reference tools that already half-follow this: `gemini_worker` (Jacky Rush) and `ai_studio` under Desktop\Testing.

Related: [[feedback_structural_fix_vs_patch]], [[feedback_audit_skill_loop]], [[feedback_retries_are_optimization]].
