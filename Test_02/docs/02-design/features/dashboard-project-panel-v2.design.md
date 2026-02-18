# Feature Design: Dashboard Project Panel v2

> Plan 문서: `docs/01-plan/features/dashboard-project-panel-v2.plan.md`
> 생성일: 2026-02-19

## 1. Design Overview

REQ-017로 구현된 프로젝트 현황 패널의 UI/UX 개편. "압축 오버뷰" 전략으로 메인 대시보드 공간을 절약하고, 상세 페이지의 빈 데이터 UX를 개선한다.

### 수정 대상 파일 (3개)

| 파일 | 변경 범위 | 라인 |
|------|-----------|------|
| `dashboard/index.html` | `ProjectStatusPanel()` 컴포넌트 + CSS 재작성 | ~955-1038 (JS), ~188-390 (CSS) |
| `dashboard/project_status.html` | `renderDetail()` 빈 필드 숨김 + 체크리스트 UX | ~362-397 (JS), 일부 CSS |
| `tests/playwright/tests/dashboard-core.spec.ts` | 변경된 data-testid 반영 | ~62-72 |

### 건드리지 않는 파일

| 파일 | 이유 |
|------|------|
| `dashboard/js/project_status_data.js` | 데이터 구조 변경 없음 |
| `scripts/sync_requests_to_dashboard.py` | 동기화 스크립트 건드리지 않기로 합의 |
| `REQUESTS.md` | REQ-017 상태 수정은 Do 단계에서 처리 |

---

## 2. Main Dashboard — ProjectStatusPanel 개편

### 2.1 Before → After 레이아웃

**Before** (현재):
```
┌─────────────────────────────────────────────────────┐
│ [전체 19] [완료 14] [개발중 4] [미착수 0]             │  ← 4열 KPI
│                                                       │
│ ┌─── 좌측: 19개 REQ 전부 나열 ───┐ ┌─ 우측 ────────┐ │
│ │ REQ-001 네이버 블로그...  완료  │ │ "상세 페이지로 │ │
│ │ REQ-002 아이디어 관리...  개발중 │ │  이동하세요"   │ │
│ │ REQ-003 Pending Packets  개발중 │ │              │ │
│ │ ...                            │ │ REQ-001 완료  │ │
│ │ REQ-019 전역 변경 가드   완료  │ │ REQ-002 개발중 │ │
│ └────────────────────────────────┘ │ ...           │ │
│                                     └──────────────┘ │
└─────────────────────────────────────────────────────┘
```

**After** (개편):
```
┌──────────────────────────────────────────────────────┐
│ 프로젝트 현황                                         │
│                                                        │
│ ████████████████████░░░░░░  73%  (14/19 완료)         │  ← Progress Bar
│ [완료 14] [진행 4] [기획 1]                            │  ← 소형 배지 행
│                                                        │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│ │ REQ-002      │ │ REQ-003      │ │ REQ-004      │   │  ← 활성 카드만
│ │ 아이디어 관리 │ │ Pending      │ │ 업황/컨센서스 │   │     (최대 5개)
│ │ ☐ 0/3  개발중│ │ ☐ 0/3  개발중│ │ ☐ 0/3  개발중│   │
│ └──────────────┘ └──────────────┘ └──────────────┘   │
│ ┌──────────────┐                                      │
│ │ REQ-006      │           전체 개발현황 보기 →        │  ← 링크
│ │ Collab-Stock │                                      │
│ │ ☐ 0/3  개발중│                                      │
│ └──────────────┘                                      │
└──────────────────────────────────────────────────────┘
```

### 2.2 컴포넌트 구조 (React JSX)

```jsx
const ProjectStatusPanel = () => {
    const total = PROJECT_STATUS_ITEMS.length;
    const completed = PROJECT_STATUS_ITEMS.filter(i => i.status === '완료').length;
    const inProgress = PROJECT_STATUS_ITEMS.filter(i => i.status === '개발중' || i.status === '진행').length;
    const planned = PROJECT_STATUS_ITEMS.filter(i => i.status === '기획').length;
    const pending = PROJECT_STATUS_ITEMS.filter(i => i.status === '미착수').length;
    const pct = total > 0 ? Math.round((completed / total) * 100) : 0;

    // 활성 항목: "개발중" 또는 "진행" 상태만 (최대 5개)
    const activeItems = PROJECT_STATUS_ITEMS
        .filter(i => i.status === '개발중' || i.status === '진행')
        .slice(0, 5);

    return (
        <div className="project-status-panel" data-testid="project-status-panel">
            {/* Progress Bar */}
            <div className="project-progress-section">
                <div className="project-progress-bar">
                    <div className="project-progress-fill"
                         style={{ width: `${pct}%` }} />
                </div>
                <span className="project-progress-text">
                    {pct}% ({completed}/{total} 완료)
                </span>
            </div>

            {/* 소형 배지 행 */}
            <div className="project-status-badges">
                <span className="project-badge badge-complete">완료 {completed}</span>
                <span className="project-badge badge-progress">진행 {inProgress}</span>
                {planned > 0 && <span className="project-badge badge-planned">기획 {planned}</span>}
                {pending > 0 && <span className="project-badge badge-pending">미착수 {pending}</span>}
            </div>

            {/* 활성 카드 그리드 또는 All Clear 메시지 */}
            {activeItems.length > 0 ? (
                <div className="project-active-grid">
                    {activeItems.map(item => {
                        const doneCount = (item.checklist || []).filter(c => c.done).length;
                        const totalCheck = (item.checklist || []).length;
                        return (
                            <a key={item.id}
                               href={`project_status.html?req=${encodeURIComponent(item.id)}`}
                               className="project-active-card"
                               data-testid={`project-checklist-${item.id}`}>
                                <div className="project-active-title">{item.title}</div>
                                <div className="project-active-meta">
                                    {totalCheck > 0
                                        ? `☑ ${doneCount}/${totalCheck}`
                                        : '체크리스트 미등록'}
                                    <span className="project-status-badge status-in-progress">
                                        {item.status === '진행' ? '개발중' : item.status}
                                    </span>
                                </div>
                            </a>
                        );
                    })}
                </div>
            ) : (
                <div className="project-all-clear">
                    All Clear! 모든 항목이 완료되었습니다.
                </div>
            )}

            {/* 전체 보기 링크 */}
            <a href="project_status.html"
               className="project-view-all"
               data-testid="project-status-open-default">
                전체 개발현황 보기 →
            </a>
        </div>
    );
};
```

### 2.3 CSS 설계

**제거할 CSS 클래스** (더 이상 사용 안 함):
- `.project-status-summary`, `.project-summary-item`, `.project-summary-label`, `.project-summary-value`
- `.project-status-layout`, `.project-checklist-list`, `.project-checklist-item`, `.project-checklist-head`, `.project-checklist-title`, `.project-checklist-meta`
- `.project-status-detail`, `.project-detail-title`, `.project-detail-meta`, `.project-detail-label`, `.project-detail-steps`, `.project-detail-step`, `.project-step-mark`, `.project-next-action`, `.project-open-link`

**신규 CSS 클래스**:

```css
/* === Progress Bar === */
.project-progress-section {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.project-progress-bar {
    flex: 1;
    height: 8px;
    background: #21262d;
    border-radius: 4px;
    overflow: hidden;
}

.project-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #238636, #2ea043);
    border-radius: 4px;
    transition: width 0.3s ease;
}

.project-progress-text {
    font-size: 0.82rem;
    font-weight: 600;
    color: #e2e8f0;
    white-space: nowrap;
}

/* === 소형 배지 행 === */
.project-status-badges {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.project-badge {
    font-size: 0.72rem;
    font-weight: 600;
    padding: 0.15rem 0.55rem;
    border-radius: 999px;
    border: 1px solid transparent;
}

.project-badge.badge-complete {
    color: #22c55e;
    background: rgba(34, 197, 94, 0.12);
    border-color: rgba(34, 197, 94, 0.35);
}

.project-badge.badge-progress {
    color: #f59e0b;
    background: rgba(245, 158, 11, 0.1);
    border-color: rgba(245, 158, 11, 0.35);
}

.project-badge.badge-planned {
    color: #60a5fa;
    background: rgba(96, 165, 250, 0.12);
    border-color: rgba(96, 165, 250, 0.35);
}

.project-badge.badge-pending {
    color: #94a3b8;
    background: rgba(148, 163, 184, 0.1);
    border-color: rgba(148, 163, 184, 0.3);
}

/* === 활성 카드 그리드 === */
.project-active-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 0.6rem;
}

.project-active-card {
    display: block;
    padding: 0.75rem;
    border-radius: 8px;
    border: 1px solid #334155;
    background: rgba(30, 41, 59, 0.35);
    color: #e2e8f0;
    text-decoration: none;
    transition: all 0.2s ease;
}

.project-active-card:hover {
    border-color: #f59e0b;
    background: rgba(245, 158, 11, 0.06);
}

.project-active-title {
    font-size: 0.8rem;
    font-weight: 600;
    color: #f8fafc;
    margin-bottom: 0.35rem;
    /* 2줄 제한 */
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.project-active-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.72rem;
    color: #94a3b8;
}

/* === All Clear === */
.project-all-clear {
    text-align: center;
    padding: 1.5rem;
    color: #22c55e;
    font-size: 0.9rem;
    font-weight: 600;
    border: 1px dashed rgba(34, 197, 94, 0.3);
    border-radius: 8px;
    background: rgba(34, 197, 94, 0.05);
}

/* === 전체 보기 링크 === */
.project-view-all {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    color: #94a3b8;
    font-size: 0.78rem;
    font-weight: 500;
    text-decoration: none;
}

.project-view-all:hover {
    color: #e2e8f0;
}

/* === 기존 유지 (배지 — 상세 페이지에서도 사용) === */
.project-status-badge { /* 기존 유지 */ }
.project-status-badge.status-complete { /* 기존 유지 */ }
.project-status-badge.status-in-progress { /* 기존 유지 */ }
.project-status-badge.status-planned { /* 기존 유지 */ }

/* === 반응형 === */
@media (max-width: 640px) {
    .project-active-grid {
        grid-template-columns: 1fr;
    }
}
```

### 2.4 data-testid 호환성

| 현재 testid | 변경 후 | 비고 |
|-------------|---------|------|
| `project-status-panel` | 유지 | 루트 컨테이너 |
| `project-checklist-REQ-XXX` | 유지 | 활성 카드에만 존재 (개발중 항목) |
| `project-status-open-default` | 유지 | "전체 보기" 링크로 이동 |
| `project-status-detail` | **삭제** | 우측 상세 패널 제거 |
| `project-status-detail-title` | **삭제** | 우측 상세 패널 제거 |

> **Playwright 테스트 영향**: `project-checklist-REQ-017`은 REQ-017이 "완료" 상태이므로 활성 카드에 표시되지 않음. 테스트에서 해당 셀렉터를 "전체 보기 → 상세 페이지" 흐름으로 변경 필요.

---

## 3. Detail Page — project_status.html 개선

### 3.1 renderDetail() 변경사항

**변경 1: 빈 필드 숨김**

```javascript
// Before: 항상 표시
els.owner.textContent = selected.owner;
els.due.textContent = selected.due;

// After: 값이 없으면 행 자체 숨김
const ownerLine = els.owner.closest('.meta-line');
const dueLine = els.due.closest('.meta-line');
if (selected.owner && selected.owner !== 'TBD' && selected.owner !== '-') {
    ownerLine.style.display = '';
    els.owner.textContent = selected.owner;
} else {
    ownerLine.style.display = 'none';
}
if (selected.due && selected.due !== '-') {
    dueLine.style.display = '';
    els.due.textContent = selected.due;
} else {
    dueLine.style.display = 'none';
}
```

**변경 2: 빈 체크리스트 처리**

```javascript
// Before: 빈 배열이면 아무것도 안 보임
(selected.checklist || []).forEach((step) => { ... });

// After: 빈 배열이면 "미등록" 메시지
const checklist = selected.checklist || [];
if (checklist.length === 0) {
    const emptyMsg = document.createElement('div');
    emptyMsg.className = 'check-empty';
    emptyMsg.textContent = '체크리스트 미등록';
    els.checklist.appendChild(emptyMsg);
} else {
    checklist.forEach((step) => { ... }); // 기존 로직 유지
}
```

**변경 3: nextAction 빈 값 숨김**

```javascript
// Before: 항상 표시
els.nextAction.textContent = `다음 조치: ${selected.nextAction || '-'}`;

// After: 값이 없으면 숨김
if (selected.nextAction && selected.nextAction !== '-') {
    els.nextAction.style.display = '';
    els.nextAction.textContent = `다음 조치: ${selected.nextAction}`;
} else {
    els.nextAction.style.display = 'none';
}
```

**변경 4: programs description 자동 라벨**

```javascript
// description이 "Related file"이면 확장자 기반 자동 라벨
const autoLabel = (program) => {
    if (program.description && program.description !== 'Related file') {
        return program.description;
    }
    const ext = program.name.split('.').pop().toLowerCase();
    const labels = {
        py: 'Python script',
        js: 'JavaScript',
        jsx: 'React component',
        ts: 'TypeScript',
        tsx: 'React TypeScript',
        html: 'HTML page',
        json: 'Configuration',
        yml: 'CI/CD workflow',
        yaml: 'CI/CD workflow',
        md: 'Documentation',
        ps1: 'PowerShell script',
        bat: 'Batch script',
        txt: 'Text file',
        css: 'Stylesheet'
    };
    return labels[ext] || 'File';
};
```

### 3.2 상세 페이지 전체 리디자인 (추가 — 2026-02-19)

**추가 변경사항 (Brain 세션 B안 채택)**:

1. **Progress Bar**: 상단 KPI 아래에 메인 대시보드와 동일한 Progress Bar 추가
2. **필터 탭**: 전체 | 진행중 | 기획 | 완료 (+ 미착수) 상태별 필터링
3. **우측 Sticky**: `.detail-grid`에 `position: sticky; top: 1.25rem; max-height: calc(100vh - 10rem); overflow-y: auto` 적용
4. **dev-meta 축약**: owner="TBD" 시 owner 텍스트 숨김 (stage만 표시)
5. **필터 URL 유지**: `?filter=개발중` 쿼리 파라미터로 필터 상태 보존
6. **모바일 대응**: 980px 이하에서 sticky 해제

**신규 CSS 클래스**:

```css
.progress-section { display: flex; align-items: center; gap: 0.75rem; }
.progress-bar { flex: 1; height: 8px; background: #21262d; border-radius: 4px; }
.progress-fill { background: linear-gradient(90deg, #238636, #2ea043); }
.filter-tabs { display: flex; gap: 0.4rem; flex-wrap: wrap; }
.filter-tab { border-radius: 999px; border: 1px solid var(--border); }
.filter-tab.is-active { background: rgba(34, 197, 94, 0.12); color: var(--accent); }
.check-empty { color: var(--muted); font-style: italic; }
.check-label-done { text-decoration: line-through; color: var(--muted); }
```

**검증 추가 항목**:

| ID | 검증 항목 | 확인 방법 |
|----|-----------|-----------|
| V-13 | 상세 페이지 Progress Bar 표시 | `.progress-bar`, `.progress-fill` 존재 |
| V-14 | 필터 탭 동작 (상태별 필터링) | `.filter-tab.is-active` + 리스트 항목 수 변화 |
| V-15 | 우측 패널 sticky 동작 | `.detail-grid` position:sticky 확인 |
| V-16 | dev-meta에서 TBD 숨김 | owner="TBD" 항목의 dev-meta에 "TBD" 미포함 |
| V-17 | 필터 URL 파라미터 지원 | `?filter=개발중` 로드 시 해당 탭 활성 |

---

## 4. Playwright 테스트 수정

### 4.1 현재 테스트 (변경 필요)

```typescript
// 현재: REQ-017 링크를 메인 대시보드에서 직접 클릭
const req017Link = page.getByTestId('project-checklist-REQ-017');
await expect(req017Link).toHaveAttribute('href', 'project_status.html?req=REQ-017');
```

### 4.2 수정 후 테스트

```typescript
// REQ-017은 "완료" 상태이므로 메인 대시보드 활성 카드에 없음
// → "전체 보기" 링크를 통해 상세 페이지 진입 후 검증
const viewAllLink = page.getByTestId('project-status-open-default');
await expect(viewAllLink).toHaveAttribute('href', 'project_status.html');

// Progress bar 존재 확인
await expect(page.locator('.project-progress-bar')).toBeVisible();

// 활성 카드 존재 확인 (개발중 항목이 있는 경우)
const activeCards = page.locator('.project-active-card');
const cardCount = await activeCards.count();
expect(cardCount).toBeGreaterThanOrEqual(0); // 0이면 All Clear

// 상세 페이지 네비게이션
await Promise.all([
    page.waitForURL('**/project_status.html'),
    viewAllLink.click(),
]);
await expect(page.getByTestId('project-status-page')).toBeVisible();

// 상세 페이지에서 REQ-017 선택 후 검증
const req017Row = page.getByTestId('project-status-row-REQ-017');
await req017Row.click();
await expect(page.getByTestId('project-status-selected-id')).toHaveText('REQ-017');
```

---

## 5. Implementation Order (Do 단계용)

| 순서 | 작업 | 파일 | 예상 변경량 |
|------|------|------|-------------|
| 1 | REQUESTS.md REQ-017 상태 불일치 수정 | `REQUESTS.md` | 1줄 |
| 2 | 메인 대시보드 CSS: 기존 제거 + 신규 추가 | `dashboard/index.html` | ~200줄 교체 |
| 3 | 메인 대시보드 JS: ProjectStatusPanel 재작성 | `dashboard/index.html` | ~80줄 교체 |
| 4 | 상세 페이지: renderDetail() + autoLabel + CSS | `dashboard/project_status.html` | ~40줄 수정 |
| 5 | Playwright 테스트 업데이트 | `tests/.../dashboard-core.spec.ts` | ~15줄 수정 |
| 6 | localhost:8080 수동 스모크 테스트 | - | 확인만 |

---

## 6. 검증 기준 (Gap Analysis용)

| ID | 검증 항목 | 확인 방법 |
|----|-----------|-----------|
| V-01 | Progress Bar가 퍼센트와 함께 표시됨 | `.project-progress-bar`, `.project-progress-fill` 존재 |
| V-02 | 소형 배지 행에 완료/진행/기획 표시 | `.project-status-badges > .project-badge` 3개 이상 |
| V-03 | 활성 카드에 "개발중/진행" 상태만 표시 | `.project-active-card` 개수 = inProgress 개수 (최대 5) |
| V-04 | 각 활성 카드에 체크리스트 진행률 표시 | `☑ done/total` 또는 `체크리스트 미등록` |
| V-05 | "전체 개발현황 보기 →" 링크 동작 | `project_status.html`로 네비게이션 |
| V-06 | 상세 페이지: owner="TBD" 행 숨김 | `.meta-line` display:none |
| V-07 | 상세 페이지: 빈 checklist에 "미등록" 표시 | `.check-empty` 존재 |
| V-08 | 상세 페이지: nextAction="-" 숨김 | `.next-action` display:none |
| V-09 | 상세 페이지: "Related file" → 자동 라벨 | `autoLabel()` 함수로 확장자 기반 라벨 |
| V-10 | Playwright 테스트 통과 | `dashboard-core.spec.ts` green |
| V-11 | 기존 다크 테마 컬러 유지 | `#0d1117`, `#21262d`, `#334155` 계열 |
| V-12 | 외부 라이브러리 추가 없음 | CSS-only progress bar |
