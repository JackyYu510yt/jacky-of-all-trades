---
name: auto
description: Universal autonomous mode. The user runs `/auto` (or says "go autonomous", "no gates", "just do it", "set and forget", "keep going until it's done") to authorize Claude to drive a task end-to-end without further prompts. The invocation IS the authorization — there is no follow-up confirmation gate. Claude states briefly what it's about to do, then executes, diagnosing and re-trying as needed, stopping only on genuine success (DONE) or genuine stuck (STUCK). Applies to any task — a single fix, a multi-step build, a long unattended job — not just pipelines. For long unattended jobs, an optional cron+monitor+shell architecture is available (see "Cron mode" section).
---

# Auto

Universal autonomous mode. The user invokes `/auto` to hand Claude a task; Claude executes it end-to-end with no further confirmations.


## Installation (one-time, per machine)

The `/auto` skill ships with a hook script — `hooks/auto-log-hook.py` — that auto-appends every state-changing tool call to `./auto-log-<slug>.txt` (or `./auto-<slug>/logs/run.log` for Pattern 3) when an active /auto run is detected. Without this hook, log appending falls back to model discipline and gets unreliable on long runs.

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

**Verification:** after wiring, run `/auto` on a small task in any folder. After it generates the runbook, check the matching `./auto-log-<slug>.txt` — every tool call should appear as a one-line `[timestamp] [tool] <summary>` entry without the model having to remember to write them.

The invocation **is** the authorization. There is no Phase-0-confirm-the-plan gate. There are no "should I proceed?" checkpoints. There are no "want me to run X to verify Y?" offers. Claude states what it's about to do in one or two sentences, then does it, and reports back when DONE or STUCK.

## When to Use This Skill

- User says `/auto`, "go autonomous", "no gates", "just do it", "stop asking, just run it", "set and forget", "keep going until it's done", "while I sleep", "run the whole thing"

- User has expressed frustration at being asked for permission

- User has stated an end goal that requires multi-step execution and explicitly does not want to babysit

- ANY task the user has handed to Claude with the implicit understanding "you drive"

This skill is a **mode**, not a tool. It modulates how Claude executes any work, not what work to do.


## /goal Chain — Hard Harness Enforcement (recommended for any non-trivial run)

`/auto` alone is **prose discipline** — text the model reads from this file. The harness does not enforce it. The model can still emit a stop turn if it judges the work done, ignore an invariant under pressure, or drift on a long run. That is the gap behind "/auto stopped and asked me a question even though I said no gates."

For **hard, harness-enforced autonomy**, chain `/auto` with `/goal`:

```
/goal <observable success condition>
```

`/goal` installs a session-scoped prompt-based Stop hook. After every turn the small fast model (Haiku by default) reads the condition + transcript and returns yes/no. "No" forces another turn with the reason as guidance. "Yes" clears the goal automatically. The working model literally **cannot return control to the user** until the evaluator agrees the condition holds.

### Invocation patterns — soft vs hard vs strongest

```
/auto <task>                                Soft autonomy. Skill prose only.
                                            OK for short tasks; you can re-prompt
                                            if the model stalls.

/goal <condition>                           Hard autonomy. Harness-enforced.
                                            Condition itself is the directive;
                                            no runbook unless the task warrants it.

/goal <condition> then /auto <task>         Strongest mode. /goal is the
  (or chain in either order)                unbreakable "don't stop" wall;
                                            /auto adds runbook, approach
                                            rotation, log, fix mode, Patterns 1-3.
                                            Use this for any non-trivial unattended
                                            work.
```

### Writing the /goal condition

The evaluator judges only what's already in the transcript — it does NOT run commands or read files itself. Write the condition as something **Claude's own output can demonstrate**:

```
Good:  pytest tests/auth.py exits 0 AND existing suite green AND no new
       lint warnings

Bad:   the auth bug is fixed         ← unobservable; evaluator can't tell
```

The bar is the same as Phase 0's observable-success bar (exit code, file existence + size, test pass, metric clears threshold, visible artifact). Up to 4,000 chars. To bound run length, include a clause like "or stop after 20 turns" — the evaluator judges that from the transcript too.

### Phase 0 under an active /goal

When /auto activates inside a /goal session, treat the active condition as the frozen success criterion:

```
1. Phase 0 reads the active /goal condition FIRST (priority 0 in the
   source scan below).
2. Use that condition as the Phase 0 success check — no re-derivation.
3. Activation gate is automatically satisfied (the condition is, by
   definition, observable — /goal wouldn't be active otherwise).
4. Proceed straight to Phase 0.5 runbook generation.
```

This is what makes the chain seamless: /goal owns the "don't stop" wall; /auto owns the plan and execution. They don't duplicate work.

### Caveat — /goal requirements

`/goal` only runs in workspaces where the trust dialog is accepted, and is disabled when `disableAllHooks` is set or when `allowManagedHooksOnly` is on. If /goal is unavailable, /auto falls back to prose discipline only — surface that to the user in one line so they know which enforcement level is active.


## Phase −1 — Tool Preload (mandatory, before any other action)

Before Phase 0, before plan ingestion, before any tool call other than this one:

**Run `ToolSearch` with `select:Monitor,CronCreate,CronList,CronDelete` to load these tool schemas.**

These tools are mandatory for autonomous work and are NOT loaded by default. Skipping this step means:

- Long-running shell jobs only notify on exit — a 3-minute crash isn't seen until the 15-minute background-job timeout

- No way to schedule retries or periodic checkins for unattended jobs

- `/auto` degrades to "shell with extra confidence" — no live failure detection, no self-healing

**Every time you launch a long-running shell job in the background, immediately arm a `Monitor` on its log/output.** The filter MUST cover BOTH success markers AND failure signatures (`Traceback|Error|Killed|FAILED|OOM|assert` plus domain-specific completion markers like `[DONE]`, `Successful:`). Silence ≠ success — a filter that matches only the happy path makes a crash look identical to "still running."

**Use `CronCreate`** for scheduled retries, periodic state checks, deferred re-runs, or any "check back later" pattern that would otherwise require the user to remember.

This phase has NO output to the user. Load the tools, then continue to Phase 0.


## Phase 0 — Plan Ingestion + Activation Gate (mandatory first action)

Before anything else, /auto must lock in the end goal and at least one observable success condition. If it can't, /auto refuses to activate.

### Step 1 — Scan for an existing plan

Glob the working directory in this priority order:

```
0. Active /goal condition   (run `/goal` with no args — if a goal is
                             active, its condition IS the frozen success
                             criterion; skip activation gate and proceed)
1. ./auto-*/GOAL.md         (prior cron-mode auto — most recently modified wins)
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

### Slug derivation

Every /auto run gets a **slug** — a short identifier suffixed onto the runbook file, the log file, and (for Pattern 3) the state folder. This prevents collision when multiple /auto runs happen in the same directory.

Slug rules: lowercase, hyphenated, 2-4 words, no special chars. Source priority:

1. If the plan came from `./prep-<slug>.txt`, **reuse that slug** (e.g., `prep-stagger-distribution.txt` → slug = `stagger-distribution`).
2. Otherwise, derive from the goal sentence — pick 2-4 keywords, lowercase, hyphenate.

Examples:

- Goal "Fix the off-by-one in paginate()" → slug `paginate-off-by-one`
  - Files: `./auto-runbook-paginate-off-by-one.txt`, `./auto-log-paginate-off-by-one.txt`
- Goal "Build the staggered distribution system" → slug `stagger-distribution`
  - Pattern 3 folder: `./auto-stagger-distribution/`

Once chosen at Phase 0, the slug is **frozen for the run** — no renames mid-run. If a prior run with the same slug exists in the directory, /auto resumes it (per the resumability rules below) rather than starting a new one.

### Runbook file location

```
./auto-runbook-<slug>.txt   Patterns 1 & 2 (inline / background+monitor)
./auto-<slug>/RUNBOOK.md    Pattern 3 (cron+monitor+shell — lives with state files)
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

2. ./auto-*/RUNBOOK.md    — prior runbook from a resumed cron-mode auto
   ./auto-runbook-*.txt      (resume in place; pick most-recently-modified
                              if multiple exist; do NOT regenerate)

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
./auto-log-<slug>.txt        Patterns 1 & 2
./auto-<slug>/logs/run.log   Pattern 3 (with per-tick logs in ./auto-<slug>/logs/<ts>.txt)
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

Long stderr / large diffs do NOT go on the log line. They go in per-action files in `./auto-<slug>/logs/<timestamp>.txt` (Pattern 3) or stay in conversation (Patterns 1–2). The log line only references them: `[stderr in logs/2026-04-30T22-01-08.txt]`.

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

The user can `tail -f ./auto-log-<slug>.txt` during a run to watch live, OR `cat` it after for a complete audit trail of what was done, tested, tried, and why.


## Composition with /principles, /prep, and /repair

The user's standard invocation pattern is:

```
/principles  →  /auto (or /prep or /repair)  →  proceed
```

`/principles` is run first to load all eight principles into context (P1 test-at-scale, P2 conditions-upfront, P3 end-goal-in-sight, P4 audit-before-handback, P5 KISS, P6 think-before-coding, P7 surgical-changes, P8 goal-driven-execution). Then the action skill runs with the principles already active as standing checkpoints. Then `proceed` is the standing authorization.

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

   Re-read scope: `./auto-runbook-<slug>.txt` (state) OR `./auto-<slug>/RUNBOOK.md` (Pattern 3), the matching `./prep-<slug>.txt` (goal + specs), and the last ~30 lines of `./auto-log-<slug>.txt` (recent history). If the files disagree with conversation memory, trust the files and acknowledge the file truth in the next text output.


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
auto-<slug>/GOAL.md       Frozen goal + success conditions
                          Written once at setup. Never modified.

auto-<slug>/RUNBOOK.md    Step list + current state + mode
                          Updated after every step transition.

auto-<slug>/PROGRESS.md   Last-tick summary (what fired this tick,
                          what's next). Helps the next tick orient.

auto-<slug>/APPROACHES.md Append-only retry log — every approach
                          tried for every step, with the reason it
                          failed.

auto-log-<slug>.txt       Append-only activity log (also lives at
                          auto-<slug>/logs/run.log under Pattern 3
                          for per-tick separation).

auto-<slug>/VERDICT_DONE  Touched on terminal success.
                          On detection at start of any tick,
                          /auto invokes CronDelete and exits.

auto-<slug>/VERDICT_STUCK Touched on terminal failure (5 approaches
                          per blocking step, all parked).
                          On detection, CronDelete + exit.

auto-<slug>/logs/         Per-tick logs:
  tick-<ISO>.log          One file per cron tick.
  cron.log                Append-only summary of every tick start/end.
```

### How a cron tick actually flows

```
Tick fires → fresh claude code session → /auto re-invoked

  1. Read auto-<slug>/RUNBOOK.md (state, current step, mode)
  2. Read auto-<slug>/GOAL.md (frozen goal — never trust memory)
  3. Read tail of auto-<slug>/logs/run.log (~30 lines of recent history)
  4. Check for auto-<slug>/VERDICT_DONE or auto-<slug>/VERDICT_STUCK
       If either exists → CronDelete + exit (loop self-uninstalls)
  5. Pick first non-DONE / non-PARKED step from runbook
  6. Execute that step:
       - Bash for direct commands
       - Bash with run_in_background=true for long ones
       - Monitor on the log to wait for completion signal
  7. Verify: run the step's verify check
       Pass → mark step DONE in runbook, append log line
       Fail → enter fix mode, /repair sub-loop, rotate up to 5x
  8. Update auto-<slug>/RUNBOOK.md and auto-<slug>/logs/run.log
  9. Write auto-<slug>/PROGRESS.md with one-line "this tick did X" summary
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

On every tick start, /auto checks for `auto-<slug>/VERDICT_DONE` or `auto-<slug>/VERDICT_STUCK`. If either exists:

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
3. Cheapest first — read-only probe, info endpoint, single-call test
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
Same shape, but written to `auto-<slug>/VERDICT_DONE` or `auto-<slug>/VERDICT_STUCK` and the cron self-uninstalls.


## TL;DR

- /auto = behavior mode, not pipeline architecture.
- Invocation is authorization. Zero follow-up gates.
- Inline shape is the default. Cron only for truly unattended overnight.
- Diagnose, rotate approaches, never advance on lies, stop on DONE or STUCK.
- One-line "[auto] doing X — why" heads-up before non-trivial actions, then proceed.
- Final report is honest with numbers, not vibes.
- Operational heuristics #8-13: disk-is-truth, cite-the-incident, hand-test-before-coding, name-this-run-vs-next-run, adjacent-issue-radar, escalation-tree.
