---
name: Structural fix vs patch — the next-run-without-Claude test
description: A fix is structural only if the next run, on a different input, with no Claude in the loop, doesn't hit the same failure mode. Anything else is a patch.
type: feedback
originSessionId: 28253a76-4221-42b2-b184-e3b62434e2f4
---
The user's operational definition of "DONE" for any repair:

> *"If I run this tomorrow with no Claude babysitting, on a different input, does the same failure happen?"*
>   - YES → it was a patch. Not done. Climb a layer.
>   - NO  → structural fix. Done.

A **patch** neutralizes *this instance* of the failure (this run, this input, this account, this state). The condition that produced the failure is still there; the patch just intercepted it once.

A **structural fix** changes the system so the condition no longer exists. The system itself now contains the logic that previously lived in Claude's head. The script can run on cron for a month with no human watching, and the same failure mode does not recur.

**Examples (same bug, two outcomes):**

- Cookie expired mid-run. Patch: refresh the cookie this time. Structural: pre-call expiry probe + auto-refresh on stale, baked into every call site.
- Function returned None on empty list. Patch: add `if not items: return []` at the failing caller. Structural: validation at the function's entry; all callers covered.
- Stage 4 OOM'd at 47 GB. Patch: re-render with WHISK_THREADS=80 for that beat. Structural: cap threads dynamically based on input size, persisted in config.
- Test flaked under 3 workers. Patch: re-run. Structural: fix the race condition; deterministic pass at any N.

**Why:** The user runs long-horizon pipelines unattended. A patch ships a fix that depends on Claude (or a human) being present next time. The user's actual standard is: I authorize the run, I walk away, the script handles every recurrence of every known failure mode it has already seen.

**How to apply:** This is now baked into /repair as Hard Invariant #16 + Universal Principle 12. Step 3 (Lock the cause) requires a climb-one-layer test ("if I fix this exact line, does the condition that produced it still exist? — keep climbing until NO"). Step 8 (verify) requires a different-instance probe (different input/state/shard) — same failure mode must NOT fire there. When debugging or reviewing fixes outside /repair, apply the same test mentally: pretend the user has walked away and a different input arrives tomorrow. Does the fix hold? If not, the cause was locked at the trigger, not the structural layer.
