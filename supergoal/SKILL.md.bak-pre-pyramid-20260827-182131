---
name: supergoal
description: One-command plan-then-build for large, fuzzy, or from-scratch projects. Runs the full /principles → /prep → /auto chain — loads principles, plans the whole job (greenfield/brownfield intake, recon, risks, decompose into phases, write a /prep plan file, independent self-review, pre-flight smoke check), then hands plain /auto, which reads that plan and builds it autonomously with /auto's verify + retry + independent final audit. Use for "build me X from scratch", big multi-stage builds, migrations, ground-up rewrites, or any large goal you want planned AND built mostly hands-off. Triggers: "/supergoal", "supergoal this", "plan and build the whole thing". NOT for small or already-known tasks — use /auto (or just do it) for those.
---

# Supergoal

`/supergoal <your task>` is a **thin orchestrator** that fuses three skills you already have into one command:

```
/principles  →  /prep  →  /auto
(load rules)     (plan)     (build + audit)
```

It does NOT reimplement them. It runs `/prep`'s planning discipline, writes the result as a `/prep` plan file, and hands off to plain `/auto` — which reads that file, generates its own runbook, and executes. Everything `/auto` already does — stall handling, visual checkpoints, the independent Terminal Refuter final audit, park-don't-halt, overnight survival, the operational heuristics — supergoal inherits **for free** by delegating, instead of re-drawing the loop.

> **Dependency:** this skill describes `/auto`'s final report showing a **coverage %** and its refuter being given a **baseline to diff against**. Those two `/auto` additions ship alongside this skill — if they're ever reverted, soften those two mentions here.

## When to use (and when NOT to)

**USE for:** big, fuzzy, or from-scratch work — "build me a new X", multi-stage pipelines, migrations, a ground-up rewrite, any large goal you want planned AND built mostly hands-off.

**DO NOT use for:** small or already-known tasks (a one-file fix, a rename, a known bug). The planning front-end is pure overhead there — use `/auto`, or just do it.

**Rule of thumb:** big/fuzzy → `/supergoal`; small/known → `/auto`.

## The two halves

Supergoal has a **PLAN** half (you review once) and a **BUILD** half (hands-off). A single review gate sits between them — the one and only pause.

### PLAN — Stages 0–7 (delegates to /prep's methodology)

**Stage 0 — Load memory + detect/preload tools.** Load `/principles` and project memory; preload the tools the run will need. (Both `/prep` and `/auto` open with this kind of preload.)

**Stage 1 — Greenfield or brownfield?**
- Greenfield (nothing exists yet): walk the full intake checklist — platform, stack, design, integrations, scope, audience.
- Brownfield (building on existing code): ask 0–2 questions; recon answers the rest.
(= `/prep` Phase 1 interview, "derive, don't ask".)

**Stage 2 — Recon (parallel).** Read the relevant files/subsystems to ground the plan. Fan out with sub-agents (per `/auto`'s fan-out + context-offload rules) so the driver stays lean.

**Stage 3 — Risks + best practices** for this specific task.

**Stage 4 — Decompose into N phases** (adaptive — no fixed count). Each phase = one clear job with an observable verify check. (Mirrors `/prep`'s function/phase breakdown, which `/auto` later turns into runbook steps.)

**Stage 5 — Write the plan as a /prep plan file.** Produce `./prep-<slug>.txt` in `/prep`'s own format (the per-phase cards: goal, RED/GREEN/REAL/AUDIT for risky pieces, verify checks, cleanliness grep). **This file is the single contract `/auto` consumes.** Do NOT hand-write `/auto`'s runbook or its `GOAL.md`/`RUNBOOK.md` state files — `/auto` Phase 0 reads the prep file and generates the runbook itself, including its own verify-check sanity pass. (You may also print a short human-readable summary for the Stage-7 review, but the prep file is what gets executed.)

**Stage 6 — Self-critique + plan review.** Run `/prep`'s independent AUDITOR second-brain on the written prep file — a fresh agent that reads it and re-derives risk. Fold its findings back; revise Stages 4–5 if it flags blockers (the "Revise" loop).

**Stage 6.5 — Pre-flight smoke check.** Confirm the plan is actually runnable before committing: tools present, paths exist, and each phase's verify check is well-formed — could it pass while the goal is still unmet? Red → back to Stage 6. Green → Stage 7.

**Stage 7 — Print the ready-to-paste handoff.** Show a short plan summary + the exact command:

```
/auto
```

Plain `/auto`. Its Phase 0 auto-detects `./prep-<slug>.txt` as the plan source (prep file = runbook source #1), generates + sanity-checks the runbook, and executes. This is `/auto`'s own documented `/prep → /auto` contract — supergoal just produced the prep file. This is the one review gate: the user reads the plan, then pastes `/auto` once to start the build.

### BUILD — the autonomous half (IS /auto)

When the user runs `/auto`, it reads the prep file supergoal wrote, generates the runbook, and executes it:

- read each phase → do the work → verify (incl. the cleanliness grep) → write memory → mark DONE.
- failure → `/auto`'s approach rotation (up to 5 distinct approaches; `/repair` sub-loop) then **park-don't-halt**.
- stalls, visual checkpoints, disk-is-truth — all of `/auto`'s operational hardening applies.
- FINAL AUDIT = `/auto`'s **Terminal Refuter Gate**: a fresh agent tries to prove it is NOT done and is given a baseline to diff the deliverables against; the final report shows **coverage %**.
- terminal verdict: AUTO DONE (with coverage %) / PARTIAL / STUCK.

Supergoal adds nothing to this half — that's the point. The build inherits every lesson `/auto` has already learned.

## Why a thin wrapper (not a self-contained loop)

If supergoal drew its own execution loop, it would have to re-implement stall handling, visual checkpoints, the independent refuter, park-don't-halt, and overnight resumability — the exact features `/auto` learned from real incidents. Delegating means **one engine, maintained once**, used by `/auto`, `/auto /prep`, `/auto /repair`, and `/supergoal` alike. (See `python-design-patterns`: reuse the engine; don't fork it.)

## The one gate

Supergoal pauses exactly once — at Stage 7 — so you can review the plan before a long build spends real time. After you paste `/auto`, there are no more gates (that's `/auto`'s "invocation is authorization"). For a small/known task even this one gate is overhead — which is why small/known work should skip supergoal and go straight to `/auto`.

## Composition

- `/supergoal` loads `/principles` at Stage 0 — don't re-invoke it.
- The PLAN half follows `/prep`'s methodology and produces a `/prep` plan file; the BUILD half IS `/auto`. Read those two skills for the deep detail — supergoal deliberately does not duplicate them.

## TL;DR

- `/supergoal` = `/principles → /prep → /auto` in one command, for big/fuzzy from-scratch builds.
- PLAN half = `/prep`'s discipline, ending in a `./prep-<slug>.txt` plan file.
- One review gate (Stage 7): paste plain `/auto` to start the build (`/auto` reads the prep file and generates its own runbook).
- BUILD half = `/auto` verbatim — inherits stall handling, visual checks, independent final audit (with coverage % + a baseline to diff against), park-don't-halt, overnight survival.
- Thin wrapper, not a fork: the runbook + loop live in `/auto`, maintained once.
- Small/known task? Don't use this — use `/auto`.
