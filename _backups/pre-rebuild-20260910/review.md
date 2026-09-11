# Review machinery — canonical text (LOADED ONLY WHEN REVIEW.txt READS `full`)

Split out of `SKILL.md` on 2026-08-30. Nothing below was changed.
In `note` and `off` mode this text never enters the context window.
Restoring `full` inline is a straight paste back into `SKILL.md`.

---

### FnReview — per-function completeness review (fresh eyes at completion)

_(Added 2026-08-22 by user directive: "have the guardian occur per function complete and run a separate reviewer that sees if it passes Heaven's principles and is a complete function or fix." Design pinned in `SPEC-function-review.md` v8 (renamed 2026-08-28 from `function-review-SPEC.md` so /spec BIND’s `SPEC-*.md` glob can see it) (CWD of that session); survived 1 AUDITOR + 1 RED-TEAM + 6 REFUTER rounds. Mechanism note: a cron is a clock, not a trigger, and the Goal-Guardian rule is one cron per run — so this is an in-turn subagent dispatch, NOT a second cron. The word **FnReview** is used everywhere — "reviewer" alone already means the blocker-review and the classification reviewer.)_

Every function — and every **function-level fix** — gets checked by a fresh pair of eyes **at the moment it completes**, before its step is DONE (Option B since 2026-08-22: all functions, not just load-bearing ones; reviews fan out in parallel so coverage costs wall-clock, not certainty): (1) does it follow the principles (the sweep's 5 items), and (2) is it **COMPLETE** — a structural fix / whole function, not a band-aid (HI #14): after this code, does the condition that produced the failure still exist? Does it hold next run, different input, no Claude in the loop? Does it ESTABLISH its precondition on any input, or FILTER for inputs that already have it? A VIOLATION / BAND-AID stops the step from going DONE and re-enters fix mode on the step that wrote the code. The periodic principles-sweep stays as the catch-up net; this is per-function and immediate.

**Trigger — at the step's verify PASS, when the step wrote or rewrote ANY function (Option B, user decision 2026-08-22: "I'd rather be super sure than go back and fix stuff"):**

```
(a) wrote or rewrote ANY function — AUTHOR or INLINE, happy path or not (the
    former AUTHOR-only arm is retired; AUTHOR still matters for the author
    sub-agent and for the AUDIT-step executor on /prep runbooks), OR
(b) satisfies the FIX-TRIGGER — kept as its own arm because it changes the
    PACKET (fix items + item 9) and the forced-refuter rule, not just "whether":
      fix-trigger := the step ran in fix mode (rotation, /repair sub-loop,
                     escalation re-dispatch)
                  OR the step REWROTE A DEF THAT EXISTED AT RUN START
                     (its hash differs from the run-start def snapshot —
                      structural, not verb-based: /auto /repair phases run
                      in NORMAL mode, "add retries to upload()" is a rewrite)
    Arm-2 exclusions (KISS): defs whose run-start body is a STUB (pass / ... /
    raise NotImplementedError / docstring-only — completing a scaffold is
    building), and TEST defs (test_* / *_test — a RED rewrite is covered by its
    own verify), and SYMBOL RENAMES — a step whose diff is token-substitution
    only (an identifier / function name replaced everywhere; no statement added,
    removed, or reordered; AND the old token no longer resolves anywhere after
    the step — the def/variable itself was renamed; a swap to a DIFFERENT
    existing symbol is a retarget = rewrite, arm 2 fires) is a non-function
    step even though callers' bodies change: it does not trigger arm 2; the
    decision is made from the step's Edit old/new strings or the logged
    sed/replace expression and recorded on the `Edit applied:` line (disk, not
    memory); afterwards the driver re-baselines the run-start snapshot for the
    touched files and carries affected `clean`/`WAIVED` stamps to the new hash
    `(inherited)`, same as a renamed function's own line. NOT excluded:
    prep-listed functions — a planned rewrite IS a fix.
Never fires for: steps that write no function (config, constants, data moves,
symbol renames, runs of existing code), test defs, standalone-harness defs,
/auto's own bookkeeping. So a Pattern-1 rename/config run dispatches zero
reviews — by the rename exclusion above, not by assertion. Not gated by the
guardian's Jobs: check.
```

**Dispatch shape — parallel per function, non-blocking for independent steps.** The driver names the functions it edits on the `Edit applied: <file>:<fn>` log line at edit time and reads them back at dispatch (fallback: every def in touched files whose hash differs from its reference — the later of the run-start snapshot and its `clean` stamp — else all defs). A step that wrote ONE function gets one dispatch; a step that wrote SEVERAL gets **one reviewer per function, dispatched in parallel** (fan-out rule: concurrency cap ~8–12, each returns a structured per-function verdict, a non-answer is that function's UNRESOLVED only — never the step's). The reviewer still sees the surrounding module, so a tightly-coupled unit may share one dispatch when splitting would hand the reviewer half the logic. While reviews are in flight the step is `VERIFIED (FnReview pending)` and the driver **may start the next step(s) that do not consume the reviewed functions** (no `requires:` on this step, no read of its output — the same independence test fan-out uses); a step that DOES consume them waits — the run never builds the next piece on top of an unreviewed one. A finding on a reviewed function still re-opens the producing step and invalidates any downstream step that consumed it (re-entry hygiene), so nothing built meanwhile survives a real diff unchecked. A finding is **acted on at the next step boundary** (the executing step's verify result is written first), never mid-action; `Current step:` names the executing step and the re-opened step is named in `Mode reason:`. **Step-DONE condition under fan-out:** the step goes DONE only when EVERY function's stamp reads clean / unreviewed / WAIVED; any VIOLATION/BAND-AID on any one function blocks the step; UNRESOLVED functions retry individually (tightened brief), sibling verdicts stand. **Rounds are per STEP, not per function:** one `FnReview dispatch:` log line per step-round listing all its functions (`<fn, fn, …>`), so the ≤2-rounds and ≤6-per-pass checks count lines, not reviewers; round 2 re-dispatches only functions whose stamp is not clean/WAIVED at the current hash. Pattern 3: the fan-out shares the tick's deadline; unreturned functions are carried, not the whole step.

**Timing on /prep-derived runbooks — the FnReview IS the AUDIT step.** RISKY: `N+1 Implement → N+2 REAL → N+3 AUDIT`; SAFE: `N+0 Implement → N+1 AUDIT`. The FnReview fires ONCE as the executor of that AUDIT step (after REAL — production-shaped evidence), and **both triggers are suppressed at every step preceding the function's AUDIT step** (Implement AND REAL), including after a fix-mode redo — the round-2 review fires at AUDIT again after REAL re-runs. The AUDIT step's own check ("traces to goal") is item 0 of the brief; the prep END GOAL / field-13 AUDIT card joins the packet. When the function met the fix-trigger on a preceding step, the AUDIT executor gets the fix packet and item 9 applies. SAFE functions' AUDIT steps are FnReview-executed too (Option B) — their dispatch fires after the smoke check, in parallel with any siblings finishing in the same step. **/repair-derived runbooks (`/auto /repair`, added 2026-08-22):** /repair's step 9 (Audit) IS the executor — `executor: audit-step`, item 0 graded against the Goal/Success line (no END GOAL card), dispatch log token `audit-step` — it runs with the fix packet (failure signature, step-2 hypothesis list + step-3 Lock evidence, rejected approaches), and both triggers are suppressed at steps 4–8 (Isolate through Step 2 — the step-4 standalone holds a copy of the NOT-yet-fixed def, so standalone-harness defs are exempt like test defs and never reviewed). A Mode-B /repair sub-loop inside a /prep step does NOT dispatch at its own step 9 — the function's AUDIT step stays the single executor; if that AUDIT step is already DONE, the rewrite re-opens it (→ PENDING on a real diff) and the review fires there; if the function has no AUDIT step at all (a Phase 9 integration step), the self-derived rule applies — the review attaches to the writing step's verify. Self-derived runbooks (no AUDIT step): the review attaches to the function-write step's verify.

**Lifecycle — a step with a pending FnReview is not DONE.** New named state between IN PROGRESS and DONE, written on the step line:

```
IN PROGRESS → VERIFIED (FnReview pending) → DONE        (review clean)
VERIFIED    → BLOCKED                                    (finding → fix mode on the PRODUCING step)
BLOCKED     → PARKED (FnReview round 2 still open — finding quoted)
PENDING     → PARKED (dependent of step N FnReview PARK)  (AUDIT + any consumer still PENDING;
                                                          reason token `dependent:N`)
```

When the VERIFIED step and the producing step differ (/prep-derived runbooks: AUDIT vs Implement/REAL; /repair-derived: step 9 vs step 7 Integrate), the **producing** step — the one whose `Edit applied: <file>:<fn>` line last wrote the function, never a fixed step number — carries BLOCKED/PARKED and the stamp; the AUDIT step goes → PENDING unconditionally (its verify IS the failed review), REAL/other consumers → PENDING on a real diff of the rewrite (HI #4). Never two BLOCKED steps for one finding. On a round-2 PARK the consumers park with it as dependents (no round 3, no re-run on the band-aid) and un-park together at guardian tick step 8 / refuter door 3.

**Resume / tick pickup of a VERIFIED step — no restore, no redo.** Check each function's current hash against the `sha:` on its `pending` stamp (the cheap intact-proof — not a re-run of a possibly long REAL verify): match → re-dispatch; differs → the step drops to IN PROGRESS and the normal door-2 restore + fix mode apply. Re-entry door 2 does NOT fire on an intact VERIFIED step. A dead-tick / Esc-killed pending is re-dispatched without consuming a round, at most twice (count = `FnReview dispatch:` lines with no `returned:` line); a pending carried without a dispatch (Pattern 3, window too short) is counted from `FnReview carried:` lines — after 2 carries the 3rd tick dispatches regardless of window with a tightened deadline; a timeout there stamps `unreviewed @<ISO> (carried ×2, timeout)` directly (skips retry-once — the tighter bound is the point). Third dead pickup → `unreviewed @<ISO> (dead-tick ×2)`. Bounded — never a wedge until the spend gate.

**The context packet.** Fresh general-purpose subagent, read-only probe license (Read/Glob/Grep; writes forbidden). **Leave `model:` UNSET — this one inherits Opus** (Model routing: adversarial judgment on code; on 2026-08-30 it found a structural fix that deleted 24 lines of machinery a cheaper reviewer had no reason to question). Hand it: Goal + Success line (GOAL.md); each function's contract (name, inputs → outputs, callers); each function's CURRENT code on disk (file + the hasher's line range — the reviewer reads from disk, nothing pasted from memory) + the surrounding module; the step's verify check + PASS evidence; an explicit `executor: audit-step | step-verify` marker; AUDIT-executor only: the END GOAL card + field-13 AUDIT card; **fix-trigger only:** the failure signature, the P11 hypothesis list, and APPROACHES.md (from fix-mode log lines, or from /repair's Hypothesize/Lock steps on a NORMAL-mode repair step); **every packet with no failure signature carries the marker `no failure signature`** (all non-fix dispatches, and fix-trigger ones with none). It does NOT get the driver's opinion, the author's note, or conversation history.

**The brief + fixed checklist:**

```
You did NOT write this code. You are the FnReview. Read each function from
disk. For each function, for each item, return exactly one of CLEAN /
VIOLATION (items 0-5) or COMPLETE / BAND-AID (items 6-9), each WITH
file:line evidence — CLEAN and COMPLETE need a citation too (the line that
satisfies the item). Item 9 may return N/A only when the packet says
`no failure signature`; item 0 may return N/A only when executor is not
audit-step. Use no other severity words. A VIOLATION is a concrete breach,
not a style nitpick. Do not rubber-stamp.

 0. GOAL-TRACE (audit-step executor) — does this function advance the Goal /
    Success line and the prep END GOAL card?
PRINCIPLES (same 5 items as the principles-sweep):
 1. HEAVEN'S NET — RECOVERY keys to evidence-mapped failure classes, never
    "symptom string X → do Y"; unmatched/assumed signals are captured, parked,
    fail loud (canonical: /error-recon). Guardrails: DETECTION may match
    mapped symptoms — it is the recovery that must be class-level; and ≤2
    handlers need no taxonomy (rule of three). Do not flag either.
    1b. PROPORTION (same canonical section) — a recovery that rests/retires
    capacity or pulls a pool sizes its cooldown / bench / share from an
    OBSERVED recovery measurement (cite where) or a bounded ≥×2
    smallest-first ladder; a guessed constant or wrong scope is a
    VIOLATION in either direction (90 s rest for a ~24-min throttle;
    rest-till-midnight on a string that may mean a 60 s limit; N members
    retired for a pool-wide blip). A signal mapped to two entries of
    different size that jumps to the larger (or a bespoke 'both' handler)
    instead of a smallest-first ladder is the same VIOLATION. Bounded
    growing backoff IS the ladder — do not flag it.
    1c. HOLD — a capacity-resting recovery counts only if it HOLDS for the
    hold-window (max of measured recovery / rung used / 15-min floor); cite
    (a) the compare of a re-fire against the stored last-recovery time for
    the same (entry, target) and (b) the counter line — a counter reset on
    verify-pass is the VIOLATION; exit a degraded state on more evidence
    than entering it; pool re-entry staggered.
    1d. CHEAP-FIRST — a lighter discriminating probe runs before the
    consuming action; VIOLATION only when such a probe is already present
    in the code (health/status read) or named in the map entry — else NOTE.
    1e. GIVEN NUMBERS — an environment-supplied magnitude (retry-after,
    quota, ETA, reset boundary) is the first rung, never overridden by a
    constant; a reset boundary is a VIOLATION unless it cites its
    measurement source (map entry / comment).
    Item 1 returns verdicts keyed `1` (class), `1b` (proportion), `1c`
    (hold), `1d` (cheap-first), `1e` (given numbers); a finding filed
    under the wrong key is re-keyed by the DRIVER at mtime validation.
 2. EVIDENCE-ONLY — no success from labels/exit codes alone.
 3. RE-ENTRY HYGIENE — retry/resume rolls back residue → re-asserts the
    precondition → invalidates downstream before redo.
 4. NO SILENCED FAILURES — no bare except/pass, no unbounded retry, failures
    surfaced by count, flight-recorder capture on unknowns.
 5. KISS — no abstraction the task didn't earn.
COMPLETENESS (COMPLETE or BAND-AID, with evidence):
 6. CONDITION TEST — name the condition that produced the failure / the gap
    this function closes. After this code, does that condition STILL EXIST?
    (yes → BAND-AID; name the surviving condition.)
 7. NEXT-RUN TEST — next run, different input, no Claude in the loop, nobody
    watching: does it still work? Cite what in the code makes that true.
 8. ESTABLISH-vs-FILTER — if the function needs a precondition, does it
    ESTABLISH it on any input, or FILTER for inputs that already have it?
    (filter → BAND-AID.)
 9. CAUSE-LOCK (fix-trigger only) — does the fix target the CONFIRMED cause
    from the hypothesis list, or route around the symptom? Was the leading
    hypothesis confirmed by a discriminating probe, or merely not disproved?
    (HI #13)
```

**Verdict handling — bounded at every exit:**

- **Write first, act second.** The `FnReview returned:` log line is written the instant the verdict lands, before any action.
- **Staleness validation.** A finding citing a function whose hash changed after the reviewer read it is discarded with one log line (hash, not file mtime — a neighbour's edit never discards a live finding). Every finding discarded → the dispatch is UNRESOLVED (not CLEAN), consumes one leniency slot, re-runs on current code.
- **Vocabulary is closed.** Any cited item verdict that is not CLEAN/COMPLETE blocks ("CONCERN", "borderline" → VIOLATION/BAND-AID). An uncited item verdict is UNRESOLVED — except a **legal N/A**, which the DRIVER checks against the packet it sent (item 9 ↔ `no failure signature` marker; item 0 ↔ `executor: step-verify`); an N/A that fails the check is UNRESOLVED.
- **Citation re-confirm.** The driver re-reads the cited line (±10). Quoted evidence present → the finding stands (a moved line is corrected in the log, not excused). Evidence absent from the function entirely → that item is UNRESOLVED (retry with "cite the exact line"). Leniency never clears a finding whose quoted evidence IS in the code.
- **VIOLATION / BAND-AID → map to the producing step, then BLOCK it.** Fix mode opens with the finding as the failure signature (P11 list → discriminating probe → approach on the confirmed cause). The function-author escalation re-dispatch is available within the one-author bound. Re-entry hygiene runs first; AUDIT → PENDING unconditionally, REAL/consumers on a real diff.
- **Fresh approach budget per review round + the aim-test gate.** `Approaches tried` resets for the re-opened step (5 per round). Before a re-opened step may re-enter VERIFIED / DONE, the driver runs the HI #14 aim-test on its fix and logs it — `aim-test: <condition> removed? yes — <how> | no` — a `no` (or an item-8 filter the driver can see itself) is a failed approach: rotation continues, no dispatch. Honest bound: **≤2 verify-passing, aim-test-passing attempts per step per guardian pass**, ≤5 approaches each. The aim-test is a cheap self-filter, not independence; the verify stays the oracle for "works", the FnReview for "complete".
- **Bound: max 2 FnReview rounds per step per guardian re-attack round** (mirrors the refuter). Round-2 still VIOLATION/BAND-AID → the producing step is **PARKED**, stamp `open <finding> (round 2) → PARKED @<ISO>`; blocker-review / re-attack owns it (Round K/3). A guardian un-park + redo that passes verify is reviewed **again with a fresh 2-round allowance**; same after a refuter door-3 re-open. Finite: ≤6 review rounds per guardian pass × 4 passes = ≤24 per step, worst case; the ≤6-per-pass check is derived from `FnReview dispatch:` lines since the last Round increment.
- **Open-finding DONE gate.** While any Functions line reads `open …`, `Status: DONE` is not written: the Terminal Refuter fires **even on a machine-checked goal** (the HI #11 override shape; `Refuter: n/a → pending` when forced — the RedTeam precedent — so the Stop-hook carrier holds), with the finding named. Forced brief adds: *"For each named open / unreviewed line return exactly BLOCKER or WAIVED(<citation>); a confirmed BAND-AID (HI #14 aim-test + items 6–9) is a BLOCKER even though the Success line is machine-green."* Silence/CONCERN/NOTE on a named line = UNRESOLVED → retry once → second UNRESOLVED falls to the refuter's same-context skeptic fallback, which must rule BLOCKER(<cited unmet item>) or WAIVED(<citation>) — never a BLOCKER without a named item, never a mute subagent turning a green goal into STUCK-user. Blocker-review's FALSE-BLOCKER is not a waiver — only a cited WAIVED closes an open finding.
- **WAIVED exit.** A finding that contradicts a recorded Design Decision in notes.md (or a recorded /prep spec-card decision), or a user-requested `BAND-AID (user-requested):`, is closed `WAIVED @<ISO> (<citation>)` by the driver, blocker-review, or the refuter; counts as resolved; lands in Open Questions. Waiving requires a citation — never "reviewer was wrong".
- **Never a user gate.** Passes silently or re-enters fix mode within the bound; surfaces only in the log, the stamps, and the final report.

**Evidence rules — leniency for a dead dispatch, never for a verdict.** UNRESOLVED = no citations, all findings hash-discarded, errored dispatch, or timeout (a legal N/A is NOT unresolved). Any UNRESOLVED → retry once per UNRESOLVED function (tightened brief; returned sibling verdicts stand) → second UNRESOLVED → that function is `unreviewed @<ISO> (<reason>)`, one log line, and the step proceeds DONE once every function is clean / unreviewed / WAIVED — the FnReview is a second net, not the oracle (same leniency the classification reviewer has). The leniency NEVER extends to a cited VIOLATION/BAND-AID. An `unreviewed` stamp is not forgotten: the sweep still covers that function, the refuter is told, and on a **fix-trigger** function an `unreviewed` stamp forces the refuter even on a machine-checked goal — the user's headline case (a fix) always gets one independent look on every run shape. Honest residual: an `unreviewed` happy-path function on an inline machine-checked run gets no further look (status quo). Pattern 3: reviewer deadline SHORTER than the tick interval; the interval is sized **at runbook generation for author + review + sweep + Navigator combined**; a dispatch that can't fit the remaining window stays `pending` and is carried (log `FnReview carried:`) — never straddles the tick.

**State — on paper, compaction-proof.** Per-function review state rides on the runbook **Functions block** line. **Non-build runs** have no block today — the first step that writes or rewrites any def **creates it** (write-time checklist label; rewritten defs tagged `(fix)`); the write-time checklist runs on every new def on every run shape (the one-shot classification *reviewer* stays build-only; `Classified: n/a` on non-build runs). An AUTHOR label earned on a non-build run also triggers the function-author dispatch under the one-author bound, and **any author dispatch for a fix-trigger def carries the fix items** (failure signature, hypothesis list, APPROACHES.md) at write time, not only on escalation.

**Run-start def snapshot.** Before the FIRST edit to any deliverable file in the run, record that file's per-def hashes (the hasher below, no other) in PROGRESS.md (create it if the run shape has none — every run has it under the Goal-Guardian rules) (`snapshot: <file> <fn> sha:<8> …`) — the reference for arm 2 and the fallback; a def absent from it is new code. PROGRESS.md already carries long-lived sections (baseline, mirrors); snapshot + FnReview ledger join them as named sections that every tick's PROGRESS write **section-merges, never overwrites**.

**The hasher (one procedure, same result on every tick):** `.py` — slice the source lines EXPLICITLY from `min(d.lineno for d in node.decorator_list)` (or `node.lineno` with no decorators) through `node.end_lineno` of the `ast` FunctionDef/AsyncFunctionDef — NOT `ast.get_source_segment(node)`, which on Python ≥3.8 starts at the `def` line and silently drops decorators (verified 2026-08-22 on 3.11) — replace the **def-line name token only** with `_` (recursive self-calls unmasked — a recursive rename reads stale, accepted as conservative), normalise line endings, strip TRAILING whitespace only (never indentation — a dedent changes control flow), sha256 → first 8 hex. Non-Python deliverables: whole-file hash, file treated as ONE unit (coarser, never wrong; accepted residual: a neighbour's edit there does invalidate). Removing `@retry` or changing a default arg invalidates a stamp; a rename or a neighbour's edit does not. "Edited after the stamp" is decided from disk — file mtime as the cheap pre-check, hash difference as the verdict (HI #8) — never from this run's log (it cannot see a human's or another run's edits).

Stamp vocabulary (closed; the round count lives on the stamp):

```
review: n/a
review: pending (round k) sha:<8>               ← in flight / carried; sha = hash at the instant the stamp
                                                  is written (step verify PASS; AUDIT-step entry on /prep; step-9 entry on /repair)
review: clean sha:<8> @<ISO> [(item 9 n/a)]
review: round k VIOLATION item n → fix mode     ← finding mapped, producing step BLOCKED
review: open <finding> (round 2) → PARKED @<ISO> ← DONE gate until WAIVED/cleared
review: unreviewed @<ISO> (<reason>)
review: WAIVED sha:<8> @<ISO> (<citation>)

Functions:
  fetch_clip:    AUTHOR — disk I/O | review: clean sha:3f9a1c2e @2026-08-22T03:40Z
  retry_upload:  AUTHOR — retries  | review: open BAND-AID item 8 (round 2) → PARKED @...
  join_paths:    INLINE — all NO   | review: n/a
  parse_flags:   INLINE (fix)      | review: clean sha:… @... (item 9 n/a)
  fetch_video:   AUTHOR — renamed from fetch_clip @... | review: clean sha:… @... (inherited)
```

Status-block summary field: `FnReview: n/a | <k> pending | <n> in fix | clean | <n> open | <m> unreviewed`. A function rewritten after a `clean` stamp gets `pending` at its next verify PASS (review is per completion, not once per name); a renamed function carries its stamp (`renamed from X`, hash still matches); a function with no stamp is reported to the refuter like `unreviewed`. FnReview rulings live in their **own ledger keyed (item, file, function)** mirrored to PROGRESS.md — NOT in the sweep's (item, file) ledger (a file-keyed entry would blind the sweep for every other function in that file).

Log lines (model-written, mirroring the author lines):

```
[ts] [Mode] [Step N] FnReview dispatch: <fn, fn, …> (trigger: new-def|author-classed|promoted|fix-mode|rewrite-existing|audit-step; round k)   ← ONE line per step-round, all functions listed
[ts] [Mode] [Step N] FnReview returned: <fn>: CLEAN+COMPLETE | VIOLATION item k file:line | BAND-AID item k <condition> → <DONE | fix mode on step M | PARKED | unreviewed>
[ts] [Mode] [Step N] FnReview carried: <fn> (window too short; carry 1|2)
```

**Interplay with the principles-sweep.** The sweep is unchanged in cadence and becomes the catch-up net (non-function edits, `unreviewed` functions, anything a stale `clean` no longer covers). The DRIVER (which has the hasher — the sweep subagent does not) recomputes each stamped function's hash at dispatch and passes ONLY the still-valid ranges as `reviewed-clean ranges: <fn> L<a>–<b> @<ISO>` (the range IS the hasher's slice); the sweep does not flag inside those. Inside a tick the step-7 sweep rider dispatches AFTER the step's FnReview has returned and written its ledger entries — "alongside" reads as same-tick, sequenced. The sweep's 5-step cap is unchanged; FnReview-driven fix-mode re-entries do NOT count against it.

**Interplay with the Terminal Refuter Gate — unchanged sequence, two forced-fire triggers, better informed.** (0) A **universal pre-DONE pending check** on EVERY DONE path (inline end-of-run, guardian SUCCESS PROBE in tick step 5, the machine-checked skip path) BEFORE "When it fires" / HI #9: no step in `[VERIFIED — FnReview pending]`, no `FnReview: k pending` or `n in fix`; if any holds, the carried review is dispatched and returned first. A finding at that check discards the "Met" verdict and falls to tick step 7 (fix mode on the producing step) — never step 8, so it never burns a guardian Round; an `in fix` carried from a prior tick routes the same way. PARKED steps are allowed (the all-parked checkpoint is untouched); an `open`-PARKED line is the forced refuter's INPUT. (i) An `open` finding or a fix-trigger `unreviewed` stamp forces the refuter even on a machine-checked goal. (ii) At gate entry the driver hands the refuter the Functions block and names every `open`, `unreviewed`, no-stamp, WAIVED line and every function whose current hash differs from its `clean` sha — "not independently reviewed, look there first". A stale `clean` must never read as coverage. Residual: on a machine-checked goal with nothing forcing the refuter, an out-of-run edit after a `clean` stamp is named to a refuter that never fires (status quo).

**Re-entry hygiene — door 5.** A FnReview finding re-opens a step whose verify passed: the standard restore runs on the producing step (rollback → pre-verify → invalidate downstream on a real diff; AUDIT → PENDING unconditionally).

**Cost + KISS bounds (P5):** one reviewer per function, dispatched in parallel within a step; ≤2 rounds per step per pass; a 40-function build = ≥40 reviews, but wall-clock ≈ the slowest single review per step because they run side by side (user's call 2026-08-22: certainty over dispatch count). No panels, no voting, no tournaments. No review for non-function steps, test/harness defs, or trivial runs. The checklist is the sweep's 5 items + goal-trace + 4 completeness items — not a new taxonomy. Sub-agents unavailable → same-context skeptic pass marked as the weaker fallback, exactly like the refuter's.




---

## Terminal Refuter Gate — independent DONE check

Before /auto writes `Status: DONE`, one fresh agent tries to prove it is NOT done. This is the **independent upgrade** of the same-context "AUDIT vs END GOAL" step: the brain that did the work shares every blind spot that produced it, so it is the wrong brain to clear it. Empirically, a model grading its own output is unreliable (intrinsic self-correction often fails to improve and can degrade), and self-preference bias bites hardest exactly when the work is weakest — the worst time to be blind. An independent verifier is the documented fix, and verification is the cheap side of the generator-verifier gap.

### When it fires

Only when "done" is a **judgment call**. If the runbook's success line is a deterministic machine check that already passed (`pytest` exits 0, checksum matches, file exists at expected size), **SKIP** the refuter — that verify check IS the independent oracle, and self-preference can't bias a green test. Fire it when success is judgment-shaped: "pipeline handles real input", "output looks right", "report is complete", "no regressions in adjacent features". **Before this rule is consulted, on every DONE path (inline end, guardian SUCCESS PROBE, the skip path): the FnReview pending check** — no step `VERIFIED (FnReview pending)`, no `FnReview: k pending / n in fix`; a carried review is dispatched and returned first. **Two FnReview carve-outs override the SKIP:** a Functions line reading `open …` (a round-2 VIOLATION/BAND-AID that parked) or a fix-trigger function stamped `unreviewed` forces the refuter even on a machine-checked goal — `Refuter: n/a → pending` (the RedTeam precedent, so the Stop-hook carrier holds). See FnReview "Interplay with the Terminal Refuter Gate".

The **RED-TEAM rider** (below) has its own, independent firing rule: it fires on the deliverable's NATURE — unattended, long-running, stateful, or concurrent — even when the refuter is skipped. A green deterministic test proves the happy path ran once; it says nothing about credits dying mid-write, a flag flipping between check and act, or a half-written folder on re-entry. Machine-checked goal + unattended deliverable ⇒ refuter skipped (barring the FnReview carve-outs), RED-TEAM still fires alone (the runbook `RedTeam:` field carries the obligation).

### Sequence (refute first, flip second)

```
1. All runbook steps verified PASS   (necessary, NOT sufficient for DONE;
   PARKED steps allowed per the all-parked checkpoint) AND no step in
   VERIFIED (FnReview pending), no FnReview: k pending / n in fix —
   dispatch any carried FnReview first (an `open` PARKED line is the
   forced refuter's INPUT, not an entry block)
2. → set runbook Refuter: pending (and RedTeam: pending when the rider
   applies), dispatch refuter + RED-TEAM in parallel   (Status still NOT DONE)
3a. refuter clean AND RedTeam clean/n/a → set fields → write Status: DONE
                          → emit AUTO DONE
3b. refuter BLOCKER or RedTeam BREAKS   → record in the owning field →
                          keep Status non-DONE, re-enter fix mode on the
                          unmet item
```

Running the refuter AFTER flipping Status would release the Stop hook (see auto-stop enforcement + Hard Invariant #9) and the run couldn't re-enter cleanly. Refute first, flip second — and the `Refuter:` field carries this in the runbook so it survives compaction.

### The refuter brief

Dispatch a fresh sub-agent (`Agent` tool, subagent_type `general-purpose`) — the same machinery /audit and /prep use. **Leave `model:` UNSET — the refuter and the RED-TEAM inherit Opus** (Model routing: these are the two that find what nobody thought to look for; on 2026-08-30 the refuter caught a substring replace matching the PREFIX of an already-marked line). Hand it ONLY:

- the **frozen Success line + per-step verify checks** (the yardstick — nothing else),
- the observable artifacts produced,
- a **baseline "before" reference if one exists** (git HEAD, a pre-change snapshot, the prior output dir) — part of the yardstick, so the refuter can diff the deliverables against it and flag unexplained or out-of-scope changes; greenfield builds have no baseline, so don't fabricate one (added 2026-06-14),
- the Implementation Notes Design Decisions / Deviations cards (so it refutes against intent, not re-litigating settled forks),
- the runbook **Functions block** (FnReview coverage hand-over): name explicitly every `open`, `unreviewed`, no-stamp and WAIVED line, and every function whose current hash differs from its `clean` stamp's sha — "these were not independently reviewed; look there first". A stale `clean` must never read as coverage. When the refuter was FORCED by an `open` line or a fix-trigger `unreviewed` stamp on a machine-checked goal, add: *"For each named open / unreviewed line return exactly BLOCKER or WAIVED(<citation>); a confirmed BAND-AID (HI #14 aim-test + FnReview items 6–9) is a BLOCKER even though the Success line is machine-green."* Silence / CONCERN / NOTE on a named line = UNRESOLVED → retry once → then the same-context skeptic fallback below must rule BLOCKER(<cited unmet item>) or WAIVED(<citation>) — never a BLOCKER without a named item.

Brief: *"You are the REFUTER. The work below claims to be DONE. Prove it is NOT — find a specific Success-line item or verify check that is unmet. Read the artifacts yourself. Return ranked findings BLOCKER / CONCERN / NOTE, each with evidence. A BLOCKER is a concrete unmet success criterion, not a nitpick. Default to finding holes; do not rubber-stamp."* (If /repair is in the chain, add: *"A real fix holds on a different input with no Claude present — does it?"* per the structural-fix rule.) When the claimed DONE rests on a diagnosis or judgment call, add: *"Were the relevant alternative explanations investigated or explicitly ruled out, or was the first hypothesis merely confirmed?"* (HI #13). When the deliverable contains recovery/error-handling code, add: *"Is any handler keyed to a symptom string instead of an evidence-mapped failure class, does any path act on an assumed/unproven signal, or is any capacity-resting recovery SIZED (cooldown / bench / scope) from a guessed constant instead of an observed measurement or a bounded smallest-first ladder? Does any recovery declare success on a verify that didn't HOLD (same recovery re-firing inside the hold-window with counters reset), skip a lighter probe that exists, or override an environment-given magnitude with a constant? (Heaven's Net — canonical in /error-recon.) Any of these is a BLOCKER."*

### RED-TEAM rider — unattended / stateful deliverables

When the deliverable will run unattended or holds state across runs (a pipeline, a cron job, a helper daemon, fallback/routing logic, a queue — anything no human watches per-step), dispatch a SECOND fresh agent in parallel with the refuter: the **RED-TEAM**. Its canonical brief lives in `~/.claude/skills/audit/SKILL.md` under the heading "**The brief handed to the RED-TEAM**" — read it there at dispatch time and hand it the actual artifact paths (code, runbook, logs). It generates concrete hostile scenarios across 10 attack categories (mid-op death, check-then-act races, half-done re-entry, flapping, two actors, boundaries, time windows, recovery-fails, poison pill, lying success) and walks each through the real code to HANDLED / DEGRADES / BREAKS / UNKNOWN.

- **Fires on the deliverable's nature — or on ≥1 guardian tick having fired** (proof the run ran unattended in practice; never on mere guardian armament) — see "When it fires." It runs even when the refuter is skipped; the runbook `RedTeam:` field carries the obligation across compaction exactly like `Refuter:` (pending → clean before `Status: DONE`; a guardian tick that fires while `RedTeam: n/a` flips it to `pending`).

- **BREAKS = BLOCKER** → re-enter fix mode on the owning step (Re-entry hygiene applies). **DEGRADES, and UNKNOWN on a load-bearing scenario,** = CONCERN → logged to the Notes file's Open Questions; does not block DONE.

- **Shares the max-2-rounds bound** with the refuter — see "Bound."

- **Internal, not a user gate** — same rule as the refuter; it passes silently or auto-re-enters fix mode within the bound.

### Verdict handling — severity-gated

- **BLOCKER** (maps to a specific unmet Success item / failed verify) → re-enter fix mode on that item (Re-entry hygiene: map it to its owning step(s) and restore each before redo). ONLY a BLOCKER re-opens /auto.

- **CONCERN / NOTE** → logged to the Notes file's Open Questions. Does NOT block DONE.

### Bound (so it can never loop forever)

Max **2 refute rounds** per re-attack round — a round is any terminal-gate dispatch (refuter and/or RED-TEAM together count as ONE round). On the 2nd round still BLOCKER (or RED-TEAM BREAKS) → emit **AUTO PARTIAL (checkpoint)** listing the open holes — the guardian's next re-attack round owns them (within the 3-round guardian cap, whose exhaustion → STUCK-user). Never silently loop; never silently DONE; never treat the refute bound as a final ending while the guardian lives.

### Review budget — the per-gate caps MULTIPLY; this is the global one

_(Added 2026-08-30 by user directive, after a run spent five reviewer rounds.
Every round found real defects, so this is NOT a licence to skip a gate that is
still finding things. The waste is structural: every cap in this skill is PER
GATE, and per-gate caps multiply — FnReview ×2, refuter ×2, RED-TEAM, plus a
plan-stage AUDITOR and RED-TEAM, is 7 dispatches before anyone counts them.)_

**Two merge rules were drafted here and DELETED the same day, on evidence.** They
said: dispatch ONE plan-stage reviewer instead of AUDITOR + RED-TEAM, and merge
FnReview with the Terminal Refuter when they read the same file. Both were reasoned
from COST, and the run that produced this section disproves both:

```
plan-stage AUDITOR      the write-only index; a FALSE evidence claim of the
                        author's; drop the SPEC.md branch (killed 5 later defects)
plan-stage RED-TEAM     MEASURED 27% concurrent append loss, and MEASURED the fix
                        at 312/312 — the number the entire final design rests on
        overlap: effectively none. The AUDITOR verified CLAIMS; the RED-TEAM ran
        EXPERIMENTS. Merging them would have risked losing the measurement.

FnReview round 2        found the STRUCTURAL fix (move the mutex off byte 0)
Refuter round 2         found a substring replace matching an already-marked line
        overlap: none. Two focused briefs went deep in different directions; one
        merged brief would likely have gone shallow in both.
```

**Do not re-add them without new evidence.** Two independent adversarial looks at
one artifact are not redundancy — the second one is where half the real defects
came from. Cut the MODEL (see Model routing), not the LOOK.

What survives is one rule:

**A GLOBAL cap of 6 reviewer dispatches per run**, counted across every gate
   (classification, FnReview, principles-sweep, blocker-review, refuter,
   RED-TEAM). At the cap: finish the round in flight, then STOP DISPATCHING and
   report what is still open. A 7th reviewer is not more safety — it is the run
   refusing to hand a decision back to the user.

**What does NOT change:** a gate still returning real BLOCKERs is still right to
run, up to the cap. This bound exists so the run reports honestly at the ceiling
instead of grinding — the same shape as the 5-approach bound, applied to reviewers.

### Not a user-facing gate

The refuter is internal — it passes silently or auto-re-enters fix mode within the bound. It never asks the user "I found holes, keep going?" (that would violate no-gates / "invocation is authorization"). It only surfaces at the terminal PARTIAL/STUCK verdict.

### Fallback

If sub-agents are unavailable, run a same-context skeptic pass against the Success line and mark it explicitly as a **same-context fallback** — weaker, since the whole point is independence.


