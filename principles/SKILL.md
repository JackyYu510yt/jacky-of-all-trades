---
name: principles
description: Core engineering and collaboration principles the user has codified from past failures. Each principle is a hard-earned rule meant to prevent a specific, real failure mode. Currently covers (1) test-at-scale — tests must exercise the actual target condition, not just set a config value; (2) figure-out-the-conditions-upfront — identify success, testing, and workflow conditions before starting any task; (3) keep-the-end-goal-in-sight — every action and every question must advance the stated goal; don't drift into tangents; don't stop to ask when the answer is already in the plan or prior context; (4) audit-against-the-goal-before-handback — before stopping, run an end-of-task checkpoint comparing current observable state to the end goal, then emit a decision-ready verdict (Result / Toward goal / Next) in one of four states (DONE / PARTIAL / BLOCKED / UNCLEAR); (5) KISS — pick the simplest solution that works; complexity must be justified by a concrete present requirement, not a hypothetical future one; duplication beats the wrong abstraction; rule of three before extracting; (6) think-before-coding — surface assumptions, forks, and tradeoffs *before* the implementation lands; present multiple interpretations rather than silently picking; push back when a simpler approach exists; name confusion instead of guessing; (7) surgical-changes — every changed line traces to the user's request; no drive-by improvements; no style impositions; mention pre-existing dead code instead of deleting it; clean only orphans your own change created. Use when writing or running a test, claiming a value or threshold "works", reporting verification results, making any claim about code behavior, starting a non-trivial task, debugging, running a multi-step pipeline, running /auto or /loop, about to ask a clarifying question, mid-task considering a "while I'm here" detour, stalled by a question the context already answers, about to finish a task and hand output back to the user, designing a new component, refactoring, choosing between an abstraction and duplication, vibe-coding or prototyping, adding a factory/registry/wrapper/decorator/config layer, writing a class hierarchy, picking inheritance vs composition, editing existing code, fixing a bug, completing a focused feature ask, working in code with a style you'd write differently, noticing unrelated dead code or bugs, picking between two valid interpretations of a request, picking silent defaults (timeout, retry, format, library), or about to say "tested" / "verified" / "confirmed" / "worked" / "fixed" / "done" / "should I" / "do you want me to" / "before I start" / "just to confirm" / "quick question" / "let me know if you want more" / "hope this helps" / "are we done?" / "what's next?" / "anything left?" / "in case we need it later" / "for future flexibility" / "to make it extensible" / "best practice" / "while I'm here" / "I also cleaned up" / "I improved" / "I refactored some adjacent code" / "I noticed" / "I'll just assume" / "they probably meant" / "I'll go with the standard". This skill is expected to grow — new principles will be appended over time, each following the template at the bottom.
---

# Principles

A living collection of rules that must be followed across all code work in this user's projects. Each principle comes from a specific real failure it is meant to prevent. Follow them all, not just the ones that feel relevant to the current task.

This file is designed to grow. New principles get appended using the template at the bottom. Every principle has the same structure so the skill stays scannable as it expands.


`========================================`

## Principles Index

1. **Test the condition, not the label** — the test must place the system in the exact condition being verified; setting a value is not the same as exercising it.

2. **Figure out the conditions upfront** — before acting, nail down the success condition, the testing conditions, and the workflow conditions; without them, "done" has no meaning.

3. **Keep the end goal in sight** — understand the goal and what "done" looks like, use the materials and context you were given, and make every action and question traceable back to the goal; don't drift, don't stall, don't do random stuff.

4. **Audit against the goal before handback** — before stopping, run a checkpoint comparing current observable state to the end goal, then emit a decision-ready verdict (Result / Toward goal / Next) in one of four states (DONE / PARTIAL / BLOCKED / UNCLEAR).

5. **KISS — keep it simple** — pick the simplest solution that solves the present requirement; every layer of abstraction, indirection, or "flexibility" needs a concrete reason that exists today, not a hypothetical one. Duplication beats the wrong abstraction. Rule of three before extracting.

6. **Think before coding** — surface assumptions, forks, and tradeoffs *before* the implementation lands; if multiple readings of the request exist, name them; if a simpler approach exists, push back; if confusion is real, name what's unclear instead of guessing.

7. **Surgical changes** — every changed line traces to the user's request; no drive-by improvements, no style impositions, no silent deletion of pre-existing dead code; mention strays, don't fix them; clean up only the orphans your own change creates.

> **Crosswalk to Karpathy's 4 principles:** Think Before Coding → P6 · Simplicity First → P5 · Surgical Changes → P7 · Goal-Driven Execution → P2 + P4.

<!-- Append new entries here as they are added. Keep entries to one line. -->


`========================================`

## Principle 1 — Test the condition, not the label

**Rule:** The test must place the system in the exact condition being verified. Setting a value is not the same as exercising it.

**One-line form:** If the question is "does N work?", fire N. Config-load ≠ load test.

### When it applies

- Any test written or run to answer "does X work?" for a specific value, condition, scale, concurrency, or failure mode.

- After any change that introduces a new constant, threshold, or config value the user asked to be verified.

- Trigger phrases: "test at N", "verify concurrency", "does this work with X", "stress test", "prove it handles Y", "pentest this", "try M threads".

### Failure modes this catches

- **Label vs behavior** — `THREADS = 80` proves the assignment works, not that 80 concurrent threads work.

- **Happy path vs target path** — a 1-item queue never reaches the N-item logic even when N=80 is configured.

- **Convenient proxy vs actual spec** — the test spec comes from the user's question, not from what's easiest to run.

### Three-check gate before declaring "tested"

Answer each in one sentence. If any answer is no, the test did NOT exercise the target — say so.

1. **Did the test actually reach the condition?** If X = "80 concurrent submissions", did 80 requests fire at the same moment? If X = "10 hour wait", did it actually wait 10 hours?

2. **Would the test have failed if the target value were wrong?** A test that passes whether the value is 8, 80, or 8000 isn't testing the value — it's testing that the code path doesn't crash.

3. **Does the test check the specific failure signature the target would produce?** If the API throws `LIMIT_403` when over capacity, did the test grep for it? Or did it just check "no exception"?

### Common invalid patterns

- `MAX_CONCURRENT = 100`, test sends 1 request → invalid

- "Does it retry on error?" test with no induced failure → invalid

- "Does it handle empty input?" test with a small non-empty list → invalid

- "Is it thread-safe?" test with sequential calls → invalid

- "Does this survive N hours?" test that runs for N minutes → invalid (unless the gap is stated explicitly)

- "Does it handle 1000 users?" load test with 10 users → invalid

### When you can't run at full scale

Real cost, destructive side effects, or external dependencies can make the true-scale test impossible. That's okay. What's NOT okay is silently downscaling.

Required:

1. **Say so explicitly** — "I cannot run the true N=1000 test because each request costs $5 / would take 6 hours / would trip the rate limit."

2. **Propose the closest realistic approximation** — "I'll run N=10 against the live system; the failure mode would be the same N thing."

3. **Report the gap in the verdict** — "Tested at M, not the requested N, because [reason]. Extrapolated verdict: …"

### Hard NOs

- Do not report "worked" when the test didn't reach the target condition.

- Do not accept "it ran without error" as proof of the target value.

- Do not substitute a convenient proxy for the user's actual question.

- Do not silently downscale — always name the gap.

- Do not re-use a smoke-test result as load-test evidence.


`========================================`

## Principle 2 — Figure out the conditions upfront

**Rule:** Before acting, figure out the conditions that define the task — what success looks like, what a valid test requires, and what preconditions the workflow needs at each step.

**One-line form:** Define the target before you shoot. "Done" has to mean something specific and observable.

### When it applies

- Starting any non-trivial task — writing a function, debugging a bug, running a pipeline, doing a refactor.

- Before writing or running a test for a specific function.

- Before claiming a bug is fixed, a feature is complete, or a workflow ran correctly.

- Trigger phrases: "test this", "debug this", "is this working?", "fix this", "run this pipeline", "let me just try X and see".

### The three kinds of conditions to nail down

- **Success condition** — what specific observable outcome means "done". Not "runs without error" — the actual thing that has to be true. Example: "file exists on disk, >10KB, valid JSON" or "all 15 beats generate and their files are ≥50KB each".

- **Testing condition** — for a specific function or debug scenario, what must hold for the test to genuinely validate the thing we care about. What inputs, what state, what pass/fail signatures. Feeds directly into Principle 1.

- **Workflow condition** — for multi-step flows, what preconditions each stage needs, what it hands off to the next stage, and what end state signals the whole thing worked.

### Output format (always include all four sections)

Whenever this principle is applied, the output MUST contain these four sections in this order. The TL;DR is not optional — it exists so the user can verify I actually understood the task, instead of just parroting the template back.

```
**Success condition**
- <observable criteria, or "n/a" with explicit reason>

**Testing condition**
- <inputs, required state, pass/fail signatures, or "n/a" with explicit reason>

**Workflow condition**
- <per-stage preconditions and handoffs, or "n/a" with explicit reason>

**TL;DR**
**<Headline: 2-4 bolded words naming the kind of task.>** <One short sentence, ~20 words max, naming what matters MOST for this specific task.>
```

Rules for the TL;DR (headline + clarifier form):

- **Headline** is 2-4 bolded words that name the *kind* of task. Examples: "Fix one function.", "Prove both directions.", "Guard every handoff.", "Chase a silent bug.", "Tighten a slow loop."

- **Clarifier** is ONE sentence, ~20 words max, written in **active voice with concrete verbs** — "Run it on X", "Watch the bug vanish", "Catch bad sizes", "Feed it N inputs", not "is expected to" / "should be verified that" / passive constructions. Active verbs move; passive voice limps.

- **Keep the specifics.** Numbers, filenames, sizes, counts — preserve them. "10 runs, empty files" beats "a bunch of runs and bad output." Active phrasing should reduce word count, not replace precision with vibes.

- **No paragraph form.** If it won't fit in one sentence, the three conditions above weren't tight enough — go tighten them, don't inflate the TL;DR.

- Don't recap "n/a" sections in the TL;DR. The TL;DR picks the single most important thing, not a summary of the template.

- Analogy or warning variants are allowed if they land cleaner than a standard clarifier, but still ≤ headline + one sentence total.

**Reference TL;DRs (hybrid style — active verbs + precision):**

- **Fix one function.** Run it on the slow file plus three fast ones — every image back real and under 30 seconds, no blurry fallback.

- **Prove both directions.** Watch the bug happen on old code, then watch it vanish on new code — 10 runs each, check for empty files.

- **Guard every handoff.** Each stage hands its work to the next — catch bad sizes at every boundary, and make sure the final file hits spec.

### Gate before starting

Answer each in one sentence. If any answer is "I don't know", stop and figure it out before acting.

1. **Can you state the success condition in one sentence with observable criteria?**

2. **Do you know what a valid test looks like — inputs, required state, pass/fail signatures?**

3. **For a workflow, can you list the preconditions and handoff for each stage?**

### Common invalid patterns

- Starting to fix a bug without pinning down what "fixed" means.

- Running a test where "no exception" is the implicit pass condition.

- Running a multi-stage pipeline without knowing what each stage should hand off.

- "Let me just try this and see what happens" as a verification strategy (fine for exploration — NOT for verification).

- Editing code in response to a bug report without first nailing down the reproducer and the expected-vs-actual behavior.

### Hard NOs

- Do not start writing code until you can state what success looks like.

- Do not declare a bug fixed without a reproducer that demonstrated the bug AND now shows the fix works.

- Do not declare a workflow "done" if you can't point to the specific outcome that proves it ran correctly.

- Do not substitute "it didn't crash" for a real success condition.

- Do not skip this gate because "the condition is obvious" — write it down, even if it's one short sentence.

### Origin

Surfaced during the WHISK_THREADS=80 episode and surrounding pentest sessions. Repeated pattern: without an upfront definition of what the test was actually verifying, we accepted degenerate "passes" that didn't exercise the target (1-beat test for an 80-thread claim, for example). This principle prevents the same class of failure as Principle 1 but earlier — before the test is even written.


`========================================`

<!--
===============================================================================
APPEND NEW PRINCIPLES BELOW THIS MARKER
===============================================================================

Copy the template block below and fill it in. Then:
1. Bump the number (Principle N)
2. Add a one-line entry to the Principles Index at the top
3. Update the skill description (frontmatter) if the new principle adds a new
   trigger phrase the model-invocation matcher should see

Keep the section order and heading names identical across all principles so the
skill stays scannable. If a principle doesn't need a subsection (e.g. no "when
you can't fully apply"), delete that subsection — don't leave it empty.
===============================================================================
-->


## Principle 3 — Keep the end goal in sight

**Rule:** Fully understand the end goal and what "done" looks like. Inventory the materials, docs, references, and context the user has given you. Then move toward the goal piece by piece using what you've got — every action and every question traceable back to the goal. Don't drift into tangents, don't stall asking questions the context answers, don't forget the initial issue that started this, and don't do random stuff.

**One-line form:** Know the target. Use what you have. Remember why you started. Don't do random stuff.

### When it applies

- Any multi-step task where the user has stated an end goal or raised an initial issue.

- User has provided source material, docs, references, examples, or prior decisions that inform the work.

- `/auto` runs, `/loop` runs, approved plans under execution, any autonomous flow.

- Any moment you're about to ask a clarifying question.

- Any moment you catch yourself "improving", "cleaning up", or exploring outside the target.

- Any point where a sub-problem has pulled focus from the original issue.

- Trigger phrases: "finish this", "keep going", "/auto", "/loop", "you know what to do", "stop asking", "use this doc", "here's the reference", "did the original thing get fixed?", "stay on track".

### Failure modes this catches

- **Drift** — tangential work that feels helpful but doesn't advance the goal. Unprompted cleanup, refactors, "while I'm here" edits.

- **Question-stalling** — asking a clarifying question whose answer is already derivable from the plan, the goal, prior turns, or materials the user provided.

- **Ignoring provided materials** — user hands over a doc / reference / example describing how to do X well, and the output doesn't use it. Decent work, but not the work the materials enabled.

- **Random output** — actions or choices that can't be traced back to the end goal. Winging it instead of reasoning from the target backward.

- **Losing the initial issue** — getting pulled into sub-problems and never circling back to verify the original problem the user raised is actually fixed. Intermediate wins without final confirmation.

- **Not picturing "done"** — starting work without a concrete mental image of what the finished state looks like. Without that, every decision becomes a guess.

- **Pre-work interrogation** — asking 3-5 clarifying questions when the task is already concrete enough to start. Stalls the goal under the guise of rigor.

- **Re-opening settled decisions** — surfacing a decision the user already made, as if it's still open, with no new evidence that would change it.

### Gate before acting or asking

Answer each in one sentence. If any answer is no or "I don't know", stop and correct course.

1. **Can I state the end goal and what "done" looks like in one sentence?** If no, re-read the request or ask ONE targeted question — not three.

2. **What do I have already?** Inventory the materials, docs, references, plan, and prior decisions that apply here. Use them.

3. **Does this action or question trace back to the goal?** If I can't draw a line from "this" to "the goal," it's random — don't do it.

4. **If I'm about to ask — is the answer derivable from the plan, the goal, prior turns, or materials the user provided?** If yes, don't ask. Act on the most logical reading.

5. **Is the initial issue still the target?** If the work has drifted into a sub-problem, make sure the original issue is going to get resolved and confirmed, not abandoned.

### When you CAN ask (the narrow list)

- Genuine ambiguity that blocks progress AND the plan / materials offer no default.

- About to take a destructive or irreversible action (deletes, force pushes, external sends).

- Two stated goals conflict with no tiebreaker in context.

- New information surfaced that invalidates a prior decision.

Everything else — pick the most logical reading, act, and note the assumption in one line.

### Common invalid patterns

- User provides a doc on how to do X well — output does X but ignores the doc's methods → invalid.

- Task is "fix the bug" — I start reformatting unrelated code → invalid.

- `/auto` is running — I stop to ask a question the plan already answers → invalid.

- User asked for one principle — I ask three clarifying questions before drafting → invalid.

- User's initial issue was A — we fixed related thing B — I declare done without rechecking A → invalid.

- User said "make it work with 80 threads" — I ask "are you sure about 80?" without new evidence → invalid.

### Hard NOs

- Do not start work without a clear picture of what "done" looks like.

- Do not ignore materials, docs, or references the user provided — read them and use them.

- Do not take actions that can't be traced back to the end goal.

- Do not stall `/auto` or `/loop` for questions the context or plan already answers.

- Do not declare a task complete without verifying the ORIGINAL issue the user raised is actually fixed and observable.

- Do not re-open a settled decision without new evidence.

- Do not wrap stalling in the language of rigor ("just to be safe", "to double-check", "before I start").

### Worked examples

Each example shows the wrong move (failure mode) and the right move (what the principle demands).

**A — Provided materials ignored**

Situation: User attaches a doc describing how to do X well, asks for X.

- ❌ Do X using general knowledge, ignore the doc's methods. Output is "decent" but not what the doc enabled.

- ✅ Read the doc first. Extract the specific techniques. Apply them. Use general knowledge only to fill gaps the doc doesn't cover. Every choice traces back to "goal + material given."

**C — Initial issue forgotten**

Situation: User reports "tests failing because of Redis timeout." You dig in, find the Redis config is wrong, fix it.

- ❌ "Fixed the Redis config. Done."

- ✅ Rerun the ORIGINAL failing tests. Confirm green. THEN declare done. Sub-problems are waypoints, not destinations — the original symptom is the finish line.

**E — `/auto` halts when a move WAS available**

Situation: `/auto` is mid-run. Hits a small choice — f-strings vs .format(), a naming style, a sensible default.

- ❌ Halt the loop and ask the user which to use.

- ✅ Check for a derivable answer. Match the file's existing style. Fall back to a modern Python default. Follow the plan's implied choice. Take the move, log it in one line, continue.

**The rule for `/auto` halts:** the bar is "genuinely no move is available," NOT "first moment of uncertainty." Most halts fall in the "a move WAS available" bucket — that's the failure.

**I — Easier-adjacent task ≠ actual goal**

Situation: User says "make the image generator 10x faster." You notice caching is easier than optimizing raw generation.

- ❌ Add caching, say "faster now" — true only on cache hits, not on the thing the user actually asked about.

- ✅ Measure raw generation speed. Improve that. Caching is a bonus, not a substitute for the stated goal.

**J — `/auto` hits a genuine blocker**

Situation: `/auto` plan step is "deploy to staging." Staging DB schema is outdated and the plan doesn't cover migrations.

- ❌ Halt the whole run and ask "should I migrate?"

- ❌ Kill the run entirely.

- ✅ Park THIS step with a clear flag ("blocked: schema migration needed, not in plan scope"). Keep the run alive on any independent work. This step waits for unblock — the run does not die, and no user input is solicited mid-flow.

Pair E and J together — they're the two halves of `/auto`'s decision rule. E is "derive and continue" when an answer exists. J is "park and flag" when one genuinely doesn't. Never "halt and ask."

**K — Random addition not traceable to goal**

Situation: Task is "build a retry wrapper that handles rate limits." You consider exponential backoff, jitter, AND a circuit breaker.

- ❌ Ship all three because they're "best practice."

- ✅ Ship what the stated goal requires (exponential backoff for rate limits). Add jitter only if the API's own docs suggest it. Skip the circuit breaker unless the goal mentions cascading failures. Every addition traces back to what was asked — unasked-for additions are drift, even if they're "good."

### Origin

Surfaced 2026-04-23 after two recurring instances:

1. Same-session meta incident: user asked to add this principle about end-goal drift and question-stalling. Instead of drafting, I responded with three clarifying questions — the exact failure the principle is meant to prevent.

2. Separate session on character consistency: user provided a source doc describing how to do character consistency well. The output was "decent" but didn't pull much from the doc — failure to connect the chain "here is the goal" + "here is helpful material" + "use the material to reach the goal." Did semi-random work that happened to land close-ish, not goal-directed reasoning.

Both failures share one root: losing sight of the end goal and what reaching it requires. This principle makes the goal, the materials, and the logical next step the primary inputs to every action — not tangents, not questions, not random effort. And it extends to remembering the initial issue so the original problem is confirmed fixed, not quietly abandoned along the way.


`========================================`


## Principle 4 — Audit against the goal before handback

**Rule:** Before handing back at the end of every task, run an active checkpoint. State the end goal. State the current observable state. Name the gap. Emit a verdict with three fields — Result, Toward goal, Next — in one of four states. The verdict is the OUTPUT of that audit, not a decoration. The user reads it to decide what to do next, so every line must be decision-useful.

**One-line form:** Before you stop: audit vs the goal, emit Result / Toward goal / Next. Cut anything the user wouldn't use.

### When it applies

- End of every task-turn where any real work was done.

- Especially after multi-step tasks, debugging, pipeline runs, code changes, refactors, anything where "are we there yet?" is a real question for the user.

- Trigger phrases in the situation: about to send a response that ends with work-output; about to say "let me know if you want more"; about to hand back without a status line; user asked "are we done?", "what's left?", "what's next?", "anything else?".

### The checkpoint procedure

Before writing the verdict, run these 4 steps:

1. **What was the end goal the user originally asked for?** State it to yourself in one sentence. Not the immediate sub-step — the thing they actually want.

2. **What is the current observable state?** Not "I did X" — what exists / runs / passes on disk right now, provable by something the user could check.

3. **What's the gap?** Zero, small, blocked, or ambiguous.

4. **Emit the verdict** based on that gap, with decision-useful content in every line.

### Verdict block format

Pick one of the four states. Headline says what's true or what's needed. Body splits into **Done** (what now exists, observable) and **Pending / Blocker / Ambiguity** (what's still open, named concretely). Always end with **Next** — one concrete action.

```
**✅ DONE — <one-line summary of what's now true>.**

Done:
- <observable artifact / state 1>
- <observable artifact / state 2>

Next: nothing. Optional: <X>.
```

```
**🟡 PARTIAL — <one-line summary of what still needs to happen>.**

Done:
- <change / artifact 1>
- <change / artifact 2>

Pending:
- <gap, named concretely>

Next: <specific action that closes the gap>.
```

```
**🔴 BLOCKED — <one-line summary of what's stopping it>.**

Done:
- <progress made before the block>

Blocker: <what stopped it, with evidence>.

Next: <what would unblock — you do X, or I retry with Y>.
```

```
**❓ UNCLEAR — need your call on <one-line headline>.**

Done:
- <what was attempted>

Ambiguity: <the one thing I can't decide without more info>.

Next: <the one piece of info that resolves it>.
```

### Rendering style

Keep the verdict block consistent with the rest of the response. Two rules, inline:

- **Active voice.** Subjects do things: "I check the current state" beats "the current state is checked." "You rerun the test" beats "the test should be rerun."

- **Spacing.** One blank line above and below any `====` separator. One blank line between bullets in a list. Don't double up.

For richer step-by-step responses that wrap a verdict block, follow the full explain skill walkthrough format — bold step names, `====` separators between steps, and a TL;DR bullet list at the end. See `~/.claude/skills/explain/SKILL.md` format #11 for the canonical example.

### Failure modes this catches

- **Silent stop** — hand back output with no verdict, user has to infer status from the prose.

- **Format without substance** — emit a verdict block that was not produced by an actual audit (writing DONE because the step finished, not because the end goal was cross-checked).

- **False complete** — declare DONE on a sub-step even though the end goal isn't hit. P3 failure, caught again here as a second net.

- **Narrative verdict** — replace the decision-ready block with a prose recap of what I did. User has to extract status manually.

- **Non-useful content** — verdict lines that don't help decide the next move. "Progress made" without naming what. "More work needed" without naming what.

- **Gap without next move** — name that something is missing but not say what action closes it.

- **Burden shift** — "let me know if you want more" / "hope this helps" / "feel free to ask" instead of telling the user where things stand and what to do.

- **Fake precision** — "75% done" with no basis for the number.

### Gate before handback

Before sending the response, answer each:

1. **Did I run the 4-step checkpoint?** If no, run it now.

2. **Is every line in the verdict decision-useful?** Would the user use each line to pick a next move? If a line wouldn't change their action, cut it.

3. **Does each "Done:" bullet name an observable thing, not a claim?** "Config updated" is a claim. "`retry_count=3` in `config.yaml`, service restarted" is observable.

4. **Does the headline contrast current state with the original end goal, not with the sub-step?** Sub-step wins are waypoints; the goal is the destination. The headline should be true at the level of the user's actual ask.

5. **If not DONE, does "Next" name one concrete action?** Not "probably need to X" — the actual action the user or I would take next.

### When you can skip the verdict block (the narrow list)

- Pure conversational replies — greetings, clarifications, meta-chat.

- Single Q&A where the answer IS the completion (e.g., "what does this function do?" — the answer satisfies, no block needed).

- Deliberate proposal or structure for user review (planning passes, draft phases) — the request for feedback IS the next step, block optional.

Everywhere else, emit the block.

### Common invalid patterns

- "Done. Let me know if you want more." → invalid (no Result, no goal-position, no concrete next).

- Format present, but `Result` line reads "All changes applied successfully" → invalid (not observable, not useful).

- Verdict says DONE on a sub-step while the end goal remains unverified → invalid (false complete).

- Verdict block wrapped around a narrative recap of every step taken → invalid (not decision-ready; user still has to extract status).

- "Toward goal — 75% done" with no basis for the number → invalid (fake precision).

- `Next — "I can help with more if you want"` → invalid (burden shift, not a concrete action).

### Hard NOs

- Do not hand back without a verdict when real work was done.

- Do not emit a verdict that was not produced by an actual checkpoint against the end goal.

- Do not declare DONE without citing observable evidence in the Result line.

- Do not name a gap without naming the concrete next move.

- Do not pad the verdict with narrative, caveats, or cheerleading.

- Do not use "let me know if you want more" as a substitute for a Next line.

- Do not fake-audit — rubber-stamping DONE because the step ran is the worst failure mode.

### Worked examples

**Example 1 — PARTIAL handback (Redis / render case)**

User asked: "fix the video render bug."

Wrong:

> Fixed the Redis config. Let me know if you want to rerun the tests.

Right:

```
**🟡 PARTIAL — render not yet re-run with the new timeout.**

Done:
- Redis timeout raised from 2s → 10s in config.yaml.
- Service restarted; new value confirmed in /healthz.

Pending:
- Original failing render (clip_42.mp4) has not been re-run against the patched config.

Next: rerun render_test.py with clip_42.mp4. If it passes, update to DONE.
```

**Example 2 — DONE handback (feature added and verified)**

User asked: "add pagination to the /videos endpoint."

Wrong:

> Added pagination to /videos. Hope this works!

Right:

```
**✅ DONE — /videos endpoint now supports pagination.**

Done:
- /videos?page=N&per_page=M parameters wired; defaults page=1, per_page=20.
- Response body includes total, page, per_page.
- Integration test test_pagination.py passes.

Next: nothing. Optional: update the client SDK if it's in use.
```

**Example 3 — BLOCKED handback (prod deploy)**

User asked: "deploy the new auth middleware to production."

Wrong:

> Tried to deploy but hit an issue. Can you check?

Right:

```
**🔴 BLOCKED — prod deploy failed at the secrets-lookup step.**

Done:
- Staging deploy succeeded; auth middleware running on staging.

Blocker: prod IAM role missing secrets:GetSecretValue on AUTH_SIGNING_KEY (403 from secretsmanager).

Next: grant the prod deploy role access to the new key, OR rotate the key into the existing accessible bundle, then rerun the prod deploy step.
```

### Relationship to the other principles

- **P2** runs BEFORE work — defines what "done" looks like.

- **P3** runs DURING work — keeps every action traceable to the goal.

- **P4** (this one) runs AFTER work — audits current state vs the goal and reports in a form the user can act on.

Before / during / after. Three checkpoints around every task.

### Origin

Surfaced 2026-04-23. Recurring pattern: task responses end with a sub-step status ("fixed the Redis config") without checking whether the END goal (the original bug) is actually hit. The user is left to ask "so are we done?" or manually run the reproducer. Related pattern: responses that close with "let me know if you want more" instead of telling the user where things stand. Both force the user to do the audit themselves. P4 pushes the audit back where it belongs — my side of the handback — and shapes the output as a decision tool, not a narrative dump.


`========================================`


## Principle 5 — KISS (Keep It Simple)

**Rule:** Pick the simplest solution that solves the present requirement. Every layer of abstraction, indirection, configuration, or "flexibility" must be justified by a concrete reason that exists *today* — not a hypothetical future one. Duplication beats the wrong abstraction. Wait for the rule of three before extracting.

**One-line form:** Simplest thing that works wins. Complexity needs a reason that exists right now.

### When it applies

- Designing a new component, function, class, or service from scratch.

- Refactoring tangled code, deciding whether to add an abstraction or live with duplication.

- Vibe-coding, prototyping, or any "just make it work" task where it's tempting to over-build.

- About to add a factory, registry, decorator, wrapper, base class, plugin system, or config layer.

- Choosing between inheritance and composition for a new class hierarchy.

- About to write a function longer than ~50 lines, or one that mixes I/O and business logic.

- Trigger phrases: "in case we need it later", "for future flexibility", "to make it extensible", "best practice", "let's make it generic", "this should be configurable", "what if we want to swap X someday", "I'll abstract this", "refactor this", "design pattern", "architecture", "let's build a framework", "vibe code this", "quick prototype", "just make it work".

### Failure modes this catches

- **Speculative generality** — code shaped for a use case that doesn't exist yet ("we might want to support YAML one day").

- **Premature abstraction** — extracting a base class or helper from two callers, then locking in the wrong shape when the third caller is different.

- **Pattern theatre** — applying a Factory / Strategy / Observer / Singleton because it's "best practice", when a dict / function / module-level value would do the same job in a fraction of the code.

- **Layer inflation** — wrapping every operation in service → repository → adapter → port when the project has one database and one caller.

- **Config-itis** — exposing a knob for a value that has only ever held one setting, "in case it changes later".

- **God class / megafunction** — opposite failure: cramming HTTP parsing, validation, business logic, DB access, and response formatting into one unit because "splitting it feels like overkill". Both extremes are KISS violations — the right size is one reason to change.

- **Inheritance trees for behavior reuse** — three-deep class hierarchies where one composed object would do.

- **Clever one-liner** — a comprehension or generator chain that takes five minutes to read; the loop version reads in five seconds.

- **Wrapping working code** — adding a helper / decorator / facade around code that already works, because the wrapper "feels cleaner". It isn't, and now the caller has two things to learn instead of one.

### Check / gate before adding complexity

Answer each in one sentence. If any answer is "no" or "I don't know", do the simpler thing.

1. **Can I name the concrete present-day problem this complexity solves?** Not a future-tense problem. A real one, today, in this codebase. If the only justification is "future flexibility", cut it.

2. **Does the simpler version actually fail to meet a stated requirement?** Run the simpler version mentally — what specifically breaks? If nothing breaks, the simpler version wins.

3. **Have I seen this pattern at least three times?** (Rule of three.) Two similar callers is duplication. Three is a pattern. One is fantasy. Wait for the third before extracting — unless the duplicates are already diverging in dangerous ways.

4. **If I'm splitting a unit: does each piece have one reason to change, in one domain?** HTTP parsing AND business logic AND SQL in one class is too many. But splitting "validate" from "save" inside one domain is often pointless. The test is "different reasons to change", not "different verbs".

5. **If I'm composing vs inheriting: would composition work?** Default to composition. Reach for inheritance only when there is a true is-a relationship AND you need polymorphism the language gives you for free. Almost never on first draft.

6. **Senior-engineer test:** would a senior engineer reading this say it's overcomplicated? If yes, it is. Cut.

### Common invalid patterns

- Two callers, extract a shared helper "for consistency" → invalid (rule of three).

- `OutputFormatterFactory.register("json")` for three formatters with no plugin system in sight → invalid (a dict beats it).

- `class BaseService` with one subclass → invalid (just be the class).

- `def get_user_by_id_with_cache_and_retry_and_logging(...)` mixing I/O, caching, retries, and logging → invalid (split, or use middleware/composition).

- `config.yaml` exposing 14 knobs that have never been changed in production → invalid (inline the defaults until someone needs to override).

- Adding an interface / Protocol with one implementation "in case we want to mock it" → invalid (mock the concrete one or pass a fake — the Protocol can come when there's a second impl).

- Wrapping a stdlib call in a 20-line helper that adds nothing the stdlib doesn't already give you → invalid.

- Replacing a 6-line for-loop with a nested comprehension that takes 30 seconds to parse → invalid (clever ≠ simple).

- 200 lines where 50 would do the job → invalid (rewrite it; if your draft is 4× the necessary size, the design is wrong).

- `try / except` blocks for failure modes that cannot occur (e.g. catching `ZeroDivisionError` on a literal `1 / 2`) → invalid (no error handling for impossible scenarios).

### Hard NOs

- Do not add a layer, abstraction, or pattern whose only justification is "we might need it later".

- Do not extract a shared abstraction from two callers — wait for the third, OR until divergence is causing bugs.

- Do not use inheritance when composition works, on first draft.

- Do not split a class until you can name two separate reasons-to-change in two separate domains.

- Do not mix HTTP parsing, business logic, and data access in the same unit — that's the *one* split that is non-negotiable.

- Do not wrap working code in a "cleaner" facade unless the wrapper removes a concrete pain (not a stylistic preference).

- Do not write clever code where plain code reads in half the time.

- Do not introduce a config knob for a value that has never varied.

- Do not call this rule "satisfied" because the code is *short*. Short clever code can still be a KISS violation. The test is **readable in one pass and justified by today's need.**

- Do not write error handling for failure modes that cannot occur. `try/except` exists to handle real failure surfaces, not to look defensive.

### Worked examples

**A — Factory vs dict**

Situation: Need to pick a formatter (`json`, `csv`, `xml`) by name.

- ❌ Build `FormatterFactory` with a `@register` decorator and a class registry.

- ✅ `FORMATTERS = {"json": JsonFormatter, "csv": CsvFormatter, "xml": XmlFormatter}` plus a four-line `get_formatter(name)`. Promote to a factory only when there's a real plugin loader, not because "factories are better".

**B — Inheritance vs composition for notifications**

Situation: Need to send notifications via email, with SMS and push planned later.

- ❌ `NotificationService` base class, subclass `EmailNotificationService`, subclass `SmsNotificationService`, override `notify()` in each.

- ✅ One `NotificationService` that takes injected `email_sender`, optional `sms_sender`, optional `push_sender`. Add channels by passing more senders, not by adding subclasses.

**C — Premature extraction (rule of three)**

Situation: Two functions, `process_orders` and `process_returns`, look structurally similar.

- ❌ Extract `_process_collection(items, validate, process)` because "DRY".

- ✅ Leave the duplication. The validation and processing rules are domain-specific and likely to drift apart. Wait for a third real case before deciding there's a pattern.

**D — God function refactor**

Situation: `process_order(order)` is 140 lines: validation, inventory, payment, notification, logging.

- ❌ Leave it because "splitting feels like overkill" — KISS doesn't mean "refuse to split".

- ✅ Five focused calls inside `process_order`: `validate_order(order)`, `reserve_inventory(order)`, `charge_payment(order)`, `send_confirmation(...)`, return result. Each function does one thing; `process_order` reads like a table of contents.

**E — Vibe-coding and "best practice" drift**

Situation: User says "vibe code a quick script that downloads a CSV and prints the rows".

- ❌ Set up a `Downloader` class, a `Parser` class, a `dataclass` for rows, an `argparse` CLI, a `logging` config, a `pyproject.toml`.

- ✅ A 15-line script: `requests.get`, `csv.reader`, a for-loop, a `print`. If the user asks for more, add it then. KISS at prototype stage means YAGNI is on by default.

**F — Optional Protocol with one impl**

Situation: One service uses one cache. Tempted to define a `Cache` Protocol so it's "swappable".

- ❌ `class Cache(Protocol): ...` plus `RedisCache(Cache)` plus injected `Cache` everywhere, with one implementation.

- ✅ Inject `RedisCache` directly. If a second cache implementation appears (rule of three: a real test fake counts as one), introduce the Protocol then. Mocking does NOT require a Protocol — `unittest.mock` patches the concrete class fine.

### Relationship to the other principles

- **P2** defines what success looks like. KISS asks: *what's the simplest thing that meets that definition?* Anything beyond that is decoration.

- **P3** keeps every action traceable to the goal. KISS is a sub-rule of P3 for the *code itself* — every layer of code must trace to a present requirement, not a hypothetical one.

- **P4** audits state vs goal at handback. If the audit shows the goal is met but the code is heavier than it needs to be, the verdict is **PARTIAL** with a "simplify" pending — not DONE.

- **`simplify` skill** — the runtime tool for applying KISS to a code change. This principle is the standard; `simplify` is the procedure.

- **`strict-mode` skill** — forbids drive-by improvements. KISS forbids drive-by *abstractions*. They're complementary: don't change what wasn't asked, AND don't add what isn't needed.

### Origin

Surfaced 2026-04-25 during a discussion of vibe-coding and keeping prototypes from ballooning. Pattern observed across multiple sessions: the user explicitly asks for "simple" or "quick" work, and the default response reaches for factories, base classes, configurable knobs, and Protocols-with-one-impl — all of which are "best practice" in the abstract but pure overhead for the actual job. The user's existing memories already encode this preference (KISS-first optimization, smallest change biggest dial, no overengineering); promoting it to a Principle puts it on the same checkpoint footing as P1–P4, so it gets actively applied at design time, not retrofitted by a later cleanup pass.

Reinforced same day by absorbing the **"Simplicity First"** principle from Andrej Karpathy's CLAUDE.md (forrestchang/andrej-karpathy-skills): the senior-engineer overcomplication test, the "200 lines could be 50, rewrite it" check, and "no error handling for impossible scenarios" all live here as a result.


`========================================`


## Principle 6 — Think before coding

**Rule:** Before writing code, surface what's silent. State your assumptions out loud. If multiple interpretations of the request exist, present them — don't pick one in your head and run with it. If a simpler approach is available, say so and push back. If something is genuinely unclear, stop and name what's confusing instead of guessing.

**One-line form:** Don't run with a silent assumption. Say it. Say the alternative. Say the tradeoff.

### When it applies

- About to start any non-trivial task — a function, a fix, a refactor, a script.

- The request is ambiguous, under-specified, or could mean two different things.

- A simpler approach exists than the one the user named, and they may not have seen it.

- An unstated assumption (about scale, format, environment, ordering, error semantics) is required to proceed.

- The default approach has a real tradeoff the user should weigh (cost, perf, complexity, lock-in).

- Trigger phrases: "implement X", "add Y", "make Z work", "write a script that…", any request where the problem statement is short and the solution space is wide. Also: any moment you catch yourself thinking "I'll just assume…" or "they probably meant…".

### Failure modes this catches

- **Silent assumption** — picking one of multiple valid interpretations without naming the choice. User reads the diff and finds you built the wrong thing.

- **Hidden confusion** — feeling unsure, charging ahead anyway, hoping it lands. The doubt was the signal — running past it just means the bug arrives later, with worse context.

- **Buried tradeoff** — choosing approach A over approach B silently, when B was simpler / cheaper / faster and the user would have picked it if shown. The "best" answer often isn't the one the user asked for verbatim.

- **No pushback** — implementing a needlessly complicated request without flagging that a one-line version exists. Silence reads as agreement.

- **Multi-interpretation collapse** — "build a cache" can mean five things. Picking one without asking erases four other valid readings.

- **Default-config drift** — assuming a default (timeout=30s, retries=3, format=JSON) without saying so. Defaults that aren't surfaced are silent assumptions.

### Gate before writing the first line of code

Answer each in one sentence. If any answer is "I'm guessing", stop and surface it.

1. **What am I assuming the user means by this request?** Write it down. If there's another reasonable reading, that's a fork — name both.

2. **Are there silent defaults I'm picking?** (Library, format, error semantics, timeout, ordering, idempotency, transactional vs not.) If yes, list them.

3. **Is there a simpler approach than the one being asked for?** If yes, say so before starting — even if I end up doing the asked-for version.

4. **Is anything genuinely unclear?** If yes, ask ONE targeted question — not three. (Pair with P3: only ask if the answer isn't already derivable from context.)

5. **Are there real tradeoffs the user should weigh?** Cost, perf, lock-in, complexity, reversibility. Surface in one line, not a paragraph.

### How to surface — the format

Keep it short. Three patterns work for almost every case.

**Single assumption:**

> Going to assume X (because Y). Say if you'd rather Z.

**Forked interpretation:**

> Two ways to read this:
> - **A:** [...] — simpler, but [tradeoff].
> - **B:** [...] — what you literally asked for.
>
> I'll go with A unless you say otherwise.

**Pushback on complexity:**

> You asked for X with N moving parts. A 5-line version using Y would do the same job for this case. Want the simple one, or do you actually need the full N?

The shape: name the choice → give the reason → invite a redirect. Three lines, not three paragraphs.

### When you do NOT need to surface

P3 still applies — don't stall on questions the context answers. Do not surface when:

- The answer is unambiguous from the request, the materials, or prior turns.

- The "assumption" is so trivial it doesn't change the diff (variable naming, formatting, file location within a clearly-scoped folder).

- The user explicitly said "just do it" / `/auto` is running and a derivable choice exists. (Pair with P3 example E: in `/auto`, take the move and log it in one line — that one line IS the assumption-surfacing.)

The bar: surface when a different choice would produce a meaningfully different diff. If the diff would look the same either way, it's not a real fork — just pick.

### Common invalid patterns

- "Add caching" → I implement Redis-backed write-through caching with TTL=300 → user wanted in-memory `functools.lru_cache` → invalid (didn't surface the fork).

- Request mentions a library; I substitute a different one I think is "better" without saying so → invalid (silent override).

- Request would take 200 lines as written, but a 30-line version exists; I write the 200 → invalid (no pushback).

- I feel unsure which of two endpoints to call, pick one, ship it. The wrong one → invalid (hidden confusion; the doubt was the signal).

- Three clarifying questions before drafting a one-line task → invalid (P3 violation; ask zero or one, not three).

- "I'll go with the standard approach" → invalid unless I say what the standard approach IS (vague reassurance is not surfacing).

### Hard NOs

- Do not pick silently between two valid interpretations.

- Do not implement a complicated request when a one-line version does the same job, without at least flagging the simpler option.

- Do not push past unresolved confusion. If you don't know, say you don't know — name what specifically is unclear.

- Do not pad the surfacing with hedges and disclaimers. One sentence per assumption, one sentence per tradeoff, then move.

- Do not use this principle as cover for stalling. Surfacing is fast; if it takes a paragraph, it's drift.

- Do not assume the user wants the verbose answer when the request was minimal — but DO surface that you're picking the minimal version.

### Worked examples

**A — Forked interpretation, surfaced**

User: "add validation to the create_user endpoint."

- ❌ Implement Pydantic schema with 12 fields, custom regex on email, password strength rules, async DB uniqueness check. Ship.

- ✅ "Two ways to read this — (A) just type/required-field checks on the input model, (B) full business validation including DB uniqueness for email. I'll start with A; say if you want B." Then start with A.

**B — Pushback on complexity**

User: "build a config system that supports YAML, TOML, JSON, and env vars with hierarchical overrides."

- ❌ Build it. 400 lines.

- ✅ "Quick check — is this a real need today, or for future flexibility? If it's just env vars + one YAML file right now, `pydantic-settings` does it in 20 lines. If you genuinely need all four formats, I'll build the full thing." Wait one turn.

**C — Hidden confusion, named instead**

Situation: User asks me to "fix the broken retry logic in worker.py". I read the file, two retry mechanisms exist (decorator + manual loop), and I'm not sure which one they mean.

- ❌ Pick one, fix it, hope it's the right one.

- ✅ "Two retry mechanisms in worker.py — the `@retry` decorator on `process_job` (line 42) and the manual `while attempts < 3` loop in `_send_request` (line 88). Which one is broken?" One question, specific, blocks progress.

**D — Surfacing in `/auto`**

Situation: `/auto` plan step says "add a CLI flag for verbose mode". The codebase uses both `argparse` and `click` in different scripts.

- ❌ Halt and ask.

- ✅ Match the file's existing style (whichever this script already uses). One-line note in the run log: "used argparse to match existing CLI in this script." Continue. (P3 example E.)

**E — Default-config drift caught**

User: "write a function that fetches a URL and returns the body."

- ❌ Use `requests.get(url).text`, no timeout, no error handling. Ship.

- ✅ "Going with `requests.get(url, timeout=10).text`, no retry, raises on HTTP error. Say if you want async, retries, or a different timeout." 15 seconds of surfacing, prevents an "oh wait, I needed httpx" round-trip.

### Relationship to the other principles

- **P2** defines what success looks like. **P6** is what runs *before* P2 when the request itself is ambiguous — you can't write success conditions for a goal you've silently re-interpreted.

- **P3** says *don't* stall asking questions the context answers. **P6** says *do* surface the ones the context doesn't. Together: ask zero questions when context resolves it, one targeted question when it doesn't, and never three.

- **P5 KISS** is the standard for the code itself. **P6** is the standard for the conversation *about* the code — surfacing the simpler approach is how P5 gets a chance to apply.

### Origin

Adopted 2026-04-25 from Andrej Karpathy's CLAUDE.md (forrestchang/andrej-karpathy-skills, principle #1 "Think Before Coding"). The user already has memories about KISS-first optimization and naming tradeoffs, but the *upstream* habit — surfacing the assumption / fork / tradeoff *before* the implementation lands — was not encoded as a principle until now. P6 makes the pre-implementation surfacing a hard checkpoint, mirroring how P4 makes the post-implementation audit a hard checkpoint.


`========================================`


## Principle 7 — Surgical changes

**Rule:** Touch only what the user's request requires. Don't drive-by improve adjacent code, comments, or formatting. Don't refactor things that aren't broken. Match the existing style even if you'd write it differently. If you notice unrelated dead code or bugs, *mention* them — don't delete or fix them silently. Clean up only the orphans your own change creates.

**One-line form:** Every changed line traces to the request. Mention strays. Don't fix them.

### When it applies

- Editing existing code anywhere — single function, single file, multi-file refactor.

- Approving a fix for a specific bug or completing a specific feature ask.

- Working in code that you didn't write, or code with a style you'd personally do differently.

- Running `/auto` or `/loop` where the temptation to "tidy while I'm in here" compounds.

- Trigger phrases: "fix X", "update Y", "change Z", "while I'm here", "I noticed…", "I also cleaned up…", "I improved…", "I refactored some adjacent code", "I fixed a typo I saw", "I removed unused imports while I was at it" — any phrasing that signals expanding beyond the asked-for scope.

### Failure modes this catches

- **Drive-by improvement** — reformatting, renaming, restructuring code that wasn't part of the ask. Bloats the diff, hides the real change, breaks `git blame`.

- **Style imposition** — replacing the file's existing patterns with the patterns I prefer (e.g. f-strings → `.format()`, list comprehension → for-loop, or vice-versa). Match what's there.

- **Silent dead-code deletion** — finding pre-existing unused imports / functions / branches and deleting them without being asked. May be load-bearing in ways not visible from the file (re-exported, monkey-patched, used by tests).

- **Side-quest fix** — noticing an unrelated bug, fixing it, shipping it in the same change. The fix may be wrong, untested, or politically not yours to make.

- **Refactor-by-stealth** — restructuring "while I was here" — extracting helpers, splitting functions, rearranging order. Even when the result is "better", the user didn't ask, and now the diff isn't reviewable as a fix.

- **Comment churn** — rewording comments to "clarify" them. Comments often encode context the original author had and you don't.

- **Orphan neglect (the one error in the OPPOSITE direction)** — removing a function but leaving its now-unused import, or renaming a thing but leaving five callers stale. Your change made these orphans; you must clean them.

### Gate before staging the diff

Answer each in one sentence. If any answer is "no" or "I added some extras", trim the diff.

1. **Does every changed line trace directly to the user's request?** If a line was changed for any other reason, revert it.

2. **Did I match the file's existing style — naming, indentation, idiom, comment voice — even where I'd personally write it differently?** If no, conform.

3. **Did I touch any pre-existing dead code or pre-existing bugs?** If yes, revert the touch and instead **mention** it in the response. Do not delete pre-existing dead code silently.

4. **Did my changes create orphans (now-unused imports, variables, functions, callers, type stubs)?** If yes, clean them up — those ARE part of the request, transitively.

5. **Is the diff reviewable as a single intent?** If a reviewer would have to ask "what is THIS line doing in here?", that line is drift.

### When mentioning vs fixing

The rule for things you noticed but weren't asked to touch:

- **Mention** — in the response: "noticed `legacy_helper` is unused at the top of `users.py` — left it untouched, flag it if you want a cleanup pass."

- **Don't fix** unless: (a) the user asked, (b) it's directly blocking the asked work, or (c) it's an orphan your own change created.

- **For genuinely critical issues** (security hole, data-loss bug) — surface immediately and ask, don't silently patch.

### Common invalid patterns

- Asked to fix a bug in `process_order`; I also reformat `validate_inventory` because "it was inconsistent" → invalid.

- Asked to add a feature; I delete three unused imports I noticed → invalid (P7 violation, even though linters would agree).

- Asked to rename `userId` to `user_id`; I also change `customerId` to `customer_id` "for consistency" → invalid (different name, different ask).

- Asked to fix a typo in a docstring; I rewrite the whole docstring "to make it clearer" → invalid.

- Asked to update a function; I "simplify" the function above it because it caught my eye → invalid.

- I notice a small bug while doing the asked work; I fix it inline without mentioning → invalid (mention, then ask).

- I make a change that leaves an import unused; I leave the import there → invalid in the OTHER direction (orphans I created are mine to clean).

### Hard NOs

- Do not change a line that doesn't trace back to the user's specific request.

- Do not "improve" working code that wasn't part of the ask.

- Do not impose your preferred style on a file that has its own style.

- Do not delete pre-existing dead code, comments, or branches silently — mention them and let the user decide.

- Do not bundle a side-quest fix into a focused change. If you notice something, surface it as a separate item.

- Do not reword comments unless the comment was wrong, the code it documents has changed, or the user asked.

- Do not leave orphans your own change created. Clean those.

- Do not use "I was already in the file" as justification. Being in the file is not authorization to edit beyond scope.

### Worked examples

**A — Asked to fix one function**

User: "fix the off-by-one in `paginate()`."

- ❌ Fix the off-by-one. Also rename the variable `lst` to `items` because it reads better. Reformat the docstring. Add a type hint that wasn't there before. Ship.

- ✅ Fix the off-by-one. Nothing else. If the docstring is now wrong because of the fix, update it (that's an orphan from my change). If the docstring was already wrong before my fix, mention it: "docstring also says page=0 returns first page; with this fix it returns empty. Want me to update the docstring too?" Wait for a yes.

**B — Mention dead code, don't delete**

While fixing a bug, I notice `_legacy_format()` is defined but never called.

- ❌ Delete `_legacy_format()` along with the bug fix.

- ✅ Bug fix lands. Response includes: "noticed `_legacy_format()` (line 142) appears unused — left it; flag if you want it removed in a follow-up." User decides.

**C — Style match, not style upgrade**

File uses `.format()` strings throughout. I'm adding a new line that builds a string.

- ❌ Use an f-string because they're "more modern".

- ✅ Use `.format()` to match the file. If `.format()` is genuinely worse for this case (e.g. multi-line, complex expressions), say so once and ask: "the rest of the file uses .format() but this expression has 4 nested calls that read cleaner as f-strings — match-the-file or pick-the-cleaner?"

**D — Orphan cleanup IS part of the change**

User asks me to remove the `legacy_auth` function.

- ❌ Remove the function, leave the `from .legacy_auth import legacy_auth` import in three other files because "the user only asked about the function".

- ✅ Remove the function AND every now-stale import / caller / test that becomes dead because of the removal. Those orphans were created by my change, so they're mine to clean. Stop at code that was *already* unused before my edit — mention those, don't delete.

**E — Side-quest bug, surfaced not bundled**

While adding pagination to `/videos`, I notice `/users` has a SQL injection.

- ❌ Patch the SQL injection in the same PR. Mention it in passing in the description.

- ✅ Pagination ships clean. Response: "🚨 separate from this change — `/users/search` (line 88 of `users.py`) builds SQL with f-string interpolation of the `q` param, which is a SQL injection. Recommend handling that as its own focused change. Want me to write a dedicated patch?" The severity earns immediate surfacing; the *fix* still gets its own review.

### Relationship to the other principles

- **P3** keeps every action traceable to the goal. **P7** keeps every *line of the diff* traceable to the request — same discipline, applied to the diff instead of to the work.

- **P5 KISS** says don't add layers without a reason. **P7** says don't add CHANGES without a reason. Together: nothing in the code or in the diff exists without justification.

- **`strict-mode` skill** is the runtime tool for applying P7 to a specific change. This principle is the standard; `strict-mode` is the procedure. (If `strict-mode` is active, P7 is implicitly active too.)

- **`audit` skill** runs before risky changes ship. It checks scope-match against the discussed intent — that check IS a P7 application.

### Origin

Adopted 2026-04-25 from Andrej Karpathy's CLAUDE.md (forrestchang/andrej-karpathy-skills, principle #3 "Surgical Changes"). Existing `strict-mode` skill already encoded most of this as a runtime-callable tool; promoting it to a Principle puts it on the same standing-checkpoint footing as P1–P6, so it applies even when `strict-mode` isn't explicitly invoked. The user's pattern of inheriting / vibe-coding into existing scripts where drive-by improvements would obscure the actual change makes this an ongoing risk, not a one-time concern.


`========================================`


## Principle N — {{ short title, imperative if possible }}

**Rule:** {{ one-sentence statement of the principle }}

**One-line form:** {{ the memorable / pithy version }}

### When it applies

- {{ situation or task type }}

- {{ trigger phrases from the user that should activate this rule }}

### Failure modes this catches

- **{{ mode name }}** — {{ what goes wrong }}

- **{{ mode name }}** — {{ what goes wrong }}

### Check / gate before claiming done

1. **{{ question }}** — {{ what a pass looks like }}

2. **{{ question }}** — {{ what a pass looks like }}

### Common invalid patterns

- {{ pattern }} → invalid

- {{ pattern }} → invalid

### Hard NOs

- Do not {{ forbidden behavior }}.

- Do not {{ forbidden behavior }}.

### Origin

{{ one or two sentences on the real incident that produced this rule, so future-you
can judge whether the rule still applies in edge cases }}


`========================================`


## How to use this skill at runtime

1. When the skill loads, scan the **Principles Index** at the top.

2. For each principle whose "When it applies" matches the current task, treat that principle as a hard constraint for the rest of the turn.

3. Before declaring a test passed / a value verified / a change safe, run through the relevant principle's **check / gate**. If any check fails, report it honestly — never paper over a failed check.

4. If the current task would violate a **Hard NO**, stop and flag it to the user before proceeding.

5. **Acknowledging the stop hook.** When a `principles-check.py` Stop hook fires (the user sees `Stop hook feedback: P4 checkpoint.`) and you respond with a bare acknowledgment, format it exactly as:

   ```
   Acknowledged — principles.

   =====
   ```

   The trailing `=====` separator gives the user a visual landmark to scroll past the enforcement chain (which can fire several times in a row) and resume the conversation. Do NOT add the separator when the response is a full P4 verdict block — the verdict block already serves as its own visual landmark. The separator applies only to bare acks where the entire reply is the acknowledgment line.


## Relationship to other skills

- **`strict-mode`** — constrains *what* code to change. `principles` constrains *how* to verify a change once made.

- **`audit`** — pre-execution gate that checks scope, risk, and assumptions. `principles` is the evidentiary standard the audit holds verification claims to.

- **`repair`** — debugging workflow. The "conclusive proof" phase of `repair` must satisfy the active principles in this skill.

- **`prep`** — planning workflow. Principles here shape what counts as an acceptable pentest result for the prototype.


## TL;DR

- Living list of hard rules, each tied to a specific past failure.

- **P1 — test-at-scale:** fire N, not 1; config-load ≠ load test.

- **P2 — figure out the conditions upfront:** state success, testing, and workflow conditions in one sentence each before acting. Don't start without them.

- **P3 — keep the end goal in sight:** understand "done", use provided materials, every action and question traces to the goal; confirm the original issue got fixed; in `/auto`, halt only when genuinely no move is available — never when one was.

- **P4 — audit against the goal before handback:** before stopping, run a checkpoint (goal / current state / gap) and emit a decision-ready verdict — Result / Toward goal / Next — in one of DONE / PARTIAL / BLOCKED / UNCLEAR. No narrative, no "let me know if you want more," no fake precision.

- **P5 — KISS, keep it simple:** simplest thing that solves the present requirement wins; complexity needs a concrete reason that exists today, not a hypothetical one; duplication beats the wrong abstraction; rule of three before extracting; default to composition over inheritance.

- **P6 — think before coding:** before writing the first line, surface assumptions, name forks when two readings exist, push back when a simpler approach is available, and stop to name confusion instead of guessing past it. Adopted from Karpathy's CLAUDE.md.

- **P7 — surgical changes:** every changed line traces to the user's request; no drive-by improvements, no style impositions, no silent deletions of pre-existing dead code; mention strays — don't fix them; clean only the orphans your own change created. Adopted from Karpathy's CLAUDE.md; pairs with the `strict-mode` skill.

- **Goal-driven execution** (Karpathy's #4): already lives across **P2** (state success conditions before acting) and **P4** (audit current state vs the goal before handback). The "transform imperative → declarative + verify in a loop" framing is the same idea — set criteria, then loop until they're met.

- Append new principles using the template. Update the index and the frontmatter description when you do.
