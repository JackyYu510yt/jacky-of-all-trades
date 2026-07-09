# How this backup works (plain-language guide)

This one GitHub repo holds your **entire Claude Code setup** — your custom
skills, your memory, your hooks, and your settings. Clone it to any Windows PC,
run one script, and you're back exactly where you left off.

Repo: https://github.com/JackyYu510yt/jacky-of-all-trades

---

## The idea, in everyday terms

Think of the repo as a **suitcase**.

- `git push` = send your packed suitcase up to GitHub.
- `git pull` / `git clone` = bring the suitcase down to a PC.

But Claude doesn't read from the suitcase. It reads from specific **drawers**:

- it runs hooks from `~/.claude/hooks/`
- it reads settings from `~/.claude/settings.json`
- it keeps memory under `~/.claude/projects/.../memory/`

So we use **shortcuts**. A shortcut (a "junction") makes a drawer point straight
at the suitcase — so the drawer and the suitcase are the *same thing*. Change one,
you've changed both. That's why a `git pull` updates your live setup instantly,
with no copying.

- **Hooks** → shortcut into the repo ✅
- **Memory** → shortcut into the repo ✅
- **Settings** → it's a single file (not a folder), which can't be shortcut as
  cleanly, so it's *copied* into place once at setup. It barely ever changes, and
  the auto-commit hook keeps the backup copy current.

---

## What's in the suitcase

```
<skill folders>/   your custom skills (auto, spec, audit, ...)
memory/            your memory files + MEMORY.md index
hooks/             your hook scripts
config/            a copy of settings.json
setup.ps1          the one-command setup for a fresh PC
GUIDE.md           this file
```

**Never** in the suitcase (secrets / throwaway — stay on the PC only):
your login token, conversation transcripts, caches.

---

## Everyday use

- **Save your work to GitHub:** just tell Claude **"push"**. (Your changes are
  auto-committed when each chat ends, so they're ready to go up.)

- **Get your latest setup onto a PC that's already set up:**
  ```
  git -C "%USERPROFILE%\.claude\skills" pull
  ```
  Hooks and memory update live immediately (they're shortcuts). If settings
  changed, re-run `setup.ps1` to refresh the copied file.

---

## Brand-new PC (two commands)

```
git clone https://github.com/JackyYu510yt/jacky-of-all-trades "%USERPROFILE%\.claude\skills"
powershell -ExecutionPolicy Bypass -File "%USERPROFILE%\.claude\skills\setup.ps1"
```

Then restart Claude Code and log in again (your token isn't backed up).

`setup.ps1` figures out paths from its own location, so it works even on a PC
with a different username — though a few paths are hardcoded as `C:\Users\Shadow`
(it will warn you and tell you what to fix if your username differs).

---

## The easiest way: hand this to an LLM

If you don't want to think about any of the above, paste the prompt below to a
fresh LLM that can run commands on the new PC. It will do the whole setup and
check its own work.

> ### Handoff prompt — copy everything between the lines
>
> ---
>
> I'm setting up my Claude Code configuration on this Windows PC from my GitHub
> backup. Please do this for me and verify each step as you go.
>
> Background: all my Claude Code config (custom skills, memory, hooks, settings)
> lives in one GitHub repo: https://github.com/JackyYu510yt/jacky-of-all-trades
> It gets cloned into my Claude folder, then a setup script wires the hooks and
> memory folders as live links (junctions) pointing into the repo, and copies
> settings.json into place.
>
> Steps:
> 1. Check git is installed (`git --version`); if not, install it.
> 2. Clone the repo into my Claude skills folder:
>    `git clone https://github.com/JackyYu510yt/jacky-of-all-trades "$env:USERPROFILE\.claude\skills"`
>    If that folder already exists and isn't empty, stop and ask me first.
> 3. Run the setup script:
>    `powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.claude\skills\setup.ps1"`
> 4. Read what the script printed. If it warns my Windows username isn't "Shadow",
>    then replace every `C:\Users\Shadow` with my real home path inside
>    `settings.json`, `hooks\repo-autocommit.ps1`, and `setup.ps1`, and tell me.
> 5. Verify: confirm that `$env:USERPROFILE\.claude\hooks` and my project memory
>    folder are junctions pointing into `...\.claude\skills`, and that
>    `$env:USERPROFILE\.claude\settings.json` exists.
> 6. Tell me to restart Claude Code and log in again (my credentials are NOT in
>    the backup, by design).
>
> After setup, to pull my latest config later:
> `git -C "$env:USERPROFILE\.claude\skills" pull` (hooks + memory apply live).
>
> ---
