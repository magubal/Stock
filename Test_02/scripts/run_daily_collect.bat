@echo off
REM ============================================================
REM  Stock Research ONE - Daily Data Collection
REM  전체 데이터 수집: 유동성 + 크립토 + 공시
REM  Windows Task Scheduler: 매일 18:00 등록
REM ============================================================

echo [%date% %time%] Starting daily collection...

REM API 서버로 전체 수집 요청
curl -s -X POST http://localhost:8000/api/v1/collector/run-all -o "%~dp0collector_log_daily.txt" 2>&1

IF %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] API call failed. Running scripts directly...
    cd /d "%~dp0.."
    python scripts/collect_disclosures.py
    python scripts/analyze_disclosures.py
    echo [%date% %time%] Direct script execution complete.
) ELSE (
    echo [%date% %time%] API collection complete. See collector_log_daily.txt
)
