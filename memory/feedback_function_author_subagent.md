---
name: function-author-subagent
description: Load-bearing functions get a dedicated author subagent — never one-shot them inline; codified in /auto Sub-agent Delegation (2026-08-15)
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5e03d2e8-2557-44ea-8409-512ba348bc88
  modified: 2026-08-15T10:50:06.767Z
---

The user found that /auto one-shotting functions inline produces "simple, usually shitty" implementations — the driver is juggling the whole run and gives each function minimal attention.

**Why:** attention is the scarce resource; a fresh subagent with one job + an explicit context packet writes materially better functions than a distracted driver.

**How to apply:** codified in /auto SKILL.md ("Function-author sub-agent" under Sub-agent Delegation). Variant D chosen by the user: fires on RISKY//prep-tagged or core-logic functions at write time, PLUS auto-escalation after 2 failed fix-mode approaches when the diagnosis implicates the function itself. Bounds: max one write-time + one escalation dispatch per function; driver is the only file writer; verify remains the oracle; driver reads returned code for exception-swallowing before accepting. Passed independent [[audit-skill-loop]] review (AUDITOR + RED-TEAM) before landing.
