# Design: Disclosure Monitoring & Insight System

> PDCA Phase: Design
> Feature: disclosure-monitoring
> Created: 2026-02-14
> Source: Gemini Architect design_document.md (original)

---

## 1. System Architecture

**Pipeline**: Collector → Analyzer → JSON → Frontend

```
[KIND 공시] → collect_disclosures.py → data/disclosures/YYYY-MM-DD.json
                                            ↓
                              analyze_disclosures.py
                                            ↓
                              dashboard/data/latest_disclosures.json
                                            ↓
                              monitor_disclosures.html (React CDN)
```

## 2. Component Design

### 2.1 Collector (`scripts/collect_disclosures.py`)
- **Source**: KIND Today's Disclosure (`todaydisclosure.do`)
- **Strategy**: `requests.post` with proper headers (User-Agent, Referer)
- **Fallback**: Excel download URL pattern
- **Output**: `data/disclosures/YYYY-MM-DD.json`
- **Fields**: `company`, `code`, `title`, `time`, `market`, `url`

### 2.2 Analyzer (`scripts/analyze_disclosures.py`)
- **Input**: `data/disclosures/YYYY-MM-DD.json`
- **Output**: `dashboard/data/latest_disclosures.json`
- **Logic**: Event Taxonomy → Sentiment Classification → Impact Score

### 2.3 Frontend (`dashboard/monitor_disclosures.html`)
- **Tech**: React 18 CDN + Babel (matches `dashboard/index.html`)
- **Components**: SentimentBanner, KPICards, DisclosureFeed

## 3. Event Taxonomy

### 3.1 Classification Rules

| Category | Keywords | Sentiment |
|----------|----------|-----------|
| Risk-On | 단일판매공급계약, 자기주식취득, 현금배당, 무상증자 | Positive |
| Risk-Off | 유상증자, 전환사채, 신주인수권부사채, 매매거래정지, 불성실공시, 소송 | Negative |
| Neutral | 임원소유상황보고, 대량보유상황보고, 단순투자 | Neutral |

### 3.2 Scoring Logic (-10 to +10)

| Event Type | Score Range | Factors |
|------------|-------------|---------|
| Supply Contract | +2 to +5 | Amount > 10% Revenue → higher |
| Buyback / Cancel | +3 to +6 | Cancellation → higher |
| Earnings Surprise | +3 to +7 | Positive turnover |
| CB / BW Issuance | -2 to -5 | Dilution |
| Rights Offering | -5 to -8 | General Public → worse |
| Suspension | -10 | Critical Risk |

## 4. Data Schema

### 4.1 Raw Disclosure (`data/disclosures/YYYY-MM-DD.json`)
```json
[{
  "company": "삼성전자",
  "code": "005930",
  "title": "단일판매·공급계약체결",
  "time": "16:30",
  "market": "유가증권시장",
  "url": "https://kind.krx.co.kr/..."
}]
```

### 4.2 Processed Disclosure (`dashboard/data/latest_disclosures.json`)
```json
{
  "date": "2026-02-14",
  "summary": {
    "total": 150,
    "risk_on": 42,
    "risk_off": 58,
    "neutral": 50,
    "sentiment_label": "주의",
    "daily_score": -3.2,
    "dilution_total": 15400000000,
    "buyback_total": 8200000000,
    "cluster_alerts": ["반도체 3사 CB 발행"]
  },
  "disclosures": [{
    "company": "삼성전자",
    "code": "005930",
    "title": "단일판매·공급계약체결",
    "time": "16:30",
    "market": "유가증권시장",
    "event_class": "supply_contract",
    "sentiment": "positive",
    "impact_score": 4,
    "badge": "공급계약",
    "detail": "계약금액: 1.5조원 (매출 25%)",
    "url": "https://kind.krx.co.kr/..."
  }]
}
```

## 5. UI Design

### 5.1 Page Structure
1. **Header**: Stock Research ONE 로고 + "← 메인 대시보드" 버튼
2. **Sentiment Banner**: 일일 시장 심리 요약
3. **KPI Cards**: Dilution Index, Return Index, Cluster Alert
4. **Disclosure Feed**: 색상 코딩된 공시 카드 목록

### 5.2 Color Coding
- **Positive (Risk-On)**: Green border (`#22c55e`)
- **Negative (Risk-Off)**: Red border (`#ef4444`)
- **Neutral**: Gray border (`#64748b`)

### 5.3 Main Dashboard Integration
- `dashboard/index.html` → `header-actions`에 "공시 모니터링" 버튼 추가
- 스타일: green border + green text

## 6. File Structure
```
scripts/
  collect_disclosures.py     # KIND 공시 수집
  analyze_disclosures.py     # 이벤트 분류 + 점수
data/
  disclosures/
    YYYY-MM-DD.json          # 일별 원본 데이터
dashboard/
  data/
    latest_disclosures.json  # 분석된 최신 데이터
  monitor_disclosures.html   # 공시 모니터 페이지
  index.html                 # (수정) 버튼 추가
```
