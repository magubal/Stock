# Plan: Disclosure Auto-Collect (공시 데이터 자동 수집)

> PDCA Phase: Plan
> Feature: disclosure-auto-collect
> Created: 2026-02-19
> Source: /brain brainstorming session

---

## 1. Overview

공시 모니터 대시보드(`monitor_disclosures.html`)에 수동 데이터 수집 버튼을 추가하고,
매일 18시에 자동으로 당일 KIND 공시를 수집·분석·갱신하는 시스템.

## 2. Problem Statement

- 공시 데이터가 2026-02-14에서 멈춰 있어, 매일 수동으로 Python 스크립트를 실행해야 갱신됨
- 사용자가 CLI 없이 브라우저에서 즉시 데이터를 갱신할 수 없음
- 일일 자동 수집 파이프라인이 없어 운영 부담 존재

## 3. Goals

1. **UI 수집 버튼**: `monitor_disclosures.html` 헤더에 "데이터 수집" 버튼 추가 → 클릭 시 collect + analyze 파이프라인 실행
2. **Backend API**: `POST /api/v1/collector/disclosure` 엔드포인트 (기존 `collector.py` 패턴 복제)
3. **run-all 통합**: `_run_all_collectors()`에 disclosure 수집 포함
4. **일일 자동 수집**: 매일 18:00 자동 실행 (Windows Task Scheduler + 배치 파일)
5. **collector_log 기록**: 수집 결과가 `/api/v1/collector/status`에 표시

## 4. Scope

### In Scope
- `backend/app/api/collector.py` — `_run_disclosure_collector()` + `POST /disclosure` 추가
- `dashboard/monitor_disclosures.html` — 수집 버튼 + 진행 상태 UI
- `scripts/run_daily_collect.bat` — 18시 자동 수집 배치 파일
- collector_log에 "disclosure" 수집 기록

### Out of Scope
- WebSocket 실시간 수집 진행률 (Phase 2)
- 과거 날짜 일괄 수집 (backfill)
- 수집 실패 시 자동 재시도 (retry logic)

## 5. Success Criteria

| Criteria | Target |
|----------|--------|
| UI 버튼 클릭 → 수집 완료 | collect + analyze 파이프라인 정상 실행 |
| 수집 후 대시보드 자동 갱신 | 새 데이터로 UI 리렌더링 |
| collector_log 기록 | status API에서 disclosure 상태 조회 가능 |
| 배치 파일 동작 | `run_daily_collect.bat` 실행 시 API 호출 성공 |
| run-all 통합 | `/api/v1/collector/run-all` 시 disclosure 포함 |

## 6. Implementation Order

1. **Step 1**: `collector.py`에 `_run_disclosure_collector()` 함수 추가
   - `collect_disclosures.py`의 `main()` 로직을 래핑
   - `analyze_disclosures.py`의 분석 로직 호출
   - collector_log에 결과 기록
2. **Step 2**: `POST /api/v1/collector/disclosure` 엔드포인트 추가
3. **Step 3**: `_run_all_collectors()`에 disclosure 수집 포함
4. **Step 4**: `monitor_disclosures.html` 수집 버튼 + 로딩 상태 + 완료 후 데이터 리로드
5. **Step 5**: `scripts/run_daily_collect.bat` 배치 파일 작성
6. **Step 6**: Windows Task Scheduler 등록 가이드

## 7. Dependencies

- 기존 `scripts/collect_disclosures.py` (302 lines) — KIND POST 수집
- 기존 `scripts/analyze_disclosures.py` (722 lines) — 이벤트 분류 + 점수
- 기존 `backend/app/api/collector.py` — 수집 API 패턴 (liquidity/crypto)
- FastAPI backend running on port 8000

## 8. Risk & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| KIND 접속 실패 | High | 기존 sample fallback 로직 + collector_log에 실패 기록 |
| 장중 수집 시 불완전 데이터 | Medium | UI에 "15:30 이후 수집 권장" 안내 + 18시 자동이 주요 수집 |
| Backend 서버 미실행 | Medium | 배치 파일에 서버 상태 체크 + 직접 Python 실행 fallback |
| analyze 스크립트 에러 | Low | collect 성공 시 raw 데이터 보존, analyze만 재실행 가능 |

## 9. Technical Notes

### Collector 패턴 (기존 유동성/크립토와 동일)
```
_run_disclosure_collector()
  ├── collect_disclosures.main() → data/disclosures/YYYY-MM-DD.json
  ├── analyze_disclosures.analyze() → dashboard/data/latest_disclosures.json
  └── _log_collection("disclosure", ...) → collector_log 테이블
```

### UI 버튼 동작 흐름
```
버튼 클릭 → POST /api/v1/collector/disclosure
         → 로딩 스피너 표시
         → 수집 결과 반환 (status, duration, steps)
         → fetch latest_disclosures.json 재로드
         → UI 리렌더링 (새 날짜 표시)
```

### 배치 파일 (run_daily_collect.bat)
```
curl -X POST http://localhost:8000/api/v1/collector/run-all
```
Windows Task Scheduler에 매일 18:00으로 등록.
