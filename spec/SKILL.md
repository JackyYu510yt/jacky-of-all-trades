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
4. **Success criteria** — the bar to clear.

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

---

## Change Log
<!-- Newest first. One structured block per real change. -->
```

Tell the user it's created and that changes are now tracked.

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
