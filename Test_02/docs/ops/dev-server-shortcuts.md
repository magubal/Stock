# Dev Server Shortcuts (Windows PowerShell)

## Start
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/start_servers.ps1
```

기본 포트:
- API: `8000`
- Dashboard: `8080`

옵션 포트 지정:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/start_servers.ps1 -ApiPort 8001 -DashboardPort 8081
```

## Stop
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/stop_servers.ps1
```

기본 동작:
- `start_servers.ps1`가 직접 띄운 프로세스만 종료
- 기존에 떠 있던 프로세스는 안전하게 유지

강제 포트 종료(선택):
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/stop_servers.ps1 -KillByPort -ApiPort 8000 -DashboardPort 8080
```

## Runtime Files
- state: `data/runtime/dev_servers_state.json`
- logs:
  - `data/runtime/logs/api_stdout.log`
  - `data/runtime/logs/api_stderr.log`
  - `data/runtime/logs/dashboard_stdout.log`
  - `data/runtime/logs/dashboard_stderr.log`
