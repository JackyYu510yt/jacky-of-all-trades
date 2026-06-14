---
name: supergoal
description: One-command plan-then-build for large, fuzzy, or from-scratch projects. Runs the full /principles → /prep → /auto chain — loads principles, plans the whole job (greenfield/brownfield intake, recon, risks, decompose into phases, write specs to disk, independent self-review, pre-flight smoke check), then hands a ready-to-paste /auto command that executes the plan autonomously with /auto's verify + retry + independent final audit. Use for "build me X from scratch", big multi-stage builds, migrations, ground-up rewrites, or any large goal you want planned AND built mostly hands-off. Triggers: "/supergoal", "supergoal this", "plan and build the whole thing". NOT for small or already-known tasks — use /auto (or just do it) for those.
---

# Supergoal

`/supergoal <your task>` is a **thin orchestrator** that fuses three skills you already have into one command:

```
/principles  →  /prep  →  /auto
(load rules)     (plan)     (build + audit)
```

It does NOT reimplement them. It runs `/prep`'s planning discipline, writes the result as an `/auto` runbook, and hands off to `/auto` for execution. Everything `/auto` already does — stall handling, visual checkpoints, the independent Terminal Refuter final audit, park-don't-halt, overnight survival, the operational heuristics — supergoal inherits **for free** by delegating, instead of re-drawing the loop.

## When to use (and when NOT to)

**USE for:** big, fuzzy, or from-scratch work — "build me a new X", multi-stage pipelines, migrations, a ground-up rewrite, any large goal you want planned AND built mostly hands-off.

**DO NOT use for:** small or already-known tasks (a one-file fix, a rename, a known bug). The 8-stage planning front-end is pure overhead there — use `/auto`, or just do it.

**Rule of thumb:** big/fuzzy → `/supergoal`; small/known → `/auto`.

## The two halves

Supergoal has a **PLAN** half (you review once) and a **BUILD** half (hands-off). A single review gate sits between them — the one and only pause.

### PLAN — Stages 0–7 (delegates to /prep's methodology)

**Stage 0 — Load memory + detect tools.** (= `/auto` Phase −1 tool preload + memory load.)

**Stage 1 — Greenfield or brownfield?**
- Greenfield (nothing exists yet): walk the full intake checklist — platform, stack, design, integrations, scope, audience.
- Brownfield (building on existing code): ask 0–2 questions; recon answers the rest.
(= `/prep` Phase 1 interview, "derive, don't ask".)

**Stage 2 — Recon (parallel).** Read the relevant files/subsystems to ground the plan. Fan out with sub-agents per `/auto`'s fan-out + context-offload rules so the driver stays lean.

**Stage 3 — Risks + best practices** for this specific task.

**Stage 4 — Decompose into N phases** (adaptive — no fixed count). Each phase = one clear job with an observable verify check. (= `/auto` stage-mode decomposition.)

**Stage 5 — Write the plan to disk** in `/auto`'s Pattern-3 state format under `./auto-runs/<slug>/`:
- `GOAL.md`       — frozen goal + success conditions (never edited after this).
- `RUNBOOK.md`    — every phase as a PENDING step with its verify check (the file `/auto resume` reads).
- `ROADMAP.md`    — human-readable phase overview.
- `phase-<n>.md`  — per-phase spec: what to build, the verify check, the cleanliness grep.

**Stage 6 — Self-critique + plan review.** Run `/prep`'s independent AUDITOR second-brain on the written plan — a fresh agent that reads the specs and re-derives risk. Fold its findings back; revise Stage 4–5 if it flags blockers (the "Revise" loop).

**Stage 6.5 — Pre-flight smoke check.** Confirm the plan is actually runnable before committing: tools present, paths exist, and each phase's verify check is well-formed — could it pass while the goal is still unmet? (= `/auto`'s self-derived verify sanity pass.) Red → back to Stage 6. Green → Stage 7.

**Stage 7 — Print the ready-to-paste handoff.** Show a short plan summary + the exact command:

```
/auto resume <slug>
```

This is the one review gate. The user reads the plan, then pastes it once to start the build.

### BUILD — the autonomous half (IS /auto)

When the user pastes `/auto resume <slug>`, `/auto` takes over and executes the runbook supergoal wrote:

- read each phase spec → do the work → verify (incl. the cleanliness grep) → write memory → mark DONE.
- failure → `/auto`'s approach rotation (up to 5 distinct approaches; `/repair` sub-loop) then **park-don't-halt**.
- stalls, visual checkpoints, disk-is-truth — all of `/auto`'s operational hardening applies.
- FINAL AUDIT = `/auto`'s **Terminal Refuter Gate**: a fresh agent tries to prove it is NOT done, diffs deliverables vs the baseline, and reports coverage %.
- terminal verdict: AUTO DONE (with coverage %) / PARTIAL / STUCK.

Supergoal adds nothing to this half — that's the point. The build inherits every lesson `/auto` has already learned.

## Why a thin wrapper (not a self-contained loop)

If supergoal drew its own execution loop, it would have to re-implement stall handling, visual checkpoints, the independent refuter, park-don't-halt, and overnight resumability — the exact features `/auto` learned from real incidents. Delegating means **one engine, maintained once**, used by `/auto`, `/auto /prep`, `/auto /repair`, and `/supergoal` alike. (See `python-design-patterns`: reuse the engine; don't fork it.)

## The one gate

Supergoal pauses exactly once — at Stage 7 — so you can review the plan before a long build spends real time. After you paste, there are no more gates (that's `/auto`'s "invocation is authorization"). For a small/known task even this one gate is overhead — which is why small/known work should skip supergoal and go straight to `/auto`.

## Composition

- `/supergoal` already loads `/principles` at Stage 0 — don't re-invoke it.
- The PLAN half follows `/prep`'s methodology; the BUILD half IS `/auto`. Read those two skills for the deep detail — supergoal deliberately does not duplicate them.

## TL;DR

- `/supergoal` = `/principles → /prep → /auto` in one command, for big/fuzzy from-scratch builds.
- PLAN half = `/prep`'s discipline, writing `/auto`'s Pattern-3 state files to `./auto-runs/<slug>/`.
- One review gate (Stage 7): paste `/auto resume <slug>` to start the build.
- BUILD half = `/auto` verbatim — inherits stall handling, visual checks, independent final audit (coverage % + baseline-diff), park-don't-halt, overnight survival.
- Thin wrapper, not a fork: the loop lives in `/auto`, maintained once.
- Small/known task? Don't use this — use `/auto`.
