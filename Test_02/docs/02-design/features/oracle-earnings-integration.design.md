# Feature Design: Oracle Earnings Integration & Growth-Adjusted Moat

> Plan 참조: `docs/01-plan/features/oracle-earnings-integration.plan.md`

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│              analyze_with_evidence.py (Pipeline)                 │
│                                                                  │
│  Step 1: DART Info   ──→  Step 2: Financials (CHANGED)          │
│                            │                                     │
│                     ┌──────┴──────┐                              │
│                     │ Financials  │                               │
│                     │  Resolver   │                               │
│                     └──────┬──────┘                              │
│                     ┌──────┼──────┐                              │
│                     ▼      ▼      ▼                              │
│               [Layer1] [Layer2] [Layer3]                          │
│               Oracle   DART분기  DART연간                         │
│                     │                                             │
│                     ▼                                             │
│              ┌─────────────┐  ┌────────────┐                     │
│              │ AsOfDate    │  │ DataQuality│                     │
│              │ price_date  │  │ source     │                     │
│              │ ttm_quarter │  │ confidence │                     │
│              │ report_base │  │ freshness  │                     │
│              └─────────────┘  └────────────┘                     │
│                     │                                             │
│  Step 3-5: Report/BM/Evidence                                    │
│  Step 6: Moat Evaluation                                         │
│  Step 6.5: Growth Scorer (NEW)  ──→  ±1 가감                    │
│  Step 7: Sustainability                                          │
│  Step 8: AI Verification                                         │
│  Step 9: op_multiple 산출 (NEW)                                  │
└──────────────────────────────────────────────────────────────────┘
```

## 2. Data Models

### 2.1 AsOfDate (시점 정합성)

```python
# utils/data_quality.py

from dataclasses import dataclass, field
from typing import List
from datetime import date, datetime

@dataclass
class AsOfDate:
    """모든 밸류에이션 산출물의 시점 기준"""
    price_date: str                  # "2025-02-14" (Yahoo 가격 조회 시점)
    ttm_quarter: str                 # "202403" (Oracle/DART TTM 기준 분기)
    report_base: str                 # "2025H1" (DART 최신 보고서)
    gap_days: int = 0                # price_date vs ttm_quarter 종료일 차이
    gap_warning: bool = False        # gap_days > 90

    def __post_init__(self):
        """ttm_quarter 종료일 계산 → gap_days 자동 산출"""
        if self.ttm_quarter and self.price_date:
            try:
                yyyy = int(self.ttm_quarter[:4])
                qq = int(self.ttm_quarter[4:])
                # 분기 종료일: Q1=03-31, Q2=06-30, Q3=09-30, Q4=12-31
                quarter_end_month = qq * 3
                if quarter_end_month in (1,3,5,7,8,10,12):
                    quarter_end_day = 31
                elif quarter_end_month in (4,6,9,11):
                    quarter_end_day = 30
                else:
                    quarter_end_day = 28
                ttm_end = date(yyyy, quarter_end_month, quarter_end_day)
                price_d = date.fromisoformat(self.price_date)
                self.gap_days = (price_d - ttm_end).days
                self.gap_warning = self.gap_days > 90
            except (ValueError, TypeError):
                pass
```

### 2.2 DataQuality (출처/품질 플래그)

```python
# utils/data_quality.py (이어서)

@dataclass
class DataQuality:
    """결과 데이터의 출처/품질 메타데이터"""
    source: str                      # "oracle" | "dart_quarterly" | "dart_annual"
    freshness_days: int              # 데이터 경과일
    confidence: str                  # "high" | "medium" | "low"
    metric_name: str = "op_multiple" # 시총/영업이익배수
    ttm_quarter: str = ""            # "202403"
    price_date: str = ""             # "2025-02-14"
    as_of_date: AsOfDate = None      # 통합 시점 객체
    warnings: List[str] = field(default_factory=list)
    unit: str = "KRW"               # 항상 원 단위

    def to_dict(self) -> dict:
        """Excel/JSON 출력용 dict 변환"""
        return {
            'data_source': self.source,
            'data_confidence': self.confidence,
            'data_freshness_days': self.freshness_days,
            'data_warnings': ' | '.join(self.warnings) if self.warnings else '',
            'ttm_quarter': self.ttm_quarter,
            'price_date': self.price_date,
        }
```

### 2.3 TTM Financials (Oracle/DART 공통 반환 포맷)

```python
@dataclass
class TTMFinancials:
    """Oracle/DART에서 조회한 TTM 실적 (공통 포맷)"""
    ttm_revenue: int             # 누적4분기 매출 (원)
    ttm_op_income: int           # 누적4분기 영업이익 (원)
    ttm_quarter: str             # 기준 분기 "202403"
    company_name: str = ""       # 종목명
    data_quality: DataQuality = None

    @property
    def ttm_op_margin(self) -> float:
        """TTM 영업이익률"""
        if self.ttm_revenue and self.ttm_revenue > 0:
            return self.ttm_op_income / self.ttm_revenue
        return 0.0
```

### 2.4 GrowthTrend (3년 추세)

```python
@dataclass
class GrowthTrend:
    """3년 TTM 추이 데이터"""
    periods: List[dict]          # [{quarter, revenue, op_income, op_margin}, ...]
    revenue_cagr: float          # 3년 매출 CAGR
    op_margin_delta: float       # 영업이익률 변화 (%p)
    is_turnaround: bool          # 적자→흑자 전환
    one_time_flag: bool          # 일회성 이익 의심
    growth_score: int            # +1 / 0 / -1
    score_reason: str            # 가감 사유
```

## 3. Module Design

### 3.1 OracleFinancialsClient (`utils/oracle_client.py`)

```python
class OracleFinancialsClient:
    """Oracle DB에서 TTM 실적 조회 (oracledb thin mode)"""

    def __init__(self, dsn: str = None, user: str = None, password: str = None):
        """
        Args:
            dsn: Oracle 접속 DSN (기본: .env의 ORACLE_DSN)
            user: 사용자 (기본: .env의 ORACLE_USER)
            password: 비밀번호 (기본: .env의 ORACLE_PASSWORD)
        """

    def connect(self) -> bool:
        """Oracle 접속 시도. 성공=True, 실패=False (예외 안 던짐)"""

    def close(self):
        """접속 종료"""

    def get_ttm(self, ticker: str) -> Optional[TTMFinancials]:
        """
        최신 TTM 실적 조회.

        SQL:
            SELECT YYYYQQ, SALE_AQ, BIZ_PRFT_AQ, COMPANY_NM
            FROM "V_FN_JEJO_LOAD_잠정포함"
            WHERE STND_CD = :stnd_cd
              AND CON_GB = '연결'
            ORDER BY YYYYQQ DESC
            FETCH FIRST 1 ROW ONLY

        변환: 백만원 × 1,000,000 → 원
        """

    def get_trend(self, ticker: str, years: int = 3) -> Optional[GrowthTrend]:
        """
        3년 TTM 추이 조회 (연간 최종 분기 기준).

        SQL:
            SELECT YYYYQQ, SALE_AQ, BIZ_PRFT_AQ
            FROM "V_FN_JEJO_LOAD_잠정포함"
            WHERE STND_CD = :stnd_cd
              AND CON_GB = '연결'
              AND YYYYQQ IN (
                  SELECT MAX(YYYYQQ) FROM "V_FN_JEJO_LOAD_잠정포함"
                  WHERE STND_CD = :stnd_cd AND CON_GB = '연결'
                  GROUP BY SUBSTR(YYYYQQ, 1, 4)
              )
            ORDER BY YYYYQQ DESC
            FETCH FIRST :limit ROWS ONLY

        limit = years + 1 (CAGR 계산에 기준년도 필요)
        변환: 백만원 × 1,000,000 → 원
        GrowthTrend에 CAGR, margin_delta만 계산 (score는 GrowthScorer가)
        """
```

**뷰명 인코딩 안전 처리**:
```python
VIEW_NAME = '"V_FN_JEJO_LOAD_잠정포함"'  # double-quote로 감싸기
# oracledb connection: encoding='UTF-8' 명시
```

### 3.2 FinancialsResolver (`utils/financials_resolver.py`)

```python
class FinancialsResolver:
    """Fallback 3계층 오케스트레이터"""

    def __init__(self, oracle_client=None, dart_client=None):
        self.oracle = oracle_client   # None이면 Layer1 스킵
        self.dart = dart_client

    def resolve_ttm(self, ticker: str, corp_code: str) -> TTMFinancials:
        """
        3계층 순서로 TTM 실적 조회:
        Layer 1: Oracle → source="oracle", confidence="high"
        Layer 2: DART 분기 재구성 → source="dart_quarterly", confidence="medium"
        Layer 3: DART 연간 → source="dart_annual", confidence="low"
        """

    def resolve_trend(self, ticker: str, corp_code: str, years: int = 3) -> Optional[GrowthTrend]:
        """
        3계층 순서로 성장 추세 조회:
        Layer 1: Oracle get_trend()
        Layer 2: DART 다년도 데이터로 추세 재구성
        Layer 3: None (추세 불가, growth_score=0)
        """

    def _layer1_oracle(self, ticker: str) -> Optional[TTMFinancials]:
        """Oracle 조회 시도"""

    def _layer2_dart_quarterly(self, corp_code: str) -> Optional[TTMFinancials]:
        """DART 분기 4개 합산 → TTM 재구성"""

    def _layer3_dart_annual(self, corp_code: str) -> Optional[TTMFinancials]:
        """DART 연간 데이터 fallback"""
```

**Layer 2 구현 상세** — `DARTClient` 확장:
```python
# dart_client.py에 추가
def get_quarterly_financials(self, corp_code: str, year: str) -> List[Dict]:
    """
    분기별 재무제표 조회 (reprt_code: 11013=1Q, 11012=반기, 11014=3Q, 11011=연간)
    최근 4분기 데이터 수집 → List[{quarter, revenue, op_income}]
    """
```

### 3.3 GrowthScorer (`utils/growth_scorer.py`)

```python
class GrowthScorer:
    """업종별 성장 임계치 기반 해자 가감점 산출"""

    def __init__(self, thresholds_path: str = None):
        """config/growth_thresholds.json 로드"""

    def score(
        self,
        trend: GrowthTrend,
        gics_sector: str,
        ttm_revenue: int = 0
    ) -> Tuple[int, str]:
        """
        성장 가감점 산출.

        Returns:
            (adjustment, reason)
            adjustment: +1, 0, -1
            reason: 가감 사유 문자열

        Rules (우선순위 순):
        1. 데이터 부족 (periods < 2) → (0, "데이터 부족")
        2. 적자→흑자 전환 (is_turnaround) → (+1, "턴어라운드")
        3. 일회성 이익 (one_time_flag) → (0, "일회성 이익 제외")
        4. 양적+질적 성장 (CAGR≥임계치 AND margin_delta>0) → (+1, "성장 우수")
        5. 양적 성장만 (CAGR≥임계치 BUT margin_delta<0) → (0, "성장↑ 질↓")
        6. 역성장+질 하락 (CAGR<0 AND margin_delta<0):
           - 초대형주(10조+) & 경기민감 → (0, "사이클 예외")
           - 그 외 → (-1, "구조적 악화")
        7. 기타 → (0, "중립")
        """

    def _get_threshold(self, gics_sector: str) -> float:
        """업종별 CAGR 임계치 반환 (미등록 시 default 0.10)"""

    def _is_cyclical_sector(self, gics_sector: str) -> bool:
        """경기민감 업종 판별 (Energy, Materials, Industrials)"""

    def _detect_turnaround(self, trend: GrowthTrend) -> bool:
        """적자→흑자 전환 판별: 직전 TTM 영업이익 < 0, 최근 TTM > 0"""

    def _detect_one_time(self, trend: GrowthTrend) -> bool:
        """일회성 이익 감지: 직전 대비 영업이익 300%+ 급증"""
```

### 3.4 config.py 확장

```python
# 추가 함수
def get_oracle_config() -> dict:
    """Oracle 접속정보 반환. 키 없으면 None 값 포함 dict 반환 (에러 안 던짐)"""
    load_env()
    return {
        'dsn': os.getenv('ORACLE_DSN'),          # "localhost:1521/XE"
        'user': os.getenv('ORACLE_USER'),
        'password': os.getenv('ORACLE_PASSWORD'),
    }

def get_growth_thresholds_path() -> str:
    """config/growth_thresholds.json 경로 반환"""
```

## 4. Pipeline Integration (analyze_with_evidence.py 수정)

### 4.1 Step 2 변경: FinancialsResolver 적용

```python
# 기존 (before)
financials = self.dart.get_financial_statements(corp_code, year) or {}
multi_year = self.dart.get_multi_year_financials(corp_code)

# 변경 (after)
print(f"\n[2/9] 재무제표 조회 (Oracle → DART fallback)...")
ttm_result = self.financials_resolver.resolve_ttm(ticker, corp_code)
trend_result = self.financials_resolver.resolve_trend(ticker, corp_code, years=3)

# 기존 financials dict도 유지 (하위 호환)
financials = self.dart.get_financial_statements(corp_code, year) or {}
multi_year = self.dart.get_multi_year_financials(corp_code)

# TTM 결과를 financials에 병합
if ttm_result:
    financials['ttm_revenue'] = ttm_result.ttm_revenue
    financials['ttm_op_income'] = ttm_result.ttm_op_income
    financials['ttm_quarter'] = ttm_result.ttm_quarter
    print(f"    [{ttm_result.data_quality.source}/{ttm_result.data_quality.confidence}]")
    print(f"    TTM Revenue: {ttm_result.ttm_revenue:,}")
    print(f"    TTM Op Income: {ttm_result.ttm_op_income:,}")
```

### 4.2 Step 6.5 신규: Growth Scorer

```python
# Step 6 (Moat Evaluation) 이후, Step 7 (Sustainability) 이전에 삽입

print(f"\n[6.5/9] 성장 추세 평가...")
growth_adjustment = 0
growth_reason = "데이터 없음"

if trend_result:
    growth_adjustment, growth_reason = self.growth_scorer.score(
        trend=trend_result,
        gics_sector=classification.get('gics_sector', ''),
        ttm_revenue=ttm_result.ttm_revenue if ttm_result else 0
    )
    print(f"    CAGR: {trend_result.revenue_cagr:.1%}")
    print(f"    Margin Δ: {trend_result.op_margin_delta:+.1f}%p")
    print(f"    Growth Score: {growth_adjustment:+d} ({growth_reason})")
```

### 4.3 Step 9 신규: op_multiple 산출

```python
# 최종 결과 빌드 시점 (Step 8 이후)

print(f"\n[9/9] 밸류에이션 (op_multiple)...")
op_multiple = None
market_cap = None

if ttm_result and ttm_result.ttm_op_income > 0:
    # Yahoo Finance v8으로 시가총액 조회
    price_data = self._get_price_data(ticker)  # 기존 Yahoo 조회 분리
    if price_data:
        market_cap = price_data['market_cap']
        op_multiple = market_cap / ttm_result.ttm_op_income
        print(f"    Market Cap: {market_cap/1e12:.1f}조원")
        print(f"    op_multiple: {op_multiple:.1f}x")

        # as_of_date 생성
        as_of_date = AsOfDate(
            price_date=price_data['date'],
            ttm_quarter=ttm_result.ttm_quarter,
            report_base=report_base_str,
        )
        if as_of_date.gap_warning:
            print(f"    [WARN] 시점 괴리 {as_of_date.gap_days}일")
elif ttm_result and ttm_result.ttm_op_income <= 0:
    print(f"    op_multiple: N/A (적자)")
    op_multiple = "N/A"
```

### 4.4 해자강도 가감 적용

```python
# 기존: final_strength = sustainability['adjusted_strength']
# 변경: 성장 가감 추가 적용

final_strength = sustainability['adjusted_strength']

# Growth adjustment (±1)
if growth_adjustment != 0:
    prev = final_strength
    final_strength = max(1, min(5, final_strength + growth_adjustment))
    print(f"    성장 가감: {prev} → {final_strength} ({growth_adjustment:+d}, {growth_reason})")
```

### 4.5 결과 dict 확장

```python
result.update({
    # 기존 필드 유지...

    # TTM 실적 (NEW)
    'ttm_revenue': ttm_result.ttm_revenue if ttm_result else None,
    'ttm_op_income': ttm_result.ttm_op_income if ttm_result else None,
    'ttm_op_margin': ttm_result.ttm_op_margin if ttm_result else None,

    # 밸류에이션 (NEW)
    'op_multiple': op_multiple,
    'market_cap': market_cap,

    # 성장 추세 (NEW)
    'growth_score': growth_adjustment,
    'growth_reason': growth_reason,
    'revenue_cagr': trend_result.revenue_cagr if trend_result else None,
    'op_margin_delta': trend_result.op_margin_delta if trend_result else None,

    # 데이터 품질 (NEW)
    'data_quality': ttm_result.data_quality.to_dict() if ttm_result and ttm_result.data_quality else {},
    'as_of_date': {
        'price_date': as_of_date.price_date,
        'ttm_quarter': as_of_date.ttm_quarter,
        'report_base': as_of_date.report_base,
        'gap_days': as_of_date.gap_days,
        'gap_warning': as_of_date.gap_warning,
    } if as_of_date else {},
})
```

## 5. Configuration Files

### 5.1 `.env` 추가 항목

```env
# Oracle DB (실적 테이블)
ORACLE_DSN=localhost:1521/XE
ORACLE_USER=your_user
ORACLE_PASSWORD=your_password
```

### 5.2 `config/growth_thresholds.json`

```json
{
  "_comment": "업종별 매출 CAGR 임계치 (3년 기준). GICS Sector 기준.",
  "_updated": "2026-02-15",
  "thresholds": {
    "Information Technology": 0.15,
    "Health Care": 0.12,
    "Consumer Discretionary": 0.10,
    "Communication Services": 0.10,
    "Industrials": 0.08,
    "Financials": 0.08,
    "Materials": 0.07,
    "Consumer Staples": 0.05,
    "Energy": 0.05,
    "Real Estate": 0.05,
    "Utilities": 0.03,
    "default": 0.10
  },
  "cyclical_sectors": [
    "Energy",
    "Materials",
    "Industrials"
  ],
  "mega_cap_threshold": 10000000000000,
  "one_time_spike_ratio": 3.0
}
```

## 6. Unit Conversion & Rounding Rules

| 소스 → 내부 | 변환 공식 | 적용 위치 |
|-------------|-----------|-----------|
| Oracle 백만원 → 원 | `value * 1_000_000` | `OracleFinancialsClient.get_ttm()` |
| DART 원 → 원 | 변환 없음 | — |
| Yahoo 원(주가) → 원 | 변환 없음 | — |

| 지표 | 라운딩 | 형식 | 코드 |
|------|--------|------|------|
| op_multiple | 소수점 1자리 | `12.3x` | `f"{val:.1f}x"` |
| CAGR | 소수점 1% | `15.2%` | `f"{val:.1%}"` |
| 영업이익률 | 소수점 1% | `10.9%` | `f"{val:.1%}"` |
| 마진 변화 | 소수점 1%p | `+2.3%p` | `f"{val:+.1f}%p"` |
| 매출/이익 (표시) | 조/억 자동 | `300.9조원` | `format_krw(val)` |
| growth_score | 정수 | `+1` | `f"{val:+d}"` |

```python
# utils/data_quality.py
def format_krw(value: int) -> str:
    """원 단위를 조/억 자동 표시"""
    if abs(value) >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:.1f}조원"
    elif abs(value) >= 100_000_000:
        return f"{value / 100_000_000:,.0f}억원"
    else:
        return f"{value:,}원"
```

## 7. Console Output Format (변경)

```
======================================================================
  Evidence-Based Moat Analysis v3: 삼성전자 (005930)
======================================================================

[1/9] DART 기업정보 조회...
    Sector: 반도체 / 반도체

[2/9] 재무제표 조회 (Oracle → DART fallback)...
    [oracle/high] TTM 기준: 202403
    TTM Revenue: 300.9조원
    TTM Op Income: 3.3조원
    TTM Op Margin: 10.9%

[3/9] 사업보고서 다운로드...
[4/9] BM 6요소 분해...
[5/9] 증거 추출...

[6/9] 해자 평가 v2...
    Moat Strength: 4/5

[6.5/9] 성장 추세 평가...
    CAGR (3Y): 16.2%  (임계치: 15.0%)
    Margin Δ: +2.3%p
    Growth Score: +1 (성장 우수)
    해자 가감: 4 → 5 (성장 반영)

[7/9] 지속가능성 검증...
[8/9] AI 독립평가...

[9/9] 밸류에이션 (op_multiple)...
    Market Cap: 1,081.7조원
    op_multiple: 33.1x [oracle/high]
    as_of_date: price=2025-02-14, ttm=202403, report=2025H1

======================================================================
  RESULT: 삼성전자 (005930)
======================================================================
  해자강도:  5/5 (Rule: 4 + Growth: +1)
  op_multiple: 33.1x
  Data Source: oracle (confidence: high)
======================================================================
```

## 8. File Map (Implementation Order)

| 순서 | 파일 | 작업 | 의존성 |
|------|------|------|--------|
| 1 | `.env` | ORACLE_DSN/USER/PASSWORD 추가 | — |
| 2 | `config/growth_thresholds.json` | 업종별 임계치 설정 파일 | — |
| 3 | `utils/data_quality.py` | AsOfDate, DataQuality, TTMFinancials, GrowthTrend, format_krw | — |
| 4 | `utils/config.py` | `get_oracle_config()`, `get_growth_thresholds_path()` 추가 | 1 |
| 5 | `utils/oracle_client.py` | OracleFinancialsClient | 3, 4 |
| 6 | `utils/dart_client.py` | `get_quarterly_financials()` 추가 (Layer 2용) | — |
| 7 | `utils/financials_resolver.py` | FinancialsResolver (3계층) | 3, 5, 6 |
| 8 | `utils/growth_scorer.py` | GrowthScorer | 2, 3 |
| 9 | `analyze_with_evidence.py` | Step 2 변경, Step 6.5/9 추가, 결과 확장 | 7, 8 |
| 10 | `utils/excel_io.py` | 신규 컬럼 추가 | 3 |

## 9. Error Handling & Fallback Matrix

| 상황 | 동작 | 콘솔 출력 |
|------|------|-----------|
| Oracle 접속 성공 | Layer 1 사용 | `[oracle/high]` |
| Oracle 접속 실패 | Layer 2 시도 | `[WARN] Oracle 미접속, DART 분기 시도` |
| Oracle + DART 분기 실패 | Layer 3 사용 | `[WARN] DART 연간 fallback` |
| 모든 Layer 실패 | 기존 financials 사용 | `[WARN] TTM 불가, 기존 데이터 사용` |
| gap_days > 90 | 경고 + 계속 진행 | `[WARN] 시점 괴리 {N}일` |
| 영업이익 ≤ 0 | op_multiple = "N/A" | `op_multiple: N/A (적자)` |
| oracledb 미설치 | Oracle 스킵 | `[INFO] oracledb 미설치, Layer 2부터 시도` |
| 성장 데이터 부족 (<2년) | growth_score = 0 | `Growth Score: 0 (데이터 부족)` |

## 10. Testing Checklist

| # | 테스트 케이스 | 기대 결과 |
|---|-------------|-----------|
| T-01 | Oracle 접속 + 삼성전자 005930 | TTM 데이터 조회, op_multiple 산출 |
| T-02 | Oracle 끈 상태 + 삼성전자 | Layer 2/3 fallback, `[WARN]` 표시 |
| T-03 | 적자 기업 (영업이익 < 0) | op_multiple = "N/A", growth_score 정상 |
| T-04 | 고성장 IT (CAGR 20%) | growth_score = +1 |
| T-05 | 역성장 + 마진하락 | growth_score = -1 |
| T-06 | 초대형 경기민감 역성장 | growth_score = 0 (사이클 예외) |
| T-07 | 적자→흑자 전환 | growth_score = +1 (턴어라운드) |
| T-08 | 일회성 이익 300%+ | growth_score = 0, one_time_flag |
| T-09 | gap_days > 90 | gap_warning=True, 경고 출력 |
| T-10 | oracledb 미설치 환경 | ImportError catch, Layer 2부터 |
| T-11 | 배치 모드 (--batch) | 전 종목에 TTM/growth/op_multiple 적용 |
