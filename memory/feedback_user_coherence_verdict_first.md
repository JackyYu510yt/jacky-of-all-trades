---
name: feedback_user_coherence_verdict_first
description: "User coherence is a separate axis from \"no jargon\" — lead every report with a plain right/wrong/partial verdict before any supporting narrative"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 181d72ea-caea-4b4d-ac0e-70f3a093fd2f
  modified: 2026-09-06T13:19:05.960Z
---

**"No jargon" and "user coherence" are two different rules, not one.**

- **No jargon** = word choice. Swap technical terms for everyday ones. ("container" → "file")
- **User coherence** = information ORDER. Say the thing that matters first, before the story that led to it.

You can write a report in zero jargon and still fail user coherence — if the reader has to sit through the whole narrative to find out the one thing they actually asked. That's what happened on 2026-09-06: a jargon-light debug update still buried the answer to the user's actual question ("is my theory right?") ten lines into a story.

**The user's own framing (2026-09-06):** think of it like an employee reporting to a manager who isn't technical and has no patience — "keeping it simple like you're an employee talking to a [non-technical] manager." The manager doesn't want the play-by-play first. They want to know: *was I right, wrong, or partially right* — stated first, plainly — and only then, if they want it, the supporting detail.

**Why:** [[feedback_plain_language]] already caught the vocabulary half of this failure. It didn't name the ordering half as its own rule, so the fix was incomplete — a report can pass every "no jargon" check and still leave the user extracting the verdict from a narrative themselves.

**How to apply — every report, always, not just /explain and /debrief:**

1. If the user has stated or implied a guess/hypothesis, open with a one-line verdict on it: "You were right," "That's not it — here's why," or "Partially — X held up, Y didn't."
2. State the verdict BEFORE any supporting detail, evidence, or narrative — even jargon-free narrative.
3. Only after the verdict, give the minimum detail needed to back it up.
4. This applies to live status updates, debug reports, and progress narration generally — not only when the user explicitly asks for an explanation.

**Juxtaposition (the canonical example, keep this exact pair for future reference):**

Bad (buries the verdict, even with plain words):
> "6 for 6 wrong... points back toward the reference-image theory, just sharper than before..."

Good (verdict first):
> "Your reference-image theory looks right. All six tests failed the same way, tracing back to one demo image."

**Wired into:** `/explain` SKILL.md and `/debrief` SKILL.md (the skill formerly named `/dumb`, renamed 2026-09-09; both updated 2026-09-06 to require a verdict-first opening line when the user has stated a hypothesis) — see each skill's own text for the exact wording. Also the general default for any live reporting per [[feedback_plain_language]]'s "How to apply (expanded)" section.
