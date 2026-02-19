param(
    [string]$CollectorTaskName = "Stock_DataCollect_0600",
    [string]$NewsTaskName = "Stock_NewsFetch_0630"
)

Write-Host "[INFO] Removing '$CollectorTaskName'..."
schtasks /Delete /F /TN $CollectorTaskName 2>$null
Write-Host "[INFO] Removing '$NewsTaskName'..."
schtasks /Delete /F /TN $NewsTaskName 2>$null
Write-Host "[OK] Tasks removed."
