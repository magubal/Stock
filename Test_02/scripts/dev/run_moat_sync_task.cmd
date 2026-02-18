@echo off
setlocal

set SCRIPT_DIR=%~dp0
for %%I in ("%SCRIPT_DIR%\..\..") do set ROOT=%%~fI

set LOG_DIR=%ROOT%\data\runtime\logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

set PYTHON_EXE=%ROOT%\backend\venv\Scripts\python.exe
set SYNC_SCRIPT=%ROOT%\scripts\moat_dashboard\scheduled_moat_sync.py
set TASK_STDOUT_LOG=%LOG_DIR%\moat_sync_stdout.log

cd /d "%ROOT%"
"%PYTHON_EXE%" "%SYNC_SCRIPT%" --scheduled >> "%TASK_STDOUT_LOG%" 2>&1

endlocal
