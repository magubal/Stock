# blog-pipeline-dedup-fix Design Document

> **Summary**: `naver_blog_collector.py`에 pub_date 기반 최근 N일 필터 추가 + CLI 파라미터화 + 스케줄러 연동
>
> **Project**: Stock Research ONE
> **Author**: PSJ + Claude
> **Date**: 2026-02-20
> **Status**: Draft
> **Planning Doc**: [blog-pipeline-dedup-fix.plan.md](../../01-plan/features/blog-pipeline-dedup-fix.plan.md)

---

## 1. Overview

### 1.1 Design Goals

1. `collect_blogger_posts()`에 pub_date 파싱 + N일 필터 추가 (기본값 7일)
2. 파싱 실패 시 수집 허용 (누락 방지 안전장치)
3. CLI `--days` 파라미터 추가 (main 함수)
4. `naver_blog_scheduler.py`에서 `days` 파라미터 전달

### 1.2 Design Principles

- **최소 변경**: 기존 `naver_blog_collector.py`의 구조/인터페이스 최대 보존
- **안전 우선**: pub_date 파싱 실패 시 수집 허용 (데이터 누락 < 불필요 수집)
- **파라미터화**: N일 값을 하드코딩하지 않고 CLI/스케줄러에서 조정 가능

---

## 2. Architecture

### 2.1 변경 영향도 맵

```
┌──────────────────────────────────────────────────────┐
│ 변경 파일                         변경 수준           │
├──────────────────────────────────────────────────────┤
│ scripts/naver_blog_collector.py   ★★☆ 함수 수정     │
│   - is_within_days() 신규 함수                       │
│   - collect_blogger_posts() days 파라미터 + 필터     │
│   - collect_all() days 파라미터 전달                 │
│   - main() argparse + --days                         │
│ scripts/naver_blog_scheduler.py   ★☆☆ 파라미터 추가 │
│   - run_daily_collection() days=7 전달               │
├──────────────────────────────────────────────────────┤
│ scripts/blog_monitor/run_blog.py  변경 없음           │
│ scripts/final_body_capture.py     변경 없음           │
│ data/naver_blog_data/index/       변경 없음           │
└──────────────────────────────────────────────────────┘
```

### 2.2 변경 전/후 흐름

```
[Before]
RSS items[:max_posts]
  for item:
    → link 없으면 skip
    → MD5(link) in tracked_posts? → skip
    → _extract_blog_content(link)
    → collected_posts.append(post_data)

[After]
RSS items[:max_posts]
  for item:
    → link 없으면 skip
    → pub_date N일 이내? (파싱 실패 시 허용) → 아니면 skip + 로그
    → MD5(link) in tracked_posts? → skip
    → _extract_blog_content(link)
    → collected_posts.append(post_data)
```

---

## 3. Detailed Design

### 3.1 `is_within_days()` 신규 함수

```python
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta

def is_within_days(pub_date_str: str, days: int) -> tuple[bool, str]:
    """pub_date가 최근 N일 이내인지 확인.

    Returns:
        (result, reason)
        - (True, "within") : N일 이내
        - (True, "no_date") : pub_date 없음 → 수집 허용
        - (True, "parse_fail") : 파싱 실패 → 수집 허용
        - (False, "too_old") : N일 초과 → skip
    """
    if not pub_date_str or not pub_date_str.strip():
        return True, "no_date"
    try:
        pub_dt = parsedate_to_datetime(pub_date_str.strip())
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=days)
        if pub_dt >= cutoff:
            return True, "within"
        else:
            return False, "too_old"
    except Exception:
        return True, "parse_fail"
```

**설계 근거**:
- `email.utils.parsedate_to_datetime`: RFC 2822 형식 파싱 (네이버 RSS `pubDate` 표준)
- timezone-aware 비교: `parsedate_to_datetime`은 tz-aware datetime 반환
- tuple 반환: 로깅 시 skip 사유 구분 가능
- 파싱 실패/빈 값 → `True` 반환: 누락 방지 안전장치

### 3.2 `collect_blogger_posts()` 수정

```python
def collect_blogger_posts(self, blogger_info: Dict, max_posts: int = 10, days: int = 7) -> List[Dict]:
    """개별 블로거의 최신 게시물 수집

    Args:
        blogger_info: {'url': rss_url, 'name': blogger_name}
        max_posts: RSS에서 가져올 최대 아이템 수
        days: pub_date 기준 최근 N일 이내만 수집 (0=필터 없음)
    """
    # ... (기존 RSS 파싱 동일)

    for item in items:
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub_date = item.findtext("pubDate", "")

        if not link:
            continue

        # [NEW] pub_date 날짜 필터 (days=0이면 비활성)
        if days > 0:
            within, reason = is_within_days(pub_date, days)
            if not within:
                print(f"    [SKIP-DATE] {title[:40]} (pub: {pub_date.strip()}, reason: {reason})")
                continue
            if reason in ("no_date", "parse_fail"):
                print(f"    [WARN] pubDate {reason}: {title[:40]}")

        # 게시물 ID 생성 (URL 기준 - Stable Hash)
        post_id = hashlib.md5(link.encode('utf-8')).hexdigest()

        # 이미 저장된 게시물인지 확인
        if str(post_id) in self.tracked_posts:
            continue

        # ... (나머지 기존 로직 동일)
```

**변경 포인트**:
- `days` 파라미터 추가 (기본값 7)
- `days=0`이면 필터 비활성 (기존 동작 호환)
- 날짜 필터는 dedup 체크 **앞에** 위치 (불필요한 `_extract_blog_content` 호출 방지)
- skip/warn 로그 출력

### 3.3 `collect_all()` 수정

```python
def collect_all(self, max_posts_per_blogger: int = 10, days: int = 7):
    """모든 블로거의 데이터 수집 (브라우저 재사용)

    Args:
        max_posts_per_blogger: 블로거당 RSS 최대 아이템 수
        days: pub_date 기준 최근 N일 이내만 수집 (0=필터 없음)
    """
    # ... (기존 코드)

    for blogger_info in rss_list:
        print(f"\n[RSS] {blogger_info['name']} 목록 수집 중...")
        posts = self.collect_blogger_posts(blogger_info, max_posts_per_blogger, days=days)
        all_posts.extend(posts)

    # ... (나머지 동일)
```

### 3.4 `main()` 수정 — argparse 추가

```python
def main():
    """메인 실행 함수"""
    import argparse
    parser = argparse.ArgumentParser(description="네이버 블로그 수집기")
    parser.add_argument("--days", type=int, default=7,
                        help="최근 N일 이내 발행 글만 수집 (0=필터없음, 기본=7)")
    parser.add_argument("--max-posts", type=int, default=10,
                        help="블로거당 RSS 최대 아이템 수 (기본=10)")
    args = parser.parse_args()

    collector = NaverBlogCollector()
    collector.collect_all(max_posts_per_blogger=args.max_posts, days=args.days)
```

### 3.5 `naver_blog_scheduler.py` 수정

```python
def run_daily_collection():
    """매일 데이터 수집 실행"""
    logging.info("=== 네이버 블로그 데이터 수집 시작 ===")

    try:
        collector = NaverBlogCollector()
        collector.collect_all(max_posts_per_blogger=5, days=7)  # [CHANGED] days=7 추가
        logging.info("데이터 수집 완료")
    except Exception as e:
        logging.error(f"데이터 수집 중 오류 발생: {e}")
```

---

## 4. Implementation Order

### Step 1: `is_within_days()` 함수 추가
- `naver_blog_collector.py` 상단에 함수 추가
- `from email.utils import parsedate_to_datetime` import 추가

### Step 2: `collect_blogger_posts()` 수정
- `days` 파라미터 추가
- pub_date 필터 로직 삽입 (dedup 앞)
- skip/warn 로그 출력

### Step 3: `collect_all()` 수정
- `days` 파라미터 추가 + 전달

### Step 4: `main()` argparse 추가
- `--days`, `--max-posts` CLI 인자

### Step 5: `naver_blog_scheduler.py` 수정
- `collect_all(max_posts_per_blogger=5, days=7)`

### Step 6: E2E 테스트
- `python naver_blog_collector.py --days 7` → 최근 7일만 수집
- `python naver_blog_collector.py --days 0` → 필터 없음 (기존 동작)
- 재실행 → dedup 100%

---

## 5. Testing Strategy

### 5.1 단위 테스트 (수동)
```bash
# 최근 7일 필터 (기본)
python scripts/naver_blog_collector.py --days 7

# 최근 3일 필터
python scripts/naver_blog_collector.py --days 3

# 필터 없음 (기존 동작 호환)
python scripts/naver_blog_collector.py --days 0

# 재실행 → 0건 수집 (dedup)
python scripts/naver_blog_collector.py --days 7
```

### 5.2 검증 포인트
- [SKIP-DATE] 로그가 출력되는지
- [WARN] pubDate parse_fail 로그 (해당 시)
- tracked_posts.json 업데이트 정상
- JSON sidecar + PDF 생성 정상
- 날짜 폴더 구조 유지
