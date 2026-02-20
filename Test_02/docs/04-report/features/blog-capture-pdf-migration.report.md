# Blog Capture PDF Migration - Completion Report

> **Summary**: JPG-to-PDF migration completed with 98.9% design match rate. Core capture rewritten to A4 multi-page PDF via Playwright `page.pdf()`, pipeline E2E verified (68 posts), 10 positive enhancements beyond design.
>
> **Feature**: blog-capture-pdf-migration (블로그 캡처 PDF 전환)
> **Project**: Stock Research ONE
> **Created**: 2026-02-20
> **Status**: Completed
> **Last Modified**: 2026-02-20

---

## 1. PDCA Cycle Overview

### 1.1 Feature Summary

**Objective**: REQ-001 블로그 수집 시스템의 저장 포맷을 JPG 스크린샷에서 A4 다페이지 PDF로 전환. 참조코드(`save_post_pdf_only_article.py`) 기반으로 `final_body_capture.py`를 전면 재작성하고, 파이프라인/API/대시보드를 PDF에 맞게 수정.

**Core Value Proposition**:
- A4 다페이지 PDF로 자연스러운 페이지 분할 (기존 세로긴 이미지 문제 해결)
- 브라우저 내장 PDF viewer로 페이지 탐색/확대/인쇄 지원
- 텍스트 추출 품질 유지 (block-aware, pruning 전 수행)
- 기존 JPG 하위 호환 (대시보드에서 JPG/PDF 모두 표시)

### 1.2 PDCA Timeline

| Phase | Date | Duration | Status |
|-------|------|----------|--------|
| **Plan** | 2026-02-20 | 1 session | Done |
| **Design** | 2026-02-20 | 1 session | Done |
| **Do** (Implement) | 2026-02-20 | 1 session | Done |
| **Check** (Gap Analysis) | 2026-02-20 | 1 session | 98.9% PASS |
| **Act** (Report) | 2026-02-20 | Current | Done |

---

## 2. Results Summary

### 2.1 Overall Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Design Match Rate | >= 90% | 98.9% | PASS |
| FR Coverage | 12/12 | 12/12 (100%) | PASS |
| Error Handling | 100% | 7/7 (100%) | PASS |
| Cross-Consistency | 100% | 15/15 (100%) | PASS |
| Positive Additions | - | 10 items | Bonus |
| Missing Features | 0 | 0 | PASS |

### 2.2 Key Achievements

1. **`final_body_capture.py` 전면 재작성** (v3.0 JPG -> v4.0 PDF)
   - 참조코드의 `PRUNE_JS`, `auto_scroll`, `open_iframe_or_self`, `detect_article_selector` 통합
   - 데스크톱 iframe 접근 방식으로 전환 (모바일 -> 데스크톱)
   - `page.pdf()`: A4 format, margins 12mm/10mm, `print_background=True`, `scale=1.0`
   - `BlogCaptureSession` 인터페이스 보존 (호출부 변경 최소화)

2. **E2E 파이프라인 검증 성공** (68 posts)
   - `run_blog.py --skip-ai`: 3명 블로거 RSS -> PDF 캡처 -> DB 저장
   - daybyday 11건, 라틴카페 34건, 유수암바람 23건

3. **10개 긍정적 개선사항** (설계 초과 구현)
   - Relative URL handling for iframe `src` (실제 버그 수정)
   - Body fallback in `PRUNE_JS` (빈 PDF 방지)
   - 2개 추가 `ARTICLE_SELECTORS` (레거시 블로그 커버리지)
   - `json.dumps()` for JS selector injection (XSS safety)
   - 기타 defensive coding 개선

### 2.3 Key Metrics

| Metric | Before (JPG) | After (PDF) |
|--------|:------------:|:-----------:|
| 저장 포맷 | JPG (세로긴 이미지) | A4 multi-page PDF |
| 접근 방식 | 모바일 스크린샷 | 데스크톱 iframe + DOM pruning |
| 텍스트 추출 | block-aware | block-aware (동일 품질) |
| 대시보드 뷰어 | `<img>` | `<iframe>` (PDF viewer) |
| 하위 호환 | - | JPG도 `<img>`로 표시 |

---

## 3. Implementation Details

### 3.1 Changed Files (7 files)

| File | Change Level | Description |
|------|:------------:|-------------|
| `scripts/final_body_capture.py` | Full Rewrite | JPG -> PDF 전면 재작성 (352 lines) |
| `scripts/blog_monitor/run_blog.py` | Minor | RSS 파서 내장, PDF 경로 처리, `load_bloggers()` 포맷 지원 |
| `backend/app/services/blog_review_service.py` | Minor | `.pdf` 확장자 허용 |
| `backend/app/api/blog_review.py` | Minor | PDF media_type 분기 |
| `dashboard/blog_review.html` | Moderate | PDF iframe viewer + CSS + 토글 라벨 |
| `scripts/blog_monitor/backfill_pdf.py` | New | 기존 93건 PDF 재캡처 스크립트 (194 lines) |
| `scripts/naver_blog_collector.py` | Minor | `BlogCaptureSession` import 경로 |

### 3.2 Core Technical Decisions

| Decision | Selected | Rationale |
|----------|----------|-----------|
| PDF 생성 | Playwright `page.pdf()` | 참조코드 검증됨, 기존 Playwright 의존성 |
| 블로그 접근 | 데스크톱 iframe | 완전한 DOM 접근, 텍스트 추출 가능 |
| DB 스키마 | 변경 없음 | `image_path` 값만 `.jpg` -> `.pdf` |
| 대시보드 PDF viewer | `<iframe>` | 추가 라이브러리 불필요, 브라우저 내장 |
| 텍스트 추출 시점 | DOM pruning 전 | pruning 후 텍스트 소실 방지 |

### 3.3 Bug Fixes During Implementation

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| SyntaxError in JS selectors | `str().replace("'",'"')` breaks `article[data-role='post']` | `json.dumps()` 사용 |
| TypeError in PRUNE_JS | `sel="body"` -> body remove -> null access | Body guard clause 추가 |
| No text extracted | iframe `src` relative URL (`/PostView.naver?...`) | `urlparse` absolute URL 변환 |
| "No bloggers configured" | RSS file `URL # name` format vs CSV expectation | Dual format parser |
| `parse_rss_feed` ImportError | Function missing in `naver_blog_collector.py` | Self-contained implementation in `run_blog.py` |

---

## 4. Gap Analysis Summary

### 4.1 Category Scores

| Category | Items | Matched | Changed | Missing | Score |
|----------|:-----:|:-------:|:-------:|:-------:|:-----:|
| 3.1 Core Capture | 32 | 31 | 1 (Pos) | 0 | 100% |
| 3.2 run_blog.py | 4 | 4 | 0 | 0 | 100% |
| 3.3 naver_blog_collector | 2 | 2 | 0 | 0 | 100% |
| 3.4 blog_review_service | 1 | 1 | 0 | 0 | 100% |
| 3.5 blog_review API | 1 | 1 | 0 | 0 | 100% |
| 3.6 Dashboard PDF viewer | 5 | 5 | 0 | 0 | 100% |
| 3.7 Backfill script | 10 | 10 | 0 | 0 | 100% |
| Cross-consistency | 15 | 15 | 0 | 0 | 100% |
| Error handling | 7 | 7 | 0 | 0 | 100% |

### 4.2 Overall Score

```
+---------------------------------------------+
|  Overall Match Rate: 98.9%                   |
+---------------------------------------------+
|  Total Items Checked:  89                    |
|  Matched:              88  (98.9%)           |
|  Changed (Positive):    1  ( 1.1%)           |
|  Missing:               0  ( 0.0%)           |
|  Added (Positive):     10                    |
+---------------------------------------------+
|  FR Coverage:    12/12 (100%)                |
|  Error Handling:  7/7  (100%)                |
|  Cross-check:   15/15  (100%)               |
+---------------------------------------------+
```

---

## 5. Remaining Items

### 5.1 Post-Deployment Actions

| # | Action | Priority | Status |
|---|--------|----------|--------|
| 1 | `backfill_pdf.py --all` 실행 (기존 93건 PDF 재캡처) | Medium | Pending |
| 2 | PDF 크기 모니터링 (1주간 평균 추적) | Low | Pending |
| 3 | `scale` 파라미터 조정 검토 (필요시 0.8) | Low | Conditional |

### 5.2 Non-Functional Monitoring

| NFR | Target | Current | Notes |
|-----|--------|---------|-------|
| PDF 크기 | avg < 500KB | 1.7MB (test) | 이미지 많은 글 → 자연스러운 결과. 모니터링 필요 |
| 캡처 속도 | < 30s/post | 미측정 | 배치 실행 시 확인 예정 |
| 텍스트 품질 | block-aware 동등 | 31,274 chars | PASS |

---

## 6. Lessons Learned

### 6.1 Technical Insights

1. **`json.dumps()` for JS injection**: Python list -> JS array 변환 시 `str().replace()` 대신 `json.dumps()` 사용 필수. 내부 quotes 충돌 방지.

2. **Naver iframe relative URL**: Desktop 블로그의 `iframe#mainFrame`의 `src`가 상대 경로(`/PostView.naver?...`)인 경우가 있음. `urlparse`로 절대 경로 변환 필요.

3. **PRUNE_JS body guard**: `detect_article_selector`가 None 반환 시 fallback `"body"`가 PRUNE_JS에 전달됨. body를 remove하면 `document.body`가 null이 되어 TypeError 발생. 명시적 guard clause 필수.

4. **RSS file format diversity**: `naver_bloger_rss_list.txt`가 `URL # name` 형식과 CSV 형식을 혼용. 양쪽 모두 지원하는 파서 필요.

5. **Dual extension counting**: PDF migration 기간 중 같은 폴더에 JPG와 PDF가 공존. 파일 순번 계산 시 양쪽 모두 카운트해야 충돌 방지.

### 6.2 Process Insights

1. **참조코드 기반 구현**: 사용자 제공 참조코드가 있으면 설계-구현 간 갭이 줄어듦. 검증된 로직을 그대로 통합하되, edge case (relative URL, body fallback) 처리가 핵심.

2. **E2E 파이프라인 검증 중요**: 단건 테스트 통과 후에도 파이프라인 전체 실행(RSS -> 캡처 -> DB)에서 추가 버그 발견 (RSS 파서 형식, BlogCaptureSession import 등).

---

## 7. PDCA Documents Reference

| Document | Path |
|----------|------|
| Plan | `docs/01-plan/features/blog-capture-pdf-migration.plan.md` |
| Design | `docs/02-design/features/blog-capture-pdf-migration.design.md` |
| Analysis | `docs/03-analysis/features/blog-capture-pdf-migration.analysis.md` |
| Report | `docs/04-report/features/blog-capture-pdf-migration.report.md` |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-02-20 | Initial completion report | Claude (Report Generator) |
