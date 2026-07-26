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

# Add uploader as a trusted device (ignore error if already added), then
# force the friendly name (the add no-ops if the device already existed)
try { & $exe cli config devices add --device-id $UploaderId --name 'Uploading PC1' } catch { Write-Host 'Uploader device already present' }
& $exe cli config devices $UploaderId name set 'Uploading PC1'

# Add the folder if missing - as SEND-ONLY first, so there is never a window
# where this PC is two-way without its ignore filter in place.
try { & $exe cli config folders add --id $FolderId --label '! Jacky Rush Rendered' --path $FolderPath --type sendonly } catch { Write-Host 'Folder already present' }
try { & $exe cli config folders $FolderId devices add --device-id $UploaderId } catch { Write-Host 'Folder already shared with uploader' }

# Set the ignore patterns through Syncthing's own local API so SYNCTHING
# writes the .stignore file itself (direct file writes can be blocked by
# folder permissions / Controlled Folder Access - Syncthing already has
# write rights in its own folder). First match wins: keep my own tagged
# videos anywhere in the tree, ignore everything else.
[xml]$stCfg = Get-Content "$env:LOCALAPPDATA\Syncthing\config.xml"
$apiKey = $stCfg.configuration.gui.apikey
$guiUrl = "http://$($stCfg.configuration.gui.address)"
$hdr = @{ 'X-API-Key' = $apiKey }
$old = Invoke-RestMethod -Uri "$guiUrl/rest/db/ignores?folder=$FolderId" -Headers $hdr
if ($old.ignore) {
    Write-Host 'Existing ignore patterns being replaced:'
    $old.ignore | ForEach-Object { Write-Host "  | $_" }
}
$body = @{ ignore = @(
    "// Only sync videos this PC rendered (watcher tags every final name with - $PcName)",
    "!(?i)**/* - $PcName.mp4",
    "*"
) } | ConvertTo-Json
Invoke-RestMethod -Uri "$guiUrl/rest/db/ignores?folder=$FolderId" -Method Post -Headers $hdr -Body $body -ContentType 'application/json' | Out-Null
$check = Invoke-RestMethod -Uri "$guiUrl/rest/db/ignores?folder=$FolderId" -Headers $hdr
if (-not ($check.ignore -contains "!(?i)**/* - $PcName.mp4")) { throw 'Ignore patterns did not stick - aborting before the two-way flip' }
Write-Host "Ignore patterns set: only '* - $PcName.mp4' syncs on this PC"

# Only NOW is it safe to go two-way
& $exe cli config folders $FolderId type set sendreceive

Write-Host ''
Write-Host "Done. '! Jacky Rush Rendered' now syncs two-way with the Uploader PC," -ForegroundColor Green
Write-Host "filtered to this PC's own videos (* - $PcName.mp4)." -ForegroundColor Green
Write-Host 'Uploader deletes of THIS PC''s videos now clean up here automatically.' -ForegroundColor Green
Write-Host "This PC's device ID (paste to the uploader so it can trust this PC):" -ForegroundColor Green
try { & $exe device-id } catch { & $exe --device-id }
