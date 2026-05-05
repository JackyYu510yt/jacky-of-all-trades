---
name: feedback_kiss_optimization
description: Complete the goal first, then strip — KISS is a final-pass filter on already-complete work, not a brake on building it in the first place
type: feedback
originSessionId: f5c7a80c-8f89-442c-b700-37f79c208fb5
---
**Complete the goal first, then strip.** Build what the stated goal needs — no more, no less. Don't add what isn't needed for the goal; don't skip what is. KISS is a final-pass filter on already-complete work, not a brake on building it in the first place.

**Why:** On 2026-05-05 the user flagged that the original KISS framing ("smallest change that moves the biggest dial") was biasing Claude toward underbuild. Concrete failure: parked a 3rd surgical /auto skill edit citing KISS when the 3rd edit actually covered /prep-specific ground the other two didn't. The lead phrase pulled toward "do less" when the right behavior was "do enough."

**How to apply:**

- Default action: cover the stated goal in full. Surface every relevant angle. If three small edits cover overlapping-but-not-identical ground, ship all three.

- Then prune: remove anything that doesn't trace back to the stated goal. That's where KISS lives.

- Anti-overengineering still applies on the "what to add" side: prefer `for attempt in range(3)` over `tenacity`. Prefer stdlib over external deps. Prefer dict lookups over factory/registry. Prefer 5-line loops over class hierarchies. Prefer `sys.argv[1]` over Click/Typer for scripts with ≤2 args. Avoid dense clever one-liners that sacrifice readability for microseconds.

- "Thoroughness" ≠ "overengineering." Reinforcing the same lesson in two contexts (e.g., a stalling-pattern entry AND a Hard NO) is thoroughness, not redundancy.

- DO still surface obvious wins (`-c copy`, `list → set`, missing retries on flaky subprocess) — KISS does not mean "leave performance on the table."

- When a tradeoff exists between minimal and complete, name it explicitly and let the user pick. Don't silently pick the smaller option.
