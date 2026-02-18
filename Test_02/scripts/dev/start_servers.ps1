param(
    [int]$ApiPort = 8000,
    [int]$DashboardPort = 8080
)

$ErrorActionPreference = "Stop"

function Get-ListeningProcessId {
    param([int]$Port)
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $conn) { return $null }
    return ($conn | Select-Object -ExpandProperty OwningProcess -Unique | Select-Object -First 1)
}

function Start-ServerProcess {
    param(
        [string]$Name,
        [string]$ExePath,
        [string[]]$ProcessArgs,
        [string]$WorkDir,
        [int]$Port,
        [string]$StdOutPath,
        [string]$StdErrPath
    )

    $existingPid = Get-ListeningProcessId -Port $Port
    if ($existingPid) {
        Write-Host "[SKIP] $Name already listening on :$Port (pid=$existingPid)"
        return [PSCustomObject]@{
            name = $Name
            port = $Port
            started = $false
            pid = $null
            existing_pid = $existingPid
            url = "http://localhost:$Port"
        }
    }

    $proc = Start-Process `
        -FilePath $ExePath `
        -ArgumentList $ProcessArgs `
        -WorkingDirectory $WorkDir `
        -RedirectStandardOutput $StdOutPath `
        -RedirectStandardError $StdErrPath `
        -WindowStyle Hidden `
        -PassThru

    Start-Sleep -Seconds 2
    $nowPid = Get-ListeningProcessId -Port $Port
    if (-not $nowPid) {
        Write-Host "[WARN] $Name start command ran, but port :$Port is not listening yet. Check logs."
    } else {
        Write-Host "[OK] $Name started on :$Port (pid=$nowPid)"
    }

    return [PSCustomObject]@{
        name = $Name
        port = $Port
        started = $true
        pid = $(if ($nowPid) { [int]$nowPid } else { [int]$proc.Id })
        existing_pid = $null
        url = "http://localhost:$Port"
    }
}

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$backendDir = Join-Path $root "backend"
$dashboardDir = Join-Path $root "dashboard"
$pythonExe = Join-Path $backendDir "venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw "Python executable not found: $pythonExe"
}
if (-not (Test-Path (Join-Path $backendDir "app\main.py"))) {
    throw "Backend entry not found: $(Join-Path $backendDir 'app\main.py')"
}
if (-not (Test-Path (Join-Path $dashboardDir "index.html"))) {
    throw "Dashboard directory/index not found: $dashboardDir"
}

$runtimeDir = Join-Path $root "data\runtime"
$logsDir = Join-Path $runtimeDir "logs"
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

$statePath = Join-Path $runtimeDir "dev_servers_state.json"
$apiOut = Join-Path $logsDir "api_stdout.log"
$apiErr = Join-Path $logsDir "api_stderr.log"
$dashOut = Join-Path $logsDir "dashboard_stdout.log"
$dashErr = Join-Path $logsDir "dashboard_stderr.log"

$api = Start-ServerProcess `
    -Name "API" `
    -ExePath $pythonExe `
    -ProcessArgs @("-m", "uvicorn", "app.main:app", "--port", "$ApiPort") `
    -WorkDir $backendDir `
    -Port $ApiPort `
    -StdOutPath $apiOut `
    -StdErrPath $apiErr

$dashboard = Start-ServerProcess `
    -Name "Dashboard" `
    -ExePath $pythonExe `
    -ProcessArgs @("-m", "http.server", "$DashboardPort", "--bind", "127.0.0.1") `
    -WorkDir $dashboardDir `
    -Port $DashboardPort `
    -StdOutPath $dashOut `
    -StdErrPath $dashErr

$state = [PSCustomObject]@{
    started_at = (Get-Date).ToString("o")
    root = $root
    api = $api
    dashboard = $dashboard
    logs = [PSCustomObject]@{
        api_stdout = $apiOut
        api_stderr = $apiErr
        dashboard_stdout = $dashOut
        dashboard_stderr = $dashErr
    }
}

$state | ConvertTo-Json -Depth 6 | Set-Content -Path $statePath -Encoding UTF8

Write-Host ""
Write-Host "State file: $statePath"
Write-Host "API URL: http://localhost:$ApiPort"
Write-Host "Dashboard URL: http://localhost:$DashboardPort/index.html"
Write-Host "Moat page: http://localhost:$DashboardPort/moat_analysis.html"
