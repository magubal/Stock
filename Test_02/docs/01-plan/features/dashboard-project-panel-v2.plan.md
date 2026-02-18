# Feature Plan: Dashboard Project Panel v2

## 1. Overview
- **Feature Name**: dashboard-project-panel-v2 (프로젝트 현황 패널 UI/UX 개편)
- **Level**: Dynamic (Static HTML Dashboard + Vanilla JS)
- **Priority**: Medium
- **Estimated Scope**: 메인 대시보드 패널 개편 + 상세 페이지 UX 개선
- **Brainstorm**: 2026-02-19 Brain 세션에서 A안(압축 오버뷰) 선정
- **REQ Reference**: REQ-017

## 2. Background & Motivation

REQ-017로 구현된 프로젝트 현황/체크리스트 패널의 현재 문제점:

1. **메인 대시보드 공간 낭비**: 19개 REQ를 전부 세로 나열 → 과도한 스크롤 필요
2. **상세 페이지 정보 부족**: 완료 항목(008~016)의 checklist 빈 배열, owner/nextAction 전부 비어있음
3. **우측 패널 무의미**: "상세 개발현황 페이지로 이동하세요" 안내 텍스트만 표시
4. **데이터 description 반복**: programs의 description이 전부 "Related file"
5. **REQUESTS.md 상태 불일치**: 요약표 "완료" vs 상세 카드 "진행"

### 핵심 원칙
- 사용자: **개인 1인** (빠른 파악이 최우선)
- 3초 내 전체 진행률 + 현재 활성 작업 파악 가능해야 함
- 기존 다크 테마 유지, CDN React+Babel 환경 유지

## 3. Requirements

### 3.1 Functional Requirements

| ID | 요구사항 | 우선순위 | 근거 |
|----|----------|----------|------|
| FR-01 | 메인 대시보드: Progress Bar (완료/전체) + 퍼센트 텍스트 표시 | Must | 한눈에 진행률 파악 |
| FR-02 | 메인 대시보드: "개발중/진행" 상태 REQ만 카드 표시 (최대 5개) | Must | 관심 항목만 부각 |
| FR-03 | 메인 대시보드: "전체 보기 →" 링크로 project_status.html 연결 | Must | 상세 진입 경로 |
| FR-04 | 메인 대시보드: 상태별 카운트(완료/진행/기획/미착수) 소형 배지 | Should | KPI 요약 |
| FR-05 | 상세 페이지: 빈 필드(owner="TBD", nextAction="-") 자동 숨김 | Must | 무의미한 정보 제거 |
| FR-06 | 상세 페이지: checklist 빈 배열 → "체크리스트 미등록" 메시지 | Must | UX 명확화 |
| FR-07 | 상세 페이지: 완료 항목의 체크리스트도 표시 (done 항목 시각 구분) | Should | 성취 기록 확인 |
| FR-08 | "진행중" 0개일 때 "All Clear!" 또는 다음 착수 추천 표시 | Should | 빈 상태 대응 |

### 3.2 Non-Functional Requirements

| ID | 요구사항 | 기준 |
|----|----------|------|
| NFR-01 | 외부 라이브러리 추가 없음 | CSS-only Progress Bar (Chart.js 불필요) |
| NFR-02 | 기존 다크 테마 컬러 팔레트 유지 | `#0d1117`, `#161b22`, `#21262d` 계열 |
| NFR-03 | project_status_data.js 데이터 구조 변경 없음 | 기존 스키마 유지 |
| NFR-04 | 기존 동기화 스크립트 건드리지 않음 | sync_requests_to_dashboard.py 수정 금지 |
| NFR-05 | 메인 대시보드 전체 로드 시간 영향 없음 | 추가 네트워크 요청 0개 |

## 4. Technical Approach

### 4.1 수정 대상 파일

| 파일 | 변경 내용 |
|------|-----------|
| `dashboard/index.html` | `ProjectStatusPanel()` 컴포넌트 재작성 |
| `dashboard/project_status.html` | 상세 페이지 `renderDetail()` 개선 |
| `REQUESTS.md` | REQ-017 상태 불일치 수정 |

### 4.2 메인 대시보드 개편 구조

```
┌─────────────────────────────────────────────────┐
│  프로젝트 현황                                    │
│                                                   │
│  ████████████████████░░░░░  73% (14/19)          │
│  [완료 14] [진행 4] [기획 1]                       │
│                                                   │
│  ┌──────────────────┐ ┌──────────────────┐       │
│  │ REQ-002 아이디어  │ │ REQ-003 Pending  │       │
│  │ 관리 시스템       │ │ Packets Inbox    │       │
│  │ ☑ 0/3  개발중    │ │ ☑ 0/3  개발중    │       │
│  └──────────────────┘ └──────────────────┘       │
│  ┌──────────────────┐ ┌──────────────────┐       │
│  │ REQ-004 업황/     │ │ REQ-006 Collab-  │       │
│  │ 컨센서스 연동     │ │ Stock Moat       │       │
│  │ ☑ 0/3  개발중    │ │ ☑ 0/3  개발중    │       │
│  └──────────────────┘ └──────────────────┘       │
│                                                   │
│              전체 보기 →                           │
└─────────────────────────────────────────────────┘
```

### 4.3 상세 페이지 개선 사항

1. **빈 필드 숨김**: `owner === "TBD"` → 행 자체 비표시
2. **빈 체크리스트 처리**: `checklist.length === 0` → "체크리스트 미등록" 회색 텍스트
3. **완료 체크리스트 시각화**: done 항목은 취소선 + 녹색 체크 아이콘
4. **programs description**: "Related file" → 파일 확장자 기반 자동 라벨 (`.py` → "Python script", `.jsx` → "React component" 등)

### 4.4 CSS-only Progress Bar

```css
.progress-bar {
    height: 8px;
    background: #21262d;
    border-radius: 4px;
    overflow: hidden;
}
.progress-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #238636, #2ea043);
    border-radius: 4px;
    transition: width 0.3s ease;
}
```

## 5. Success Criteria

| 기준 | 측정 방법 |
|------|-----------|
| 메인 대시보드에서 3초 내 진행률 파악 가능 | Progress Bar + 퍼센트 표시로 즉시 확인 |
| 메인 패널 세로 높이 50% 이상 절감 | 19개 나열 → 최대 5개 활성 카드만 표시 |
| 상세 페이지 빈 필드 비노출 | owner="TBD", nextAction="-" 숨김 확인 |
| 기존 Playwright 테스트 통과 | `dashboard-core.spec.ts` 그린 |
| 신규 라이브러리 추가 없음 | CSS-only, 기존 CDN만 사용 |

## 6. Risks & Mitigation

| 리스크 | 영향 | 완화 |
|--------|------|------|
| R1: "진행중" 0개일 때 패널 허전 | UX 품질 저하 | "All Clear!" 메시지 + 최근 완료 항목 1-2개 표시 |
| R2: Playwright 테스트가 기존 DOM 구조에 의존 | 테스트 깨짐 | 테스트 셀렉터를 data-testid 기반으로 유지/수정 |
| R3: REQUESTS.md ↔ data.js 향후 불일치 누적 | 데이터 신뢰도 | 동기화 스크립트 복구 (이번 스코프 밖, 별도 REQ) |

## 7. Implementation Order

1. REQUESTS.md REQ-017 상태 불일치 수정
2. `dashboard/index.html` — `ProjectStatusPanel()` 개편
3. `dashboard/project_status.html` — `renderDetail()` 빈 필드 숨김 + 체크리스트 개선
4. Playwright 테스트 업데이트
5. 수동 스모크 테스트 (localhost:8080)

## 8. Out of Scope

- project_status_data.js 데이터 구조 변경
- sync_requests_to_dashboard.py 동기화 스크립트 수정
- 빈 데이터(owner, nextAction) 실제 값 채우기
- 모바일 반응형 (개인 PC 사용)
