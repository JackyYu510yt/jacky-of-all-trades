---
name: confidence-risk-footer
description: "Every /explain, /auto, /prep, /spec report ends with a goal-compass (ULTIMATE GOAL / NEXT STEP / SUGGESTED ACTION) + CONFIDENCE (PERFECT/HIGH/MED/LOW) + RISK footer; anything pending caps confidence below HIGH"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ebc6e6ed-9992-4cc1-8fb3-8e137a5d94c3
  modified: 2026-08-13T09:54:21.152Z
---

Every report from /explain, /auto, /prep, and /spec must END with this block:

```
ULTIMATE GOAL (4 lenses, derived per scenario — frozen):
  Delivers:   <the finished result that arrives with zero input from the user>
  Heals:      <how failures recover or surface themselves, no human needed>
  Replaces:   <whose job/attention the system deletes — nobody left in the loop>
  Guarantees: <what wrongness is structurally impossible>
NEXT STEP: <the immediate milestone between current state and that goal>
SUGGESTED ACTION: <ONE concrete move to take now — and how it advances the next step AND the ultimate goal>
CONFIDENCE: PERFECT | HIGH | MEDIUM | LOW — <what was verified directly vs inferred/assumed>
RISK: HIGH | MEDIUM | LOW — <what's exposed if this report is wrong; which parts are unproven>
```

**Why:** On 8/12/26 the user nearly closed a chat believing thumbnail work was "all done" because the NET line read as complete — but 6 thumbnails were still wrong/waiting on a dead external service. False confidence in summaries makes the user act on unfinished work. The footer forces the report to grade its own trustworthiness. The compass (added 8/13/26) anchors every report to the user's original goal so any drift is visible at a glance.

**How to apply:**
- Confidence rates VERIFICATION, not optimism. PERFECT (added 8/13/26) = 100%-guaranteed, FULL-AUTOPILOT grade — the user's own definition: "it must work full autopilot with no human thought and no human intervention." Requires: every angle empirically tested (happy AND failure paths, real inputs at real scale), every result directly observed, zero pending items, an independent adversarial check (refuter/AUDITOR/discriminating test) tried to break it and failed, AND the autopilot itself proven — ran and recovered end-to-end with no human thought/decision/intervention and no Claude in the loop (the [[structural-fix-vs-patch]] bar: next run, different input, nobody watching, still works). The evidence clause must NAME the tests per angle including the unattended-run proof; one untested angle → HIGH at best. A false PERFECT is the worst failure the footer can commit.
- HIGH = every load-bearing claim directly observed this session, but not every angle adversarially tested. Inferred/secondhand → MEDIUM. Assumed → LOW.
- Hard cap: any "waiting", "queued", "retrying", "should", "expected", or external-dependency claim anywhere in the report → CONFIDENCE cannot be HIGH (PERFECT unreachable). If the status says DONE but the cap applies, the STATUS is wrong — downgrade the status, never inflate the grade.
- Compass anti-drift: ULTIMATE GOAL is derived fresh PER SCENARIO (per conversation/objective — not a generic principle), framed at the systems level from the user's seat (a human building automation so they never have to give input). User's chosen shape (8/13/26): ALL FOUR lenses, every report — Delivers (factory view: finished result arrives with zero input), Heals (organism view: failures recover or surface themselves), Replaces (operator view: whose job/attention the system deletes), Guarantees (structure view: what wrongness is impossible by construction). Fill every lens; a genuinely inapplicable lens gets "n/a — why", never a silent skip. Lens WRITING STYLE (user-confirmed 8/13/26 — "i like the logic and reasoning and explanation style from these examples"): concrete and first-person from the user's seat, real actors and real stakes ("me", "the VA", "at 2 AM"), good state contrasted against bad ("delivered correct" vs "wrong and quiet"), consequences stated ("one bad item never costs the other 200") — never abstract boilerplate like "the system operates autonomously". Once stated it is frozen — rewording it toward what was achieved is exactly the drift the user wants to catch. SUGGESTED ACTION is one move (not a menu) and must state how it advances both the next step and the goal; an action whose chain doesn't connect is drift and must not be suggested. Goal reached → NEXT STEP "none", SUGGESTED ACTION "nothing — goal reached".
- A bare grade with no evidence clause is invalid.
- Codified in: /principles P13 "The report grades itself" (the canonical statement, added 8/13/26), /explain (goal compass + footer section + final check), /auto (report contract + compass rules + all 3 final templates + TL;DR), /prep (FINAL VERDICT card rows + compass/confidence rules), /spec (goal-compass + footer section under Evidence discipline).

Related: [[see-it-before-you-call-it]], [[probe-dont-assume]], [[evidence-first-error-recon]]
