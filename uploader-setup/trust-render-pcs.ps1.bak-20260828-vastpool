# Makes the LIVE uploader trust every render PC and share "! Jacky Rush Rendered"
# with each - so a render PC setup connects with ZERO clicks on this machine.
# Idempotent: safe to re-run any time. Run on the Uploading PC whenever the
# render fleet roster changes:
#   irm https://raw.githubusercontent.com/JackyYu510yt/jacky-of-all-trades/main/uploader-setup/trust-render-pcs.ps1 | iex
#
# Keep this list in lockstep with setup.ps1 $RenderPCs and
# render-setup/setup.ps1 $EXPECTED_DEVICE_ID (identities are payload-sealed,
# so these IDs survive render PC rebuilds).

$ErrorActionPreference = 'Stop'

$RenderPCs = @(
    @{ Name = 'Render PC1'; Id = 'VYEHZ24-DHRHMQ7-U6R4O4E-FL7DANW-WZIGZKO-AXL2PKZ-O5F4MRU-DDB4VQU' },
    @{ Name = 'Render PC2'; Id = 'NSBTRAN-KTBVNJH-TXEQDYW-6KA3RYS-WWV34MU-XSMYIL5-WWU7RRH-OYBI2A4' },
    @{ Name = 'Render PC3'; Id = 'ZGSLY26-WJMJXAC-6EU2K7I-C6U7FYU-RDXI5SI-FPVC5GR-IKCIUTA-2U2H2A5' },
    @{ Name = 'Render PC4'; Id = 'XSXJ73D-M4ZEYXP-3TMZGIX-5AQTZBP-47ZN2S2-C6PXQF4-6TAB5MV-VDUSJQE' },
    @{ Name = 'Render PC5'; Id = 'OBY47V5-FXCSZCM-2WQT55V-IHMJXJF-QKGUFXG-J6RONWC-UFMJKL7-EPWRFAG' }
)
$FolderId = 'jr-rendered'

# Talk to the local Syncthing through its own REST API (no exe path guessing).
$cfgPath = "$env:LOCALAPPDATA\Syncthing\config.xml"
if (-not (Test-Path $cfgPath)) { $cfgPath = "$env:APPDATA\Syncthing\config.xml" }
if (-not (Test-Path $cfgPath)) { throw 'Syncthing config.xml not found - is Syncthing installed on this machine?' }
[xml]$cfg = Get-Content $cfgPath
$base = "http://$($cfg.configuration.gui.address)/rest"
$hdr  = @{ 'X-API-Key' = $cfg.configuration.gui.apikey }

try { Invoke-RestMethod -Uri "$base/system/ping" -Headers $hdr | Out-Null }
catch { throw 'Syncthing is not running (or the API is unreachable) - start it first, then re-run.' }

# 1. Trust each render PC. Only ADD missing devices - never overwrite an
#    existing entry (that would reset its per-device settings).
$known = @(Invoke-RestMethod -Uri "$base/config/devices" -Headers $hdr | ForEach-Object { $_.deviceID })
foreach ($pc in $RenderPCs) {
    if ($known -contains $pc.Id) {
        Write-Host "already trusted : $($pc.Name)"
    } else {
        $body = @{ deviceID = $pc.Id; name = $pc.Name; addresses = @('dynamic') } | ConvertTo-Json
        Invoke-RestMethod -Uri "$base/config/devices/$($pc.Id)" -Method Put -Headers $hdr -ContentType 'application/json' -Body $body | Out-Null
        Write-Host "trusted NEW     : $($pc.Name)" -ForegroundColor Green
    }
}

# 2. Share the Rendered folder with each of them (append-only, same reason).
$folder = Invoke-RestMethod -Uri "$base/config/folders/$FolderId" -Headers $hdr
$have = @($folder.devices | ForEach-Object { $_.deviceID })
$added = $false
foreach ($pc in $RenderPCs) {
    if ($have -contains $pc.Id) {
        Write-Host "already shared  : $($pc.Name)"
    } else {
        $folder.devices += [pscustomobject]@{ deviceID = $pc.Id; introducedBy = ''; encryptionPassword = '' }
        $added = $true
        Write-Host "shared NEW      : $($pc.Name)" -ForegroundColor Green
    }
}
if ($added) {
    Invoke-RestMethod -Uri "$base/config/folders/$FolderId" -Method Put -Headers $hdr -ContentType 'application/json' -Body ($folder | ConvertTo-Json -Depth 10) | Out-Null
}

Write-Host ''
Write-Host 'Done. Every render PC is pre-trusted + pre-shared on jr-rendered.' -ForegroundColor Green
Write-Host 'A fresh render PC setup now syncs with zero clicks on this machine.' -ForegroundColor Green
