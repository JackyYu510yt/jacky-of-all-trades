---
name: scale-soak-verification
description: "Canonical Scale-Soak method in /auto — prove \"fixed in production\" via real-logic/stubbed-leaf harness ladder; riders in /repair /spec /prep"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 037b7014-3a8e-4834-bdf6-3d32b83f0778
  modified: 2026-08-24T17:40:38.125Z
---

2026-08-24 user directive: the scaled soak harness (`Testing\Jacky Rush\scale_soak.py`, from the
image-scale-soak run) "actually resolved a lot of issues" — bake its method into the skills so runs
know how to thoroughly figure out if something is ACTUALLY fixed in production. Second directive
same session: keep it FOUNDATIONAL and UNIVERSAL, not specific to that one instance.

**Why:** unit tests can't reach production-scale claims; live-prod verification is days-slow and
risky. The harness pattern (real decision logic, only the external leaf stubbed) verified fixes in
hours and killed a bad proposal before it shipped.

**How to apply:** canonical section lives in `~/.claude/skills/auto/SKILL.md` →
"Scale-Soak Verification". Core: 5 foundation principles (verify the claim where it lives;
instruments guilty until proven via negative control; reconcile independent tallies; calibrate the
simulator against a real measured slice inside a FROZEN gate before believing it; evidence carries
its scope + a live-confirmation debt) + 7 mechanical laws + the SMOKE→INJECT→SCALE→VALIDITY→
EXPERIMENT ladder (reference names them H1/H2/H3/S0/S1+). Riders cite it from /repair (principle 10
Step-2), /spec (Success-criteria scale-proof bar), /prep (Phase 9 — planned in Phase 6, built in
Phase 8, Phase 9 runs injections only). Survived 1 AUDITOR + 1 RED-TEAM round (2 blockers, 7 BREAKS
integrated: tripwire negative control, prod-untouched [CHK], frozen validity band, calibration
recency, DROP is terminal — no seed re-rolls, live contradiction outranks blind-spot soak PASS,
soak-substitute owes a named live follow-up). Related: [[heavens-net]] (INJECT rung consumes the
failure-class map), [[hard-source-consensus]], [[redteam-scenario-attack]],
[[discriminating-tests]].
