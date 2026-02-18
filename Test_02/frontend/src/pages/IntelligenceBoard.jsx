import React, { useState, useEffect, useCallback } from 'react';
import './IntelligenceBoard.css';

// ─── Helpers ───
function confColor(c) {
    if (c >= 0.8) return '#ef4444';
    if (c >= 0.6) return '#f59e0b';
    if (c >= 0.4) return '#94a3b8';
    return '#64748b';
}
function confLabel(c) {
    if (c >= 0.8) return 'HIGH';
    if (c >= 0.6) return 'MED';
    if (c >= 0.4) return 'LOW';
    return 'WEAK';
}
function categoryBadgeClass(cat) {
    const map = { RISK: 'badge-red', SECTOR: 'badge-blue', PORTFOLIO: 'badge-purple', THEME: 'badge-green' };
    return map[cat] || 'badge-gray';
}
function timeAgo(isoStr) {
    if (!isoStr) return '';
    const diff = (Date.now() - new Date(isoStr).getTime()) / 1000;
    if (diff < 60) return 'just now';
    if (diff < 3600) return Math.floor(diff / 60) + 'min ago';
    if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
    return Math.floor(diff / 86400) + 'd ago';
}
function formatValue(v) {
    if (v === null || v === undefined) return 'N/A';
    if (typeof v === 'number') return v.toFixed ? v.toFixed(2) : v;
    if (typeof v === 'boolean') return v ? 'Yes' : 'No';
    return String(v);
}

// ─── SignalCard ───
const SignalCard = React.memo(({ signal, isActive, onClick }) => {
    const color = confColor(signal.confidence);
    const sources = (signal.data_sources || []).join(' + ');
    const gaps = (signal.data_gaps || []).length;

    return (
        <div className={`signal-card ${isActive ? 'active' : ''}`} onClick={onClick}>
            <div className="signal-card-top">
                <span className="conf-dot" style={{ background: color }}></span>
                <span className="conf-text" style={{ color }}>{Math.round(signal.confidence * 100)}%</span>
                <span className="signal-card-title">{signal.title}</span>
            </div>
            <div className="signal-card-meta">
                <span className={`badge ${categoryBadgeClass(signal.category)}`}>{signal.category}</span>
                <span>{sources}</span>
            </div>
            {signal.suggested_action && (
                <div className="signal-card-action">{signal.suggested_action}</div>
            )}
            <div className="signal-card-bottom">
                <span>{timeAgo(signal.created_at)}</span>
                <span className="badge badge-gray">{signal.status}</span>
                {gaps > 0 && <span className="gap-warn">&#9888; gaps: {gaps}</span>}
            </div>
        </div>
    );
});

// ─── AISection ───
const AISection = ({ aiData }) => {
    if (!aiData) return <span className="ai-unavailable">No interpretation available</span>;
    return (
        <>
            {aiData.interpretation && <div className="ai-text">{aiData.interpretation}</div>}
            {aiData.hypothesis && <div className="ai-hypothesis">{aiData.hypothesis}</div>}
            {aiData.actions?.length > 0 && (
                <ul className="ai-actions">{aiData.actions.map((a, i) => <li key={i}>{a}</li>)}</ul>
            )}
            {aiData.risk_factors?.length > 0 && (
                <>
                    <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#94a3b8' }}>Risk Factors:</div>
                    <ul className="ai-actions">{aiData.risk_factors.map((r, i) => <li key={i} style={{ color: '#fbbf24' }}>{r}</li>)}</ul>
                </>
            )}
            {aiData.confidence_adjustment && aiData.confidence_adjustment !== 0 && (
                <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#94a3b8' }}>
                    AI Confidence Adjustment: <span style={{ color: aiData.confidence_adjustment > 0 ? '#22c55e' : '#ef4444' }}>
                        {aiData.confidence_adjustment > 0 ? '+' : ''}{(aiData.confidence_adjustment * 100).toFixed(0)}%
                    </span>
                </div>
            )}
            {aiData.reason && <div className="ai-unavailable">{aiData.reason}</div>}
        </>
    );
};

// ─── DetailPanel ───
const DetailPanel = ({ signal, gapResult, onRequestAI, aiLoading, onAccept, onUpdateStatus }) => {
    if (!signal) return <div className="detail-empty">Select a signal from the feed to view details</div>;

    const color = confColor(signal.confidence);
    const pct = Math.round(signal.confidence * 100);
    let aiData = null;
    if (signal.ai_interpretation) {
        try { aiData = JSON.parse(signal.ai_interpretation); } catch { aiData = { interpretation: signal.ai_interpretation }; }
    }
    const gaps = gapResult?.gaps || [];
    const recs = gapResult?.recommendations || [];
    const enrichments = gapResult?.enrichments || [];

    return (
        <div className="detail-content">
            <div className="detail-header">
                <h2>{signal.title}</h2>
                <p>{signal.description || ''}</p>
                <div className="detail-conf">
                    <span className={`badge ${categoryBadgeClass(signal.category)}`}>{signal.category}</span>
                    <span className="badge badge-gray">{signal.signal_type}</span>
                    <span className="badge badge-gray">{signal.status}</span>
                    <span style={{ color, fontWeight: 700, fontSize: '0.9rem' }}>{pct}% {confLabel(signal.confidence)}</span>
                    <div className="conf-bar-bg">
                        <div className="conf-bar" style={{ width: `${pct}%`, background: color }}></div>
                    </div>
                </div>
            </div>

            {/* Evidence */}
            <div className="detail-section">
                <div className="detail-section-header">
                    <span style={{ color: '#3b82f6' }}>&#9632;</span> Evidence Data
                </div>
                <div className="detail-section-body">
                    {(signal.evidence || []).length > 0
                        ? signal.evidence.map((e, i) => (
                            <div key={i} className="evidence-item">
                                <span className="evidence-module">{e.module}</span>
                                <span className="evidence-label">{e.label}</span>
                                <span className="evidence-value">{formatValue(e.value)}</span>
                            </div>
                        ))
                        : <span className="ai-unavailable">No evidence data</span>
                    }
                </div>
            </div>

            {/* AI Strategist */}
            <div className="detail-section">
                <div className="detail-section-header">
                    <span style={{ color: '#a855f7' }}>&#9632;</span> AI Strategist Interpretation
                    {!aiData && (
                        <button className="intel-btn intel-btn-primary" style={{ marginLeft: 'auto', fontSize: '0.7rem' }}
                            onClick={() => onRequestAI(signal.id)} disabled={aiLoading}>
                            {aiLoading ? 'Analyzing...' : 'Request AI Analysis'}
                        </button>
                    )}
                </div>
                <div className="detail-section-body">
                    {aiData ? <AISection aiData={aiData} /> : <span className="ai-unavailable">AI 해석 미요청. 버튼을 클릭하여 분석을 요청하세요.</span>}
                </div>
            </div>

            {/* Gaps & Recommendations */}
            <div className="detail-section">
                <div className="detail-section-header">
                    <span style={{ color: '#f59e0b' }}>&#9632;</span> Data Gaps & External Source Recommendations
                    <span className="badge badge-amber" style={{ marginLeft: 'auto' }}>{gaps.length} gaps</span>
                </div>
                <div className="detail-section-body">
                    {gaps.length > 0
                        ? gaps.map((g, i) => (
                            <div key={i} className="gap-item">
                                <div className="gap-module">&#9888; {g.module}</div>
                                <div className="gap-reason">{g.reason}</div>
                                {g.impact && <div className="gap-impact">{g.impact}</div>}
                            </div>
                        ))
                        : <span style={{ color: '#22c55e', fontSize: '0.85rem' }}>All data sources available</span>
                    }
                    {recs.length > 0 && (
                        <>
                            <div style={{ marginTop: '1rem', fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>Recommended External Sources</div>
                            {recs.map((r, i) => (
                                <div key={i} className="rec-item">
                                    <div className="rec-name">{r.name}</div>
                                    <div className="rec-synergy">{r.synergy}</div>
                                    <div className="rec-boost">Confidence boost: {r.confidence_boost}</div>
                                    {r.url && <div className="rec-url"><a href={r.url} target="_blank" rel="noopener noreferrer">&rarr; {r.url}</a></div>}
                                </div>
                            ))}
                        </>
                    )}
                    {enrichments.length > 0 && (
                        <>
                            <div style={{ marginTop: '1rem', fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>Enrichment Sources</div>
                            {enrichments.map((e, i) => (
                                <div key={i} className="rec-item">
                                    <div className="rec-name">{e.name}</div>
                                    <div className="rec-synergy">{e.synergy}</div>
                                    <div className="rec-boost">{e.benefit}</div>
                                </div>
                            ))}
                        </>
                    )}
                </div>
            </div>

            {/* Action Bar */}
            <div className="action-bar">
                {signal.status !== 'accepted' && signal.status !== 'rejected' ? (
                    <>
                        <button className="intel-btn intel-btn-success" onClick={() => onAccept(signal.id)}>&#10003; Accept &rarr; Create Idea</button>
                        <button className="intel-btn" onClick={() => onUpdateStatus(signal.id, 'reviewed')}>Mark Reviewed</button>
                        <button className="intel-btn intel-btn-danger" onClick={() => onUpdateStatus(signal.id, 'rejected')}>&#10005; Reject</button>
                    </>
                ) : (
                    <>
                        <span className={`badge ${signal.status === 'accepted' ? 'badge-green' : 'badge-red'}`} style={{ fontSize: '0.85rem', padding: '6px 14px' }}>
                            {signal.status === 'accepted' ? '✓ Accepted' : '✕ Rejected'}
                        </span>
                        {signal.related_idea_id && <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>&rarr; Idea #{signal.related_idea_id}</span>}
                    </>
                )}
                <span style={{ flex: 1 }}></span>
                <span style={{ fontSize: '0.7rem', color: '#475569' }}>Signal ID: {signal.signal_id}</span>
            </div>
        </div>
    );
};

// ─── Main Component ───
const IntelligenceBoard = () => {
    const [signals, setSignals] = useState([]);
    const [selectedId, setSelectedId] = useState(null);
    const [selectedSignal, setSelectedSignal] = useState(null);
    const [gapResult, setGapResult] = useState(null);
    const [filterStatus, setFilterStatus] = useState('new');
    const [filterCategory, setFilterCategory] = useState('');
    const [genStatus, setGenStatus] = useState('Ready — Click "Generate Signals" to detect cross-data patterns');
    const [feedLoading, setFeedLoading] = useState(false);
    const [detailLoading, setDetailLoading] = useState(false);
    const [aiLoading, setAiLoading] = useState(false);

    const loadSignals = useCallback(async () => {
        setFeedLoading(true);
        let url = '/api/v1/signals?limit=50';
        if (filterStatus) url += '&status=' + filterStatus;
        if (filterCategory) url += '&category=' + filterCategory;

        try {
            const res = await fetch(url);
            const data = await res.json();
            setSignals(data.signals || []);
        } catch (e) {
            setSignals([]);
            setGenStatus('API connection error: ' + e.message);
        } finally {
            setFeedLoading(false);
        }
    }, [filterStatus, filterCategory]);

    useEffect(() => { loadSignals(); }, [loadSignals]);

    const generateSignals = async () => {
        setGenStatus('Generating signals...');
        try {
            const res = await fetch('/api/v1/signals/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ days: 3 }),
            });
            const data = await res.json();
            setGenStatus(`Generated ${data.signals_count} signals at ${new Date().toLocaleTimeString()}`);
            loadSignals();
        } catch (e) {
            setGenStatus('Error: ' + e.message);
        }
    };

    const selectSignal = async (id) => {
        setSelectedId(id);
        setDetailLoading(true);
        try {
            const [sigRes, gapRes] = await Promise.all([
                fetch('/api/v1/signals/' + id),
                fetch('/api/v1/signals/' + id + '/gaps'),
            ]);
            const signal = await sigRes.json();
            const gapData = await gapRes.json();
            setSelectedSignal(signal);
            setGapResult(gapData.gaps || {});
        } catch (e) {
            setSelectedSignal(null);
            setGapResult(null);
        } finally {
            setDetailLoading(false);
        }
    };

    const requestAI = async (id) => {
        setAiLoading(true);
        try {
            await fetch('/api/v1/signals/' + id + '/interpret', { method: 'POST' });
            await selectSignal(id);
        } catch (e) {
            alert('AI analysis error: ' + e.message);
        } finally {
            setAiLoading(false);
        }
    };

    const acceptSignal = async (id) => {
        try {
            const res = await fetch('/api/v1/signals/' + id + '/accept', { method: 'POST' });
            const data = await res.json();
            if (data.idea) alert(`Idea created: #${data.idea.id} — ${data.idea.title}`);
            loadSignals();
            selectSignal(id);
        } catch (e) {
            alert('Accept error: ' + e.message);
        }
    };

    const updateStatus = async (id, status) => {
        try {
            await fetch('/api/v1/signals/' + id + '/status', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status }),
            });
            loadSignals();
            selectSignal(id);
        } catch (e) {
            alert('Status update error: ' + e.message);
        }
    };

    return (
        <div className="intel-page">
            <div className="intel-title-bar">
                <h1>Intelligence Board</h1>
                <span className="badge badge-blue">Signal Engine v1.0</span>
                <button className="intel-btn" onClick={generateSignals}>Generate Signals</button>
                <button className="intel-btn" onClick={loadSignals}>Refresh</button>
            </div>

            <div className="intel-main">
                <div className="signal-feed">
                    <div className="feed-header">
                        <h2>Signal Feed</h2>
                        <div className="feed-controls">
                            <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
                                <option value="">All Status</option>
                                <option value="new">New</option>
                                <option value="reviewed">Reviewed</option>
                                <option value="accepted">Accepted</option>
                                <option value="rejected">Rejected</option>
                            </select>
                            <select value={filterCategory} onChange={e => setFilterCategory(e.target.value)}>
                                <option value="">All Category</option>
                                <option value="RISK">RISK</option>
                                <option value="SECTOR">SECTOR</option>
                                <option value="PORTFOLIO">PORTFOLIO</option>
                                <option value="THEME">THEME</option>
                            </select>
                        </div>
                    </div>
                    <div className="generate-bar">
                        <span className="gen-status">{genStatus}</span>
                    </div>
                    <div className="feed-list">
                        {feedLoading ? (
                            <div className="intel-loading"><div className="intel-spinner"></div></div>
                        ) : signals.length === 0 ? (
                            <div className="intel-loading">No signals found. Try generating new signals.</div>
                        ) : (
                            signals.map(s => (
                                <SignalCard key={s.id} signal={s} isActive={s.id === selectedId} onClick={() => selectSignal(s.id)} />
                            ))
                        )}
                    </div>
                </div>

                <div className="detail-panel">
                    {detailLoading ? (
                        <div className="intel-loading"><div className="intel-spinner"></div> Loading...</div>
                    ) : (
                        <DetailPanel
                            signal={selectedSignal}
                            gapResult={gapResult}
                            onRequestAI={requestAI}
                            aiLoading={aiLoading}
                            onAccept={acceptSignal}
                            onUpdateStatus={updateStatus}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};

export default IntelligenceBoard;
