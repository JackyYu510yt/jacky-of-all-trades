# Uploader PC one-shot setup
# Turns a blank Windows box into the fleet's upload station: Syncthing with a
# RECEIVE-ONLY "! Jacky Rush Rendered" folder fed by all three render PCs,
# bulk storage junctioned onto the biggest data drive, autostart wired.
#
#   irm https://raw.githubusercontent.com/JackyYu510yt/jacky-of-all-trades/main/uploader-setup/setup.ps1 | iex
#
# Safe to re-run - finished steps are skipped. No admin needed except for
# initializing a brand-new (RAW) data disk.

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$FolderId    = 'jr-rendered'
$FolderLabel = '! Jacky Rush Rendered'
$SharedRoot  = Join-Path $env:USERPROFILE 'Desktop\Compiled Binaries\Shared Folder'
$FolderPath  = Join-Path $SharedRoot $FolderLabel
$StDir       = "$env:LOCALAPPDATA\Programs\Syncthing"
$StExe       = "$StDir\syncthing.exe"

# Render PCs that feed this uploader (must match render-setup/README.md mesh facts)
$RenderPCs = @(
    @{ Name = 'Render PC1'; Id = 'VYEHZ24-DHRHMQ7-U6R4O4E-FL7DANW-WZIGZKO-AXL2PKZ-O5F4MRU-DDB4VQU' },
    @{ Name = 'Render PC2'; Id = 'NSBTRAN-KTBVNJH-TXEQDYW-6KA3RYS-WWV34MU-XSMYIL5-WWU7RRH-OYBI2A4' },
    @{ Name = 'Render PC3'; Id = 'ZGSLY26-WJMJXAC-6EU2K7I-C6U7FYU-RDXI5SI-FPVC5GR-IKCIUTA-2U2H2A5' }
)

function Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }

# --- 1. Syncthing binary -----------------------------------------------------
Step 'Syncthing binary'
if (Test-Path $StExe) {
    Write-Host "Already installed: $(& $StExe version)"
} else {
    Write-Host 'Downloading latest Syncthing from GitHub...'
    $rel = Invoke-RestMethod 'https://api.github.com/repos/syncthing/syncthing/releases/latest'
    $asset = $rel.assets | Where-Object { $_.name -like 'syncthing-windows-amd64-*.zip' } | Select-Object -First 1
    $zip = "$env:TEMP\syncthing.zip"
    Invoke-WebRequest $asset.browser_download_url -OutFile $zip -UseBasicParsing
    Expand-Archive $zip -DestinationPath "$env:TEMP\syncthing-extract" -Force
    $inner = Get-ChildItem "$env:TEMP\syncthing-extract" -Directory | Select-Object -First 1
    New-Item -ItemType Directory -Force $StDir | Out-Null
    Copy-Item "$($inner.FullName)\*" $StDir -Recurse -Force
    Remove-Item $zip, "$env:TEMP\syncthing-extract" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Installed: $(& $StExe version)"
}

# --- 2. Identity -------------------------------------------------------------
Step 'Syncthing identity'
if (-not (Test-Path "$env:LOCALAPPDATA\Syncthing\cert.pem")) {
    & $StExe generate
    Write-Host 'NEW identity generated - render PCs must be told about it (see final instructions).' -ForegroundColor Yellow
    $script:NewIdentity = $true
} else {
    Write-Host 'Identity already exists - keeping it (render PCs already trust it).'
    $script:NewIdentity = $false
}
$MyId = (& $StExe device-id | Select-Object -Last 1).Trim()
Write-Host "Device ID: $MyId"

# --- 3. Bulk storage: junction Shared Folder onto the biggest data drive -----
Step 'Bulk storage'
# Initialize any RAW disk first (brand-new drive, nothing on it)
$raw = Get-Disk | Where-Object { $_.PartitionStyle -eq 'RAW' }
foreach ($d in $raw) {
    Write-Host "Found uninitialized $([math]::Round($d.Size/1GB)) GB disk (number $($d.Number)) - initializing as NTFS..."
    Initialize-Disk -Number $d.Number -PartitionStyle GPT
    $p = New-Partition -DiskNumber $d.Number -UseMaximumSize -AssignDriveLetter
    $p | Format-Volume -FileSystem NTFS -NewFileSystemLabel 'Storage' -Confirm:$false | Out-Null
    Write-Host "Formatted as $($p.DriveLetter):"
}
# Pick the biggest non-C fixed drive
$data = Get-Volume | Where-Object { $_.DriveLetter -and $_.DriveLetter -ne 'C' -and $_.DriveType -eq 'Fixed' } |
        Sort-Object Size -Descending | Select-Object -First 1
$existing = Get-Item $SharedRoot -ErrorAction SilentlyContinue
if ($existing -and $existing.LinkType -eq 'Junction') {
    Write-Host "Junction already in place: $SharedRoot -> $($existing.Target)"
} elseif ($data) {
    $hddRoot = "$($data.DriveLetter):\Shared Folder"
    Write-Host "Using $($data.DriveLetter): ($([math]::Round($data.Size/1GB)) GB) for bulk storage"
    if ($existing) {
        Write-Host "Moving existing $SharedRoot content to $hddRoot..."
        Get-Process syncthing -ErrorAction SilentlyContinue | Stop-Process -Force
        Start-Sleep 3
        robocopy $SharedRoot $hddRoot /E /MOVE /R:2 /W:2 /NFL /NDL /NP | Out-Null
        if (Test-Path $SharedRoot) { Remove-Item $SharedRoot -Recurse -Force }
    } else {
        New-Item -ItemType Directory -Force $hddRoot | Out-Null
        New-Item -ItemType Directory -Force (Split-Path $SharedRoot) | Out-Null
    }
    New-Item -ItemType Junction -Path $SharedRoot -Target $hddRoot | Out-Null
    Write-Host "Junction created: $SharedRoot -> $hddRoot"
} else {
    Write-Host 'WARNING: no data drive found - falling back to C: (watch free space!)' -ForegroundColor Yellow
}
New-Item -ItemType Directory -Force $FolderPath | Out-Null

# --- 4. Start Syncthing ------------------------------------------------------
Step 'Start Syncthing'
if (-not (Get-Process syncthing -ErrorAction SilentlyContinue)) {
    Start-Process $StExe -ArgumentList 'serve','--no-console','--no-browser' -WindowStyle Hidden
}
# Wait for the API to come up
$deadline = (Get-Date).AddSeconds(60)
while ((Get-Date) -lt $deadline) {
    try { & $StExe cli config devices list | Out-Null; break } catch { Start-Sleep 2 }
}

# --- 5. Configure receive-only folder + trusted render PCs -------------------
Step 'Configure sync (receive-only)'
foreach ($pc in $RenderPCs) {
    try { & $StExe cli config devices add --device-id $pc.Id --name $pc.Name } catch { Write-Host "$($pc.Name) already present" }
}
try {
    & $StExe cli config folders add --id $FolderId --label $FolderLabel --path $FolderPath --type receiveonly
} catch { Write-Host 'Folder already present' }
& $StExe cli config folders $FolderId type set receiveonly
foreach ($pc in $RenderPCs) {
    try { & $StExe cli config folders $FolderId devices add --device-id $pc.Id } catch { Write-Host "Folder already shared with $($pc.Name)" }
}

# --- 6. Autostart ------------------------------------------------------------
Step 'Autostart'
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'Syncthing' `
    -Value "`"$StExe`" serve --no-console --no-browser"
Write-Host 'Syncthing registered in HKCU Run.'

# --- Done --------------------------------------------------------------------
Step 'DONE'
Write-Host "Uploader device ID: $MyId" -ForegroundColor Green
Write-Host "Renders will arrive in: $FolderPath" -ForegroundColor Green
if ($script:NewIdentity) {
    Write-Host ''
    Write-Host 'NEW IDENTITY - each render PC must be pointed at it. On PC1/PC2/PC3 run:' -ForegroundColor Yellow
    Write-Host "  `$u = 'https://raw.githubusercontent.com/JackyYu510yt/jacky-of-all-trades/main/render-setup/share-rendered-to-uploader.ps1'" -ForegroundColor Yellow
    Write-Host "  & ([scriptblock]::Create((irm `$u))) -UploaderId '$MyId'" -ForegroundColor Yellow
    Write-Host 'Then remove the OLD uploader device in each render PC''s Syncthing GUI (or leave it; it''s harmless).' -ForegroundColor Yellow
}
