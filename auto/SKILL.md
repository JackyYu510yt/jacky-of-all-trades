---
name: auto
description: Universal autonomous mode. The user runs `/auto` (or says "go autonomous", "no gates", "just do it", "set and forget", "keep going until it's done") to authorize Claude to drive a task end-to-end without further prompts. The invocation IS the authorization — there is no follow-up confirmation gate. Claude states briefly what it's about to do, then executes, diagnosing and re-trying as needed, stopping only on genuine success (DONE) or genuine stuck (STUCK). Applies to any task — a single fix, a multi-step build, a long unattended job — not just pipelines. Any run that would pause unfinished arms a session-lifetime Goal-Guardian cron that keeps pushing toward a pinned contract (success + circumstances + never-do) until DONE or genuinely user-blocked — PARTIAL is a checkpoint, never an ending (see "Goal-Guardian" section). For long unattended jobs the cron+monitor architecture (Pattern 3) rides under the guardian.
---

# Auto

Universal autonomous mode. The user invokes `/auto` to hand Claude a task; Claude executes it end-to-end with no further confirmations.


## Installation (one-time, per machine)

The `/auto` skill ships with a hook script — `hooks/auto-log-hook.py` — that auto-appends every state-changing tool call to `./auto-runs/<slug>/log.txt` (or `./auto-runs/<slug>/logs/run.log` for Pattern 3) when an active /auto run is detected. Without this hook, log appending falls back to model discipline and gets unreliable on long runs.

To wire it up on a fresh install (or new PC), add this block to your `~/.claude/settings.json` under `hooks` (merge with existing hooks if any):

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python \"<HOME>/.claude/skills/auto/hooks/auto-log-hook.py\""
          }
        ]
      }
    ]
  }
}
```

Replace `<HOME>` with your actual home path:

```
Windows  →  C:/Users/<your-username>
macOS    →  /Users/<your-username>
Linux    →  /home/<your-username>
```

Empty `"matcher": ""` means "fire on every tool call" — the hook itself filters down to state-changing tools (Bash, Edit, Write, NotebookEdit, PowerShell). Read-only tools (Read, Glob, Grep, etc.) are skipped at the hook level so the log stays focused.

**Verification:** after wiring, run `/auto` on a small task in any folder. After it generates the runbook, check the matching `./auto-runs/<slug>/log.txt` — every tool call should appear as a one-line `[timestamp] [tool] <summary>` entry without the model having to remember to write them.

The invocation **is** the authorization. There is no Phase-0-confirm-the-plan gate. There are no "should I proceed?" checkpoints. There are no "want me to run X to verify Y?" offers. Claude states what it's about to do in one or two sentences, then does it, and reports back when DONE or STUCK.

## When to Use This Skill

- User says `/auto`, "go autonomous", "no gates", "just do it", "stop asking, just run it", "set and forget", "keep going until it's done", "while I sleep", "run the whole thing"

- User has expressed frustration at being asked for permission

- User has stated an end goal that requires multi-step execution and explicitly does not want to babysit

- ANY task the user has handed to Claude with the implicit understanding "you drive"

This skill is a **mode**, not a tool. It modulates how Claude executes any work, not what work to do.


## Phase −1 — Tool Preload (mandatory, before any other action)

Before Phase 0, before plan ingestion, before any tool call other than this one:

**Run `ToolSearch` with `select:Monitor,CronCreate,CronList,CronDelete` to load these tool schemas.**

These tools are mandatory for autonomous work and are NOT loaded by default. Skipping this step means:

- Long-running shell jobs only notify on exit — a 3-minute crash isn't seen until the 15-minute background-job timeout

- No way to schedule retries or periodic checkins for unattended jobs

- `/auto` degrades to "shell with extra confidence" — no live failure detection, no self-healing

**Every time you launch a long-running shell job in the background, immediately arm a `Monitor` on its log/output.** The filter MUST cover BOTH success markers AND failure signatures (`Traceback|Error|Killed|FAILED|OOM|assert` plus domain-specific completion markers like `[DONE]`, `Successful:`). Silence ≠ success — a filter that matches only the happy path makes a crash look identical to "still running."

**Every Monitor wait needs a deadline.** A hang produces neither a success marker nor a failure signature — so a filter watching only for those two waits forever on a wedged job (a stalled ffmpeg encode, a frozen download). Set a max wait of ~2× the step's expected duration; on expiry, treat the job as **STALLED** (not done, not failed) and escalate per heuristic #13 (cheapest action first — probe the artifact layer, then kill+retry, never silent wait). For tool-specific jobs, add that tool's real failure strings to the filter (e.g. ffmpeg: `Conversion failed|Invalid data|No space left`), and lean on exit code + artifact checks as the primary oracle rather than log-string matching alone. On a STALLED verdict for a job with a visual surface, capture + read a visual checkpoint BEFORE the kill/retry (see Visual Checkpoints) — see the stall, don't just infer it. And when the deadline has been shortened to a checkpoint interval, an expiry means "look now," not STALLED — the ~2× stall clock accrues across re-arms.

**Use `CronCreate`** for scheduled retries, periodic state checks, deferred re-runs, or any "check back later" pattern that would otherwise require the user to remember.

This phase has NO output to the user. Load the tools, then continue to Phase 0.


## Phase 0 — Plan Ingestion + Activation Gate (mandatory first action)

Before anything else, /auto must lock in the end goal and at least one observable success condition. If it can't, /auto refuses to activate.

### Step 1 — Scan for an existing plan

/auto NEVER picks up another run's runbook or `auto-runs/*/GOAL.md` from disk. A new invocation always means a new slug and a new runbook. The one exception is explicit resumption (see Resumability below).

Glob the working directory for **input plans only** (not state from prior or parallel /auto runs):

```
1. Explicit blueprint pointer in the invocation (/auto <path>/SPEC.md)
2. ./prep-*.txt             (output of /prep — most recently modified wins)
3. ./PLAN.md                (manual plan)
4. ./SPEC.md                (ONLY when BOUND — a pointer, a chained /spec, or
                             your direction; never by mere presence. See
                             "Phase Blueprint Mode" below)
5. ./.claude/plans/*.md     (older /prep outputs)
6. User's invocation message + recent context
```

A `SPEC.md` with a `## Phases` blueprint is a plan source ONLY when /auto is
**bound** to it per the binding rule in **Phase Blueprint Mode** below (explicit
pointer, a chained `/spec`, or your direction). A SPEC.md merely sitting in the
working directory does NOT make it a source — and a SPEC.md with NO `## Phases`
section is never an execution plan. In both cases /auto falls through to the
rest of the list and runs as normal.

Existing `./auto-runs/*/runbook.txt`, `./auto-runs/*/RUNBOOK.md`, and `./auto-runs/*/GOAL.md` files are state from prior or parallel /auto runs and are deliberately ignored here. This is what makes parallel chats in the same directory safe — each gets its own slug and its own runbook with no glob-based crosstalk.

### Step 1.5 — If no plan exists AND task is non-trivial, invoke /prep autonomously

Before falling back to deriving from the invocation alone, check whether the task is non-trivial (>3 implied steps OR involves building new code OR involves design choices the invocation doesn't pin down). If yes:

```
1. State the handoff in one line:
   [auto] No plan found. Invoking /prep in autonomous mode to
          generate one before runbook generation.

2. Invoke /prep with the autonomous-mode trigger active. /prep:
   - Derives the four conditions (goal / workflow / testing / success)
     from invocation + context
   - Skips all interactive gates (Phase 1 questions, Phase 4
     iteration, Phase 5 interviews, Phase 8 per-function approval)
   - Logs every derivation in the plan's ASSUMPTIONS & FORKS card
   - Writes ./prep-<slug>.txt to CWD

3. Wait for the plan file to land. Read it. Treat its conditions
   as FROZEN (per Phase 0 normal rules).

4. If autonomous /prep emitted a "could not derive" partial plan,
   surface that to the user and halt — same as the activation
   gate failure path.
```

For trivial tasks (1-2 atomic steps, e.g. "rename `userId` to `user_id` across these 3 files"), skip the /prep handoff and derive conditions directly from the invocation.

### Step 2 — Extract conditions

Read the first match (or the just-generated /prep file). Extract:

- **End goal** — one observable sentence
- **Success conditions** — specific, checkable bar (a command exits 0, a file exists at a path with a size threshold, a test passes, a metric clears a numeric threshold)
- (Bonus, if present) testing conditions, workflow conditions, step list with verify checks

If a plan exists, goals and conditions are **frozen**. Do NOT ask the user to confirm them. Do NOT re-derive them. Use them.

### Step 3 — Activation Gate

Both of these must hold before any execution:

```
[ ] End goal stated in one observable sentence
[ ] At least one success condition is checkable
    (exit code, file existence + size, test pass, metric threshold,
     visible artifact — not "looks right" or "should work")
```

**The Success line must name the USER'S result, not machinery (P12).** "The retry
loop works" / "the fix is merged" are sub-goals the run can pass while the user's
actual outcome ("the correct thumbnail exists in the VA folder") stays unmet —
that's goal substitution, and it produces truthful-but-false DONE reports. Write
the Success line as the user-visible deliverable; machinery milestones belong in
steps, never in the Success line.

**If both clear** → state them in one line and proceed:

```
[auto] Goal: <one sentence>. Success = <observable check>. Proceeding.
```

**If either fails** → /auto REFUSES TO ACTIVATE. Print:

```
[auto] Cannot activate — missing:
  - <end goal>            (or: <success conditions>)

Run /prep first to nail these down, OR restate /auto with both in
one sentence. Example:

  /auto fix the off-by-one in paginate() — done when
  test_paginate.py passes AND existing suite green.

No execution will occur. Awaiting your input.
```

This is the ONE place /auto pauses before doing real work. The authorization rule still holds — the user authorized execution by invoking, but they did not authorize working blind. Without observable criteria, "done" is opinion, not observation (P2 + P8).

Once the gate clears, the rule is permanent for the rest of the run: no further pauses except the Hard Invariant trips and STUCK.


## Phase Blueprint Mode — follow a /spec blueprint when one is bound

A `SPEC.md` produced by `/spec` can carry a `## Phases` **blueprint**: an ordered
plan nested in three zoom levels — **PHASE ▸ MILESTONE ▸ STEP**:

```
PHASE      a milestone-sized goal with REQUIRES / VERIFY-REQUIRES / PRODUCES / DONE-WHEN
  MILESTONE  a waypoint inside a phase with its own DONE-WHEN (optional layer — only on big phases)
    STEP       a single action (the flexible doing)
```

(`MILESTONE` is the blueprint's middle layer — distinct from build **stage-mode**'s
`stages/stage_N.py` file layout; they don't interact.) When /auto is bound to a
blueprint, it follows it instead of deriving its own step list — the blueprint
pins *where* each checkpoint is; /auto still owns *how* to reach it (it
improvises the route between checkpoints; `STEP`s are guidance, not a script).

### Binding — exactly one blueprint, never a scan

/auto runs the ONE blueprint it is bound to. It does not hunt across multiple
SPEC.md / blueprint files and pick one.

Binding requires a POSITIVE signal — the mere presence of a `SPEC.md` in the
working directory does NOT bind. /auto binds only when one of these holds:

```
1. Explicit pointer   — invocation names a file (/auto <path>/SPEC.md) → use it.
2. /spec chained      — /spec is invoked alongside /auto (e.g. `/auto /spec`,
                         or /spec is the active spec lane this session) → bind
                         to that spec's `## Phases` blueprint.
3. You direct it       — the user references the spec/blueprint as what to run,
                         or it's the blueprint we've actively been working in
                         this session → bind to it.
4. None of the above   → run as NORMAL /auto, even if a `## Phases` SPEC.md is
                         sitting in the folder. Presence is not a clue. Derive
                         the runbook from the other plan sources / invocation.
                         Nothing changes from today's behavior.
5. Ambiguous signal    — an explicit pointer that doesn't resolve, OR a genuine
                         in-play signal pointing at several candidate blueprints
                         → HALT and ask which one. Never guess; never blend two.
```

The bias is conservative: when in doubt whether a SPEC.md was meant for this
run, treat it as NOT bound and run normal autopilot — binding is opt-in via a
pointer, a chained /spec, or your direction, not automatic discovery.

Binding is a Phase-0 concern — resolve it before runbook generation. Once bound,
the chosen blueprint's path is frozen for the run alongside the slug.

### Blueprint → runbook

Each phase becomes a runbook step cluster. Carry the phase's fields onto it
verbatim — do NOT re-derive them:

```
Cluster for Phase N:
  pre-verify: <the phase's VERIFY-REQUIRES check>   (gate before any work runs)
  action:     <the phase's STEPS>                   (guidance — may improvise)
  verify:     <the phase's DONE-WHEN check>         (the checkpoint)
```

When a phase has the **milestone layer**, each milestone becomes its own
sub-step with its own `DONE-WHEN` checkpoint, run in order between the phase's
pre-verify and the phase's final `DONE-WHEN`. This is what makes a failure
narrow to one waypoint: phase red → the milestone whose checkpoint failed → its
steps.

The blueprint's `DONE-WHEN`s and `VERIFY-REQUIRES` are the verify checks — they
were already vetted by /spec's quality bar (and /audit if it ran), so the
self-derived verify sanity pass is not needed for blueprint-sourced steps. But
when the blueprint did NOT route through /audit, the Phase 0.5 pre-flight
principles pass (see "Self-derived runbooks" there) still runs on it — the
quality bar vets checkability, not principles.

**Assumptions & Unknowns → early probes.** When the bound SPEC.md carries an
`Assumptions & Unknowns` section (see /spec — one unproven belief + its
cheapest probe per line), schedule each **load-bearing** assumption's probe as
an EARLY runbook step, before the phases that stand on that assumption; the
step's verify is the probe's expected fact. A wrong assumption then dies on
minute one, not at hour three of the run. A probe that DISPROVES its assumption
is a failed foundation, not a fix-mode bug: branch like a failed pre-verify —
an earlier phase can establish the real condition → STUCK naming it; the
assumption was externally supplied → stop and surface the recipe. Assumptions
whose probe no phase depends on may run in any order (KISS — don't front-load
what nothing stands on).

### Per-phase loop — verify the foundation BEFORE the work

For each phase in order:

```
1. Run VERIFY-REQUIRES (the readiness gate).
     PASS → go to step 2.
     FAIL → identify WHICH `REQUIRES` condition the gate actually failed on
            (when a phase lists several, with mixed tags), then branch on THAT
            line's SOURCE TAG:
        ← from Phase X  → STUCK. A phase that should have produced this
                          under-delivered. Do NOT fake the condition, do NOT
                          test on a missing foundation. Report which phase.
        ← external      → STOP and surface the how-to-get-it recipe to the
                          user ("Missing <condition>. To get it: <recipe>.
                          Supply it, then resume."). This is a Phase-0-style
                          activation stop, not a STUCK — the run resumes once
                          the external condition is supplied. (One of the few
                          places /auto pauses; it pauses because it CANNOT
                          manufacture the condition, per Probe-don't-assume.)
2. Run the work, improvising the route as needed (fix mode on sub-failures):
     - flat phase  → run STEPS.
     - milestone'd → for each MILESTONE in order: run its STEPS, then check its
                     DONE-WHEN. A milestone whose DONE-WHEN fails localizes the
                     break to that waypoint → fix mode there before advancing.
3. Run the phase DONE-WHEN (the final checkpoint).
     PASS → mark PRODUCES satisfied, advance to the next phase.
     FAIL → fix mode / approach rotation on this phase, up to the 5-approach
            bound, then PARK or STUCK as usual.
```

The "stop on a missing external condition" branch is the blueprint form of the
Phase 0 activation gate — /auto does not work blind on a foundation it can't
build. Everything else (rotation, parking, the refuter gate, honest reporting)
works exactly as in NORMAL mode.


## Phase 0.5 — Generate the Runbook (mandatory before execution)

After the activation gate clears, /auto writes a runbook file BEFORE any step runs. The runbook is the contract /auto follows — every step lists the action and the observable check that means "step done." /auto executes the runbook deterministically, only entering "fix mode" (diagnose + rotate) when a step's verify check fails.

### Everything lives under `./auto-runs/<slug>/`

**All of /auto's own artifacts for a run live inside one per-run folder: `./auto-runs/<slug>/`.** The working directory only ever gains a single visible `auto-runs/` folder no matter how many /auto runs happen there — runbook, log, notes, and (Pattern 3) the full state set all nest inside the slug subfolder. This keeps the user's working directory clean instead of scattering loose `auto-*` files alongside their own code. The only marker outside a slug folder is `./auto-runs/.session-<session_id>` at the root (see Session marker).

Create the folder (`mkdir -p ./auto-runs/<slug>/`) before writing the first artifact. Artifacts the user's own scripts/build produce (logs, backups, caches) are NOT /auto's to relocate — this folder is for /auto's bookkeeping only.

### Slug derivation

Every /auto run gets a **slug** — a short identifier suffixed onto the runbook file, the log file, and (for Pattern 3) the state folder. The slug uniquely identifies ONE /auto run for the rest of that run's life. Two parallel chats in the same directory must never resolve to the same slug.

Slug shape: `<keywords>-<HHMMSS>` where `<keywords>` is 2-4 lowercase hyphenated words derived from the task, and `<HHMMSS>` is the local time at Phase 0 to second precision.

Keyword source priority:

1. If the plan came from `./prep-<keywords>.txt`, **reuse those keywords** (e.g., `prep-stagger-distribution.txt` → keywords = `stagger-distribution`).
2. Otherwise, derive from the goal sentence — pick 2-4 keywords, lowercase, hyphenate.

The `-HHMMSS` suffix is appended in both cases. Two parallel chats can legitimately derive the same keywords from the same prep file or a similar goal — the timestamp is what guarantees their slugs differ.

Examples:

- Goal "Fix the off-by-one in paginate()" at 14:32:05 → slug `paginate-off-by-one-143205`
  - Files: `./auto-runs/paginate-off-by-one-143205/runbook.txt`, `./auto-runs/paginate-off-by-one-143205/log.txt`
- Goal "Build the staggered distribution system" at 02:18:44 → slug `stagger-distribution-021844`
  - Pattern 3 folder: `./auto-runs/stagger-distribution-021844/`

Once chosen at Phase 0, the slug is **frozen for the run** — no renames mid-run, and a new /auto invocation never adopts a prior run's slug by reading it off disk. Resumption of an interrupted run is explicit-only (see Resumability below).

### Session marker

Right after the slug is frozen and before the runbook is written, /auto creates the `auto-runs/` root (if absent) and writes a session-marker file at its root — NOT inside the per-run slug folder, because the hook reads the marker to *learn* the slug and can't look inside a folder it can't yet name:

```
./auto-runs/.session-<session_id>
```

The file contains the slug as its single line of content. `<session_id>` is the claude code session ID available in the conversation environment (the same value the harness passes to PostToolUse hooks).

The PostToolUse hook (`hooks/auto-log-hook.py`) reads this marker on every tool call. If a marker for the firing session exists, the hook routes the log line to that session's slug-specific log file. Without the marker, two parallel chats in the same directory writing to `auto-runs/*/log.txt` would race for the "most recently modified" runbook and trample each other's logs. With the marker, each session's tool calls flow only to its own log.

On a terminal verdict (DONE / STUCK-user / STUCK (stopped by user)), /auto deletes its session marker as part of the final report step — but ONLY if the marker's content names this run's slug; if it names another coexisting run's slug, leave it and log one line (Goal-Guardian rule). If the chat closes mid-run without a terminal verdict, the marker file is harmless leftover — the next /auto run will overwrite it (same session) or ignore it (different session).

### Contract + Guardian (universal)

Right after the slug is frozen, /auto pins the run's **contract** (Goal / Success / Circumstances / Never-do / Validation / False-pass / Run-start) into `./auto-runs/<slug>/GOAL.md`, and creates `APPROACHES.md` + `PROGRESS.md` for EVERY run, any pattern. The Goal-Guardian cron arms LAZILY — at the first moment the run would end a turn non-terminal. Full rules, tick protocol, checkpoint-writer, and terminals live in the **Goal-Guardian** section below; that section is canonical.

### Runbook file location

```
./auto-runs/<slug>/runbook.txt   Patterns 1 & 2 (inline / background+monitor)
./auto-runs/<slug>/RUNBOOK.md    Pattern 3 (cron+monitor+shell — lives with state files)
```

### Runbook format

```
RUNBOOK — <slug>

Goal:    <one observable sentence>
Success: <checkable bar — what makes the whole task DONE>
Pattern: <1 synchronous | 2 background+monitor | 3 cron+monitor+shell>
Mode:    NORMAL | DIAGNOSING | ROTATING

Functions:  (any run that writes/rewrites a def — labeled by the author checklist; see Function-author sub-agent + FnReview)
  <name>: AUTHOR | INLINE — <one-line reason naming the deciding checklist line> | review: <FnReview stamp — see FnReview stamp vocabulary>

Steps:
  1. [PENDING] <action one-liner>
        requires:   <precondition + source tag: ← from step X | ← external: recipe>  (optional)
        pre-verify: <yes/no check the requires hold — run BEFORE the action>          (optional)
        verify: <observable check the step is done>
        rollback: <undo if step later breaks — optional>

  2. [PENDING] <action one-liner>
        verify: <observable check>

  ...

  N. [PENDING] <action one-liner>
        verify: <observable check>

Status:
  Current step:      1
  Approaches tried:  0   (resets each step)
  Parked steps:      []
  Mode reason:       (filled when Mode != NORMAL)
  Refuter:           n/a   (judgment-based goals: pending | clean | <n> BLOCKERs | round 1|2)
  RedTeam:           n/a   (fires on deliverable NATURE or ≥1 guardian tick: pending | clean | <n> BREAKS | round 1|2)
  Classified:        n/a   (build tasks: pending | clean | checklist-only)
  Principles:        n/a   (code deliverables: pending @<ISO> | clean @<ISO> | unswept @<ISO> (<reason>) | <n> violations)
  FnReview:          n/a   (function-writing runs: <k> pending | <n> in fix | clean | <n> open | <m> unreviewed — see FnReview)
  Guardian:          unarmed | armed <cron-id>, every N min, expires <date> | stood-down (<reason>)
  Contract:          pinned <date> | pinned+asked
  Round:             0/3   (guardian re-attack rounds used)
  Jobs:              []    (live background jobs: id/PID + artifact path + expected duration)
  Reviewer:          n/a | pending | <last verdict>
  Turn-end rule:     checkpoint = Status: PARTIAL (checkpoint); STUCK only when user-blocked
```

`Refuter` rides in the runbook (the file the Stop hook reads) — not just in prose — so the "refute before DONE" rule survives context compaction. On a judgment-based goal it starts `pending` and the terminal `Status: DONE` MUST NOT be written until it reads `clean`. On a machine-checked goal it stays `n/a` (the verify check is the oracle; see Terminal Refuter Gate) — unless a FnReview `open` line or a fix-trigger `unreviewed` stamp forces the refuter, then `n/a → pending` (see FnReview). `RedTeam` rides the same way for the RED-TEAM rider: on an unattended / stateful deliverable it starts `pending` — regardless of whether the goal is machine-checked — and `Status: DONE` MUST NOT be written until it reads `clean`; on an attended one-shot it stays `n/a` (see RED-TEAM rider under Terminal Refuter Gate). `Principles:` rides the same way for code deliverables — the principles-sweep (Goal-Guardian section) stamps it mid-run; only its appended violation STEPS gate DONE (via all-steps-verified), never the field itself.

### Per-step lifecycle

Each transition is written back to the runbook file:

```
PENDING → IN PROGRESS → DONE          (verify passed → next step)
PENDING → IN PROGRESS → BLOCKED       (verify failed → fix mode)
BLOCKED → IN PROGRESS → DONE          (rotation succeeded → NORMAL)
BLOCKED → PARKED                      (5 approaches failed → continue
                                       on independent steps)

FnReview steps (see FnReview — per-function completeness review):
IN PROGRESS → VERIFIED (FnReview pending) → DONE   (review clean; a step with a
                                                    pending FnReview is NOT DONE)
VERIFIED    → BLOCKED                               (finding → fix mode on the
                                                    PRODUCING step)
BLOCKED     → PARKED (FnReview round 2 still open — finding quoted)
PENDING     → PARKED (dependent of step N FnReview PARK)
```

### Fix mode — only entered on a verify failure

Fix mode is the ONLY time /auto deviates from the runbook. When a step's verify fails:

```
1. Mode → DIAGNOSING — read the failure signature, then run the P11 debug
   loop (standard: /principles P11 "Pin the cause before the fix"; full
   procedure: /repair — pointer, not a copy): log the known FACTS, then
   ≥2 ranked falsifiable hypotheses — OR one explicit fast-path
   declaration when the cause is genuinely one-read obvious (typo,
   missing import). No hypothesis list and no fast-path line in the log
   → rotation may NOT start.
2. Mode → ROTATING   — pick the approach targeting the LEADING hypothesis
   (Approach Rotation Rules). Before applying any edit, pre-register ONE
   cheapest one-variable probe in the log — variable / expected /
   CONFIRMS / DISPROVES — run it, and interpret against those written
   predictions. Probe disproves the leader → re-rank survivors and probe
   the next; NEVER edit on a disproved or untested cause (fast path
   exempt).
3. Restore the precondition (Re-entry hygiene), then apply + re-run the step
4. Verify pass → (if this fix mode was opened by a FnReview finding: log
   `aim-test:` FIRST — a `no` = failed approach, stay ROTATING, no dispatch)
   → Mode → NORMAL; if the step edited a def (fix mode IS FnReview's
   fix-trigger): on a /prep-derived runbook where an AUDIT step follows, stay
   suppressed — the review fires at AUDIT (never at a redone Implement/REAL);
   otherwise step → VERIFIED (FnReview pending) — DONE only when the review
   returns clean. No def edited → mark DONE, advance
5. 5 fails       → Mode → NORMAL, step PARKED, advance to next
                   independent step (Park, don't halt)
```

In NORMAL mode, /auto follows the runbook step by step without diagnosis or rotation. The runbook IS the path; the loop just walks it.

### Re-entry hygiene — restore the precondition before any retry

Every recovery path is a **re-entry over partial state**: the prior attempt may have half-written a file, mutated a row, or left a downstream step standing on output that's about to change. The happy path only moves forward through clean states; recovery paths move *backward into* a step that already ran. Before re-attempting a step at any of the re-entry points below, restore its starting condition first — never retry on top of the last attempt's residue.

The re-entry points:

```
1. Approach rotation   — a verify failed; a different approach on the same step
2. Resume / cron tick  — a tick died; the next picks up a step left IN PROGRESS
                         (a step left VERIFIED — FnReview pending — is NOT restored:
                          hash matches its pending stamp → resume at the dispatch;
                          hash differs → it drops to IN PROGRESS and this door applies)
3. Refuter re-open     — a BLOCKER re-opens a step already marked DONE
4. Guardian un-park    — tick step 8 re-attacks a PARKED step (Goal-Guardian)
5. FnReview finding    — a VIOLATION / BAND-AID re-opens the PRODUCING step of a
                         function whose verify passed (see FnReview)
```

At door 3 the refuter names an unmet **Success-line item / failed verify**, not a step — so first **map that item to the step(s) that produced it**, then apply the restore below to each.

The restore, in order, before the retry runs:

```
a. Run the step's `rollback:` action if it has one (undo partial effects —
   delete the half-written artifact, revert the partial edit, reset the row).
   No rollback field + a non-idempotent action → probe the artifact layer
   (heuristic #8) for what the dead/partial attempt left, and clear it before
   retrying. If the residue can't be safely identified and cleared, the step
   goes BLOCKED — never retried blind (HI #10: don't guess).
b. Re-assert the step's `pre-verify` (precondition true again) BEFORE the
   action — identical to the first-run gate. A precondition an earlier step
   produced may have been invalidated by the failure; re-check, don't assume.
c. Invalidate downstream — but only on a real change. After restore+redo, if
   this step's output differs (checksum / size) from what a later step consumed,
   every such later step goes DONE → PENDING; if the output is byte-identical
   they stay DONE (HI #4 — don't burn budget re-running on an unchanged
   foundation). "Consumed" = a later step whose `requires:` names this step, or
   (tags absent — the common case) a later DONE step that read a file this step
   wrote (detect via the heuristic #8 artifact probe).
```

This is the missing wiring for the runbook's `rollback:` field (defined in the runbook format, invoked here). KISS (P5): an idempotent step **with no dependents** that overwrites (not appends to) its own output needs only (b); (a) and (c) fire only when a partial attempt could have left residue or fed a downstream consumer. A trivial Pattern-1 step with no artifact and no dependents has nothing to restore — the rule no-ops.

_(Added 2026-06-30 — closes the orphaned-`rollback:` gap: the field was defined in the runbook schema but invoked at no recovery door, so rotation / resume / refuter re-entry could run on a prior attempt's partial state. Independent /audit review applied.)_

### Resumability

Resumption is **explicit-only** — /auto never auto-resumes a prior run by globbing for runbooks. The slug must be supplied by the invocation itself. Two ways this happens:

```
1. Guardian tick — the cron prompt is pinned verbatim:
   "/auto guardian slug=<slug> run=<absolute run-folder path>".
   Each tick reads ONLY the runbook matching that exact slug and
   follows the Goal-Guardian tick protocol.

2. User-initiated resume — the user types
   "/auto resume <slug>" to manually pick up a prior interrupted run
   (e.g., after a session close killed the crons).

3. Kill switch — the user types "/auto stop slug=<slug>": CronDelete
   + honest STOPPED report (ledger + resume command) + Status: STUCK
   (stopped by user) + session marker deleted if it names this slug.
```

On resume, the runbook file is the source of truth:

```
1. Read ./auto-runs/<slug>/runbook.txt (or ./auto-runs/<slug>/RUNBOOK.md)
2. Find the first step that is not DONE and not PARKED
3. IN PROGRESS → restore that step's precondition (Re-entry hygiene), then resume from it
   VERIFIED (FnReview pending) → no restore: hash-check vs the pending stamp, then
   re-dispatch the FnReview (see FnReview "Resume / tick pickup")
```

If no slug is supplied, /auto generates a fresh one and starts a new run — parallel chats and accidental re-invocations never collide on someone else's state.

This is what makes Pattern 3 (cron mode) survive a chat going silent — the cron schedule carries the slug, and the heartbeat keeps reading the exact runbook it owns. (Silent = idle. A CLOSED window kills the session's crons — see Goal-Guardian's session-lifetime honesty; resume then is explicit via `/auto resume slug=<slug>`.)

### Generating the runbook — sources in priority order

```
1. ./prep-*.txt           — convert /prep's function list into runbook
                              steps; one runbook step per cycle phase
                              (Red / Green / Real / Audit per RISKY
                              function; Green + smoke per SAFE function)

2. ./auto-runs/*/RUNBOOK.md    — prior runbook from a resumed cron-mode auto
   ./auto-runs/*/runbook.txt      (resume in place; pick most-recently-modified
                              if multiple exist; do NOT regenerate)

3. ./PLAN.md              — manual plan with explicit steps

4. The user's invocation  — derive 3-10 atomic, verifiable steps from
                              the goal + success conditions
```

Steps must be **atomic and verifiable**. "Implement the feature" is the GOAL, not a step. "Write feature_X.py with function `foo(bar) -> baz`" with verify "`python -c 'from feature_X import foo'` exits 0" is a step.

If a step's verify can't be expressed as an observable check, the step is not atomic enough — split it.

**Self-derived runbooks (source 4) get a verify-check sanity pass.** When the runbook came from a /prep file (source 1), its verify checks were already vetted by /prep's auditor. When /auto wrote the checks itself from the user's one-liner, nothing vetted them — and the Terminal Refuter Gate is *skipped* for machine-checked goals (barring the FnReview carve-outs), so a weak check is the last line of defense and there's no net under it. Before executing a self-derived runbook, run one cheap sanity pass (a fresh sub-agent, no artifacts yet): hand it the Goal + Success line + the proposed verify checks and ask *"could any of these checks pass while the goal is still unmet?"* (the P1 test-at-scale failure — `import foo` that never calls `foo`, asserts a file exists but not its content, greps a string the script prints unconditionally). Any "yes" → tighten that check before running. The same sub-agent, in the same dispatch, also grades the PLAN against the principles-sweep's fixed 5-item checklist (Heaven's Net / evidence-only / re-entry hygiene / no silenced failures / KISS — see Principles-sweep under Goal-Guardian): a planned step that bakes in a symptom-keyed handler, an assumed signal, or a retry with no rollback gets revised before execution, exactly like a weak verify check. This pre-flight principles pass ALSO runs on a bound blueprint that did not route through /audit (the /spec quality bar vets checkability, not principles); plans from /prep (source 1) skip it — /prep's Phase 7 AUDITOR already graded the plan. For EVERY self-derived check, record the answer as a named **false-pass trap** on its runbook step — one line, `false-pass: <what a passing check would look like while the goal is still unmet>` — the pre-registered "DISPROVES" half of the check (P11): naming the trap before any result exists is what turns the sanity question from rhetorical into checkable. At verify time, a result matching the trap's shape is FAIL, not PASS. This only fires on the bare path that lacks /prep's vetting.

**Freeze the self-derived Success line.** A Success line from /prep is frozen (line 137). A self-derived Success line gets the **same** freeze: once written to the runbook it is never re-derived or edited mid-run — only the steps beneath it change. This stops "done" from quietly redefining itself toward whatever was achieved after a compaction.

### Condition-first runbooks — name the testing conditions, set them up first

A self-derived runbook (sources 3–4) gets the same condition discipline a /spec blueprint carries — this is the front half a bare step list usually omits, and the gap that lets /auto test on a broken foundation (the logged-out-account confusion). When generating the runbook for a non-trivial task:

1. **Name the preconditions first.** Before listing actions, ask what must already be true for the task to be testable — the *testing conditions* (a live logged-in account, seeded data, a reachable service, a built artifact). Tag each with its source: `← from step X` (an earlier step produces it) or `← external: <how to obtain it>` (a human / a dropped-in file / another system supplies it).

2. **Make establishing each condition its own early step** — never fold "log in an account" into the step that tests the login. Setup is its own step, with its own verify (the condition is now true). And the step **establishes** the condition on whatever input it's given — it never satisfies a precondition by picking only inputs that already have it (already-logged-in, already-warm, already-built); that's the band-aid shape HI #14 forbids, and it fails the moment the pre-qualified pool runs dry.

3. **Gate each dependent step on a `pre-verify`** — run the readiness check BEFORE the action, not after. A step that needs a live session re-checks the session is live first.

4. **On a failed `pre-verify`, branch on the source tag** (identical to Phase Blueprint Mode): `← from step X` → **STUCK** (the producing step under-delivered; don't fake the condition, don't test on a missing foundation); `← external` → **STOP and surface the how-to-get-it recipe**, resume once supplied (a Phase-0-style activation pause, not a STUCK — see Hard Invariant #1).

Depth scales (KISS): a trivial one-shot needs no preconditions section — skip it. The win is that /auto stops testing on broken foundations whether or not a /spec blueprint was bound. Same machinery as Phase Blueprint Mode, applied to the plans /auto writes itself.

### Stage-mode runbook (auto-detected for build tasks)

When the goal is to build a multi-stage script or program, /auto generates a **stage-shaped runbook** instead of a monolithic build. Each stage becomes a standalone-runnable puzzle piece under `./stages/`, and the final `main.py` is a thin orchestrator that imports them. If one piece breaks later, you re-run that one stage by itself and the line of blame is one file long.

**Trigger — ALL of these must hold:**

- Goal verb is one of: `build`, `create`, `make`, `write`, `generate`, `automate`, `set up`
- Deliverable is a script/program (not a refactor, rename, bug fix, config tweak, single-file edit)
- Task has **3+ distinct operations** (`load → upload → prompt → download` qualifies; a one-shot single-purpose script does not)

If any condition fails, use the standard runbook format from "sources in priority order" above.

**Stage decomposition.** Break the goal into 3-N stages, each with one clear job, each exercisable with a hardcoded test input, each producing an observable artifact (return value, printed line, file written) the next stage would consume. Name stages in short kebab-case: `load-config`, `upload-image`, `send-prompt`, `download-result`.

**File layout (frozen at runbook generation):**

```
./stages/
  stage_1_<name>.py
  stage_2_<name>.py
  ...
  stage_N_<name>.py
./main.py        (written last, imports from stages/)
```

Each stage file follows this shape (Python example — mirror in the project's language):

```python
"""Stage K — <name>. Runnable standalone for debug."""

def <name>(<inputs>) -> <output>:
    ...   # the actual stage logic

if __name__ == "__main__":
    result = <name>(<hardcoded test input>)
    assert <observable check on result>, f"stage K failed: {result!r}"
    print(f"[stage K OK] {<short summary>}")
```

The `__main__` block IS the verify check. `python stages/stage_K_<name>.py` exits 0 iff the stage works alone.

**Failure-prone stages build + smoke-test their recovery.** When a stage can leave **pre-seedable partial state** behind (it writes a file or mutates state you can stage by hand — i.e. it has a `RECOVERS-BY` in the bound spec, or a field-9/field-12 entry from /prep), the stage implements that recovery — roll back partial work → re-assert the precondition → invalidate downstream → resume — and its `__main__` block proves it: pre-seed the residue (a half-written output / stale state), call the stage, and assert it cleans up and still reaches `[stage K OK]`. This is the standalone twin of /spec's RECOVERS-BY proof, and it's orthogonal to the N+2 different-input re-run (that proves *not-hardcoded*; this proves *survives-residue*). A stage whose only failure mode is a flaky external service can't be cheaply broken in a one-file standalone block — defer its recovery proof to the field-13 REAL / integration test, not here. A pure-compute stage that can't leave residue keeps the happy-path block only (KISS).

**Stage-mode runbook shape:**

```
Steps:
  1. [PENDING] Write stages/stage_1_<name>.py
        verify: python stages/stage_1_<name>.py exits 0, prints "[stage 1 OK]"
  2. [PENDING] Write stages/stage_2_<name>.py
        verify: python stages/stage_2_<name>.py exits 0, prints "[stage 2 OK]"
  ...
  N. [PENDING] Write stages/stage_N_<name>.py
        verify: python stages/stage_N_<name>.py exits 0, prints "[stage N OK]"
  N+1. [PENDING] Write main.py — import stages/, compose pipeline
        verify: python main.py exits 0 producing the success-condition artifact
  N+2. [PENDING] End-to-end re-run with a different input
        verify: produces a different valid artifact (proves not hardcoded)
```

**Why this shape.** If step N+1 fails but stages 1..N still pass alone, the blame is the integration layer — not a puzzle piece. If a stage's standalone verify fails, the failure is contained to one file and one command. Each stage's `__main__` block doubles as a permanent smoke test for future regressions: any later breakage can be re-isolated by re-running that one stage.

**Skill-chain interaction.**

- `/auto /prep` — /prep's function list takes precedence over generic stage decomp. Each RISKY function becomes its own stage; SAFE functions can share a stage. File layout (`./stages/`) and standalone-runnable shape still apply.
- `/auto /repair` and `/auto /optimize` — not builds; stage mode does not apply.

**When NOT to use stage mode** (even if the goal verb matches):

- One-file scripts under ~50 lines with a single clear operation
- Adding a feature to an existing pipeline (not a from-scratch build)
- "Write a quick X" / "give me a one-shot Y"


## Graduated Scale-Up — prove on a little before committing to the whole

Stage mode decomposes by **component** (load → upload → render → save). This decomposes by **volume**. The two compose: a stage that processes many items is itself climbed in rungs.

A runbook step that processes MANY items, or is a long unattended run, is NOT one step. Split it into rungs — **smoke (1) → batch (small) → full** — where each rung is a verify gate and the next rung does not start until the prior rung's output is checked. The cost of a bad foundation then gets paid early and cheap, on item 1, not at hour two of the full run.

**Trigger — any one of these:**

- A step processes a collection where a full pass is expensive (batch render, bulk upload/download, migration over many rows, classification over a large set)
- A step is a long unattended run (>~10 min, or "while I sleep" / "overnight" framing)

**Rung shape in the runbook:**

```
Steps:
  N.   [PENDING] <op> on 1 item (smoke)
          verify: that 1 output actually works end-to-end (exists, valid,
                  plays/parses — not just "no error printed")
  N+1. [PENDING] <op> on a small batch (~10, or ~5% — whichever is smaller)
          verify: all succeed, 0 errors in log, outputs consistent
                  (sizes / durations / row counts in expected range)
  N+2. [PENDING] <op> on the full set
          verify: full count produced OR honest failure count
                  (HI #6 — failures reported, never silently dropped)
```

**Real inputs on every rung (P1 test-at-scale).** The smoke and batch rungs use REAL data and REAL paths — a ramp on toy fixtures proves nothing about the full run. The point of the ladder is to hit the actual target condition at increasing volume, not to exercise a happy path on fake input.

**Each passing rung is the BASELINE for the next (diagnosis anchor — added 2026-08-16, user directive).** Record every passing rung's observed numbers — item counts, sizes/durations, and resource readings (process counts, RAM, chrome tabs) — in PROGRESS.md and the log at the moment it passes. When rung N+1 fails, the cause lives in the DELTA between the passing rung and the failing one (more volume, more concurrency, longer duration — whatever changed between them); diagnosis STARTS by naming that delta and never re-litigates what the lower rung already proved. The rung pair is a ready-made discriminating test (HI #13): rerunning the lower rung mid-diagnosis instantly separates "the machinery regressed" from "the scale broke it."

**KISS bounds (P5) — when NOT to ramp:**

- One-shot single-item tasks (convert THIS file, fix THIS bug) — there's only ever 1, so there's no ladder to climb. Don't fabricate `1 → 10 → all` rungs for a task that runs once.
- Renames, config tweaks, single-file edits — no volume.
- If a smoke rung and the full set are the same size, the rung IS the run — collapse them, don't write three steps that all process the same one item.


## The Activity Log

Alongside the runbook, /auto keeps an append-only activity log. Where the runbook tracks **state** (what step you're on), the log tracks **history** (everything that's been done, tested, tried, and why).

### Log file location

```
./auto-runs/<slug>/log.txt        Patterns 1 & 2
./auto-runs/<slug>/logs/run.log   Pattern 3 (with per-tick logs in ./auto-runs/<slug>/logs/<ts>.txt)
```

### Log entry format

One line per event, ≤120 chars:

```
[ISO timestamp] [Mode] [Step N] <event>: <details>
```

### Events that get logged

```
Step transition       STARTED, DONE, BLOCKED, PARKED
Bash command          command + exit code + duration
File edit/write       file path + lines changed; `Edit applied: <file>:<fn>` names the
                      function(s) touched (FnReview scoping reads these back)
Mode transition       NORMAL → DIAGNOSING → ROTATING (or back)
Approach choice       which N/5 + the reason
Author dispatch       dispatch + return lines (function-author sub-agent)
FnReview              dispatch / returned / carried lines + the `aim-test:` line (FnReview)
Classification        Functions-block labels, reviewer promotions, mid-run appends
Hypothesis list       DIAGNOSING: ranked falsifiable causes, or the explicit fast-path declaration
Probe pre-reg         BEFORE the probe runs: variable / expected / CONFIRMS / DISPROVES
Probe result          which pre-registered prediction fired; cause confirmed or disproved
Verify result         PASS/FAIL + the check that ran
Screenshot            shots/ path + trigger, then one-line Shot read verdict
Sibling note          P7 violation parked for later
/repair sub-loop      entry (with hypothesis list) and exit (verdict)
Cron tick             tick start and tick end (Pattern 3 only)
```

Long stderr / large diffs do NOT go on the log line. They go in per-action files in `./auto-runs/<slug>/logs/<timestamp>.txt` (Pattern 3) or stay in conversation (Patterns 1–2). The log line only references them: `[stderr in logs/2026-04-30T22-01-08.txt]`.

### When the log is read

The "File is the contract" Hard Invariant pulls the **last ~30 lines** of the log on every re-read trigger. This is the recovery mechanism after context compression — even if conversation memory is fuzzy, recent history (what was just tried, what failed, what mode the run is in) is one tail away.

In Pattern 3 cron mode, every cron tick begins with reading the log tail before deciding the next action. This is what makes the architecture survive compression — each tick is stateless, but recent context is one disk read away.

### Example tail

```
[2026-04-30T22:00:14Z] [NORMAL] [Step 1] STARTED: build distribution
[2026-04-30T22:00:18Z] [NORMAL] [Step 1] Ran: python build.py → exit 0 (4.2s)
[2026-04-30T22:00:19Z] [NORMAL] [Step 1] Verify PASS: ls dist/ → 14 files
[2026-04-30T22:00:19Z] [NORMAL] [Step 1] DONE
[2026-04-30T22:01:08Z] [NORMAL] [Step 2] Ran: pytest test_module_a.py → FAIL
[2026-04-30T22:01:08Z] [NORMAL] [Step 2] Stderr: AssertionError test_widget_count
[2026-04-30T22:01:10Z] [DIAGNOSING] [Step 2] Reading test output, hypothesizing
[2026-04-30T22:02:12Z] [DIAGNOSING] [Step 2] Hypothesis list: 1) widget_count off-by-one 2) stale test fixture
[2026-04-30T22:02:14Z] [DIAGNOSING] [Step 2] Probe pre-reg: print len(items) at widgets.py:42 — expect 10; 11 CONFIRMS #1; 10 DISPROVES
[2026-04-30T22:02:20Z] [DIAGNOSING] [Step 2] Probe result: len(items)=11 — #1 CONFIRMED, cause locked
[2026-04-30T22:02:21Z] [ROTATING] [Step 2] Approach 1/5: edit widgets.py:42
[2026-04-30T22:02:30Z] [ROTATING] [Step 2] Edit applied: len(items) → len(items)-1
[2026-04-30T22:02:34Z] [ROTATING] [Step 2] Re-ran pytest → exit 0
[2026-04-30T22:02:35Z] [NORMAL] [Step 2] Verify PASS, Mode → NORMAL
[2026-04-30T22:02:35Z] [NORMAL] [Step 2] DONE
```

The user can `tail -f ./auto-runs/<slug>/log.txt` during a run to watch live, OR `cat` it after for a complete audit trail of what was done, tested, tried, and why.


## Visual Checkpoints — screenshots so a stall can be SEEN

Logs only report what the code thought to print. A frozen progress bar, a surprise GUI dialog, a browser parked on a login wall, a render writing black frames — none of these print a Traceback. The verbose output goes quiet (or keeps repeating) and everything *looks* fine in text. Visual checkpoints close that gap: /auto captures what the screen (or the output artifact) actually looks like, then READS the image itself and judges it.

### When to capture

```
Major events (any step with a visual surface):
  - Step transition: STARTED → DONE / BLOCKED / PARKED
  - Mode → DIAGNOSING                (capture the failure as it looks NOW)
  - STALLED verdict (Monitor deadline expired) — capture BEFORE kill/retry
  - Right before terminal DONE on a job whose output is visual

Timer interval (long steps):
  - Step expected to run >10 min → capture every ~10 min while it runs
  - Pattern 3 → one capture per cron tick while a long step is
    IN PROGRESS (the tick IS the timer)
```

Interval mechanics: either set the Monitor wait deadline to the interval so each expiry is a checkpoint moment (capture → read → re-arm), or launch a tiny background loop that saves a shot every interval and read the newest at each check-in. Never foreground-sleep to wait for the next shot.

**Checkpoint expiry ≠ stall verdict.** When the Monitor deadline is shortened to the checkpoint interval, an expiry means "look now," not "STALLED." The Phase −1 stall rule (~2× expected step duration) still governs: keep a running clock across re-arms, and only declare STALLED when the cumulative wait crosses it — or earlier, when the shots themselves show no progress (two-identical-shots rule below) AND a heuristic #8 artifact probe (output file mtime/size growth) agrees.

### How to capture — match the surface

```
Browser automation       Playwright screenshot (browser-use / webapp-testing)
GUI app on the desktop   PowerShell full-screen grab (snippet below)
Video render in flight   frame-grab the newest FINISHED segment (primary):
                           ffmpeg -sseof -1 -i seg_0042.mp4 -frames:v 1 shot.png
                         A half-written default mp4 has no moov atom — ffmpeg
                         can't open it at all. -sseof on the GROWING file works
                         only for seekable formats (MKV, fragmented mp4, .ts).
Background process       No window — a desktop grab proves nothing. Frame-grab
                         the output artifact instead.
No visual surface        SKIP — use heuristic #8 artifact probes instead
```

Desktop grab (Windows):

```powershell
$shots = "<ABSOLUTE path to auto-runs/<slug>/shots>"
New-Item -ItemType Directory -Force $shots | Out-Null
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
$s = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap $s.Width,$s.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($s.Location,[System.Drawing.Point]::Empty,$s.Size)
$bmp.Save("$shots\<timestamp>-<trigger>.png")
$g.Dispose(); $bmp.Dispose()
```

Absolute path + `New-Item -Force` are load-bearing: `Bitmap.Save` resolves relative paths against the process CurrentDirectory (not `$PWD`) and throws an opaque GDI+ error if the folder is missing.

If the grab fails or returns black / a lock screen (headless cron tick, no interactive desktop), that is NOT a job failure — log "shot unavailable" once and fall back to heuristic #8 artifact probes for the rest of the run.

### Files + log lines

```
./auto-runs/<slug>/shots/<timestamp>-<trigger>.png
```

`<trigger>` is one of `step-done`, `step-blocked`, `diagnosing`, `stalled`, `interval`, `pre-done`. Timestamps use the filename-safe form the logs already use (`2026-04-30T22-01-08`). Every capture appends TWO log lines (model-written — the PostToolUse hook logs the capture command itself but not these):

```
[ts] [Mode] [Step N] Screenshot: shots/<file> (<trigger>)
[ts] [Mode] [Step N] Shot read: <one-line verdict>
```

### Capturing is half the job — READ every shot

A screenshot nobody reads is dead weight. Immediately after each capture, Read the image and log a one-line verdict against what the step SHOULD look like right now:

```
[ts] [NORMAL] [Step 4] Shot read: frame ~8100 rendering, progress moving — OK
[ts] [NORMAL] [Step 4] Shot read: same frame as last interval + "Out of memory" dialog — STALLED
```

**Two-identical-shots rule:** on interval captures, compare the new shot against the previous one — compare the JOB'S surface (the window, the frame content), not the whole desktop (the taskbar clock alone makes full screens differ; an idle desktop is identical by design). A job that should be progressing showing the same surface two intervals in a row is strong STALLED evidence — corroborate with one heuristic #8 artifact probe (is the output file still growing?), then escalate per heuristic #13. Don't wait for a third shot.

**Pattern 2 long runs: offload the reads.** Dozens of interval-shot Reads over a multi-hour run bloat the driver's context (see Context offloading). Delegate "Read shots A and B, compare the job surface, return a one-line verdict" to a throwaway sub-agent; the driver keeps only the verdict. Pattern 3 is naturally immune — each tick is a fresh session.

### Smoke-test / verify capture — the eye on a pass/fail

The captures above watch /auto's OWN steps for stalls. This subsection covers the other surface: a **smoke test or verify step** that decides PASS/FAIL on something you can see. The account-95 incident lives here — a warmup asserted READY because a prompt box existed, a screenshot was taken, but the verdict was read off the page's text ("image creation isn't available in your location"). The shot plainly showed a "Sign in" badge; the account was just signed out. Present-but-unread shot + weak text assertion = a confident wrong verdict. This subsection closes both holes.

**Capture is built INTO the test, not bolted on after.** The screenshot fires from inside the test code at the truth-instant, so it's already on disk when /auto checks. A post-hoc "take a screenshot now" shell/PowerShell grab routed through the model is slow (seconds + a round-trip) and times the shot wrong — it is the **fallback only**, for a pre-existing test /auto can't edit. When /auto (or /prep) generates the test, it injects the capture automatically.

**Capture points = state-changes + assertions, NOT every click.** A state-change is the surface meaningfully changing — navigation (page A→B), an auth flip (signed-out→signed-in), a form submit, a tool/mode toggle, an error appearing. An assertion is the line that decides pass/fail — the load-bearing one, since that is exactly where account-95 lied. A click that opens a menu counts; typing characters, focusing a field, hovering do not.

**Generator contract — how an in-script shot reaches the eye.** Capture fires inside the test process, where the model is NOT in the loop, so the test itself can't write the `Shot read:` verdict. The contract: the test (a) captures at each state-change/assertion, (b) prints one parseable `[shot] <path>` line per capture to stdout. /auto harvests those lines, reads the must-read subset, and writes BOTH activity-log lines (`Screenshot:` + `Shot read:`) at verify time.

**Read-before-verdict + INCONCLUSIVE handling.** A visual verify is not PASS/FAIL until /auto has read the assertion shot (plus the final shot, plus any failure shot) — text + exit code alone can't pass it (Hard Invariant #11). If a must-read shot is missing, black, or unreadable, the verify is INCONCLUSIVE → BLOCKED/PARKED, never PASS; the "shot unavailable → artifact probes" fallback above is for stall detection only, because a signed-out page produces a valid artifact too. A headless/cron run that can't screenshot a visual verify parks it for a run that can.

**Mechanical must-read (no silent skip).** Bind the must-read set to the fan-out "non-answer is a failure" rule: each must-read shot (assertion + final + failure) gets an explicit per-shot `Shot read:` verdict; a missing verdict fails the step. "Must read" is a checkbox, not a promise — a skipped look leaves a blank that trips the failure. This is what stops the account-95 attention-miss from recurring.

**Keep BOTH nets — the shot doesn't excuse a weak assertion.** account-95 also had a weak text check (prompt-box presence, true on a signed-out page too). The screenshot is a second net, not a license to skip tightening the first. For a visual surface, the self-derived verify sanity pass (see runbook "sources in priority order") explicitly asks: *does this assertion distinguish signed-in from signed-out / ready from error?* Tighten the text assertion AND read the shot.

**Naming — reads as a story, in its own subdir.** Smoke-test shots live in `./auto-runs/<slug>/shots/smoke/` and are step-numbered + labeled: `01_before_login.png`, `02_after_submit.png`, `03_assert_ready.png`. Numbered + labeled means the sequence reads top-to-bottom and a gap (still "Sign in" at the READY assertion) jumps out. /auto's own step/stall captures keep their `shots/<timestamp>-<trigger>.png` scheme and `<trigger>` enum untouched — different folders, no collision.

**What counts as a "visual surface" (decidable test).** If a human would need to *look* at the result to confirm it's correct — rather than read a number or string — it's a visual surface (browser, GUI app, rendered frame/image, TUI). If correctness is fully captured by an exit code, a returned value, or a file's size/contents, it's not.

### KISS bounds (P5)

- Pattern 1 trivial tasks: no screenshots — they finish before any timer fires.
- No desktop captures of steps with no visual surface just to follow the rule.
- Non-visual verifies (exit code, returned value, file size/contents): no shot — the machine check IS the oracle.
- PNG stills only — no video capture, no pixel-diff tooling; "Read both images and compare" IS the diff.


## The Implementation Notes (per-run narrative)

Alongside the runbook (state) and activity log (mechanical history), /auto maintains a per-run **implementation notes** file. Where the activity log records *what happened*, the notes capture *why* — the decisions /auto made that the spec didn't pin down, deviations from the planned path, tradeoffs considered, and questions the user should review.

### Time window (the strict rule)

The notes file covers **exactly one /auto run**:

- **Created** at Phase 0.5, right after the runbook is written
- **Appended to** throughout execution as decisions are made
- **Finalized** at DONE or STUCK with a closing summary section
- **Resumed** (not recreated) if /auto re-enters on the same slug — chat closes mid-run and a cron tick continues; Pattern 3 ticks against an existing runbook; etc.

The notes do NOT span multiple /auto runs. A new /auto with a different slug gets its own notes file. A prior run's notes are never modified after that run's terminal verdict — the file is sealed by the Final Summary section.

### File location

```
./auto-runs/<slug>/notes.md           Patterns 1 & 2
./auto-runs/<slug>/NOTES.md           Pattern 3 (lives with state files)
```

Markdown by default — universally readable, renders in editors and `cat`. Use `.html` instead only if the user explicitly asks for browser-friendly output.

### File structure

The file is initialized with four narrative sections:

```markdown
# Implementation Notes — <slug>

Started: <ISO timestamp>
Goal:    <one observable sentence — copy from runbook>
Success: <checkable bar — copy from runbook>

## Design Decisions
Choices made where the spec or runbook was ambiguous.

## Deviations
Places where execution intentionally departed from the runbook, and why.

## Tradeoffs
Alternatives considered and why the chosen path won.

## Findings
What we LEARNED — context, proven result, and the *suspected* reason why.

## Open Questions
Anything the user should confirm or revise.

---
(entries appended below as the run progresses)
```

### When to append an entry

Append a dated entry under the matching section when:

- **Design decision** — a step's action wasn't fully specified (default values, edge-case handling, choice of library/API, file naming) and /auto picked one
- **Deviation** — /auto departed from the runbook (added a step, skipped one, swapped an approach mid-step); log it here AND mark the runbook
- **Tradeoff** — more than one valid path existed and /auto picked one; name the alternatives and the reason
- **Open question** — something /auto resolved tentatively but the user might want to revise (library version, API timeout, file naming, a guessed default)
- **Finding** — we learned *why* something was the way it was. Two cases fire it: (a) a failure got resolved and we now think we know the cause, or (b) a small success flipped a prior assumption — the classic being "the tool finally worked once we logged in → the account was never cooked, we just weren't authenticated and that's why it did nothing." A "surprising result" (worked when it shouldn't have, or vice-versa) also counts. Do NOT fire one on a routine, expected success.

Entry format:

```markdown
### <ISO timestamp> — <one-line summary>

**Context:**     <step or situation>
**Choice:**      <what was decided>
**Why:**         <reason — usually grounded in spec, principle, or a probe result>
**Alternatives:** <only on tradeoff entries>
```

**Finding entries use their own three-field shape** (under the `## Findings` section):

```markdown
### <ISO timestamp> — FINDING: <one-line summary>

**Context:**           <what we were doing + the assumption we held going in>
**Result:**            <what actually happened — observed and PROVEN, not inferred>
**Suspected verdict:** <best-guess reason WHY — explicitly a hypothesis, never stated as fact>
```

The `Result` line is the proven part (what the tool/output actually did). The `Suspected verdict` is the *guess* at the cause — always phrased as suspected, per the evidence-first rule: state what was seen, hypothesize the why. A verdict backed by a decisive check (one experiment that isolates the cause — "pin the fix, don't guess") is far stronger than one inferred from a single happy outcome; note the check in the verdict line when one was run.

Keep entries short — 4-8 lines. The notes file is for human skim, not exhaustive log. Mechanical tool-call detail belongs in the activity log.

### Closing summary at DONE or STUCK

When /auto reaches terminal verdict, append a Final Summary section that seals the file:

```markdown
---
## Final Summary

Ended:    <ISO timestamp>
Status:   DONE | PARTIAL | STUCK
Duration: <wall-clock from Started>

### Headline
<one-paragraph plain-language summary of what landed>

### By the numbers
- Design decisions logged: N
- Deviations logged:       N
- Tradeoffs logged:        N
- Findings logged:         N
- Open questions pending:  N

### Open questions worth your review
- <one-line summary per open question entry>

### Next move (if not DONE)
<concrete suggested next step — mirrors AUTO REPORT's Next field>
```

This summary is the deliverable handed to the user. The in-chat AUTO REPORT stays short; the notes file is the deeper read with provenance for every non-obvious choice.

### Promote keeper findings to SPEC.md (only if a SPEC.md exists)

A Finding is a lesson; lessons outlive the run. At terminal verdict, if the project has a `SPEC.md`, promote the **keeper** findings (the ones that explain a real cause — skip throwaway/obvious ones) into its Change Log.

**Ordering is mandatory** — do this *before* writing `Status: DONE` to the runbook. Route the promotion through `spec_tool.py log` (not a raw Edit): the helper advances the logged-edit marker as it writes, so the SPEC.md change lands already-logged and the Stop hooks (`spec-guard`, `auto-stop-block`) see no dangling unlogged edit. A raw Edit to SPEC.md *after* `Status: DONE` would re-trip spec-guard and violate the Refuter Gate's frozen window (nothing runs between DONE and stop).

The ledger's field names don't match the Change Log schema, so **translate** as you pipe each keeper:

```
finding   →  change   (prefix "FINDING: ")
context   →  context
(prior assumption / what was failing)  →  before
result    →  after
suspected verdict  →  why   (keep the word "suspected" — it's still a guess)
```

```bash
printf 'change: FINDING: %s\nwhy: suspected — %s\ncontext: %s\nbefore: %s\nafter: %s\n' \
  "<summary>" "<suspected verdict>" "<context>" "<prior assumption>" "<proven result>" \
  | python "C:\Users\Shadow\.claude\skills\spec\spec_tool.py" log
```

No `SPEC.md` in the project → skip promotion silently (the findings still live in `notes.md`). One `spec_tool.py log` call per keeper finding.

### Relationship to the other artifacts

```
Runbook         current state of steps (mutable, source of truth for "where am I")
Activity log    every state-changing tool call (append-only, mechanical, for replay)
Notes (this)    the WHY (decisions, tradeoffs, findings/lessons, open questions; sealed at terminal verdict)
AUTO REPORT     terminal in-chat summary that points at the notes file
```

A user who reads only the notes file should still understand what /auto did and why, without needing to crawl the activity log.


## Composition with /principles, /prep, and /repair

The user's standard invocation pattern is:

```
/principles  →  /auto (or /prep or /repair)  →  proceed
```

`/principles` is run first to load all ten principles into context (P1 test-at-scale, P2 conditions-upfront, P3 end-goal-in-sight, P4 audit-before-handback, P5 KISS, P6 think-before-coding, P7 surgical-changes, P8 goal-driven-execution, P9 build-for-the-real-run, P10 see-it-before-you-call-it). Then the action skill runs with the principles already active as standing checkpoints. Then `proceed` is the standing authorization.

When this pattern is detected (recent `/principles` skill invocation OR principle keywords in recent context), /auto skips re-reminding the user about principles and proceeds straight into Phase 0 plan ingestion + activation gate. The principles are already loaded; don't restate them.

/auto is most often run on top of /prep, /repair, or both. The runbook structure changes based on what /auto is consuming.

### Skill chaining contract (applies to any chain — /auto /X /Y, /auto /X /Y /Z)

When /auto is invoked with multiple methodology skills chained — `/auto /prep /repair`, `/auto /repair /audit`, `/auto /prep /optimize`, etc. — position determines role:

```
/auto /<lens> /<phase-1> [/<phase-2> ...]

  /<lens>     The planning methodology. Owns Phase 0.5 runbook
              generation. Its loop dictates the plan's STRUCTURE.

  /<phase-N>  Each later skill is BOTH a principle source AND a
              named phase under the lens. Its principles inform the
              plan's CONTENT; its loop runs as a named phase of the
              runbook (proactively in planning, reactively in fix mode).
```

Before generating the runbook, /auto MUST:

```
1. Read the lens skill's SKILL.md           (drives plan structure)
2. Read each subsequent skill's SKILL.md    (informs plan content)
3. Generate a plan where:
   - Structure follows the lens
     (e.g., /prep's 16-field per-function cards when /prep is the lens)
   - Content is enriched by every later skill's principles
     (e.g., RED tests are reproduction probes when /repair is chained;
      GREEN is minimal isolation; REAL is production-shaped verification;
      AUDIT traces back to the failure signature)
   - Runbook steps explicitly name which chained skill owns each phase
     (e.g., "Step 3 — /repair RED: reproduce the failure")
4. On verify failure during execution, /auto invokes the matching
   chained skill's loop as the sub-loop (not generic rotation).
   The chained skill's principles were already in the plan, so the
   sub-loop is continuation, not context switch.
```

**Compatibility check.** If a chained skill's principles can't meaningfully apply to the lens (e.g., `/auto /audit /prep` — audit reviews finished work, prep designs new work), /auto refuses to generate the runbook and surfaces the conflict at the Phase 0 activation gate.

**Why this works.** The user already proved `/auto /prep` works because /prep's loop maps cleanly to runbook steps and /auto's fix mode handles deviations. Chaining a third skill works the same way IF the third skill's principles get baked into the plan upfront — not bolted on reactively. That's the whole contract.

### /auto on top of /prep

```
/prep   — generates ./prep-<slug>.txt with function list + 16-field
          per-function specs (RED/GREEN/REAL/AUDIT pre-written for
          every RISKY function in field 13)

/auto   — Phase 0 reads the prep file → Phase 0.5 generates a runbook
          where each function's build cycle becomes 4 steps (RISKY)
          or 1-2 steps (SAFE):

   For each RISKY function:
     Step N+0:  Write RED test from field 13.RED       verify: test fails
     Step N+1:  Implement function (KISS, P5)          verify: test passes
     Step N+2:  Run REAL test from field 13.REAL       verify: REAL passes
     Step N+3:  AUDIT vs END GOAL card                 verify: traces to goal

   For each SAFE function:
     Step N+0:  Implement function                     verify: smoke check
     Step N+1:  AUDIT vs END GOAL card                 verify: traces to goal

   The AUDIT step of EVERY function (RISKY and SAFE alike — Option B,
   2026-08-22) is executed by the FnReview dispatch — an independent
   reviewer, not the driver grading its own work — with "traces to goal"
   as item 0; both FnReview triggers are suppressed at Implement and REAL
   so it fires once, after REAL (SAFE: after the smoke check). Several
   functions finishing together are reviewed in parallel. See FnReview.

   Then Phase 9 integration steps from TESTING CONDITIONS card.

   Then BUILD STATUS card update + FINAL VERDICT (the terminal
   FINAL VERDICT routes through the Terminal Refuter Gate when the
   success condition is judgment-based).
```

### /auto on top of /repair

```
/repair — has its own 9-step loop (Transform → Hypothesize → Lock →
          Isolate → RED → GREEN → Integrate → Step 2 → Audit)

/auto   — runs each repair phase as a runbook step. Approach rotation
          inside /auto maps to repair's hypothesis rotation. STUCK
          condition aligns with repair's "5 hypotheses tried"
          terminal state.

   The repair loop IS the runbook. /auto's job is to drive the loop
   without pausing for input — exactly the property /repair already
   wants. /repair's step 9 (Audit) is executed by the FnReview (the
   independent per-function completeness review) with the fix
   packet; FnReview's triggers are suppressed at steps 4–8 so there
   is exactly one dispatch per fixed function (see FnReview, "Timing").
```

### /auto on top of /prep + /repair

There are two distinct ways /prep and /repair compose under /auto. They are NOT the same and the user's invocation tells you which one to run.

**Mode A — Chained invocation (`/auto /prep /repair`): proactive — repair informs prep**

The user wants the prep file itself to be repair-aware before any execution. Per the Skill chaining contract above:

```
Lens:    /prep         (drives plan structure)
Phase:   /repair       (informs plan content + owns fix phase)

Plan generation enriches /prep's 16-field cards with /repair principles:
  - field 13.RED    → reproduction probe (must reproduce a failure mode
                      under realistic inputs, not just verify the
                      happy path)
  - field 13.GREEN  → fix the STRUCTURAL cause, not the proximate
                      trigger (/repair HI #16 + Principle 12 — the
                      climb-one-layer test must return NO before
                      the cause is locked)
  - field 13.REAL   → production-shaped verification (real data,
                      real paths — not toy fixtures) AND a
                      different-instance probe (different input /
                      state / shard) — the same failure mode must
                      not fire there
  - field 13.AUDIT  → traces the fix back to the structural cause
                      (logged climb trail), not just the failure
                      signature

Runbook execution:
  - Each function's Red/Green/Real/Audit cycle runs as planned
  - On verify failure, /auto enters fix mode and invokes /repair's
    9-step loop as a sub-loop (Mode B below kicks in for that step).
    The sub-loop's step 3 climbs to the structural cause; its step 8
    different-instance probe catches symptomatic patches before they
    ship.
  - Because /repair's structural-cause principle was already baked
    into the plan, the sub-loop is continuation, not context switch
```

This is what makes `/auto /prep /repair` distinct from `/auto /prep` followed by ad-hoc /repair: the prep file is repair-shaped from the start, and structural-fix is the verification bar — not symptom-pass.

**Mode B — Reactive sub-loop (the common case during execution)**

Whether the user invoked `/auto /prep` or `/auto /prep /repair`, when a step's verify fails mid-runbook, /auto invokes /repair as a sub-loop on that step:

```
1. /auto walks the prep-derived runbook
2. Step N — function W's GREEN — fails verify (test won't pass)
3. /auto enters fix mode, recognizes this as a repair situation, and
   invokes /repair as a sub-loop instead of generic rotation
4. /repair runs its 9-step loop on the failing test
5. /repair returns DONE (or STUCK)
6. /auto resumes the build runbook at step N+1 (or PARKs and continues
   if /repair STUCK)
```

The runbook tracks ALL of this — the original prep-derived steps stay; a /repair sub-loop is logged as a single step's "Approaches tried" entries with the diagnosis trail.

**Mode A and Mode B work together.** Mode A makes the plan anticipate failure; Mode B handles the failures that happen anyway. Chained invocation activates both. Plain `/auto /prep` activates only Mode B.


## Hard Invariants

These never bend.

1. **Invocation is authorization.** The act of saying `/auto` (or any of the trigger phrases above) authorizes the entire task end-to-end. Claude does not ask "are you sure?", "should I proceed with the plan?", "want me to run X to check?", or any other confirmation. The user already said yes by invoking.

   This holds even when:
   - Multiple valid approaches exist (pick one, log it in one line, proceed)
   - An unexpected error appears (diagnose + rotate, don't ask)
   - The output is ambiguous (check it against the success condition — don't ask "does this look right?")
   - The work turns out bigger than expected (continue; budgeting is internal)
   - A step is taking longer than expected (use Monitor, continue planning)
   - A choice has to be made about a default (timeout, retry count, format) — pick the modern reasonable default, log it, proceed

   The ONLY exits from a /auto RUN: **DONE**, **STUCK-user** (genuinely blocked on something only the user can supply — including guardian round-cap exhaustion), **/auto stop**, or a Hard-Invariant trip in "Auto Does NOT Waive." A SESSION turn may end at `PARTIAL (checkpoint)` — that ends the turn, never the run: the Goal-Guardian cron carries the run onward. Two activation-class exceptions pause without ending the run: (a) the Phase 0 activation gate, which fires before /auto activates; and (b) the **missing-external-condition stop** — whether from Phase Blueprint Mode or a condition-first self-derived runbook — which can fire mid-run at a phase/step boundary when an `← external` precondition isn't met — /auto pauses because it genuinely cannot manufacture that condition, surfaces the how-to-get-it recipe, and resumes once it's supplied. Both are foundations-/auto-can't-build pauses, not approvals.

2. **Pre-action context, not pre-action gate.** Before doing something non-trivial, Claude states one or two sentences naming what it's about to do and why. This is for *user awareness*, not for *user approval*. There is no waiting period. Claude finishes the sentence and proceeds.

3. **Never advance on a bad result.** If a step's output doesn't satisfy the success condition, Claude does not pretend it did. The step is judged failed and a different approach is tried.

4. **Never repeat a failed approach.** Each retry must differ from prior attempts in at least one concrete variable (different parameter, different prompt, different command flag, different input). If five distinct approaches have all failed, declare STUCK and stop. Don't burn budget on cosmetic variations. (A FnReview finding is a NEW failure signature: it resets the step's 5-approach budget for that review round — ≤2 rounds per guardian pass — and a fix that fails the driver's own HI #14 aim-test counts as a failed approach without a dispatch. See FnReview.)

5. **Stop on DONE or STUCK-user, not on "looks good enough."** DONE means the actual success condition is met and verified against the pinned contract (circumstances + never-dos included). STUCK-user means the run is genuinely blocked on something only the user can supply — a step merely exhausting its 5 approaches gets PARKED and re-attacked by the guardian (up to 3 rounds), not declared terminal. A step PARKED by a round-2 FnReview finding (`open …`) is a DONE gate — the refuter must rule on it (BLOCKER or cited WAIVED) before DONE, even on a machine-checked goal; and a FnReview finding resets the step's 5-approach budget for that review round, gated by the driver's HI #14 aim-test (≤2 rounds per guardian pass — still bounded, still never "looks good enough").

6. **Honest reporting.** If 24 of 269 things failed, the report says 24 failed. Not "245 succeeded" with the rest swept under. The user can decide what to do with partial success — Claude's job is to surface it accurately.

7. **No skill-internal gates.** Phase-by-phase confirmations, "ready to proceed?" prompts, "I'll need your approval before X" — all forbidden. Genuinely destructive actions on shared/external state (force-pushing to a public repo, dropping a production database) are still flagged before execution, but routine local actions are not.

8. **File is the contract.** Before any non-trivial action, RE-READ the runbook + plan + log tail from disk. Conversation context is the transcript; the files are the truth. Trust the files when they disagree.

   "Non-trivial action" triggers a re-read:
   - Writing/modifying a code file >10 lines
   - Running a command that changes state (deploy, migration, delete, kill, restart)
   - Invoking /repair as a sub-loop
   - Mode transition (NORMAL → DIAGNOSING → ROTATING)
   - Starting a new runbook step
   - Every 5 tool calls since last re-read (compression hedge)
   - First action of every cron tick (Pattern 3 — mandatory)

   Re-read scope: `./auto-runs/<slug>/runbook.txt` (state) OR `./auto-runs/<slug>/RUNBOOK.md` (Pattern 3), the matching `./prep-<slug>.txt` (goal + specs), and the last ~30 lines of `./auto-runs/<slug>/log.txt` (recent history). If the files disagree with conversation memory, trust the files and acknowledge the file truth in the next text output.

9. **No terminal DONE before the refuter clears (judgment-based goals).** When the Success line is a judgment call, the terminal `Status: DONE` / `FINAL VERDICT: DONE` line MUST NOT be written until the runbook's `Refuter:` field reads `clean`. The Stop hook releases on that `Status:` line, so writing DONE first would let the run stop before the refuter can re-open it. All-steps-PASS — and no FnReview pending / in fix (the universal pre-DONE pending check, evaluated on every DONE path before this exemption is consulted) — is necessary but NOT sufficient for DONE — the refuter gate is. Machine-checked goals are exempt (`Refuter: n/a`) **except** when a FnReview line reads `open …` or a fix-trigger function is `unreviewed`: then the refuter fires anyway and `Refuter:` flips `n/a → pending` (FnReview's open-finding DONE gate — the same override shape as #11). See Terminal Refuter Gate + FnReview.

10. **Probe, don't assume — empirical evidence governs every claim.** Never act on what *seems* true — what an error means, whether a step worked, whether a dependency / credential / file is in the expected state. Get the evidence first: run the cheapest probe that turns the assumption into an observation (artifact check, exit code, a one-shot **smoke test**, a re-read of the actual file). When there's no cheap probe, write a **specialized check that exercises the real target condition** (P1 test-at-scale — not a config flag standing in for the real thing) and run it. A verdict from one happy outcome is a hypothesis; a verdict from an isolating check is evidence ("pin the fix, don't guess" — one experiment that isolates a single variable beats inference). This generalizes #3 (never advance on a bad result) and the artifact rule in Universal Principles: those say *don't trust a bad or absent signal* — this says *go manufacture the signal rather than assume one*. A one-shot patch used to *make the probe possible* (work-once-to-smoke-test) is fine as scaffolding — but it is never DONE; the deliverable is the structural heal that survives the next-run-without-Claude test (see /repair HI #17). Patch to learn, then fix the cause.

11. **See it before you call it — a visual verify is not PASS until the shot is read.** When a verify/smoke step decides pass/fail on a visual surface (a browser, a GUI window, a rendered frame), its screenshot is captured *inside the test* at each state-change + assertion, and /auto MUST read the relevant shot (assertion + final + any failure shot) before recording PASS/FAIL. A passing exit code or a matched log string is necessary but NOT sufficient on a visual surface — a signed-out page prints a prompt box and exits 0 just like a signed-in one (the account-95 miss: a captured-but-unread shot plus a weak text assertion produced a confident wrong verdict). So a visual verify is treated as judgment-shaped: the Terminal Refuter Gate does NOT skip it (this overrides the machine-check exemption in #9 for that step), and a missing / black / unread assertion shot makes the verify INCONCLUSIVE → the step goes BLOCKED/PARKED, never PASS. The stall-detection fallback ("shot unavailable → artifact probes") is for watching long jobs, NOT for clearing a visual verify. See the "Smoke-test / verify capture" subsection under Visual Checkpoints.

12. **Restore the precondition before any retry.** Never re-attempt a step on top of the prior attempt's residue. At every recovery door — approach rotation, resume / cron-tick pickup of an IN-PROGRESS step, a refuter re-opening a DONE step, a guardian un-park, and a FnReview finding re-opening a producing step — run the step's `rollback:`, re-assert its `pre-verify`, and invalidate any downstream step whose foundation actually changed (checksum differs), BEFORE re-running. Re-entry that skips this ships a stale foundation. A step left `VERIFIED (FnReview pending)` is NOT an IN-PROGRESS pickup: its action already succeeded — hash-check it against its pending stamp and resume at the dispatch; only a hash mismatch or a finding opens the restore. See "Re-entry hygiene."

13. **No premature convergence — probes must discriminate, alternatives must be ruled out.** (Always cite as "HI #13" — heuristic #13 is a different rule.) In fix mode and on any judgment-shaped verdict, do not prematurely converge on the current hypothesis. The pre-registered probe must be a **discriminating test** — its CONFIRMS / DISPROVES outcomes must separate the leading hypothesis from its ranked rivals, not merely confirm the current assumption (a probe both hypotheses would pass discriminates nothing). Avoid **search-space neglect** and **anchoring bias** by actively checking plausible alternatives: DONE is not written simply because the initial hypothesis appears correct — the conclusion must be supported by evidence with the relevant alternatives investigated or explicitly ruled out (the hypothesis list + probe log is that evidence). This sharpens HI #10: #10 says manufacture the signal; this says the signal must be able to say NO to the favorite.

14. **Aim at the right fix — structural by default, band-aids only on explicit request.** When choosing WHAT fix to build, the target is the fix that **structurally strengthens the system** — the one that removes the condition that produced the failure. That aim is set at design time: never build the band-aid first planning to upgrade later, and never present a band-aid as the fix. A band-aid is any fix that neutralizes *this instance* (this input, this account, this state) while the producing condition survives — a special case, a narrowed scope, a workaround routed around the broken part. The aim test, before building: *"after my fix, does the condition that produced this failure still exist?"* — YES → band-aid; climb a layer and re-aim. One common band-aid shape worth naming: a mechanism needs a precondition and the fix **filters** for inputs that already satisfy it instead of **establishing** it on any input (cohort incident 2026-08-20: "promote an already-logged-in spare" — band-aid, dies when no logged-in spare exists; right fix: log in + clean-slate ANY account as part of promotion). A second band-aid shape: a recovery UNDER-sized by a guessed constant (a 90 s rest for a throttle measured at ~24 min) — the aim-test can read "condition removed? yes" only if the constant is trusted, so check its source: an observed measurement or a bounded smallest-first ladder (Heaven's Net Proportion guardrail, canonical in /error-recon). Over-sizing is not a band-aid but is the same guardrail's other violation. The only sanctioned band-aid is the work-once-to-smoke-test scaffold in #10, and it is never the deliverable. If the user explicitly requests a quick/temporary patch, ship it labeled `BAND-AID (user-requested):` with the structural version named beside it so the debt is visible. **No clash with Graduated Scale-Up:** the ramp and this rule turn different dials — **scale-up shrinks SCOPE, never STRUCTURE.** Rung 1 (smoke) runs the REAL mechanism on one input; a band-aid is a *different, weaker* mechanism, not a smaller one, and scale doesn't cure it (rung 1 of the cohort fix = run the real login+clean-slate promotion on ONE account — correct; "promote an already-logged-in spare" stays a band-aid even run on 100 accounts). Litmus at rung 1: *"is this a small version of the right mechanism, or a different mechanism that only handles the easy case?"* Full sequence: scaffold to probe (#10) → build the right fix → prove it small → scale it up — band-aids only ever live in the scaffold step, and they die there.


## Pre-Action One-Liner Format

Before each substantive action (running a command that takes >30s, editing >3 files, hitting an external API, kicking off a long process), print one short line so the user knows what's happening:

```
[auto] <action> — <why>
```

Examples:

- `[auto] Killing PID 78561 and restarting farmer — Timestamp worker died, Video 2 projects sitting idle`
- `[auto] Re-rendering Stage 4 with WHISK_THREADS=300 — prior 80 was the bottleneck`
- `[auto] Diff of proposed change to stage_2_plan.py:` *(then show it and apply it without asking)*

This is **not** "do you approve?" It's "FYI, here's what just happened / is about to happen." Continue immediately.


## Execution Shape — Three Patterns

Pick by task duration and presence requirement.

### Pattern 1 — Synchronous inline (small tasks)

A single file edit, one command, one quick test. Sub-30s work that finishes inside one tool call. No background, no monitor, no cron.

Use when: typo fix, rename, single-test run, single-file refactor, one-shot script, single command verification.

### Pattern 2 — Background + Monitor (DEFAULT for non-trivial work)

Any task with steps that take >30s or wait on external systems (downloads, builds, browser automation, API calls, multi-stage pipelines). The model is NOT sitting idle — it launches work in the background and watches for completion.

```
a. Bash with run_in_background=true to launch the step
b. Monitor on the log file (or process stdout) to stream progress
c. Continue planning / launching independent parallel steps while the
   background work runs
d. Monitor notification fires when the "done" pattern matches
e. Verify the success condition; rotate or continue
```

This is the right default for most /auto invocations. Use the Monitor tool to wait on conditions (e.g., until-loop watching for a string in a log) rather than polling with sleep.

### Pattern 3 — CronCreate + Monitor + Bash (default for build pipelines and unattended work)

Use whenever the work needs the heartbeat + stateless tick architecture: build pipelines (every `/prep + /auto` run qualifies), multi-hour data jobs, overnight unattended runs, or any task where survivability across chat-session idleness or context compression matters.

**The architecture is in-session — Claude Code itself is the executor.** Pattern 3 uses three claude code tools coordinating around state files on disk:

```
CronCreate    Schedules wake-ups every N minutes. Each fire enqueues
              its prompt as a new TURN into THIS same session while
              the REPL is idle (session-only; dies with the window;
              7-day auto-expiry — see Goal-Guardian). The cron's
              prompt is PINNED, e.g. "/auto guardian slug=<slug>
              run=<absolute path>" — so every tick targets the exact
              runbook this cron owns and the skill reloads after
              compaction. The Goal-Guardian IS this cron — one cron
              per run, ever.

Monitor       In-session: streams events from a Bash background
              process so /auto can wait on a "done" pattern in a
              log without polling.

Bash          Runs the actual work. Use run_in_background=true for
              steps >30s so /auto keeps planning while they run.
```

There are NO external shell scripts (`monitor.py`, `shell.sh`, `teardown.sh` are gone). The assistant IS the monitor and shell. Each cron tick is a fresh TURN in this same session that re-reads the files (HI #8 — files beat memory, surviving compaction), decides the next action, executes, writes back, and checkpoint-exits.

Trigger conditions (any of these → Pattern 3):

```
- /prep + /auto in same prompt (canonical trigger — build pipeline)
- Task involves Red/Green/Real/Audit cycles per RISKY function
- Task expected to run >1 hour or >10 atomic steps
- Phrases: "while I sleep", "overnight", "by morning",
  "set up a loop and walk away", "set up cron mode"
```

State files (created by /auto on Pattern 3 setup):

```
auto-runs/<slug>/GOAL.md       Frozen goal + success conditions
                          Written once at setup. Never modified.

auto-runs/<slug>/RUNBOOK.md    Step list + current state + mode
                          Updated after every step transition.

auto-runs/<slug>/PROGRESS.md   Last-tick summary (what fired this tick,
                          what's next). Helps the next tick orient.

auto-runs/<slug>/APPROACHES.md Append-only retry log — every approach
                          tried for every step, with the reason it
                          failed.

auto-runs/<slug>/log.txt       Append-only activity log (also lives at
                          auto-runs/<slug>/logs/run.log under Pattern 3
                          for per-tick separation).

auto-runs/<slug>/VERDICT_DONE  Touched on terminal success.
                          On detection at start of any tick,
                          /auto invokes CronDelete and exits.
                          NEVER written at PARTIAL (checkpoints
                          write no VERDICT file).

auto-runs/<slug>/VERDICT_STUCK Touched ONLY on STUCK-user or
                          STUCK (stopped by user). A legacy
                          VERDICT_STUCK carrying the old all-
                          parked/machine-retryable meaning is
                          treated as a CHECKPOINT, not a
                          terminus (Goal-Guardian rule).

auto-runs/<slug>/logs/         Per-tick logs:
  tick-<ISO>.log          One file per cron tick.
  cron.log                Append-only summary of every tick start/end.

auto-runs/<slug>/shots/        Visual checkpoints — one PNG per capture
                          (see Visual Checkpoints).
```

### How a cron tick actually flows

```
Tick fires → new TURN in this same session → /auto re-invoked by the pinned prompt

  1. Read auto-runs/<slug>/RUNBOOK.md (state, current step, mode)
  2. Read auto-runs/<slug>/GOAL.md (frozen goal — never trust memory)
  3. Read tail of auto-runs/<slug>/logs/run.log (~30 lines of recent history)
  4. Check for auto-runs/<slug>/VERDICT_DONE or auto-runs/<slug>/VERDICT_STUCK
       If either exists → CronDelete + exit (loop self-uninstalls)
  4b. OWN-JOBS CHECK (replaces the retired TICK_LOCK — same-session
      turns serialize, so no lock file is needed): read the runbook's
      Jobs: field (never conversation memory). Any of this run's
      background jobs alive → no success probe, no reviewer-step
      execution this tick; task-alive OUTRANKS artifact-flat (see
      Goal-Guardian tick step 4 — canonical).
  4c. If the runbook shows a long step IN PROGRESS with a visual
      surface → capture + read a visual checkpoint (see Visual
      Checkpoints). Job surface identical to the previous tick's shot
      AND the heuristic #8 artifact probe shows no growth → treat the
      step as STALLED (heuristic #13). Background jobs with no window:
      frame-grab the output artifact instead of the desktop.
  5. Pick first non-DONE / non-PARKED step from runbook
       (if none and success unmet → NOT a terminus: increment Round,
        dispatch the blocker-review subagent, act on its verdict via
        the constraint compass — Goal-Guardian tick step 8. Round
        cap exhausted → STUCK-user with the ledger. PARTIAL is only
        ever a checkpoint; no VERDICT file is written at PARTIAL)
  6. Execute that step (if it was left IN PROGRESS by a dead tick, restore its
     precondition first — Re-entry hygiene; if it was left VERIFIED (FnReview
     pending) do NOT re-execute: hash-check vs the pending stamp and resume at
     the FnReview dispatch — and if that review is carried/in flight, it does
     NOT occupy the tick: pick the next runnable step that does not consume
     the reviewed functions; an IN PROGRESS step found alongside gets its
     door-2 restore in the same pass):
       - Bash for direct commands
       - Bash with run_in_background=true for long ones
       - Monitor on the log to wait for completion signal
  7. Verify: run the step's verify check
       Pass → if the step wrote or rewrote any function (Option B; the
              fix-trigger adds the fix packet; on /prep runbooks suppressed
              at Implement/REAL — it fires at the AUDIT step, where the
              review IS the verify and is dispatched at step entry) →
              VERIFIED, dispatch one reviewer per function in parallel;
              DONE only when every function's verdict is clean / unreviewed
              / WAIVED (a finding → BLOCKED on the producing step, fix mode).
              Otherwise mark step DONE in runbook, append log line
       Fail → enter fix mode, /repair sub-loop, rotate up to 5x
  8. Update auto-runs/<slug>/RUNBOOK.md and auto-runs/<slug>/logs/run.log
  9. Write auto-runs/<slug>/PROGRESS.md with one-line "this tick did X" summary
 10. CHECKPOINT-EXIT: write all state atomically, set Status:
     PARTIAL (checkpoint), end the turn. Next tick fires N min
     later and flips it back to active.
```

Each tick **trusts files over memory** — every state file is re-read at tick start (HI #8), so the architecture survives context compression and chat idleness. (Ticks fire in the SAME session and may retain conversation context — but they never rely on it; the files are the truth. The session closing ends the crons: resume then needs `/auto resume slug=<slug>`.)

### Cron interval rule of thumb

```
tick interval ≥ 2 × expected step duration

Fast steps (file edits, quick commands)              → 1–2 min
Slow steps (test suites, builds, multi-min API)       → 5–15 min
Very slow steps (overnight ffmpeg renders)            → 15–30 min
```

Don't tick faster than the work can finish — overlapping ticks just stack. If unsure, start at 10 min and adjust based on PROGRESS.md observation. On build / fix runs size the interval at runbook generation for **author dispatch + FnReview dispatch + principles-sweep combined** — a dispatch must never straddle the tick that opened it; a FnReview that can't fit the remaining window is carried to the next tick (FnReview "carried" rule).

### Self-uninstall

On every tick start, /auto checks for `auto-runs/<slug>/VERDICT_DONE` or `auto-runs/<slug>/VERDICT_STUCK`. If either exists:

```
1. Invoke CronDelete with the cron name (e.g., auto_<slug>)
2. Append final log line "[tick stop] verdict found, cron deleted"
3. Exit
```

The schedule self-cleans. No leftover scheduled tasks polluting your system.

### Picking the pattern

```
Trivial: 1-2 atomic actions, total <5 min                  → Pattern 1
/prep + /auto in same prompt                                → Pattern 3
Build pipeline (Red/Green/Real/Audit + integration)         → Pattern 3
Multi-hour task OR explicit "overnight" / "while I sleep"    → Pattern 3
Everything else (3-10 steps, 5-30 min, user present)         → Pattern 2
```

`/prep + /auto` is the canonical Pattern 3 trigger. Build pipelines always warrant the cron heartbeat + files-first tick architecture, regardless of whether the user is present. The session may idle or compress and the cron survives both — a CLOSED window does kill it (session-only crons), which is why every checkpoint leaves the runbook resumable via `/auto resume slug=<slug>`.

When in doubt for shorter tasks, prefer Pattern 2 over Pattern 1.


## Sub-agent Delegation — fan-out & context offloading

Three execution disciplines that keep /auto fast, survivable, and high-quality on long jobs. All delegate to throwaway sub-agents (the `Agent` tool) with isolated context, so the **driver's own context stays lean**. A sub-agent never inherits the session history — construct exactly the scope + inputs it needs, and take back only its conclusion (or, for the function author, its finished code).

### Fan-out — same action × N independent items

When a runbook step is "do the same check/action to N independent items" (verify 200 render outputs, validate N config files, pre-flight N source clips), do NOT loop through them in the driver's context.

```
Trigger:  N >= ~5 independent items, no shared state, same operation
Below 5:  just loop inline (KISS — fan-out overhead isn't worth it)
```

Procedure:

- Dispatch one sub-agent per item (or per batch of items), concurrency capped at **~8-12 at a time** — not unlimited; match the machine, don't thrash it.

- Each sub-agent returns a **structured verdict ONLY** — `pass`, or `fail + reason + item id` — never raw logs/output.

- Merge into one step verify result. The step PASSES iff every item passes. Failures list the offending item ids → those become fix-mode targets.

**A non-answer is a failure, never a pass.** A sub-agent can crash, hang, or return garbage. Handle it explicitly — silence must not be read as success:

- **No verdict / unparseable / hallucinated item id** → that item is `fail (no verdict)`. Never count a missing `pass` as a pass.
- **Hang** → give each sub-agent a deadline; on expiry the item is `fail (timeout)`.
- Validate every returned item id against the set you dispatched; an id you didn't send is `fail`.

This is the operational form of the "launch independent parallel steps" note: wall-clock collapses to the slowest single item, and the driver's context never fills with N items' worth of detail.

### Context offloading — keep the driver lean

The driver's context is the scarce resource on long jobs; when it fills, the session compacts and quality drops. Offload heavy reads so the bulk never lands in the driver.

- Any discovery/read that pulls large content into the driver's context but isn't needed verbatim afterward — scanning a large file, grepping a big tree, reading many files to locate something — delegate to a throwaway sub-agent that returns **ONLY the conclusion** (the path, the line, the answer).

- The driver keeps decisions + state; the raw content stays in the sub-agent's disposable context and is discarded.

```
Offload:  "find which of these 40 files defines X" → sub-agent returns the path
Don't:    content you must edit or quote exactly   → read it directly in the driver
```

**Re-confirm before acting on a returned pointer.** The sub-agent's context is discarded, so its answer can't be audited later — a wrong or hallucinated path would silently send the driver editing the wrong file. Before acting on a returned path/line, the driver does one cheap check that it exists (a `Read` of that line, a `Test-Path`). Confirm, then act.

This is the long-job survival lever: a lean driver runs a multi-hour pipeline end to end without hitting the context wall.

### Function-author sub-agent — dedicated writer for load-bearing functions

A driver juggling the whole run (runbook, verifies, logs, monitors) one-shots functions minimally — working, but bare. For the functions that carry the pipeline, delegate the WRITING itself: dispatch a throwaway sub-agent whose only job is that one function, hand it an explicit context packet, take back the finished code, and verify it exactly like any other step output.

**Trigger — either one fires:**

```
1. AUTHOR-classed — the function is tagged RISKY by /prep (source-1 runbooks),
                    OR promoted by the classification review below,
                    OR any checklist line below is YES — or even UNCERTAIN
                    (ties promote to AUTHOR, never demote):
                      - touches subprocess/ffmpeg, network, or disk I/O
                      - transforms the user's actual data (not config plumbing)
                      - implements retries, recovery, or checkpointing
                      - sits in the main loop / hot path of the pipeline
                    All lines NO → INLINE (glue, config, small helpers).
2. Escalation     — a function-write step's verify has failed 2 distinct
                    approaches in fix mode AND the leading hypothesis implicates
                    the function's own implementation (not a fixture, caller,
                    input, or environment — P11: never rewrite on a disproved
                    or untested cause). Then the next approach IS the author
                    dispatch, counting as one of the five distinct approaches.
                    On prep-derived steps where fix mode runs as a /repair
                    sub-loop, "2 failed approaches" = 2 failed fix attempts
                    inside that sub-loop.
```

INLINE-classed functions (path joins, small wrappers, arg parsing) are written inline — KISS (P5). Non-build tasks (fixes, renames, config tweaks) have no one-shot classification *reviewer* — but the write-time checklist runs on every new def on EVERY run shape, and the first step that writes or rewrites any def creates the Functions block (an AUTHOR label earned on a non-build run triggers the author dispatch under the same one-author bound; `Classified:` stays `n/a`). See FnReview "State".

**Classification table + one-shot review (runbook generation).** For build tasks, every function the plan names gets an explicit `AUTHOR` or `INLINE` label in the runbook's `Functions:` block, with a one-line reason that NAMES the deciding checklist line (`AUTHOR — disk I/O`, `INLINE — all four checklist lines NO`) — the call is re-checkable later, never just asserted. Then ONE cheap reviewer sub-agent — fresh context, handed ONLY the Goal + Success line and the labeled list with reasons, with a deadline (Pattern 3: shorter than the tick interval; timeout = returned nothing) — answers a single question: *"which INLINE function could wreck the user's outcome if written half-assed?"* Every VALID flag (validate names against the list you sent; unknown names are ignored + logged) is promoted UNCONDITIONALLY, and the promotion is written on paper: rewrite that function's `Functions:` line in place to `AUTHOR (promoted) — <reviewer reason>` BEFORE any step executes. If every function is already AUTHOR, skip the dispatch and set `Classified: clean` with a `no INLINE candidates` log line. Reviewer returns nothing → retry once; still nothing → set `Classified: checklist-only`, log it, proceed — this leniency is the reviewer's alone (it is a second net, not an oracle) and NEVER extends to verify verdicts, where a non-answer stays a failure. The review's state rides in the runbook Status block as `Classified:` (`pending` before dispatch → `clean` / `checklist-only` on completion) so it survives compaction like `Refuter:`; a resume finding `pending` re-runs the reviewer before executing steps.

**Mid-run functions + the one-way ratchet.** The Functions block is the generation-time record, not a cage: any function born AFTER classification (fix mode, approach rotation, plan drift/renames) is classified by the same checklist AT WRITE TIME, appended to the block with its reason, and logged — no function is ever written unclassified, and a block entry whose function no longer exists is inert. Labels ratchet one way: INLINE may be promoted (reviewer flag or a fresh checklist read), AUTHOR is never demoted mid-run — same freeze discipline as the Success line; if the block shows a demotion contradicting a promotion log line, trust the promotion and restore it. The swallow-read applies to INLINE writes too: before a step's verify, re-read any just-written INLINE function for failure-swallowing, same rejection rule as author returns.

**The context packet.** The sub-agent inherits no session history (delegation rule above), so the driver constructs the packet explicitly:

```
- Goal + Success line, verbatim from the runbook
- The function contract: name, inputs → outputs, callers, data shapes
- The surrounding code it must fit (the stage file / module it lands in)
- Source-1 functions: that function's /prep card verbatim (RED/GREEN/REAL/AUDIT)
- Constraints in force: bounded retries on subprocess/network/disk calls,
  checkpointing for long operations, perf/storage limits from the plan
- The step's verify check (what the function must survive)
- Escalation only: the failing version + both failure signatures — snapshot
  these into the packet BEFORE Re-entry hygiene's restore reverts/deletes them
- Fix-trigger defs (any author dispatch, build or non-build runbook): the
  failure signature, the P11 hypothesis list, and APPROACHES.md — at write
  time, not only on escalation — so the author writes against the locked
  cause (FnReview item 9 checks it)
```

**Return contract.** The author returns ONE function + a ≤3-line note on what it optimized for — never edits to surrounding files; the driver is the only writer. One dispatch may cover one tightly-coupled unit (a mutually recursive pair, a function + its class) when splitting would hand the author half the logic. Before integrating, the driver READS the returned code for silent failure-swallowing (bare `except`, default-return-on-error) — a swallow that would let a shallow verify pass while hiding failure is a REJECTED return (one failed approach), not a pass. Then integrate and run the step's normal verify. Standard rules hold: the verify is the oracle (author confidence is not a pass), a non-answer/timeout is a failure (fan-out rule above), and fix mode on the result belongs to the driver, not the author.

**Bounds + re-dispatch (the one-author rule).** Per function: at most ONE write-time dispatch (trigger 1) plus at most ONE escalation re-dispatch (trigger 2, carrying the failure packet) — never a third; a failed escalation dispatch is never repeated (HI #4), rotation continues with non-author approaches. A dispatch that died in flight (Author dispatch logged, no Author returned line) counts as that approach's timeout failure and does NOT consume the allowance — re-entry may re-dispatch cleanly. Pattern 3: give the author a deadline SHORTER than the cron tick interval (or size the interval above expected author latency at runbook generation) — never leave a dispatch in flight past the tick that opened it. If sub-agents are unavailable, write the function inline with the same packet discipline and log the fallback.

**Log lines (model-written):**

```
[ts] [Mode] [Step N] Author dispatch: <function> (trigger: author-classed|promoted|escalation)
[ts] [Mode] [Step N] Author returned: <one-line summary> → running verify
```

**KISS bounds (P5):** no panels, no variant tournaments; one function (or one tightly-coupled unit) per dispatch — a stage with 3 risky functions = 3 dispatches; no author dispatch below the trigger just to follow the rule.

### FnReview — per-function completeness review (fresh eyes at completion)

_(Added 2026-08-22 by user directive: "have the guardian occur per function complete and run a separate reviewer that sees if it passes Heaven's principles and is a complete function or fix." Design pinned in `function-review-SPEC.md` v8 (CWD of that session); survived 1 AUDITOR + 1 RED-TEAM + 6 REFUTER rounds. Mechanism note: a cron is a clock, not a trigger, and the Goal-Guardian rule is one cron per run — so this is an in-turn subagent dispatch, NOT a second cron. The word **FnReview** is used everywhere — "reviewer" alone already means the blocker-review and the classification reviewer.)_

Every function — and every **function-level fix** — gets checked by a fresh pair of eyes **at the moment it completes**, before its step is DONE (Option B since 2026-08-22: all functions, not just load-bearing ones; reviews fan out in parallel so coverage costs wall-clock, not certainty): (1) does it follow the principles (the sweep's 5 items), and (2) is it **COMPLETE** — a structural fix / whole function, not a band-aid (HI #14): after this code, does the condition that produced the failure still exist? Does it hold next run, different input, no Claude in the loop? Does it ESTABLISH its precondition on any input, or FILTER for inputs that already have it? A VIOLATION / BAND-AID stops the step from going DONE and re-enters fix mode on the step that wrote the code. The periodic principles-sweep stays as the catch-up net; this is per-function and immediate.

**Trigger — at the step's verify PASS, when the step wrote or rewrote ANY function (Option B, user decision 2026-08-22: "I'd rather be super sure than go back and fix stuff"):**

```
(a) wrote or rewrote ANY function — AUTHOR or INLINE, happy path or not (the
    former AUTHOR-only arm is retired; AUTHOR still matters for the author
    sub-agent and for the AUDIT-step executor on /prep runbooks), OR
(b) satisfies the FIX-TRIGGER — kept as its own arm because it changes the
    PACKET (fix items + item 9) and the forced-refuter rule, not just "whether":
      fix-trigger := the step ran in fix mode (rotation, /repair sub-loop,
                     escalation re-dispatch)
                  OR the step REWROTE A DEF THAT EXISTED AT RUN START
                     (its hash differs from the run-start def snapshot —
                      structural, not verb-based: /auto /repair phases run
                      in NORMAL mode, "add retries to upload()" is a rewrite)
    Arm-2 exclusions (KISS): defs whose run-start body is a STUB (pass / ... /
    raise NotImplementedError / docstring-only — completing a scaffold is
    building), and TEST defs (test_* / *_test — a RED rewrite is covered by its
    own verify), and SYMBOL RENAMES — a step whose diff is token-substitution
    only (an identifier / function name replaced everywhere; no statement added,
    removed, or reordered; AND the old token no longer resolves anywhere after
    the step — the def/variable itself was renamed; a swap to a DIFFERENT
    existing symbol is a retarget = rewrite, arm 2 fires) is a non-function
    step even though callers' bodies change: it does not trigger arm 2; the
    decision is made from the step's Edit old/new strings or the logged
    sed/replace expression and recorded on the `Edit applied:` line (disk, not
    memory); afterwards the driver re-baselines the run-start snapshot for the
    touched files and carries affected `clean`/`WAIVED` stamps to the new hash
    `(inherited)`, same as a renamed function's own line. NOT excluded:
    prep-listed functions — a planned rewrite IS a fix.
Never fires for: steps that write no function (config, constants, data moves,
symbol renames, runs of existing code), test defs, standalone-harness defs,
/auto's own bookkeeping. So a Pattern-1 rename/config run dispatches zero
reviews — by the rename exclusion above, not by assertion. Not gated by the
guardian's Jobs: check.
```

**Dispatch shape — parallel per function, non-blocking for independent steps.** The driver names the functions it edits on the `Edit applied: <file>:<fn>` log line at edit time and reads them back at dispatch (fallback: every def in touched files whose hash differs from its reference — the later of the run-start snapshot and its `clean` stamp — else all defs). A step that wrote ONE function gets one dispatch; a step that wrote SEVERAL gets **one reviewer per function, dispatched in parallel** (fan-out rule: concurrency cap ~8–12, each returns a structured per-function verdict, a non-answer is that function's UNRESOLVED only — never the step's). The reviewer still sees the surrounding module, so a tightly-coupled unit may share one dispatch when splitting would hand the reviewer half the logic. While reviews are in flight the step is `VERIFIED (FnReview pending)` and the driver **may start the next step(s) that do not consume the reviewed functions** (no `requires:` on this step, no read of its output — the same independence test fan-out uses); a step that DOES consume them waits — the run never builds the next piece on top of an unreviewed one. A finding on a reviewed function still re-opens the producing step and invalidates any downstream step that consumed it (re-entry hygiene), so nothing built meanwhile survives a real diff unchecked. A finding is **acted on at the next step boundary** (the executing step's verify result is written first), never mid-action; `Current step:` names the executing step and the re-opened step is named in `Mode reason:`. **Step-DONE condition under fan-out:** the step goes DONE only when EVERY function's stamp reads clean / unreviewed / WAIVED; any VIOLATION/BAND-AID on any one function blocks the step; UNRESOLVED functions retry individually (tightened brief), sibling verdicts stand. **Rounds are per STEP, not per function:** one `FnReview dispatch:` log line per step-round listing all its functions (`<fn, fn, …>`), so the ≤2-rounds and ≤6-per-pass checks count lines, not reviewers; round 2 re-dispatches only functions whose stamp is not clean/WAIVED at the current hash. Pattern 3: the fan-out shares the tick's deadline; unreturned functions are carried, not the whole step.

**Timing on /prep-derived runbooks — the FnReview IS the AUDIT step.** RISKY: `N+1 Implement → N+2 REAL → N+3 AUDIT`; SAFE: `N+0 Implement → N+1 AUDIT`. The FnReview fires ONCE as the executor of that AUDIT step (after REAL — production-shaped evidence), and **both triggers are suppressed at every step preceding the function's AUDIT step** (Implement AND REAL), including after a fix-mode redo — the round-2 review fires at AUDIT again after REAL re-runs. The AUDIT step's own check ("traces to goal") is item 0 of the brief; the prep END GOAL / field-13 AUDIT card joins the packet. When the function met the fix-trigger on a preceding step, the AUDIT executor gets the fix packet and item 9 applies. SAFE functions' AUDIT steps are FnReview-executed too (Option B) — their dispatch fires after the smoke check, in parallel with any siblings finishing in the same step. **/repair-derived runbooks (`/auto /repair`, added 2026-08-22):** /repair's step 9 (Audit) IS the executor — `executor: audit-step`, item 0 graded against the Goal/Success line (no END GOAL card), dispatch log token `audit-step` — it runs with the fix packet (failure signature, step-2 hypothesis list + step-3 Lock evidence, rejected approaches), and both triggers are suppressed at steps 4–8 (Isolate through Step 2 — the step-4 standalone holds a copy of the NOT-yet-fixed def, so standalone-harness defs are exempt like test defs and never reviewed). A Mode-B /repair sub-loop inside a /prep step does NOT dispatch at its own step 9 — the function's AUDIT step stays the single executor; if that AUDIT step is already DONE, the rewrite re-opens it (→ PENDING on a real diff) and the review fires there; if the function has no AUDIT step at all (a Phase 9 integration step), the self-derived rule applies — the review attaches to the writing step's verify. Self-derived runbooks (no AUDIT step): the review attaches to the function-write step's verify.

**Lifecycle — a step with a pending FnReview is not DONE.** New named state between IN PROGRESS and DONE, written on the step line:

```
IN PROGRESS → VERIFIED (FnReview pending) → DONE        (review clean)
VERIFIED    → BLOCKED                                    (finding → fix mode on the PRODUCING step)
BLOCKED     → PARKED (FnReview round 2 still open — finding quoted)
PENDING     → PARKED (dependent of step N FnReview PARK)  (AUDIT + any consumer still PENDING;
                                                          reason token `dependent:N`)
```

When the VERIFIED step and the producing step differ (/prep-derived runbooks: AUDIT vs Implement/REAL; /repair-derived: step 9 vs step 7 Integrate), the **producing** step — the one whose `Edit applied: <file>:<fn>` line last wrote the function, never a fixed step number — carries BLOCKED/PARKED and the stamp; the AUDIT step goes → PENDING unconditionally (its verify IS the failed review), REAL/other consumers → PENDING on a real diff of the rewrite (HI #4). Never two BLOCKED steps for one finding. On a round-2 PARK the consumers park with it as dependents (no round 3, no re-run on the band-aid) and un-park together at guardian tick step 8 / refuter door 3.

**Resume / tick pickup of a VERIFIED step — no restore, no redo.** Check each function's current hash against the `sha:` on its `pending` stamp (the cheap intact-proof — not a re-run of a possibly long REAL verify): match → re-dispatch; differs → the step drops to IN PROGRESS and the normal door-2 restore + fix mode apply. Re-entry door 2 does NOT fire on an intact VERIFIED step. A dead-tick / Esc-killed pending is re-dispatched without consuming a round, at most twice (count = `FnReview dispatch:` lines with no `returned:` line); a pending carried without a dispatch (Pattern 3, window too short) is counted from `FnReview carried:` lines — after 2 carries the 3rd tick dispatches regardless of window with a tightened deadline; a timeout there stamps `unreviewed @<ISO> (carried ×2, timeout)` directly (skips retry-once — the tighter bound is the point). Third dead pickup → `unreviewed @<ISO> (dead-tick ×2)`. Bounded — never a wedge until the spend gate.

**The context packet.** Fresh general-purpose subagent, read-only probe license (Read/Glob/Grep; writes forbidden). Hand it: Goal + Success line (GOAL.md); each function's contract (name, inputs → outputs, callers); each function's CURRENT code on disk (file + the hasher's line range — the reviewer reads from disk, nothing pasted from memory) + the surrounding module; the step's verify check + PASS evidence; an explicit `executor: audit-step | step-verify` marker; AUDIT-executor only: the END GOAL card + field-13 AUDIT card; **fix-trigger only:** the failure signature, the P11 hypothesis list, and APPROACHES.md (from fix-mode log lines, or from /repair's Hypothesize/Lock steps on a NORMAL-mode repair step); **every packet with no failure signature carries the marker `no failure signature`** (all non-fix dispatches, and fix-trigger ones with none). It does NOT get the driver's opinion, the author's note, or conversation history.

**The brief + fixed checklist:**

```
You did NOT write this code. You are the FnReview. Read each function from
disk. For each function, for each item, return exactly one of CLEAN /
VIOLATION (items 0-5) or COMPLETE / BAND-AID (items 6-9), each WITH
file:line evidence — CLEAN and COMPLETE need a citation too (the line that
satisfies the item). Item 9 may return N/A only when the packet says
`no failure signature`; item 0 may return N/A only when executor is not
audit-step. Use no other severity words. A VIOLATION is a concrete breach,
not a style nitpick. Do not rubber-stamp.

 0. GOAL-TRACE (audit-step executor) — does this function advance the Goal /
    Success line and the prep END GOAL card?
PRINCIPLES (same 5 items as the principles-sweep):
 1. HEAVEN'S NET — RECOVERY keys to evidence-mapped failure classes, never
    "symptom string X → do Y"; unmatched/assumed signals are captured, parked,
    fail loud (canonical: /error-recon). Guardrails: DETECTION may match
    mapped symptoms — it is the recovery that must be class-level; and ≤2
    handlers need no taxonomy (rule of three). Do not flag either.
    1b. PROPORTION (same canonical section) — a recovery that rests/retires
    capacity or pulls a pool sizes its cooldown / bench / share from an
    OBSERVED recovery measurement (cite where) or a bounded ≥×2
    smallest-first ladder; a guessed constant or wrong scope is a
    VIOLATION in either direction (90 s rest for a ~24-min throttle;
    rest-till-midnight on a string that may mean a 60 s limit; N members
    retired for a pool-wide blip). A signal mapped to two entries of
    different size that jumps to the larger (or a bespoke 'both' handler)
    instead of a smallest-first ladder is the same VIOLATION. Bounded
    growing backoff IS the ladder — do not flag it. Item 1 returns two
    verdicts, keyed `1` (class) and `1b` (proportion); a size finding
    filed as `1` is re-keyed `1b`.
 2. EVIDENCE-ONLY — no success from labels/exit codes alone.
 3. RE-ENTRY HYGIENE — retry/resume rolls back residue → re-asserts the
    precondition → invalidates downstream before redo.
 4. NO SILENCED FAILURES — no bare except/pass, no unbounded retry, failures
    surfaced by count, flight-recorder capture on unknowns.
 5. KISS — no abstraction the task didn't earn.
COMPLETENESS (COMPLETE or BAND-AID, with evidence):
 6. CONDITION TEST — name the condition that produced the failure / the gap
    this function closes. After this code, does that condition STILL EXIST?
    (yes → BAND-AID; name the surviving condition.)
 7. NEXT-RUN TEST — next run, different input, no Claude in the loop, nobody
    watching: does it still work? Cite what in the code makes that true.
 8. ESTABLISH-vs-FILTER — if the function needs a precondition, does it
    ESTABLISH it on any input, or FILTER for inputs that already have it?
    (filter → BAND-AID.)
 9. CAUSE-LOCK (fix-trigger only) — does the fix target the CONFIRMED cause
    from the hypothesis list, or route around the symptom? Was the leading
    hypothesis confirmed by a discriminating probe, or merely not disproved?
    (HI #13)
```

**Verdict handling — bounded at every exit:**

- **Write first, act second.** The `FnReview returned:` log line is written the instant the verdict lands, before any action.
- **Staleness validation.** A finding citing a function whose hash changed after the reviewer read it is discarded with one log line (hash, not file mtime — a neighbour's edit never discards a live finding). Every finding discarded → the dispatch is UNRESOLVED (not CLEAN), consumes one leniency slot, re-runs on current code.
- **Vocabulary is closed.** Any cited item verdict that is not CLEAN/COMPLETE blocks ("CONCERN", "borderline" → VIOLATION/BAND-AID). An uncited item verdict is UNRESOLVED — except a **legal N/A**, which the DRIVER checks against the packet it sent (item 9 ↔ `no failure signature` marker; item 0 ↔ `executor: step-verify`); an N/A that fails the check is UNRESOLVED.
- **Citation re-confirm.** The driver re-reads the cited line (±10). Quoted evidence present → the finding stands (a moved line is corrected in the log, not excused). Evidence absent from the function entirely → that item is UNRESOLVED (retry with "cite the exact line"). Leniency never clears a finding whose quoted evidence IS in the code.
- **VIOLATION / BAND-AID → map to the producing step, then BLOCK it.** Fix mode opens with the finding as the failure signature (P11 list → discriminating probe → approach on the confirmed cause). The function-author escalation re-dispatch is available within the one-author bound. Re-entry hygiene runs first; AUDIT → PENDING unconditionally, REAL/consumers on a real diff.
- **Fresh approach budget per review round + the aim-test gate.** `Approaches tried` resets for the re-opened step (5 per round). Before a re-opened step may re-enter VERIFIED / DONE, the driver runs the HI #14 aim-test on its fix and logs it — `aim-test: <condition> removed? yes — <how> | no` — a `no` (or an item-8 filter the driver can see itself) is a failed approach: rotation continues, no dispatch. Honest bound: **≤2 verify-passing, aim-test-passing attempts per step per guardian pass**, ≤5 approaches each. The aim-test is a cheap self-filter, not independence; the verify stays the oracle for "works", the FnReview for "complete".
- **Bound: max 2 FnReview rounds per step per guardian re-attack round** (mirrors the refuter). Round-2 still VIOLATION/BAND-AID → the producing step is **PARKED**, stamp `open <finding> (round 2) → PARKED @<ISO>`; blocker-review / re-attack owns it (Round K/3). A guardian un-park + redo that passes verify is reviewed **again with a fresh 2-round allowance**; same after a refuter door-3 re-open. Finite: ≤6 review rounds per guardian pass × 4 passes = ≤24 per step, worst case; the ≤6-per-pass check is derived from `FnReview dispatch:` lines since the last Round increment.
- **Open-finding DONE gate.** While any Functions line reads `open …`, `Status: DONE` is not written: the Terminal Refuter fires **even on a machine-checked goal** (the HI #11 override shape; `Refuter: n/a → pending` when forced — the RedTeam precedent — so the Stop-hook carrier holds), with the finding named. Forced brief adds: *"For each named open / unreviewed line return exactly BLOCKER or WAIVED(<citation>); a confirmed BAND-AID (HI #14 aim-test + items 6–9) is a BLOCKER even though the Success line is machine-green."* Silence/CONCERN/NOTE on a named line = UNRESOLVED → retry once → second UNRESOLVED falls to the refuter's same-context skeptic fallback, which must rule BLOCKER(<cited unmet item>) or WAIVED(<citation>) — never a BLOCKER without a named item, never a mute subagent turning a green goal into STUCK-user. Blocker-review's FALSE-BLOCKER is not a waiver — only a cited WAIVED closes an open finding.
- **WAIVED exit.** A finding that contradicts a recorded Design Decision in notes.md (or a recorded /prep spec-card decision), or a user-requested `BAND-AID (user-requested):`, is closed `WAIVED @<ISO> (<citation>)` by the driver, blocker-review, or the refuter; counts as resolved; lands in Open Questions. Waiving requires a citation — never "reviewer was wrong".
- **Never a user gate.** Passes silently or re-enters fix mode within the bound; surfaces only in the log, the stamps, and the final report.

**Evidence rules — leniency for a dead dispatch, never for a verdict.** UNRESOLVED = no citations, all findings hash-discarded, errored dispatch, or timeout (a legal N/A is NOT unresolved). Any UNRESOLVED → retry once per UNRESOLVED function (tightened brief; returned sibling verdicts stand) → second UNRESOLVED → that function is `unreviewed @<ISO> (<reason>)`, one log line, and the step proceeds DONE once every function is clean / unreviewed / WAIVED — the FnReview is a second net, not the oracle (same leniency the classification reviewer has). The leniency NEVER extends to a cited VIOLATION/BAND-AID. An `unreviewed` stamp is not forgotten: the sweep still covers that function, the refuter is told, and on a **fix-trigger** function an `unreviewed` stamp forces the refuter even on a machine-checked goal — the user's headline case (a fix) always gets one independent look on every run shape. Honest residual: an `unreviewed` happy-path function on an inline machine-checked run gets no further look (status quo). Pattern 3: reviewer deadline SHORTER than the tick interval; the interval is sized **at runbook generation for author + review + sweep combined**; a dispatch that can't fit the remaining window stays `pending` and is carried (log `FnReview carried:`) — never straddles the tick.

**State — on paper, compaction-proof.** Per-function review state rides on the runbook **Functions block** line. **Non-build runs** have no block today — the first step that writes or rewrites any def **creates it** (write-time checklist label; rewritten defs tagged `(fix)`); the write-time checklist runs on every new def on every run shape (the one-shot classification *reviewer* stays build-only; `Classified: n/a` on non-build runs). An AUTHOR label earned on a non-build run also triggers the function-author dispatch under the one-author bound, and **any author dispatch for a fix-trigger def carries the fix items** (failure signature, hypothesis list, APPROACHES.md) at write time, not only on escalation.

**Run-start def snapshot.** Before the FIRST edit to any deliverable file in the run, record that file's per-def hashes (the hasher below, no other) in PROGRESS.md (create it if the run shape has none — every run has it under the Goal-Guardian rules) (`snapshot: <file> <fn> sha:<8> …`) — the reference for arm 2 and the fallback; a def absent from it is new code. PROGRESS.md already carries long-lived sections (baseline, mirrors); snapshot + FnReview ledger join them as named sections that every tick's PROGRESS write **section-merges, never overwrites**.

**The hasher (one procedure, same result on every tick):** `.py` — slice the source lines EXPLICITLY from `min(d.lineno for d in node.decorator_list)` (or `node.lineno` with no decorators) through `node.end_lineno` of the `ast` FunctionDef/AsyncFunctionDef — NOT `ast.get_source_segment(node)`, which on Python ≥3.8 starts at the `def` line and silently drops decorators (verified 2026-08-22 on 3.11) — replace the **def-line name token only** with `_` (recursive self-calls unmasked — a recursive rename reads stale, accepted as conservative), normalise line endings, strip TRAILING whitespace only (never indentation — a dedent changes control flow), sha256 → first 8 hex. Non-Python deliverables: whole-file hash, file treated as ONE unit (coarser, never wrong; accepted residual: a neighbour's edit there does invalidate). Removing `@retry` or changing a default arg invalidates a stamp; a rename or a neighbour's edit does not. "Edited after the stamp" is decided from disk — file mtime as the cheap pre-check, hash difference as the verdict (HI #8) — never from this run's log (it cannot see a human's or another run's edits).

Stamp vocabulary (closed; the round count lives on the stamp):

```
review: n/a
review: pending (round k) sha:<8>               ← in flight / carried; sha = hash at the instant the stamp
                                                  is written (step verify PASS; AUDIT-step entry on /prep; step-9 entry on /repair)
review: clean sha:<8> @<ISO> [(item 9 n/a)]
review: round k VIOLATION item n → fix mode     ← finding mapped, producing step BLOCKED
review: open <finding> (round 2) → PARKED @<ISO> ← DONE gate until WAIVED/cleared
review: unreviewed @<ISO> (<reason>)
review: WAIVED sha:<8> @<ISO> (<citation>)

Functions:
  fetch_clip:    AUTHOR — disk I/O | review: clean sha:3f9a1c2e @2026-08-22T03:40Z
  retry_upload:  AUTHOR — retries  | review: open BAND-AID item 8 (round 2) → PARKED @...
  join_paths:    INLINE — all NO   | review: n/a
  parse_flags:   INLINE (fix)      | review: clean sha:… @... (item 9 n/a)
  fetch_video:   AUTHOR — renamed from fetch_clip @... | review: clean sha:… @... (inherited)
```

Status-block summary field: `FnReview: n/a | <k> pending | <n> in fix | clean | <n> open | <m> unreviewed`. A function rewritten after a `clean` stamp gets `pending` at its next verify PASS (review is per completion, not once per name); a renamed function carries its stamp (`renamed from X`, hash still matches); a function with no stamp is reported to the refuter like `unreviewed`. FnReview rulings live in their **own ledger keyed (item, file, function)** mirrored to PROGRESS.md — NOT in the sweep's (item, file) ledger (a file-keyed entry would blind the sweep for every other function in that file).

Log lines (model-written, mirroring the author lines):

```
[ts] [Mode] [Step N] FnReview dispatch: <fn, fn, …> (trigger: new-def|author-classed|promoted|fix-mode|rewrite-existing|audit-step; round k)   ← ONE line per step-round, all functions listed
[ts] [Mode] [Step N] FnReview returned: <fn>: CLEAN+COMPLETE | VIOLATION item k file:line | BAND-AID item k <condition> → <DONE | fix mode on step M | PARKED | unreviewed>
[ts] [Mode] [Step N] FnReview carried: <fn> (window too short; carry 1|2)
```

**Interplay with the principles-sweep.** The sweep is unchanged in cadence and becomes the catch-up net (non-function edits, `unreviewed` functions, anything a stale `clean` no longer covers). The DRIVER (which has the hasher — the sweep subagent does not) recomputes each stamped function's hash at dispatch and passes ONLY the still-valid ranges as `reviewed-clean ranges: <fn> L<a>–<b> @<ISO>` (the range IS the hasher's slice); the sweep does not flag inside those. Inside a tick the step-7 sweep rider dispatches AFTER the step's FnReview has returned and written its ledger entries — "alongside" reads as same-tick, sequenced. The sweep's 5-step cap is unchanged; FnReview-driven fix-mode re-entries do NOT count against it.

**Interplay with the Terminal Refuter Gate — unchanged sequence, two forced-fire triggers, better informed.** (0) A **universal pre-DONE pending check** on EVERY DONE path (inline end-of-run, guardian SUCCESS PROBE in tick step 5, the machine-checked skip path) BEFORE "When it fires" / HI #9: no step in `[VERIFIED — FnReview pending]`, no `FnReview: k pending` or `n in fix`; if any holds, the carried review is dispatched and returned first. A finding at that check discards the "Met" verdict and falls to tick step 7 (fix mode on the producing step) — never step 8, so it never burns a guardian Round; an `in fix` carried from a prior tick routes the same way. PARKED steps are allowed (the all-parked checkpoint is untouched); an `open`-PARKED line is the forced refuter's INPUT. (i) An `open` finding or a fix-trigger `unreviewed` stamp forces the refuter even on a machine-checked goal. (ii) At gate entry the driver hands the refuter the Functions block and names every `open`, `unreviewed`, no-stamp, WAIVED line and every function whose current hash differs from its `clean` sha — "not independently reviewed, look there first". A stale `clean` must never read as coverage. Residual: on a machine-checked goal with nothing forcing the refuter, an out-of-run edit after a `clean` stamp is named to a refuter that never fires (status quo).

**Re-entry hygiene — door 5.** A FnReview finding re-opens a step whose verify passed: the standard restore runs on the producing step (rollback → pre-verify → invalidate downstream on a real diff; AUDIT → PENDING unconditionally).

**Cost + KISS bounds (P5):** one reviewer per function, dispatched in parallel within a step; ≤2 rounds per step per pass; a 40-function build = ≥40 reviews, but wall-clock ≈ the slowest single review per step because they run side by side (user's call 2026-08-22: certainty over dispatch count). No panels, no voting, no tournaments. No review for non-function steps, test/harness defs, or trivial runs. The checklist is the sweep's 5 items + goal-trace + 4 completeness items — not a new taxonomy. Sub-agents unavailable → same-context skeptic pass marked as the weaker fallback, exactly like the refuter's.


## Universal Principles (apply in both shapes)

These are the principles that make /auto trustworthy regardless of execution shape.

### 1. State the goal in one sentence before starting

Even on tiny tasks. If Claude can't compress what it's trying to do into a single sentence, it doesn't understand the task well enough to drive it.

### 2. Define the success condition before doing the work

Per `principles` skill P2 (figure out the conditions upfront): success must be observable, not vibes. "It compiles" isn't enough. "It compiles AND `pytest tests/` exits 0 AND no new warnings in the log" — that's a success condition.

### 3. Approach rotation on failure

Maintain (in memory or in `APPROACHES.md` if cron mode) a record of every distinct approach tried. Before retrying, confirm the next approach genuinely differs. Five strikes → STUCK.

### 4. Evidence-based judgment

Every "PASS" claim must point to a specific artifact: a log line, an exit code, a file existence + size match, a probe result. "It looks done" is not evidence.

### 5. Default to action, not menu

When a step has an obvious next move, take it. Only present a choice when there are genuinely competing directions the user must decide between — and even then, lead with a confident recommendation, not an open menu.

### 6. Bound the spend

Even with no-gates, Claude doesn't burn unlimited resources. Reasonable defaults:

- Max 5 distinct approaches per failing step.
- Max 2 full re-runs of expensive operations (e.g. full pipeline run, large API batch) without checking in.
- For irreversible / cross-system / shared-state actions: still warn before executing, even in /auto mode (see "Auto does not waive..." below).

### 7. Honest end-of-task report

```
=== AUTO REPORT ===

Goal:        <one sentence>

Status:      DONE | PARTIAL | STUCK

Result:      <what actually happened, with numbers>

Toward goal: <how this moves the goal forward, honestly>

Failures:    <every failure surfaced, not buried>

━━ CURRENT STAGE ━━

BEFORE:   <the state before this run's work — one plain sentence>

NOW:      <the state right now — what exists, what's verified, what's still waiting>

CHANGED:  <what changed and WHY — the evidence or decision that moved it>

NEXT:     <the immediate milestone between here and the ultimate goal — "none" if fully reached>

MEANT TO: <what NEXT is supposed to achieve in the system + the specific problem it fixes>

FEYNMAN:  <NEXT re-explained to a smart 12-year-old, one everyday analogy, zero jargon — how it fits Heaven's Net AND the ultimate goal>

━━ ULTIMATE GOAL (4 lenses, derived from THIS run's scenario — frozen) ━━

Delivers:   <the finished result that arrives with zero input from the user>

Heals:      <how failures recover or surface themselves, no human needed>

Replaces:   <whose job/attention the system deletes — nobody left in the loop>

Guarantees: <what wrongness is structurally impossible>

━━ SUGGESTED ACTION ━━

PASTE THIS: <the answer to THIS TURN'S question, pasted verbatim as the next message. Turn ended on a PICK → the pick in the user's voice + one line of why ("Go with Choice 2 — <why>"); the work-prompt waits for the next turn. Turn was a DO-IT request → the work prompt: what / which files / limits / corrected facts / what to show or ask before anything costly. "nothing — goal reached" if DONE>

→ TOWARD THE GOAL: <a CHAIN, not a tag: "this move → gets us <concrete thing> → which is what <lens> needs because <why>", per lens pushed + what the rejected option would have cost>

→ HEAVEN'S NET: <why we can proceed with confidence. On a PICK: (1) SEEN evidence the pick stands on, (2) what the other options were ruled out on (same evidence), (3) how we'd know fast if wrong + bounded fallback; unchecked things NAMED — never "n/a" on a pick. On a WORK STEP: how it leaves a STRONGER system — class-keyed recovery, evidence-only detection, bounded tries, fail-loud — or "n/a — no recovery logic in this step">

━━ GRADE ━━

Confidence:  PERFECT | HIGH | MEDIUM | LOW — <what was verified directly vs inferred vs assumed>

Risk:        HIGH | MEDIUM | LOW — <what's exposed if this report is wrong; which parts are unproven>
```

The report is the contract. If it says DONE, it's done. If it says PARTIAL, it lists exactly what's missing.

**Result-gap first (P12, 2026-08-12):** whenever the user's deliverable is not fully
met, the report LEADS with what the user still doesn't have — before any wins.
Shipped machinery is reported as progress-toward, never as the headline. Claims are
tagged VERIFIED (observed) / ASSUMED (inferred) where the difference matters. An
external dependency dead >~2h is reported as an incident with a reroute, never as
"retrying, fine."

**Confidence + Risk are mandatory and evidence-tied.** The scale:

- Confidence PERFECT — the 100%-guaranteed, full-autopilot grade. Requires ALL of: every angle empirically tested (happy path AND failure/recovery paths, on real inputs at real scale — the P1/P9 bar), every verify directly observed this run, zero pending/external anything, an independent adversarial check (Terminal Refuter or an equivalent discriminating test) tried to break it and failed, AND the autopilot itself was PROVEN — the deliverable ran (and recovered) end-to-end with no human thought, no human decision, no human intervention, and no Claude in the loop (the structural-fix bar: next run, different input, nobody watching, still works). The evidence clause must NAME the tests that covered each angle, including the unattended-run proof. One untested angle → HIGH at best. PERFECT is the only grade that licenses "walk away, it needs zero human input" — a false PERFECT is the worst failure the footer can commit.
- Confidence HIGH — every claim above was verified this run (exit codes read, artifacts checked, shots read), but not every angle was adversarially tested. MEDIUM — core verified, some parts inferred or reported secondhand by a tool. LOW — key claims rest on assumption or an external service's say-so.
- Risk LOW — nothing pending, wrongness is cheap/reversible. MEDIUM — unverified pieces exist; wrongness costs rework or delay. HIGH — unverified pieces touch production, shared state, or user-facing output; wrongness ships something bad or blocks the pipeline silently.
- **Hard cap:** any "waiting", "queued", "retrying", "should", "expected", or dependency on an external recovery anywhere in the report → Confidence cannot be HIGH. If the Status says DONE but a claim would need the cap, the STATUS is wrong — downgrade to PARTIAL; never inflate the rating to match the status.
- A bare grade with no evidence clause is invalid. The dash and the justification are part of the line.

**Goal-compass rules (anti-drift):** `Ultimate goal` is derived fresh PER RUN from the current scenario — the end-state of THIS objective, not a generic principle. Frame it at the systems level, from the user's seat (a human building automation so they never have to give input), through ALL FOUR lenses: **Delivers** (factory view — the finished result that arrives with zero input), **Heals** (organism view — failures recover or surface themselves), **Replaces** (operator view — whose job/attention the system deletes), **Guarantees** (structure view — what wrongness is impossible by construction). Fill every lens; a lens that genuinely doesn't apply gets "n/a — <why>", never a silent skip. Write each lens in the user's confirmed style (8/13/26): concrete and first-person from their seat, real actors and real stakes ("me", "the VA", "at 2 AM"), good state contrasted against bad ("delivered correct" vs "wrong and quiet"), consequences stated ("one bad item never costs the other 200") — never abstract boilerplate. Once stated the block is FROZEN (same freeze as the Success line): never quietly reworded toward what was achieved, because that rewording is exactly the drift the user wants to be able to catch by comparing the block against their original ask. `NEXT` (inside CURRENT STAGE — it replaced the old Next-step line, 8/22/26) is the immediate milestone between here and that goal; `MEANT TO` states what NEXT achieves + the problem it fixes; `FEYNMAN` re-explains NEXT to a smart 12-year-old with one analogy and must name both the Heaven's Net fit and the goal fit. `SUGGESTED ACTION` is ONE move, not a menu (v3 8/22/26): `PASTE THIS` answers THIS TURN'S question — on a pick it IS the pick in the user's voice + one line of why (the after-pick work prompt waits for the next turn; writing it now skips the question and reads as drift); on a do-it request it is the complete standalone work prompt (what / files / limits / corrected facts / what to show-or-ask before anything costly); `→ TOWARD THE GOAL` is a chain in plain words, never a bare lens tag — this move → gets us <concrete thing> → which is what <lens> needs because <why>, per lens pushed, plus what the rejected option would have cost — an action whose chain doesn't connect to the goal is drift and must not be suggested; `→ HEAVEN'S NET` answers "why can we proceed with confidence?": on a pick = (1) the SEEN evidence the pick stands on, (2) what the other options were ruled out on — same evidence, not vibes, (3) how we'd know fast if it's wrong + the bounded fallback, with anything unchecked NAMED, never "n/a"; on a work step it follows the canonical definition in error-recon (class-keyed recovery toward required state, evidence-only detection, bounded, fail-loud — read it, don't paraphrase from memory; "n/a — no recovery logic in this step" only when a work step has none). Layout: one blank line between every field; labels fixed, explaining text plain-language.

Before emitting DONE on a **judgment-based** goal, the report must have passed the **Terminal Refuter Gate** (see below) — on those goals, DONE is the refuter's verdict, not the driver's self-grade.


### Build for the real run (P9 — practicality)

Judge every step and the final verdict against the REAL operating envelope, not the demo: the real input size, the real run duration, unattended execution, messy/missing inputs, resource limits, and recovery after a partial failure. A green run on a small or clean sample is NOT DONE if the real job is bigger, longer, or dirtier — verify against the conditions the task will actually meet. This covers only conditions you can prove will occur; a safeguard for an imaginary case is still a P5 (KISS) violation, not practicality.

Most of /auto's machinery already serves this — the self-derived verify sanity pass (P1), stage-mode's different-input re-run, disk-is-truth (#8), the escalation tree (heuristic #13), checkpointed cron state, and the Terminal Refuter's "holds on a different input with no Claude present" check. P9 is the name that ties them together and the bar the final report is judged against. (Unnumbered on purpose — the numbered list 1–7 continues into the Operational Heuristics' #8–14, so this anchor sits outside that run to avoid renumbering them.)

## Operational Heuristics — patterns from production runs

The principles above are abstract. These seven are the tactical patterns that make /auto trustworthy on long-running, real-world systems (pipelines, services, vendors). Born from real incidents.

### 8. Disk is source of truth when logs go silent

Logs lie, get redirected, or get lost (e.g., a background process launched with hidden window loses stdout). When the log isn't moving, do NOT assume work has stopped. Go to the artifact layer:

- File counts in the output directory
- File mtimes on intermediate state files
- Manifest `status` fields written by the worker
- Database row counts, S3 object counts

The artifact is the contract. The log is commentary on the artifact. If they disagree, trust the artifact.

### 9. Cite the incident in every patch comment

Every fix landed under /auto should have a one-line comment naming the **incident** that motivated it — date + failure signature + verified evidence. Not "fix bug" but:

```python
# Bumped 15→30 on 2026-05-12 — vendor's shared-pool/assign can take
# 20+ seconds under load (verified: crashed Spanish V3 stage 3).
```

Future readers (including future Claude) see WHY, not just WHAT. P5/P7 KISS-surgical changes are good, but a surgical change with no rationale becomes mysterious in a year.

### 10. Hand-test the recovery before baking it in

When diagnosing a stall and designing a fix, the order is:

1. Diagnose the failure mode with read-only probes
2. **Hand-test the fix** via direct API calls / shell commands / one-shot scripts
3. Observe recovery (artifact-level evidence — not just "200 OK")
4. **Then** write the code that automates the recovery

Hand-testing first means the patch is grounded in a *working sequence*, not a guess. The cost is ~10 minutes; the benefit is committing code that's been proven against the live failure mode. This is P1 (test-at-scale) applied in reverse — verify the manual fix, then commit.

### 11. Name what changes apply to THIS run vs NEXT run

When patching code that's loaded by a live process (Python imports cached at module load, services with hot-reload disabled, daemons holding old binaries), explicitly state in the report:

```
Live farmer (PID 63700) won't pick up these changes — Python imported
the modules at 09:57. The patch takes effect on next farmer restart.
V3 + GoT will finish on the old code; FG V5-V9 (after the planner
swap restart) will get the new self-healing.
```

Avoids the trap of "I patched it" → user assumes the live run is fixed. Let the user choose: restart now to get the fix, or defer to a natural restart point. P8 — keep the goal in sight, including "when does the fix actually land."

### 12. One stall teaches a class of failures (adjacent-issue radar)

P7 says surgical changes — don't expand scope. This heuristic carves a disciplined exception: when fixing a specific stall reveals an **upstream trigger gap** that would let the same class of failures recur, fix both.

Example: a vendor pool got stuck on one account. The hand-tested fix was a force-rotation API sequence. But reading the existing rotation code revealed: the trigger condition only fired on `HTTP_403` or `THROTTLE_ERROR`, not on `ReadTimeout` — which is what we'd just seen. The patch added both the new helper AND extended the trigger to catch timeouts. One stall, two surgical edits, a whole class of stalls now handled.

The bar: the adjacent fix must be (a) one or two lines, (b) directly visible from the code path of the original fix, and (c) demonstrably needed by the same incident. Anything bigger = back to strict P7.

### 13. Escalation tree under stalls — cheapest action first, never restart first

When something stops making forward progress:

```
1. Diagnose       — what changed? (Service alive? Disk writes? Network?)
2. Differentiate  — slow (just wait) vs. stuck (intervene)?
3. Cheapest first — read-only probe, info endpoint, single-call test,
                    visual checkpoint (screenshot + read it)
4. Escalate       — release → release+assign → stop-all+release+assign
                    → service restart → host restart
5. Verify recovery via artifacts — not API success codes alone
6. Bake the fix in — the next time this happens, the system should
                     self-heal (heuristic #10 + #12)
```

Never restart the farmer / vendor / database / host as a first move. That's the loudest hammer; reach for it last. Cheap actions can succeed silently and teach you about the failure mode for free.

### 14. Heaven's Net — recovery you BUILD keys to failure classes, not symptoms

Heuristics #10–#13 govern how /auto handles ITS OWN stalls; this one governs the error handling /auto writes INTO a deliverable (stage-mode recovery, retry wrappers, healing code). Never "error string X → do Y": handlers key to a failure class (navigation / auth-session / element / timing / network / resource / unknown) and recover toward the state the operation requires — diagnose actual state → classify → recover by class → verify the invariant restored with evidence → bounded escalate, fail loud. Heuristic #12's worked example (extending a rotation trigger from two error codes to the whole timeout class) is this principle already at work. STRICT evidence caveats, non-negotiable: a runtime class comes ONLY from a matched, evidence-backed map entry — a new symptom joins a class via a new map entry, never by resemblance (unmatched = unknown: capture, park, stop loud); confidence tiers still gate which entries may run a chain; and a job-level recovery budget bounds the whole item, not just each chain. Proportion (a guardrail in that same canonical section): the SIZE of a recovery that rests/retires capacity or pulls a pool — cooldown, bench length, share of a pool — comes from an observed recovery measurement or a bounded ≥×2 smallest-first ladder, never a constant picked by feel; under-sized (hammer) and over-sized (retire healthy) are equal failures. Trigger phrase: the user saying "heaven's net" invokes this shape explicitly — read the canonical definition + guardrails in /error-recon ("Heaven's Net" section) before designing recovery; never run it from memory. KISS: 1–2 failure modes need no taxonomy; the third symptom-specific handler in the SAME class forces the refactor.


## Auto Does NOT Waive

Even under /auto, these still get flagged before execution (briefly — one sentence, then proceed unless the user objects within the same turn):

- **Destructive operations on shared state**: force-push to a remote main branch, drop production tables, delete files outside the project tree, mass-delete data.
- **Operations costing real money beyond a small budget**: spinning up cloud resources, large external API jobs, anything billable past ~$10.
- **Sending external messages**: posting to Slack/Discord, sending emails, opening PRs against public repos, posting to social.
- **Modifying credentials, security settings, or system-level config**: registry, firewall, services, scheduled tasks (those CAN be created in cron mode but are flagged in the recap).

Inside /auto these get a **single-line heads-up**, not a yes/no gate:

```
[auto] About to force-push to origin/main — this overwrites public history. Continuing.
```

Then proceed. The user can interrupt mid-stream if they object. The default is forward motion.


## Approach Rotation Rules

(Rotation is entered only via fix mode, so the P11 hypothesis gate has already run — each approach targets the current leading hypothesis, re-ranked as probes confirm or disprove.)

When a step fails, before retrying, name the new approach in one line:

```
[auto] Retry 2/5 — different parameter (was timeout=30, trying timeout=120)
```

If the new approach is *not* meaningfully different from a prior one, that's a sign you've exhausted ideas — declare STUCK rather than burn another attempt.

"Different" means:

- Different command flag, parameter, or config value
- Different code path (different function, different fallback)
- Different input (different file, different data shape)
- Different stage boundary (re-run a parent stage to regenerate input)
- Escalating a function-write to the function-author sub-agent (see Sub-agent Delegation) — the dispatch counts as one of the five distinct approaches

"Different" does NOT mean:

- Same command after a sleep
- Same prompt with reworded punctuation
- Same approach with a slightly larger timeout (unless the prior failure was specifically a timeout signature)


## When to Surface vs When to Resolve Internally

Auto absorbs most decisions. But some things must surface to the user:

- **Genuine STUCK-user.** The run is blocked on something only the user can supply, or the guardian's 3 re-attack rounds are exhausted with no legal move left. Stop, report exactly what's needed + the resume command, hand back. (A single step exhausting 5 approaches is a PARK, not a surface — the guardian re-attacks it.)
- **Discovery that contradicts the goal.** Mid-task you find the user's stated goal can't be achieved as described (e.g., "fix the test" → the test is testing impossible behavior). Stop, report the contradiction, ask for redirect.
- **Cross-system irreversibility.** About to do something that affects external state in a way that can't be undone (see "Auto Does NOT Waive" above).
- **The single-line heads-up format above.** Brief acknowledgment, proceed.

Do NOT surface for:

- Picking between two implementations when one is obviously better
- Choosing a retry parameter
- Deciding whether to add error handling
- Deciding whether the next step should be A or B when both achieve the goal
- "Should I commit this?" → if the user said /auto on a task that ends with a commit, yes


### Common stalling patterns — recognize and break out

If you find yourself about to type any of these, the answer is "don't ask":

```
"Should I try approach A or B?"
   → Pick the one most likely to make the verify check pass. If
     equal, pick A. If A fails, B becomes retry 2/5.

"I hit an error — want me to investigate or try a workaround?"
   → Both. Diagnose AND prepare workaround as next retry. Run them
     in parallel if independent.

"The output looks weird — should I check with you first?"
   → "Weird" is not a verdict. Check against the success criterion.
     Pass = continue. Fail = rotate. Never "weird."

"Should I commit this change?"
   → If the task ends in a working state, yes. Commit.

"I'm not sure if this is what you meant by X."
   → Pick the most reasonable reading, log it in one line, continue.
     Surfacing late = stalling.

"Want me to run the tests?"
   → Yes. Always. The test pass IS the verify step.

"Should I ask the user to..."
   → No. The user said /auto. Do it.

"The plan is written — should I build it now?" / "Phase 8 ready — proceed?"
   → No. /prep's internal phase boundaries (Phase 7 audit, Phase 8 build,
     Phase 9 pentest) are NOT user-confirmation gates under /auto. The
     plan landing is the runbook-generation trigger, not a stop point.
     Plan → runbook → execute → verify is one continuous flow. The
     ONLY stop conditions are DONE-verified or STUCK-with-reason.

"I just finished /prep / /repair / /optimize phase N — surface to user?"
   → No. Chained skills' phase boundaries are runbook transitions, not
     gates. Continue to phase N+1 silently. The user authorized the
     end-to-end run by chaining /auto with the lens skill.

"This is taking longer than expected — should I keep waiting?"
   → Yes if the verify hasn't fired AND retry budget isn't exhausted.
     Use Monitor to stream progress, continue planning next steps.

"I'm not sure if I have permission to..."
   → /auto IS the permission. Only the "Auto Does NOT Waive" list
     gets a heads-up — everything else proceeds.
```

The bar: surface ONLY when (a) a Hard Invariant trips, (b) 5 distinct approaches all failed (STUCK), or (c) an item from "Auto Does NOT Waive" is about to fire. Everything else = diagnose + rotate + continue.


### Park, don't halt

When a single step refuses to clear after bounded retries, do NOT halt the whole /auto run. Park that step:

```
1. Mark the step BLOCKED in the run log with the failure reason.
2. Identify remaining work that does NOT depend on the blocked step.
3. Continue on the independent work.
4. In the final report, list parked steps under "Pending" with the
   reason for each.
```

Halting the whole run for one stuck step is the worst version of pause-and-ask. The other 80% of the work could have made it home.

This is P3 example J applied: park and flag, never halt and ask.

**The all-parked checkpoint (never freeze, never quit).** When no step is PENDING or IN PROGRESS — every remaining step is DONE or PARKED (a `VERIFIED (FnReview pending)` step is neither: the pending check dispatches its review first) — the run is NOT terminal (Goal-Guardian rule, 2026-08-15):

```
- Success condition met (despite parked steps)  → refuter gate, then Status: DONE
- Success condition NOT met → Status: PARTIAL (checkpoint), listing each
  parked step + reason — then the guardian's next tick re-attacks:
  Round++ → blocker-review subagent → constraint compass → act.
  Round cap (3) exhausted → STUCK-user with the ledger.
```

`PARTIAL (checkpoint)` releases the SESSION cleanly (the Stop hook honors PARTIAL) while the GOAL stays owned by the guardian cron. A runbook with no advanceable step and no `Status:` line at turn-end is still the silent-freeze failure — always write the checkpoint. PARTIAL is never a final answer; only DONE or STUCK-user ends a run.


## Cron Mode (see Pattern 3 above + Goal-Guardian below)

Cron mode is Pattern 3 in the Execution Shape section above; the Goal-Guardian section below is the universal layer that owns the cron on EVERY run. When reading older docs or code that still references `monitor.py` / `shell.sh` / `schtasks`: those are obsolete. Everything is **claude code's own tools** (CronCreate, Monitor, Bash, Agent) coordinating around state files. There are no external scripts.


## Goal-Guardian — the run outlives the turn (universal)

_(Added 2026-08-15 by user directive after 9 of the last 25 runs orphaned at PARTIAL. Design pinned in `prep-goal-guardian.txt` v4; survived three independent AUDITOR/RED-TEAM rounds. This section is CANONICAL — where older text conflicts, this wins.)_

The guardian is one in-session cron per run that refuses to stand down until the run's **pinned contract** is observably satisfied (DONE) or the run is genuinely blocked on something only the user can supply (STUCK-user). PARTIAL is a **checkpoint, never an ending**.

**Session-lifetime honesty (verified 2026-08-15):** CronCreate jobs are session-only — in-memory, they fire prompts as new TURNS into THIS session while its REPL is idle, they die when the window closes, and they auto-expire after 7 days. The guardian therefore lives exactly as long as the window does. Keep the window open and it pushes all night; close it and the run waits for `/auto resume slug=<slug>`. The old claim that a cron "survives the chat closing" was false and is retired.

### The pinned contract (contract-pin)

A stated goal is a headline, not a contract. Before autonomy starts, expand the invocation into a contract, frozen in `./auto-runs/<slug>/GOAL.md` (write-once, atomic):

```
Goal:          <one observable sentence>
Success:       <checkable bar — the user's outcome, not machinery>
Circumstances: <what makes it COUNT: free / local / unattended /
                deadline / quality floor>
Never-do:      <moves that are cheating even if they "work" —
                paid APIs in a free tool, deleting sources,
                asking a human mid-run>
Validation:    <type-aware probes for the deliverable + any
                FULL-RERUN flags for specific deliverables>
False-pass:    <what a passing check would look like while the
                goal is still unmet>
Run-start:     <ISO timestamp — the provenance anchor>
```

- **Ask once, only when genuinely ambiguous.** Derive from the invocation + context. If two materially different readings survive, ask the user ONE startup question (this is a startup gate, allowed). Then the engine runs blind — never a mid-run question. Log the decision either way: readings considered + which fired, or `readings considered: 1`.
- The arming one-liner prints the contract summary — the user's veto point for a wrong pin.
- **Frozen means frozen.** Steps change; the contract never does. A wrong contract surfaces at STUCK-user and is fixed by the user restating the goal — never by the run editing GOAL.md.

### Lazy arming (guardian-arm)

**The invariant: nothing pauses unfinished unguarded.** Arm at the FIRST moment the run would end a turn non-terminal (it coincides with the checkpoint flip-back moment below). Runs that reach DONE inline never arm — zero overhead on trivial tasks.

- `CronCreate` one recurring job, off-minute, prompt PINNED verbatim: `/auto guardian slug=<slug> run=<ABSOLUTE run-folder path>` — the `/auto` trigger reloads this skill after compaction; the absolute path defeats cwd drift.
- Interval: adaptive — ~2× the longest expected step, **floor 10 min** (guardian ticks cost a subagent-capable turn; the Pattern 3 1-2 min band does not apply), 30-60 min for overnight renders.
- Record `armed:`/`expires:` dates + cron id in the runbook `Guardian:` field, mirrored to PROGRESS.md. Print: `[auto] Guardian armed (every N min, expires <date>) — lives in this window; keep it open.`
- **Near-expiry rotation overrides idempotency:** cron present but <24h to expiry → CronCreate the replacement → update cron-id + expires in BOTH files → CronDelete the old id. Rotation-create fails → retry next tick, one log line, never fatal while the old cron lives. Cron present and >24h out → no-op. Cron missing → recreate. This liveness check runs on EVERY /auto activity in the session (any turn type, via the HI #8 re-read), not just ticks.
- **CronCreate fails at first arming** → log one line, cap the report's Confidence at HIGH with that reason, and the run may NOT checkpoint: it drives to a terminal in-turn or goes STUCK-user. An unarmed checkpoint is an orphan — the exact disease this section cures.
- The guardian SUBSUMES the Pattern 3 execution cron: **one cron per run, ever.**

### Universal state files (every run, every pattern)

```
./auto-runs/<slug>/GOAL.md           the contract (write-once)
./auto-runs/<slug>/runbook.txt|RUNBOOK.md  + new Status fields:
     Guardian:  armed <cron-id>, every N min, expires <date>
                | unarmed | stood-down (<reason>)
     Contract:  pinned <date> | pinned+asked
     Round:     K/3 re-attack rounds used
     Jobs:      <id/PID + artifact path + expected duration>
                per live background job (registered at launch)
     Reviewer:  n/a | pending | <last verdict>
     Principles: n/a | pending @<ISO> | clean @<ISO>
                | unswept @<ISO> (<reason>) | <n> violations
     FnReview:  n/a | <k> pending | <n> in fix | clean | <n> open
                | <m> unreviewed   (per-function stamps live on the
                Functions block lines — see FnReview)
     Turn-end rule: checkpoint = Status: PARTIAL (checkpoint);
                STUCK only when user-blocked
./auto-runs/<slug>/APPROACHES.md     append-only approach history
./auto-runs/<slug>/PROGRESS.md       last-tick summary + deliverable
     artifact BASELINE (paths/sizes/mtimes at arming) + MIRRORS of
     Round / cron-id / blocker-since (rebuild-proof) + the FnReview
     run-start def SNAPSHOT + (item, file, function) LEDGER — named
     sections every tick SECTION-MERGES, never overwrites
./auto-runs/<slug>/spend-<YYYY-MM-DD>.txt  per-slug tick counter
```

The `Turn-end rule` line is not decoration — it is the compaction-proof carrier of the checkpoint protocol (the file, not this skill text, is what every turn re-reads). **ALL state files use atomic temp+rename writes** — load-bearing twice over: a truncated runbook breaks the next tick AND trips the Stop hook's fail-open path.

### The tick protocol (guardian-tick) — strict order

A tick is a cron-fired turn in this same session. Its prompt re-invokes /auto in guardian mode for one slug. Steps, in order:

```
1. SPEND GATE — read/increment ./auto-runs/<slug>/spend-<today>.txt
   (~30 ticks/day per run). Over cap → one pause note, checkpoint-
   exit. Two consecutive counter WRITE failures → STUCK-user (disk
   trouble is a real blocker). Resets at date rollover.
2. RE-READ + LIVENESS — GOAL.md + runbook + log tail (~30) +
   PROGRESS.md (HI #8; files beat memory). Guardian liveness /
   near-expiry rotation (above). Corrupt GOAL.md → stand down +
   STUCK-user naming the corruption (never improvise a contract).
   Corrupt runbook → rebuild steps from GOAL.md + log tail; Round /
   cron-id / since restored from the PROGRESS.md mirrors; the
   contract is never re-derived. Slug folder missing but auto-runs/
   root present → stand down (CronDelete + one line).
3. TERMINAL CHECK — Status DONE / STUCK-user / STUCK (stopped by
   user) → CronDelete (recorded id; fallback: resolve by name
   auto_guardian_<slug>) → exit.
4. OWN-JOBS CHECK (before ANY DONE path) — read the Jobs: field
   (never conversation memory). Any job alive → NO success probe,
   NO reviewer-step execution this tick.
     alive + artifact growing → noop tick (one log line)…
       …but past ~10× expected duration → dispatch blocker-review
       even while growing (no immortal healthy-noop).
     alive + flat → the ~2× stall clock governs (visual checkpoint
       on visual steps); only an expired clock escalates (kill/
       drain per heuristic #13). Task-alive OUTRANKS artifact-flat.
5. SUCCESS PROBE — validate vs the contract (type-aware floor +
   PROVENANCE: deliverable must postdate Run-start; the arming
   baseline corroborates, run-start decides; consult False-pass).
   Met → [FnReview pending check: any step VERIFIED-pending, or
   FnReview: k pending / n in fix → dispatch + return the carried
   review FIRST; a finding discards "Met" and falls to step 7, never
   step 8] → Terminal Refuter Gate / RED-TEAM per their rules
   (an `open` FnReview line or a fix-trigger `unreviewed` stamp
   forces the refuter even on a machine-checked goal) → DONE →
   CronDelete.
6. SUSPECT — no own jobs, artifact flat → mark SUSPECT (any growth
   tick clears it). SECOND consecutive flat tick → blocker-review.
7. PENDING STEPS — runbook has runnable steps → execute the next
   one normally (re-entry hygiene on redo). A VERIFIED (FnReview
   pending) step whose review is carried or in flight does not
   occupy the tick — run the next step that does not consume its
   functions; the review is dispatched/collected in the same tick
   when the window allows.
   Principles-sweep rider (step-7 ticks ONLY; never while Reviewer:
   is pending): every 3rd tick (today's spend counter divisible by
   3), if DELIVERABLE edits landed since the last sweep's ISO stamp
   (log entries after the stamp showing Edit/Write/mutating Bash on
   files OUTSIDE auto-runs/), dispatch the principles-sweep (below)
   alongside normal execution. `Principles: pending @<ISO>` enforces
   one sweep at a time — but a pending stamp older than one sweep
   window (~3 ticks), or found on resume, is STALE: set
   `unswept @<ISO> (stale)`, one log line, eligible to re-dispatch.
8. DRY/PARKED/BLOCKED → increment Round FIRST (post-increment K>3
   → STUCK-user with the ledger; = 3 real re-attack rounds) →
   dispatch blocker-review → act on its verdict via the constraint
   compass. Un-parking uses the 4th re-entry door: rollback →
   re-assert pre-verify → invalidate downstream → retry.
   GOAL-MET verdicts re-enter step 5 — never direct DONE.
9. CHECKPOINT-EXIT — the ONLY legal non-terminal turn end: write
   all state atomically, set Status: PARTIAL (checkpoint), exit.
```

### Checkpoint-writer — how ANY turn legally ends mid-run

The Stop hook releases a turn only on DONE / STUCK / PARTIAL. So, in an armed session, **every turn of every type** (tick, Monitor notification, user exchange) ends the same way: if the run is non-terminal, last act = arm-if-unarmed, then `Status: PARTIAL (checkpoint)`. Tick-start flips PARTIAL → active; turn-end flips it back.

- The hook's stderr reflex ("do not return control until DONE or STUCK") is SATISFIED by checkpoint-then-stop — never escape via a false STUCK: a false STUCK reads as terminal and kills the guardian with the goal unmet (the worst failure this section defines). The runbook's `Turn-end rule` line carries this across compaction.
- Esc-interrupt recovery: a turn killed before its flip-back costs exactly ONE hook-dragged turn (which arms + checkpoints), then frees. Designed recovery, not a bug.
- The hook enforces `Refuter:` on DONE but not `RedTeam:` or `Principles:` — model discipline + the runbook fields carry those obligations.
- Between ticks the runbook always reads PARTIAL, so a user who repurposes the session is never dragged — their turns release instantly.

### Blocker-review — the fresh-eyes subagent

Dispatched by tick steps 6/8 (one at a time — `Reviewer: pending` in the runbook enforces it across turns). Hand ONE fresh general-purpose subagent: the contract (GOAL.md), runbook, APPROACHES.md, log tail (~30), the claimed blocker/stall, the deliverable/artifact paths, and an explicit **read-only probe license** (Read/Glob/ffprobe-class commands; writes forbidden) — it grades evidence from disk, not the run's testimony.

Brief: *"You did not do this work. Decide: (a) FALSE-BLOCKER — the run can legally continue; return the ONE next step (must trace to Success, violate zero Never-dos, differ from every APPROACHES.md entry); (b) REAL-machine — name the machine-checkable condition + its probe; (c) REAL-user — name exactly what only the user can supply; (d) GOAL-MET — cite the validating evidence. Default to skepticism of the run's own excuses."*

- **Verdict validity:** every verdict must cite the specific contract line(s) + observable evidence read from disk. No citation or no evidence = UNRESOLVED — retry once with a tightened brief, then treat as REAL-user with "reviewer could not rule" noted. Never silently continue.
- GOAL-MET decides nothing by itself — it re-enters tick step 5 (machine probes) and the Terminal Refuter.
- The DRIVER validates and executes the proposed step; the reviewer never acts.
- REAL-machine → slow-heartbeat: re-arm at 30-60 min; `since` = FIRST seen, never reset by flaps; two clear probes apart before resuming; 24h unresolved → STUCK-user (a dead dependency is an incident, not a wait).
- **A REAL-machine blocker with a known recovery path is NEVER a user decision** (incident 2026-08-16, gemini-fallback-live-023001: run parked itself on an "A/B?" menu where A was the protocol's own prescribed path). The run CONTINUES on the recovery path automatically. A bar-lowering shortcut ("accept the partial proof, skip ahead") may be OFFERED as a non-blocking aside in the checkpoint report — but the run keeps driving toward the frozen Success line without waiting for an answer. Parking a legal path to await permission is a menu-stall (violates HI #1 + Principle 5); only a genuine contract dead-end or user-only supply justifies waiting.
- Subagents unavailable → same-context skeptic pass, explicitly marked as the weaker fallback.

### Principles-sweep — the mid-run compliance check (fresh eyes)

_(Added 2026-08-18 by user directive: the guardian should verify the principles are actually being FOLLOWED mid-run, not just that progress is happening. Survived one AUDITOR + RED-TEAM round; the bounds below are their fixes.)_

Fires only on runs whose deliverable is code (build/repair chains — the driver sets `Principles: n/a` at runbook generation for no-code deliverables, flipping it to sweep-eligible on the first deliverable code edit), on the step-7 rider's schedule. Deliverable edits only: files under `auto-runs/` (runbook, PROGRESS, spend, logs, shots) are NEVER part of the trigger or the changed-set — the guardian does not sweep its own bookkeeping. Blocked/step-8 ticks are consciously unswept (blocker-review owns those); their edits are caught at the next step-7 window.

Dispatch ONE fresh general-purpose subagent with a read-only probe license. Hand it: the deliverable files changed since the last sweep's ISO stamp (from log entries AFTER that stamp — the stamp, not a ~30-line tail, bounds the read), GOAL.md, a `reviewed-clean ranges: <fn> L<a>–<b> @<ISO>, …` note (the DRIVER recomputes each FnReview-stamped function's hash and lists only the still-valid ranges — the sweep does not flag inside those; see FnReview), and this fixed checklist — nothing else. Inside a tick the rider dispatches AFTER the step's FnReview has returned and written its ledger — "alongside" means same tick, sequenced — so the two nets never double-flag one function:

```
1. HEAVEN'S NET — RECOVERY/error handling keys to evidence-mapped
   failure classes, never "symptom string X → do Y"; unmatched or
   assumed signals are captured, parked, fail loud — never
   guess-classified (canonical: /error-recon, "Heaven's Net").
   Guardrails: DETECTION may match mapped symptoms — it is the
   recovery that must be class-level; ≤2 handlers need no taxonomy
   (rule of three). Do not flag either.
   1b. PROPORTION (same canonical section) — a recovery that rests/retires
   capacity or pulls a pool sizes its cooldown / bench / share from an
   OBSERVED recovery measurement (cite where) or a bounded ≥×2
   smallest-first ladder; a guessed constant or wrong scope is a
   VIOLATION in either direction (90 s rest for a ~24-min throttle;
   rest-till-midnight on a string that may mean a 60 s limit; N members
   retired for a pool-wide blip). A signal mapped to two entries of
   different size that jumps to the larger (or a bespoke 'both' handler)
   instead of a smallest-first ladder is the same VIOLATION. Bounded
   growing backoff IS the ladder — do not flag it. Item 1 returns two
   verdicts, keyed `1` (class) and `1b` (proportion); a size finding
   filed as `1` is re-keyed `1b`.
2. EVIDENCE-ONLY — no success declared from labels/exit codes
   alone; verdicts rest on verified output or independent signals;
   nothing assumed.
3. RE-ENTRY HYGIENE — every retry/resume rolls back residue →
   re-asserts the precondition → invalidates downstream before redo.
4. NO SILENCED FAILURES — no bare except/pass, no unbounded retry,
   failures surfaced by count, flight-recorder capture on unknowns.
5. KISS — no frameworks/abstractions the task didn't earn.
```

Brief: *"You did not write this code. For each checklist item return CLEAN or VIOLATION with file:line evidence read from disk. A VIOLATION is a concrete breach, not a style nitpick. Do not rubber-stamp."*

**Verdict handling — bounded at every exit:**

- **Mtime validation first.** Before acting on findings, the DRIVER checks them against current file mtimes: a finding citing a file that changed after the sweep read it is discarded with one log line (stale read, not evidence).
- **Self-contained violation steps.** Each surviving VIOLATION appends as a fix-mode step whose text carries the checklist item + file:line + the quoted evidence + a verify checkable WITHOUT re-sweeping. A violation step is EXEMPT from constraint-compass check (a) — the five checklist items are standing quality constraints, not Success-line work — while (b) Never-do and (c) no-repeat still apply in full.
- **Dedupe + cumulative cap.** A (checklist-item, file) pair a prior sweep already ruled on is never re-flagged (ruled pairs mirror to PROGRESS.md); max 5 sweep-appended steps per run — beyond the cap, findings go to the Notes' Open Questions as report-only. Sweeps must never become the reason a run can't end. FnReview rulings live in their OWN (item, file, function) ledger — never in this file-keyed one — and FnReview-driven fix-mode re-entries do NOT count against the 5-step cap.
- **Won't-fix exit.** A violation step that contradicts a recorded Design Decision, or that parks after honest attempts, may be closed **WAIVED** (intentional design / won't-fix — cite the evidence) by the driver or blocker-review; WAIVED counts as resolved for the all-steps gate and lands in Open Questions. A checklist misread must never drive a goal-met run to STUCK-user.
- **The field never sticks at pending.** CLEAN → `Principles: clean @<ISO>`. A sweep with no evidence citations is UNRESOLVED → retry once at the next window; a second failure, an errored dispatch, or a never-returned result → `unswept @<ISO> (2 failures | error | stale)`, one log line, later windows may try again.
- **At the Terminal Refuter Gate:** deliverable edits newer than the last sweep stamp → annotate the field `clean @<ISO>, unswept tail` and say so in the final report (the refuter-brief Heaven's Net line covers recovery code) — a stale `clean` must never read as full coverage. A `pending` at gate entry follows the staleness rule above: it never blocks DONE silently and never waits unbounded.
- The sweep never pauses the tick's normal work and is never a user gate.

### Constraint compass — no winning by cheating

Before ANY derived, reviewer-proposed, or un-parked step executes: (a) it traces to the frozen Success line; (b) it violates ZERO Never-do lines; (c) it differs from every APPROACHES.md entry. Any failure → step REJECTED (logged with the broken constraint; the rejection consumes an approach slot so cosmetic variants can't loop). Every remaining path violates a constraint → **STUCK-user with the tradeoff spelled out**: "goal reachable only by breaking <constraint> — your call." The purpose is never traded away silently.

### Terminals + kill switch

```
DONE                       validated deliverable + refuter/redteam
                           per their rules → CronDelete → marker
                           deleted IF it names this slug.
STUCK-user                 only-the-user-can-supply blocker, round
                           cap exhausted, 24h dead dependency, or
                           compass dead-end. Names exactly what is
                           needed + the resume command. CronDelete.
STUCK (stopped by user)    /auto stop slug=<slug>: CronDelete +
                           honest STOPPED report with ledger +
                           resume command + marker deleted IF it
                           names this slug. Always works — the
                           spelling is hook-regex-safe by design.
PARTIAL (checkpoint)       NOT a terminus. Never writes a VERDICT
                           file. Never seals the notes. The
                           guardian carries the run onward.
```

Legacy `VERDICT_STUCK` files (the old all-parked, machine-retryable shape) are treated as checkpoints, not termini — only STUCK-user stands the guardian down. Session-marker deletion always checks content: delete only if it names YOUR slug; if it names another run's, leave it and log one line (with coexisting runs the hook backstops the marker's run; the others are guarded by their own crons + checkpoint discipline).

### RED-TEAM scoping under the guardian

The RED-TEAM rider fires on the deliverable's NATURE (unchanged rule) **or** when the guardian actually fired ≥1 tick — proof the run ran unattended in practice. Never on mere armament: a 20-second attended run stays cheap.


## Hard NOs

- **No "Phase 0: present plan for confirmation."** That phase is gone. The user already authorized by saying `/auto`.
- **No "should I proceed?" / "want me to do X?" / "ready to continue?"** These all violate hard invariant #1.
- **No asking after a plan is written.** When /auto is chained with a planning skill (`/auto /prep`, `/auto /optimize`, `/auto /repair`), the plan landing is the runbook-generation trigger — NOT a confirmation point. Asking "should I build the plan now?" or "Phase 8 ready, proceed?" is a hard-invariant violation. Plan → runbook → execute is one continuous flow.
- **No silently advancing on bad output.** If a step failed, say so and rotate the approach.
- **No declaring DONE without evidence.** "I think it worked" is not done.
- **No standing down before the goal.** The guardian cron is deleted ONLY on DONE, STUCK-user, or /auto stop. (The old "cron is for overnight jobs only" rule is retired 2026-08-15 by user directive — any run that pauses unfinished is armed; instant-finish runs never arm, so trivial tasks stay free.)
- **No treating PARTIAL as an ending.** PARTIAL is a checkpoint the guardian pushes past — a report may say PARTIAL, the run doesn't end there.
- **No burning past 5 failed approaches without declaring STUCK.** The whole point is bounded autonomy. (A FnReview finding opens a fresh 5-approach budget for that review round — ≤2 rounds per guardian pass, ≤24 review rounds per step worst case; still bounded. See FnReview.)


## Terminal Refuter Gate — independent DONE check

Before /auto writes `Status: DONE`, one fresh agent tries to prove it is NOT done. This is the **independent upgrade** of the same-context "AUDIT vs END GOAL" step: the brain that did the work shares every blind spot that produced it, so it is the wrong brain to clear it. Empirically, a model grading its own output is unreliable (intrinsic self-correction often fails to improve and can degrade), and self-preference bias bites hardest exactly when the work is weakest — the worst time to be blind. An independent verifier is the documented fix, and verification is the cheap side of the generator-verifier gap.

### When it fires

Only when "done" is a **judgment call**. If the runbook's success line is a deterministic machine check that already passed (`pytest` exits 0, checksum matches, file exists at expected size), **SKIP** the refuter — that verify check IS the independent oracle, and self-preference can't bias a green test. Fire it when success is judgment-shaped: "pipeline handles real input", "output looks right", "report is complete", "no regressions in adjacent features". **Before this rule is consulted, on every DONE path (inline end, guardian SUCCESS PROBE, the skip path): the FnReview pending check** — no step `VERIFIED (FnReview pending)`, no `FnReview: k pending / n in fix`; a carried review is dispatched and returned first. **Two FnReview carve-outs override the SKIP:** a Functions line reading `open …` (a round-2 VIOLATION/BAND-AID that parked) or a fix-trigger function stamped `unreviewed` forces the refuter even on a machine-checked goal — `Refuter: n/a → pending` (the RedTeam precedent, so the Stop-hook carrier holds). See FnReview "Interplay with the Terminal Refuter Gate".

The **RED-TEAM rider** (below) has its own, independent firing rule: it fires on the deliverable's NATURE — unattended, long-running, stateful, or concurrent — even when the refuter is skipped. A green deterministic test proves the happy path ran once; it says nothing about credits dying mid-write, a flag flipping between check and act, or a half-written folder on re-entry. Machine-checked goal + unattended deliverable ⇒ refuter skipped (barring the FnReview carve-outs), RED-TEAM still fires alone (the runbook `RedTeam:` field carries the obligation).

### Sequence (refute first, flip second)

```
1. All runbook steps verified PASS   (necessary, NOT sufficient for DONE;
   PARKED steps allowed per the all-parked checkpoint) AND no step in
   VERIFIED (FnReview pending), no FnReview: k pending / n in fix —
   dispatch any carried FnReview first (an `open` PARKED line is the
   forced refuter's INPUT, not an entry block)
2. → set runbook Refuter: pending (and RedTeam: pending when the rider
   applies), dispatch refuter + RED-TEAM in parallel   (Status still NOT DONE)
3a. refuter clean AND RedTeam clean/n/a → set fields → write Status: DONE
                          → emit AUTO DONE
3b. refuter BLOCKER or RedTeam BREAKS   → record in the owning field →
                          keep Status non-DONE, re-enter fix mode on the
                          unmet item
```

Running the refuter AFTER flipping Status would release the Stop hook (see auto-stop enforcement + Hard Invariant #9) and the run couldn't re-enter cleanly. Refute first, flip second — and the `Refuter:` field carries this in the runbook so it survives compaction.

### The refuter brief

Dispatch a fresh sub-agent (`Agent` tool, subagent_type `general-purpose`) — the same machinery /audit and /prep use. Hand it ONLY:

- the **frozen Success line + per-step verify checks** (the yardstick — nothing else),
- the observable artifacts produced,
- a **baseline "before" reference if one exists** (git HEAD, a pre-change snapshot, the prior output dir) — part of the yardstick, so the refuter can diff the deliverables against it and flag unexplained or out-of-scope changes; greenfield builds have no baseline, so don't fabricate one (added 2026-06-14),
- the Implementation Notes Design Decisions / Deviations cards (so it refutes against intent, not re-litigating settled forks),
- the runbook **Functions block** (FnReview coverage hand-over): name explicitly every `open`, `unreviewed`, no-stamp and WAIVED line, and every function whose current hash differs from its `clean` stamp's sha — "these were not independently reviewed; look there first". A stale `clean` must never read as coverage. When the refuter was FORCED by an `open` line or a fix-trigger `unreviewed` stamp on a machine-checked goal, add: *"For each named open / unreviewed line return exactly BLOCKER or WAIVED(<citation>); a confirmed BAND-AID (HI #14 aim-test + FnReview items 6–9) is a BLOCKER even though the Success line is machine-green."* Silence / CONCERN / NOTE on a named line = UNRESOLVED → retry once → then the same-context skeptic fallback below must rule BLOCKER(<cited unmet item>) or WAIVED(<citation>) — never a BLOCKER without a named item.

Brief: *"You are the REFUTER. The work below claims to be DONE. Prove it is NOT — find a specific Success-line item or verify check that is unmet. Read the artifacts yourself. Return ranked findings BLOCKER / CONCERN / NOTE, each with evidence. A BLOCKER is a concrete unmet success criterion, not a nitpick. Default to finding holes; do not rubber-stamp."* (If /repair is in the chain, add: *"A real fix holds on a different input with no Claude present — does it?"* per the structural-fix rule.) When the claimed DONE rests on a diagnosis or judgment call, add: *"Were the relevant alternative explanations investigated or explicitly ruled out, or was the first hypothesis merely confirmed?"* (HI #13). When the deliverable contains recovery/error-handling code, add: *"Is any handler keyed to a symptom string instead of an evidence-mapped failure class, does any path act on an assumed/unproven signal, or is any capacity-resting recovery SIZED (cooldown / bench / scope) from a guessed constant instead of an observed measurement or a bounded smallest-first ladder? (Heaven's Net — canonical in /error-recon.) Any of these is a BLOCKER."*

### RED-TEAM rider — unattended / stateful deliverables

When the deliverable will run unattended or holds state across runs (a pipeline, a cron job, a helper daemon, fallback/routing logic, a queue — anything no human watches per-step), dispatch a SECOND fresh agent in parallel with the refuter: the **RED-TEAM**. Its canonical brief lives in `~/.claude/skills/audit/SKILL.md` under the heading "**The brief handed to the RED-TEAM**" — read it there at dispatch time and hand it the actual artifact paths (code, runbook, logs). It generates concrete hostile scenarios across 10 attack categories (mid-op death, check-then-act races, half-done re-entry, flapping, two actors, boundaries, time windows, recovery-fails, poison pill, lying success) and walks each through the real code to HANDLED / DEGRADES / BREAKS / UNKNOWN.

- **Fires on the deliverable's nature — or on ≥1 guardian tick having fired** (proof the run ran unattended in practice; never on mere guardian armament) — see "When it fires." It runs even when the refuter is skipped; the runbook `RedTeam:` field carries the obligation across compaction exactly like `Refuter:` (pending → clean before `Status: DONE`; a guardian tick that fires while `RedTeam: n/a` flips it to `pending`).

- **BREAKS = BLOCKER** → re-enter fix mode on the owning step (Re-entry hygiene applies). **DEGRADES, and UNKNOWN on a load-bearing scenario,** = CONCERN → logged to the Notes file's Open Questions; does not block DONE.

- **Shares the max-2-rounds bound** with the refuter — see "Bound."

- **Internal, not a user gate** — same rule as the refuter; it passes silently or auto-re-enters fix mode within the bound.

### Verdict handling — severity-gated

- **BLOCKER** (maps to a specific unmet Success item / failed verify) → re-enter fix mode on that item (Re-entry hygiene: map it to its owning step(s) and restore each before redo). ONLY a BLOCKER re-opens /auto.

- **CONCERN / NOTE** → logged to the Notes file's Open Questions. Does NOT block DONE.

### Bound (so it can never loop forever)

Max **2 refute rounds** per re-attack round — a round is any terminal-gate dispatch (refuter and/or RED-TEAM together count as ONE round). On the 2nd round still BLOCKER (or RED-TEAM BREAKS) → emit **AUTO PARTIAL (checkpoint)** listing the open holes — the guardian's next re-attack round owns them (within the 3-round guardian cap, whose exhaustion → STUCK-user). Never silently loop; never silently DONE; never treat the refute bound as a final ending while the guardian lives.

### Not a user-facing gate

The refuter is internal — it passes silently or auto-re-enters fix mode within the bound. It never asks the user "I found holes, keep going?" (that would violate no-gates / "invocation is authorization"). It only surfaces at the terminal PARTIAL/STUCK verdict.

### Fallback

If sub-agents are unavailable, run a same-context skeptic pass against the Success line and mark it explicitly as a **same-context fallback** — weaker, since the whole point is independence.


## Final Report Templates

### Inline auto, success
```
=== AUTO DONE ===
Goal:    <one sentence>
Result:  <what happened, with numbers>
Verified by: <evidence — log line / exit code / file existence>
Coverage: <success checks passed, e.g. 7/7 = 100%>
Current stage:
  Before:   <state before this run>
  Now:      <state right now — exists / verified / waiting>
  Changed:  <what changed and WHY>
  Next:     <"none" if fully reached, else the milestone remaining>
  Meant to: <what Next achieves + the problem it fixes>
  Feynman:  <Next to a smart 12-year-old, one analogy — fits Heaven's Net + the goal>
Ultimate goal (4 lenses): Delivers <...> · Heals <...> · Replaces <...> · Guarantees <...>
Suggested action:
  Paste this:     <"nothing — goal reached", or the answer to THIS TURN'S question — on a pick: the pick + one line why; on a do-it: self-contained prompt: what / files / limits / facts / show-or-ask>
  → Toward goal:  <a chain, not a tag: move → concrete gain → which lens needs it and why, + cost of the rejected option>
  → Heaven's Net: <on a pick: seen evidence + what ruled others out + how we'd know if wrong + bounded fallback, never n/a; on a work step: class-keyed, evidence-only, bounded, fail-loud — or n/a>
Confidence: PERFECT|HIGH|MEDIUM|LOW — <verified directly vs inferred; DONE with anything unverified is forbidden; PERFECT only with all angles tested + refuter-clean, tests named>
Risk:       HIGH|MEDIUM|LOW — <what's exposed if this is wrong>
Notes:   ./auto-runs/<slug>/notes.md  (decisions + open questions)
```

### Inline auto, partial
```
=== AUTO PARTIAL ===
Goal:        <one sentence>
Done:        <what landed>
Missing:     <what didn't, with reason>
Coverage:    <success checks passed, e.g. 5/7 = 71%>
Ledger (for the missing part — the P11 facts/unknowns handoff):
  Facts:                   <what is PROVEN about the gap, with evidence>
  Unknowns:                <what is still unverified>
  Leading hypothesis:      <best guess why + confidence high/med/low>
  Next highest-value test: <the one probe that would teach the most>
Current stage:
  Before:   <state before this run>
  Now:      <state right now — landed / verified / missing>
  Changed:  <what changed and WHY>
  Next:     <the immediate milestone between here and that goal>
  Meant to: <what Next achieves + the problem it fixes>
  Feynman:  <Next to a smart 12-year-old, one analogy — fits Heaven's Net + the goal>
Ultimate goal (4 lenses): Delivers <...> · Heals <...> · Replaces <...> · Guarantees <...>
Suggested action:
  Paste this:     <answers THIS TURN'S question — on a pick: the pick + one line why (work prompt waits for next turn); on a do-it: self-contained prompt: what / files / limits / facts / show-or-ask before anything costly>
  → Toward goal:  <a chain, not a tag: move → concrete gain → which lens needs it and why, + cost of the rejected option>
  → Heaven's Net: <on a pick: seen evidence + what ruled others out + how we'd know if wrong + bounded fallback, never n/a; on a work step: class-keyed, evidence-only, bounded, fail-loud — or n/a>
Confidence:  HIGH|MEDIUM|LOW — <verified vs inferred; the "Done" list must be all-verified or this drops; PERFECT is impossible on a PARTIAL>
Risk:        HIGH|MEDIUM|LOW — <what the Missing part exposes; who/what gets hit if it stays missing>
Notes:       ./auto-runs/<slug>/notes.md  (decisions + open questions)
```

### Inline auto, stuck
```
=== AUTO STUCK ===
Goal:        <one sentence>
Approaches tried (N):
  1. <approach> → <failure reason>
  2. <approach> → <failure reason>
  ...
Why I'm stopping: <why no 6th approach exists>
Ledger (the P11 facts/unknowns handoff — a STUCK is a resume point, not a dead end):
  Facts:                   <what is PROVEN, with evidence>
  Unknowns:                <what is still unverified>
  Leading hypothesis:      <best remaining guess + confidence high/med/low>
  Next highest-value test: <the one probe that would teach the most>
Current stage:
  Before:   <state before this run>
  Now:      <state right now — what's proven, what's parked>
  Changed:  <what changed and WHY>
  Next:     <the milestone this STUCK is blocking>
  Meant to: <what Next achieves + the problem it fixes>
  Feynman:  <Next to a smart 12-year-old, one analogy — fits Heaven's Net + the goal>
Ultimate goal (4 lenses): Delivers <...> · Heals <...> · Replaces <...> · Guarantees <...>
Suggested action (hand back to user):
  Paste this:     <answers THIS TURN'S question — if the block is a pick the user must make: the recommended pick + one line why; else self-contained prompt for the best unblocking step: what / files / limits / facts / show-or-ask>
  → Toward goal:  <a chain, not a tag: this unblocking move → concrete gain → which lens needs it and why, + cost of staying stuck>
  → Heaven's Net: <on a pick: seen evidence + what ruled others out + how we'd know if wrong + bounded fallback, never n/a; on a work step: class-keyed, evidence-only, bounded, fail-loud — or n/a>
Confidence:  HIGH|MEDIUM|LOW — <how solid the Facts list is; anything inferred drops it; PERFECT is impossible on a STUCK>
Risk:        HIGH|MEDIUM|LOW — <what stays exposed while this sits stuck>
Notes:       ./auto-runs/<slug>/notes.md  (decisions + open questions)
```

### Cron auto, on terminal verdict
Same shape, but written to `auto-runs/<slug>/VERDICT_DONE` or `auto-runs/<slug>/VERDICT_STUCK` and the cron self-uninstalls. VERDICT files are written ONLY at true termini (DONE / STUCK-user / stopped-by-user) — never at a PARTIAL checkpoint.

### Any report on a non-terminal run
Add one line so the user always knows who owns the goal:
```
Guardian: armed (every N min, expires <date>) — next tick <~time>.
          Stop anytime: /auto stop slug=<slug>
```


## TL;DR

- /auto = behavior mode, not pipeline architecture.
- Invocation is authorization. Zero follow-up gates.
- Inline shape is the default; any run that would pause unfinished arms the Goal-Guardian cron (session-lifetime, lazy, one per run) — nothing pauses unfinished unguarded.
- The goal is a pinned CONTRACT (success + circumstances + never-do, frozen in GOAL.md); no step may win by cheating it; PARTIAL is a checkpoint, never an ending.
- Every non-terminal turn ends with Status: PARTIAL (checkpoint); ticks flip it active and back. Only DONE (validated + provenance-checked) or STUCK-user ends a run; /auto stop slug=<x> is the kill switch.
- Diagnose, rotate approaches, never advance on lies; parked steps get up to 3 guardian re-attack rounds via the fresh-eyes blocker-review subagent (citations required).
- One-line "[auto] doing X — why" heads-up before non-trivial actions, then proceed.
- Final report is honest with numbers, not vibes — and ends with Confidence + Risk grades tied to evidence; anything pending/unverified caps Confidence below HIGH. PERFECT = all angles tested + refuter-clean + tests named; the only grade licensing zero-human-input runs.
- On judgment-based goals, an independent refuter must fail to break it before DONE (bounded 2 rounds → PARTIAL; BLOCKER-only re-entry). Machine-checked goals skip it — unless a FnReview line is `open` or a fix-trigger function is `unreviewed`, which force it.
- FnReview: EVERY function written or rewritten (and every function-level fix — fix mode OR a rewritten pre-existing def — with the fix packet) gets a fresh-eyes reviewer at its verify PASS, fanned out in parallel per function, non-blocking for independent steps — 5 principles + goal-trace + 4 "complete, not band-aid" items; a finding blocks the producing step and re-enters fix mode; ≤2 rounds per step per guardian pass; stamps on the Functions block (content-hash); a pending review is never DONE; an open finding is a DONE gate. In-turn dispatch, not a second cron.
- Fan out same-check × N-item steps to capped sub-agents; offload heavy reads to throwaway sub-agents to keep the driver's context lean.
- Visual checkpoints: screenshot major events + ~10-min intervals on long visual steps, READ every shot; two identical job-surface shots + a flat artifact probe = STALLED.
- Operational heuristics #8-14: disk-is-truth, cite-the-incident, hand-test-before-coding, name-this-run-vs-next-run, adjacent-issue-radar, escalation-tree, heavens-net-class-recovery.
