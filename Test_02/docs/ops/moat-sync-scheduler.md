# Moat Sync Scheduler (Daily 19:00)

## 목적
- 기준 소스: `data/국내상장종목 해자 투자가치.xlsx`
- 매일 19:00에 파일 변경 여부를 확인하고, 변경된 경우에만 DB/JSON을 갱신합니다.

## 구성
- 실행 스크립트: `scripts/moat_dashboard/scheduled_moat_sync.py`
- 작업 등록: `scripts/dev/register_moat_sync_task.ps1`
- 작업 해제: `scripts/dev/unregister_moat_sync_task.ps1`
- 상태 파일: `data/runtime/moat_sync_state.json`
- 로그 파일:
  - `data/runtime/logs/moat_sync_task.log` (스크립트 상태 로그)
  - `data/runtime/logs/moat_sync_stdout.log` (작업 스케줄러 stdout/stderr)

## 작업 등록 (Windows PowerShell)
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/register_moat_sync_task.ps1
```

기본값:
- 작업명: `Stock_Moat_DailySync_1900`
- 실행시각: 매일 `19:00`

## 수동 실행
```powershell
backend/venv/Scripts/python.exe scripts/moat_dashboard/scheduled_moat_sync.py
```

강제 실행(변경 없어도 동기화):
```powershell
backend/venv/Scripts/python.exe scripts/moat_dashboard/scheduled_moat_sync.py --force
```

## 작업 해제
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/unregister_moat_sync_task.ps1
```
