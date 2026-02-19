# News Intelligence Monitor - Completion Report

> **Status**: Complete
>
> **Project**: Stock Research ONE
> **Author**: Claude Opus 4.6
> **Completion Date**: 2026-02-19
> **PDCA Cycle**: #1

---

## 1. Summary

### 1.1 Project Overview

| Item | Content |
|------|---------|
| Feature | news-intelligence-monitor |
| Start Date | 2026-02-19 |
| End Date | 2026-02-19 |
| Duration | 1 day (single-session implementation) |
| Brain Session | B안 (뉴스 인텔리전스 2-Layer) 채택 |

### 1.2 Results Summary

```
┌─────────────────────────────────────────────┐
│  Completion Rate: 100%                       │
├─────────────────────────────────────────────┤
│  ✅ Complete:     32 / 32 items              │
│  ⏳ In Progress:   0 / 32 items              │
│  ❌ Cancelled:     0 / 32 items              │
└─────────────────────────────────────────────┘
```

### 1.3 Architecture Summary

```
Finviz (5 categories) ──parse──→ news_articles (DB)
                                       │
                                  Claude Sonnet API
                                       │
                              market_narratives (DB)
                              ├─ key_issues (JSON)
                              ├─ narrative (Text)
                              ├─ sector_impact (JSON)
                              └─ sentiment (Float + Label)

Finviz Groups ──scrape──→ sector_performances (DB)
                         industry_performances (DB)  ← mapped via JSON

Finviz Screener ──batch──→ industry_stocks (DB)   ← 144 industries, 4-8s delay
                           ├─ price, change_pct (당일)
                           ├─ perf_week/month/quarter/half/ytd/year
                           └─ market_cap, pe_ratio, volume

FastAPI ──GET /articles──────→ Dashboard: News List
        ──GET /narrative─────→ Dashboard: AI Briefing + Sector Matrix
        ──GET /industries────→ Dashboard: Industry Drill-down
        ──GET /stocks────────→ Dashboard: Stock Drill-down (개별 종목)
        ──GET /stocks/coverage→ Dashboard: 종목 진척률 Badge
        ──POST /fetch────────→ 통합 파이프라인 (News→Stock→Sector→AI)

CLI ──run_news.py──→ 4-Step Unified Pipeline
     │  --skip-stocks     Skip Step 2
     │  --skip-sector     Skip Step 3
     │  --skip-analysis   Skip Step 4
     │  --max-stocks N    Limit industries
     │  --stocks-only     Run Step 2 only
     └  --date YYYY-MM-DD Target date
```

---

## 2. Related Documents

| Phase | Document | Status |
|-------|----------|--------|
| Plan | [news-intelligence-monitor.plan.md](../../01-plan/features/news-intelligence-monitor.plan.md) | Finalized |
| Design | [news-intelligence-monitor.design.md](../../02-design/features/news-intelligence-monitor.design.md) | Finalized |
| Check | [news-intelligence-monitor.analysis.md](../../03-analysis/features/news-intelligence-monitor.analysis.md) | Complete (98.4%) |
| Act | Current document | Complete |

---

## 3. Completed Items

### 3.1 Functional Requirements

| ID | Requirement | Status | Notes |
|----|-------------|--------|-------|
| FR-01 | Finviz 뉴스 HTML 파싱 (5 카테고리) | Complete | market, market_pulse, stock, etf, crypto |
| FR-02 | 뉴스 저장용 DB 테이블 (multi-source) | Complete | NewsArticle + (source, url) unique |
| FR-03 | AI 분석 결과 DB 테이블 | Complete | MarketNarrative (date unique) |
| FR-04 | Claude Sonnet API 분석 자동화 | Complete | key_issues, narrative, sector_impact, sentiment |
| FR-05 | FastAPI 라우터 (3 GET + 1 POST) | Complete | articles, narrative, industries, fetch |
| FR-06 | 대시보드 페이지 | Complete | news_intelligence.html |
| FR-07 | 메인 대시보드 링크 | Complete | dashboard/index.html 시장모니터링 |
| FR-08 | 시드 데이터 (DEMO 규칙 준수) | Complete | 66 articles + 3 narratives |
| FR-09 | Sector Impact Matrix (실제 데이터) | Complete | Finviz Groups 스크래핑 |
| FR-10 | Sector-Industry 매핑 + DB 저장 | Complete | 11 sectors → 144 industries |
| FR-11 | Industry drill-down 대시보드 | Complete | 섹터 클릭 → 인더스트리 패널 |
| FR-12 | POST /fetch 통합 (뉴스+섹터+인더스트리) | Complete | 원클릭 전체 갱신 |
| FR-13 | Industry → Stock drill-down (개별 종목) | Complete | IndustryStock 모델 + 배치 스크래퍼 |
| FR-14 | Stock 배치 수집기 (anti-blocking) | Complete | 4-8s delay, 144 industries, progressive DB save |
| FR-15 | Stock 1Y trend bar 시각화 | Complete | TrendBar component (gradient bar + value) |
| FR-16 | Finviz industry slug 매핑 (144개) | Complete | data/finviz_industry_slugs.json |
| FR-17 | Unified 4-step pipeline (News→Stock→Sector→AI) | Complete | run_news.py 재작성 (v1.2.0) |
| FR-18 | Stock coverage API (진척률 조회) | Complete | GET /stocks/coverage endpoint |
| FR-19 | Coverage badge (Sector Matrix 헤더) | Complete | 색상 코딩 + 실시간 갱신 |
| FR-20 | POST /fetch 파이프라인 통합 | Complete | include_stocks, max_stocks 옵션 |

### 3.2 Non-Functional Requirements

| Item | Target | Achieved | Status |
|------|--------|----------|--------|
| Dark theme 일관성 | 기존 모니터 패턴 | `#0a0a0a`→`#1a1a2e` gradient | Complete |
| DEMO 데이터 규칙 | CLAUDE.md 규칙 준수 | source="DEMO", [DEMO] prefix, badge, banner | Complete |
| React best practices | useState/useEffect/useCallback/useMemo | 모두 적용 | Complete |
| 에러 핸들링 | Finviz 변경/API 실패 대응 | 3-level HTML fallback + Claude JSON fallback | Complete |
| 타임존 대응 | KST/UTC 양쪽 지원 | 로컬 날짜 + dual-date 서버 갱신 | Complete |

### 3.3 Deliverables

| Deliverable | Location | Lines | Status |
|-------------|----------|:-----:|--------|
| DB Models | `backend/app/models/news_article.py` | 112 | Complete (5 models) |
| Service Layer | `backend/app/services/news_intelligence_service.py` | 214 | Complete (+coverage) |
| API Router | `backend/app/api/news_intelligence.py` | 179 | Complete (6 endpoints) |
| Dashboard | `dashboard/news_intelligence.html` | ~1320 | Complete (+coverage badge) |
| Finviz Parser | `scripts/news_monitor/finviz_fetch.py` | ~450 | Complete |
| AI Analyzer | `scripts/news_monitor/narrative_analyzer.py` | 182 | Complete |
| Config | `scripts/news_monitor/config.py` | 40 | Complete |
| Unified CLI Runner | `scripts/news_monitor/run_news.py` | 154 | Complete (4-step pipeline) |
| Seed Data | `scripts/news_monitor/seed_data.py` | 141 | Complete |
| Sector-Industry Map | `data/finviz_sector_industry_map.json` | 78 | Complete |
| Mapping Verifier | `scripts/news_monitor/verify_mapping.py` | 20 | Complete |
| Stock Batch Scraper | `scripts/news_monitor/stock_fetch.py` | 314 | Complete |
| Industry Slug Map | `data/finviz_industry_slugs.json` | 146 | Complete (144 industries) |

**Total: ~3,350+ lines across 17 files**

---

## 4. Incomplete Items

### 4.1 Carried Over (Phase 2 Candidates)

| Item | Reason | Priority | Notes |
|------|--------|----------|-------|
| Yahoo Finance / Reuters 추가 소스 | Out of scope (DB는 대응) | Low | NewsArticle.source 필드로 확장 가능 |
| 센티먼트 시계열 차트 | Phase 2 | Medium | market_narratives에 데이터 축적 중 |
| 섹터 히트맵 시각화 | Phase 2 | Low | IndustryPerformance 데이터 활용 가능 |
| 4시간 배치 스케줄러 (cron) | Phase 2 | Medium | run_news.py + stock_fetch.py 통합 배치 |
| 전 인더스트리 Stock 배치 실행 | Post-deploy | ~~High~~ Done | v1.2.0에서 full batch 실행 완료 |

### 4.2 Cancelled/On Hold Items

None.

---

## 5. Quality Metrics

### 5.1 Final Analysis Results

| Metric | Target | Final | Status |
|--------|--------|-------|--------|
| Design Match Rate | 90% | 98.4% | PASS |
| Architecture Compliance | 90% | 100% | PASS |
| Convention Compliance | 90% | 97.4% | PASS |
| Error Handling | 80% | 88.9% | PASS |
| Verification Criteria | 19/19 | 19/19 (100%) | PASS |
| Cross-Consistency | 15/15 | 15/15 (100%) | PASS |
| Missing Features | 0 | 0 | PASS |

### 5.2 Resolved Issues (During Implementation)

| # | Issue | Root Cause | Resolution |
|---|-------|------------|------------|
| 1 | Finviz market articles = 0 | API limit=200 too low | limit=500 (articles), limit=1000 (API param) |
| 2 | Sector Impact showing wrong direction | DEMO 시드 데이터 고정값 | 실제 Finviz sector scraper 구현 |
| 3 | Sector scraper returning 0 | Finviz `<th>` not `<td>` | `find_all("th")` 로 수정 |
| 4 | Claude API credits insufficient | API 호출 실패 | `generate_from_sector_data()` fallback (AI 없이 실제 데이터) |
| 5 | Dashboard showing DEMO after refresh | `new Date().toISOString()` = UTC date | 로컬 KST 날짜로 변경 |
| 6 | Server not picking up changes | Old uvicorn process | kill + fresh restart |
| 7 | Timezone mismatch in article filter | UTC vs KST 날짜 경계 | `or_()` filter with prev_date 15:00 UTC |
| 8 | Shell Companies unmapped | JSON 매핑 누락 | Financial 섹터에 추가 |
| 9 | Stock batch not running in background | Python buffered output | `-u` flag + `nohup` redirect |
| 10 | AhnLab V3 false positive (MDP.Powershell.M2514) | PowerShell 프로세스 관리 명령 | PowerShell 사용 중단, bash 사용 |

---

## 6. Lessons Learned & Retrospective

### 6.1 What Went Well (Keep)

- **Finviz Groups 공통 파서**: `_parse_groups_table()` 함수가 sector/industry 양쪽 모두 처리하여 코드 재사용성 높음
- **실제 데이터 우선**: DEMO 시드 → 실제 Finviz 데이터 전환이 빠르게 이루어짐
- **타임존 이중 대응**: UTC/KST 양쪽 날짜 모두 처리하는 패턴이 안정적
- **Brain → Plan → Design → Do → Check 순서** 준수로 요구사항 누락 방지

### 6.2 What Needs Improvement (Problem)

- **Finviz HTML 구조 변경에 취약**: `<th>` vs `<td>` 문제처럼 HTML 구조에 의존하는 파서는 잦은 수정 필요
- **DEMO 데이터에서 실제 데이터 전환 시 혼란**: 시드 데이터가 오래 남아있으면 실제 데이터와 섞임
- **서버 reload 감지 지연**: `--reload` 옵션이 때때로 변경을 감지하지 못함

### 6.3 What to Try Next (Try)

- Playwright E2E 테스트에 News Intelligence 페이지 추가
- 4시간 배치 스케줄러 구현 (cron job or Windows Task Scheduler)
- 섹터 히트맵 시각화 (IndustryPerformance 데이터 활용)

### 6.4 Key Learnings (v1.2.0)

- **파이프라인 순서 중요**: Stock 수집은 반드시 Sector Matrix 직전에 실행해야 데이터 일관성 확보
- **Background Python**: Windows에서 `python -u` (unbuffered) + `nohup` 필수, 기본 `&`는 output 없음
- **AhnLab V3 오탐**: PowerShell `Get-Process | Stop-Process` 패턴이 `MDP.Powershell.M2514`로 감지됨 → bash로 대체
- **Coverage badge 패턴**: `func.count(func.distinct(column))` → 진척률 추적에 재사용 가능한 패턴

---

## 7. DB Tables Summary

### 7.1 New Tables (5)

| Table | Records | Key Fields |
|-------|:-------:|-----------|
| `news_articles` | 66+ (DEMO) + live | source, category, title, url, publisher, published_at |
| `market_narratives` | 3+ (DEMO) + live | date (unique), key_issues (JSON), narrative, sector_impact (JSON), sentiment |
| `sector_performances` | 11/day | date, sector, change_pct, market_cap, pe_ratio, volume |
| `industry_performances` | 144/day | date, industry, sector (mapped), change_pct, market_cap, pe_ratio, volume |
| `industry_stocks` | ~2000+/day | date, ticker (unique), industry, sector, price, change_pct, perf_week/month/quarter/half/ytd/year, market_cap, pe_ratio, volume |

### 7.2 Sector-Industry Mapping

11 GICS sectors → 144 Finviz industries, static JSON at `data/finviz_sector_industry_map.json`.

### 7.3 Industry Slug Mapping

144 industries → Finviz screener URL slugs at `data/finviz_industry_slugs.json`.
Batch collection via `scripts/news_monitor/stock_fetch.py` with 4-8s anti-blocking delay.

---

## 8. API Endpoints Summary

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/news-intel/articles` | 뉴스 기사 목록 (category, date, source, limit) |
| GET | `/api/v1/news-intel/narrative` | AI 분석 내러티브 (date) |
| GET | `/api/v1/news-intel/industries` | 섹터→인더스트리 퍼포먼스 (sector, date) |
| GET | `/api/v1/news-intel/stocks` | 인더스트리별 개별 종목 (industry, sector, date) |
| GET | `/api/v1/news-intel/stocks/coverage` | 종목 수집 진척률 (collected/144, date) |
| POST | `/api/v1/news-intel/fetch` | 통합 파이프라인 (include_stocks, max_stocks) |

---

## 9. Next Steps

### 9.1 Immediate

- [ ] Archive PDCA documents (`/pdca archive news-intelligence-monitor`)
- [ ] Playwright 테스트에 news_intelligence.html 추가

### 9.2 Phase 2 (Future PDCA Cycle)

| Item | Priority | Notes |
|------|----------|-------|
| 센티먼트 시계열 차트 | Medium | 30일 트렌드 시각화 |
| 4시간 배치 스케줄러 | Medium | cron / Task Scheduler |
| Yahoo Finance 소스 추가 | Low | 파서만 추가하면 DB 대응 완료 |
| 섹터 히트맵 | Low | D3.js or Chart.js treemap |

---

## 10. Changelog

### v1.2.0 (2026-02-19)

**Added:**
- Unified 4-step pipeline: News → Stock → Sector Matrix → AI Narrative
- `run_news.py` 완전 재작성 (154 lines, 6 CLI flags)
- GET `/stocks/coverage` endpoint (종목 수집 진척률)
- `get_stock_coverage()` service method (SQLAlchemy `func.count(func.distinct())`)
- Coverage badge UI (Sector Impact Matrix 헤더, 색상 코딩: green/orange/gray)
- POST `/fetch` 파이프라인 통합 (`include_stocks`, `max_stocks` params)
- `--skip-stocks`, `--skip-sector`, `--stocks-only`, `--max-stocks` CLI 옵션

**Changed:**
- Stock 배치 수집이 Sector Matrix **직전**에 실행되도록 파이프라인 순서 변경
- POST `/fetch` response에 `stocks` 필드 추가

**Resolved:**
- 전체 144 인더스트리 Stock 배치 수집 완료 (이전 Phase 2 candidate → 완료)

### v1.1.0 (2026-02-19)

**Added:**
- Industry → Stock drill-down (인더스트리 클릭 → 개별 종목 테이블)
- Finviz screener 배치 수집기 (144 industries, 4-8s anti-blocking delay)
- IndustryStock DB 모델 (price, change_pct, 6-period perf, market_cap, PE, volume)
- GET /stocks API endpoint
- TrendBar component (1Y 퍼포먼스 그래디언트 바 시각화)
- Industry slug 매핑 파일 (data/finviz_industry_slugs.json, 144개)

### v1.0.0 (2026-02-19)

**Added:**
- Finviz 뉴스 5 카테고리 파싱 (market, market_pulse, stock, etf, crypto)
- Claude Sonnet API 기반 AI 분석 (key_issues, narrative, sector_impact, sentiment)
- FastAPI 4 endpoints (articles, narrative, industries, fetch)
- Dashboard: AI Briefing + Sector Impact Matrix + Industry Drill-down + News List
- DB 4 tables: news_articles, market_narratives, sector_performances, industry_performances
- Sector-Industry 매핑 (11 sectors → 144 industries)
- DEMO 시드 데이터 (66 articles + 3 narratives)
- 메인 대시보드 시장모니터링 섹션 링크

**Fixed:**
- Finviz HTML `<th>` 파싱 문제
- KST/UTC 타임존 날짜 경계 문제
- Claude API fallback (실제 섹터 데이터 직접 사용)

---

## Related Documents

- Plan: [news-intelligence-monitor.plan.md](../../01-plan/features/news-intelligence-monitor.plan.md)
- Design: [news-intelligence-monitor.design.md](../../02-design/features/news-intelligence-monitor.design.md)
- Analysis: [news-intelligence-monitor.analysis.md](../../03-analysis/features/news-intelligence-monitor.analysis.md)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-02-19 | Completion report created | Claude Opus 4.6 |
| 1.1 | 2026-02-19 | Stock drill-down feature added (v1.1.0) | Claude Opus 4.6 |
| 1.2 | 2026-02-19 | Unified pipeline + coverage badge (v1.2.0) | Claude Opus 4.6 |
