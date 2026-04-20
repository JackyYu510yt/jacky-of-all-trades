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

## Install on a New Machine

**Recommended (works in any scenario):**

```bash
# 1. Clone anywhere convenient (NOT inside ~/.claude/skills)
git clone https://github.com/JackyYu510yt/jacky-of-all-trades ~/jacky-of-all-trades

# 2. Run the installer — creates junctions/symlinks into ~/.claude/skills/
cd ~/jacky-of-all-trades

# Windows (PowerShell):
.\install.ps1

# Mac / Linux / Git Bash:
bash install.sh
```

The installer creates `~/.claude/skills/explain`, `/optimize`, `/prep`, `/repair` as **junctions (Windows) or symlinks (Unix)** pointing into the cloned repo. That means:

- Skills are discoverable by Claude Code immediately.
- Editing any `SKILL.md` in this repo updates what Claude sees — no re-install.
- `git pull` in this folder propagates updates to all skills instantly.
- Other skills in `~/.claude/skills/` (from other sources) are left alone.

**Already-cloned-to-wrong-place fix:** if you already did `git clone https://github.com/JackyYu510yt/jacky-of-all-trades ~/.claude/skills/jacky-of-all-trades` (creating an extra layer), just run the installer from inside that folder — it will set up the junctions correctly. Then you can optionally move the repo out of `~/.claude/skills/` to keep things clean.

---

## Updating

From any PC where you've cloned and installed:

```bash
cd ~/jacky-of-all-trades
git pull
```

Skills update instantly — no re-install needed (the junctions/symlinks point at the repo, so pulling new commits updates the live files).

---

## Design Principles

- **KISS first.** Smallest change that moves the biggest dial.
- **Self-healing.** Every risky operation gets bounded retry, checkpointing, or atomic writes.
- **Evidence-based.** `repair` requires conclusive, replicable proof before any fix is applied.
- **Plain language + learning.** Technical terms appear with inline definitions; TL;DRs drop all jargon.
- **ADHD-friendly formatting.** Rainbow top separator, `====` between chunks, bold anchors, generous spacing.
