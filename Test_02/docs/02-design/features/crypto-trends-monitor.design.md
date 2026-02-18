# Feature Design: Crypto Trends Monitor (크립토 동향 모니터)

## 1. Data Architecture

### 1.1 MVP (Phase 1): 외부 API 직접 호출 + localStorage
MVP에서는 Backend DB 없이, 프론트엔드에서 직접 외부 API를 호출하고
수동 입력값은 localStorage에 저장한다.

### 1.2 데이터 소스 매핑

| 지표 | 소스 | 방식 | 갱신 |
|------|------|------|------|
| Total Market Cap | CoinGecko `/api/v3/global` | 자동 API | 페이지 로드 시 |
| 24h Volume | CoinGecko `/api/v3/global` | 자동 API | 페이지 로드 시 |
| BTC Dominance | CoinGecko `/api/v3/global` | 자동 API | 페이지 로드 시 |
| ETH Dominance | CoinGecko `/api/v3/global` | 자동 API | 페이지 로드 시 |
| ETH/BTC | CoinGecko `/api/v3/simple/price?ids=ethereum&vs_currencies=btc` | 자동 API | 페이지 로드 시 |
| Fear & Greed | `api.alternative.me/fng/?limit=2` | 자동 API | 페이지 로드 시 |
| Stablecoin Supply | DefiLlama `/stablecoins` | 자동 API | 페이지 로드 시 |
| Stablecoin by Chain | DefiLlama `/stablecoins/chains` (응답 내 체인별 데이터) | 자동 API | 페이지 로드 시 |
| ETH ETF Net Flow | 수동 입력 | localStorage | 사용자 업데이트 |
| MVRV Z-Score | 수동 입력 | localStorage | 사용자 업데이트 |

### 1.3 CoinGecko API Response 구조 (`/api/v3/global`)
```json
{
  "data": {
    "total_market_cap": { "usd": 2800000000000 },
    "total_volume": { "usd": 85000000000 },
    "market_cap_percentage": { "btc": 58.5, "eth": 12.3 },
    "market_cap_change_percentage_24h_usd": -1.2,
    "updated_at": 1739500000
  }
}
```

### 1.4 DefiLlama API Response 구조 (`/stablecoins`)
```json
{
  "peggedAssets": [...],
  "chains": [
    { "name": "Ethereum", "totalCirculatingUSD": { "peggedUSD": 80000000000 } },
    { "name": "Tron", "totalCirculatingUSD": { "peggedUSD": 58000000000 } },
    ...
  ]
}
```

### 1.5 Fear & Greed API (`api.alternative.me/fng/?limit=2`)
```json
{
  "data": [
    { "value": "52", "value_classification": "Neutral", "timestamp": "1739500000" },
    { "value": "48", "value_classification": "Fear", "timestamp": "1739413600" }
  ]
}
```

## 2. 중요도 자동 산정 엔진 (Trigger Engine)

### 2.1 카드별 트리거 규칙

#### Card A: Crypto Overview
```javascript
const triggersA = {
  mktCapChange: Math.abs(mktCap24hChangePct) >= 3,      // ±3%
  volumeSpike: volume24h / volume7dAvg >= 1.5,           // 1.5배
  btcDomShift: Math.abs(btcDom7dDelta) >= 0.7,           // ±0.7pp
};
// 충족 0 → LOW, 1 → MID, 2+ → HIGH
```

#### Card B: Ethereum ETF (수동 입력 기반)
```javascript
const triggersB = {
  flowConsistency: consecutiveSameDirection >= 4,         // 5일 중 4일
  flowMagnitude: Math.abs(flow1d) >= flowP90,             // 상위 10%
  decoupling: (flow1d > 0 && ethBtc7dDelta < 0)          // 유입인데 ETH/BTC 약세
              || (flow1d < 0 && ethBtc7dDelta > 0),
};
```

#### Card C: MVRV Z-Score (수동 입력 기반)
```javascript
const thresholds = [0, 1, 3, 5, 7];
const triggersC = {
  regimeChange: thresholds.some(t =>
    (prevZScore < t && currentZScore >= t) ||
    (prevZScore >= t && currentZScore < t)
  ),
};
// 레짐 전환 시 무조건 HIGH, 아니면 LOW
```

#### Card D: Stablecoin (자동 API 기반)
```javascript
const triggersD = {
  supplyGrowth: stablecoin7dChangePct >= supplyGrowthP80, // 상위 20%
  chainRotation: Math.abs(topChainShareDelta7d) >= 1.0,   // ±1pp
};
```

### 2.2 종합 중요도 라벨
```javascript
function getImportance(triggers) {
  const count = Object.values(triggers).filter(Boolean).length;
  if (count >= 2) return 'HIGH';
  if (count >= 1) return 'MID';
  return 'LOW';
}
```

### 2.3 색상 매핑
| Level | 배지 색상 | 배경 | 점(dot) |
|-------|-----------|------|---------|
| HIGH | `#ef4444` (red) | `rgba(239, 68, 68, 0.15)` | 빨간 점 |
| MID | `#f59e0b` (amber) | `rgba(245, 158, 11, 0.15)` | 노란 점 |
| LOW | `#64748b` (gray) | `rgba(100, 116, 139, 0.15)` | 없음 |

## 3. 레짐 라벨 정의

### 3.1 MVRV Z-Score 레짐
| Z-Score 범위 | 레짐 라벨 | 색상 | 의미 |
|-------------|-----------|------|------|
| < 0 | 극저평가 | `#22c55e` deep green | 역사적 매수 구간 |
| 0 ~ 2 | 축적 | `#4ade80` green | 저평가 축적 |
| 2 ~ 3 | 중립 | `#fbbf24` yellow | 적정 가치 |
| 3 ~ 5 | 과열 초입 | `#f97316` orange | 주의 |
| 5 ~ 7 | 과열 | `#ef4444` red | 차익실현 고려 |
| > 7 | 극단 과열 | `#dc2626` dark red | 사이클 최고 |

### 3.2 Fear & Greed 레짐
| 값 | 라벨 | 색상 |
|-----|------|------|
| 0~24 | Extreme Fear | `#ef4444` |
| 25~44 | Fear | `#f97316` |
| 45~55 | Neutral | `#fbbf24` |
| 56~75 | Greed | `#4ade80` |
| 76~100 | Extreme Greed | `#22c55e` |

## 4. Frontend Page Layout

### 4.1 전체 페이지 구조 (1스크린 완결)
```
+================================================================+
| Header: "Crypto Pulse" [← 대시보드] [🔄 새로고침] [최종 업데이트 시각] |
+================================================================+
|                                                                  |
| [한 줄 결론 배너]                                                  |
| "[추정] ETF 흐름은 중립인데 스테이블코인이 늘어                       |
|  '유동성 기반 리스크온' 가능성"                                      |
|                                                                  |
+------------------------------------------------------------------+
|                    Gauge Bar (7개 계기판)                          |
| ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                     |
| │Mkt Cap │ │Volume  │ │BTC.D   │ │ETH/BTC │                     |
| │$2.8T   │ │$85B    │ │58.5%   │ │0.042   │                     |
| │▼-1.2%  │ │×1.3avg │ │▲+0.5pp │ │▼-2.1%  │                     |
| └────────┘ └────────┘ └────────┘ └────────┘                     |
| ┌────────┐ ┌────────┐ ┌────────┐                                 |
| │ETH ETF │ │MVRV-Z  │ │Stable  │                                 |
| │+$120M  │ │3.2     │ │$182B   │                                 |
| │5D누적▲ │ │과열초입 │ │▲+2.3%  │                                  |
| └────────┘ └────────┘ └────────┘                                 |
+------------------------------------------------------------------+
|                 Source Cards (4개, 2×2 그리드)                     |
| ┌─[HIGH]─ Crypto Overview ──┐ ┌─[MID]── Ethereum ETF ──────┐   |
| │ 변화: ...                  │ │ 변화: ...                    │   |
| │ 의미: ...                  │ │ 의미: ...                    │   |
| │ 행동: ...                  │ │ 행동: ...                    │   |
| │  [🔗 CoinMarketCap →]     │ │  [🔗 CoinMarketCap →]       │   |
| └────────────────────────────┘ └──────────────────────────────┘  |
| ┌─[LOW]── MVRV Z-Score ────┐ ┌─[HIGH]─ Stablecoin ─────────┐   |
| │ 변화: ...                  │ │ 변화: ...                    │   |
| │ 의미: ...                  │ │ 의미: ...                    │   |
| │ 행동: ...                  │ │ 행동: ...                    │   |
| │  [🔗 BitcoinMagazine →]   │ │  [🔗 DefiLlama →]           │   |
| └────────────────────────────┘ └──────────────────────────────┘  |
+------------------------------------------------------------------+
| (선택) 주식 전이 체크                                              |
| □ 크립토 강세 → 주식 전이 조건 충족?                                 |
| 경로: 크립토→나스닥→코스피 | 달러→스테이블→크립토 | ETF→수급           |
+================================================================+
```

### 4.2 상단 Gauge Bar 컴포넌트 상세

각 게이지 카드 구조:
```html
<div class="gauge-card">
  <div class="gauge-label">Total Market Cap</div>
  <div class="gauge-value">$2.8T</div>
  <div class="gauge-delta negative">▼ -1.2% (1D)</div>
  <div class="gauge-delta-sub">7D: +3.4%</div>
</div>
```

게이지 Δ 색상:
- 양수: `#22c55e` (green), `▲` 접두사
- 음수: `#ef4444` (red), `▼` 접두사
- 중립(±0.1% 이내): `#94a3b8` (gray), `━` 접두사

### 4.3 Source Card 컴포넌트 상세

```html
<div class="source-card" data-importance="HIGH">
  <!-- 헤더 -->
  <div class="card-header">
    <span class="importance-badge high">HIGH</span>
    <span class="card-title">Crypto Overview</span>
    <span class="card-subtitle">시장 전체 온도</span>
  </div>

  <!-- 요약 3줄 (고정 포맷) -->
  <div class="card-summary">
    <div class="summary-line observed">
      <span class="tag">[확인]</span>
      Market Cap 1D -3.2%, Volume 7D 평균 대비 1.8배
    </div>
    <div class="summary-line interpreted">
      <span class="tag">[추정]</span>
      거래량 확대와 함께 하락 → 패닉 매도 아닌 리밸런싱 가능성
    </div>
    <div class="summary-line action">
      <span class="tag">[추정]</span>
      ETH ETF 카드와 교차 확인 권장
    </div>
  </div>

  <!-- 핵심 지표 미니 테이블 -->
  <div class="card-metrics">
    <div class="metric">Mkt Cap 1D: <span class="red">-3.2%</span></div>
    <div class="metric">Vol/7D avg: <span class="red">×1.8</span></div>
    <div class="metric">BTC.D 7D: <span class="green">+0.5pp</span></div>
  </div>

  <!-- 외부 링크 -->
  <a href="https://coinmarketcap.com/charts/" target="_blank" rel="noopener"
     class="external-link">
    CoinMarketCap에서 자세히 보기 →
  </a>
</div>
```

### 4.4 수동 입력 컴포넌트 (ETH ETF, MVRV)

API 없는 카드에 포함되는 수동 입력 영역:
```html
<div class="manual-input-area">
  <div class="input-row">
    <label>오늘 Net Flow ($M)</label>
    <input type="number" id="ethEtfFlow1d" placeholder="+120" />
  </div>
  <div class="input-row">
    <label>5D 연속 방향</label>
    <select id="ethEtfDirection">
      <option value="inflow">유입 (4일+)</option>
      <option value="outflow">유출 (4일+)</option>
      <option value="mixed">혼합</option>
    </select>
  </div>
  <button onclick="saveManualData('ethEtf')">저장</button>
  <span class="last-saved">최종 저장: 2026-02-14 09:30</span>
</div>
```

localStorage 키 구조:
```javascript
// 저장
localStorage.setItem('crypto_manual_ethEtf', JSON.stringify({
  flow1d: 120,
  flow5d: 340,
  direction: 'inflow',
  updatedAt: '2026-02-14T09:30:00'
}));

localStorage.setItem('crypto_manual_mvrv', JSON.stringify({
  zScore: 3.2,
  prevZScore: 2.8,
  regime: 'overheating_early',
  updatedAt: '2026-02-14T09:30:00'
}));
```

## 5. dashboard/index.html 수정 설계

### 5.1 시장 모니터링 섹션에 3번째 링크 추가

기존 "유동성 및 신용 스트레스" 블록(line 899~933) 아래에 추가:

```jsx
<a href="crypto_trends.html" style={{...linkStyle}}
   onMouseOver={(e) => {
     e.currentTarget.style.borderColor = '#a855f7';  // purple
     e.currentTarget.style.background = 'rgba(168, 85, 247, 0.1)';
   }}
   onMouseOut={(e) => {
     e.currentTarget.style.borderColor = '#334155';
     e.currentTarget.style.background = 'rgba(30, 41, 59, 0.5)';
   }}>
  <div style={{...iconStyle, background: 'rgba(168, 85, 247, 0.15)', color: '#a855f7'}}>
    <i data-lucide="bitcoin" style={{ width: 18, height: 18 }}></i>
  </div>
  <div style={{ flex: 1 }}>
    <div style={{ fontSize: '0.875rem', fontWeight: '600', color: '#f8fafc' }}>
      크립토 동향
    </div>
    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
      유동성/ETF/온체인 레짐
    </div>
  </div>
  {/* 중요도 배지 (향후 API 연동 시) */}
  <i data-lucide="chevron-right" style={{ width: 16, height: 16, color: '#64748b' }}></i>
</a>
```

### 5.2 색상 테마: Purple (#a855f7)
- 공시 모니터: Green (#22c55e)
- 유동성 스트레스: Orange (#f97316)
- **크립토 동향: Purple (#a855f7)** ← 구분되는 새 색상

## 6. 요약 생성 로직 (템플릿 기반)

### 6.1 Card A: Crypto Overview
```javascript
function generateSummaryA(data) {
  const { mktCapChange1d, volume24h, volume7dAvg, btcDom, btcDom7dDelta } = data;
  const volRatio = (volume24h / volume7dAvg).toFixed(1);

  const observed = `Market Cap 1D ${formatDelta(mktCapChange1d)}%, ` +
                   `Volume 7D 평균 대비 ×${volRatio}`;

  let interpreted = '';
  if (mktCapChange1d < -3 && volRatio > 1.5) {
    interpreted = '거래량 확대와 함께 하락 → 패닉 매도 또는 대규모 리밸런싱';
  } else if (mktCapChange1d > 3 && volRatio > 1.5) {
    interpreted = '거래량 동반 상승 → 위험선호 강화, 주식 전이 가능성 체크';
  } else if (Math.abs(btcDom7dDelta) > 0.7) {
    interpreted = `BTC 도미넌스 ${formatDelta(btcDom7dDelta)}pp → ` +
                  (btcDom7dDelta > 0 ? '알트 약세, BTC 쏠림' : '알트 시즌 초입 가능');
  } else {
    interpreted = '주요 지표 변동 범위 내, 특이사항 없음';
  }

  let action = '';
  const triggerCount = countTriggers(data);
  if (triggerCount >= 2) {
    action = '상세 확인 필요 → 클릭하여 차트 검증 권장';
  } else if (triggerCount === 1) {
    action = '참고 수준, 다른 카드와 교차 확인';
  } else {
    action = '대기, 특별 확인 불필요';
  }

  return { observed, interpreted, action };
}
```

### 6.2 Card B: Ethereum ETF
```javascript
function generateSummaryB(manual) {
  const { flow1d, flow5d, direction } = manual;

  const observed = `ETH ETF 1D ${flow1d > 0 ? '+' : ''}$${flow1d}M, ` +
                   `5D 누적 ${flow5d > 0 ? '+' : ''}$${flow5d}M (${direction})`;

  let interpreted = '';
  if (direction === 'inflow' && flow1d > 0) {
    interpreted = '기관 수급 지속 유입 → ETH 수요 기반 확보';
  } else if (direction === 'outflow') {
    interpreted = '기관 이탈 지속 → ETH 약세 압력, 주식 전이 제한적';
  } else {
    interpreted = '방향성 불명확, 추가 관찰 필요';
  }

  const action = direction === 'inflow'
    ? 'ETF 상세 구성 확인 → 어떤 ETF에 집중되는지 클릭 확인'
    : '대기, ETF 흐름 안정화 후 재확인';

  return { observed, interpreted, action };
}
```

### 6.3 Card C: MVRV Z-Score
```javascript
function generateSummaryC(manual) {
  const { zScore, prevZScore, regime } = manual;
  const regimeLabels = {
    deep_undervalued: '극저평가', accumulation: '축적', neutral: '중립',
    overheating_early: '과열 초입', overheating: '과열', extreme: '극단 과열'
  };

  const observed = `MVRV Z-Score: ${zScore} (${regimeLabels[regime]})`;

  const thresholds = [0, 1, 3, 5, 7];
  const crossed = thresholds.find(t =>
    (prevZScore < t && zScore >= t) || (prevZScore >= t && zScore < t)
  );

  let interpreted = '';
  if (crossed !== undefined) {
    interpreted = `임계대 ${crossed} 돌파 → 사이클 레짐 전환 신호!`;
  } else if (zScore > 5) {
    interpreted = '과열 구간 지속 → 차익실현 타이밍 모니터링';
  } else if (zScore < 1) {
    interpreted = '저평가 구간 → 장기 매수 관점 유효';
  } else {
    interpreted = '레짐 변화 없음, 현 구간 유지';
  }

  const action = crossed !== undefined
    ? '즉시 클릭 → 차트에서 돌파 패턴 확인 필수'
    : '정기 체크 수준, 긴급 확인 불필요';

  return { observed, interpreted, action };
}
```

### 6.4 Card D: Stablecoin
```javascript
function generateSummaryD(data) {
  const { totalSupply, totalSupply7dAgo, topChainDelta } = data;
  const supplyChangePct = ((totalSupply - totalSupply7dAgo) / totalSupply7dAgo * 100).toFixed(1);

  const observed = `스테이블 총량 7D ${formatDelta(supplyChangePct)}%, ` +
                   `${topChainDelta.chain} ${formatDelta(topChainDelta.deltaPp)}pp`;

  let interpreted = '';
  if (supplyChangePct > 1) {
    interpreted = `달러 유동성 증가 → '${topChainDelta.chain}' 체인으로 자금 이동`;
  } else if (supplyChangePct < -1) {
    interpreted = '달러 유동성 감소 → 리스크오프 환경, 주식 전이 약화';
  } else {
    interpreted = '유동성 변화 미미, 체인 로테이션만 관찰';
  }

  const action = Math.abs(supplyChangePct) > 2 || Math.abs(topChainDelta.deltaPp) > 1
    ? 'DefiLlama 상세 확인 → 체인별 분포 변화 검증'
    : '대기, 큰 변화 없음';

  return { observed, interpreted, action };
}
```

### 6.5 한 줄 결론 생성
```javascript
function generateOneLiner(cardResults) {
  const highCards = cardResults.filter(c => c.importance === 'HIGH');
  const midCards = cardResults.filter(c => c.importance === 'MID');

  if (highCards.length === 0 && midCards.length === 0) {
    return '[추정] 크립토 시장 특이사항 없음. 정기 모니터링 수준.';
  }

  // 가장 높은 중요도 카드의 해석을 중심으로 결론 구성
  const primary = highCards[0] || midCards[0];
  return `[추정] ${primary.interpreted} → ${primary.action}`;
}
```

## 7. File Structure (MVP)

```
dashboard/
├── index.html                  # 수정: 시장 모니터링에 "크립토 동향" 링크 추가
├── crypto_trends.html          # 신규: 크립토 동향 모니터 페이지
├── monitor_disclosures.html    # 기존
├── liquidity_stress.html       # 기존 (구현 중)
```

Phase 2 추가:
```
backend/app/
├── api/crypto_trends.py        # 프록시/캐시 API (CORS 우회용)
├── services/crypto_service.py  # CoinGecko/DefiLlama 캐시 서비스

scripts/crypto_monitor/
├── fetch_coingecko.py          # CoinGecko 수집 (7D 히스토리)
├── fetch_defillama.py          # DefiLlama 수집
├── fetch_fear_greed.py         # Fear & Greed 수집
```

## 8. CSS Design Tokens

기존 monitor_disclosures.html 패턴을 따르되, 크립토 전용 색상 추가:

```css
/* 크립토 동향 전용 */
:root {
  /* 기본 테마 (기존 대시보드 동일) */
  --bg-primary: #0a0a0a;
  --bg-card: rgba(15, 23, 42, 0.8);
  --border-default: #334155;
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;

  /* 크립토 테마 색상: Purple */
  --crypto-accent: #a855f7;
  --crypto-accent-bg: rgba(168, 85, 247, 0.15);
  --crypto-accent-border: rgba(168, 85, 247, 0.3);

  /* 중요도 */
  --importance-high: #ef4444;
  --importance-high-bg: rgba(239, 68, 68, 0.15);
  --importance-mid: #f59e0b;
  --importance-mid-bg: rgba(245, 158, 11, 0.15);
  --importance-low: #64748b;
  --importance-low-bg: rgba(100, 116, 139, 0.15);

  /* 방향 */
  --delta-up: #22c55e;
  --delta-down: #ef4444;
  --delta-flat: #94a3b8;
}
```

## 9. 반응형 레이아웃

```css
/* Gauge Bar: 7개 → 모바일에서 줄바꿈 */
.gauge-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 0.75rem;
}

/* Source Cards: 2×2 그리드 → 모바일 1열 */
.source-cards-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

@media (max-width: 768px) {
  .source-cards-grid {
    grid-template-columns: 1fr;
  }
}
```

## 10. 외부 API 호출 전략

### 10.1 CORS 이슈 대응
- CoinGecko: CORS 허용 (프론트에서 직접 호출 가능)
- DefiLlama: CORS 허용 (프론트에서 직접 호출 가능)
- alternative.me: CORS 허용 (프론트에서 직접 호출 가능)

### 10.2 Rate Limit 대응
```javascript
const API_CONFIG = {
  coingecko: {
    baseUrl: 'https://api.coingecko.com/api/v3',
    rateLimit: 30,       // calls/min (free tier)
    cacheDuration: 300,  // 5분 캐시
  },
  defillama: {
    baseUrl: 'https://stablecoins.llama.fi',
    rateLimit: null,     // 무제한
    cacheDuration: 600,  // 10분 캐시
  },
  fearGreed: {
    baseUrl: 'https://api.alternative.me/fng',
    rateLimit: null,
    cacheDuration: 3600, // 1시간 캐시
  }
};
```

### 10.3 캐시 전략 (sessionStorage)
```javascript
async function fetchWithCache(key, fetchFn, duration) {
  const cached = sessionStorage.getItem(key);
  if (cached) {
    const { data, timestamp } = JSON.parse(cached);
    if (Date.now() - timestamp < duration * 1000) return data;
  }
  const data = await fetchFn();
  sessionStorage.setItem(key, JSON.stringify({ data, timestamp: Date.now() }));
  return data;
}
```

## 11. Implementation Order

| 순서 | 작업 | 예상 규모 |
|------|------|-----------|
| 1 | `dashboard/index.html` — 시장 모니터링에 "크립토 동향" 링크 추가 | 소 |
| 2 | `dashboard/crypto_trends.html` — 기본 레이아웃 + CSS | 대 |
| 3 | 외부 API 연동 (CoinGecko, DefiLlama, Fear&Greed) | 중 |
| 4 | 수동 입력 UI (ETH ETF, MVRV) + localStorage | 중 |
| 5 | 트리거 엔진 + 중요도 자동 산정 | 중 |
| 6 | 요약 생성 로직 (템플릿 기반) | 중 |
| 7 | 한 줄 결론 + 주식 전이 체크 (선택) | 소 |

## 12. 성공 기준 (Design 관점)

| # | 기준 | 검증 방법 |
|---|------|-----------|
| DC-1 | 1스크린에 게이지 7개 + 카드 4개 모두 표시 (1920×1080) | 스크린샷 |
| DC-2 | 각 카드에 중요도 배지 (HIGH/MID/LOW) 표시 | 목시 확인 |
| DC-3 | 4개 외부 링크 새 창 열기 정상 | 클릭 테스트 |
| DC-4 | CoinGecko + DefiLlama API 데이터 정상 표시 | API 호출 로그 |
| DC-5 | 수동 입력 → localStorage 저장/복원 | 새로고침 테스트 |
| DC-6 | 요약 3줄 포맷 ([확인]/[추정]/[추정]) 일관 적용 | 육안 확인 |
| DC-7 | 기존 dashboard 스타일과 시각적 일관성 | 비교 스크린샷 |