---
name: options
description: Display a decision as a clean, goal-aware picker — lay the choices out with plain one-line explanations, and mark one "(Recommended)" only when the user's stated goal clearly points to it. Use when the user faces a fork and wants the options shown so they can pick: "show me my options", "lay out the choices", "help me decide between X and Y", "what are my options for Z", "weigh these against my goal", or any moment a decision should be displayed clearly instead of argued in prose. It is a display tool, not a planner — it shows, weighs, and recommends; the user always picks. Standalone — not wired into /prep, /spec, or /auto.
---

# options — show a decision, goal-aware

## What this skill does

One job: take a decision and **show it so it's easy to pick.**

Given a question, 2–4 choices, and (if known) the user's **end goal**, it renders the choices
with plain, jargon-free descriptions and marks **one** `(Recommended)` — but only when the goal
genuinely points to it. When the goal can't decide, it says so honestly instead of faking a pick.

It is the *dashboard*, not the *plumbing*. It displays and recommends. The user decides.

## When to use

- The user is at a fork and wants the options laid out: "show me my options", "lay out the
  choices", "help me decide between X and Y", "what are my options here".
- A skill or conversation reaches a real decision point and a clean, goal-aware picker would
  beat a wall of prose.

Do NOT use it to plan, build, or run anything — it only *shows a decision*.

## The display format

Use Claude's built-in picker — the **`AskUserQuestion`** tool. For each decision:

- **Question** — one line.
- **2–4 options.** Each option's label is the loud, clear part. Each description is ONE plain,
  `/explain`-style sentence — no jargon, the everyday word over the technical one.
- **`(Recommended)`** appended to at most ONE option's label — and only when earned (see the
  engine below). Put the recommended option **first** in the list.
- **A "why" line** on the recommended option's description, tracing the pick back to a goal word:
  e.g. `↳ why: your goal said "overnight" — this is the fastest option that still fits.`
- **No clear pick?** Then NO `(Recommended)` tag at all. Instead, the question text names *what
  actually decides it* (the human axis), so the user picks on the right basis.

The built-in picker is always the default surface. Keep descriptions short — the picker's preview
panel clips long text (≤ ~9 lines for any rich preview).

## The recommendation engine

How it decides whether to recommend, and which one. It is not magic — it builds a tiny grid and
reads its shape.

1. **Break the goal into criteria.** Each criterion is one of two kinds:
   - **LIMIT** — a window or ceiling the result must fit inside ("overnight", "under 5 GB",
     "by Friday", "runs on my laptop").
   - **TARGET** — a thing to maximize ("smallest files", "best quality", "fastest", "least setup").
2. **Score every option** against every criterion — fits / fails / better / worse.
3. **Read the shape of the grid** — that shape tells you the flavor, and the flavor tells you the move.

## The four flavors (grid shape → move)

- **GOAL DECIDES** — one option wins every column → recommend it, with the `↳ why` line.
- **SILENT** — no column touches this decision (the goal says nothing about it) → **no
  recommendation**; name the human axis the user should decide on instead.
- **TIE** — several options tie across the goal's columns → break the tie with the universal
  default order **faster → simpler → safer/reversible**, recommend the winner, and label it as
  a tiebreak ("both fit your goal; going with the one that's easier to undo").
- **COMPROMISE** — each option wins some columns and loses others, no clean winner → **no fake
  recommendation**; lay the tradeoff bare and ask which cost is acceptable. This is the pivotal
  fork where the optional rich view (below) earns its keep.

## Hard rules

1. **Constraint vs preference.** A LIMIT is a *filter*, never a vote for the slowest/worst option
   that happens to fit. The logic is two steps: (1) drop options that fail a limit, then (2) among
   the survivors, recommend the one that best serves the TARGETs (faster, frees the machine,
   hands-off, higher quality). Reading "overnight" as "slow is fine, so recommend the slow one"
   is the exact bug this rule forbids — "overnight" is a deadline, and the fastest option that
   still fits wins.
2. **Never fake a recommendation.** `(Recommended)` appears ONLY on a genuine win (GOAL DECIDES)
   or a clean tiebreak (TIE). On SILENT and COMPROMISE there is no tag — a confident-but-wrong
   recommendation is worse than none.
3. **Descriptions are `/explain`-style.** Plain, one sentence, zero jargon. If a technical term is
   unavoidable, define it inline in a few plain words.
4. **Keep the built-in picker as the default.** Its preview panel has a height cap and clips long
   text, so any optional rich view stays short (≤ ~9 lines).

## The optional rich view (pivotal / compromise forks only)

NOT the default. Reserve it for the rare fork where the goal can't decide and the consequences
aren't obvious from the option names (the COMPROMISE flavor). Put it in the option's `preview`
field — short enough not to clip — with up to three layers:

```
✅ the good thing about this option
⚠️ the catch

🎬 THIS RUN
   what happens on this specific job if you pick it (real numbers)

📊 BIG PICTURE
   what it does to the whole operation / end goal — the ripple effect
```

`🎬 THIS RUN` is zoomed in (this job). `📊 BIG PICTURE` is zoomed out (the consequence for
everything around the job). Use only the layers that add something.

## Worked example — the recommendation follows the goal

**Goal: "render reels overnight, hands-off."** Encode options score like this — every option fits
the LIMIT ("overnight"), and the goal names no speed TARGET, so it's a TIE → tiebreak (faster +
frees the machine) recommends GPU:

```
  How should it encode?

  1. GPU (NVENC)  (Recommended)
     ~20 min — easily inside your overnight window, machine free by morning.
     ↳ why: all options fit "overnight", so the tiebreak decides — fastest that fits, frees the machine.

  2. Auto
     Uses the GPU if you have one, else CPU. Same speed with your card, safe fallback without.

  3. CPU (libx264)
     Best quality / smallest files, but ~3 hrs and pins the machine.
```

**Now add "...and keep my storage small."** That adds a TARGET column (small files) that GPU loses
and CPU wins. Each option now wins a column → COMPROMISE → no fake pick; show the tradeoff and ask:
*"speed, or storage?"* Same options, same decision — the grid's shape flipped because the goal grew
a column. That is the whole engine.

## What this skill is NOT

- NOT wired into `/prep`, `/spec`, or `/auto`. Zero integration. It stands alone as a presentation
  style another skill (or the user) can reach for.
- It does not plan, build, run, or save anything. It shows a decision, weighs the options against
  the goal, recommends only when earned, and hands the choice back. The user picks.
