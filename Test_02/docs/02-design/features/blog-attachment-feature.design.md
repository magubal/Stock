> **PDCA Phase**: Design
> **Feature**: blog-attachment-feature
> **Created**: 2026-02-22
> **Source**: User request
> **Author**: AI Assistant (bkit)

# 1. Architecture Overview
첨부 파일(PDF, 이미지 등)을 DB 스키마 수정 없이 관리하기 위해 동적으로 OS 파일 시스템(디렉토리 스캔)을 기반으로 동작하는 Attachment API를 설계한다. 기존 크롤링된 PDF가 저장되는 `data/naver_blog_data` 디렉토리 아래에 블로그별 독립된 첨부 폴더를 만들고 관리한다.

# 2. Key Components

## 2.1 Backend API (FastAPI)
### Endpoints
1. `GET /api/v1/blogs/{blog_id}/attachments`
   - 블로그의 `pub_date`를 조회하여 `naver_blog_data/{pub_date}/{blog_id}_첨부/` 경로를 특정.
   - 폴더가 존재하면 `os.listdir()`를 통해 내부 파일들의 목록 반환.
   - 응답 포맷: `{"items": [{"filename": "...", "url": "..."}], "folder": "..."}`
2. `POST /api/v1/blogs/{blog_id}/attachments`
   - 복수의 `UploadFile`을 폼 데이터로 수신.
   - `naver_blog_data/{pub_date}/{blog_id}_첨부/` 디렉토리가 없으면 `os.makedirs`로 생성.
   - `shutil.copyfileobj`를 이용하여 파일 물리적 저장.
3. `GET /api/v1/blogs/{blog_id}/attachments/{filename}`
   - 실제 물리적 파일을 `FileResponse` 로 반환하여 다운로드/열람 지원.
4. `DELETE /api/v1/blogs/{blog_id}/attachments/{filename}`
   - `os.remove` 처리하여 파일 삭제. 성공 여부 반환.

## 2.2 Frontend (blog_review.html)
- 상세 보기 창 안에서 탭(Tab) 또는 하단 패널(Panel) 형태로 "첨부 파일" 영역 확보.
- Drag & Drop 및 File Input 태그 삽입.
- 파일을 선택하면 즉시 AJAX 통신으로 POST 업로드 수행.
- 업로드 성공 시 GET 엔드포인트를 다시 호출(또는 리턴 데이터 파싱)하여 첨부 목록 UI 리액티브 업데이트.
- 삭제 버튼(휴지통 아이콘)을 두어 DELETE API를 호출하고 알림창(토스트) 표시.

# 3. Data Flow
1. 사용자가 브라우저에서 파일 업로드 `->` FastAPI `POST`
2. FastAPI `->` SQLite(`naver_blog`) 테이블에서 Pub Date 조회 `->` (ex: `2026-02-21`)
3. FastAPI `->` OS 파일 시스템 `f:/PSJ/AntigravityWorkPlace/Stock/Test_02/data/naver_blog_data/2026-02-21/105_첨부/` 에 파일 생성
4. 프론트엔드가 파일 리스트 요청 GET `->` FastAPI가 위 경로 `os.listdir` 후 JSON 반환.

# 4. Next Step
- `/pdca do blog-attachment-feature`를 수행하여 API 라우터와 프론트엔드 모듈 연동을 구현한다.
