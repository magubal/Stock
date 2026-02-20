# blog-investor-digest Design Document

> **Summary**: 투자자 블로그 수집글을 열람/AI정리/수정저장하는 대시보드 + 수집 파이프라인 강화
>
> **Project**: Stock Research ONE
> **Author**: PSJ + Claude
> **Date**: 2026-02-19
> **Status**: Draft
> **Planning Doc**: [blog-investor-digest.plan.md](../../01-plan/features/blog-investor-digest.plan.md)

---

## 1. Overview

### 1.1 Design Goals

1. 기존 REQ-001 수집기에 **텍스트 추출** 기능을 추가하여 이미지+텍스트 동시 수집
2. 수집된 데이터를 **DB(SQLite)** 에 적재하여 API로 조회 가능하게 구성
3. **Claude API** 기반 자동 요약(내용/관점/시사점) 생성, Vision fallback
4. **Master-Detail 대시보드**에서 날짜별 열람, 수정/저장, 원문 링크 제공

### 1.2 Design Principles

- 기존 dashboard/ 정적 HTML + CDN React 패턴 일관성 유지
- 기존 `final_body_capture.py` Playwright 세션에 텍스트 추출만 추가 (최소 변경)
- 텍스트 우선 AI 분석으로 비용 억제, Vision은 fallback으로만 사용

---

## 2. Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 22:00 배치 스크립트 (scripts/blog_monitor/run_blog.py)       │
│                                                             │
│  RSS 파싱 → Playwright 캡처(이미지+텍스트) → DB 저장          │
│         → Claude API 요약 생성 → DB blog_summaries 저장      │
└─────────────────┬───────────────────────────────────────────┘
                  │ SQLite
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ FastAPI Backend (backend/app/api/blog_review.py)            │
│                                                             │
│  GET  /posts?date=         → 날짜별 글 리스트               │
│  GET  /posts/{id}          → 글 상세 + 요약                 │
│  PUT  /posts/{id}/summary  → 사용자 수정 저장               │
│  GET  /posts/{id}/image    → 캡처 이미지 서빙               │
│  POST /posts/analyze/{id}  → 단건 AI 재분석                 │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTP
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ Dashboard (dashboard/blog_review.html)                       │
│                                                             │
│  ┌──────────────┐  ┌──────────────────────────────────────┐ │
│  │ 좌측 패널     │  │ 우측 패널                             │ │
│  │ (30%)        │  │ (70%)                                │ │
│  │              │  │                                      │ │
│  │ 날짜 선택    │  │ AI 정리본 (내용/관점/시사점)          │ │
│  │ 블로거 필터  │  │ 캡처 이미지 미리보기                  │ │
│  │ 글 제목 리스트│  │ 수정/저장 버튼                       │ │
│  │              │  │ 원문 링크 (새탭)                      │ │
│  └──────────────┘  └──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
[수집 배치 22:00]
RSS 파싱 (naver_blog_collector.py 재사용)
    → 새 글 감지 (tracked_posts.json 체크)
    → Playwright 캡처 세션 (final_body_capture.py 확장)
        → 이미지 캡처 (기존 .jpg)
        → 본문 텍스트 추출 (NEW: innerText)
    → DB blog_posts INSERT
    → Claude API 요약 생성
        → 텍스트 있으면: claude-sonnet text 분석
        → 텍스트 없으면: claude-sonnet vision 분석 (이미지)
    → DB blog_summaries INSERT
    → JSON 메타데이터 저장 (기존 호환)

[대시보드 조회]
사용자 날짜 선택 → GET /posts?date → 좌측 리스트 렌더링
글 클릭 → GET /posts/{id} → 우측 패널 (요약 + 이미지)
수정/저장 → PUT /posts/{id}/summary → DB UPDATE
제목 클릭 → window.open(original_link) → 새탭
```

### 2.3 Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| blog_review.html | FastAPI backend | API 호출 |
| blog_review API | SQLAlchemy models | DB CRUD |
| 수집 배치 | Playwright, anthropic SDK | 캡처 + AI 분석 |
| 수집 배치 | naver_blog_collector.py | RSS 파싱 재사용 |
| AI 분석 | ANTHROPIC_API_KEY | Claude API 접근 |

---

## 3. Data Model

### 3.1 Entity Definition (SQLAlchemy)

```python
# backend/app/models/blog_post.py

class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    blogger = Column(String(50), nullable=False)       # 블로거 이름
    title = Column(String(500), nullable=False)        # 글 제목
    link = Column(String(1000), nullable=False)        # 원문 URL
    pub_date = Column(DateTime, nullable=True)         # 게시일시
    text_content = Column(Text, nullable=True)         # 추출된 본문 텍스트
    image_path = Column(String(500), nullable=True)    # 캡처 이미지 상대경로
    image_size_kb = Column(Integer, default=0)         # 이미지 크기 (KB)
    collected_at = Column(DateTime, default=func.now()) # 수집일시
    source = Column(String(20), default="COLLECTOR")   # COLLECTOR or DEMO

    summaries = relationship("BlogSummary", back_populates="post")

class BlogSummary(Base):
    __tablename__ = "blog_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("blog_posts.id"), nullable=False)
    summary = Column(Text, nullable=True)              # 내용 요약
    viewpoint = Column(Text, nullable=True)            # 핵심 관점
    implications = Column(Text, nullable=True)         # 시사점
    is_edited = Column(Boolean, default=False)         # 사용자 수정 여부
    edited_at = Column(DateTime, nullable=True)        # 수정일시
    ai_model = Column(String(50), nullable=True)       # claude-text / claude-vision
    created_at = Column(DateTime, default=func.now())

    post = relationship("BlogPost", back_populates="summaries")
```

### 3.2 Entity Relationships

```
[BlogPost] 1 ──── N [BlogSummary]
   │
   ├── blogger (투자자명)
   ├── title (글 제목)
   ├── link (원문 URL)
   ├── text_content (본문 텍스트)
   └── image_path (캡처 이미지)
```

> 1:N 관계이나, 실질적으로 1:1 사용 (AI 재분석 시 새 row 생성, latest 사용)

---

## 4. API Specification

### 4.1 Endpoint List

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/blog-review/posts` | 날짜별 글 리스트 | - |
| GET | `/api/v1/blog-review/posts/{id}` | 글 상세 + 최신 요약 | - |
| PUT | `/api/v1/blog-review/posts/{id}/summary` | 요약 수정/저장 | - |
| GET | `/api/v1/blog-review/posts/{id}/image` | 캡처 이미지 서빙 | - |
| POST | `/api/v1/blog-review/posts/{id}/analyze` | 단건 AI 재분석 | - |
| GET | `/api/v1/blog-review/bloggers` | 블로거 목록 | - |

### 4.2 Detailed Specification

#### `GET /api/v1/blog-review/posts`

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| date | string | today | YYYY-MM-DD 필터 |
| blogger | string | null | 블로거명 필터 (optional) |

**Response (200):**
```json
{
  "date": "2026-02-19",
  "total": 25,
  "posts": [
    {
      "id": 1,
      "blogger": "daybyday",
      "title": "26.2.19 Day 미국 주식 마감 시황",
      "link": "https://blog.naver.com/...",
      "pub_date": "2026-02-19T08:52:19",
      "has_summary": true,
      "is_edited": false,
      "image_size_kb": 350,
      "source": "COLLECTOR"
    }
  ]
}
```

#### `GET /api/v1/blog-review/posts/{id}`

**Response (200):**
```json
{
  "id": 1,
  "blogger": "daybyday",
  "title": "26.2.19 Day 미국 주식 마감 시황",
  "link": "https://blog.naver.com/...",
  "pub_date": "2026-02-19T08:52:19",
  "text_content": "본문 텍스트...",
  "image_path": "data/naver_blog_data/2026-02-19/daybyday_001.jpg",
  "summary": {
    "id": 1,
    "summary": "내용 요약...",
    "viewpoint": "핵심 관점...",
    "implications": "시사점...",
    "is_edited": false,
    "ai_model": "claude-text",
    "created_at": "2026-02-19T22:05:00"
  }
}
```

#### `PUT /api/v1/blog-review/posts/{id}/summary`

**Request:**
```json
{
  "summary": "수정된 내용 요약",
  "viewpoint": "수정된 핵심 관점",
  "implications": "수정된 시사점"
}
```

**Response (200):**
```json
{
  "id": 1,
  "post_id": 1,
  "is_edited": true,
  "edited_at": "2026-02-19T23:10:00"
}
```

#### `GET /api/v1/blog-review/posts/{id}/image`

**Response**: Binary image (JPEG), Content-Type: image/jpeg
- Path traversal 보안 검증 적용
- 이미지 없으면 404

---

## 5. UI/UX Design

### 5.1 Screen Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  ← 대시보드    투자자 블로그 정리                     2026-02-19 ▼  │
├──────────────────────┬──────────────────────────────────────────────┤
│  📅 날짜: [2026-02-19]│                                            │
│  블로거: [전체 ▼]     │  📄 26.2.19 Day 미국 주식 마감 시황  ↗     │
│                      │  by daybyday | 2026-02-19 08:52             │
│  ── daybyday (3) ──  │                                             │
│  > 미국 주식 마감 시황│  ┌─ 내용 요약 ──────────────────────────┐  │
│    미 증시 3대 지수   │  │ [textarea - editable]                │  │
│    오늘의 특징주      │  │ AI가 생성한 내용 요약 텍스트...       │  │
│                      │  └──────────────────────────────────────┘  │
│  ── 라틴카페 (2) ──  │                                             │
│    시장 관전 포인트   │  ┌─ 핵심 관점 ──────────────────────────┐  │
│    섹터 분석 노트     │  │ [textarea - editable]                │  │
│                      │  │ 투자자의 핵심 관점...                  │  │
│  ── 유수암바람 (1) ── │  └──────────────────────────────────────┘  │
│    매매 일지          │                                             │
│                      │  ┌─ 시사점 ────────────────────────────┐   │
│                      │  │ [textarea - editable]                │  │
│                      │  │ 나에게 주는 시사점...                  │  │
│                      │  └──────────────────────────────────────┘  │
│                      │                                             │
│                      │  [💾 저장]  [🔄 AI 재분석]                   │
│                      │                                             │
│  25건 수집됨          │  ┌─ 캡처 이미지 ───────────────────────┐  │
│  3건 AI 미분석        │  │ [이미지 축소 표시, 클릭시 확대]      │  │
│                      │  └──────────────────────────────────────┘  │
└──────────────────────┴──────────────────────────────────────────────┘
```

### 5.2 User Flow

```
대시보드 index.html
    → "투자자 글정리" 카드 클릭
    → blog_review.html 이동
    → 날짜 선택 (기본: 오늘)
    → 좌측: 블로거별 글 제목 리스트 로딩
    → 글 제목 클릭 → 우측: AI 정리본 표시
    → 제목 옆 ↗ 아이콘 클릭 → 새탭에서 원문 확인
    → 정리본 수정 → 저장 버튼 → DB 반영
    → (선택) AI 재분석 버튼 → 새 요약 생성
```

### 5.3 Component List

| Component | Location | Responsibility |
|-----------|----------|----------------|
| DatePicker | blog_review.html 좌측 상단 | 날짜 선택 → API 호출 |
| BloggerFilter | blog_review.html 좌측 | 블로거별 필터링 |
| PostList | blog_review.html 좌측 | 글 제목 리스트 (그룹핑) |
| SummaryPanel | blog_review.html 우측 | AI 정리본 표시/수정 |
| ImagePreview | blog_review.html 우측 하단 | 캡처 이미지 축소 표시 |
| SaveButton | blog_review.html 우측 | PUT API 호출 |

### 5.4 대시보드 테마

| 항목 | 값 |
|------|-----|
| 테마 색상 | Green `#22c55e` |
| 카드 위치 | `dashboard/index.html` 시장모니터링 섹션 |
| 파일명 | `dashboard/blog_review.html` |

---

## 6. 수집 파이프라인 설계

### 6.1 텍스트 추출 확장 (final_body_capture.py)

기존 `capture()` 메서드에 텍스트 추출 추가:

```python
# 기존 이미지 캡처 후, 텍스트도 추출
text_content = page.evaluate("""
    () => {
        const selectors = ['.se-main-container', '#postViewArea',
                          '.blogview_content', 'article'];
        for (let sel of selectors) {
            const el = document.querySelector(sel);
            if (el && el.innerText.trim().length > 100) {
                return el.innerText.trim();
            }
        }
        return document.body.innerText.trim().substring(0, 5000);
    }
""")
```

반환값에 `text_content` 필드 추가:
```python
result = {
    "success": True,
    "file_path": str(final_path),
    "file_size_mb": file_size_mb,
    "text_content": text_content,  # NEW
    "message": "OK"
}
```

### 6.2 배치 스크립트 구조

```
scripts/blog_monitor/
├── config.py              # 설정 (DB 경로, API 키, 블로거 목록)
├── run_blog.py            # 메인 배치 (CLI entry point)
├── blog_db_service.py     # DB CRUD (blog_posts, blog_summaries)
├── blog_analyzer.py       # Claude API 요약 생성 (text + vision)
└── seed_data.py           # DEMO 시드 데이터
```

### 6.3 AI 분석 프롬프트

```
당신은 한국 주식시장 전문 애널리스트입니다.
아래 투자자 블로그 글을 분석하여 JSON으로 응답하세요.

블로거: {blogger}
제목: {title}
본문:
{text_content}

응답 형식:
{
  "summary": "글의 핵심 내용을 3-5문장으로 요약",
  "viewpoint": "투자자의 핵심 관점과 논거를 2-3문장으로 정리",
  "implications": "이 글이 나의 투자에 주는 시사점을 2-3문장으로 정리"
}
```

### 6.4 Vision Fallback

텍스트가 100자 미만이면 Vision API 사용:
```python
if len(text_content) < 100 and image_path:
    # Claude Vision으로 이미지 분석
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()
    # vision prompt로 분석 요청
```

---

## 7. Security Considerations

- [x] 이미지 서빙 path traversal 차단 (`..` 금지, resolve 검증)
- [x] 이미지 확장자 허용 목록 (.jpg, .png, .jpeg)
- [x] API rate limiting 불필요 (로컬 전용)
- [ ] ANTHROPIC_API_KEY 노출 방지 (환경변수)

---

## 8. Error Handling

| Code | Scenario | Handling |
|------|----------|----------|
| 404 | 해당 날짜에 수집 데이터 없음 | "수집된 글이 없습니다" 메시지 표시 |
| 404 | 이미지 파일 없음 | placeholder 이미지 표시 |
| 500 | AI 분석 실패 | "AI 분석 실패" 메시지 + 수동 입력 안내 |
| 500 | DB 저장 실패 | 에러 toast + retry 안내 |

---

## 9. Implementation Order

### Phase 1: Core (MVP)
1. [ ] DB 모델 생성: `backend/app/models/blog_post.py` (BlogPost, BlogSummary)
2. [ ] `backend/app/models/__init__.py`에 import 추가
3. [ ] 수집기 텍스트 추출 강화: `scripts/final_body_capture.py` 수정
4. [ ] 배치 스크립트: `scripts/blog_monitor/` (config, run_blog, blog_db_service)
5. [ ] 기존 파일 데이터 → DB 마이그레이션 스크립트
6. [ ] FastAPI 라우터: `backend/app/api/blog_review.py`
7. [ ] Service 레이어: `backend/app/services/blog_review_service.py`
8. [ ] `backend/app/main.py` 라우터 등록
9. [ ] 대시보드 페이지: `dashboard/blog_review.html`
10. [ ] `dashboard/index.html` 시장모니터링에 카드 추가

### Phase 2: AI + Schedule
11. [ ] AI 분석기: `scripts/blog_monitor/blog_analyzer.py`
12. [ ] Vision fallback 경로
13. [ ] POST /posts/{id}/analyze 재분석 엔드포인트
14. [ ] 시드 데이터: `scripts/blog_monitor/seed_data.py` (DEMO 규칙)
15. [ ] 22:00 배치 스크립트 + Task Scheduler 등록

### Phase 3: 최적화
16. [ ] 이미지 JPEG 품질 조정 (60~70%, ~300KB 목표)
17. [ ] 기존 이미지 일괄 리사이즈 유틸리티

---

## 10. Coding Convention

| Item | Convention |
|------|-----------|
| Dashboard 파일 | `dashboard/blog_review.html` (정적 HTML + CDN React) |
| API prefix | `/api/v1/blog-review/` |
| DB model 파일 | `backend/app/models/blog_post.py` |
| 스크립트 폴더 | `scripts/blog_monitor/` |
| 테마 색상 | Green `#22c55e` |
| DEMO 데이터 | `source="DEMO"` 필수 마킹 |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-19 | Initial draft | PSJ + Claude |
