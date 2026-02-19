포트를 점유하고 있는 좀비 프로세스를 정리합니다. 인자: $ARGUMENTS

## 실행 방법

1. 인자가 없으면 기본 8000만 정리 (uvicorn 좀비가 주 원인)
2. `all` 이면 전체 포트 정리 (8000, 8080, 3000)
3. 숫자 인자면 해당 포트만 정리 (예: `/kill-port 8000 3000`)

아래 명령을 실행하세요:

```bash
python scripts/kill_port.py $ARGUMENTS
```

## 동작 원리
- `netstat -ano` 로 LISTENING 상태의 PID를 탐지
- `taskkill /PID <pid> /F /T` 로 프로세스 트리 전체 종료
- PowerShell 파이프라인 미사용 (AhnLab V3 오탐 회피)
- 아무것도 없으면 "All ports are free" 출력 (에러 없음)

## 사용 시나리오
- 서버 시작 시 "port already in use" 에러 발생
- VS Code Run/Debug 전에 이전 세션 잔여 프로세스 정리
- uvicorn --reload 후 좀비 워커 프로세스 잔존
