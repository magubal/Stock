# manual-collector-trigger Planning Document

> **Summary**: 메뉴얼 기반 블로그 수집기 실행 트리거 및 상태 연동 기능
>
> **Project**: Stock Research ONE
> **Author**: PSJ + Claude
> **Date**: 2026-02-20
> **Status**: Dev

---

## 1. Overview
사용자가 `blog_review.html` 대시보드 화면 내에서 즉시 `naver_blog_collector.py` 파이프라인을 구동하고 진행률을 시각적으로 확인할 수 있는 기능.

## 2. Scope
- `blog_review.py` FastAPI에 `POST /collect` 및 `GET /collect/status` 엔드포인트 비동기 구성
- 백그라운드로 Python `subprocess` 구동 및 OOM 폭주 방지를 위한 `lock` 메커니즘 구축
- `blog_review.html` 대시보드 상단에 수동 수집 버튼 및 진행률(`progress-text`) UI 추가

## 3. Architecture Decisions
- **비동기 팝업 프로세스 (Subprocess)**: 수집기(Playwright)가 FastAPI에 부하를 주지 않도록 독립된 OS 프로세스로 가동하고, 로그 파일(`data/blog_collection.log`) 출력을 활용하여 진행 상태를 Polling 없이(새로고침 기준) UI로 렌더링.
- **Lock 파일 기반 동시성 제어**: `data/collection.lock` 파일을 사용하여 버튼 연타 시 발생할 수 있는 브라우저 인스턴트 중복 생성 메모리 폭발(OOM) 방지.

## 4. Success Criteria
- [ ] 버튼 클릭 시 실제 `naver_blog_collector.py` 스크립트 가동
- [ ] 실행 도중에는 중복 실행되지 않으며, 버튼이 비활성화 됨
- [ ] 페이지를 새로고침 했을 때 백엔드 동작 상태 및 로그 마지막 줄이 대시보드 진행률 항목에 정상 템플릿 처리됨
