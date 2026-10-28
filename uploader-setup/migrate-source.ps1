# ============================================================================
#  migrate-source.ps1 - the OLD uploader's side of moving to a new box
#
#  -InstallAgent  Run ONCE, any time before the move (elevated). Opens SMB
#                 (445) to the Tailscale network only, on the Tailscale adapter
#                 only, and installs a tiny scheduled task that answers the new
#                 box. After this, moving is ONE command on the new box -
#                 nothing more to run here.
#  -Agent         What that task runs every minute. Does nothing unless the
#                 new box (which needs this box's admin password to get in)
#                 has dropped a request file into C:\ProgramData\uploader-migration:
#                   PACK-REQUEST.txt    -> stage identity/config/tools into
#                                          .\pack, then write READY.txt
#                   CUTOVER-REQUEST.txt -> -Cutover, which writes INERT.txt
#  -Prepare       Just the SMB rule (no agent).
#  -Cutover       Makes this box inert so the new box can own its identity:
#                 stops Syncthing, AdsPower, Chrome, ClipAngel and WSL,
#                 disables every way Syncthing or the uploader tasks could
#                 start again, writes INERT.txt.
#                 Two machines must NEVER run the same Syncthing identity.
#  -Undo          Rollback of -Cutover. Only before the new box has started
#                 Syncthing.
#  -Uninstall     Removes the agent task and the SMB rule.
# ============================================================================

param([switch]$InstallAgent, [switch]$Agent, [switch]$Prepare, [switch]$Cutover, [switch]$Undo, [switch]$Uninstall)

$ErrorActionPreference = 'Stop'

$RuleName  = 'Uploader migration - SMB from Tailscale only'
$AgentTask = 'UploaderMigrationAgent'
$StateDir  = 'C:\ProgramData\uploader-migration'
$Marker    = Join-Path $StateDir 'INERT.txt'
$RunSave   = Join-Path $StateDir 'run-syncthing.txt'
$Log       = Join-Path $StateDir 'agent.log'
$RawBase   = 'https://raw.githubusercontent.com/JackyYu510yt/jacky-of-all-trades/main/uploader-setup'
$Tasks     = 'Syncthing (boot, no login)', 'JackyRushChecksumGuard', 'JackyRushUploaderReaper', 'JackyRushReapRequests'
$RunKey    = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) { throw 'Run this from an elevated (Run as administrator) PowerShell.' }
if (-not ($InstallAgent -or $Agent -or $Prepare -or $Cutover -or $Undo -or $Uninstall)) { throw 'Pick one: -InstallAgent, -Prepare, -Cutover, -Undo or -Uninstall' }
New-Item -ItemType Directory -Force $StateDir | Out-Null

function Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function LogLine($msg) { Add-Content -LiteralPath $Log -Value "$(Get-Date -Format s) $msg" }

if ($Agent) {
    if (Test-Path "$StateDir\PACK-REQUEST.txt") {
        LogLine 'pack requested'
        Remove-Item "$StateDir\READY.txt" -ErrorAction SilentlyContinue
        & powershell -NoProfile -ExecutionPolicy Bypass -File "$StateDir\pack_uploader_payload.ps1" -StageOnly "$StateDir\pack" 2>&1 |
            ForEach-Object { LogLine "  $_" }
        if ($LASTEXITCODE -eq 0) { Set-Content "$StateDir\READY.txt" (Get-Date -Format s); LogLine 'pack READY' }
        else { LogLine "pack FAILED ($LASTEXITCODE)" }
        Remove-Item "$StateDir\PACK-REQUEST.txt" -ErrorAction SilentlyContinue
    }
    if ((Test-Path "$StateDir\CUTOVER-REQUEST.txt") -and -not (Test-Path $Marker)) {
        LogLine 'cutover requested'
        $Cutover = $true
    }
    if (-not $Cutover) { return }
}

if ($InstallAgent -or $Prepare) {
    Step 'Open SMB to Tailscale only'
    if (-not (Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -DisplayName $RuleName -Direction Inbound -Protocol TCP -LocalPort 445 `
            -RemoteAddress '100.64.0.0/10' -InterfaceAlias 'Tailscale' -Action Allow | Out-Null
    }
    Set-Service LanmanServer -StartupType Automatic
    Start-Service LanmanServer
    Write-Host 'SMB reachable from Tailscale devices only (public adapter stays closed).'
}

if ($InstallAgent) {
    Step 'Install migration agent'
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    foreach ($f in 'migrate-source.ps1', 'pack_uploader_payload.ps1') {
        Invoke-WebRequest "$RawBase/$f" -OutFile (Join-Path $StateDir $f) -UseBasicParsing
    }
    # The staged pack holds the identity keys unencrypted - Administrators + SYSTEM only.
    icacls $StateDir /inheritance:r /grant:r '*S-1-5-32-544:(OI)(CI)F' '*S-1-5-18:(OI)(CI)F' | Out-Null
    $action    = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$StateDir\migrate-source.ps1`" -Agent"
    $trigger   = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 1) -RepetitionDuration (New-TimeSpan -Days 3650)
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Highest
    $set       = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
    Register-ScheduledTask -TaskName $AgentTask -Action $action -Trigger $trigger -Principal $principal -Settings $set -Force `
        -Description 'Answers a new uploader box during migration (see uploader-setup/README.md). Idle unless a request file appears.' | Out-Null
    $ip = (& "C:\Program Files\Tailscale\tailscale.exe" ip -4 | Select-Object -First 1).Trim()
    Write-Host ''
    Write-Host 'Agent installed. Nothing else to run on this box.' -ForegroundColor Green
    Write-Host "Moving day = one command on the new box. It will ask for this box's Windows password ($env:COMPUTERNAME\$env:USERNAME)." -ForegroundColor Green
    Write-Host "This box's Tailscale IP: $ip" -ForegroundColor Green
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
    foreach ($p in 'syncthing', 'AdsPower Global', 'SunBrowser', 'chrome', 'firefox', 'ClipAngel') {
        Get-Process -Name $p -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    }
    try { wsl --shutdown } catch { }
    Start-Sleep 3
    if (Get-Process syncthing -ErrorAction SilentlyContinue) { throw 'Syncthing is still running - stop it by hand, then re-run -Cutover.' }
    Set-Content -LiteralPath $Marker -Value "Inert since $(Get-Date -Format s). Syncthing identity handed to the new uploader."
    Remove-Item "$StateDir\CUTOVER-REQUEST.txt" -ErrorAction SilentlyContinue
    if ($Agent) { LogLine 'INERT' }
    Write-Host ''
    Write-Host 'INERT. This box no longer runs Syncthing or the uploader tasks.' -ForegroundColor Green
    Write-Host 'Do not start Syncthing here again - the new box now owns this identity.' -ForegroundColor Yellow
}

if ($Undo) {
    Step 'Roll back'
    foreach ($t in $Tasks) {
        if (Get-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue) { Enable-ScheduledTask -TaskName $t | Out-Null; Write-Host "enabled task : $t" }
    }
    if (Test-Path $RunSave) { Set-ItemProperty $RunKey -Name Syncthing -Value (Get-Content -LiteralPath $RunSave -Raw).Trim(); Remove-Item $RunSave }
    Remove-Item $Marker, "$StateDir\CUTOVER-REQUEST.txt" -ErrorAction SilentlyContinue
    Start-ScheduledTask -TaskName 'Syncthing (boot, no login)' -ErrorAction SilentlyContinue
    Write-Host 'Rolled back: this box is the uploader again.' -ForegroundColor Green
}

if ($Uninstall) {
    Step 'Remove migration agent'
    Unregister-ScheduledTask -TaskName $AgentTask -Confirm:$false -ErrorAction SilentlyContinue
    Remove-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue
    Write-Host 'Agent and SMB rule removed.' -ForegroundColor Green
}
