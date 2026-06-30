---
name: error-recon
description: Evidence-first failure mapping for any tool — smoke-test it, provoke failures within a user-set budget, capture exact messages + verbose output + screenshots, map the expected flow and every error, verify the map with an independent auditor, then spec self-healing protocols on paper. Use when the user says "error-recon this", "smoke test this tool", "map the errors", "figure out all the errors", "what can go wrong with this tool", when starting a new automation tool, mid-build when failure handling needs designing, or when one error just appeared and the full picture is needed. NOT for fixing a single bug right now — that is /repair; NOT a cold code read for latent bugs — that is /deep-audit.
---

# Error Recon

**Map the failures before you build the healing — otherwise you're shooting blind.**

A tool may only act on failures that have been **seen, captured, and proven**. This skill produces the evidence map and the healing spec that make that possible. It does NOT build the healing code — building happens later, on explicit user go, gated through `/audit`.

## When to Use This Skill

Three doors in. Detect which from the invocation; if genuinely ambiguous, ask one question — never guess.

- **Door 1 — from scratch.** User names a tool, no error in sight. Full sweep. NOTE: on a tool whose headline failures are observe-only (daily caps, bans, captchas), a from-scratch run with no history to mine will honestly map only the cheap, provokable errors — the rest become `described — unseen` provisional entries (Phase 3) that the flight recorder confirms over time. Set this expectation up front; Door 1 is often the *first* of several passes, not a one-shot.

- **Door 2 — mid-build.** The tool partially exists in this session. Same sweep, scoped to what's built so far; the map grows with the tool.

- **Door 3 — incident.** An error just happened — in chat, in a run, or sitting in the tool's `unmapped/` inbox. Capture that one fully first. Then **ask** whether to widen to a full sweep — do not auto-expand a single-error deep-dive into budgeted provocation without a gate. If an `error-recon/<slug>/unmapped/` inbox exists with captures, always start there. Door 3 (after real failures have landed in `unmapped/`) is where this skill is strongest.

## Core Principle — the evidence hierarchy

**Signals tell you WHY it failed. Only the output tells you WHETHER it worked.**

1. **Verified output** — the artifact the tool exists to produce: the file on disk that opens cleanly, the logged-in session that can perform a real action, the ledger row that survives verification. The only judge. SUCCESS may never be declared from anything else.

2. **Visible screen** — strong witness. Used to diagnose WHY something failed. Never used to declare success.

3. **Hidden DOM text, logs, labels, exit codes** — weak witnesses. Corroborate only; never decide alone.

Witnesses that disagree don't fight it out by rank — they trigger an output check, and the disagreement itself gets recorded in the map as evidence.

## The Anti-Guessing Rules (always on)

Born from real misreads (umbrella "FAILED/cooked" labels, a transitional URL treated as a verdict, hidden HTML contradicting the visible page, 498 ledger rows that were really 192 accounts). Hard rules, not suggestions:

1. **No umbrella labels.** Every state a tool reports maps 1:1 to a map entry ID. A bare "FAILED" is forbidden — print `soft-block [E05]`, never a scary catch-all word. (Real example: `gemini_worker`'s `all_accounts_at_limit` lumps 4 distinct causes into one label — exactly what this rule forbids.)

2. **Terminal vs transitional — two separate axes, never one.**
   - **Navigation axis: pass-through vs settled.**
     - *Short steps (normal time ≲ 10 min):* a state counts as settled only if it survives a **stability re-check whose wait exceeds the step's max normal timing** (from THE FLOW, Phase 1a) — never a free-floating "a beat." A "Processing…" page on a step that normally takes 90 s is NOT settled at 3 s.
     - *Long steps (normal time ≳ 10 min — renders, big uploads, batch jobs):* do NOT out-wait the longest legitimate run. Declare settled from a **positive stall signal** — no movement on that step's own progress checkpoint (Phase 1a) across two consecutive checks — not from elapsed time. (Out-waiting a 60-min render to call it "stuck" is both unworkable and budget-eating; watch the progress checkpoint you already defined instead.)
   - **Semantic axis: recoverable (with measured recovery time) vs permanent.** Set by the duration-probing ladder (Phase 1b: 1/2/5/15 min), not by the re-check. A soft block and a daily cap can both be "settled" — what separates them is the measured recovery time, recorded explicitly.

3. **Spot with OR, confirm the verdict with AND — and the two AND signals must be genuinely INDEPENDENT.** A state may show up in several alternate forms — list them as an OR set so the tool *spots* it however it appears (real example: `ai_studio` OR's 4 rate-limit signals). Assigning the *meaning* (the verdict that drives a protocol) needs **two independent signals agreeing**. *Independent* = different layers/channels that can disagree (e.g., HTTP status + the on-disk artifact, or a `Retry-After` header + the rendered page) — NOT two reads of one rendered surface. Two DOM elements from the same server response (e.g., a banner's text + the URL it rendered with) are one signal read twice, not two — they fail together. A single-signal verdict is allowed only when one channel is all that exists (e.g., an API client with only status+body) — and the entry must say so and justify it.

4. **Denominators before verdicts.** No claims about a population (accounts, jobs, files) without total / unique-count / source. When evidence is a ledger or log, record its semantics in the map: append-only? rows ≠ items? unique key? **written by multiple processes concurrently?**

5. **The map is the only interpreter.** Once a map exists, nothing improvises — not the tool, not Claude in a later session. A signal either matches an entry (act per its protocol) or it doesn't (UNMAPPED: capture, park, stop loud). Never paraphrase an error message — verbatim or nothing.

## Confidence tiers (what earns a real protocol)

- **`confirmed`** — reproduced deliberately, evidence audited CONFIRMED. Gets a full protocol.
- **`confirmed-stochastic`** — seen ≥2 times from the same cause but NOT reproducible on demand (a 1-in-N race, load-dependent OOM, flaky network). Earned by *frequency in history*, not by deliberate reproduction. Gets a real protocol — bounded retry is the natural fit, since intermittence is exactly what retries exist for — tagged with the observed frequency (`~1 in N`). This is the class that kills long unattended jobs; do not leave it protocol-less.
- **`seen once — unconfirmed`** — one sighting, not yet reproduced. Conservative handling only (capture, park, stop loud).
- **`described — unseen`** — the user describes a failure recon cannot safely provoke (cap, ban, captcha). Recorded with the user's account of the signal, marked explicitly un-evidenced. May get a **provisional** protocol (Phase 3) so the tool isn't defenceless — but it activates as `provisional` and must be confirmed by a real flight-recorder capture before it is trusted.

## Artifacts — one folder per tool, living next to the tool

```
<tool project dir>/error-recon/<tool-slug>/
  map.md            # THE FLOW + THE ERRORS — single source of truth
  healing-spec.md   # Phase 3 output (only after its gate)
  screenshots/      # evidence images, e.g. E05-soft-block-01.png
  raw/              # verbatim logs, DOM dumps, response bodies
  unmapped/         # flight-recorder inbox, filled by production runs
```

- Maps are **living documents**: later runs APPEND, never overwrite.
- A disproven entry is marked `RETRACTED — superseded by <evidence>`, never deleted (the wrong reading must stay visible so a later session can't re-derive it).
- A once-correct entry whose world moved on (site redesign, policy change, API bump) is marked `STALE — target may have changed, re-verify` — distinct from RETRACTED (which means *we were wrong*; STALE means *we were right, reality moved*). Every entry carries a `Last-verified: <date>`; a confirmed entry that hasn't been re-verified since the target visibly changed is treated as STALE, not trusted.
- If Phase 2.5 was skipped, the map is stamped **`UNAUDITED`** at the top and no entry in it may be cited as `confirmed` — skipping the audit must be *visible*, never silently pass as audited-grade.
- Multi-day evidence (e.g., confirming a daily-cap reset) is normal — recon persists state in the folder and resumes where it left off.
- The map must be readable by a cold-start session with zero chat context.
- **`/auto` exemption:** this folder lives next to the tool even under `/auto`. The map is part of the tool, not a run artifact — it does NOT get nested under `auto-runs/<slug>/`.

## Runtime Workflow

Phase gates: after Phase 0, Phase 2.5, and Phase 3, stop and ask the user whether to proceed (AskUserQuestion). Under `/auto`, gates collapse per the user's standing rule — only DONE or STUCK ends the run. **The budget is the one exception: it is NOT a collapsible gate.** Under `/auto`, budget must be supplied in the invocation; if absent, recon runs **safe-and-zero-cost only** (no costly provocations at all), and budget exhaustion ends the run as **STUCK**. Recon never invents its own permission to burn.

`========================================`

### Phase 0 — Scope (one screen, then a gate)

1. **Identify target type** — web automation / CLI script / API client / mixed. This selects the capture playbook (below).

2. **Mine existing evidence FIRST.** Old logs, ledgers, screenshots, past run output, the `unmapped/` inbox. Already-paid-for evidence costs nothing — provocation only fills the holes. Tag these entries `source: history`. (On a brand-new tool this bucket is often empty — say so, and lean on `described — unseen` for the failures you can't provoke.)

3. **Inventory the surfaces** — every step/action where something can fail. **If the tool ever runs in parallel with itself or others** (multi-account workers, fan-out renders), also inventory shared-resource contention as its own surface: locks, quota shared across instances, the same output path, concurrent writes to an append-only ledger. Single-instance recon will never surface these.

4. **Sort candidate failures by WORST PLAUSIBLE CONSEQUENCE — not by how cheap the trigger looks:**
   - **Safe to provoke** — outcome is fully reversible and touches nothing shared: bad CLI arg, missing local file, a network cut you control, malformed local data. Trigger freely.
   - **Costly** — anything touching auth, quota, payment, rate limits, or a target's anti-abuse surface. A *cheap* trigger here is still costly (e.g., repeated bad logins are trivially easy to send but escalate to a lockout). Only within budget.
   - **Observe-only** — bans, lockouts, destructive or irreversible outcomes. NEVER provoked. Mapped from history, from natural occurrence, or as `described — unseen` from the user's account.

   Rule of thumb: classify by what could happen at worst, then provoke at the cheapest level that still produces the evidence.

5. **Ask the budget question — the cheap half now, the priced half after measurement.** In Phase 0, ask only what's knowable up front (AskUserQuestion): may recon run the safe / zero-cost sweep, and roughly how much is the user willing to risk overall (sacrificial resources like "2 burnable accounts", appetite for wait-time)? The concrete spend units get re-confirmed after Phase 1a measures what one real run actually costs (don't make the user denominate blind). **All consumption counts** — happy-path baselines and the outcome check burn budget too, not just provocations. Within the confirmed budget, recon runs free without re-asking; beyond it, it stops and asks (or, under `/auto`, ends as STUCK).

6. Present the scope plan. **Gate: proceed?**

`========================================`

### Phase 1a — Baseline: map the expected flow first

You can't recognize "wrong" without writing down what "right" looks like.

Run the happy path at least twice (budget permitting) and record, step by step:

- **Action** — what the tool does ("click generate").
- **Expected result** — what should happen next.
- **Checkpoint** — the one signal that proves this step was truly reached. This is what built tools later use to know where they are — and, for long steps, the **progress checkpoint** the stall-detection in Rule 2 watches.
- **Normal timing** — measured range ("30–90 s"). Every timeout AND every stability re-check window in later phases derives from these measurements. Two samples is a thin basis for a *maximum* — treat the early max as provisional, widen it as production data arrives, and never let a single slow-but-legit run trip a "settled = failed" verdict.
- **Outcome check** — defined here, once, for the whole tool: the exact, concrete verification of real success (file exists + nonzero + opens cleanly; session performs a real action; etc.). **When direct verification is expensive (costs quota), or impossible from here (fire-and-forget, third-party delivery):** define the cheapest *sufficient* check, count its cost against the budget, and record the verification gap in the map as a known weakness. Never silently fall back to a screen/label proxy.

Record **realistic variations** — branches that are normal, not broken: cookie banner, already-logged-in skip, slow load, occasional popup. Each tagged: **"normal variation — handle by X, not an error."** Only variations actually seen or genuinely likely. No imaginary branches.

**Budget re-confirm checkpoint:** now that one real run's cost is measured, convert the Phase 0 risk appetite into concrete spend units and confirm with the user: *"one run costs ~X (quota/time/resource) — your budget allows ~N runs and the duration ladder up to 15 min per block; still good?"* This is the point where blind denomination becomes informed.

`========================================`

### Phase 1b — Provoke and capture

- **One variable at a time** — every captured error must trace to a known cause.
- **Space out provocations** — recon must never look like an attack on the target. Derive the spacing from Phase 1a's measured timings (don't fire faster than a normal run would).
- **Reproduce safe errors once to confirm.** Costly errors stay `seen once — unconfirmed`. A failure seen repeatedly in history but not reproducible on demand is `confirmed-stochastic`, not unconfirmed — frequency is its evidence.
- **Duration probing** for blocks: when a block appears, probe at growing intervals (1, 2, 5, 15 min). Measured recovery time is the evidence separating a soft block from a daily cap, and it sets the semantic axis of Rule 2. Budget-gated.
- **Capture at every state change**, not just at the end — one snapshot can miss the moment. "State change" = URL change, DOM-mutation settle, network-idle, or a new line on stdout — whichever the target type makes observable.

**Capture playbook per target type — every capture gets all that apply:**

| Target | Capture |
|---|---|
| Web automation | Screenshot at the failure moment (always) + DOM snapshot + exact visible text + the script's own exception text + current URL |
| CLI script | Full stderr/stdout verbatim + exit code + re-run with verbose/debug flags |
| API client | Status code + full response body + headers (e.g. `Retry-After`) + timing |

**When the TOOL owns the browser** (the common case — the user's own headless automation): Claude usually can't screenshot inside a browser the tool launched. Pick one, in order of preference: (a) **instrument the target** — add a small READ-ONLY debug hook that dumps screenshot + DOM into `raw/` on failure (this captures, it does not heal — it is not the forbidden "healing code"); (b) **run it headed / attach via CDP** and capture from outside — but tag such captures `mode: headed (tool runs headless)`, because headed and headless can fail differently (bot-detection, timeouts), and the map must record the discrepancy; (c) **attach `browser-trace`** to the session. If none is possible, say so in the map and downgrade that entry's confidence — don't pretend a screenshot was taken.

**Context stamped on every capture:** timestamp, triggering action, flow step (from Phase 1a), actions-since-start count, session/account state.

`========================================`

### Phase 2 — Draft the map

`map.md` has two halves:

**THE FLOW** — from Phase 1a: steps, checkpoints (incl. progress checkpoints for long steps), timings, variations, the outcome check.

**THE ERRORS** — one entry per failure. Fill the fields the evidence supports; omit fields that don't apply (a CLI error needs ~5 of these, not all of them — the template is a menu, not a quota):

```
## E05 — soft block
- Step: 4 (submit prompt)
- Spot (OR — any of these forms): visible text "Try again later" | banner id #rate-msg
- Verdict signals (AND — must be INDEPENDENT, agree): "Try again later" [visible page]
  + HTTP 429 / Retry-After header [transport layer — different channel]
  + screenshot: screenshots/E05-soft-block-01.png
- Single-signal? no  (if yes: which channel is the only one, and why it suffices)
- Source: provoked 2026-06-12 | history | natural | described — unseen
- Last-verified: 2026-06-12
- Meaning: temporary rate block
- Navigation axis: settled (survived re-check / stalled-checkpoint)
- Semantic axis: recoverable — recovery measured at ~4 min via duration probe
- State: session alive, quota NOT exhausted, job resumable at step 3
- Residue: partial side effects this failure can leave (half-written output at step 4, uncommitted ledger row) that a rollback must undo before resume — (none / list)
- Distinguish-from: E06 daily cap — cap survives the 15-min probe, soft block does not
- Ledger semantics (if evidence is a log): append-only? rows≠items? unique key? concurrent writers?
- Confidence: confirmed | confirmed-stochastic (~1 in N) | seen once — unconfirmed | described — unseen
- Protocol: (Phase 3)
```

Plus an **UNMAPPED** section (witnessed but not yet understood), a **RETRACTED** section (audit-disproved), and a **STALE** section (was confirmed, target may have changed).

`========================================`

### Phase 2.5 — Independent evidence audit (second brain)

The misinterpretation layer is where guessing lives — so the evidence→meaning links get attacked by a brain that didn't write them. **This validates INTERPRETATION, not COVERAGE** — un-provoked failure modes are caught later by the flight recorder, not here. Skipping this phase stamps the map `UNAUDITED` (see Artifacts).

Dispatch a fresh subagent (`Agent`, general-purpose). Hand it ONLY:
- the raw captures (paths to `screenshots/`, `raw/`),
- the draft `map.md`,
- this brief — never the chat's running assumptions:

```
You are an evidence auditor. You did NOT write this map and must not
assume it is correct. Re-derive each entry's meaning from the raw
captures alone. For every entry return ONE of:
  CONFIRMED     — you independently reached the same meaning, OR
  WEAK          — captures are adequate, but consistent with another
                  explanation too (name it), OR
  WRONG         — captures contradict the claimed meaning (show how), OR
  UNDERCAPTURED — the captures are INSUFFICIENT to decide this entry's
                  meaning at all (deciding signal missing / mis-timed /
                  not captured). This is NOT the same as WEAK: WEAK is a
                  close call on adequate evidence; UNDERCAPTURED is a
                  blind spot. Say what capture is missing.
Check specifically: single-signal verdicts, two signals that are really
one (same render read twice — not independent), transitional pages
treated as settled (re-check shorter than the step's normal time),
hidden-vs-visible conflicts, ledger row/item confusion, and any success
declared from something other than the verified output.
Do not rubber-stamp.
```

Reconcile: **WRONG** → mark `RETRACTED` (never delete). **WEAK** → more recon if budget allows, else `seen once — unconfirmed`. **UNDERCAPTURED** → route back for more capture, or flag to the user as un-decidable — NEVER silently downgrade to "unconfirmed but plausible" (that would let a blind spot pose as a close call). Disagreements are shown to the user, not silently resolved.

**Gate: "Audited map ready — N confirmed, M unconfirmed, K undercaptured. Healing spec now or later?"**

`========================================`

### Phase 3 — Healing spec (paper, not code)

Written to `healing-spec.md`. **`confirmed` and `confirmed-stochastic` entries get real protocols.** `seen once — unconfirmed` and `UNDERCAPTURED` entries get conservative treatment (capture, park, stop loud). `described — unseen` entries may get a **provisional** protocol (below).

**Opens with the outcome check** (from Phase 1a): the only way the tool may ever declare SUCCESS. Every other signal diagnoses failures.

**Per protocol-eligible error:**

- **Detect** — the spot-set (OR) plus the verdict match (two *independent* signals agreeing + stability/stall check sized from THE FLOW). A single-signal verdict is allowed only where the entry already justified it in Phase 2. No fuzzy matching.
- **Options, priced** — 2–4 realistic moves, each with cost / risk / when-it-works. (e.g., wait 4 min: cheap, proven · rotate account: burns a resource · park job, continue batch: free · abort day: expensive, only correct for a true daily cap.) Options that would never be chosen don't get written.
- **Chosen chain** — ordered, every rung bounded (max retries, backoff), a resume-at-step from THE FLOW, bottom rung always fail-loud. When a rung resumes a step that may have run partway, it follows the canonical re-entry order — roll back partial work (the entry's `Residue`) → re-assert the precondition → invalidate downstream (later FLOW steps whose persisted output is now stale) → resume — never re-running on a prior attempt's residue. Never an infinite loop. (For `confirmed-stochastic`, bounded retry is usually the chosen chain — capped, with the `~1 in N` frequency noted so the cap is sane.) When the right chain is a judgment call (burning a resource vs waiting), show the user the priced options and let them pick.
- **Label** — the exact string the tool prints, 1:1 with the entry ID (`soft-block [E05]`).
- **Provenance** — at decision time the tool logs entry ID + the signal that matched, so "why did you call it that?" is always answerable from the log.

**Provisional protocols for `described — unseen`:** for an un-provokable failure the user most needs to survive (the daily cap, the soft block), spec a protocol from the user's description — but flag it `provisional — unconfirmed`. It runs, but it is wired so the **first real capture** (via the flight recorder) is checked against the description; if they match, promote to `confirmed`; if not, the protocol is suspended and the entry returns to recon. This gives the user a real survival plan day one without pretending it's evidence-backed.

**The catch-all, always last:** unknown error → never guess-handled. Capture trifecta, write to `unmapped/`, stop safe and loud.

**The flight recorder — required in every tool built from this spec:**

- Mapped error → handle per protocol + one provenance log line.
- Unmapped error → full capture (message, log tail, screenshot if a screen exists) into `unmapped/` BEFORE anything else. (Real gap this closes: `ai_studio` logs nothing on a timeout, just a label; `gemini_worker` keeps transient state in memory and loses it on restart.)
- It is also what confirms `provisional` and `described — unseen` entries: their first real occurrence is captured and checked against the description.
- Capture can never crash the tool — best-effort, wrapped, no network calls, no dependencies. ~20 lines, not a framework.
- Repeats don't flood the disk: full capture of the first 3 occurrences, then a counter.

**KISS throughout:** 5-line `for` retry loops, no retry frameworks; dict lookups, no registries. Complexity must earn its place.

**Gate: "Spec done — build?"** Building is OUT OF SCOPE for this skill. It happens as a normal follow-up, gated through `/audit`.

`========================================`

## Hard NOs

- Never paraphrase an error message — verbatim or nothing.
- Never declare success from a screen, a label, or a log line — only from the verified output.
- Never provoke observe-only failures, and never exceed the budget silently. Under `/auto` with no budget supplied, never provoke anything costly.
- Never classify a short step as settled off a re-check shorter than its normal timing; never out-wait a long step to call it stuck — use its progress checkpoint.
- Never count two reads of one render as two independent signals.
- Never downgrade an UNDERCAPTURED entry to "unconfirmed but plausible" — a blind spot is not a close call.
- Never overwrite or delete a map entry — append, `RETRACTED`, or `STALE`.
- Never let an unmapped signal be "probably X" — it is UNMAPPED until evidence says otherwise.
- Never trust a `provisional` or `described — unseen` protocol as if it were confirmed.
- Never write healing code inside this skill — spec only.

## Relationship to Other Skills

- **`deep-audit`** — cold-reads existing CODE for latent bugs. `error-recon` runs the TOOL against reality and captures real failures. Code-in vs world-in. (For a tool you own, `deep-audit` + good logging may be cheaper for the CLI/API parts; `error-recon` earns its keep on the interpretation discipline — outcome check, no umbrella labels, denominators — and on opaque third-party surfaces.)
- **`repair`** — fixes a failure after it happens. `error-recon` maps the failure space so future repairs become map lookups instead of investigations.
- **`spec`** — `error-recon`'s map is the upstream source of the *known failure modes* /spec's self-healing success criteria require: each confirmed entry feeds a phase's `RECOVERS-BY` (failure mode + ordered recovery). No map → /spec's "recovers from its known failures" criterion has nothing concrete to point at.
- **`prep`** — the map + healing-spec feed /prep's per-function design: confirmed entries become field-9 (Failure modes table) and field-12 (rollback, via the `Residue` field) content, and the safe-to-provoke set plus the `described — unseen` modes become /prep's field-6 TESTING-CONDITIONS injection list. /prep designs the healing; `error-recon` supplies the evidence it heals against.
- **`audit`** — gates the build step that follows this skill.
- **`auto`** — under `/auto`, phase gates collapse; only DONE or STUCK ends the run. The budget is the exception — it must be pre-supplied, never invented.
- **`optimize`** — tune the tool after it's correct and self-healing.

## TL;DR

- Break it on purpose, within a budget — classified by worst consequence, not how cheap the trigger looks; the priced budget is confirmed after one run is measured, not guessed blind.
- Capture every failure like a crime scene: exact words, full output, screenshot.
- Map what RIGHT looks like (flow, checkpoints, timings) and what every WRONG looks like — anchored to steps. Long steps detect "stuck" from a stalled progress checkpoint, not by out-waiting the run.
- Spot a state with OR; assign its meaning only when two genuinely independent signals agree.
- A fresh second brain re-derives every conclusion from raw evidence — and can say UNDERCAPTURED when it's blind, not just WEAK.
- Failures you can't safely provoke get `described — unseen` provisional protocols; flaky-but-frequent ones get `confirmed-stochastic` + bounded retry. Neither is left defenceless.
- Healing is specced on paper, built later, gated by `/audit`. Every built tool carries a flight recorder that captures new errors and confirms the provisional ones.
- Success is only ever the verified output. Everything else is a witness.
