---
name: principles
description: The user's 14 engineering principles, each codified after a specific real failure: (1) test the condition, not the label; (2) figure out the conditions upfront; (3) keep the end goal in sight; (4) audit against the goal before handback; (5) KISS; (6) think before coding; (7) surgical changes; (8) goal-driven execution; (9) build for the real run; (10) see it before you call it; (11) pin the cause before the fix; (12) completed means delivered; (13) the report grades itself; (14) a question must earn its way to the user. Load at the start of a non-trivial task; before claiming anything is tested, verified, fixed or done; before asking the user a clarifying question; before a refactor, a new abstraction, or a drive-by cleanup; when debugging an unexplained failure; and on any unattended, overnight, or real-scale run. Read the skill body for the full text of any principle - this line only decides WHEN to load it.
---

# Principles

A living collection of rules that must be followed across all code work in this user's projects. Each principle comes from a specific real failure it is meant to prevent. Follow them all, not just the ones that feel relevant to the current task.

This file is designed to grow. New principles get appended using the template at the bottom. Every principle has the same structure so the skill stays scannable as it expands.


## Installation (one-time, per machine)

The `/principles` skill ships with a hook script — `hooks/principles-check.py` — that fires on Stop and blocks the assistant from declaring `done` / `fixed` / `verified` without engaging the principles checkpoint. The hook has two modes:

- **P4 reminder** — the conversation has stated an end goal + success conditions; nudges for the audit-before-handback verdict
- **P2 + P4 reminder** — no observable goal/success-condition was stated; forces the assistant to state them and then audit before declaring done

Without this hook, claim-words slip through and the discipline is purely advisory.

To wire it up on a fresh install (or new PC), add this block to your `~/.claude/settings.json` under `hooks` (merge with existing hooks if any):

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python \"<HOME>/.claude/skills/principles/hooks/principles-check.py\""
          }
        ]
      }
    ]
  }
}
```

Replace `<HOME>` with your actual home path:

```
Windows  →  C:/Users/<your-username>
macOS    →  /Users/<your-username>
Linux    →  /home/<your-username>
```

**Verification:** after wiring, end any assistant turn that contains a claim word (`done` / `fixed` / `verified` / `works` / `tested` / `confirmed` / `complete`) without engaging the principles skill — the hook should block and emit `P4 checkpoint.` (or `P2 + P4 checkpoint — ...` if no goal was stated). If you don't see that block, the hook isn't wired correctly.


`========================================`

## Plan vocabulary — one pyramid, all skills (canonical, added 2026-08-27)

Every skill that breaks work into pieces uses these three words, in this order,
with no synonyms and no reordering. This section is the source of truth; `/auto`,
`/spec`, and `/supergoal` follow it.

```
MILESTONE    the biggest unit — a named chunk of the goal, in the user's own
             words, with its own checkpoint. Most jobs have exactly ONE.

  PHASE      an ordered waypoint inside a milestone, with its own observable
             DONE-WHEN checkpoint. Typically 3–6 per milestone.

    STEP     a single action. The flexible layer — the plan pins WHERE the
             checkpoints are, not HOW to reach them.
```

**Milestone is the top of the chain because it is the biggest.** A phase is
part of a milestone, never the other way around.

**The one collision to know about.** `/auto` and `/prep` number their OWN
internal procedure steps as "Phase −1 / Phase 0 / Phase 8". Those are the
skill's machinery, not the user's work plan, and they are NOT part of this
pyramid — do not rename them and do not confuse them with a work PHASE. When
ambiguity is possible, write *"Phase 3 · transcribe"* (work, always named) vs
*"Phase 0"* (machinery, always a bare number).

**Legacy specs.** `SPEC.md` files written before 2026-08-27 use a `## Phases`
heading with the old PHASE ▸ MILESTONE ▸ STEP order. Read them with the two
upper layers renamed in place (top-level blocks are milestones, inner waypoints
are phases). Never mix the two vocabularies inside one run.

**Depth scales (P5 — KISS).** A one-line fix is one milestone and one phase, and
the board is three lines. Structure is always present; size is not.

## Principles Index

1. **Test the condition, not the label** — the test must place the system in the exact condition being verified; setting a value is not the same as exercising it.

2. **Figure out the conditions upfront** — before acting, nail down the success condition, the testing conditions, and the workflow conditions; without them, "done" has no meaning.

3. **Keep the end goal in sight** — understand the goal and what "done" looks like, use the materials and context you were given, and make every action and question traceable back to the goal; don't drift, don't stall, don't do random stuff.

4. **Audit against the goal before handback** — before stopping, run a checkpoint comparing current observable state to the end goal, then emit a decision-ready verdict (Result / Toward goal / Next) in one of four states (DONE / PARTIAL / BLOCKED / UNCLEAR).

5. **KISS — keep it simple** — pick the simplest solution that solves the present requirement; every layer of abstraction, indirection, or "flexibility" needs a concrete reason that exists today, not a hypothetical one. Duplication beats the wrong abstraction. Rule of three before extracting.

6. **Think before coding** — surface assumptions, forks, and tradeoffs *before* the implementation lands; if multiple readings of the request exist, name them; if a simpler approach exists, push back; if confusion is real, name what's unclear instead of guessing.

7. **Surgical changes** — every changed line traces to the user's request; no drive-by improvements, no style impositions, no silent deletion of pre-existing dead code; mention strays, don't fix them; clean up only the orphans your own change creates.

8. **Goal-driven execution** — transform every imperative ("do X") into a declarative goal with an observable check ("X is done when test_X passes"); for multi-step work, pair every step with its own verify check; strong, checkable success criteria are what enable autonomous loops.

9. **Build for the real run** — design for the actual operating envelope: real scale, real duration, unattended execution, messy inputs, resource limits, recovery. The demo passing is not the goal; the real job surviving is. Only counts conditions you can prove will occur — speculative robustness still falls to P5.

10. **See it before you call it** — when a result is visible (a rendered page, an app window, a generated image), confirm it by reading a screenshot captured at the assertion; an exit code or a matched log string is not proof on a visual surface.

11. **Pin the cause before the fix** — hypothesis-driven debugging (RCA): evidence first → 2–4 ranked falsifiable causes → one pre-registered, cheapest, one-variable probe at a time → only edit code once exactly one cause has positive proof.

12. **Completed means delivered** — a task is complete ONLY when the user-visible result exists in the world and was verified (seen, not inferred); shipped machinery (fixes, loops, specs, retries) is progress, never completion. Reports lead with the result gap and failures FIRST; a dependency dead >2h is an incident to reroute around, not a wait state to normalize.

13. **The report grades itself** — every report ends with NET + CURRENT STAGE (BEFORE/NOW/CHANGED/NEXT/MEANT TO/FEYNMAN) + the goal-compass (4-lens ULTIMATE GOAL derived per scenario — Delivers/Heals/Replaces/Guarantees) + a USER OPTION block whenever the turn puts a decision to the user (the menu, `+`/`−` pros and cons, and a HOLDS UP durability read per option, exactly one marked ← RECOMMENDED, plus IF YOU SAY NOTHING and WHY THAT DEFAULT) + one SUGGESTED ACTION (PASTE THIS, a verbatim-pasteable prompt, with → TOWARD THE GOAL, → HEAVEN'S NET and FEYNMAN lines) and a self-grade (CONFIDENCE: PERFECT/HIGH/MED/LOW + RISK, each with named evidence). Anything pending caps confidence below HIGH; PERFECT requires proven full-autopilot (no human thought, no human intervention, no Claude in the loop); the goal block is frozen — rewording it toward what was achieved is the drift the footer exists to expose.

14. **A question must earn its way to the user** — before any question reaches the user it must pass all four gates: the answer changes what I DO next; I cannot get it myself from a file, command, log or cheap probe; being wrong is costly or irreversible; and it is about WHAT they want, not HOW to build it. Fail one → decide, log one line, keep going. HOW is mine even when I'm unsure. What passes is batched and arrives with a recommendation and a default, so silence is always a valid answer.

> **Crosswalk to Karpathy's 4 principles:** Think Before Coding → P6 · Simplicity First → P5 · Surgical Changes → P7 · Goal-Driven Execution → P8 (also touches P2 + P4).

> **Tiebreaker:** when two principles pull opposite ways, ask which choice keeps the thing working for the *real job* — real-world fit (P9) breaks the tie. This does NOT license speculative complexity: P9 only fires on conditions you can prove will occur, so "practicality" can never be the reason for a safeguard against an imaginary case (that's still a P5 violation). Real fit wins ties; it does not win invented ones.

<!-- Append new entries here as they are added. Keep entries to one line. -->


`========================================`

## The 14 principles in full — one file each

**The Index above is the contract.** Every principle in a paragraph, and it is what
the `P1`..`P14` shorthand in /auto, /prep, /repair, /spec and /supergoal resolves
against. It stays here and always loads.

The FULL text of a principle — when it applies, the real failures behind it, its
checks and its Hard NOs — lives in its own file in this folder and loads ONLY when
that principle is actually in play:

```
  P1   p01-test-the-condition-not-the-label.md      Test the condition, not the label       3227 chars
  P2   p02-figure-out-the-conditions-upfront.md     Figure out the conditions upfront       6446 chars
  P3   p03-keep-the-end-goal-in-sight.md            Keep the end goal in sight              9327 chars
  P4   p04-audit-against-the-goal-before-handback.md Audit against the goal before handback  9434 chars
  P5   p05-kiss-keep-it-simple.md                   KISS (Keep It Simple)                  11346 chars
  P6   p06-think-before-coding.md                   Think before coding                     9334 chars
  P7   p07-surgical-changes.md                      Surgical changes                        9384 chars
  P8   p08-goal-driven-execution.md                 Goal-driven execution                  10741 chars
  P9   p09-build-for-the-real-run.md                Build for the real run                  6130 chars
  P10  p10-see-it-before-you-call-it.md             See it before you call it               3700 chars
  P11  p11-pin-the-cause-before-the-fix.md          Pin the cause before the fix            7324 chars
  P12  p12-completed-means-delivered.md             Completed means delivered               2410 chars
  P13  p13-the-report-grades-itself.md              The report grades itself                5465 chars
  P14  p14-a-question-must-earn-its-way-to-the-us.md A question must earn its way to the us  5616 chars
```

Read the Index first. Open a file only when the paragraph is not enough for the
decision in front of you. **Never quote or cite a principle you have not opened** —
the Index is a summary, and a summary is not the check.

_(Split 2026-08-30. Nothing was reworded; each file is its section verbatim. The
body was 116 KB loaded in full on every invocation, of which a task typically needs
one or two principles. Restoring the old shape is a paste of these files back above
the template section below, in order.)_

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

- **P8 — goal-driven execution:** transform every imperative ("do X") into a declarative goal with an observable check ("X is done when test_X passes"); for multi-step work, pair every step with its own verify check; strong checkable criteria are what enable autonomous loops to keep going without pausing for guidance. Adopted from Karpathy's CLAUDE.md; pairs with P2 (define conditions upfront) and P4 (audit at handback).

- **P9 — build for the real run:** design for the real operating envelope — real scale, real duration, unattended execution, messy inputs, resource limits, recovery; a passing demo isn't the finish line, the real job surviving is. Only fires on conditions you can prove will occur — speculative robustness still falls to P5, which is its hard boundary. Real-world fit is also the tiebreaker when two principles conflict.

- **P10 — see it before you call it:** when a check's result is visible (a rendered page, an app window, a generated image), confirm it by reading a screenshot captured at the assertion before trusting it; an exit code or matched log line is not proof on a visual surface. Capture inside the test at each state-change/assertion; a captured-but-unread shot is the account-95 miss. Encoded into /auto (Hard Invariant #11) and /prep (visual smoke capture).

- **P11 — pin the cause before the fix:** hypothesis-driven debugging (RCA) — observe and collect evidence, list 2–4 ranked falsifiable causes, run one pre-registered cheapest one-variable probe at a time (confirms/disproves written before the result exists), keep a facts/unknowns ledger, and only edit code once exactly one cause has positive proof; fast path only for one-read-obvious causes. Standard here; full procedure in /repair; runs inside /auto fix mode and /prep build/pentest failures.

- Append new principles using the template. Update the index and the frontmatter description when you do.
