# News Intelligence Monitor Planning Document

> **Summary**: Finviz 뉴스 파싱 + AI 기반 핵심이슈/내러티브/섹터 영향도 분석 모니터
>
> **Project**: Stock Research ONE
> **Author**: Claude
> **Date**: 2026-02-19
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

글로벌 뉴스를 자동 수집하고, AI(Claude API)로 당일 핵심이슈/시장 내러티브/섹터별 영향도를 분석하여 투자 심리 관점의 뉴스 인텔리전스를 제공한다. 단순 뉴스 피드가 아닌 "뉴스 → 투자 심리 → 시장 영향" 연결고리를 자동화하는 것이 핵심 가치.

### 1.2 Background

- 현재 시장 모니터링 섹션에 공시/유동성/크립토/해자/Intelligence Board가 있지만, **글로벌 뉴스 기반 시장 심리 분석** 부재
- 투자 의사결정에서 당일 뉴스 흐름과 시장 내러티브 파악은 핵심 입력값
- Finviz는 5개 카테고리(Market, Market Pulse, Stock, ETF, Crypto) 뉴스를 무료로 제공
- 확장 가능한 설계로 향후 Yahoo Finance, Reuters 등 추가 소스 대응

### 1.3 Related Documents

- Brain 결과: B안 (뉴스 인텔리전스 2-Layer) 채택
- 기존 패턴 참고: `dashboard/liquidity_stress.html`, `dashboard/crypto_trends.html`

---

## 2. Scope

### 2.1 In Scope

- [ ] Finviz 뉴스 HTML 파싱 (5개 카테고리: market, market_pulse, stock, etf, crypto)
- [ ] 뉴스 저장용 DB 테이블 (multi-source 확장 가능)
- [ ] AI 분석 결과 저장용 DB 테이블 (핵심이슈, 내러티브, 섹터 영향도)
- [ ] 4시간 배치 수집 스크립트
- [ ] Claude Sonnet API 기반 당일 뉴스 분석 자동화
- [ ] FastAPI 라우터 (뉴스 조회 + 내러티브 조회)
- [ ] 대시보드 페이지 (`dashboard/news_intelligence.html`)
- [ ] 메인 대시보드 시장모니터링 섹션 링크 추가

### 2.2 Out of Scope

- Yahoo Finance / Reuters 등 추가 소스 구현 (테이블은 대응, 파서는 미구현)
- 실시간 WebSocket 피드
- 센티먼트 시계열 차트 (Phase 2 후보)
- 섹터 히트맵 시각화 (Phase 2 후보)
- 알림/푸시 시스템
- `scripts/sync_requests_to_dashboard.py` 변경 금지

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | Finviz 5개 카테고리 뉴스 HTML 파싱 (title, url, source, time, category) | High | Pending |
| FR-02 | `news_articles` 테이블에 source 필드로 multi-source 확장 가능하게 저장 | High | Pending |
| FR-03 | (source, url) 유니크 인덱스로 중복 방지 | High | Pending |
| FR-04 | 4시간 배치 수집 스크립트 (CLI 수동 실행도 가능) | High | Pending |
| FR-05 | Claude Sonnet API로 당일 뉴스 분석: 핵심이슈 3개, 시장 내러티브, 섹터별 영향도 | High | Pending |
| FR-06 | `market_narratives` 테이블에 분석 결과 저장 (날짜별 유니크) | High | Pending |
| FR-07 | FastAPI GET /api/v1/news-intel/articles?category=&date=&limit= | High | Pending |
| FR-08 | FastAPI GET /api/v1/news-intel/narrative?date= | High | Pending |
| FR-09 | 대시보드 페이지: 카테고리 필터 탭 + 뉴스 리스트 (시간순) | High | Pending |
| FR-10 | 대시보드 페이지: AI 브리핑 패널 (핵심이슈 + 내러티브 + 센티먼트) | High | Pending |
| FR-11 | 대시보드 페이지: 섹터별 영향도 매트릭스 (bullish/bearish/neutral) | Medium | Pending |
| FR-12 | 메인 대시보드 시장모니터링 섹션에 "글로벌 뉴스" 링크 추가 | Medium | Pending |
| FR-13 | DEMO 데이터 규칙 준수 (seed data는 source="DEMO" 마킹) | Medium | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| 성능 | 뉴스 파싱 1회 < 30초 (네트워크 제외) | CLI 실행 시간 측정 |
| 확장성 | 새 뉴스소스 추가 시 파서만 작성 (테이블 변경 없음) | 코드 리뷰 |
| 비용 | Claude API 호출 하루 6회 이하 (~$3/월) | API 사용량 모니터링 |
| 안정성 | Finviz 차단 시 graceful degradation (캐시 데이터 표시) | 에러 핸들링 확인 |
| 보안 | API key 환경변수 관리 (ANTHROPIC_API_KEY 기존 사용) | .env 확인 |

---

## 4. Data Model

### 4.1 news_articles 테이블 (신규)

기존 `news` 테이블과 별도 생성 (기존 테이블은 source_id FK 기반, 호환성 유지).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, auto | |
| source | String(50) | NOT NULL, INDEX | 소스 식별자 (finviz, yahoo, reuters...) |
| category | String(50) | NOT NULL, INDEX | 카테고리 (market, market_pulse, stock, etf, crypto) |
| title | String(500) | NOT NULL | 뉴스 제목 |
| url | String(500) | NOT NULL | 원문 링크 |
| publisher | String(100) | | 원 매체명 (Bloomberg, CNBC...) |
| published_at | DateTime | INDEX | 기사 발행 시각 |
| fetched_at | DateTime | server_default=now() | 수집 시각 |
| summary | Text | | AI 생성 요약 (선택) |

**유니크 제약**: `(source, url)` composite unique index

### 4.2 market_narratives 테이블 (신규)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, auto | |
| date | String(10) | UNIQUE, INDEX | 분석 대상 날짜 (YYYY-MM-DD) |
| key_issues | JSON | | 핵심이슈 배열 [{title, summary, impact, category}] |
| narrative | Text | | 시장 내러티브 요약 (2~3문단) |
| sector_impact | JSON | | 섹터별 영향도 [{sector, direction, confidence, reason}] |
| sentiment_score | Float | | 종합 센티먼트 (-1.0 ~ 1.0) |
| sentiment_label | String(20) | | fear/cautious/neutral/optimistic/greed |
| article_count | Integer | | 분석에 사용된 기사 수 |
| generated_by | String(50) | | 생성 모델 (claude-sonnet, manual) |
| created_at | DateTime | server_default=now() | |
| updated_at | DateTime | onupdate=now() | |

---

## 5. Architecture

### 5.1 Data Flow

```
Finviz HTML ──→ finviz_fetch.py ──→ news_articles (DB)
                                          │
                                          ▼
                              narrative_analyzer.py (Claude API)
                                          │
                                          ▼
                              market_narratives (DB)
                                          │
                                          ▼
                              FastAPI Router ──→ Dashboard Page
```

### 5.2 File Structure

```
scripts/news_monitor/
├── __init__.py
├── config.py              # 소스별 설정 (URL, 카테고리, rate limit)
├── finviz_fetch.py        # Finviz HTML 파서
├── narrative_analyzer.py  # Claude API 분석기
└── run_news.py            # 배치 실행 (파싱 → 저장 → 분석)

backend/app/
├── models/
│   └── news_article.py    # NewsArticle, MarketNarrative 모델
├── api/
│   └── news_intelligence.py  # GET articles, GET narrative
└── services/
    └── news_intelligence_service.py  # 비즈니스 로직

dashboard/
└── news_intelligence.html  # 뉴스 인텔리전스 페이지
```

### 5.3 Key Architectural Decisions

| Decision | Selected | Rationale |
|----------|----------|-----------|
| 기존 News 테이블 재사용 vs 신규 | 신규 news_articles | 기존 테이블은 source_id FK + content(본문) 기반, 구조 상이 |
| 파싱 라이브러리 | BeautifulSoup + requests | 기존 프로젝트에서 사용 중, Playwright 불필요 |
| AI 분석 타이밍 | 수집 직후 동기 실행 | 별도 스케줄러 불필요, run_news.py에서 순차 실행 |
| 대시보드 프레임워크 | 정적 HTML (vanilla JS) | 기존 모니터 페이지 패턴 일관성 |

---

## 6. Success Criteria

### 6.1 Definition of Done

- [ ] Finviz 5개 카테고리 뉴스가 DB에 저장됨 (최소 50건 이상)
- [ ] Claude API로 당일 핵심이슈 3개 + 내러티브 + 섹터 영향도 자동 생성됨
- [ ] API 엔드포인트 2개 정상 응답 (articles, narrative)
- [ ] 대시보드 페이지에서 카테고리 필터 + AI 브리핑 + 영향도 표시됨
- [ ] 메인 대시보드에서 링크 클릭으로 페이지 접근 가능
- [ ] DEMO 데이터 규칙 준수

### 6.2 Verification Criteria (Gap Analysis용)

| ID | 검증 항목 | 확인 방법 |
|----|-----------|-----------|
| V-01 | news_articles 테이블 존재 + (source,url) 유니크 | DB 스키마 확인 |
| V-02 | market_narratives 테이블 존재 + date 유니크 | DB 스키마 확인 |
| V-03 | finviz_fetch.py가 5개 카테고리 파싱 | 스크립트 실행 + DB 건수 확인 |
| V-04 | narrative_analyzer.py가 JSON 구조 분석 생성 | API 호출 결과 확인 |
| V-05 | run_news.py 배치 정상 동작 | CLI 실행 확인 |
| V-06 | GET /api/v1/news-intel/articles 응답 | curl/httpie 테스트 |
| V-07 | GET /api/v1/news-intel/narrative 응답 | curl/httpie 테스트 |
| V-08 | 대시보드 카테고리 필터 탭 동작 | 브라우저 확인 |
| V-09 | AI 브리핑 패널 (핵심이슈 3개 + 내러티브) | 브라우저 확인 |
| V-10 | 섹터 영향도 매트릭스 표시 | 브라우저 확인 |
| V-11 | 메인 대시보드 링크 존재 | 시장모니터링 섹션 확인 |
| V-12 | 외부 라이브러리 추가 없음 (CSS-only) | HTML 스크립트 태그 확인 |
| V-13 | 다크 테마 일관성 | 기존 모니터와 색상 비교 |

---

## 7. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Finviz 스크래핑 차단 (robots.txt 403) | High | Medium | User-Agent 로테이션 + 2초 딜레이 + 차단 시 캐시 데이터 표시 |
| Claude API 분석 품질 불일치 | Medium | Low | 구조화 JSON 응답 강제 + 프롬프트 버전 관리 + 수동 보정 가능 |
| 뉴스 중복 저장 | Low | Medium | (source, url) composite unique index |
| Finviz HTML 구조 변경 | High | Low | 파서를 소스별 모듈로 분리, 변경 시 해당 파서만 수정 |
| API 비용 초과 | Low | Low | 하루 6회 제한 + 동일 날짜 재분석 방지 (date unique) |

---

## 8. Implementation Order (Design 참고용)

| 순서 | 작업 | 파일 | 예상 변경량 |
|------|------|------|-------------|
| 1 | DB 모델 정의 | `backend/app/models/news_article.py` | ~60줄 |
| 2 | 모델 등록 | `backend/app/models/__init__.py` | ~2줄 |
| 3 | Finviz 파서 | `scripts/news_monitor/finviz_fetch.py` | ~120줄 |
| 4 | AI 분석기 | `scripts/news_monitor/narrative_analyzer.py` | ~100줄 |
| 5 | 배치 스크립트 | `scripts/news_monitor/run_news.py` | ~60줄 |
| 6 | API 서비스 | `backend/app/services/news_intelligence_service.py` | ~60줄 |
| 7 | API 라우터 | `backend/app/api/news_intelligence.py` | ~50줄 |
| 8 | main.py 라우터 등록 | `backend/app/main.py` | ~2줄 |
| 9 | 대시보드 페이지 | `dashboard/news_intelligence.html` | ~600줄 |
| 10 | 메인 대시보드 링크 | `dashboard/index.html` | ~5줄 |
| 11 | 시드 데이터 (DEMO) | `scripts/news_monitor/seed_data.py` | ~80줄 |

---

## 9. Next Steps

1. [ ] Design 문서 작성 (`/pdca design news-intelligence-monitor`)
2. [ ] 구현 시작 (`/pdca do news-intelligence-monitor`)
3. [ ] Gap Analysis (`/pdca analyze news-intelligence-monitor`)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-19 | Initial draft (Brain B안 채택) | Claude |
