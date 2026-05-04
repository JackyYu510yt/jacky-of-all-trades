---
name: Autonomous engine, optional startup gate
description: The engine of every user script runs blind — no input() mid-pipeline. A startup gate that asks the user is OPTIONAL; some scripts auto-detect from inputs and have no gate at all.
type: feedback
originSessionId: 28253a76-4221-42b2-b184-e3b62434e2f4
---
**The non-negotiable part.** The engine — the part that does the actual work — runs blind. Once it fires, no `input()`, no `getpass()`, no "press Y to continue", no GUI dialog, no blocking on stdin. Every decision the engine would have asked about resolves from: startup-gate config (if any), env vars, CLI flags, defaults, computed-from-input-files, computed-from-state, or retry policies. Stop conditions: DONE, FAILED (irrecoverable, state preserved), or CHECKPOINT (resumable next run). Never "waiting for human input."

**The optional part.** A *startup gate* — a one-shot setup phase before the engine fires — is a tool, not a requirement. Two valid shapes:

- **Shape A — with startup gate.** Script asks the user one-shot questions ("which config?", "how many videos?", "which account?"), then the engine runs blind. Example: the user's video-generation script.

- **Shape B — no startup gate.** Script auto-detects work from inputs, queue, drop-folder, watcher state, or fixed config. No setup question; the inputs ARE the configuration. Example: the user's Jacky Rush pipeline detects whatever's in the input files and knows exactly what to do. Cron-driven workers fit this shape — schedule + queue state IS the configuration.

The shape depends on the script and pipeline. Don't force a startup gate on a script that doesn't need one.

**The user's test:** *"After whatever startup it has — does the rest of the run work without me?"* The script asking at startup OR not asking at all are both fine. The script asking mid-pipeline is not.

**Why:** The user runs long-horizon scripts (video rendering, batch ffmpeg, multi-hour jobs) on cron, overnight, or while sleeping. A script that prompts mid-run silently halts. The "engine runs blind" rule is what makes a script survivable unattended.

**How to apply:** When designing or reviewing any script, the question is "does the engine run blind?" not "is there a startup gate?" In /prep, every function gets classified as STARTUP-GATE (optional, may ask) or ENGINE (mandatory autonomy) at field 16 of the 17-field card. ENGINE functions that depend on a human decision must either move it to a startup gate (Shape A), compute it from input files / queue / state (Shape B), or use a logged default. Hard NO documented in /prep's SKILL.md.
