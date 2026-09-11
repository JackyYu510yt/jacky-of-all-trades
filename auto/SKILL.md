---
name: auto
description: Universal autonomous mode. The user runs `/auto` (or says "go autonomous", "no gates", "just do it", "set and forget", "keep going until it's done") to authorize Claude to drive a task end-to-end without further prompts. The invocation IS the authorization — there is no follow-up confirmation gate. /auto refuses to start without a plan file, writes one file of its own (RUN.md) per run, and refuses to report a verdict until check_exit.py confirms every claimed criterion is actually evidenced. Findings are captured live (note.py) and surfaced automatically at session start and on first touch of a file with known issues — nothing here needs to be remembered to work.
---

# Auto

A small executor. `/auto` hands Claude a task; Claude drives it to a verdict
with no further prompts, on a plan it did not invent.

**Rebuilt 2026-09-10** from a 3,114-line predecessor, per
`Skills/prep-auto-rebuild.txt` and its charter. The old file's guardian cron,
per-function reviewer, and three separate report templates are retired —
see "What changed" at the bottom if you're looking for them.

## The rung — read this once, it explains every tag below

Every rule in this file carries one of three tags:

```
(generated)  Derived from its source of truth at the moment it's needed.
             Cannot disagree with reality because it's never hand-kept.
(checked)    A script verifies the obligation and refuses to let the run
             continue until it passes. Loud, not silent.
(judgment)   A human-reasoning call. Nothing enforces it. Get it right by
             thinking, not by a script backstopping you.
```

If a rule you're tempted to add can't be generated or checked, it still
belongs here — but label it `(judgment)` so a future reader knows nothing
is watching it. That labelling discipline is the whole reason this file is
under 600 lines instead of 3,114.

## Hard Invariants (unchanged from the original, still absolute)

1. **Invocation is authorization.** No "should I proceed?", no phase-confirm
   gates. `(judgment)`
2. **Never advance on a bad result.** A failed check is a failed check —
   don't narrate around it. `(judgment)`
3. **Honest reporting.** If 3 of 8 criteria are unmet, the report says so.
   `(checked` — check_exit.py refuses a report with unevidenced "met" boxes`)`
4. **File is the contract.** RUN.md + its log.txt are re-read before any
   non-trivial action; conversation memory is not trusted over them.
   `(judgment)`
5. **Auto Does NOT Waive** on: destructive ops on shared state (force-push
   to public main, dropping prod tables, mass-delete), spend beyond a small
   budget, external messages (Slack/email/PRs/social), credentials/registry/
   firewall/scheduled-task changes. These get a one-line heads-up, then
   proceed — not a yes/no gate. `(judgment)`

## Phase 0 — refuse without a plan (the only gate)

`/auto` will not invent a plan. Look, in order:

```
1. An explicit path in the invocation ("/auto <path>")
2. Exactly one prep-*.txt in the working directory
3. ./PLAN.md
4. A SPEC.md's `## Milestones` blueprint — ONLY when explicitly bound
   (named in the invocation, chained via /spec, or you're already working
   in it this session). Mere presence never binds it.
```
`(judgment` — the refusal itself; nothing forces the model to actually stop`)`

**Zero matches, or more than one `prep-*.txt` with no way to tell which:**
refuse, name exactly what was looked for and what was found, and stop. No
guessing which plan was meant — Q1 of the original plan's Open Questions
decided this the safe way: zero typing in the common case (one file), loud
in the ambiguous one (more than one, or none).

**A match exists:** extract the goal (one sentence) and at least one
checkable success condition. Both frozen from here on — never re-derived,
never asked about again this run.

## Read prior findings — mostly automatic now

Two mechanisms do this without being asked (built 2026-09-10, Milestone 1):

- **Session start:** `~/.claude/hooks/findings-session-start.py` already
  printed this folder's newest findings + every universal one into context
  before this turn began. `(generated` — derived from FINDINGS.md fresh
  every session, never hand-kept`)`
- **Point of need:** `~/.claude/hooks/findings-point-of-need.py` prints a
  one-line notice the first time this session edits a file with a known
  finding attached. `(checked` — fires from the actual file, not memory`)`

If neither fired (a fresh project, or the hook didn't run) run by hand:
```
python "~/.claude/skills/spec/note.py" --recent <ABS project>
```
`(judgment` — the fallback; the two mechanisms above cover the common case`)`

**Known gap, named rather than hidden:** the point-of-need hook can only
connect a project's FINDINGS.md to code that shares its directory tree. A
project whose FINDINGS.md sits somewhere the code doesn't live under (this
skill's own folder is exactly this case) never gets the automatic notice —
run the `--recent` fallback there.

## Claim a lane

Before doing real work, claim this run's scope so a concurrent session
never collides with it:

```
python "~/.claude/skills/auto/lanes.py" claim --folder <ABS project> \
  --files "<one line: what this run touches>" --session <session_id>
```
`(checked` — mechanical write, one row per session, locked`)`. Deciding
*what to write* in `--files` is `(judgment)` — name the real scope, not
"everything" or "TBD".

`lanes.py read` shows every other live claim; if this run's scope genuinely
overlaps a row whose folder+files were touched in the last 24h, don't touch
that overlap — work the rest, name the overlap in the report. A row with no
overlap, or one that's aged out, is not your concern. Release happens
automatically at exit (see below) — never left for the user to notice.

## Write RUN.md — the one file this run owns

`./auto-runs/<slug>/RUN.md`, created once, updated as the run proceeds.
Schema (canonical copy lives in `check_exit.py`'s own docstring — this is
the same shape, not a second copy that can drift):

```
RUN -- <slug>

Goal: <one sentence, frozen from Phase 0>
Plan: <path to the plan file> (sha256: <hash computed right now>)

## Criteria
- [ ] <criterion text> | evidence:
- [x] <criterion text> | evidence: <pasted proof>

## Findings
<a note.py-shaped entry, or "no findings -- <reason>">

## Big Lesson
<ONE sentence -- or the literal line "none this run">

## Verdict
Status: RUNNING | DONE | STOPPED
```

**Big Lesson IS the `big_lesson:` field** — the global CLAUDE.md capture
rule already asks every finding to lead with one (the generalized principle
a FUTURE, DIFFERENT run would apply, as opposed to `change:`'s specific
measured fact). This section is not a second, separate thing that then
needs translating into that field — it's the same field, just given a home
in RUN.md before the run ends. When it's real, file it via `note.py` with
that exact sentence as the finding's `big_lesson:` line, verbatim, not
re-derived — that's what makes `spec_tool.py sync-findings` surface it as
its own sub-line in SPEC.md automatically.

**Not the same as Findings.** Findings is the granular list — every
specific thing learned, however small. Big Lesson is at most one sentence:
the ONE takeaway worth a future run changing its behavior over. Most runs'
honest answer is "none this run" — that's legal and expected, not a failure
to find something. `(judgment` — deciding whether anything rose to that
level`)`; the section's mere presence is `(checked` — C7 refuses a run with
no Big Lesson section, or a blank one`)`.

One criterion per success condition from Phase 0, plus one per any load-
bearing step whose failure would sink the goal. `(judgment` — deciding what
counts as a criterion`)`. Everything else about the file — the evidence
field, the findings section, the hash — is read back and enforced by
`check_exit.py` at exit `(checked)`.

The sibling `log.txt` is written by the PostToolUse hook
(`hooks/auto-log-hook.py`) automatically, for every state-changing tool call
in a session whose marker names this slug. `(generated)` — see "What
changed" for the fix that makes this reliable.

## Execute steps: one transient retry, else stop dead

This replaces the old skill's five-approach rotation loop. Per step:

```
1. Run it.
2. Pass -> mark the criterion met, paste the real evidence, move on.
3. Fail:
     - the failure looks TRANSIENT (a timeout, a lock held by another
       writer, a flaky network call) -> retry EXACTLY once, with one
       concrete thing different (a longer timeout, a re-read after the
       lock clears) -- never the identical command again.
     - anything else, OR the retry fails too -> STOP. Do not diagnose in a
       loop, do not rotate through five approaches. Write the Verdict as
       STOPPED, run the exit sequence below, report honestly.
```
`(judgment)` throughout — telling transient from structural is a real call,
and it is deliberately the ONLY retry budget in this design. A step that
needs more than one retry to pass is telling you something is actually
broken; find out what, don't paper over it with more attempts.

**Independent steps still run** even after one stops — a stopped step
blocks only what depends on it. Name every stopped step in the report,
with why.

## Evidence capture

Every criterion marked met needs its evidence field filled with the real
proof — a pasted command + exit code, a file listing, an actual number —
never "assumed", never blank. `(checked` — check_exit.py's C1/C2 refuse
both`)`.

**Visual surface (a browser, a GUI, a rendered frame):** the screenshot
must actually be READ — viewed, not just captured — before the criterion is
marked met. A passing exit code with an unread screenshot is not evidence;
a signed-out page can print a prompt box and exit 0 exactly like a signed-in
one. `(judgment)`

**A test/check passing is not evidence by itself — prove it can say NO.**
When a criterion's evidence is "a test passes" or "a check refuses X," paste
a **mutation test** alongside it: on a copy, take the fix or check back OUT,
re-run the same test, and confirm it now FAILS. A test nobody has watched
fail proves nothing — it would pass here whether or not the thing it's
supposed to catch is real. `(judgment` — deciding what to revert and how`)`,
but the proof itself is a pasted, verifiable result, same as any other
evidence field.

## Exit: check_exit.py, promote, release lane, report

Before printing ANY verdict:

```
1. python "~/.claude/skills/auto/check_exit.py" <ABS project> \
     <path to RUN.md> <session_id> --stamp
   Exit 0 -> continue. Exit 1 -> fix every named FAIL line, re-run. Do NOT
   print DONE or STOPPED until this returns 0.                    (checked)

2. python "~/.claude/skills/auto/promote.py" --dir <ABS project> \
     --path finish|blocker-stop --session <session_id>
   One routine, either exit path, idempotent -- regenerates SPEC.md's
   findings block from FINDINGS.md and releases this run's LANES.md row.
   (generated + checked)

3. Print the report (below).
```

**Named residual, not fixed:** nothing stops the model from skipping step 1
and just printing a verdict. Making that impossible needs a fail-closed Stop
hook — one was built and removed 2026-08-29 after three review rounds
returned a RISING 3→6→7 blockers (see FINDINGS.md). That history stands;
this rebuild did not re-attempt it without new evidence. `--stamp` (step 1)
is the compromise: it writes a content-hash file after a real pass, so a
skipped check is detectable after the fact even though it isn't prevented.
`(judgment)`

## The report — ONE template, always

No more separate DONE/PARTIAL/STUCK templates. The criteria checklist
already shows the state; the footer explains it.

```
=== AUTO REPORT ===

Goal:    <one sentence>
Status:  DONE | STOPPED

Criteria:
  [x] <criterion> -- <evidence, one line>
  [ ] <criterion> -- <why it's unmet, if STOPPED>

Findings this run: <n, or "none -- <reason>">
Lane released: <yes/no>
check_exit: <PASS -- stamped | the FAIL lines, if you are reporting despite
             a failure, which should not happen>

NET: <one sentence -- where things actually stand>

CURRENT STAGE
  Before:   <state before this run>
  Now:      <state right now>
  Changed:  <what changed and why>
  Next:     <the next milestone, or "none -- goal reached">

ULTIMATE GOAL (4 lenses, frozen per run)
  Delivers:   <the finished result with zero further input>
  Heals:      <how failures recover or surface themselves>
  Replaces:   <whose attention this deletes>
  Guarantees: <what wrongness is now impossible>

USER OPTION  (omit entirely if this turn has no real fork)
  Question: <the one decision, plain>
    1. <option>  (<cost>) -- +/- , Holds up: <survives next run? maintenance?>
    2. <option>  (<cost>) -- +/- , Holds up: ...   <- RECOMMENDED
  If you say nothing: <default>.  Why: <structural reason, not "faster">

SUGGESTED ACTION
  Paste this:     <answers this turn's actual question>
  Toward goal:    <this move -> concrete gain -> why the goal needs it>
  Heaven's net:   <why we can proceed with confidence -- on a pick: SEEN
                  evidence it stands on + what ruled the other option(s)
                  out (same evidence) + how we'd know fast if wrong and
                  the bounded fallback, unchecked things named, never
                  "n/a" on a pick. On a work step touching recovery
                  logic: class-keyed recovery, evidence-only detection,
                  bounded tries, fail-loud -- or "n/a -- no recovery
                  logic in this step">
  Feynman:        <the choice in kid words, one everyday analogy, zero
                  jargon, four beats: why this move won, how it pushes
                  toward the finish line (plain-words version of
                  "Toward goal", said outright), what we passed on
                  instead, what happens if it turns out wrong. "n/a --
                  <why>" only when there's no action (goal reached)>
  Confidence/Risk: <PERFECT|HIGH|MEDIUM|LOW -- <what's verified vs assumed>>
```

`(judgment)` for the prose fields; the Criteria block and `check_exit:` line
are copied straight from RUN.md and check_exit.py's own output — never
re-typed, never summarized into something check_exit didn't say.

**Added 2026-09-11.** `Heaven's net` and `Feynman` were absent from this
block — a leftover from when it reported once per guardian tick and stayed
terse on purpose. The guardian cron is gone (see "What changed" below); this
report now fires once per checkpoint/exit, the same shape as `/explain` and
`/spec`'s `SUGGESTED ACTION`, so the reason to skip them no longer holds.
Same rules as those two skills: `Heaven's net` never reads "n/a" on a pick,
and `Feynman` must state the goal-connection outright as its own beat, not
leave it implied by the `Toward goal` line above it.

## Sub-agent fan-out (unchanged, kept minimal)

Same-check-over-N-independent-items (N ≳ 5): dispatch one sub-agent per
item or small batch, cap concurrency ~8-12, each returns `pass` or
`fail + reason` only — never raw output. A missing or hung verdict is a
`fail`, never silently dropped. `(judgment` — the "~5" threshold is
inherited from the original design with no fresh measurement behind it,
kept as a judgment call rather than re-litigated`)`.

## What changed (2026-09-10 rebuild — for anyone expecting the old shape)

```
GONE   GUARDIAN.txt / REVIEW.txt / guardian.md / review.md -- the session-
       lifetime cron and the per-function reviewer. Both were switches
       flipped off 2026-08-30 with the reasoning already on record (three
       review rounds returning a RISING blocker count on one section); this
       rebuild made the "off" state permanent instead of a switch nobody
       remembers is there.
GONE   GOAL.md, BOARD.md, notes.md, APPROACHES.md, DIGEST.md, PROGRESS.md,
       runbook.txt/RUNBOOK.md -- eight files, replaced by RUN.md + log.txt.
GONE   auto-stop-block.py -- never registered in settings.json; removed
       rather than wired, per the same "don't rebuild an enforcement layer
       without new evidence" reasoning above.
GONE   The three separate DONE/PARTIAL/STUCK report templates -- one
       template now; the criteria checklist carries the state.
NEW    note.py `scope: universal` tagging + the two findings hooks
       (Milestone 1); check_exit.py + promote.py (Milestone 2); lanes.py
       (Milestone 3) -- all four are what this file's phases above call.
FIXED  hooks/auto-log-hook.py's legacy fallback (it appended a live
       session's tool calls into a run folder that had closed 11 days
       earlier -- 50,837 bytes of contamination, found by `ls -la`, not by
       reading code). No session marker now means no log line, full stop.
```

Full rebuild record: `Skills/SPEC.md` Change Log, entries dated 2026-09-10.
Prep plan + evidence base: `Skills/prep-auto-rebuild.txt`.
