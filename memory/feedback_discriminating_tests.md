---
name: discriminating-tests
description: "Probes must distinguish rival hypotheses, not confirm the favorite — no premature convergence, no search-space neglect, no anchoring bias; conclusions require alternatives investigated or explicitly ruled out"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 264b04ae-82f9-4f21-8011-956d5a90ee60
  modified: 2026-08-11T22:37:37.912Z
---

Use **discriminating tests** rather than tests that merely confirm the current assumption. Do not prematurely converge on the current hypothesis: before concluding, systematically consider the relevant alternative hypotheses and identify what evidence or tests would distinguish between them. Avoid **search-space neglect** and **anchoring bias** by actively checking plausible alternatives. Do not declare the task complete simply because the initial hypothesis appears correct — the end state is a high-confidence conclusion supported by evidence, with the relevant alternatives investigated or explicitly ruled out.

**Why:** The user found (2026-08-11, via a ChatGPT-refined /auto prompt) that testing/debugging sessions were converging on the first plausible hypothesis and running confirming tests that a rival cause would also pass — so "verified" conclusions could still be wrong. Verbatim key phrases were deliberately kept.

**How to apply:** A probe only earns its run if its outcomes separate the leading hypothesis from its ranked rivals (a probe both would pass discriminates nothing). Before declaring DONE on any diagnosis or judgment call, list the plausible alternatives and either investigate or explicitly rule out each. Codified in /repair HI #18 + /auto HI #13 (cite qualified — heuristic #13 is a different rule) + /error-recon Anti-Guessing Rule 6. Related: [[pin-the-fix]], [[probe-dont-assume]], [[evidence-first-error-recon]].
