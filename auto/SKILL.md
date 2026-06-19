---
name: auto
description: Universal autonomous mode. The user runs `/auto` (or says "go autonomous", "no gates", "just do it", "set and forget", "keep going until it's done") to authorize Claude to drive a task end-to-end without further prompts. The invocation IS the authorization — there is no follow-up confirmation gate. Claude states briefly what it's about to do, then executes, diagnosing and re-trying as needed, stopping only on genuine success (DONE) or genuine stuck (STUCK). Applies to any task — a single fix, a multi-step build, a long unattended job — not just pipelines. For long unattended jobs, an optional cron+monitor+shell architecture is available (see "Cron mode" section).
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
1. ./prep-*.txt             (output of /prep — most recently modified wins)
2. ./PLAN.md                (manual plan)
3. ./.claude/plans/*.md     (older /prep outputs)
4. User's invocation message + recent context
```

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

On DONE or STUCK, /auto deletes its session marker as part of the final report step. If the chat closes mid-run without a terminal verdict, the marker file is harmless leftover — the next /auto run will overwrite it (same session) or ignore it (different session).

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
  Refuter:           n/a   (judgment-based goals: pending | clean | <n> BLOCKERs | round 1|2)
```

`Refuter` rides in the runbook (the file the Stop hook reads) — not just in prose — so the "refute before DONE" rule survives context compaction. On a judgment-based goal it starts `pending` and the terminal `Status: DONE` MUST NOT be written until it reads `clean`. On a machine-checked goal it stays `n/a` (the verify check is the oracle; see Terminal Refuter Gate).

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

Resumption is **explicit-only** — /auto never auto-resumes a prior run by globbing for runbooks. The slug must be supplied by the invocation itself. Two ways this happens:

```
1. Pattern 3 cron tick — the CronCreate command encodes the slug
   in its prompt (e.g., "/auto resume slug=paginate-off-by-one-143205").
   Each tick reads ONLY the runbook matching that exact slug.

2. User-initiated resume — the user types
   "/auto resume <slug>" to manually pick up a prior interrupted run.
```

On resume, the runbook file is the source of truth:

```
1. Read ./auto-runs/<slug>/runbook.txt (or ./auto-runs/<slug>/RUNBOOK.md)
2. Find the first step that is not DONE and not PARKED
3. Resume from that step
```

If no slug is supplied, /auto generates a fresh one and starts a new run — parallel chats and accidental re-invocations never collide on someone else's state.

This is what makes Pattern 3 (cron mode) survive a chat going silent — the cron schedule carries the slug, and the heartbeat keeps reading the exact runbook it owns.

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

**Self-derived runbooks (source 4) get a verify-check sanity pass.** When the runbook came from a /prep file (source 1), its verify checks were already vetted by /prep's auditor. When /auto wrote the checks itself from the user's one-liner, nothing vetted them — and the Terminal Refuter Gate is *skipped* for machine-checked goals, so a weak check is the last line of defense and there's no net under it. Before executing a self-derived runbook, run one cheap sanity pass (a fresh sub-agent, no artifacts yet): hand it the Goal + Success line + the proposed verify checks and ask *"could any of these checks pass while the goal is still unmet?"* (the P1 test-at-scale failure — `import foo` that never calls `foo`, asserts a file exists but not its content, greps a string the script prints unconditionally). Any "yes" → tighten that check before running. This only fires on the bare path that lacks /prep's vetting.

**Freeze the self-derived Success line.** A Success line from /prep is frozen (line 137). A self-derived Success line gets the **same** freeze: once written to the runbook it is never re-derived or edited mid-run — only the steps beneath it change. This stops "done" from quietly redefining itself toward whatever was achieved after a compaction.

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
File edit/write       file path + lines changed
Mode transition       NORMAL → DIAGNOSING → ROTATING (or back)
Approach choice       which N/5 + the reason
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
[2026-04-30T22:02:14Z] [DIAGNOSING] [Step 2] Diagnosis: widget_count off-by-one
[2026-04-30T22:02:15Z] [ROTATING] [Step 2] Approach 1/5: edit widgets.py:42
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

`/principles` is run first to load all nine principles into context (P1 test-at-scale, P2 conditions-upfront, P3 end-goal-in-sight, P4 audit-before-handback, P5 KISS, P6 think-before-coding, P7 surgical-changes, P8 goal-driven-execution, P9 build-for-the-real-run). Then the action skill runs with the principles already active as standing checkpoints. Then `proceed` is the standing authorization.

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
   wants.
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

   Re-read scope: `./auto-runs/<slug>/runbook.txt` (state) OR `./auto-runs/<slug>/RUNBOOK.md` (Pattern 3), the matching `./prep-<slug>.txt` (goal + specs), and the last ~30 lines of `./auto-runs/<slug>/log.txt` (recent history). If the files disagree with conversation memory, trust the files and acknowledge the file truth in the next text output.

9. **No terminal DONE before the refuter clears (judgment-based goals).** When the Success line is a judgment call, the terminal `Status: DONE` / `FINAL VERDICT: DONE` line MUST NOT be written until the runbook's `Refuter:` field reads `clean`. The Stop hook releases on that `Status:` line, so writing DONE first would let the run stop before the refuter can re-open it. All-steps-PASS is necessary but NOT sufficient for DONE — the refuter gate is. Machine-checked goals are exempt (`Refuter: n/a`). See Terminal Refuter Gate.

10. **Probe, don't assume — empirical evidence governs every claim.** Never act on what *seems* true — what an error means, whether a step worked, whether a dependency / credential / file is in the expected state. Get the evidence first: run the cheapest probe that turns the assumption into an observation (artifact check, exit code, a one-shot **smoke test**, a re-read of the actual file). When there's no cheap probe, write a **specialized check that exercises the real target condition** (P1 test-at-scale — not a config flag standing in for the real thing) and run it. A verdict from one happy outcome is a hypothesis; a verdict from an isolating check is evidence ("pin the fix, don't guess" — one experiment that isolates a single variable beats inference). This generalizes #3 (never advance on a bad result) and the artifact rule in Universal Principles: those say *don't trust a bad or absent signal* — this says *go manufacture the signal rather than assume one*. A one-shot patch used to *make the probe possible* (work-once-to-smoke-test) is fine as scaffolding — but it is never DONE; the deliverable is the structural heal that survives the next-run-without-Claude test (see /repair HI #17). Patch to learn, then fix the cause.

11. **See it before you call it — a visual verify is not PASS until the shot is read.** When a verify/smoke step decides pass/fail on a visual surface (a browser, a GUI window, a rendered frame), its screenshot is captured *inside the test* at each state-change + assertion, and /auto MUST read the relevant shot (assertion + final + any failure shot) before recording PASS/FAIL. A passing exit code or a matched log string is necessary but NOT sufficient on a visual surface — a signed-out page prints a prompt box and exits 0 just like a signed-in one (the account-95 miss: a captured-but-unread shot plus a weak text assertion produced a confident wrong verdict). So a visual verify is treated as judgment-shaped: the Terminal Refuter Gate does NOT skip it (this overrides the machine-check exemption in #9 for that step), and a missing / black / unread assertion shot makes the verify INCONCLUSIVE → the step goes BLOCKED/PARKED, never PASS. The stall-detection fallback ("shot unavailable → artifact probes") is for watching long jobs, NOT for clearing a visual verify. See the "Smoke-test / verify capture" subsection under Visual Checkpoints.


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
              The cron's prompt MUST encode the slug, e.g.
              "/auto resume slug=<slug>" — so every tick targets
              the exact runbook this cron owns. Without the explicit
              slug, parallel /auto runs in the same directory would
              collide on Phase 0 slug derivation.

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

auto-runs/<slug>/VERDICT_STUCK Touched on terminal failure (5 approaches
                          per blocking step, all parked).
                          On detection, CronDelete + exit.

auto-runs/<slug>/logs/         Per-tick logs:
  tick-<ISO>.log          One file per cron tick.
  cron.log                Append-only summary of every tick start/end.

auto-runs/<slug>/shots/        Visual checkpoints — one PNG per capture
                          (see Visual Checkpoints).
```

### How a cron tick actually flows

```
Tick fires → fresh claude code session → /auto re-invoked

  1. Read auto-runs/<slug>/RUNBOOK.md (state, current step, mode)
  2. Read auto-runs/<slug>/GOAL.md (frozen goal — never trust memory)
  3. Read tail of auto-runs/<slug>/logs/run.log (~30 lines of recent history)
  4. Check for auto-runs/<slug>/VERDICT_DONE or auto-runs/<slug>/VERDICT_STUCK
       If either exists → CronDelete + exit (loop self-uninstalls)
  4b. TICK LOCK — check auto-runs/<slug>/TICK_LOCK:
       - fresh lock (timestamp < one interval old) → a prior tick is
         still working; exit immediately (do NOT start a duplicate —
         this is what prevents two ffmpeg jobs on the same output)
       - stale lock (older than one interval) → prior tick died mid-step;
         treat its in-progress step as STALLED, escalate per heuristic #13
       - no lock → write TICK_LOCK with current timestamp, continue
  4c. If the runbook shows a long step IN PROGRESS with a visual
      surface → capture + read a visual checkpoint (see Visual
      Checkpoints). Job surface identical to the previous tick's shot
      AND the heuristic #8 artifact probe shows no growth → treat the
      step as STALLED (heuristic #13). Background jobs with no window:
      frame-grab the output artifact instead of the desktop.
  5. Pick first non-DONE / non-PARKED step from runbook
       (if none and success unmet → write Status: PARTIAL + VERDICT, exit —
        the all-parked terminus; never tick forever with nothing to do)
  6. Execute that step:
       - Bash for direct commands
       - Bash with run_in_background=true for long ones
       - Monitor on the log to wait for completion signal
  7. Verify: run the step's verify check
       Pass → mark step DONE in runbook, append log line
       Fail → enter fix mode, /repair sub-loop, rotate up to 5x
  8. Update auto-runs/<slug>/RUNBOOK.md and auto-runs/<slug>/logs/run.log
  9. Write auto-runs/<slug>/PROGRESS.md with one-line "this tick did X" summary
 10. Remove auto-runs/<slug>/TICK_LOCK (release for the next tick), then exit.
     Next tick fires N min later.
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

`/prep + /auto` is the canonical Pattern 3 trigger. Build pipelines always warrant the cron heartbeat + stateless tick architecture, regardless of whether the user is present. The chat may close, the session may compress; the cron survives both.

When in doubt for shorter tasks, prefer Pattern 2 over Pattern 1.


## Sub-agent Delegation — fan-out & context offloading

Two execution disciplines that keep /auto fast and survivable on long jobs. Both delegate to throwaway sub-agents (the `Agent` tool) with isolated context, so the **driver's own context stays lean**. A sub-agent never inherits the session history — construct exactly the scope + inputs it needs, and take back only its conclusion.

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

Before emitting DONE on a **judgment-based** goal, the report must have passed the **Terminal Refuter Gate** (see below) — on those goals, DONE is the refuter's verdict, not the driver's self-grade.


### Build for the real run (P9 — practicality)

Judge every step and the final verdict against the REAL operating envelope, not the demo: the real input size, the real run duration, unattended execution, messy/missing inputs, resource limits, and recovery after a partial failure. A green run on a small or clean sample is NOT DONE if the real job is bigger, longer, or dirtier — verify against the conditions the task will actually meet. This covers only conditions you can prove will occur; a safeguard for an imaginary case is still a P5 (KISS) violation, not practicality.

Most of /auto's machinery already serves this — the self-derived verify sanity pass (P1), stage-mode's different-input re-run, disk-is-truth (#8), the escalation tree (#13), checkpointed cron state, and the Terminal Refuter's "holds on a different input with no Claude present" check. P9 is the name that ties them together and the bar the final report is judged against. (Unnumbered on purpose — the numbered list 1–7 continues into the Operational Heuristics' #8–13, so this anchor sits outside that run to avoid renumbering them.)

## Operational Heuristics — patterns from production runs

The principles above are abstract. These six are the tactical patterns that make /auto trustworthy on long-running, real-world systems (pipelines, services, vendors). Born from real incidents.

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

**The all-parked terminus (never freeze).** When no step is PENDING or IN PROGRESS — every remaining step is DONE or PARKED — the run is terminal. It MUST write a verdict, never keep ticking with nothing to advance:

```
- Success condition met (despite parked steps)  → refuter gate, then Status: DONE
- Success condition NOT met (parked steps blocked it) → Status: PARTIAL,
  listing each parked step + reason
```

A runbook with no advanceable step and no terminal `Status:` line is the silent-freeze failure: the Stop hook keeps returning "continue" while there is nothing to do. `PARTIAL` is a terminal verdict the Stop hook honors — writing it ends the run cleanly. Never leave an all-parked runbook without a `Status:` verdict.


## Cron Mode (see Pattern 3 above)

Cron mode is Pattern 3 in the Execution Shape section above. The full architecture — CronCreate + Monitor + Bash, in-session, with state files on disk and self-uninstall via CronDelete on terminal verdict — is documented there.

The key thing to remember when reading older docs or code that still references `monitor.py` / `shell.sh` / `schtasks`: those are obsolete. Pattern 3 today is **claude code's own tools** (CronCreate, Monitor, Bash) coordinating around state files. There are no external scripts.


## Hard NOs

- **No "Phase 0: present plan for confirmation."** That phase is gone. The user already authorized by saying `/auto`.
- **No "should I proceed?" / "want me to do X?" / "ready to continue?"** These all violate hard invariant #1.
- **No asking after a plan is written.** When /auto is chained with a planning skill (`/auto /prep`, `/auto /optimize`, `/auto /repair`), the plan landing is the runbook-generation trigger — NOT a confirmation point. Asking "should I build the plan now?" or "Phase 8 ready, proceed?" is a hard-invariant violation. Plan → runbook → execute is one continuous flow.
- **No silently advancing on bad output.** If a step failed, say so and rotate the approach.
- **No declaring DONE without evidence.** "I think it worked" is not done.
- **No requiring cron/monitor/shell for every /auto.** That architecture is for unattended overnight jobs only. Most /auto tasks are inline.
- **No burning past 5 failed approaches without declaring STUCK.** The whole point is bounded autonomy.


## Terminal Refuter Gate — independent DONE check

Before /auto writes `Status: DONE`, one fresh agent tries to prove it is NOT done. This is the **independent upgrade** of the same-context "AUDIT vs END GOAL" step: the brain that did the work shares every blind spot that produced it, so it is the wrong brain to clear it. Empirically, a model grading its own output is unreliable (intrinsic self-correction often fails to improve and can degrade), and self-preference bias bites hardest exactly when the work is weakest — the worst time to be blind. An independent verifier is the documented fix, and verification is the cheap side of the generator-verifier gap.

### When it fires

Only when "done" is a **judgment call**. If the runbook's success line is a deterministic machine check that already passed (`pytest` exits 0, checksum matches, file exists at expected size), **SKIP** the refuter — that verify check IS the independent oracle, and self-preference can't bias a green test. Fire it when success is judgment-shaped: "pipeline handles real input", "output looks right", "report is complete", "no regressions in adjacent features".

### Sequence (refute first, flip second)

```
1. All runbook steps verified PASS   (necessary, NOT sufficient for DONE)
2. → set runbook Refuter: pending, dispatch refuter   (Status still NOT DONE)
3a. refuter clean      → set Refuter: clean → write Status: DONE → emit AUTO DONE
3b. refuter BLOCKER    → set Refuter: <n> BLOCKERs → keep Status non-DONE,
                          re-enter fix mode on the unmet item
```

Running the refuter AFTER flipping Status would release the Stop hook (see auto-stop enforcement + Hard Invariant #9) and the run couldn't re-enter cleanly. Refute first, flip second — and the `Refuter:` field carries this in the runbook so it survives compaction.

### The refuter brief

Dispatch a fresh sub-agent (`Agent` tool, subagent_type `general-purpose`) — the same machinery /audit and /prep use. Hand it ONLY:

- the **frozen Success line + per-step verify checks** (the yardstick — nothing else),
- the observable artifacts produced,
- a **baseline "before" reference if one exists** (git HEAD, a pre-change snapshot, the prior output dir) — part of the yardstick, so the refuter can diff the deliverables against it and flag unexplained or out-of-scope changes; greenfield builds have no baseline, so don't fabricate one (added 2026-06-14),
- the Implementation Notes Design Decisions / Deviations cards (so it refutes against intent, not re-litigating settled forks).

Brief: *"You are the REFUTER. The work below claims to be DONE. Prove it is NOT — find a specific Success-line item or verify check that is unmet. Read the artifacts yourself. Return ranked findings BLOCKER / CONCERN / NOTE, each with evidence. A BLOCKER is a concrete unmet success criterion, not a nitpick. Default to finding holes; do not rubber-stamp."* (If /repair is in the chain, add: *"A real fix holds on a different input with no Claude present — does it?"* per the structural-fix rule.)

### Verdict handling — severity-gated

- **BLOCKER** (maps to a specific unmet Success item / failed verify) → re-enter fix mode on that item. ONLY a BLOCKER re-opens /auto.

- **CONCERN / NOTE** → logged to the Notes file's Open Questions. Does NOT block DONE.

### Bound (so it can never loop forever)

Max **2 refute rounds** per run. /auto has no other run-level loop counter — without this bound, a refuter that keeps finding holes prevents termination. On the 2nd round still BLOCKER → stop and emit **AUTO PARTIAL** listing the refuter's open holes. Never silently loop; never silently DONE.

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
Notes:   ./auto-runs/<slug>/notes.md  (decisions + open questions)
```

### Inline auto, partial
```
=== AUTO PARTIAL ===
Goal:        <one sentence>
Done:        <what landed>
Missing:     <what didn't, with reason>
Coverage:    <success checks passed, e.g. 5/7 = 71%>
Next:        <concrete suggested move>
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
Hand back to user — recommend: <best concrete next step>
Notes:       ./auto-runs/<slug>/notes.md  (decisions + open questions)
```

### Cron auto, on terminal verdict
Same shape, but written to `auto-runs/<slug>/VERDICT_DONE` or `auto-runs/<slug>/VERDICT_STUCK` and the cron self-uninstalls.


## TL;DR

- /auto = behavior mode, not pipeline architecture.
- Invocation is authorization. Zero follow-up gates.
- Inline shape is the default. Cron only for truly unattended overnight.
- Diagnose, rotate approaches, never advance on lies, stop on DONE or STUCK.
- One-line "[auto] doing X — why" heads-up before non-trivial actions, then proceed.
- Final report is honest with numbers, not vibes.
- On judgment-based goals, an independent refuter must fail to break it before DONE (bounded 2 rounds → PARTIAL; BLOCKER-only re-entry). Machine-checked goals skip it.
- Fan out same-check × N-item steps to capped sub-agents; offload heavy reads to throwaway sub-agents to keep the driver's context lean.
- Visual checkpoints: screenshot major events + ~10-min intervals on long visual steps, READ every shot; two identical job-surface shots + a flat artifact probe = STALLED.
- Operational heuristics #8-13: disk-is-truth, cite-the-incident, hand-test-before-coding, name-this-run-vs-next-run, adjacent-issue-radar, escalation-tree.
