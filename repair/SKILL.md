---
name: repair
description: Universal repair methodology. The user invokes /repair (or says "fix this", "debug this", "it's broken", "something's wrong", "I'm getting an error", "why is X failing", "this crashed") to engage a disciplined fix process for any failure — a failing test, a UI bug, a slow query, a crashed pipeline, a regression after a refactor, a function returning the wrong value, a flaky deploy, a misbehaving API client, or any random complicated issue. Repair is a methodology, not a workflow per system. It defines HOW to fix things reliably regardless of WHAT'S broken. Never guess-and-edit. Never ship a fix without verification under real conditions.
---

# Repair

Universal repair methodology. The user invokes `/repair` to hand Claude a failure; Claude works the failure through a disciplined sequence — gather evidence, prove the cause, isolate it, fix it in isolation, integrate the fix, verify under real conditions, report.

Repair is a **methodology**, not a workflow per system. It defines HOW to fix things reliably regardless of WHAT'S broken. The discipline is the same whether the failure is in a unit test, a CSS layout, a slow database query, an overnight pipeline, a deploy that flakes, or a function quietly returning the wrong value.

This skill modulates how Claude debugs and fixes any work — it does not constrain what kind of work the failure lives in.


## When to Use This Skill

- User says "it's broken", "not working", "crashed", "getting an error", "debug this", "fix Y", "why is Z failing", "this is throwing", "this regressed", "this used to work", "something's off"

- A test is failing, a build is red, a deploy is flaking, a query is slow, a UI is rendering wrong, an API client is returning unexpected shape, a function is returning the wrong value, a script is dying on input it shouldn't die on

- After a failed pipeline run, a failed CI job, a failed scheduled task — any reproducible bad outcome

- Any time a fix is being proposed without isolation + verification — stop and run `/repair` instead

If the failure is reproducible, /repair applies. If it's a one-time event with no way to reproduce and no symptom you can recheck, this skill won't help — gather more occurrences first.


## Hard Invariants

These never bend, regardless of what's being repaired or how urgent it feels.

1. **Evidence before theory.** Read what's actually broken — log line, error, test output, browser console, network trace, observed behavior — before forming any hypothesis. Theorizing without evidence is guessing dressed up as analysis.

2. **Multiple falsifiable hypotheses, not one favorite.** Propose 2–4 concrete causes, each with a check that could rule it out. Picking one cause and chasing it is how repairs miss the actual bug.

3. **Push back on weak diagnoses.** If the user's stated cause is contradicted by evidence, or a simpler cause better fits the observed failure, surface it before fixing. "I think it's the cookie" gets a "noted, but the evidence says X — recommend probing X first." Don't silently implement a fix the evidence doesn't support, and don't silently substitute a different fix without saying so (P6 + P7).

4. **Conclusive / verifiable / replicable.** A cause is "locked in" only when the evidence answers all three: it proves the cause beyond reasonable doubt, someone else running the same check sees the same result, and the failure happens on demand — not "sometimes."

5. **Process of elimination is not proof.** Ruling out three of four hypotheses doesn't prove the fourth. The remaining cause needs *positive* evidence — a probe that directly demonstrates it.

6. **Isolate before you fix.** Never edit the real codebase first. Reproduce the failure in the smallest standalone context that still fails the same way. The standalone is the proof contract — a fix is real only when the standalone is green.

7. **Real inputs, narrow scope.** When isolating, don't shrink the inputs to make the test "cleaner" — that hides data-dependent bugs. Shrink the scope around the inputs (call only the failing function/component, not the system around it). The 47 GB video that triggered the bug is the file the standalone must use.

8. **Same failure signature.** The standalone must fail with the same error, the same line/symptom, the same way the real system fails. A different failure means you isolated the wrong thing — something got stripped that mattered.

9. **Fix in isolation, then integrate.** Try repairs on the standalone only. Apply to the real codebase only after the standalone is green. Edit the minimum needed in the real code; don't rewrite surrounding logic.

10. **Two verifications, not one.** PoC verification (one clean pass of the standalone) proves the fix concept works. That alone is *not* shippable. Step 2 — actual-usecase verification — runs the fix the way it'll actually run in real conditions (the concurrency, scale, hostile inputs, slow networks, race conditions the real failure faced). PoC-only is never declared a pass.

11. **Match the test to the failure mode.** "Actual usecase" means whatever shape the real failure took. If the bug only appears under three concurrent requests, single-request testing doesn't prove it's fixed. If it only appears on the 47 GB video, the 12-second test clip doesn't prove it.

12. **One fix, one scope.** Don't refactor while repairing. Don't add unrelated improvements. Don't "while I'm here" the surrounding code. The fix's blast radius matches the bug's blast radius.

13. **Never silence the failure.** `try/except: pass`, swallowed errors, blanket retry-until-green, log filters that hide the symptom — those are not fixes. They hide the bug, which means the bug ships.

14. **No guessing.** If evidence is inconclusive, gather more. If you can't gather more, surface that to the user honestly — don't fill the gap with intuition.

15. **Atomic phases.** Each phase fully succeeds before the next begins. No "we'll figure that out later." If a phase fails, loop back to the previous phase — do not advance.


## The Repair Loop in P8 Form

Every repair is an instance of P8 (goal-driven execution): transform the imperative ("fix the bug") into a declarative goal with an observable check, then loop until the check clears.

Repair's transform — always the same shape:

```
"Fix the bug"   →   "test_repro.py currently FAILS (proves the bug
                     exists in the real codebase).
                     Standalone-pass when test_repro.py PASSES on the
                     fix.
                     Step 2-pass when the same fix holds under the
                     real production-shape conditions the bug faced.
                     DONE = standalone-pass AND step-2-pass AND no
                     existing tests regressed."
```

The repair loop is then:

```
 1. Transform        → declarative goal stated above
 2. Hypothesize      → 2-4 falsifiable causes, each with a check
 3. Lock the cause   → positive evidence for one survivor
 4. Isolate          → standalone with real inputs, same signature
 5. RED              → standalone fails 3x with same signature
 6. GREEN (PoC)      → standalone passes after fix
 7. Integrate        → minimum edit to real codebase
 8. Step 2           → fix holds under real conditions
 9. Audit            → DONE / PARTIAL / STUCK verdict
```

Every step is gated. If a step fails, loop back to the previous one — do not advance. The user only intervenes when a step refuses to clear after bounded effort (STUCK) or when a Hard Invariant trips.

This is what makes repair runnable under `/auto`: the goal is checkable and every step has its own verify. The model can run the loop without pausing for guidance unless something genuinely blocks.


## Universal Principles

These principles apply to any repair, in any execution shape, on any system. Each one prevents a specific, repeatable failure mode in the *act of repairing*.

### 1. State the failure in one sentence before working it

If you can't compress what's broken into a single sentence, you don't understand the failure well enough to repair it. "Stage 4 is failing" is not enough. "Stage 4 image generation returns no_images_generated for ~12% of beats when WHISK_THREADS exceeds 80" — that's a failure statement.

### 2. Define success before doing the work

Per `principles` skill P2: success must be observable. "It works again" is vibes. "The standalone runs three times in a row with exit 0, and the real test suite passes the previously-failing test in CI under the same load conditions" — that's a success condition.

### 3. Read what's broken before theorizing

Logs, error messages, stack traces, screenshots, network panel, browser console, query plan, test output — whatever artifact the failure produces, read it first. The discipline is identical whether the artifact is a Python traceback or a CSS DevTools box-model overlay.

Examples across domains:

- Failing test → read the test output, the assertion error, the lines of the test, the lines of the code under test.
- UI bug → read the rendered DOM, computed CSS, browser console, network panel screenshot.
- Slow query → read the query plan (`EXPLAIN ANALYZE`), the indexes that exist, the row counts.
- Crashed pipeline → read the last 500 lines of stdout/stderr, the stage's checkpoint files.
- Flaky deploy → read the deploy log, the health-check output, the previous deploy's diff.
- Wrong-value function → read the inputs, the outputs, and the intermediate values via probe.

### 4. Propose 2–4 concrete, falsifiable hypotheses

Use the `explain` skill's tiered-options format. Each hypothesis names a specific cause and a check that would confirm or rule it out:

- *Option A — Cookie expiry.* Evidence: `_strict_accounts` reports cooldown active. Check: print the cookie expiry timestamp from the session cache and compare to wall-clock.
- *Option B — Quota exhaustion.* Evidence: prompt-counts log shows account hit 300 in last 3h. Check: query `prompt_counts.json` for the account name with the failing prompts.
- *Option C — Network jitter.* Evidence: failures cluster in 30-second bursts. Check: time-series the failures and compare to a `ping -t` log.

Rank by likelihood given the evidence so far. Never lock in a single hypothesis without checking the others.

### 5. Lock the cause with positive evidence

Run the cheapest check first. Each check confirms or rules out one hypothesis. Stop when:

- Exactly one hypothesis remains AND
- That one hypothesis has at least one piece of evidence that *directly proves it* (not just "everything else is ruled out").

If the surviving hypothesis has no positive proof, the cause is not locked. Loop back, add candidates, run more checks. Process-of-elimination alone has shipped more wrong fixes than any other shortcut.

### 6. Isolate the failure in the smallest context that still fails

The standalone reproduces the bug *outside* the real system, using the *same* inputs, the *same* failure-triggering conditions.

- A failing test? The standalone is just that test, run in a minimal harness.
- A UI bug? A tiny HTML page with the same component, the same CSS, the same data shape.
- A slow query? The exact query against the same database, the same row count, the same indexes.
- A pipeline stage? Just that stage, called with the actual files the parent stage emitted.
- A wrong-value function? A 10-line script that calls the function with the input that produced the wrong output.

The narrowing is *scope*, not *inputs*. Real inputs go through a thin shell around the failing call. If the bug only shows up with the real 47 GB video, use the real 47 GB video. Don't trim it. Don't synthesize a "similar" file. The whole point is to prove we can reproduce *this specific failure*.

### 7. Confirm the repro before trying any fix

Run the standalone three times against the real inputs. It must fail every run, with the same signature as the real system. If:

- It doesn't fail → the diagnosis is wrong, or the standalone is missing context.
- It fails differently → the narrowing stripped something important.
- It fails sometimes → the bug is intermittent; that itself is a clue worth investigating before moving on.

Don't accept a 2-out-of-3 repro as good enough. Intermittency hides bugs.

### 8. Fix in isolation, prove the concept

Now — and only now — try fixes. KISS applies: simplest approach first. Apply only to the standalone. Run it. If it passes once cleanly, that's the PoC.

Default: one clean pass. Expand only with a *named reason*:

- **Stability check** — fix stability is the known concern → 3 passes in a row.
- **Multiple code paths** — fix touches >1 path → one PoC per path.
- **Known-fragile axis** — boundary conditions matter → one PoC at the boundary, one at the normal case.
- **Intermittent bug** — flake was the original symptom → 10+ passes to confirm the flake is gone.

If none of the proposed fixes work, the diagnosis is wrong. Loop back to hypothesis-listing.

### 9. Integrate with minimum scope

Apply the same fix pattern to the real codebase. Same logic, same shape. Edit the minimum lines required. No surrounding cleanup, no "while I'm here" improvements, no new abstractions. The bug had a blast radius; the fix matches it.

### 10. Verify under real conditions (Step 2)

Before running anything, answer in one sentence: *"How will this actually run in production?"*

That sentence IS the Step 2 test spec. Simulate exactly that — the composition, the concurrency, the scale, the hostile-input mix the real failure faced.

Examples:

- Failing test in CI → run the full test suite in CI conditions, not just the previously-failing test locally.
- UI bug under specific browser → run on that browser, that version, that resolution.
- Slow query under load → run with realistic concurrent connections, not just one query in isolation.
- Pipeline stage that died at 47 GB → re-run the stage with the 47 GB file, not a 200 MB sample.
- Concurrency bug with 3 workers → launch 3 concurrent workers, not one.
- Bug that hits at scale → run at scale.

A fix is not shippable while Step 2 is red, regardless of Step 1.

### 11. Report honestly

The final report names the cause, the evidence that proved it, the exact fix applied, and the verification results — both PoC and actual-usecase. If anything regressed during integration, the report says so. Half-fixes get labeled PARTIAL, not DONE.


## Execution Shapes

The methodology is universal. The amount of ceremony scales with the scope of what's broken. Pick one based on the failure's complexity.

### Quick — clear cause + obvious fix

For a failure where the cause is genuinely obvious from the first read of the evidence: a typo, an off-by-one, a missing import, a wrong variable name. The cause is named, the fix is one line, and "could it be something else?" honestly returns no.

- Read the evidence.
- Name the cause and the fix in one sentence each.
- Verify with the smallest test that proves the fix (often a quick re-run of the failing case).
- Report.

Skip the standalone-repro phase ONLY when the fix is verifiably one line and verification is single-step. The first time you find yourself thinking "let me just try this" — you're past Quick. Drop to Standard.

### Standard — most bugs

For any repair where the cause is not immediately obvious or the fix touches more than one place: the full discipline applies.

- All 15 hard invariants.
- All 11 universal principles.
- Standalone repro required.
- PoC + actual-usecase verification both required.

Standard is the default. When in doubt, use Standard.

### Multi-Stage — failure spans systems / pipelines / multi-stage flows

For failures that span multiple stages, processes, or systems — the original "pipeline" framing belongs here. The methodology is the same, with one extension:

- **Stage isolation in addition to scope isolation.** When the failure is in stage 5 of a 9-stage flow, the standalone calls only stage 5 with the *real intermediate output* that stage 4 produced (read from disk, from a checkpoint, or from a captured trace). This keeps the repro fast even when the upstream pipeline is slow.
- **Real intermediate inputs.** Same rule as Real Inputs — don't synthesize stage-4-shaped data; use what stage 4 actually wrote.
- **Cross-stage hypotheses are valid.** "Stage 5 fails because stage 4 emits malformed checkpoints under load" is a legitimate hypothesis. The repro then includes a stage-4-under-load trigger.

Multi-Stage is opt-in based on the failure's structure. Most repairs are Standard.


## Repair Heads-Up Format

Before each substantive action — running a probe, building a standalone, applying a fix to the real codebase, kicking off a verification run — print a one-line heads-up so the user sees the discipline unfolding:

```
[repair] <phase>: <action> — <why>
```

Examples:

- `[repair] Evidence: reading stage_4_image_gen.log lines 2400-end — last 200 before the crash`
- `[repair] Hypotheses: 3 candidates — content-filter / quota / cookie expiry`
- `[repair] Lock: probing cookie expiry first (cheapest check)`
- `[repair] Isolate: building repair_stage4_no_images.py with the real beat that failed`
- `[repair] PoC: standalone passes 1/1 — fix concept holds`
- `[repair] Integrate: editing gemini_worker.py:413 — same change as standalone`
- `[repair] Step 2: re-running the originally-failing CI job under real load`

This is *not* a "do you approve?" gate. It is "FYI, here's where the repair is." Continue immediately.


## Repair Does NOT Waive

Even mid-repair, certain actions still get a one-line heads-up before execution — not a yes/no gate, just acknowledgment so the user can object within the same turn if they want:

- **Destructive operations on shared state**: dropping a production table, force-pushing to a remote main branch, deleting files outside the project tree, modifying credentials others depend on.

- **Operations that cost real money**: spinning up cloud resources, large external API jobs, anything billable past a small budget.

- **External messages**: posting to Slack/Discord, sending email, opening PRs against public repos.

- **System-level config changes**: registry, firewall, services, scheduled tasks (those CAN be installed as part of a fix but are flagged in the recap).

Format:

```
[repair] About to drop the prod table `sessions_old` — irreversible without restore. Continuing.
```

Then proceed unless the user interrupts. Default is forward motion.


## What Counts as Conclusive Evidence

Good evidence:

- A log line that directly shows the failure with a timestamp and stack.
- A variable value printed from a probe that matches the failure condition.
- A specific branch of code proven to execute via instrumentation.
- A standalone that fails every run on the current codebase and passes every run after the fix.
- A query plan that shows the index isn't being used.
- A network trace that shows the request shape mismatch.
- A screenshot of the broken UI alongside the rendered DOM.

Bad evidence (do not lock in a cause based on these):

- "It usually fails around this point."
- "I think it's probably X."
- "We saw this once last week."
- "The other engineer said this is the cause."
- Process of elimination alone, with no positive proof of the surviving candidate.


## Hard NOs

- **No guess-and-edit.** Editing the real codebase before the diagnosis is locked.
- **No skipping the standalone repro because "the bug is obvious"** — drop to Quick mode if it really is obvious, but don't fake it.
- **No "it passed once" claims** — single PoC proves only the concept, not stability or actual-usecase.
- **No `try/except: pass` "fixes."** That's hiding, not repairing.
- **No silent retry-until-green wrappers.** That's papering over an underlying failure.
- **No unrelated refactors during a repair.** One fix, one scope.
- **No declaring DONE without Step 2 verification.** PoC-only is never shippable.
- **No advancing past 5 failed approaches without declaring STUCK.** Bounded effort. After 5 distinct approaches that all fail, the diagnosis or assumptions are likely wrong — surface and stop.


## Final Report Templates

Repair always ends with one of three reports.

### DONE — fix shipped, verified

```
=== REPAIR DONE ===

Failure:        <one sentence>
Cause:          <one plain-language sentence>
Evidence:       <log line / probe output / standalone result that proved it>

Fix applied:    <what changed, file:line>
Standalone:     <path to the repro script — kept for regression reference>

PoC:            <N passed / 0 failed>
Actual usecase: <prod spec in one sentence — N passed / 0 failed>

Verdict:        SHIPPABLE
```

### PARTIAL — fix landed, something still off

```
=== REPAIR PARTIAL ===

Failure:        <one sentence>
Cause:          <one sentence>
Evidence:       <what proved it>

Fix applied:    <what changed, file:line>

PoC:            <result>
Actual usecase: <result — what failed>

Still off:      <what's still wrong + reason>
Next:           <concrete suggested move>

Verdict:        NOT SHIPPABLE
```

### STUCK — diagnosis or fix exhausted

```
=== REPAIR STUCK ===

Failure:        <one sentence>
Hypotheses tried (N):
  1. <hypothesis> → <why ruled out / why fix didn't hold>
  2. <hypothesis> → <why ruled out / why fix didn't hold>
  ...
Why I'm stopping: <why no honest 6th approach exists>

Best guess remaining:  <if any — clearly labeled as guess, not conclusion>
Recommend:             <best concrete next step for the user>

Hand back to user.
```


## Composition With Other Skills

- **Under `/auto`** — `/auto` invokes /repair as one phase of a larger autonomous task. The repair methodology runs to completion (DONE / PARTIAL / STUCK) and the auto report incorporates the outcome. /repair never asks for permission inside /auto.

- **Before `/audit`** — when a repair produces edits to the real codebase, /audit can be run on the proposed integration before it lands. Optional; /audit is the safety belt, not a requirement.

- **Pairs with `principles`** — every claim a repair makes ("evidence is conclusive", "fix is verified", "repair is done") routes through the principles checkpoint:
    - **P1 test-at-scale** — Step 2 enforces "test the actual condition," not a smaller proxy
    - **P2 conditions-upfront** — success defined before work begins
    - **P3 end-goal-in-sight** — one fix, one scope; no drift mid-repair
    - **P4 audit-before-handback** — the DONE/PARTIAL/STUCK report IS the handback verdict
    - **P5 KISS** — simplest fix that clears the goal wins; no rewrites in a debugging context
    - **P6 think-before-coding** — push back on weak diagnoses; surface alternative causes; don't guess-and-edit
    - **P7 surgical-changes** — fix's blast radius matches the bug's; no "while I'm here" cleanup
    - **P8 goal-driven-execution** — the repair loop IS the P8 loop; standalone-fails-then-passes is the per-step verify

- **After `deep-audit`** — if `deep-audit` surfaces a latent failure that the user wants fixed, /repair takes the surfaced issue and works it through the methodology.


## TL;DR

- **Repair is a P8 loop.** Transform "fix it" → "test_repro fails → fix → test_repro passes AND Step 2 green." Loop until both clear.
- **Repair is a methodology, not a workflow per system.** Same discipline for a failing test, a UI bug, a slow query, a crashed pipeline, a wrong-value function.
- **Evidence first.** Read what's broken before theorizing.
- **Multiple falsifiable hypotheses.** 2–4 candidates, each with a check.
- **Lock the cause with positive evidence.** Process of elimination is not proof.
- **Isolate before you fix.** Standalone with real inputs, narrow scope.
- **Same failure signature.** Near-miss is not a repro.
- **Fix in isolation, then integrate.** Real code only after standalone is green.
- **Two verifications: PoC and actual-usecase.** PoC alone is never shippable.
- **One fix, one scope.** No refactoring while repairing. No silencing the failure.
- **DONE / PARTIAL / STUCK.** Honest reports, every time.
