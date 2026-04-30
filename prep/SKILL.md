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

## Autonomous Mode (when /auto invokes /prep, or user opts in)

### When autonomous mode triggers

Activate autonomous mode when ANY of these hold:

```
1. /auto has invoked /prep as a sub-skill (Phase 0 handoff)
2. User says "autonomous prep", "no questions, just plan it",
   "auto-prep", "prep this without asking", or invokes /prep with
   /auto in the same prompt
3. The user's prior /principles → /auto → proceed pattern is
   active in this session
```

### What autonomous mode does to each phase

```
Phase 1 (4-condition intake)
  Normal:  AskUserQuestion for each of goal / workflow / testing /
           success conditions.
  Auto:    Derive all four from the invocation message, recent context,
           and any code or files visible in CWD. Log each derivation
           as a one-liner in the ASSUMPTIONS & FORKS card with the
           reasoning ("Picked X because <signal>; alt to challenge:
           Y"). Continue without asking.

Phase 4 (structure proposal)
  Normal:  Iterate function list with the user until they agree.
  Auto:    Propose the function list once. Write it into the plan.
           Skip the iterate-until-agreement gate.

Phase 5 (risky-function interviews)
  Normal:  AskUserQuestion per risky function with 2-4 options.
  Auto:    For every risky function, auto-pick "I don't know —
           recommend something" and apply the documented default
           (smooth → consistent → reliable → self-healing → optimized
           priority). Document the rationale in field 2 (Reasoning)
           of that function's spec.

Phase 7 (Codex audit)
  Normal:  Pause for the user to run Codex and paste feedback.
  Auto:    Either (a) invoke the `Agent` tool with subagent_type
           "code-reviewer" as a stand-in reviewer, integrate its
           feedback automatically with `> [Auto-review]` callouts,
           or (b) skip if no reviewer agent is configured. Note
           which path was taken in the plan's open-questions card.

Phase 8 (per-function approval)
  Normal:  Ask "does this match what you pictured?" after each
           function clears AUDIT.
  Auto:    Drop that gate. The Red → Green → Real → Audit cycle IS
           the verify; AUDIT pass = function done. Update the BUILD
           STATUS card and move to the next function.
```

### What autonomous mode does NOT skip

These remain mandatory regardless of mode:

- The four condition cards (END GOAL / WORKFLOW / TESTING / SUCCESS) — they're derived, not skipped
- The Red → Green → Real → Audit cycle for every RISKY function
- The P7 guards in Phase 8 (per-function isolation, spec-broadening-stop, style-locks-after-2)
- The BUILD STATUS card live updates
- The FINAL VERDICT card as a P4 block

Autonomous mode skips **gates**, not **rigor**. Every output a normal /prep run would produce, an autonomous /prep run also produces — just without pausing for human input at each gate.

### The "could not derive" exit

If autonomous /prep cannot derive an observable end goal OR a checkable success condition from the invocation + context, it does NOT proceed. It writes a partial plan file containing only the cards it could fill, plus a top card noting:

```
[autonomous prep] Could not derive observable success conditions
from invocation. Need from user: <specific missing piece>.
Plan generation halted; will resume on user input.
```

This mirrors /auto's activation gate. Without observable criteria, "done" is opinion (P2 + P8).


## Phase 1 — Capture the four conditions

P2 (figure out the conditions upfront) requires three condition types nailed down before any work starts. Plus the end goal itself. Four answers, four cards in the plan file.

In **interactive mode**, ask each in turn — one question at a time, `AskUserQuestion` for each so the answer is explicit and traceable.

In **autonomous mode**, derive all four from invocation + context in one pass. Log each derivation in the ASSUMPTIONS & FORKS card. Continue without asking.

**1. End goal — one sentence + concrete shape + out-of-scope.**
- One-sentence statement of what "done" means
- Concrete input/output shape (file paths, formats)
- Explicit out-of-scope list (what is NOT in v1)
- Time horizon (how long unattended)

**2. Workflow conditions — preconditions and handoffs per stage.**
- For each stage of the planned pipeline: what must hold going in, what it hands to the next stage
- The end-state signal that means the whole pipeline ran right (e.g., "every input id has a matching output file AND a line in progress.jsonl")

**3. Testing conditions — how we'll prove it works.**
- The production-reality sentence (Phase 9 Step 2 spec, P1 form): "<scale + concurrency + duration + environment + realistic failure mode>"
- The specific failure injections we'll simulate (kill mid-run, network drop, auth expiry, malformed input)
- What we are explicitly NOT testing in v1

**4. Success conditions — the bar to clear.**
- MUST-hold checklist (blocks v1 from shipping)
- SHOULD-hold checklist (nice to have, not blocking)
- Hard fail signals (signatures that mean a real bug, not noise)

If the user's first answer to any of these is vague, ask ONE narrowing follow-up — never three (P3).

Each answer goes into its own card in Phase 6's plan file. They become the spine the rest of the plan hangs off — every later phase points back at them.

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

Write the plan file in the **current working directory** as a `.txt` file:

```
./prep-<goal-slug>.txt
```

Use the **card-stack format** (Style C). Every section is its own bounded card with `╭── HEADER ───╮ ... ╰────╯` borders. The title card uses `┌── ──┐` borders. One blank line between cards.

**Card order — keep it exactly this:**

1. **Title card** — name + one-line goal
2. **TL;DR** — bolded headline + ≤20-word active-voice clarifier (P2 mandate)
3. **END GOAL** — one-sentence goal, concrete shape (input/output/side-files/run command), out-of-scope list, time horizon
4. **ASSUMPTIONS & FORKS** — silent defaults the plan is making, each with: pick / why / tradeoff / alt-to-challenge (P6)
5. **WORKFLOW CONDITIONS** — per-stage preconditions and handoffs, plus the end-state signal (P2)
6. **TESTING CONDITIONS** — Phase 9 production-reality sentence + specific failure injections + explicit NOT-testing list (P1)
7. **SUCCESS CONDITIONS** — MUST-hold checklist, SHOULD-hold checklist, hard-fail signals
8. **Plain-language walkthrough** — the Phase-4 friend-explanation
9. **Function list** — name, purpose, risky?, agreed behavior
10. **Data flow** — text diagram
11. **Self-healing mechanisms** — where retries / checkpoints / atomic writes live
12. **Files the script reads/writes** — explicit paths and formats
13. **Dependencies** — libraries and external tools, versions if they matter
14. **Open questions** — for Codex to weigh in on
15. **Per-function specs** — Phase 7.5 16-field cards appended below, one per RISKY function
16. **BUILD STATUS** — progress tracker, updated by Phase 8 after each cycle phase clears (see format below)

Cards 1–7 lock in WHAT we're building before any function-level design appears. Every later phase (function specs, build cycles, pentest checks) points back at these front-matter cards. Card 16 lets the user (and Phase 8 itself) see exactly where the build is at any moment — and lets a resumed Phase 8 pick up where it left off.

### BUILD STATUS card format

Phase 6 emits this card with all phases unchecked. Phase 8 updates it after each cycle phase (RED / GREEN / REAL / AUDIT) clears.

```
╭─ BUILD STATUS ──────────────────────────────────────────────╮
│                                                              │
│  Mode:      NORMAL | DIAGNOSING | ROTATING                  │
│                                                              │
│  Progress per function — columns [R][G][L][A] =              │
│    Red, Green, reaL, Audit                                   │
│  (SAFE rows show only [G][A]; RISKY rows show all four)      │
│                                                              │
│    [ ] [ ] [ ] [ ]   <function_1>            (RISKY/SAFE)    │
│    [ ] [ ] [ ] [ ]   <function_2>            (RISKY/SAFE)    │
│    [ ] [ ] [ ] [ ]   <function_3>            (RISKY/SAFE)    │
│    ...                                                       │
│                                                              │
│  Current function:                <name or "—" if not started>│
│  Approaches tried (this cycle):   0                          │
│  Sibling notes (carried forward): []                         │
│                                                              │
╰──────────────────────────────────────────────────────────────╯
```

A function is **complete** when every visible column is `[x]`. The build is shippable when every function row is fully checked AND Phase 9 integration checks have all cleared (see FINAL VERDICT card).

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

**The 16 Fields** (in this order, every time)

```
 0. Traces to goal           One sentence: how this function
                             moves the pipeline toward the
                             END GOAL card. If you can't draw
                             that line, the function is drift —
                             cut it (P3).

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

13. Test specs (4 sub)       The Phase 8 build cycle, pre-written:

                             RED:    The failing-first test.
                                     Spec the input state, the
                                     call, and the expected
                                     failure signature. Must be
                                     specific enough to fail
                                     before the function exists.

                             GREEN:  The minimum behavior the
                                     function must show to pass
                                     the RED test. Plus one
                                     positive case (the happy
                                     path).

                             REAL:   How this function will be
                                     tested in production-shape
                                     (chained with neighbors,
                                     real inputs, real I/O).
                                     Pulls directly from the
                                     TESTING CONDITIONS card.

                             AUDIT:  The one-sentence criterion
                                     that means this function
                                     traces to the END GOAL and
                                     can clear the cycle. Pulls
                                     from field 0.

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

Append the 16-field block to the plan file. Phase 7.5 ends when every risky function has a completed spec.


### Phase 8 — Build the prototype

Build one function at a time. Each function goes through a tiered cycle keyed off its Phase 5 risk tag.

**RISKY function — full Red → Green → Real → Audit cycle**

```
RED      Write the test FIRST. Run it. Watch it fail.
         The failing-first run proves the test actually
         exercises the target — without it you can't tell
         a real test from a label (P1).

GREEN    Write the function. Run the test. Watch it pass.
         Then add one positive case (happy path) and run
         that too. Function-then-test makes it too easy to
         tailor the test to whatever the function happens
         to do — this ordering blocks that.

REAL     Run the function in production-shape — the
         conditions named in the TESTING CONDITIONS card.
         Real inputs, real I/O, chained with neighbor
         functions. Catches "passes alone, breaks in
         pipeline."

AUDIT    P4 checkpoint vs the END GOAL card. One sentence:
         "this function moves us from <prior state> to
         <next state>; here's the observable evidence."
         If the line doesn't draw to the goal, the function
         is drift — revert and rethink before moving on (P3).
```

**SAFE function — Green + smoke check.** No separate failing-first test for trivial functions (e.g., reading a text file into a list). Write it, run it, confirm output shape. One-line log in the plan file.

**P7 guards on every cycle (RISKY and SAFE alike).**

```
Per-function isolation     Each cycle touches ONE function.
                           Edits outside that function are
                           not allowed during the cycle. If a
                           sibling function needs work, MENTION
                           it in the AUDIT card — do not fix
                           inline (P7).

Spec-broadening requires   If a cycle reveals the function's
a stop                     Phase 7.5 spec is wrong or
                           incomplete, halt. Renegotiate the
                           spec card with the user. Do not
                           silently broaden the function beyond
                           its agreed spec.

Style locks after          The first two built functions set
function 2                 the file's style — naming, error
                           handling, logging shape, return
                           semantics. Every later function
                           matches. AUDIT explicitly checks for
                           style match. No "I'd write it
                           better" past function 2.
```

**Sibling notes field on AUDIT.** Every AUDIT card includes a "Sibling notes" line — anything noticed about other functions during this cycle, not fixed. Each note becomes a candidate for a dedicated cycle the user can open later.

**Other rules that still apply:**

- Self-healing in every risky function — bounded retries, checkpoint writes, idempotent operations. Never bare `try/except Exception: pass`.
- KISS (P5) — no class hierarchies for linear flows, no `tenacity` when a 5-line loop works, no CLI framework for ≤ 2 args.
- Every subprocess and network call gets a retry wrapper. Every file write uses write-to-temp-then-rename.

After each function clears AUDIT, ask the user one quick question: "Does this match what you pictured?" (Yes / Tweak / Rewrite). The user is reviewing a proven function, not a hopeful one.

### Updating the BUILD STATUS card

Phase 8 keeps the BUILD STATUS card (Phase 6 card 16) live. Update it after every cycle phase clears AND when mode changes:

- After RED clears for a function → check the `[R]` column
- After GREEN clears → check `[G]`
- After REAL clears → check `[L]`
- After AUDIT clears → check `[A]`, set Current function to next, reset Approaches counter
- On entering DIAGNOSING / ROTATING (verify failed, picking new approach) → update Mode
- On returning to NORMAL after a successful rotation → set Mode back to NORMAL
- On adding a sibling note from an AUDIT card → append to the Sibling notes list

This is what makes Phase 8 resumable: if the build is interrupted, the next run reads the BUILD STATUS card, finds the first function with un-checked phases, and resumes from there.

The BUILD STATUS card is also the file `/auto` reads when running on top of `/prep` to know where to pick up the build runbook.

### Phase 9 — Pentest the integrated system

By the time Phase 9 starts, every RISKY function has already cleared its own Red → Green → Real → Audit cycle in Phase 8. Per-function correctness is proven. Phase 9 proves the functions **compose** — that the integrated system survives the production-shape conditions named in the TESTING CONDITIONS card.

Phase 9 has one job: source its checks directly from the TESTING CONDITIONS card. Nothing here is invented fresh — if a check isn't in that card, it doesn't run. This keeps Phase 9 from drifting into "tests I felt like writing."

**The integration + scale + failure-injection check list.**

```
Pull each item from the TESTING CONDITIONS card and run it:

[ ] Production-shape sentence test
       The full pipeline at the scale and duration the card
       names (e.g., "200 prompts, single Chrome profile,
       8-hour wall clock, home network").

[ ] Each named failure injection
       Kill mid-run → resume from progress.jsonl
       Network drop → retry succeeds
       Auth expiry → recovery fires
       Malformed input → logs error, continues
       (Each one a separate run. Pass/fail per row.)

[ ] End-state signal from the WORKFLOW CONDITIONS card
       The thing that means "the whole pipeline ran right"
       holds at the end of the production-shape run.

[ ] MUST-hold checklist from the SUCCESS CONDITIONS card
       Each item passes or fails explicitly.
```

**No standalone Step 1 PoC layer.** It's been folded into Phase 8's per-function REAL step. The historical Step 1 / Step 2 split existed for skills that don't have a per-function build cycle — `prep` does, so Phase 9 is integration-only.

**Verdict block — formatted as a P4 card (see Final Report below).**

A prototype is not shippable while any MUST-hold or end-state check is red, regardless of how many SHOULD-hold items pass.

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

P4 verdict-format. One of DONE / PARTIAL / BLOCKED / UNCLEAR. Append as a card to the bottom of `./prep-<slug>.txt` and print to the user.

```
╭─ FINAL VERDICT ─────────────────────────────────────────────╮
│                                                              │
│  **<✅/🟡/🔴/❓> <STATE> — <one-line headline contrasting    │
│  current state with the END GOAL>.**                         │
│                                                              │
│  Done:                                                       │
│  • <observable artifact / state>                             │
│  • <observable artifact / state>                             │
│  • Plan iterations: <N>  (plan → Codex → revise → approve)   │
│  • Functions built: <N>                                      │
│  • Self-healing hooks: <retry/checkpoint/atomic-write spots> │
│                                                              │
│  Pending / Blocker / Ambiguity:                              │
│  • <each MUST-hold or end-state check that didn't clear,     │
│    or each Codex point not yet integrated>                   │
│  • Permanent changes installed: <change + exact removal>     │
│    (omit if none installed)                                  │
│  • Known limitations: <out-of-scope items the user accepted> │
│                                                              │
│  Next: <one concrete action — first real run command, OR     │
│         what would unblock, OR the info needed to resolve    │
│         the ambiguity. Not "let me know if you want more."   │
│         Include metrics to watch on first run when DONE.>    │
│                                                              │
╰──────────────────────────────────────────────────────────────╯
```

The headline contrasts current state with the END GOAL card, not with a sub-step. SHIPPABLE / NOT SHIPPABLE is implied by the state — DONE means shippable, anything else means not.
