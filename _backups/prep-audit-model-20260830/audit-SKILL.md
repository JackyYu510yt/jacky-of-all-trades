---
name: audit
description: Review proposed changes one last time before they're applied, using an independent AUDITOR second-brain (a fresh reviewer subagent that re-derives risk from the actual files, not the same context that proposed the change) plus a dedicated RED-TEAM attacker subagent that invents hostile scenarios (mid-operation resource death, races, half-done re-entry, poison pills, lying success signals) and walks each through the change to a HANDLED/DEGRADES/BREAKS/UNKNOWN verdict. Lists every change, checks scope match to the discussed intent, flags destructive or irreversible actions, surfaces silent assumptions and regression risks, and presents a final go/revise/stop verdict. Use right before executing any non-trivial change — edits to multiple files, deletions, refactors, config changes, git operations, external API calls, or any action the user might regret. Acts as a safety gate between "plan" and "execute". Use when the user says "audit this", "before you do that", "double check", "what are you about to do", "hold on — review first", or any pause-before-action prompt.
---

# Audit

Last-chance safety gate. Before any non-trivial change is applied, enumerate exactly what is about to happen and measure it against what the user actually asked for. Prove understanding before acting.


## When to Use This Skill

- User says "audit this", "before you do that", "double check", "hold on", "wait review first", "what are you about to do"

- Right before Claude is about to apply any of:
  - Multi-file edits
  - Deletions or overwrites
  - Git operations (commit, push, rebase, reset)
  - External API calls with side effects
  - Config changes (settings.json, system config, env vars)
  - Destructive or irreversible actions
  - Any refactor touching code that currently works

- Any time there's doubt about whether the proposed action matches the discussed intent


## Core Principle

**Before you apply, prove you understood.** Audit forces an explicit enumeration of every change and a deliberate match-check against the user's stated goal. No "trust me, I got it." No silent side effects. No surprises.

**The second-brain rule.** The brain that proposed the change is the wrong brain to clear it — it shares every blind spot that produced the plan. So the core review is run by an **independent AUDITOR**: a fresh reviewer subagent that did NOT author the plan, is handed only the stated goal + the enumerated changes, and **reads the actual target files itself** to re-derive scope, reversibility, assumptions, and regressions from source. Same-context "re-reading" is not an audit — it's the same brain agreeing with itself.

Three questions every proposed change must answer truthfully:

- **Scope** — is this exactly what was discussed, nothing more and nothing less?

- **Reversibility** — if this turns out wrong, how easy is it to undo?

- **Assumptions** — what are we treating as true that we haven't actually verified?


## Runtime Workflow

Seven phases. Run them all before executing. Do not skip.


`========================================`

### Phase 1: Enumerate the Proposed Changes

List every single change about to happen. Be explicit:

- **Files to edit** — full path + what's changing (line range or summary).

- **Files to create** — full path + purpose.

- **Files to delete** — full path + why.

- **Commands to run** — exact command string.

- **External calls** — API endpoints, services to hit.

- **State to modify** — git operations, config changes, credential operations, env vars.

If the list is empty, there's nothing to audit — let the user know and exit.

`========================================`

### Phase 2: Scope Match Check

For each proposed change, check it against the user's stated goal:

- **In scope** — directly asked for or a necessary consequence.

- **Incidental** — not asked for but small and obviously needed (e.g., adding an import that a new call requires). Flag it as incidental but usually OK.

- **Out of scope** — not asked for and not necessary. Flag loudly. Almost always should be removed from the plan.

The bias: if in doubt, it's out of scope. The user can always ask for more after the main change is applied.

`========================================`

### Phase 3: Classify Risk Per Change

Tag each proposed change with one of these labels:

- **Safe** — reversible via undo / git revert, affects only local files, no external state.

- **Reversible with effort** — deletions, large renames, moving files between dirs. Recoverable from git but requires work.

- **Irreversible local** — deletions outside git, removing tracked-but-uncommitted files, truncating log files, rm -rf.

- **External** — API calls, emails, PR creation, push to remote, deploying, messages to chat platforms. Once sent, cannot be unsent.

- **Destructive on third parties** — dropping database tables, canceling orders, revoking credentials others depend on, force-pushing to shared branches.

Higher-risk categories get more scrutiny and more explicit user confirmation.

`========================================`

### Phase 4: Check Silent Assumptions

Look at the proposed changes and ask: what does this plan assume is true, that we haven't actually verified?

Typical assumptions to flag:

- **File exists / has expected content** — did we read it recently?

- **Function signature matches** — are we calling it the way it's defined right now?

- **Dependency is installed** — `import X` works in this env?

- **Permissions / credentials** — does the user have access to what we're touching?

- **No one else is editing** — shared systems can change under us.

- **Assumed env var is set** — PATH, API_KEY, etc.

- **Assumed tool version** — behavior differs between versions.

For each assumption, either verify it now or explicitly flag it as an unchecked assumption in the audit report.

`========================================`

### Phase 5: Regression Risk

What currently works that could break as a result of this change?

- **Callers of modified functions** — does the signature / behavior change break any caller?

- **Tests that might now fail** — existing tests that exercise the changed area.

- **Adjacent features** — features that share code with the changed area.

- **Config consumers** — if config changes, who reads it and with what expectations?

- **Downstream systems** — for external calls, is the downstream prepared for this?

Flag each concrete regression risk. If the answer is "probably fine," say "probably fine" — don't pretend there's no risk when there is.

`========================================`

### Phase 5.5: Dispatch the Independent Reviewers (Second Brain + Red Team)

This is the heart of the audit. Phases 1–5 are *your* pass — the same brain that proposed the change. Now hand it to brains that didn't. Two independent agents, two different jobs: the **AUDITOR** re-derives scope / reversibility / assumptions / regressions; the **RED-TEAM** invents hostile scenarios and walks each one through the change until something breaks. When both apply, dispatch them IN PARALLEL — one message, two `Agent` calls.

**Dispatch the AUDITOR (in priority order):**

1. **Preferred — a fresh reviewer subagent.** Invoke the `Agent` tool (subagent_type `general-purpose`, or `code-reviewer` if available). Give it ONLY:
   - the user's stated goal, in the user's own words (not your paraphrase),
   - the enumerated list of proposed changes (Phase 1) — the *what*, with exact file paths and commands,
   - the explicit instruction below.

   Crucially, do **not** feed it your scope/assumption/regression conclusions — those are what you want it to re-derive independently. It must form its own view.

2. **Fallback — only if subagents are unavailable.** Open a section headed `=== AUDITOR (second brain) ===`, drop the author's stance, and review as a skeptic whose job is to catch what the author missed. Run the RED-TEAM the same way — a second section headed `=== RED-TEAM (fallback) ===` walking the scenario categories below. State clearly that this was a same-context fallback, not a true independent pass.

**The brief handed to the reviewer:**

```
You are the AUDITOR — an independent reviewer. You did NOT write this
plan and must not assume it is correct. Below is a user's stated goal
and a list of changes someone is about to apply.

Your job:
1. READ each target file yourself (current state on disk) before
   judging — do not trust the change descriptions.
2. SCOPE — does each change trace to the stated goal? Flag anything
   out of scope or missing.
3. REVERSIBILITY — classify each change's blast radius (safe /
   reversible / irreversible-local / external / destructive).
4. ASSUMPTIONS — what is the plan treating as true that the files
   don't actually support right now? (stale reads, wrong signatures,
   missing deps, unset env, wrong paths.)
5. REGRESSIONS — what currently works that this could break? Name
   concrete callers / tests / consumers.
Return ranked findings (BLOCKER / CONCERN / NOTE), each with the
evidence you found in the files. Do not rubber-stamp.

Stated goal: <verbatim>
Proposed changes: <Phase 1 enumeration>
```

**When the RED-TEAM is mandatory vs skippable.** Mandatory whenever the change touches anything unattended, long-running, stateful, or concurrent — pipelines, cron jobs, helper daemons, fallback/routing logic, queues, anything that writes checkpoints or gets retried without a human watching. For a plainly attended one-shot (a config flip, a rename the user watches happen), it may be skipped — but the Phase 6 report must then carry the explicit line `RED-TEAM: skipped — not unattended/stateful`. Silence is not a skip.

**The brief handed to the RED-TEAM:**

```
You are the RED-TEAM — an independent attacker reviewing a change you
did NOT write. Your ONLY success metric is breaking it with concrete
scenarios. Scope, style, and regressions are the AUDITOR's job — do
not spend words there.

1. READ the actual target files (and plan, if given) yourself first.
2. GENERATE at least one concrete hostile scenario per category below —
   two for any category the change touches directly. Skipping a
   category requires writing "N/A — <why it cannot apply>".
   C1  MID-OP DEATH        a resource (credits/quota/disk/network) dies
                           HALFWAY through an operation, not before it
   C2  CHECK-THEN-ACT      state flips between the decision and the act
   C3  HALF-DONE RE-ENTRY  process killed mid-write — what does the
                           NEXT run find on disk, and what does it do
                           with the partial?
   C4  FLAPPING            fail → recover → fail again inside one poll
                           window
   C5  TWO ACTORS          a human or a second process acts
                           mid-automation
   C6  BOUNDARIES          0 items, 1 item, exactly-at-cap,
                           empty/missing file
   C7  TIME WINDOWS        poll interval straddles a batch boundary;
                           restart mid-window; long stall then burst
   C8  RECOVERY FAILS      the recovery path itself errors (probe
                           passes but the real call fails; flag delete
                           fails; rollback interrupted)
   C9  POISON PILL         one item that LOOKS valid but fails every
                           retry, re-enters the queue each run, and
                           starves everything behind it
   C10 LYING SUCCESS       exit 0 / plausible artifact that is wrong
                           (black frames, a signed-out page saved as
                           valid HTML) — attack the success check
                           itself
3. WALK each scenario through the real code/plan step by step to its
   end-state — cite the exact line/step where the outcome is decided.
4. VERDICT each scenario:
   HANDLED  — cite the line/mechanism that absorbs it
   DEGRADES — bounded loss; name the cost out loud
   BREAKS   — name the concrete bad END-STATE (data loss, wedge,
              duplicate output, silent stop), not just the trigger
   UNKNOWN  — the artifact doesn't contain enough to trace the
              outcome; say exactly what's missing. Never guess a
              verdict.
Return the scenario table, BREAKS first, then UNKNOWN, then DEGRADES,
then HANDLED. Do not manufacture findings to look busy — but if every
row came back HANDLED, re-check that you walked each scenario to its
actual end-state instead of trusting the change's own description.

Stated goal: <verbatim>
Target files / plan: <paths, or plan contents>
```

**Reconcile.** When the reviewers return, merge their findings with your own Phase 1–5 pass — the RED-TEAM's scenario table goes into the report verbatim. Anything a reviewer flagged that you missed is exactly the value of the second brain — surface it prominently. Disagreements — yours vs a reviewer's, or AUDITOR vs RED-TEAM — get shown to the user, not silently resolved.

`========================================`

### Phase 6: Present the Verdict

Emit a structured audit report. Template:

```
=== AUDIT REPORT ===

Stated goal: <one-sentence restatement of what the user asked for>

Proposed changes (N):
 1. [SAFE]           pipeline.py:45 — rename variable foo → bar
 2. [REVERSIBLE]     config.json — add retry_count=3 key
 3. [EXTERNAL]       git push origin main
 4. [IRREVERSIBLE]   delete old_backups/*.log

Scope check:
 - In scope (3): 1, 2, 3
 - Incidental (0): —
 - Out of scope (1): 4 — user didn't ask for log cleanup

Unchecked assumptions (2):
 - Assuming pipeline.py has not been modified since we last read it
 - Assuming git remote 'origin' still points at the expected repo

Regression risk (1):
 - retry_count key added — no existing code reads this key, so no behavior changes for existing runs. Probably fine.

Independent reviewer (second brain):
 - [BLOCKER] config.json already has retry_count=5 at line 12 — item 2
   would overwrite a real setting (the author's pass missed this).
 - [CONCERN] item 1 rename: 3 callers in jobs/ reference `foo`.
 - Agreed with author on items 3, 4.
 - (or: "fallback same-context review — no subagent available")

Scenario attack (RED-TEAM):
 #   Cat  Scenario                                    Verdict
 1   C1   engine cap dies at item 3 of 8, mid-write   HANDLED — requeued next batch (helper.py:214)
 2   C2   flag deleted between check and dispatch     DEGRADES — ≤1 batch on wrong engine
 3   C3   killed mid-folder-write                     BREAKS — next run ships the half-written folder
 ... (all 10 categories covered or explicitly N/A)
 (or: "RED-TEAM: skipped — not unattended/stateful")

Verdict: NEEDS REVISION
Recommendation: drop item 4 (out of scope); reviewer found item 2
clobbers an existing key — re-check before applying; update the 3
callers for item 1. Then re-audit.
```

Verdict options:

- **GO** — safe to apply as-is. Still requires user's explicit "yes" before executing.

- **PROCEED WITH CAUTION** — apply-able, but user should know about the risks listed. Requires explicit "yes".

- **NEEDS REVISION** — something is out of scope, or an unchecked assumption is too important to skip. Revise the plan and re-audit.

- **STOP** — a destructive or cross-user action that should not happen without deeper review. Back to planning phase.

**Hard rule:** any RED-TEAM scenario with verdict **BREAKS** caps the verdict at **NEEDS REVISION** (or **STOP** if the broken end-state is destructive or external). BREAKS is never "noted and passed." A load-bearing **UNKNOWN** doesn't block on its own, but must appear under unchecked assumptions with the cheapest probe that would resolve it.

`========================================`

### Phase 7: Wait for User Go

After the verdict is presented, do not execute. Wait for the user to say one of:

- **"go"** / **"proceed"** / **"yes"** — apply all proposed changes.

- **"fix X and re-audit"** — adjust the plan, re-run audit from Phase 1.

- **"stop"** / **"rethink"** — abandon the plan, return to discussion.

If the user's response is ambiguous, ask one clarifying AskUserQuestion instead of guessing.

`========================================`


## What Counts as "Non-Trivial" (trigger threshold)

Audit is not required for:

- Single-line fixes you just discussed with the user.

- Read-only operations (ls, cat, grep, diff).

- One-shot file reads.

- Running a test suite or linter.

Audit IS required for:

- Touching 3+ files.

- Any delete, overwrite, or rename of existing code / config.

- Any git operation with remote side effects.

- Any external API call with side effects.

- Refactors or restructures, even "small" ones.

- Anything the user specifically asked to audit.


## Hard NOs

- Do not skip audit because "the changes are obvious."

- Do not skip the independent reviewer (Phase 5.5) and call your own Phase 1–5 pass "the audit." The author brain re-reading its own plan is not a second brain. If a subagent truly can't run, say so explicitly and mark the review as a same-context fallback.

- Do not skip the RED-TEAM scenario attack on anything unattended, long-running, stateful, or concurrent — and never accept a scenario table that drops a category without an explicit N/A reason, or a skip without the explicit `RED-TEAM: skipped` line in the report.

- Do not approve-and-proceed in the same breath — the user gets to see the audit and decide.

- Do not continue past a NEEDS REVISION verdict without the user's explicit acknowledgement.

- Do not treat audit as a formality — if any phase surfaces a real concern, it matters.

- Do not summarize away the details — every proposed change must appear individually in the report, not bundled.


## Relationship to Other Skills

- **`prep`** — plans new work from scratch, runs an independent AUDITOR second-brain review before execution. `audit` is the inline equivalent, run right before executing any non-trivial plan — and both use the same independent AUDITOR + RED-TEAM pair (Phase 5.5 holds the canonical RED-TEAM brief that `prep` and `auto` reference).

- **`repair`** — after a failure. `audit` is before an execution. Opposite ends of the same principle: prove what you think is true.

- **`optimize`** / **`simplify`** — propose changes. `audit` reviews the proposals from any skill before they're applied.

- **`explain`** — the audit report uses `explain`'s formatting conventions (rainbow top, `====` separators, bolded anchors, plain-language TL;DR).


## TL;DR

- **Pre-execution gate** — runs right before any non-trivial change is applied.
- **Independent second brain** — a fresh reviewer subagent reads the real files and re-derives the risks, so the audit isn't the same brain agreeing with itself.
- **Scenario attack** — a dedicated RED-TEAM agent invents hostile scenarios across 10 attack categories (mid-op death, races, half-done re-entry, flapping, two actors, boundaries, time windows, recovery-fails, poison pill, lying success) and walks each through the change to HANDLED / DEGRADES / BREAKS / UNKNOWN; any BREAKS blocks GO.
- **Lists every change** — files, commands, external calls, state modifications.
- **Checks scope** — match to what the user actually asked for, flag out-of-scope.
- **Classifies risk** — safe, reversible, irreversible, external, destructive.
- **Surfaces assumptions** — what we're treating as true without checking.
- **Spots regressions** — what currently works that could break.
- **Waits for go-ahead** — never executes without explicit user approval.
