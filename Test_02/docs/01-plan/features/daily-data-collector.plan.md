# daily-data-collector Planning Document

> **Summary**: 유동성 스트레스 + 크립토 동향 데이터 매일 자동 수집, 뉴스 전 스케줄링, 수동 트리거 버튼
>
> **Project**: Stock Research ONE
> **Author**: Claude + User
> **Date**: 2026-02-19
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

유동성 스트레스 모니터와 크립토 동향 모니터의 데이터 수집을 자동화하여, 매일 설정된 시간에 데이터가 갱신되고 대시보드에서 수동으로도 즉시 수집할 수 있도록 한다.

### 1.2 Background

현재 상태:
- **유동성 스트레스**: `scripts/liquidity_monitor/run_eod.py` 수동 실행 필요 (FRED, Yahoo, News, Fed Speech → StressIndex 계산)
- **크립토 동향**: `dashboard/crypto_trends.html`에서 브라우저가 CoinGecko/DefiLlama/Fear&Greed API 직접 호출 (히스토리 미축적)
- **뉴스 수집**: `POST /api/v1/news-intel/fetch` API + 대시보드 버튼 존재, 수동 실행
- **기존 스케줄러**: Windows Task Scheduler로 moat_sync 등록 전례 있음

문제:
1. 수동 실행을 잊으면 데이터 공백 발생
2. 크립토 데이터는 히스토리가 쌓이지 않음 (브라우저 직접 호출)
3. 수집 순서 보장 없음 (유동성/크립토가 뉴스보다 먼저 완료되어야 분석 정확)

### 1.3 Related Documents

- Brainstorm: `/brain` 세션 (2026-02-19)
- 유동성 모니터 설계: `docs/archive/2026-02/liquidity-stress-monitor/`
- 크립토 모니터: `dashboard/crypto_trends.html`
- 기존 스케줄러 참고: `scripts/dev/register_moat_sync_task.ps1`

---

## 2. Scope

### 2.1 In Scope

- [ ] 크립토 데이터 백엔드 수집 스크립트 신규 생성 (`scripts/crypto_monitor/`)
- [ ] 크립토 DB 모델 추가 (CryptoPrice, CryptoMetric)
- [ ] 백엔드 수집 트리거 API (`POST /api/v1/collector/liquidity`, `/crypto`, `/run-all`)
- [ ] 대시보드 수동 수집 버튼 (유동성 모니터, 크립토 모니터, 메인 대시보드)
- [ ] Windows Task Scheduler 등록 스크립트 (`register_daily_collector.ps1`)
- [ ] 수집 실행 순서: 유동성 → 크립토 → 뉴스 (순차 보장)
- [ ] 수집 상태/이력 표시 (마지막 수집 시간, 성공/실패)
- [ ] `crypto_trends.html` DB 데이터 연동 전환

### 2.2 Out of Scope

- Celery/Redis 기반 분산 태스크 큐 (현재 Docker 미사용)
- 크립토 거래소별 실시간 가격 스트리밍
- 뉴스 수집 자동 스케줄 (기존 수동 방식 유지, 별도 feature로)
- 알림/노티피케이션 (Slack, Email 등)

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | 크립토 수집 스크립트: CoinGecko top 20 coins 가격/시총/24h변동 | High | Pending |
| FR-02 | 크립토 수집 스크립트: DefiLlama 총 TVL + 주요 프로토콜 TVL | High | Pending |
| FR-03 | 크립토 수집 스크립트: Fear & Greed Index | High | Pending |
| FR-04 | 크립토 DB 모델: CryptoPrice (coin, date, price, market_cap, change_24h, volume) | High | Pending |
| FR-05 | 크립토 DB 모델: CryptoMetric (date, total_tvl, fear_greed_index, btc_dominance) | High | Pending |
| FR-06 | API: `POST /api/v1/collector/liquidity` — 유동성 데이터 수집 트리거 | High | Pending |
| FR-07 | API: `POST /api/v1/collector/crypto` — 크립토 데이터 수집 트리거 | High | Pending |
| FR-08 | API: `POST /api/v1/collector/run-all` — 순차 수집 (유동성→크립토→뉴스) | Medium | Pending |
| FR-09 | API: `GET /api/v1/collector/status` — 최근 수집 상태/이력 조회 | Medium | Pending |
| FR-10 | 대시보드 수동 수집 버튼: 유동성 모니터 페이지 | High | Pending |
| FR-11 | 대시보드 수동 수집 버튼: 크립토 모니터 페이지 | High | Pending |
| FR-12 | 대시보드: "마지막 수집 시간" 표시 | Medium | Pending |
| FR-13 | Windows Task Scheduler 등록/해제 스크립트 | High | Pending |
| FR-14 | 스케줄: 유동성+크립토 06:00 KST → 뉴스 06:30 KST | High | Pending |
| FR-15 | `crypto_trends.html` DB 연동 전환 (브라우저 직접 API → 백엔드 DB) | Medium | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| 안정성 | 개별 수집기 실패 시 나머지 계속 실행 | try/except 격리, 로그 확인 |
| Rate Limit | CoinGecko 무료 API 50회/분 준수 | 요청 간 2초 sleep |
| 수집 시간 | 전체 수집 5분 이내 완료 | 로그 타임스탬프 |
| 데이터 무결성 | 중복 INSERT 방지 (date + coin/metric PK) | SQLite UPSERT |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] 크립토 수집 스크립트 동작 확인 (CoinGecko + DefiLlama + Fear&Greed)
- [ ] 유동성/크립토 수집 API 엔드포인트 동작 확인
- [ ] 대시보드 수동 수집 버튼 클릭 → 데이터 갱신 확인
- [ ] Windows Task Scheduler 태스크 등록 → 스케줄 실행 확인
- [ ] `crypto_trends.html` DB 데이터로 렌더링 확인
- [ ] 수집 순서 보장: 유동성 → 크립토 완료 후 뉴스 시작

### 4.2 Quality Criteria

- [ ] 개별 수집기 실패 시 전체 파이프라인 중단 없음
- [ ] DEMO 데이터 컨벤션 준수 (source="DEMO" 마킹)
- [ ] 수집 로그에 시작/완료/에러 기록

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| CoinGecko API rate limit (50/min) | Medium | Medium | 요청 간 2초 sleep, 실패 시 재시도 1회 |
| Yahoo Finance 429 (유동성 가격) | Medium | High | DB 캐시 fallback 이미 구현됨 |
| 서버 미기동 시 스케줄 실패 | High | Low | start_servers.ps1 자동 기동, 태스크에 서버 헬스체크 포함 |
| FRED API key 미설정 | Low | Medium | credit/funding/treasury 모듈 SKIP 허용 (기존 동작) |
| 수집 중 HTTP 타임아웃 | Medium | Low | background thread 비동기 실행, 개별 타임아웃 30초 |

---

## 6. Architecture Considerations

### 6.1 Project Level

Enterprise — 기존 프로젝트와 동일

### 6.2 Key Architectural Decisions

| Decision | Options | Selected | Rationale |
|----------|---------|----------|-----------|
| 수집 트리거 | API endpoint / CLI only | API endpoint | 대시보드 버튼과 스케줄러가 동일 코드 경로 사용 |
| 스케줄러 | Windows Task Scheduler / Python schedule / Celery | Windows Task Scheduler | 이미 moat_sync에서 사용, OS 레벨 안정성 |
| 크립토 DB | 기존 테이블 확장 / 신규 테이블 | 신규 테이블 2개 | 관심사 분리, 독립적 관리 |
| 비동기 실행 | asyncio.to_thread / background task | asyncio.to_thread | 기존 패턴 유지 (news_analysis.py와 동일) |
| 스케줄 호출 | curl POST / Python script | curl POST | 서버 로그 통합, 단순 |

### 6.3 파일 구조 (예상)

```
scripts/
├── crypto_monitor/
│   ├── __init__.py
│   ├── config.py              # API URLs, rate limit 설정
│   ├── coingecko_fetch.py     # Top coins 가격/시총
│   ├── defi_fetch.py          # DefiLlama TVL
│   ├── fear_greed_fetch.py    # Fear & Greed Index
│   └── run_crypto.py          # 통합 배치 러너
├── liquidity_monitor/
│   └── run_eod.py             # 기존 (변경 없음)
└── dev/
    ├── register_daily_collector.ps1    # 스케줄 등록
    └── unregister_daily_collector.ps1  # 스케줄 해제

backend/app/
├── api/
│   └── collector.py           # POST /collector/liquidity, /crypto, /run-all, GET /status
├── models/
│   └── crypto.py              # CryptoPrice, CryptoMetric
└── main.py                    # collector 라우터 등록

dashboard/
├── crypto_trends.html         # DB 연동 전환
└── liquidity_stress.html      # 수동 수집 버튼 추가
```

---

## 7. Convention Prerequisites

### 7.1 기존 프로젝트 컨벤션 준수

- [x] CLAUDE.md 코딩 컨벤션
- [x] DEMO Data Convention (source="DEMO")
- [x] 수집기 실패 격리 패턴 (try/except + [SKIP] 로그)
- [x] asyncio.to_thread 비동기 패턴

### 7.2 환경 변수

| Variable | Purpose | Scope | Status |
|----------|---------|-------|--------|
| `FRED_API_KEY` | FRED 매크로 지표 | Server | 선택 (미설정 시 SKIP) |
| `COINGECKO_API_KEY` | CoinGecko Pro (선택) | Server | 선택 (무료 API 기본) |

---

## 8. Next Steps

1. [ ] Design 문서 작성 (`daily-data-collector.design.md`)
2. [ ] 구현 (Do phase)
3. [ ] Gap Analysis (Check phase)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-19 | Initial draft from /brain session | Claude + User |
