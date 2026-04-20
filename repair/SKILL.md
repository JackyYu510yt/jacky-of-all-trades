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

Create a minimal script that reproduces the bug **outside the real codebase**.

- Save it as `repair_<slug>.py` (or `.sh`) in a scratch location — not in the user's main codebase.

- It must: run by itself, import only what's strictly needed, fail in the same way as the real script with the same error message.

- No side effects on real data. No writing to the user's actual output directories. Use a temp dir.

- Keep it small. If the repro is more than ~50 lines, the isolation isn't tight enough — keep reducing.

`========================================`

### Phase 5: Confirm the Repro

Run the standalone script.

- **It must fail.** Same error, same symptom.

- If it does not fail, the hypothesis is wrong. Go back to Phase 2.

- If it fails differently, the repro is missing context. Refine and run again.

- Run it **three times** to confirm it fails consistently, not intermittently.

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

- **Minimal** — under ~50 lines. If longer, the isolation is weak.

- **Self-contained** — runs with `python repair_<slug>.py` and nothing else. No env vars, no project-specific paths (use hardcoded temp files).

- **Same failure** — the error message and stack shape match the real failure, not just "it errors somewhere."

- **Fast** — runs in under a few seconds so you can iterate quickly.

- **Temp-scoped** — writes only to `tempfile` dirs, reads only from local fixtures you create inline.


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
