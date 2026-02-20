# kill-port-v2-upgrade Plan

> kill_port.py를 PID 검증 + 단계적 종료 + ghost 진단이 가능한 v2로 업그레이드

## 배경

Windows 개발 중 포트 8000 충돌을 `/kill-port`로 정리하려다가:
- netstat에는 LISTENING + PID가 나오는데
- tasklist/taskkill에는 해당 PID가 존재하지 않는 **유령(ghost) 프로세스** 발생
- v1이 무의미한 `taskkill /F /T`를 반복하여 상황 악화 → winsock reset + 재부팅 필요

## v1 문제점

| 문제 | 원인 |
|------|------|
| 유령 PID에 무한 kill 시도 | netstat PID를 무조건 신뢰 |
| 항상 강제 종료 | `/F /T` 만 사용, 정상 종료 기회 박탈 |
| 진단 기능 없음 | ghost/stuck 원인 파악 불가 |

## v2 개선사항

| 개선 | 설명 |
|------|------|
| PID 실존 검증 | `tasklist`로 확인 후 kill, 없으면 GHOST 분류 |
| 2단계 종료 | 1차 `taskkill /T` (부드럽게) → 2차 `/F /T` (강제) |
| Ghost 진단 | `portproxy`, `http servicestate`, `sc query http` 자동 출력 |
| diagnose 모드 | `python scripts/kill_port.py diagnose 8000` |
| V3 오탐 회피 유지 | PowerShell 파이프라인 미사용 |

## 범위

- `Test_02/scripts/kill_port.py` — 내용을 v2로 교체 (파일명 유지)
- `Test_02/.claude/commands/kill-port.md` — 설명 업데이트
- `Test_02/.gemini/commands/kill-port.toml` — 설명 업데이트

## 성공 기준

1. 포트 비어있을 때: "All ports are free." 출력
2. 실제 서버 kill: PID 검증 후 2단계 종료 성공
3. Ghost 상황: GHOST 분류 + 진단 정보 출력
4. 기존 호출 인터페이스 100% 호환

## 구현 산출물

| 파일 | 용도 |
|------|------|
| `scripts/kill_port.py` | v2 포트 정리 유틸리티 (ghost 감지 + 진단) |
| `.claude/commands/kill-port.md` | Claude Code `/kill-port` 커맨드 (v2 설명) |
| `.gemini/commands/kill-port.toml` | Gemini CLI `/kill-port` 커맨드 (v2 설명) |

## 승격 계획

- Test_02에서 검증 완료 후 `Stock/scripts/kill_port.py`에 동일 적용
- `Stock/.claude/commands/kill-port.md` 동일 업데이트
