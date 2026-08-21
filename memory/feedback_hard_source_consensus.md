---
name: hard-source-consensus
description: "Verdicts need 2 independent signals, at least one a HARD source of truth (artifact on disk / re-read ledger / measured behavior); counters are SOFT and must reconcile against artifacts"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fa29e16c-35e4-4aef-9e9a-2006a04da2f9
  modified: 2026-08-21T06:12:24.281Z
---

User's principle (2026-08-20, their own wording): "Always look for hard sources of truth that cannot lie. Do not trust systems/signals 100%. Reach consensus — at least 2 signals, one of which must be a hard source of truth."

**Why:** The AI-Studio double-feed incident — two code paths each reported the same image to the health tracker, so accounts "confirmed" daily caps at ~13 real images instead of 25. The tally (a SOFT, system-written signal) had been silently promoted to judge; nothing ever compared it to the actual files on disk. Consensus with a hard source would have caught it on day one.

**How to apply:** Canonical text lives in `~/.claude/skills/error-recon/SKILL.md`, section "Hard Sources of Truth — the consensus bar". HARD = artifact on disk, ledger row surviving re-read, behavior measured yourself. SOFT = messages/labels/headers/exit codes AND the system's own counters/tallies. Action-driving verdicts need 2 independent signals, ≥1 HARD, wherever a hard source can exist; where none can, the entry declares it and gets conservative handling. Counters gate verdicts only with one-writer-per-fact + periodic reconciliation vs the artifact; mismatch = UNKNOWN signal (capture, park, stop loud). Related: [[heavens-net]] (the section sits beside it), [[evidence-first-error-recon]], [[pin-the-fix]].
