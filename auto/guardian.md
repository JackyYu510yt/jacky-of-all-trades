# Goal-Guardian — canonical text (LOADED ONLY WHEN THE SWITCH IS `on`)

This file was split out of `SKILL.md` on 2026-08-30. Nothing in it was changed.
It is read ONLY when `GUARDIAN.txt` in this folder reads `on`. While the switch
is `off` this text never enters the context window — that is the point of the split.

Restoring it inline is a straight paste back above `## Hard NOs` in `SKILL.md`.

---

## Goal-Guardian — the run outlives the turn (universal)

_(Added 2026-08-15 by user directive after 9 of the last 25 runs orphaned at PARTIAL. Design pinned in `prep-goal-guardian.txt` v4; survived three independent AUDITOR/RED-TEAM rounds. This section is CANONICAL — where older text conflicts, this wins.)_

The guardian is one in-session cron per run that refuses to stand down until the run's **pinned contract** is observably satisfied (DONE) or the run is genuinely blocked on something only the user can supply (STUCK-user). PARTIAL is a **checkpoint, never an ending**.

**Session-lifetime honesty (verified 2026-08-15):** CronCreate jobs are session-only — in-memory, they fire prompts as new TURNS into THIS session while its REPL is idle, they die when the window closes, and they auto-expire after 7 days. The guardian therefore lives exactly as long as the window does. Keep the window open and it pushes all night; close it and the run waits for `/auto resume slug=<slug>`. The old claim that a cron "survives the chat closing" was false and is retired.

### The pinned contract (contract-pin)

A stated goal is a headline, not a contract. Before autonomy starts, expand the invocation into a contract, frozen in `./auto-runs/<slug>/GOAL.md` (write-once, atomic):

```
Goal:          <one observable sentence>
Success:       <checkable bar — the user's outcome, not machinery>
Circumstances: <what makes it COUNT: free / local / unattended /
                deadline / quality floor>
Never-do:      <moves that are cheating even if they "work" —
                paid APIs in a free tool, deleting sources,
                asking a human mid-run>
Validation:    <type-aware probes for the deliverable + any
                FULL-RERUN flags for specific deliverables>
False-pass:    <what a passing check would look like while the
                goal is still unmet>
Run-start:     <ISO timestamp — the provenance anchor>
```

- **Ask once, only when genuinely ambiguous.** Derive from the invocation + context. If two materially different readings survive, ask the user ONE startup question (this is a startup gate, allowed). Then the engine runs blind — never a mid-run question. Log the decision either way: readings considered + which fired, or `readings considered: 1`.
- The arming one-liner prints the contract summary — the user's veto point for a wrong pin.
- **Frozen means frozen.** Steps change; the contract never does. A wrong contract surfaces at STUCK-user and is fixed by the user restating the goal — never by the run editing GOAL.md.

### Lazy arming (guardian-arm)

**The invariant: nothing pauses unfinished unguarded.** Arm at the FIRST moment the run would end a turn non-terminal (it coincides with the checkpoint flip-back moment below). Runs that reach DONE inline never arm — zero overhead on trivial tasks.

- `CronCreate` one recurring job, off-minute, prompt PINNED verbatim: `/auto guardian slug=<slug> run=<ABSOLUTE run-folder path>` — the `/auto` trigger reloads this skill after compaction; the absolute path defeats cwd drift.
- Interval: adaptive — ~2× the longest expected step, **floor 10 min** (guardian ticks cost a subagent-capable turn; the Pattern 3 1-2 min band does not apply), 30-60 min for overnight renders.
- Record `armed:`/`expires:` dates + cron id in the runbook `Guardian:` field, mirrored to PROGRESS.md. Print: `[auto] Guardian armed (every N min, expires <date>) — lives in this window; keep it open.`
- **Near-expiry rotation overrides idempotency:** cron present but <24h to expiry → CronCreate the replacement → update cron-id + expires in BOTH files → CronDelete the old id. Rotation-create fails → retry next tick, one log line, never fatal while the old cron lives. Cron present and >24h out → no-op. Cron missing → recreate. This liveness check runs on EVERY /auto activity in the session (any turn type, via the HI #8 re-read), not just ticks.
- **CronCreate fails at first arming** → log one line, cap the report's Confidence at HIGH with that reason, and the run may NOT checkpoint: it drives to a terminal in-turn or goes STUCK-user. An unarmed checkpoint is an orphan — the exact disease this section cures.
- The guardian SUBSUMES the Pattern 3 execution cron: **one cron per run, ever.**

### Universal state files (every run, every pattern)

_(Layout only — every artifact's READ TRIGGER is defined once in the canonical
ARTIFACT LEDGER (Pattern 3 section). Where this list and the ledger disagree, the
ledger wins.)_

```
./auto-runs/<slug>/GOAL.md           the contract (write-once)
./auto-runs/<slug>/runbook.txt|RUNBOOK.md  + new Status fields:
     Guardian:  armed <cron-id>, every N min, expires <date>
                | unarmed | stood-down (<reason>)
     Contract:  pinned <date> | pinned+asked
     Round:     K/3 re-attack rounds used
     Jobs:      <id/PID + artifact path + expected duration>
                per live background job (registered at launch)
     Reviewer:  n/a | pending | <last verdict>
     Navigator: n/a | <verdict> @<ISO> — <one-line reasoning>
     Principles: n/a | pending @<ISO> | clean @<ISO>
                | unswept @<ISO> (<reason>) | <n> violations
     FnReview:  n/a | <k> pending | <n> in fix | clean | <n> open
                | <m> unreviewed   (per-function stamps live on the
                Functions block lines — see FnReview)
     Turn-end rule: checkpoint = Status: PARTIAL (checkpoint);
                STUCK only when user-blocked
./auto-runs/<slug>/BOARD.md          chronological milestone/phase board
     — rewritten on every phase transition, reprinted in every
     checkpoint report (see The Board)
./auto-runs/<slug>/APPROACHES.md     append-only approach history
./auto-runs/<slug>/PROGRESS.md       last-tick summary + deliverable
     artifact BASELINE (paths/sizes/mtimes at arming) + MIRRORS of
     Round / cron-id / blocker-since / last Navigator verdict
     (rebuild-proof) + the FnReview
     run-start def SNAPSHOT + (item, file, function) LEDGER — named
     sections every tick SECTION-MERGES, never overwrites
./auto-runs/<slug>/DIGEST.md         the compact area — a bounded one-page
     running brief (target ≤ ~25 lines, HARD CAP 40 — over the cap the
     driver prunes oldest/least-significant lines before writing):
     SIGNIFICANT FINDINGS / NEW IMPLEMENTATIONS / ERRORS SEEN /
     TRAJECTORY. The DRIVER rewrites it every tick from the Navigator's
     DIGEST-DELTA (atomic temp+rename); pruned for significance, never
     append-only — log.txt and APPROACHES.md stay the complete records.
     DIGEST is CONTEXT, never EVIDENCE (tick step 4.6). Corrupt or
     missing → recreate an empty skeleton, one log line (it is a brief,
     never a contract — nothing stands down over it).
./auto-runs/<slug>/spend-<YYYY-MM-DD>.txt  per-slug tick counter
```

The `Turn-end rule` line is not decoration — it is the compaction-proof carrier of the checkpoint protocol (the file, not this skill text, is what every turn re-reads). **ALL state files use atomic temp+rename writes** — load-bearing twice over: a truncated runbook breaks the next tick AND trips the Stop hook's fail-open path.

### The tick protocol (guardian-tick) — strict order

A tick is a cron-fired turn in this same session. Its prompt re-invokes /auto in guardian mode for one slug. Steps, in order:

```
1. SPEND GATE — read/increment ./auto-runs/<slug>/spend-<today>.txt
   (~30 ticks/day per run). Over cap → one pause note, checkpoint-
   exit. Two consecutive counter WRITE failures → STUCK-user (disk
   trouble is a real blocker). Resets at date rollover.
2. RE-READ + LIVENESS — GOAL.md + runbook + the FULL log +
   PROGRESS.md + DIGEST.md (HI #8; files beat memory). Guardian liveness /
   near-expiry rotation (above). Corrupt GOAL.md → stand down +
   STUCK-user naming the corruption (never improvise a contract).
   Corrupt runbook → rebuild steps from GOAL.md + the full log; Round /
   cron-id / since restored from the PROGRESS.md mirrors; the
   contract is never re-derived. Slug folder missing but auto-runs/
   root present → stand down (CronDelete + one line).
3. TERMINAL CHECK — Status DONE / STUCK-user / STUCK (stopped by
   user) → CronDelete (recorded id; fallback: resolve by name
   auto_guardian_<slug>) → exit.
4. OWN-JOBS CHECK (before ANY DONE path) — read the Jobs: field
   (never conversation memory). Any job alive → NO success probe,
   NO reviewer-step execution this tick.
     alive + artifact growing → noop tick (one log line)…
       …but past ~10× expected duration → dispatch blocker-review
       even while growing (no immortal healthy-noop).
     alive + flat → the ~2× stall clock governs (visual checkpoint
       on visual steps); only an expired clock escalates (kill/
       drain per heuristic #13). Task-alive OUTRANKS artifact-flat.
4.6 NAVIGATOR — every tick (analyze-then-recommend; added 2026-08-24
   by user directive). SKIPPED (one log line) while Reviewer: reads
   pending — the stuck ruling in flight owns the analysis; a pending
   with no returned verdict after one full tick interval is a
   timed-out dispatch (blocker-review's UNRESOLVED path). Otherwise
   dispatch ONE fresh general-purpose subagent **with `model: "sonnet"`**
   (Model routing: this is the highest-volume dispatch in the skill —
   it fires EVERY tick, and its job is reading files and reporting what
   they say) with a read-only
   probe license and: GOAL.md, runbook, APPROACHES.md, PROGRESS.md,
   DIGEST.md, log tail (~50), and the deliverable/artifact paths.
   DIGEST is CONTEXT, never EVIDENCE: every claim below must cite
   primary disk sources (log lines, artifacts, runbook state); a
   digest claim contradicted by disk is corrected in this tick's
   DIGEST-DELTA, never propagated. The Navigator returns four parts:
     HAPPENED      what the evidence says just occurred — citations
                   from disk, never the run's testimony
     VERDICT       GOAL-MET | CONTINUE (wait) | NEXT-ACTION |
                   STALL-SUSPECT | BLOCKED-machine | BLOCKED-user
     NEXT          the ONE most logical action toward the frozen
                   Success line
     DIGEST-DELTA  the updated compact-area content
   Driver: write DIGEST.md + the runbook Navigator: field (mirrored
   to PROGRESS.md) FIRST — a failed write is one log line, never a
   wedge — then route the verdict. 4.6 EXECUTES NOTHING; the ladder
   below stays the only executor, so its gates and riders (success
   probe, FnReview, principles-sweep, Round) can be neither starved
   nor doubled:
     GOAL-MET      decides nothing by itself — step 5's machine
                   probes + the Terminal Refuter rule as written.
     CONTINUE (wait) / STALL-SUSPECT — advisory input to steps 4/6's
                   own clocks and conditions; never a bypass of them.
     BLOCKED-machine / BLOCKED-user — advisory: recorded in the
                   Navigator: field + digest. Step 8 enters ONLY on
                   its own condition (no runnable step); a Navigator
                   verdict NEVER increments Round.
     NEXT-ACTION   validated by the constraint compass, then handed
                   to step 7 as the tick's ONE action — the pick
                   SUBSTITUTES for "the next pending step" and runs
                   AS step 7, so step-7's riders (FnReview,
                   principles-sweep, re-entry hygiene) bind
                   unchanged and the owning step's rollback/doors
                   own any residue. BEFORE it runs, the driver books
                   it: append to APPROACHES.md (action + tick;
                   outcome APPENDED as a follow-up line after verify
                   — append-only preserved) and, when it deviates
                   from the runbook's next pending step, a
                   Deviations entry in notes.md — booked before
                   execution so a mid-action death leaves recorded
                   intent and the compass no-repeat check sees it
                   next tick. A NEXT targeting a PARKED step is
                   never executed at step 7 and never forces step-8
                   entry — un-parking remains exclusively step 8's
                   business, entered only on step 8's own condition
                   (Round++, stuck packet, 4th re-entry door live
                   there). A NEXT with no pending step to substitute
                   for (all steps DONE/PARKED) is advisory only —
                   dropped with one log line; step 8 runs on its own
                   condition. A compass REJECTION is logged (one
                   line) and the plain ladder runs — rejections
                   NEVER consume the executing step's 5-approach
                   budget (that budget counts the run's own
                   attempts, not a reviewer's proposals; see the
                   compass carve-out).
   Bounds + degradation (the guardian never DEPENDS on the
   Navigator): a verdict with no citations = UNRESOLVED → retry
   once (tightened brief) → this tick runs the plain ladder (steps
   5–9 as written). Deadline SHORTER than the tick interval (same
   rule as FnReview dispatches); a dead or late dispatch = one log
   line + plain ladder, never a wedge. The spend gate (~30
   ticks/day) is the cost cap — no new counter. Jobs alive (step
   4): the Navigator still fires for analysis + digest, but step
   4's no-success-probe / no-reviewer-execution rule binds whatever
   it recommends. Subagents unavailable → same-context skeptic
   pass, explicitly marked as the weaker fallback.
5. SUCCESS PROBE — validate vs the contract (type-aware floor +
   PROVENANCE: deliverable must postdate Run-start; the arming
   baseline corroborates, run-start decides; consult False-pass).
   Met → [FnReview pending check: any step VERIFIED-pending, or
   FnReview: k pending / n in fix → dispatch + return the carried
   review FIRST; a finding discards "Met" and falls to step 7, never
   step 8] → Terminal Refuter Gate / RED-TEAM per their rules
   (an `open` FnReview line or a fix-trigger `unreviewed` stamp
   forces the refuter even on a machine-checked goal) → DONE →
   CronDelete.
6. SUSPECT — no own jobs, artifact flat → mark SUSPECT (any growth
   tick clears it). SECOND consecutive flat tick → blocker-review.
7. PENDING STEPS — runbook has runnable steps → execute the next
   one normally (re-entry hygiene on redo). A VERIFIED (FnReview
   pending) step whose review is carried or in flight does not
   occupy the tick — run the next step that does not consume its
   functions; the review is dispatched/collected in the same tick
   when the window allows.
   Principles-sweep rider (step-7 ticks ONLY; never while Reviewer:
   is pending): every 3rd tick (today's spend counter divisible by
   3), if DELIVERABLE edits landed since the last sweep's ISO stamp
   (log entries after the stamp showing Edit/Write/mutating Bash on
   files OUTSIDE auto-runs/), dispatch the principles-sweep (below)
   alongside normal execution. `Principles: pending @<ISO>` enforces
   one sweep at a time — but a pending stamp older than one sweep
   window (~3 ticks), or found on resume, is STALE: set
   `unswept @<ISO> (stale)`, one log line, eligible to re-dispatch.
8. DRY/PARKED/BLOCKED → increment Round FIRST (post-increment K>3
   → STUCK-user with the ledger; = 3 real re-attack rounds) →
   dispatch blocker-review → act on its verdict via the constraint
   compass. Un-parking uses the 4th re-entry door: rollback →
   re-assert pre-verify → invalidate downstream → retry.
   GOAL-MET verdicts re-enter step 5 — never direct DONE.
9. CHECKPOINT-EXIT — the ONLY legal non-terminal turn end: write
   all state atomically, refresh this run's global ACTIVE-LANES row
   (status + full-datetime last-touch; Step 0 write discipline —
   Edit own row only), set Status: PARTIAL (checkpoint), exit.
```

### Checkpoint-writer — how ANY turn legally ends mid-run

The Stop hook releases a turn only on DONE / STUCK / PARTIAL. So, in an armed session, **every turn of every type** (tick, Monitor notification, user exchange) ends the same way: if the run is non-terminal, last act = arm-if-unarmed, then `Status: PARTIAL (checkpoint)`. Tick-start flips PARTIAL → active; turn-end flips it back.

- The hook's stderr reflex ("do not return control until DONE or STUCK") is SATISFIED by checkpoint-then-stop — never escape via a false STUCK: a false STUCK reads as terminal and kills the guardian with the goal unmet (the worst failure this section defines). The runbook's `Turn-end rule` line carries this across compaction.
- Esc-interrupt recovery: a turn killed before its flip-back costs exactly ONE hook-dragged turn (which arms + checkpoints), then frees. Designed recovery, not a bug.
- The hook enforces `Refuter:` on DONE but not `RedTeam:` or `Principles:` — model discipline + the runbook fields carry those obligations.
- Between ticks the runbook always reads PARTIAL, so a user who repurposes the session is never dragged — their turns release instantly.

### Navigator / blocker-review — the fresh-eyes subagent

The Navigator (tick step 4.6) and the blocker-review are ONE subagent shape at two intensities: every tick gets the analyze-then-recommend dispatch; when a tick reaches steps 6/8 the same shape is re-dispatched carrying the STUCK PACKET below — that stuck-context dispatch keeps the name **blocker-review**, so every existing cross-reference here and in /prep, /spec, /repair, /error-recon still resolves. Round counting (3-round cap → STUCK-user), `Reviewer: pending` serialization, and the un-park doors are unchanged. The two intensities intentionally DIFFER in packet and rules — apply each context's own: the blocker-review keeps its leaner packet (log tail ~30, NO DIGEST — its independence from the run's distilled testimony is the point), its own verdict vocabulary (FALSE-BLOCKER / REAL-machine / REAL-user / GOAL-MET), and its own UNRESOLVED rule (retry once → REAL-user "reviewer could not rule"); the every-tick Navigator (step 4.6) uses its four-part return and falls back to the plain ladder instead.

Dispatched by tick steps 6/8 (one at a time — `Reviewer: pending` in the runbook enforces it across turns). Hand ONE fresh general-purpose subagent **dispatched with `model: "sonnet"`** (Model routing — same job shape as the Navigator: grade what the disk says): the contract (GOAL.md), runbook, APPROACHES.md, log tail (~30), the claimed blocker/stall, the deliverable/artifact paths, and an explicit **read-only probe license** (Read/Glob/ffprobe-class commands; writes forbidden) — it grades evidence from disk, not the run's testimony.

Brief: *"You did not do this work. Decide: (a) FALSE-BLOCKER — the run can legally continue; return the ONE next step (must trace to Success, violate zero Never-dos, differ from every APPROACHES.md entry); (b) REAL-machine — name the machine-checkable condition + its probe; (c) REAL-user — name exactly what only the user can supply; (d) GOAL-MET — cite the validating evidence. Default to skepticism of the run's own excuses."*

- **Verdict validity:** every verdict must cite the specific contract line(s) + observable evidence read from disk. No citation or no evidence = UNRESOLVED — retry once with a tightened brief, then treat as REAL-user with "reviewer could not rule" noted. Never silently continue.
- GOAL-MET decides nothing by itself — it re-enters tick step 5 (machine probes) and the Terminal Refuter.
- The DRIVER validates and executes the proposed step; the reviewer never acts.
- REAL-machine → slow-heartbeat: re-arm at 30-60 min; `since` = FIRST seen, never reset by flaps; two clear probes apart before resuming; 24h unresolved → STUCK-user (a dead dependency is an incident, not a wait).
- **A REAL-machine blocker with a known recovery path is NEVER a user decision** (incident 2026-08-16, gemini-fallback-live-023001: run parked itself on an "A/B?" menu where A was the protocol's own prescribed path). The run CONTINUES on the recovery path automatically. A bar-lowering shortcut ("accept the partial proof, skip ahead") may be OFFERED as a non-blocking aside in the checkpoint report — but the run keeps driving toward the frozen Success line without waiting for an answer. Parking a legal path to await permission is a menu-stall (violates HI #1 + Principle 5); only a genuine contract dead-end or user-only supply justifies waiting.
- Subagents unavailable → same-context skeptic pass, explicitly marked as the weaker fallback.

### Principles-sweep — the mid-run compliance check (fresh eyes)

_(Added 2026-08-18 by user directive: the guardian should verify the principles are actually being FOLLOWED mid-run, not just that progress is happening. Survived one AUDITOR + RED-TEAM round; the bounds below are their fixes.)_

Fires only on runs whose deliverable is code (build/repair chains — the driver sets `Principles: n/a` at runbook generation for no-code deliverables, flipping it to sweep-eligible on the first deliverable code edit), on the step-7 rider's schedule. Deliverable edits only: files under `auto-runs/` (runbook, PROGRESS, spend, logs, shots) are NEVER part of the trigger or the changed-set — the guardian does not sweep its own bookkeeping. Blocked/step-8 ticks are consciously unswept (blocker-review owns those); their edits are caught at the next step-7 window.

Dispatch ONE fresh general-purpose subagent with a read-only probe license, **`model: "sonnet"`** (Model routing — a fixed 5-item checklist against named files). Hand it: the deliverable files changed since the last sweep's ISO stamp (from log entries AFTER that stamp — the stamp, not a ~30-line tail, bounds the read), GOAL.md, a `reviewed-clean ranges: <fn> L<a>–<b> @<ISO>, …` note (the DRIVER recomputes each FnReview-stamped function's hash and lists only the still-valid ranges — the sweep does not flag inside those; see FnReview), and this fixed checklist — nothing else. Inside a tick the rider dispatches AFTER the step's FnReview has returned and written its ledger — "alongside" means same tick, sequenced — so the two nets never double-flag one function:

```
1. HEAVEN'S NET — RECOVERY/error handling keys to evidence-mapped
   failure classes, never "symptom string X → do Y"; unmatched or
   assumed signals are captured, parked, fail loud — never
   guess-classified (canonical: /error-recon, "Heaven's Net").
   Guardrails: DETECTION may match mapped symptoms — it is the
   recovery that must be class-level; ≤2 handlers need no taxonomy
   (rule of three). Do not flag either.
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
2. EVIDENCE-ONLY — no success declared from labels/exit codes
   alone; verdicts rest on verified output or independent signals;
   nothing assumed.
3. RE-ENTRY HYGIENE — every retry/resume rolls back residue →
   re-asserts the precondition → invalidates downstream before redo.
4. NO SILENCED FAILURES — no bare except/pass, no unbounded retry,
   failures surfaced by count, flight-recorder capture on unknowns.
5. KISS — no frameworks/abstractions the task didn't earn.
```

Brief: *"You did not write this code. For each checklist item return CLEAN or VIOLATION with file:line evidence read from disk. A VIOLATION is a concrete breach, not a style nitpick. Do not rubber-stamp."*

**Verdict handling — bounded at every exit:**

- **Mtime validation first.** Before acting on findings, the DRIVER checks them against current file mtimes: a finding citing a file that changed after the sweep read it is discarded with one log line (stale read, not evidence).
- **Self-contained violation steps.** Each surviving VIOLATION appends as a fix-mode step whose text carries the checklist item + file:line + the quoted evidence + a verify checkable WITHOUT re-sweeping. A violation step is EXEMPT from constraint-compass check (a) — the five checklist items are standing quality constraints, not Success-line work — while (b) Never-do and (c) no-repeat still apply in full.
- **Dedupe + cumulative cap.** A (checklist-item, file) pair a prior sweep already ruled on is never re-flagged (ruled pairs mirror to PROGRESS.md); max 5 sweep-appended steps per run — beyond the cap, findings go to the Notes' Open Questions as report-only. Sweeps must never become the reason a run can't end. FnReview rulings live in their OWN (item, file, function) ledger — never in this file-keyed one — and FnReview-driven fix-mode re-entries do NOT count against the 5-step cap.
- **Won't-fix exit.** A violation step that contradicts a recorded Design Decision, or that parks after honest attempts, may be closed **WAIVED** (intentional design / won't-fix — cite the evidence) by the driver or blocker-review; WAIVED counts as resolved for the all-steps gate and lands in Open Questions. A checklist misread must never drive a goal-met run to STUCK-user.
- **The field never sticks at pending.** CLEAN → `Principles: clean @<ISO>`. A sweep with no evidence citations is UNRESOLVED → retry once at the next window; a second failure, an errored dispatch, or a never-returned result → `unswept @<ISO> (2 failures | error | stale)`, one log line, later windows may try again.
- **At the Terminal Refuter Gate:** deliverable edits newer than the last sweep stamp → annotate the field `clean @<ISO>, unswept tail` and say so in the final report (the refuter-brief Heaven's Net line covers recovery code) — a stale `clean` must never read as full coverage. A `pending` at gate entry follows the staleness rule above: it never blocks DONE silently and never waits unbounded.
- The sweep never pauses the tick's normal work and is never a user gate.

### Constraint compass — no winning by cheating

Before ANY derived, reviewer-proposed, or un-parked step executes: (a) it traces to the frozen Success line; (b) it violates ZERO Never-do lines; (c) it differs from every APPROACHES.md entry. Any failure → step REJECTED (logged with the broken constraint; the rejection consumes an approach slot so cosmetic variants can't loop — EXCEPT a Navigator NEXT rejection, which is logged only and consumes no slot: that budget counts the run's own attempts, not a reviewer's proposals; tick step 4.6). Every remaining path violates a constraint → **STUCK-user with the tradeoff spelled out**: "goal reachable only by breaking <constraint> — your call." The purpose is never traded away silently.

### Terminals + kill switch

```
DONE                       validated deliverable + refuter/redteam
                           per their rules → CronDelete → marker
                           deleted IF it names this slug.
STUCK-user                 only-the-user-can-supply blocker, round
                           cap exhausted, 24h dead dependency, or
                           compass dead-end. Names exactly what is
                           needed + the resume command. CronDelete.
STUCK (stopped by user)    /auto stop slug=<slug>: CronDelete +
                           honest STOPPED report with ledger +
                           resume command + marker deleted IF it
                           names this slug. Always works — the
                           spelling is hook-regex-safe by design.
PARTIAL (checkpoint)       NOT a terminus. Never writes a VERDICT
                           file. Never seals the notes. The
                           guardian carries the run onward.
```

Legacy `VERDICT_STUCK` files (the old all-parked, machine-retryable shape) are treated as checkpoints, not termini — only STUCK-user stands the guardian down. Session-marker deletion always checks content: delete only if it names YOUR slug; if it names another run's, leave it and log one line (with coexisting runs the hook backstops the marker's run; the others are guarded by their own crons + checkpoint discipline).

### RED-TEAM scoping under the guardian

The RED-TEAM rider fires on the deliverable's NATURE (unchanged rule) **or** when the guardian actually fired ≥1 tick — proof the run ran unattended in practice. Never on mere armament: a 20-second attended run stays cheap.


