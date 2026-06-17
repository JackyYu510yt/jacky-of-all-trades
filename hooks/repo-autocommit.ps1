# Auto-commit hook: stages and commits the config backup repo (skills, memory,
# hooks, settings) after each conversation, but does NOT push. Pushing is left
# manual — the user decides when changes are ready to share with the other PC.
# Auto-commit is the safety belt (work is captured locally, reversible via
# reset/amend/rebase before the next manual git push).
#
# Silent on success and on "nothing to commit". Failures are swallowed so
# they never block the Stop hook chain.

$ErrorActionPreference = "SilentlyContinue"
$src  = "C:\Users\Shadow\.claude"
$repo = "C:\Users\Shadow\.claude\skills"

# Bail if not a git repo (defensive — should always be one).
$null = git -C $repo rev-parse --is-inside-work-tree 2>$null
if ($LASTEXITCODE -ne 0) { exit 0 }

# Snapshot machine config into the repo so hooks + settings ride the same
# backup flow. The live files run from ~/.claude; these are tracked copies.
# (See BACKUP.md for the layout and restore.ps1 for redeploy.)
$hooksDst  = Join-Path $repo "hooks"
$configDst = Join-Path $repo "config"
New-Item -ItemType Directory -Force $hooksDst  | Out-Null
New-Item -ItemType Directory -Force $configDst | Out-Null
Copy-Item "$src\hooks\*.py"    $hooksDst -Force
Copy-Item "$src\hooks\*.ps1"   $hooksDst -Force
Copy-Item "$src\settings.json" (Join-Path $configDst "settings.json") -Force

# Stage everything.
git -C $repo add -A 2>$null | Out-Null

# Commit only if there's something staged.
$dirty = git -C $repo status --porcelain
if (-not [string]::IsNullOrWhiteSpace($dirty)) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    git -C $repo commit -m "auto-commit $ts" 2>$null | Out-Null
}

exit 0
