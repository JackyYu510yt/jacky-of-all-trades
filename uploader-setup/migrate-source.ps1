# ============================================================================
#  migrate-source.ps1 - run on the OLD uploader when moving to a new box
#
#  -Prepare  Lets the new box copy files from this one: SMB (port 445) opened
#            to the Tailscale network ONLY, on the Tailscale adapter ONLY.
#            The public adapter stays closed. Nothing stops; uploading goes on.
#  -Cutover  Makes this box inert so the new box can take over its identity:
#            stops Syncthing, AdsPower, Chrome and WSL, disables every way
#            Syncthing or the uploader tasks could start again, then drops an
#            INERT marker that the new box's setup.ps1 waits for.
#            Two machines must NEVER run the same Syncthing identity at once.
#  -Undo     Rollback: re-enables everything -Cutover disabled, removes the
#            marker and the firewall rule. Only use it if the new box has NOT
#            started Syncthing yet.
#
#  Run elevated.
# ============================================================================

param([switch]$Prepare, [switch]$Cutover, [switch]$Undo)

$ErrorActionPreference = 'Stop'

$RuleName = 'Uploader migration - SMB from Tailscale only'
$StateDir = 'C:\ProgramData\uploader-migration'
$Marker   = Join-Path $StateDir 'INERT.txt'
$RunSave  = Join-Path $StateDir 'run-syncthing.txt'
$Tasks    = 'Syncthing (boot, no login)', 'JackyRushChecksumGuard', 'JackyRushUploaderReaper'
$RunKey   = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) { throw 'Run this from an elevated (Run as administrator) PowerShell.' }
if (-not ($Prepare -or $Cutover -or $Undo)) { throw 'Pick one: -Prepare, -Cutover or -Undo' }
New-Item -ItemType Directory -Force $StateDir | Out-Null

function Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }

if ($Prepare) {
    Step 'Open SMB to Tailscale only'
    if (-not (Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -DisplayName $RuleName -Direction Inbound -Protocol TCP -LocalPort 445 `
            -RemoteAddress '100.64.0.0/10' -InterfaceAlias 'Tailscale' -Action Allow | Out-Null
    }
    Set-Service LanmanServer -StartupType Automatic
    Start-Service LanmanServer
    $ip = (& "C:\Program Files\Tailscale\tailscale.exe" ip -4 | Select-Object -First 1).Trim()
    Write-Host "Ready. On the NEW box, when setup.ps1 asks for the old uploader, give it:" -ForegroundColor Green
    Write-Host "  address : $ip" -ForegroundColor Green
    Write-Host "  login   : $env:COMPUTERNAME\$env:USERNAME (this box's Windows password)" -ForegroundColor Green
}

if ($Cutover) {
    Step 'Stop everything that holds files or the identity'
    foreach ($t in $Tasks) {
        if (Get-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue) {
            Stop-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue
            Disable-ScheduledTask -TaskName $t | Out-Null
            Write-Host "disabled task : $t"
        }
    }
    $run = (Get-ItemProperty $RunKey -ErrorAction SilentlyContinue).Syncthing
    if ($run) {
        Set-Content -LiteralPath $RunSave -Value $run
        Remove-ItemProperty $RunKey -Name Syncthing
        Write-Host 'removed       : HKCU Run Syncthing (saved for -Undo)'
    }
    foreach ($p in 'syncthing', 'AdsPower Global', 'SunBrowser', 'chrome', 'ClipAngel') {
        Get-Process -Name $p -ErrorAction SilentlyContinue | Stop-Process -Force
    }
    wsl --shutdown
    Start-Sleep 3
    if (Get-Process syncthing -ErrorAction SilentlyContinue) { throw 'Syncthing is still running - stop it by hand, then re-run -Cutover.' }
    Set-Content -LiteralPath $Marker -Value "Inert since $(Get-Date -Format s). Syncthing identity handed to the new uploader."
    Write-Host ''
    Write-Host 'INERT. This box no longer runs Syncthing or the uploader tasks.' -ForegroundColor Green
    Write-Host 'Do not start Syncthing here again - the new box now owns this identity.' -ForegroundColor Yellow
    Write-Host 'Leave this box ON until the new box''s setup.ps1 says DONE (it copies from here).' -ForegroundColor Yellow
}

if ($Undo) {
    Step 'Roll back'
    foreach ($t in $Tasks) {
        if (Get-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue) { Enable-ScheduledTask -TaskName $t | Out-Null; Write-Host "enabled task : $t" }
    }
    if (Test-Path $RunSave) { Set-ItemProperty $RunKey -Name Syncthing -Value (Get-Content -LiteralPath $RunSave -Raw).Trim(); Remove-Item $RunSave }
    Remove-Item $Marker -ErrorAction SilentlyContinue
    Remove-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue
    Start-ScheduledTask -TaskName 'Syncthing (boot, no login)' -ErrorAction SilentlyContinue
    Write-Host 'Rolled back: this box is the uploader again.' -ForegroundColor Green
}
