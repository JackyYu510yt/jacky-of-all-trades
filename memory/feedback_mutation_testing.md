---
name: mutation-testing
description: "A test only proves something if it fails when the fix/check it protects is reverted — prove that on a copy before trusting the test's pass"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3956edc8-4fe6-4214-9b58-cd342615bc53
  modified: 2026-09-11T01:25:38.100Z
---

A passing test proves nothing by itself — a test that always passes would
pass here too. The proof is a **mutation test**: take the change back OUT,
on a copy, and re-run the same test. It must now FAIL. Only a test that can
say NO has said anything by saying YES.

**Why:** stated by the user 2026-09-10 as "gold" after a plain explanation
of mutation testing, mid-conversation. This session had already been doing
exactly this, unnamed, throughout the `/auto` rebuild (M2/M3/M4): `check_exit.py`'s
each check was proven with a deliberately-broken `RUN.md` fixture; `lanes.py`'s
own test suite caught a real parser bug (header prose parsed as a phantom
row) specifically because a case existed that should have failed and didn't
until fixed. Naming the technique is what makes it something a future run
reaches for on purpose instead of stumbling into by habit.

**How to apply:** whenever a test or check is written to prove a fix, a
feature, or a validator works, don't stop at "it passes now" — revert the
change on a copy and confirm the SAME test now fails. If it still passes,
the test doesn't discriminate and proves nothing (this is the concrete,
mechanical form of [[discriminating-tests]] — that memory is the general
principle, this is the specific move: don't just avoid a test that both
hypotheses would pass, actively PROVE it can say NO by making it say NO
once, on the broken version). A whole test SUITE earns the same treatment
at the check level: each individual check/assertion should have its own
deliberately-broken fixture proving THAT check, not just the suite overall.

Codified 2026-09-10 in `~/.claude/skills/auto/SKILL.md` (Evidence capture)
and `~/.claude/skills/repair/SKILL.md` (What Counts as Conclusive Evidence).
Related: [[discriminating-tests]], [[pin-the-fix]], [[probe-dont-assume]].
