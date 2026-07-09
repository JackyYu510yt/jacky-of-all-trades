---
name: feedback_probe_dont_assume
description: "Probe, don't assume — get empirical evidence for every claim; smoke test or write a specialized test when no cheap probe exists"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ac8b4d65-a235-4234-9083-69a26d714192
---

Never act on what *seems* true — what an error means, whether a step worked,
whether a dependency / credential / file is in the expected state. Get the
evidence first. Run the cheapest probe that turns the assumption into an
observation (artifact check, exit code, a one-shot smoke test, a re-read of the
real file). When there is no cheap probe, **write a specialized check/test that
exercises the actual target condition and run it** — don't let the assumption
stand.

**Why:** A verdict from one happy outcome is a hypothesis, not proof; an
unprobed assumption is the root of most silent failures. This is the active,
generalized form of evidence-first: not just "don't trust a bad or absent
signal" but "go manufacture the signal rather than assume one."

**How to apply:** Codified as a critical rule in /auto (Hard Invariant #10) and
/spec ("Evidence discipline (all modes)" — success criteria must be empirically
checkable, not proxies). Pairs with [[feedback_pin_the_fix]] (isolate a single
variable with one decisive check) and [[feedback_evidence_first_error_recon]]
(the error-meaning half). Honors P1 test-at-scale — the specialized test must
hit the real condition, not a config flag standing in for it.
