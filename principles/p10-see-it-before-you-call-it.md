## Principle 10 — See it before you call it

**Rule:** When a check's result is something you can *see* — a rendered page, an app window, a generated image — confirm it by reading a screenshot before you trust it. A passing exit code or a matched log string is not proof on a visual surface. Capture the shot inside the test at each state-change and assertion, and read it before declaring pass or fail.

**One-line form:** If the answer is visible, look at it. Exit 0 is not a pass on a screen.

### When it applies

- Writing or running a smoke test / verify step against a browser, a GUI app, a rendered frame, or any surface a human would *look* at to judge.

- Warmup / readiness checks that decide "this account / session / page is good to go."

- `/auto`, `/prep`, `/repair` runs that gate a step on a visual outcome.

- Trigger phrases: "is it logged in?", "did the page load?", "did it render?", "smoke test the UI", "check the screen", "is the account ready?", "did the image generate?".

### Failure modes this catches

- **Present-but-unread shot** — a screenshot was captured but the verdict was read off log text instead of the image. The exact account-95 miss.

- **Exit-0 illusion** — a signed-out page shows a prompt box and exits 0 just like a signed-in one; the machine check passes while the real state is wrong.

- **Weak visible assertion** — the check tests "an element exists" when that element exists in both the good and bad state (a prompt box on signed-in AND signed-out pages).

- **Text-trusting** — believing the page's own words ("image creation isn't available in your location") over what the screenshot plainly shows ("Sign in").

### Check / gate before claiming done

1. **Is this verdict about something visible?** — if a human would look at it to judge, a screenshot must be read before pass/fail.

2. **Was the shot captured at the assertion, inside the test?** — built-in capture at the state-change/assertion, not a slow after-the-fact grab.

3. **Did I actually read it, with a written one-line verdict?** — a missing read makes the verify INCONCLUSIVE (blocked), never a silent pass.

4. **Does the visible assertion distinguish the good state from the bad one?** — "element exists" fails this if it's true in both; tighten it AND read the shot.

### Common invalid patterns

- Warmup asserts READY because a prompt box exists; the page is actually signed out → invalid (exit-0 illusion + weak assertion).

- Screenshot saved to disk but the verdict drawn from the reply text → invalid (present-but-unread).

- Headless run can't screenshot, so the visual verify "passes" on an artifact probe → invalid (a signed-out page has a valid artifact too — that's INCONCLUSIVE, not pass).

### Hard NOs

- Do not declare a visual check passed from an exit code or log string alone.

- Do not trust a page's text over a screenshot of the page.

- Do not treat a captured-but-unread screenshot as if it were read.

- Do not let "must look" stay a promise — make it a recorded per-shot verdict, or the step fails.

### Origin

Surfaced 2026-06-18 from the account-95 incident: an autonomous run concluded "new-build accounts can't generate images" from a page's text reply, when the captured screenshot plainly showed the account was simply signed out. The shot existed and was never read; the readiness check only looked for a prompt box, which a signed-out page also shows. Two holes — present-but-unread shot and a weak visible assertion — that this principle closes. Encoded into `/auto` (Hard Invariant #11 + the Smoke-test/verify capture subsection) and `/prep` (visual smoke capture in the build + pentest phases).


`========================================`
