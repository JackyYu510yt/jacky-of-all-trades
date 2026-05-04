---
name: feedback_kiss_optimization
description: User wants KISS-first optimization advice — never overengineer, but never leave obvious wins unmentioned either
type: feedback
originSessionId: e603725b-6687-40da-af59-af62bed45597
---
When proposing optimizations, prefer the smallest change that moves the biggest dial. Complexity must earn its place.

**Why:** User explicitly invoked `python-design-patterns` and emphasized KISS multiple times. They dislike class hierarchies, plugin systems, CLI frameworks, retry libraries, async/await, and external deps when stdlib or a 5-line loop does the job. They also dislike dense clever one-liners that sacrifice readability for microseconds.

**How to apply:**
- Prefer `for attempt in range(3)` over `tenacity`.
- Prefer one filter chain over multi-stage orchestration.
- Prefer `sys.argv[1]` over Click/Typer for scripts with ≤ 2 args.
- Prefer a dict lookup over a factory/registry.
- But DO still surface obvious wins (`-c copy`, `list → set`, missing retries on flaky subprocess) — KISS does not mean "leave performance on the table."
- When a tradeoff exists, name it explicitly and let the user pick. Don't hide complexity behind a confident silent choice.
