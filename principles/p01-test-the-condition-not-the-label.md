## Principle 1 — Test the condition, not the label

**Rule:** The test must place the system in the exact condition being verified. Setting a value is not the same as exercising it.

**One-line form:** If the question is "does N work?", fire N. Config-load ≠ load test.

### When it applies

- Any test written or run to answer "does X work?" for a specific value, condition, scale, concurrency, or failure mode.

- After any change that introduces a new constant, threshold, or config value the user asked to be verified.

- Trigger phrases: "test at N", "verify concurrency", "does this work with X", "stress test", "prove it handles Y", "pentest this", "try M threads".

### Failure modes this catches

- **Label vs behavior** — `THREADS = 80` proves the assignment works, not that 80 concurrent threads work.

- **Happy path vs target path** — a 1-item queue never reaches the N-item logic even when N=80 is configured.

- **Convenient proxy vs actual spec** — the test spec comes from the user's question, not from what's easiest to run.

### Three-check gate before declaring "tested"

Answer each in one sentence. If any answer is no, the test did NOT exercise the target — say so.

1. **Did the test actually reach the condition?** If X = "80 concurrent submissions", did 80 requests fire at the same moment? If X = "10 hour wait", did it actually wait 10 hours?

2. **Would the test have failed if the target value were wrong?** A test that passes whether the value is 8, 80, or 8000 isn't testing the value — it's testing that the code path doesn't crash.

3. **Does the test check the specific failure signature the target would produce?** If the API throws `LIMIT_403` when over capacity, did the test grep for it? Or did it just check "no exception"?

### Common invalid patterns

- `MAX_CONCURRENT = 100`, test sends 1 request → invalid

- "Does it retry on error?" test with no induced failure → invalid

- "Does it handle empty input?" test with a small non-empty list → invalid

- "Is it thread-safe?" test with sequential calls → invalid

- "Does this survive N hours?" test that runs for N minutes → invalid (unless the gap is stated explicitly)

- "Does it handle 1000 users?" load test with 10 users → invalid

### When you can't run at full scale

Real cost, destructive side effects, or external dependencies can make the true-scale test impossible. That's okay. What's NOT okay is silently downscaling.

Required:

1. **Say so explicitly** — "I cannot run the true N=1000 test because each request costs $5 / would take 6 hours / would trip the rate limit."

2. **Propose the closest realistic approximation** — "I'll run N=10 against the live system; the failure mode would be the same N thing."

3. **Report the gap in the verdict** — "Tested at M, not the requested N, because [reason]. Extrapolated verdict: …"

### Hard NOs

- Do not report "worked" when the test didn't reach the target condition.

- Do not accept "it ran without error" as proof of the target value.

- Do not substitute a convenient proxy for the user's actual question.

- Do not silently downscale — always name the gap.

- Do not re-use a smoke-test result as load-test evidence.


`========================================`
