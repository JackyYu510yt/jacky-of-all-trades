---
name: heavens-net-class-recovery
description: "Heaven's Net" = user's trigger term for class-level failure recovery — recover by evidence-mapped failure class + required state, never symptom-specific "X happened → do Y" handlers; strictly evidence-only
metadata:
  type: feedback
---

"Heaven's Net" is the user's reusable vibe-coding term (adopted 2026-08-18, born
from web-automation work) for class-level error handling.

**Why:** Symptom-specific handlers ("error X → do Y") overfit to the first
observed error and multiply forever. The user wants recovery designed around
failure CLASSES and the state an operation requires — a wide net over the
plausible failure space. The user separately made the evidence rule STRICT
(2026-08-18): "false signals can completely ruin a system" — nothing may be
assumed, ever.

**How to apply:** When the user says "heaven's net", read the canonical
definition in `~/.claude/skills/error-recon/SKILL.md` ("Heaven's Net" section)
before designing recovery — never run it from memory. The shape: diagnose the
ACTUAL state → classify into a failure class (navigation / auth-session /
element / timing / network / resource / unknown) → recover by class toward the
required state → verify restored with evidence → bounded escalate, fail loud.
STRICT guardrails that never bend: a runtime class comes ONLY from a matched,
evidence-backed map entry — an unmatched signal is "unknown" (capture, park,
stop loud), never bucketed by resemblance; confidence tiers still gate which
entries run a chain; a job-level recovery budget (persisted to the checkpoint
file) bounds the whole item. KISS: taxonomy earned at the 3rd handler in the
same class, not before. Codified 2026-08-18 across /error-recon (canonical),
/auto (heuristic #14), /prep (Self-Healing Patterns + field 9), /spec (success
criteria), /repair (HI #16), + global CLAUDE.md trigger rule. Related:
[[structural-fix-vs-patch]], [[evidence-first-error-handling]],
[[kiss-first-optimization]].
