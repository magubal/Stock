@echo off
REM Daily Data Collector - 유동성 + 크립토 수집
REM Called by Windows Task Scheduler at 06:00 KST
set LOGFILE=%~dp0..\..\data\runtime\logs\collector_stdout.log
echo [%date% %time%] Starting daily collector >> "%LOGFILE%"
curl -s -X POST http://localhost:8000/api/v1/collector/run-all >> "%LOGFILE%" 2>&1
echo. >> "%LOGFILE%"
echo [%date% %time%] Done >> "%LOGFILE%"
