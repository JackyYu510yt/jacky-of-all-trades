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
criteria), /repair (HI #16), + global CLAUDE.md trigger rule.

**Proportion guardrail (added 2026-08-23, from two live incidents):** confirming
the signal is half the rule; the other half is REACT IN PROPORTION. Under-sized
(90 s rest for a ~24-min-median throttle → account hammered 37×) and over-sized
(rest-till-midnight on a string that can mean a 60 s limit → healthy accounts
benched) are equal violations. Size from an OBSERVED recovery measurement (block
actually lifted, n recorded; a probe that hit its 15-min ceiling is a lower
bound, not a measurement); unmeasured → smallest-first ≥×2 ladder, verify,
escalate bounded; scope matches evidence (per-member vs pool-wide `Scope:`
field); applies only to responses that rest/retire capacity or pull a pool —
growing backoff IS the ladder. Codified: error-recon Heaven's Net guardrail +
`Scope:` template field + Phase 3 chain rule; /auto heuristic #14, sweep +
FnReview item `1b` (own ledger key), HI #14 (under-size = band-aid), refuter
brief; pointers in /prep (Self-Healing Patterns), /spec (success criteria),
/repair (HI #16). Also 8/23/26: multi-match rule (two entries, same class +
chain-eligible → smallest-first ladder IS the discriminating test; else C7),
and Phase 1b ceiling rule (15-min probe = default ceiling = lower bound, not a
cap verdict; 30/60 rungs only if budget-approved).

**Three broad companions (added 2026-08-23, user wants DOMAIN-AGNOSTIC recovery
principles, not pipeline-specific rules):** HOLD — restored means it holds;
hold-window = max(measured recovery, rung used, 15-min floor); a re-fire on the
same (entry, target) inside it is a RECURRENCE = failed recovery (continue the
chain, counters persist, never reset on a verify-pass that didn't hold — the
37×-in-3h incident was 37 "successes"); exit a degraded state on more evidence
than entering; staggered pool re-entry. CHEAPEST-FIRST — a lighter
discriminating probe runs before the consuming action, may only FAIL the gate;
the first consuming success is the verdict (two-signal rule kept). GIVEN
NUMBERS — environment-supplied magnitudes (retry-after, quota, ETA, reset
boundary) are the FIRST rung, never overridden by a constant; guards for ≤0 /
absent / hostile values; reset boundaries observed, never assumed from a clock.
Codified: error-recon step 4 + new Hold guardrail + Proportion rule (1) + job
budget; /auto sweep + FnReview sub-keys 1c/1d/1e (own ledger keys), heuristic
#14, refuter brief; /prep one sentence; /spec success criterion "recovery
HOLDS". Every batch went draft → independent refuter → fix → show → apply. Related:
[[structural-fix-vs-patch]], [[evidence-first-error-handling]],
[[kiss-first-optimization]].
