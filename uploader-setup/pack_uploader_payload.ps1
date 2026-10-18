# ============================================================================
#  pack_uploader_payload.ps1 - run on the LIVE uploader to (re)build payload.enc
#
#  Seals what makes this machine "the uploader" into one password-locked file:
#    - Syncthing identity (cert/key) + full config.xml (every trusted device,
#      both folders, GUI key) + the exact Syncthing binary
#    - C:\Tools (uploader reaper + its Supabase config) and the checksum guard
#    - the scheduled task definitions, pip package list, user PATH, Run keys
#    - small app settings (ClipAngel, VS Code, Windows Terminal, WinRAR)
#  Same lock as render-setup/pack_payload.ps1 (AES-256, PBKDF2-SHA256 600k),
#  so payload.enc is safe to host publicly.
#
#  Bulk data (videos, browser profiles, WSL disk, Desktop) is NOT in here -
#  setup.ps1 copies that straight from the old box over Tailscale.
#
#  -Upload publishes it as the uploader-setup-v1 GitHub release asset, using
#  the git credential already stored in Windows Credential Manager.
#
#  Re-run any time the uploader's setup changes, same password, -Upload.
#
#  -StageOnly <dir> stages the same content unencrypted into <dir> and stops
#  (used by migrate-source.ps1 -Agent, which hands it to a new box over SMB).
# ============================================================================

param([string]$Password, [switch]$Upload, [string]$StageOnly)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Repo       = 'JackyYu510yt/jacky-of-all-trades'
$ReleaseTag = 'uploader-setup-v1'
$StHome     = "$env:LOCALAPPDATA\Syncthing"
$StDir      = "$env:LOCALAPPDATA\Programs\Syncthing"
$GuardDir   = Join-Path $env:USERPROFILE 'Desktop\Compiled Binaries\uploader_checksum_guard'
$PyExe      = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
$Tasks      = 'Syncthing (boot, no login)', 'JackyRushChecksumGuard', 'JackyRushUploaderReaper'
$OutFile    = Join-Path $PSScriptRoot 'payload.enc'

foreach ($f in 'cert.pem', 'key.pem', 'config.xml') {
    if (-not (Test-Path "$StHome\$f")) { throw "Not an uploader: $StHome\$f missing" }
}

if ($StageOnly) { $p1 = $null }
elseif ($Password) { $p1 = $Password }
else {
    $s1 = Read-Host 'Choose the unlock password (you will type this on the new uploader)' -AsSecureString
    $s2 = Read-Host 'Type it again to confirm' -AsSecureString
    $p1 = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s1))
    $p2 = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s2))
    if ($p1 -ne $p2) { throw 'Passwords did not match - run again.' }
}
if (-not $StageOnly -and $p1.Length -lt 16) { throw 'Password must be at least 16 characters - it guards the uploader identity in a public download.' }

# stage: one folder holding exactly what setup.ps1 expects to find in the zip
$stage = if ($StageOnly) { $StageOnly } else { Join-Path $env:TEMP 'uploader-payload-stage' }
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory $stage | Out-Null
function Stage([string]$From, [string]$To) {
    if (-not (Test-Path -LiteralPath $From)) { Write-Host "  (absent, skipped) $From" -ForegroundColor DarkGray; return }
    $dest = Join-Path $stage $To
    New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
    Copy-Item -LiteralPath $From $dest -Recurse -Force
    Write-Host "  + $To"
}

Write-Host 'Staging...'
# Identity + config. NOT index-v2: a fresh index is what makes the new box
# re-hash its copied files instead of trusting a stale database.
foreach ($f in 'cert.pem', 'key.pem', 'https-cert.pem', 'https-key.pem', 'config.xml') { Stage "$StHome\$f" "syncthing-home\$f" }
Stage $StDir                                  'syncthing-bin'
Stage 'C:\Tools'                              'tools'
Stage $GuardDir                               'checksum-guard'
Stage "$env:LOCALAPPDATA\ClipAngel\Settings.settings" 'settings\ClipAngel\Settings.settings'
Stage "$env:APPDATA\Code\User\settings.json"          'settings\Code-User\settings.json'
Stage "$env:APPDATA\Code\User\keybindings.json"       'settings\Code-User\keybindings.json'
Stage "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json" 'settings\WindowsTerminal\settings.json'
Stage "$env:APPDATA\WinRAR"                   'settings\WinRAR'

New-Item -ItemType Directory (Join-Path $stage 'tasks') | Out-Null
foreach ($t in $Tasks) {
    if (Get-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue) {
        Export-ScheduledTask -TaskName $t | Set-Content -LiteralPath (Join-Path $stage "tasks\$t.xml") -Encoding Unicode
        Write-Host "  + tasks\$t.xml"
    }
}

& $PyExe -m pip freeze --disable-pip-version-check | Set-Content (Join-Path $stage 'pip-freeze.txt') -Encoding ascii
Write-Host '  + pip-freeze.txt'

$run = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$deviceId = (& "$StDir\syncthing.exe" device-id | Select-Object -Last 1).Trim()
$manifest = [ordered]@{
    packed_at    = (Get-Date).ToString('s')
    source_host  = $env:COMPUTERNAME
    source_user  = $env:USERNAME
    source_home  = $env:USERPROFILE
    device_id    = $deviceId
    user_path    = [Environment]::GetEnvironmentVariable('Path', 'User')
    run_keys     = [ordered]@{ ClipAngel = $run.ClipAngel; Syncthing = $run.Syncthing }
}
[IO.File]::WriteAllText((Join-Path $stage 'manifest.json'), ($manifest | ConvertTo-Json), (New-Object Text.UTF8Encoding $false))
Write-Host "  + manifest.json (device $($deviceId.Substring(0,7)))"

# strip what must never ship
Get-ChildItem $stage -Recurse -Force -Include '__pycache__', '*.pyc', 'syncthing.lock' |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

if ($StageOnly) { Write-Host "STAGED -> $stage"; exit 0 }

Write-Host 'Zipping...'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = Join-Path $env:TEMP 'uploader-payload.zip'
if (Test-Path $zip) { Remove-Item $zip }
[IO.Compression.ZipFile]::CreateFromDirectory($stage, $zip, 'Optimal', $false)

Write-Host 'Locking with your password (AES-256)...'
$plain = [IO.File]::ReadAllBytes($zip)
$salt  = New-Object byte[] 16
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($salt)
$kdf = New-Object Security.Cryptography.Rfc2898DeriveBytes(
           $p1, $salt, 600000, [Security.Cryptography.HashAlgorithmName]::SHA256)
$aes = [Security.Cryptography.Aes]::Create()
$aes.Key = $kdf.GetBytes(32)
$aes.GenerateIV()
$cipher = $aes.CreateEncryptor().TransformFinalBlock($plain, 0, $plain.Length)
[IO.File]::WriteAllBytes($OutFile, ($salt + $aes.IV + $cipher))

Remove-Item $zip, $stage -Recurse -Force
$mb = [math]::Round((Get-Item $OutFile).Length / 1MB, 1)
Write-Host ''
Write-Host "DONE -> $OutFile  ($mb MB)" -ForegroundColor Green
Write-Host "SHA256: $((Get-FileHash $OutFile -Algorithm SHA256).Hash)"

if (-not $Upload) {
    Write-Host "Next: re-run with -Upload, or attach payload.enc to the '$ReleaseTag' GitHub release by hand."
    return
}

# --- publish to the GitHub release (token from Windows Credential Manager) ---
Add-Type -Namespace W -Name Cred -MemberDefinition @'
[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
public struct CREDENTIAL { public int Flags; public int Type; public string TargetName; public string Comment;
  public long LastWritten; public int CredentialBlobSize; public IntPtr CredentialBlob; public int Persist;
  public int AttributeCount; public IntPtr Attributes; public string TargetAlias; public string UserName; }
[DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
public static extern bool CredRead(string target, int type, int flags, out IntPtr cred);
public static string Get(string target) {
  IntPtr p; if (!CredRead(target, 1, 0, out p)) return null;
  var c = (CREDENTIAL)Marshal.PtrToStructure(p, typeof(CREDENTIAL));
  return Marshal.PtrToStringUni(c.CredentialBlob, c.CredentialBlobSize / 2); }
'@
$token = [W.Cred]::Get('git:https://github.com')
if (-not $token) { throw 'No GitHub credential in Credential Manager (git:https://github.com) - upload payload.enc by hand.' }
$h = @{ Authorization = "token $token"; 'User-Agent' = 'uploader-pack'; Accept = 'application/vnd.github+json' }

try { $rel = Invoke-RestMethod "https://api.github.com/repos/$Repo/releases/tags/$ReleaseTag" -Headers $h -UseBasicParsing }
catch {
    $body = @{ tag_name = $ReleaseTag; name = 'Uploader setup payload'; body = 'Encrypted uploader identity + config. See uploader-setup/README.md.' } | ConvertTo-Json
    $rel = Invoke-RestMethod "https://api.github.com/repos/$Repo/releases" -Method Post -Headers $h -Body $body -ContentType 'application/json' -UseBasicParsing
    Write-Host "Created release $ReleaseTag"
}
foreach ($a in @($rel.assets | Where-Object { $_.name -eq 'payload.enc' })) {
    Invoke-RestMethod "https://api.github.com/repos/$Repo/releases/assets/$($a.id)" -Method Delete -Headers $h -UseBasicParsing | Out-Null
}
$up = Invoke-RestMethod "https://uploads.github.com/repos/$Repo/releases/$($rel.id)/assets?name=payload.enc" -Method Post `
        -Headers $h -InFile $OutFile -ContentType 'application/octet-stream' -UseBasicParsing
Write-Host "UPLOADED -> $($up.browser_download_url)" -ForegroundColor Green
