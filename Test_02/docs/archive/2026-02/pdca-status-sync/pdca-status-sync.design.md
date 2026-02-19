# pdca-status-sync Design Document

> **Summary**: REQ/PDCA 프로젝트 현황 통합 표시 — ID 네임스페이스 분리 + 하이브리드 merge
>
> **Project**: Stock Research ONE
> **Author**: Claude Opus 4.6
> **Date**: 2026-02-19
> **Status**: Draft
> **Plan**: `docs/01-plan/features/pdca-status-sync.plan.md`

---

## 1. System Architecture

```
┌─ Static (기존) ──────────────────────────────────────────┐
│  project_status_data.js                                   │
│    window.PROJECT_STATUS_ITEMS = [                         │
│      { id: "REQ-001", source: "req", ... },               │
│      { id: "REQ-022", source: "req", ... },               │
│    ]                                                      │
└──────────────────┬────────────────────────────────────────┘
                   │
                   │  merge (frontend)
                   │
┌─ Dynamic (신규) ─┼────────────────────────────────────────┐
│  GET /api/v1/project-status/pdca                          │
│    Response: [                                            │
│      { id: "PDCA-001", source: "pdca", ... },             │
│      { id: "PDCA-009", source: "pdca", ... },             │
│    ]                                                      │
│                                                           │
│  Sources:                                                 │
│    ├─ docs/.pdca-status.json (활성, planPath 있는 것만)    │
│    ├─ docs/archive/YYYY-MM/_INDEX.md (완료된 것)           │
│    └─ config/pdca_id_map.json (ID 고정 매핑)              │
└───────────────────────────────────────────────────────────┘
                   │
          ┌────────┴────────┐
          ▼                 ▼
  dashboard/index.html   dashboard/project_status.html
  (React: merge → render) (Vanilla JS: merge → render)
```

---

## 2. ID Namespace Design (핵심)

### 2.1 고정 ID 매핑 파일: `config/pdca_id_map.json`

```json
{
  "_comment": "PDCA feature → 고정 번호 매핑. 삭제 시 번호 재사용 금지.",
  "_nextId": 10,
  "map": {
    "stock-moat-estimator": 1,
    "evidence-based-moat": 2,
    "stock-research-dashboard": 3,
    "disclosure-monitoring": 4,
    "idea-ai-collaboration": 5,
    "oracle-earnings-integration": 6,
    "investment-intelligence-engine": 7,
    "news-intelligence-monitor": 8,
    "data-source-footer": 9
  }
}
```

**규칙**:
- 새 feature 발견 시: `_nextId` 값 할당 후 `_nextId++`
- 기존 feature 삭제 시: map에서 제거하되 번호 재사용 금지
- ID 형식: `PDCA-{번호:03d}` → PDCA-001, PDCA-002, ...
- REQ-XXX와 접두사가 다르므로 충돌 원천 차단

### 2.2 source 필드 추가

기존 `project_status_data.js` 항목에 `source: "req"` 추가 (백워드 호환: 없으면 "req" 기본값).
PDCA API 응답에는 `source: "pdca"` 포함.

---

## 3. Backend API

### 3.1 파일: `backend/app/api/project_status.py` (신규)

```python
# GET /api/v1/project-status/pdca
# Response: { "items": [...], "meta": { "total": N, "source": "pdca-status-sync" } }
```

### 3.2 로직 흐름

```
1. config/pdca_id_map.json 읽기 (없으면 자동 생성)
2. docs/.pdca-status.json 읽기
   → features 중 planPath 있는 것만 필터
   → phase → 상태 매핑
3. docs/archive/YYYY-MM/_INDEX.md 파싱
   → ### {feature-name} 패턴으로 추출
   → phase = "archived", 상태 = "완료"
4. 각 feature에 pdca_id_map에서 고정 ID 부여
   → 새 feature 발견 시 _nextId 할당 + map 갱신 + 파일 저장
5. PROJECT_STATUS_ITEMS 형식으로 변환하여 반환
```

### 3.3 Phase → 상태 매핑

| PDCA Phase | 대시보드 상태 | stage 텍스트 |
|------------|-------------|-------------|
| plan | 기획 | Plan |
| design | 설계 | Design |
| do | 개발중 | Implementation |
| check | 검증 | Verification |
| archived | 완료 | Archived |

### 3.4 PDCA Item → PROJECT_STATUS_ITEM 변환

```python
{
    "id": "PDCA-006",
    "title": "PDCA-006 oracle-earnings-integration",
    "status": "검증",           # phase → 상태 매핑
    "stage": "check",           # phase 원문
    "owner": "bkit",
    "due": "-",
    "source": "pdca",           # 출처 구분
    "matchRate": 97.5,          # PDCA 전용 (없으면 null)
    "programs": [],             # 간소화: 빈 배열 (design 파싱은 Phase 2)
    "checklist": [
        { "label": "Plan 문서 작성", "done": true },
        { "label": "Design 문서 작성", "done": true },
        { "label": "구현 (Do)", "done": true },
        { "label": "Gap Analysis (Check)", "done": true },
        { "label": "Archive", "done": false }
    ],
    "nextAction": "/pdca report oracle-earnings-integration"
}
```

**체크리스트 자동 생성 규칙**:
| 조건 | 체크 항목 | done 판정 |
|------|----------|----------|
| planPath 존재 | "Plan 문서 작성" | true |
| designPath 존재 | "Design 문서 작성" | true |
| doCompletedAt 존재 또는 phase >= do | "구현 (Do)" | phase가 do/check/archived |
| matchRate 존재 | "Gap Analysis (Check)" | true |
| phase === "archived" | "Archive" | true |

**nextAction 자동 생성 규칙**:
| Phase | nextAction |
|-------|-----------|
| plan | `/pdca design {name}` |
| design | `/pdca do {name}` |
| do | `/pdca analyze {name}` |
| check | `/pdca report {name}` |
| archived | `-` (완료) |

---

## 4. Frontend 수정

### 4.1 dashboard/index.html — ProjectStatusPanel

**변경 포인트**: `PROJECT_STATUS_ITEMS`를 정적 배열이 아닌, 정적 REQ + 동적 PDCA merge 결과로 변경.

```javascript
// 기존 (정적만)
const PROJECT_STATUS_ITEMS = Array.isArray(window.PROJECT_STATUS_ITEMS)
    ? window.PROJECT_STATUS_ITEMS.map(...)
    : [];

// 변경 (정적 + 동적 merge)
const [allItems, setAllItems] = React.useState(() => {
    const reqItems = (window.PROJECT_STATUS_ITEMS || []).map(item => ({
        ...item,
        source: item.source || 'req',
        status: item.status === '진행' ? '개발중' : item.status
    }));
    return reqItems;
});

React.useEffect(() => {
    fetch('http://localhost:8000/api/v1/project-status/pdca')
        .then(r => r.json())
        .then(data => {
            const pdcaItems = (data.items || []).map(item => ({
                ...item,
                status: item.status === '진행' ? '개발중' : item.status
            }));
            setAllItems(prev => {
                const reqItems = prev.filter(i => (i.source || 'req') === 'req');
                return [...reqItems, ...pdcaItems];
            });
        })
        .catch(() => { /* graceful: REQ만 유지 */ });
}, []);
```

**배지 색상 추가** (CSS):
```css
.project-badge.badge-pdca {
    color: #a78bfa;
    background: rgba(139, 92, 246, 0.12);
    border-color: rgba(139, 92, 246, 0.35);
}
.project-badge.badge-design {
    color: #60a5fa;
    background: rgba(96, 165, 250, 0.12);
    border-color: rgba(96, 165, 250, 0.35);
}
.project-badge.badge-check {
    color: #facc15;
    background: rgba(250, 204, 21, 0.12);
    border-color: rgba(250, 204, 21, 0.35);
}
```

**출처 배지 렌더링**: 각 카드 왼쪽에 작은 `[REQ]` / `[PDCA]` 배지 표시.

### 4.2 dashboard/project_status.html — 상세 페이지

**변경 포인트**:
1. `initialize()` 시 `/api/v1/project-status/pdca` fetch → `items` 배열에 append
2. 필터 탭에 "출처" 필터 추가: `전체 | REQ만 | PDCA만`
3. 상세 패널: PDCA 항목은 `matchRate` 표시, `nextAction`에 PDCA 명령 안내
4. getStatusBadgeClass에 "설계", "검증" 상태 추가

**수정 코드 (Vanilla JS)**:
```javascript
// initialize() 내부
const initialize = async () => {
    // 1. PDCA 데이터 fetch (실패 시 무시)
    try {
        const resp = await fetch('http://localhost:8000/api/v1/project-status/pdca');
        const data = await resp.json();
        (data.items || []).forEach(item => {
            items.push({
                ...item,
                status: item.status === '진행' ? '개발중' : item.status
            });
        });
    } catch (e) { /* graceful: REQ만 */ }

    // 2. URL params 처리 (기존 로직)
    const params = new URLSearchParams(window.location.search);
    // ...
    render();
};
```

### 4.3 CSS — 출처 배지 (양쪽 페이지 공통)

```css
.source-badge {
    font-size: 0.62rem;
    font-weight: 700;
    padding: 0.08rem 0.35rem;
    border-radius: 4px;
    margin-right: 0.35rem;
    vertical-align: middle;
}
.source-badge-req {
    color: #60a5fa;
    background: rgba(96, 165, 250, 0.15);
    border: 1px solid rgba(96, 165, 250, 0.3);
}
.source-badge-pdca {
    color: #a78bfa;
    background: rgba(139, 92, 246, 0.15);
    border: 1px solid rgba(139, 92, 246, 0.3);
}
```

---

## 5. 파일 변경 목록

| 파일 | 변경 유형 | 설명 |
|------|----------|------|
| `config/pdca_id_map.json` | **신규** | PDCA feature → 고정 ID 매핑 |
| `backend/app/api/project_status.py` | **신규** | PDCA 데이터 API endpoint (~120 lines) |
| `backend/app/main.py` | **수정** | project_status 라우터 등록 (1줄) |
| `dashboard/index.html` | **수정** | ProjectStatusPanel: useState+useEffect+merge (~30줄 변경) |
| `dashboard/project_status.html` | **수정** | initialize() async+fetch+merge (~25줄 변경) + CSS (~20줄) |

---

## 6. 정렬 규칙

통합 목록 정렬 순서:
1. **개발중** (상위 — 활성 작업)
2. **기획/설계/검증** (중간 — 계획/진행 중)
3. **완료** (하위 — 완료된 항목)

각 그룹 내에서:
- source 무관 (REQ/PDCA 혼합)
- 개발중: 원래 순서 유지
- 완료: matchRate 높은 순 (PDCA) → 일반 (REQ)

---

## 7. Graceful Degradation

| 상황 | 동작 |
|------|------|
| Backend 정상 | REQ + PDCA 통합 표시 |
| Backend 미기동/실패 | REQ만 표시, 에러 표시 없음 |
| pdca_id_map.json 없음 | API가 자동 생성 |
| .pdca-status.json 없음 | 빈 PDCA 목록 반환 |
| archive 디렉토리 없음 | 아카이브 항목 0개 |

---

## 8. Test Plan

| 테스트 | 방법 | 기대 결과 |
|--------|------|----------|
| API 응답 확인 | curl `/api/v1/project-status/pdca` | 9개 PDCA items, 각각 고유 ID |
| ID 충돌 검증 | REQ ID와 PDCA ID 비교 | 접두사 다름, 중복 0건 |
| ID 불변성 | API 2회 호출 | 동일 feature → 동일 번호 |
| index.html 통합 | 브라우저 확인 | REQ+PDCA 카드 함께 표시 |
| project_status.html 통합 | 브라우저 확인 | 필터탭에 출처 필터, 리스트에 배지 |
| Graceful degradation | Backend 중지 후 dashboard 로드 | REQ만 표시, 에러 없음 |
| 기존 테스트 회귀 | Playwright dashboard-core.spec.ts | PASS |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-19 | Initial design | Claude Opus 4.6 |
