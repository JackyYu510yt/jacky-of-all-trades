---
name: function-author-subagent
description: Load-bearing functions get a dedicated author subagent — never one-shot them inline; codified in /auto Sub-agent Delegation (2026-08-15)
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5e03d2e8-2557-44ea-8409-512ba348bc88
  modified: 2026-08-15T11:03:29.174Z
---

The user found that /auto one-shotting functions inline produces "simple, usually shitty" implementations — the driver is juggling the whole run and gives each function minimal attention.

**Why:** attention is the scarce resource; a fresh subagent with one job + an explicit context packet writes materially better functions than a distracted driver.

**How to apply:** codified in /auto SKILL.md ("Function-author sub-agent" under Sub-agent Delegation). Variant D chosen by the user: fires on RISKY//prep-tagged or checklist-classed functions at write time, PLUS auto-escalation after 2 failed fix-mode approaches when the diagnosis implicates the function itself. Bounds: max one write-time + one escalation dispatch per function; driver is the only file writer; verify remains the oracle; driver reads returned code for exception-swallowing before accepting (applies to INLINE writes too). Passed independent [[audit-skill-loop]] review (AUDITOR + RED-TEAM) before landing.

Upgraded 2026-08-15 (user: "worried the judgment could be wrong for important stuff"): importance is now a mechanical checklist (subprocess/ffmpeg, network/disk I/O, transforms user data, retries/recovery, hot path; YES or UNCERTAIN → AUTHOR — ties always promote), every function gets an AUTHOR/INLINE label + reason in the runbook's `Functions:` block, one reviewer subagent audits the INLINE list with unconditional promotion written back into the block, `Classified:` status field survives compaction, mid-run-born functions get checklist-classified at write time, labels ratchet promote-only. Second audit round (AUDITOR + RED-TEAM) passed before landing.
