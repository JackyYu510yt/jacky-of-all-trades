---
name: auto-runs-folder-layout
description: /auto now nests ALL its artifacts under one per-run folder ./auto-runs/<slug>/ instead of scattering loose auto-* files in CWD
metadata:
  type: project
---

As of 2026-06-07, the `/auto` skill places every bookkeeping artifact for a run inside a single per-run folder: `./auto-runs/<slug>/` (runbook, log, notes, and the full Pattern 3 state set — GOAL/PROGRESS/APPROACHES/VERDICT_*/logs/). The only thing at the `auto-runs/` root is the session marker `./auto-runs/.session-<session_id>` (the hook reads it to learn the slug, so it can't live inside the slug folder it names). The working directory only ever gains ONE visible `auto-runs/` folder no matter how many runs.

**Why:** the user's tinker folders (e.g. `C:\Users\Shadow\Desktop\Testing\Account Setup`) were drowning in loose `auto-runbook-*.txt` / `auto-log-*.txt` / `auto-notes-*.md`. Their fix request: "create a subfolder and just place everything relevant inside there." Chosen shape: one visible root, per-run subfolders inside. /auto does NOT relocate files the user's own scripts produce (`_*.log`, `*.bak_*`, `__pycache__`) — only its own bookkeeping.

**How to apply:** old loose-file paths (`./auto-runbook-<slug>.txt`, `./.auto-session-<id>`, Pattern 3 `./auto-<slug>/`) are gone. Files touched in the change: `skills/auto/SKILL.md`, `skills/auto/hooks/auto-log-hook.py`, the wired `~/.claude/hooks/auto-stop-block.py` + its `test_auto_stop_block.py` (10/10 pass). Note: `~/.claude/hooks/auto-log-hook.py` is a stale UNWIRED copy on an even older layout — only `auto-stop-block.py` is wired in settings.json. Related: [[auto-stop-hook-enforcement]].
