---
name: prep
description: Interactively plan, prototype, and pentest a new script from scratch. Captures the end goal, breaks it into specifics, asks the user broad preferences, proposes a plain-language structure, interviews the user on risky or high-impact functions, drafts a full plan, pauses for external audit (typically Codex) and iterates on feedback, then builds a first prototype and pentests each part. Use when the user says "let's plan X", "prep a new script", "help me design Y", "plan a project", or wants a collaborative plan + external-audit + build + test loop. Every artifact this skill produces must be smooth, consistent, reliable, self-healing, and optimized for speed.
---

# Prep

A guided, collaborative workflow for creating new scripts from a blank page. Unlike `optimize`, which improves existing code, `prep` starts with nothing but an end goal and walks the user through a disciplined path: clarify → structure → explain in plain terms → interview on risky pieces → plan → external audit loop → prototype → pentest.

## When to Use This Skill

- User wants to plan or design a new script or tool from scratch
- Explicit phrases: "let's plan X", "prep a script for Y", "help me design Z", "plan out a new project"
- User has a fuzzy goal and needs it broken down into specifics before coding
- User wants an external review step (e.g. Codex) built into the workflow

## Core Principle

Every artifact this skill produces — the plan, the prototype, every function — must optimize for five properties, in this priority order:

1. **Smooth** — runs without jank, user-facing steps feel continuous.
2. **Consistent** — same inputs produce same outputs; no hidden state.
3. **Reliable** — handles realistic failure modes without silent data loss.
4. **Self-healing** — on failure, recovers automatically (retry, checkpoint, state restore) rather than requiring manual intervention.
5. **Optimized** — fast and resource-efficient, within the limits set by the first four.

When two properties conflict, preserve the higher-priority one.

## Plain-Language Rule

The user has asked for explanations in extremely simple terms. **Obey this strictly.**

- Short sentences.
- Concrete analogies (compare to physical things the user sees every day).
- Define any technical term the first time it appears, in one plain sentence.
- Never assume background knowledge. If you use a word like "idempotent" or "async", explain it in parentheses the first time.
- No abbreviations without expansion on first use.
- No condescension. Plain ≠ dumbed-down. The user is thinking clearly; they just want no jargon fog.

Example of the tone:

> **Checkpointing** means the script saves its progress every few steps, the way a video game saves after each level. If something crashes, we restart from the last checkpoint instead of from zero.

## Runtime Workflow

Follow these phases in order. Do not skip. Use `AskUserQuestion` for every user-facing decision so choices are explicit.

### Phase 1 — Capture the end goal

Ask the user, in one question, what they want the script to do when it's finished. Keep the question open-ended. Accept the answer as stated; do not guess at details yet.

Examples of good goal statements to probe for:
- "Batch-convert 200 videos to 1080p and upload them to Drive."
- "Scrape three websites every morning and email me a summary."
- "Rename and tag my music library based on audio fingerprints."

If the user's first answer is vague ("I want a script that does video stuff"), ask one follow-up that narrows it: "What's the concrete thing you'd want it to do when you run it once?"

### Phase 2 — Derive the specifics

From the goal, list the concrete sub-tasks the script must do. Each should be one sentence. Present them as a bulleted list and ask the user to confirm, add, or remove items.

Example:

> **Goal:** Batch-convert 200 videos to 1080p and upload to Drive.
>
> **Specifics I think this involves:**
> - Read a folder of source videos.
> - For each video, check if it's already 1080p or needs scaling.
> - Re-encode to 1080p with a known codec.
> - Upload the result to a specific Drive folder.
> - Keep track of which ones have already been done so we don't repeat work.
> - Report failures at the end so you know what to re-run.
>
> Which of these are right? Anything missing? Anything I should drop?

### Phase 3 — Broad preferences (one question per specific)

For each confirmed specific, ask one **broad** preference question. Not implementation details — preferences. Use `AskUserQuestion` with 2–4 options each.

Examples:
- "For the upload step — do you want it to retry on network flakiness, or fail fast and let you handle it?"
- "For tracking already-done files — a simple text log, or a small database file?"
- "For the re-encode — speed-priority (GPU, some quality loss), quality-priority (CPU, slower, better), or whichever is idle?"

Keep each question to one decision. Do not stack.

### Phase 4 — Propose a simple structure

Write a one-page sketch of the script's shape:

- A short **plain-language walkthrough** — 4–8 sentences describing what the script does when it runs, start to finish, like telling a friend.
- A **function list** — 5–15 functions, each with a one-line purpose. Group by stage (setup / main work / cleanup / reporting).
- A **data flow diagram in text** — "A reads X, passes to B, B writes Y, C reads Y and does Z."

Example plain-language walkthrough:

> When you run the script, it first looks at a folder full of videos (like looking in a drawer to count the socks). It writes down which ones it's already done before (in a small notepad file). For each new video, it asks ffmpeg — the tool that handles video — to shrink it to 1080p. When ffmpeg is done, it uploads the result and ticks that video off the notepad. If anything fails, it tries again up to three times. At the end, it tells you which ones worked and which ones didn't.

Ask the user: does the structure match what they pictured? Iterate until yes.

### Phase 5 — Interview on risky functions

A **risky function** is one that affects one or more of these:

- The final output (correctness).
- Speed (bottleneck potential).
- Reliability (likely failure points).
- Data loss (anything that deletes, overwrites, or uploads).

From the function list in Phase 4, mark each function as **risky** or **safe**. For each risky function, run one `AskUserQuestion` block:

- Header: the function name.
- Question: "How should `<function_name>` behave?"
- Describe the function's purpose in one plain sentence.
- 2–4 options, each a concrete behavior choice with tradeoffs named.
- Always include: "I don't know — recommend something."

If the user picks "I don't know", propose a default grounded in the five core properties (smooth / consistent / reliable / self-healing / optimized) and explain the reasoning in plain language.

### Phase 6 — Draft the plan

Write a full plan file at:

```
C:\Users\Shadow\.claude\plans\prep-<goal-slug>.md
```

Sections the plan MUST include:

1. **Goal** — one sentence.
2. **Plain-language summary** — the Phase-4 walkthrough.
3. **Function list** — name, purpose, risky?, agreed behavior.
4. **Data flow** — text diagram.
5. **Self-healing mechanisms** — where retries live, where checkpoints live, how the script recovers from each realistic failure.
6. **Files the script reads/writes** — explicit paths and formats.
7. **Dependencies** — libraries or external tools (ffmpeg, curl, etc.) with versions if they matter.
8. **Open questions** — anything still unresolved, for Codex to weigh in on.

### Phase 7 — Codex audit loop

Tell the user the plan is ready for Codex. Provide the exact text to paste — the full plan file contents, framed by a short instruction block:

```
Please audit this plan for a new script. Evaluate:
1. Does the function list cover the goal, or is anything missing?
2. Are the self-healing mechanisms adequate? Where could the script silently lose data?
3. Are there simpler approaches that meet the same five properties (smooth, consistent, reliable, self-healing, optimized)?
4. Any open questions you can answer?
Return specific, actionable feedback — not just approval.

=== PLAN BEGINS ===
<plan contents here>
=== PLAN ENDS ===
```

When the user returns with Codex's feedback, integrate each item explicitly:

- For each Codex point: restate it, show the user, and ask `AskUserQuestion` with options: "Accept", "Reject (reason)", "Modify (how)".
- Update the plan file with every accepted change, noted with a `> [Codex]` callout so edits are traceable.

Loop until the user says they are satisfied. Do not proceed to Phase 8 without explicit user go-ahead.

### Phase 8 — Build the prototype

Once the plan is approved, build version 1. Rules:

- **One function at a time.** Write, then briefly describe what it does in plain language. Do not dump the whole file at once.
- **Self-healing in every risky function** — bounded retries, checkpoint writes, idempotent operations. Never bare `try/except Exception: pass`.
- **KISS** — follow the same anti-overengineering rules as the `optimize` skill. No class hierarchies for linear flows. No `tenacity` when a 5-line loop works. No CLI framework for ≤ 2 args.
- **Every subprocess and network call gets a retry wrapper.** Every file write gets a "write-to-temp-then-rename" pattern so a crash mid-write can't corrupt the destination.

After each function, ask the user one quick question: "Does this match what you pictured?" (Yes / Tweak / Rewrite). Small corrections early beat large rewrites later.

### Phase 9 — Pentest each part

After the prototype exists, run each part under pressure. The goal: verify it is smooth, consistent, reliable, self-healing, and performant under realistic stress.

For each non-trivial function, run at least these checks:

1. **Happy path** — give it the input it's designed for. Confirm expected output.
2. **Empty / zero input** — empty folder, empty file, zero-length list. Confirm graceful handling (no crash, sensible message).
3. **Wrong-type input** — wrong format, corrupted file, unexpected encoding. Confirm it fails loudly, not silently.
4. **Failure injection** — simulate the realistic failure mode (kill subprocess, disconnect network mid-call, fill disk). Confirm the self-healing path actually fires.
5. **Repeat run (idempotency)** — run the script twice back-to-back. Confirm the second run does nothing new on already-processed items.
6. **Stress** — if the script is a batch job, give it a batch larger than usual. Confirm it doesn't blow memory or temp disk.

Record each check's result in a short pentest log (one line per check). Any failure triggers a fix-and-rerun loop. Do not declare the prototype done while any check fails.

## Interview Template (reuse across phases 3 and 5)

```
AskUserQuestion(
  header: "<short tag or function name>",
  question: "<one specific question>",
  options: [
    { label: "<Option A> (Recommended)", description: "<one-sentence tradeoff>" },
    { label: "<Option B>",                description: "<one-sentence tradeoff>" },
    { label: "I don't know — recommend something", description: "Skill proposes a default grounded in the five core properties and explains why." }
  ]
)
```

## Self-Healing Patterns (reference for Phase 6 and 8)

Use these primitives when writing the plan and the prototype. Prefer simple versions.

- **Bounded retry with jitter** — 3 attempts, `2**n + random()` seconds, retry only on specific exceptions.
- **Atomic write** — write to `path.tmp`, then `os.replace(path.tmp, path)`. Partial writes never corrupt the destination.
- **Checkpoint file** — after each stage, append the item id to `progress.jsonl`. On restart, skip ids already in the file.
- **Idempotent operations** — every stage should be safe to re-run. If output exists and is valid, skip it. If not, produce it.
- **Fail-fast on non-transient errors** — bad codec, missing file, wrong credentials: raise immediately. Only retry truly transient conditions.
- **Health check before heavy work** — ffprobe the input before a 2-hour encode. Ping the upload endpoint before batching.

## Hard NOs

Same list as the `optimize` skill, plus these specific to Phase 8:

- Do not write the whole script in one pass before the user has approved each function.
- Do not skip Phase 7 (Codex audit) because "the plan looks fine to me."
- Do not declare Phase 9 done while any pentest check is failing.
- Do not invent requirements the user did not ask for — if uncertain, ask.

## Final Report (end of Phase 9)

Emit one block at the end:

```
=== Prep Report ===

Goal: <one-sentence goal>

Plan iterations: <N>   (plan → Codex → revise → approve)
Functions built:   <N>
Pentest checks:    <P passed / F failed>

Self-healing hooks in place:
- <list specific retry/checkpoint/atomic-write spots>

Known limitations:
- <anything the user accepted as out-of-scope>

Next steps:
- Suggested first real run: <command>
- Metrics to watch on first run: <e.g. wall time, peak RAM, retry count>
```
