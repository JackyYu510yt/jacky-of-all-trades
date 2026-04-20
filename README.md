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

One command:

```bash
git clone https://github.com/JackyYu510yt/jacky-of-all-trades ~/.claude/skills
```

Done. Claude Code picks up all four skills on its next session.

## Update Later

```bash
cd ~/.claude/skills
git pull
```

---

## If `~/.claude/skills` Already Has Stuff

The clone above only works when the target is empty. If you already have skills there, use this instead:

```bash
# Clone the repo somewhere else
git clone https://github.com/JackyYu510yt/jacky-of-all-trades ~/jacky-of-all-trades

# Copy each skill folder into the right place
cp -r ~/jacky-of-all-trades/explain ~/.claude/skills/
cp -r ~/jacky-of-all-trades/optimize ~/.claude/skills/
cp -r ~/jacky-of-all-trades/prep ~/.claude/skills/
cp -r ~/jacky-of-all-trades/repair ~/.claude/skills/
```

To update later: `cd ~/jacky-of-all-trades && git pull`, then re-run the `cp` lines.

---

## Design Principles

- **KISS first.** Smallest change that moves the biggest dial.
- **Self-healing.** Every risky operation gets bounded retry, checkpointing, or atomic writes.
- **Evidence-based.** `repair` requires conclusive, replicable proof before any fix is applied.
- **Plain language + learning.** Technical terms appear with inline definitions; TL;DRs drop all jargon.
- **ADHD-friendly formatting.** Rainbow top separator, `====` between chunks, bold anchors, generous spacing.
