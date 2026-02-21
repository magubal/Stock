> **PDCA Phase**: Plan
> **Feature**: blog-attachment-feature
> **Created**: 2026-02-22
> **Source**: User request
> **Author**: AI Assistant (bkit)

# 1. Goal
블로그 리뷰(`blog_review.html`) 화면에서 PC 내의 다양한 파일(PDF, 이미지, 엑셀 등)을 손쉽게 첨부하고 저장/열람할 수 있는 기능을 구현한다.

# 2. Context & Constraints
- 기존에 크롤링 되는 PDF 본문 파일들과 동일한 `naver_blog_data/{date}/` 디렉토리 하위에 첨부 파일들을 저장하여 관리 일관성을 유지한다.
- 과도한 DB Scheme 변동과 관리의 복잡도를 줄이기 위해, DB에 별도의 첨부 파일 테이블이나 컬럼을 추가하지 않고 디렉토리를 **동적 스캔(os.listdir)**하는 C안을 채택하였다.
- 글 하나(`blog_id`)당 하나의 독립된 첨부 폴더(`{blog_id}_첨부`)를 갖도록 하여 첨부 파일의 꼬임을 원천 차단한다.

# 3. Acceptance Criteria (DoD)
- [ ] 블로그 리뷰 화면 UI에 파일 첨부 컴포넌트 추가
- [ ] 파일 업로드 시 `data/naver_blog_data/{pub_date}/{blog_id}_첨부/` 경로에 정상 저장됨
- [ ] 블로그를 조회할 때 해당 폴더를 스캔하여 첨부 파일 목록이 즉시 화면에 노출됨
- [ ] 노출된 링크를 클릭하여 파일 다운로드 또는 열람이 가능함

# 4. Next Step
- `/pdca design blog-attachment-feature`를 통해 API 엔드포인트와 프론트엔드 연동 명세를 작성한다.
