# Feature Plan: Oracle Earnings Integration & Growth-Adjusted Moat

## 1. Overview
- **Feature Name**: oracle-earnings-integration (Oracle 실적 연동 + 성장속도 해자 가감점)
- **Level**: Dynamic (Python Scripts + Oracle DB + Existing Moat Pipeline)
- **Priority**: High
- **Estimated Scope**: Oracle Client + Fallback 3계층 + 성장 Scorer + 파이프라인 통합
- **Brainstorm**: 2026-02-15 Brain 세션에서 A안(Oracle Direct) 선정

## 2. Background & Motivation

현재 해자 평가 파이프라인(`analyze_with_evidence.py`)은 **DART 연간 사업보고서** 기준으로
밸류에이션(PER 등)을 산출한다. 그러나:

1. **시점 괴리**: 최신 보고서가 2025.06 반기보고서인데, PER 계산은 2024년 연간 데이터 사용
2. **성장 무시**: 직전 3년간 매출/영업이익 변화율 추세가 해자 평가에 반영되지 않음
3. **데이터 중복**: 로컬 Oracle DB(`V_FN_JEJO_LOAD_잠정포함`)에 TTM 누적 실적이 이미 존재

해결 방향:
- Oracle DB의 **TTM(최근 4분기 누적)** 데이터를 해자 평가에 연동
- **시총/영업이익 배수**(op_multiple)로 정확한 밸류에이션 산출
- 3년 성장 추세 기반 **해자강도 ±1점 가감**
- Oracle 미접속 시 DART 분기→TTM 재구성→연간 fallback 3계층

## 3. Requirements

### 3.1 Functional Requirements

| ID | 요구사항 | 우선순위 | 보정근거 |
|----|----------|----------|----------|
| FR-01 | `OracleFinancialsClient` 클래스: oracledb thin mode 연결 | Must | — |
| FR-02 | `get_ttm(ticker)` → 최신 YYYYQQ의 SALE_AQ, BIZ_PRFT_AQ 반환 | Must | — |
| FR-03 | `get_trend(ticker, years=3)` → 3년 TTM 추이 리스트 | Must | — |
| FR-04 | **as_of_date 시점 정합성**: 가격일자, TTM 기준분기, 리포트 기준일 통합 저장 | Must | 보정1 |
| FR-05 | **op_multiple 산출**: 시가총액(Yahoo) ÷ TTM 영업이익(Oracle BIZ_PRFT_AQ) | Must | 보정2 |
| FR-06 | **Fallback 3계층**: Oracle TTM → DART 분기누적 TTM 재구성 → DART 연간 | Must | 보정3 |
| FR-07 | **GrowthScorer**: 업종별 CAGR 임계치 테이블 + 예외 규칙(적자전환/일회성) | Must | 보정4 |
| FR-08 | **DataQuality 플래그**: source, freshness_days, confidence, warnings 모든 결과에 첨부 | Must | 보정5 |
| FR-09 | 성장 가감점 ±1 해자강도 적용 (1~5 범위 클램프) | Must | — |
| FR-10 | 결과 출력에 성장 추세 섹션 추가 (TTM, CAGR, 마진 트렌드, op_multiple) | Must | — |
| FR-11 | Excel 출력 시 신규 컬럼 추가 (ttm_revenue, ttm_op_income, op_multiple, growth_score, data_source, data_confidence) | Should | — |
| FR-12 | `.env`에 Oracle 접속정보, `config.py` 로드 | Must | — |
| FR-13 | 단위 변환 통일: Oracle(백만원×1,000,000→원), 라운딩 규칙 고정 | Must | 보정5 |

### 3.2 Non-Functional Requirements
- Oracle 미접속 시에도 기존 파이프라인 100% 정상 동작 (graceful degradation)
- oracledb thin mode 사용 (Oracle Instant Client 설치 불필요)
- 한국어 뷰명(`V_FN_JEJO_LOAD_잠정포함`) 인코딩 안전 처리
- 모든 금액 단위: 파이프라인 내부는 **원(KRW)** 통일
- 라운딩 규칙: 배수(op_multiple)는 소수점 1자리, 비율(CAGR/마진)은 소수점 1%

## 4. Technical Approach

### 4.1 Oracle DB 소스 정보

```
Host:     localhost:1521
View:     "V_FN_JEJO_LOAD_잠정포함"
Driver:   oracledb (thin mode, Oracle Client 불필요)
```

**뷰 컬럼 정의**:
| 컬럼명 | 설명 | 예시 |
|--------|------|------|
| `YYYYQQ` | 년도+분기 | 202403 (2024년 3분기) |
| `CON_GB` | 개별/연결 구분 | "연결" |
| `STND_CD` | A+종목코드 | "A005930" |
| `COMPANY_NM` | 종목명 | "삼성전자" |
| `SALE_QQ` | 분기 매출액 (백만원) | 79,174,153 |
| `SALE_AQ` | 누적4분기 매출액 (백만원) | 300,870,903 |
| `BIZ_PRFT_QQ` | 분기 영업이익 (백만원) | 10,440,296 |
| `BIZ_PRFT_AQ` | 누적4분기 영업이익 (백만원) | 32,727,765 |

### 4.2 as_of_date 시점 정합성 (보정1)

```python
@dataclass
class AsOfDate:
    """모든 밸류에이션 산출물의 시점 기준"""
    price_date: str        # Yahoo 가격 조회 시점 (YYYY-MM-DD)
    ttm_quarter: str       # TTM 기준 분기 (YYYYQQ, e.g. "202403")
    report_base: str       # DART 최신 보고서 기준 (e.g. "2025H1")
    gap_days: int          # price_date와 ttm_quarter 종료일 간 차이 (일)
    gap_warning: bool      # gap_days > 90 이면 True
```

**규칙**:
- `gap_days > 90`: `[WARN] 시점 괴리 {gap_days}일` 콘솔 출력 + DataQuality.warnings에 추가
- TTM 기준분기 종료일 계산: `YYYYQQ=202403` → `2024-09-30`

### 4.3 PER 분모 정의 → op_multiple (보정2)

```
op_multiple = 시가총액 ÷ TTM 영업이익(BIZ_PRFT_AQ × 1,000,000)
```

- **네이밍**: `op_multiple` (기존 PER 대신 사용)
- 이유: Oracle 뷰에 순이익 컬럼 없음 → 영업이익 기반 배수가 더 신뢰성 높음
- 표시 형식: `12.3x` (소수점 1자리)
- 영업이익 ≤ 0 (적자) 시: `op_multiple = "N/A (적자)"`, 배수 산출하지 않음

### 4.4 Fallback 3계층 (보정3)

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: Oracle TTM (최우선)                         │
│  → V_FN_JEJO_LOAD_잠정포함.SALE_AQ, BIZ_PRFT_AQ    │
│  → source="oracle", confidence="high"               │
├─────────────────────────────────────────────────────┤
│ Layer 2: DART 분기누적 → TTM 재구성 (Oracle 실패 시) │
│  → DART DS003 최근 4분기 합산                        │
│  → source="dart_quarterly", confidence="medium"      │
├─────────────────────────────────────────────────────┤
│ Layer 3: DART 연간 보고서 (최종 fallback)             │
│  → 기존 get_financial_statements() 연간 데이터       │
│  → source="dart_annual", confidence="low"            │
└─────────────────────────────────────────────────────┘
```

**Layer 2 구현**: `DARTClient.get_quarterly_ttm(corp_code)` 신규 메서드
- DART API `DS003` 분기 데이터 4개 조회 → 합산
- 분기 데이터 불완전(3개 이하) 시 Layer 3으로 전환

### 4.5 성장 가감점 규칙 (보정4)

#### 4.5.1 업종별 CAGR 임계치 (설정 파일)

파일: `config/growth_thresholds.json`
```json
{
  "_comment": "업종별 매출 CAGR 임계치 (3년 기준)",
  "Information Technology": 0.15,
  "Health Care": 0.12,
  "Consumer Discretionary": 0.10,
  "Industrials": 0.08,
  "Financials": 0.08,
  "Materials": 0.07,
  "Consumer Staples": 0.05,
  "Communication Services": 0.10,
  "Energy": 0.05,
  "Utilities": 0.03,
  "Real Estate": 0.05,
  "default": 0.10
}
```

#### 4.5.2 가감점 매트릭스

| 조건 | 가감 | 비고 |
|------|------|------|
| 매출 CAGR ≥ 업종임계치 **AND** 영업이익률 개선(Δ > 0) | **+1** | 양적+질적 성장 |
| 매출 CAGR ≥ 업종임계치 **BUT** 영업이익률 하락(Δ < 0) | **0** | 성장은 하나 질 저하 |
| 매출 CAGR < 0 (역성장) **AND** 영업이익률 하락 | **-1** | 구조적 악화 |
| 매출 CAGR < 0 **BUT** 초대형주(매출10조+) & 경기민감 업종 | **0** | 사이클 예외 |
| 적자→흑자 전환 (직전TTM 적자, 최근TTM 흑자) | **+1** | 턴어라운드 보너스 |
| 일회성 이익으로 영업이익 급증 (직전 대비 300%+) | **0** | 일회성 제외, `one_time_flag=True` |
| 데이터 부족 (TTM 이력 2년 미만) | **0** | 판단 보류 |

#### 4.5.3 예외 처리
- **적자전환 판별**: `BIZ_PRFT_AQ` 부호 변화 (직전 < 0, 최근 > 0)
- **일회성 이익 감지**: 직전 4Q 대비 영업이익 300%+ 급증 시 `one_time_flag=True`, 가감 0
- **경기민감 업종**: `SECTOR_GROWTH_THRESHOLD`에서 Energy, Materials, Industrials는 역성장 시 -1 대신 0
- **최종 클램프**: 해자강도 = max(1, min(5, 기존강도 + growth_adjustment))

### 4.6 DataQuality 플래그 (보정5)

```python
@dataclass
class DataQuality:
    source: str              # "oracle" | "dart_quarterly" | "dart_annual"
    freshness_days: int      # as_of_date.price_date 기준 데이터 경과일
    confidence: str          # "high" | "medium" | "low"
    metric_name: str         # "op_multiple" (시총/영업이익배수)
    ttm_quarter: str         # "202403"
    price_date: str          # "2025-02-14"
    as_of_date: AsOfDate     # 통합 시점 객체
    warnings: List[str]      # ["시점괴리 92일", "one_time_flag", ...]
    unit: str                # "KRW" (항상 원 단위)
```

**저장 규칙**:
- 모든 결과 dict에 `data_quality: DataQuality` 포함
- Excel 출력 시 `data_source`, `data_confidence`, `data_freshness`, `data_warnings` 컬럼 추가
- 콘솔 출력 시 `[oracle/high]` 또는 `[dart_annual/low]` 형식으로 소스 표시

### 4.7 단위 변환 & 라운딩 (보정5)

| 소스 | 원본 단위 | 변환 | 파이프라인 내부 |
|------|-----------|------|----------------|
| Oracle | 백만원 | × 1,000,000 | 원 (KRW) |
| DART | 원 | 그대로 | 원 (KRW) |
| Yahoo | 원 (주가) | 그대로 | 원 (KRW) |

**라운딩 규칙 (고정)**:
| 지표 | 소수점 | 예시 |
|------|--------|------|
| op_multiple | 1자리 | `12.3x` |
| CAGR | 1% | `15.2%` |
| 영업이익률 | 1% | `10.9%` |
| 마진 변화(Δ) | 1%p | `+2.3%p` |
| 매출/이익 표시 | 조/억 자동 | `300.9조원`, `3,273억원` |
| growth_score | 정수 | `+1`, `0`, `-1` |

## 5. Implementation Plan

### Phase 1: Oracle Client & Config (Core)
1. `pip install oracledb` + `.env`에 `ORACLE_DSN`, `ORACLE_USER`, `ORACLE_PASSWORD` 추가
2. `config.py`에 Oracle 접속정보 로드 함수 추가
3. `OracleFinancialsClient` 클래스 생성 (`utils/oracle_client.py`)
   - `connect()`, `close()`, `get_ttm(ticker)`, `get_trend(ticker, years)`
   - 한국어 뷰명 안전 처리 (double-quote)
   - 단위 변환: 백만원 → 원 (조회 시점에 변환)
4. `AsOfDate`, `DataQuality` 데이터클래스 정의 (`utils/data_quality.py`)

### Phase 2: Fallback 3계층
5. `DARTClient`에 `get_quarterly_ttm(corp_code)` 메서드 추가 (Layer 2)
6. `FinancialsResolver` 클래스: Layer 1→2→3 순서로 시도, 사용된 Layer 기록
7. 각 Layer에서 `DataQuality` 자동 생성

### Phase 3: Growth Scorer
8. `config/growth_thresholds.json` 설정 파일 생성
9. `GrowthScorer` 클래스 생성 (`utils/growth_scorer.py`)
   - `calculate_cagr(trend_data)` → 3년 CAGR
   - `calculate_margin_delta(trend_data)` → 영업이익률 변화
   - `detect_turnaround(trend_data)` → 적자→흑자 판별
   - `detect_one_time(trend_data)` → 일회성 이익 감지
   - `score(ticker, sector, trend_data)` → +1/0/-1

### Phase 4: Pipeline Integration
10. `analyze_with_evidence.py` Step 2(재무제표) 확장:
    - `FinancialsResolver` 사용 (Oracle→DART분기→DART연간)
    - `AsOfDate` 생성 및 gap_warning 체크
11. 최종 해자강도에 `growth_adjustment` 적용
12. 결과 dict에 `data_quality`, `op_multiple`, `growth_score`, `as_of_date` 추가
13. 콘솔 출력에 성장 추세 섹션 추가
14. Excel 출력 컬럼 추가

## 6. File Map (신규/수정)

| 파일 | 유형 | 설명 |
|------|------|------|
| `.agent/skills/stock-moat/utils/oracle_client.py` | **신규** | OracleFinancialsClient |
| `.agent/skills/stock-moat/utils/data_quality.py` | **신규** | AsOfDate, DataQuality 데이터클래스 |
| `.agent/skills/stock-moat/utils/growth_scorer.py` | **신규** | GrowthScorer + 예외 규칙 |
| `.agent/skills/stock-moat/utils/financials_resolver.py` | **신규** | Fallback 3계층 오케스트레이터 |
| `config/growth_thresholds.json` | **신규** | 업종별 CAGR 임계치 설정 |
| `.env` | **수정** | ORACLE_DSN, ORACLE_USER, ORACLE_PASSWORD 추가 |
| `.agent/skills/stock-moat/utils/config.py` | **수정** | Oracle 접속정보 로드 |
| `.agent/skills/stock-moat/utils/dart_client.py` | **수정** | get_quarterly_ttm() 추가 |
| `scripts/stock_moat/analyze_with_evidence.py` | **수정** | FinancialsResolver 통합, 성장 가감 |
| `.agent/skills/stock-moat/utils/excel_io.py` | **수정** | 신규 컬럼 추가 |

## 7. Success Criteria

| 기준 | 조건 |
|------|------|
| Oracle 연결 | `--ticker 005930` 실행 시 Oracle TTM 데이터 자동 조회 |
| op_multiple | 시가총액 ÷ TTM 영업이익 배수 정확 산출 (소수점 1자리) |
| as_of_date | 가격일/TTM분기/리포트 기준일 모두 결과에 포함 |
| Fallback | Oracle 끈 상태에서도 DART 기반 분석 정상 완료 |
| 성장 가감 | 삼성전자(IT, CAGR 16%+) → +1점, 역성장 종목 → -1점 확인 |
| DataQuality | 모든 결과에 source/confidence/warnings 포함 |
| 단위 통일 | Oracle(백만원→원) 변환 후 DART 데이터와 동일 스케일 확인 |

## 8. Risks & Mitigation

| 리스크 | 완화책 |
|--------|--------|
| Oracle 미접속 | try/except + Fallback Layer 2→3, `[WARN]` 출력 |
| 한국어 뷰명 인코딩 | oracledb NLS_LANG=UTF-8, double-quote 뷰명 |
| TTM 데이터 지연 (분기 마감 전) | freshness_days 체크, 90일 이상 gap_warning |
| 일회성 이익 오탐 | 300% 임계치 + one_time_flag 수동 확인 유도 |
| oracledb 설치 실패 | thin mode는 순수 Python, pip install만으로 충분 |

## 9. Dependencies
- `oracledb` >= 2.0 (thin mode)
- 기존: `analyze_with_evidence.py`, `MoatEvaluatorV2`, `DARTClient`, `ExcelIO`
- Oracle DB 서비스 가동 (localhost:1521)
- Yahoo Finance v8 API (시가총액 조회)
