# Shares "! Jacky Rush Rendered" one-way (send-only) to the Uploader PC.
# Run on each render PC (PC1/PC2/PC3) with Syncthing already running:
#   irm https://raw.githubusercontent.com/JackyYu510yt/jacky-of-all-trades/main/render-setup/share-rendered-to-uploader.ps1 | iex
#
# If the uploader was rebuilt and has a NEW device ID, pass it explicitly:
#   & ([scriptblock]::Create((irm <same url>))) -UploaderId 'NEW-DEVICE-ID'
param([string]$UploaderId = 'MSZZ6T4-36EREEI-V4ZERUA-ULGZY7O-BLLRTCI-Z5376VE-XSS3445-2EKUVA5')

$ErrorActionPreference = 'Stop'

$FolderId   = 'jr-rendered'
$FolderPath = Join-Path $env:USERPROFILE 'Desktop\Compiled Binaries\Shared Folder\! Jacky Rush Rendered'

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

# Add uploader as a trusted device (ignore error if already added)
try { & $exe cli config devices add --device-id $UploaderId --name 'Uploader PC' } catch { Write-Host 'Uploader device already present' }

# Add the folder as SEND-ONLY (ignore error if already added), then share it with the uploader
try { & $exe cli config folders add --id $FolderId --label '! Jacky Rush Rendered' --path $FolderPath --type sendonly } catch { Write-Host 'Folder already present' }
try { & $exe cli config folders $FolderId devices add --device-id $UploaderId } catch { Write-Host 'Folder already shared with uploader' }

Write-Host ''
Write-Host 'Done. Folder "! Jacky Rush Rendered" is now shared send-only to the Uploader PC.' -ForegroundColor Green
Write-Host "This PC's device ID (paste to the uploader so it can trust this PC):" -ForegroundColor Green
try { & $exe device-id } catch { & $exe --device-id }
