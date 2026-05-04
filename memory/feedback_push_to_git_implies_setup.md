---
name: "Push to git" implies setup permission
description: When user says "push to git", that's the authorization for any local git config setup (user.email, user.name) needed to complete it — don't gate on a separate permission question.
type: feedback
originSessionId: 72ba9d11-2c49-48ef-bf01-a702b3a6a340
---
When the user says "push to git" (or equivalent — "push", "ship it", "send it to git"), treat that as explicit authorization for whatever local config setup is needed to complete the push. Specifically: setting `user.email` and `user.name` in the LOCAL repo config (`git config user.email ...` without `--global`) is included in the directive.

**Why:** the user explicitly said this — *"if i say push to git, that obviously means i just gave u permisison."* Got frustrated when I gated the push twice on a separate "may I set the config" question after they had already said "push to git" two turns in a row. The CLAUDE.md "NEVER update the git config" rule is the safety default; it applies to unsolicited config changes, NOT to setup that's necessary to fulfill an explicit user directive.

**How to apply:**

- If `git commit` fails with "Author identity unknown," set the local config using identity from auto-memory (or sensible defaults if none) and re-run the commit. Don't ask first.
- Still NEVER touch `--global` config. Only `git config user.email/user.name` (no flag) which writes to `.git/config` for the current repo.
- If no identity is in memory and no sensible default exists, then ask — but that's a missing-info ask, not a permission ask.
- Other "push to git" implicit authorizations: creating an initial commit if the repo is fresh, staging untracked files that obviously belong to the session's work, fetching from remote before push if needed.

**Out of scope (still ask):**

- Force-push, push to non-default branch, push --no-verify, anything destructive
- `--global` git config changes
- Modifying remote URL
- Adding signing keys / GPG setup
