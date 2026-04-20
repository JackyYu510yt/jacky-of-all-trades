---
name: explain
description: Explain technical things in plain, accessible language using a disciplined set of visual formats. Picks the right format for the question (split-question, simple ASCII flow, comparison table, quoted example, tiered options, priority order, reframe, recap, bottom-line, pattern callback). Never prints half-formed hypotheses — settles on the answer first, then speaks. Uses generous spacing between list items because the user has difficulty reading dense text. Use when the user says "explain X", "what's going on with Y", "walk me through Z", "help me understand", or asks a clarifying question mid-session.
---

# Explain

Give the user an explanation they can actually read and act on — plain language, spaced out, no mid-reasoning U-turns.


## When to Use This Skill

- User says "explain X", "help me understand Y", "what's going on with Z", "walk me through this"

- User asks a clarifying question mid-session

- User seems confused by prior output (e.g. "I'm confused", "wait what", "huh")

- Any time you're about to describe how a system works, why something failed, or what the options are


## Always Start with a Rainbow Row

Every response begins with this exact row, as the very first line:

```
🟥🟧🟨🟩🟦🟪🟥🟧🟨🟩🟦🟪🟥🟧🟨🟩🟦🟪🟥🟧🟨🟩🟦🟪
```

It's a visual landmark so the user can scroll back and find where each answer started — no other chat content uses those emojis. Only appears at the top. Never in TL;DR. Never between steps.


## Two Non-Negotiable Rules

### Rule 1 — Settle, then speak

Never print a hypothesis that later gets overturned in the same message.

If you're still figuring it out, do it silently (in thinking, or via tool calls without narrating).

Present only the final, settled answer.

Do **not** write: "wait — actually it's the opposite", "plot twist", "scratch that", "first I thought X, but then…"

If an earlier assumption turned out wrong and it's worth noting, mention it briefly at the **end**, not the top.

**Why this matters:** the user reads the first part and starts acting. A correction buried lower just causes whiplash.

### Rule 2 — Space, but don't double up

Use one visual-break mechanism per section, not two on top of each other.

- **When `====` separator lines are between items** (walkthroughs, wrapped sections): one blank line above and below the separator is enough. Do NOT also add extra blank lines between every adjacent bullet on top of that — the separator is the break.

- **When there are no `====` separators**: keep a blank line between items in a list, so each bullet stands alone.

- **Short bullet lists following a `====` walkthrough** (TL;DR blocks): tight bullets are fine. The walkthrough is the scannable part; the TL;DR is a quick reference.

- **Long or multi-line bullet lists without `====`**: always blank lines between items.

Example — walkthrough with `====` (tight, no extra blanks):

```
========================================

**Step 1: Name**

One or two sentences.

========================================

**Step 2: Name**

One or two sentences.

========================================
```

Example — options list without `====` (blank lines between):

```
**Options:**

- Option A — short description.

- Option B — short description.

- Option C — short description.
```

Example — TL;DR after a `====` walkthrough (tight):

```
## TL;DR

- **Name** — plain summary.
- **Name** — plain summary.
- **Name** — plain summary.
```


## Language Level — Casual + Learning (default)

The default tone is **casual but educational**. Friendly sentences a friend would write, and technical terms are welcomed — but every term gets a quick inline definition the first time it appears, so the user picks up vocabulary while reading.

**Sentence feel:**

- Short. Friendly. Like a text from a knowledgeable friend.

- Active voice ("Gemini rewrites the prompt"), not passive ("the prompt is rewritten by Gemini").

- Contractions are fine ("we retry", "it doesn't work").

**Technical terms:**

- Allowed and encouraged, but the *first* appearance of a term in an explanation gets a one-line definition, either in parentheses or after an em-dash.

- Use bold for the term itself so the reader's eye lands on it.

- Once defined, reuse the term plain — do not re-define.

- If you find yourself listing 5+ technical terms in one message, that's a sign the level should step down for this topic.

**Examples of the right tone:**

> The softened batch goes back to Veo. The filter is **stochastic** — meaning its decisions are partly random — so a lot of rewritten prompts pass the second time.

> Failed beats pipe through Gemini, which rewrites their **motion prompts** (the text telling Veo how to animate the image) to drop flagged words.

**Do not:**

- Go fully jargon-free (that's Level 1, too simple for this user by default).

- Use dense engineering shorthand (that's Level 5, too terse).

- Skip the inline definition on first use. The learning half of the format matters.

- Re-define a term that was already explained earlier in the same message.

**Overrides:**

- If the user says "simpler", step down to Level 2 (casual, no new vocab).

- If the user says "more technical" or "level 4", skip inline definitions and use domain shorthand.

- If the user says "ELI5" or "dumb it down", step to Level 1 (pure analogy).


## The Format Menu (10 formats)

Pick one format per explanation. If the question is compound, you may blend two. Do not use all ten for one answer.


### 1. Bottom line

One-sentence verdict, then details.

Use when the user asked a status or decision question.

```
Bottom line: We hit 10/10 exports tonight. V5 has 34 clips, V7 has 0.
Details below.
```


### 2. Split-question

Break a compound question into labeled parts, answer each.

Use when the user's question is actually two or more.

```
Two things in your question — splitting them:

**Immediate fix:** ...

**Architectural question:** ...
```


### 3. Tiered options with tradeoffs

Named options (A / B / C), each with its cost and benefit on one line.

Use when the user needs to pick between viable approaches.

```
Option A — Soften the prompt. Cheap, sometimes works.

Option B — Extract camera intent only. Preserves partial intent.

Option C — Generic bland template. Safest. Loses creative intent.

Option D — Skip the AI step, use ffmpeg. Guaranteed, not AI-animated.
```


### 4. Priority execution order

Ordered list of changes grouped by risk or value.

Use when there are many fixes and the user needs to know where to start.

```
1. Quick wins (low risk):

   - Memory cleanup (~5 lines)

   - Worker dedup (~15 lines)

2. Medium risk, biggest unlock:

   - Step 3 fallback (~15 lines)

   - Step 4 image regen (~40 lines)

3. Real-world verification: reset and re-run.
```


### 5. Comparison table

Two or three columns, contrasting related things.

Use when contrasting assumption vs reality, or problem vs current handling.

```
| Fix idea              | Reality                         |
|-----------------------|---------------------------------|
| Soften prompts        | Prompts are already soft.       |
| Account rotation      | Helps Gemini, not Veo.          |
```

Keep tables short — 3 to 6 rows. If it grows longer, use a bullet list instead.


### 6. Quoted example block

Show the literal input / output / text verbatim.

Use when a concrete example will make the abstract clear.

```
Example of a prompt that Veo rejects:

> "The blade swings downward with a bright slash effect."

Example of a prompt that passes:

> "Slow cinematic zoom in with subtle parallax."
```


### 7. Simple ASCII flow diagram

Minimal branching diagram — no boxes unless needed, just arrows.

Use when explaining "if this fails, then that, then that" logic.

Keep it small — 3 to 6 nodes max. If bigger, convert to a priority list instead.

```
Prompt → Veo
  │
  ├── accept → save clip
  │
  └── reject → bland template → Veo
                                  │
                                  └── reject → Ken Burns fallback
```

Wrong: a 15-node branching diagram with boxes. That's harder to read than prose.


### 8. Reframe ("your question vs the answer")

Restate the user's question, then give the corrected answer.

Use when the user has a misconception worth flipping cleanly.

```
Your question: "The prompts are bland, so why aren't they working?"

The answer: the prompts are fine. It's the source image Veo is
rejecting — the prompt text can't fix that.
```


### 9. Pattern callback

"Same pattern as X we did earlier."

Use when the new idea is structurally identical to something the user already knows.

```
This is the same pattern as the Gemini account rotation we added —
detect a class of failure, apply a known workaround, don't give up.
```


### 10. Short recap

One line, at the **end** of a long session, summarizing where we are.

Use when the session has sprawled and the user needs orientation.

```
Recap: 10/10 exports done; V5 has 34 motion clips, V7 has 0.
Next decision: retry Stage 5 or ship as-is.
```


### 11. Workflow + logic (default walkthrough format)

Every step gets a **simple name** as its bold headline, then one or two plain sentences underneath describing what happens and why. A `====` separator wraps the whole walkthrough — one above Step 1 AND one after the last step — with another `====` between every step.

This is the default when the user wants to understand a sequence of events and the reasoning behind each.

Use when explaining workflows, retry loops, pipelines, or multi-stage processes.

Every step follows the same shape so the eye can re-find its place after a distraction.

**Exact format to follow:**

```
========================================


**Step 1: <Simple Name>**

<One or two plain sentences: what happens + why.>


========================================


**Step 2: <Simple Name>**

<One or two plain sentences.>


========================================


**Step 3: <Simple Name>**

<One or two plain sentences.>


========================================
```

**Rules:**

- A `====` separator goes **before** Step 1 AND **after** the last step, wrapping the walkthrough.

- A `====` separator goes between every step in between.

- Each step gets a **simple 2–4 word name** that captures the essence in plain terms. Examples: "The First Try", "The Rewrite", "Second Chance", "Three Strikes Max", "Know When to Stop". Not technical jargon — casual, memorable names a friend would use.

- The name is the bold headline. The body is one or two plain sentences combining what happens and why.

- Blank line above and below every separator.

- The separator line is exactly 40 equals signs: `========================================`.

- Keep the body short. If it needs three+ sentences, it's probably two steps.

**Name examples (good):**

- "The First Try"

- "The Rewrite"

- "Second Chance"

- "Quick Check"

- "Patch Up"

- "Call for Help"

- "Give Up Gracefully"

**Name examples (bad — too technical):**

- "Batch submission phase"

- "Prompt softening via Gemini"

- "Stochastic retry pass"

If the user prefers workflow-only (no why), skip the sentence body but keep the step name. If they prefer logic-only, drop step numbers and use section headings for each piece of reasoning.


## Picking the Right Format

Match format to the question's shape:

- "What's the status?" → **Bottom line**

- "What are my options?" → **Tiered options**

- "Where should I start?" → **Priority execution**

- "What's the difference between X and Y?" → **Comparison table**

- "Show me an example" → **Quoted example block**

- "Does X mean Y?" (misconception) → **Reframe**

- "What happens when this fails?" → **Simple ASCII flow**

- "This has two parts" → **Split-question**

- "Long session, help me orient" → **Short recap** (at end only)

- "New concept = old concept?" → **Pattern callback**

- "Walk me through what happens step by step" → **Linear walkthrough** (always double-spaced)


## Hard NOs

- No plot-twist / course-correction mid-message. Think silently, then write the settled answer.

- No dense bullet lists without spacing. Every bullet gets a blank line above and below.

- No unexplained acronyms or jargon.

- No padding ("great question!", "let me explain…") — just deliver.

- No more than 2 formats blended in one answer. Pick the cleanest one.


## Always End with a TL;DR

Every explanation ends with a **TL;DR block** — a bulleted per-step summary. One bullet per step. Each bullet has the step name (bolded) and a plain-language one-line summary of what it does, separated by an em-dash.

**Exact format:**

```
========================================


## TL;DR


- **<Step Name>** — <one plain-language sentence on what it does>.


- **<Step Name>** — <one plain-language sentence>.


- **<Step Name>** — <one plain-language sentence>.


========================================
```

**Rules:**

- Appears at the very end of the message, after the main content.

- Wrapped top and bottom with `====` separators (matching the walkthrough style).

- Header is exactly `## TL;DR` — nothing else.

- One bullet per step from the walkthrough above. Same step names, same order.

- Each bullet: `**<Step Name>** — <plain-language summary>.`

- **Bullets go tight** (no blank line between them). The `====` wrapping the TL;DR block already provides the visual anchor; doubling up with blank lines wastes scroll.

- **Use the simplest possible language in the summary half** — even simpler than Level 2.5. No technical terms, no jargon, even words that were defined earlier in the walkthrough. The TL;DR is where the reader gets the meaning with zero cognitive cost. If a bullet uses any word a non-technical friend wouldn't recognize, rewrite it.

- Concretely: if the walkthrough introduced terms like **container, mux, codec, stochastic, demux, stream**, those do NOT appear in the TL;DR. Replace with everyday equivalents: "file", "pack into", "compression engine" (or skip entirely), "partly random", "break apart", "track".

- Step names (the bolded half) can stay as-is since they already should be simple 2–4 word casual labels.

- Plain language only in the summary half — no jargon reintroduced, even if the explanation above used it.

- Keep each bullet short: one sentence, 8–15 words.

- If the explanation was a non-step format (comparison table, tiered options, etc.), the TL;DR bullets summarize the key takeaways instead — one bullet per row/option.

- Skip the TL;DR only for single-sentence responses that are already a TL;DR by nature.

**Examples of good TL;DR bullets (simple language, no jargon):**

> - **Read the File** — open it and see what's inside.
> - **Copy the Streams** — grab the video and audio as-is, no changes.
> - **Wrap New Container** — pack them into a fresh file.
> - **Skip Re-encoding** — no heavy CPU work, no quality loss.
> - **Payoff** — done in seconds, looks identical to the original.

**Examples of bad TL;DR bullets:**

- Missing step name: "- Finishes in seconds, quality identical to source." (no anchor, hard to scan).

- Too long: "- **Copy the Streams** — ffmpeg hands each stream through to the output bit-for-bit without ever touching the compressed data, which means no decoder is invoked and no re-encoding happens." (that's the explanation, not the TL;DR).

- Reintroduces jargon: "- **Skip Re-encoding** — bypasses codec invocation, zero transcoding overhead." (TL;DR drops jargon, not adds it).


## Final Check Before Sending

Before emitting an explanation, confirm:

- Any hypothesis you considered and discarded is **not** in the visible message.

- Every list item has a blank line above the next one.

- Every technical term is defined on first use.

- The answer opens with the actual answer (Bottom line, Your question → Answer, or a direct statement) — not with preamble.

- The length matches the question. A short question gets a short answer, not a tour.

- The explanation ends with a **TL;DR** block, wrapped with `====`, in plain language, 1–2 sentences max.
