## Principle 8 — Goal-driven execution

**Rule:** For any non-trivial task, transform the imperative request ("do X") into a declarative goal with built-in verification ("X is done when <observable check> passes"). For multi-step tasks, pair every step with its verify check and run the loop until all checks clear. Strong, observable success criteria are what enable autonomous looping — without them, every fork becomes a question for the user.

**One-line form:** Don't loop on instructions. Loop on success criteria.

### When it applies

- Any non-trivial task — feature add, bug fix, refactor, migration, pipeline run.

- Especially multi-step work where the same loop will run several times before "done."

- Any `/auto` or `/loop` run — these are the canonical environments for autonomous looping.

- Any moment work is about to start with a goal stated as a verb but no observable check named.

- Trigger phrases: "add X", "fix Y", "refactor Z", "make it work", "implement W", "build a script that…", "/auto", "/loop", "keep going until", "set and forget", "until it's done", "make it pass", "get it green".

### What "transform" means

Take the imperative form and rewrite it as a goal + verification, before starting:

```
"Add validation"     →    "Inputs failing schema X get rejected with code 400.
                          test_invalid_inputs.py covers each case. Done when
                          test_invalid_inputs.py passes AND existing suite green."

"Fix the bug"        →    "test_repro.py currently demonstrates the bug
                          (failing). Done when test_repro.py passes AND no
                          other test regressed."

"Refactor X"         →    "Behavior unchanged: existing test suite was green
                          at SHA <A>; same suite is green at SHA <B> after
                          refactor. Done when both runs match."

"Make it faster"     →    "Benchmark P95 latency was Y ms. Done when post-
                          change benchmark shows ≤ Z ms AND no functional
                          test regressed."
```

The transformed form contains a check the work can run *itself* against. That's what enables the loop.

### The verify-loop pattern (multi-step tasks)

```
For tasks with N steps, write the plan as N pairs:

  1. <step>   → verify: <observable check>
  2. <step>   → verify: <observable check>
  3. <step>   → verify: <observable check>
  ...
  N. <step>   → verify: <observable check>

Then run the loop:

  for step in plan:
      do(step)
      if verify(step) fails:
          diagnose, fix, retry (bounded)
      else:
          continue

  if every check clears: DONE
  if any check refuses to clear after bounded retries: BLOCKED
```

The plan is the list. The loop is the execution. The user only intervenes when something genuinely refuses to clear (P3 example J — park and flag).

### Failure modes this catches

- **Imperative-only execution** — taking "add validation" at face value, writing code that *looks* like validation, declaring done with no test. The goal was never made checkable, so "done" is opinion, not observation.

- **Unverified step** — multi-step work where step 3 silently broke step 1, but no per-step check caught it. Discovered hours later, often in production.

- **Pause-and-ask drift** — autonomous run halts at every minor fork to ask the user, because the success criterion is too vague to act on alone. The criterion was the bug, not the model.

- **Synthetic verification** — adding a test that passes whether the change is correct or not. The "verify" step exists but proves nothing (P1 cousin — same root cause).

- **Verb-without-noun** — "make it work" / "fix it up" / "improve it" as the entire goal. Nothing to verify against; every fork becomes a guess.

### Gate before starting

Answer each in one sentence. If any answer is "I can't", restate the goal before starting.

1. **Have I rewritten the imperative as a declarative goal with an observable check?** "Add X" alone is not a goal; "X is done when test_X passes" is.

2. **For multi-step work, have I written the verify check for EACH step?** Not just the final step.

3. **Could the work run itself against these checks without me at the keyboard?** If no, the criteria are too weak — sharpen them before starting (this is what enables `/auto`).

4. **Does the verify check actually exercise the target?** (P1 crosscheck — a test that passes whether the change is right or wrong is not a verify check.)

### Common invalid patterns

- "Add input validation" → I add a Pydantic schema, no test → invalid (no observable check; "done" is just my opinion).

- "Fix the bug" → I edit code that looks plausible, no reproducer → invalid (the bug was never made observable; "fixed" can't be proven).

- "Refactor the auth layer" → I move code around, run no tests → invalid (refactor's whole guarantee is "behavior unchanged"; without a test pass before/after, that guarantee is unverified).

- Multi-step plan: 5 steps, only step 5 has a verify check → invalid (steps 1–4 can break each other silently).

- `/auto` run pauses at every step to ask "is this what you want?" → invalid (criteria were too weak; the model is asking because it can't verify alone).

### Hard NOs

- Do not start non-trivial work from an imperative without a checkable goal.

- Do not run multi-step work where intermediate steps have no verify check.

- Do not declare done on a "make it work"-style task without naming the test that proves it works.

- Do not accept a verify check that would pass whether the change is correct or not.

- Do not treat the user as the verify step. If the only way to know "done" is to ask the user, the criterion is too weak.

- Do not skip writing the verify check because "it's obvious." Obvious checks are the easiest to write; not writing them is laziness, not efficiency.

### Worked examples

**A — Bug fix, transformed**

User: "Fix the off-by-one in `paginate()`."

- ❌ Read the function, change `<` to `<=`, ship. No test of the bug, no test of the fix.

- ✅ Write `test_paginate_off_by_one.py` first. Run it — it fails (proves the bug). Now make the change. Run the test — it passes (proves the fix). Run the full suite — it passes (proves no regression). DONE means all three observations, not just the change being made.

**B — Multi-step plan, every step paired**

User: "Migrate the users table from int to UUID."

```
Plan:
  1. Add uuid column nullable        → verify: schema has uuid col, all NULL
  2. Backfill uuids                  → verify: 0 NULLs in uuid col
  3. Add unique index on uuid        → verify: index exists, no duplicates
  4. Update writers to set uuid      → verify: new rows have uuid set
  5. Update readers to use uuid      → verify: app test suite green
  6. Drop int id column              → verify: schema has no int id col
```

- ❌ Do all six steps, run tests at the end, hope for the best.

- ✅ Each step is its own gate. Step 3 can't start until step 2 verifies. Step 6 can't start until step 5 verifies. If step 4 fails, fix step 4 — don't drag the failure forward into 5 and 6.

**C — Autonomous run, criteria-driven**

User: "/auto build the rate-limit middleware described in the spec."

- ❌ Goal is "build the middleware." Halt at every micro-decision (which decorator style? which header for the limit? what's the default rate?) and ask.

- ✅ Goal becomes: "test_rate_limit.py passes AND existing suite green AND README rate-limit section updated." Now every fork has a tiebreaker: does this choice make the test pass without breaking others? If yes, take it. If genuinely no answer fits (P3 example J), park that step and continue elsewhere.

**D — Refactor with the strongest possible criterion**

User: "Refactor `process_order` — it's a god function."

- ❌ Split it up by feel. Run the test suite at the end, hope it's green.

- ✅ Run the test suite BEFORE — record the green. Now refactor. Run the suite AFTER — must match the BEFORE result exactly. The verify is "test set X was green at SHA A; same set X is green at SHA B." Anything else (a flaky test, a new failure) blocks the refactor from being declared done.

### When this principle does NOT apply

- Trivial one-liners — typo fixes, rename a variable, fix a comment. Writing a test for a typo fix is the wrong tradeoff; visual diff IS the verification.

- Exploratory / scratch work the user explicitly wants quick-and-dirty.

- Cases where the user explicitly says "just try it and see" — they're using me as a fast prototyping tool, not asking for production rigor.

The bar: when work is non-trivial AND the user expects it to actually work, transform-then-verify is on. When trivial or exploratory, judgment.

### Relationship to the other principles

- **P2** says: define success/testing/workflow conditions BEFORE starting. **P8** says: rewrite the imperative as one of those conditions and use it as the loop's exit criterion. P2 is the upfront definition; P8 is what you do with it during execution.

- **P4** says: audit current state vs goal at handback. **P8** says: audit *at every step*, not just at handback. P4 is the final gate; P8 is the per-step gate that makes the final gate honest.

- **P1** says: a test must actually exercise the target condition. **P8** says: every step needs a verify check. **P1 + P8 together:** every step needs a verify check that actually exercises the target. A weak P8 check is just P1's failure mode under a new name.

- **P3** says: every action traces to the goal. **P8** says: every step has its own verify against the goal, so traceability is built into execution, not a manual audit afterward.

- **`prep` skill** — Phase 8's Red → Green → Real → Audit cycle is P8 applied per-function during prototype build. Phase 9 is P8 applied at the integration/scale layer.

- **`test-driven-development` skill** — the runtime tool for the verify-first half of P8. This principle sets the standard; that skill is the procedure.

### Origin

Adopted 2026-04-30 from Andrej Karpathy's CLAUDE.md (forrestchang/andrej-karpathy-skills, principle #4 "Goal-Driven Execution"). Karpathy's framing: *"LLMs are exceptionally good at looping until they meet specific goals... Don't tell it what to do, give it success criteria and watch it go."*

Already partially covered by P2 (define conditions upfront) and P4 (audit at handback), but the *in-flight* pattern — transforming every imperative into a declarative goal and pairing every step of multi-step work with its own verify check — was not encoded as a hard checkpoint. P8 makes the transformation and the per-step verify mandatory, so autonomous loops have something concrete to loop *on*.


`========================================`
