# Design: Disclosure Auto-Collect (공시 데이터 자동 수집)

> PDCA Phase: Design
> Feature: disclosure-auto-collect
> Created: 2026-02-19
> Plan Reference: `docs/01-plan/features/disclosure-auto-collect.plan.md`

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  monitor_disclosures.html                               │
│  ┌──────────────────────┐                               │
│  │ Header               │                               │
│  │  [메인] [수집▶] [새로고침]                           │
│  └──────────┬───────────┘                               │
│             │ POST /api/v1/collector/disclosure          │
│             ▼                                           │
│  ┌──────────────────────┐   ┌────────────────────────┐  │
│  │ 로딩 오버레이        │   │ 결과 토스트            │  │
│  │ (스피너+단계표시)    │   │ (성공/실패+건수)       │  │
│  └──────────────────────┘   └────────────────────────┘  │
│             │ 완료 시                                    │
│             ▼                                           │
│  fetch('data/latest_disclosures.json') → 데이터 리렌더  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Backend: collector.py                                  │
│                                                         │
│  POST /api/v1/collector/disclosure                      │
│    └─ _run_disclosure_collector()                       │
│        ├─ Step 1: collect_disclosures.main()            │
│        │   → data/disclosures/YYYY-MM-DD.json           │
│        ├─ Step 2: analyze_disclosures.analyze()         │
│        │   → dashboard/data/latest_disclosures.json     │
│        └─ Step 3: _log_collection("disclosure", ...)    │
│                                                         │
│  POST /api/v1/collector/run-all                         │
│    └─ 유동성 → 크립토 → 공시 (순차 실행)               │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Daily Scheduler                                        │
│  scripts/run_daily_collect.bat                          │
│    └─ curl POST http://localhost:8000/.../run-all       │
│    └─ Windows Task Scheduler: 매일 18:00               │
└─────────────────────────────────────────────────────────┘
```

## 2. Component Design

### 2.1 Backend: 비동기 백그라운드 수집 패턴 in `collector.py`

**위치**: `backend/app/api/collector.py` 기존 파일에 추가

> KIND 공시 스크래핑은 30~60초+ 소요되므로 HTTP 타임아웃 방지를 위해
> **백그라운드 스레드 + 폴링** 패턴을 사용한다.

**상태 관리 (모듈 레벨)**:
```python
_disclosure_task = {"running": False, "result": None, "step": "", "started_at": None}
_disclosure_lock = threading.Lock()
```

**`_run_disclosure_collector_bg()`**: 실제 수집+분석 로직 (백그라운드 스레드에서 실행)
```python
def _run_disclosure_collector_bg():
    """공시 데이터 수집 + 분석 (백그라운드 실행)."""
    # Step 1: KIND 공시 수집 → _disclosure_task["step"] = "collecting"
    # Step 2: 분석 → _disclosure_task["step"] = "analyzing"
    # 완료 → _disclosure_task["step"] = "done", result 저장
```

**`_run_disclosure_collector()`**: 스레드 시작 + 즉시 응답
```python
def _run_disclosure_collector() -> dict:
    """공시 수집을 백그라운드로 시작하고 즉시 accepted 반환."""
    # already_running 체크 (중복 실행 방지)
    # threading.Thread(target=_run_disclosure_collector_bg) 시작
    # 즉시 {"status": "accepted"} 반환
```

### 2.2 API Endpoints

**`POST /api/v1/collector/disclosure`**: 수집 트리거 (즉시 응답)
```python
@router.post("/disclosure")
async def collect_disclosure():
    """공시 데이터 수집 트리거 (백그라운드 실행, 즉시 응답)."""
    result = _run_disclosure_collector()
    return result  # {"status": "accepted"} 즉시 반환
```

**`GET /api/v1/collector/disclosure/progress`**: 진행 상태 폴링 (NEW)
```python
@router.get("/disclosure/progress")
async def get_disclosure_progress():
    """공시 수집 진행 상태 폴링."""
    # running → {"status": "running", "step": "collecting", "elapsed": 5.2}
    # completed → {"status": "completed", "result": {...}}  (1회 소비)
    # idle → {"status": "idle"}
```

### 2.3 `_run_all_collectors()` 수정

```python
def _run_all_collectors() -> dict:
    """순차 수집: 유동성 → 크립토 → 공시."""
    start = time.time()
    results = []

    result_liq = _run_liquidity_collector()
    results.append(result_liq)

    result_crypto = _run_crypto_collector()
    results.append(result_crypto)

    result_disclosure = _run_disclosure_collector()  # 추가
    results.append(result_disclosure)

    total = time.time() - start
    all_ok = all(r["status"] == "success" for r in results)
    any_ok = any(r["status"] != "failed" for r in results)

    return {
        "status": "success" if all_ok else ("partial" if any_ok else "failed"),
        "total_duration": round(total, 1),
        "collectors": results,
    }
```

### 2.4 Frontend: 수집 버튼 (Header 컴포넌트 수정)

**위치**: `dashboard/monitor_disclosures.html` Header 컴포넌트

**수정 대상**: `header-actions` 영역에 수집 버튼 추가

```jsx
// DisclosureMonitor 컴포넌트에 상태 추가
const [collecting, setCollecting] = useState(false);
const [collectStep, setCollectStep] = useState('');    // 현재 단계 표시
const [collectElapsed, setCollectElapsed] = useState(0); // 경과 시간
const [collectResult, setCollectResult] = useState(null);

// 수집 핸들러 (비동기 + 폴링 패턴)
const handleCollect = async () => {
    if (collecting) return;
    setCollecting(true);
    setCollectResult(null);
    setCollectStep('starting');
    setCollectElapsed(0);

    try {
        // 1) 백그라운드 수집 시작 (즉시 응답)
        await fetch(`${API_BASE}/api/v1/collector/disclosure`, { method: 'POST' });

        // 2) 3초 간격으로 progress 폴링
        const poll = setInterval(async () => {
            const res = await fetch(`${API_BASE}/api/v1/collector/disclosure/progress`);
            const progress = await res.json();

            if (progress.status === 'running') {
                setCollectStep(progress.step);
                setCollectElapsed(progress.elapsed);
            } else if (progress.status === 'completed') {
                clearInterval(poll);
                setCollectResult(progress.result);
                setCollecting(false);
                // 데이터 리로드
                const dataRes = await fetch('data/latest_disclosures.json?t=' + Date.now());
                setData(await dataRes.json());
            }
        }, 3000);
    } catch (err) {
        setCollectResult({ status: 'failed', error: err.message });
        setCollecting(false);
    }
};
```

**Header에 버튼 추가**:
```jsx
const Header = React.memo(({ date, onCollect, collecting, collectResult }) => (
    <div className="monitor-header">
        <div className="header-content">
            <div className="header-left">
                <div className="logo">...</div>
                <span className="page-badge">공시 모니터링{date ? ` · ${date}` : ''}</span>
            </div>
            <div className="header-actions">
                <a href="index.html" className="btn btn-back">
                    <i data-lucide="arrow-left" style={{ width: 16, height: 16 }}></i>
                    메인 대시보드
                </a>
                {/* 수집 버튼 (NEW) */}
                <button
                    className={`btn ${collecting ? 'btn-collecting' : 'btn-collect'}`}
                    onClick={onCollect}
                    disabled={collecting}
                >
                    <i data-lucide={collecting ? "loader" : "download"}
                       style={{ width: 16, height: 16 }}
                       className={collecting ? "spin" : ""}></i>
                    {collecting ? `수집 중... ${collectElapsed}s` : '데이터 수집'}
                </button>
                <button className="btn btn-secondary" onClick={() => window.location.reload()}>
                    <i data-lucide="refresh-cw" style={{ width: 16, height: 16 }}></i>
                    새로고침
                </button>
            </div>
        </div>
        {/* 수집 결과 토스트 */}
        {collectResult && (
            <div className={`collect-toast ${collectResult.status === 'failed' ? 'toast-error' : 'toast-success'}`}>
                {collectResult.status === 'failed'
                    ? `수집 실패: ${collectResult.error || '서버 오류'}`
                    : `${collectResult.status === 'partial' ? '수집 부분 완료' : '수집 완료'} (${collectResult.duration}초) — ${collectResult.steps?.collect || ''}`}
                <span style={{fontSize:'0.7rem',color:'#94a3b8',marginLeft:'0.5rem'}}>
                    15:30 이후 수집을 권장합니다
                </span>
            </div>
        )}
    </div>
));
```

### 2.5 CSS 추가

```css
/* 수집 버튼 */
.btn-collect {
    background: linear-gradient(135deg, #22c55e, #10b981);
    color: white;
    border: none;
}
.btn-collect:hover {
    background: linear-gradient(135deg, #16a34a, #059669);
    transform: translateY(-1px);
}
.btn-collecting {
    background: #1e293b;
    color: #94a3b8;
    border: 1px solid #334155;
    cursor: wait;
}

/* 스피너 애니메이션 */
.spin {
    animation: spin 1s linear infinite;
}
@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

/* 수집 결과 토스트 */
.collect-toast {
    max-width: 1400px;
    margin: 0.5rem auto 0;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-size: 0.85rem;
    text-align: center;
}
.toast-success {
    background: rgba(34, 197, 94, 0.15);
    border: 1px solid rgba(34, 197, 94, 0.3);
    color: #22c55e;
}
.toast-error {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: #ef4444;
}
```

### 2.6 배치 파일: `scripts/run_daily_collect.bat`

```bat
@echo off
REM 전체 데이터 수집 (유동성 + 크립토 + 공시)
REM Windows Task Scheduler에 매일 18:00으로 등록

echo [%date% %time%] Starting daily collection...

curl -s -X POST http://localhost:8000/api/v1/collector/run-all > "%~dp0\..\scripts\collector_log_daily.txt" 2>&1

IF %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] API call failed. Running scripts directly...
    cd /d "%~dp0\.."
    python scripts/collect_disclosures.py
    python scripts/analyze_disclosures.py
)

echo [%date% %time%] Daily collection complete.
```

## 3. Data Flow

```
[수동] UI 버튼 클릭                    [자동] Task Scheduler 18:00
       │                                      │
       ▼                                      ▼
POST /collector/disclosure          POST /collector/run-all
       │                                      │
       ▼                                      ▼
_run_disclosure_collector()         _run_all_collectors()
       │                                ├── liquidity
       ├── collect_all_pages(today)     ├── crypto
       │   → data/disclosures/          └── disclosure ←── 여기
       │     YYYY-MM-DD.json
       │
       ├── analyze(today)
       │   → dashboard/data/
       │     latest_disclosures.json
       │
       └── _log_collection()
           → collector_log 테이블
```

## 4. Implementation Order

| Step | File | 작업 | 예상 LOC |
|------|------|------|:--------:|
| 1 | `backend/app/api/collector.py` | `_run_disclosure_collector_bg()` 백그라운드 함수 | ~70 |
| 2 | `backend/app/api/collector.py` | `_run_disclosure_collector()` 스레드 시작 + 즉시 응답 | ~20 |
| 3 | `backend/app/api/collector.py` | `POST /disclosure` 엔드포인트 | ~8 |
| 4 | `backend/app/api/collector.py` | `GET /disclosure/progress` 폴링 엔드포인트 (NEW) | ~18 |
| 5 | `backend/app/api/collector.py` | `_run_all_collectors()` 수정 (disclosure 포함) | ~3 |
| 6 | `dashboard/monitor_disclosures.html` | CSS: btn-collect, spin, toast 스타일 | ~35 |
| 7 | `dashboard/monitor_disclosures.html` | Header: 수집 버튼 + 경과시간 + 토스트 | ~35 |
| 8 | `dashboard/monitor_disclosures.html` | DisclosureMonitor: 폴링 기반 handleCollect | ~40 |
| 9 | `scripts/run_daily_collect.bat` | 배치 파일 (NEW) | ~15 |
| | | **Total** | **~244** |

## 5. Error Handling

| 상황 | 처리 |
|------|------|
| Backend 서버 미실행 | fetch 실패 → toast-error "서버에 연결할 수 없습니다" |
| KIND 접속 실패 | collect_disclosures.py sample fallback → steps.collect = "sample_fallback" |
| analyze 실패 | collect 성공 데이터는 보존, toast에 "분석 실패" 표시 |
| 이미 수집 중 | `collecting` 상태로 버튼 비활성화 (중복 호출 방지) |
| run-all 중 disclosure 실패 | 다른 collector 영향 없음 (independent steps) |

## 6. API Response Format

```json
// POST /api/v1/collector/disclosure (즉시 응답)
{"status": "accepted"}
// 또는 이미 실행 중:
{"status": "already_running", "step": "collecting"}

// GET /api/v1/collector/disclosure/progress (폴링)
// 실행 중:
{"status": "running", "step": "collecting", "elapsed": 5.2}
// 완료 시 (1회 소비):
{
    "status": "completed",
    "result": {
        "collector": "disclosure",
        "status": "success",      // "success" | "partial" | "failed"
        "duration": 12.3,
        "date": "2026-02-19",
        "steps": {
            "collect": "success: 847 items",
            "analyze": "success: 847 analyzed"
        }
    }
}
// 미실행:
{"status": "idle"}
```

## 7. UI Interaction Spec

### 7.1 수집 버튼 상태
| 상태 | 버튼 텍스트 | 색상 | 아이콘 |
|------|-------------|------|--------|
| idle | "데이터 수집" | 초록 그라데이션 (#22c55e → #10b981) | download |
| collecting | "수집 중..." | 회색 (#1e293b) disabled | loader (spin) |

### 7.2 토스트 메시지
| 결과 | 색상 | 메시지 |
|------|------|--------|
| success | 초록 | "수집 완료 (12.3초) — success: 847 items" |
| partial | 초록 | "수집 부분 완료 (12.3초) — ..." |
| failed | 빨강 | "수집 실패: 서버 오류" |

### 7.3 토스트 자동 숨김
- 성공: 8초 후 자동 사라짐
- 실패: 수동 닫기 (클릭 시 사라짐)

## 8. Task Scheduler 설정 가이드

```
프로그램: C:\...\scripts\run_daily_collect.bat
트리거: 매일 18:00
조건: 네트워크 연결 시에만 실행
설정: 실패 시 1시간 후 재시도 (최대 3회)
```
