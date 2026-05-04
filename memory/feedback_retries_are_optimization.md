---
name: feedback_retries_are_optimization
description: Treat retries as first-class optimization work, not reliability-only — long-running jobs failing late is a huge waste
type: feedback
originSessionId: e603725b-6687-40da-af59-af62bed45597
---
Retries, backoff, and checkpointing are part of optimization, not a separate concern. Include them when reviewing or optimizing scripts.

**Why:** User corrected me when I listed "speculative retries" as a thing to avoid. Their reasoning: a 2-hour render that fails at 80% and restarts from zero is a massive compute cost — adding a bounded retry or a `-f segment` checkpoint recovers that. For long jobs, retries optimize *total wall-clock time and wasted work*, which is the real end goal.

**How to apply:**
- Recommend bounded retries with exponential backoff + jitter for subprocess, network, and disk I/O calls that have realistic transient failure modes.
- For long renders, recommend checkpointed output (ffmpeg `-f segment` + concat) so a retry resumes from the last segment.
- Retry on specific exceptions (`OSError`, `TimeoutError`, `CalledProcessError`), never bare `Exception`.
- Keep retry implementations simple — a 5-line `for` loop, not `tenacity`, unless >3 call sites all share the same policy.
- Do still warn against: retry decorators on operations that cannot meaningfully fail, bare `except Exception: retry` that hides real bugs.
