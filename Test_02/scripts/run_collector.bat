@echo off
setlocal

:: Set encoding to UTF-8
chcp 65001 >nul

:: Set working directory
cd /d "%~dp0.."

:: Get current date and time for log
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set "timestamp=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2% %datetime:~8,2%:%datetime:~10,2%:%datetime:~12,2%"

echo. >> scripts\collector_log.txt
echo ================================================== >> scripts\collector_log.txt
echo [Start] %timestamp% >> scripts\collector_log.txt
echo ================================================== >> scripts\collector_log.txt

:: Run Python script
python scripts\naver_blog_collector.py >> scripts\collector_log.txt 2>&1

:: Check exit code
if %ERRORLEVEL% EQU 0 (
    echo [Success] Execution completed successfully. >> scripts\collector_log.txt
) else (
    echo [Error] Execution failed with code %ERRORLEVEL%. >> scripts\collector_log.txt
)

echo [End] %timestamp% >> scripts\collector_log.txt
echo. >> scripts\collector_log.txt

endlocal
