@echo off
REM News Fetch - 글로벌 뉴스 수집
REM Called by Windows Task Scheduler at 06:30 KST (after collector)
set LOGFILE=%~dp0..\..\data\runtime\logs\news_fetch_stdout.log
echo [%date% %time%] Starting news fetch >> "%LOGFILE%"
curl -s -X POST http://localhost:8000/api/v1/news-intel/fetch >> "%LOGFILE%" 2>&1
echo. >> "%LOGFILE%"
echo [%date% %time%] Done >> "%LOGFILE%"
