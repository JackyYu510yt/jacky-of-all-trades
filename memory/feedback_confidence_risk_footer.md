---
name: confidence-risk-footer
description: "Every /explain, /auto, /prep, /spec report ends with CONFIDENCE + RISK lines (HIGH/MED/LOW + evidence); anything pending/unverified caps confidence below HIGH"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ebc6e6ed-9992-4cc1-8fb3-8e137a5d94c3
  modified: 2026-08-13T01:15:24.679Z
---

Every report from /explain, /auto, /prep, and /spec must END with two lines:

```
CONFIDENCE: HIGH | MEDIUM | LOW — <what was verified directly vs inferred/assumed>
RISK: HIGH | MEDIUM | LOW — <what's exposed if this report is wrong; which parts are unproven>
```

**Why:** On 8/12/26 the user nearly closed a chat believing thumbnail work was "all done" because the NET line read as complete — but 6 thumbnails were still wrong/waiting on a dead external service. False confidence in summaries makes the user act on unfinished work. The footer forces the report to grade its own trustworthiness so a re-read catches it.

**How to apply:**
- Confidence rates VERIFICATION, not optimism. HIGH = every load-bearing claim directly observed this session (output read, file opened, screenshot read). Inferred/secondhand → MEDIUM. Assumed → LOW.
- Hard cap: any "waiting", "queued", "retrying", "should", "expected", or external-dependency claim anywhere in the report → CONFIDENCE cannot be HIGH. If the status says DONE but the cap applies, the STATUS is wrong — downgrade the status, never inflate the grade.
- A bare grade is invalid — the dash and one-line evidence clause are mandatory.
- Codified in: /explain (basics + final check), /auto (report contract + all 3 final templates + TL;DR), /prep (FINAL VERDICT card rows + rules), /spec (footer section under Evidence discipline).

Related: [[see-it-before-you-call-it]], [[probe-dont-assume]], [[evidence-first-error-recon]]
