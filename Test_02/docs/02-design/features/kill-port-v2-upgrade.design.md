# kill-port-v2-upgrade Design

> Plan 문서: [kill-port-v2-upgrade.plan.md](../../01-plan/features/kill-port-v2-upgrade.plan.md)

## 아키텍처

```
사용자 (/kill-port 8000)
  │
  ▼
kill_port.py main()
  │
  ├─ parse_ports() ─── diagnose flag + 포트 리스트 파싱
  │
  ▼
cleanup_port(port, diagnose)
  │
  ├─ parse_netstat_listeners(port) ── netstat -ano 파싱 → Listener[]
  │
  ├─ for each unique PID:
  │   ├─ pid_exists(pid) ── tasklist 검증
  │   │   ├─ False → ghost[] (kill 시도 안 함)
  │   │   └─ True  → get_process_name(pid)
  │   │              ├─ try_kill_pid(pid, force=False)  ── 1차 부드러운 종료
  │   │              └─ try_kill_pid(pid, force=True)   ── 2차 강제 종료
  │   └─ sleep(0.2) ── 포트 해제 대기
  │
  ├─ parse_netstat_listeners(port) ── 재확인
  │
  ├─ status 분류: free | cleaned | partial | ghost | stuck
  │
  └─ (ghost/stuck 시) diagnose_http_and_portproxy(port)
      ├─ netsh interface portproxy show all
      ├─ cmd /c netsh http show servicestate | findstr
      └─ sc query http
```

## 데이터 모델

### Listener (dataclass)
| 필드 | 타입 | 설명 |
|------|------|------|
| proto | str | 프로토콜 (TCP) |
| local_addr | str | 바인딩 주소 (0.0.0.0, 127.0.0.1, [::]) |
| local_port | int | 포트 번호 |
| pid | int | 프로세스 ID |

### cleanup_port 반환값 (Dict)
| 필드 | 타입 | 설명 |
|------|------|------|
| port | int | 대상 포트 |
| status | str | free / cleaned / partial / ghost / stuck |
| killed | list | 성공적으로 종료된 PID 목록 |
| failed | list | 종료 실패한 PID 목록 |
| ghost | list | tasklist에 없는 유령 PID 목록 |
| still_listening | bool | 정리 후에도 LISTENING 남아있는지 |
| remaining_pids | list | 잔존 PID 목록 |
| diagnostics | dict | (ghost/stuck 시) 진단 결과 |

## Status 분류 로직

```
if 리스너 없음 → "free"
if 모두 kill 성공 + 포트 해제 → "cleaned"
if kill 일부 실패 → "partial"
if ghost만 있고 포트 남음 → "ghost"
if ghost + failed + 포트 남음 → "stuck"
```

## 인터페이스 (v1 호환)

| 호출 | v1 | v2 |
|------|----|----|
| `kill_port.py` | 8000 kill | 8000 kill (동일) |
| `kill_port.py 8000 3000` | 지정 포트 kill | 동일 |
| `kill_port.py all` | 8000+8080+3000 | 동일 |
| `kill_port.py diagnose 8000` | ❌ 없음 | ✅ 진단 모드 (추가) |

## 수정 파일

| 파일 | 변경 내용 |
|------|----------|
| `scripts/kill_port.py` | v1 → v2 내용 교체 |
| `.claude/commands/kill-port.md` | v2 동작 원리 + diagnose 설명 추가 |
| `.gemini/commands/kill-port.toml` | 동일 내용 TOML 포맷 |

## 보안/안전

- PowerShell 파이프라인 미사용 → AhnLab V3 오탐 회피
- `cmd /c ... | findstr` 는 cmd.exe 내부 파이프라인 → V3 안전
- PID 검증 후 kill → 존재하지 않는 프로세스 kill 방지
- 부드러운 종료 우선 → 프로세스 정리 루틴 실행 기회 보장
