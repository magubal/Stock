param(
    [switch]$KillByPort,
    [int]$ApiPort = 8000,
    [int]$DashboardPort = 8080
)

$ErrorActionPreference = "Stop"

function Stop-IfRunning {
    param([int]$ProcessId, [string]$Name)
    if (-not $ProcessId) { return }
    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($proc) {
        try {
            Stop-Process -Id $ProcessId -Force -ErrorAction Stop
            Write-Host "[OK] Stopped $Name pid=$ProcessId"
        } catch {
            Write-Host "[WARN] Failed to stop $Name pid=$ProcessId : $($_.Exception.Message)"
        }
    } else {
        Write-Host "[SKIP] $Name pid=$ProcessId already exited"
    }
}

function Stop-ByPort {
    param([int]$Port, [string]$Name)
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $conn) {
        Write-Host "[SKIP] $Name port :$Port not listening"
        return
    }
    $owningPid = ($conn | Select-Object -ExpandProperty OwningProcess -Unique | Select-Object -First 1)
    if ($owningPid) {
        Stop-IfRunning -ProcessId $owningPid -Name "$Name(port:$Port)"
    }
}

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$statePath = Join-Path $root "data\runtime\dev_servers_state.json"

if (Test-Path $statePath) {
    $state = Get-Content -Raw -Path $statePath | ConvertFrom-Json

    if ($state.api.started -eq $true) {
        Stop-IfRunning -ProcessId ([int]$state.api.pid) -Name "API"
        Stop-ByPort -Port ([int]$state.api.port) -Name "API"
    } else {
        Write-Host "[SKIP] API was not started by script (state indicates pre-existing listener)"
    }

    if ($state.dashboard.started -eq $true) {
        Stop-IfRunning -ProcessId ([int]$state.dashboard.pid) -Name "Dashboard"
        Stop-ByPort -Port ([int]$state.dashboard.port) -Name "Dashboard"
    } else {
        Write-Host "[SKIP] Dashboard was not started by script (state indicates pre-existing listener)"
    }

    Remove-Item -Path $statePath -Force
    Write-Host "Removed state file: $statePath"
} else {
    Write-Host "[INFO] No state file found: $statePath"
}

if ($KillByPort) {
    Write-Host "[INFO] KillByPort enabled"
    Stop-ByPort -Port $ApiPort -Name "API"
    Stop-ByPort -Port $DashboardPort -Name "Dashboard"
}
