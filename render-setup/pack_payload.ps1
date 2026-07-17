# ============================================================================
#  pack_payload.ps1 - run on the FARMER to (re)build payload.enc
#
#  Zips the render template + all identity key bundles, then locks the zip
#  with a password you type. The locked file (payload.enc) is safe to host
#  publicly - without the password it is random noise.
#
#  Re-run any time the template changes, type the same password, re-upload.
# ============================================================================

param([string]$Password)

$ErrorActionPreference = 'Stop'

$TemplateDir = 'C:\Users\Shadow\Desktop\Testing\Jacky Rush Render PC Template'
$KeysDir     = 'C:\Users\Shadow\Desktop\render-pc-identities'
$OutFile     = Join-Path $PSScriptRoot 'payload.enc'

if (-not (Test-Path $TemplateDir)) { throw "Template folder not found: $TemplateDir" }
foreach ($pc in 'pc1', 'pc2', 'pc3') {
    if (-not (Test-Path "$KeysDir\$pc\key.pem")) { throw "Key bundle missing: $KeysDir\$pc" }
}

if ($Password) { $p1 = $Password }
else {
    $s1 = Read-Host 'Choose the unlock password (you will type this on every future PC setup)' -AsSecureString
    $s2 = Read-Host 'Type it again to confirm' -AsSecureString
    $p1 = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s1))
    $p2 = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s2))
    if ($p1 -ne $p2) { throw 'Passwords did not match - run again.' }
}
if ($p1.Length -lt 16) { throw 'Password must be at least 16 characters - it guards identity keys in a public download.' }

# stage: one folder holding exactly what setup.ps1 expects to find in the zip
$stage = Join-Path $env:TEMP 'payload-stage'
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory $stage | Out-Null
Write-Host 'Staging template + keys...'
Copy-Item $TemplateDir (Join-Path $stage 'Jacky Rush Render PC Template') -Recurse
Copy-Item $KeysDir     (Join-Path $stage 'render-pc-identities') -Recurse

# strip machine-specific junk that must never ship (per the rebuild handoff)
Get-ChildItem $stage -Recurse -Force -Include 'render_watcher_log.txt', '_render_manifest.*.json', '__pycache__' |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# zip tools drop empty dirs (render_scratch, background_music) - plant placeholders
Get-ChildItem $stage -Recurse -Directory | Where-Object { -not (Get-ChildItem $_.FullName -Force) } |
    ForEach-Object { New-Item -ItemType File (Join-Path $_.FullName '.keep') | Out-Null }

Write-Host 'Zipping...'
$zip = Join-Path $env:TEMP 'payload.zip'
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
Write-Host 'Next: upload payload.enc as the GitHub release asset (setup.ps1 knows the URL).'
