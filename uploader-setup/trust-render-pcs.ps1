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

# The rented-rig delivery pool (added 2026-08-28). Kept SEPARATE from $RenderPCs
# above because those are physical machines with payload-sealed identities that must
# stay in lockstep with setup.ps1; these 8 are fixed pool identities a vast.ai rig
# assumes at boot (one per concurrent rig — core/vast.py:150 "uploader is told to
# trust exactly these 8"). Same trust + same share, different provenance.
#
# WHY THEY ARE HERE (2026-08-28): completeness, NOT a diagnosis. This list is the
# durable roster; a future uploader rebuild would otherwise silently drop the 8 pool
# identities. Adding them is idempotent and free.
#
# DO NOT READ THIS AS "the trust step was never run" — that was checked and is FALSE.
# The vast-syncthing-delivery-003714 run records device-trust already done
# (log.txt:615, 2026-08-25) and the folder-share half fixed 8/8 the same day
# (log.txt:675), followed by a real DELIVERY_CONFIRMED via PCvast-1 (log.txt:690).
# Delivery has been PROVEN working on this fleet.
#
# The still-open 2026-08-28 failure is therefore NOT this: a rented rig staged a real
# 49.5 MB video under the exactly-correct filename, then sat in "confirming delivery"
# for the full 1800s timeout with ZERO `[pcvast] completion(...)` lines — i.e.
# connected_seen=False, the uploader never connected AS PCvast-2 in that window.
# Proven on 08-25 with PCvast-1, failing on 08-28 as PCvast-2, so the cause is
# something specific to that slot or to that moment (uploader offline / discovery /
# a per-slot share gap), NOT a missing trust step. Diagnose before spending again.
$VastPCs = @(
    @{ Name = 'PCvast-1'; Id = '6EKZ3ZM-42PKZRE-35RPCZG-OAB4YJM-HACLJKG-SJ3UO3O-I2ZIFXV-POLDEAE' },
    @{ Name = 'PCvast-2'; Id = 'KNQDU33-KWGWB6U-V3TDO3K-AHH6FJG-NPJLSSH-UQ576QY-JDBIPH4-FJSWRQG' },
    @{ Name = 'PCvast-3'; Id = '7RTASOV-YWMT4JU-62Z6QCZ-QED6DZC-4B7A6MR-OQAIBVR-5SWMTH6-2K3BGQ6' },
    @{ Name = 'PCvast-4'; Id = '6OCVMHB-WWIKJV2-3K5ZD26-QSOFRW6-DS7ICMM-QWEAH42-S6SMCGX-MQ5VJAY' },
    @{ Name = 'PCvast-5'; Id = 'YBKI7BS-QVTBWDL-HTH4XW7-63SL3FL-BDRQW2O-NLUB3XR-5LE6DK5-VLE3CA3' },
    @{ Name = 'PCvast-6'; Id = 'X6QUUG7-QQM5245-4XJDUQH-UQ7TFCT-AKA6CAL-5HUUFJQ-3H3UZXA-K2NMWAK' },
    @{ Name = 'PCvast-7'; Id = 'IXO5VVY-WTKVDWD-I4IXZTM-UJ3PYOF-EODKSAQ-MV243NF-2XMOAQZ-WXJYIAX' },
    @{ Name = 'PCvast-8'; Id = 'KKEZOOY-PMFDNZ7-NIF34X7-AOAGOFI-DAAGPE3-WUOR373-VJSZSDN-XTZLMAX' }
)

# One list from here down — trust + share treat both kinds identically.
$RenderPCs = $RenderPCs + $VastPCs

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
