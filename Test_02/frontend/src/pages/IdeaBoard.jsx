
import React, { useEffect, useMemo, useState } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import {
    AlertTriangle,
    CalendarClock,
    GripVertical,
    Inbox,
    Lightbulb,
    Plus,
    RefreshCw,
    Search,
    Trash2,
    UserRound,
} from 'lucide-react';

const STATUS_COLUMNS = [
    { id: 'draft', title: '초안', color: '#64748b' },
    { id: 'active', title: '검토 중', color: '#3b82f6' },
    { id: 'testing', title: '검증 중', color: '#f59e0b' },
    { id: 'validated', title: '유효', color: '#22c55e' },
    { id: 'invalidated', title: '무효', color: '#ef4444' },
    { id: 'archived', title: '보관', color: '#6b7280' },
];

const CATEGORY_OPTIONS = [
    { value: 'SECTOR', label: '섹터' },
    { value: 'US_MARKET', label: '미국시장' },
    { value: 'THEME', label: '테마' },
    { value: 'RISK', label: '리스크' },
    { value: 'NEXT_DAY', label: '내일전략' },
    { value: 'PORTFOLIO', label: '포트폴리오' },
    { value: 'AI_RESEARCH', label: 'AI리서치' },
    { value: 'CROSS', label: '크로스' },
];

const CATEGORY_COLORS = {
    SECTOR: 'bg-blue-900/70 text-blue-200',
    US_MARKET: 'bg-indigo-900/70 text-indigo-200',
    THEME: 'bg-green-900/70 text-green-200',
    RISK: 'bg-red-900/70 text-red-200',
    NEXT_DAY: 'bg-amber-900/70 text-amber-200',
    PORTFOLIO: 'bg-purple-900/70 text-purple-200',
    AI_RESEARCH: 'bg-cyan-900/70 text-cyan-200',
    CROSS: 'bg-pink-900/70 text-pink-200',
};

const TRIAGE_ACTION_OPTIONS = [
    { value: 'validate', label: '검증' },
    { value: 'extend', label: '확장' },
    { value: 'challenge', label: '반박' },
    { value: 'infer', label: '추정(추론)' },
    { value: 'synthesize', label: '종합' },
];

const LEGACY_STATUS_MAP = {
    NEW: 'draft',
    IN_PROGRESS: 'active',
    REVIEW: 'testing',
    DONE: 'validated',
};

const ACTION_TO_IDEA_STATUS = {
    validate: 'testing',
    extend: 'active',
    challenge: 'testing',
    infer: 'testing',
    synthesize: 'validated',
};
const TRIAGE_ACTION_LABELS = Object.fromEntries(TRIAGE_ACTION_OPTIONS.map((option) => [option.value, option.label]));

const AGENT_PRESETS = ['Agent-Inference', 'Agent-Research', 'Agent-Risk', 'Agent-Execution'];
const PACKET_TYPE_OPTIONS = ['시장기대', '시장우려', '섹터산업', '종목', '트랜드', '주요일정', '이슈전망'];
const CATEGORY_TO_PACKET_TYPE = {
    SECTOR: '섹터산업',
    US_MARKET: '시장기대',
    RISK: '시장우려',
    THEME: '트랜드',
    NEXT_DAY: '주요일정',
    PORTFOLIO: '종목',
    AI_RESEARCH: '이슈전망',
    CROSS: '이슈전망',
};
const HISTORY_EVENT_LABELS = {
    created: '생성',
    triaged: '즉시처리',
    status_updated: '상태변경',
    stock_pipeline_attempted: '파이프라인시도',
    idea_gate_blocked: '아이디어차단',
    consistency_alert: '일관성경고',
};

const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const apiUrl = (path) => `${API_BASE}${path}`;

const emptyForm = { title: '', content: '', category: '', priority: 3, tags: '', source: 'Manual' };

const emptyTriageForm = {
    packet_type: '이슈전망',
    action: 'validate',
    assignee_ai: '',
    due_at: '',
    note: '',
    result_summary: '',
    result_evidence: '',
    result_risks: '',
    result_next_step: '',
    result_confidence: '',
    result_industry_outlook: '',
    result_consensus_revenue: '',
    result_consensus_op_income: '',
    result_consensus_unit: '억원',
    result_scenario_bear: '',
    result_scenario_base: '',
    result_scenario_bull: '',
    result_final_comment: '',
    run_stock_pipeline: false,
    stock_ticker: '',
    stock_name: '',
    stock_year: 'auto',
    create_idea: true,
    force_create_idea: false,
    idea_priority: 3,
    idea_status: '',
};

const isDemo = (source) => {
    if (!source) return false;
    const value = String(source).toUpperCase();
    return value === 'DEMO' || value.includes('[DEMO]');
};

const statusExists = (status) => STATUS_COLUMNS.some((column) => column.id === status);

const normalizeStatus = (status) => {
    if (!status) return 'draft';
    const normalized = String(status).trim().toLowerCase();
    if (statusExists(normalized)) return normalized;

    const mapped = LEGACY_STATUS_MAP[String(status).trim().toUpperCase()];
    if (mapped && statusExists(mapped)) return mapped;
    return 'draft';
};

const normalizeIdea = (idea) => ({
    ...idea,
    status: normalizeStatus(idea.status),
    tags: Array.isArray(idea.tags) ? idea.tags : [],
});

const normalizeTriageAction = (value) => {
    if (!value) return 'validate';
    const normalized = String(value).trim().toLowerCase();
    return TRIAGE_ACTION_OPTIONS.some((item) => item.value === normalized) ? normalized : 'validate';
};

const createPacketId = () => {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
        return crypto.randomUUID();
    }
    return `pkt-${Date.now()}-${Math.random().toString(16).slice(2, 10)}`;
};

const parseJsonSafe = (rawValue) => {
    if (!rawValue || typeof rawValue !== 'string') return {};
    try {
        const parsed = JSON.parse(rawValue);
        return parsed && typeof parsed === 'object' ? parsed : {};
    } catch {
        return {};
    }
};

const extractTriageFromPacket = (packet) => {
    const payload = parseJsonSafe(packet?.content_json);
    return payload?._triage && typeof payload._triage === 'object' ? payload._triage : {};
};

const extractResultFromPacket = (packet) => {
    const triage = extractTriageFromPacket(packet);
    return triage?.result && typeof triage.result === 'object' ? triage.result : {};
};

const inferPacketTypeFromIdea = (idea) => {
    if (!idea?.category) return '이슈전망';
    if (idea.category === 'SECTOR') return '섹터산업';
    if (idea.category === 'RISK') return '시장우려';
    if (idea.category === 'US_MARKET') return '시장기대';
    return '이슈전망';
};

const repairMojibake = (value) => {
    if (!value || typeof value !== 'string') return '';
    try {
        const bytes = Uint8Array.from(Array.from(value), (char) => char.charCodeAt(0) & 0xff);
        return new TextDecoder('utf-8', { fatal: true }).decode(bytes);
    } catch {
        return value;
    }
};

const normalizePacketTypeDisplay = (value, fallbackCategory = '') => {
    const fallback = CATEGORY_TO_PACKET_TYPE[String(fallbackCategory || '').toUpperCase()] || '';
    const raw = typeof value === 'string' ? value.trim() : '';
    if (!raw) return fallback;
    if (PACKET_TYPE_OPTIONS.includes(raw)) return raw;

    const fromCategoryCode = CATEGORY_TO_PACKET_TYPE[raw.toUpperCase()];
    if (fromCategoryCode) return fromCategoryCode;

    const repaired = repairMojibake(raw);
    if (PACKET_TYPE_OPTIONS.includes(repaired)) return repaired;
    return repaired || fallback;
};

const sanitizeTimelineNote = (value) => {
    if (!value || typeof value !== 'string') return '';
    return value.trim();
};

const formatHistoryNote = (row) => {
    const noteText = sanitizeTimelineNote(row?.note);
    if (!noteText) return '';

    if (row?.event_type !== 'stock_pipeline_attempted') {
        return noteText;
    }

    try {
        const parsed = JSON.parse(noteText);
        const source = parsed?.source_ai || '-';
        const requested = parsed?.requested ? 'Y' : 'N';
        const executed = parsed?.executed ? 'Y' : 'N';
        const ticker = parsed?.ticker || '-';
        const name = parsed?.name || '-';
        const error = parsed?.error ? ` | err:${parsed.error}` : '';
        return `source:${source} | requested:${requested} | executed:${executed} | ${name}(${ticker})${error}`;
    } catch {
        return noteText;
    }
};

const sanitizeDisplayText = (value, fallback = '') => {
    if (value === null || value === undefined) return fallback;
    const raw = String(value).trim();
    if (!raw) return fallback;
    // Raw text policy: keep original text visible (including "???") and avoid masking.
    let text = repairMojibake(raw);
    text = text.replace(/\s+/g, ' ').trim();
    return text || fallback;
};
const safeResultText = (value, fallback = '-') => sanitizeDisplayText(value, fallback);

const normalizePacketItem = (packet) => {
    const payload = parseJsonSafe(packet?.content_json);
    const topicDisplay =
        sanitizeDisplayText(packet?.topic, '') ||
        sanitizeDisplayText(payload?.summary, '') ||
        'Untitled packet';
    const askDisplay =
        sanitizeDisplayText(packet?.request_ask, '') ||
        sanitizeDisplayText(payload?.request_ask, '') ||
        '요청 질문 없음';

    return {
        ...packet,
        assignee_ai: packet?.assignee_ai || null,
        due_at: packet?.due_at || null,
        triage_action: packet?.triage_action || null,
        triage_note: packet?.triage_note || null,
        packet_type: normalizePacketTypeDisplay(packet?.packet_type || payload?.packet_type, packet?.category) || null,
        work_date: packet?.work_date || (packet?.created_at ? String(packet.created_at).slice(0, 10) : null),
        topic_display: topicDisplay,
        request_ask_display: askDisplay,
    };
};
const toDateTimeLocalValue = (value) => {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '';

    const pad = (num) => String(num).padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
};

const toIsoOrNull = (value) => {
    if (!value) return null;
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return null;
    return date.toISOString();
};

const toNumberOrNull = (value) => {
    if (value === null || value === undefined) return null;
    const text = String(value).trim();
    if (!text) return null;
    const parsed = Number(text.replace(/,/g, ''));
    if (!Number.isFinite(parsed)) return null;
    return parsed;
};

const formatDateTime = (value) => {
    if (!value) return '-';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '-';
    return date.toLocaleString('ko-KR', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
    });
};

const buildTriageDefaults = (packet) => ({
    packet_type: normalizePacketTypeDisplay(
        extractTriageFromPacket(packet)?.packet_type || packet?.packet_type,
        packet?.category
    ) || '이슈전망',
    action: normalizeTriageAction(extractTriageFromPacket(packet)?.action || packet?.request_action),
    assignee_ai: extractTriageFromPacket(packet)?.assignee_ai || packet?.assignee_ai || '',
    due_at: toDateTimeLocalValue(extractTriageFromPacket(packet)?.due_at || packet?.due_at),
    note: extractTriageFromPacket(packet)?.note || packet?.triage_note || '',
    result_summary: extractResultFromPacket(packet)?.summary || '',
    result_evidence: extractResultFromPacket(packet)?.evidence || '',
    result_risks: extractResultFromPacket(packet)?.risks || '',
    result_next_step: extractResultFromPacket(packet)?.next_step || '',
    result_confidence:
        extractResultFromPacket(packet)?.confidence === 0 || extractResultFromPacket(packet)?.confidence
            ? String(extractResultFromPacket(packet).confidence)
            : '',
    result_industry_outlook: extractResultFromPacket(packet)?.industry_outlook || '',
    result_consensus_revenue:
        extractResultFromPacket(packet)?.consensus_revenue === 0 || extractResultFromPacket(packet)?.consensus_revenue
            ? String(extractResultFromPacket(packet).consensus_revenue)
            : '',
    result_consensus_op_income:
        extractResultFromPacket(packet)?.consensus_op_income === 0 || extractResultFromPacket(packet)?.consensus_op_income
            ? String(extractResultFromPacket(packet).consensus_op_income)
            : '',
    result_consensus_unit: extractResultFromPacket(packet)?.consensus_unit || '억원',
    result_scenario_bear: extractResultFromPacket(packet)?.scenario_bear || '',
    result_scenario_base: extractResultFromPacket(packet)?.scenario_base || '',
    result_scenario_bull: extractResultFromPacket(packet)?.scenario_bull || '',
    result_final_comment: extractResultFromPacket(packet)?.final_comment || '',
    run_stock_pipeline: false,
    stock_ticker: '',
    stock_name: '',
    stock_year: 'auto',
    create_idea: true,
    force_create_idea: false,
    idea_priority: 3,
    idea_status: '',
});

const categoryLabel = (value) => CATEGORY_OPTIONS.find((option) => option.value === value)?.label || value;

const IdeaBoard = () => {
    const [ideas, setIdeas] = useState([]);
    const [packets, setPackets] = useState([]);
    const [packetArchive, setPacketArchive] = useState([]);

    const [loading, setLoading] = useState(true);
    const [packetsLoading, setPacketsLoading] = useState(true);
    const [historyLoading, setHistoryLoading] = useState(false);

    const [error, setError] = useState('');
    const [packetsError, setPacketsError] = useState('');
    const [historyError, setHistoryError] = useState('');

    const [savingId, setSavingId] = useState(null);
    const [creating, setCreating] = useState(false);
    const [triageSaving, setTriageSaving] = useState(false);

    const [showForm, setShowForm] = useState(false);

    const [form, setForm] = useState(emptyForm);
    const [filters, setFilters] = useState({ status: '', category: '', query: '' });

    const [selectedPacketId, setSelectedPacketId] = useState(null);
    const [triageForm, setTriageForm] = useState(emptyTriageForm);
    const [packetHistory, setPacketHistory] = useState([]);
    const [reviewIdea, setReviewIdea] = useState(null);
    const [reviewStatus, setReviewStatus] = useState('');
    const [reviewSaving, setReviewSaving] = useState(false);

    const selectedPacket = useMemo(
        () => packets.find((packet) => packet.packet_id === selectedPacketId) || null,
        [packets, selectedPacketId]
    );
    const selectedPacketDetail = useMemo(
        () => packetArchive.find((packet) => packet.packet_id === selectedPacketId) || selectedPacket,
        [packetArchive, selectedPacket, selectedPacketId]
    );
    const selectedPacketResult = useMemo(
        () => extractResultFromPacket(selectedPacketDetail),
        [selectedPacketDetail]
    );

    const latestPacketByIdea = useMemo(() => {
        const sorted = [...packetArchive].sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
        const map = new Map();
        sorted.forEach((packet) => {
            const ideaId = Number(packet?.related_idea_id || 0);
            if (!ideaId || map.has(ideaId)) return;
            map.set(ideaId, packet);
        });
        return map;
    }, [packetArchive]);

    const reviewPackets = useMemo(() => {
        if (!reviewIdea?.id) return [];
        return [...packetArchive]
            .filter((packet) => Number(packet.related_idea_id || 0) === Number(reviewIdea.id))
            .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
    }, [packetArchive, reviewIdea]);

    const reviewLatestPacket = reviewPackets[0] || null;
    const reviewLatestTriage = useMemo(() => extractTriageFromPacket(reviewLatestPacket), [reviewLatestPacket]);
    const reviewLatestResult = useMemo(() => extractResultFromPacket(reviewLatestPacket), [reviewLatestPacket]);

    const demoCount = useMemo(() => ideas.filter((idea) => isDemo(idea.source)).length, [ideas]);

    const loadIdeas = async () => {
        setLoading(true);
        setError('');
        try {
            const response = await fetch(apiUrl('/ideas/?limit=500'));
            if (!response.ok) throw new Error(`아이디어 로딩 실패 (${response.status})`);
            const items = await response.json();
            setIdeas(items.map(normalizeIdea));
        } catch (err) {
            setError(err.message || '아이디어 로드 실패');
        } finally {
            setLoading(false);
        }
    };

    const loadPacketArchive = async () => {
        try {
            const response = await fetch(apiUrl('/api/v1/collab/packets?limit=500'));
            if (!response.ok) return;
            const items = await response.json();
            setPacketArchive((Array.isArray(items) ? items : []).map(normalizePacketItem));
        } catch {
            setPacketArchive([]);
        }
    };

    const loadPackets = async () => {
        setPacketsLoading(true);
        setPacketsError('');
        try {
            let response = await fetch(apiUrl('/api/v1/collab/inbox?status=pending&limit=200'));
            let items = [];

            if (response.ok) {
                items = await response.json();
            } else if (response.status === 404) {
                // Fallback for older backend that only exposes /packets.
                const legacyResponse = await fetch(apiUrl('/api/v1/collab/packets?status=pending&limit=200'));
                if (!legacyResponse.ok) throw new Error(`인박스 로딩 실패 (${legacyResponse.status})`);
                items = await legacyResponse.json();
                setPacketsError('구버전 백엔드입니다. 기본 패킷 목록 모드로 동작합니다.');
            } else {
                throw new Error(`인박스 로딩 실패 (${response.status})`);
            }

            const normalizedItems = (Array.isArray(items) ? items : []).map(normalizePacketItem);
            setPackets(normalizedItems);

            if (!normalizedItems.length) {
                setSelectedPacketId(null);
                setTriageForm(emptyTriageForm);
                return;
            }

            const stillSelected = normalizedItems.some((item) => item.packet_id === selectedPacketId);
            if (!stillSelected) {
                setSelectedPacketId(normalizedItems[0].packet_id);
                const selectedDetail = packetArchive.find((item) => item.packet_id === normalizedItems[0].packet_id) || normalizedItems[0];
                setTriageForm(buildTriageDefaults(selectedDetail));
            }
        } catch (err) {
            setPacketsError(err.message || '인박스 로드 실패');
        } finally {
            setPacketsLoading(false);
        }
    };

    const loadPacketHistory = async (packetId) => {
        if (!packetId) {
            setPacketHistory([]);
            setHistoryError('');
            return;
        }
        setHistoryLoading(true);
        setHistoryError('');
        try {
            const response = await fetch(apiUrl(`/api/v1/collab/packets/${packetId}/history`));
            if (response.status === 404) {
                setPacketHistory([]);
                setHistoryError('이력 API 미지원 백엔드입니다.');
                return;
            }
            if (!response.ok) throw new Error(`이력 로딩 실패 (${response.status})`);
            const rows = await response.json();
            setPacketHistory(
                (Array.isArray(rows) ? rows : []).map((row) => ({
                    ...row,
                    packet_type: normalizePacketTypeDisplay(row?.packet_type, selectedPacketDetail?.category),
                    note: sanitizeTimelineNote(row?.note),
                }))
            );
        } catch (err) {
            setHistoryError(err.message || '이력 로딩 실패');
            setPacketHistory([]);
        } finally {
            setHistoryLoading(false);
        }
    };

    useEffect(() => {
        loadIdeas();
        loadPacketArchive();
        loadPackets();
    }, []);

    useEffect(() => {
        if (!selectedPacketId) {
            setPacketHistory([]);
            setHistoryError('');
            return;
        }
        loadPacketHistory(selectedPacketId);
    }, [selectedPacketId]);

    const filteredIdeas = useMemo(() => {
        const query = filters.query.trim().toLowerCase();
        return ideas.filter((idea) => {
            if (filters.status && idea.status !== filters.status) return false;
            if (filters.category && (idea.category || '') !== filters.category) return false;
            if (!query) return true;
            return `${idea.title || ''} ${idea.content || ''} ${(idea.tags || []).join(' ')}`.toLowerCase().includes(query);
        });
    }, [ideas, filters]);

    const ideasByStatus = useMemo(() => {
        const grouped = Object.fromEntries(STATUS_COLUMNS.map((column) => [column.id, []]));
        filteredIdeas.forEach((idea) => {
            if (grouped[idea.status]) grouped[idea.status].push(idea);
        });
        return grouped;
    }, [filteredIdeas]);
    const upsertIdeaFromTriage = (ideaSummary, packet, formState) => {
        if (!ideaSummary) return;

        const incoming = normalizeIdea({
            id: ideaSummary.id,
            title: ideaSummary.title || packet.topic_display || packet.topic,
            content: packet.request_ask_display || packet.request_ask || packet.topic_display || packet.topic,
            source: `COLLAB:${packet.source_ai}`,
            category: ideaSummary.category || packet.category || null,
            status: ideaSummary.status,
            priority: ideaSummary.priority || formState.idea_priority || 3,
            tags: ['triage', formState.action],
            author: formState.assignee_ai || packet.source_ai,
        });

        setIdeas((previous) => {
            const existingIndex = previous.findIndex((idea) => idea.id === incoming.id);
            if (existingIndex < 0) return [incoming, ...previous];

            const existing = previous[existingIndex];
            const merged = normalizeIdea({
                ...existing,
                ...incoming,
                tags: Array.from(new Set([...(existing.tags || []), ...(incoming.tags || [])])),
            });

            const next = [...previous];
            next[existingIndex] = merged;
            return next;
        });
    };

    const onDragEnd = async (result) => {
        const { destination, source, draggableId } = result;
        if (!destination || destination.droppableId === source.droppableId) return;
        if (!statusExists(destination.droppableId)) return;

        const targetId = Number(draggableId);
        const fromStatus = source.droppableId;
        const toStatus = destination.droppableId;

        setSavingId(targetId);
        setError('');
        setIdeas((prev) => prev.map((idea) => (idea.id === targetId ? { ...idea, status: toStatus } : idea)));

        try {
            const response = await fetch(apiUrl(`/ideas/${targetId}`), {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: toStatus }),
            });
            if (!response.ok) throw new Error(`상태 변경 실패 (${response.status})`);

            const updated = normalizeIdea(await response.json());
            setIdeas((prev) => prev.map((idea) => (idea.id === targetId ? updated : idea)));
        } catch (err) {
            setIdeas((prev) => prev.map((idea) => (idea.id === targetId ? { ...idea, status: fromStatus } : idea)));
            setError(err.message);
        } finally {
            setSavingId(null);
        }
    };

    const handleCreate = async (event) => {
        event.preventDefault();

        const title = form.title.trim();
        const content = form.content.trim();
        if (!title || !content) {
            setError('제목과 내용을 입력하세요.');
            return;
        }

        const tags = form.tags.split(',').map((item) => item.trim()).filter(Boolean);
        const payload = {
            title,
            content,
            source: form.source || 'Manual',
            category: form.category || null,
            status: 'draft',
            priority: Number(form.priority) || 3,
            tags,
            author: 'User',
        };

        setCreating(true);
        setError('');
        try {
            const response = await fetch(apiUrl('/ideas/'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (!response.ok) throw new Error(`아이디어 생성 실패 (${response.status})`);

            const created = normalizeIdea(await response.json());
            setIdeas((prev) => [created, ...prev]);
            setForm(emptyForm);
            setShowForm(false);
        } catch (err) {
            setError(err.message);
        } finally {
            setCreating(false);
        }
    };

    const handleDelete = async (ideaId) => {
        if (!window.confirm('이 아이디어를 삭제하시겠습니까?')) return;

        const previous = ideas;
        setIdeas((prev) => prev.filter((idea) => idea.id !== ideaId));
        setSavingId(ideaId);
        setError('');

        try {
            const response = await fetch(apiUrl(`/ideas/${ideaId}`), { method: 'DELETE' });
            if (!response.ok) throw new Error(`삭제 실패 (${response.status})`);
        } catch (err) {
            setIdeas(previous);
            setError(err.message);
        } finally {
            setSavingId(null);
        }
    };

    const handleSendToInbox = async (idea) => {
        setSavingId(idea.id);
        setPacketsError('');
        setError('');
        try {
            const packetType = inferPacketTypeFromIdea(idea);
            const payload = {
                packet_id: createPacketId(),
                source_ai: 'USER',
                topic: idea.title,
                category: idea.category || null,
                packet_type: packetType,
                content_json: JSON.stringify({
                    summary: idea.content,
                    tags: idea.tags || [],
                    source_idea_id: idea.id,
                    packet_type: packetType,
                }),
                request_action: 'validate',
                request_ask: `Idea #${idea.id} 초안을 검토하고 다음 실행안을 제안하세요.`,
                related_idea_id: idea.id,
            };

            const response = await fetch(apiUrl('/api/v1/collab/packets'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (!response.ok) throw new Error(`패킷 생성 실패 (${response.status})`);

            await loadPackets();
            await loadPacketArchive();
        } catch (err) {
            setPacketsError(err.message || '인박스 패킷 생성에 실패했습니다.');
        } finally {
            setSavingId(null);
        }
    };

    const handleSelectPacket = (packet) => {
        setSelectedPacketId(packet.packet_id);
        const selectedDetail = packetArchive.find((item) => item.packet_id === packet.packet_id) || packet;
        setTriageForm(buildTriageDefaults(selectedDetail));
    };

    const handleTriageSubmit = async (event) => {
        event.preventDefault();
        if (!selectedPacket) {
            setPacketsError('선택된 패킷이 없습니다.');
            return;
        }

            const payload = {
                packet_type: triageForm.packet_type || null,
                action: triageForm.action,
                assignee_ai: triageForm.assignee_ai.trim() || null,
                due_at: toIsoOrNull(triageForm.due_at),
                note: triageForm.note.trim() || null,
                result_summary: triageForm.result_summary.trim() || null,
                result_evidence: triageForm.result_evidence.trim() || null,
                result_risks: triageForm.result_risks.trim() || null,
                result_next_step: triageForm.result_next_step.trim() || null,
                result_industry_outlook: triageForm.result_industry_outlook.trim() || null,
                result_consensus_revenue: toNumberOrNull(triageForm.result_consensus_revenue),
                result_consensus_op_income: toNumberOrNull(triageForm.result_consensus_op_income),
                result_consensus_unit: triageForm.result_consensus_unit.trim() || null,
                result_scenario_bear: triageForm.result_scenario_bear.trim() || null,
                result_scenario_base: triageForm.result_scenario_base.trim() || null,
                result_scenario_bull: triageForm.result_scenario_bull.trim() || null,
                result_final_comment: triageForm.result_final_comment.trim() || null,
                run_stock_pipeline: Boolean(triageForm.run_stock_pipeline),
                stock_ticker: triageForm.stock_ticker.trim() || null,
                stock_name: triageForm.stock_name.trim() || null,
                stock_year: triageForm.stock_year.trim() || 'auto',
                create_idea: triageForm.create_idea,
                force_create_idea: Boolean(triageForm.force_create_idea),
                idea_priority: Number(triageForm.idea_priority) || 3,
            };

            if (triageForm.result_confidence !== '') {
                payload.result_confidence = Number(triageForm.result_confidence);
            }

        if (triageForm.idea_status) {
            payload.idea_status = triageForm.idea_status;
        }

        setTriageSaving(true);
        setPacketsError('');
        setError('');

        try {
            const response = await fetch(apiUrl(`/api/v1/collab/packets/${selectedPacket.packet_id}/triage`), {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (response.status === 404) {
                // Legacy fallback: mark packet reviewed and update/create idea client-side.
                const legacyStatusResponse = await fetch(apiUrl(`/api/v1/collab/packets/${selectedPacket.packet_id}/status`), {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: 'reviewed' }),
                });
                if (!legacyStatusResponse.ok) throw new Error(`즉시 처리 실패 (${legacyStatusResponse.status})`);

                let ideaPayload = null;
                if (triageForm.create_idea) {
                    const mappedStatus = ACTION_TO_IDEA_STATUS[triageForm.action] || 'active';
                    if (selectedPacket.related_idea_id) {
                        const ideaUpdateResponse = await fetch(apiUrl(`/ideas/${selectedPacket.related_idea_id}`), {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                status: triageForm.idea_status || mappedStatus,
                                priority: Number(triageForm.idea_priority) || 3,
                                author: triageForm.assignee_ai || undefined,
                            }),
                        });
                        if (ideaUpdateResponse.ok) {
                            const idea = await ideaUpdateResponse.json();
                            ideaPayload = {
                                id: idea.id,
                                title: idea.title,
                                status: idea.status,
                                category: idea.category,
                                priority: idea.priority,
                            };
                        }
                    } else {
                        const ideaCreateResponse = await fetch(apiUrl('/ideas/'), {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                title: selectedPacket.topic_display || selectedPacket.topic,
                                content:
                                    selectedPacket.request_ask_display ||
                                    selectedPacket.request_ask ||
                                    selectedPacket.topic_display ||
                                    selectedPacket.topic,
                                source: `COLLAB:${selectedPacket.source_ai}`,
                                category: selectedPacket.category || null,
                                status: triageForm.idea_status || mappedStatus,
                                priority: Number(triageForm.idea_priority) || 3,
                                tags: ['triage', triageForm.action],
                                author: triageForm.assignee_ai || null,
                            }),
                        });
                        if (ideaCreateResponse.ok) {
                            const idea = await ideaCreateResponse.json();
                            ideaPayload = {
                                id: idea.id,
                                title: idea.title,
                                status: idea.status,
                                category: idea.category,
                                priority: idea.priority,
                            };
                        }
                    }
                }

                if (ideaPayload) {
                    upsertIdeaFromTriage(ideaPayload, selectedPacket, triageForm);
                }
                setPacketsError('구버전 백엔드 모드입니다. 담당 AI/기한 저장은 서버 업데이트 후 활성화됩니다.');
                await loadPackets();
                await loadPacketArchive();
                await loadPacketHistory(selectedPacket.packet_id);
                return;
            }

            if (!response.ok) throw new Error(`즉시 처리 실패 (${response.status})`);

            const data = await response.json();
            if (data.idea) {
                upsertIdeaFromTriage(data.idea, selectedPacket, triageForm);
            } else if (data.idea_gate && data.idea_gate.should_create === false) {
                const reasons = Array.isArray(data.idea_gate.reasons) ? data.idea_gate.reasons.join(', ') : 'gate_blocked';
                setPacketsError(`아이디어 자동등록 제외: ${reasons}`);
            }

            await loadPackets();
            await loadPacketArchive();
            await loadPacketHistory(selectedPacket.packet_id);
        } catch (err) {
            setPacketsError(err.message || '즉시 처리 중 오류가 발생했습니다.');
        } finally {
            setTriageSaving(false);
        }
    };

    const openReviewModal = (idea) => {
        setReviewIdea(idea);
        setReviewStatus(idea.status || 'draft');
    };

    const closeReviewModal = () => {
        setReviewIdea(null);
        setReviewStatus('');
        setReviewSaving(false);
    };

    const handleReviewStatusSave = async () => {
        if (!reviewIdea?.id || !reviewStatus) return;
        setReviewSaving(true);
        setError('');
        try {
            const response = await fetch(apiUrl(`/ideas/${reviewIdea.id}`), {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: reviewStatus }),
            });
            if (!response.ok) throw new Error(`상태 변경 실패 (${response.status})`);
            const updated = normalizeIdea(await response.json());
            setIdeas((prev) => prev.map((idea) => (idea.id === updated.id ? updated : idea)));
            setReviewIdea(updated);
        } catch (err) {
            setError(err.message || '상태 저장 중 오류가 발생했습니다.');
        } finally {
            setReviewSaving(false);
        }
    };

    const handleRefreshAll = () => {
        loadIdeas();
        loadPacketArchive();
        loadPackets();
        if (selectedPacketId) {
            loadPacketHistory(selectedPacketId);
        }
    };
    return (
        <div className="p-4 bg-slate-950 min-h-screen text-slate-100">
            <div className="max-w-[1800px] mx-auto">
                <div className="flex items-center justify-between gap-4 mb-4">
                    <div className="flex items-center gap-3">
                        <Lightbulb size={24} className="text-amber-400" />
                        <h1 className="text-2xl font-bold">투자 아이디어 보드</h1>
                        <span className="text-sm text-slate-400">
                            {filteredIdeas.length}건{filters.query || filters.status || filters.category ? ' (필터 적용)' : ''}
                        </span>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-sm font-medium transition-colors"
                            onClick={() => setShowForm((previous) => !previous)}
                        >
                            <Plus size={14} /> 새 아이디어
                        </button>
                        <button
                            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-sm transition-colors"
                            onClick={handleRefreshAll}
                            disabled={loading || packetsLoading}
                        >
                            <RefreshCw size={14} className={loading || packetsLoading ? 'animate-spin' : ''} />
                            {loading || packetsLoading ? '로딩...' : '새로고침'}
                        </button>
                    </div>
                </div>

                {demoCount > 0 && (
                    <div className="mb-4 px-4 py-2.5 rounded-lg bg-red-950/60 border border-red-800/50 flex items-center gap-2 text-sm">
                        <AlertTriangle size={16} className="text-red-400 flex-shrink-0" />
                        <span className="text-red-200">DEMO 데이터 {demoCount}건이 포함되어 있습니다. 실제 투자 판단에 사용하지 마세요.</span>
                    </div>
                )}

                <div className="grid grid-cols-1 xl:grid-cols-[1.7fr_1fr] gap-4 mb-4">
                    <section className="bg-slate-900/60 border border-slate-800/50 rounded-xl p-3">
                        <div className="flex items-center justify-between mb-3">
                            <h2 className="text-sm font-semibold flex items-center gap-2">
                                <Inbox size={16} className="text-sky-300" />
                                Pending Packets Inbox
                            </h2>
                            <span className="text-xs px-2 py-1 rounded-full bg-slate-800 text-slate-400">{packets.length}건</span>
                        </div>

                        <div className="mb-2 p-2 rounded bg-slate-900/70 border border-slate-800 text-[11px] text-slate-300 leading-relaxed">
                            사용순서: 1) 초안 카드에서 <span className="text-sky-300">인박스</span> 버튼 클릭
                            {' '}2) 인박스 패킷 선택
                            {' '}3) 우측에서 분류/담당 AI/기한 입력
                            {' '}4) 즉시 처리 실행
                        </div>

                        {packetsError && (
                            <div className="mb-2 p-2 rounded bg-red-900/30 border border-red-800/60 text-xs text-red-200">
                                {packetsError}
                            </div>
                        )}

                        {packetsLoading ? (
                            <div className="text-sm text-slate-400 py-8 text-center">패킷 로딩 중...</div>
                        ) : packets.length === 0 ? (
                            <div className="text-sm text-slate-500 py-8 text-center">대기 중인 패킷이 없습니다.</div>
                        ) : (
                            <div className="space-y-2 max-h-[330px] overflow-y-auto pr-1">
                                {packets.map((packet) => {
                                    const selected = selectedPacketId === packet.packet_id;
                                    return (
                                        <button
                                            key={packet.packet_id}
                                            type="button"
                                            onClick={() => handleSelectPacket(packet)}
                                            className={`w-full text-left rounded-lg border p-3 transition-colors ${
                                                selected
                                                    ? 'border-emerald-500/70 bg-slate-800/80'
                                                    : 'border-slate-700/60 bg-slate-900/40 hover:border-slate-600'
                                            }`}
                                        >
                                            <div className="flex items-start justify-between gap-2">
                                                <div className="min-w-0">
                                                    <div className="text-sm font-semibold truncate">{packet.topic_display || packet.topic}</div>
                                                    <div className="text-xs text-slate-400 mt-1 line-clamp-2">{packet.request_ask_display || packet.request_ask || '요청 질문 없음'}</div>
                                                </div>
                                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700 text-slate-200">
                                                    {packet.source_ai}
                                                </span>
                                            </div>
                                            <div className="mt-2 flex flex-wrap gap-1 text-[10px]">
                                                {packet.packet_type && (
                                                    <span className="px-1.5 py-0.5 rounded bg-violet-900/60 text-violet-200">
                                                        {packet.packet_type}
                                                    </span>
                                                )}
                                                {packet.category && (
                                                    <span className={`px-1.5 py-0.5 rounded ${CATEGORY_COLORS[packet.category] || 'bg-slate-700 text-slate-300'}`}>
                                                        {categoryLabel(packet.category)}
                                                    </span>
                                                )}
                                                {packet.request_action && (
                                                    <span className="px-1.5 py-0.5 rounded bg-emerald-900/50 text-emerald-300">
                                                        {packet.request_action}
                                                    </span>
                                                )}
                                                {packet.related_idea_id && (
                                                    <span className="px-1.5 py-0.5 rounded bg-slate-700 text-slate-300">
                                                        Idea #{packet.related_idea_id}
                                                    </span>
                                                )}
                                            </div>
                                            <div className="mt-2 text-[10px] text-slate-500">
                                                등록: {formatDateTime(packet.created_at)} | 작업일자: {packet.work_date || '-'}
                                            </div>
                                        </button>
                                    );
                                })}
                            </div>
                        )}
                    </section>

                    <section className="bg-slate-900/60 border border-slate-800/50 rounded-xl p-3">
                        <h2 className="text-sm font-semibold mb-3">즉시 처리 패널</h2>

                        {!selectedPacket ? (
                            <div className="text-sm text-slate-500 py-8 text-center">왼쪽 인박스에서 패킷을 선택하세요.</div>
                        ) : (
                            <form onSubmit={handleTriageSubmit} className="space-y-3">
                                <div className="text-xs text-slate-400 leading-relaxed p-2 rounded bg-slate-900/80 border border-slate-800/60">
                                    선택 패킷: <span className="text-slate-200">{selectedPacket.topic_display || selectedPacket.topic}</span>
                                </div>

                                <div className="text-xs text-slate-300 leading-relaxed p-2 rounded bg-slate-900/70 border border-slate-800/60">
                                    <div className="font-semibold text-slate-200 mb-1">현재 저장된 분석 참조</div>
                                    <div>업황: {safeResultText(selectedPacketResult?.industry_outlook, '-')}</div>
                                    <div>
                                        컨센서스: 매출 {selectedPacketResult?.consensus_revenue ?? '-'} {selectedPacketResult?.consensus_unit || ''}
                                        {' '}| 영업이익 {selectedPacketResult?.consensus_op_income ?? '-'} {selectedPacketResult?.consensus_unit || ''}
                                    </div>
                                    <div>
                                        시나리오: {safeResultText(selectedPacketResult?.scenario_bear, '-')} / {safeResultText(selectedPacketResult?.scenario_base, '-')} / {safeResultText(selectedPacketResult?.scenario_bull, '-')}
                                    </div>
                                    <div>최종 코멘트: {safeResultText(selectedPacketResult?.final_comment, '-')}</div>
                                </div>

                                <div className="space-y-1">
                                    <label className="text-xs text-slate-300">패킷 유형</label>
                                    <select
                                        className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm"
                                        value={triageForm.packet_type}
                                        onChange={(event) => setTriageForm((prev) => ({ ...prev, packet_type: event.target.value }))}
                                    >
                                        {PACKET_TYPE_OPTIONS.map((item) => (
                                            <option key={item} value={item}>{item}</option>
                                        ))}
                                    </select>
                                </div>

                                <div className="space-y-1">
                                    <label className="text-xs text-slate-300">분류</label>
                                    <select
                                        className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm"
                                        value={triageForm.action}
                                        onChange={(event) => setTriageForm((prev) => ({ ...prev, action: event.target.value }))}
                                    >
                                        {TRIAGE_ACTION_OPTIONS.map((option) => (
                                            <option key={option.value} value={option.value}>{option.label}</option>
                                        ))}
                                    </select>
                                </div>

                                <div className="space-y-1">
                                    <label className="text-xs text-slate-300 flex items-center gap-1"><UserRound size={12} /> 담당 AI</label>
                                    <input
                                        className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm placeholder:text-slate-500"
                                        placeholder="예: Agent-Research"
                                        value={triageForm.assignee_ai}
                                        onChange={(event) => setTriageForm((prev) => ({ ...prev, assignee_ai: event.target.value }))}
                                    />
                                    <div className="flex flex-wrap gap-1 pt-1">
                                        {AGENT_PRESETS.map((agent) => (
                                            <button
                                                key={agent}
                                                type="button"
                                                onClick={() => setTriageForm((prev) => ({ ...prev, assignee_ai: agent }))}
                                                className="px-1.5 py-0.5 text-[10px] rounded bg-slate-700 hover:bg-slate-600 text-slate-200"
                                            >
                                                {agent}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div className="space-y-1">
                                    <label className="text-xs text-slate-300 flex items-center gap-1"><CalendarClock size={12} /> 기한</label>
                                    <input
                                        type="datetime-local"
                                        className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm"
                                        value={triageForm.due_at}
                                        onChange={(event) => setTriageForm((prev) => ({ ...prev, due_at: event.target.value }))}
                                    />
                                </div>

                                <div className="space-y-1">
                                    <label className="text-xs text-slate-300">처리 메모</label>
                                    <textarea
                                        rows={2}
                                        className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm placeholder:text-slate-500 resize-none"
                                        placeholder="이 패킷을 어떻게 처리할지 요약"
                                        value={triageForm.note}
                                        onChange={(event) => setTriageForm((prev) => ({ ...prev, note: event.target.value }))}
                                    />
                                </div>

                                <div className="space-y-1">
                                    <label className="text-xs text-slate-300">AI 결과 요약</label>
                                    <textarea
                                        rows={2}
                                        className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm placeholder:text-slate-500 resize-none"
                                        placeholder="결론 요약 (예: 근거는 있으나 추가 검증 필요)"
                                        value={triageForm.result_summary}
                                        onChange={(event) => setTriageForm((prev) => ({ ...prev, result_summary: event.target.value }))}
                                    />
                                </div>

                                <div className="space-y-1">
                                    <label className="text-xs text-slate-300">핵심 근거 / 반박 포인트</label>
                                    <textarea
                                        rows={2}
                                        className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm placeholder:text-slate-500 resize-none"
                                        placeholder="핵심 근거"
                                        value={triageForm.result_evidence}
                                        onChange={(event) => setTriageForm((prev) => ({ ...prev, result_evidence: event.target.value }))}
                                    />
                                    <textarea
                                        rows={2}
                                        className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm placeholder:text-slate-500 resize-none"
                                        placeholder="반박/리스크"
                                        value={triageForm.result_risks}
                                        onChange={(event) => setTriageForm((prev) => ({ ...prev, result_risks: event.target.value }))}
                                    />
                                </div>

                                <div className="grid grid-cols-2 gap-2">
                                    <div className="space-y-1">
                                        <label className="text-xs text-slate-300">다음 액션</label>
                                        <input
                                            className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm placeholder:text-slate-500"
                                            placeholder="예: 10-Q 수치 대조"
                                            value={triageForm.result_next_step}
                                            onChange={(event) => setTriageForm((prev) => ({ ...prev, result_next_step: event.target.value }))}
                                        />
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-xs text-slate-300">신뢰도 (0-100)</label>
                                        <input
                                            type="number"
                                            min="0"
                                            max="100"
                                            className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm"
                                            value={triageForm.result_confidence}
                                            onChange={(event) => setTriageForm((prev) => ({ ...prev, result_confidence: event.target.value }))}
                                        />
                                    </div>
                                </div>

                                <div className="space-y-1">
                                    <label className="text-xs text-slate-300">업황 요약 (30일 기준)</label>
                                    <textarea
                                        rows={2}
                                        className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm placeholder:text-slate-500 resize-none"
                                        placeholder="예: 메모리 ASP 반등 + 재고 정상화 구간"
                                        value={triageForm.result_industry_outlook}
                                        onChange={(event) => setTriageForm((prev) => ({ ...prev, result_industry_outlook: event.target.value }))}
                                    />
                                </div>

                                <div className="grid grid-cols-3 gap-2">
                                    <div className="space-y-1">
                                        <label className="text-xs text-slate-300">2026E 매출</label>
                                        <input
                                            className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm placeholder:text-slate-500"
                                            placeholder="예: 3336059"
                                            value={triageForm.result_consensus_revenue}
                                            onChange={(event) => setTriageForm((prev) => ({ ...prev, result_consensus_revenue: event.target.value }))}
                                        />
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-xs text-slate-300">2026E 영업이익</label>
                                        <input
                                            className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm placeholder:text-slate-500"
                                            placeholder="예: 436011"
                                            value={triageForm.result_consensus_op_income}
                                            onChange={(event) => setTriageForm((prev) => ({ ...prev, result_consensus_op_income: event.target.value }))}
                                        />
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-xs text-slate-300">단위</label>
                                        <input
                                            className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm"
                                            placeholder="억원"
                                            value={triageForm.result_consensus_unit}
                                            onChange={(event) => setTriageForm((prev) => ({ ...prev, result_consensus_unit: event.target.value }))}
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                                    <div className="space-y-1">
                                        <label className="text-xs text-slate-300">Bear 시나리오</label>
                                        <input
                                            className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm placeholder:text-slate-500"
                                            placeholder="예: 수요 둔화, 마진 압박"
                                            value={triageForm.result_scenario_bear}
                                            onChange={(event) => setTriageForm((prev) => ({ ...prev, result_scenario_bear: event.target.value }))}
                                        />
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-xs text-slate-300">Base 시나리오</label>
                                        <input
                                            className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm placeholder:text-slate-500"
                                            placeholder="예: 완만한 회복"
                                            value={triageForm.result_scenario_base}
                                            onChange={(event) => setTriageForm((prev) => ({ ...prev, result_scenario_base: event.target.value }))}
                                        />
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-xs text-slate-300">Bull 시나리오</label>
                                        <input
                                            className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm placeholder:text-slate-500"
                                            placeholder="예: AI 수요 상향"
                                            value={triageForm.result_scenario_bull}
                                            onChange={(event) => setTriageForm((prev) => ({ ...prev, result_scenario_bull: event.target.value }))}
                                        />
                                    </div>
                                </div>

                                <div className="space-y-1">
                                    <label className="text-xs text-slate-300">최종 투자 코멘트</label>
                                    <textarea
                                        rows={2}
                                        className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm placeholder:text-slate-500 resize-none"
                                        placeholder="비워두면 시나리오/컨센서스 기반으로 자동 생성됩니다."
                                        value={triageForm.result_final_comment}
                                        onChange={(event) => setTriageForm((prev) => ({ ...prev, result_final_comment: event.target.value }))}
                                    />
                                </div>

                                <label className="flex items-center gap-2 text-xs text-slate-300">
                                    <input
                                        type="checkbox"
                                        checked={triageForm.create_idea}
                                        onChange={(event) => setTriageForm((prev) => ({ ...prev, create_idea: event.target.checked }))}
                                    />
                                    처리 결과를 아이디어 칸반에 자동 반영
                                </label>

                                <div className="grid grid-cols-2 gap-2">
                                    <div className="space-y-1">
                                        <label className="text-xs text-slate-300">아이디어 우선순위</label>
                                        <input
                                            type="number"
                                            min="1"
                                            max="5"
                                            className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm"
                                            value={triageForm.idea_priority}
                                            onChange={(event) => setTriageForm((prev) => ({ ...prev, idea_priority: event.target.value }))}
                                        />
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-xs text-slate-300">아이디어 상태(선택)</label>
                                        <select
                                            className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm"
                                            value={triageForm.idea_status}
                                            onChange={(event) => setTriageForm((prev) => ({ ...prev, idea_status: event.target.value }))}
                                        >
                                            <option value="">액션 기반 자동</option>
                                            {STATUS_COLUMNS.map((column) => (
                                                <option key={column.id} value={column.id}>{column.title}</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>

                                <button
                                    type="submit"
                                    disabled={triageSaving}
                                    className="w-full px-3 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-60 text-sm font-semibold transition-colors"
                                >
                                    {triageSaving ? '처리 중...' : '즉시 처리 실행'}
                                </button>

                                <div className="pt-2 border-t border-slate-800/70">
                                    <div className="flex items-center justify-between mb-2">
                                        <h3 className="text-xs font-semibold text-slate-300">처리 이력</h3>
                                        <span className="text-[10px] text-slate-500">{packetHistory.length}건</span>
                                    </div>

                                    {historyError && (
                                        <div className="mb-2 p-2 rounded bg-red-900/30 border border-red-800/60 text-xs text-red-200">
                                            {historyError}
                                        </div>
                                    )}

                                    {historyLoading ? (
                                        <div className="text-xs text-slate-500 py-2">이력 로딩 중...</div>
                                    ) : packetHistory.length === 0 ? (
                                        <div className="text-xs text-slate-500 py-2">기록된 이력이 없습니다.</div>
                                    ) : (
                                        <div className="space-y-2 max-h-44 overflow-y-auto pr-1">
                                            {packetHistory.map((row) => {
                                                const actionLabel = TRIAGE_ACTION_LABELS[row.action] || row.action || '-';
                                                const packetTypeLabel = normalizePacketTypeDisplay(row.packet_type, selectedPacketDetail?.category);
                                                const noteText = formatHistoryNote(row);
                                                return (
                                                    <div key={row.id} className="rounded-lg border border-slate-800 bg-slate-900/70 p-2 text-[11px]">
                                                        <div className="flex items-center justify-between">
                                                            <span className="font-semibold text-slate-200">
                                                                {HISTORY_EVENT_LABELS[row.event_type] || row.event_type}
                                                            </span>
                                                            <span className="text-slate-500">{row.work_date || '-'}</span>
                                                        </div>
                                                        <div className="mt-1 text-slate-400">
                                                            {actionLabel ? `분류:${actionLabel}` : '-'}
                                                            {packetTypeLabel ? ` | 유형:${packetTypeLabel}` : ''}
                                                            {row.assignee_ai ? ` | 담당:${row.assignee_ai}` : ''}
                                                        </div>
                                                        <div className="mt-1 text-slate-500">
                                                            기한:{' '}{row.due_at ? formatDateTime(row.due_at) : '-'} | 처리:{' '}{formatDateTime(row.created_at)}
                                                        </div>
                                                        {noteText && <div className="mt-1 text-slate-300 line-clamp-2">{noteText}</div>}
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    )}
                                </div>
                            </form>
                        )}
                    </section>
                </div>

                {showForm && (
                    <form onSubmit={handleCreate} className="bg-slate-900/80 border border-slate-700/50 rounded-xl p-4 mb-4 space-y-3">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <input
                                className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm placeholder:text-slate-500 focus:border-emerald-500 focus:outline-none"
                                placeholder="아이디어 제목"
                                value={form.title}
                                onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
                            />
                            <div className="flex gap-2">
                                <select
                                    className="flex-1 px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm"
                                    value={form.category}
                                    onChange={(event) => setForm((prev) => ({ ...prev, category: event.target.value }))}
                                >
                                    <option value="">카테고리 선택</option>
                                    {CATEGORY_OPTIONS.map((option) => (
                                        <option key={option.value} value={option.value}>{option.label}</option>
                                    ))}
                                </select>
                                <input
                                    className="w-16 px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm text-center"
                                    type="number"
                                    min="1"
                                    max="5"
                                    placeholder="P"
                                    value={form.priority}
                                    onChange={(event) => setForm((prev) => ({ ...prev, priority: event.target.value }))}
                                />
                            </div>
                        </div>

                        <textarea
                            className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm placeholder:text-slate-500 focus:border-emerald-500 focus:outline-none resize-none"
                            rows={3}
                            placeholder="투자 아이디어 내용"
                            value={form.content}
                            onChange={(event) => setForm((prev) => ({ ...prev, content: event.target.value }))}
                        />

                        <div className="flex gap-2">
                            <input
                                className="flex-1 px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm placeholder:text-slate-500"
                                placeholder="태그 (콤마 구분)"
                                value={form.tags}
                                onChange={(event) => setForm((prev) => ({ ...prev, tags: event.target.value }))}
                            />
                            <input
                                className="w-32 px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm placeholder:text-slate-500"
                                placeholder="출처"
                                value={form.source}
                                onChange={(event) => setForm((prev) => ({ ...prev, source: event.target.value }))}
                            />
                            <button
                                type="submit"
                                className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-sm font-medium disabled:opacity-50 transition-colors"
                                disabled={creating}
                            >
                                {creating ? '등록 중...' : '추가'}
                            </button>
                        </div>
                    </form>
                )}

                <div className="bg-slate-900/60 border border-slate-800/50 rounded-xl p-3 mb-4 flex flex-wrap items-center gap-2">
                    <Search size={14} className="text-slate-500" />
                    <input
                        className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-sm min-w-[200px] placeholder:text-slate-500 focus:border-blue-500 focus:outline-none"
                        placeholder="검색..."
                        value={filters.query}
                        onChange={(event) => setFilters((prev) => ({ ...prev, query: event.target.value }))}
                    />
                    <select
                        className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-sm"
                        value={filters.status}
                        onChange={(event) => setFilters((prev) => ({ ...prev, status: event.target.value }))}
                    >
                        <option value="">전체 상태</option>
                        {STATUS_COLUMNS.map((column) => (
                            <option key={column.id} value={column.id}>{column.title}</option>
                        ))}
                    </select>
                    <select
                        className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-sm"
                        value={filters.category}
                        onChange={(event) => setFilters((prev) => ({ ...prev, category: event.target.value }))}
                    >
                        <option value="">전체 카테고리</option>
                        {CATEGORY_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>{option.label}</option>
                        ))}
                    </select>
                    {(filters.query || filters.status || filters.category) && (
                        <button
                            className="text-xs text-slate-400 hover:text-slate-200 underline"
                            onClick={() => setFilters({ status: '', category: '', query: '' })}
                        >
                            필터 초기화
                        </button>
                    )}
                </div>

                {error && (
                    <div className="mb-4 p-3 rounded-lg bg-red-900/40 border border-red-500/50 text-red-200 text-sm">{error}</div>
                )}

                <DragDropContext onDragEnd={onDragEnd}>
                    <div className="flex gap-3 overflow-x-auto pb-4" style={{ scrollbarWidth: 'thin' }}>
                        {STATUS_COLUMNS.map((column) => {
                            const items = ideasByStatus[column.id] || [];
                            return (
                                <div key={column.id} className="bg-slate-900/60 border border-slate-800/50 rounded-xl p-3 w-72 flex-shrink-0">
                                    <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-800/50">
                                        <div className="flex items-center gap-2">
                                            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: column.color }} />
                                            <h3 className="text-sm font-semibold">{column.title}</h3>
                                        </div>
                                        <span className="text-xs px-1.5 py-0.5 rounded-full bg-slate-800 text-slate-400">{items.length}</span>
                                    </div>
                                    <Droppable droppableId={column.id}>
                                        {(provided, snapshot) => (
                                            <div
                                                ref={provided.innerRef}
                                                {...provided.droppableProps}
                                                className={`min-h-[100px] rounded-lg transition-colors ${snapshot.isDraggingOver ? 'bg-slate-800/40' : ''}`}
                                            >
                                                {items.map((idea, index) => {
                                                    const latestPacket = latestPacketByIdea.get(idea.id);
                                                    const latestResult = extractResultFromPacket(latestPacket);
                                                    const hasAiResult = Boolean(
                                                        latestResult?.summary || latestResult?.evidence || latestResult?.risks || latestResult?.next_step
                                                    );
                                                    const hasForecastResult = Boolean(
                                                        latestResult?.industry_outlook ||
                                                        latestResult?.consensus_revenue ||
                                                        latestResult?.consensus_op_income ||
                                                        latestResult?.scenario_bear ||
                                                        latestResult?.scenario_base ||
                                                        latestResult?.scenario_bull ||
                                                        latestResult?.final_comment
                                                    );
                                                    return (
                                                        <Draggable key={String(idea.id)} draggableId={String(idea.id)} index={index}>
                                                            {(dragProvided, dragSnapshot) => (
                                                                <div
                                                                    ref={dragProvided.innerRef}
                                                                    {...dragProvided.draggableProps}
                                                                    {...dragProvided.dragHandleProps}
                                                                    onClick={() => openReviewModal(idea)}
                                                                    className={`bg-slate-800/80 border border-slate-700/50 p-3 mb-2 rounded-lg transition-shadow cursor-pointer ${
                                                                        dragSnapshot.isDragging ? 'shadow-lg shadow-black/40 border-slate-600' : 'hover:border-slate-600'
                                                                    } ${savingId === idea.id ? 'opacity-60' : ''}`}
                                                                    title="클릭하여 AI 처리 결과 확인"
                                                                >
                                                                    <div className="flex items-start gap-2">
                                                                        <div className="mt-0.5 text-slate-600 hover:text-slate-400 cursor-grab">
                                                                            <GripVertical size={14} />
                                                                        </div>
                                                                        <div className="flex-1 min-w-0">
                                                                            <div className="flex items-start justify-between gap-1">
                                                                                <div className="font-medium text-sm leading-snug truncate">{idea.title}</div>
                                                                                <div className="flex items-center gap-1">
                                                                                    {hasAiResult && (
                                                                                        <span className="flex-shrink-0 text-[10px] px-1.5 py-0.5 rounded bg-emerald-700/70 text-emerald-100 font-semibold">
                                                                                            결과
                                                                                        </span>
                                                                                    )}
                                                                                    {hasForecastResult && (
                                                                                        <span className="flex-shrink-0 text-[10px] px-1.5 py-0.5 rounded bg-sky-700/70 text-sky-100 font-semibold">
                                                                                            전망
                                                                                        </span>
                                                                                    )}
                                                                                    {isDemo(idea.source) && (
                                                                                        <span className="flex-shrink-0 text-[10px] px-1.5 py-0.5 rounded bg-red-600 text-white font-bold">
                                                                                            DEMO
                                                                                        </span>
                                                                                    )}
                                                                                </div>
                                                                            </div>
                                                                            <div className="text-xs text-slate-400 mt-1.5 line-clamp-2">{idea.content}</div>
                                                                            <div className="mt-2 flex flex-wrap gap-1 text-[10px]">
                                                                                {idea.category && (
                                                                                    <span className={`px-1.5 py-0.5 rounded ${CATEGORY_COLORS[idea.category] || 'bg-slate-700 text-slate-300'}`}>
                                                                                        {categoryLabel(idea.category)}
                                                                                    </span>
                                                                                )}
                                                                                <span className="px-1.5 py-0.5 rounded bg-slate-700 text-slate-300">P{idea.priority || 3}</span>
                                                                                {(idea.tags || []).slice(0, 2).map((tag) => (
                                                                                    <span key={`${idea.id}-${tag}`} className="px-1.5 py-0.5 rounded bg-emerald-900/50 text-emerald-300">#{tag}</span>
                                                                                ))}
                                                                            </div>
                                                                            <div className="flex items-center justify-between mt-2">
                                                                                <span className="text-[10px] text-slate-500">{idea.source || 'Manual'}</span>
                                                                                <div className="flex items-center gap-1">
                                                                                    <button
                                                                                        className="px-1.5 py-0.5 rounded bg-sky-900/50 hover:bg-sky-800 text-[10px] text-sky-200"
                                                                                        onClick={(event) => {
                                                                                            event.stopPropagation();
                                                                                            handleSendToInbox(idea);
                                                                                        }}
                                                                                        disabled={savingId === idea.id}
                                                                                        title="인박스로 보내기"
                                                                                    >
                                                                                        인박스
                                                                                    </button>
                                                                                    <button
                                                                                        className="text-slate-600 hover:text-red-400 transition-colors"
                                                                                        onClick={(event) => {
                                                                                            event.stopPropagation();
                                                                                            handleDelete(idea.id);
                                                                                        }}
                                                                                        disabled={savingId === idea.id}
                                                                                        title="삭제"
                                                                                    >
                                                                                        <Trash2 size={12} />
                                                                                    </button>
                                                                                </div>
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            )}
                                                        </Draggable>
                                                    );
                                                })}
                                                {provided.placeholder}
                                                {items.length === 0 && !snapshot.isDraggingOver && (
                                                    <div className="text-center py-6 text-xs text-slate-600">아이디어를 여기에 드래그</div>
                                                )}
                                            </div>
                                        )}
                                    </Droppable>
                                </div>
                            );
                        })}
                    </div>
                </DragDropContext>

                {reviewIdea && (
                    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm p-4 overflow-y-auto">
                        <div className="max-w-3xl mx-auto mt-8 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl">
                            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
                                <div>
                                    <h3 className="text-lg font-semibold text-slate-100">{reviewIdea.title}</h3>
                                    <p className="text-xs text-slate-400 mt-1">
                                        진행 카드 클릭 상세보기 | 아이디어 #{reviewIdea.id}
                                    </p>
                                </div>
                                <button
                                    type="button"
                                    className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm"
                                    onClick={closeReviewModal}
                                >
                                    닫기
                                </button>
                            </div>

                            <div className="p-4 space-y-4">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                                    <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
                                        <div className="text-slate-400">현재 상태</div>
                                        <div className="text-slate-100 font-semibold mt-1">
                                            {STATUS_COLUMNS.find((column) => column.id === reviewIdea.status)?.title || reviewIdea.status}
                                        </div>
                                    </div>
                                    <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
                                        <div className="text-slate-400">카테고리 / 우선순위</div>
                                        <div className="text-slate-100 font-semibold mt-1">
                                            {(reviewIdea.category && categoryLabel(reviewIdea.category)) || '-'} / P{reviewIdea.priority || 3}
                                        </div>
                                    </div>
                                </div>

                                <div className="rounded-lg border border-slate-800 bg-slate-950/30 p-3">
                                    <h4 className="text-sm font-semibold text-slate-200 mb-2">AI 처리 결과</h4>
                                    {!reviewLatestPacket ? (
                                        <div className="text-xs text-slate-500">연결된 패킷 처리 결과가 없습니다. 먼저 인박스에서 즉시 처리를 실행하세요.</div>
                                    ) : (
                                        <div className="space-y-2 text-xs">
                                            <div className="text-slate-400">
                                                분류: {TRIAGE_ACTION_LABELS[reviewLatestTriage?.action] || reviewLatestTriage?.action || '-'}
                                                {' '}| 담당: {reviewLatestTriage?.assignee_ai || '-'}
                                                {' '}| 유형: {normalizePacketTypeDisplay(reviewLatestTriage?.packet_type || reviewLatestPacket?.packet_type, reviewLatestPacket?.category) || '-'}
                                            </div>
                                            <div className="text-slate-400">
                                                기한: {reviewLatestTriage?.due_at ? formatDateTime(reviewLatestTriage.due_at) : '-'}
                                                {' '}| 처리시각: {formatDateTime(reviewLatestPacket?.created_at)}
                                            </div>
                                            <div className="grid grid-cols-1 gap-2 pt-1">
                                                <div className="rounded border border-slate-800 bg-slate-900/50 p-2">
                                                    <div className="text-[11px] text-slate-400 mb-1">결론 요약</div>
                                                    <div className="text-slate-200">{safeResultText(reviewLatestResult?.summary, '-')}</div>
                                                </div>
                                                <div className="rounded border border-slate-800 bg-slate-900/50 p-2">
                                                    <div className="text-[11px] text-slate-400 mb-1">핵심 근거</div>
                                                    <div className="text-slate-200">{safeResultText(reviewLatestResult?.evidence, '-')}</div>
                                                </div>
                                                <div className="rounded border border-slate-800 bg-slate-900/50 p-2">
                                                    <div className="text-[11px] text-slate-400 mb-1">반박/리스크</div>
                                                    <div className="text-slate-200">{safeResultText(reviewLatestResult?.risks, '-')}</div>
                                                </div>
                                                <div className="rounded border border-slate-800 bg-slate-900/50 p-2">
                                                    <div className="text-[11px] text-slate-400 mb-1">다음 액션 / 신뢰도</div>
                                                    <div className="text-slate-200">
                                                        {safeResultText(reviewLatestResult?.next_step, '-')}
                                                        {' '}| {reviewLatestResult?.confidence === 0 || reviewLatestResult?.confidence
                                                            ? `${reviewLatestResult.confidence}/100`
                                                            : '-'}
                                                    </div>
                                                </div>
                                                <div className="rounded border border-slate-800 bg-slate-900/50 p-2">
                                                    <div className="text-[11px] text-slate-400 mb-1">업황 요약</div>
                                                    <div className="text-slate-200">{safeResultText(reviewLatestResult?.industry_outlook, '-')}</div>
                                                </div>
                                                <div className="rounded border border-slate-800 bg-slate-900/50 p-2">
                                                    <div className="text-[11px] text-slate-400 mb-1">2026E 컨센서스</div>
                                                    <div className="text-slate-200">
                                                        매출: {reviewLatestResult?.consensus_revenue ?? '-'} {reviewLatestResult?.consensus_unit || ''}
                                                        {' '}| 영업이익: {reviewLatestResult?.consensus_op_income ?? '-'} {reviewLatestResult?.consensus_unit || ''}
                                                    </div>
                                                </div>
                                                <div className="rounded border border-slate-800 bg-slate-900/50 p-2">
                                                    <div className="text-[11px] text-slate-400 mb-1">시나리오 (Bear/Base/Bull)</div>
                                                    <div className="text-slate-200">
                                                        {safeResultText(reviewLatestResult?.scenario_bear, '-')} / {safeResultText(reviewLatestResult?.scenario_base, '-')} / {safeResultText(reviewLatestResult?.scenario_bull, '-')}
                                                    </div>
                                                </div>
                                                <div className="rounded border border-slate-800 bg-slate-900/50 p-2">
                                                    <div className="text-[11px] text-slate-400 mb-1">최종 투자 코멘트</div>
                                                    <div className="text-slate-200">{safeResultText(reviewLatestResult?.final_comment, '-')}</div>
                                                </div>
                                                <div className="rounded border border-slate-800 bg-slate-900/50 p-2">
                                                    <div className="text-[11px] text-slate-400 mb-1">처리 메모</div>
                                                    <div className="text-slate-200">{safeResultText(reviewLatestTriage?.note, '-')}</div>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <div className="rounded-lg border border-slate-800 bg-slate-950/30 p-3">
                                    <h4 className="text-sm font-semibold text-slate-200 mb-2">상태 수동 이동</h4>
                                    <div className="flex flex-col sm:flex-row gap-2">
                                        <select
                                            className="flex-1 px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm"
                                            value={reviewStatus}
                                            onChange={(event) => setReviewStatus(event.target.value)}
                                        >
                                            {STATUS_COLUMNS.map((column) => (
                                                <option key={column.id} value={column.id}>{column.title}</option>
                                            ))}
                                        </select>
                                        <button
                                            type="button"
                                            className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-60 text-sm font-semibold"
                                            onClick={handleReviewStatusSave}
                                            disabled={reviewSaving}
                                        >
                                            {reviewSaving ? '저장 중...' : '상태 저장'}
                                        </button>
                                    </div>
                                    <p className="text-[11px] text-slate-500 mt-2">
                                        권장: 검토 중/검증 중 카드를 클릭해 AI 결과를 확인한 뒤 `유효` 또는 `무효`로 이동하세요.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default IdeaBoard;
