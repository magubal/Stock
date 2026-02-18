import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { TrendingDown, TrendingUp, AlertTriangle, Zap } from 'lucide-react';
import './Disclosures.css';

// ─── SentimentBanner ──────────────────────────────────
const SentimentBanner = React.memo(({ summary }) => {
    if (!summary) return null;
    const label = summary.sentiment_label || '분석 중';
    const score = summary.daily_score || 0;

    let bannerClass = 'sentiment-neutral';
    if (score >= 2) bannerClass = 'sentiment-positive';
    else if (score <= -2 && score > -5) bannerClass = 'sentiment-cautious';
    else if (score <= -5) bannerClass = 'sentiment-negative';

    const scoreColor = score > 0 ? 'text-green' : score < 0 ? 'text-red' : 'text-gray';

    return (
        <div className={`sentiment-banner ${bannerClass}`}>
            <div className="banner-main">
                <h2>오늘의 시장 심리: <strong>{label}</strong></h2>
                <div className="banner-sub">
                    일일 종합 점수: <span className={scoreColor} style={{ fontWeight: 700 }}>{score > 0 ? '+' : ''}{score}</span>
                    {' · '}총 {summary.total || 0}건 공시
                </div>
            </div>
            <div className="banner-stats">
                <div className="banner-stat">
                    <div className="banner-stat-value text-green">{summary.risk_on || 0}</div>
                    <div className="banner-stat-label">Risk-On</div>
                </div>
                <div className="banner-stat">
                    <div className="banner-stat-value text-red">{summary.risk_off || 0}</div>
                    <div className="banner-stat-label">Risk-Off</div>
                </div>
                <div className="banner-stat">
                    <div className="banner-stat-value text-gray">{summary.neutral || 0}</div>
                    <div className="banner-stat-label">Neutral</div>
                </div>
            </div>
        </div>
    );
});

// ─── KPICards ─────────────────────────────────────────
const KPICards = React.memo(({ summary, onClusterClick, activeCluster }) => {
    if (!summary) return null;
    return (
        <div className="kpi-grid">
            <div className="kpi-card">
                <div className="kpi-header">
                    <div className="kpi-icon kpi-icon-red"><TrendingDown size={20} /></div>
                    <span className="kpi-label">희석 이벤트 (Dilution)</span>
                </div>
                <div className="kpi-value text-red">{summary.dilution_count || 0}건</div>
                <div className="kpi-detail">CB / BW / 유상증자 발행 건수</div>
            </div>
            <div className="kpi-card">
                <div className="kpi-header">
                    <div className="kpi-icon kpi-icon-green"><TrendingUp size={20} /></div>
                    <span className="kpi-label">환원 이벤트 (Return)</span>
                </div>
                <div className="kpi-value text-green">{summary.buyback_count || 0}건</div>
                <div className="kpi-detail">자사주매입 / 배당 결정 건수</div>
            </div>
            <div className="kpi-card">
                <div className="kpi-header">
                    <div className="kpi-icon kpi-icon-yellow"><AlertTriangle size={20} /></div>
                    <span className="kpi-label">클러스터 알림</span>
                </div>
                {(summary.cluster_alerts || []).length > 0 ? (
                    <div className="cluster-alerts">
                        {summary.cluster_alerts.map((alert, i) => (
                            <div key={i}
                                className={`cluster-item ${activeCluster === alert ? 'cluster-active' : ''}`}
                                onClick={() => onClusterClick && onClusterClick(alert)}>
                                <Zap size={14} />
                                {alert}
                            </div>
                        ))}
                    </div>
                ) : (
                    <div>
                        <div className="kpi-value text-green" style={{ fontSize: '1.25rem' }}>정상</div>
                        <div className="kpi-detail">동일 이벤트 집중 발생 없음</div>
                    </div>
                )}
            </div>
        </div>
    );
});

// ─── DisclosureCard ───────────────────────────────────
const DisclosureCard = React.memo(({ item }) => {
    const sentiment = item.sentiment || 'neutral';
    const score = item.impact_score || 0;

    const cardClass = sentiment === 'positive' ? 'disclosure-positive'
        : sentiment === 'negative' ? 'disclosure-negative' : 'disclosure-neutral';
    const badgeClass = sentiment === 'positive' ? 'badge-positive'
        : sentiment === 'negative' ? 'badge-negative' : 'badge-neutral';
    const scoreClass = score > 0 ? 'score-positive' : score < 0 ? 'score-negative' : 'score-neutral';

    const handleClick = (e) => {
        e.preventDefault();
        if (item.url) {
            window.open(item.url, '_blank', 'width=1000,height=975,scrollbars=yes,resizable=yes,menubar=no,toolbar=no,location=no,status=no');
        }
    };

    return (
        <div className={`disclosure-card ${cardClass}`}
            onClick={handleClick}
            style={{ cursor: item.url ? 'pointer' : 'default' }}>
            <div className="disclosure-time">{item.time || ''}</div>
            <div className={`disclosure-badge ${badgeClass}`}>{item.badge || '기타'}</div>
            <div className="disclosure-body">
                <div>
                    <span className="disclosure-company">{item.company || ''}</span>
                    {item.code && <span className="disclosure-company-code">({item.code})</span>}
                </div>
                <div className="disclosure-title">{item.title || ''}</div>
            </div>
            <div className={`disclosure-score ${scoreClass}`}>
                {score > 0 ? '+' : ''}{score}
            </div>
        </div>
    );
});

// ─── Main ────────────────────────────────────────────
const CLUSTER_LABEL_TO_CLASSES = {
    'CB 발행': ['cb_issuance'],
    'BW 발행': ['bw_issuance'],
    '유상증자': ['rights_offering'],
    '공급계약': ['supply_contract'],
    '자사주매입': ['buyback'],
    '배당': ['dividend'],
    '소송': ['lawsuit'],
    '거래정지': ['suspension'],
    '실적공시': ['earnings_surprise', 'earnings_guidance'],
};

const Disclosures = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filter, setFilter] = useState('all');
    const [clusterAlert, setClusterAlert] = useState(null);

    useEffect(() => {
        const loadData = async () => {
            try {
                setLoading(true);
                const response = await fetch('/data/latest_disclosures.json');
                if (!response.ok) throw new Error('데이터를 불러올 수 없습니다.');
                const json = await response.json();
                setData(json);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, []);

    const stats = useMemo(() => {
        if (!data?.disclosures) return { performance: 0, contract: 0, lawsuit: 0, suspension: 0 };
        return {
            performance: data.disclosures.filter(d => ['earnings_surprise', 'earnings_guidance', 'earnings_variance'].includes(d.event_class)).length,
            contract: data.disclosures.filter(d => d.event_class === 'supply_contract').length,
            lawsuit: data.disclosures.filter(d => d.event_class === 'lawsuit').length,
            suspension: data.disclosures.filter(d => d.event_class === 'suspension').length,
        };
    }, [data]);

    const filteredDisclosures = useMemo(() => {
        if (!data?.disclosures) return [];
        let result = [];
        let shouldSort = false;

        if (clusterAlert) {
            const labelMatch = clusterAlert.match(/\d+개사 동시 (.+)/);
            if (labelMatch) {
                const label = labelMatch[1];
                const classes = CLUSTER_LABEL_TO_CLASSES[label];
                result = classes
                    ? data.disclosures.filter(d => classes.includes(d.event_class))
                    : data.disclosures.filter(d => d.event_class === label);
            } else {
                result = data.disclosures;
            }
            shouldSort = true;
        }
        else if (filter === 'all') result = data.disclosures;
        else if (filter === 'positive') result = data.disclosures.filter(d => d.sentiment === 'positive');
        else if (filter === 'negative') result = data.disclosures.filter(d => d.sentiment === 'negative');
        else if (filter === 'neutral') result = data.disclosures.filter(d => d.sentiment === 'neutral');
        else if (filter === 'performance') { result = data.disclosures.filter(d => ['earnings_surprise', 'earnings_guidance', 'earnings_variance'].includes(d.event_class)); shouldSort = true; }
        else if (filter === 'contract') { result = data.disclosures.filter(d => d.event_class === 'supply_contract'); shouldSort = true; }
        else if (filter === 'lawsuit') { result = data.disclosures.filter(d => d.event_class === 'lawsuit'); shouldSort = true; }
        else if (filter === 'suspension') { result = data.disclosures.filter(d => d.event_class === 'suspension'); shouldSort = true; }
        else result = data.disclosures;

        return shouldSort ? [...result].sort((a, b) => a.company.localeCompare(b.company, 'ko')) : result;
    }, [data, filter, clusterAlert]);

    const handleFilterChange = useCallback((newFilter) => {
        setFilter(newFilter);
        setClusterAlert(null);
    }, []);

    const handleClusterClick = useCallback((alertText) => {
        if (clusterAlert === alertText) {
            setClusterAlert(null);
            setFilter('all');
        } else {
            setClusterAlert(alertText);
            setFilter('all');
        }
    }, [clusterAlert]);

    if (loading) {
        return (
            <div className="disclosures-page">
                <div className="loading-spinner"><div className="disc-spinner"></div></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="disclosures-page">
                <div className="empty-state">
                    <h3>데이터 로딩 실패</h3>
                    <p>{error}</p>
                    <p style={{ marginTop: '1rem', fontSize: '0.875rem' }}>
                        collect_disclosures.py → analyze_disclosures.py 를 먼저 실행하세요.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="disclosures-page">
            <div className="page-title-bar">
                <h1>공시 모니터링</h1>
                {data?.date && <span className="page-badge">{data.date}</span>}
            </div>

            <SentimentBanner summary={data?.summary} />
            <KPICards summary={data?.summary} onClusterClick={handleClusterClick} activeCluster={clusterAlert} />

            <div className="filter-bar">
                <button className={`filter-btn ${filter === 'all' ? 'active' : ''}`} onClick={() => handleFilterChange('all')}>전체 ({data?.summary?.total || 0})</button>
                <button className={`filter-btn ${filter === 'positive' ? 'active' : ''}`} onClick={() => handleFilterChange('positive')}>Risk-On ({data?.summary?.risk_on || 0})</button>
                <button className={`filter-btn ${filter === 'negative' ? 'active' : ''}`} onClick={() => handleFilterChange('negative')}>Risk-Off ({data?.summary?.risk_off || 0})</button>
                <button className={`filter-btn ${filter === 'neutral' ? 'active' : ''}`} onClick={() => handleFilterChange('neutral')}>Neutral ({data?.summary?.neutral || 0})</button>
                <div style={{ width: '1px', height: '24px', background: '#334155', margin: '0 0.5rem' }}></div>
                <button className={`filter-btn ${filter === 'performance' ? 'active' : ''}`} onClick={() => handleFilterChange('performance')}>실적 ({stats.performance})</button>
                <button className={`filter-btn ${filter === 'contract' ? 'active' : ''}`} onClick={() => handleFilterChange('contract')}>계약 ({stats.contract})</button>
                <button className={`filter-btn ${filter === 'lawsuit' ? 'active' : ''}`} onClick={() => handleFilterChange('lawsuit')}>소송 ({stats.lawsuit})</button>
                <button className={`filter-btn ${filter === 'suspension' ? 'active' : ''}`} onClick={() => handleFilterChange('suspension')}>거래정지 ({stats.suspension})</button>
            </div>

            <div className="disclosure-feed">
                {filteredDisclosures.length > 0 ? (
                    filteredDisclosures.map((item, idx) => (
                        <DisclosureCard key={`${item.code}-${item.time}-${idx}`} item={item} />
                    ))
                ) : (
                    <div className="empty-state"><h3>해당 분류의 공시가 없습니다</h3></div>
                )}
            </div>
        </div>
    );
};

export default Disclosures;
