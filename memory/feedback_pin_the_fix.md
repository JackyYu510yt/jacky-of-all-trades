---
name: feedback_pin_the_fix
description: "Before patching, run one decisive check that isolates the variable — pin the fix, don't guess"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ac8b4d65-a235-4234-9083-69a26d714192
---

Before applying a fix, run ONE cheap, decisive check that isolates the single
variable in question — ideally with a binary outcome that localizes the cause.

Example the user loved: a working API request was failing after a change.
Instead of guessing, replay the *same working request* with only the
`x-goog-ext` headers stripped. If it goes empty → those headers are the missing
piece, patch exactly that. If it still generates → the gap is elsewhere. One
experiment, one variable, one conclusion.

**Why:** Guessing introduces random variables that "might mess us up down the
line." A decisive check removes them — you get a clear solution with no loose
ends, and the fix targets a *proven* cause instead of a hypothesis.

**How to apply:** When about to patch, first ask "what single experiment would
make the cause unambiguous?" Run that before editing. Change one variable at a
time. Phrase it as a binary: "if X → cause is A; if not → cause is elsewhere."
Pairs with [[feedback_evidence_first_error_recon]] (act only on proven
failures) — this is its forward-looking half: prove the cause before the fix.
The Findings Ledger's `suspected_verdict` is strongest when backed by one of
these decisive checks.
