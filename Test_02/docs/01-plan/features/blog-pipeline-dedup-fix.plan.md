# blog-pipeline-dedup-fix Planning Document

> **Summary**: `naver_blog_collector.py` 파이프라인에 pub_date 기반 최근 N일 필터 추가 + tracked_posts.json 데이터 무결성 보장 + run_blog.py 역할 명확화
>
> **Project**: Stock Research ONE
> **Author**: PSJ + Claude
> **Date**: 2026-02-20
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

REQ-01 블로그 수집 파이프라인(`naver_blog_collector.py`)에 pub_date 기반 날짜 필터를 추가하여, RSS에서 가져온 글 중 최근 N일 이내에 발행된 글만 수집한다. 또한 tracked_posts.json의 데이터 무결성을 보장하고, `run_blog.py`와의 역할 분리를 명확히 한다.

### 1.2 Background

- **REQ-01 현재 동작**: RSS 최근 10개 아이템을 가져와서 `tracked_posts.json`(MD5 해시) 기반 dedup만 수행. pub_date 필터 없음.
- **문제 발견**: `run_blog.py`가 별도 dedup(DB 기반)을 사용하여 기존 수집분 68건을 재수집함
- **데이터 분석 결과** (2026-02-01 ~ 2026-02-20, 251건):
  - pub_date vs collected_date 차이: 평균 3.4일, 최대 12일
  - 0일(당일): 33건 (13.2%)
  - 0~3일: 157건 (62.5%)
  - 0~7일: 220건 (87.6%)
  - 8일+: 31건 (12.4%)
- **tracked_posts.json 불일치**: 실제 수집 파일 93건 vs tracked_posts 48건 → 재구축 완료 (98건)
- **브레인스토밍 결과**: A안(collector에 pub_date 필터 추가, 최소 변경) 채택

### 1.3 Related Documents

- 주력 수집기: `scripts/naver_blog_collector.py` (tracked_posts.json dedup)
- 보조 수집기: `scripts/blog_monitor/run_blog.py` (DB dedup, AI 분석)
- 캡처 모듈: `scripts/final_body_capture.py` (v4.0 PDF, PDCA 완료 98.9%)
- 스케줄러: `scripts/naver_blog_scheduler.py` (매일 09:00)
- dedup 파일: `data/naver_blog_data/index/tracked_posts.json` (현재 98건)
- 메타데이터: `data/naver_blog_data/YYYY-MM-DD/*.json` (sidecar 파일)
- RSS 목록: `data/naver_blog_data/naver_bloger_rss_list.txt` (3명 블로거)

---

## 2. Scope

### 2.1 In Scope

- [ ] `naver_blog_collector.py`에 pub_date 기반 필터 추가 (최근 N일, 기본값 7)
- [ ] `pubDate` 파싱 로직 강화 (RFC 2822 + fallback 포맷)
- [ ] 파싱 실패 시 수집 허용 (누락 방지 안전장치)
- [ ] `naver_blog_scheduler.py` 스케줄 시간 확인/조정
- [ ] `run_blog.py` 역할 명확화: DB sync 전용 (수집은 collector 전담)
- [ ] tracked_posts.json 무결성 검증 스크립트
- [ ] 2026-02-20_backup 정리 판단

### 2.2 Out of Scope

- `run_blog.py` 대폭 수정 (현재는 역할 분리만)
- 블로거 자동 추가/삭제 기능
- AI 분석 파이프라인 수정 (blog_analyzer.py)
- `final_body_capture.py` 수정 (PDF 마이그레이션 완료)

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | `collect_blogger_posts()`에 pub_date 파싱 + N일 이내 필터 | High | Pending |
| FR-02 | N일 기본값 = 7 (CLI 파라미터 `--days`로 조정 가능) | High | Pending |
| FR-03 | `pubDate` 파싱: `email.utils.parsedate_to_datetime` + timezone-aware 비교 | High | Pending |
| FR-04 | 파싱 실패 시 해당 글은 수집 허용 (누락 방지) | High | Pending |
| FR-05 | `main()` 함수에 `--days` CLI 인자 추가 | Medium | Pending |
| FR-06 | `naver_blog_scheduler.py`에서 `max_posts_per_blogger` + `days` 파라미터 전달 | Medium | Pending |
| FR-07 | `run_blog.py` docstring에 역할 명확화 (DB sync 전용) | Low | Pending |
| FR-08 | tracked_posts 무결성 검증: JSON sidecar 파일과 tracked_posts.json 대조 | Low | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| Dedup 정확도 | 날짜 변경 후에도 중복 0건 | 재실행 테스트 |
| 수집 누락 | pub_date 파싱 실패 글은 수집 허용 | 로그 확인 |
| 하위 호환 | 기존 JSON sidecar + tracked_posts.json 형식 유지 | 파일 구조 비교 |
| 성능 | pub_date 비교 추가로 인한 수집 시간 변화 < 1초 | 배치 로그 |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] `naver_blog_collector.py`가 최근 7일 이내 발행 글만 수집
- [ ] `python naver_blog_collector.py --days 3` 실행 시 3일 이내 글만 수집
- [ ] pubDate 파싱 실패 글도 수집됨 (로그에 `[WARN] pubDate 파싱 실패` 표시)
- [ ] 재실행 시 dedup 100% (이전 수집분 전부 skip)
- [ ] tracked_posts.json + JSON sidecar + PDF 모두 정상 생성
- [ ] `naver_blog_scheduler.py`에서 `days=7` 전달 가능

### 4.2 Quality Criteria

- [ ] 기존 93+5=98건 tracked_posts 데이터 보존
- [ ] 기존 2026-02-01~2026-02-18 JPG/JSON 데이터에 영향 없음
- [ ] cp949 인코딩 에러 없음 (`sys.stdout.reconfigure` 적용)

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| RSS `pubDate` 포맷 불일치 | 수집 누락 | Medium | 파싱 실패 시 수집 허용 (FR-04) |
| N일 값이 너무 작으면 주간 블로거 글 누락 | 데이터 손실 | Medium | 기본값 7일 (87.6% 커버리지), 파라미터화 |
| tracked_posts.json 파일 손상/삭제 | 대량 재수집 | Low | JSON sidecar에서 재구축 스크립트 존재 |
| `naver_blog_scheduler.py`와 파라미터 불일치 | 의도와 다른 동작 | Low | 스케줄러 코드에 명시적 `days=7` 추가 |

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
| 필터 위치 | collect_blogger_posts 내부 / 별도 함수 | collect_blogger_posts 내부 | 변경 최소화, 기존 흐름 유지 |
| N일 기본값 | 3일 / 7일 / 14일 | 7일 | 실데이터 87.6% 커버리지, 주간 블로거 포함 |
| 파싱 실패 처리 | skip / 허용 | 허용 (수집) | 데이터 누락 방지 우선 |
| 시간대 비교 | UTC / KST / timezone-aware | timezone-aware | `parsedate_to_datetime`은 tz-aware 반환 |

### 6.3 변경 흐름 (before/after)

```
[Before]
RSS items[:max_posts]
  → MD5(link) dedup check → tracked_posts.json
  → 통과하면 무조건 수집

[After]
RSS items[:max_posts]
  → pubDate 파싱 → N일 이내? (파싱 실패 시 허용)
  → MD5(link) dedup check → tracked_posts.json
  → 통과하면 수집
```

### 6.4 pub_date 필터 로직 (핵심)

```python
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta

def is_within_days(pub_date_str: str, days: int) -> bool:
    """pub_date가 최근 N일 이내인지 확인. 파싱 실패 시 True 반환."""
    if not pub_date_str:
        return True  # 파싱 실패 → 수집 허용
    try:
        pub_dt = parsedate_to_datetime(pub_date_str)
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=days)
        return pub_dt >= cutoff
    except Exception:
        return True  # 파싱 실패 → 수집 허용
```

---

## 7. Implementation Order

### Phase 1: Core Filter (FR-01~04)
1. `naver_blog_collector.py`에 `is_within_days()` 함수 추가
2. `collect_blogger_posts()`에 `days` 파라미터 추가 + pubDate 필터
3. 파싱 실패 로깅 + 수집 허용 로직

### Phase 2: CLI + Scheduler (FR-05~06)
4. `main()`에 `argparse` + `--days` 인자
5. `naver_blog_scheduler.py`에 `days=7` 전달

### Phase 3: Docs + Integrity (FR-07~08)
6. `run_blog.py` docstring 역할 명확화
7. tracked_posts 무결성 검증 (선택적)

### Phase 4: E2E Verification
8. collector 실행: `--days 7` → 신규만 수집 확인
9. 재실행: dedup 100% 확인
10. `--days 3` vs `--days 7` 결과 비교

---

## 8. Convention Prerequisites

### 8.1 Existing Project Conventions

- [x] `CLAUDE.md` has coding conventions section
- [x] DEMO Data Convention (source="DEMO")
- [x] tracked_posts.json: MD5 해시 배열 형식
- [x] JSON sidecar: {blogger, title, link, pub_date, collected_date, image_file, file_size_mb}
- [x] 날짜 폴더: `data/naver_blog_data/YYYY-MM-DD/`

### 8.2 Convention Changes

- `collect_blogger_posts()` 시그니처: `max_posts` → `max_posts, days=7`
- `collect_all()` 시그니처: `max_posts_per_blogger` → `max_posts_per_blogger, days=7`
- `main()`: argparse 추가 (`--days`, `--max-posts`)
- 로그 형식: `[SKIP-DATE] {title} (pub: {pub_date})` (날짜 필터 skip 시)
