---
name: auto
description: Universal autonomous mode. The user runs `/auto` (or says "go autonomous", "no gates", "just do it", "set and forget", "keep going until it's done") to authorize Claude to drive a task end-to-end without further prompts. The invocation IS the authorization — there is no follow-up confirmation gate. Claude states briefly what it's about to do, then executes, diagnosing and re-trying as needed, stopping only on genuine success (DONE) or genuine stuck (STUCK). Applies to any task — a single fix, a multi-step build, a long unattended job — not just pipelines. For long unattended jobs, an optional cron+monitor+shell architecture is available (see "Cron mode" section).
---

# Auto

Universal autonomous mode. The user invokes `/auto` to hand Claude a task; Claude executes it end-to-end with no further confirmations.

The invocation **is** the authorization. There is no Phase-0-confirm-the-plan gate. There are no "should I proceed?" checkpoints. There are no "want me to run X to verify Y?" offers. Claude states what it's about to do in one or two sentences, then does it, and reports back when DONE or STUCK.

## When to Use This Skill

- User says `/auto`, "go autonomous", "no gates", "just do it", "stop asking, just run it", "set and forget", "keep going until it's done", "while I sleep", "run the whole thing"

- User has expressed frustration at being asked for permission

- User has stated an end goal that requires multi-step execution and explicitly does not want to babysit

- ANY task the user has handed to Claude with the implicit understanding "you drive"

This skill is a **mode**, not a tool. It modulates how Claude executes any work, not what work to do.


## Hard Invariants

These never bend.

1. **Invocation is authorization.** The act of saying `/auto` (or any of the trigger phrases above) authorizes the entire task end-to-end. Claude does not ask "are you sure?", "should I proceed with the plan?", "want me to run X to check?", or any other confirmation. The user already said yes by invoking.

2. **Pre-action context, not pre-action gate.** Before doing something non-trivial, Claude states one or two sentences naming what it's about to do and why. This is for *user awareness*, not for *user approval*. There is no waiting period. Claude finishes the sentence and proceeds.

3. **Never advance on a bad result.** If a step's output doesn't satisfy the success condition, Claude does not pretend it did. The step is judged failed and a different approach is tried.

4. **Never repeat a failed approach.** Each retry must differ from prior attempts in at least one concrete variable (different parameter, different prompt, different command flag, different input). If five distinct approaches have all failed, declare STUCK and stop. Don't burn budget on cosmetic variations.

5. **Stop on DONE or STUCK, not on "looks good enough."** DONE means the actual success condition is met and verified. STUCK means approach rotation is exhausted and Claude can't honestly identify a sixth distinct approach.

6. **Honest reporting.** If 24 of 269 things failed, the report says 24 failed. Not "245 succeeded" with the rest swept under. The user can decide what to do with partial success — Claude's job is to surface it accurately.

7. **No skill-internal gates.** Phase-by-phase confirmations, "ready to proceed?" prompts, "I'll need your approval before X" — all forbidden. Genuinely destructive actions on shared/external state (force-pushing to a public repo, dropping a production database) are still flagged before execution, but routine local actions are not.


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


## Execution Shape — Inline vs Cron

Auto has two shapes. Pick one based on task duration and whether the user is present.

### Inline (DEFAULT)

For tasks that complete within the current Claude session — minutes to hours, user is around to receive the final report.

- No state files. No cron. No schtasks.
- Claude executes step by step within the chat.
- Background commands via `Bash` `run_in_background` for long-running work.
- Monitor tool for streaming progress events from logs.
- Reports DONE / STUCK / PARTIAL at the end.

This covers ~90% of `/auto` invocations. A bug fix, a refactor, a build-and-test cycle, an investigation, a sequence of file edits, a chained set of commands. Use it.

### Cron (ONLY when truly unattended overnight)

For tasks that genuinely run for hours unattended while the user sleeps — multi-hour builds, overnight data jobs, anything the user cannot stay around for.

- Set up `auto/` directory with `GOAL.md`, `PROGRESS.md`, `APPROACHES.md`.
- Generate `monitor.py` (judges output) and `shell.sh` (executes next action).
- Install Windows scheduled task or Unix cron heartbeat.
- Self-uninstall on DONE or STUCK.

Trigger keywords for cron mode: "while I sleep", "overnight", "by morning", "set up a loop and walk away", or the user explicitly asks for it.

If unsure, default to **inline**. The cron architecture is only worth it when the heartbeat-restart-on-crash property genuinely matters.


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


## Cron Mode — When Truly Unattended

If the task genuinely needs to run while the user is asleep / AFK / traveling, set up the cron architecture:

```
auto/
  GOAL.md           Task goal + success criteria. Immutable.
  PROGRESS.md       Current step, last action, last output.
                    Rewritten by shell each tick.
  APPROACHES.md     Append-only log of every retry approach +
                    why it failed. Approach rotation reads from
                    here.
  monitor.py        Reads state, judges current step, writes
                    next_action.sh, exits.
  shell.sh          Reads next_action.sh, executes, logs result,
                    deletes next_action.sh, exits.
  next_action.sh    Generated by monitor each tick. Consumed by
                    shell. Absent = nothing to do this tick.
  teardown.sh       Removes the cron entry on DONE / STUCK.
  VERDICT_DONE      Touched on success → loop self-uninstalls.
  VERDICT_STUCK     Touched on exhaustion → loop self-uninstalls,
                    leaves diagnosis for the user.
  logs/
    cron.log        Every cron tick.
    <ts>.log        Per-action shell log.
```

Cron interval rule of thumb: tick interval ≥ 2× expected step duration. Fast steps → 1–2 min. Slow steps (ffmpeg, multi-min API calls) → 5–15 min. Don't tick faster than the work can finish — it just stacks.

On Windows, use `schtasks /Create /SC MINUTE /MO N /TN "auto_<slug>" /TR "..." /F`. On Unix, `crontab` with the equivalent. Always self-uninstall on terminal verdict.

The cron architecture is opt-in. Default to inline.


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
