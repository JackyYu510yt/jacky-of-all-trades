## Principle 7 — Surgical changes

**Rule:** Touch only what the user's request requires. Don't drive-by improve adjacent code, comments, or formatting. Don't refactor things that aren't broken. Match the existing style even if you'd write it differently. If you notice unrelated dead code or bugs, *mention* them — don't delete or fix them silently. Clean up only the orphans your own change creates.

**One-line form:** Every changed line traces to the request. Mention strays. Don't fix them.

### When it applies

- Editing existing code anywhere — single function, single file, multi-file refactor.

- Approving a fix for a specific bug or completing a specific feature ask.

- Working in code that you didn't write, or code with a style you'd personally do differently.

- Running `/auto` or `/loop` where the temptation to "tidy while I'm in here" compounds.

- Trigger phrases: "fix X", "update Y", "change Z", "while I'm here", "I noticed…", "I also cleaned up…", "I improved…", "I refactored some adjacent code", "I fixed a typo I saw", "I removed unused imports while I was at it" — any phrasing that signals expanding beyond the asked-for scope.

### Failure modes this catches

- **Drive-by improvement** — reformatting, renaming, restructuring code that wasn't part of the ask. Bloats the diff, hides the real change, breaks `git blame`.

- **Style imposition** — replacing the file's existing patterns with the patterns I prefer (e.g. f-strings → `.format()`, list comprehension → for-loop, or vice-versa). Match what's there.

- **Silent dead-code deletion** — finding pre-existing unused imports / functions / branches and deleting them without being asked. May be load-bearing in ways not visible from the file (re-exported, monkey-patched, used by tests).

- **Side-quest fix** — noticing an unrelated bug, fixing it, shipping it in the same change. The fix may be wrong, untested, or politically not yours to make.

- **Refactor-by-stealth** — restructuring "while I was here" — extracting helpers, splitting functions, rearranging order. Even when the result is "better", the user didn't ask, and now the diff isn't reviewable as a fix.

- **Comment churn** — rewording comments to "clarify" them. Comments often encode context the original author had and you don't.

- **Orphan neglect (the one error in the OPPOSITE direction)** — removing a function but leaving its now-unused import, or renaming a thing but leaving five callers stale. Your change made these orphans; you must clean them.

### Gate before staging the diff

Answer each in one sentence. If any answer is "no" or "I added some extras", trim the diff.

1. **Does every changed line trace directly to the user's request?** If a line was changed for any other reason, revert it.

2. **Did I match the file's existing style — naming, indentation, idiom, comment voice — even where I'd personally write it differently?** If no, conform.

3. **Did I touch any pre-existing dead code or pre-existing bugs?** If yes, revert the touch and instead **mention** it in the response. Do not delete pre-existing dead code silently.

4. **Did my changes create orphans (now-unused imports, variables, functions, callers, type stubs)?** If yes, clean them up — those ARE part of the request, transitively.

5. **Is the diff reviewable as a single intent?** If a reviewer would have to ask "what is THIS line doing in here?", that line is drift.

### When mentioning vs fixing

The rule for things you noticed but weren't asked to touch:

- **Mention** — in the response: "noticed `legacy_helper` is unused at the top of `users.py` — left it untouched, flag it if you want a cleanup pass."

- **Don't fix** unless: (a) the user asked, (b) it's directly blocking the asked work, or (c) it's an orphan your own change created.

- **For genuinely critical issues** (security hole, data-loss bug) — surface immediately and ask, don't silently patch.

### Common invalid patterns

- Asked to fix a bug in `process_order`; I also reformat `validate_inventory` because "it was inconsistent" → invalid.

- Asked to add a feature; I delete three unused imports I noticed → invalid (P7 violation, even though linters would agree).

- Asked to rename `userId` to `user_id`; I also change `customerId` to `customer_id` "for consistency" → invalid (different name, different ask).

- Asked to fix a typo in a docstring; I rewrite the whole docstring "to make it clearer" → invalid.

- Asked to update a function; I "simplify" the function above it because it caught my eye → invalid.

- I notice a small bug while doing the asked work; I fix it inline without mentioning → invalid (mention, then ask).

- I make a change that leaves an import unused; I leave the import there → invalid in the OTHER direction (orphans I created are mine to clean).

### Hard NOs

- Do not change a line that doesn't trace back to the user's specific request.

- Do not "improve" working code that wasn't part of the ask.

- Do not impose your preferred style on a file that has its own style.

- Do not delete pre-existing dead code, comments, or branches silently — mention them and let the user decide.

- Do not bundle a side-quest fix into a focused change. If you notice something, surface it as a separate item.

- Do not reword comments unless the comment was wrong, the code it documents has changed, or the user asked.

- Do not leave orphans your own change created. Clean those.

- Do not use "I was already in the file" as justification. Being in the file is not authorization to edit beyond scope.

### Worked examples

**A — Asked to fix one function**

User: "fix the off-by-one in `paginate()`."

- ❌ Fix the off-by-one. Also rename the variable `lst` to `items` because it reads better. Reformat the docstring. Add a type hint that wasn't there before. Ship.

- ✅ Fix the off-by-one. Nothing else. If the docstring is now wrong because of the fix, update it (that's an orphan from my change). If the docstring was already wrong before my fix, mention it: "docstring also says page=0 returns first page; with this fix it returns empty. Want me to update the docstring too?" Wait for a yes.

**B — Mention dead code, don't delete**

While fixing a bug, I notice `_legacy_format()` is defined but never called.

- ❌ Delete `_legacy_format()` along with the bug fix.

- ✅ Bug fix lands. Response includes: "noticed `_legacy_format()` (line 142) appears unused — left it; flag if you want it removed in a follow-up." User decides.

**C — Style match, not style upgrade**

File uses `.format()` strings throughout. I'm adding a new line that builds a string.

- ❌ Use an f-string because they're "more modern".

- ✅ Use `.format()` to match the file. If `.format()` is genuinely worse for this case (e.g. multi-line, complex expressions), say so once and ask: "the rest of the file uses .format() but this expression has 4 nested calls that read cleaner as f-strings — match-the-file or pick-the-cleaner?"

**D — Orphan cleanup IS part of the change**

User asks me to remove the `legacy_auth` function.

- ❌ Remove the function, leave the `from .legacy_auth import legacy_auth` import in three other files because "the user only asked about the function".

- ✅ Remove the function AND every now-stale import / caller / test that becomes dead because of the removal. Those orphans were created by my change, so they're mine to clean. Stop at code that was *already* unused before my edit — mention those, don't delete.

**E — Side-quest bug, surfaced not bundled**

While adding pagination to `/videos`, I notice `/users` has a SQL injection.

- ❌ Patch the SQL injection in the same PR. Mention it in passing in the description.

- ✅ Pagination ships clean. Response: "🚨 separate from this change — `/users/search` (line 88 of `users.py`) builds SQL with f-string interpolation of the `q` param, which is a SQL injection. Recommend handling that as its own focused change. Want me to write a dedicated patch?" The severity earns immediate surfacing; the *fix* still gets its own review.

### Relationship to the other principles

- **P3** keeps every action traceable to the goal. **P7** keeps every *line of the diff* traceable to the request — same discipline, applied to the diff instead of to the work.

- **P5 KISS** says don't add layers without a reason. **P7** says don't add CHANGES without a reason. Together: nothing in the code or in the diff exists without justification.

- **`strict-mode` skill** is the runtime tool for applying P7 to a specific change. This principle is the standard; `strict-mode` is the procedure. (If `strict-mode` is active, P7 is implicitly active too.)

- **`audit` skill** runs before risky changes ship. It checks scope-match against the discussed intent — that check IS a P7 application.

### Origin

Adopted 2026-04-25 from Andrej Karpathy's CLAUDE.md (forrestchang/andrej-karpathy-skills, principle #3 "Surgical Changes"). Existing `strict-mode` skill already encoded most of this as a runtime-callable tool; promoting it to a Principle puts it on the same standing-checkpoint footing as P1–P6, so it applies even when `strict-mode` isn't explicitly invoked. The user's pattern of inheriting / vibe-coding into existing scripts where drive-by improvements would obscure the actual change makes this an ongoing risk, not a one-time concern.


`========================================`
