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
