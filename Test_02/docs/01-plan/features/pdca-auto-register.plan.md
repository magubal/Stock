# pdca-auto-register Plan

> Plan 없이 구현된 기능도 개발현황 대시보드에 자동 등록되도록 규칙을 명시하는 건

## 배경
- `project_status.py`가 `planPath` 기준으로 필터링하여, PDCA Plan 없이 구현한 기능(kill-port 등)이 대시보드에서 누락됨
- `/brain` 브레인스토밍 → 직접 구현, hotfix, 유틸리티 등은 Plan 단계를 건너뜀
- 자동 추적 노이즈(backend, scripts 등)는 여전히 필터링 필요

## 범위
- CLAUDE.md Key Conventions에 "Plan-less Feature Registration (MANDATORY)" 규칙 추가
- 규칙: 구현 완료 시 세션 종료 전 경량 Plan 생성 + .pdca-status.json 등록
- 코드 변경 없음 (project_status.py 필터 로직 유지)

## 산출물

| 파일 | 변경 내용 |
|------|-----------|
| `CLAUDE.md` | Key Conventions에 Plan-less Feature Registration 규칙 추가 |
| `docs/01-plan/features/zombie-process-cleanup.plan.md` | kill-port 경량 Plan (소급 적용) |
| `.pdca-status.json` | zombie-process-cleanup 등록 (소급 적용) |

## 완료 상태
- 2026-02-19 규칙 명시 완료
- 브레인스토밍(C안: 규칙+자동 경량 Plan) 채택
- zombie-process-cleanup 소급 등록 완료
