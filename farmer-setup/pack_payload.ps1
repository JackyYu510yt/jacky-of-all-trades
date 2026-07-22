# ============================================================================
#  pack_payload.ps1 - run on the FARMER to (re)build farmer payload.enc
#
#  Zips everything only this machine has - Syncthing identity + live mesh
#  config, the pc1/pc2/pc3 identity bundles, the master render template, the
#  orchestrator scripts (no logs/outputs), the snapshot scanner, and the small
#  autostart helpers - then locks the zip with a password you type. The locked
#  file (payload.enc) is safe to host publicly - without the password it is
#  random noise.
#
#  Re-run any time the scripts change, type the same password, re-upload.
#  Same AES format as render-setup/pack_payload.ps1: [16B salt][16B IV][cipher]
# ============================================================================

param([string]$Password)

$ErrorActionPreference = 'Stop'

$StHome      = Join-Path $env:LOCALAPPDATA 'Syncthing'
$KeysDir     = 'C:\Users\Shadow\Desktop\render-pc-identities'
$TemplateDir = 'C:\Users\Shadow\Desktop\Testing\Jacky Rush Render PC Template'
$JackyDir    = 'C:\Users\Shadow\Desktop\Testing\Jacky Rush'
$VercelDir   = 'C:\Users\Shadow\Desktop\Testing\Vercel'
$JarvisDir   = 'C:\Users\Shadow\Desktop\Compiled Binaries\Tinkering\jarvis'
$StartupDir  = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
$OutFile     = Join-Path $PSScriptRoot 'payload.enc'

foreach ($must in @("$StHome\cert.pem", "$StHome\key.pem", "$StHome\config.xml")) {
    if (-not (Test-Path $must)) { throw "Syncthing identity file missing: $must" }
}
foreach ($pc in 'pc1', 'pc2', 'pc3') {
    if (-not (Test-Path "$KeysDir\$pc\key.pem")) { throw "Key bundle missing: $KeysDir\$pc" }
}
if (-not (Test-Path $TemplateDir)) { throw "Template folder not found: $TemplateDir" }
if (-not (Test-Path "$JackyDir\jacky_rush_farmer.py")) { throw "Orchestrator folder not found: $JackyDir" }

if ($Password) { $p1 = $Password }
else {
    $s1 = Read-Host 'Choose the unlock password (you will type this on a future farmer rebuild)' -AsSecureString
    $s2 = Read-Host 'Type it again to confirm' -AsSecureString
    $p1 = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s1))
    $p2 = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s2))
    if ($p1 -ne $p2) { throw 'Passwords did not match - run again.' }
}
if ($p1.Length -lt 16) { throw 'Password must be at least 16 characters - it guards identity keys in a public download.' }

# stage: one folder holding exactly what setup.ps1 expects to find in the zip
$stage = Join-Path $env:TEMP 'farmer-payload-stage'
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory $stage | Out-Null

# --- Syncthing identity + live config: cert, key, config.xml and NOTHING else.
#     NEVER the index-v2 database - an old index next to empty folders
#     broadcasts deletions mesh-wide, and versioning is off (permanent).
Write-Host 'Staging Syncthing identity + config...'
$stStage = New-Item -ItemType Directory (Join-Path $stage 'syncthing-identity')
Copy-Item "$StHome\cert.pem"   $stStage
Copy-Item "$StHome\key.pem"    $stStage
Copy-Item "$StHome\config.xml" $stStage

# --- the render PCs' identity bundles (these exist ONLY on this machine)
Write-Host 'Staging render PC identities...'
Copy-Item $KeysDir (Join-Path $stage 'render-pc-identities') -Recurse

# --- master render template (same junk-strip as render-setup/pack_payload.ps1)
Write-Host 'Staging master template...'
Copy-Item $TemplateDir (Join-Path $stage 'Jacky Rush Render PC Template') -Recurse
Get-ChildItem (Join-Path $stage 'Jacky Rush Render PC Template') -Recurse -Force -Include 'render_watcher_log.txt', '_render_manifest.*.json', '__pycache__' |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# --- orchestrator scripts + configs + state, WITHOUT logs/outputs/backups.
#     Kept: all code, configs, secrets (cookies.txt, proxies.txt), quota state.
#     Dropped: render outputs, scratch, test-run dirs (_*), logs, ledgers, baks.
Write-Host 'Staging orchestrator (scripts only, no logs/outputs)...'
$jrDst = Join-Path $stage 'Jacky Rush'
$xd = @('outputFiles', 'render_scratch', 'output', 'auto', 'auto-runs',
        'error-recon', '.claude', '__pycache__') +
      (Get-ChildItem $JackyDir -Directory | Where-Object { $_.Name -like '_*' } | ForEach-Object { $_.FullName })
robocopy $JackyDir $jrDst /E /XJ /NFL /NDL /NJH /NJS /R:1 /W:1 `
    /XD @xd `
    /XF *.log *.jsonl *.csv *.old *.lock *.tmp *_log.txt *_slim.txt *.bak* | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed staging $JackyDir (exit $LASTEXITCODE)" }

# --- snapshot scanner (feeds the yt-dashboard on Supabase)
Write-Host 'Staging snapshot scanner...'
$vDst = New-Item -ItemType Directory (Join-Path $stage 'Vercel')
foreach ($f in 'render_snapshot_scanner.py', 'start_render_scanner.bat',
               'render_snapshot_setup.sql', 'README_deploy.md') {
    Copy-Item (Join-Path $VercelDir $f) $vDst
}

# --- jarvis overlay scripts
Write-Host 'Staging jarvis...'
$jDst = Join-Path $stage 'jarvis'
robocopy $JarvisDir $jDst /E /XJ /NFL /NDL /NJH /NJS /R:1 /W:1 /XD __pycache__ /XF *.log | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed staging $JarvisDir (exit $LASTEXITCODE)" }

# --- small autostart helpers that live outside any project folder
Write-Host 'Staging autostart helpers...'
$misc = New-Item -ItemType Directory (Join-Path $stage 'misc')
$mStartup = New-Item -ItemType Directory (Join-Path $misc 'startup')
foreach ($f in 'Copy Title Transcript Downloader V5.vbs', 'transcript_api.py', 'proxies.txt') {
    Copy-Item (Join-Path $StartupDir $f) $mStartup
}
Copy-Item "$env:LOCALAPPDATA\bot_restart.ps1" $misc
Copy-Item 'C:\Users\Shadow\Desktop\Compiled Binaries\Tinkering\stagger-dashboard\helper\supervisor.ps1' $misc
Copy-Item 'C:\Tools\AutoHotkey\WinVDitto.exe' $misc
Copy-Item 'C:\Users\Shadow\Desktop\ClipAngel 2.22' (Join-Path $misc 'ClipAngel 2.22') -Recurse

# zip tools drop empty dirs (inputFiles, processing, niches...) - plant placeholders
Get-ChildItem $stage -Recurse -Directory | Where-Object { -not (Get-ChildItem $_.FullName -Force) } |
    ForEach-Object { New-Item -ItemType File (Join-Path $_.FullName '.keep') | Out-Null }

Write-Host 'Zipping...'
$zip = Join-Path $env:TEMP 'farmer-payload.zip'
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive "$stage\*" -DestinationPath $zip -CompressionLevel Optimal

Write-Host 'Locking with your password (AES-256)...'
$plain = [IO.File]::ReadAllBytes($zip)
$salt  = New-Object byte[] 16
$rng   = [Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($salt)
$kdf = New-Object Security.Cryptography.Rfc2898DeriveBytes(
           $p1, $salt, 600000, [Security.Cryptography.HashAlgorithmName]::SHA256)
$aes = [Security.Cryptography.Aes]::Create()
$aes.Key = $kdf.GetBytes(32)
$aes.GenerateIV()
$cipher = $aes.CreateEncryptor().TransformFinalBlock($plain, 0, $plain.Length)
[IO.File]::WriteAllBytes($OutFile, ($salt + $aes.IV + $cipher))

Remove-Item $zip, $stage -Recurse -Force
$mb = [math]::Round((Get-Item $OutFile).Length / 1MB, 1)
$sha = (Get-FileHash $OutFile -Algorithm SHA256).Hash
Write-Host ''
Write-Host "DONE -> $OutFile  ($mb MB)" -ForegroundColor Green
Write-Host "SHA256: $sha"
if ($mb -gt 1900) { Write-Host 'WARNING: over GitHub''s 2 GB release-asset cap - trim the staging list.' -ForegroundColor Yellow }
Write-Host 'Next: upload payload.enc as the GitHub release asset (tag farmer-setup-v1).'
