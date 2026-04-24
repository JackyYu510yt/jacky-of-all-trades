---
name: auto
description: Hands-off autonomous execution of a goal using a cron/monitor/shell loop. The user runs `/auto "<goal>"` (optionally `--audit` for a Codex review), Claude drafts a plan with steps, success conditions, fix scope, and verification approach, presents it for a single yes/no confirmation, then arms the loop and exits. From that point the loop runs every tick — the monitor judges actual output against the success condition, the shell applies fixes with the smallest verification that proves them, and the system only advances a step once it genuinely passes. Use when the user says "/auto", "run this autonomously", "work on this while I sleep", "set and forget", "keep going until it's done", or describes a multi-step task they can't babysit. Never pauses for user input once the confirmation gate is cleared.
---

# Auto

A hands-off autonomous execution loop. The user hands Claude a goal, Claude drafts the plan and presents it for one confirmation, then the user walks away. From there the loop runs until the goal is genuinely reached — no human in the loop, no pausing to ask, no advancing on bad output.


## When to Use This Skill

- User says `/auto`, "run this autonomously", "keep working on this while I sleep", "set and forget"

- User is about to step away and wants a multi-step task finished by the time they return

- A task has a clear end state but the path to it involves retries, diagnosis, and approach rotation

- User explicitly cannot accept interactive prompts (sleeping, traveling, AFK for hours)


## Invocation Forms

```
/auto "<goal>"             Draft plan → confirm → arm loop
/auto --audit "<goal>"     Draft plan → Codex audit → confirm → arm loop
```

The `--audit` flag is optional. Use it when the goal is fuzzy, the failure modes aren't obvious, or the stakes justify 1–3 extra minutes before arming. Skip it when the goal is well-understood and you want to sleep fast.


## Core Principle

**The monitor is the judge. The shell is the worker. The cron is the pulse.**

Three pieces, each with exactly one job:

- **Cron** — a heartbeat that can't be killed by a failure. Fires on an interval. Doesn't read output, doesn't reason, doesn't care if last tick crashed. Just wakes the monitor back up.

- **Monitor** — the brain. Reads the actual output of the last step, judges it against the success condition (not just "did files appear" — did the result satisfy the goal), and writes a diagnosis.

- **Shell** — the hands. Acts on the monitor's diagnosis. Runs the next step, retries the failing one with a new approach, or applies the fix the monitor identified.

The loop:

```
cron tick
  → monitor judges current output
    → PASS     → shell runs next step → cron tick
    → FAIL     → diagnose why → shell applies fix → cron tick
    → DONE     → write verdict → uninstall cron → stop
    → STUCK    → write verdict with reasoning → stop
```

**Nothing moves forward on a lie.** Most autonomous systems just keep going regardless of output quality. Auto re-judges the same step with a new approach until it's genuinely good, *then* advances.


## Hard Invariants

These never bend. Every part of the generated system must honor them.

- **No user prompts. Ever.** Once `/auto` exits, the system cannot ask anything. If the shell hits a question (sudo password, API key missing, "are you sure?"), that counts as a failure and goes into the diagnosis pipeline.

- **No advancing on bad output.** A step is not "done" because it ran without crashing. It's done because the monitor compared real output to the success condition and said yes.

- **Never retry the exact same failed approach.** Every failed attempt goes into `APPROACHES.md` with what was tried and why it failed. The next attempt must differ in at least one concrete variable.

- **Every failure produces a diagnosis backed by concrete evidence.** The monitor writes *why* the step failed AND the artifact that proves it — a log line, an exit code, an ffprobe value, a probe result. No hunches. A diagnosis without evidence is invalid, and the monitor must gather evidence before writing a next approach.

- **Bounded retries per step.** Default max is 5 distinct approaches per step. After that, the monitor writes `VERDICT_STUCK` with the full approach history and exits. (This is a user-visible stop, not a pause — they come back and decide.)

- **Cron is external.** If the monitor crashes mid-tick, cron still fires on schedule and restarts it. Self-healing at the loop level, not just the step level.


`========================================`

## Runtime Workflow

Seven phases. Phase 0 is interactive (you and Claude, together, before you sleep). Phases 1–5 are Claude's setup work after you confirm. Phase 6 is the loop running while you're gone.


`========================================`

### Phase 0: Plan and Confirm

The only phase that needs you awake. Goal: turn your prompt into a plan tight enough to run unattended, and get your one yes/no before arming.

1. **Quick read of the project.** Same sources as Phase 1 (prompt, README/CLAUDE.md, entry point, recent logs, existing state files), but at planning depth — enough to propose, not enough to finalize.

2. **Draft the plan inline.** Print these sections in plain language:

   - **Goal** — one sentence restating what you asked for.

   - **Steps** — numbered list, each with one-line action + one-line success test.

   - **Fix Scope** — what Claude can change during the loop (prompts, configs, params, stage rerun order) and what it can't (pipeline code, secrets, data deletion).

   - **Verification per step** — which of {probe, stage rerun, end-to-end, skip} fits, and what failure mode each catches. A step may stack multiple.

   - **Budget** — tick interval, max attempts per step, total wall-time cap if you named one ("by 7am"), rough cost ceiling if Claude calls are expected.

3. **Optional Codex audit.** If you passed `--audit`, route the drafted plan through Codex. Fold Codex's feedback inline, show the deltas as a diff-style block — *don't silently adopt changes*. You still have the gate after this; Codex informs, doesn't decide.

4. **Single confirmation gate.** Print:

   ```
   TL;DR:   Arm Auto to finish <goal>. <N> steps, <M> min ticks,
            <max> tries each, ~<est duration> total.
   Risk:    HIGH — runs unattended. Fix scope: <one-line summary>.
   Mode:    AUTONOMOUS until DONE or STUCK.
   Next:    Write GOAL.md, generate monitor + shell, install cron,
            exit. Teardown on DONE or STUCK is automatic.
   Proceed?
   ```

5. **You answer once.**

   - **Yes** → Phase 1. From here Claude is hands-on, you are hands-off.

   - **No** → ask what to revise, iterate the draft, gate again. No partial arming.

After the yes, no more interactive anything until you wake up and check `VERDICT_DONE` or `VERDICT_STUCK`.


`========================================`

### Phase 1: Read the Room

Before writing anything, understand what the user is trying to finish.

- Read the user's prompt carefully — the explicit goal is almost never enough. Look for implicit constraints: quality bars, time budgets, cost limits, "by morning", "before the meeting".

- Read the project files. Use Glob + Grep + Read on:

  - Any `README.md`, `CLAUDE.md`, or `GOAL.md` in the working directory.

  - The entry point of the pipeline or task they named.

  - Recent logs (if present) that show where things currently stand.

  - Any `PROGRESS.md` / state file already on disk — if this is a resumption, build on it rather than overwriting.

- Identify the *current step*. Not the full pipeline — the next real action the system is about to take. Everything downstream flows from being right about this.

Phase 1 ends when you can say in one sentence: "The user wants X, starting from Y, and will know it's done when Z."


`========================================`

### Phase 2: Define the Success Condition

This is the most important phase. A vague success condition breaks the whole system — the monitor can't judge, the loop can't stop, and the user wakes up to nothing finished.

A success condition must be:

- **Testable by a script.** Not "looks good". Something the monitor can check with file existence, ffprobe, a hash, a comparison, a Claude visual read, a return code.

- **Specific.** Not "the video renders" — "three MP4s exist in `outputFiles/<slug>/`, each ≥4s, each with audio, all frame-extractable by ffmpeg".

- **Tied to the actual goal.** "Stage 5 runs without crashing" is necessary but not sufficient. The real test is whether the output of Stage 5 satisfies what the user asked for.

- **Decomposable.** Multi-step goals break into per-step success conditions, each with its own test.

Write this to `GOAL.md` in a dedicated `auto/` directory inside the project. Format:

```markdown
# Goal

<One sentence: what the user asked for, in plain language.>

## Success Condition (Overall)

<Testable criteria for the full goal — the thing that must be true to write VERDICT_DONE.>

## Steps

1. <Step name>
   - Action: <what the shell does>
   - Success: <what the monitor checks to call this step passed>
   - Known failure modes:
     - <mode> → <fix approach>
     - <mode> → <fix approach>

2. <Step name>
   ...

## Fix Scope

Claude (inside the loop) is allowed to:
- <e.g. rerun any stage, edit prompts in config.json, swap API accounts>

Claude is NOT allowed to:
- <e.g. edit core pipeline code, delete user data, upload anything>

## Stop Conditions

- DONE: <full success condition met>
- STUCK: <max 5 approaches per step exhausted>
```

`GOAL.md` is **immutable** after Phase 2. The monitor reads it but never edits it. This is the anchor — everything else in the system can churn, but the definition of done cannot.


`========================================`

### Phase 3: Generate the Monitor

The monitor is a script the cron fires every tick. It reads state, judges, and either triggers the shell or writes the verdict.

Pick language by what's on hand:

- **Python** if the project is Python-heavy (ffmpeg pipelines, data jobs). Can use `subprocess`, `ffprobe`, `pathlib`, and invoke `claude -p` for reasoning tasks.

- **Bash** if the checks are pure file-existence / exit codes.

Place at `auto/monitor.py` (or `.sh`). Every tick it must:

1. **Read state.** Load `GOAL.md`, `PROGRESS.md`, `APPROACHES.md`.

2. **Short-circuit on done.** If `auto/VERDICT_DONE` or `auto/VERDICT_STUCK` exists, exit 0 immediately. (Cron will still fire, but these tick costs are near-zero.)

3. **Judge the current step.** Run the specific tests from `GOAL.md` for the current step. Pass or fail is a concrete boolean, not a vibe.

4. **Escalate to Claude only when needed.** For judgments a rule can't make (visual quality, "does this writing match the tone"), shell out to `claude -p "<prompt>"` with the state files as context. Give Claude a structured response format (e.g. JSON with `verdict`, `reason`, `next_action`) so the monitor can parse it. This is the only place the monitor reasons via LLM — everything else is rules.

5. **Write the diagnosis.** On fail, append to `APPROACHES.md`:

   ```markdown
   ## Step <N>.<attempt>  —  <timestamp>

   **Tried:** <one line — what the shell did last tick>

   **Result:** <one line — what the output was>

   **Evidence:** <the log line, exit code, ffprobe value, parsed output,
                 or probe result that proves the "why failed" — a concrete
                 artifact, not a hunch>

   **Why failed:** <diagnosis — specific, grounded in the Evidence line>

   **Next approach:** <what to try, different from everything above>

   **Verification plan:** <which checks from the menu will validate this
                          approach — probe, stage rerun, end-to-end, skip
                          — and what failure mode each catches>
   ```

   An entry without a concrete Evidence line is invalid. If the monitor can't cite specific evidence, it must run a probe or re-read logs until it can — or write `VERDICT_STUCK` with the reason "no conclusive evidence for last failure".

6. **Check approach budget.** If attempts on the current step ≥ 5, write `VERDICT_STUCK` with the full approach history in a reason block and exit.

7. **Hand off to shell.** Write a one-line command or action file (`auto/next_action.sh` or `auto/next_action.json`) for the shell to execute. Do not invoke the shell directly — let the shell be its own process so a shell crash doesn't take down the monitor.


**Template:**

```python
#!/usr/bin/env python3
# auto/monitor.py
import json, subprocess, sys, pathlib, datetime

AUTO_DIR = pathlib.Path(__file__).parent
GOAL = (AUTO_DIR / "GOAL.md").read_text()
PROGRESS_FILE = AUTO_DIR / "PROGRESS.md"
APPROACHES_FILE = AUTO_DIR / "APPROACHES.md"
VERDICT_DONE = AUTO_DIR / "VERDICT_DONE"
VERDICT_STUCK = AUTO_DIR / "VERDICT_STUCK"
NEXT_ACTION = AUTO_DIR / "next_action.sh"

def short_circuit():
    return VERDICT_DONE.exists() or VERDICT_STUCK.exists()

def judge_step(step_id: str) -> tuple[str, str]:
    """Return (verdict, diagnosis). Verdict is PASS/FAIL/DONE."""
    # Project-specific checks go here — Claude generates these from GOAL.md
    ...

def escalate_to_claude(context: str) -> dict:
    """For judgments rules can't make. Returns parsed JSON from Claude."""
    result = subprocess.run(
        ["claude", "-p", f"Read the files and respond in JSON with keys verdict, reason, next_action.\n\n{context}"],
        capture_output=True, text=True, timeout=300,
    )
    return json.loads(result.stdout)

def main():
    if short_circuit():
        return 0
    # ... read PROGRESS, run checks, write diagnosis or next action ...

if __name__ == "__main__":
    sys.exit(main())
```

Claude generates the `judge_step` body specific to the project. Every check in `GOAL.md` maps to one function in the monitor.


`========================================`

### Phase 4: Generate the Shell

The shell reads the monitor's handoff (`next_action.sh` or `next_action.json`) and executes it. It's dumb on purpose — no reasoning, no judgment, just "run this command, capture stdout/stderr/exit code, update PROGRESS".

Place at `auto/shell.sh` (or `.py` if the commands need structured args). Every invocation:

1. **Read `next_action`.** If missing, exit 0 (monitor hasn't decided yet).

2. **Execute.** Run the command. Capture stdout, stderr, exit code, wall time.

3. **Write to log.** Append a block to `auto/logs/<timestamp>.log` with command + output. Rotate or prune at 7 days.

4. **Update PROGRESS.md.** Record step, attempt number, command, exit code, output tail (last 50 lines).

5. **Delete `next_action`.** So the monitor has to produce a fresh decision next tick.

6. **Exit.** The next cron tick wakes the monitor, which re-judges.

**Do not** have the shell loop or self-schedule. One tick, one action, done. Cron is the only scheduler.


`========================================`

### Phase 5: Install the Cron Heartbeat

On Windows (the user's platform), use **Task Scheduler** via `schtasks`. Example for a 5-minute interval:

```bash
schtasks /Create /TN "auto_<project_slug>" \
  /SC MINUTE /MO 5 \
  /TR "bash -lc 'cd /c/path/to/project && python auto/monitor.py >> auto/logs/cron.log 2>&1'" \
  /F
```

Pick the interval based on step latency:

- Fast steps (seconds): 1–2 min ticks.

- Medium (ffmpeg, API calls that take a minute): 5 min ticks.

- Slow (multi-account scraping, long renders): 10–15 min ticks.

Rule of thumb: tick interval ≥ 2× the expected step duration. The cron's job is to wake the monitor *after* the last action finished, not to overlap.

**On DONE or STUCK**, the monitor (last task before exit) must also remove the scheduled task:

```bash
schtasks /Delete /TN "auto_<project_slug>" /F
```

Write this teardown into `auto/teardown.sh` so it's idempotent and inspectable.

On non-Windows hosts, use `crontab -e` equivalents. Detect platform in the setup session and generate the right one.


`========================================`

### Phase 6: The Loop (Running After You Exit)

This is what happens while the user sleeps. No /auto session is active — just cron, monitor, shell.

```
[cron tick every N minutes]
      ↓
[monitor.py]
  → VERDICT_DONE exists?  → exit 0 (nothing to do)
  → VERDICT_STUCK exists? → exit 0 (nothing to do)
  → read GOAL + PROGRESS + APPROACHES
  → judge current step
      ├─ PASS → advance PROGRESS to next step → write next_action → exit
      ├─ FAIL → diagnose → append APPROACHES → write next_action (new approach) → exit
      ├─ DONE (all steps pass) → touch VERDICT_DONE → teardown cron → exit
      └─ STUCK (≥5 attempts on step) → touch VERDICT_STUCK → teardown cron → exit
      ↓
[shell.sh]
  → read next_action → execute → log → update PROGRESS → delete next_action → exit
      ↓
[wait for next cron tick]
```

The user wakes up and checks `auto/VERDICT_DONE` or `auto/VERDICT_STUCK`. Either way, the state tells the full story — what was tried, what worked, what didn't.


`========================================`

## State File Layout

Everything lives in an `auto/` directory inside the working project.

```
auto/
  GOAL.md              — Goal + success condition + per-step success tests.
                         Written once in Phase 2. Immutable after.
  PROGRESS.md          — Current step, last attempt, last output tail, status.
                         Rewritten by shell each tick.
  APPROACHES.md        — Append-only log of every attempt on every step.
                         Prevents retrying the same thing.
  next_action.sh       — Monitor's handoff to shell. Deleted after shell runs.
                         Absent = shell has nothing to do this tick.
  monitor.py           — Generated in Phase 3. Project-specific judge.
  shell.sh             — Generated in Phase 4. Dumb executor.
  teardown.sh          — Removes the cron on DONE or STUCK.
  VERDICT_DONE         — Touched on full success. Loop stops.
  VERDICT_STUCK        — Touched on approach exhaustion. Reason inside.
  logs/
    cron.log           — Every cron tick's output.
    <timestamp>.log    — Per-action shell logs.
```

`GOAL.md`, `PROGRESS.md`, `APPROACHES.md` are plain Markdown so the user can skim them by eye when they wake up.


## Approach Rotation — The Anti-Stuck Mechanism

The single most common autonomous-loop failure is retrying the same broken thing forever. Auto prevents this with a hard rule:

**Before the monitor writes `next_action`, it must read all prior attempts in `APPROACHES.md` for the current step and confirm the new approach differs in at least one concrete variable.**

"Different" means:

- Different CLI flag or parameter.

- Different config value (API account, quality preset, model, temperature).

- Different prompt text (if the failing step is a Claude call).

- Different input file (if the input was the cause).

- Different stage boundary (re-run a parent stage to regenerate the failing stage's input).

"Different" does **not** mean:

- Same command with a longer timeout.

- Same command after a sleep.

- Same prompt with different punctuation.

If the monitor can't identify a genuinely different next approach after 5 attempts, it writes `VERDICT_STUCK` with the full history. Better to stop and let the user decide than to burn hours on cosmetic variations.


## Judging Output: Rules vs Claude Reasoning

The monitor has two judgment modes:

- **Rule-based** — file exists, exit code = 0, ffprobe returns duration ≥ 4.0, hash matches, row count > 0. Fast, deterministic, free. Use this wherever possible.

- **Claude-based** — visual quality check on an image pair, tone match on generated text, "does this output actually answer the prompt". Shell out to `claude -p "..."` with a structured-response schema. Slow (seconds), costs API credits, not deterministic.

**Rule:** always try the rule-based check first. Only escalate to Claude when rules genuinely can't decide. Every Claude call costs time and money, and the cron ticks every few minutes — the budget adds up.

When escalating, pass a focused prompt and a JSON response schema:

```bash
claude -p "$(cat <<EOF
Read these files:
- auto/GOAL.md
- auto/PROGRESS.md
- output at outputFiles/scene_plate_test/

Judge: does the current output of step 3 satisfy the success condition in GOAL.md?

Respond with JSON only, no markdown:
{"verdict": "PASS"|"FAIL", "reason": "<one sentence>", "next_action": "<one sentence or empty>"}
EOF
)"
```

Parse that JSON in the monitor. If parsing fails, treat as FAIL with reason "claude response unparseable" and escalate as a new approach.


## Verifying Fixes: The Menu, Not a Protocol

When the monitor diagnoses a cause and the shell has a fix, it does **not** automatically rerun the whole stage or the whole pipeline. It picks the smallest set of checks that would actually catch the fix being wrong. A fix may need zero, one, or several checks — whatever matches its risk surface.


**The menu:**

```
Check                When it's the right pick
─────────────────   ─────────────────────────────────────────────────
Probe                Fix is a single value / path / flag / config key.
                     A 5-second script can confirm it — open the file,
                     render the prompt template, read the env var, diff
                     the config — without touching any slow API.

Stage rerun          The fix only manifests in the stage's real output.
                     Rerun just that stage against existing upstream
                     outputs on disk. Don't rerun upstream stages.

End-to-end           The goal requires the integrated artifact (scene
                     consistency across clips, final concat, cross-stage
                     handoff). Run the pipeline on the already-produced
                     outputs when possible; fresh full run only when the
                     integrated output can't be assembled from parts.

Skip                 Fix is obviously correct and any check is wasted
                     work (e.g., renaming a string that the OS would
                     immediately error on if wrong). Rare — default to
                     at least one check.
```


**How Claude picks:**

- Name the failure modes the fix could introduce. One per line.

- For each failure mode, pick the cheapest check that would catch it.

- If multiple failure modes share a check, stack — don't duplicate.

- If a probe alone covers everything, don't also add a stage rerun "to be safe."

- If a probe doesn't cover the integration surface, add the stage rerun (or end-to-end) that does.

- Every chosen check is written into the `Verification plan` field of the APPROACHES.md entry, with its failure mode labeled.


**Stackable by design — examples:**

```
Fix                                     Checks chosen
───────────────────────────────────    ───────────────────────────────
Change one env var value                Probe only (read the var back,
                                        confirm type/format)

Change a prompt word in Stage 3         Probe (render template) +
                                        Stage 3 rerun (API output shape)

Change a ref path feeding Stages 3→5    Probe (file exists) +
                                        Stage 3 rerun +
                                        Stage 4 rerun +
                                        Stage 5 rerun
                                        (cascade — all downstream)

Swap API account on a rate-limited      Stage rerun only (the account
stage                                   swap only matters at real call)

Risky config change on high-stakes      Probe + Stage rerun + focused
stage that affects final artifact       end-to-end on the affected
                                        output pair
```


**Two negative rules:**

- **Never skip a check to save time on a risky fix.** Time saved on a bad fix that silently passes = night wasted on garbage output.

- **Never add a check that can't name a failure mode it catches.** Padding with "just to be safe" checks burns budget and muddies signals. If a check can't fail meaningfully, it shouldn't run.


**The DONE question is the same rule applied to the final state.** When all steps pass individually, run whatever minimal check proves the *integrated* goal holds. If per-step rules + the integrated artifact check both pass, DONE. If the goal is naturally per-step (no integration surface), the per-step passes are enough.


## What Counts as DONE

Strict definition: **every step in `GOAL.md` has been judged PASS, and the overall success condition has been judged PASS via whatever integrated check the goal calls for** (from the menu above — probe, end-to-end, or skip if the goal is naturally per-step).

Not enough:

- Last step ran and exited 0.

- Output files exist.

- No errors in the log.

These are necessary, not sufficient. DONE requires the monitor to judge the *integrated* state against the goal — lightweight when the goal is already satisfied by per-stage artifacts, heavier when the goal demands cross-stage integration. The check is picked during Phase 0 and written into `GOAL.md`; the monitor doesn't invent it at the last tick.


## What Counts as STUCK

The monitor writes `VERDICT_STUCK` when *any one* of these is true:

- Any single step has accumulated 5 distinct failed approaches.

- Total loop wall time exceeds a user-set budget (if specified in the original prompt, e.g. "finish by 7am" → compute a hard cutoff).

- An approach reveals an external blocker Auto cannot fix (expired credential, service down, hardware unavailable, requires sudo).

- The monitor detects state corruption (GOAL.md tampered, APPROACHES.md unreadable).

STUCK is not a failure of Auto — it's Auto being honest instead of thrashing.


## Hard NOs

- Do not prompt the user once setup exits. Not for confirmation, not for credentials, not for "are you sure".

- Do not edit `GOAL.md` after Phase 2. Even if the user prompt was ambiguous — better STUCK than goal drift.

- Do not advance a step because it "probably" passed. The success check is a function, run it.

- Do not retry without updating `APPROACHES.md`. Every attempt gets a diagnosis backed by concrete evidence, or the system goes in circles. No hunches in the Evidence field — a log line, an exit code, a probe output, or nothing.

- Do not stack verification checks that can't each name a failure mode they catch. "Just to be safe" is not a failure mode.

- Do not bundle multiple steps into one shell invocation. One tick, one action. Parallelism inside a step is fine (a single action can fan out); parallelism across steps is not.

- Do not edit core project code unless `GOAL.md`'s Fix Scope explicitly allows it. Prompts, configs, params — yes. Pipeline logic — no, unless the user opted in.

- Do not leave the cron installed after DONE or STUCK. Teardown is mandatory.

- Do not store secrets in `auto/` files. Reference env vars or existing config paths.


## Setup-Session Verdict Block

At the end of the `/auto` invocation, before exiting, print this block:

```
===========================================================
AUTO ARMED

Project:    <project dir>
Goal:       <one sentence>
Steps:      <N> steps
Tick:       every <N> min
Max tries:  <N> per step
Budget:     <total wall-time cap, or "none">

State:      auto/GOAL.md  auto/PROGRESS.md
Monitor:    auto/monitor.py
Shell:      auto/shell.sh
Cron:       <schtasks task name>

Stop on:    auto/VERDICT_DONE   or   auto/VERDICT_STUCK
Teardown:   auto/teardown.sh
===========================================================
```

The user reads this and knows exactly what's running, where to look when they wake up, and how to pull the plug if they change their mind.


## TL;DR

- **Phase 0 is the only time you're awake.** Plan, optional `--audit`, single confirmation gate. After yes → you're out.

- **Cron fires, monitor judges, shell acts.** Three pieces, one job each.

- **Success condition is defined upfront in GOAL.md.** Testable. Immutable.

- **Nothing advances until the current step genuinely passes.** No lies.

- **Fixes get the smallest verification that covers their failure modes.** Probe, stage rerun, end-to-end, or skip — stacked as the fix's risk demands, picked per-fix, not by a fixed protocol.

- **Every failure gets a diagnosis backed by concrete evidence.** Log line, exit code, probe output — no hunches.

- **5 distinct approaches max per step.** Then VERDICT_STUCK, not infinite thrash.

- **Cron teardown is automatic on DONE or STUCK.** No orphaned tasks.

- **Never pauses for the user after the gate.** Hands-off is the contract.
