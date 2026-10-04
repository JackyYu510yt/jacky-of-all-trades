---
name: paste-this-answers-the-question
description: "SUGGESTED ACTION v3: PASTE THIS answers the question actually asked this turn (on a pick → the pick, not the after-pick work prompt); → TOWARD THE GOAL is a plain-words chain not a lens tag; → HEAVEN'S NET on a pick = seen evidence + what ruled others out + how we'd know if wrong + bounded fallback, never n/a"
metadata:
  type: feedback
---

When a turn ends on a decision the user must make (Choice 1 vs 2, Option A/B, pick a variant), the footer's PASTE THIS line must be the **answer to that question** — e.g. `"Go with Choice 2 — fix the lanes in the live folder, re-sync the factory copy after."` — in the user's voice, one line of why. The prompt for the work that follows the pick belongs to the NEXT turn, after they've chosen.

**Why:** 8/22/26 — asked "explain the choices again" (factory-vs-live folder), the footer's PASTE THIS jumped ahead to "Fix the image lanes in …" — a prompt for the step after the decision. User: "the suggested action doesn't really make sense with what I asked — it should have suggested 'Option B' since that was the actual question." A suggested action that skips the question on the table reads as drift and can't be pasted as-is.

Same turn, the two arrow lines were also called out: "→ TOWARD THE GOAL: Moves NEXT; pushes Delivers and Heals" names lenses without saying HOW the move gets closer to the goal, and "→ HEAVEN'S NET: n/a" dodges why this pick is the right, most thorough, evidence-backed option we can proceed on with confidence. User-confirmed fix (8/22/26):
- → TOWARD THE GOAL = a chain in plain words: this move → gets us <concrete thing> → which is what <lens> needs because <why>, per lens pushed — plus what the rejected option would have cost ("Choice 1 would spend today moving folders and ship zero images").
- → HEAVEN'S NET on a pick = (1) the SEEN evidence the pick stands on (diffs run, files read, backups found), (2) what the other options were ruled out on — same evidence, (3) how we'd know fast if the pick is wrong + the bounded fallback (nothing deleted, other option still open); anything unchecked NAMED. "n/a" is only valid on a work step with no recovery logic — never on a pick.

**How to apply:**
- Before writing PASTE THIS, name the question this turn was answering. If it was a *which-one* question, PASTE THIS = the pick + one-line reason. If it was a *do-it* request, PASTE THIS = the next work prompt (existing rule).
- Still one move, not a menu — the pick IS the one move.
- Pairs with [[pick-from-options]] (show variants, user picks) and [[leaning-toward-not-authorization]] (a pick is the user's explicit authorization; don't pre-write the work as if already chosen).
- v3.1 (8/27/26) added a fourth line to the block: a SUGGESTED ACTION **FEYNMAN** closing it — the choice re-told in kid words (why this move won / what we passed on / what happens if wrong), the plain-words twin of these two arrows. Never a repeat of the CURRENT STAGE FEYNMAN. Backups: ~/.claude/skills/_backups/footer-v3.1-20260827/.
- Canonical footer lives in [[confidence-risk-footer]]; wired 8/22/26 into /explain (template + rules), /auto (contract template, compass rule, 3 inline DONE/PARTIAL/STUCK templates — STUCK variant: 'recommended pick + why' when the block is a user decision), /prep (card + compass rule), /spec (block + paragraph). Backups: ~/.claude/skills/_backups/footer-v3-20260822/.
