# install.ps1 — Windows installer for jacky-of-all-trades skills
#
# Run from anywhere. It creates directory junctions from ~/.claude/skills/<name>
# to each skill folder in this repo, so edits / git pulls here propagate
# automatically to Claude Code.
#
# Usage (PowerShell):
#   cd <path-to-cloned-repo>
#   .\install.ps1
#
# Junctions (mklink /J) do NOT require admin or Developer Mode — unlike symlinks.

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$SkillsDir = Join-Path $env:USERPROFILE ".claude\skills"

if (-not (Test-Path $SkillsDir)) {
    New-Item -ItemType Directory -Path $SkillsDir -Force | Out-Null
    Write-Host "Created $SkillsDir"
}

$Skills = Get-ChildItem -Path $RepoRoot -Directory | Where-Object {
    Test-Path (Join-Path $_.FullName "SKILL.md")
}

if ($Skills.Count -eq 0) {
    Write-Error "No skill folders (containing SKILL.md) found in $RepoRoot"
    exit 1
}

Write-Host "Found $($Skills.Count) skill(s): $($Skills.Name -join ', ')"
Write-Host ""

foreach ($Skill in $Skills) {
    $Target = Join-Path $SkillsDir $Skill.Name

    if (Test-Path $Target) {
        $Item = Get-Item $Target -Force
        if ($Item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
            Remove-Item $Target -Force
            Write-Host "  [replaced] $($Skill.Name)"
        } else {
            Write-Warning "  [skipped]  $($Skill.Name) — real folder already exists at $Target. Delete or rename it manually, then rerun."
            continue
        }
    } else {
        Write-Host "  [added]    $($Skill.Name)"
    }

    cmd /c mklink /J "`"$Target`"" "`"$($Skill.FullName)`"" | Out-Null
}

Write-Host ""
Write-Host "Done. Claude Code will discover skills at $SkillsDir on next session."
Write-Host "To update later: cd $RepoRoot ; git pull   (no reinstall needed — junctions point at the repo)"
