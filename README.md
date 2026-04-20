# jacky-of-all-trades

Personal Claude Code skills. Four custom skills designed for KISS-first, ADHD-friendly, self-healing scripting work.

## What's Inside

| Skill | Purpose |
|-------|---------|
| `explain` | Explain technical things in plain language using disciplined visual formats. Bold step names, `====` separators, rainbow top row, inline term definitions, bulleted TL;DR. |
| `optimize` | Audit a script or pipeline for speed, storage, retry, and concurrency wins. Applies safe fixes automatically; interviews user on risky ones. |
| `prep` | Plan, prototype, and pentest a new script from scratch. Includes external-audit (Codex) loop before execution. |
| `repair` | Debug with strict discipline — gather evidence, lock in one cause with conclusive proof, build a standalone repro, verify the fix in isolation before touching the real code. |

---

## Install on a Fresh PC

**PowerShell / Git Bash / Mac / Linux** (the `~` is your home directory):

```bash
git clone https://github.com/JackyYu510yt/jacky-of-all-trades ~/.claude/skills
```

**Windows cmd.exe** (cmd doesn't understand `~`, use `%USERPROFILE%` instead):

```cmd
git clone https://github.com/JackyYu510yt/jacky-of-all-trades "%USERPROFILE%\.claude\skills"
```

Either way: done. Claude Code picks up all four skills on its next session.

---

## Update Later

**PowerShell / Git Bash / Mac / Linux:**

```bash
cd ~/.claude/skills
git pull
```

**Windows cmd.exe:**

```cmd
cd /d "%USERPROFILE%\.claude\skills"
git pull
```

---

## If `~/.claude/skills` Already Has Stuff

The clone above only works when the target is empty. If you already have skills there, clone elsewhere and copy the folders in manually.

**PowerShell / Git Bash / Mac / Linux:**

```bash
# Clone somewhere else
git clone https://github.com/JackyYu510yt/jacky-of-all-trades ~/jacky-of-all-trades

# Copy each skill folder into place
cp -r ~/jacky-of-all-trades/explain  ~/.claude/skills/
cp -r ~/jacky-of-all-trades/optimize ~/.claude/skills/
cp -r ~/jacky-of-all-trades/prep     ~/.claude/skills/
cp -r ~/jacky-of-all-trades/repair   ~/.claude/skills/
```

**Windows cmd.exe:**

```cmd
git clone https://github.com/JackyYu510yt/jacky-of-all-trades "%USERPROFILE%\jacky-of-all-trades"

xcopy /E /I /Y "%USERPROFILE%\jacky-of-all-trades\explain"  "%USERPROFILE%\.claude\skills\explain"
xcopy /E /I /Y "%USERPROFILE%\jacky-of-all-trades\optimize" "%USERPROFILE%\.claude\skills\optimize"
xcopy /E /I /Y "%USERPROFILE%\jacky-of-all-trades\prep"     "%USERPROFILE%\.claude\skills\prep"
xcopy /E /I /Y "%USERPROFILE%\jacky-of-all-trades\repair"   "%USERPROFILE%\.claude\skills\repair"
```

To update later: `git pull` in the cloned folder, then re-run the copy commands.

---

## Design Principles

- **KISS first.** Smallest change that moves the biggest dial.
- **Self-healing.** Every risky operation gets bounded retry, checkpointing, or atomic writes.
- **Evidence-based.** `repair` requires conclusive, replicable proof before any fix is applied.
- **Plain language + learning.** Technical terms appear with inline definitions; TL;DRs drop all jargon.
- **ADHD-friendly formatting.** Rainbow top separator, `====` between chunks, bold anchors, generous spacing.
