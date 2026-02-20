# blog-investor-digest Planning Document

> **Summary**: 투자자 네이버블로그 수집글을 웹 대시보드에서 열람/AI정리/수정저장하는 시스템
>
> **Project**: Stock Research ONE
> **Author**: PSJ + Claude
> **Date**: 2026-02-19
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

REQ-001에서 매일 수집하는 투자자 네이버블로그 캡처 이미지+메타데이터를 웹 대시보드에서 날짜별 열람하고, AI 자동 정리(내용/관점/시사점)를 사용자가 검토/수정/저장하여 투자 관점을 확장한다.

### 1.2 Background

- REQ-001(완료): 3명 블로거 RSS 기반 자동 수집기 운영 중 (Playwright 스크린샷 + JSON 메타)
- 일평균 ~25건 수집, 이미지 ~1.2MB/건
- 현재는 파일시스템(`data/naver_blog_data/YYYY-MM-DD/`)에만 저장 → 웹에서 열람/정리 불가
- 투자자 글을 빠르게 훑고 시사점을 정리하는 워크플로우가 필요

### 1.3 Related Documents

- Requirements: `REQUESTS.md` REQ-001 (네이버 블로그 데이터 자동 수집)
- 기존 수집기: `scripts/naver_blog_collector.py`, `scripts/final_body_capture.py`
- RSS 목록: `data/naver_blog_data/naver_bloger_rss_list.txt`
- 대시보드: `dashboard/index.html` (시장모니터링 섹션)

---

## 2. Scope

### 2.1 In Scope

- [ ] DB 모델: `blog_posts`(글 메타+본문텍스트+이미지경로), `blog_summaries`(AI정리+사용자수정)
- [ ] 수집 파이프라인 강화: Playwright 본문 텍스트 추출 추가 + DB 저장
- [ ] AI 분석 서비스: 텍스트 기반 Claude API 요약 (Vision fallback)
- [ ] 대시보드 페이지: `dashboard/blog_review.html` (Master-Detail 레이아웃)
- [ ] FastAPI 라우터: blog-review (CRUD + 이미지 서빙)
- [ ] 매일 22:00 자동 수집+분석 스케줄
- [ ] `dashboard/index.html` 시장모니터링 섹션에 카드 링크 추가
- [ ] 이미지 최적화: JPEG 품질 조정으로 용량 절감 (최종 단계)

### 2.2 Out of Scope

- 블로거 자동 발견/추천 (RSS 목록은 수동 관리 유지)
- 다른 플랫폼(티스토리, 브런치 등) 수집
- 블로거 간 관점 비교/교차 분석 (향후 확장)
- 모바일 반응형 최적화

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | 날짜 필터링: 날짜 선택 시 해당일 수집글 리스트 표시 | High | Pending |
| FR-02 | 투자자별 글 제목 리스트 (좌측 패널) | High | Pending |
| FR-03 | 클릭 시 AI 정리본 표시 (내용요약/핵심관점/시사점) (우측 패널) | High | Pending |
| FR-04 | 제목 클릭 시 원문 블로그 새탭 열기 | High | Pending |
| FR-05 | AI 정리본 수정 및 DB 저장 기능 | High | Pending |
| FR-06 | Playwright 본문 텍스트 추출 추가 (이미지 + 텍스트 동시 수집) | High | Pending |
| FR-07 | AI 자동 분석: 텍스트 우선 → Vision fallback | High | Pending |
| FR-08 | 매일 22:00 자동 수집+분석 배치 | Medium | Pending |
| FR-09 | 캡처 이미지 대시보드 표시 (원문 참조용) | Medium | Pending |
| FR-10 | 이미지 압축 최적화 (JPEG 60~70%, ~300KB 목표) | Low | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| Performance | 날짜별 글 리스트 로딩 < 1초 | 브라우저 Network 탭 |
| 데이터 정합성 | 수집 글 DB 저장 누락율 < 5% | 파일 vs DB 건수 비교 |
| AI 분석 비용 | 월 $10 이하 (텍스트 우선 전략) | Anthropic API 사용량 |
| 보안 | 이미지 서빙 경로 탐색 차단 | path traversal 테스트 |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] 날짜 선택 → 투자자별 글 리스트 표시
- [ ] 글 클릭 → AI 정리본(내용/관점/시사점) 우측 패널 표시
- [ ] 제목 클릭 → 원문 블로그 새탭 열기
- [ ] 정리본 수정/저장 → DB 반영
- [ ] 22:00 자동 수집 배치 동작 확인
- [ ] 이미지 캡처 + 텍스트 추출 동시 수행
- [ ] `dashboard/index.html`에서 링크 접근 가능

### 4.2 Quality Criteria

- [ ] DEMO 데이터 컨벤션 준수 (source="DEMO")
- [ ] 기존 대시보드 패턴 일관성 (CDN React + 정적 HTML)
- [ ] API path traversal 보안 검증

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| 네이버 블로그 iframe 구조 변경 → 텍스트 추출 실패 | High | Medium | 3단계 selector fallback + Vision API 자동 전환 |
| 이미지 용량 과다 (1.2MB x 25건/일 = 30MB/일) | Medium | High | JPEG 품질 60~70%로 리사이즈 (FR-10) |
| AI 요약 품질 불만족 | Medium | Low | 사용자 수정/저장 기능(FR-05)으로 보완 + 프롬프트 튜닝 |
| Claude API 크레딧 부족 | Medium | Low | 텍스트 우선 전략으로 비용 최소화 + fallback 없이 빈 요약 표시 |

---

## 6. Architecture Considerations

### 6.1 Project Level Selection

| Level | Characteristics | Recommended For | Selected |
|-------|-----------------|-----------------|:--------:|
| **Starter** | Simple structure | Static sites | |
| **Dynamic** | Feature-based modules, BaaS integration | Web apps with backend | **X** |
| **Enterprise** | Strict layer separation, DI, microservices | Complex architectures | |

### 6.2 Key Architectural Decisions

| Decision | Options | Selected | Rationale |
|----------|---------|----------|-----------|
| Frontend | CDN React HTML / Vite SPA | CDN React HTML | 기존 dashboard/ 패턴 일관성 |
| Backend | FastAPI router | FastAPI router | 기존 아키텍처 |
| DB | SQLite (SQLAlchemy) | SQLite | 기존 DB 유지 |
| AI 분석 | Claude Text / Vision / OpenAI | Claude Text+Vision | ANTHROPIC_API_KEY 보유, fallback 전략 |
| 이미지 서빙 | FastAPI static / Nginx | FastAPI endpoint | 보안 제어 가능 |
| 스케줄러 | Windows Task Scheduler / cron | Task Scheduler | Windows 환경 |

### 6.3 데이터 흐름

```
[22:00 배치]
RSS 파싱 → 새 글 감지
    → Playwright 캡처 (이미지 + 텍스트 추출)
    → DB blog_posts 저장
    → Claude API 요약 생성 (텍스트 우선 → Vision fallback)
    → DB blog_summaries 저장

[대시보드]
GET /posts?date=YYYY-MM-DD → 좌측 리스트
GET /posts/{id} → 우측 AI 정리본 + 이미지
PUT /posts/{id}/summary → 수정/저장
GET /posts/{id}/image → 캡처 이미지 서빙
```

---

## 7. Convention Prerequisites

### 7.1 Existing Project Conventions

- [x] `CLAUDE.md` has coding conventions section
- [x] DEMO Data Convention (source="DEMO")
- [x] dashboard/ 정적 HTML + CDN React 패턴
- [x] FastAPI router prefix: `/api/v1/{feature}`

### 7.2 DB 테이블 설계 (초안)

**blog_posts**
| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | Auto increment |
| blogger | String | 블로거 이름 (daybyday, 라틴카페 등) |
| title | String | 글 제목 |
| link | String | 원문 URL |
| pub_date | DateTime | 게시일시 |
| text_content | Text | 추출된 본문 텍스트 |
| image_path | String | 캡처 이미지 상대경로 |
| image_size_kb | Integer | 이미지 크기 (KB) |
| collected_at | DateTime | 수집일시 |
| source | String | "COLLECTOR" or "DEMO" |

**blog_summaries**
| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | Auto increment |
| post_id | Integer FK | blog_posts.id |
| summary | Text | 내용 요약 |
| viewpoint | Text | 핵심 관점 |
| implications | Text | 시사점 |
| is_edited | Boolean | 사용자 수정 여부 |
| edited_at | DateTime | 수정일시 (nullable) |
| ai_model | String | 사용된 AI 모델 (claude-text/claude-vision) |
| created_at | DateTime | 생성일시 |

### 7.3 Environment Variables Needed

| Variable | Purpose | Scope | Status |
|----------|---------|-------|:------:|
| `ANTHROPIC_API_KEY` | Claude API (요약 생성) | Server | 기존 보유 |
| `DATABASE_URL` | SQLite 연결 | Server | 기존 보유 |

---

## 8. 구현 순서 (Phase 계획)

### Phase 1: Core (MVP)
1. DB 모델 생성 (blog_posts, blog_summaries)
2. 수집 파이프라인 강화 (텍스트 추출 + DB 저장)
3. FastAPI 라우터 (CRUD + 이미지 서빙)
4. 대시보드 페이지 (blog_review.html)
5. dashboard/index.html 링크 추가

### Phase 2: AI + Schedule
6. AI 분석 서비스 (텍스트 → Claude API → DB 저장)
7. Vision fallback 경로
8. 22:00 배치 스크립트 + Task Scheduler 등록

### Phase 3: 최적화
9. 이미지 압축 (JPEG 품질 조정)
10. 기존 수집 데이터 마이그레이션 (파일 → DB)

---

## 9. Next Steps

1. [ ] Write design document (`blog-investor-digest.design.md`)
2. [ ] Team review and approval
3. [ ] Start implementation

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-19 | Initial draft from brainstorm | PSJ + Claude |
