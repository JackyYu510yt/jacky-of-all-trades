# setup.ps1 — one-command setup of this Claude Code config on a PC.
#
# Run this ONCE after cloning the repo to <home>\.claude\skills. It wires the
# hooks folder and the project's memory folder as live shortcuts (junctions)
# pointing INTO this repo, and copies settings.json into place. After this, a
# plain `git pull` keeps everything live — no other step needed.
#
# Idempotent: safe to re-run. If something is already linked correctly it is
# left alone; a real folder in the way is moved aside to *.local-backup first.

$ErrorActionPreference = "Stop"

$repo   = Split-Path -Parent $MyInvocation.MyCommand.Path   # ...\.claude\skills
$claude = Split-Path -Parent $repo                          # ...\.claude

function Ensure-Junction($link, $target) {
    if (Test-Path $link) {
        $item = Get-Item $link -Force
        if ($item.LinkType -eq 'Junction' -and ($item.Target -contains $target)) {
            Write-Host "  [ok]     $link  (already linked)"
            return
        }
        $backup = "$link.local-backup"
        if (Test-Path $backup) { $backup = "$backup-$(Get-Date -Format yyyyMMddHHmmss)" }
        Move-Item $link $backup
        Write-Host "  [moved]  $link  ->  $backup"
    }
    New-Item -ItemType Directory -Force (Split-Path -Parent $link) | Out-Null
    New-Item -ItemType Junction -Path $link -Target $target | Out-Null
    Write-Host "  [linked] $link  ->  $target"
}

Write-Host "Setting up Claude Code config under $claude ..."
Write-Host ""

# 1. Hooks: the live hooks folder becomes a shortcut into the repo.
Ensure-Junction "$claude\hooks" "$repo\hooks"

# 2. Memory: the Skills project's memory folder becomes a shortcut into the repo.
#    (Tied to the project at C:\Users\Shadow\Desktop\Compiled Binaries\Skills.
#     If you keep memory for other projects, link those the same way.)
Ensure-Junction "$claude\projects\C--Users-Shadow-Desktop-Compiled-Binaries-Skills\memory" "$repo\memory"

# 3. Settings: a single file, so it is copied (cannot be a folder shortcut).
Copy-Item "$repo\config\settings.json" "$claude\settings.json" -Force
Write-Host "  [copied] settings.json  ->  $claude\settings.json"

Write-Host ""
if ($env:USERNAME -ne "Shadow") {
    Write-Host "!! WARNING: your Windows username is '$($env:USERNAME)', not 'Shadow'."
    Write-Host "   Some paths are hardcoded as C:\Users\Shadow inside:"
    Write-Host "     - config\settings.json   (the hook command paths)"
    Write-Host "     - hooks\repo-autocommit.ps1"
    Write-Host "   Replace C:\Users\Shadow with C:\Users\$($env:USERNAME) in those,"
    Write-Host "   or the hooks will not fire. (An LLM can do this for you.)"
    Write-Host ""
}
Write-Host "Done. Restart Claude Code so it re-reads settings.json,"
Write-Host "then log in again (credentials are intentionally NOT backed up)."
