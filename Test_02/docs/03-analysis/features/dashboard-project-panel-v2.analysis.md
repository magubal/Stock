# Gap Analysis: dashboard-project-panel-v2

> **Summary**: Design vs Implementation gap analysis for Dashboard Project Panel v2 (REQ-017 UX overhaul)
>
> **Author**: gap-detector
> **Created**: 2026-02-19
> **Last Modified**: 2026-02-19
> **Status**: Approved

---

## Analysis Overview

- **Analysis Target**: dashboard-project-panel-v2
- **Design Document**: `docs/02-design/features/dashboard-project-panel-v2.design.md`
- **Implementation Paths**:
  - `dashboard/index.html` (ProjectStatusPanel component + CSS)
  - `dashboard/project_status.html` (detail page full redesign)
  - `tests/playwright/tests/dashboard-core.spec.ts`
  - `tests/playwright/tests/project-status-page.spec.ts`
  - `REQUESTS.md` (REQ-017 status)
- **Analysis Date**: 2026-02-19
- **Design Verification Criteria**: V-01 through V-17 (Section 6 + Section 3.2)

---

## Overall Scores

| Category | Score | Status |
|----------|:-----:|:------:|
| Design Match (V-01~V-12) | 100% | PASS |
| Detail Page Redesign (V-13~V-17) | 100% | PASS |
| Additional Improvements | 100% | PASS |
| **Overall** | **100% (17/17)** | **PASS** |

---

## V-01 ~ V-12: Main Dashboard + Detail Page Base

### V-01: Progress Bar displays with percentage -- PASS

`.project-progress-bar` and `.project-progress-fill` exist in `dashboard/index.html:200-213`. JSX renders `{pct}% ({completed}/{total} ...)` at lines 911-918. Exact match to design Section 2.2.

### V-02: Small badge row shows complete/progress/planned -- PASS

`.project-status-badges` with 4 badge variants defined in CSS (lines 222-258). JSX renders 3+ badges with conditional planned/pending (lines 920-925). Match to design Section 2.2.

### V-03: Active cards show only "in-progress" items (max 5) -- PASS

Filter `.filter(i => status === '...' || '...')` and `.slice(0, 5)` at lines 905-907. Current data: 4 active items (REQ-002, 003, 004, 006). Match to design.

### V-04: Each active card shows checklist progress -- PASS

`doneCount/totalCheck` or fallback text at lines 930-941. All active items show `0/3`. Match to design.

### V-05: "View all" link navigates to project_status.html -- PASS

`<a href="project_status.html" data-testid="project-status-open-default">` at lines 956-958. Match to design.

### V-06: Detail page hides owner="TBD" rows -- PASS

`ownerLine.style.display = 'none'` when owner is "TBD" or "-" at `project_status.html:529-535`. Match to design Section 3.1.

### V-07: Empty checklist shows "not registered" message -- PASS

`.check-empty` class with "체크리스트 미등록" at `project_status.html:297-302` (CSS) and `554-558` (JS). Match to design.

### V-08: Detail page hides nextAction="-" -- PASS

`els.nextAction.style.display = 'none'` when "-" at `project_status.html:569-574`. Match to design Section 3.1.

### V-09: "Related file" auto-label by extension -- PASS

`autoLabel()` function at `project_status.html:496-509` with 14 extension mappings. Match to design Section 3.1.

### V-10: Playwright tests updated -- PASS

`dashboard-core.spec.ts` checks `.project-progress-bar`, navigates via `project-status-open-default`, clicks "전체" filter tab, then selects REQ-017. `project-status-page.spec.ts` uses `?filter=all` for full-list test. Both aligned with implementation.

### V-11: Dark theme colors maintained -- PASS

`#21262d`, `#334155`, `#238636`/`#2ea043` gradient, `#22c55e`, `#f59e0b`, `#60a5fa`, `#94a3b8` all present. Consistent with existing dashboard dark theme.

### V-12: No external libraries added -- PASS

Script imports unchanged (React 18, Babel, Chart.js, Lucide). Progress bar is CSS-only.

---

## V-13 ~ V-17: Detail Page Full Redesign

### V-13: Detail page Progress Bar -- PASS

**Requirement**: `.progress-bar`, `.progress-fill` exist in `project_status.html`.

**Evidence** (`project_status.html`):

CSS (lines 95-122):
```css
.progress-section { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }
.progress-bar { flex: 1; height: 8px; background: #21262d; border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #238636, #2ea043); ... }
```

HTML (lines 356-359):
```html
<section class="progress-section" id="progress-section">
    <div class="progress-bar"><div class="progress-fill" id="progress-fill"></div></div>
    <span class="progress-text" id="progress-text">0%</span>
</section>
```

JS (lines 439-441): Calculates `pct`, sets `progressFill.style.width` and text.

Match to design Section 3.2 item 1.

---

### V-14: Filter tabs with status filtering -- PASS

**Requirement**: `.filter-tab.is-active` + list item count changes per filter.

**Evidence** (`project_status.html`):

CSS (lines 124-152): `.filter-tabs`, `.filter-tab`, `.filter-tab.is-active` with green accent.

JS (lines 443-462): Dynamic filter tab generation:
```javascript
const filters = [
    { key: 'all', label: '전체 ' + items.length },
    { key: '개발중', label: '개발중 ' + inProgress },
    { key: '기획', label: '기획 ' + planned },
    { key: '완료', label: '완료 ' + completed }
];
if (pending > 0) filters.push({ key: '미착수', label: '미착수 ' + pending });
```

JS (lines 465-469): `renderList()` filters items by `state.filter`.

Default filter: `'개발중'` (line 399) -- user-requested change from `'all'`.

Match to design Section 3.2 item 2. Label naming unified to "개발중" (was "진행중").

---

### V-15: Right panel sticky behavior -- PASS

**Requirement**: `.detail-grid` has `position: sticky; top: 1.25rem; max-height: calc(100vh - 10rem); overflow-y: auto`.

**Evidence** (`project_status.html`, lines 239-248):
```css
.detail-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
    position: sticky;
    top: 1.25rem;
    max-height: calc(100vh - 10rem);
    overflow-y: auto;
    align-self: start;
}
```

Mobile breakpoint (lines 326-330): Removes sticky at `max-width: 980px`.

Match to design Section 3.2 items 3 and 6.

---

### V-16: dev-meta hides TBD owner -- PASS

**Requirement**: owner="TBD" items should not show "TBD" in dev-meta section of list items.

**Evidence** (`project_status.html`, lines 478-479):
```javascript
const ownerText = (item.owner && item.owner !== 'TBD' && item.owner !== '-')
    ? ' · ' + item.owner : '';
// ...
button.innerHTML = `<div class="dev-meta">${item.stage}${ownerText}</div>`;
```

When owner is "TBD", `ownerText` is empty. Only `item.stage` is shown.

Match to design Section 3.2 item 4.

---

### V-17: Filter URL parameter support -- PASS

**Requirement**: `?filter=개발중` loads with that filter active.

**Evidence** (`project_status.html`, lines 583-589):
```javascript
const initialize = () => {
    const params = new URLSearchParams(window.location.search);
    const filterParam = params.get('filter');
    if (filterParam && ['all', '개발중', '기획', '완료', '미착수'].includes(filterParam)) {
        state.filter = filterParam;
    }
    // ...
};
```

`project-status-page.spec.ts` line 5 uses `?filter=all` to override default, confirming URL param works.

Match to design Section 3.2 item 5.

---

## Additional Changes (Post-Design)

These changes were made after the design document's initial V-13~V-17 section and represent user-requested refinements:

| Change | File | Detail | Impact |
|--------|------|--------|--------|
| Default filter `'개발중'` | `project_status.html:399` | Changed from `'all'` to `'개발중'` | Positive -- shows actionable items first |
| Filter label unification | `project_status.html:445` | `'진행중'` -> `'개발중'` | Positive -- consistent naming with badges |
| Test filter override | `project-status-page.spec.ts:5` | Added `?filter=all` to test URL | Required -- REQ-015 is "완료" status |
| Test filter tab click | `dashboard-core.spec.ts:72-73` | Click "전체" filter before selecting REQ-017 | Required -- REQ-017 is "완료" status |

---

## Verification Summary

| ID | Verification Item | Result | Evidence File:Line |
|----|-------------------|:------:|-------------------|
| V-01 | Progress Bar with percentage | PASS | `index.html:200-218, 911-918` |
| V-02 | Badge row (complete/progress/planned) | PASS | `index.html:222-258, 920-925` |
| V-03 | Active cards = in-progress only (max 5) | PASS | `index.html:905-907` |
| V-04 | Checklist progress on each card | PASS | `index.html:930-941` |
| V-05 | "View all" link to project_status.html | PASS | `index.html:956-958` |
| V-06 | Hide owner="TBD" rows | PASS | `project_status.html:529-535` |
| V-07 | Empty checklist "not registered" | PASS | `project_status.html:554-558` |
| V-08 | Hide nextAction="-" | PASS | `project_status.html:569-574` |
| V-09 | "Related file" auto-label | PASS | `project_status.html:496-509` |
| V-10 | Playwright tests updated | PASS | `dashboard-core.spec.ts, project-status-page.spec.ts` |
| V-11 | Dark theme colors maintained | PASS | `index.html:203, 270, +15 refs` |
| V-12 | No external libraries added | PASS | `index.html:7-11` |
| V-13 | Detail page Progress Bar | PASS | `project_status.html:95-122, 356-359` |
| V-14 | Filter tabs (status filtering) | PASS | `project_status.html:124-152, 443-462` |
| V-15 | Right panel sticky | PASS | `project_status.html:239-248, 326-330` |
| V-16 | dev-meta TBD hidden | PASS | `project_status.html:478-479` |
| V-17 | Filter URL parameter | PASS | `project_status.html:583-589` |

**Result: 17/17 PASS (100%)**

---

## Gap List

**No FAIL items found.** All 17 verification criteria pass.

Minor cosmetic differences (non-blocking):

| Type | Item | Design | Implementation | Impact |
|------|------|--------|----------------|--------|
| Changed | Responsive breakpoint (index.html) | 640px | 768px | Negligible (consistent with dashboard convention) |
| Changed | Default filter | `'all'` (design) | `'개발중'` (user request) | Positive improvement |
| Changed | Filter tab label | `'진행중'` | `'개발중'` | Naming unification (user request) |

---

## Related Documents

- Plan: [dashboard-project-panel-v2.plan.md](../../01-plan/features/dashboard-project-panel-v2.plan.md)
- Design: [dashboard-project-panel-v2.design.md](../../02-design/features/dashboard-project-panel-v2.design.md)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-02-19 | Initial gap analysis -- 12/12 PASS | gap-detector |
| 2.0 | 2026-02-19 | V-13~V-17 added (detail page redesign) + post-design changes -- 17/17 PASS | gap-detector |
