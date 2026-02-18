param(
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"

Write-Host "[Global Guard] Running mandatory checklist..." -ForegroundColor Cyan
& $PythonExe "scripts/ci/check_global_change_guard.py"
$code = $LASTEXITCODE

if ($code -ne 0) {
    Write-Host "[Global Guard] FAILED (exit=$code)" -ForegroundColor Red
    exit $code
}

Write-Host "[Global Guard] PASSED" -ForegroundColor Green

