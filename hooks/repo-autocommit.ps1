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

# Snapshot settings.json into the repo so it rides the same backup flow.
# Hooks + memory are live junctions INTO the repo (see GUIDE.md), so editing
# them already edits the tracked copy — only settings.json needs copying,
# because a single file can't be a folder junction.
$configDst = Join-Path $repo "config"
New-Item -ItemType Directory -Force $configDst | Out-Null
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
