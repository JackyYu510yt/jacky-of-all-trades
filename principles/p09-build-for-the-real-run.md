## Principle 9 — Build for the real run

**Rule:** Design for the conditions the thing will actually meet in real use — real input size, real run duration, unattended execution, messy/missing inputs, resource limits, and recovery after partial failure. A passing demo is not the finish line; the real job completing under real conditions is. This applies ONLY to conditions you can prove will occur in this use case — speculative "might happen someday" robustness is a P5 (KISS) violation, not practicality.

**One-line form:** Build for the real job, not the demo. Real conditions only — not imagined ones.

### When it applies

- Anything that will run on real data: big files, long jobs, batch pipelines, renders.

- Anything that runs unattended — `/auto`, cron, overnight jobs, no human at the keyboard.

- Before declaring DONE on code that worked once on a small/clean input.

- Trigger phrases: "run it for real", "this runs overnight", "the real file is huge", "set and forget", "it died at 3am", "works on my test clip but not the real one", "it filled the disk", "it hung halfway".

### Failure modes this catches

- **Demo-scale fit** — verified on a 3-second clip; the real input is a 4GB file and the memory/disk/time profile is completely different. (Pairs with P1 — test the real condition; P9 is the design-time half of that.)

- **No recovery** — a 10-hour job dies at hour 9 with no checkpoint, so the whole run is lost. Real long jobs need resume points and bounded retries.

- **Blocks unattended** — an `input()` prompt, a confirmation gate, or an unhandled prompt mid-pipeline that stalls a job nobody is watching.

- **Resource blindness** — disk fills, pagefile exhausts, memory blows up, temp files never cleaned. The DWM-crash class of failure.

- **Messy-input fragility** — assumes inputs are present, well-formed, and correctly encoded; the real corpus has gaps, garbage, and odd encodings.

- **No progress visibility** — a long unattended run gives no signal whether it's working, stuck, or dead, so failure is discovered hours late.

### Check / gate before claiming done

Answer each in one sentence. If any answer is "only the demo case", the design isn't done.

1. **What does the REAL input look like?** Size, count, duration, messiness. Did I verify against that, or against a convenient small/clean proxy? (Feeds P1.)

2. **How long does the real run take, and what happens if it dies partway?** If there's no checkpoint/resume and the job is long, that's a gap.

3. **Does this run unattended?** If yes, is there any `input()` / confirmation / prompt that would stall it? Are retries bounded and self-healing?

4. **What real resource limit could it hit?** Disk, memory, pagefile, time, rate limits. Is the limit handled or at least surfaced?

5. **Can someone tell it's alive?** Is there progress/heartbeat output for a long run?

6. **Is every safeguard tied to a condition I can prove will occur?** If a safeguard defends an imaginary case, cut it — that's P5, not P9.

### Common invalid patterns

- "Works" claimed after one run on a clean 5-row sample; real input is 5M messy rows → invalid.

- A long render with no checkpoint, so a crash at 90% restarts from zero → invalid.

- An unattended `/auto` job that hits `input()` and silently waits forever → invalid.

- Temp files written every iteration, never cleaned, disk fills mid-run → invalid.

- Adding retries/fallbacks/guards for failure modes that cannot occur → invalid (P5, not P9 — practicality is not a license to overbuild).

### Hard NOs

- Do not declare done after testing only the demo-scale, clean-input case.

- Do not ship a long unattended job with no checkpoint, no bounded retries, and no progress signal.

- Do not leave an `input()`/confirmation in a path that runs unattended.

- Do not ignore a provable resource limit (disk/memory/pagefile/time).

- Do not invoke "practicality" to justify handling a condition you cannot show will occur — that is a KISS violation wearing this principle's name.

### Worked examples

**A — Demo-scale vs real run**

Situation: A frame-extraction script works on a 10-second test clip.

- ❌ "Works — done." Real input is a 2-hour 4K file; it OOMs at minute 12.

- ✅ Profile against a realistic file first. Stream/chunk instead of loading whole. Verify at real scale (P1). THEN done.

**B — Long job, no recovery**

Situation: An overnight batch renders 500 clips sequentially.

- ❌ One loop, no state. Crash at clip 480 → all 480 redone.

- ✅ Checkpoint completed clips to disk; on restart, skip done ones; bounded retry per clip. (Pairs with the retries-are-optimization memory.)

**C — Practicality misused (the anti-example)**

Situation: A one-shot local script that reads one config file you control.

- ❌ Wrap config load in retry-with-backoff and three format fallbacks "to be practical".

- ✅ Just read the file. The failure modes don't occur here — P5 wins. P9 only fires on conditions you can prove will happen.

### Relationship to the other principles

- **P1** tests the real condition; **P9** is the design-time mandate to build for it. P9 decides what real conditions matter; P1 proves you actually exercised them.

- **P5 (KISS)** is the hard boundary. P9 justifies robustness for proven conditions; P5 forbids it for speculative ones. The dividing line — "can I prove this occurs?" — is what keeps P9 from becoming an overengineering loophole.

- **P4** audits state vs goal at handback; P9 adds the operational rows to that audit (real scale hit? survives unattended? recovers?).

### Origin

Surfaced 2026-06-08. The user's recurring burns are operational, not algorithmic: the DWM crash from commit/resource exhaustion, long video/ffmpeg jobs needing checkpoint+resume, and unattended `/auto` runs that must not stall on a prompt. P1–P8 covered honest testing, goal-tracking, and code restraint, but none made "does it survive the real job under real conditions" a checkpoint at design time. P9 does, with a hard P5 boundary so practicality strengthens robustness without reopening the overengineering door.


`========================================`
