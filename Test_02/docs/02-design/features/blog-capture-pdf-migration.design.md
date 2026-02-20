# blog-capture-pdf-migration Design Document

> **Summary**: 블로그 캡처 저장을 JPG→A4 PDF로 전환, 참조코드 기반 통합, 기존 93건 재캡처
>
> **Project**: Stock Research ONE
> **Author**: PSJ + Claude
> **Date**: 2026-02-20
> **Status**: Draft
> **Planning Doc**: [blog-capture-pdf-migration.plan.md](../../01-plan/features/blog-capture-pdf-migration.plan.md)

---

## 1. Overview

### 1.1 Design Goals

1. `final_body_capture.py`를 **참조코드 기반**으로 전면 재작성 → PDF 출력
2. 데스크톱 iframe 접근 + DOM pruning + A4 `page.pdf()` 통합
3. **텍스트 추출**은 DOM pruning 전에 수행 (기존 block-aware 로직 유지)
4. 파이프라인/API/대시보드를 PDF에 맞게 수정
5. 기존 93건 블로그 URL 재방문 → PDF 재캡처

### 1.2 Design Principles

- 참조코드(`save_post_pdf_only_article.py`)의 검증된 로직을 최대한 유지
- `BlogCaptureSession` 클래스 인터페이스 보존 (호출부 변경 최소화)
- DB 스키마 변경 없음 (`image_path` 컬럼 값만 `.jpg` → `.pdf`)
- 기존 JPG 파일은 삭제하지 않음 (PDF 재캡처 후 수동 판단)

---

## 2. Architecture

### 2.1 변경 영향도 맵

```
┌──────────────────────────────────────────────────────┐
│ 변경 파일                        변경 수준           │
├──────────────────────────────────────────────────────┤
│ scripts/final_body_capture.py    ★★★ 전면 재작성    │
│ scripts/blog_monitor/run_blog.py ★☆☆ 확장자 변경    │
│ scripts/naver_blog_collector.py  ★☆☆ 확장자 변경    │
│ backend/app/api/blog_review.py   ★☆☆ media_type     │
│ backend/app/services/blog_review_service.py          │
│                                  ★☆☆ 확장자 허용    │
│ dashboard/blog_review.html       ★★☆ PDF viewer     │
│ scripts/blog_monitor/backfill_pdf.py ★★★ 신규 생성  │
├──────────────────────────────────────────────────────┤
│ backend/app/models/blog_post.py  변경 없음           │
│ docs/.bkit-memory.json           phase 업데이트       │
└──────────────────────────────────────────────────────┘
```

### 2.2 데이터 흐름 (변경 후)

```
[22:00 배치] run_blog.py
  ↓ RSS 파싱 → 새 글 감지
  ↓ BlogCaptureSession.capture(url, blogger)
  │   ├── 1) goto 데스크톱 URL
  │   ├── 2) iframe#mainFrame → src 추출 → goto iframe URL
  │   ├── 3) auto_scroll (lazy-load, break on scroll stop)
  │   ├── 4) 텍스트 추출 (block-aware, content selector 기반)
  │   ├── 5) PRUNE_JS (본문만 body에 남기기 + print CSS)
  │   ├── 6) page.emulate_media("print")
  │   └── 7) page.pdf(format="A4", margins, print_background)
  │         → data/naver_blog_data/YYYY-MM-DD/blogger_NNN.pdf
  ↓ DB blog_posts INSERT (image_path=*.pdf, text_content)
  ↓ Claude API 요약 생성 → DB blog_summaries INSERT

[대시보드] blog_review.html
  GET /posts/{id}/image → FileResponse(*.pdf, application/pdf)
  <iframe src="..." /> → 브라우저 내장 PDF viewer
```

---

## 3. Detailed Design

### 3.1 `scripts/final_body_capture.py` (전면 재작성)

#### 3.1.1 클래스 구조 (인터페이스 보존)

```python
class BlogCaptureSession:
    """브라우저를 재사용하는 캡처 세션 (PDF 버전)"""

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None

    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 2000},
            device_scale_factor=2,
            user_agent="Mozilla/5.0 ..."
        )
        return self

    def __exit__(self, *args):
        # cleanup (기존과 동일)

    def capture(self, blog_url: str, blogger_id: str) -> dict:
        """단일 블로그 글 캡처 → PDF + 텍스트"""
        return {
            "success": bool,
            "file_path": str,       # *.pdf 경로
            "file_size_mb": float,
            "text_content": str,    # block-aware 추출 텍스트
            "message": str,
        }
```

#### 3.1.2 `capture()` 내부 흐름

```python
def capture(self, blog_url, blogger_id):
    page = self.context.new_page()
    try:
        # Step 1: URL 정리 (RSS 파라미터 제거, 데스크톱 유지)
        clean_url = strip_rss_params(blog_url)

        # Step 2: 페이지 접속 + iframe 처리
        open_iframe_or_self(page, clean_url)

        # Step 3: auto_scroll (lazy-load, break 조건)
        auto_scroll(page, step=1500, pause=0.12, loops=400)
        time.sleep(2.0)

        # Step 4: 텍스트 추출 (pruning 전!)
        text_content = extract_text(page)

        # Step 5: DOM pruning (PRUNE_JS)
        sel = detect_article_selector(page)
        page.evaluate(PRUNE_JS, sel or "body")

        # Step 6: PDF 생성
        page.emulate_media(media="print")
        page.pdf(
            path=final_path,
            print_background=True,
            format="A4",
            margin={"top":"12mm","right":"10mm","bottom":"12mm","left":"10mm"},
            prefer_css_page_size=True,
            scale=1.0,
        )

        return {"success": True, "file_path": str(final_path),
                "file_size_mb": ..., "text_content": text_content}
    finally:
        page.close()
```

#### 3.1.3 핵심 함수들 (참조코드에서 통합)

**`open_iframe_or_self(page, url)`**
```python
def open_iframe_or_self(page, url):
    """데스크톱 네이버 블로그 접속 + iframe 내부 진입."""
    try:
        page.goto(url, wait_until="networkidle", timeout=60000)
    except TimeoutError:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)

    iframe = page.query_selector("iframe#mainFrame")
    if iframe:
        src = iframe.get_attribute("src")
        if src and src.startswith("http"):
            page.goto(src, wait_until="networkidle", timeout=60000)
```

**`auto_scroll(page)`**
```python
def auto_scroll(page, step=1500, pause=0.12, loops=400):
    """스크롤하여 lazy-load 트리거. scrollY 변화 없으면 중단."""
    last = -1
    for _ in range(loops):
        page.evaluate(f"window.scrollBy(0,{step})")
        time.sleep(pause)
        cur = page.evaluate("window.scrollY")
        if cur == last:
            break
        last = cur
    page.evaluate("window.scrollTo(0,0)")
```

**`detect_article_selector(page)`**
```python
ARTICLE_SELECTORS = [
    ".se-main-container",
    "#postViewArea",
    "article.se_component",
    "article[data-role='post']",
    ".se-viewer",
]

def detect_article_selector(page):
    """본문 컨테이너 셀렉터 자동 감지."""
    for sel in ARTICLE_SELECTORS:
        loc = page.locator(sel)
        if loc.count() > 0 and loc.first.is_visible():
            return sel
    return None
```

**`PRUNE_JS`** (참조코드 그대로)
```javascript
(sel) => {
  const el = document.querySelector(sel);
  if (!el) return false;

  // 이미지 지연로딩 해제
  document.querySelectorAll('img[data-src]').forEach(img => {
    img.src = img.getAttribute('data-src');
  });

  // body 정리 → 본문만 남기기
  Array.from(document.body.children).forEach(c => {
    if (!el.contains(c) && c !== el) c.remove();
  });

  // 본문을 body 직속으로 이동
  if (el.parentElement !== document.body) {
    el.remove();
    document.body.innerHTML = "";
    document.body.appendChild(el);
  }

  // 스타일 정리
  el.style.maxWidth = '100%';
  el.style.margin = '0';
  el.style.padding = '0';

  // print용 CSS 주입
  const css = `@media print {
    html, body { margin:0!important; padding:0!important; background:#fff!important; }
    * { visibility:visible!important; }
    a { color:inherit; text-decoration:none; }
    img { max-width:100%!important; height:auto!important; }
  }`;
  const s = document.createElement('style');
  s.textContent = css;
  document.head.appendChild(s);

  window.scrollTo(0,0);
  return true;
}
```

**`extract_text(page)`** (기존 block-aware 로직)
```python
def extract_text(page):
    """DOM pruning 전에 본문 텍스트를 block-aware로 추출."""
    # 기존 backfill_text.py의 개선된 로직 사용:
    # - content selector 매칭 (.se-main-container 등)
    # - unwanted elements 제거
    # - br → \n, block elements 앞에 \n 삽입
    # - zero-width space 제거, 빈 줄 정리
    # - max 50,000 chars
```

#### 3.1.4 파일 저장 경로

```
# 기존 JPG 패턴 (유지, 확장자만 변경)
data/naver_blog_data/YYYY-MM-DD/blogger_NNN.pdf

# 예시
data/naver_blog_data/2026-02-20/daybyday_001.pdf
data/naver_blog_data/2026-02-20/daybyday_002.pdf
data/naver_blog_data/2026-02-20/라틴카페_001.pdf
```

#### 3.1.5 호환 함수 (기존 API 유지)

```python
def extract_body_only_capture(blog_url, blogger_id="unknown"):
    """단일 블로그 글 캡처 (기존 호환)."""
    with BlogCaptureSession() as session:
        return session.capture(blog_url, blogger_id)
```

---

### 3.2 `scripts/blog_monitor/run_blog.py` 수정

변경 포인트:
- `image_path` 계산 시 `.jpg` → `.pdf` (실제로는 capture 결과의 file_path 그대로 사용)
- `image_size_kb` 계산: `int(cap["file_size_mb"] * 1024)` (동일)
- `register_from_files()`: 파일 확장자 검색 `.pdf` 추가

```python
# 기존
for ext in (".jpg", ".jpeg", ".png"):
    candidate = date_dir / f"{stem}{ext}"

# 변경
for ext in (".pdf", ".jpg", ".jpeg", ".png"):
    candidate = date_dir / f"{stem}{ext}"
```

---

### 3.3 `scripts/naver_blog_collector.py` 수정

변경 포인트:
- 파일 이름 생성: `{blogger}_{seq:03d}.jpg` → `{blogger}_{seq:03d}.pdf`
- 기존 파일 카운팅: `save_dir.glob(f"{blogger_id}_*.jpg")` → `.pdf`

---

### 3.4 `backend/app/services/blog_review_service.py` 수정

`resolve_image_path()`:

```python
# 기존
if full.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
    return None

# 변경
if full.suffix.lower() not in (".pdf", ".jpg", ".jpeg", ".png", ".webp"):
    return None
```

---

### 3.5 `backend/app/api/blog_review.py` 수정

`get_post_image()`:

```python
# 기존
media = "image/jpeg" if resolved.suffix.lower() in (".jpg", ".jpeg") else "image/png"

# 변경
suffix = resolved.suffix.lower()
if suffix == ".pdf":
    media = "application/pdf"
elif suffix in (".jpg", ".jpeg"):
    media = "image/jpeg"
elif suffix == ".png":
    media = "image/png"
else:
    media = "application/octet-stream"

return FileResponse(str(resolved), media_type=media)
```

---

### 3.6 `dashboard/blog_review.html` 수정

#### PDF 표시 섹션 (기존 `<img>` → `<iframe>`)

```jsx
{/* 기존: 이미지 섹션 */}
<img src={`${API_BASE}/posts/${postDetail.id}/image`} alt={postDetail.title} />

{/* 변경: PDF 뷰어 */}
{postDetail.image_path && postDetail.image_path.endsWith('.pdf') ? (
    <iframe
        src={`${API_BASE}/posts/${postDetail.id}/image`}
        style={{width:'100%', height:'80vh', border:'1px solid #333'}}
        title={postDetail.title}
    />
) : postDetail.image_path ? (
    <img src={`${API_BASE}/posts/${postDetail.id}/image`}
         alt={postDetail.title}
         style={{maxWidth:'100%'}} />
) : (
    <div className="no-image">캡처 파일 없음</div>
)}
```

- PDF: `<iframe>` 사용 → 브라우저 내장 PDF viewer (페이지 탐색, 확대/축소, 인쇄)
- JPG 호환: 기존 이미지도 표시 가능 (하위 호환)
- 토글 라벨: "캡처 이미지" → "캡처 PDF" (PDF일 때) / "캡처 이미지" (JPG일 때)

---

### 3.7 `scripts/blog_monitor/backfill_pdf.py` (신규)

```python
"""
기존 blog_posts의 JPG를 PDF로 재캡처.
URL 재방문 → PDF 생성 → DB image_path 업데이트.

Usage:
    python backfill_pdf.py                    # 전체 (limit 50)
    python backfill_pdf.py --date 2026-02-18  # 특정 날짜만
    python backfill_pdf.py --id 93            # 특정 ID만
    python backfill_pdf.py --limit 100        # 최대 N건
"""

# 흐름:
# 1) DB에서 image_path가 .jpg/.png인 포스트 조회
# 2) BlogCaptureSession으로 URL 재방문 → PDF 생성
# 3) text_content도 함께 업데이트 (NULL이면)
# 4) DB image_path를 .pdf 경로로 UPDATE
# 5) 성공/실패 통계 출력
```

---

## 4. Implementation Order

### Step 1: `final_body_capture.py` 전면 재작성
- `BlogCaptureSession` PDF 버전 구현
- 참조코드 `PRUNE_JS`, `auto_scroll`, `open_iframe_or_self` 통합
- `extract_text()` block-aware 로직 통합
- 단건 테스트: `extract_body_only_capture(url, blogger)` 호출

### Step 2: Pipeline 수정
- `run_blog.py`: PDF 경로 처리 (확장자 변경)
- `naver_blog_collector.py`: 파일명 `.pdf`, glob 패턴 변경

### Step 3: Backend 수정
- `blog_review_service.py`: `resolve_image_path()` PDF 허용
- `blog_review.py`: media_type 분기

### Step 4: Dashboard 수정
- `blog_review.html`: `<img>` → `<iframe>` PDF viewer (JPG 하위 호환)

### Step 5: Backfill
- `backfill_pdf.py` 생성
- 기존 93건 PDF 재캡처 실행

---

## 5. Testing Strategy

### 5.1 단건 검증
```bash
# PDF 캡처 테스트 (단일 URL)
python scripts/final_body_capture.py
# → data/naver_blog_data/YYYY-MM-DD/test_001.pdf 생성 확인
# → A4 다페이지 확인, 이미지 선명도, 텍스트 추출 확인
```

### 5.2 배치 검증
```bash
# run_blog.py 실행
python scripts/blog_monitor/run_blog.py --skip-ai
# → PDF 파일 생성 확인
# → DB image_path에 .pdf 경로 저장 확인
```

### 5.3 API 검증
```bash
# PDF 서빙 확인
curl http://localhost:8000/api/v1/blog-review/posts/93/image -o test.pdf
file test.pdf  # → PDF document 확인
```

### 5.4 대시보드 검증
- `blog_review.html` 접속
- 글 선택 → PDF viewer 표시 확인
- 페이지 넘기기, 확대/축소 동작 확인
- 기존 JPG 글도 이미지로 표시 확인 (하위 호환)

### 5.5 백필 검증
```bash
python scripts/blog_monitor/backfill_pdf.py --date 2026-02-18
# → 1건 PDF 재캡처 성공 확인
# → DB image_path 업데이트 확인
```
