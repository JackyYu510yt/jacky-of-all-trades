---
name: dumb
description: Explain whatever was just said, shown, or done in 1-3 plain sentences with zero jargon, for a layman vibe coder — then give a chronological timeline of how things work now. Use when the user types /dumb, or says "dumb it down", "what does this mean", "explain like I'm not technical", "so what actually happens now".
---

# dumb — say it plain, then lay out the order

Answer the user's target (the thing just discussed, pasted, built, or errored) in
**exactly this shape, nothing else**:

## 1. What it means

**1–3 sentences. Maximum.** No jargon. If a technical word is unavoidable, replace it
with an everyday word — do not define it, do not add a parenthetical.

Written for a **vibe coder**: someone who ships real things but does not want the
internals. Say what it *is* and why it matters to them. No hedging, no caveats,
no "it depends".

## 2. How things work now

A **chronological timeline** of the flow as it stands *after* this change — the
order events actually happen in, start to finish.

**Render it as a Minecraft-style unlock tree inside a fenced code block.**
Not a numbered list, not bullets -- a branching tree. The code fence is required so
the box-drawing characters stay aligned in the terminal.

Shape:

```
[✦] First thing that happens
 └─ [✦] What that leads to
     └─ [✦] And then this
         │      one detail line, only if the step needs it
         └─ [✦] The step where things fan out        ← new
             ├─ [✦] Sibling -- happens at this stage
             ├─ [✦] Sibling -- same stage
             └─ [✦] Sibling -- same stage
                 └─ [✦] The end
```

Rules for the tree:

1. **Each step unlocks the next.** Nest with `└─` to show "this happens because that
   finished". Indent one level per step, three spaces per level.
2. **Things that happen at the same stage are siblings** -- `├─` for all but the last,
   `└─` for the last. This is what makes it a tree instead of a list: use it whenever
   two or more steps belong to the same moment.
3. **Every node is a complete thought on its own line.** The reader should understand
   the step without the detail line.
4. **Detail lines are the exception, not the rule.** At most two or three in the whole
   tree, on steps that are genuinely surprising. Format: a `│` spacer line at the child's
   indent, then six spaces, then plain lowercase text. Never bold, never a full sentence
   with a period.
5. **Mark what changed** with `← new` or `← changed`, right-aligned-ish at the end of the
   node line. Only on steps that this conversation actually created or altered.
6. **Only steps that really exist.** Do not invent stages to fill out the tree.
7. **Keep it under about 12 nodes.** Longer means the steps are too fine-grained -- merge
   them until it fits.

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
- **Part 2 is always the tree.** Never fall back to bullets or a numbered list, even for
  a two-step flow. A short tree is still a tree.
- **Part 3 stays at the ceiling.** If a word is not in the allowed tier and not a plain
  English word, it does not go in. No exceptions for "but it's the correct term".
- **No glossary.** Part 3 is prose, not a term list. No "deeper dive" section beyond it.
  If they want depth they will run `/explain`.
- **No preamble.** Do not restate the question or say "sure, here's the simple version".
- Keep the user's formatting preferences (headlines, spacing) but stay short.
- If the target is genuinely ambiguous, pick the most recent thing in the conversation
  and explain that. Do not ask a clarifying question — this skill exists to reduce
  friction, not add a turn.
