# data-source-footer Planning Document

> **Summary**: 시장 모니터링 6개 페이지 하단에 데이터 소스 요약 패널(Footer) 추가
>
> **Project**: Stock Research ONE
> **Author**: Claude + User
> **Date**: 2026-02-19
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

각 모니터링 대시보드의 **데이터 소스, DB 테이블, 마지막 수집 시점, 수집 상태**를 한눈에 파악할 수 있는 Footer 섹션을 추가한다. 현재는 데이터가 언제 갱신되었는지 확인할 방법이 없어, 오래된 데이터로 판단할 위험이 있다.

### 1.2 Background

- 6개 모니터링 페이지(유동성, 크립토, 공시, 해자분석, 뉴스인텔, 아이디어보드)가 운영 중
- `collector/status` API가 liquidity, crypto 수집기 상태를 이미 제공
- 일부 페이지(공시, 해자)는 수집 API가 없으며 수동 입력 또는 정적 데이터 사용
- 사용자가 "이 데이터가 언제 것인지" 확인하려면 직접 DB를 열어야 하는 상황

### 1.3 Related Documents

- [daily-data-collector Plan](daily-data-collector.plan.md) — 수집 자동화 기반
- [liquidity-stress-monitor Design](../../02-design/features/liquidity-stress-monitor.design.md)
- [crypto-trends-monitor Design](../../02-design/features/crypto-trends-monitor.design.md)

---

## 2. Scope

### 2.1 In Scope

- [ ] 6개 모니터링 페이지 하단에 DataSourceFooter 컴포넌트 추가
- [ ] 페이지별 `DATA_SOURCES` JS 상수 정의 (소스명, DB테이블, API URL, 수집 스크립트)
- [ ] `collector/status` API 확장: 공시/해자/뉴스인텔 수집기 상태도 반환
- [ ] 기본 모드: 요약 테이블 (소스명 | DB | 마지막 수집 | 상태)
- [ ] 상세 펼치기: API URL, 스크립트 경로, 에러 메시지, 데이터 건수
- [ ] 공유 CSS 클래스 (`data-source-footer.*`)
- [ ] collector/status 미지원 소스에 "정적/수동" 배지 표시
- [ ] DEMO 데이터 소스에 빨간 DEMO 배지 연동

### 2.2 Out of Scope

- collector/status API 자체의 인증/권한 관리
- 수집 스케줄러 UI (이미 daily-data-collector에서 다룸)
- 외부 공유용 PDF/이미지 내보내기
- 모니터링 페이지 자체의 기능 변경

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | 각 모니터링 페이지 하단에 접이식(collapsible) DataSourceFooter 표시 | High | Pending |
| FR-02 | 요약 모드: 소스명, DB테이블, 마지막 수집시간, 상태 도트(green/yellow/red) | High | Pending |
| FR-03 | 상세 모드: API URL, 수집 스크립트 경로, 최근 에러, 데이터 건수 | Medium | Pending |
| FR-04 | collector/status API에 모든 수집기(6종) 상태 포함 | High | Pending |
| FR-05 | 자동 수집 미지원 소스에 "수동 입력" / "정적 데이터" 배지 | Medium | Pending |
| FR-06 | DEMO 데이터 배지 연동 (source="DEMO" 감지) | Medium | Pending |
| FR-07 | 마지막 수집 시간 기준 상태 색상: <1h 초록, <24h 노랑, >24h 빨강 | High | Pending |
| FR-08 | 공유 CSS로 6개 페이지 일관된 스타일 적용 | Medium | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| Performance | Footer 로딩 < 500ms (collector/status API 응답 포함) | Network 탭 확인 |
| UX | 접힌 상태 기본, 1-click 펼치기 | 수동 확인 |
| 유지보수 | 새 수집기 추가 시 `DATA_SOURCES` 배열에 1항목 추가만으로 확장 | 코드 리뷰 |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] 6개 모니터링 페이지 모두에 DataSourceFooter 렌더링
- [ ] collector/status API 호출하여 실시간 상태 표시
- [ ] 수집기 없는 소스는 "정적"/"수동" 배지 정상 표시
- [ ] 접기/펼치기 토글 동작 확인
- [ ] DEMO 배지 연동 확인

### 4.2 Quality Criteria

- [ ] 6개 페이지에서 Footer CSS 일관성 확인
- [ ] collector/status 5초 이내 응답
- [ ] 에러 시 Footer가 깨지지 않고 "상태 불명" 표시

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| collector/status API 확장 시 기존 응답 형식 변경 | Medium | Low | 기존 필드 유지, 새 수집기만 추가 |
| 6개 페이지 각각 다른 CSS 컨텍스트 | Medium | Medium | 공유 CSS 인라인 또는 별도 파일 |
| 일부 수집기(공시/해자) 상태 추적 어려움 | Low | High | "수동" 배지로 우아하게 처리 |

---

## 6. Architecture Considerations

### 6.1 Project Level Selection

| Level | Characteristics | Recommended For | Selected |
|-------|-----------------|-----------------|:--------:|
| **Starter** | Simple structure | Static sites | ☐ |
| **Dynamic** | Feature-based modules, BaaS | Web apps with backend | ☑ |
| **Enterprise** | Strict layer separation | High-traffic systems | ☐ |

### 6.2 Key Architectural Decisions

| Decision | Options | Selected | Rationale |
|----------|---------|----------|-----------|
| 렌더링 방식 | CDN React (기존) | CDN React | 기존 dashboard HTML 패턴 유지 |
| Footer 메타데이터 | 하드코딩 / API / 하이브리드 | 하이브리드 (C안) | 정적 메타 + 동적 상태 분리 |
| CSS 공유 | 별도 CSS 파일 / 인라인 | 인라인 `<style>` | 기존 페이지 패턴과 동일, 독립 배포 가능 |
| 상태 API | 기존 collector/status 확장 | collector/status 확장 | 엔드포인트 1개 유지, 수집기명만 추가 |

### 6.3 구현 구조

```
대상 페이지 (6개):
├── dashboard/liquidity_stress.html    ← 유동성 스트레스
├── dashboard/crypto_trends.html       ← 크립토 트렌드
├── dashboard/monitor_disclosures.html ← 공시 모니터
├── dashboard/moat_analysis.html       ← 해자 분석
├── dashboard/news_intelligence.html   ← 뉴스 인텔리전스
└── dashboard/idea_board.html          ← 아이디어 보드

Backend:
└── backend/app/api/collector.py       ← /status 확장

각 페이지 구조:
┌─────────────────────────────────────────┐
│ DATA_SOURCES = [                        │  ← JS 상수 (정적 메타)
│   { name, db_table, api_url,            │
│     script, collector_key, type }       │
│ ]                                       │
├─────────────────────────────────────────┤
│ DataSourceFooter 컴포넌트               │  ← React 컴포넌트
│   - fetch /api/v1/collector/status      │
│   - DATA_SOURCES + API 응답 merge       │
│   - 접기/펼치기 토글                     │
│   - 요약 테이블 + 상세 정보              │
└─────────────────────────────────────────┘
```

---

## 7. Implementation Plan

### 7.1 구현 순서

| Step | Task | Estimated Size |
|------|------|---------------|
| 1 | `collector/status` API 확장 (6종 수집기 + 데이터 건수) | Small |
| 2 | 공유 CSS 스타일 정의 (인라인 `<style>`) | Small |
| 3 | DataSourceFooter React 컴포넌트 패턴 작성 | Medium |
| 4 | liquidity_stress.html에 적용 + 테스트 | Small |
| 5 | crypto_trends.html에 적용 | Small |
| 6 | monitor_disclosures.html에 적용 | Small |
| 7 | moat_analysis.html에 적용 | Small |
| 8 | news_intelligence.html에 적용 | Small |
| 9 | idea_board.html에 적용 | Small |
| 10 | E2E 테스트 (전체 6개 페이지) | Medium |

### 7.2 페이지별 DATA_SOURCES 목록

#### liquidity_stress.html
| Source | DB Table | Collector Key | Type |
|--------|----------|--------------|------|
| FRED (금리/신용) | liquidity_macro | liquidity | auto |
| Yahoo Finance (가격) | liquidity_price | liquidity | auto |
| Google News (뉴스) | liquidity_news | liquidity | auto |
| Fed Speech (연준 발언) | fed_tone | liquidity | auto |
| Stress Calculator | stress_index | liquidity | auto |

#### crypto_trends.html
| Source | DB Table | Collector Key | Type |
|--------|----------|--------------|------|
| CoinGecko (Top 20) | crypto_price | crypto | auto |
| DefiLlama (TVL) | crypto_defi | crypto | auto |
| Fear & Greed Index | crypto_sentiment | crypto | auto |
| ETH ETF Flow | - | - | manual |
| MVRV Z-Score | - | - | manual |

#### monitor_disclosures.html
| Source | DB Table | Collector Key | Type |
|--------|----------|--------------|------|
| DART API (공시) | disclosures | - | static |
| DART API (재무) | - | - | on-demand |

#### moat_analysis.html
| Source | DB Table | Collector Key | Type |
|--------|----------|--------------|------|
| DART 연간재무 | - | - | on-demand |
| Oracle DB (TTM) | - | - | on-demand |
| 해자 분석 결과 | moat_evaluations | - | on-demand |

#### news_intelligence.html
| Source | DB Table | Collector Key | Type |
|--------|----------|--------------|------|
| Naver Blog | naver_blog_data | news | auto |
| 뉴스 분석 결과 | news_analysis | news | auto |

#### idea_board.html
| Source | DB Table | Collector Key | Type |
|--------|----------|--------------|------|
| Daily Work (Excel) | daily_work | - | manual |
| AI Insights | insights | - | on-demand |
| Investment Ideas | ideas | - | manual |
| Sector Momentum | - | - | on-demand |
| Market Events | - | - | static |

---

## 8. Next Steps

1. [ ] Write design document (`data-source-footer.design.md`)
2. [ ] Team review and approval
3. [ ] Start implementation

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-19 | Initial draft from brainstorm C안 (hybrid approach) | Claude + User |
