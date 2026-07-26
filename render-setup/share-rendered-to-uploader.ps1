# Shares "! Jacky Rush Rendered" two-way with the Uploader PC, filtered by
# origin: this PC only ever syncs videos whose filename carries its own tag
# ("... - PC1.mp4"), which the watcher already bakes into every final name.
# A .stignore file makes it blind to the other render PCs' videos, so nothing
# cross-copies - but a delete on the uploader DOES reach the PC that made the
# file (that's the point: post-upload cleanup wipes the origin's copy too).
#
# Run on each render PC (PC1/PC2/PC3) with Syncthing already running:
#   irm https://raw.githubusercontent.com/JackyYu510yt/jacky-of-all-trades/main/render-setup/share-rendered-to-uploader.ps1 | iex
#
# If the uploader was rebuilt and has a NEW device ID, pass it explicitly:
#   & ([scriptblock]::Create((irm <same url>))) -UploaderId 'NEW-DEVICE-ID'
# If PC-name auto-detection fails, pass it explicitly:
#   & ([scriptblock]::Create((irm <same url>))) -PcName 'PC2'
param(
    [string]$UploaderId = 'MSZZ6T4-36EREEI-V4ZERUA-ULGZY7O-BLLRTCI-Z5376VE-XSS3445-2EKUVA5',
    [string]$PcName = ''
)

$ErrorActionPreference = 'Stop'

$FolderId   = 'jr-rendered'
$FolderPath = Join-Path $env:USERPROFILE 'Desktop\Compiled Binaries\Shared Folder\! Jacky Rush Rendered'

# Which PC am I? The watcher config already knows (my_pc_name: "PC1"/"PC2"/"PC3").
if (-not $PcName) {
    $cfgPath = Join-Path $env:USERPROFILE 'Desktop\Compiled Binaries\Jacky Rush Render PC Template\render_watcher_config.json'
    if (Test-Path $cfgPath) {
        $PcName = (Get-Content $cfgPath -Raw | ConvertFrom-Json).my_pc_name
    }
}
if (-not $PcName) { throw "Could not auto-detect this PC's name - re-run with -PcName 'PC1' (or PC2/PC3)" }
Write-Host "This machine is: $PcName"

# Locate syncthing.exe
$exe = $null
$cmd = Get-Command syncthing -ErrorAction SilentlyContinue
if ($cmd) { $exe = $cmd.Source }
if (-not $exe) {
    $candidates = @(
        "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Syncthing.Syncthing*\syncthing.exe",
        "$env:ProgramFiles\Syncthing\syncthing.exe",
        "$env:LOCALAPPDATA\Programs\Syncthing\syncthing.exe"
    )
    foreach ($c in $candidates) {
        $hit = Get-Item $c -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($hit) { $exe = $hit.FullName; break }
    }
}
if (-not $exe) { throw 'syncthing.exe not found on this machine' }
Write-Host "Using $exe"

if (-not (Get-Process syncthing -ErrorAction SilentlyContinue)) {
    throw 'Syncthing is not running - start it first, then re-run this script'
}

if (-not (Test-Path $FolderPath)) { New-Item -ItemType Directory -Force $FolderPath | Out-Null }

# Write .stignore BEFORE the folder ever goes two-way, so this PC is already
# blind to the other PCs' videos when it starts accepting remote changes.
# First match wins: keep my own tagged videos (anywhere in the tree), ignore
# everything else. MUST be UTF-8 without BOM (WriteAllText default).
$stignore = @(
    "// Only sync videos this PC rendered (watcher tags every final name with - $PcName)",
    "!(?i)**/* - $PcName.mp4",
    "*"
) -join "`n"
$igPath = Join-Path $FolderPath '.stignore'
if (Test-Path $igPath) {
    # An existing .stignore may be hidden and/or read-only (Syncthing marks its
    # dotfiles hidden on Windows) - WriteAllText refuses to open it then.
    # Show what it held, normalize attributes, then overwrite.
    Write-Host 'Existing .stignore found, replacing. Old content was:'
    Get-Content $igPath -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "  | $_" }
    (Get-Item $igPath -Force).Attributes = 'Normal'
}
[IO.File]::WriteAllText($igPath, $stignore + "`n")
Write-Host ".stignore written: only '* - $PcName.mp4' syncs on this PC"

# Add uploader as a trusted device (ignore error if already added)
try { & $exe cli config devices add --device-id $UploaderId --name 'Uploader PC' } catch { Write-Host 'Uploader device already present' }

# Add the folder as SEND & RECEIVE (ignore error if already added), then share it with the uploader
try { & $exe cli config folders add --id $FolderId --label '! Jacky Rush Rendered' --path $FolderPath --type sendreceive } catch { Write-Host 'Folder already present' }
& $exe cli config folders $FolderId type set sendreceive
try { & $exe cli config folders $FolderId devices add --device-id $UploaderId } catch { Write-Host 'Folder already shared with uploader' }

Write-Host ''
Write-Host "Done. '! Jacky Rush Rendered' now syncs two-way with the Uploader PC," -ForegroundColor Green
Write-Host "filtered to this PC's own videos (* - $PcName.mp4)." -ForegroundColor Green
Write-Host 'Uploader deletes of THIS PC''s videos now clean up here automatically.' -ForegroundColor Green
Write-Host "This PC's device ID (paste to the uploader so it can trust this PC):" -ForegroundColor Green
try { & $exe device-id } catch { & $exe --device-id }
