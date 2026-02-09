# 요청 관리 (REQUESTS)

> 마지막 업데이트: 2026-02-02 02:50 by Gemini

---

## 📋 요청 목록

### REQ-001: 네이버 블로그 데이터 자동 수집

| 항목 | 내용 |
|------|------|
| **요청 ID** | REQ-001 |
| **요청일** | 2026-02-02 |
| **상태** | ✅ 완료 (100%) |
| **우선순위** | 높음 |

#### 🎯 요구사항

1. **블로거 리스트 관리**
   - 수집 대상 블로거 RSS 목록 파일 유지
   - 파일 위치: `../test_data/naver_bloger_rss_list.txt`
   - ⚠️ Test_02 상위 폴더에 있음 (Stock 폴더 아래)
   
2. **최신 글 링크 수집**
   - RSS 피드에서 최근 1일간 최신 글 링크 추출
   - 중복 방지 (이미 수집된 글 제외)

3. **본문 이미지 저장**
   - 각 링크를 방문하여 본문만 이미지로 캡처
   - 저장 구조: `data/naver_blog_data/YYYY-MM-DD/블로거_순번.jpg`
   - **조건**: 하트/댓글/관련링크 제거

4. **자동화**
   - 매일 자동 실행
   - 시장 평가용 정보 수집 목적

---

## 📁 관련 파일

### 설정 파일
| 파일 | 위치 | 설명 |
|------|------|------|
| 블로거 리스트 | `f:\PSJ\AntigravityWorkPlace\Stock\Test_02\data\naver_blog_data\naver_bloger_rss_list.txt` | RSS 피드 목록 |

### 스크립트
| 파일 | 위치 | 용도 | 상태 |
|------|------|------|------|
| 메인 수집기 | `scripts/naver_blog_collector.py` | 전체 프로세스 제어 | ✅ 완성 |
| 본문 캡처 | `scripts/final_body_capture.py` | 본문만 추출 캡처 | ✅ 완성 (v2.0) |

### 데이터 폴더
| 폴더 | 위치 | 설명 |
|------|------|------|
| 수집 데이터 | `data/naver_blog_data/` | 일자별 이미지 저장 |
| 인덱스 | `data/naver_blog_data/index/` | 진행 상태, 추적 정보 |

---

## 📝 블로거 리스트 (현재)

```
https://rss.blog.naver.com/allsix6      # daybyday
https://rss.blog.naver.com/redserpent   # 라틴카페
https://rss.blog.naver.com/kmsmir04     # 유수암바람
```

**파일 수정 시**: `f:\PSJ\AntigravityWorkPlace\Stock\Test_02\data\naver_blog_data\naver_bloger_rss_list.txt`

---

## 🔄 진행 상태

### ✅ 완료
- [x] 블로그 전체 페이지 캡처
- [x] 일자별 폴더 자동 생성
- [x] 순번 자동 부여
- [x] 하트/댓글/관련링크 DOM 제거
- [x] 메인 수집기(`naver_blog_collector.py`)에 `final_body_capture.py` 통합
- [x] 자동화 스케줄러 등록 및 테스트 (09:00 매일)

---

## 💡 다음 모델을 위한 노트

1. **블로거 리스트 수정 시**: 상위 폴더 `test_data/naver_bloger_rss_list.txt`
2. **새 블로거 추가**: `RSS_URL # 블로거명` 형식
3. **수집기 통합 필요**: `final_body_capture.py` → `naver_blog_collector.py`
