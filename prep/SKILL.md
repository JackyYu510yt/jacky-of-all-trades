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


## Interaction Protocol

The guiding stance for this skill: **I drive. You steer. You only steer when it actually matters.**

Every yes/no comes with the story baked in. No menus for the user to pick from. No commands for the user to paste. No gates for busywork. One gate per real decision — and the gate always arrives with "here's what, here's why, here's the risk."


### The Four-Field Offer Block

Every decision point prints this shape:

```
TL;DR:   [1–2 lines — what's going on + why this step]

Risk:    [LOW / MEDIUM / HIGH + one-line reason]

Mode:    [STEP-BY-STEP / AUTONOMOUS]   (omit for LOW defaults)

Next:    [one action in plain language]

Proceed?
```

- **TL;DR** is the story before the button. The user never sees "Proceed?" without first knowing what's happening and why.

- **Risk** sets the stakes explicitly.

- **Mode** sets expectations about who drives the next stretch.

- **Next** is one concrete action, not a menu.

- **Proceed?** is a yes/no gate.


### Risk Tiers

```
LOW      Read-only or trivially reversible. No state changes,
         or the change undoes itself on restart.

MEDIUM   System state changes, but reversible. May need a reboot.
         No data loss path.

HIGH     Destructive, irreversible, or affects shared state.
         Data loss possible, running work can be lost, or another
         user/process is affected.
```

**Behavior by tier:**

- **LOW** → may auto-proceed under a standing "yes" from the user; still print the block so a veto is possible.

- **MEDIUM** → always gates. Always show the rollback path in the Risk line.

- **HIGH** → always gates. Both-sides consequences spelled out (what's lost on yes, what's lost on no). Never bundled with other actions.


### Default to Action, Not Menu

Pick the obvious next move and state it in one line. Only show a menu when there are **genuinely competing directions** the user needs to choose between — and include a confident lean.

Bundle safe read-only checks under a single Proceed — don't fragment into five questions.


### Offers, Not Commands

Closing questions are offers to act, not commands for the user to execute.

Pattern: *"It seems like [hypothesis]. Do you want me to [action] to check?"*

- Never hand the user a command to run when the skill can run it.

- Every offer names a hypothesis + a specific action + the evidence it will produce.

- The user remains the decider. The skill remains the hands.


### Closing Question Must Unblock the Next Step

End-of-phase questions must pass this test:

> *Does answering this question advance the plan, or does it just inform me?*

If it only informs, save it for a post-mortem. The closing prompt's job is to keep the work moving, never to poll preferences or ask the user to recall something from memory.


### Autonomous Mode

When all remaining steps are LOW or MEDIUM and fully reversible, offer a single four-field gate whose `Next` lists the entire chain. Mark `Mode: AUTONOMOUS` — one "proceed" authorizes the whole chain.

**Auto-offer criteria** (all must hold):

- All steps LOW or MEDIUM risk
- Every step reversible without data loss
- Fix is well-understood (no "try this and see")
- No HIGH-risk step anywhere in the chain
- User has given at least one prior proceed in this session

**User-invoked phrases** (skip the auto-offer, go straight to one authorization gate):

- "run it autonomously"
- "autonomous mode"
- "just do it"
- "don't ask me again this session"

**Execution tools:** shell (run commands, elevate where needed), monitor (poll logs/processes for completion), session cron (one-shot scheduled tasks that self-delete).

**Tripwires that drop back to step-by-step:**

- Step turns out to be HIGH-risk

- Step fails mid-chain

- Shell output contradicts the plan

- Monitor times out

- External dependency needed (credential rot, manual service start)

- Step wants to install permanent state (see below)

Always print a recap at the end.


### Session Cron vs Permanent Cron

```
SESSION CRON     Lives only for the current plan/build session.
                 Used for: poll a log, schedule a one-shot action,
                 wake up and verify. Self-removes when the task
                 fires OR the session ends. No lasting footprint.
                 Safe inside autonomous mode.

PERMANENT CRON   Part of the actual fix/plan output. Runs forever
                 until removed. Creates lasting system state. NOT
                 safe to bundle silently into autonomous mode.
                 Always its own four-field gate, even inside an
                 autonomous chain. Listed in the final recap with
                 exact removal instructions.
```

Same rule applies to any permanent system state: scheduled tasks, registry keys, startup entries, services, firewall rules, env vars in user/system scope, pagefile changes.


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

Loop until the user says they are satisfied. Do not proceed to Phase 7.5 without explicit user go-ahead.


### Phase 7.5 — Per-Function Audit Spec

For every function flagged as **risky** in Phase 5, produce a full audit-grade specification using the 15-field template below. This is the artifact Codex actually audits — every field exists to give the reviewer something specific to engage with, not rubber-stamp.

Safe functions get a one-line summary. Only risky ones get the full spec.

**The 15 Fields** (in this order, every time)

```
 1. Logic                    What it does, 2–4 plain sentences.

 2. Reasoning                Why THIS approach, not the obvious
                             generic one.

 3. Alternatives considered  2–3 rejected approaches, each with
                             the one-line reason. Critical for
                             audit — lets the reviewer challenge
                             the rejection, not rubber-stamp the
                             winner.

 4. Scenario fit             The SPECIFIC project constraints
                             that shaped this choice. Long jobs?
                             Large files? GPU-bound? Rate limits?
                             Generic textbook answers die here.

 5. Pipeline integration     Upstream:    who calls, with what
                                          input shape, what
                                          guarantees I rely on.
                             Downstream:  who reads my output,
                                          what shape they expect,
                                          what I guarantee them.
                             Invariants:  what stays true at
                                          every hand-off.

 6. State ownership          Owns (writes) / Reads only /
                             Never touches. Prevents silent
                             coupling across functions.

 7. Protocols followed       Standard 8-row checklist:
                             [ ] Atomic write
                             [ ] Idempotent
                             [ ] Bounded retry with jitter
                             [ ] Retry only on transient errors
                             [ ] Fail-fast on non-transient
                             [ ] Health check before heavy work
                             [ ] Checkpoint after confirmation
                             [ ] Structured log, no bare prints

 8. Pipelining / concurrency Streaming vs batching, parallelism
                             cap, backpressure, place in the
                             producer/consumer graph.

 9. Failure modes            Table: failure → self-healing path
                             → if that fails, what next.

10. Performance profile      CPU / IO / net bound? Cost per
                             item? Where the bottleneck lives?
                             What would make it 10x slower?

11. Observability hook       What it logs (fields). ONE metric
                             to watch on the first real run.

12. Rollback plan            If this misbehaves mid-batch, how
                             to undo. What state needs cleanup.

13. Test technique           PoC: one clean check.
                             Usecase: matches how prod runs.
                             (See Phase 9 pentest rules.)

14. KISS check               What I deliberately did NOT add,
                             and why a future reader might be
                             tempted to add it anyway.

15. Open questions (Codex)   Explicit prompts for audit: "I'm
                             not sure about X — can you
                             challenge it?" Makes the review
                             targeted, not hunt-and-peck.
```

**Header format**

Each function's spec begins with:

```
================================================================
FUNCTION:  <signature>
PIPELINE:  stage <N> of <M> — <one-line position>
================================================================
```

Append the 15-field block to the plan file. Phase 7.5 ends when every risky function has a completed spec.


### Phase 8 — Build the prototype

Once the plan is approved, build version 1. Rules:

- **One function at a time.** Write, then briefly describe what it does in plain language. Do not dump the whole file at once.
- **Self-healing in every risky function** — bounded retries, checkpoint writes, idempotent operations. Never bare `try/except Exception: pass`.
- **KISS** — follow the same anti-overengineering rules as the `optimize` skill. No class hierarchies for linear flows. No `tenacity` when a 5-line loop works. No CLI framework for ≤ 2 args.
- **Every subprocess and network call gets a retry wrapper.** Every file write gets a "write-to-temp-then-rename" pattern so a crash mid-write can't corrupt the destination.

After each function, ask the user one quick question: "Does this match what you pictured?" (Yes / Tweak / Rewrite). Small corrections early beat large rewrites later.

### Phase 9 — Pentest each part

Two steps. Both required. Neither alone is sufficient.


**Step 1 — Proof of Concept**

One clean test per primitive. Minimum sufficient proof that the concept works at all.

- Single happy-path run per function.

- Pass → concept is valid, move on.

- Fail → stop. Fix the primitive before touching anything else.

Default is **one** PoC test per function. Expand to more than one ONLY if:

- The function has **multiple distinct code paths that must each fire** (e.g. three fallback strategies — one test per strategy).

- The function has a **specifically known-fragile axis** (e.g. window-size extremes known to break). One PoC at the fragile boundary, one at the normal case.

Each expansion must be named with a reason. No combinatorial explosion.


**Step 2 — Actual Usecase**

The code running the way production will run it. Composition, concurrency, and scale intact — not a tidier abstraction of it.

Before writing any Step 2 test, answer this in one sentence:

> *"How will this actually run in production?"*

That sentence IS the Step 2 test spec. Then simulate **exactly that**.

Examples:

- *"3–5 Chrome profiles running concurrently, hitting CF at overlapping times, sharing one mouse and one foreground window."* → Step 2 = launch 3 profiles at once and verify no race.

- *"200 videos, home uplink, user asleep, 8-hour wall clock."* → Step 2 = scale run on real inputs, not a 3-item smoke test.

- *"Overnight unattended during a 6-hour render."* → Step 2 = verify the fix doesn't interfere with a running render.


**Verdict block**

Print both layers explicitly. PoC-only results are never declared shippable.

```
===========================================================
PENTEST

Step 1 — PoC
  [x] <check>                 result

Step 2 — Actual usecase
  Prod is: <one-sentence spec>
  [x/⚠/✗] <check>            result

Verdict: SHIPPABLE / NOT SHIPPABLE
===========================================================
```

A prototype is not shippable while Step 2 is red, regardless of Step 1 status.

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
Pentest verdict:   SHIPPABLE / NOT SHIPPABLE
  Step 1 (PoC):     <P passed / F failed>
  Step 2 (Usecase): <P passed / F failed>

Self-healing hooks in place:
- <list specific retry/checkpoint/atomic-write spots>

Permanent changes installed (survive reboot):
- <change>
  Remove: <exact command or click-path>
(Omit section if none installed.)

Known limitations:
- <anything the user accepted as out-of-scope>

Next steps:
- Suggested first real run: <command>
- Metrics to watch on first run: <e.g. wall time, peak RAM, retry count>
```
