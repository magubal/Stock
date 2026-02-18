param(
    [string]$TaskName = "Stock_Moat_DailySync_1900"
)

$ErrorActionPreference = "Stop"

Write-Host "[INFO] Removing task '$TaskName'"
schtasks /Delete /TN $TaskName /F | Out-Null
Write-Host "[OK] Removed."
