---
name: see-it-before-you-call-it
description: "when a check's result is visible (page/window/image), read a screenshot before declaring pass/fail; exit-0 or log text is not proof on a visual surface"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5bfbbca1-864d-4b00-8958-2e95f407d519
---

When a smoke test / verify step decides pass/fail on something you can SEE (a browser, a GUI window, a rendered image), capture a screenshot built INTO the test at each state-change + assertion, and READ that screenshot before declaring pass or fail. A passing exit code or a matched log string is not proof on a visual surface.

**Why:** the account-95 incident — an autonomous run concluded "new-build accounts can't generate images" from the page's text reply, when the captured screenshot plainly showed the account was just signed out. The shot existed and was never read; the readiness check only looked for a prompt box, which a signed-out page also shows. Two holes: a present-but-unread screenshot, and a weak visible assertion. The missing sense was eyes.

**How to apply:** capture is in-script (not a slow after-the-fact shell grab); fire on state-changes + assertions, not every click; the test prints `[shot] <path>`, the model reads the must-read set (assertion + final + failure) and writes a per-shot verdict — a missing verdict fails the step. A missing/black/unread shot = INCONCLUSIVE → blocked, never a silent pass. Keep BOTH nets: tighten the text assertion AND read the shot.

Codified 2026-06-19 into /principles (Principle 10 "See it before you call it"), /auto (Hard Invariant #11 + "Smoke-test / verify capture" subsection under Visual Checkpoints), and /prep (Phase 8 build bullet + Phase 9 pentest row). Extends [[feedback_probe_dont_assume]] and [[feedback_evidence_first_error_recon]] — manufacture the empirical signal, and on a visual surface the signal is the eye.
