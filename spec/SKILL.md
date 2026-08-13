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
proxy). And they must name the **user-visible result** (the deliverable existing
in the world), never machinery milestones ("the loop runs", "the fix is merged")
— machinery belongs in phases; criteria phrased as sub-goals produce truthful
"DONE" reports over undelivered results (P12, adopted 2026-08-12). When a Change Log or Findings entry claims something works, or explains
*why*, it rests on observed evidence — a run, a probe, a test result — not on
what seemed true. A suspected verdict stays flagged as suspected until a
decisive check confirms it. A `why:` that claims a **cause** must NAME the
decisive check that pinned it — the one probe that isolated the variable
(/principles P11, "Pin the cause before the fix") — or stay flagged
"suspected". A cause with no named probe is a guess wearing a conclusion's
clothes.

The decisive check must be a **discriminating test** — one whose outcome
separates the claimed cause from its plausible rivals, not one that merely
confirms the current assumption (a check both causes would pass pins nothing).
Same bar for success criteria and every `DONE-WHEN`: a check that would also
pass while the goal is unmet is not a real check — it must distinguish
goal-met from the nearest plausible not-met state (signed-in vs signed-out,
rendered vs black frames). Do not prematurely converge on the first reading: a
cause is written as fact only when the relevant alternatives were investigated
or explicitly ruled out — avoid **search-space neglect** and **anchoring
bias** by actively checking plausible alternatives.

## Goal-compass + confidence/risk footer (all user-facing /spec reports)

Every user-facing /spec report — the INIT completion message, the LOG
confirmation, any "spec updated" summary — ends with this block:

```
ULTIMATE GOAL (4 lenses, derived from the spec's Goal — frozen):
  Delivers:   <the finished result that arrives with zero input from the user>
  Heals:      <how failures recover or surface themselves, no human needed>
  Replaces:   <whose job/attention the system deletes — nobody left in the loop>
  Guarantees: <what wrongness is structurally impossible>
NEXT STEP: <the immediate milestone between current state and that goal>
SUGGESTED ACTION: <ONE concrete move to take now — and how it advances the next step and the ultimate goal>
CONFIDENCE: PERFECT | HIGH | MEDIUM | LOW — <what was verified directly vs inferred/assumed>
RISK: HIGH | MEDIUM | LOW — <what's exposed if this report is wrong; which claims are unproven>
```

The compass is the anti-drift anchor: ULTIMATE GOAL is derived fresh PER
SCENARIO from the spec's Goal section — the end-state of THIS project, not a
generic principle. Frame it at the systems level, from the user's seat (a human
building automation so they never have to give input), through ALL FOUR lenses:
**Delivers** (factory view — the finished result that arrives with zero input),
**Heals** (organism view — failures recover or surface themselves), **Replaces**
(operator view — whose job/attention the system deletes), **Guarantees**
(structure view — what wrongness is impossible by construction). Fill every
lens; a lens that genuinely doesn't apply gets "n/a — <why>", never a silent
skip. Once stated, the block is frozen — if a report's goal block ever differs
from what the user actually asked, that IS the drift they want to catch, so
never quietly reword it toward what was achieved. SUGGESTED ACTION must trace to the NEXT
STEP and the goal; an action whose chain doesn't connect is drift and must not
be suggested. Goal fully reached → next step "none", suggested action
"nothing — goal reached".

Confidence rates verification, not optimism: PERFECT is the 100%-guaranteed
full-autopilot grade — every angle empirically tested (happy AND failure paths,
real inputs at real scale), every claim directly observed, zero pending items,
an independent adversarial check found nothing, AND the autopilot itself was
proven: the deliverable ran (and recovered) end-to-end with no human thought,
no human decision, no human intervention, and no Claude in the loop (the
structural-fix bar — next run, different input, nobody watching, still works);
the evidence clause must name the tests including the unattended-run proof, and
one untested angle drops it to HIGH. HIGH only when every
claim in the report was directly observed this session (but not every angle
adversarially tested); inferred or secondhand claims cap it at MEDIUM;
assumptions cap it at LOW. **Hard cap:** anything pending, waiting, retrying,
or "should work" in the report → Confidence cannot be HIGH (PERFECT
unreachable), and the RISK line must name the unproven part. A bare grade with
no evidence clause is invalid. This is the last-line defense against a spec
session ending on false "all done" confidence.

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

   For a tool meant to run **unattended / on autopilot** (a pipeline, an
   overnight job, anything where no human watches each step), the bar must
   also pin the **failure path**, not just the happy path — most failures
   happen there, so a spec that grades only the happy path grades the wrong
   thing. Add self-healing criteria, each empirically checkable: recovers
   from its *known* failure modes with no human in the loop (the modes come
   from `/error-recon`), checkpoints progress so a restart resumes instead of
   starting over, never blocks on mid-run input, and surfaces failures by
   count rather than hiding them. Sweep the known modes against the
   10-category hostile-scenario seed (canonical RED-TEAM brief in
   `~/.claude/skills/audit/SKILL.md`: mid-op death, check-then-act race,
   half-done re-entry, flapping, two actors, boundaries, time windows,
   recovery-fails, poison pill, lying success) — each load-bearing scenario
   lands in the spec as a RECOVERS-BY line or an ASSUME + PROBE line, and a
   category with no line means it was checked and doesn't apply, not that it
   was skipped. Same propagation as the ladder — any
   executor that reads the spec inherits these — and the same KISS bound: a
   one-shot a human watches doesn't need them. (Planning-time twin of
   `/auto`'s Re-entry-hygiene rule: design how recovery is ordered; don't
   just hope the happy path holds.)
5. **Assumptions & Unknowns** — the ledger of unproven beliefs (P11's
   facts-vs-unknowns split, applied at planning time). One line per thing we
   *believe* but haven't proven ("the API returns UTF-8", "the session stays
   live for 8h", "ffmpeg handles this codec"), each with the CHEAPEST probe
   that would turn it into a fact. `/auto`, when bound to this spec, schedules
   the load-bearing probes as EARLY runbook steps — a wrong assumption dies on
   minute one, not at hour three. An assumption with no probe counts as a
   blank HARD field (quality bar). Skip this section only when the task has no
   real unknowns (KISS) — don't fabricate doubts for a trivial one-shot.

6. **Phases / blueprint** — the **default** for any task beyond a trivial
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
<!-- Happy-path bar AND, for unattended tools, the recovery bar (self-heals known
     failures, checkpoints, no mid-run input, failures reported by count) — known
     failures swept against the 10-category RED-TEAM scenario seed (canonical
     brief in the /audit skill). -->
- <...>

## Assumptions & Unknowns (skip when the task has no real unknowns)
<!-- One line per unproven belief + the CHEAPEST probe that turns it into a fact.
     /auto schedules load-bearing probes as EARLY runbook steps. An assumption
     with no probe = a blank HARD field. -->
- ASSUME: <belief>   PROBE: <cheapest check that proves or disproves it>

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
RECOVERS-BY:       <failure-prone / unattended phases only — failure mode + ORDERED   [HARD when
                   recovery: roll back partial write → re-assert precondition (re-run  applicable]
                   this phase's VERIFY-REQUIRES, not a new check) → invalidate
                   downstream → resume. Proof: after injecting the named failure,
                   the phase still reaches its DONE-WHEN.>

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
- **Design the failure path, not just the happy path.** On a failure-prone or
  unattended phase, add `RECOVERS-BY`: name how it fails and the *ordered*
  recovery — roll back partial work → re-assert the precondition → invalidate
  downstream → resume — the planning-time form of `/auto`'s Re-entry hygiene.
  The happy-path `DONE-WHEN` proves it worked; `RECOVERS-BY` proves it survives
  when it doesn't (proof: inject the named failure, confirm the phase still
  reaches its `DONE-WHEN`). When the phase uses the milestone layer, attach
  `RECOVERS-BY` to whichever milestone can leave partial state. Skip it on
  phases that can't leave partial state behind (KISS).

**Quality bar — a blueprint isn't done until it's airtight.** Do NOT consider
the Phases section complete while any HARD field is blank or hand-wavy (a
`REQUIRES`, `VERIFY-REQUIRES`, or `DONE-WHEN` that isn't concretely checkable,
or a `REQUIRES` with no source tag). On a phase flagged failure-prone or
unattended, a missing or hand-wavy `RECOVERS-BY` trips this bar too
(HARD-when-applicable); on a happy-path phase that can't leave partial state
it's simply absent, and that's fine. A vague field is exactly the gap `/auto`
would improvise into — close it here, at planning time. A HARD check that
cannot say NO — a `VERIFY-REQUIRES` or `DONE-WHEN` that would also pass in the
nearest failure state — is hand-wavy and trips this bar too (discriminating
tests, not confirming tests). For a non-trivial
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
