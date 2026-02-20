/**
 * Magubal Research Platform - Main JavaScript
 */

// ==================== Configuration ====================
const API_BASE = '/api';

let myChart = null;
let currentInterval = '1d';
let currentRange = '3mo';
let serverOnline = false;
let currentSymbol = '';
let currentPrice = 0;

// Stock name mapping
const STOCK_NAME_MAP = {
    '삼성전자': '005930', '삼성': '005930',
    'SK하이닉스': '000660', '하이닉스': '000660',
    'LG에너지솔루션': '373220',
    '삼성바이오로직스': '207940', '삼성바이오': '207940',
    '현대차': '005380', '현대자동차': '005380',
    '기아': '000270',
    '셀트리온': '068270',
    '삼성SDI': '006400',
    'KB금융': '105560',
    '신한지주': '055550',
    'NAVER': '035420', '네이버': '035420',
    '카카오': '035720',
    '포스코홀딩스': '005490', '포스코': '005490',
    '현대모비스': '012330',
    'LG화학': '051910',
};

function resolveSymbol(input) {
    const trimmed = input.trim();
    if (STOCK_NAME_MAP[trimmed]) return STOCK_NAME_MAP[trimmed];
    if (/^\d{6}$/.test(trimmed)) return trimmed;
    return trimmed.toUpperCase();
}

// ==================== Initialization ====================
document.addEventListener('DOMContentLoaded', async () => {
    await loadFlywheelNav();
    await checkServerStatus();
    loadSavedStocks();
    fetchStockData();
    fetchMarketIssues();
    setupEventListeners();
});

function setupEventListeners() {
    // Search
    document.getElementById('searchInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') fetchStockData();
    });
    document.getElementById('searchBtn').addEventListener('click', fetchStockData);

    // Chart controls
    document.querySelectorAll('#intervalGroup .control-btn').forEach(btn => {
        btn.addEventListener('click', () => setMode('interval', btn.dataset.value, btn));
    });
    document.querySelectorAll('#rangeGroup .control-btn').forEach(btn => {
        btn.addEventListener('click', () => setMode('range', btn.dataset.value, btn));
    });
}

// ==================== Flywheel Navigation ====================
async function loadFlywheelNav() {
    try {
        const response = await fetch(`${API_BASE}/flywheel/stages`);
        const data = await response.json();

        if (data.success) {
            const nav = document.getElementById('flywheelNav');
            nav.innerHTML = data.stages.map((stage, i) => `
                <div class="flywheel-stage ${stage.id === data.currentStage ? 'active' : ''}" 
                     data-stage="${stage.id}" data-workflow="${stage.workflow}">
                    <span class="icon">${stage.icon}</span>
                    <span>${stage.name}</span>
                    ${i < data.stages.length - 1 ? '<span class="arrow">→</span>' : ''}
                </div>
            `).join('');

            // Add click handlers
            nav.querySelectorAll('.flywheel-stage').forEach(el => {
                el.addEventListener('click', () => selectStage(el.dataset.stage));
            });
        }
    } catch (e) {
        console.log('Flywheel nav failed:', e);
    }
}

function selectStage(stageId) {
    document.querySelectorAll('.flywheel-stage').forEach(el => {
        el.classList.toggle('active', el.dataset.stage == stageId);
    });
}

// ==================== Server Status ====================
async function checkServerStatus() {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    try {
        const response = await fetch(`${API_BASE}/health`);
        if (response.ok) {
            const data = await response.json();
            serverOnline = true;
            statusDot.className = 'status-dot online';
            statusText.textContent = `🟢 ${data.platform || 'Server'} 연결됨`;
        }
    } catch (e) {
        serverOnline = false;
        statusText.textContent = '🔴 서버 연결 실패';
    }
}

// ==================== Mode Toggle ====================
function setMode(type, value, element) {
    if (type === 'interval') currentInterval = value;
    if (type === 'range') currentRange = value;

    element.parentElement.querySelectorAll('.control-btn').forEach(btn =>
        btn.classList.remove('active'));
    element.classList.add('active');

    fetchStockData();
}

// ==================== UI Helpers ====================
function showLoading(show) {
    document.getElementById('loading').classList.toggle('show', show);
    document.getElementById('searchBtn').disabled = show;
}

function formatPrice(price, currency = 'KRW') {
    if (currency === 'KRW') {
        return price.toLocaleString('ko-KR') + '원';
    }
    return '$' + price.toFixed(2);
}

// ==================== Main Data Fetch ====================
async function fetchStockData() {
    const rawInput = document.getElementById('searchInput').value.trim();
    if (!rawInput) return;

    const symbol = resolveSymbol(rawInput);
    currentSymbol = symbol;
    showLoading(true);

    try {
        const url = `${API_BASE}/stock/${symbol}?interval=${currentInterval}&range=${currentRange}`;
        const response = await fetch(url);
        const data = await response.json();

        if (data.success) {
            currentPrice = data.currentPrice;
            updateStockDisplay(data);
            updateChart(data);
            fetchStockNews(symbol, data.name);
            fetchScenarios(symbol, data.currentPrice);
        }
    } catch (e) {
        console.error('Fetch error:', e);
    }

    showLoading(false);
}

function updateStockDisplay(data) {
    document.getElementById('stockName').textContent = data.name || data.symbol;
    document.getElementById('stockPrice').textContent = formatPrice(data.currentPrice, data.currency);

    const changeEl = document.getElementById('stockChange');
    const isUp = data.percentChange >= 0;
    changeEl.textContent = `${isUp ? '+' : ''}${data.percentChange.toFixed(2)}%`;
    changeEl.className = `stock-change ${isUp ? 'up' : 'down'}`;
}

function updateChart(data) {
    const ctx = document.getElementById('stockChart').getContext('2d');

    if (myChart) myChart.destroy();

    const isUp = data.prices[data.prices.length - 1] >= data.prices[0];
    const color = isUp ? '#10b981' : '#ef4444';

    myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: data.name,
                data: data.prices,
                borderColor: color,
                backgroundColor: `${color}15`,
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                pointHoverRadius: 5,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.04)' },
                    ticks: { color: '#64748b', maxTicksLimit: 8, font: { size: 10 } }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.04)' },
                    ticks: { color: '#64748b', font: { size: 10 } }
                }
            },
            interaction: { intersect: false, mode: 'index' }
        }
    });
}

// ==================== News ====================
async function fetchStockNews(symbol, stockName) {
    document.getElementById('newsStockName').textContent = stockName || symbol;
    document.getElementById('newsList').innerHTML = '<div class="inline-loading">뉴스를 불러오는 중...</div>';

    try {
        const response = await fetch(`${API_BASE}/data/news/${symbol}`);
        const data = await response.json();

        if (data.success && data.news.length > 0) {
            document.getElementById('newsList').innerHTML = data.news.map(item => `
                <div class="news-item" onclick="window.open('${item.link}', '_blank')">
                    <div class="news-title">${item.title}</div>
                    <div class="news-meta">
                        <span class="news-source">${item.source}</span>
                        <span>${item.time}</span>
                        ${item.importance ? `<span class="importance-badge ${item.importance.level}">${item.importance.level.toUpperCase()}</span>` : ''}
                    </div>
                </div>
            `).join('');
        } else {
            document.getElementById('newsList').innerHTML = '<div class="inline-loading">뉴스 없음</div>';
        }
    } catch (e) {
        document.getElementById('newsList').innerHTML = '<div class="inline-loading">뉴스 로드 실패</div>';
    }
}

async function fetchMarketIssues() {
    try {
        const response = await fetch(`${API_BASE}/data/market-issues`);
        const data = await response.json();

        if (data.success) {
            const issues = [...(data.issues || []), ...(data.risks || [])].slice(0, 6);
            document.getElementById('issuesList').innerHTML = issues.map(item => `
                <div class="news-item" onclick="window.open('${item.link}', '_blank')">
                    <div class="news-title">${item.title}</div>
                    <div class="news-meta">
                        <span class="news-source">${item.source}</span>
                        <span>${item.time}</span>
                    </div>
                </div>
            `).join('');
        }
    } catch (e) {
        document.getElementById('issuesList').innerHTML = '<div class="inline-loading">이슈 로드 실패</div>';
    }
}

// ==================== Scenarios ====================
async function fetchScenarios(symbol, price) {
    try {
        const response = await fetch(`${API_BASE}/decision/scenario`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, currentPrice: price })
        });
        const data = await response.json();

        if (data.success && data.scenarios) {
            document.getElementById('scenarioList').innerHTML = data.scenarios.map(s => `
                <div class="scenario-item ${s.type}">
                    <div class="scenario-name">${s.name} (${s.probability}%)</div>
                    <div class="scenario-target">목표가: ${formatPrice(s.target_price)}</div>
                </div>
            `).join('');
        }
    } catch (e) {
        console.log('Scenario fetch failed:', e);
    }
}

// ==================== Saved Stocks ====================
async function loadSavedStocks() {
    try {
        const response = await fetch(`${API_BASE}/stocks`);
        const data = await response.json();

        if (data.success && data.stocks.length > 0) {
            document.getElementById('stockTags').innerHTML = data.stocks.slice(0, 8).map(stock => `
                <div class="stock-tag" onclick="searchStock('${stock.symbol}')">
                    ${stock.name} <span class="symbol">${stock.symbol}</span>
                </div>
            `).join('');
        } else {
            document.getElementById('stockTags').innerHTML = '<span class="inline-loading">저장된 종목 없음</span>';
        }
    } catch (e) {
        document.getElementById('stockTags').innerHTML = '';
    }
}

function searchStock(symbol) {
    document.getElementById('searchInput').value = symbol;
    fetchStockData();
}
