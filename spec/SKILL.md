---
name: spec
description: Create and maintain a project's SPEC.md — a single source-of-truth file that pins the goal/logic/scope/success on top and keeps a newest-first "why" change log below. Run /spec to start a project's spec (full interview) or to log the current session's changes as one structured block. Use when the user says "/spec", "start a spec", "log this", "update the spec", "write a change log entry", or when an in-project edit session needs its reasoning captured before the chat ends. Paired with the spec-collect (PostToolUse) and spec-guard (Stop) hooks.
---

# /spec — source-of-truth spec + self-maintaining "why" log

Three modes, auto-detected. The fiddly file mechanics (lock, atomic write,
durable line-count marker) live in `spec_tool.py` next to this file — call it,
do NOT re-implement them by hand.

Helper path: `C:\Users\Shadow\.claude\skills\spec\spec_tool.py`

## Evidence discipline (all modes)

Never write an assumption into the spec as if it were fact. **Success criteria**
especially must be things you can *prove* — each one empirically checkable (a
smoke test, a probe, a specialized test that hits the real condition, not a
proxy). When a Change Log or Findings entry claims something works, or explains
*why*, it rests on observed evidence — a run, a probe, a test result — not on
what seemed true. A suspected verdict stays flagged as suspected until a
decisive check confirms it.

## Mode detection

- No `SPEC.md` in the current project dir → **INIT**.
- The user's arg is `skip` → **SKIP**.
- `SPEC.md` exists and no `skip` arg → **LOG**.

## INIT — full interview, then scaffold

The goal is the strongest possible foundation. Ask the user — one thing at a
time, plainly — then write the file:

1. **Goal** — one or two sentences; what "done" looks like.
2. **Logic / how it works** — the approach and the reasoning behind it.
3. **Scope** — what's IN v1, and what's explicitly OUT.
4. **Success criteria** — the bar to clear. When the project processes
   volume (a batch, many items, a long unattended run), the bar must be
   *graduated and scale-proof*, not "works once": one rung per scale —
   smoke (1 item works end-to-end), batch (a small set, 0 failures,
   consistent output), full (the whole set, failures reported by count,
   never hidden). Pinning the ramp here means any executor that reads
   this spec (e.g. `/auto`) inherits the ladder automatically. Skip the
   rungs only when there's no volume (a rename, a one-shot single-item
   script) — don't fabricate a ladder for a task that only ever runs once.
5. **Phases / blueprint** — the **default** for any task beyond a trivial
   one-shot. Break the work into an ordered blueprint using the three-level
   format below (PHASES ▸ MILESTONES ▸ STEPS — only as deep as the task needs).
   This is the step-by-step plan `/auto` follows so it doesn't guess. Skip it
   ONLY for a trivial single-action task (a rename, a config flip), where one
   phase would just restate the success criteria.

Then Write `./SPEC.md` from this template (fill the sections; leave the Change
Log empty):

```
# <Project> — Spec

## Goal
<goal>

## Logic / How it works
<logic>

## Scope
**In (v1):**
- <...>
**Out (v1):**
- <...>

## Success criteria
- <...>

## Phases (blueprint — default; omit only for a trivial one-shot)
<!-- Ordered PHASE ▸ MILESTONE ▸ STEP plan /auto follows. One block per phase. -->

---

## Change Log
<!-- Newest first. One structured block per real change. -->
```

Tell the user it's created and that changes are now tracked.

### Phase blueprint — the step-by-step plan /auto follows

For any task beyond a trivial one-shot, the `## Phases` section holds an ordered
blueprint `/auto` runs without guessing. It nests in **three zoom levels** —
write only as deep as the task needs:

```
PHASE        a milestone-sized goal with its own conditions + checkpoint
  MILESTONE    a waypoint inside a phase, with its own checkpoint (optional layer)
    STEP         a single action (the flexible doing)
```

**Depth scales with the task** (KISS — don't nest deeper than it earns):
- Trivial one-shot (a rename) → no blueprint; the top-level Goal + Success
  criteria already cover it.
- Normal task → PHASES with STEPS directly under each (no milestone layer).
- Big / risky / failure-prone (a login flow) → full depth PHASE ▸ MILESTONE ▸
  STEP, so a failure narrows to one waypoint instead of the whole phase.

**Phase block — the unit `/auto` reads and runs:**

```
## Phase N — <what this phase achieves>

REQUIRES:          <condition that must be true first>   ← from Phase <X>            [HARD]
                   <another condition>                   ← external: <how to get it>  [HARD]
VERIFY-REQUIRES:   <exact yes/no check that proves we're ready>                       [HARD]
PRODUCES:          <output / now-true condition that feeds later phases>
DONE-WHEN:         <observable checkpoint proving this phase succeeded>               [HARD]

STEPS:             1. <action>   2. <action>   ...        (guidance — flexible)
```

**When a phase earns the milestone layer**, replace its flat `STEPS` with named
milestones, each carrying its own checkpoint:

```
  Milestone N.1 — <waypoint name>
        DONE-WHEN: <checkpoint for this waypoint>         [HARD]
        STEP: <action>   STEP: <action>
  Milestone N.2 — <waypoint name>
        DONE-WHEN: <checkpoint>                           [HARD]
        STEP: <action>
```

- **Hard vs flexible.** `REQUIRES`, `VERIFY-REQUIRES`, and every `DONE-WHEN`
  (phase- or milestone-level) are the rails — crisp and checkable (an exit
  code, a file + size, a parseable assertion, a read screenshot). `STEP`s are
  guidance; `/auto` improvises the route between checkpoints. The blueprint pins
  the *where*, not the *how*.
- **Setup is its own phase.** Reaching a condition is always written as an
  earlier phase, never fixed inline. The first phase(s) usually *establish the
  testing conditions* (e.g. *get a logged-in account*); the phases that need
  them list those conditions under `REQUIRES`.
- **Source-of-condition tag.** Every `REQUIRES` line names its source:
  `← from Phase <X>` (an earlier phase produces it — `/auto` can satisfy it) or
  `← external: <how to obtain it>` (a human / a dropped-in file / another system
  supplies it — `/auto` cannot manufacture it, so the recipe is written right
  there). This is what lets `/auto` tell *"I'm stuck"* apart from *"I need
  accounts — here's how to get them."*
- **More, smaller units = closer checkpoints = less drift.** Each `DONE-WHEN`
  is a place `/auto` re-checks it's still on track; the milestone layer exists
  so a failure boxes into one waypoint instead of the whole phase.

**Quality bar — a blueprint isn't done until it's airtight.** Do NOT consider
the Phases section complete while any HARD field is blank or hand-wavy (a
`REQUIRES`, `VERIFY-REQUIRES`, or `DONE-WHEN` that isn't concretely checkable,
or a `REQUIRES` with no source tag). A vague field is exactly the gap `/auto`
would improvise into — close it here, at planning time. For a non-trivial
blueprint, route it through `/audit` (independent review of the *plan*) before
any step runs.

## LOG — one tidy block per *logical* change

1. Look at what changed this session — your own edits, and for the record
   `./.spec/pending-*.jsonl`.
2. Compose ONE block covering the whole logical change. Field lines (omit
   `context` / `before` / `after`, or use `n/a`, when they don't apply):

   ```
   change: <short title of what changed>
   why: <the reason it was added/changed>
   context: <surrounding constraints / situation>
   before: <state before this change>
   after: <state now, after it>
   ```

3. Pipe those field lines to the helper on stdin (it stamps the date, prepends
   newest-first under a lock, and advances the marker):

   ```
   python "C:\Users\Shadow\.claude\skills\spec\spec_tool.py" log
   ```

4. Confirm to the user: one block written, marker advanced.

**Do NOT** write one block per file-touch — one block per *logical* change.
The note-taker already records every edit; your job is the reasoning.

### Incoming findings from /auto and /prep

`/auto` and `/prep` keep a per-run **Findings Ledger** (lessons learned: context,
proven result, and a *suspected* verdict for why). At their terminal verdict they
promote keeper findings here by piping a translated block to `spec_tool.py log`,
so promoted entries land in the Change Log already mapped to this schema:

```
change:  FINDING: <summary>        ← the finding
why:     suspected — <verdict>     ← the suspected verdict (stays flagged a guess)
context: <context>
before:  <prior assumption / what was failing>
after:   <proven result>
```

These arrive pre-formatted from the helper — nothing extra to do. The `FINDING:`
prefix and `suspected —` marker are what distinguish a promoted lesson from a
normal change block; preserve them. Do not "upgrade" a suspected verdict into a
stated fact when you see one.

## SKIP — throwaway session

```
python "C:\Users\Shadow\.claude\skills\spec\spec_tool.py" skip
```

Arms a one-shot release so the Stop guard lets this chat end once without a log
entry. Use only when the session's edits genuinely don't need a "why".

## Notes

- All of this only matters in projects that have a `SPEC.md`. Everywhere else
  the hooks are silent (zero footprint).
- The Stop guard's nudge is internal — tagged "NOT a message to you". It's the
  cue for you to run `/spec log`, not user-facing output.
- `status` subcommand prints the unlogged-edit count (debug).
- To hand a fresh chat the full picture, give it `SPEC.md` (manual — there is
  no auto-load).
