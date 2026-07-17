# ============================================================================
#  Jacky Rush Render PC - one-shot setup
#
#  Run on a BLANK Shadow PC (PowerShell, any directory):
#     irm https://raw.githubusercontent.com/JackyYu510yt/jacky-of-all-trades/main/render-setup/setup.ps1 | iex
#  or locally:
#     .\setup.ps1
#
#  It asks two questions - "Which PC number?" and "Password?" - then does
#  EVERYTHING: programs, dependencies, identity, sync, autostart, watcher.
#
#  Safe to re-run: every step checks whether it's already done and skips.
# ============================================================================

$ErrorActionPreference = 'Stop'

# ----------------------------------------------------------------------------
# Fixed facts about the farm (change here if the mesh ever changes)
# ----------------------------------------------------------------------------
$FARMER_ID   = 'XFLEVVM-KVCRGNJ-L2K6ARD-LZHPH45-GZZZC4B-AVPCU5E-H6QGOGS-OQMJMQ7'
$FARMER_ADDR = 'tcp://173.208.165.122:22000'
$PC2_ID      = 'NSBTRAN-KTBVNJH-TXEQDYW-6KA3RYS-WWV34MU-XSMYIL5-WWU7RRH-OYBI2A4'

$EXPECTED_DEVICE_ID = @{
    1 = 'VYEHZ24-DHRHMQ7-U6R4O4E-FL7DANW-WZIGZKO-AXL2PKZ-O5F4MRU-DDB4VQU'
    2 = 'NSBTRAN-KTBVNJH-TXEQDYW-6KA3RYS-WWV34MU-XSMYIL5-WWU7RRH-OYBI2A4'
    3 = 'ZGSLY26-WJMJXAC-6EU2K7I-C6U7FYU-RDXI5SI-FPVC5GR-IKCIUTA-2U2H2A5'
}

$FOLDER_OUTPUT     = 'sjetj-h9jpa'   # ! Jacky Rush Output   (the work)
$FOLDER_THUMBS     = 'xkrz4-rfveh'   # ! Thumbnails
$PAYLOAD_URL       = 'https://github.com/JackyYu510yt/jacky-of-all-trades/releases/download/render-setup-v1/payload.enc'

$SharedRoot  = Join-Path $env:USERPROFILE 'Desktop\Compiled Binaries\Shared Folder'
$TemplateDir = Join-Path $env:USERPROFILE 'Desktop\Compiled Binaries\Jacky Rush Render PC Template'
$OutputDir   = Join-Path $SharedRoot '! Jacky Rush Output'
$ThumbsDir   = Join-Path $SharedRoot '! Thumbnails'
$RenderedDir = Join-Path $SharedRoot '! Jacky Rush Rendered'
$StHome      = Join-Path $env:LOCALAPPDATA 'Syncthing'
$PyExe       = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe'

# ----------------------------------------------------------------------------
# Helpers
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
    # a correct password always yields a zip, which starts with 'PK'
    if ($plain[0] -ne 0x50 -or $plain[1] -ne 0x4B) { Fail "Wrong password (payload is not a valid archive)." }
    [IO.File]::WriteAllBytes($OutFile, $plain)
}

function Find-Syncthing {
    $c = Get-Command syncthing -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    $link = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links\syncthing.exe'
    if (Test-Path $link) { return $link }
    $pkg = Get-ChildItem (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages') -Recurse -Filter syncthing.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($pkg) { return $pkg.FullName }
    $legacy = Join-Path $env:LOCALAPPDATA 'Programs\Syncthing\syncthing.exe'
    if (Test-Path $legacy) { return $legacy }
    return $null
}

function Get-StApi {
    $cfg = [xml](Get-Content (Join-Path $StHome 'config.xml'))
    @{ Base = "http://$($cfg.configuration.gui.address)/rest"
       Head = @{ 'X-API-Key' = $cfg.configuration.gui.apikey } }
}

# ----------------------------------------------------------------------------
# STEP 0 - elevation + the two questions
# ----------------------------------------------------------------------------
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
           ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Log "Elevation needed (Windows Update disable + VC++ runtime). Relaunching as admin..."
    $self = $MyInvocation.MyCommand.Path
    if (-not $self) {
        # running via irm|iex - save ourselves to disk first, then elevate
        $self = Join-Path $env:TEMP 'render-setup.ps1'
        Invoke-WithRetry { Invoke-WebRequest 'https://raw.githubusercontent.com/JackyYu510yt/jacky-of-all-trades/main/render-setup/setup.ps1' -OutFile $self -UseBasicParsing } 'script self-download'
    }
    Start-Process powershell -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -NoExit -File `"$self`""
    return
}

$PcNumber = 0
while ($PcNumber -notin 1, 2, 3) {
    $in = Read-Host 'Which PC number is this? (1 / 2 / 3)'
    if ($in -match '^\s*[123]\s*$') { $PcNumber = [int]$in.Trim() }
}
$PcName     = "PC$PcNumber"
$ExpectedId = $EXPECTED_DEVICE_ID[$PcNumber]
$sec        = Read-Host 'Password to unlock the identity keys' -AsSecureString
$Password   = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
              [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
Log "Setting up as $PcName (identity $($ExpectedId.Substring(0,7))...)"

# ----------------------------------------------------------------------------
# STEP 1 - get + unlock the payload (template + identity keys)
# ----------------------------------------------------------------------------
$work = Join-Path $env:TEMP 'render-setup-work'
New-Item -ItemType Directory -Force $work | Out-Null
# if anything fails from here on, never leave decrypted identity keys in TEMP
trap { Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue; break }

$payload = $null
if (-not [string]::IsNullOrEmpty($PSScriptRoot)) {
    # $PSScriptRoot is empty when run via irm|iex - only trust it when set
    $local = Join-Path $PSScriptRoot 'payload.enc'
    if (Test-Path $local) { $payload = $local }
}
if (-not $payload) {
    $payload = Join-Path $work 'payload.enc'
    if (-not (Test-Path $payload)) {
        Log "Downloading setup payload..."
        Invoke-WithRetry { Invoke-WebRequest $PAYLOAD_URL -OutFile $payload -UseBasicParsing } 'payload download'
    }
}

Log "Unlocking payload..."
$zip = Join-Path $work 'payload.zip'
Unprotect-Payload $payload $zip $Password
Expand-Archive $zip -DestinationPath $work -Force
Remove-Item $zip
Ok "Payload unlocked."

$srcTemplate = Join-Path $work 'Jacky Rush Render PC Template'
$srcKeys     = Join-Path $work "render-pc-identities\pc$PcNumber"
if (-not (Test-Path $srcTemplate)) { Fail "Payload is missing the template folder." }
if (-not (Test-Path (Join-Path $srcKeys 'key.pem'))) { Fail "Payload is missing the pc$PcNumber key bundle." }

if (-not (Test-Path $TemplateDir)) {
    Log "Installing template folder..."
    New-Item -ItemType Directory -Force (Split-Path $TemplateDir) | Out-Null
    Copy-Item $srcTemplate $TemplateDir -Recurse
    Ok "Template installed."
} else { Ok "Template folder already present - leaving it alone." }

# ----------------------------------------------------------------------------
# STEP 2 - preflight
# ----------------------------------------------------------------------------
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { Fail "winget is missing on this machine - install 'App Installer' from the Microsoft Store first." }
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) { Ok "NVIDIA driver present." }
else { Warn "nvidia-smi not found - GPU rendering will not work until the NVIDIA driver is installed. Continuing anyway." }
if (-not (Test-Path "$env:windir\System32\msvcp140.dll")) {
    Log "Installing VC++ runtime..."
    Invoke-WithRetry { winget install --id Microsoft.VCRedist.2015+.x64 --silent --accept-package-agreements --accept-source-agreements | Out-Null } 'VC++ install'
}
Ok "Preflight done."

# ----------------------------------------------------------------------------
# STEP 3 - permanently disable Windows Update
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
Ok "Windows Update disabled (policy + services off, incl. the medic service)."

# ----------------------------------------------------------------------------
# STEP 4 - Python 3.11
# ----------------------------------------------------------------------------
if (Test-Path $PyExe) { Ok "Python 3.11 already installed." }
else {
    Log "Installing Python 3.11..."
    Invoke-WithRetry { winget install --id Python.Python.3.11 --scope user --silent --accept-package-agreements --accept-source-agreements | Out-Null } 'Python install'
    if (-not (Test-Path $PyExe)) { Fail "Python installed but not found at $PyExe" }
    Ok "Python 3.11 installed."
}

# ----------------------------------------------------------------------------
# STEP 5 - pip dependencies (pinned; includes pillow + NVIDIA packages)
# ----------------------------------------------------------------------------
$req = Join-Path $TemplateDir 'requirements.txt'
if (-not (Test-Path $req)) { Fail "requirements.txt not found in the template." }
Log "Installing Python packages (this is the slow step - several GB)..."
Invoke-WithRetry { & $PyExe -m pip install -r $req --no-warn-script-location; if ($LASTEXITCODE -ne 0) { throw "pip exited $LASTEXITCODE" } } 'pip install' 2
Ok "Python packages installed."

# ----------------------------------------------------------------------------
# STEP 6 - NVIDIA DLL folders onto the user PATH
# ----------------------------------------------------------------------------
$site = & $PyExe -c "import sysconfig; print(sysconfig.get_paths()['purelib'])"
$dllDirs = @("$site\nvidia\cublas\bin", "$site\nvidia\cudnn\bin", "$site\nvidia\cuda_nvrtc\bin")
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$added = 0
foreach ($d in $dllDirs) {
    if (-not (Test-Path $d)) { Warn "NVIDIA DLL folder not found (skipping): $d"; continue }
    if ($userPath -notlike "*$d*") { $userPath = "$userPath;$d" }
    $added++
}
[Environment]::SetEnvironmentVariable('Path', $userPath, 'User')
if ($added -eq 0) { Warn "No NVIDIA DLL folders found - GPU whisper may not work." }
Ok "NVIDIA DLL folders on user PATH ($added found)."

# ----------------------------------------------------------------------------
# STEP 7 - Syncthing install
# ----------------------------------------------------------------------------
$st = Find-Syncthing
if ($st) { Ok "Syncthing already installed: $st" }
else {
    Log "Installing Syncthing..."
    Invoke-WithRetry { winget install --id Syncthing.Syncthing --scope user --silent --accept-package-agreements --accept-source-agreements | Out-Null } 'Syncthing install'
    $st = Find-Syncthing
    if (-not $st) { Fail "Syncthing installed but its exe could not be located." }
    Ok "Syncthing installed: $st"
}

# ----------------------------------------------------------------------------
# STEP 8 - identity FIRST, then config (keys-first, never generate-then-swap)
# ----------------------------------------------------------------------------
Get-Process syncthing -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $StHome | Out-Null
$certDst = Join-Path $StHome 'cert.pem'
if (-not (Test-Path $certDst)) {
    Log "Planting $PcName's permanent identity..."
    Copy-Item (Join-Path $srcKeys 'cert.pem') $StHome
    Copy-Item (Join-Path $srcKeys 'key.pem')  $StHome
}
# generate fills in config.xml around EXISTING keys (it never overwrites them).
# no 2>&1 here: syncthing warnings on stderr would throw under EAP=Stop in PS 5.1
& $st generate --home=$StHome | Out-Null
if ($LASTEXITCODE -ne 0) { Fail "syncthing generate failed (exit $LASTEXITCODE)" }
$actualId = (& $st device-id --home=$StHome).Trim()
if ($actualId -ne $ExpectedId) { Fail "IDENTITY MISMATCH - this box computed $actualId but $PcName must be $ExpectedId. Stopping before anything connects." }
Ok "Identity verified: this machine IS $PcName ($($actualId.Substring(0,7))...)."

# never leave versioning/index surprises: a fresh index is CORRECT here and
# means this box can only pull, never claim deletions.

# ----------------------------------------------------------------------------
# STEP 9 - Syncthing autostart + start now
# ----------------------------------------------------------------------------
$run = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
Set-ItemProperty $run -Name 'Syncthing' -Value "`"$st`" serve --no-console --no-browser"
Start-Process $st -ArgumentList 'serve', '--no-console', '--no-browser' -WindowStyle Hidden
Wait-Until { $api = Get-StApi; (Invoke-RestMethod "$($api.Base)/system/status" -Headers $api.Head).myID -eq $ExpectedId } 'Syncthing API up' 120
Ok "Syncthing running + autostarts at login."

# ----------------------------------------------------------------------------
# STEP 10 - local folders: video bulk lives on the HDD via ONE junction
#   SSD (C:) keeps scripts/tools; Shared Folder -> D:\Shared Folder (junction)
# ----------------------------------------------------------------------------
$hdd = Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" |
       Where-Object { $_.DeviceID -ne 'C:' } |
       Sort-Object Size -Descending | Select-Object -First 1
$existing = Get-Item $SharedRoot -ErrorAction SilentlyContinue
if ($existing -and ($existing.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    Ok "Shared Folder junction already in place."
} elseif ($existing) {
    Warn "Shared Folder already exists as a REAL folder on C: - leaving it alone (migrate to the HDD manually later)."
} elseif ($hdd) {
    $hddRoot = "$($hdd.DeviceID)\Shared Folder"
    New-Item -ItemType Directory -Force $hddRoot | Out-Null
    New-Item -ItemType Directory -Force (Split-Path $SharedRoot) | Out-Null
    New-Item -ItemType Junction -Path $SharedRoot -Target $hddRoot | Out-Null
    Ok "Video storage -> HDD $($hdd.DeviceID) ($([math]::Round($hdd.Size/1GB)) GB) via Desktop junction."
} else {
    Warn "No HDD found - video folders will live on the small C: drive."
}
foreach ($d in $OutputDir, $ThumbsDir, $RenderedDir) {
    New-Item -ItemType Directory -Force $d | Out-Null
}
Ok "Local folders ready."

# ----------------------------------------------------------------------------
# STEP 11 - wire the mesh: name self, add peers, add folders (PAUSED)
# ----------------------------------------------------------------------------
$api = Get-StApi
# name self
Invoke-RestMethod "$($api.Base)/config/devices/$ExpectedId" -Headers $api.Head -Method Patch -ContentType 'application/json' -Body (@{ name = $PcName } | ConvertTo-Json)
# peers
$peers = @(
    @{ deviceID = $FARMER_ID; name = 'Orchestrator PC'; addresses = @($FARMER_ADDR, 'dynamic') }
    @{ deviceID = $PC2_ID;    name = 'ShadowPC2';       addresses = @('dynamic') }
)
$existing = @(Invoke-RestMethod "$($api.Base)/config/devices" -Headers $api.Head)
foreach ($p in $peers) {
    if ($existing.deviceID -notcontains $p.deviceID) {
        $body = @{ deviceID = $p.deviceID; name = $p.name; addresses = $p.addresses
                   compression = 'metadata'; introducer = $false; paused = $false
                   autoAcceptFolders = $false } | ConvertTo-Json -Depth 5
        Invoke-RestMethod "$($api.Base)/config/devices" -Headers $api.Head -Method Post -ContentType 'application/json' -Body $body | Out-Null
        Ok "Peer added: $($p.name)"
    }
}
# folders - exact IDs, sendreceive, PAUSED until we stage the unpause
$folders = @(
    @{ id = $FOLDER_THUMBS; label = '! Thumbnails';        path = $ThumbsDir }
    @{ id = $FOLDER_OUTPUT; label = '! Jacky Rush Output'; path = $OutputDir }
)
$existingF = @(Invoke-RestMethod "$($api.Base)/config/folders" -Headers $api.Head)
foreach ($f in $folders) {
    if ($existingF.id -notcontains $f.id) {
        $body = @{ id = $f.id; label = $f.label; path = $f.path; type = 'sendreceive'
                   paused = $true
                   devices = @(
                       @{ deviceID = $FARMER_ID; introducedBy = ''; encryptionPassword = '' }
                       @{ deviceID = $PC2_ID;    introducedBy = ''; encryptionPassword = '' }
                   ) } | ConvertTo-Json -Depth 6
        Invoke-RestMethod "$($api.Base)/config/folders" -Headers $api.Head -Method Post -ContentType 'application/json' -Body $body | Out-Null
        Ok "Folder added (paused): $($f.label)"
    }
}

# ----------------------------------------------------------------------------
# STEP 12 - general tools: Chrome, WinRAR, Git, Claude Code + dsp + skills
# (runs BEFORE the long sync so all interaction happens early)
# ----------------------------------------------------------------------------
foreach ($app in @(
    @{ id = 'Google.Chrome'; name = 'Chrome' }
    @{ id = 'RARLab.WinRAR'; name = 'WinRAR' }
    @{ id = 'Git.Git';       name = 'Git' }
)) {
    Log "Installing $($app.name)..."
    try {
        Invoke-WithRetry { winget install --id $app.id --silent --accept-package-agreements --accept-source-agreements | Out-Null } "$($app.name) install" 2
        Ok "$($app.name) ready."
    } catch { Warn "$($app.name) install failed - install it by hand later; setup continues." }
}

# Claude Code + the dsp command
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

# Skills repo + Claude config wiring (the repo's own setup.ps1 does the junctions)
$skills = Join-Path $env:USERPROFILE '.claude\skills'
$env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User') + ";$claudeBin"
if (-not (Test-Path (Join-Path $skills '.git'))) {
    Log "Cloning skills repo..."
    # via cmd so git's stderr chatter can't trip EAP=Stop; the repo has one
    # Windows-illegal filename, so a partial checkout is expected and tolerated
    & cmd /c "git clone https://github.com/JackyYu510yt/jacky-of-all-trades `"$skills`" 2>nul"
    if ($LASTEXITCODE -ne 0) { Warn "git clone reported errors (known: one repo filename is illegal on Windows) - continuing with what checked out." }
} else { Ok "Skills repo already present." }
if (Test-Path (Join-Path $skills 'setup.ps1')) {
    Log "Wiring Claude config (hooks + memory + settings)..."
    try { & powershell -ExecutionPolicy Bypass -File (Join-Path $skills 'setup.ps1') | Out-Null; Ok "Claude config wired." }
    catch { Warn "Skills setup.ps1 failed - run it by hand later." }
} else { Warn "Skills repo setup.ps1 not found - wire Claude config by hand later." }

# ----------------------------------------------------------------------------
# STEP 13 - Chrome Remote Desktop: install always, link with ONE paste
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
    $pin = ''
    $settingsPath = Join-Path $work 'setup_settings.json'
    if (Test-Path $settingsPath) { $pin = (Get-Content $settingsPath -Raw | ConvertFrom-Json).crd_pin }
    if (-not $pin -or $pin -eq 'CHANGE_ME') { $pin = Read-Host 'Choose the Chrome Remote Desktop PIN (6+ digits)' }
    Write-Host ''
    Write-Host '  LINK THIS PC TO YOUR GOOGLE ACCOUNT (one paste):' -ForegroundColor Yellow
    Write-Host '  1. On ANY device where you are logged into Google, open:'
    Write-Host '       https://remotedesktop.google.com/headless'
    Write-Host '  2. Click Begin -> Next -> Authorize, then COPY the command shown under "Windows".'
    Write-Host '  3. Paste it below. (Press Enter alone to SKIP - you can link later.)'
    $pasted = Read-Host '  paste here'
    if ($pasted -match '--code="?([^"\s]+)"?') {
        Log "Registering with Google as $PcName..."
        $eapBak = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
        $out = $pin, $pin | & $crdExe --code="$($Matches[1])" --redirect-url="https://remotedesktop.google.com/_/oauthredirect" --name="$PcName" 2>&1
        $ErrorActionPreference = $eapBak
        if ($LASTEXITCODE -eq 0) { Ok "Chrome Remote Desktop linked - this PC is '$PcName' in your device list." }
        else { Warn "CRD registration failed: $($out | Out-String)" }
    } elseif ($pasted.Trim()) { Warn 'Could not find --code=... in that paste - CRD link skipped.' }
    else { Warn 'CRD linking skipped by choice.' }
}

# ----------------------------------------------------------------------------
# STEP 14 - staged unpause: thumbnails first, then the big work folder
# ----------------------------------------------------------------------------
Log "Waiting for a connection to the farmer..."
Wait-Until {
    $c = Invoke-RestMethod "$($api.Base)/system/connections" -Headers $api.Head
    $c.connections.$FARMER_ID.connected
} 'farmer connection' 600
Ok "Connected to the farmer."

function Unpause-AndSync([string]$Fid, [string]$Label, [int]$TimeoutSec) {
    Invoke-RestMethod "$($api.Base)/config/folders/$Fid" -Headers $api.Head -Method Patch -ContentType 'application/json' -Body '{"paused":false}' | Out-Null
    Log "Syncing $Label..."
    Wait-Until {
        $s = Invoke-RestMethod "$($api.Base)/db/completion?folder=$Fid" -Headers $api.Head
        # globalBytes>0 guards the startup race: an index that hasn't arrived yet
        # reports completion=100 on an empty folder
        ($s.globalBytes -gt 0) -and ($s.completion -ge 100) -and ($s.needBytes -eq 0)
    } "$Label fully synced" $TimeoutSec 10
    Ok "$Label synced."
}
Unpause-AndSync $FOLDER_THUMBS '! Thumbnails' 1800
Unpause-AndSync $FOLDER_OUTPUT '! Jacky Rush Output' 14400   # up to 4h - the work folder can be 20+ GB

# ----------------------------------------------------------------------------
# STEP 15 - watcher config: this machine's claim-protocol name
# ----------------------------------------------------------------------------
$cfgPath = Join-Path $TemplateDir 'render_watcher_config.json'
if (-not (Test-Path $cfgPath)) { Fail "render_watcher_config.json not found in the template." }
$cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
$cfg.my_pc_name = $PcName
# NOTE: mats_output_path intentionally points at ! Jacky Rush Output - do not "fix"
[IO.File]::WriteAllText($cfgPath, ($cfg | ConvertTo-Json -Depth 10), (New-Object Text.UTF8Encoding($false)))
Ok "Watcher config: my_pc_name = $PcName"

# ----------------------------------------------------------------------------
# STEP 16 - start the watcher + its autostart (only now that sync is complete)
# ----------------------------------------------------------------------------
$launch = Join-Path $TemplateDir 'launch.bat'
if (-not (Test-Path $launch)) { Fail "launch.bat not found in the template." }
Set-ItemProperty $run -Name 'JackyRushWatcher' -Value "cmd.exe /c cd /d `"$TemplateDir`" && launch.bat"
# refresh PATH so this FIRST launch already sees the just-installed py launcher
# and NVIDIA DLL dirs (they were written to the registry, not this session)
$env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { Warn "'py' launcher not on PATH yet - if the watcher window errors, reboot once and it will autostart correctly." }
Start-Process cmd.exe -ArgumentList '/c', 'launch.bat' -WorkingDirectory $TemplateDir
Ok "Watcher started + autostarts at login."

# ----------------------------------------------------------------------------
# cleanup + summary
# ----------------------------------------------------------------------------
Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
Write-Host ""
Write-Host "=====================================================" -ForegroundColor Green
Write-Host " $PcName IS FULLY SET UP" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green
Write-Host " identity   : $ExpectedId"
Write-Host " folders    : ! Jacky Rush Output + ! Thumbnails (synced)"
Write-Host " watcher    : running, autostarts at login"
Write-Host " win update : permanently disabled"
Write-Host " tools      : Chrome, WinRAR, Git, Claude Code (+dsp), skills repo, CRD"
Write-Host ""
Write-Host " Remaining by hand: run 'claude login' once (credentials are never bundled)."
Write-Host " Reboot once to prove autostart if you want the full test."
