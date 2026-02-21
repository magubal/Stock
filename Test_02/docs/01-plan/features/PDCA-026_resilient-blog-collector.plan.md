# Resilient Blog Collector Plan

> (PDCA-026)
> **Summary**: run_blog.py의 개별 캡처 예외 처리 및 블로거별 최신 글 동적 필터링 고도화

## 배경
- `.pdca-status.json`에 새로 등록된 피처 (PDCA-026)
- `run_blog.py` 실행 시 개별 플래그/네트워크 장애로 시스템 전체가 다운되는 현상 방지 필요
- 일괄 최신 일수(`days`) 필터링을 각 블로거 DB 최종 수집일(`max(pub_date)`) 기반의 동적 필터링으로 개선하여 누락 방지 및 효율성 향상

## 범위
- `run_blog.py` Phase 1: DB의 `max(pub_date)`를 조회하여 블로거별 동적 날짜 필터링(`is_within_days` 보완) 적용
- `run_blog.py` Phase 2: Playwright 캡처 로직 구간을 `try-except`로 묶어 예외 발생 시 다음 글로 넘어가며, 개별 성공 건만 `session.commit()` 처리

## 산출물
| 파일 | 변경 내용 |
|------|-----------|
| `scripts/blog_monitor/run_blog.py` | 예외 복원력 부여 및 동적 날짜 조회 로직 추가 |

## 완료 상태
- [ ] 미완료
