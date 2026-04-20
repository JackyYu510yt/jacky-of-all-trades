---
name: optimize
description: Audit a script or pipeline for speed, storage, retry, and concurrency optimizations. Scans every function in scope, classifies each as optimizable or not, applies obvious low-risk wins automatically, and interviews the user on risky or controversial changes. Use when the user says "optimize X", "make X faster", "speed up", "reduce storage", when reviewing a rendering, data-processing, or batch-job script, or any time the user wants a pipeline made more efficient without overengineering it.
---

# Optimize

Audit a script or pipeline end-to-end, then surgically improve it. Focused on KISS: the smallest change that moves the biggest dial. Complexity must earn its place. Tailors recommendations to the actual machine (CPU cores, free RAM, free disk, GPU presence) rather than giving generic advice.

## When to Use This Skill

- User says "optimize this", "make it faster", "speed this up", "reduce storage usage", "why is this slow"
- Reviewing a rendering pipeline, batch job, data-processing script, or any multi-stage script
- A long-running script is failing partway and wasting compute
- Scripts are accumulating large intermediate files or hitting disk limits
- User wants resilience (retries, checkpointing) added to a brittle pipeline

## Core Principle

**The end goal is not "make one function faster." It is: minimize total wall-clock time and wasted work across the pipeline, while keeping the script simple enough to read a month later.** A 2-hour render that fails at 80% is a bigger cost than a suboptimal flag. A pipeline that re-does unchanged work is worse than a slow preset.

## Runtime Workflow

Follow these six phases in order. Do not skip phases.

### Phase 1 — Discover the pipeline

- Start from the target script (current file, or the file the user pointed at).
- Follow imports: Python `import` / `from`, shell `source`, subprocess calls that invoke other scripts.
- Include sibling scripts in the same project directory when they appear related (same prefix, same subdir, referenced by name).
- Cap scope: if more than ~20 files would be pulled in, stop and ask the user (via AskUserQuestion) to narrow scope before continuing.

### Phase 2 — Inspect the machine (once)

Read once and cache:

- CPU cores (`os.cpu_count()` on Unix, `wmic cpu get NumberOfCores` on Windows)
- Free RAM (`psutil.virtual_memory()` if available, else `wmic OS get FreePhysicalMemory`)
- Free disk on the script's working drive
- GPU presence (`nvidia-smi`, `wmic path win32_VideoController get name`)

A simple dict is enough. Do not build a class.

```python
machine = {"cpu": 8, "ram_gb": 32, "free_disk_gb": 140, "gpu": "RTX 3070"}
```

Every recommendation in later phases must reference real values from this dict. No suggestion like "parallelize with 16 workers" if `machine["cpu"] == 8`.

### Phase 3 — Build the function inventory

- Extract every function or method definition across the in-scope files.
- For each, record: name, file, line, a one-line purpose inferred from the body or docstring, and a classification tag:
  - `optimizable` — contains loops, I/O, subprocess, network calls, ffmpeg, data crunching, retries, or algorithmic work.
  - `glue` — pure argument plumbing, trivial getters, dataclass `__init__`. Skip in later phases.
- Present the inventory to the user as a compact table before analysis. The user can cross out functions they don't care about.

### Phase 4 — Analyze each optimizable function

For each, produce an analysis block of this shape:

```
Function: transcode_batch() — pipeline.py:45
Purpose: Re-encodes N clips sequentially with libx264.
Opportunities:
  1. Swap -c:v libx264 -preset slow → h264_nvenc -preset p4
     Impact: ~8x faster on your RTX 3070. Cost: ~10% larger file.
  2. Parallelize with ThreadPoolExecutor(max_workers=min(cpu_cores, 4))
     Impact: another ~2x on batch runtime. Cost: 6 lines added.
  3. Add bounded retry + checkpoint (-f segment)
     Impact: resume from last segment on ffmpeg crash, not frame 0.
     Cost: ~10 lines, changes temp-file layout.
Risk: Medium — NVENC has quality tradeoff; parallelism could saturate disk I/O on HDDs.
```

Classify each opportunity as **Tier 1**, **2**, or **3** using the catalog below. Tier 1 is applied automatically in Phase 5. Tier 2 and 3 get interviewed.

### Phase 5 — Act

- **Tier 1 (auto-apply):** apply directly via Edit. Collect into one summary block: "Applied N low-risk changes:" followed by `file:line — what changed` per item.
- **Tier 2 and 3 (interview):** use AskUserQuestion per function. See the Interview Template section below for exact shape. Always include an "Apply nothing here" option.
- After all interviews, apply chosen changes and emit the Final Report (see template below).

### Phase 6 — Verify

- If the script has tests, run them. Do not invent tests; just run what exists.
- If no tests and a small sample input is identifiable (e.g. a `sample.mp4` referenced in the script), run the script on that sample.
- Report pass/fail. If regression, revert the last-applied batch and flag which change caused it.

## Tier Catalog

### Tier 1 — Auto-apply (no tradeoff, no risk, obvious win)

**ffmpeg:**
- Use `-c copy` when operation is pure remux/trim/concat and no re-encode is needed.
- Add `-c:a copy` when audio is untouched but video is being re-encoded.
- Replace missing or wrong `-threads N` with `-threads 0` (let ffmpeg pick).
- Use `-preset fast` instead of `-preset slow` for explicitly-named draft or preview renders.

**Python:**
- `list` → `set` or `frozenset` for repeated `in` checks.
- `pathlib.Path` over `os.path.join` string juggling.
- Generator (`yield`) over building a full list that is iterated once.
- Remove dead code (unreachable branches, unused imports, unused variables).
- Replace `open(f).read()` on large files with `for line in f` when lines are processed independently.
- Remove redundant existence checks (`os.path.exists` immediately before `open` with the check never gating anything).

**Retry (where none exists):**
- Wrap bare subprocess/network calls in a 3-attempt bounded loop with exponential backoff + jitter.
- Retry on specific transient exceptions only: `OSError`, `TimeoutError`, `subprocess.CalledProcessError` with non-zero return. Never `except Exception`.

```python
import random, time

for attempt in range(3):
    try:
        result = subprocess.run(cmd, capture_output=True, check=True)
        break
    except subprocess.CalledProcessError:
        if attempt == 2:
            raise
        time.sleep((2 ** attempt) + random.random())
```

### Tier 2 — Interview (meaningful win, modest complexity)

- **Stage fusion**: collapse N ffmpeg calls into one `-filter_complex` or concat demuxer call, removing per-call startup cost.
- **Piping between stages**: `ffmpeg ... -f rawvideo - | ffmpeg -i - ...` instead of writing and reading temp files.
- **Incremental / idempotent pipeline**: skip stages where output exists and is newer than input (Make-style).
- **ThreadPoolExecutor** for orchestrating I/O-bound subprocess batches; **ProcessPoolExecutor** only for CPU-bound Python work.
- **Encoder cycling**: NVENC for drafts or short clips, libx264 for final or archival output.
- **ffprobe / scene-detection cache** keyed on file hash, stored next to the script or in a `.cache/` dir.
- **Temp-dir rotation** across drives to avoid serializing I/O on one disk.
- **Preset / CRF sweep** on a representative sample clip, pick the quality knee, lock it for the batch.
- **Delete intermediates inside the loop**, not at script end, when disk is tight.

### Tier 3 — Interview (advanced; strongly encourage profiling first)

Before suggesting any Tier 3 change, recommend the user profile first:

```bash
python -m cProfile -s cumulative script.py | head -40
```

- **Two-pass x264/x265** encoding for archival deliverables.
- **Hardware decode + software encode** pipelines (GPU-decode, CPU-encode).
- **RAM-disk intermediates** when free RAM comfortably exceeds working-set size.
- **Retry budgets across a whole run** — cap total retry time to a percent of expected runtime, not just per call.
- **Adaptive backoff** tied to last attempt's duration (don't retry in 2s after a 20-minute attempt).
- **Per-error-type retry policy** (network: retry; invalid codec: fail fast).
- **Checkpointed long renders** with `-f segment` + concat, so a retry resumes from the last segment.
- **Personal history file** (`~/.script-stats.jsonl`) appending per-run duration, peak RAM, outcome. Future runs read it to give ETAs.

## Hard NOs — Never Suggest

These are anti-patterns regardless of how tempting they look:

- Rewriting in Rust, Cython, or Numba for a script that runs occasionally.
- Class hierarchies, abstract base classes, or plugin systems for linear pipelines.
- CLI frameworks (Click, Typer, argparse) for scripts with ≤ 2 arguments — `sys.argv[1]` is fine.
- External retry libraries (`tenacity`, `backoff`) when a 5-line `for attempt in range(3)` loop does the job.
- `async` / `await` for single-shot work or a handful of sequential subprocess calls.
- Config files + loaders for a few hardcoded paths.
- Type hints or dataclasses sprinkled across a 30-line glue script.
- Speculative error handling: `try/except` around operations that cannot meaningfully fail, generic fallbacks, or bare `except Exception` that swallows real bugs.
- `multiprocessing.Pool` wrapping ffmpeg calls — ffmpeg is already multithreaded via `-threads 0`, and the Python orchestration is not the bottleneck.
- Introducing dependencies (`numpy`, `pandas`, `psutil`) purely to shorten 5 lines of stdlib code.

## Interview Template

For every Tier 2 and Tier 3 opportunity, call AskUserQuestion with this shape:

- `header`: the function name, truncated to ≤ 12 chars.
- `question`: "Optimize `<function_name>()`? (<risk level>)"
- Option per opportunity: label = one-sentence description, description = "Impact: ... / Cost: ... / Risk: ...".
- Mark the recommended option with "(Recommended)" at the end of the label.
- Always include a final option: "Apply nothing here" with description "Skip this function and move on."

Group related opportunities for one function into one AskUserQuestion call with up to 4 options. If a function has more than 4 distinct candidates, pick the top 3 + "Skip".

## Final Report Template

After Phase 5 completes, print one block:

```
=== Optimization Report ===

Applied automatically (Tier 1):
- pipeline.py:45 — list → frozenset for extension check
- pipeline.py:78 — added bounded retry around ffmpeg subprocess
- encode.py:12  — -threads 0 added

Applied after review:
- pipeline.py:120 — switched to NVENC for draft renders (your choice)

Declined:
- pipeline.py:200 — stage fusion (user kept separate for debuggability)

Suggested follow-ups:
- Profile before touching Tier 3 items:
    python -m cProfile -s cumulative pipeline.py | head -40
- Consider adding a personal stats file after a few runs.

Machine context used: cpu=8, ram_gb=32, free_disk_gb=140, gpu=RTX 3070
```

## Judgment Calls

When a candidate change could go either way, name the tradeoff in the interview instead of silently choosing. Examples:

- "Faster encode but 10% larger file. You're already tight on disk — worth the speed?"
- "Parallel would double throughput, but your drive is HDD — I/O contention may erase the win. Want me to try anyway?"
- "Adding retry adds 8 lines. This call has never failed in your history — skip?"

The skill never hides a tradeoff behind a confident recommendation. It names the cost, gives a rough number, and lets the user decide.
