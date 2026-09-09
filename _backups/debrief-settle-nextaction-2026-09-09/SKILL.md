---
name: debrief
description: Explain whatever was just said, shown, or done in 1-3 plain sentences with zero jargon, for a layman vibe coder — then give a chronological timeline of how things work now. Use when the user types /debrief, or says "dumb it down", "debrief this", "what does this mean", "explain like I'm not technical", "so what actually happens now".
---

# debrief — say it plain, then lay out the order

Answer the user's target (the thing just discussed, pasted, built, or errored) in
**exactly this shape, nothing else**:

## 1. What it means

**1–3 sentences. Maximum.** No jargon. If a technical word is unavoidable, replace it
with an everyday word — do not define it, do not add a parenthetical.

Written for a **vibe coder**: someone who ships real things but does not want the
internals. Say what it *is* and why it matters to them. No hedging, no caveats,
no "it depends".

**If the user has stated or implied a guess** ("is it X?", "I think it's Y", "so
was I right?") — sentence one of this section is the verdict, plain: "You were
right," "That's not it," or "Partially — X held up, Y didn't." This is separate
from the no-jargon rule above it: jargon is about which words you use, this is
about what order you say them in. Don't make the reader sit through part 1 to
find the answer to the thing they actually asked.

## 2. How things work now

A **chronological timeline** of the flow as it stands *after* this change — the
order events actually happen in, start to finish.

**Render it as a numbered timeline grouped into named stages, inside a fenced
code block.** Every step gets a whole number in reading order (1, 2, 3 ...) so the
user can point at "step 8" in chat. Stages are short ALL-CAPS labels with a blank line
before each, so the eye can skip to the part it cares about. The code fence is
required so the alignment survives the terminal.

Shape:

```
SETUP
1.  First thing that happens
2.  What that leads to
3.  And then this
      3.1  one note line, only if the step needs it

THE MIDDLE PART
4.  The step where things fan out                       ← new
5.  Sibling -- happens at the same stage
6.  Sibling -- same stage

WHAT HAPPENS NEXT
7.  Outcome one  → what it does
8.  Outcome two  → what it does
      9.  sub-outcome of 8 → what it does
      10. other sub-outcome of 8 → what it does

ENDINGS
11. How it ends well   → what the user gets
12. How it ends badly  → what the user sees
```

Rules for the timeline:

1. **Number every step, top to bottom.** Whole numbers, in the order the lines appear,
   never restarting inside a stage. The number is a name the user can say back to you.
   Two spaces after a one-digit number, one after a two-digit one, so the text lines up.
2. **Group into 3 to 5 named stages.** A stage label is 1 to 3 plain words in ALL CAPS
   (SETUP, RECORDING, ALARMS, NEXT LANE, ENDINGS). One blank line before each label,
   none after it. Labels describe what the block is *for*, not what it is called in code.
3. **Branches are shown with `→`, not tree lines.** When a step has more than one
   outcome, each outcome is its own numbered line: a short condition, an arrow, then
   what happens. Line the arrows up inside the block. If an outcome itself forks, indent
   its outcomes six spaces under it -- one level of indent at most.
4. **Every step is a complete thought on its own line.** The reader should understand
   the step without the note line.
5. **Notes are numbered off their step: `5.1`, `5.2`.** A note is not a step -- it is
   a fact hanging off one (a measurement, a threshold, a "counts as"). Indent six spaces
   under its step, then `N.1`, two spaces, then plain lowercase text. Never bold, never a
   full sentence with a period. At most two or three notes in the whole timeline, on
   steps that are genuinely surprising.
6. **Mark what changed** with `← new` or `← changed`, right-aligned-ish at the end of the
   step line. Only on steps that this conversation actually created or altered.
7. **Only steps that really exist.** Do not invent stages or steps to fill out a block.
8. **Keep it under about 14 steps.** Longer means the steps are too fine-grained -- merge
   them until it fits. A two-step flow is still one stage with two numbered lines.

## 3. The actual words

**Same answer as part 1, retold using the real names for things.** Two to four
sentences. This is the only place technical words are allowed.

Allowed vocabulary ceiling: **words a person picks up in their first month of
shipping things.** file, folder, function, variable, argument, API, endpoint,
request, error, log, install, package, import, repo, commit, branch, push,
server, database, JSON, environment variable, script, path, config.

Anything past that tier -- idempotent, race condition, mutex, AST, coroutine,
marshalling, monad, side effect, memoization -- gets replaced with plain English,
even in this section. When in doubt, it is too advanced: leave it out.

Say what the parts are actually **called** and, where it matters, say what a thing
is **not** ("it is not a hook") -- the wrong-neighbour correction is often the most
useful line in the whole answer.

Never more than four sentences. Never a bulleted glossary.

## Rules

- **Never exceed 3 sentences** in part 1. This is the whole point of the skill.
- **Part 2 is always the staged numbered timeline.** Never fall back to bullets, a
  box-drawing tree, or an unlabeled flat list, even for a two-step flow.
- **Part 3 stays at the ceiling.** If a word is not in the allowed tier and not a plain
  English word, it does not go in. No exceptions for "but it's the correct term".
- **No glossary.** Part 3 is prose, not a term list. No "deeper dive" section beyond it.
  If they want depth they will run `/explain`.
- **No preamble.** Do not restate the question or say "sure, here's the simple version".
- Keep the user's formatting preferences (headlines, spacing) but stay short.
- If the target is genuinely ambiguous, pick the most recent thing in the conversation
  and explain that. Do not ask a clarifying question — this skill exists to reduce
  friction, not add a turn.
