## Principle 15 — State the error verbatim before classifying

**Rule:** When a failure surfaces — an exception, a log line, a rejected request, a
crash — the exact text is written down and read AS GIVEN before any classification,
grouping, or explanation is attempted. Two errors are never treated as the same
class, the same root cause, or even related, because they happened close together in
time or in the same run. Proximity is not evidence. Relatedness is established only
by matching the errors' own content — same exception type, same failing call, same
stack frame, same error code — never by "it happened right after the other one, so
it's probably the same thing."

**One-line form:** Read the error first, classify it second — never let timing do
the classifying's job.

### When it applies

- Any moment a failure is reported, logged, or pasted in — before it gets summarized,
  bucketed, or folded into an existing hypothesis.

- Debugging sessions where multiple things failed in the same run/window and the
  instinct is to explain them together.

- Writing an error map, a failure class, or a recovery handler (`/error-recon`,
  `/repair`, Heaven's Net class assignment).

- Trigger phrases: "these are probably the same issue", "this is likely related to
  the earlier error", "it's the same bug as before" — said WITHOUT quoting both
  error texts side by side first.

### Failure modes this catches

- **Proximity-as-causation** — error B is assumed to be caused by, or the same class
  as, error A simply because B appeared shortly after A, in the same log block, or
  in the same function call chain. They may be two unrelated failures that happened
  to land close together.

- **Paraphrase drift** — restating an error in your own words ("looks like some kind
  of timeout") loses the exact signal (a specific status code, a specific exception
  name) that would have told two errors apart. A paraphrase can accidentally make two
  different errors LOOK identical.

- **Umbrella grouping** — several distinct verbatim messages get collapsed into one
  label ("connection issue", "failed") before anyone checks whether they actually
  share a cause. See `/error-recon`'s "No umbrella labels" rule — this principle is
  its general form, not specific to error-recon's domain.

- **Silent misclassification carried forward** — once two unrelated errors are
  filed under one class, every future occurrence of either gets treated with the
  other's fix, and the wrong one usually gets missed because the class "already has
  an explanation."

### Check / gate before classifying or explaining an error

1. **Is the verbatim text captured?** — exact message, exception type, stack trace,
   status code, or log line, copied exactly, not summarized. If not captured, capture
   it before doing anything else with it.

2. **If two-or-more errors are being called related, are they being read side by
   side?** — the verbatim text of each, not a memory of what each "was about." If
   they aren't both in front of you right now, the claim of relatedness is a guess.

3. **What in the text itself — not the timing — supports the relation?** Name the
   shared field (same exception class, same failing line, same error code). "They
   happened one after another" is never a valid answer to this question.

### Common invalid patterns

- "This new error is probably from the same thing as the one five minutes ago" →
  invalid without comparing both verbatim texts.

- Summarizing a stack trace as "a null pointer somewhere in rendering" before writing
  down the actual line and exception name → invalid; the summary is allowed only
  after the verbatim capture exists.

- Grouping errors under one fix because they showed up in the same test run →
  invalid; a test run can trip multiple unrelated failures.

### Hard NOs

- Do not classify, group, or explain an error before its verbatim text is captured
  and read.

- Do not call two errors related on the basis of proximity (time, log position, call
  stack adjacency) alone.

- Do not paraphrase an error message in a report, a map entry, or a fix description —
  quote it. (Same rule already stated in `/error-recon` Rule 5 and Hard NOs; this
  principle makes it apply everywhere, not only inside error-recon runs.)

### Origin

The user has repeatedly hit errors getting grouped into the wrong class simply
because they occurred near each other, when reading each error's exact text would
have shown immediately that they were unrelated. Stated 2026-09-18: "errors that
dont belong in the same class get grouped together, simply because the error
happened within proximity and it was assumed related. instead, imagine if it was
stated verbatim and we just read it, it would be a lot easier to classify and
understand the exact response to our action." `/error-recon` already carried the
verbatim rule (Rule 5, Hard NOs) and the "no umbrella labels" / "no anchoring" rules,
but scoped to that skill's error-mapping workflow. This principle generalizes it to
every failure, everywhere, including quick one-off debugging that never invokes
`/error-recon` at all.


`========================================`
