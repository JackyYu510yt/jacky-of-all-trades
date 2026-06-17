# restore.ps1 — redeploy this backed-up machine config onto a fresh PC.
#
# After cloning this repo to <home>\.claude\skills, run this script to copy
# the tracked hooks + settings snapshot back into place under <home>\.claude
# (where Claude Code actually reads them from).
#
# Paths are derived from this script's own location, so it works regardless
# of your Windows username. Safe to re-run — it overwrites the live hooks and
# settings with the repo snapshot.

$ErrorActionPreference = "Stop"

$repo   = Split-Path -Parent $MyInvocation.MyCommand.Path   # ...\.claude\skills
$claude = Split-Path -Parent $repo                          # ...\.claude

Write-Host "Restoring machine config into $claude ..."

# hooks/ -> ~/.claude/hooks
$hooksDst = Join-Path $claude "hooks"
New-Item -ItemType Directory -Force $hooksDst | Out-Null
Copy-Item (Join-Path $repo "hooks\*") $hooksDst -Recurse -Force
Write-Host "  hooks\*              -> $hooksDst"

# config/settings.json -> ~/.claude/settings.json
$settingsSrc = Join-Path $repo "config\settings.json"
if (Test-Path $settingsSrc) {
    Copy-Item $settingsSrc (Join-Path $claude "settings.json") -Force
    Write-Host "  config\settings.json -> $claude\settings.json"
}

Write-Host ""
Write-Host "Done. Restart Claude Code so it re-reads settings.json."
Write-Host "NOTE: credentials are NOT in this backup by design — log in again on the new PC."
