import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { ExternalLink, RefreshCw } from 'lucide-react';
import './CryptoTrends.css';

// ============================================
// API Configuration
// ============================================
const API = {
    coingecko: {
        global: 'https://api.coingecko.com/api/v3/global',
        ethBtc: 'https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=btc,usd',
        cacheDuration: 300,
    },
    defillama: {
        stablecoins: 'https://stablecoins.llama.fi/stablecoins?includePrices=false',
        stablecoinChains: 'https://stablecoins.llama.fi/stablecoinchains',
        cacheDuration: 600,
    },
    fearGreed: {
        url: 'https://api.alternative.me/fng/?limit=2',
        cacheDuration: 3600,
    }
};

// ============================================
// Utility Functions
// ============================================
function formatNum(n, decimals = 1) {
    if (n == null || isNaN(n)) return '-';
    if (Math.abs(n) >= 1e12) return (n / 1e12).toFixed(decimals) + 'T';
    if (Math.abs(n) >= 1e9) return (n / 1e9).toFixed(decimals) + 'B';
    if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(decimals) + 'M';
    return n.toLocaleString(undefined, { maximumFractionDigits: decimals });
}

function formatDelta(val, suffix = '%') {
    if (val == null || isNaN(val)) return '-';
    const sign = val > 0 ? '+' : '';
    return sign + val.toFixed(1) + suffix;
}

function deltaClass(val) {
    if (val == null) return 'delta-flat';
    if (val > 0.1) return 'delta-up';
    if (val < -0.1) return 'delta-down';
    return 'delta-flat';
}

function deltaArrow(val) {
    if (val == null) return '';
    if (val > 0.1) return '\u25B2 ';
    if (val < -0.1) return '\u25BC ';
    return '\u2501 ';
}

// Cache helpers
async function fetchWithCache(key, fetchFn, durationSec) {
    try {
        const cached = sessionStorage.getItem(key);
        if (cached) {
            const { data, ts } = JSON.parse(cached);
            if (Date.now() - ts < durationSec * 1000) return data;
        }
    } catch (e) { /* ignore parse errors */ }
    const data = await fetchFn();
    try {
        sessionStorage.setItem(key, JSON.stringify({ data, ts: Date.now() }));
    } catch (e) { /* ignore quota errors */ }
    return data;
}

// localStorage manual data
function loadManual(key) {
    try {
        const raw = localStorage.getItem('crypto_manual_' + key);
        return raw ? JSON.parse(raw) : null;
    } catch { return null; }
}

function saveManual(key, data) {
    data.updatedAt = new Date().toISOString();
    localStorage.setItem('crypto_manual_' + key, JSON.stringify(data));
}

// ============================================
// Data Fetching
// ============================================
async function fetchCoinGeckoGlobal() {
    return fetchWithCache('cg_global', async () => {
        const res = await fetch(API.coingecko.global);
        if (!res.ok) throw new Error('CoinGecko API error');
        const json = await res.json();
        return json.data;
    }, API.coingecko.cacheDuration);
}

async function fetchEthBtc() {
    return fetchWithCache('cg_ethbtc', async () => {
        const res = await fetch(API.coingecko.ethBtc);
        if (!res.ok) throw new Error('CoinGecko ETH/BTC error');
        return res.json();
    }, API.coingecko.cacheDuration);
}

async function fetchFearGreed() {
    return fetchWithCache('fg_index', async () => {
        const res = await fetch(API.fearGreed.url);
        if (!res.ok) throw new Error('Fear & Greed API error');
        return res.json();
    }, API.fearGreed.cacheDuration);
}

async function fetchStablecoins() {
    return fetchWithCache('dl_stablecoins', async () => {
        const res = await fetch(API.defillama.stablecoins);
        if (!res.ok) throw new Error('DefiLlama stablecoins error');
        return res.json();
    }, API.defillama.cacheDuration);
}

async function fetchStablecoinChains() {
    return fetchWithCache('dl_stablechain', async () => {
        const res = await fetch(API.defillama.stablecoinChains);
        if (!res.ok) throw new Error('DefiLlama chains error');
        return res.json();
    }, API.defillama.cacheDuration);
}

// ============================================
// Trigger Engine
// ============================================
function calcTriggersA(mktCapChange1d, volRatio, btcDom7dDelta) {
    return {
        mktCapBig: Math.abs(mktCapChange1d || 0) >= 3,
        volumeSpike: (volRatio || 0) >= 1.5,
        domShift: Math.abs(btcDom7dDelta || 0) >= 0.7,
    };
}

function calcTriggersB(manual) {
    if (!manual) return {};
    return {
        flowConsistency: manual.direction === 'inflow' || manual.direction === 'outflow',
        flowMagnitude: Math.abs(manual.flow1d || 0) >= (manual.flowThreshold || 100),
        decoupling: manual.decoupling || false,
    };
}

function calcTriggersC(manual) {
    if (!manual) return {};
    const thresholds = [0, 1, 3, 5, 7];
    const crossed = thresholds.some(t =>
        (manual.prevZScore < t && manual.zScore >= t) ||
        (manual.prevZScore >= t && manual.zScore < t)
    );
    return { regimeChange: crossed };
}

function calcTriggersD(supplyChangePct, chainRotationPp) {
    return {
        supplyGrowth: Math.abs(supplyChangePct || 0) >= 1.5,
        chainRotation: Math.abs(chainRotationPp || 0) >= 1.0,
    };
}

function getImportance(triggers) {
    if (triggers.regimeChange) return 'HIGH';
    const count = Object.values(triggers).filter(Boolean).length;
    if (count >= 2) return 'HIGH';
    if (count >= 1) return 'MID';
    return 'LOW';
}

// ============================================
// Summary Generation
// ============================================
function genSummaryA(data) {
    if (!data) return { observed: '데이터 로딩 중...', interpreted: '-', action: '-' };
    const mc = data.mktCapChange1d;
    const vr = data.volRatio;
    const bd = data.btcDom7dDelta;

    const observed = `Market Cap 1D ${formatDelta(mc)}, Volume/7D avg \u00D7${(vr || 0).toFixed(1)}, BTC.D 7D ${formatDelta(bd, 'pp')}`;

    let interpreted;
    if (mc < -3 && vr > 1.5) interpreted = '거래량 확대 + 하락 → 패닉 매도 또는 리밸런싱';
    else if (mc > 3 && vr > 1.5) interpreted = '거래량 동반 상승 → 위험선호 강화, 주식 전이 체크';
    else if (Math.abs(bd) > 0.7) interpreted = `BTC 도미넌스 ${formatDelta(bd, 'pp')} → ${bd > 0 ? '알트 약세, BTC 쏠림' : '알트 시즌 초입 가능'}`;
    else interpreted = '주요 지표 변동 범위 내, 특이사항 없음';

    const tc = Object.values(calcTriggersA(mc, vr, bd)).filter(Boolean).length;
    const action = tc >= 2 ? '상세 확인 필요 → 클릭하여 차트 검증 권장'
        : tc === 1 ? '참고 수준, 다른 카드와 교차 확인'
        : '대기, 특별 확인 불필요';

    return { observed, interpreted, action };
}

function genSummaryB(manual) {
    if (!manual) return {
        observed: '수동 입력 필요 (ETF 데이터 입력 후 저장)',
        interpreted: 'CoinMarketCap에서 확인 후 입력해주세요',
        action: '외부 링크 클릭 → 데이터 확인 후 입력'
    };
    const { flow1d, flow5d, direction } = manual;
    const observed = `ETH ETF 1D ${flow1d > 0 ? '+' : ''}$${flow1d}M, 5D 누적 ${flow5d > 0 ? '+' : ''}$${flow5d}M (${direction === 'inflow' ? '유입' : direction === 'outflow' ? '유출' : '혼합'})`;

    let interpreted;
    if (direction === 'inflow' && flow1d > 0) interpreted = '기관 수급 지속 유입 → ETH 수요 기반 확보';
    else if (direction === 'outflow') interpreted = '기관 이탈 지속 → ETH 약세 압력, 주식 전이 제한적';
    else interpreted = '방향성 불명확, 추가 관찰 필요';

    const action = direction === 'inflow' ? 'ETF 상세 구성 확인 → 어떤 ETF에 집중되는지 클릭' : '대기, ETF 흐름 안정화 후 재확인';
    return { observed, interpreted, action };
}

function genSummaryC(manual) {
    if (!manual) return {
        observed: '수동 입력 필요 (MVRV Z-Score 입력 후 저장)',
        interpreted: 'BitcoinMagazinePro에서 확인 후 입력해주세요',
        action: '외부 링크 클릭 → 데이터 확인 후 입력'
    };
    const regimeLabels = {
        deep_undervalued: '극저평가', accumulation: '축적', neutral: '중립',
        overheating_early: '과열 초입', overheating: '과열', extreme: '극단 과열'
    };
    const observed = `MVRV Z-Score: ${manual.zScore} (${regimeLabels[manual.regime] || manual.regime})`;

    const thresholds = [0, 1, 3, 5, 7];
    const crossed = thresholds.find(t =>
        (manual.prevZScore < t && manual.zScore >= t) || (manual.prevZScore >= t && manual.zScore < t)
    );

    let interpreted;
    if (crossed !== undefined) interpreted = `임계대 ${crossed} 돌파 → 사이클 레짐 전환 신호!`;
    else if (manual.zScore > 5) interpreted = '과열 구간 지속 → 차익실현 타이밍 모니터링';
    else if (manual.zScore < 1) interpreted = '저평가 구간 → 장기 매수 관점 유효';
    else interpreted = '레짐 변화 없음, 현 구간 유지';

    const action = crossed !== undefined
        ? '즉시 클릭 → 차트에서 돌파 패턴 확인 필수'
        : '정기 체크 수준, 긴급 확인 불필요';
    return { observed, interpreted, action };
}

function genSummaryD(data) {
    if (!data) return { observed: '데이터 로딩 중...', interpreted: '-', action: '-' };
    const { supplyChangePct, topChainName, topChainDelta } = data;

    const observed = `스테이블 총량 7D ${formatDelta(supplyChangePct)}, ${topChainName || '-'} ${formatDelta(topChainDelta, 'pp')}`;

    let interpreted;
    if (supplyChangePct > 1) interpreted = `달러 유동성 증가 → '${topChainName}' 체인으로 자금 이동`;
    else if (supplyChangePct < -1) interpreted = '달러 유동성 감소 → 리스크오프 환경, 주식 전이 약화';
    else interpreted = '유동성 변화 미미, 체인 로테이션만 관찰';

    const action = Math.abs(supplyChangePct) > 2 || Math.abs(topChainDelta) > 1
        ? 'DefiLlama 상세 확인 → 체인별 분포 변화 검증'
        : '대기, 큰 변화 없음';
    return { observed, interpreted, action };
}

function genOneLiner(cards) {
    const high = cards.filter(c => c.importance === 'HIGH');
    const mid = cards.filter(c => c.importance === 'MID');
    if (high.length === 0 && mid.length === 0) {
        return { text: '크립토 시장 특이사항 없음. 정기 모니터링 수준.', regime: 'normal' };
    }
    const primary = high[0] || mid[0];
    const regime = high.length >= 2 ? 'critical' : high.length >= 1 ? 'alert' : 'normal';
    return { text: `${primary.summary.interpreted} → ${primary.summary.action}`, regime };
}

// ============================================
// MVRV / Fear&Greed Helpers
// ============================================
function mvrvRegimeColor(regime) {
    const map = {
        deep_undervalued: '#22c55e', accumulation: '#4ade80', neutral: '#fbbf24',
        overheating_early: '#f97316', overheating: '#ef4444', extreme: '#dc2626'
    };
    return map[regime] || '#94a3b8';
}

function mvrvRegimeLabel(regime) {
    const map = {
        deep_undervalued: '극저평가', accumulation: '축적', neutral: '중립',
        overheating_early: '과열초입', overheating: '과열', extreme: '극단'
    };
    return map[regime] || '-';
}

function fgColor(val) {
    if (val <= 24) return '#ef4444';
    if (val <= 44) return '#f97316';
    if (val <= 55) return '#fbbf24';
    if (val <= 75) return '#4ade80';
    return '#22c55e';
}

function fgLabel(val) {
    if (val <= 24) return 'Extreme Fear';
    if (val <= 44) return 'Fear';
    if (val <= 55) return 'Neutral';
    if (val <= 75) return 'Greed';
    return 'Extreme Greed';
}

// ============================================
// Gauge Detail Definitions
// ============================================
const GAUGE_DETAILS = {
    mktCap: {
        title: 'Total Crypto Market Cap',
        subtitle: '전체 암호화폐 시가총액',
        description: '전체 암호화폐 시장의 시가총액 합계입니다. 1D/7D 변화율이 ±3% 이상이면 유의미한 시장 변동으로 봅니다. 시가총액이 상승하면서 거래량도 증가하면 위험선호(Risk-On) 환경, 하락+거래량 감소는 관망, 하락+거래량 급증은 패닉 가능성입니다.',
        refs: [
            { name: 'CoinMarketCap - Global Charts', url: 'https://coinmarketcap.com/charts/' },
            { name: 'CoinGecko - Global Crypto Stats', url: 'https://www.coingecko.com/en/global-charts' },
        ]
    },
    volume: {
        title: '24h Trading Volume',
        subtitle: '24시간 거래량',
        description: '전체 암호화폐의 24시간 거래량입니다. 7일 평균 대비 1.5배 이상이면 비정상적 활동(거래량 스파이크)으로 판단합니다. 가격 상승 + 거래량 증가는 추세 확인, 가격 하락 + 거래량 증가는 패닉 매도 또는 큰 손 리밸런싱 가능성입니다.',
        refs: [
            { name: 'CoinMarketCap - Charts', url: 'https://coinmarketcap.com/charts/' },
            { name: 'CoinGecko - Volume', url: 'https://www.coingecko.com/en/global-charts' },
        ]
    },
    btcDom: {
        title: 'BTC Dominance',
        subtitle: 'BTC 시가총액 점유율',
        description: 'BTC의 전체 암호화폐 시가총액 대비 점유율입니다. 7D 변화가 +0.7pp 이상이면 "BTC로 자금 쏠림(알트 약세)", -0.7pp 이상 하락이면 "알트 시즌 초입 가능"입니다. 도미넌스가 높아지면 BTC 중심 방어적 장세, 낮아지면 위험선호 확산입니다.',
        refs: [
            { name: 'CoinMarketCap - Dominance Chart', url: 'https://coinmarketcap.com/charts/#dominance-percentage' },
            { name: 'TradingView - BTC.D', url: 'https://www.tradingview.com/symbols/BTC.D/' },
        ]
    },
    ethBtc: {
        title: 'ETH/BTC',
        subtitle: 'Ethereum vs Bitcoin 상대 가격',
        description: 'ETH의 BTC 대비 상대 가치입니다. ETH/BTC 상승은 "ETH 주도 장세(DeFi/스마트컨트랙트 부흥)", 하락은 "BTC 주도, 안전자산 선호"를 의미합니다. ETH ETF 유입과 함께 ETH/BTC 상승이면 기관 ETH 선호 신호, 유입인데도 하락이면 디커플링(지연 반영)입니다.',
        refs: [
            { name: 'CoinGecko - ETH/BTC', url: 'https://www.coingecko.com/en/coins/ethereum/btc' },
            { name: 'TradingView - ETHBTC', url: 'https://www.tradingview.com/symbols/ETHBTC/' },
        ]
    },
    ethEtf: {
        title: 'ETH ETF Net Flow',
        subtitle: 'Ethereum ETF 순유입/유출',
        description: 'Ethereum ETF의 일별 순 자금 유출입입니다. 5거래일 중 4일 이상 같은 방향이면 "추세 형성", 1D flow가 최근 20일 상위 10% 규모면 "유의미한 규모"로 판단합니다. 유입 지속인데 ETH/BTC가 약세면 "지연 반영" 또는 "헤지 수요" 가능성입니다.',
        refs: [
            { name: 'CoinMarketCap - Ethereum ETF', url: 'https://coinmarketcap.com/etf/ethereum/' },
            { name: 'Farside Investors - ETH ETF Flows', url: 'https://farside.co.uk/ethereum-etf-flow-all-data/' },
        ]
    },
    mvrv: {
        title: 'MVRV Z-Score',
        subtitle: 'Bitcoin Market Value to Realized Value',
        description: 'BTC의 시장가치(MV) 대 실현가치(RV) 비율을 표준화한 지표입니다 (오태민 관점). Z < 0 = 극저평가(역사적 매수 구간), 0~2 = 축적, 2~3 = 중립, 3~5 = 과열 초입, 5~7 = 과열(차익실현 고려), > 7 = 극단 과열. 임계대(0, 1, 3, 5, 7) 돌파 시 "사이클 레짐 전환 신호"로 무조건 HIGH 중요도입니다.',
        refs: [
            { name: 'Bitcoin Magazine Pro - MVRV Z-Score', url: 'https://www.bitcoinmagazinepro.com/charts/mvrv-zscore/' },
            { name: 'LookIntoBitcoin - MVRV', url: 'https://www.lookintobitcoin.com/charts/mvrv-zscore/' },
        ]
    },
    stablecoin: {
        title: 'Stablecoin Supply',
        subtitle: '스테이블코인 총 공급량',
        description: '전체 스테이블코인(USDT, USDC, DAI 등) 발행량 합계입니다. 7D 증가율이 상위 20%면 "새로운 달러 유동성 유입"으로 위험자산에 긍정적입니다. 체인별 점유율 변화가 1pp 이상이면 "자금 로테이션(예: ETH→SOL, Tron→ETH)" 발생 중입니다.',
        refs: [
            { name: 'DefiLlama - Stablecoins by Chain', url: 'https://defillama.com/stablecoins/chains' },
            { name: 'DefiLlama - Stablecoins Overview', url: 'https://defillama.com/stablecoins' },
        ]
    },
    fearGreed: {
        title: 'Crypto Fear & Greed Index',
        subtitle: '공포 & 탐욕 지수',
        description: 'BTC 변동성, 거래량, SNS 언급, 설문, 도미넌스, 트렌드를 종합한 심리 지표입니다. 0~24 = 극단 공포(역발상 매수 구간), 25~44 = 공포, 45~55 = 중립, 56~75 = 탐욕, 76~100 = 극단 탐욕(주의). 극단 구간에서의 반전이 가장 중요한 시그널입니다.',
        refs: [
            { name: 'Alternative.me - Fear & Greed Index', url: 'https://alternative.me/crypto/fear-and-greed-index/' },
            { name: 'CoinMarketCap - Fear & Greed', url: 'https://coinmarketcap.com/charts/#fear-and-greed-index' },
        ]
    },
};

// ============================================
// GaugeDetailModal Component
// ============================================
const GaugeDetailModal = React.memo(({ gaugeKey, gauges, stableChainInfo, manualEtf, manualMvrv, fgData, onClose }) => {
    const def = GAUGE_DETAILS[gaugeKey];
    if (!def) return null;

    let kpis = [];
    switch (gaugeKey) {
        case 'mktCap':
            kpis = [
                { label: '현재', value: '$' + formatNum(gauges.mktCap), delta: gauges.mktCapChange1d, suffix: '% (1D)' },
                { label: 'BTC 점유율', value: (gauges.btcDom?.toFixed(1) || '-') + '%' },
                { label: 'ETH 점유율', value: (gauges.ethDom?.toFixed(1) || '-') + '%' },
            ];
            break;
        case 'volume':
            kpis = [
                { label: '24h Volume', value: '$' + formatNum(gauges.vol) },
                { label: 'vs 7D 평균', value: '-', note: 'Phase 2에서 자동 계산' },
            ];
            break;
        case 'btcDom':
            kpis = [
                { label: '현재 BTC.D', value: (gauges.btcDom?.toFixed(1) || '-') + '%' },
                { label: 'ETH.D', value: (gauges.ethDom?.toFixed(1) || '-') + '%' },
                { label: '7D \u0394', value: '-', note: 'Phase 2' },
            ];
            break;
        case 'ethBtc':
            kpis = [
                { label: 'ETH/BTC', value: gauges.ethBtc?.toFixed(4) || '-' },
                { label: 'ETH.D', value: (gauges.ethDom?.toFixed(1) || '-') + '%' },
                { label: 'BTC.D', value: (gauges.btcDom?.toFixed(1) || '-') + '%' },
            ];
            break;
        case 'ethEtf':
            kpis = manualEtf ? [
                { label: '1D Flow', value: '$' + manualEtf.flow1d + 'M', delta: manualEtf.flow1d },
                { label: '5D 누적', value: '$' + (manualEtf.flow5d || '?') + 'M', delta: manualEtf.flow5d },
                { label: '5D 방향', value: manualEtf.direction === 'inflow' ? '유입' : manualEtf.direction === 'outflow' ? '유출' : '혼합' },
            ] : [{ label: '상태', value: '수동 입력 필요' }];
            break;
        case 'mvrv':
            kpis = manualMvrv ? [
                { label: 'Z-Score', value: String(manualMvrv.zScore) },
                { label: '레짐', value: mvrvRegimeLabel(manualMvrv.regime) },
                { label: '이전 Z', value: String(manualMvrv.prevZScore) },
            ] : [{ label: '상태', value: '수동 입력 필요' }];
            break;
        case 'stablecoin':
            kpis = [
                { label: '총 공급량', value: '$' + formatNum(gauges.stableTotal) },
                { label: '7D \u0394', value: formatDelta(stableChainInfo.supplyChangePct), delta: stableChainInfo.supplyChangePct },
                { label: 'Top Chain', value: stableChainInfo.topChainName },
            ];
            break;
        case 'fearGreed': {
            const fg = gauges.fg;
            const prev = fgData?.data?.[1] ? Number(fgData.data[1].value) : null;
            kpis = [
                { label: '현재', value: fg != null ? String(fg) : '-', color: fg != null ? fgColor(fg) : null },
                { label: '레짐', value: fg != null ? fgLabel(fg) : '-', color: fg != null ? fgColor(fg) : null },
                { label: '어제', value: prev != null ? String(prev) : '-', color: prev != null ? fgColor(prev) : null },
            ];
            break;
        }
    }

    return (
        <div className="crypto-modal-overlay" onClick={onClose}>
            <div className="crypto-modal-panel" onClick={e => e.stopPropagation()}>
                <div className="crypto-modal-header">
                    <div className="crypto-modal-title-area">
                        <h2>{def.title}</h2>
                        <p>{def.subtitle}</p>
                    </div>
                    <button className="crypto-modal-close" onClick={onClose}>{'\u00D7'}</button>
                </div>
                <div className="crypto-modal-body">
                    <div className="crypto-modal-kpi-grid">
                        {kpis.map((k, i) => (
                            <div key={i} className="crypto-modal-kpi">
                                <div className="crypto-modal-kpi-label">{k.label}</div>
                                <div className="crypto-modal-kpi-value" style={k.color ? { color: k.color } : {}}>
                                    {k.value}
                                </div>
                                {k.delta != null && (
                                    <div className={`crypto-modal-kpi-sub ${deltaClass(k.delta)}`}>
                                        {deltaArrow(k.delta)}{formatDelta(k.delta, k.suffix || '%')}
                                    </div>
                                )}
                                {k.note && <div style={{ fontSize: '0.65rem', color: '#475569', marginTop: '0.15rem' }}>{k.note}</div>}
                            </div>
                        ))}
                    </div>
                    <div className="crypto-modal-desc">{def.description}</div>
                    <div className="crypto-modal-refs">
                        <div className="crypto-modal-refs-title">참조:</div>
                        {def.refs.map((r, i) => (
                            <a key={i} href={r.url} target="_blank" rel="noopener noreferrer" className="crypto-modal-ref-link">
                                <div className="crypto-modal-ref-icon">
                                    <ExternalLink size={12} />
                                </div>
                                {r.name}
                            </a>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
});

// ============================================
// SourceCard Component
// ============================================
const SourceCard = React.memo(({ title, question, importance, summary, metrics, linkUrl, linkLabel, manualInput }) => {
    const badgeCls = importance === 'HIGH' ? 'crypto-badge-high' : importance === 'MID' ? 'crypto-badge-mid' : 'crypto-badge-low';
    const cardCls = `crypto-source-card crypto-importance-${importance.toLowerCase()}`;

    return (
        <div className={cardCls}>
            <div className="crypto-card-header">
                <span className={`crypto-importance-badge ${badgeCls}`}>{importance}</span>
                <span className="crypto-card-title">{title}</span>
            </div>
            <div className="crypto-card-question">{question}</div>

            <div className="crypto-summary-lines">
                <div className="crypto-summary-line">
                    <span className="crypto-summary-tag crypto-tag-observed">확인</span>
                    {summary.observed}
                </div>
                <div className="crypto-summary-line">
                    <span className="crypto-summary-tag crypto-tag-interpreted">추정</span>
                    {summary.interpreted}
                </div>
                <div className="crypto-summary-line">
                    <span className="crypto-summary-tag crypto-tag-action">행동</span>
                    {summary.action}
                </div>
            </div>

            {metrics.length > 0 && (
                <div className="crypto-card-metrics">
                    {metrics.map((m, i) => (
                        <div key={i} className="crypto-metric-item">
                            {m.label}: <span className={m.cls}>{m.value}</span>
                        </div>
                    ))}
                </div>
            )}

            {manualInput}

            <a href={linkUrl} target="_blank" rel="noopener noreferrer" className="crypto-external-link">
                <ExternalLink size={14} />
                {linkLabel} {'\u2192'}
            </a>
        </div>
    );
});

// ============================================
// ManualEtfInput Component
// ============================================
const ManualEtfInput = React.memo(({ initial, onSave }) => {
    const [flow1d, setFlow1d] = useState(initial?.flow1d || '');
    const [flow5d, setFlow5d] = useState(initial?.flow5d || '');
    const [direction, setDirection] = useState(initial?.direction || 'mixed');

    return (
        <div className="crypto-manual-area">
            <div className="crypto-manual-title">수동 입력 (CoinMarketCap 참조)</div>
            <div className="crypto-manual-row">
                <label>1D Flow ($M)</label>
                <input type="number" value={flow1d}
                    onChange={e => setFlow1d(e.target.value)}
                    placeholder="+120" />
            </div>
            <div className="crypto-manual-row">
                <label>5D Flow ($M)</label>
                <input type="number" value={flow5d}
                    onChange={e => setFlow5d(e.target.value)}
                    placeholder="+340" />
            </div>
            <div className="crypto-manual-row">
                <label>5D 방향</label>
                <select value={direction} onChange={e => setDirection(e.target.value)}>
                    <option value="inflow">유입 (4일+)</option>
                    <option value="outflow">유출 (4일+)</option>
                    <option value="mixed">혼합</option>
                </select>
            </div>
            <button className="crypto-manual-save-btn" onClick={() => onSave({
                flow1d: Number(flow1d), flow5d: Number(flow5d), direction
            })}>저장</button>
            {initial?.updatedAt && (
                <div className="crypto-manual-saved">최종: {new Date(initial.updatedAt).toLocaleString('ko-KR')}</div>
            )}
        </div>
    );
});

// ============================================
// ManualMvrvInput Component
// ============================================
const ManualMvrvInput = React.memo(({ initial, onSave }) => {
    const [zScore, setZScore] = useState(initial?.zScore || '');
    const [prevZScore, setPrevZScore] = useState(initial?.prevZScore || '');
    const [regime, setRegime] = useState(initial?.regime || 'neutral');

    return (
        <div className="crypto-manual-area">
            <div className="crypto-manual-title">수동 입력 (BitcoinMagazinePro 참조)</div>
            <div className="crypto-manual-row">
                <label>Z-Score</label>
                <input type="number" step="0.1" value={zScore}
                    onChange={e => setZScore(e.target.value)}
                    placeholder="3.2" />
            </div>
            <div className="crypto-manual-row">
                <label>이전 Z</label>
                <input type="number" step="0.1" value={prevZScore}
                    onChange={e => setPrevZScore(e.target.value)}
                    placeholder="2.8" />
            </div>
            <div className="crypto-manual-row">
                <label>레짐</label>
                <select value={regime} onChange={e => setRegime(e.target.value)}>
                    <option value="deep_undervalued">극저평가 (&lt; 0)</option>
                    <option value="accumulation">축적 (0~2)</option>
                    <option value="neutral">중립 (2~3)</option>
                    <option value="overheating_early">과열초입 (3~5)</option>
                    <option value="overheating">과열 (5~7)</option>
                    <option value="extreme">극단 (&gt; 7)</option>
                </select>
            </div>
            <button className="crypto-manual-save-btn" onClick={() => onSave({
                zScore: Number(zScore), prevZScore: Number(prevZScore), regime
            })}>저장</button>
            {initial?.updatedAt && (
                <div className="crypto-manual-saved">최종: {new Date(initial.updatedAt).toLocaleString('ko-KR')}</div>
            )}
        </div>
    );
});

// ============================================
// Main CryptoTrends Component
// ============================================
const CryptoTrends = () => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [globalData, setGlobalData] = useState(null);
    const [ethBtcData, setEthBtcData] = useState(null);
    const [fgData, setFgData] = useState(null);
    const [stableData, setStableData] = useState(null);
    const [chainData, setChainData] = useState(null);
    const [manualEtf, setManualEtf] = useState(() => loadManual('ethEtf'));
    const [manualMvrv, setManualMvrv] = useState(() => loadManual('mvrv'));
    const [lastUpdate, setLastUpdate] = useState(null);
    const [transferCheck, setTransferCheck] = useState(false);
    const [selectedGauge, setSelectedGauge] = useState(null);

    const loadAll = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [g, eb, fg, sc, sch] = await Promise.allSettled([
                fetchCoinGeckoGlobal(),
                fetchEthBtc(),
                fetchFearGreed(),
                fetchStablecoins(),
                fetchStablecoinChains(),
            ]);
            if (g.status === 'fulfilled') setGlobalData(g.value);
            if (eb.status === 'fulfilled') setEthBtcData(eb.value);
            if (fg.status === 'fulfilled') setFgData(fg.value);
            if (sc.status === 'fulfilled') setStableData(sc.value);
            if (sch.status === 'fulfilled') setChainData(sch.value);

            const anyOk = [g, eb, fg, sc, sch].some(r => r.status === 'fulfilled');
            if (!anyOk) setError('API 연결 실패. 잠시 후 새로고침 해주세요.');
            setLastUpdate(new Date());
        } catch (e) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadAll();
    }, [loadAll]);

    // ---- Derived data ----
    const gauges = useMemo(() => {
        const mktCap = globalData?.total_market_cap?.usd;
        const mktCapChange1d = globalData?.market_cap_change_percentage_24h_usd;
        const vol = globalData?.total_volume?.usd;
        const btcDom = globalData?.market_cap_percentage?.btc;
        const ethDom = globalData?.market_cap_percentage?.eth;
        const ethBtc = ethBtcData?.ethereum?.btc;
        const fg = fgData?.data?.[0] ? Number(fgData.data[0].value) : null;

        let stableTotal = null;
        let stableTotal7dAgo = null;
        if (stableData?.peggedAssets) {
            stableTotal = stableData.peggedAssets.reduce((sum, a) => sum + (a.circulating?.peggedUSD || 0), 0);
            stableTotal7dAgo = stableData.peggedAssets.reduce((sum, a) => {
                const circ = a.circulating?.peggedUSD || 0;
                const change7d = a.circulatingPrevDay?.peggedUSD || circ;
                return sum + change7d;
            }, 0);
        }

        return {
            mktCap, mktCapChange1d, vol, btcDom, ethDom, ethBtc, fg,
            stableTotal, stableTotal7dAgo,
            ethEtf: manualEtf, mvrv: manualMvrv,
        };
    }, [globalData, ethBtcData, fgData, stableData, manualEtf, manualMvrv]);

    const stableChainInfo = useMemo(() => {
        if (!chainData || !Array.isArray(chainData)) return { topChainName: '-', topChainDelta: 0, supplyChangePct: 0 };
        const sorted = [...chainData].sort((a, b) => (b.totalCirculatingUSD?.peggedUSD || 0) - (a.totalCirculatingUSD?.peggedUSD || 0));
        const top = sorted[0];
        const stableChangePct = gauges.stableTotal && gauges.stableTotal7dAgo
            ? ((gauges.stableTotal - gauges.stableTotal7dAgo) / gauges.stableTotal7dAgo) * 100 : 0;

        return {
            topChainName: top?.name || '-',
            topChainDelta: 0,
            supplyChangePct: stableChangePct,
        };
    }, [chainData, gauges]);

    const cards = useMemo(() => {
        const triA = calcTriggersA(gauges.mktCapChange1d, 1.0, 0);
        const triB = calcTriggersB(manualEtf);
        const triC = calcTriggersC(manualMvrv);
        const triD = calcTriggersD(stableChainInfo.supplyChangePct, stableChainInfo.topChainDelta);

        const dataA = {
            mktCapChange1d: gauges.mktCapChange1d,
            volRatio: 1.0,
            btcDom7dDelta: 0,
        };

        return [
            { id: 'overview', importance: getImportance(triA), triggers: triA, summary: genSummaryA(dataA) },
            { id: 'ethEtf', importance: getImportance(triB), triggers: triB, summary: genSummaryB(manualEtf) },
            { id: 'mvrv', importance: getImportance(triC), triggers: triC, summary: genSummaryC(manualMvrv) },
            { id: 'stablecoin', importance: getImportance(triD), triggers: triD, summary: genSummaryD(stableChainInfo) },
        ];
    }, [gauges, manualEtf, manualMvrv, stableChainInfo]);

    const oneLiner = useMemo(() => genOneLiner(cards), [cards]);

    // ---- Manual input handlers ----
    const handleSaveEtf = useCallback((data) => {
        saveManual('ethEtf', data);
        setManualEtf({ ...data, updatedAt: new Date().toISOString() });
    }, []);

    const handleSaveMvrv = useCallback((data) => {
        saveManual('mvrv', data);
        setManualMvrv({ ...data, updatedAt: new Date().toISOString() });
    }, []);

    return (
        <div className="crypto-page">
            {/* Title bar */}
            <div className="crypto-title-bar">
                <h1>Crypto Pulse</h1>
                <span className="crypto-page-badge">Market Monitor</span>
                <div className="crypto-title-actions">
                    {lastUpdate && (
                        <span className="crypto-update-time">
                            {lastUpdate.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })} updated
                        </span>
                    )}
                    <button className="crypto-btn-refresh" onClick={loadAll}>
                        <RefreshCw size={14} />
                        새로고침
                    </button>
                </div>
            </div>

            {loading && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '1rem 0' }}>
                    <span className="crypto-loading-pulse"></span>
                    <span className="crypto-loading-text">데이터 로딩 중...</span>
                </div>
            )}

            {error && <div className="crypto-error-text">{error}</div>}

            {!loading && (
                <>
                    {/* One-liner Banner */}
                    <div className={`crypto-oneliner-banner crypto-regime-${oneLiner.regime}`}>
                        <div className="crypto-oneliner-text">
                            <span className="crypto-oneliner-tag crypto-tag-estimate">추정</span>
                            {oneLiner.text}
                        </div>
                    </div>

                    {/* Gauge Grid */}
                    <div className="crypto-gauge-grid">
                        <div className="crypto-gauge-card" onClick={() => setSelectedGauge('mktCap')}>
                            <div className="crypto-gauge-label">Total Market Cap</div>
                            <div className="crypto-gauge-value">${formatNum(gauges.mktCap)}</div>
                            <div className={`crypto-gauge-delta ${deltaClass(gauges.mktCapChange1d)}`}>
                                {deltaArrow(gauges.mktCapChange1d)}{formatDelta(gauges.mktCapChange1d)} (1D)
                            </div>
                        </div>

                        <div className="crypto-gauge-card" onClick={() => setSelectedGauge('volume')}>
                            <div className="crypto-gauge-label">24h Volume</div>
                            <div className="crypto-gauge-value">${formatNum(gauges.vol)}</div>
                            <div className="crypto-gauge-delta delta-flat">vs 7D avg: -</div>
                        </div>

                        <div className="crypto-gauge-card" onClick={() => setSelectedGauge('btcDom')}>
                            <div className="crypto-gauge-label">BTC Dominance</div>
                            <div className="crypto-gauge-value">{gauges.btcDom?.toFixed(1) || '-'}%</div>
                            <div className="crypto-gauge-delta delta-flat">7D: -</div>
                        </div>

                        <div className="crypto-gauge-card" onClick={() => setSelectedGauge('ethBtc')}>
                            <div className="crypto-gauge-label">ETH/BTC</div>
                            <div className="crypto-gauge-value">{gauges.ethBtc?.toFixed(4) || '-'}</div>
                            <div className="crypto-gauge-delta delta-flat">ETH.D: {gauges.ethDom?.toFixed(1) || '-'}%</div>
                        </div>

                        <div className="crypto-gauge-card" onClick={() => setSelectedGauge('ethEtf')}>
                            <div className="crypto-gauge-label">ETH ETF Flow</div>
                            <div className="crypto-gauge-value">
                                {manualEtf ? `$${manualEtf.flow1d}M` : '-'}
                            </div>
                            <div className={`crypto-gauge-delta ${manualEtf ? deltaClass(manualEtf.flow1d) : 'delta-flat'}`}>
                                {manualEtf ? `5D: $${manualEtf.flow5d || '?'}M` : '수동 입력'}
                            </div>
                        </div>

                        <div className="crypto-gauge-card" onClick={() => setSelectedGauge('mvrv')}>
                            <div className="crypto-gauge-label">MVRV Z-Score</div>
                            <div className="crypto-gauge-value">{manualMvrv?.zScore || '-'}</div>
                            {manualMvrv?.regime && (
                                <div className="crypto-gauge-regime" style={{
                                    background: `${mvrvRegimeColor(manualMvrv.regime)}22`,
                                    color: mvrvRegimeColor(manualMvrv.regime),
                                }}>
                                    {mvrvRegimeLabel(manualMvrv.regime)}
                                </div>
                            )}
                            {!manualMvrv && <div className="crypto-gauge-delta delta-flat">수동 입력</div>}
                        </div>

                        <div className="crypto-gauge-card" onClick={() => setSelectedGauge('stablecoin')}>
                            <div className="crypto-gauge-label">Stablecoin Supply</div>
                            <div className="crypto-gauge-value">${formatNum(gauges.stableTotal)}</div>
                            <div className={`crypto-gauge-delta ${deltaClass(stableChainInfo.supplyChangePct)}`}>
                                {deltaArrow(stableChainInfo.supplyChangePct)}{formatDelta(stableChainInfo.supplyChangePct)} (7D)
                            </div>
                        </div>

                        {gauges.fg != null && (
                            <div className="crypto-gauge-card" onClick={() => setSelectedGauge('fearGreed')}>
                                <div className="crypto-gauge-label">Fear & Greed</div>
                                <div className="crypto-gauge-value" style={{ color: fgColor(gauges.fg) }}>{gauges.fg}</div>
                                <div className="crypto-gauge-delta" style={{ color: fgColor(gauges.fg) }}>
                                    {fgLabel(gauges.fg)}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Gauge Detail Modal */}
                    {selectedGauge && (
                        <GaugeDetailModal
                            gaugeKey={selectedGauge}
                            gauges={gauges}
                            stableChainInfo={stableChainInfo}
                            manualEtf={manualEtf}
                            manualMvrv={manualMvrv}
                            fgData={fgData}
                            onClose={() => setSelectedGauge(null)}
                        />
                    )}

                    {/* Source Cards */}
                    <div className="crypto-source-grid">
                        <SourceCard
                            title="Crypto Overview"
                            question="오늘 시장에 위험선호가 붙었는가?"
                            importance={cards[0].importance}
                            summary={cards[0].summary}
                            metrics={[
                                { label: 'Mkt Cap 1D', value: formatDelta(gauges.mktCapChange1d), cls: deltaClass(gauges.mktCapChange1d) },
                                { label: 'BTC.D', value: `${gauges.btcDom?.toFixed(1) || '-'}%`, cls: 'delta-flat' },
                                { label: 'Vol', value: `$${formatNum(gauges.vol)}`, cls: 'delta-flat' },
                            ]}
                            linkUrl="https://coinmarketcap.com/charts/"
                            linkLabel="CoinMarketCap Charts"
                        />

                        <SourceCard
                            title="Ethereum ETF"
                            question="ETH에 기관성 수급이 들어오는가?"
                            importance={cards[1].importance}
                            summary={cards[1].summary}
                            metrics={manualEtf ? [
                                { label: '1D Flow', value: `$${manualEtf.flow1d}M`, cls: deltaClass(manualEtf.flow1d) },
                                { label: '5D Flow', value: `$${manualEtf.flow5d || '?'}M`, cls: deltaClass(manualEtf.flow5d) },
                                { label: 'Direction', value: manualEtf.direction === 'inflow' ? '유입' : manualEtf.direction === 'outflow' ? '유출' : '혼합', cls: 'delta-flat' },
                            ] : []}
                            linkUrl="https://coinmarketcap.com/etf/ethereum/"
                            linkLabel="ETH ETF on CoinMarketCap"
                            manualInput={
                                <ManualEtfInput initial={manualEtf} onSave={handleSaveEtf} />
                            }
                        />

                        <SourceCard
                            title="MVRV Z-Score"
                            question="BTC가 지금 싼가, 비싼가? (사이클 위치)"
                            importance={cards[2].importance}
                            summary={cards[2].summary}
                            metrics={manualMvrv ? [
                                { label: 'Z-Score', value: manualMvrv.zScore, cls: 'delta-flat' },
                                { label: '레짐', value: mvrvRegimeLabel(manualMvrv.regime), cls: 'delta-flat' },
                                { label: 'Prev', value: manualMvrv.prevZScore, cls: 'delta-flat' },
                            ] : []}
                            linkUrl="https://www.bitcoinmagazinepro.com/charts/mvrv-zscore/"
                            linkLabel="MVRV Z-Score Chart"
                            manualInput={
                                <ManualMvrvInput initial={manualMvrv} onSave={handleSaveMvrv} />
                            }
                        />

                        <SourceCard
                            title="Stablecoin & Chain"
                            question="시장에 달러 유동성이 새로 들어오는가?"
                            importance={cards[3].importance}
                            summary={cards[3].summary}
                            metrics={[
                                { label: 'Total', value: `$${formatNum(gauges.stableTotal)}`, cls: 'delta-flat' },
                                { label: '7D \u0394', value: formatDelta(stableChainInfo.supplyChangePct), cls: deltaClass(stableChainInfo.supplyChangePct) },
                                { label: 'Top Chain', value: stableChainInfo.topChainName, cls: 'delta-flat' },
                            ]}
                            linkUrl="https://defillama.com/stablecoins/chains"
                            linkLabel="DefiLlama Stablecoins"
                        />
                    </div>

                    {/* Transfer Check */}
                    <div className="crypto-transfer-block">
                        <div className="crypto-transfer-title">주식 전이 체크</div>
                        <div className="crypto-transfer-paths">
                            <div className="crypto-transfer-path">크립토 → 나스닥 → 코스피 성장주</div>
                            <div className="crypto-transfer-path">달러 → 스테이블코인 → 크립토</div>
                            <div className="crypto-transfer-path">ETF 수급 → 시장 유동성</div>
                        </div>
                        <label className="crypto-transfer-check">
                            <input type="checkbox"
                                checked={transferCheck}
                                onChange={(e) => setTransferCheck(e.target.checked)}
                            />
                            크립토 강세가 주식으로 번지는 조건 충족?
                        </label>
                    </div>
                </>
            )}
        </div>
    );
};

export default CryptoTrends;
