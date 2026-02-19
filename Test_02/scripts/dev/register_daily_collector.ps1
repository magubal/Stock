param(
    [string]$CollectorTaskName = "Stock_DataCollect_0600",
    [string]$CollectorTime = "06:00",
    [string]$NewsTaskName = "Stock_NewsFetch_0630",
    [string]$NewsTime = "06:30"
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$collectorCmd = Join-Path $root "scripts\dev\run_daily_collector.cmd"
$newsCmd = Join-Path $root "scripts\dev\run_news_fetch.cmd"

if (-not (Test-Path $collectorCmd)) {
    throw "Collector runner not found: $collectorCmd"
}
if (-not (Test-Path $newsCmd)) {
    throw "News fetch runner not found: $newsCmd"
}

$logDir = Join-Path $root "data\runtime\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

# Register collector task (06:00 KST)
Write-Host "[INFO] Registering '$CollectorTaskName' at $CollectorTime"
schtasks /Create /F /SC DAILY /ST $CollectorTime /TN $CollectorTaskName /TR "`"$collectorCmd`"" | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "schtasks create failed for collector (exit=$LASTEXITCODE)"
}
Write-Host "[OK] Collector task registered."

# Register news fetch task (06:30 KST)
Write-Host "[INFO] Registering '$NewsTaskName' at $NewsTime"
schtasks /Create /F /SC DAILY /ST $NewsTime /TN $NewsTaskName /TR "`"$newsCmd`"" | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "schtasks create failed for news (exit=$LASTEXITCODE)"
}
Write-Host "[OK] News fetch task registered."

Write-Host ""
Write-Host "Summary:"
Write-Host "  1) $CollectorTaskName at $CollectorTime -> liquidity + crypto"
Write-Host "  2) $NewsTaskName at $NewsTime -> global news"
Write-Host "  Log dir: $logDir"

Write-Host ""
Write-Host "Registered tasks:"
schtasks /Query /TN $CollectorTaskName /FO LIST /V 2>$null | Select-String "TaskName|Next Run Time|Status" | ForEach-Object { $_.Line }
schtasks /Query /TN $NewsTaskName /FO LIST /V 2>$null | Select-String "TaskName|Next Run Time|Status" | ForEach-Object { $_.Line }
