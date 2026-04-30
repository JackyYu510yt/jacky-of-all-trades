---
name: auto
description: Universal autonomous mode. The user runs `/auto` (or says "go autonomous", "no gates", "just do it", "set and forget", "keep going until it's done") to authorize Claude to drive a task end-to-end without further prompts. The invocation IS the authorization — there is no follow-up confirmation gate. Claude states briefly what it's about to do, then executes, diagnosing and re-trying as needed, stopping only on genuine success (DONE) or genuine stuck (STUCK). Applies to any task — a single fix, a multi-step build, a long unattended job — not just pipelines. For long unattended jobs, an optional cron+monitor+shell architecture is available (see "Cron mode" section).
---

# Auto

Universal autonomous mode. The user invokes `/auto` to hand Claude a task; Claude executes it end-to-end with no further confirmations.


## Installation (one-time, per machine)

The `/auto` skill ships with a hook script — `hooks/auto-log-hook.py` — that auto-appends every state-changing tool call to `./auto-log.txt` (or `./auto/logs/run.log` for Pattern 3) when an active /auto run is detected. Without this hook, log appending falls back to model discipline and gets unreliable on long runs.

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

**Verification:** after wiring, run `/auto` on a small task in any folder. After it generates the runbook, check `./auto-log.txt` — every tool call should appear as a one-line `[timestamp] [tool] <summary>` entry without the model having to remember to write them.

The invocation **is** the authorization. There is no Phase-0-confirm-the-plan gate. There are no "should I proceed?" checkpoints. There are no "want me to run X to verify Y?" offers. Claude states what it's about to do in one or two sentences, then does it, and reports back when DONE or STUCK.

## When to Use This Skill

- User says `/auto`, "go autonomous", "no gates", "just do it", "stop asking, just run it", "set and forget", "keep going until it's done", "while I sleep", "run the whole thing"

- User has expressed frustration at being asked for permission

- User has stated an end goal that requires multi-step execution and explicitly does not want to babysit

- ANY task the user has handed to Claude with the implicit understanding "you drive"

This skill is a **mode**, not a tool. It modulates how Claude executes any work, not what work to do.


## Phase 0 — Plan Ingestion + Activation Gate (mandatory first action)

Before anything else, /auto must lock in the end goal and at least one observable success condition. If it can't, /auto refuses to activate.

### Step 1 — Scan for an existing plan

Glob the working directory in this priority order:

```
1. ./auto/GOAL.md           (prior cron-mode auto)
2. ./prep-*.txt             (output of /prep)
3. ./PLAN.md                (manual plan)
4. ./.claude/plans/*.md     (older /prep outputs)
5. User's invocation message + recent context
```

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


## Phase 0.5 — Generate the Runbook (mandatory before execution)

After the activation gate clears, /auto writes a runbook file BEFORE any step runs. The runbook is the contract /auto follows — every step lists the action and the observable check that means "step done." /auto executes the runbook deterministically, only entering "fix mode" (diagnose + rotate) when a step's verify check fails.

### Runbook file location

```
./auto-runbook.txt        Patterns 1 & 2 (inline / background+monitor)
./auto/RUNBOOK.md         Pattern 3 (cron+monitor+shell — lives with state files)
```

### Runbook format

```
RUNBOOK — <slug>

Goal:    <one observable sentence>
Success: <checkable bar — what makes the whole task DONE>
Pattern: <1 synchronous | 2 background+monitor | 3 cron+monitor+shell>
Mode:    NORMAL | DIAGNOSING | ROTATING

Steps:
  1. [PENDING] <action one-liner>
        verify: <observable check>
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
```

### Per-step lifecycle

Each transition is written back to the runbook file:

```
PENDING → IN PROGRESS → DONE          (verify passed → next step)
PENDING → IN PROGRESS → BLOCKED       (verify failed → fix mode)
BLOCKED → IN PROGRESS → DONE          (rotation succeeded → NORMAL)
BLOCKED → PARKED                      (5 approaches failed → continue
                                       on independent steps)
```

### Fix mode — only entered on a verify failure

Fix mode is the ONLY time /auto deviates from the runbook. When a step's verify fails:

```
1. Mode → DIAGNOSING — read the failure signature
2. Mode → ROTATING   — pick a different approach (Approach Rotation Rules)
3. Apply, re-run the step
4. Verify pass → Mode → NORMAL, mark DONE, advance
5. 5 fails       → Mode → NORMAL, step PARKED, advance to next
                   independent step (Park, don't halt)
```

In NORMAL mode, /auto follows the runbook step by step without diagnosis or rotation. The runbook IS the path; the loop just walks it.

### Resumability

If /auto is interrupted (chat closes, reboot, cron tick missed), the runbook is the source of truth on resume:

```
1. Read the runbook file
2. Find the first step that is not DONE and not PARKED
3. Resume from that step
```

This is what makes Pattern 3 (cron mode) actually survive a chat going silent — the runbook is the contract; the cron heartbeat just keeps reading it.

### Generating the runbook — sources in priority order

```
1. ./prep-*.txt           — convert /prep's function list into runbook
                              steps; one runbook step per cycle phase
                              (Red / Green / Real / Audit per RISKY
                              function; Green + smoke per SAFE function)

2. ./auto/RUNBOOK.md      — prior runbook from a resumed cron-mode auto
   ./auto-runbook.txt        (resume in place; do NOT regenerate)

3. ./PLAN.md              — manual plan with explicit steps

4. The user's invocation  — derive 3-10 atomic, verifiable steps from
                              the goal + success conditions
```

Steps must be **atomic and verifiable**. "Implement the feature" is the GOAL, not a step. "Write feature_X.py with function `foo(bar) -> baz`" with verify "`python -c 'from feature_X import foo'` exits 0" is a step.

If a step's verify can't be expressed as an observable check, the step is not atomic enough — split it.


## The Activity Log

Alongside the runbook, /auto keeps an append-only activity log. Where the runbook tracks **state** (what step you're on), the log tracks **history** (everything that's been done, tested, tried, and why).

### Log file location

```
./auto-log.txt          Patterns 1 & 2
./auto/logs/run.log     Pattern 3 (with per-tick logs in ./auto/logs/<ts>.txt)
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
File edit/write       file path + lines changed
Mode transition       NORMAL → DIAGNOSING → ROTATING (or back)
Approach choice       which N/5 + the reason
Verify result         PASS/FAIL + the check that ran
Sibling note          P7 violation parked for later
/repair sub-loop      entry (with hypothesis list) and exit (verdict)
Cron tick             tick start and tick end (Pattern 3 only)
```

Long stderr / large diffs do NOT go on the log line. They go in per-action files in `./auto/logs/<timestamp>.txt` (Pattern 3) or stay in conversation (Patterns 1–2). The log line only references them: `[stderr in logs/2026-04-30T22-01-08.txt]`.

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
[2026-04-30T22:02:14Z] [DIAGNOSING] [Step 2] Diagnosis: widget_count off-by-one
[2026-04-30T22:02:15Z] [ROTATING] [Step 2] Approach 1/5: edit widgets.py:42
[2026-04-30T22:02:30Z] [ROTATING] [Step 2] Edit applied: len(items) → len(items)-1
[2026-04-30T22:02:34Z] [ROTATING] [Step 2] Re-ran pytest → exit 0
[2026-04-30T22:02:35Z] [NORMAL] [Step 2] Verify PASS, Mode → NORMAL
[2026-04-30T22:02:35Z] [NORMAL] [Step 2] DONE
```

The user can `tail -f ./auto-log.txt` during a run to watch live, OR `cat` it after for a complete audit trail of what was done, tested, tried, and why.


## Composition with /principles, /prep, and /repair

The user's standard invocation pattern is:

```
/principles  →  /auto (or /prep or /repair)  →  proceed
```

`/principles` is run first to load all eight principles into context (P1 test-at-scale, P2 conditions-upfront, P3 end-goal-in-sight, P4 audit-before-handback, P5 KISS, P6 think-before-coding, P7 surgical-changes, P8 goal-driven-execution). Then the action skill runs with the principles already active as standing checkpoints. Then `proceed` is the standing authorization.

When this pattern is detected (recent `/principles` skill invocation OR principle keywords in recent context), /auto skips re-reminding the user about principles and proceeds straight into Phase 0 plan ingestion + activation gate. The principles are already loaded; don't restate them.

/auto is most often run on top of /prep, /repair, or both. The runbook structure changes based on what /auto is consuming.

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

   Then Phase 9 integration steps from TESTING CONDITIONS card.

   Then BUILD STATUS card update + FINAL VERDICT.
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
   wants.
```

### /auto on top of /prep + /repair

The common case: /prep builds a function, the build cycle hits a RED-stays-failing or REAL-fails-in-pipeline situation, /auto invokes /repair as a sub-loop on that one failing step, then resumes the build runbook.

```
1. /auto walks the prep-derived runbook
2. Step N — function W's GREEN — fails verify (test won't pass)
3. /auto enters fix mode, but instead of generic rotation, recognizes
   this as a repair situation and invokes /repair as a sub-loop
4. /repair runs its 9-step loop on the failing test
5. /repair returns DONE (or STUCK)
6. /auto resumes the build runbook at step N+1 (or PARKs and continues
   if /repair STUCK)
```

The runbook tracks ALL of this — the original prep-derived steps stay; a /repair sub-loop is logged as a single step's "Approaches tried" entries with the diagnosis trail.


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

   The ONLY exits from /auto: **DONE**, **STUCK** (after 5 distinct failed approaches), or a Hard-Invariant trip in "Auto Does NOT Waive." The Phase 0 activation gate is the single exception, and it fires before /auto activates — not mid-run.

2. **Pre-action context, not pre-action gate.** Before doing something non-trivial, Claude states one or two sentences naming what it's about to do and why. This is for *user awareness*, not for *user approval*. There is no waiting period. Claude finishes the sentence and proceeds.

3. **Never advance on a bad result.** If a step's output doesn't satisfy the success condition, Claude does not pretend it did. The step is judged failed and a different approach is tried.

4. **Never repeat a failed approach.** Each retry must differ from prior attempts in at least one concrete variable (different parameter, different prompt, different command flag, different input). If five distinct approaches have all failed, declare STUCK and stop. Don't burn budget on cosmetic variations.

5. **Stop on DONE or STUCK, not on "looks good enough."** DONE means the actual success condition is met and verified. STUCK means approach rotation is exhausted and Claude can't honestly identify a sixth distinct approach.

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

   Re-read scope: `./auto-runbook.txt` (state) OR `./auto/RUNBOOK.md` (Pattern 3), the matching `./prep-<slug>.txt` (goal + specs), and the last ~30 lines of `./auto-log.txt` (recent history). If the files disagree with conversation memory, trust the files and acknowledge the file truth in the next text output.


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
CronCreate    Schedules wake-ups every N minutes. Each fire spawns
              a fresh claude code session that re-invokes /auto.

Monitor       In-session: streams events from a Bash background
              process so /auto can wait on a "done" pattern in a
              log without polling.

Bash          Runs the actual work. Use run_in_background=true for
              steps >30s so /auto keeps planning while they run.
```

There are NO external shell scripts (`monitor.py`, `shell.sh`, `teardown.sh` are gone). The assistant IS the monitor and shell. Each cron tick is a fresh model run that reads files, decides next action, executes, writes back, exits.

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
auto/GOAL.md            Frozen goal + success conditions
                        Written once at setup. Never modified.

auto/RUNBOOK.md         Step list + current state + mode
                        Updated after every step transition.

auto/PROGRESS.md        Last-tick summary (what fired this tick,
                        what's next). Helps the next tick orient.

auto/APPROACHES.md      Append-only retry log — every approach
                        tried for every step, with the reason it
                        failed.

auto-log.txt            Append-only activity log (also lives at
                        auto/logs/run.log under Pattern 3 for
                        per-tick separation).

auto/VERDICT_DONE       Touched on terminal success.
                        On detection at start of any tick,
                        /auto invokes CronDelete and exits.

auto/VERDICT_STUCK      Touched on terminal failure (5 approaches
                        per blocking step, all parked).
                        On detection, CronDelete + exit.

auto/logs/              Per-tick logs:
  tick-<ISO>.log        One file per cron tick.
  cron.log              Append-only summary of every tick start/end.
```

### How a cron tick actually flows

```
Tick fires → fresh claude code session → /auto re-invoked

  1. Read auto/RUNBOOK.md (state, current step, mode)
  2. Read auto/GOAL.md (frozen goal — never trust memory)
  3. Read tail of auto-log.txt (~30 lines of recent history)
  4. Check for auto/VERDICT_DONE or auto/VERDICT_STUCK
       If either exists → CronDelete + exit (loop self-uninstalls)
  5. Pick first non-DONE / non-PARKED step from runbook
  6. Execute that step:
       - Bash for direct commands
       - Bash with run_in_background=true for long ones
       - Monitor on the log to wait for completion signal
  7. Verify: run the step's verify check
       Pass → mark step DONE in runbook, append log line
       Fail → enter fix mode, /repair sub-loop, rotate up to 5x
  8. Update auto/RUNBOOK.md and auto-log.txt
  9. Write auto/PROGRESS.md with one-line "this tick did X" summary
 10. Exit. Next tick fires N min later.
```

Each tick is **stateless from the model's perspective** — every file read on every tick. No conversation memory carries between ticks. This is what makes the architecture survive context compression and chat idleness.

### Cron interval rule of thumb

```
tick interval ≥ 2 × expected step duration

Fast steps (file edits, quick commands)              → 1–2 min
Slow steps (test suites, builds, multi-min API)       → 5–15 min
Very slow steps (overnight ffmpeg renders)            → 15–30 min
```

Don't tick faster than the work can finish — overlapping ticks just stack. If unsure, start at 10 min and adjust based on PROGRESS.md observation.

### Self-uninstall

On every tick start, /auto checks for `auto/VERDICT_DONE` or `auto/VERDICT_STUCK`. If either exists:

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

`/prep + /auto` is the canonical Pattern 3 trigger. Build pipelines always warrant the cron heartbeat + stateless tick architecture, regardless of whether the user is present. The chat may close, the session may compress; the cron survives both.

When in doubt for shorter tasks, prefer Pattern 2 over Pattern 1.


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

Next:        <concrete next move if status != DONE,
              or "nothing — task complete" if DONE>
```

The report is the contract. If it says DONE, it's done. If it says PARTIAL, it lists exactly what's missing.


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

"Different" does NOT mean:

- Same command after a sleep
- Same prompt with reworded punctuation
- Same approach with a slightly larger timeout (unless the prior failure was specifically a timeout signature)


## When to Surface vs When to Resolve Internally

Auto absorbs most decisions. But some things must surface to the user:

- **Genuine STUCK.** All 5 approaches exhausted, no honest sixth available. Stop, report, hand back.
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


## Cron Mode (see Pattern 3 above)

Cron mode is Pattern 3 in the Execution Shape section above. The full architecture — CronCreate + Monitor + Bash, in-session, with state files on disk and self-uninstall via CronDelete on terminal verdict — is documented there.

The key thing to remember when reading older docs or code that still references `monitor.py` / `shell.sh` / `schtasks`: those are obsolete. Pattern 3 today is **claude code's own tools** (CronCreate, Monitor, Bash) coordinating around state files. There are no external scripts.


## Hard NOs

- **No "Phase 0: present plan for confirmation."** That phase is gone. The user already authorized by saying `/auto`.
- **No "should I proceed?" / "want me to do X?" / "ready to continue?"** These all violate hard invariant #1.
- **No silently advancing on bad output.** If a step failed, say so and rotate the approach.
- **No declaring DONE without evidence.** "I think it worked" is not done.
- **No requiring cron/monitor/shell for every /auto.** That architecture is for unattended overnight jobs only. Most /auto tasks are inline.
- **No burning past 5 failed approaches without declaring STUCK.** The whole point is bounded autonomy.


## Final Report Templates

### Inline auto, success
```
=== AUTO DONE ===
Goal:    <one sentence>
Result:  <what happened, with numbers>
Verified by: <evidence — log line / exit code / file existence>
```

### Inline auto, partial
```
=== AUTO PARTIAL ===
Goal:        <one sentence>
Done:        <what landed>
Missing:     <what didn't, with reason>
Next:        <concrete suggested move>
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
Hand back to user — recommend: <best concrete next step>
```

### Cron auto, on terminal verdict
Same shape, but written to `auto/VERDICT_DONE` or `auto/VERDICT_STUCK` and the cron self-uninstalls.


## TL;DR

- /auto = behavior mode, not pipeline architecture.
- Invocation is authorization. Zero follow-up gates.
- Inline shape is the default. Cron only for truly unattended overnight.
- Diagnose, rotate approaches, never advance on lies, stop on DONE or STUCK.
- One-line "[auto] doing X — why" heads-up before non-trivial actions, then proceed.
- Final report is honest with numbers, not vibes.
