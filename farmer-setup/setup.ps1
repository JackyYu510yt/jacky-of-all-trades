# ============================================================================
#  Jacky Rush FARMER (Orchestrator) - one-shot rebuild
#
#  Run on a freshly reinstalled Wholesale Internet box (PowerShell, any dir):
#     irm https://raw.githubusercontent.com/JackyYu510yt/jacky-of-all-trades/main/farmer-setup/setup.ps1 | iex
#  or locally:
#     .\setup.ps1
#
#  It asks ONE question - the payload password - then restores everything:
#  Syncthing with the farmer's permanent identity + the LIVE mesh config,
#  the orchestrator scripts, the master template, the pc1/pc2/pc3 identity
#  bundles, all scheduled tasks and autostart entries, and the desktop tools.
#
#  Safe to re-run: every step checks whether it's already done and skips.
#  This is Windows SERVER - there is no winget; everything direct-downloads.
# ============================================================================

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# ----------------------------------------------------------------------------
# Fixed facts about this machine (change here if they ever change)
# ----------------------------------------------------------------------------
$FARMER_ID  = 'XFLEVVM-KVCRGNJ-L2K6ARD-LZHPH45-GZZZC4B-AVPCU5E-H6QGOGS-OQMJMQ7'
$FARMER_IP  = '173.208.165.122'   # /29, gateway .121 - Wholesale Internet static
$FARMER_GW  = '173.208.165.121'
$FARMER_DNS = @('192.187.107.16', '69.30.209.16')

$PAYLOAD_URL = 'https://github.com/JackyYu510yt/jacky-of-all-trades/releases/download/farmer-setup-v1/payload.enc'

$Desk        = Join-Path $env:USERPROFILE 'Desktop'
$JackyDir    = Join-Path $Desk 'Testing\Jacky Rush'
$TemplateDir = Join-Path $Desk 'Testing\Jacky Rush Render PC Template'
$VercelDir   = Join-Path $Desk 'Testing\Vercel'
$KeysDir     = Join-Path $Desk 'render-pc-identities'
$JarvisDir   = Join-Path $Desk 'Compiled Binaries\Tinkering\jarvis'
$StaggerHlp  = Join-Path $Desk 'Compiled Binaries\Tinkering\stagger-dashboard\helper'
$StartupDir  = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
$StHome      = Join-Path $env:LOCALAPPDATA 'Syncthing'
$StDir       = Join-Path $env:LOCALAPPDATA 'Programs\Syncthing'
$StExe       = Join-Path $StDir 'syncthing.exe'
$PyExe       = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe'
$RunKey      = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'

# ----------------------------------------------------------------------------
# Helpers (same shapes as render-setup/setup.ps1)
# ----------------------------------------------------------------------------
function Log($msg)  { Write-Host "[setup] $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "[ OK  ] $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "[warn ] $msg" -ForegroundColor Yellow }
function Fail($msg) { Write-Host "[FAIL ] $msg" -ForegroundColor Red; throw $msg }

function Invoke-WithRetry([scriptblock]$Action, [string]$What, [int]$Tries = 3) {
    for ($i = 1; $i -le $Tries; $i++) {
        try { return & $Action }
        catch {
            if ($i -eq $Tries) { throw }
            $wait = 5 * $i
            Warn "$What failed (try $i/$Tries): $($_.Exception.Message) - retrying in ${wait}s"
            Start-Sleep -Seconds $wait
        }
    }
}

function Wait-Until([scriptblock]$Condition, [string]$What, [int]$TimeoutSec = 300, [int]$PollSec = 5) {
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try { if (& $Condition) { return } } catch { }
        Start-Sleep -Seconds $PollSec
    }
    Fail "Timed out after ${TimeoutSec}s waiting for: $What"
}

# AES-256 decrypt (matches pack_payload.ps1): [16B salt][16B IV][ciphertext]
function Unprotect-Payload([string]$InFile, [string]$OutFile, [string]$Password) {
    $raw  = [IO.File]::ReadAllBytes($InFile)
    $salt = $raw[0..15]; $iv = $raw[16..31]
    $kdf  = New-Object Security.Cryptography.Rfc2898DeriveBytes(
                $Password, [byte[]]$salt, 600000,
                [Security.Cryptography.HashAlgorithmName]::SHA256)
    $aes  = [Security.Cryptography.Aes]::Create()
    $aes.Key = $kdf.GetBytes(32); $aes.IV = [byte[]]$iv
    try {
        $plain = $aes.CreateDecryptor().TransformFinalBlock($raw, 32, $raw.Length - 32)
    } catch { Fail "Wrong password (decryption failed)." }
    if ($plain[0] -ne 0x50 -or $plain[1] -ne 0x4B) { Fail "Wrong password (payload is not a valid archive)." }
    [IO.File]::WriteAllBytes($OutFile, $plain)
}

function Get-StApi {
    $cfg = [xml](Get-Content (Join-Path $StHome 'config.xml'))
    @{ Base = "http://$($cfg.configuration.gui.address)/rest"
       Head = @{ 'X-API-Key' = $cfg.configuration.gui.apikey } }
}

# restore a payload folder to its home; an existing folder is left untouched
function Restore-Folder([string]$Src, [string]$Dst, [string]$What) {
    if (Test-Path $Dst) { Ok "$What already present - leaving it alone."; return }
    if (-not (Test-Path $Src)) { Fail "Payload is missing: $What" }
    New-Item -ItemType Directory -Force (Split-Path $Dst) | Out-Null
    Copy-Item $Src $Dst -Recurse
    Ok "$What restored."
}

# ----------------------------------------------------------------------------
# STEP 0 - elevation + the one question
# ----------------------------------------------------------------------------
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
           ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Log "Elevation needed (Windows Update disable + scheduled tasks). Relaunching as admin..."
    $self = $MyInvocation.MyCommand.Path
    if (-not $self) {
        # running via irm|iex - save ourselves to disk first, then elevate
        $self = Join-Path $env:TEMP 'farmer-setup.ps1'
        Invoke-WithRetry { Invoke-WebRequest 'https://raw.githubusercontent.com/JackyYu510yt/jacky-of-all-trades/main/farmer-setup/setup.ps1' -OutFile $self -UseBasicParsing } 'script self-download'
    }
    Start-Process powershell -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -NoExit -File `"$self`""
    return
}

$sec      = Read-Host 'Password to unlock the farmer payload' -AsSecureString
$Password = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
            [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
Log "Rebuilding this box as THE FARMER (identity $($FARMER_ID.Substring(0,7))...)"

# ----------------------------------------------------------------------------
# STEP 1 - get + unlock the payload
# ----------------------------------------------------------------------------
$work = Join-Path $env:TEMP 'farmer-setup-work'
New-Item -ItemType Directory -Force $work | Out-Null
# if anything fails from here on, never leave decrypted identity keys in TEMP
trap { Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue; break }

$payload = $null
if (-not [string]::IsNullOrEmpty($PSScriptRoot)) {
    $local = Join-Path $PSScriptRoot 'payload.enc'
    if (Test-Path $local) { $payload = $local }
}
if (-not $payload) {
    $payload = Join-Path $work 'payload.enc'
    if (-not (Test-Path $payload)) {
        Log "Downloading farmer payload..."
        Invoke-WithRetry { Invoke-WebRequest $PAYLOAD_URL -OutFile $payload -UseBasicParsing } 'payload download'
    }
}

Log "Unlocking payload..."
$zip = Join-Path $work 'payload.zip'
Unprotect-Payload $payload $zip $Password
Expand-Archive $zip -DestinationPath $work -Force
Remove-Item $zip
foreach ($need in 'syncthing-identity\cert.pem', 'syncthing-identity\key.pem',
                  'syncthing-identity\config.xml', 'render-pc-identities\pc1\key.pem',
                  'Jacky Rush\jacky_rush_farmer.py') {
    if (-not (Test-Path (Join-Path $work $need))) { Fail "Payload is missing: $need" }
}
Ok "Payload unlocked."

# ----------------------------------------------------------------------------
# STEP 2 - static IP sanity (verify only - never touch a working NIC remotely)
# ----------------------------------------------------------------------------
$haveIp = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
          Where-Object { $_.IPAddress -eq $FARMER_IP }
if ($haveIp) { Ok "Static IP $FARMER_IP already on the NIC." }
else {
    Warn "This box does NOT have the farmer's static IP ($FARMER_IP)."
    Warn "The render PCs dial tcp://${FARMER_IP}:22000 - without it they cannot find the farmer."
    Warn "If Wholesale Internet did not preconfigure it, set it by hand on the main NIC:"
    Warn "  New-NetIPAddress -InterfaceAlias '<NIC>' -IPAddress $FARMER_IP -PrefixLength 29 -DefaultGateway $FARMER_GW"
    Warn "  Set-DnsClientServerAddress -InterfaceAlias '<NIC>' -ServerAddresses $($FARMER_DNS -join ',')"
    Warn "Continuing - everything else still installs."
}

# ----------------------------------------------------------------------------
# STEP 3 - permanently disable Windows Update (same as render PCs)
# ----------------------------------------------------------------------------
Log "Disabling Windows Update..."
$au = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU'
New-Item -Path $au -Force | Out-Null
Set-ItemProperty $au -Name NoAutoUpdate -Value 1 -Type DWord
Set-ItemProperty $au -Name NoAutoRebootWithLoggedOnUsers -Value 1 -Type DWord
foreach ($svc in 'wuauserv', 'UsoSvc', 'WaaSMedicSvc') {
    try { Stop-Service $svc -Force -ErrorAction Stop } catch { }
    try { Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\$svc" -Name Start -Value 4 -ErrorAction Stop }
    catch { Warn "Could not disable service $svc - the policy keys above still block auto-updates." }
}
Ok "Windows Update disabled."

# ----------------------------------------------------------------------------
# STEP 4 - Python 3.11 (direct download - no winget on Server)
# ----------------------------------------------------------------------------
if (Test-Path $PyExe) { Ok "Python 3.11 already installed." }
else {
    Log "Installing Python 3.11..."
    $pyInst = Join-Path $work 'python-3.11.9-amd64.exe'
    Invoke-WithRetry { Invoke-WebRequest 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile $pyInst -UseBasicParsing } 'Python download'
    Start-Process $pyInst -ArgumentList '/quiet', 'InstallAllUsers=0', 'PrependPath=1', 'Include_launcher=1' -Wait
    if (-not (Test-Path $PyExe)) { Fail "Python installed but not found at $PyExe" }
    Ok "Python 3.11 installed."
}

# ----------------------------------------------------------------------------
# STEP 5 - restore all folders from the payload (existing ones left alone)
# ----------------------------------------------------------------------------
Restore-Folder (Join-Path $work 'Jacky Rush')                     $JackyDir    'Orchestrator folder (Jacky Rush)'
Restore-Folder (Join-Path $work 'Jacky Rush Render PC Template')  $TemplateDir 'Master render template'
Restore-Folder (Join-Path $work 'render-pc-identities')           $KeysDir     'Render PC identity bundles'
Restore-Folder (Join-Path $work 'jarvis')                         $JarvisDir   'jarvis overlay scripts'
# Vercel: restore the scanner files without clobbering a fuller existing dir
New-Item -ItemType Directory -Force $VercelDir | Out-Null
foreach ($f in Get-ChildItem (Join-Path $work 'Vercel') -File) {
    if (-not (Test-Path (Join-Path $VercelDir $f.Name))) { Copy-Item $f.FullName $VercelDir }
}
Ok "Snapshot scanner files in place."
# small autostart helpers
if (-not (Test-Path "$env:LOCALAPPDATA\bot_restart.ps1")) { Copy-Item (Join-Path $work 'misc\bot_restart.ps1') $env:LOCALAPPDATA }
New-Item -ItemType Directory -Force $StaggerHlp | Out-Null
if (-not (Test-Path "$StaggerHlp\supervisor.ps1")) { Copy-Item (Join-Path $work 'misc\supervisor.ps1') $StaggerHlp }
New-Item -ItemType Directory -Force 'C:\Tools\AutoHotkey' | Out-Null
if (-not (Test-Path 'C:\Tools\AutoHotkey\WinVDitto.exe')) { Copy-Item (Join-Path $work 'misc\WinVDitto.exe') 'C:\Tools\AutoHotkey' }
Restore-Folder (Join-Path $work 'misc\ClipAngel 2.22') (Join-Path $Desk 'ClipAngel 2.22') 'ClipAngel'
Ok "Helper files in place."

# ----------------------------------------------------------------------------
# STEP 6 - pip dependencies for the orchestrator
# ----------------------------------------------------------------------------
$req = Join-Path $JackyDir 'requirements.txt'
if (Test-Path $req) {
    Log "Installing Python packages..."
    Invoke-WithRetry { & $PyExe -m pip install -r $req --no-warn-script-location; if ($LASTEXITCODE -ne 0) { throw "pip exited $LASTEXITCODE" } } 'pip install' 2
    Ok "Python packages installed."
} else { Warn "No requirements.txt in Jacky Rush - install pip packages by hand when a script complains." }

# ----------------------------------------------------------------------------
# STEP 7 - Syncthing: binary, then identity FIRST, then start
# ----------------------------------------------------------------------------
if (Test-Path $StExe) { Ok "Syncthing already installed." }
else {
    Log "Downloading latest Syncthing from GitHub..."
    Invoke-WithRetry {
        $rel = Invoke-RestMethod 'https://api.github.com/repos/syncthing/syncthing/releases/latest'
        $asset = $rel.assets | Where-Object { $_.name -like 'syncthing-windows-amd64-*.zip' } | Select-Object -First 1
        $stZip = Join-Path $work 'syncthing.zip'
        Invoke-WebRequest $asset.browser_download_url -OutFile $stZip -UseBasicParsing
        Expand-Archive $stZip -DestinationPath (Join-Path $work 'syncthing-extract') -Force
    } 'Syncthing download'
    $inner = Get-ChildItem (Join-Path $work 'syncthing-extract') -Directory | Select-Object -First 1
    New-Item -ItemType Directory -Force $StDir | Out-Null
    Copy-Item "$($inner.FullName)\*" $StDir -Recurse -Force
    Ok "Syncthing installed: $StExe"
}

# identity + LIVE config BEFORE Syncthing ever starts. Only cert/key/config.xml
# are restored - NEVER an index/database. A fresh index can only pull; an old
# index next to empty folders broadcasts deletions (versioning is off
# mesh-wide - deletions are permanent).
Get-Process syncthing -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $StHome | Out-Null
if (-not (Test-Path (Join-Path $StHome 'cert.pem'))) {
    Log "Planting the farmer's permanent identity + mesh config..."
    Copy-Item (Join-Path $work 'syncthing-identity\cert.pem')   $StHome
    Copy-Item (Join-Path $work 'syncthing-identity\key.pem')    $StHome
    Copy-Item (Join-Path $work 'syncthing-identity\config.xml') $StHome
}
$actualId = (& $StExe device-id --home=$StHome | Select-Object -Last 1).Trim()
if ($actualId -ne $FARMER_ID) { Fail "IDENTITY MISMATCH - this box computed $actualId but the farmer must be $FARMER_ID. Stopping before anything connects." }
Ok "Identity verified: this machine IS the farmer ($($actualId.Substring(0,7))...)."

# the restored config.xml references folder paths - create each one plus its
# .stfolder marker so Syncthing accepts them instead of erroring on first start
$cfgXml = [xml](Get-Content (Join-Path $StHome 'config.xml'))
foreach ($f in $cfgXml.configuration.folder) {
    $p = $f.path
    if ($p.StartsWith('~')) { $p = $env:USERPROFILE + $p.Substring(1) }
    New-Item -ItemType Directory -Force $p | Out-Null
    New-Item -ItemType Directory -Force (Join-Path $p '.stfolder') | Out-Null
}
Ok "Sync folder paths + markers ready ($(@($cfgXml.configuration.folder).Count) folders)."

# the live farmer autostarts via the official installer's "Start Syncthing at
# logon (...)" task - if that exists (re-run on the live box), don't add a
# second autostart path; a fresh rebuild gets a Run key (uploader-setup style)
$stTask = Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object { $_.TaskName -like 'Start Syncthing at logon*' }
if (-not $stTask) { Set-ItemProperty $RunKey -Name 'Syncthing' -Value "`"$StExe`" serve --no-console --no-browser" }
if (-not (Get-Process syncthing -ErrorAction SilentlyContinue)) {
    Start-Process $StExe -ArgumentList 'serve', '--no-console', '--no-browser' -WindowStyle Hidden
}
Wait-Until { $api = Get-StApi; (Invoke-RestMethod "$($api.Base)/system/status" -Headers $api.Head).myID -eq $FARMER_ID } 'Syncthing API up' 120
Ok "Syncthing running with the live mesh config + autostarts at login."

# ----------------------------------------------------------------------------
# STEP 8 - scheduled tasks (recreated exactly as audited on the real farmer)
# ----------------------------------------------------------------------------
$pyw = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\pythonw.exe'
$noLimit = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) `
           -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
           -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Log "Registering scheduled tasks..."
Register-ScheduledTask -TaskName 'CMDUnhideDaemon' -Force `
    -Action (New-ScheduledTaskAction -Execute $pyw -Argument "`"$JackyDir\cmd_unhide_daemon.py`"") `
    -Trigger (New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME) `
    -Settings $noLimit | Out-Null

$scanSettings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) `
                -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
                -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName 'RenderSnapshotScanner' -Force `
    -Action (New-ScheduledTaskAction -Execute "$VercelDir\start_render_scanner.bat" -WorkingDirectory $VercelDir) `
    -Trigger (New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME) `
    -Settings $scanSettings | Out-Null

# these two exist but are DISABLED on the real farmer - recreate them the same
Register-ScheduledTask -TaskName 'Nightly Bot Restart' -Force `
    -Action (New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$env:LOCALAPPDATA\bot_restart.ps1`"") `
    -Trigger (New-ScheduledTaskTrigger -Daily -At 4:00AM) `
    -Settings (New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 10)) `
    -RunLevel Highest | Out-Null
Disable-ScheduledTask -TaskName 'Nightly Bot Restart' | Out-Null

$stagTrig = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddHours(18) `
            -RepetitionInterval (New-TimeSpan -Minutes 10) -RepetitionDuration (New-TimeSpan -Days 3650)
Register-ScheduledTask -TaskName 'StaggerHelperSupervisor' -Force `
    -Action (New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$StaggerHlp\supervisor.ps1`"") `
    -Trigger $stagTrig `
    -Settings (New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 72)) | Out-Null
Disable-ScheduledTask -TaskName 'StaggerHelperSupervisor' | Out-Null
Ok "Tasks: CMDUnhideDaemon + RenderSnapshotScanner (on), Nightly Bot Restart + StaggerHelperSupervisor (recreated disabled)."

if (-not (Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'render_snapshot_scanner' })) {
    Start-ScheduledTask -TaskName 'RenderSnapshotScanner'
    Ok "Snapshot scanner started."
} else { Ok "Snapshot scanner already running." }

# ----------------------------------------------------------------------------
# STEP 9 - Startup folder: the transcript service trio
# ----------------------------------------------------------------------------
foreach ($f in 'Copy Title Transcript Downloader V5.vbs', 'transcript_api.py', 'proxies.txt') {
    if (-not (Test-Path (Join-Path $StartupDir $f))) { Copy-Item (Join-Path $work "misc\startup\$f") $StartupDir }
}
Ok "Transcript service in the Startup folder (starts at next logon, port 8080)."

# ----------------------------------------------------------------------------
# STEP 10 - desktop tools: what's scriptable installs itself, the rest is README
# ----------------------------------------------------------------------------
Set-ItemProperty $RunKey -Name 'WinVDitto' -Value 'C:\Tools\AutoHotkey\WinVDitto.exe'
Set-ItemProperty $RunKey -Name 'ClipAngel' -Value "`"$Desk\ClipAngel 2.22\ClipAngel.exe`" /m"
Ok "WinVDitto + ClipAngel autostart wired."

function Install-Tool([string]$Name, [string]$TestPath, [scriptblock]$GetUrl, [string[]]$InstallArgs) {
    if (Test-Path $TestPath) { Ok "$Name already installed."; return }
    Log "Installing $Name..."
    try {
        $url = & $GetUrl
        $inst = Join-Path $work ([IO.Path]::GetFileName(($url -split '\?')[0]))
        Invoke-WithRetry { Invoke-WebRequest $url -OutFile $inst -UseBasicParsing } "$Name download" 2
        if ($inst -like '*.msi') { Start-Process msiexec -ArgumentList (@('/i', "`"$inst`"") + $InstallArgs) -Wait }
        else { Start-Process $inst -ArgumentList $InstallArgs -Wait }
        Ok "$Name installed."
    } catch { Warn "$Name install failed - install it by hand later; setup continues." }
}

Install-Tool 'Chrome' "$env:ProgramFiles\Google\Chrome\Application\chrome.exe" `
    { 'https://dl.google.com/chrome/install/googlechromestandaloneenterprise64.msi' } @('/qn')
Install-Tool 'Git' "$env:ProgramFiles\Git\cmd\git.exe" `
    { $r = Invoke-RestMethod 'https://api.github.com/repos/git-for-windows/git/releases/latest'
      ($r.assets | Where-Object { $_.name -like 'Git-*-64-bit.exe' } | Select-Object -First 1).browser_download_url } `
    @('/VERYSILENT', '/NORESTART')
Install-Tool 'GitHub CLI' "$env:ProgramFiles\GitHub CLI\gh.exe" `
    { $r = Invoke-RestMethod 'https://api.github.com/repos/cli/cli/releases/latest'
      ($r.assets | Where-Object { $_.name -like '*_windows_amd64.msi' } | Select-Object -First 1).browser_download_url } `
    @('/qn')
Install-Tool 'Ditto' "$env:ProgramFiles\Ditto\Ditto.exe" `
    { $r = Invoke-RestMethod 'https://api.github.com/repos/sabrogden/Ditto/releases/latest'
      ($r.assets | Where-Object { $_.name -like '*64bit*.exe' -and $_.name -notlike '*portable*' } | Select-Object -First 1).browser_download_url } `
    @('/VERYSILENT', '/NORESTART', '/S')   # covers Inno AND NSIS; the wrong one is ignored
if (Test-Path "$env:ProgramFiles\Ditto\Ditto.exe") { Set-ItemProperty $RunKey -Name 'Ditto' -Value "$env:ProgramFiles\Ditto\Ditto.exe" }
Install-Tool 'ShareX' "$env:ProgramFiles\ShareX\ShareX.exe" `
    { $r = Invoke-RestMethod 'https://api.github.com/repos/ShareX/ShareX/releases/latest'
      ($r.assets | Where-Object { $_.name -like '*-setup.exe' } | Select-Object -First 1).browser_download_url } `
    @('/VERYSILENT', '/NORESTART')
if ((Test-Path "$env:ProgramFiles\ShareX\ShareX.exe") -and -not (Test-Path "$StartupDir\ShareX.lnk")) {
    $ws = New-Object -ComObject WScript.Shell
    $lnk = $ws.CreateShortcut("$StartupDir\ShareX.lnk")
    $lnk.TargetPath = "$env:ProgramFiles\ShareX\ShareX.exe"; $lnk.Arguments = '-silent'; $lnk.Save()
    Ok "ShareX autostart shortcut restored."
}

# ----------------------------------------------------------------------------
# STEP 11 - Claude Code + dsp + skills repo (same as render PCs)
# ----------------------------------------------------------------------------
$claudeBin = Join-Path $env:USERPROFILE '.local\bin'
New-Item -ItemType Directory -Force $claudeBin | Out-Null
if (Get-Command claude -ErrorAction SilentlyContinue) { Ok "Claude Code already installed." }
else {
    Log "Installing Claude Code..."
    try { Invoke-WithRetry { irm https://claude.ai/install.ps1 | iex } 'Claude Code install' 2; Ok "Claude Code installed." }
    catch { Warn "Claude Code install failed - run  irm https://claude.ai/install.ps1 | iex  by hand later." }
}
$up = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($up -notlike "*$claudeBin*") { [Environment]::SetEnvironmentVariable('Path', "$up;$claudeBin", 'User') }
$env:Path += ";$claudeBin"
Set-Content -Path (Join-Path $claudeBin 'dsp.cmd') -Value "@echo off`r`nclaude --dangerously-skip-permissions %*"
Ok "dsp command ready."

$skills = Join-Path $env:USERPROFILE '.claude\skills'
$env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User') + ";$claudeBin"
if (-not (Test-Path (Join-Path $skills '.git'))) {
    Log "Cloning skills repo..."
    & cmd /c "git clone https://github.com/JackyYu510yt/jacky-of-all-trades `"$skills`" 2>nul"
    if ($LASTEXITCODE -ne 0) { Warn "git clone reported errors (known: one repo filename is illegal on Windows) - continuing with what checked out." }
} else { Ok "Skills repo already present." }
if (Test-Path (Join-Path $skills 'setup.ps1')) {
    Log "Wiring Claude config (hooks + memory + settings)..."
    try { & powershell -ExecutionPolicy Bypass -File (Join-Path $skills 'setup.ps1') | Out-Null; Ok "Claude config wired." }
    catch { Warn "Skills setup.ps1 failed - run it by hand later." }
} else { Warn "Skills repo setup.ps1 not found - wire Claude config by hand later." }

# ----------------------------------------------------------------------------
# STEP 12 - Chrome Remote Desktop: the way back into this box
# ----------------------------------------------------------------------------
$crdExe = "${env:ProgramFiles(x86)}\Google\Chrome Remote Desktop\CurrentVersion\remoting_start_host.exe"
if (-not (Test-Path $crdExe)) {
    Log "Installing Chrome Remote Desktop host..."
    $msi = Join-Path $work 'crdhost.msi'
    try {
        Invoke-WithRetry { Invoke-WebRequest 'https://dl.google.com/edgedl/chrome-remote-desktop/chromeremotedesktophost.msi' -OutFile $msi -UseBasicParsing } 'CRD download'
        Start-Process msiexec -ArgumentList '/i', "`"$msi`"", '/qn' -Wait
    } catch { Warn "CRD host install failed - install by hand later; setup continues." }
}
if (Test-Path $crdExe) {
    Ok "Chrome Remote Desktop host installed."
    Write-Host ''
    Write-Host '  LINK THIS PC TO YOUR GOOGLE ACCOUNT (one paste):' -ForegroundColor Yellow
    Write-Host '  1. On ANY device where you are logged into Google, open:'
    Write-Host '       https://remotedesktop.google.com/headless'
    Write-Host '  2. Click Begin -> Next -> Authorize, then COPY the command shown under "Windows".'
    Write-Host '  3. Paste it below. (Press Enter alone to SKIP - you can link later.)'
    $pasted = Read-Host '  paste here'
    if ($pasted -match '--code="?([^"\s]+)"?') {
        $pin = Read-Host 'Choose the Chrome Remote Desktop PIN (6+ digits)'
        Log "Registering with Google as Farmer..."
        $eapBak = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
        $out = $pin, $pin | & $crdExe --code="$($Matches[1])" --redirect-url="https://remotedesktop.google.com/_/oauthredirect" --name="Farmer" 2>&1
        $ErrorActionPreference = $eapBak
        if ($LASTEXITCODE -eq 0) { Ok "Chrome Remote Desktop linked - this PC is 'Farmer' in your device list." }
        else { Warn "CRD registration failed: $($out | Out-String)" }
    } elseif ($pasted.Trim()) { Warn 'Could not find --code=... in that paste - CRD link skipped.' }
    else { Warn 'CRD linking skipped by choice.' }
}

# ----------------------------------------------------------------------------
# cleanup + summary
# ----------------------------------------------------------------------------
Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
Write-Host ""
Write-Host "=====================================================" -ForegroundColor Green
Write-Host " THE FARMER IS REBUILT" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green
Write-Host " identity   : $FARMER_ID"
Write-Host " sync       : live mesh config restored (all folders + devices)"
Write-Host " tasks      : scanner + unhide daemon on; bot-restart + stagger off"
Write-Host " orchestr.  : Jacky Rush scripts + template + pc identities restored"
Write-Host ""
Write-Host " Remaining BY HAND (never bundled):" -ForegroundColor Yellow
Write-Host "  - gh auth login          (GitHub token lives in the keyring)"
Write-Host "  - claude login"
Write-Host "  - AdsPower + Proxifier   (install + log in)"
Write-Host "  - browser profiles       (Chrome/chrome-for-testing worker logins are gone -"
Write-Host "                            re-log-in the gemini/aistudio/flow accounts)"
Write-Host "  - stagger-dashboard      (restore the project, then re-enable its task if wanted)"
Write-Host "  - start the farmer       ('launch jacky_rush_farmer.bat' - it is manual on purpose)"
Write-Host " Reboot once to prove autostart if you want the full test."
