---
name: audit
description: Review proposed changes one last time before they're applied. First scopes the scene — recons the relevant files/subsystems the change actually sits inside (fanned out to sub-agents for a real area, mirroring supergoal's Stage 2 recon), then checks prior findings/SPEC.md for what recon turned up (via note.py) so nothing re-discovers something already on record. States the plain facts of what's about to happen, then hands those facts — plus the real target files — to an independent AUDITOR second-brain subagent (a fresh reviewer that did not author the plan) that does a full scope/reversibility/assumptions/regressions pass internally but must compress it to a strong, unhedged YES or NO on "should this proceed?" — a finding only drives NO if it's both likely-to-happen and consequential AND backed by real evidence or stated high-confidence reasoning, so trivial or unverified edge cases can't false-block. No BLOCKER/CONCERN scoring, no scenario tables — one question, one clean answer, then the user's own go/no-go. Use right before executing any non-trivial change — edits to multiple files, deletions, refactors, config changes, git operations, external API calls, or any action the user might regret. Acts as a safety gate between "plan" and "execute". Use when the user says "audit this", "before you do that", "double check", "what are you about to do", "hold on — review first", or any pause-before-action prompt.
---

# Audit

Last-chance safety gate. Scope the scene, check what's already known, state the facts, ask one question, get one strong answer. No essay, no scoring rubric.


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

**Ground it, then facts, then one question, then one strong answer.** Audit is not an essay contest. It grounds itself in the real surrounding code first, states exactly what's about to happen in plain lines, then asks exactly one thing — *should this proceed?* — and refuses to accept a hedge as the answer.

**The second-brain rule.** The brain that proposed the change is the wrong brain to clear it — it shares every blind spot that produced the plan. So the answer comes from an **independent AUDITOR**: a fresh reviewer subagent that did NOT author the plan, is handed only the stated facts, and **reads the actual target files itself** before answering. Same-context "re-reading" is not an audit — it's the same brain agreeing with itself.

**No hedging.** "Probably fine," "mostly OK," "yes, but…" are not answers. If there's a real caveat, the caveat makes it **NO** — and the caveat becomes the one sentence of why.


## Runtime Workflow

Six steps. Do not skip any of them.

`========================================`

### Step 1: Scope the Scene (Recon)

Before anything else, ground yourself in what's actually there — the same move `supergoal`'s Stage 2 recon makes before it plans: read the relevant files/subsystems the change actually sits inside, not just the literal files being edited.

- Identify what surrounds the change: callers, adjacent modules, the conventions already in use, anything that explains *why* the current code looks the way it does.
- If it's a real area (multiple files/subsystems, not a one-liner), fan out with `Agent` sub-agents in parallel to read it — same fan-out-and-offload rule `/auto` and `supergoal` use, so the driver stays lean instead of reading everything itself serially.
- For a genuinely small, self-contained change (one file, no callers, nothing adjacent), this step is quick — say "scene is just this file, nothing adjacent" and move on. Don't manufacture recon for a one-liner.

Output: a short grounding note — what's actually there, in plain lines. This is what Step 3's facts get checked against, and what Step 2's findings lookup runs over (recon may surface adjacent files worth checking too, not just the ones named in the original ask).

`========================================`

### Step 2: Check What's Already Known

Before stating anything, check whether this exact ground has already been covered — the whole point is to stop re-discovering (and re-spending a day on) something that's already on record.

For every file that matters — the target files AND anything Step 1's recon surfaced as relevant — plus the project as a whole, run:

```
python "C:\Users\Shadow\.claude\skills\spec\note.py" --for "<ABS path to file>"
python "C:\Users\Shadow\.claude\skills\spec\note.py" --recent "<ABS project dir>"
```

Also read the project's `SPEC.md` if one exists — specifically the `Assumptions & Unknowns` section and the Change Log — for any decision or open question that bears on this change.

If something surfaces that already answers, decides, or warns about part of what's about to happen: **that finding goes straight into the facts list as its own line, verbatim (with its id/date)**, and it is decisive — the plan doesn't get to silently re-derive something already on record. If a finding was retracted, say so and say what replaced it (the retraction body, not just "it's dead").

If nothing surfaces, say so in one line ("no prior findings on these files/project") and move on — this step isn't meant to manufacture busywork, only to catch the expensive case.

`========================================`

### Step 3: State the Facts

Plainly, in a flat list — no analysis, no framing, just what is true right now. **Every fact carries its evidence, named** — same rule `supergoal` uses for derived items: "the evidence clause is mandatory, not decoration." A fact without the thing it came from is a guess wearing a fact's clothes.

- **What's changing** — each file/command/external call, one line: path + what changes (or command string, or endpoint hit). Evidence: you're about to make this change — no citation needed, it's the proposal itself.
- **Why (this change)** — the one-sentence goal this specific change serves, in the user's own words if possible.
- **End goal (the actual finish line)** — the project's pinned goal, not just this change's excuse for existing. Pull SPEC.md's `## Goal` section if one exists (quote it); otherwise the user's stated end objective for this session/thread, in their words. This is what tells the auditor whether the change is a step toward the real target or a local fix that misses it — a change can pass every other check and still not be what the finish line needs.
- **What already works that this touches** — from Step 1's recon: name it if there's anything, or say "nothing existing." Evidence: `<file:line you read it at>`, or the recon sub-agent's finding.
- **What's unverified** — at most the handful of things the plan is trusting without having checked. Labeling something "unverified" IS its evidence tag — that's the honest alternative to a fact you can't back.
- **Prior findings/decisions (Step 2)** — anything that surfaced, verbatim (finding id/date is its own evidence), or "none found."

Each fact is either **empirical** (you read it, ran it, or a finding/spec states it — cite where) or **explicitly unverified** — never a bare assertion presented as settled. If you can't name where a "fact" came from, either verify it now (a quick read/run) or move it to the unverified line. This replaces any separate scope/risk/assumption/regression writeup — those belong in this one list, stated plainly with evidence, not scored or categorized. If the list is empty, there's nothing to audit — say so and exit.

`========================================`

### Step 4: Ask the Independent Auditor

Dispatch a fresh reviewer subagent (`Agent` tool, `subagent_type: general-purpose`, or `code-reviewer` if available — model unset, keep Opus). Give it ONLY:

- the Step 3 facts, verbatim (including anything that surfaced in Steps 1-2),
- the real file paths to read (target files + whatever Step 1 identified as adjacent),
- the brief below.

Do **not** feed it your own opinion of whether it should proceed — that's what it must derive itself from the facts and the actual files.

**The brief:**

```
You are the AUDITOR — an independent reviewer. You did NOT write this
plan. Below are the stated facts of a change about to be applied,
including recon of the surrounding code and any prior findings/
decisions that already surfaced.

Before answering, actually do the work — this is not a rubber stamp:
1. READ the actual target files yourself (current state on disk). Do
   not trust the facts' description of them blindly. If prior findings
   were handed to you, independently check whether THIS change is the
   thing they already cover, or something genuinely new.
2. SCOPE — two separate checks, don't collapse them:
   a. does each change trace to the stated goal FOR THIS CHANGE? Anything
      extra riding along that wasn't asked for?
   b. does it actually serve the END GOAL (the project's real finish
      line, given below)? A change can be perfectly in-scope for its
      own stated purpose and still be the wrong move for where the
      project is actually trying to end up — flag that mismatch if you
      see it.
3. REVERSIBILITY — if this is wrong, how bad and how hard to undo?
4. ASSUMPTIONS — what is the plan treating as true that the files on
   disk don't actually support right now (stale read, wrong signature,
   missing dependency, unset env, wrong path)?
5. REGRESSIONS — name concrete callers / tests / consumers of what's
   being changed that could break.

That analysis is real work you must do — but it is NOT what you hand
back. Compress it into exactly ONE question and answer it:
SHOULD THIS PROCEED?

6. MATERIALITY FILTER — before anything from steps 2-5 gets to drive
   your answer, it must clear BOTH bars:
     - LIKELY: this would actually happen on a normal run, not just
       "technically possible in some contrived case."
     - CONSEQUENTIAL: if it happened, the outcome would actually be
       bad (data loss, wrong result, broken caller, silent corruption)
       — not cosmetic, not "slightly less elegant," not a style
       preference.
   A finding that fails either bar gets NOTED, never gets to cause a
   NO. Do not manufacture a hypothetical just to have found something
   — "nothing material" is a legitimate, complete result of steps 2-5,
   and should produce a YES. You are not scored on finding problems;
   you are scored on being RIGHT about whether this specific change,
   as it will actually run, is safe.

7. EVIDENCE CHECK — the decisive fact behind your answer must be one
   of:
     - EMPIRICAL — something you actually verified: read it in the
       file, ran it, found it in a prior finding/spec. Cite where.
     - HIGH-CONFIDENCE LOGIC — no direct evidence exists, but you can
       state the reasoning chain in one clause and would stake real
       confidence on it (not "seems fine," not a vibe, not "probably
       works like similar code elsewhere").
   If a claim driving your answer is neither — you didn't check and
   can't reason it through with confidence — that claim doesn't get to
   decide the answer. Either verify it now (re-read the file, run the
   check) or fall back to the next-most-decisive claim that IS backed.

Answer format — first line is a single word, YES or NO. Second line is
exactly one sentence of why, naming the SPECIFIC fact from your
analysis that decided it (a concrete file/line/caller, not a category
label like "regression risk"), including why it clears both materiality
bars above (or, on YES, that nothing found cleared them) and whether
it's empirical or high-confidence logic.

No hedging. "Probably", "mostly", "with caveats", "yes but" are not
valid first words. Only a caveat that clears BOTH materiality bars AND
the evidence check makes the answer NO — an unlikely, trivial, or
unverified-and-unreasoned caveat does not, even if it's real.

If asked to elaborate afterward, you must be able to produce the full
scope/reversibility/assumptions/regressions findings from steps 2-5 —
so keep that work, don't discard it once you've compressed to one line.

Facts: <Step 3 facts, verbatim>
Files to read: <paths>
```

If subagents are genuinely unavailable, answer this yourself under a heading `=== AUDITOR (fallback, same-context) ===`, state plainly that it's a same-context fallback and not independent, and hold yourself to the same YES/NO-plus-one-sentence format.

**If the auditor hedges anyway:** send the brief back once — "Answer YES or NO only, first word." A second hedge does not get a third try; treat it as **NO** (unresolved risk defaults to no-go) and say so in the report.

**Detail on demand.** The one-sentence answer is the default surface, not the ceiling. If the user asks "why" / "what did it find" / "show your work," relay the auditor's full scope/reversibility/assumptions/regressions findings — they did that analysis, it isn't thrown away, it's just not dumped unprompted.

`========================================`

### Step 5: Present the Verdict

```
=== AUDIT ===

Scene: pipeline.py calls into jobs/retry.py; config.json is read once at startup, no live reload.

Facts:
 - pipeline.py:45 — rename variable foo -> bar               [the proposal itself]
 - config.json — add retry_count=3 key                        [the proposal itself]
 - git push origin main                                       [the proposal itself]
 - goal (this change): <one sentence, user's words>
 - end goal (project): <quoted from SPEC.md ## Goal, or user's stated finish line> [SPEC.md / session]
 - touches: retry logic in jobs/                               [read jobs/retry.py:12-30]
 - unverified: assuming config.json hasn't changed since last read

Auditor: NO — config.json already sets retry_count=5 at line 12, so this would silently overwrite a real setting.

Your call: blocked on the auditor's NO — fix the conflicting key before proceeding, or tell me to override.
```

On a **YES**, the line reads `Your call: auditor cleared it — still need your go-ahead to execute.`

`========================================`

### Step 6: Wait for User Go

Never execute on a YES alone, and never execute past a NO. After the verdict is presented, wait for the user to say one of:

- **"go" / "proceed" / "yes"** — apply all proposed changes (only meaningful after a YES, or as an explicit override of a NO — if it's an override, say so out loud before acting).

- **"fix X and re-audit"** — adjust the plan, re-run from Step 1.

- **"stop" / "rethink"** — abandon the plan, return to discussion.

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

- Do not skip Step 1's recon and plan off the literal edit targets alone — the change sits inside a system, and the auditor's regression check is only as good as what got read.

- Do not skip the prior-findings check (Step 2) to save time — that's the step that catches "we already spent a day on this."

- Do not skip stating the facts, even for a change that "looks obvious."

- Do not skip the independent AUDITOR call (Step 4) and call your own Step 1-3 pass "the audit." The author brain re-reading its own facts is not a second brain. If a subagent truly can't run, say so explicitly and mark the answer as a same-context fallback.

- Do not accept a hedged answer as final — one resend, then a second hedge counts as NO.

- Do not let the auditor block on something that fails the materiality filter (unlikely or trivial) or the evidence check (unverified and not high-confidence reasoned) — that's re-manufacturing the old "bullshit edge case" problem this rewrite exists to kill.

- Do not proceed past a NO without the user explicitly overriding it, out loud.

- Do not approve-and-proceed in the same breath — the user gets to see the verdict and decide, even on YES.

- Do not pad the facts list with categorized scoring, scenario tables, or risk labels — that's exactly the essay this workflow replaced. Facts stay flat lines.

- Do not turn Step 1's recon into busywork on a genuinely trivial, self-contained change — state "nothing adjacent" and move on.

- Do not state a Step 3 fact without its evidence tag — a fact with no citation and no "unverified" label is a guess presented as settled, and it poisons the auditor's answer downstream since the auditor trusts these facts as the starting frame.


## Relationship to Other Skills

- **`supergoal`** — Step 1's recon mirrors `supergoal`'s Stage 2 (parallel recon before planning) and its fan-out-and-offload rule. `audit` runs a scaled-down version of the same move right before execution, instead of at the start of a whole build.

- **`prep`** — plans new work from scratch, and can hand its plan to `audit` before execution. `audit` is the inline last-chance gate; both lean on the same independent-AUDITOR principle, kept as simple as this file describes.

- **`repair`** — after a failure. `audit` is before an execution. Opposite ends of the same principle: prove what you think is true.

- **`optimize`** / **`simplify`** — propose changes. `audit` reviews the proposals from any skill before they're applied.

- **`explain`** — the audit report uses `explain`'s formatting conventions (rainbow top, `====` separators, bolded anchors, plain-language TL;DR).


## TL;DR

- **Pre-execution gate** — runs right before any non-trivial change is applied.
- **Scopes the scene first** — recons the relevant surrounding files/subsystems (fanned out to sub-agents for a real area), same move `supergoal` makes before planning — so the audit is grounded in the real system, not just the literal edit targets.
- **Checks what's already known** — `note.py --for`/`--recent` + SPEC.md, over both the target files and whatever recon surfaced, so nothing re-discovers (and re-burns a day on) a finding already on record.
- **Facts, not essays** — a flat list of what's changing, why, the project's real end goal (SPEC.md's `## Goal` or the user's stated finish line, not just this change's local excuse), what it touches, what's unverified, each carrying its own evidence tag (where it was read/run, or explicitly "unverified"). No scope tables, no risk labels, no scenario categories.
- **End-goal aware** — the auditor checks scope against BOTH this change's stated purpose AND the actual finish line, so a change can't pass just for being locally consistent while missing what the project is really for.
- **Evidence-first end to end** — not just the auditor's final call: the facts it's handed already have to be empirical or explicitly flagged unverified, so nothing downstream is fact-checking an unbacked assertion.
- **One question** — "should this proceed?" — handed to an independent AUDITOR subagent that reads the real files itself and does the full scope/reversibility/assumptions/regressions pass internally.
- **Materiality + evidence gates** — a finding only gets to drive NO if it's likely AND consequential, AND backed by something actually verified or a stated high-confidence reasoning chain. Kills the "bullshit edge case" false-block problem.
- **One strong answer** — YES or NO, first word, one sentence why. Hedges get sent back once, then default to NO.
- **NO blocks** — no proceeding past it without an explicit user override, said out loud.
- **User still decides** — even a YES needs the user's own go-ahead before anything executes.
