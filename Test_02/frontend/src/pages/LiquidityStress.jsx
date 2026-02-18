import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import Chart from 'chart.js/auto';
import './LiquidityStress.css';

const LEVEL_CONFIG = {
    normal:  { label: '안정', color: '#22c55e', bg: 'rgba(34,197,94,0.15)',  border: 'rgba(34,197,94,0.3)',  badgeText: '#0f172a' },
    watch:   { label: '관심', color: '#eab308', bg: 'rgba(234,179,8,0.15)',  border: 'rgba(234,179,8,0.3)',  badgeText: '#0f172a' },
    caution: { label: '주의', color: '#f97316', bg: 'rgba(249,115,22,0.15)', border: 'rgba(249,115,22,0.3)', badgeText: '#0f172a' },
    stress:  { label: '경계', color: '#ef4444', bg: 'rgba(239,68,68,0.15)',  border: 'rgba(239,68,68,0.3)',  badgeText: '#f8fafc' },
    crisis:  { label: '위기', color: '#dc2626', bg: 'rgba(220,38,38,0.15)',  border: 'rgba(220,38,38,0.3)',  badgeText: '#f8fafc' },
};

const MODULE_NAMES = {
    volatility: '변동성 (VIX)', credit: '크레딧 스프레드', funding: '자금시장 (SOFR)',
    treasury: '국채 유동성', news: '뉴스 위기 키워드', fedTone: 'Fed 톤',
};

const MODULE_WEIGHTS = { volatility: 0.25, credit: 0.25, funding: 0.20, treasury: 0.15, news: 0.10, fedTone: 0.05 };
const MODULE_HISTORY_KEYS = { volatility: 'volScore', credit: 'creditScore', funding: 'fundingScore', treasury: 'treasuryScore', news: 'newsScore', fedTone: 'fedToneScore' };

const MODULE_SOURCES = {
    volatility: [{ name: 'Yahoo Finance - VIX', url: 'https://finance.yahoo.com/quote/%5EVIX/' }, { name: 'CBOE VIX Index', url: 'https://www.cboe.com/tradable_products/vix/' }],
    credit: [{ name: 'FRED - HY OAS (ICE BofA)', url: 'https://fred.stlouisfed.org/series/BAMLH0A0HYM2' }, { name: 'FRED - IG OAS (ICE BofA)', url: 'https://fred.stlouisfed.org/series/BAMLC0A0CM' }],
    funding: [{ name: 'FRED - SOFR', url: 'https://fred.stlouisfed.org/series/SOFR' }, { name: 'FRED - 역리포 잔고 (RRP)', url: 'https://fred.stlouisfed.org/series/RRPONTSYD' }],
    treasury: [{ name: 'FRED - 10Y Treasury (DGS10)', url: 'https://fred.stlouisfed.org/series/DGS10' }, { name: 'Yahoo Finance - TLT', url: 'https://finance.yahoo.com/quote/TLT/' }],
    news: [{ name: 'Google News - Liquidity Crisis', url: 'https://news.google.com/search?q=liquidity+crisis' }],
    fedTone: [{ name: 'Fed 보도자료', url: 'https://www.federalreserve.gov/newsevents/pressreleases.htm' }],
};

const MODULE_DESCRIPTIONS = {
    volatility: 'VIX(CBOE 변동성 지수)를 기반으로 시장 공포 수준을 측정합니다.\n\n\u2022 VIX 12 이하 = 극도의 안정\n\u2022 VIX 20~25 = 보통 수준\n\u2022 VIX 35 이상 = 극심한 공포 (패닉 구간)',
    credit: 'HY OAS(하이일드 스프레드)로 신용 위험을 측정합니다.\n\n\u2022 HY OAS 2.5% 이하 = 크레딧 안정\n\u2022 HY OAS 4.0~5.0% = 크레딧 긴장\n\u2022 HY OAS 6.0% 이상 = 심각한 신용 경색',
    funding: 'SOFR과 역리포 잔고로 단기 자금시장 긴장도를 측정합니다.',
    treasury: 'TLT(20년+ 국채 ETF) 변동성으로 국채시장 유동성을 측정합니다.',
    news: 'Google News RSS에서 6개 위기 키워드의 뉴스 빈도를 실시간 집계합니다.',
    fedTone: 'Fed 보도자료에서 유동성·크레딧·금융안정 관련 키워드 비중을 분석합니다.',
};

// ─── GaugeChart ───
const GaugeChart = React.memo(({ score, level }) => {
    const cfg = LEVEL_CONFIG[level] || LEVEL_CONFIG.normal;
    const pct = Math.min(Math.max(score, 0), 1);
    const radius = 60, cx = 80, cy = 85;
    const startAngle = Math.PI;
    const endAngle = Math.PI - pct * Math.PI;
    const x1 = cx + radius * Math.cos(startAngle);
    const y1 = cy + radius * Math.sin(startAngle);
    const x2 = cx + radius * Math.cos(endAngle);
    const y2 = cy + radius * Math.sin(endAngle);
    const largeArc = pct > 0.5 ? 1 : 0;
    const bgX = cx + radius * Math.cos(0);
    const bgY = cy + radius * Math.sin(0);

    return (
        <div className="gauge-wrapper">
            <svg className="gauge-svg" viewBox="0 0 160 100">
                <path d={`M ${x1} ${y1} A ${radius} ${radius} 0 1 1 ${bgX} ${bgY}`} fill="none" stroke="#1e293b" strokeWidth="12" strokeLinecap="round" />
                {pct > 0.01 && <path d={`M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`} fill="none" stroke={cfg.color} strokeWidth="12" strokeLinecap="round" />}
            </svg>
            <div className="gauge-label">
                <div className="gauge-score" style={{ color: cfg.color }}>{score.toFixed(2)}</div>
                <div className="gauge-level" style={{ color: cfg.color }}>{cfg.label}</div>
            </div>
        </div>
    );
});

// ─── ModuleBar ───
const ModuleBar = React.memo(({ name, moduleKey, score, weight, onClick }) => {
    const pct = Math.min(Math.max(score, 0), 1) * 100;
    let color = '#22c55e';
    if (score >= 0.55) color = '#ef4444';
    else if (score >= 0.40) color = '#f97316';
    else if (score >= 0.25) color = '#eab308';

    return (
        <div className="module-bar" onClick={() => onClick && onClick(moduleKey)}>
            <div className="module-bar-header">
                <span className="module-name">{name} <span style={{ color: '#475569', fontSize: '0.7rem' }}>({(weight * 100).toFixed(0)}%)</span></span>
                <span className="module-score" style={{ color }}>{score.toFixed(3)}</span>
            </div>
            <div className="bar-track"><div className="bar-fill" style={{ width: `${pct}%`, background: color }}></div></div>
        </div>
    );
});

// ─── DetailModal ───
const DetailModal = ({ moduleKey, modules, history, macro, onClose }) => {
    const canvasRef = useRef(null);
    const chartRef = useRef(null);
    const [chartMetric, setChartMetric] = useState(null);
    const name = MODULE_NAMES[moduleKey] || moduleKey;
    const histKey = MODULE_HISTORY_KEYS[moduleKey];
    const desc = MODULE_DESCRIPTIONS[moduleKey] || '';
    const mod = modules[moduleKey] || {};

    const moduleLevel = useMemo(() => {
        const s = mod.score || 0;
        if (s >= 0.75) return 'crisis';
        if (s >= 0.55) return 'stress';
        if (s >= 0.40) return 'caution';
        if (s >= 0.25) return 'watch';
        return 'normal';
    }, [mod.score]);
    const mlCfg = LEVEL_CONFIG[moduleLevel];

    const fmtChg = (chg, unit = '', digits = 2) => {
        if (chg == null) return null;
        const sign = chg > 0 ? '+' : '';
        const cls = chg > 0 ? 'chg-up' : chg < 0 ? 'chg-down' : 'chg-flat';
        return { text: `${sign}${chg.toFixed ? chg.toFixed(digits) : chg}${unit}`, cls };
    };

    const scoreChg = fmtChg(mod.prevScore != null ? (mod.score || 0) - mod.prevScore : null, '', 3);

    const detailItems = useMemo(() => {
        switch (moduleKey) {
            case 'volatility': return [
                { label: 'VIX 현재', value: mod.vix?.toFixed(1) ?? '-', color: (mod.vix || 0) >= 25 ? '#ef4444' : '#22c55e', chg: fmtChg(mod.vixChange, '%', 1), chartKey: 'vix', chartColor: '#ef4444', yMin: 10, yMax: 50 },
                { label: '모듈 점수', value: mod.score?.toFixed(3) ?? '0', color: '#f97316', chg: scoreChg, chartKey: histKey, chartColor: '#f97316', yMin: 0, yMax: 1 },
            ];
            case 'credit': return [
                { label: 'HY OAS', value: mod.hyOas ? `${mod.hyOas.toFixed(2)}%` : '-', color: (mod.hyOas || 0) >= 4.5 ? '#ef4444' : '#eab308', chg: fmtChg(mod.hyOasChg, '', 2), chartKey: 'hyOas', chartColor: '#eab308', yMin: 0, yMax: 8 },
                { label: 'IG OAS', value: mod.igOas ? `${mod.igOas.toFixed(2)}%` : '-', color: '#94a3b8', chg: fmtChg(mod.igOasChg, '', 2), chartKey: 'igOas', chartColor: '#94a3b8', yMin: 0, yMax: 3 },
                { label: '모듈 점수', value: mod.score?.toFixed(3) ?? '0', color: '#f97316', chg: scoreChg, chartKey: histKey, chartColor: '#f97316', yMin: 0, yMax: 1 },
            ];
            case 'funding': return [
                { label: 'SOFR', value: mod.sofr ? `${mod.sofr.toFixed(2)}%` : '-', color: '#f97316', chg: fmtChg(mod.sofrChg, '', 2), chartKey: 'sofr', chartColor: '#f97316', yMin: 3, yMax: 6 },
                { label: '역리포 잔고', value: mod.rrpBalance != null ? `${mod.rrpBalance.toFixed(1)}B$` : '-', color: '#60a5fa', chg: fmtChg(mod.rrpChg, '', 1), chartKey: 'rrpBalance', chartColor: '#60a5fa', yMin: 0, yMax: null },
                { label: '모듈 점수', value: mod.score?.toFixed(3) ?? '0', color: '#f97316', chg: scoreChg, chartKey: histKey, chartColor: '#f97316', yMin: 0, yMax: 1 },
            ];
            case 'treasury': return [
                { label: '10Y 금리', value: macro?.dgs10 ? `${macro.dgs10.toFixed(2)}%` : '-', color: '#60a5fa', chg: fmtChg(macro?.dgs10Chg, '', 2), chartKey: 'dgs10', chartColor: '#60a5fa', yMin: 3, yMax: 6 },
                { label: '2Y 금리', value: macro?.dgs2 ? `${macro.dgs2.toFixed(2)}%` : '-', color: '#94a3b8', chg: fmtChg(macro?.dgs2Chg, '', 2), chartKey: 'dgs2', chartColor: '#94a3b8', yMin: 3, yMax: 6 },
                { label: 'TLT 종가', value: mod.tltClose ? `$${mod.tltClose.toFixed(1)}` : '-', color: '#22c55e', chg: fmtChg(mod.tltChg, '%', 1), chartKey: 'tltClose', chartColor: '#22c55e', yMin: 80, yMax: 110 },
                { label: '모듈 점수', value: mod.score?.toFixed(3) ?? '0', color: '#f97316', chg: scoreChg, chartKey: histKey, chartColor: '#f97316', yMin: 0, yMax: 1 },
            ];
            case 'news': return [
                { label: 'Top 키워드', value: mod.topKeyword || '-', color: '#f97316' },
                { label: '총 뉴스 수', value: `${mod.totalCount ?? 0}건`, color: '#eab308', chg: fmtChg(mod.countChg, '건', 0), chartKey: 'newsCount', chartColor: '#eab308', yMin: 0, yMax: null },
                { label: '모듈 점수', value: mod.score?.toFixed(3) ?? '0', color: '#f97316', chg: scoreChg, chartKey: histKey, chartColor: '#f97316', yMin: 0, yMax: 1 },
            ];
            case 'fedTone': return [
                { label: '유동성 키워드', value: mod.liquidityFocus?.toFixed(3) ?? '0', color: '#f97316', chg: fmtChg(mod.liqChg, '', 3), chartKey: 'fedLiquidity', chartColor: '#f97316', yMin: 0, yMax: 0.5 },
                { label: '안정성 키워드', value: mod.stabilityFocus?.toFixed(3) ?? '0', color: '#22c55e', chg: fmtChg(mod.stabChg, '', 3), chartKey: 'fedStability', chartColor: '#22c55e', yMin: 0, yMax: 0.5 },
                { label: '모듈 점수', value: mod.score?.toFixed(3) ?? '0', color: '#f97316', chg: scoreChg, chartKey: histKey, chartColor: '#f97316', yMin: 0, yMax: 1 },
            ];
            default: return [];
        }
    }, [moduleKey, mod, macro, scoreChg, histKey]);

    const scoreComment = useMemo(() => {
        const s = mod.score || 0;
        const lvl = s >= 0.55 ? '경계' : s >= 0.40 ? '주의' : s >= 0.25 ? '관심' : '안정';
        const lvlColor = s >= 0.55 ? '#ef4444' : s >= 0.40 ? '#f97316' : s >= 0.25 ? '#eab308' : '#22c55e';
        switch (moduleKey) {
            case 'volatility': {
                const vix = mod.vix;
                if (vix == null) return null;
                const zone = vix >= 35 ? '극심한 공포(패닉) 구간' : vix >= 25 ? '높은 공포 구간' : vix >= 20 ? '보통 수준의 변동성' : '낮은 변동성 (안정)';
                return { text: `VIX ${vix.toFixed(1)}로 ${zone}. 모듈 점수 ${s.toFixed(3)}은 ${lvl} 수준입니다.`, color: lvlColor };
            }
            case 'credit': {
                const hy = mod.hyOas;
                if (hy == null) return null;
                const zone = hy >= 6.0 ? '심각한 신용 경색 구간' : hy >= 4.0 ? '크레딧 긴장 구간' : '크레딧 안정 구간';
                return { text: `HY OAS ${hy.toFixed(2)}%로 ${zone}에 위치. 모듈 점수 ${s.toFixed(3)}은 ${lvl} 수준입니다.`, color: lvlColor };
            }
            default: return { text: `모듈 점수 ${s.toFixed(3)}은 ${lvl} 수준입니다.`, color: lvlColor };
        }
    }, [moduleKey, mod]);

    const activeChart = useMemo(() => {
        if (chartMetric) return chartMetric;
        return { key: histKey, label: '모듈 점수', color: '#f97316', yMin: 0, yMax: 1 };
    }, [chartMetric, histKey]);

    useEffect(() => {
        if (!canvasRef.current || !history || !activeChart.key) return;
        if (chartRef.current) chartRef.current.destroy();

        const labels = history.map(h => h.date.slice(5));
        const rawData = history.map(h => h[activeChart.key]);
        const validData = rawData.filter(v => v != null);
        const autoMin = validData.length > 0 ? Math.floor(Math.min(...validData) * 0.9 * 100) / 100 : 0;
        const autoMax = validData.length > 0 ? Math.ceil(Math.max(...validData) * 1.1 * 100) / 100 : 1;
        const yMin = activeChart.yMin != null ? activeChart.yMin : autoMin;
        const yMax = activeChart.yMax != null ? activeChart.yMax : autoMax;
        const chartColor = activeChart.color || '#f97316';

        chartRef.current = new Chart(canvasRef.current, {
            type: 'line',
            data: { labels, datasets: [{ label: activeChart.label, data: rawData, borderColor: chartColor, backgroundColor: chartColor + '14', borderWidth: 2, fill: true, tension: 0.3, pointRadius: 2, pointBackgroundColor: chartColor, spanGaps: true }] },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => { const v = ctx.parsed.y; return v != null ? `${activeChart.label}: ${v.toFixed(3)}` : 'N/A'; } } } },
                scales: { y: { min: yMin, max: yMax, grid: { color: 'rgba(51,65,85,0.4)' }, ticks: { color: '#64748b', font: { size: 10 } } }, x: { grid: { display: false }, ticks: { color: '#64748b', font: { size: 9 }, maxRotation: 45, maxTicksLimit: 10 } } },
            },
        });
        return () => { if (chartRef.current) { chartRef.current.destroy(); chartRef.current = null; } };
    }, [history, activeChart]);

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <button className="modal-close" onClick={onClose}>&times;</button>
                <div className="modal-title">{name} <span className="modal-level-badge" style={{ background: mlCfg.color, color: mlCfg.badgeText }}>{mlCfg.label}</span></div>
                <div className="modal-subtitle">30일 추이 및 세부 지표 &middot; 가중치 {(MODULE_WEIGHTS[moduleKey] * 100).toFixed(0)}% &middot; 항목 클릭 시 차트 전환</div>
                <div className="detail-grid">
                    {detailItems.map((item, i) => {
                        const isSelected = item.chartKey && (activeChart.key === item.chartKey);
                        const isSelectable = !!item.chartKey;
                        return (
                            <div key={i} className={`detail-item${isSelectable ? ' selectable' : ''}${isSelected ? ' selected' : ''}`}
                                onClick={() => isSelectable && setChartMetric({ key: item.chartKey, label: item.label, color: item.chartColor, yMin: item.yMin, yMax: item.yMax })}>
                                <div className="detail-item-label">{item.label} {isSelected && '\u25C0'}</div>
                                <div className="detail-item-value" style={{ color: item.color }}>
                                    <span>{item.value}</span>
                                    {item.chg && <span className={`detail-item-change ${item.chg.cls}`}>{item.chg.text}</span>}
                                </div>
                            </div>
                        );
                    })}
                </div>
                <div className="detail-chart-wrapper"><canvas ref={canvasRef}></canvas></div>
                {scoreComment && (
                    <div className="detail-comment">
                        <span className="comment-badge" style={{ background: scoreComment.color + '22', color: scoreComment.color, border: `1px solid ${scoreComment.color}44` }}>현재 상태</span>
                        <span className="comment-text">{scoreComment.text}</span>
                    </div>
                )}
                <div className="detail-explanation">{desc}</div>
                {MODULE_SOURCES[moduleKey] && (
                    <div className="detail-sources">
                        <div className="sources-label">참조:</div>
                        {MODULE_SOURCES[moduleKey].map((src, i) => (
                            <a key={i} href={src.url} target="_blank" rel="noopener noreferrer" className="source-link">&#x1F517; {src.name}</a>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

// ─── HistoryChart ───
const HistoryChart = React.memo(({ history }) => {
    const canvasRef = useRef(null);
    const chartRef = useRef(null);

    useEffect(() => {
        if (!canvasRef.current || !history || history.length === 0) return;
        if (chartRef.current) chartRef.current.destroy();

        const labels = history.map(h => h.date.slice(5));
        const scores = history.map(h => h.totalScore);
        const colors = history.map(h => (LEVEL_CONFIG[h.level] || LEVEL_CONFIG.normal).color);

        chartRef.current = new Chart(canvasRef.current, {
            type: 'line',
            data: { labels, datasets: [{ label: '종합 스트레스', data: scores, borderColor: '#f97316', backgroundColor: 'rgba(249,115,22,0.1)', borderWidth: 2, fill: true, tension: 0.3, pointRadius: 3, pointBackgroundColor: colors, pointBorderColor: colors }] },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => { const h = history[ctx.dataIndex]; const cfg = LEVEL_CONFIG[h.level] || LEVEL_CONFIG.normal; return `${h.totalScore.toFixed(3)} (${cfg.label})`; } } } },
                scales: { y: { min: 0, max: 1, grid: { color: 'rgba(51,65,85,0.5)' }, ticks: { color: '#94a3b8', stepSize: 0.25 } }, x: { grid: { display: false }, ticks: { color: '#94a3b8', maxRotation: 45 } } },
            },
        });
        return () => { if (chartRef.current) { chartRef.current.destroy(); chartRef.current = null; } };
    }, [history]);

    return (
        <div className="chart-section">
            <div className="chart-title">30일 스트레스 추이</div>
            <div className="chart-wrapper"><canvas ref={canvasRef}></canvas></div>
        </div>
    );
});

// ─── Main Component ───
const LiquidityStress = () => {
    const [data, setData] = useState(null);
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [detailModule, setDetailModule] = useState(null);

    const handleModuleClick = useCallback((key) => setDetailModule(key), []);
    const handleCloseDetail = useCallback(() => setDetailModule(null), []);

    useEffect(() => {
        const load = async () => {
            try {
                setLoading(true);
                const [latestRes, historyRes] = await Promise.all([
                    fetch('/api/v1/liquidity-stress'),
                    fetch('/api/v1/liquidity-stress/history?days=30'),
                ]);
                if (!latestRes.ok) throw new Error(`API error: ${latestRes.status}`);
                if (!historyRes.ok) throw new Error(`History API error: ${historyRes.status}`);
                const latest = await latestRes.json();
                const hist = await historyRes.json();
                setData(latest);
                setHistory(hist.history || []);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, []);

    const modules = data?.modules || {};
    const level = data?.level || 'normal';
    const cfg = LEVEL_CONFIG[level] || LEVEL_CONFIG.normal;

    const stressDiagnosis = useMemo(() => {
        if (!data?.totalScore) return null;
        const moduleKeys = ['volatility', 'credit', 'funding', 'treasury', 'news', 'fedTone'];
        const shortNames = { volatility: 'VIX', credit: '크레딧', funding: 'SOFR', treasury: '국채', news: '뉴스', fedTone: 'Fed' };
        const barColors = { volatility: '#ef4444', credit: '#f97316', funding: '#eab308', treasury: '#3b82f6', news: '#a855f7', fedTone: '#06b6d4' };
        const contributions = moduleKeys.map(k => ({ key: k, name: shortNames[k], color: barColors[k], weighted: (modules[k]?.score || 0) * MODULE_WEIGHTS[k] })).sort((a, b) => b.weighted - a.weighted);
        const total = contributions.reduce((s, c) => s + c.weighted, 0);
        contributions.forEach(c => { c.pct = total > 0 ? (c.weighted / total * 100) : 0; });
        const drivers = contributions.filter(c => c.weighted >= 0.05).slice(0, 3).map(c => c.name);
        const reason = drivers.length > 0 ? `주요 요인: ${drivers.join(' · ')}` : '전반적으로 안정적';
        return { reason, contributions };
    }, [data, modules]);

    const dataSourceInfo = useMemo(() => {
        if (!modules || !Object.keys(modules).length) return { sources: [], hasSeed: false };
        const sources = [];
        if (modules.volatility?.vix) sources.push({ module: 'VIX/가격', type: modules.volatility.vix > 0 ? 'REAL' : 'SEED', via: 'Yahoo v8 API' });
        if (modules.credit?.score != null) sources.push({ module: '크레딧', type: modules.credit.hyOas > 5.5 ? 'SEED' : 'MIX', via: 'FRED API' });
        if (modules.funding?.score != null) sources.push({ module: '자금시장', type: modules.funding.score > 0.8 ? 'SEED' : 'MIX', via: 'FRED API' });
        if (modules.news?.totalCount != null) sources.push({ module: '뉴스', type: modules.news.totalCount > 100 ? 'REAL' : 'SEED', via: 'Google News' });
        if (modules.fedTone?.score != null) sources.push({ module: 'Fed톤', type: modules.fedTone.score < 0.1 ? 'REAL' : 'SEED', via: 'Fed 연설문' });
        const hasSeed = sources.some(s => s.type !== 'REAL');
        return { sources, hasSeed };
    }, [modules]);

    const newsInfo = modules.news || {};

    if (loading) return <div className="liq-page"><div className="liq-loading"><div className="liq-spinner"></div></div></div>;
    if (error) return <div className="liq-page"><div className="liq-empty"><h3>데이터 로딩 실패</h3><p>{error}</p><p style={{ marginTop: '1rem', fontSize: '0.875rem', color: '#64748b' }}>백엔드 서버를 실행하고 시드 데이터를 삽입하세요.<br /><code style={{ color: '#f97316' }}>python scripts/liquidity_monitor/seed_data.py</code></p></div></div>;
    if (!data?.date) return <div className="liq-page"><div className="liq-empty"><h3>데이터 없음</h3><p>시드 데이터를 생성해주세요.</p></div></div>;

    return (
        <div className="liq-page">
            <div className="page-title-bar">
                <h1>유동성 &amp; 신용 스트레스 모니터</h1>
                <span className="page-badge">{data.date}</span>
            </div>

            {dataSourceInfo.hasSeed && (
                <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '8px', padding: '0.5rem 1rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap', fontSize: '0.75rem', color: '#94a3b8' }}>
                    <span style={{ color: '#f87171', fontWeight: 700, fontSize: '0.65rem', padding: '1px 6px', background: 'rgba(239,68,68,0.15)', borderRadius: '3px', border: '1px solid rgba(239,68,68,0.3)' }}>SEED DATA</span>
                    <span>일부 모듈 데이터가 시드(데모)입니다:</span>
                    {dataSourceInfo.sources.filter(s => s.type !== 'REAL').map(s => <span key={s.module} style={{ color: '#f87171' }}>{s.module}({s.via})</span>)}
                </div>
            )}

            <div className="stress-banner" style={{ background: `linear-gradient(135deg, ${cfg.bg}, rgba(15,23,42,0.8))`, border: `1px solid ${cfg.border}` }}>
                <div className="banner-main">
                    <h2>유동성 &amp; 신용 스트레스: <strong style={{ color: cfg.color }}>{cfg.label}</strong></h2>
                    <div className="banner-sub" style={{ marginTop: '0.3rem' }}>기준일: {data.date} &middot; 종합 점수: <span style={{ color: cfg.color, fontWeight: 700 }}>{data.totalScore.toFixed(3)}</span></div>
                    {stressDiagnosis && (
                        <div className="banner-diagnosis">
                            <div className="diagnosis-reason">
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
                                {stressDiagnosis.reason}
                            </div>
                            <div className="diagnosis-bar">
                                {stressDiagnosis.contributions.map(c => c.pct > 0 && (
                                    <div key={c.key} className="diagnosis-segment" style={{ width: `${Math.max(c.pct, 8)}%`, background: c.color }} title={`${c.name}: ${c.weighted.toFixed(3)} (${c.pct.toFixed(0)}%)`}>
                                        {c.pct >= 15 ? c.name : ''}
                                    </div>
                                ))}
                            </div>
                            <div className="diagnosis-legend">
                                {stressDiagnosis.contributions.map(c => <span key={c.key} className="legend-item"><span className="legend-dot" style={{ background: c.color }}></span>{c.name} {c.weighted.toFixed(3)}</span>)}
                            </div>
                        </div>
                    )}
                </div>
                <div className="gauge-section"><GaugeChart score={data.totalScore} level={level} /></div>
            </div>

            <div className="modules-grid">
                {Object.entries(MODULE_NAMES).map(([key, n]) => <ModuleBar key={key} moduleKey={key} name={n} score={modules[key]?.score || 0} weight={MODULE_WEIGHTS[key]} onClick={handleModuleClick} />)}
            </div>

            <div className="liq-kpi-grid">
                <div className="liq-kpi-card" onClick={() => handleModuleClick('volatility')}>
                    <div className="liq-kpi-label">VIX (공포지수)</div>
                    <div className="liq-kpi-value" style={{ color: (modules.volatility?.vix || 0) >= 25 ? '#ef4444' : '#22c55e' }}>{modules.volatility?.vix?.toFixed(1) ?? '-'}</div>
                    {modules.volatility?.vixChange != null && <div className="liq-kpi-change" style={{ color: modules.volatility.vixChange > 0 ? '#ef4444' : '#22c55e' }}>{modules.volatility.vixChange > 0 ? '+' : ''}{modules.volatility.vixChange}%</div>}
                </div>
                <div className="liq-kpi-card" onClick={() => handleModuleClick('credit')}>
                    <div className="liq-kpi-label">HY OAS (하이일드 스프레드)</div>
                    <div className="liq-kpi-value" style={{ color: (modules.credit?.hyOas || 0) >= 4.5 ? '#ef4444' : '#eab308' }}>{modules.credit?.hyOas?.toFixed(2) ?? '-'}%</div>
                    <div className="liq-kpi-change" style={{ color: '#94a3b8' }}>IG OAS: {modules.credit?.igOas?.toFixed(2) ?? '-'}%</div>
                </div>
                <div className="liq-kpi-card" onClick={() => handleModuleClick('funding')}>
                    <div className="liq-kpi-label">SOFR (자금시장 금리)</div>
                    <div className="liq-kpi-value" style={{ color: '#f97316' }}>{modules.funding?.sofr?.toFixed(2) ?? '-'}%</div>
                    <div className="liq-kpi-change" style={{ color: '#94a3b8' }}>역리포: {modules.funding?.rrpBalance?.toFixed(0) ?? '-'}B</div>
                </div>
                <div className="liq-kpi-card" onClick={() => handleModuleClick('treasury')}>
                    <div className="liq-kpi-label">10년 국채금리</div>
                    <div className="liq-kpi-value" style={{ color: '#60a5fa' }}>{data.macro?.dgs10?.toFixed(2) ?? '-'}%</div>
                    <div className="liq-kpi-change" style={{ color: '#94a3b8' }}>2Y: {data.macro?.dgs2?.toFixed(2) ?? '-'}% &middot; 30Y: {data.macro?.dgs30?.toFixed(2) ?? '-'}%</div>
                </div>
            </div>

            <HistoryChart history={history} />

            {detailModule && <DetailModal moduleKey={detailModule} modules={modules} history={history} macro={data.macro} onClose={handleCloseDetail} />}

            <div className="news-section">
                <div className="news-title">위기 키워드 현황</div>
                {newsInfo.topKeyword ? (
                    <div>
                        <div className="news-item">
                            <div className="news-rank">1</div>
                            <div className="news-keyword">{newsInfo.topKeyword}</div>
                            <div className="news-count">{newsInfo.totalCount ?? 0}건</div>
                        </div>
                        <div style={{ padding: '0.75rem 0', fontSize: '0.8rem', color: '#64748b' }}>
                            뉴스 모듈 점수: <span style={{ color: '#f97316', fontWeight: 600 }}>{modules.news?.score?.toFixed(3) ?? '0'}</span>
                            {' '}&middot; Fed 톤 점수: <span style={{ color: '#f97316', fontWeight: 600 }}>{modules.fedTone?.score?.toFixed(3) ?? '0'}</span>
                        </div>
                    </div>
                ) : <div style={{ padding: '1rem 0', color: '#64748b', fontSize: '0.875rem' }}>키워드 데이터가 없습니다.</div>}
            </div>
        </div>
    );
};

export default LiquidityStress;
