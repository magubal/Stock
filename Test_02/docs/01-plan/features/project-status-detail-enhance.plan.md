# project-status-detail-enhance Plan

> 개발현황 상세 패널에 기능 설명 한 줄과 Plan/Design 문서 링크를 표시하여 문맥 파악을 용이하게 한다

## 배경
- 체크리스트 요약에 "Plan 문서 작성 / 완료" 등 라벨만 표시되어 기능이 무엇인지 알 수 없음
- Plan/Design 문서를 보려면 파일 탐색기에서 직접 찾아야 함

## 범위
- Backend: plan.md에서 설명(인용문) 자동 파싱 + checklist에 문서 link 추가
- Frontend: description 표시 + doc 링크 클릭 시 경로 복사

## 산출물

| 파일 | 변경 내용 |
|------|-----------|
| `backend/app/api/project_status.py` | `_parse_plan_description()`, checklist `link` 필드, item `description` 필드 |
| `dashboard/project_status.html` | CSS(feature-desc, check-doc-link), description 영역, 체크리스트 링크 렌더링 |

## 완료 상태
- 2026-02-19 구현 완료 (Plan-less Registration 규칙 적용)
