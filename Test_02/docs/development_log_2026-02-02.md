# 프로젝트 개발 로그

## 세션 정보
- **일시**: 2026-02-02
- **모델**: opencode/big-pickle (무료)
- **사용자**: 미정
- **세션 목표**: 블로그 캡처 프로그램 본문 추출 완성

---

## 현재 프로젝트 상태

### ✅ 완료된 작업 (100%)
1. **블로그 글 전체 이미지 캡처 기능**
   - Playwright 기반 스크린샷
   - 일자별 폴더 자동 생성
   - 순번 자동 부여 (daybyday_001.jpg)
   - 이미지 품질 최적화 (5.2MB)

### 🔄 진행 중인 작업 (85% 완성)
1. **본문만 추출 시스템**
   - 현재 상태: 전체 페이지 캡처
   - 문제: 하트/댓글/관련링크 포함됨
   - 목표: 순수 본문만 추출

---

## 결정 사항

### 기술적 선택
1. **Playwright 선택**: 안정성 우선 (Selenium 대비)
2. **품질 정책**: 정보 완성도 > 용량 (6.2MB 유지)
3. **파일 구조**: `data/naver_blog_data/YYYY-MM-DD/블로거_순번.jpg`

### 이전 시도 기록
1. **용량 최적화 실패**: 6.2MB → 2.6MB 시도 (정보 누락 발생)
2. **롤백 결정**: 정보 완성도 우선 원복

---

## 남은 과제

### 🎯 우선순위 높음
1. **하트/댓글 영역 DOM 제거**
   - CSS 선택자 기반 제거
   - 공감 버튼, 댓글 영역 타겟
2. **관련링크/사이드바 제거**
   - 관련글, 추천글 섹션 제거
   - 순수 본문만 남기기

### 📋 우선순위 중간
3. **메인 수집기 통합**
4. **자동화 스케줄러 테스트**

---

## 다음 모델을 위한 컨텍스트

### ⚠️ 중요 기억사항
1. **이미 성공한 기능**: 전체 캡처는 완벽히 동작
2. **핵심 목표**: 순수 본문만 추출 (85% → 95%)
3. **품질 기준**: 누락 없는 정보 > 작은 파일 크기
4. **파일 위치**: `scripts/final_body_capture.py`가 최종 버전

### 💡 다음 시도 방향
- DOM 조작으로 불필요 요소 제거
- JavaScript 기반 클리닝 적용
- 기존 성공 코드 수정보다는 개선 방식

---

## 사용자 요청사항

- 확인: 프로그램 실행 확인 완료
- 질문: LLM 비용 및 성능 차이 문의
- 관심: 업무 연속성 및 기록 시스템

---

## 🔄 모델 전환 (Gemini 이어받음)

### 세션 정보
- **일시**: 2026-02-02 02:30
- **모델**: Gemini (Antigravity)
- **이전 모델**: opencode/big-pickle

### ✅ 완료 작업

1. **작업 연속성 시스템 점검**
   - `AGENTS.md`, `DEVELOPMENT_LOG.md`, `development_log_2026-02-02.md` 확인
   - 문제점 발견: TODO 파일 누락, 스크립트 버전 혼재

2. **시스템 정리**
   - `TODO.md` 신규 생성 (구조화된 작업 목록)
   - 임시 파일 삭제 (temp_*.png, precise_temp_*.png 160개+)

3. **정책 추가**
   - `AGENTS.md`에 "지속적 개선 정책" 추가
   - TODO 없을 때 investment-philosophy 기반 보완점 제안 의무화

4. **본문 추출 스크립트 완성**
   - `scripts/final_body_capture.py` v2.0 작성
   - DOM 제거 로직 완성 (하트/댓글/관련링크)
   - 함수 인터페이스 개선 (결과 dict 반환)

### 📋 다음 모델을 위한 노트

**핵심 파일**:
- `scripts/final_body_capture.py` - 최종 버전 (v2.0)
- `TODO.md` - 구조화된 작업 목록
- `AGENTS.md` - 업무 연속성 정책

**다음 작업**:
- [x] 스크립트 실제 테스트 실행 (완료)
- [x] 메인 수집기에 통합 (완료)
- [x] 자동화 스케줄러 테스트 (완료)

### ✅ 검증 완료 (04:00)

1. **브라우저 최적화**
   - `BlogCaptureSession` 도입 (브라우저 재사용)
   - 속도 대폭 향상 및 자원 효율화

2. **중복 방지 강화**
   - Python `hash()` → **MD5** 변경
   - `tracked_posts.json` 저장 안정성 확보 (`try-finally`)
   - 테스트: 1차(6개 수집) → 2차(0개 수집) 성공

3. **자동화 구축 (04:05)**
   - **배치 파일**: `scripts/run_collector.bat` (로그 기록 포함)
   - **스케줄러**: `NaverBlogCollector` 등록 (매일 09:00)

### 📁 최종 산출물
- `scripts/naver_blog_collector.py` (Main Logic)
- `scripts/final_body_capture.py` (Capture Module v3.0)
- `scripts/run_collector.bat` (Automation Script)
- `data/naver_blog_data/index/tracked_posts.json` (Trace Data)

### ⚠️ 경로 수정 (04:30)
- **블로거 리스트**: `Test_02/data/naver_blog_data/naver_bloger_rss_list.txt`로 변경
- **관련 파일 수정**: `naver_blog_collector.py`, `REQUESTS.md` 업데이트 완료

---

## 📝 다음 모델을 위한 참고사항

- **자동화 상태**: 매일 09:00에 스케줄러가 돕니다. `collector_log.txt`를 확인하세요.
- **수집 로직**: `collect_all` → `BlogCaptureSession` → `captured` 순서로 동작합니다.
- **브라우저**: Playwright `browser.close()` 지연 이슈가 간혹 있으나, `try-finally`로 데이터는 안전하게 저장됩니다.