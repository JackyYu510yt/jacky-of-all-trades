# Uploader PC one-shot setup
# Turns a blank Windows box into the fleet's upload station: Syncthing with a
# SEND & RECEIVE "! Jacky Rush Rendered" folder fed by the render PCs
# (each render PC filters to its own videos via .stignore, so deleting an
# uploaded video here wipes the origin PC's copy - and only that copy),
# a SEND & RECEIVE "! Thumbnails" folder shared with the farmer,
# bulk storage junctioned onto the biggest data drive, autostart wired.
#
#   irm https://raw.githubusercontent.com/JackyYu510yt/jacky-of-all-trades/main/uploader-setup/setup.ps1 | iex
#
# Run from an ELEVATED PowerShell. After installing apps and logging into
# Tailscale it picks one of three modes on its own:
#
#   LIVE MIGRATION  The old uploader answers on Tailscale (it ran
#                   migrate-source.ps1 -InstallAgent once). Asks for the old
#                   box's Windows password, then does EVERYTHING: pulls the
#                   identity/config/tools, copies videos + Desktop while the
#                   old box keeps uploading, makes the old box stand down,
#                   copies the rest (browser profiles, AdsPower, WSL) and comes
#                   up as the SAME uploader - render PCs, vast rigs and the
#                   farmer reconnect with zero changes.
#   PAYLOAD         Old box gone: the payload password unlocks payload.enc
#                   (pack_uploader_payload.ps1) - same identity and setup,
#                   but videos that lived only on the old box are lost.
#   FRESH           Enter at the payload prompt: NEW identity (render PCs
#                   must then be re-pointed - instructions printed).
#
# No-prompt variant: set $env:UPLOADER_SOURCE_PW (and optionally
# $env:TS_AUTHKEY) before the irm line.
#
# Safe to re-run - finished steps are skipped.

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$FolderId    = 'jr-rendered'
$FolderLabel = '! Jacky Rush Rendered'
$SharedRoot  = Join-Path $env:USERPROFILE 'Desktop\Compiled Binaries\Shared Folder'
$FolderPath  = Join-Path $SharedRoot $FolderLabel
$ThumbFolderId    = 'xkrz4-rfveh'
$ThumbFolderLabel = '! Thumbnails'
$ThumbFolderPath  = Join-Path $SharedRoot $ThumbFolderLabel
$StHome      = "$env:LOCALAPPDATA\Syncthing"
$StDir       = "$env:LOCALAPPDATA\Programs\Syncthing"
$StExe       = "$StDir\syncthing.exe"
$PyExe       = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
$TsExe       = 'C:\Program Files\Tailscale\tailscale.exe'
$PAYLOAD_URL = 'https://github.com/JackyYu510yt/jacky-of-all-trades/releases/download/uploader-setup-v1/payload.enc'
$Work        = "$env:TEMP\uploader-setup"
# The current uploader (Tailscale IP + login). Override with $env:UPLOADER_SOURCE.
$DefaultSource = '100.125.166.12'
$SourceLogin   = 'WIN-L3OQCKM6FUM\Administrator'

# Render PCs that feed this uploader (must match render-setup/README.md mesh facts)
$RenderPCs = @(
    @{ Name = 'Render PC1'; Id = 'VYEHZ24-DHRHMQ7-U6R4O4E-FL7DANW-WZIGZKO-AXL2PKZ-O5F4MRU-DDB4VQU' },
    @{ Name = 'Render PC2'; Id = 'NSBTRAN-KTBVNJH-TXEQDYW-6KA3RYS-WWV34MU-XSMYIL5-WWU7RRH-OYBI2A4' },
    @{ Name = 'Render PC3'; Id = 'ZGSLY26-WJMJXAC-6EU2K7I-C6U7FYU-RDXI5SI-FPVC5GR-IKCIUTA-2U2H2A5' },
    @{ Name = 'Render PC4'; Id = 'XSXJ73D-M4ZEYXP-3TMZGIX-5AQTZBP-47ZN2S2-C6PXQF4-6TAB5MV-VDUSJQE' },
    @{ Name = 'Render PC5'; Id = 'OBY47V5-FXCSZCM-2WQT55V-IHMJXJF-QKGUFXG-J6RONWC-UFMJKL7-EPWRFAG' }
)

# Farmer (orchestrator) - feeds the thumbnails folder
$Farmer = @{ Name = 'Farmer PC1'; Id = 'XFLEVVM-KVCRGNJ-L2K6ARD-LZHPH45-GZZZC4B-AVPCU5E-H6QGOGS-OQMJMQ7' }

# Apps the uploader runs (same versions where the vendor allows pinning).
# AdsPower has no stable download URL - it is copied from the old box instead.
$Apps = @(
    @{ Name = 'Python 3.11.9'; Test = $PyExe; Url = 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe'; File = 'python.exe'
       Args = '/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_test=0' },
    @{ Name = 'Google Chrome'; Test = 'C:\Program Files\Google\Chrome\Application\chrome.exe'; Url = 'https://dl.google.com/chrome/install/googlechromestandaloneenterprise64.msi'; File = 'chrome.msi' },
    @{ Name = 'Firefox'; Test = 'C:\Program Files\Mozilla Firefox\firefox.exe'; Url = 'https://download.mozilla.org/?product=firefox-latest-ssl&os=win64&lang=en-US'; File = 'firefox.exe'; Args = '/S' },
    @{ Name = 'Tailscale'; Test = $TsExe; Url = 'https://pkgs.tailscale.com/stable/tailscale-setup-latest-amd64.msi'; File = 'tailscale.msi' },
    @{ Name = 'VS Code'; Test = "$env:LOCALAPPDATA\Programs\Microsoft VS Code\Code.exe"; Url = 'https://update.code.visualstudio.com/latest/win32-x64-user/stable'; File = 'vscode.exe'
       Args = '/VERYSILENT /NORESTART /MERGETASKS=!runcode,addtopath' },
    @{ Name = 'WinRAR 7.23'; Test = 'C:\Program Files\WinRAR\WinRAR.exe'; Url = 'https://www.rarlab.com/rar/winrar-x64-723.exe'; File = 'winrar.exe'; Args = '/S' },
    @{ Name = 'Process Hacker 2.39'; Test = 'C:\Program Files\Process Hacker 2\ProcessHacker.exe'; Url = 'https://github.com/processhacker/processhacker/releases/download/v2.39/processhacker-2.39-setup.exe'; File = 'processhacker.exe'
       Args = '/VERYSILENT /NORESTART' }
)

function Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "WARNING: $msg" -ForegroundColor Yellow; $script:Warnings += $msg }
$script:Warnings = @()

# Mirror one folder with robocopy; exit codes 0-7 are success.
function Copy-Tree([string]$From, [string]$To, [switch]$Mirror, [string[]]$ExcludeDirs) {
    if (-not (Test-Path -LiteralPath $From)) { Write-Host "  (not there, skipped) $From" -ForegroundColor DarkGray; return }
    New-Item -ItemType Directory -Force $To | Out-Null
    $a = @($From, $To, $(if ($Mirror) { '/MIR' } else { '/E' }), '/COPY:DAT', '/DCOPY:T', '/XJ', '/R:2', '/W:5', '/MT:16', '/NP', '/NFL', '/NDL', '/NJH')
    if ($ExcludeDirs) { $a += '/XD'; $a += $ExcludeDirs }
    Write-Host "  $From -> $To"
    & robocopy @a | Where-Object { $_ -match '(Dirs|Files|Bytes) :' } | ForEach-Object { Write-Host "    $($_.Trim())" -ForegroundColor DarkGray }
    if ($LASTEXITCODE -ge 8) { Warn "robocopy exit $LASTEXITCODE copying $From (some files failed - re-run setup to retry)" }
}

# --- 0. Elevation + mode -----------------------------------------------------
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) { throw 'Open PowerShell with "Run as administrator" and run this again.' }
New-Item -ItemType Directory -Force $Work | Out-Null

function Test-Port([string]$TargetHost, [int]$Port) {
    $c = New-Object Net.Sockets.TcpClient
    try { $ar = $c.BeginConnect($TargetHost, $Port, $null, $null); $ar.AsyncWaitHandle.WaitOne(4000) -and $c.Connected } catch { $false } finally { $c.Close() }
}
function Read-Secret([string]$Prompt) {
    $s = Read-Host $Prompt -AsSecureString
    [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
}
$Restore = $false; $Live = $false; $Copied = $false
$Done = Test-Path "$StHome\cert.pem"   # identity already here = re-run, just finish leftovers

# --- 1. Apps -----------------------------------------------------------------
Step 'Apps'
foreach ($app in $Apps) {
    if (Test-Path $app.Test) { Write-Host "already installed : $($app.Name)"; continue }
    Write-Host "installing        : $($app.Name)..."
    $f = Join-Path $Work $app.File
    Invoke-WebRequest $app.Url -OutFile $f -UseBasicParsing
    if ($f -like '*.msi') { $p = Start-Process msiexec.exe -ArgumentList "/i `"$f`" /qn /norestart" -Wait -PassThru }
    else { $p = Start-Process $f -ArgumentList $app.Args -Wait -PassThru }
    if (-not (Test-Path $app.Test)) { Warn "$($app.Name) did not install (exit $($p.ExitCode))" }
}

# --- 2. Tailscale ------------------------------------------------------------
Step 'Tailscale'
if (Test-Path $TsExe) {
    & $TsExe status *> $null
    if ($LASTEXITCODE -ne 0) {
        if ($env:TS_AUTHKEY) { & $TsExe up --unattended --auth-key=$env:TS_AUTHKEY }
        else {
            Write-Host 'Log in to Tailscale with the fleet account (open the link below)...' -ForegroundColor Yellow
            & $TsExe up --unattended
        }
    }
    Write-Host "Tailscale IP: $(& $TsExe ip -4 | Select-Object -First 1)"
}

# --- 3. Where the uploader comes from ----------------------------------------
# LIVE: the old uploader is reachable over Tailscale and has the migration
#       agent (migrate-source.ps1 -InstallAgent) - identity, config, tools and
#       all data come straight from it, and it cuts itself over on request.
# PAYLOAD: old box gone - identity/config/tools from payload.enc (password).
# FRESH: neither - brand-new identity.
if (-not $Done) {
    Step 'Find the old uploader'
    $Src = if ($env:UPLOADER_SOURCE) { $env:UPLOADER_SOURCE } else { $DefaultSource }
    $Mig = "\\$Src\C$\ProgramData\uploader-migration"
    if (Test-Port $Src 445) {
        Write-Host "Old uploader reachable at $Src."
        $pwPlain = if ($env:UPLOADER_SOURCE_PW) { $env:UPLOADER_SOURCE_PW } else { Read-Secret "Old uploader's Windows password ($SourceLogin)" }
        foreach ($share in 'C$', 'D$') {
            net use "\\$Src\$share" /delete /y 2>$null | Out-Null
            net use "\\$Src\$share" $pwPlain /user:$SourceLogin /persistent:no | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "Cannot open \\$Src\$share - wrong password for $SourceLogin?" }
        }
        if (Test-Path "$Mig\migrate-source.ps1") { $Live = $true }
        else { Warn "Old uploader has no migration agent (run migrate-source.ps1 -InstallAgent there) - falling back to the payload." }
    } else {
        Write-Host "Old uploader not reachable at $Src - using the payload."
    }

    if ($Live) {
        Step 'Get identity + config from the old uploader'
        Remove-Item "$Mig\READY.txt" -ErrorAction SilentlyContinue
        Set-Content "$Mig\PACK-REQUEST.txt" (Get-Date -Format s)
        Write-Host 'Asked it to pack (its agent checks every minute)...'
        $deadline = (Get-Date).AddMinutes(10)
        while (-not (Test-Path "$Mig\READY.txt")) {
            if ((Get-Date) -gt $deadline) { throw "Old uploader never answered - see $Mig\agent.log" }
            Start-Sleep 10
        }
        $P = Join-Path $Work 'payload'
        if (Test-Path $P) { Remove-Item $P -Recurse -Force }
        Copy-Tree "$Mig\pack" $P
        Remove-Item "$Mig\pack", "$Mig\READY.txt" -Recurse -Force -ErrorAction SilentlyContinue   # unencrypted keys - don't leave them there
        $Manifest = Get-Content (Join-Path $P 'manifest.json') -Raw | ConvertFrom-Json
        $Restore = $true
        Write-Host "Got uploader identity $($Manifest.device_id.Substring(0,7)) from $($Manifest.source_host)." -ForegroundColor Green
    } else {
        $Password = Read-Secret 'Uploader payload password (Enter = fresh install with a NEW identity)'
        $Restore = [bool]$Password
    }
} else {
    Write-Host "`nIdentity already on this box - finishing any remaining steps."
}

# --- 3b. Payload (old box gone) ----------------------------------------------
if ($Restore -and -not $Live) {
    Step 'Unlock payload'
    $enc = Join-Path $Work 'payload.enc'
    if (-not (Test-Path $enc)) { Invoke-WebRequest $PAYLOAD_URL -OutFile $enc -UseBasicParsing }
    # AES-256 decrypt (matches pack_uploader_payload.ps1): [16B salt][16B IV][ciphertext]
    $raw  = [IO.File]::ReadAllBytes($enc)
    $kdf  = New-Object Security.Cryptography.Rfc2898DeriveBytes(
                $Password, [byte[]]$raw[0..15], 600000, [Security.Cryptography.HashAlgorithmName]::SHA256)
    $aes  = [Security.Cryptography.Aes]::Create()
    $aes.Key = $kdf.GetBytes(32)
    $aes.IV  = [byte[]]$raw[16..31]
    try { $plain = $aes.CreateDecryptor().TransformFinalBlock($raw, 32, $raw.Length - 32) }
    catch { throw 'Wrong password.' }
    if ($plain[0] -ne 0x50 -or $plain[1] -ne 0x4B) { throw 'Wrong password (payload is not a valid archive).' }
    $zip = Join-Path $Work 'payload.zip'
    [IO.File]::WriteAllBytes($zip, $plain)
    $P = Join-Path $Work 'payload'
    if (Test-Path $P) { Remove-Item $P -Recurse -Force }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::ExtractToDirectory($zip, $P)
    Remove-Item $zip
    $Manifest = Get-Content (Join-Path $P 'manifest.json') -Raw | ConvertFrom-Json
    Write-Host "Unlocked. Uploader identity $($Manifest.device_id.Substring(0,7)), packed $($Manifest.packed_at) on $($Manifest.source_host)."
}

if ($Restore -and (Test-Path $PyExe)) {
    Step 'Python packages (same versions as the old uploader)'
    & $PyExe -m pip install --disable-pip-version-check -q -r (Join-Path $P 'pip-freeze.txt')
    if ($LASTEXITCODE -ne 0) { Warn 'some pip packages failed to install - see output above' }
}

# --- 4. Bulk storage: junction Shared Folder onto the biggest data drive -----
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

# --- 5. Copy from the old uploader (restore mode) ----------------------------
# Two passes. Pass 1 runs while the old box is still uploading (videos +
# Desktop, the bulk). Pass 2 runs after the old box is made inert, mirrors
# the videos exactly and takes what is locked while in use (browser profiles,
# AdsPower, ClipAngel, the WSL disk). Videos MUST come across this way: ones
# delivered by vast rigs that no longer exist live only on the old uploader.
if ($Restore -and -not $Done) {
    if ($Live) {
        $OldHome = "\\$Src\C$" + $Manifest.source_home.Substring(2)
        $OldData = "\\$Src\D$"
        $Marker  = "$Mig\INERT.txt"
        $Dl      = if ($data) { "$($data.DriveLetter):" } else { 'C:' }

        function Copy-Bulk([switch]$Final) {
            Copy-Tree "$OldData\Shared Folder\$FolderLabel"      $FolderPath      -Mirror:$Final
            Copy-Tree "$OldData\Shared Folder\$ThumbFolderLabel" $ThumbFolderPath -Mirror:$Final
            Copy-Tree "$OldHome\Desktop"   "$env:USERPROFILE\Desktop" -ExcludeDirs 'Shared Folder', 'uploader_checksum_guard'
            Copy-Tree "$OldHome\Downloads" "$env:USERPROFILE\Downloads"
            Copy-Tree "$OldHome\Documents" "$env:USERPROFILE\Documents"
            Copy-Tree "\\$Src\C$\ffmpeg"   'C:\ffmpeg'
            Copy-Tree "\\$Src\C$\jat"      'C:\jat'
            # Claude Code (binary in .local\bin, settings/memory in .claude) + VS Code extensions
            Copy-Tree "$OldHome\.local"    "$env:USERPROFILE\.local"
            Copy-Tree "$OldHome\.claude"   "$env:USERPROFILE\.claude"
            Copy-Item "$OldHome\.claude.json" "$env:USERPROFILE\" -ErrorAction SilentlyContinue
            Copy-Tree "$OldHome\.vscode"   "$env:USERPROFILE\.vscode"
        }

        if (-not (Test-Path $Marker)) {
            Step 'Pass 1 of 2 - bulk copy while the old uploader keeps working'
            Copy-Bulk
            Step 'Cutover - old uploader stops so this box can take its identity'
            Set-Content "$Mig\CUTOVER-REQUEST.txt" (Get-Date -Format s)
            Write-Host 'Asked the old uploader to stand down (its agent checks every minute)...'
            $deadline = (Get-Date).AddMinutes(10)
            while (-not (Test-Path $Marker)) {
                if ((Get-Date) -gt $deadline) { throw "Old uploader never reported INERT - see $Mig\agent.log. Nothing was taken over; re-run setup." }
                Start-Sleep 10
            }
        }
        Write-Host 'Old uploader is INERT.' -ForegroundColor Green

        Step 'Pass 2 of 2 - exact mirror + in-use data'
        Copy-Bulk -Final
        Copy-Tree "$OldHome\AppData\Local\Google\Chrome\User Data" "$env:LOCALAPPDATA\Google\Chrome\User Data" -Mirror
        Copy-Tree "$OldHome\AppData\Roaming\Mozilla" "$env:APPDATA\Mozilla" -Mirror
        Copy-Tree "$OldHome\AppData\Roaming\adspower_global" "$env:APPDATA\adspower_global" -Mirror
        Copy-Tree "\\$Src\C$\Program Files\AdsPower Global" 'C:\Program Files\AdsPower Global' -Mirror
        Copy-Tree "\\$Src\C$\.ADSPOWER_GLOBAL" 'C:\.ADSPOWER_GLOBAL' -Mirror
        if ($Dl -eq 'D:') { Copy-Tree "$OldData\.ADSPOWER_GLOBAL" 'D:\.ADSPOWER_GLOBAL' -Mirror }
        else { Warn "No D: drive here - AdsPower's D:\.ADSPOWER_GLOBAL cache was not copied (AdsPower re-downloads it)." }
        Copy-Tree "$OldHome\AppData\Local\ClipAngel" "$env:LOCALAPPDATA\ClipAngel"
        Copy-Item "\\$Src\C$\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp\AdsPower.lnk" `
                  'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp\' -ErrorAction SilentlyContinue
        $oldWsl = Get-ChildItem "$OldHome\AppData\Local\wsl" -Directory -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($oldWsl) { Copy-Tree $oldWsl.FullName "$env:LOCALAPPDATA\wsl\$($oldWsl.Name)"; $WslDisk = "$env:LOCALAPPDATA\wsl\$($oldWsl.Name)\ext4.vhdx" }

        $Copied = $true
    } else {
        $ok = Read-Host 'No copy. Is the OLD uploader permanently OFF (it must never run Syncthing again)? (y/N)'
        if ($ok -notmatch '^y') { throw 'Stopped before taking over the identity. Run migrate-source.ps1 -Cutover on the old box first.' }
    }
}

# --- 6. Syncthing binary -----------------------------------------------------
Step 'Syncthing binary'
if ($Restore -and -not (Test-Path $StExe)) {
    Copy-Tree (Join-Path $P 'syncthing-bin') $StDir
    Write-Host "Restored: $(& $StExe version)"
} elseif (Test-Path $StExe) {
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

# --- 7. Identity -------------------------------------------------------------
Step 'Syncthing identity'
if (Test-Path "$StHome\cert.pem") {
    Write-Host 'Identity already exists - keeping it (render PCs already trust it).'
    $script:NewIdentity = $false
} elseif ($Restore) {
    New-Item -ItemType Directory -Force $StHome | Out-Null
    Copy-Item (Join-Path $P 'syncthing-home\*') $StHome -Force
    # Folder paths in config.xml point into the old user profile - re-home them if it differs.
    if ($Manifest.source_home -ne $env:USERPROFILE) {
        $cx = "$StHome\config.xml"
        [IO.File]::WriteAllText($cx, ([IO.File]::ReadAllText($cx)).Replace($Manifest.source_home, $env:USERPROFILE))
    }
    Write-Host 'Restored the old uploader''s identity + full config (device roster, folders, GUI).' -ForegroundColor Green
    $script:NewIdentity = $false
} else {
    & $StExe generate
    Write-Host 'NEW identity generated - render PCs must be told about it (see final instructions).' -ForegroundColor Yellow
    $script:NewIdentity = $true
}
$MyId = (& $StExe device-id | Select-Object -Last 1).Trim()
Write-Host "Device ID: $MyId"
if ($Restore -and $MyId -ne $Manifest.device_id) { Warn "Device ID $MyId does not match the payload's $($Manifest.device_id)" }

# --- 8. Uploader tools + settings (restore mode) -----------------------------
if ($Restore) {
    Step 'Uploader tools + settings'
    Copy-Tree (Join-Path $P 'tools') 'C:\Tools'
    Copy-Tree (Join-Path $P 'checksum-guard') (Join-Path $env:USERPROFILE 'Desktop\Compiled Binaries\uploader_checksum_guard')
    $s = Join-Path $P 'settings'
    if (Test-Path "$s\ClipAngel") { Copy-Tree "$s\ClipAngel" "$env:LOCALAPPDATA\ClipAngel" }
    if (Test-Path "$s\Code-User") { Copy-Tree "$s\Code-User" "$env:APPDATA\Code\User" }
    if (Test-Path "$s\WinRAR")    { Copy-Tree "$s\WinRAR" "$env:APPDATA\WinRAR" }
    if (Test-Path "$s\WindowsTerminal") {
        $wt = Get-ChildItem "$env:LOCALAPPDATA\Packages" -Directory -Filter 'Microsoft.WindowsTerminal_*' -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($wt) { Copy-Tree "$s\WindowsTerminal" "$($wt.FullName)\LocalState" }
    }
    # User PATH: add any entry the old box had that this one lacks
    $cur = @([Environment]::GetEnvironmentVariable('Path', 'User') -split ';' | Where-Object { $_ })
    $old = @($Manifest.user_path.Replace($Manifest.source_home, $env:USERPROFILE) -split ';' | Where-Object { $_ })
    $merged = $cur + @($old | Where-Object { $cur -notcontains $_ })
    [Environment]::SetEnvironmentVariable('Path', ($merged -join ';'), 'User')
    Write-Host 'User PATH merged.'
}

# --- 9. Start Syncthing ------------------------------------------------------
Step 'Start Syncthing'
if (-not (Get-Process syncthing -ErrorAction SilentlyContinue)) {
    Start-Process $StExe -ArgumentList 'serve','--no-console','--no-browser' -WindowStyle Hidden
}
# Wait for the API to come up
$deadline = (Get-Date).AddSeconds(60)
while ((Get-Date) -lt $deadline) {
    try { & $StExe cli config devices list | Out-Null; break } catch { Start-Sleep 2 }
}

# --- 10. Configure sync folders + trusted render PCs (fresh mode) ------------
# Restore mode already has the exact config (every device incl. the vast pool).
if (-not $Restore -and -not $Done) {
    Step 'Configure sync'
    foreach ($pc in $RenderPCs) {
        try { & $StExe cli config devices add --device-id $pc.Id --name $pc.Name } catch { Write-Host "$($pc.Name) already present" }
    }
    try { & $StExe cli config devices add --device-id $Farmer.Id --name $Farmer.Name } catch { Write-Host "$($Farmer.Name) already present" }
    # Names: adds above no-op if the device already existed (e.g. added via a GUI
    # banner, which defaults to the Windows hostname) - force the friendly names,
    # and name this machine itself so other devices see 'Uploader PC' by default.
    foreach ($pc in $RenderPCs) { & $StExe cli config devices $pc.Id name set $pc.Name }
    & $StExe cli config devices $Farmer.Id name set $Farmer.Name
    & $StExe cli config devices $MyId name set 'Uploading PC1'
    # Rendered videos: send & receive. Each render PC's .stignore filters to its
    # own "* - PCx.mp4" videos, so a delete here wipes exactly the origin's copy
    # and render PCs never cross-copy each other's videos.
    try {
        & $StExe cli config folders add --id $FolderId --label $FolderLabel --path $FolderPath --type sendreceive
    } catch { Write-Host 'Folder already present' }
    & $StExe cli config folders $FolderId type set sendreceive
    foreach ($pc in $RenderPCs) {
        try { & $StExe cli config folders $FolderId devices add --device-id $pc.Id } catch { Write-Host "Folder already shared with $($pc.Name)" }
    }

    # Thumbnails: send & receive with the farmer, so each video's thumbnail sits
    # next to it at upload time. INTENTIONALLY two-way: deleting a thumbnail here
    # (post-upload cleanup) deletes it fleet-wide (versioning is off mesh-wide).
    New-Item -ItemType Directory -Force $ThumbFolderPath | Out-Null
    try {
        & $StExe cli config folders add --id $ThumbFolderId --label $ThumbFolderLabel --path $ThumbFolderPath --type sendreceive
    } catch { Write-Host 'Thumbnails folder already present' }
    & $StExe cli config folders $ThumbFolderId type set sendreceive
    try { & $StExe cli config folders $ThumbFolderId devices add --device-id $Farmer.Id } catch { Write-Host 'Thumbnails already shared with Farmer' }
}

# --- 11. Autostart + scheduled tasks -----------------------------------------
Step 'Autostart'
$RunKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
Set-ItemProperty -Path $RunKey -Name 'Syncthing' -Value "`"$StExe`" serve --no-console --no-browser"
Write-Host 'Syncthing registered in HKCU Run.'
if ($Restore) {
    if ($Manifest.run_keys.ClipAngel) {
        Set-ItemProperty -Path $RunKey -Name 'ClipAngel' -Value $Manifest.run_keys.ClipAngel.Replace($Manifest.source_home, $env:USERPROFILE)
        Write-Host 'ClipAngel registered in HKCU Run.'
    }
    # Same tasks as the old box (Syncthing at boot with nobody logged in, the
    # checksum guard every 5 min, the reaper daily + its delete-request poll
    # every minute, the RDP clipboard fix) - re-owned by this machine's user.
    $mySid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    foreach ($x in Get-ChildItem (Join-Path $P 'tasks') -Filter *.xml) {
        [xml]$t = Get-Content -LiteralPath $x.FullName -Raw
        $t.Task.Principals.Principal.UserId = $mySid
        foreach ($lt in @($t.Task.Triggers.LogonTrigger)) { if ($lt) { $lt.UserId = "$env:COMPUTERNAME\$env:USERNAME" } }
        $xmlText = $t.OuterXml.Replace($Manifest.source_home, $env:USERPROFILE)
        Register-ScheduledTask -TaskName $x.BaseName -Xml $xmlText -Force | Out-Null
        Write-Host "scheduled task    : $($x.BaseName)"
    }
}

# --- 12. WSL (restore mode) --------------------------------------------------
# On the re-run after the WSL-install reboot the copy step is skipped, so find the disk it left.
if (-not $WslDisk) { $WslDisk = Get-ChildItem "$env:LOCALAPPDATA\wsl\*\ext4.vhdx" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName }
if ($WslDisk -and (Test-Path $WslDisk)) {
    Step 'WSL'
    $env:WSL_UTF8 = '1'
    wsl --status *> $null
    if ($LASTEXITCODE -ne 0) {
        wsl --install --no-distribution
        Warn 'WSL was just installed - REBOOT, then re-run this setup to attach the Ubuntu disk (everything else is skipped).'
    } elseif (-not (@(wsl -l -q) -contains 'Ubuntu')) {
        wsl --import-in-place Ubuntu $WslDisk
        wsl --set-default Ubuntu
        Write-Host 'Ubuntu attached from the old uploader''s disk.'
    } else { Write-Host 'Ubuntu already registered.' }
}

# --- Done --------------------------------------------------------------------
Step 'DONE'
Write-Host "Uploader device ID: $MyId" -ForegroundColor Green
Write-Host "Renders will arrive in: $FolderPath" -ForegroundColor Green
Write-Host "Thumbnails will arrive in: $ThumbFolderPath" -ForegroundColor Green
if ($Restore) {
    Write-Host ''
    Write-Host 'Same identity as the old uploader: render PCs, vast rigs and the farmer reconnect on their own.' -ForegroundColor Green
    Write-Host 'Still by hand (logins cannot be copied between machines):' -ForegroundColor Yellow
    Write-Host '  - open AdsPower and log in - profiles + their cookies come back from AdsPower''s cloud' -ForegroundColor Yellow
    Write-Host '  - open Chrome: profiles/bookmarks/extensions are there, but sign in to Google + sites again' -ForegroundColor Yellow
    if (-not $Copied) { Write-Host '  - nothing was copied from the old box: videos only on it are NOT here' -ForegroundColor Yellow }
}
foreach ($w in $script:Warnings) { Write-Host "WARNING: $w" -ForegroundColor Yellow }
if ($script:NewIdentity) {
    Write-Host ''
    Write-Host 'NEW IDENTITY - each render PC must be pointed at it. On PC1/PC2/PC3 run:' -ForegroundColor Yellow
    Write-Host "  `$u = 'https://raw.githubusercontent.com/JackyYu510yt/jacky-of-all-trades/main/render-setup/share-rendered-to-uploader.ps1'" -ForegroundColor Yellow
    Write-Host "  & ([scriptblock]::Create((irm `$u))) -UploaderId '$MyId'" -ForegroundColor Yellow
    Write-Host 'Then remove the OLD uploader device in each render PC''s Syncthing GUI (or leave it; it''s harmless).' -ForegroundColor Yellow
    Write-Host ''
    Write-Host 'The FARMER must also be told (thumbnails). On the farmer run:' -ForegroundColor Yellow
    Write-Host "  `$exe = `"`$env:LOCALAPPDATA\Programs\Syncthing\syncthing.exe`"" -ForegroundColor Yellow
    Write-Host "  & `$exe cli config devices add --device-id '$MyId' --name 'Uploader'" -ForegroundColor Yellow
    Write-Host "  & `$exe cli config folders xkrz4-rfveh devices add --device-id '$MyId'" -ForegroundColor Yellow
}
