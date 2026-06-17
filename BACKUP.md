# Machine Config Backup

This repo is the single backup of the Claude Code setup on this PC. Clone it
to a fresh machine, run `restore.ps1`, and pick up where you left off.

## What's tracked here

```
<skill dirs>/   the skills (auto, spec, audit, ...)
memory/         persistent memory files + MEMORY.md index
hooks/          snapshot of ~/.claude/hooks/  (the live ones run from there)
config/         snapshot of ~/.claude/settings.json
restore.ps1     redeploys hooks/ + config/ onto a fresh PC
BACKUP.md       this file
```

`hooks/` and `config/` are **snapshots** — the files Claude Code actually runs
live one level up under `~/.claude/`. The auto-commit hook
(`hooks/repo-autocommit.ps1`) refreshes these snapshots into the repo on every
Stop, so they stay current without any manual step.

## What is NEVER in this backup (by design)

These stay on the local machine only — they are secrets or throwaway state:

- `~/.claude/.credentials.json`  — login token
- `~/.claude/history.jsonl`, `projects/`, `sessions/`  — conversation transcripts
- `cache/`, `image-cache/`, `paste-cache/`, `file-history/`, `telemetry/`  — junk/state

## Restore on a fresh PC

```powershell
git clone <this repo> $HOME\.claude\skills
powershell -ExecutionPolicy Bypass -File $HOME\.claude\skills\restore.ps1
# then restart Claude Code, and log in again (credentials are not backed up)
```

`restore.ps1` derives paths from its own location, so it works even if the new
PC has a different Windows username.

## Adding more to the backup later

Drop a new top-level folder here (mirroring `hooks/` / `config/`), then add a
copy line to the snapshot block in `hooks/repo-autocommit.ps1` and a restore
line to `restore.ps1`. That's the whole pattern.
