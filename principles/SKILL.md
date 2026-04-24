---
name: principles
description: Core engineering and collaboration principles the user has codified from past failures. Each principle is a hard-earned rule meant to prevent a specific, real failure mode. Currently covers (1) test-at-scale — tests must exercise the actual target condition, not just set a config value; (2) figure-out-the-conditions-upfront — identify success, testing, and workflow conditions before starting any task; (3) keep-the-end-goal-in-sight — every action and every question must advance the stated goal; don't drift into tangents; don't stop to ask when the answer is already in the plan or prior context; (4) audit-against-the-goal-before-handback — before stopping, run an end-of-task checkpoint comparing current observable state to the end goal, then emit a decision-ready verdict (Result / Toward goal / Next) in one of four states (DONE / PARTIAL / BLOCKED / UNCLEAR). Use when writing or running a test, claiming a value or threshold "works", reporting verification results, making any claim about code behavior, starting a non-trivial task, debugging, running a multi-step pipeline, running /auto or /loop, about to ask a clarifying question, mid-task considering a "while I'm here" detour, stalled by a question the context already answers, about to finish a task and hand output back to the user, or about to say "tested" / "verified" / "confirmed" / "worked" / "fixed" / "done" / "should I" / "do you want me to" / "before I start" / "just to confirm" / "quick question" / "let me know if you want more" / "hope this helps" / "are we done?" / "what's next?" / "anything left?". This skill is expected to grow — new principles will be appended over time, each following the template at the bottom.
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

Pick one of the four states and fill its fields. Nothing else.

```
✅ DONE
Result — <observable output / artifact / state that now exists>
Toward goal — fully there (confirmed by <evidence>)
Next — nothing; you are at the end goal  |  optional: <X>
```

```
🟡 PARTIAL
Result — <what was actually produced or changed>
Toward goal — <how close we are, what's still missing>
Next — <the specific next move that would close the gap>
```

```
🔴 BLOCKED
Result — <progress made before the block>
Blocker — <what stopped it, with evidence>
Next — <what would unblock — you do X, or I retry with Y>
```

```
❓ UNCLEAR
Result — <what was attempted>
Ambiguity — <the one thing I cannot decide without more info>
Next — <the one piece of info that would resolve it>
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

3. **Does the "Result" field name an observable thing, not a claim?** "Config updated" is a claim. "`retry_count=3` in `config.yaml`, service restarted" is observable.

4. **Does the "Toward goal" field contrast current state with the original end goal, not with the sub-step?** Sub-step wins are waypoints; the goal is the destination.

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
🟡 PARTIAL
Result — Redis timeout raised from 2s → 10s in config.yaml, service restarted.
Toward goal — unblocks the likely cause of the render hang, but the original failing render has not been re-run.
Next — rerun render_test.py with the failing clip; if it passes, update to DONE.
```

**Example 2 — DONE handback (feature added and verified)**

User asked: "add pagination to the /videos endpoint."

Wrong:

> Added pagination to /videos. Hope this works!

Right:

```
✅ DONE
Result — /videos?page=N&per_page=M parameters added; default page=1, per_page=20; response body includes total, page, per_page. Integration test test_pagination.py passes.
Toward goal — fully there (endpoint now supports the paginated shape).
Next — nothing. Optional: update the client SDK if it's in use.
```

**Example 3 — BLOCKED handback (prod deploy)**

User asked: "deploy the new auth middleware to production."

Wrong:

> Tried to deploy but hit an issue. Can you check?

Right:

```
🔴 BLOCKED
Result — staging deploy succeeded; production deploy failed at the secrets-lookup step.
Blocker — prod IAM role missing secrets:GetSecretValue on AUTH_SIGNING_KEY (403 from secretsmanager).
Next — grant the prod deploy role access to the new key, OR rotate the key into the existing accessible bundle; then rerun the prod deploy step.
```

### Relationship to the other principles

- **P2** runs BEFORE work — defines what "done" looks like.

- **P3** runs DURING work — keeps every action traceable to the goal.

- **P4** (this one) runs AFTER work — audits current state vs the goal and reports in a form the user can act on.

Before / during / after. Three checkpoints around every task.

### Origin

Surfaced 2026-04-23. Recurring pattern: task responses end with a sub-step status ("fixed the Redis config") without checking whether the END goal (the original bug) is actually hit. The user is left to ask "so are we done?" or manually run the reproducer. Related pattern: responses that close with "let me know if you want more" instead of telling the user where things stand. Both force the user to do the audit themselves. P4 pushes the audit back where it belongs — my side of the handback — and shapes the output as a decision tool, not a narrative dump.


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

- Append new principles using the template. Update the index and the frontmatter description when you do.
