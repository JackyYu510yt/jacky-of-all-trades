## Principle 11 — Pin the cause before the fix

**Rule:** On any unexpected failure, run the debug loop before touching code: observe the actual failure artifact, collect the facts, list 2–4 concrete falsifiable causes, rank them by likelihood, then run ONE cheapest one-variable probe at a time — pre-registering what result confirms and what disproves BEFORE the probe runs — until exactly one cause has positive proof. Only then edit.

**One-line form:** Hypothesis-driven debugging (RCA): rank causes, pre-register one cheap probe, lock the cause, THEN edit.

### The canonical loop

```
THE DEBUG LOOP — hypothesis-driven debugging / root cause analysis
(standard: P11 · full procedure: /repair)

1. Observe            read the actual failure artifact — log, trace, output
2. Collect evidence   list the known FACTS; separate facts from UNKNOWNS
3. Hypothesize        2–4 concrete, falsifiable causes
4. Rank               order by likelihood given the evidence; name the leader
5. Design the test    cheapest probe that isolates ONE variable. Pre-register
                      before running: variable tested / expected result /
                      what result CONFIRMS / what result DISPROVES
6. Run ONE test       one probe at a time — never a shotgun of changes
7. Interpret          compare against the pre-registered predictions;
                      confirm or rule out — only positive evidence locks
8. Update + repeat    update the facts/unknowns ledger, re-rank survivors,
                      loop 5–7 until ONE cause has positive proof
9. Only then edit     no code change before the cause is locked

Running ledger (long investigations): facts · unknowns · leading hypothesis
+ confidence · next highest-value test. In /auto this maps onto the
activity log's DIAGNOSING entries.

Fast path (KISS): cause genuinely obvious on first read (typo, missing
import, wrong variable name) → name cause + fix in one sentence each,
verify, done. First "let me just try this" = past the fast path — run the loop.
```

Pre-registration (step 5) is what makes step 7 honest: the pass/fail meaning of the probe is written down *before* the result exists, so the result can't be rationalized after the fact.

### When it applies

- Any unexpected failure, in any lane — a failing test, a wrong value, a crashed run, a misbehaving page, a regression. If the cause is not locked, the loop is on.

- Mid-build (a prototype part breaks), mid-run (/auto verify fails), mid-analysis (a probe returns something surprising).

- Trigger phrases: "why is this failing?", "debug this", "it's broken", "hypothesis-driven debugging", "root cause analysis", "RCA", "let me just try this", "I'll just change X and see".

### Failure modes this catches

- **Guess-and-edit** — editing code on the first plausible theory. The edit becomes a new variable, evidence is contaminated, and the real cause is now harder to find.

- **Favorite-hypothesis lock-in** — chasing one cause without listing rivals; the actual bug was candidate #3 that never got written down.

- **Shotgun probing** — changing three things at once; whatever happens next proves nothing (no single variable isolated).

- **Post-hoc rationalizing** — running a probe with no pre-registered prediction, then reading whatever came back as support for the favorite theory.

- **Elimination-as-proof** — ruling out three of four candidates and declaring the fourth guilty with no positive evidence of its own.

### Check / gate before editing code

1. **Are 2–4 falsifiable causes written down and ranked?** — one candidate is a hunch, not a differential.

2. **Was the probe pre-registered?** — variable / expected / confirms / disproves stated before the result existed.

3. **Did the probe isolate ONE variable?** — a multi-change probe locks nothing.

4. **Does the surviving cause have POSITIVE proof?** — not just "everything else ruled out."

5. **If claiming the fast path: is the cause genuinely one-read obvious?** — the first "let me just try this" means no.

### Common invalid patterns

- Error appears → immediately edit the line in the traceback → invalid (guess-and-edit; the traceback line is the trigger, not necessarily the cause).

- "It's probably the cookie" → refresh the cookie → worked once → declared fixed → invalid (no isolating probe, no positive proof).

- Change timeout + retries + input file at once, run passes → invalid (three variables; which one fixed it is unknown).

- Probe run first, prediction written after → invalid (post-hoc rationalizing).

### Hard NOs

- Do not edit code before exactly one cause has positive proof (fast path excepted, honestly).

- Do not run a probe without pre-registering what confirms and what disproves.

- Do not change more than one variable per probe.

- Do not treat process of elimination as proof.

- Do not claim the fast path after the first failed "obvious" fix — that failure IS the evidence the cause wasn't obvious.

### Worked examples

**A — The loop, run properly**

Stage 4 image gen returns `no_images_generated` for ~12% of beats.

- ❌ "Probably rate limiting — I'll add a sleep." Edit shipped; failure rate unchanged; now the run is slower AND still broken.

- ✅ Facts: failures cluster on one account; other accounts clean. Causes: (1) cookie expiry on that account, (2) quota hit, (3) content filter. Rank: cookie first (cheapest probe + failures started ~4h after login). Pre-register: "print the session cookie expiry; CONFIRMS if expiry < now; DISPROVES if expiry > now+1h." Probe → expiry was 3h ago → locked. Fix the refresh logic. One probe, one edit.

**B — Fast path, honestly claimed**

`NameError: name 'confg' is not defined` on a line written 2 minutes ago.

- ✅ Typo, visible on first read. Name it, fix it, re-run. Loop not required — and if the re-run still fails, the fast path is over: run the loop.

### Relationship to the other principles

- **`/repair`** — the full 9-step *procedure* this standard compresses (Transform → Hypothesize → Lock → Isolate → RED → GREEN → Integrate → Step 2 → Audit). P11 is the rule that applies everywhere; /repair is the methodology when a repair is the task. Same split as P5 ↔ `/simplify`.

- **P6 (think before coding)** covers assumptions before *new* code; **P11** covers causes before *fix* code. Both forbid running on a silent guess.

- **P1 (test the condition)** — a probe that can't disprove anything is P1's failure mode inside the loop.

- **/auto** — fix mode runs this loop (ranked hypotheses + pre-registered probe before any rotation edit). **/prep** — build/pentest failures route here. **/spec** — a `why:` claiming a cause must name the decisive probe that pinned it.

### Origin

Adopted 2026-08-06. The loop existed only as /repair's internal procedure; outside /repair (mid-build in /prep, fix mode in /auto, ad-hoc debugging) nothing formally forbade guess-and-edit. User asked to codify the observe → evidence → hypothesize → rank → cheapest-test → one-test → interpret → update → only-then-edit sequence as a standing principle, upgraded with pre-registration and the facts/unknowns ledger from a hypothesis-driven-debugging protocol comparison. Matches the existing "Pin the fix, don't guess" memory — this principle is its promoted, enforceable form.


`========================================`
