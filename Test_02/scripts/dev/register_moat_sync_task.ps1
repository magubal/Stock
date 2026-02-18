param(
    [string]$TaskName = "Stock_Moat_DailySync_1900",
    [string]$RunTime = "19:00"
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$runnerCmd = Join-Path $root "scripts\dev\run_moat_sync_task.cmd"

if (-not (Test-Path $runnerCmd)) {
    throw "Task runner cmd not found: $runnerCmd"
}

$logDir = Join-Path $root "data\runtime\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$taskLog = Join-Path $logDir "moat_sync_stdout.log"

$taskCommand = "`"$runnerCmd`""

Write-Host "[INFO] Registering task '$TaskName' at $RunTime"
schtasks /Create /F /SC DAILY /ST $RunTime /TN $TaskName /TR $taskCommand | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "schtasks create failed (exit=$LASTEXITCODE)"
}

Write-Host "[OK] Registered."
Write-Host "  Task Name : $TaskName"
Write-Host "  Time      : $RunTime (daily)"
Write-Host "  Command   : $taskCommand"
Write-Host "  Stdout Log: $taskLog"
Write-Host "  State Log : $(Join-Path $logDir 'moat_sync_task.log')"

Write-Host ""
Write-Host "[INFO] Task summary:"
schtasks /Query /TN $TaskName /FO LIST /V | Select-String "TaskName|Next Run Time|Last Run Time|Status|Task To Run" | ForEach-Object { $_.Line }
