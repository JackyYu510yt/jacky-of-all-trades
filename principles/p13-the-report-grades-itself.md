## Principle 13 — The report grades itself

**Rule:** Every report ends with a state block, a goal-compass and a self-grade — one blank line between every field, labels fixed, explaining text plain-language (layout confirmed 8/22/26): NET (where things stand now); CURRENT STAGE (BEFORE / NOW / CHANGED with WHY / NEXT — the immediate milestone / MEANT TO — what NEXT achieves + the problem it fixes / FEYNMAN — NEXT to a smart 12-year-old with one analogy, naming the Heaven's Net fit and the goal fit); a 4-lens ULTIMATE GOAL derived fresh per scenario (Delivers / Heals / Replaces / Guarantees); a USER OPTION block — present ONLY when the turn puts a decision to the user, omitted entirely otherwise — laying out each choice with its cost, balanced `+` pros and `−` cons, and a HOLDS UP line judging it on FUTURE runs (next run, different input, nobody watching; what it costs to maintain; what breaks later — band-aids named as band-aids, and a structurally better option not on the original list must be added rather than skipped), exactly one option marked ← RECOMMENDED on the HOLDS UP reads first and cost second, closing with IF YOU SAY NOTHING and a WHY THAT DEFAULT that argues on structure rather than speed; one SUGGESTED ACTION (PASTE THIS — a self-contained prompt the user pastes verbatim; → TOWARD THE GOAL — which lens(es), how it advances NEXT; → HEAVEN'S NET — class-keyed recovery, evidence-only, bounded, fail-loud per the canonical error-recon definition, or n/a; FEYNMAN — the CHOICE in kid words, one everyday analogy, three beats: why THIS move won, what we passed on, what happens if it turns out wrong, never a repeat of the CURRENT STAGE FEYNMAN); a CONFIDENCE grade (PERFECT / HIGH / MEDIUM / LOW) with named evidence; and a RISK grade naming the exposure and the unproven parts. The canonical template lives in /explain; /auto, /prep, /spec mirror it.

**One-line form:** A report you can't grade is a report you can't trust — the footer IS the grade.

### When it applies

- Every report from /explain, /auto, /prep, /spec — and any end-of-task summary or DONE claim anywhere.

- Trigger phrases: any status report, any "done/finished/fixed" claim, any NET line, any handback.

### Failure modes this catches

- **False confidence** — a summary reads "all done" while work is pending or unverified; the user acts on it and closes the chat.

- **Goal drift** — the stated goal quietly rewords itself toward whatever got achieved, so partial work grades as complete.

- **Buried live wires** — a dangerous unknown (unverified claim touching production) hides mid-report instead of being named on the risk line.

- **Aimless next moves** — a suggested action that doesn't advance the user's actual goal (tangent work dressed as progress).

### Check / gate before claiming done

1. **Is the footer present and complete?** — NET; CURRENT STAGE with all six lines (BEFORE / NOW / CHANGED / NEXT / MEANT TO / FEYNMAN); all four lenses filled (or "n/a — why"); USER OPTION present iff the turn puts a decision to the user, with all four fields per option (option+cost / `+` / `−` / HOLDS UP), exactly one ← RECOMMENDED, plus IF YOU SAY NOTHING and WHY THAT DEFAULT — and PASTE THIS naming that same recommended option (the ECHO RULE; a mismatch means the report is wrong); SUGGESTED ACTION with PASTE THIS + → TOWARD THE GOAL + → HEAVEN'S NET + FEYNMAN ("n/a" allowed, never skipped); both grades with evidence clauses; one blank line between every field.

2. **Does the confidence grade survive the hard cap?** — anything waiting/queued/retrying/"should" anywhere in the report → below HIGH. PERFECT only with every angle tested (happy + failure paths, real inputs) AND proven full-autopilot (no human thought, no human intervention, no Claude in the loop) AND an independent breaker-check failed to break it — tests named.

3. **Does the goal block match the user's original ask?** — compare against what the user actually said, not what got built. Frozen once stated.

4. **Does the risk line name the live wire?** — every unproven claim that touches production/user-facing output is called out, not summarized away.

### Common invalid patterns

- Bare grade with no evidence clause ("CONFIDENCE: HIGH") → invalid

- PERFECT without a named unattended-run proof → invalid

- Status DONE + confidence capped by pending work → the STATUS is wrong; downgrade the status, never inflate the grade

- Goal lens filled with abstract boilerplate ("the system operates autonomously") → invalid; lenses use the user's concrete style (real actors, real stakes, good state vs bad state, consequences)

### Hard NOs

- Do not reword the frozen ULTIMATE GOAL toward what was achieved.

- Do not award PERFECT on faith, inference, or "should work" — it requires empirical proof of full-autopilot operation.

- Do not suggest an action whose connection to the goal can't be stated in the same line.

### Origin

Adopted 2026-08-13 from the thumbnail-pipeline aftermath: the user nearly closed a chat on a false "all done" reading (P12's origin incident), then asked for reports to carry their own trust-gauge — a confidence/risk footer, a PERFECT tier meaning "full autopilot, no human thought, no human intervention," and a per-scenario goal compass so drift is visible at a glance. Codified in /explain, /auto, /prep, /spec + the confidence-risk-footer memory; this principle is the canonical statement.


`========================================`
