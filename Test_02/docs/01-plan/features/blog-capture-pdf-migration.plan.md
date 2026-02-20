# blog-capture-pdf-migration Planning Document

> **Summary**: REQ-001 블로그 캡처 저장 포맷을 JPG 이미지에서 A4 다페이지 PDF로 전환하고, 기존 93건도 PDF로 재캡처
>
> **Project**: Stock Research ONE
> **Author**: PSJ + Claude
> **Date**: 2026-02-20
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

REQ-001 블로그 수집 시스템의 저장 포맷을 JPG 스크린샷에서 A4 다페이지 PDF로 전환한다. PDF는 원문 레이아웃을 충실히 보존하면서 파일 크기를 최적화하고, 여러 페이지로 자연스럽게 나뉘어 가독성을 높인다. 텍스트 추출은 PDF 생성과 병행하여 AI 분석에 활용한다.

### 1.2 Background

- REQ-001(운영 중): 3명 블로거 RSS 기반 자동 수집기 (`scripts/final_body_capture.py`)
- 현재: Playwright 모바일 스크린샷 → PNG → JPG 변환 (quality=75, 평균 ~1.2MB/건)
- 문제점: 긴 글은 하나의 세로긴 이미지(8000px+)로 저장 → 가독성 낮음, 확대/스크롤 불편
- 해결: A4 PDF 다페이지로 전환하면 자연스러운 페이지 분할 + 내장 텍스트 검색 가능
- 사용자 제공 참조코드(`save_post_pdf_only_article.py`): Playwright `page.pdf()` 기반 검증된 PDF 생성 로직

### 1.3 Related Documents

- 기존 수집기: `scripts/final_body_capture.py` (Playwright JPG 캡처)
- 수집 배치: `scripts/blog_monitor/run_blog.py` (22:00 스케줄)
- RSS 수집기: `scripts/naver_blog_collector.py`
- DB 모델: `backend/app/models/blog_post.py` (BlogPost, BlogSummary)
- API: `backend/app/api/blog_review.py` (이미지 서빙 엔드포인트)
- 대시보드: `dashboard/blog_review.html` (이미지 표시 섹션)
- 선행 feature: `blog-investor-digest` (현재 Do phase, 중단 후 본 작업 선행)

---

## 2. Scope

### 2.1 In Scope

- [ ] `final_body_capture.py` 전면 수정: JPG 스크린샷 → `page.pdf()` A4 출력
- [ ] 참조코드 핵심 로직 통합: `PRUNE_JS`, `auto_scroll`, `open_iframe_or_self`
- [ ] 데스크톱 iframe 접근 방식으로 전환 (기존 모바일 → 데스크톱)
- [ ] 텍스트 추출: DOM pruning 전에 block-aware 텍스트 추출 수행
- [ ] DB 스키마: `image_path` 컬럼 재사용 (값만 `.jpg` → `.pdf`)
- [ ] `run_blog.py` 수정: PDF 파일 경로 처리
- [ ] `naver_blog_collector.py` 수정: 캡처 결과 `.pdf` 처리
- [ ] 백필 스크립트: 기존 93건 블로그 URL 재방문 → PDF 재캡처
- [ ] API 수정: 파일 서빙 endpoint PDF 지원 (media_type 변경)
- [ ] 대시보드 수정: `<img>` → PDF embed/iframe viewer

### 2.2 Out of Scope

- 기존 JPG 파일 삭제 (PDF 재캡처 성공 후 수동 판단)
- 블로거 자동 발견/추천
- 로그인 필요 글 자동 처리 (참조코드의 `--login` 기능은 제외)
- PIL/Pillow 의존성 제거 (다른 모듈에서 사용 가능)

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | `final_body_capture.py` PDF 출력: `page.pdf()` A4 format, 여백 12mm/10mm | High | Pending |
| FR-02 | 데스크톱 iframe 접근: `open_iframe_or_self` 패턴 (기존 모바일 전환 제거) | High | Pending |
| FR-03 | DOM pruning: 본문만 남기고 나머지 제거 (`PRUNE_JS`) | High | Pending |
| FR-04 | Auto-scroll: lazy-loaded 이미지/텍스트 완전 로딩 (break 조건 포함) | High | Pending |
| FR-05 | 텍스트 병행 추출: PDF 생성 전 DOM에서 block-aware 텍스트 추출 | High | Pending |
| FR-06 | 파일 저장: `data/naver_blog_data/YYYY-MM-DD/blogger_NNN.pdf` | High | Pending |
| FR-07 | DB: `image_path`에 `.pdf` 경로 저장, `image_size_kb` PDF 크기 | High | Pending |
| FR-08 | `run_blog.py` PDF 경로 처리 (확장자 변경) | Medium | Pending |
| FR-09 | 백필: 기존 93건 URL 재방문 → PDF 생성 + DB 업데이트 | Medium | Pending |
| FR-10 | API: PDF 파일 서빙 (application/pdf media_type) | Medium | Pending |
| FR-11 | 대시보드: PDF viewer (embed/iframe, 페이지 탐색) | Medium | Pending |
| FR-12 | print용 CSS 주입: 이미지 max-width, 배경색 등 | Low | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| PDF 크기 | 평균 500KB 이하 (기존 JPG 1.2MB 대비 절감) | 파일 크기 통계 |
| PDF 품질 | A4 페이지 분할 자연스러움, 이미지 선명도 유지 | 육안 검증 |
| 캡처 속도 | 글 1건당 30초 이내 | 배치 실행 로그 |
| 텍스트 추출 | 기존 block-aware 추출과 동일 품질 | 문자 수 비교 |
| 호환성 | 기존 blog-investor-digest 대시보드와 연동 | UI 검증 |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] `final_body_capture.py`가 PDF를 출력하고 `text_content`를 함께 반환
- [ ] A4 다페이지 PDF가 정상 생성됨 (3명 블로거 각 1건 이상 검증)
- [ ] `run_blog.py --skip-ai` 실행 시 PDF 파일이 `data/naver_blog_data/YYYY-MM-DD/`에 저장
- [ ] DB `image_path`에 `.pdf` 경로가 저장됨
- [ ] API `/posts/{id}/image`가 PDF를 정상 반환
- [ ] `dashboard/blog_review.html`에서 PDF가 표시됨
- [ ] 기존 93건 중 80% 이상 PDF 재캡처 성공 (삭제된 글은 skip)
- [ ] 텍스트 추출이 기존과 동일한 품질로 동작

### 4.2 Quality Criteria

- [ ] 참조코드의 핵심 로직(`PRUNE_JS`, `auto_scroll`) 정확히 통합
- [ ] DEMO 데이터 컨벤션 준수 (source="DEMO")
- [ ] 모바일 fallback 로직 유지 (iframe 접근 실패 시)

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| 네이버 블로그 iframe 구조 변경 → 데스크톱 캡처 실패 | High | Medium | 모바일 fallback 로직 유지, selector 다단계 fallback |
| 기존 93건 재캡처 시 블로그 글 삭제/비공개 전환 | Medium | Medium | 실패 건은 skip, 기존 JPG 유지 |
| PDF 파일 크기 예상보다 큼 (이미지 많은 블로그) | Medium | Low | `scale` 파라미터 조정 (0.8~1.0), device_scale_factor 조절 |
| Playwright headless에서 PDF 렌더링 불안정 | Low | Low | Chromium 버전 고정, timeout 여유 확보 |

---

## 6. Architecture Considerations

### 6.1 Project Level Selection

| Level | Characteristics | Recommended For | Selected |
|-------|-----------------|-----------------|:--------:|
| **Starter** | Simple structure | Static sites | |
| **Dynamic** | Feature-based modules | Web apps with backend | **X** |
| **Enterprise** | Strict layer separation | Complex architectures | |

### 6.2 Key Architectural Decisions

| Decision | Options | Selected | Rationale |
|----------|---------|----------|-----------|
| PDF 생성 | Playwright page.pdf() / wkhtmltopdf / ReportLab | Playwright page.pdf() | 참조코드 검증됨, 기존 Playwright 의존성 |
| 블로그 접근 | 모바일 / 데스크톱 iframe | 데스크톱 iframe | 참조코드 방식, 완전한 텍스트 접근 |
| DB 스키마 | 새 컬럼 추가 / 기존 컬럼 재사용 | 기존 재사용 | `image_path`→ pdf 경로, 변경 최소화 |
| 대시보드 PDF 뷰어 | iframe embed / PDF.js / 브라우저 내장 | iframe embed | 추가 라이브러리 불필요 |
| 백필 전략 | 전체 한번에 / 날짜별 분할 | 날짜별 분할 | 실패 시 재시도 용이, 부하 분산 |

### 6.3 데이터 흐름 (변경 후)

```
[22:00 배치] run_blog.py
RSS 파싱 → 새 글 감지
    → Playwright 데스크톱 접속
    → iframe#mainFrame 내부 진입
    → auto_scroll (lazy-load 트리거)
    → 텍스트 추출 (block-aware, pruning 전)
    → DOM pruning (PRUNE_JS: 본문만 남기기)
    → page.pdf() → A4 다페이지 PDF 저장
    → DB blog_posts 저장 (pdf_path + text_content)
    → Claude API 요약 생성
    → DB blog_summaries 저장

[대시보드] blog_review.html
GET /posts?date=YYYY-MM-DD → 좌측 리스트
GET /posts/{id} → 우측 AI 정리본 + PDF
PUT /posts/{id}/summary → 수정/저장
GET /posts/{id}/image → PDF 파일 서빙 (application/pdf)
```

### 6.4 참조코드 핵심 통합 포인트

```python
# 1. open_iframe_or_self: 데스크톱 iframe 접근
page.goto(url, wait_until="networkidle")
iframe = page.query_selector("iframe#mainFrame")
if iframe: page.goto(iframe.src, wait_until="networkidle")

# 2. auto_scroll: break 조건 포함 (scrollY 변화 없으면 중단)
for _ in range(400):
    page.evaluate("window.scrollBy(0,1500)")
    if cur == last: break

# 3. PRUNE_JS: 본문 element만 body에 남기기 + print CSS 주입
# 4. page.pdf(): A4, margins, print_background, scale=1.0
```

---

## 7. Implementation Order

### Phase 1: Core Capture (FR-01~06)
1. `final_body_capture.py` 전면 수정 (JPG→PDF, 데스크톱 iframe)
2. 참조코드 `PRUNE_JS`, `auto_scroll`, `open_iframe_or_self` 통합
3. 텍스트 추출 로직 유지 (pruning 전 수행)
4. 단건 테스트 검증

### Phase 2: Pipeline Integration (FR-07~08)
5. `run_blog.py` 수정 (PDF 경로 처리)
6. `naver_blog_collector.py` 수정 (확장자 변경)
7. DB 저장 검증

### Phase 3: API + Dashboard (FR-10~11)
8. API endpoint PDF 서빙 수정
9. 대시보드 PDF viewer 변경
10. blog-investor-digest 연동 확인

### Phase 4: Backfill (FR-09)
11. 백필 스크립트 작성 (`backfill_pdf.py`)
12. 기존 93건 PDF 재캡처 실행
13. 성공/실패 리포트

---

## 8. Convention Prerequisites

### 8.1 Existing Project Conventions

- [x] `CLAUDE.md` has coding conventions section
- [x] DEMO Data Convention (source="DEMO")
- [x] Dashboard pattern: CDN React + 정적 HTML
- [x] 파일 저장: `data/naver_blog_data/YYYY-MM-DD/` 구조

### 8.2 Convention Changes

- 파일 확장자: `.jpg` → `.pdf` (저장 경로 패턴 동일)
- API media_type: `image/jpeg` → `application/pdf`
- 대시보드: `<img>` → `<iframe>` or `<embed>` for PDF display
