## 작업: REQUESTS 인코딩 일관성 복구 (2026-02-19)

### 이슈
- `REQUESTS.md`가 UTF-8/CP949 혼입 및 일부 바이트 손상 상태여서 IDE에서 한글이 깨짐.
- 동일 원인으로 `docs/development_log_2026-02-18.md`도 UTF-8 strict decode 실패.

### 조치
1. 손상 원본 보존
- `docs/archive/REQUESTS_corrupted_2026-02-19.md` 백업.

2. 요청 문서 정리
- `REQUESTS.md`를 UTF-8 기준으로 전체 재작성.
- REQ-001~REQ-019를 읽기 가능한 한글/영문으로 정리.
- 최근 진행사항(REQ-017/018/019) 반영.

3. 로그 파일 복구
- `docs/development_log_2026-02-18.md`의 혼입 구간을 UTF-8로 변환하여 decode 가능 상태로 복구.

### 검증
- `REQUESTS.md` UTF-8 strict decode: PASS
- `docs/development_log_2026-02-18.md` UTF-8 strict decode: PASS
- `docs/development_log_2026-02-02.md` UTF-8 strict decode: PASS
- `docs/development_log_2026-02-14.md` UTF-8 strict decode: PASS
- `docs/development_log_2026-02-15.md` UTF-8 strict decode: PASS

### 후속 권장
- 핵심 문서(AGENTS/REQUESTS/development_log_*.md) UTF-8 검사를 CI 전역 가드에 추가.
## 작업: 깨진 markdown 파일 정리 (2026-02-19)

### 조치
1. `docs/archive/REQUESTS_corrupted_2026-02-19.md`
- 손상 원본을 `docs/archive/REQUESTS_corrupted_2026-02-19.bin`으로 이동.
- 동일 경로 `.md`는 UTF-8 안내 문서로 재작성.

2. `data/runtime/requests_decoded_preview_utf8.md`
- 임시 모지바케 프리뷰 내용을 UTF-8 안내 문서로 교체.

### 검증
- 프로젝트 전체 `*.md` 파일 UTF-8 strict decode 검사 결과: `BAD_COUNT=0`
