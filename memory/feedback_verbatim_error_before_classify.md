---
name: feedback-verbatim-error-before-classify
description: "Always capture and read an error's exact text before classifying/grouping it; never treat errors as related just because they happened close together in time"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fdf8f712-5906-45f4-a7e4-ad29d52b26be
  modified: 2026-09-18T17:38:58.225Z
---

Never classify, group, or explain a failure before capturing its exact verbatim text (message, exception type, stack line, status code). Two errors must never be treated as the same class or root cause just because they occurred close together in time or in the same run/log block — proximity is not evidence of relatedness.

**Why:** User (2026-09-18): "ive ran into this issue so many times where errors that dont belong in the same class get grouped together, simply because the error happened within proximity and it was assumed related. instead, imagine if it was stated verbatim and we just read it, it would be a lot easier to classify and understand the exact response to our action." This generalizes rules that already existed narrowly inside `/error-recon` (Rule 5 "never paraphrase", "no umbrella labels", Rule 6 "no anchoring") — the gap was that those only applied inside a formal error-recon run, not to everyday debugging.

**How to apply:** Codified as [[principles P15 — state the error verbatim before classifying]] in `~/.claude/skills/principles/p15-state-the-error-verbatim.md`, indexed in `~/.claude/skills/principles/SKILL.md`, and cross-referenced into `~/.claude/skills/error-recon/SKILL.md` Rule 6 (added an explicit "proximity is not evidence" clause). Applies everywhere, not just inside `/error-recon` runs: any time a failure surfaces, quote it exactly before saying what it means or whether it's related to another one nearby.
