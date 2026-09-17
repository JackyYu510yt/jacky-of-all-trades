---
name: deep-audit
description: Trace an existing script or pipeline end-to-end to surface latent bugs before they bite — silent exception swallows, cascade failures, timeout mismatches, counter drift, wasted work, implicit assumptions. Three passes: map the flow function-by-function, trace a failing item through every retry and fallback, then catalog every external dependency. Use when code already works but you don't trust it yet: inherited scripts, pipelines about to run unattended for hours, post-mortems where logs were insufficient, or any time you want a cold read of code you didn't just write. Triggers: "cold read this", "trace this end to end", "deep audit", "what could silently fail here", "audit before the long run", "this died last night and the logs are useless", "find the silent failures".
---

# Deep Audit

Slow, deliberate read of code that already runs. Finds latent bugs *before* they surface under load — silent `except: pass`, timeout mismatches, cascade failures, counter drift, fragile assumptions that only hold by luck.

Distinct from `audit`: that skill is a pre-flight check on *proposed changes*. This skill is an x-ray of *existing code* that you're about to trust with a long, unattended run.


## When to Use This Skill

- User says "cold read this", "trace this end to end", "deep audit", "what could silently fail", "find the silent failures", "audit before the long run"

- Inherited or legacy code that's about to be relied on

- A script or pipeline about to run unattended for hours (video renders, batch jobs, overnight processing)

- Post-mortem on a job that died silently with useless logs — paired with `repair` when a clean reproduction doesn't exist

- Any time suspicion exists but there's no specific bug to chase yet


## Core Principle

**Code that looks fine and runs fine can still harbor bugs that only surface under load, at scale, or after hours of execution.** A bare `except: pass` hides an OSError for months before biting. A 5-second timeout is fine on a 50MB upload and lethal on a 5GB one. A retry counter that resets each loop is invisible until the outer job takes twice as long as planned.

Deep-audit is the slow read that catches those before they cost a 4-hour job.

Three questions every function must answer:

- **Flow** — what does it do, what does it wait on, what does it hand to the next step?

- **Failure** — when something goes wrong here, where does the wrongness go?

- **Dependency** — what outside this code has to be true for this to work?


## Runtime Workflow

Five phases. Run them in order. The output is a structured report, not a go/no-go verdict — deep-audit is diagnostic, not gating.


`========================================`

### Phase 1: Scope the Target

Lock in what code is being audited before reading anything.

- **Files in scope** — list every file that will be read.

- **Entry point** — which function or command starts execution?

- **Boundary** — where does the audit stop? (e.g., "follow into render_one() but stop at the ffmpeg subprocess — that's a black box here")

- **Runtime profile** — one-shot script, long-running daemon, batch pipeline, unattended overnight job? Failure modes differ wildly across these.

If the target is ambiguous ("audit the renderer"), ask one `AskUserQuestion` to clarify before starting. Don't guess — the scope determines everything downstream.

`========================================`

### Phase 2: Map the Flow

Read the code end-to-end. For each function, in execution order, record:

- **Name + file:line** — where it lives.

- **What it does** — one plain sentence.

- **What it waits on** — subprocess completion, network response, file lock, a sleep, a queue item.

- **What triggers the next step** — return value, callback, event, state mutation.

- **Timing values** — every hard-coded sleep, timeout, retry delay, polling interval. Write the actual number.

- **Data handoff** — format in, format out, what the next function expects.

Be literal. If the code checks for a spinner in the UI before declaring success, *write that*. Don't paraphrase it as "checks UI state." If it catches `ValueError` but re-raises `OSError`, *write that* — don't say "handles errors gracefully."

Vague flow maps produce vague bug reports.

`========================================`

### Phase 3: Trace a Failing Item

Pick one item (video, request, file, row) and follow it through every retry and fallback path. Start with a plausible fault — network drops, ffmpeg exits non-zero, output file is 0 bytes — and trace exactly what happens next, until the item is either recovered or abandoned.

At each junction, apply the six flags:

**1. Silent exception swallowing** — bare `except:`, `except Exception: pass`, broad catches that log nothing. What specific errors are being hidden? What state does the code land in afterward?

**2. Cascade failures** — does one component dying kill unrelated components? Shared thread pool, shared client, shared lock that never releases. List the blast radius.

**3. Timeout mismatches** — is the timeout value sane for what it's actually waiting on? A 10s timeout on an ffmpeg render is too short. A 5-minute timeout on a health check is too long. Call out both directions.

**4. Counter / limit drift** — retries not actually counted, limits checked at setup but never at execution, counters reset inside a loop that was supposed to cap them, off-by-one on max attempts.

**5. Wasted work** — anything repeated unnecessarily across retries. Re-downloading the same file, re-initializing the same client, re-running expensive setup after a transient failure.

**6. Implicit assumptions** — things that only work because of timing, execution order, or unchecked external state. "Works because the previous function happens to leave the cwd correct." "Works because the API usually responds in under 2s."

For each flag:

- **Where** — function name + file:line.

- **Scenario** — the concrete failure story, not a category.

- **State involved** — which variables, counters, handles, connections are implicated.

`========================================`

### Phase 4: Dependency Map

Every external thing the code relies on, with the blast radius if it misbehaves.

Categories:

- **Libraries** — pip packages, especially ones with platform-specific behavior (ffmpeg-python, Pillow, anything that shells out).

- **Binaries on PATH** — ffmpeg, ffprobe, git, docker. What if missing? What if wrong version?

- **Files read / written** — config files, log files, caches, state files, lock files. What if missing, empty, malformed, locked, read-only, on a full disk?

- **Services called** — HTTP endpoints, S3, databases, queues. What if slow, down, returning unexpected shape, rate-limited?

- **OS-level assumptions** — writable `/tmp`, enough RAM, specific line endings, specific shell available, specific timezone.

- **Browser / GUI state** — if the code drives a browser or UI, what must already be true? User logged in? Specific window focused? No modal open?

For each dependency, state:

- **What it is** — one line.

- **If missing** — what happens, how soon, with what error (or none).

- **If slow** — what timeout catches it, or does it hang forever?

- **If malformed / unexpected** — does the code validate, or does it propagate garbage?

`========================================`

### Phase 5: Present the Report

Emit a structured report. Template:

```
=== DEEP AUDIT REPORT ===

Target: <files / scope>
Entry point: <function or command>
Runtime profile: <one-shot | long-running | batch | unattended>

--- FLOW MAP ---
 1. main() [app.py:12] — reads config.json, calls render_batch()
 2. render_batch() [app.py:34] — loops videos, 300s timeout per item
 3. render_one() [app.py:78] — spawns ffmpeg, writes output
 4. ...

--- LATENT FAILURES ---
 [HIGH]  render_one():92 — bare `except: pass` swallows ffmpeg OSError.
         Scenario: ffmpeg crashes mid-encode, function returns success,
         output file is 0 bytes, downstream copy step "succeeds".
         State: proc.returncode never checked, output_path never verified.

 [HIGH]  render_batch():45 — retry counter reset to 0 inside loop.
         Scenario: transient network error triggers retry, counter resets,
         retry budget effectively unbounded. Under sustained network flake,
         job never completes.
         State: retries_left reassigned each iteration.

 [MED]   main():12 — assumes /tmp writable.
         Scenario: full disk → silent PermissionError → job exits with
         cryptic traceback, no partial progress saved.
         State: no pre-flight check on disk space.

 [LOW]   cleanup():200 — deletes files matching *.tmp in cwd without
         checking ownership.

--- DEPENDENCY SURFACE ---
 - ffmpeg (PATH)
     missing → caught at startup, clean exit
     slow → hangs past 300s timeout, killed, retried
     wrong version → unpredictable; no version check

 - config.json
     missing → KeyError on first access, no helpful message
     malformed → silent partial load, defaults fill the gaps

 - /tmp
     full → silent truncation of intermediate files
     read-only → PermissionError propagates to top level

 - S3 upload
     timeout 5s, too aggressive for files > 500MB
     no retry wrapper; single failure aborts entire batch

--- SUMMARY ---
Two HIGH-severity flags worth fixing before the next long run.
Biggest risk: silent ffmpeg failures produce 0-byte outputs that pass
existence checks. Recommend adding explicit returncode + filesize
validation at render_one():92.
```

Use the same visual conventions as other response skills: rainbow top separator, `====` between sections, bolded anchors, double line breaks between items in dense lists. Plain-language summary at the bottom, no jargon dump.

`========================================`


## What Counts as "Deep" (how far to go)

Deep-audit is expensive — don't over-apply it.

**Yes, run deep-audit when:**

- Script will run unattended for 1+ hours.

- Script handles irreplaceable data (rendered assets, transcoded masters, one-shot uploads).

- Inherited code with no test coverage and no clear author.

- Post-mortem where the logs didn't explain the failure.

**No, don't run deep-audit when:**

- The code is under 100 lines and you can read it at a glance.

- You just wrote it — you already know the flow.

- There's a specific bug with a clean reproduction. Use `repair` instead.

- You're about to apply a change. Use `audit` instead.


## Hard NOs

- **Do not paraphrase.** If the code catches `OSError`, write `OSError`. Not "handles errors."

- **Do not skip Pass 2 for being tedious.** Tracing a failing item is where the real bugs surface. The flow map alone is just reading.

- **Do not emit a report without severity rankings.** Every latent failure must be tagged HIGH / MED / LOW or the user can't triage it.

- **Do not issue a go/no-go verdict.** Deep-audit is diagnostic. The user decides what to fix; this skill only surfaces.

- **Do not invent dependencies.** If the code doesn't actually import `requests`, don't list it. The dependency map reflects real code, not guesses.

- **Do not confuse this with `audit`.** Audit gates a change. Deep-audit reads existing code. If the user is about to apply a diff, route them to `audit`.


## Relationship to Other Skills

- **`audit`** — gates a *proposed change* about to be applied. Deep-audit reads *existing code* you're about to run. Audit is fast pre-flight; deep-audit is slow x-ray.

- **`repair`** — post-failure with a symptom. Deep-audit is pre-failure, no symptom yet — "what could go wrong" vs. "what did go wrong."

- **`prep`** — designing new code from scratch. Deep-audit reads code that already exists.

- **`optimize`** / **`simplify`** — improving code that works. Deep-audit surfaces risk; optimize/simplify act on it.

- **`explain`** — the deep-audit report uses explain's visual conventions: rainbow top, `====` separators, bold anchors, generous spacing, plain-language summary.


## TL;DR

- **Diagnostic, not gating** — surfaces latent bugs; doesn't approve or block anything.

- **For code that already runs** — inherited scripts, long unattended jobs, post-mortems without clean repros.

- **Three passes (five phases)** — scope, flow map, failure trace, dependency map, report.

- **Six flags in the failure trace** — silent swallow, cascade, timeout mismatch, counter drift, wasted work, implicit assumptions.

- **Output is a structured report** — flow map + ranked failures + dependency surface + plain-language summary.

- **Tuned for long-running jobs** — exactly the bugs that hide until hour 3 of a 4-hour render.
