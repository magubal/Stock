# zombie-process-cleanup Plan

> Windows 개발 환경에서 포트를 점유하는 좀비 프로세스를 자동 정리하는 유틸리티

## 배경
- uvicorn --reload 사용 시 부모 프로세스만 종료되고 자식(워커)이 포트를 계속 점유
- VS Code Run/Debug 종료 후에도 이전 세션 프로세스가 잔존
- PowerShell 파이프라인 사용 시 AhnLab V3 오탐 (MDP.Powershell.M2514)

## 범위
- Python 기반 포트 정리 스크립트 (`scripts/kill_port.py`)
- Claude Code 커스텀 커맨드 (`/kill-port`)
- VS Code Tasks 연동 (`.vscode/tasks.json`)
- FastAPI graceful shutdown (engine.dispose)

## 성공 기준
- `python scripts/kill_port.py` 실행 시 8000 포트 좀비 프로세스 자동 정리
- `/kill-port` 커맨드로 Claude Code에서 즉시 실행 가능
- AhnLab V3 오탐 없음 (PowerShell 미사용)

## 구현 산출물
| 파일 | 용도 |
|------|------|
| `scripts/kill_port.py` | netstat + taskkill 기반 포트 정리 유틸리티 |
| `.claude/commands/kill-port.md` | Claude Code `/kill-port` 커맨드 |
| `.vscode/tasks.json` | VS Code 포트 정리 태스크 |
| `backend/app/main.py` | engine.dispose() graceful shutdown 추가 |

## 완료 상태
- 2026-02-19 구현 완료 (brainstorming → 직접 구현)
- 기본 포트: 8000만 정리 (uvicorn 좀비가 주 원인)
- `all` 인자: 8000 + 8080 + 3000 전체 정리
