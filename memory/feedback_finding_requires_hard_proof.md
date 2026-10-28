---
name: feedback_finding_requires_hard_proof
description: "never label a claim FINDING/root-cause until a HARD, directly-read artifact confirms it -- inference from absence is a theory, not a finding"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 26ca3627-0418-4780-b1f6-50f2a9168d12
  modified: 2026-09-20T03:07:22.907Z
---

A claim only earns the label FINDING or "root cause" once it clears two bars: (1)
you personally read a piece of evidence, not inferred one from absence ("the log
doesn't mention it, so probably..."), and (2) that evidence is HARD -- a real
artifact (log line, timestamp, ledger entry), not a pattern-match to how things
usually go. Anything short of both bars gets labeled "leading theory,
unconfirmed" instead -- same content, but not written to disk as settled and not
acted on as proven.

**Why:** 2026-09-19, video-farm reaper investigation. A finding was filed and
later retracted: "the reaper deleted the file prematurely" was stated as root
cause, but it was an inference, not a read fact. The one artifact that would
have proven or disproven it (`scheduled_reaper_uploader.log` on Uploading PC1)
was never opened before the claim shipped. It only got caught because the user
pushed back -- the check wasn't structural. Once the log question was actually
asked, the theory flipped back to "delivery from farm to upload PC silently
failed" -- the opposite culprit.

This duplicates [[feedback_hard_source_consensus]] (2 signals, >=1 hard) and
[[feedback_heavens_net]] (STRICT evidence, no classifying by resemblance) --
those rules already exist and are correct. The gap is that both are wired into
specific skill flows (/error-recon, /auto's note-mode), so they went dormant in
this session because it was plain diagnostic chat, not a skill invocation.

**How to apply:** the moment a specific artifact is identified as "this would
settle it," that identification is a stop sign, not a preamble -- go read the
artifact before writing the conclusion, not after. In any root-cause diagnosis,
skill-driven or not, use "leading theory" language until a hard artifact is
actually in hand; never let "I know what would confirm this" get written as if
it already had been. See also [[feedback_pin_the_fix]] (isolate one variable
before patching) and [[feedback_verbatim_error_before_classify]].
