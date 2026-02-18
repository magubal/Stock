# Plan: Disclosure Monitoring & Insight System (공시 모니터링 시스템)

> PDCA Phase: Plan
> Feature: disclosure-monitoring
> Created: 2026-02-14
> Source: Gemini Architect design_document.md

---

## 1. Overview

KIND(한국거래소 공시시스템)의 당일 공시 데이터를 수집하여 이벤트를 분류하고,
시장 심리 점수를 산출하여 대시보드로 시각화하는 시스템.

## 2. Problem Statement

- 투자자가 매일 수백 건의 공시를 수동으로 확인하는 데 시간이 많이 소요
- 공시의 투자 영향도(긍정/부정)를 즉시 판단하기 어려움
- 업종별 클러스터 패턴(예: 반도체 CB 동시 발행) 감지 불가

## 3. Goals

1. KIND 당일 공시 데이터 자동 수집 (Collector)
2. 이벤트 분류 및 감성 점수 산출 (Analyzer)
3. 대시보드 시각화 — 일일 시장 심리 배너, KPI 카드, 공시 피드 (Frontend)
4. 메인 대시보드와 연동 — "공시 모니터링" 버튼 추가

## 4. Scope

### In Scope
- `scripts/collect_disclosures.py` — KIND 공시 수집
- `scripts/analyze_disclosures.py` — 이벤트 분류 + 감성 점수
- `dashboard/monitor_disclosures.html` — React CDN 기반 공시 모니터 페이지
- `dashboard/data/latest_disclosures.json` — 분석된 공시 데이터
- `dashboard/index.html` — "공시 모니터링" 버튼 추가

### Out of Scope
- 실시간 WebSocket 푸시 (Phase 2)
- 종목별 상세 분석 페이지
- 알림(텔레그램/이메일) 연동

## 5. Success Criteria

| Criteria | Target |
|----------|--------|
| KIND 공시 수집 성공률 | >= 90% |
| 이벤트 분류 정확도 | >= 85% (키워드 기반) |
| 프론트엔드 렌더링 | JSON → 카드 UI 정상 표시 |
| 메인 대시보드 연동 | 버튼 클릭 → 공시 페이지 이동 |

## 6. Implementation Order

1. **Step 1**: Collector 스크립트 (`scripts/collect_disclosures.py`)
2. **Step 2**: Analyzer 스크립트 (`scripts/analyze_disclosures.py`)
3. **Step 3**: Frontend 공시 모니터 페이지 (`dashboard/monitor_disclosures.html`)
4. **Step 4**: 메인 대시보드 연동 (`dashboard/index.html` 버튼 추가)

## 7. Dependencies

- `requests` — HTTP 요청 (KIND 스크래핑)
- `beautifulsoup4` — HTML 파싱
- React 18 CDN — 프론트엔드 (기존 대시보드와 동일)
- Babel Standalone — JSX 트랜스파일
- Lucide Icons — 아이콘

## 8. Risk & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| KIND 직접 GET 차단 | High | POST 요청 + User-Agent 헤더, Fallback: Selenium/Playwright |
| EUC-KR 인코딩 이슈 | Medium | response.encoding 명시 설정 |
| 공시 데이터 구조 변경 | Medium | 파서 모듈화로 변경 시 최소 수정 |
