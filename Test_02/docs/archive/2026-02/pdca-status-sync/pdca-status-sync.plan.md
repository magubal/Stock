# pdca-status-sync Planning Document

> **Summary**: PDCA로 개발된 기능들을 프로젝트 현황 대시보드에 자동 통합 표시
>
> **Project**: Stock Research ONE
> **Author**: Claude
> **Date**: 2026-02-19
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

현재 프로젝트 현황 대시보드(`dashboard/index.html` ProjectStatusPanel + `dashboard/project_status.html`)에는 `REQUESTS.md` 기반 REQ-001~022만 표시된다. bkit PDCA 워크플로우로 개발된 12+ 기능(stock-moat-estimator, evidence-based-moat, oracle-earnings-integration 등)은 `.pdca-status.json`과 `docs/archive/`에만 존재하고 대시보드에 반영되지 않는다.

이 기능은 두 추적 시스템(REQ vs PDCA)을 대시보드에서 통합 표시하고, 향후 PDCA 기능 추가 시 자동 반영되도록 한다.

### 1.2 Background

- `project_status_data.js`: 정적 JS 파일, `window.PROJECT_STATUS_ITEMS` 배열 (22개 REQ 항목)
- `.pdca-status.json`: PDCA 활성 기능 (phase, matchRate, startedAt 등)
- `docs/archive/YYYY-MM/_INDEX.md`: 완료/아카이브된 PDCA 기능
- 두 시스템이 독립 운영되어 프로젝트 전체 현황 파악 불가

### 1.3 Related Documents

- Brain 결과: C안 하이브리드 (정적 REQ + 동적 PDCA API merge) 채택
- `dashboard/index.html`: ProjectStatusPanel 컴포넌트 (CDN React+Babel)
- `dashboard/project_status.html`: 전체 현황 상세 페이지 (Vanilla JS)

---

## 2. Scope

### 2.1 In Scope

- [ ] Backend API: `GET /api/v1/project-status/pdca` - PDCA 데이터를 PROJECT_STATUS_ITEMS 형식으로 반환
- [ ] `dashboard/index.html` ProjectStatusPanel 수정: API에서 PDCA 항목 fetch → REQ와 merge
- [ ] `dashboard/project_status.html` 수정: 동일한 API fetch + merge 로직
- [ ] PDCA phase → 상태 매핑 (plan→기획, design→설계, do→개발중, check→검증, archived→완료)
- [ ] REQ/PDCA 출처 구분 배지 (파란/보라)
- [ ] Graceful degradation: API 실패 시 REQ만 표시
- [ ] PDCA 체크리스트 자동 생성: plan 문서 scope에서 추출
- [ ] PDCA 관련 파일 자동 생성: design 문서 file structure에서 추출

### 2.2 Out of Scope

- REQ 시스템 폐기 또는 통합 (두 시스템 공존 유지)
- PDCA 항목의 REQUESTS.md 자동 등록
- 프로젝트 현황 페이지 UI 전면 리디자인

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | Backend API가 .pdca-status.json + archive/_INDEX.md 파싱하여 JSON 반환 | High | Pending |
| FR-02 | PDCA 항목에 고정 ID 부여 (PDCA-001, PDCA-002, ...) — REQ-XXX와 절대 충돌 불가 | High | Pending |
| FR-02a | **ID 네임스페이스 완전 분리**: REQ-XXX 범위와 PDCA-XXX 범위는 접두사가 다르므로 충돌 원천 차단. `config/pdca_id_map.json`에 feature→번호 고정 매핑 저장하여 번호 안정성 보장 | High | Pending |
| FR-02b | 대시보드에서 `source` 필드(`"req"` / `"pdca"`)로 출처 구분, 필터탭에서도 분리 필터 가능 | High | Pending |
| FR-02c | **ID 불변 규칙**: 한 번 할당된 PDCA-NNN은 해당 feature가 삭제되어도 번호 재사용 금지. 새 feature는 항상 max+1 번호 할당 | High | Pending |
| FR-03 | phase→상태 매핑: plan→기획, design→설계, do→개발중, check→검증, archived→완료 | High | Pending |
| FR-04 | ProjectStatusPanel에서 정적 REQ + 동적 PDCA 병합 표시 | High | Pending |
| FR-05 | project_status.html에서 동일한 병합 표시 | High | Pending |
| FR-06 | REQ(파랑)/PDCA(보라) 출처 구분 배지 | Medium | Pending |
| FR-07 | API 실패 시 REQ만 표시 (graceful degradation) | High | Pending |
| FR-08 | PDCA 체크리스트: plan 문서 scope "In Scope" 항목에서 자동 추출 | Medium | Pending |
| FR-09 | PDCA 관련 파일: design 문서에서 주요 파일 경로 추출 | Medium | Pending |
| FR-10 | archived 기능에 matchRate % 표시 | Low | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| Performance | API 응답 < 500ms | 파일 I/O 기반이므로 충분 |
| 안정성 | API 실패 시에도 REQ 표시 보장 | fetch catch fallback |
| 호환성 | 기존 Playwright 테스트 통과 | dashboard-core.spec.ts |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] Backend API `/api/v1/project-status/pdca` 동작 확인
- [ ] ProjectStatusPanel에서 REQ + PDCA 통합 표시
- [ ] project_status.html에서 REQ + PDCA 통합 표시
- [ ] API 미기동 시에도 REQ 정상 표시
- [ ] 기존 Playwright 테스트 통과

### 4.2 Quality Criteria

- [ ] PDCA 항목 ID 중복 없음
- [ ] 상태 배지 색상 정확
- [ ] 정렬: 개발중 → 기획/설계/검증 → 완료

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| API 응답 지연으로 대시보드 로딩 느림 | Medium | Low | REQ 먼저 렌더, PDCA 비동기 append |
| .pdca-status.json 파싱 오류 | Medium | Low | try-catch + empty array fallback |
| REQ와 PDCA ID 충돌 | High | Impossible | 접두사 완전 분리 (REQ- vs PDCA-). source 필드 이중 구분. pdca_id_map.json으로 번호 불변 보장 |
| PDCA ID 변동 (기능 추가/삭제 시 번호 밀림) | High | Medium | `config/pdca_id_map.json` 고정 매핑. 삭제 시 번호 재사용 금지 (max+1 할당) |
| REQ와 PDCA 항목이 같은 기능을 가리킬 때 중복 | Medium | Medium | 허용 — 두 시스템은 별도 추적 체계이므로 중복 가능. UI에서 출처 배지로 구분 |

---

## 6. Architecture Considerations

### 6.1 하이브리드 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│ dashboard/index.html (CDN React)                        │
│   ProjectStatusPanel                                    │
│     ├── window.PROJECT_STATUS_ITEMS (REQ, 정적 JS)      │
│     └── fetch /api/v1/project-status/pdca (PDCA, 동적)  │
│           └── merge → 통합 렌더링                        │
├─────────────────────────────────────────────────────────┤
│ dashboard/project_status.html (Vanilla JS)              │
│     ├── window.PROJECT_STATUS_ITEMS (REQ, 정적 JS)      │
│     └── fetch /api/v1/project-status/pdca (PDCA, 동적)  │
│           └── merge → 통합 렌더링                        │
├─────────────────────────────────────────────────────────┤
│ Backend API: GET /api/v1/project-status/pdca            │
│     ├── .pdca-status.json 읽기 (활성 PDCA)              │
│     ├── docs/archive/YYYY-MM/_INDEX.md 파싱 (완료 PDCA) │
│     └── PROJECT_STATUS_ITEMS 형식으로 변환               │
└─────────────────────────────────────────────────────────┘
```

### 6.2 PDCA → PROJECT_STATUS_ITEMS 변환 규칙

```
PDCA feature → {
  id: "PDCA-NNN",
  title: "PDCA-NNN {feature-name} ({한글 요약})",
  status: phase→상태매핑,
  stage: phase 원문,
  owner: "bkit PDCA",
  due: "-",
  source: "pdca",         // 출처 구분용 새 필드
  matchRate: 97.5,        // PDCA 전용 필드
  programs: [...],        // design 문서에서 추출 또는 빈 배열
  checklist: [...],       // plan scope에서 추출 또는 빈 배열
  nextAction: "/pdca next 추천 명령"
}
```

### 6.3 Phase → 상태 매핑

| PDCA Phase | 대시보드 상태 | 배지 색상 |
|------------|-------------|-----------|
| plan | 기획 | 파랑 |
| design | 설계 | 파랑 |
| do | 개발중 | 주황 |
| check | 검증 | 노랑 |
| completed/report | 완료 | 초록 |
| archived | 완료 | 초록 |

---

## 7. Implementation Approach

### 7.1 수정 대상 파일

| 파일 | 변경 내용 |
|------|-----------|
| `backend/app/api/project_status.py` (신규) | PDCA 데이터 API endpoint |
| `backend/app/main.py` | 라우터 등록 |
| `dashboard/index.html` | ProjectStatusPanel 수정: fetch + merge |
| `dashboard/project_status.html` | 상세 페이지: fetch + merge |

### 7.2 구현 순서

1. Backend API 생성 (.pdca-status.json + archive 파서)
2. dashboard/index.html ProjectStatusPanel 수정
3. dashboard/project_status.html 수정
4. E2E 테스트 확인

---

## 8. Next Steps

1. [ ] Design 문서 작성 (`pdca-status-sync.design.md`)
2. [ ] 구현 (Do phase)
3. [ ] Gap Analysis (Check phase)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-19 | Initial draft from brain session | Claude |
