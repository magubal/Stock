# Industry Outlook + FnGuide Consensus Design

Date: 2026-02-15
Scope: `Test_02` only

## Goal
주식 종목 분석 실행 시:
1) 최근 업황(30일)이 있으면 재사용
2) 없으면 섹터 핵심요소를 생성해 저장
3) FnGuide 컨센서스를 조회/저장해 재사용

## User-Approved Decisions
- FnGuide 수집 방식: 자동 스크래핑
- 업황 캐시 TTL: 30일
- 저장 원칙: as_of_date 기준 append (히스토리 유지)

## Architecture
- `IndustryOutlookService`
  - 입력: `classification`(GICS, 한국 섹터)
  - 처리: Oracle에서 최신 업황 조회 -> TTL(30일) 유효 시 재사용
  - 미존재/만료 시: 섹터 기반 핵심요소 생성 후 Oracle 저장
- `FnGuideConsensusClient`
  - 입력: ticker (6자리)
  - 처리: FnGuide 페이지 스크래핑으로 연도별 매출/영업이익 전망 추출 시도
  - 결과: raw payload + 정규화 값
- `ForecastRepository`
  - Oracle 테이블 생성/조회/저장 담당
  - 테이블: `SR_INDUSTRY_OUTLOOK`, `SR_STOCK_CONSENSUS`, `SR_FORECAST_SCENARIO`

## Data Model
### SR_INDUSTRY_OUTLOOK
- `ID` NUMBER PK
- `SECTOR_KEY` VARCHAR2(120)
- `SECTOR_TOP` VARCHAR2(80)
- `SECTOR_SUB` VARCHAR2(120)
- `SUMMARY` CLOB
- `KEY_FACTORS_JSON` CLOB
- `SOURCE` VARCHAR2(30)
- `CONFIDENCE` VARCHAR2(20)
- `AS_OF_DATE` DATE
- `VALID_UNTIL` DATE
- `CREATED_AT` DATE DEFAULT SYSDATE

### SR_STOCK_CONSENSUS
- `ID` NUMBER PK
- `TICKER` VARCHAR2(20)
- `FISCAL_YEAR` VARCHAR2(8)
- `REVENUE_EST` NUMBER
- `OP_INCOME_EST` NUMBER
- `RAW_JSON` CLOB
- `SOURCE` VARCHAR2(30)
- `CONFIDENCE` VARCHAR2(20)
- `AS_OF_DATE` DATE
- `FRESHNESS_DAYS` NUMBER
- `CREATED_AT` DATE DEFAULT SYSDATE

### SR_FORECAST_SCENARIO
- `ID` NUMBER PK
- `TICKER` VARCHAR2(20)
- `FISCAL_YEAR` VARCHAR2(8)
- `SCENARIO` VARCHAR2(12)
- `REVENUE_EST` NUMBER
- `OP_INCOME_EST` NUMBER
- `PROBABILITY` NUMBER
- `SOURCE` VARCHAR2(30)
- `CONFIDENCE` VARCHAR2(20)
- `AS_OF_DATE` DATE
- `CREATED_AT` DATE DEFAULT SYSDATE

## Runtime Flow (analyze_with_evidence)
1. 섹터 분류 이후 업황 조회
2. 업황 TTL 유효: 재사용 / 무효: 생성+저장
3. FnGuide 컨센서스 조회
4. 성공 시 저장, 실패 시 최신 저장분 재사용
5. 컨센서스 기준 시나리오(bear/base/bull) 저장
6. 최종 결과에 `industry_outlook`, `consensus_2026`, `forecast_scenarios`, `source/freshness/confidence` 포함

## Error Handling
- Oracle 미연결: 기능 비활성, 분석 본체는 기존 경로로 진행
- FnGuide 스크래핑 실패: 저장된 최신 컨센서스 fallback
- 모두 실패: 결과에 warning 남기고 기존 해자 분석은 계속

## Test Strategy
- 컴파일: 신규/수정 모듈 `py_compile`
- 런타임: `analyze_with_evidence.py --ticker 005930 --name 삼성전자`
- 확인 포인트:
  - Oracle connected 시 테이블 자동 준비
  - 업황/컨센서스 결과가 result dict에 포함
  - 재실행 시 업황 reused 플래그 확인
