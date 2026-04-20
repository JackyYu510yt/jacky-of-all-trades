---
name: repair
description: Debug and fix a broken script with strict discipline — gather evidence, list possible causes, lock in the one true cause with conclusive and replicable proof, build a standalone test script that reproduces the bug, try repair methods on the standalone until one works and is verified, then and only then apply the fix to the real code. Use when the user says "it's broken", "something's wrong", "I'm getting an error", "debug X", "fix Y", "why is Z failing", "this crashed", or after any failed pipeline run. Never guess-and-edit. Never ship a fix without standalone verification.
---

# Repair

A disciplined debugging workflow. Every step must produce **conclusive, verifiable, replicable** evidence before moving on. No shipping a fix based on a hunch. The standalone test script is the proof contract — the fix is not "done" until the isolated repro turns green.


## When to Use This Skill

- User says "it's broken", "not working", "crashed", "getting an error", "debug this", "fix Y", "why is Z failing"

- Right after a failed pipeline run or a user-reported regression

- Any time a fix is being proposed without a matching isolated test — stop and run `/repair` instead


## Core Principle

Every step produces evidence strong enough to answer three questions truthfully:

- **Conclusive** — does this prove the cause beyond reasonable doubt?

- **Verifiable** — can someone else run the same check and see the same result?

- **Replicable** — does the bug reproduce on demand, not just "sometimes"?

Also: the workflow is **atomic**. Each phase must fully succeed before the next begins. No "we'll figure that out later." No integrating a fix before the isolated test passes. If a phase fails, loop back — do not proceed.


## Runtime Workflow

Nine phases. Do not skip. Do not reorder.


`========================================`

### Phase 1: Gather Evidence

Before forming any theory, collect what's already known.

- **Logs first.** If a log file exists (stdout capture, app log, error dump), read it. Look for: stack traces, error messages, timestamps of the failure, what was running just before, any recent warnings.

- **If no log, read the code.** Start from the file the user identifies as broken, or the entry point of the pipeline, or the function named in the error they mention.

- **Ask the user** (via AskUserQuestion) what they observed: what they ran, what they expected, what they got instead. Exact command and exact output if available.

Phase 1 ends when you have at least one concrete artifact (log line, error message, stack trace, user-described symptom).

`========================================`

### Phase 2: List Possible Causes

Propose 2–4 specific hypotheses. Each must be:

- **Concrete** — not "something's wrong in Stage 5", but "the Gemini call returns None because the API key is expired".

- **Falsifiable** — there must be a check that could disprove it.

- **Ranked** by likelihood given the evidence so far.

Present them to the user using the `explain` skill's tiered-options format (`Option A / B / C`) — each option one sentence, with its evidence-so-far and the check that would confirm or rule it out.

`========================================`

### Phase 3: Lock In One Cause With Conclusive Evidence

For each hypothesis, design a specific **check** that would either confirm or rule it out. Acceptable checks include:

- Reading a specific line or branch in the code.

- Running a probe command (`print`, `type()`, a single `ffprobe`, etc.).

- Inspecting a file's contents or permissions.

- Reproducing the exact call with known-good inputs.

Execute the checks in order of cheapest-first. Rule out or confirm each hypothesis.

**Stopping condition:** exactly one hypothesis remains AND there is at least one piece of evidence that directly proves it (not just "everything else is ruled out"). If the last-remaining hypothesis has no positive proof, loop back to Phase 2 and add more candidates.

`========================================`

### Phase 4: Build a Standalone Repro Script

Create a standalone script that reproduces the bug **outside the real pipeline**, using **the exact same inputs, files, and conditions that caused the original failure**.

- Save it as `repair_<slug>.py` (or `.sh`) in a scratch location — not in the user's main codebase.

- **Use the real failing inputs.** The same video file that failed, the same config, the same args. Not a synthetic mini-version. A "similar" test can hide data-dependent bugs. The whole point of this phase is to prove we can reproduce *this specific failure*, not a cousin of it.

- **Narrow the scope, not the inputs.** If the real pipeline has 9 stages and stage 5 failed, the repro runs *just stage 5* — not all 9. Grab the real file that was passed into stage 5 (from the pipeline's intermediate output on disk, or from a checkpoint) and call only the failing step. This keeps the repro fast even when the whole pipeline is slow.

- Read input files from their actual on-disk locations — do not copy to temp, do not synthesize fake data. If the bug only happens on that specific 47 GB video, use that specific 47 GB video.

- Write output to a temp dir so the repro doesn't pollute the user's real output directories — but inputs come straight from the real source.

- If the failing step is destructive on its input (mutates or moves a file), copy the file to a temp location first and run against the copy. Preserve it bit-for-bit — do not shrink it.

`========================================`

### Phase 5: Confirm the Repro

Run the standalone script against the real inputs.

- **It must fail with the same error as the real pipeline.** Same exception, same line (or equivalent), same symptom. A near-miss is not enough.

- If it does not fail, either the hypothesis is wrong OR the repro is missing context (env var, config flag, earlier-stage side effect the real pipeline provided). Go back to Phase 3, tighten the diagnosis or add the missing context to the repro.

- If it fails *differently* than the real pipeline, the narrowing stripped something important. Add it back.

- Run it **three times** against the same real inputs to confirm the failure is consistent, not intermittent. If intermittent, that itself is a clue worth investigating before moving to Phase 6.

`========================================`

### Phase 6: Try Repair Methods on the Standalone

Now — and only now — try fixes.

- Propose 1–3 repair approaches. Pick the simplest one first (KISS applies here too).

- Apply the fix ONLY to the standalone script. Do not touch the real code yet.

- Run the standalone. If it passes, move to Phase 7. If not, try the next approach.

- If none work, loop back to Phase 3 — the diagnosis was wrong.

`========================================`

### Phase 7: Verify the Fix Is Stable

Don't trust a single pass. Before calling it fixed:

- Run the standalone **3 times in a row**. All must pass.

- Run it with 2–3 different inputs (edge cases relevant to the bug). All must pass.

- If the bug was intermittent, run it 10+ times to confirm the flake is gone.

- If any run fails, the fix is incomplete. Back to Phase 6.

`========================================`

### Phase 8: Integrate Into the Real Code

Only after Phase 7 fully passes.

- Apply the exact same fix pattern to the real codebase. Same logic, same change shape.

- Edit only the minimum needed. Do not rewrite surrounding code.

- Run the real script's existing tests, if any. Run a small sample of the real workflow.

- If anything regresses, revert and go back to Phase 6 — the fix didn't translate cleanly.

`========================================`

### Phase 9: Final Report

Emit a closing report. See template below.

`========================================`


## What Makes a Good Standalone Repro

- **Same inputs as the real failure.** Same files, same paths, same params, same env. Reproduction fidelity beats test brevity. If the bug needs a 47 GB video, use the 47 GB video.

- **Narrow scope, not narrow inputs.** Isolate to just the failing step or function, not the whole pipeline. Real inputs going into a thin wrapper around the failing call.

- **Self-contained execution.** Runs as `python repair_<slug>.py` from any directory. Imports only the specific code paths needed to reach the failing line — not the orchestration layer.

- **Same failure signature.** The error message, stack trace, and symptom match the real failure one-to-one.

- **Fast enough to iterate.** By narrowing to the failing step, even a 2-hour pipeline becomes a 30-second repro. If the failing step itself is slow (e.g., a large encode), that's unavoidable — but most real bugs fail within the first few seconds of the step that's broken.

- **Output temp-scoped.** Inputs from real source paths, outputs to `tempfile` dirs. Never overwrites the user's real output locations.

- **Inputs preserved.** Never shrink, trim, or alter the real input to make the repro "cleaner" — that defeats the purpose of using real inputs.


## What Counts as Conclusive Evidence

Good evidence:

- A log line that directly shows the failure with a timestamp and stack.

- A variable value printed from the standalone that matches the failure condition.

- A specific branch of code proven to execute via a probe.

- A reproduction that fails every run on the current codebase and passes every run after the fix.

Bad evidence (do not lock in a cause based on these):

- "It usually fails around this point."

- "I think it's probably X."

- "We saw this once last week."

- Process of elimination alone, with no positive proof of the remaining candidate.


## Hard NOs

- Do not edit the real codebase before Phase 8.

- Do not skip the standalone repro because "the bug is obvious".

- Do not accept "it passed once" as a fix being verified — Phase 7 requires 3+ passes.

- Do not introduce unrelated refactors while fixing the bug. One fix, one scope.

- Do not wrap the failing code in `try/except: pass` as a "fix" — that hides the bug, it doesn't repair it.

- Do not guess. If evidence is inconclusive, gather more. If you can't gather more, tell the user and ask.

- Do not ship a fix based only on process of elimination.


## Final Report Template

`========================================`

**Cause:** <one plain-language sentence>.

**Evidence:** <the log line / probe output / standalone result that proved it>.

**Fix applied:** <what changed, file:line>.

**Verification:** <N standalone runs passed, real-script sample passed, any existing tests passed>.

**Standalone repro:** `repair_<slug>.py` — kept for regression reference.

**Related concerns surfaced but not addressed:** <list, if any — user decides whether to file follow-up>.

`========================================`


## Presentation Style

Use the `explain` skill's conventions for every user-facing message:

- Wrap phase summaries with `====` separators.

- Bold step/phase names. One plain-sentence body under each.

- Use Casual + Learning language level — inline definitions for any technical term on first use.

- End every multi-phase report with a TL;DR bullet list in plain language.

- Never print a ruled-out hypothesis as if it might still be right — once ruled out, it's gone.


## TL;DR

- **Evidence first** — read logs or code before theorizing.
- **List causes** — 2 to 4 concrete, falsifiable hypotheses.
- **Prove one** — with evidence that's conclusive, verifiable, replicable.
- **Build a standalone** — tiny script outside the real code that fails the same way.
- **Fix in isolation** — try repairs on the standalone only.
- **Verify stability** — 3+ clean runs before trusting the fix.
- **Then integrate** — apply the same fix to the real code, confirm nothing regressed.
- **Report** — cause, evidence, fix, verification — all written down.
