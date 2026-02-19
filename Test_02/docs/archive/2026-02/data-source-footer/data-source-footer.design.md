# data-source-footer Design Document

> **Summary**: 6개 모니터링 페이지 하단에 데이터 소스 요약 패널(접이식 Footer) 추가
>
> **Project**: Stock Research ONE
> **Author**: Claude + User
> **Date**: 2026-02-19
> **Status**: Draft
> **Planning Doc**: [data-source-footer.plan.md](../../01-plan/features/data-source-footer.plan.md)

---

## 1. Overview

### 1.1 Design Goals

- 각 모니터링 페이지에서 **데이터의 신선도와 출처**를 즉시 확인 가능하게 함
- 기존 collector/status API를 확장하여 동적 상태를 제공하되, 정적 메타데이터와 결합하는 하이브리드 방식
- 6개 페이지에 일관된 UX/스타일 적용 (공유 CSS 패턴)

### 1.2 Design Principles

- **최소 침습**: 기존 페이지 코드에 Footer 컴포넌트 삽입만으로 완성 (기존 코드 변경 최소화)
- **확장 용이**: 새 수집기 추가 시 `DATA_SOURCES` 배열에 항목 1개 추가로 충분
- **우아한 실패**: API 응답 실패 시에도 정적 메타는 표시, 상태만 "불명"으로 표시

---

## 2. Architecture

### 2.1 Component Diagram

```
각 모니터링 페이지 (.html)
┌─────────────────────────────────────────────────────────────┐
│  <style> ... data-source-footer CSS ...  </style>           │
│                                                             │
│  const DATA_SOURCES = [ ... ];  ← 페이지별 정적 메타데이터   │
│                                                             │
│  const DataSourceFooter = () => {                           │
│      fetch('/api/v1/collector/status')  ← 동적 상태          │
│      merge(DATA_SOURCES, apiResponse)                       │
│      render table                                           │
│  };                                                         │
│                                                             │
│  // Main App return:                                        │
│  <MainContainer>                                            │
│      ... existing content ...                               │
│      <DataSourceFooter />  ← 삽입 위치                      │
│  </MainContainer>                                           │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│  Backend: GET /api/v1/collector/status │
│  ┌──────────────────────────────────┐ │
│  │ collectors: {                    │ │
│  │   liquidity: { date, status, …} │ │
│  │   crypto:    { date, status, …} │ │
│  │   news:      { date, status, …} │ │
│  │   disclosure:{ date, status, …} │ │  ← 확장
│  │   moat:      { date, status, …} │ │  ← 확장
│  │   idea:      { date, status, …} │ │  ← 확장
│  │ }                                │ │
│  │ table_counts: {                  │ │  ← 신규
│  │   liquidity_macro: 48,           │ │
│  │   crypto_price: 120, …           │ │
│  │ }                                │ │
│  └──────────────────────────────────┘ │
└──────────────────────────────────────┘
```

### 2.2 Data Flow

```
페이지 로드 → DataSourceFooter mount
  → fetch /api/v1/collector/status
  → merge DATA_SOURCES (static) + API response (dynamic)
  → render: 접힌 상태 (1-line 요약)
  → 클릭 → 펼친 상태 (상세 테이블)
```

### 2.3 Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| DataSourceFooter (React) | DATA_SOURCES 상수 | 정적 메타데이터 |
| DataSourceFooter (React) | /api/v1/collector/status | 동적 상태 + 건수 |
| collector/status API | CollectorLog 테이블 | 수집 이력 |
| collector/status API | 각 DB 테이블 | row count 조회 |

---

## 3. Data Model

### 3.1 DATA_SOURCES 상수 (프론트엔드, 페이지별)

```javascript
const DATA_SOURCES = [
    {
        name: "FRED (금리/신용)",          // 표시 이름
        db_table: "liquidity_macro",      // DB 테이블명
        collector_key: "liquidity",       // collector/status의 key (null이면 정적)
        type: "auto",                     // auto | manual | static | on-demand
        api_url: "https://fred.stlouisfed.org/",  // 원본 데이터 출처
        script: "scripts/liquidity_monitor/fred_fetch.py",  // 수집 스크립트
    },
    // ...
];
```

### 3.2 collector/status API 응답 확장

```json
{
    "collectors": {
        "liquidity": {
            "date": "2026-02-19",
            "status": "success",
            "duration": 25.4,
            "triggered_by": "api",
            "created_at": "2026-02-19T12:00:00"
        },
        "crypto": { ... },
        "news": { ... },
        "disclosure": null,
        "moat": null,
        "idea": null
    },
    "table_counts": {
        "liquidity_macro": 48,
        "liquidity_price": 48,
        "liquidity_news": 569,
        "fed_tone": 5,
        "stress_index": 30,
        "crypto_price": 120,
        "crypto_defi": 20,
        "crypto_sentiment": 30,
        "disclosures": 0,
        "moat_evaluations": 0,
        "daily_work": 14,
        "insights": 10,
        "ideas": 5
    }
}
```

---

## 4. API Specification

### 4.1 확장: GET /api/v1/collector/status

기존 응답에 `table_counts` 필드 추가.

**기존 응답:**
```json
{ "collectors": { "liquidity": {...}, "crypto": {...}, "news": {...} } }
```

**확장 응답:**
```json
{
    "collectors": {
        "liquidity": { "date": "...", "status": "...", "duration": 0, "triggered_by": "...", "created_at": "..." },
        "crypto": { ... },
        "news": { ... },
        "disclosure": null,
        "moat": null,
        "idea": null
    },
    "table_counts": {
        "liquidity_macro": 48,
        "liquidity_price": 48,
        "liquidity_news": 569,
        "fed_tone": 5,
        "stress_index": 30,
        "crypto_price": 120,
        "crypto_defi": 20,
        "crypto_sentiment": 30,
        "disclosures": 0,
        "moat_evaluations": 0,
        "daily_work": 14,
        "insights": 10,
        "ideas": 5
    }
}
```

**변경사항:**
1. `collectors` 목록에 `"disclosure"`, `"moat"`, `"idea"` 추가 (현재 미지원이므로 null)
2. `table_counts` 필드 추가: 주요 DB 테이블별 row count
3. 기존 클라이언트 호환성 유지 (새 필드 추가만)

---

## 5. UI/UX Design

### 5.1 Footer 레이아웃

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ▸ 데이터 소스 (5개 소스 · 마지막 수집 2026-02-19 15:30)    [접기/펼치기] │
└─────────────────────────────────────────────────────────────────────────┘

  ↓ 펼치면:

┌─────────────────────────────────────────────────────────────────────────┐
│ ▾ 데이터 소스 (5개 소스 · 마지막 수집 2026-02-19 15:30)    [접기/펼치기] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  소스명             │ DB 테이블        │ 건수  │ 마지막 수집   │ 상태    │
│  ────────────────── │ ──────────────── │ ───── │ ──────────── │ ─────── │
│  FRED (금리/신용)   │ liquidity_macro  │ 48    │ 02-19 15:30  │ 🟢      │
│  Yahoo (가격)       │ liquidity_price  │ 48    │ 02-19 15:30  │ 🟢      │
│  Google News        │ liquidity_news   │ 569   │ 02-19 15:30  │ 🟢      │
│  Fed Speech         │ fed_tone         │ 5     │ 02-19 15:30  │ 🟢      │
│  Stress Calculator  │ stress_index     │ 30    │ 02-19 15:30  │ 🟢      │
│                                                                         │
│  ─── 상세 (개별 행 클릭 시) ───                                          │
│  API: https://fred.stlouisfed.org/                                      │
│  Script: scripts/liquidity_monitor/fred_fetch.py                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 상태 색상 규칙

| 조건 | 색상 | 아이콘 |
|------|------|--------|
| 수집 성공 + 1시간 이내 | `#22c55e` (초록) | 채워진 원 |
| 수집 성공 + 24시간 이내 | `#eab308` (노랑) | 채워진 원 |
| 수집 성공 + 24시간 초과 | `#ef4444` (빨강) | 채워진 원 |
| 수집 실패/에러 | `#ef4444` (빨강) | 느낌표 원 |
| 수동 입력 | `#64748b` (회색) | "수동" 배지 |
| 정적 데이터 | `#64748b` (회색) | "정적" 배지 |
| on-demand | `#8b5cf6` (보라) | "요청 시" 배지 |
| 상태 불명 (API 실패) | `#475569` (어두운회색) | 물음표 |

### 5.3 DEMO 배지 연동

- `table_counts`에서 DEMO source 건수를 별도 집계하는 것은 과도 → **기존 페이지 DEMO 배너와 독립**
- DATA_SOURCES에 `source: "DEMO"` 표시된 항목은 빨간 DEMO 배지 추가

### 5.4 Component 구조

| Component | 위치 | 역할 |
|-----------|------|------|
| `DataSourceFooter` | 각 페이지 `<script type="text/babel">` 내 | 접이식 Footer 렌더 |
| `DATA_SOURCES` | 각 페이지 상단 상수 | 페이지별 소스 메타 |
| CSS classes | 각 페이지 `<style>` 내 | 공통 스타일 |

---

## 6. Error Handling

### 6.1 시나리오별 처리

| 시나리오 | 처리 |
|----------|------|
| collector/status API 200 | 정상 merge + 렌더 |
| collector/status API 500 | 정적 메타만 표시, 상태 열 "불명" |
| collector/status API timeout | 5초 timeout 후 정적 메타만 표시 |
| table_counts에 해당 테이블 없음 | 건수 "-" 표시 |
| collector_key null (수동/정적) | 상태 열에 type 배지 표시 |

---

## 7. CSS 설계

### 7.1 공유 CSS 클래스 (인라인)

각 페이지 `<style>` 블록에 아래 클래스를 추가합니다. 기존 페이지의 dark theme 색상 체계를 따릅니다.

```css
/* ─── Data Source Footer ─── */
.ds-footer {
    margin: 2rem auto 1rem;
    max-width: 1400px;
    padding: 0 2rem;
}

.ds-footer-toggle {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    cursor: pointer;
    transition: background 0.2s;
    width: 100%;
    color: #94a3b8;
    font-size: 0.8rem;
}

.ds-footer-toggle:hover {
    background: rgba(30, 41, 59, 0.9);
}

.ds-footer-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 0.5rem;
    font-size: 0.78rem;
}

.ds-footer-table th {
    text-align: left;
    color: #64748b;
    padding: 0.4rem 0.6rem;
    border-bottom: 1px solid #1e293b;
    font-weight: 500;
}

.ds-footer-table td {
    padding: 0.4rem 0.6rem;
    color: #cbd5e1;
    border-bottom: 1px solid rgba(30, 41, 59, 0.5);
}

.ds-footer-table tr:hover td {
    background: rgba(51, 65, 85, 0.3);
}

.ds-status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 4px;
}

.ds-badge {
    display: inline-block;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 0.68rem;
    font-weight: 600;
}

.ds-badge-auto   { background: rgba(34,197,94,0.15); color: #22c55e; }
.ds-badge-manual  { background: rgba(100,116,139,0.2); color: #94a3b8; }
.ds-badge-static  { background: rgba(100,116,139,0.2); color: #64748b; }
.ds-badge-ondemand { background: rgba(139,92,246,0.15); color: #a78bfa; }
.ds-badge-demo    { background: rgba(239,68,68,0.15); color: #ef4444; }

.ds-detail-row td {
    padding: 0.3rem 0.6rem 0.5rem;
    color: #64748b;
    font-size: 0.72rem;
    border-bottom: 1px solid rgba(30, 41, 59, 0.3);
}

.ds-detail-row a {
    color: #60a5fa;
    text-decoration: none;
}

.ds-detail-row a:hover {
    text-decoration: underline;
}
```

---

## 8. 구현 가이드

### 8.1 DataSourceFooter React 컴포넌트 (공통 패턴)

```jsx
const DataSourceFooter = React.memo(() => {
    const [expanded, setExpanded] = useState(false);
    const [status, setStatus] = useState(null);
    const [detailIdx, setDetailIdx] = useState(null);

    useEffect(() => {
        fetch(`${API_BASE}/api/v1/collector/status`)
            .then(r => r.json())
            .then(setStatus)
            .catch(() => setStatus(null));
    }, []);

    const getStatusColor = (src) => {
        if (!src.collector_key || !status?.collectors?.[src.collector_key]) {
            return src.type === 'manual' ? '#64748b'
                 : src.type === 'static' ? '#64748b'
                 : src.type === 'on-demand' ? '#8b5cf6'
                 : '#475569';
        }
        const c = status.collectors[src.collector_key];
        if (!c || c.status !== 'success') return '#ef4444';
        const hours = (Date.now() - new Date(c.created_at).getTime()) / 3600000;
        if (hours < 1) return '#22c55e';
        if (hours < 24) return '#eab308';
        return '#ef4444';
    };

    const getLastTime = (src) => {
        if (!src.collector_key || !status?.collectors?.[src.collector_key]) return '-';
        const c = status.collectors[src.collector_key];
        if (!c?.created_at) return '-';
        return new Date(c.created_at).toLocaleString('ko-KR', {
            month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit'
        });
    };

    const getCount = (src) => {
        if (!src.db_table || !status?.table_counts) return '-';
        const count = status.table_counts[src.db_table];
        return count != null ? count.toLocaleString() : '-';
    };

    const latestTime = DATA_SOURCES
        .map(s => s.collector_key && status?.collectors?.[s.collector_key]?.created_at)
        .filter(Boolean)
        .sort().pop();

    const typeBadge = (type) => {
        const labels = { auto: '자동', manual: '수동', static: '정적', 'on-demand': '요청시' };
        const cls = type === 'on-demand' ? 'ondemand' : type;
        return <span className={`ds-badge ds-badge-${cls}`}>{labels[type] || type}</span>;
    };

    return (
        <div className="ds-footer">
            <button className="ds-footer-toggle" onClick={() => setExpanded(!expanded)}>
                <span>
                    {expanded ? '\u25BE' : '\u25B8'} 데이터 소스
                    ({DATA_SOURCES.length}개 소스
                    {latestTime ? ` \u00b7 마지막 수집 ${new Date(latestTime).toLocaleString('ko-KR', {
                        month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit'
                    })}` : ''})
                </span>
                <span style={{fontSize: '0.72rem'}}>
                    {expanded ? '접기' : '펼치기'}
                </span>
            </button>

            {expanded && (
                <table className="ds-footer-table">
                    <thead>
                        <tr>
                            <th>소스</th>
                            <th>DB 테이블</th>
                            <th>건수</th>
                            <th>마지막 수집</th>
                            <th>유형</th>
                            <th>상태</th>
                        </tr>
                    </thead>
                    <tbody>
                        {DATA_SOURCES.map((src, i) => (
                            <React.Fragment key={i}>
                                <tr onClick={() => setDetailIdx(detailIdx === i ? null : i)}
                                    style={{cursor: 'pointer'}}>
                                    <td>{src.name}</td>
                                    <td><code style={{fontSize:'0.72rem',color:'#94a3b8'}}>
                                        {src.db_table || '-'}</code></td>
                                    <td>{getCount(src)}</td>
                                    <td>{getLastTime(src)}</td>
                                    <td>{typeBadge(src.type)}</td>
                                    <td>
                                        <span className="ds-status-dot"
                                            style={{backgroundColor: getStatusColor(src)}}></span>
                                    </td>
                                </tr>
                                {detailIdx === i && (
                                    <tr className="ds-detail-row">
                                        <td colSpan={6}>
                                            {src.api_url && <div>API: <a href={src.api_url}
                                                target="_blank" rel="noopener noreferrer">{src.api_url}</a></div>}
                                            {src.script && <div>Script: <code>{src.script}</code></div>}
                                        </td>
                                    </tr>
                                )}
                            </React.Fragment>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
});
```

### 8.2 idea_board.html용 Vanilla JS 패턴

`idea_board.html`은 React가 아닌 Vanilla JS이므로 별도 구현:

```javascript
function renderDataSourceFooter(containerId) {
    const container = document.getElementById(containerId);
    // DOM 직접 생성하여 같은 테이블 구조 렌더링
    // fetch('/api/v1/collector/status') 호출하여 상태 merge
}
```

### 8.3 구현 순서

| Step | Task | Files | Size |
|------|------|-------|------|
| 1 | collector/status API 확장 (collector 목록 + table_counts) | `backend/app/api/collector.py` | S |
| 2 | liquidity_stress.html에 CSS + DATA_SOURCES + DataSourceFooter 추가 | `dashboard/liquidity_stress.html` | M |
| 3 | crypto_trends.html에 적용 | `dashboard/crypto_trends.html` | S |
| 4 | monitor_disclosures.html에 적용 | `dashboard/monitor_disclosures.html` | S |
| 5 | moat_analysis.html에 적용 | `dashboard/moat_analysis.html` | S |
| 6 | news_intelligence.html에 적용 | `dashboard/news_intelligence.html` | S |
| 7 | idea_board.html에 Vanilla JS 버전 적용 | `dashboard/idea_board.html` | M |
| 8 | E2E 테스트 (서버 기동 → 6개 페이지 Footer 확인) | - | S |

### 8.4 페이지별 DATA_SOURCES 정의

#### liquidity_stress.html
```javascript
const DATA_SOURCES = [
    { name: "FRED (금리/신용)", db_table: "liquidity_macro", collector_key: "liquidity", type: "auto", api_url: "https://fred.stlouisfed.org/", script: "scripts/liquidity_monitor/fred_fetch.py" },
    { name: "Yahoo Finance (가격)", db_table: "liquidity_price", collector_key: "liquidity", type: "auto", api_url: "https://finance.yahoo.com/", script: "scripts/liquidity_monitor/price_fetch.py" },
    { name: "Google News (뉴스)", db_table: "liquidity_news", collector_key: "liquidity", type: "auto", api_url: "https://news.google.com/", script: "scripts/liquidity_monitor/news_fetch.py" },
    { name: "Fed Speech (연준 발언)", db_table: "fed_tone", collector_key: "liquidity", type: "auto", api_url: "https://www.federalreserve.gov/", script: "scripts/liquidity_monitor/fed_speech_fetch.py" },
    { name: "Stress Calculator", db_table: "stress_index", collector_key: "liquidity", type: "auto", script: "scripts/liquidity_monitor/stress_calculator.py" },
];
```

#### crypto_trends.html
```javascript
const DATA_SOURCES = [
    { name: "CoinGecko (Top 20)", db_table: "crypto_price", collector_key: "crypto", type: "auto", api_url: "https://www.coingecko.com/", script: "scripts/crypto_monitor/coingecko_fetch.py" },
    { name: "DefiLlama (TVL)", db_table: "crypto_defi", collector_key: "crypto", type: "auto", api_url: "https://defillama.com/", script: "scripts/crypto_monitor/defi_fetch.py" },
    { name: "Fear & Greed Index", db_table: "crypto_sentiment", collector_key: "crypto", type: "auto", api_url: "https://alternative.me/crypto/fear-and-greed-index/", script: "scripts/crypto_monitor/fear_greed_fetch.py" },
    { name: "ETH ETF Flow", db_table: null, collector_key: null, type: "manual", api_url: "https://coinmarketcap.com/etf/ethereum/" },
    { name: "MVRV Z-Score", db_table: null, collector_key: null, type: "manual", api_url: "https://bitcoinmagazinepro.com/" },
];
```

#### monitor_disclosures.html
```javascript
const DATA_SOURCES = [
    { name: "DART 공시 API", db_table: "disclosures", collector_key: null, type: "on-demand", api_url: "https://opendart.fss.or.kr/", script: "scripts/dart_client.py" },
    { name: "DART 재무 API", db_table: null, collector_key: null, type: "on-demand", api_url: "https://opendart.fss.or.kr/" },
];
```

#### moat_analysis.html
```javascript
const DATA_SOURCES = [
    { name: "DART 연간재무", db_table: null, collector_key: null, type: "on-demand", api_url: "https://opendart.fss.or.kr/", script: "scripts/dart_client.py" },
    { name: "Oracle DB (TTM)", db_table: null, collector_key: null, type: "on-demand", script: "scripts/moat_analysis/oracle_client.py" },
    { name: "해자 분석 결과", db_table: "moat_evaluations", collector_key: null, type: "on-demand", script: "scripts/moat_analysis/analyze_with_evidence.py" },
];
```

#### news_intelligence.html
```javascript
const DATA_SOURCES = [
    { name: "Naver Blog 수집", db_table: "naver_blog_data", collector_key: "news", type: "auto", api_url: "https://blog.naver.com/", script: "scripts/naver_blog_collector.py" },
    { name: "뉴스 분석 결과", db_table: "news_analysis", collector_key: "news", type: "auto", script: "scripts/naver_blog_scheduler.py" },
];
```

#### idea_board.html
```javascript
const DATA_SOURCES = [
    { name: "Daily Work (Excel)", db_table: "daily_work", collector_key: null, type: "manual", script: "scripts/idea_pipeline/ingest.py" },
    { name: "AI Insights", db_table: "insights", collector_key: null, type: "on-demand" },
    { name: "Investment Ideas", db_table: "ideas", collector_key: null, type: "manual" },
    { name: "Sector Momentum", db_table: null, collector_key: null, type: "on-demand", script: "scripts/idea_pipeline/sector_momentum.py" },
    { name: "Market Events", db_table: null, collector_key: null, type: "static", api_url: null, script: "data/market_events.json" },
];
```

---

## 9. Test Plan

### 9.1 Test Scope

| Type | Target | Method |
|------|--------|--------|
| API Test | collector/status 확장 응답 | curl + 브라우저 |
| UI Test | 6개 페이지 Footer 렌더링 | 브라우저 수동 확인 |
| Error Test | API 다운 시 Footer 동작 | 서버 중지 후 페이지 로드 |

### 9.2 Test Cases

- [ ] collector/status API가 `table_counts` 포함하여 응답
- [ ] liquidity_stress.html Footer 접기/펼치기 동작
- [ ] 상태 색상이 시간 경과에 따라 정확히 변경
- [ ] 수동 입력 소스에 "수동" 배지 표시
- [ ] API 실패 시에도 Footer 렌더링 (정적 메타만 표시)
- [ ] idea_board.html (Vanilla JS) Footer 정상 렌더링

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-19 | Initial draft | Claude + User |
