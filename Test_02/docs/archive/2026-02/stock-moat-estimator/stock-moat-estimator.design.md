# [Design] Stock Moat Estimator

> **Feature**: stock-moat-estimator
> **Phase**: Design
> **Created**: 2026-02-09
> **Plan Reference**: `docs/01-plan/features/stock-moat-estimator.plan.md`
> **Status**: In Progress

---

## 1. Agent Architecture

### 1.1 Agent Specification

**Agent Name**: `stock-moat-estimator`

**Agent Definition File**: `.agent/agents/stock-moat-estimator/agent.json`

```json
{
  "name": "stock-moat-estimator",
  "description": "Specialized agent for analyzing Korean stock moats and core business sectors",
  "version": "1.0.0",
  "model": "claude-sonnet-4-5",
  "fallback_model": "claude-haiku-4-5",
  "capabilities": [
    "korean-corporate-disclosure-analysis",
    "moat-strength-evaluation",
    "sector-classification",
    "competitive-analysis",
    "batch-processing"
  ],
  "knowledge_domains": [
    "Korean corporate disclosures (DART, KIND)",
    "229 sector taxonomy (Korean business classifications)",
    "Economic moat framework (5 categories)",
    "Investment philosophy (docs/investment-philosophy.md)",
    "Korean financial terminology"
  ],
  "tools": [
    "WebFetch",
    "Grep",
    "Read",
    "Write",
    "Bash"
  ],
  "memory": {
    "scope": "project",
    "path": ".agent/memory/stock-moat-estimator/",
    "persistent": true
  },
  "quality_thresholds": {
    "moat_verification_required": 4,
    "min_source_citations": 2,
    "max_tokens_per_stock": 10000
  }
}
```

### 1.2 Agent Knowledge Base

**Directory**: `.agent/memory/stock-moat-estimator/`

```
.agent/memory/stock-moat-estimator/
├── KNOWLEDGE.md                    # Core domain knowledge
├── sector_patterns.md              # Industry-specific moat patterns
├── moat_examples.md                # Reference analyses (learning)
├── error_corrections.md            # Quality improvements log
├── research_sources.md             # Reliable data sources catalog
└── taxonomy_mapping.json           # 229 sector → business mapping
```

**KNOWLEDGE.md Structure**:
```markdown
# Stock Moat Estimator Knowledge Base

## Data Sources (Priority Order)
1. DART (dart.fss.or.kr) - 사업보고서, 분기보고서
2. KIND (kind.krx.co.kr) - 기업개요, 재무정보
3. Company IR - 투자자 정보, 기업 소개
4. 증권보고서 - 상세 재무/사업 분석
5. Naver Finance - 뉴스, 공시 요약

## Moat Framework (5 Categories)
- 브랜드 파워 (Brand Power): 1-5 scale
- 원가 우위 (Cost Advantage): 1-5 scale
- 네트워크 효과 (Network Effects): 1-5 scale
- 전환 비용 (Switching Costs): 1-5 scale
- 규제/허가 (Regulatory Moat): 1-5 scale

## Sector Taxonomy Rules
- MUST use only 229 approved Korean names
- NO English names in core_sector_top
- core_sector_sub format: "category/subcategory"
```

### 1.3 Agent Prompts

**System Prompt Template** (`.agent/agents/stock-moat-estimator/system_prompt.md`):

```markdown
You are a specialized stock moat analyst for Korean companies. Your expertise:

1. **Data Sources**: DART, KIND, IR materials, 증권보고서
2. **Analysis Framework**:
   - Identify core business (본업) from disclosures
   - Map to 229 Korean sector categories (NO English)
   - Evaluate moat strength (1-5 scale, 5 categories)
   - Re-verify if moat ≥ 4 (mandatory quality gate)

3. **Output Requirements**:
   - Cite sources for all claims
   - Use structured format (see examples)
   - Korean language only
   - No speculation; facts only

4. **Quality Standards**:
   - Accuracy > Speed
   - Re-verify high moat scores (≥4)
   - Learn from corrections in error_corrections.md
```

---

## 2. Skill API Design

### 2.1 Skill Definition

**Skill Name**: `/stock-moat`

**Skill File**: `.agent/skills/stock-moat/skill.json`

```json
{
  "name": "stock-moat",
  "description": "Analyze stock moat strength and core business sectors",
  "version": "1.0.0",
  "commands": {
    "analyze": {
      "description": "Analyze single stock",
      "args": ["ticker"],
      "example": "/stock-moat analyze 005930"
    },
    "batch": {
      "description": "Batch process multiple stocks",
      "args": ["--all", "--range {start}-{end}"],
      "example": "/stock-moat batch --range 1-50"
    },
    "verify": {
      "description": "Re-verify high moat stock (≥4)",
      "args": ["ticker"],
      "example": "/stock-moat verify 005930"
    },
    "report": {
      "description": "Generate completion report",
      "args": [],
      "example": "/stock-moat report"
    },
    "status": {
      "description": "Check progress status",
      "args": [],
      "example": "/stock-moat status"
    }
  },
  "agent": "stock-moat-estimator",
  "auto_triggers": [
    "moat analysis",
    "해자 분석",
    "업종 분류",
    "sector classification",
    "core business"
  ]
}
```

### 2.2 Command Specifications

#### 2.2.1 `/stock-moat analyze {ticker}`

**Purpose**: Analyze a single stock and fill all missing fields

**Workflow**:
```
1. Load stock data from Excel (ticker row)
2. Check if already complete (skip if filled)
3. Research workflow:
   a. Fetch DART 사업보고서
   b. Identify core business
   c. Classify sector (229 taxonomy)
   d. Evaluate moat (5 categories)
   e. If moat ≥ 4 → trigger verify
4. Write results to Excel (atomic update)
5. Log completion status
```

**Input**: Stock ticker (6-digit code or name)

**Output**: Updated Excel row with all fields filled

**Example Usage**:
```bash
/stock-moat analyze 005930        # Samsung Electronics
/stock-moat analyze 네오위즈        # By name
```

---

#### 2.2.2 `/stock-moat batch --all` or `--range {start}-{end}`

**Purpose**: Process multiple stocks in parallel batches

**Workflow**:
```
1. Load incomplete stocks list (196 stocks)
2. Split into batches of 10 stocks
3. For each batch:
   a. Process 10 stocks in parallel
   b. Checkpoint after each batch
   c. Log progress to .stock-moat-status.json
4. Generate batch completion report
```

**Arguments**:
- `--all`: Process all 196 incomplete stocks
- `--range {start}-{end}`: Process rows start to end (e.g., 1-50)

**Example Usage**:
```bash
/stock-moat batch --all             # All 196 stocks
/stock-moat batch --range 1-50      # First 50 stocks
```

**Batch Processing Strategy**:
```python
# Parallel execution (10 concurrent)
batch_size = 10
batches = split_stocks_into_batches(incomplete_stocks, batch_size)

for batch_idx, batch in enumerate(batches):
    # Process 10 stocks in parallel
    results = parallel_process(batch, analyze_stock)

    # Checkpoint progress
    checkpoint(batch_idx, results)

    # Estimate: 5 min per batch → 20 batches × 5 = 100 min (1.7 hours)
```

---

#### 2.2.3 `/stock-moat verify {ticker}`

**Purpose**: Re-verify high moat stocks (≥4) with deeper research

**Workflow**:
```
1. Load stock with moat ≥ 4
2. Deep research:
   a. Cross-reference multiple sources
   b. Analyze competitors
   c. Validate moat sustainability
3. Update 검증용desc with verification details
4. Adjust moat score if needed
```

**Quality Gate**: Mandatory for all stocks with initial moat ≥ 4

**Example Usage**:
```bash
/stock-moat verify 005930
```

---

#### 2.2.4 `/stock-moat report`

**Purpose**: Generate analysis completion report

**Output**: `docs/04-report/stock-moat-estimator.report.md`

**Report Contents**:
- Completion statistics (208/208)
- Moat strength distribution (1-5 histogram)
- Sector breakdown (top 10 sectors)
- High moat stocks (≥4) list with verification status
- Quality metrics (avg tokens/stock, error rate)

---

#### 2.2.5 `/stock-moat status`

**Purpose**: Check current progress

**Output**:
```
📊 Stock Moat Analysis Status
─────────────────────────────
Total Stocks: 208
Completed: 45 / 208 (21.6%)
Remaining: 163
─────────────────────────────
Current Batch: 5 / 20
Moat ≥4 (Need Verification): 8
Verified: 5 / 8
─────────────────────────────
Estimated Time Remaining: 80 min
```

---

## 3. Data Schema & Excel I/O

### 3.1 Excel File Structure

**File**: `data/ask/stock_core_master_v2_korean_taxonomy_2026-01-30_요청용_011.xlsx`

**Sheets**:
1. `stock_core_master` - Main data (208 rows)
2. `schema` - Field definitions
3. `분류유형(참고)` - 229 sector taxonomy
4. `TODO` - Requirements
5. `change_log` - Modification history

### 3.2 stock_core_master Schema

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `ticker` | String(6) | Stock code | Required, unique |
| `name` | String | Company name | Required |
| `core_sector_top` | String | 업종 분류 (상위) | Must be from 229 approved list |
| `core_sector_sub` | String | 업종 분류 (하위) | Format: "cat/subcat" |
| `core_desc` | Text | 본업 설명 (1-3줄) | Min 20 chars |
| `해자강도` | Integer | Moat strength (1-5) | Range: 1-5 |
| `해자DESC` | Text | Moat category breakdown | Structured format (see below) |
| `moat_name` | String | (Deprecated) | Legacy field |
| `desc` | Text | (Deprecated) | Legacy field |
| `검증용desc` | Text | Re-verification notes | Required if 해자강도 ≥ 4 |

### 3.3 해자DESC Format Specification

**Structure**:
```
브랜드 파워: {score}/5 ({brief_reason})
원가 우위: {score}/5 ({brief_reason})
네트워크 효과: {score}/5 ({brief_reason})
전환 비용: {score}/5 ({brief_reason})
규제/허가: {score}/5 ({brief_reason})
---
총점: {sum}/25 → 해자강도 {final_score}
```

**Example**:
```
브랜드 파워: 4/5 (국내 1위 브랜드 인지도)
원가 우위: 3/5 (중규모 생산시설)
네트워크 효과: 2/5 (제한적)
전환 비용: 4/5 (기업 고객 장기 계약)
규제/허가: 5/5 (의료기기 허가 보유)
---
총점: 18/25 → 해자강도 4
```

**Calculation Logic**:
```python
def calculate_moat_strength(category_scores: dict) -> int:
    """
    category_scores = {
        'brand': 4,
        'cost': 3,
        'network': 2,
        'switching': 4,
        'regulatory': 5
    }
    """
    total = sum(category_scores.values())  # 18
    avg = total / 5  # 3.6
    moat_strength = round(avg)  # 4
    return moat_strength
```

### 3.4 Excel I/O Implementation

**Library**: `pandas` + `openpyxl`

**Read Operation**:
```python
import pandas as pd

def load_stock_data(file_path: str) -> pd.DataFrame:
    """Load stock_core_master sheet"""
    df = pd.read_excel(
        file_path,
        sheet_name='stock_core_master',
        engine='openpyxl'
    )
    return df

def get_incomplete_stocks(df: pd.DataFrame) -> pd.DataFrame:
    """Filter stocks with missing data"""
    incomplete = df[
        df['core_sector_top'].isna() |
        df['해자강도'].isna()
    ]
    return incomplete  # 196 stocks
```

**Write Operation** (Atomic):
```python
def update_stock_row(
    file_path: str,
    ticker: str,
    data: dict
) -> bool:
    """
    Atomic update of single stock row

    Args:
        ticker: Stock code (e.g., '005930')
        data: {
            'core_sector_top': '반도체',
            'core_sector_sub': '메모리/시스템반도체',
            'core_desc': '...',
            '해자강도': 5,
            '해자DESC': '...',
            '검증용desc': '...'
        }
    """
    # 1. Create backup
    backup_file = f"{file_path}.backup"
    shutil.copy2(file_path, backup_file)

    try:
        # 2. Load Excel
        with pd.ExcelFile(file_path, engine='openpyxl') as xls:
            df = pd.read_excel(xls, sheet_name='stock_core_master')

        # 3. Update row
        row_idx = df[df['ticker'] == ticker].index[0]
        for field, value in data.items():
            df.at[row_idx, field] = value

        # 4. Write back (atomic)
        with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            df.to_excel(writer, sheet_name='stock_core_master', index=False)

        # 5. Remove backup if successful
        os.remove(backup_file)
        return True

    except Exception as e:
        # Restore from backup
        shutil.copy2(backup_file, file_path)
        raise e
```

---

## 4. Research Workflow

### 4.1 Single Stock Analysis Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                 Stock Analysis Workflow                      │
└─────────────────────────────────────────────────────────────┘

[1] Load Stock Data
    ↓
    Input: ticker (e.g., '005930')
    Query: df[df['ticker'] == ticker]
    Check: Skip if already complete

[2] Fetch Company Info
    ↓
    Sources (priority order):
    1. DART API: https://opendart.fss.or.kr/api/company.json?crtfc_key={api_key}&corp_code={corp_code}
    2. KIND: http://kind.krx.co.kr/corpgeneral/corpList.do
    3. Naver Finance: https://finance.naver.com/item/main.nhn?code={ticker}
    ↓
    Extract:
    - 사업의 내용 (business description)
    - 주요 제품 및 서비스 (products/services)
    - 매출 구성 (revenue breakdown)

[3] Identify Core Business
    ↓
    Analysis:
    - Parse 사업보고서 "사업의 내용" section
    - Identify primary revenue source (>50% revenue)
    - Map business description to keywords
    ↓
    Output:
    - core_desc (1-3 sentences summary)

[4] Classify Sector
    ↓
    Mapping Process:
    - Load 229 sector taxonomy from '분류유형(참고)' sheet
    - Match keywords to sector names
    - Use fuzzy matching if needed
    - Validate: MUST use Korean name only
    ↓
    Output:
    - core_sector_top (e.g., "반도체")
    - core_sector_sub (e.g., "메모리/시스템반도체")

[5] Evaluate Moat Strength
    ↓
    Framework (5 categories):

    A. 브랜드 파워 (Brand Power)
       - Consumer recognition
       - Brand loyalty metrics
       - Market share in brand-sensitive segments

    B. 원가 우위 (Cost Advantage)
       - Economies of scale
       - Proprietary technology
       - Exclusive access to resources

    C. 네트워크 효과 (Network Effects)
       - Platform dynamics
       - User growth → value growth
       - Multi-sided markets

    D. 전환 비용 (Switching Costs)
       - Customer lock-in
       - Integration complexity
       - Long-term contracts

    E. 규제/허가 (Regulatory Moat)
       - Licenses and permits
       - Regulatory barriers to entry
       - Government approvals

    ↓
    Scoring:
    - Each category: 1-5 scale
    - Total: sum(scores) / 5 = avg
    - Round to nearest integer → 해자강도

    ↓
    Output:
    - 해자강도: 1-5
    - 해자DESC: structured breakdown

[6] Quality Gate: Re-verification (if 해자강도 ≥ 4)
    ↓
    Deep Research:
    - Cross-reference multiple sources
    - Analyze top 3 competitors
    - Validate moat sustainability (3-5 years)
    - Check for structural vs temporary advantages
    ↓
    Verification Questions:
    1. Can competitors easily replicate this advantage?
    2. Is the moat widening or narrowing?
    3. What could destroy this moat?
    ↓
    Output:
    - 검증용desc: detailed verification notes
    - Adjusted 해자강도 (if needed)

[7] Write Results to Excel
    ↓
    Atomic Write:
    - Backup file
    - Update row
    - Validate write
    - Remove backup
    ↓
    Log: completion status to .stock-moat-status.json

[8] Update Agent Memory
    ↓
    Learning:
    - Add to moat_examples.md (if exemplary)
    - Update sector_patterns.md (new insights)
    - Log errors to error_corrections.md
```

### 4.2 Batch Processing Workflow

```
┌─────────────────────────────────────────────────────────────┐
│              Batch Processing Architecture                   │
└─────────────────────────────────────────────────────────────┘

[1] Load Incomplete Stocks
    ↓
    Query: df[df['해자강도'].isna()]
    Result: 196 stocks

[2] Split into Batches
    ↓
    batch_size = 10
    batches = [stocks[i:i+10] for i in range(0, 196, 10)]
    Total batches: 20

[3] Process Batch (Parallel)
    ↓
    For each batch:

    ┌──────────────────────────────────────────────┐
    │  Parallel Executor (10 concurrent tasks)     │
    ├──────────────────────────────────────────────┤
    │  Task 1: analyze(stock_1)  [Haiku/Sonnet]   │
    │  Task 2: analyze(stock_2)  [Haiku/Sonnet]   │
    │  Task 3: analyze(stock_3)  [Haiku/Sonnet]   │
    │  ...                                         │
    │  Task 10: analyze(stock_10) [Haiku/Sonnet]  │
    └──────────────────────────────────────────────┘

    Model Selection:
    - Use Haiku for simple cases (moat likely < 4)
    - Use Sonnet for complex/large companies
    - Auto-upgrade to Sonnet if Haiku uncertain

[4] Checkpoint Progress
    ↓
    After each batch:
    - Save progress to .stock-moat-status.json
    - Log completed tickers
    - Record errors for retry

    Status File Format:
    {
      "total": 196,
      "completed": 45,
      "failed": 2,
      "in_progress": 10,
      "current_batch": 5,
      "last_updated": "2026-02-09T12:30:00Z",
      "high_moat_stocks": ["005930", "000660", ...],
      "needs_verification": 8
    }

[5] Error Handling
    ↓
    Retry Logic:
    - API failure: retry 3x with exponential backoff
    - Data missing: mark for manual review
    - Rate limit: pause 60s, resume

    Fallback:
    - If DART fails: try KIND
    - If KIND fails: try Naver Finance
    - If all fail: log to manual_review.json

[6] Re-verification Queue
    ↓
    After batch completion:
    - Collect stocks with 해자강도 ≥ 4
    - Process verification queue (sequential)
    - Use Sonnet model (higher quality)
    - Update 검증용desc

[7] Generate Report
    ↓
    Final report:
    - Completion rate (208/208)
    - Moat distribution histogram
    - Sector breakdown
    - Quality metrics
```

---

## 5. Moat Evaluation Framework (Detailed)

### 5.1 Scoring Rubric

#### 브랜드 파워 (Brand Power)

| Score | Criteria | Examples |
|-------|----------|----------|
| 5 | 글로벌 톱티어 브랜드, 독점적 인지도 | 삼성, 현대차 |
| 4 | 국내 1-2위 브랜드, 강한 충성도 | 네이버, 카카오 |
| 3 | 일부 세그먼트에서 인정받음 | 중견기업 브랜드 |
| 2 | 브랜드 인지도 낮음, 일부만 인지 | 소형주 |
| 1 | 브랜드 무관한 사업 (commoditized) | 2차전지 소재 |

**Indicators**:
- 브랜드 가치 평가액 (Interbrand, Brand Finance)
- 소비자 설문 인지도 (Top-of-Mind)
- 프리미엄 가격 책정 능력 (price premium)

---

#### 원가 우위 (Cost Advantage)

| Score | Criteria | Examples |
|-------|----------|----------|
| 5 | 압도적 규모의 경제, 독점적 자원 | 삼성전자 파운드리, POSCO 제철 |
| 4 | 업계 최대 생산시설, 수직계열화 | 현대제철, LG화학 |
| 3 | 중규모 시설, 일부 원가 우위 | 중견 제조업 |
| 2 | 원가 우위 제한적 | 소형 제조업 |
| 1 | 외주 의존, 원가 경쟁력 없음 | 유통업 |

**Indicators**:
- COGS (Cost of Goods Sold) / Revenue ratio
- Gross margin vs industry average
- CAPEX 규모 (진입장벽)
- 생산능력 (Capacity) 업계 순위

---

#### 네트워크 효과 (Network Effects)

| Score | Criteria | Examples |
|-------|----------|----------|
| 5 | 강력한 플랫폼, 사용자 증가 = 가치 증가 | 카카오톡, 네이버 |
| 4 | 플랫폼 비즈니스, 양면시장 | 쿠팡, 배달의민족 |
| 3 | 일부 네트워크 효과 존재 | 온라인 커뮤니티 |
| 2 | 제한적 네트워크 효과 | 단방향 서비스 |
| 1 | 네트워크 효과 무관 | 제조업 |

**Indicators**:
- MAU (Monthly Active Users) 성장률
- Network density (사용자당 연결 수)
- Multi-homing cost (타 플랫폼 병행 사용 비용)

---

#### 전환 비용 (Switching Costs)

| Score | Criteria | Examples |
|-------|----------|----------|
| 5 | 전환 거의 불가능 (시스템 의존) | ERP 솔루션, 은행 코어뱅킹 |
| 4 | 전환 비용 높음 (장기 계약, 기술 의존) | B2B SaaS, 반도체 장비 |
| 3 | 중간 수준 전환 비용 | 보험, 통신 |
| 2 | 낮은 전환 비용 | 소비재 |
| 1 | 전환 매우 쉬움 | Commodities |

**Indicators**:
- 평균 계약 기간 (B2B)
- Churn rate (이탈률)
- Integration complexity (시스템 연동)
- Data migration cost

---

#### 규제/허가 (Regulatory Moat)

| Score | Criteria | Examples |
|-------|----------|----------|
| 5 | 독점 라이선스, 특허 보호 | 의약품, 카지노 |
| 4 | 엄격한 허가 필요, 진입장벽 높음 | 의료기기, 금융 |
| 3 | 일부 규제 장벽 | 건설, 에너지 |
| 2 | 기본 인허가만 필요 | 일반 제조업 |
| 1 | 규제 장벽 없음 | IT 서비스 |

**Indicators**:
- 허가/라이선스 취득 기간
- 규제 기관 수
- 신규 진입자 수 (최근 3년)

---

### 5.2 Moat Scoring Examples (Detailed)

#### Example 1: 삼성전자 (005930)

**Research Sources**:
- DART 사업보고서 2024
- KIND 기업개요
- 삼성전자 IR 자료

**Core Business**:
```
core_sector_top: 반도체
core_sector_sub: 메모리/시스템반도체
core_desc: 메모리 반도체(D램, 낸드), 시스템반도체(파운드리, AP) 제조.
           글로벌 메모리 시장 점유율 1위(40%), 파운드리 2위(18%).
```

**Moat Analysis**:
```
브랜드 파워: 5/5 (글로벌 톱티어 브랜드, Interbrand 5위)
원가 우위: 5/5 (초대규모 fab(CAPEX 50조/년), 수직계열화)
네트워크 효과: 3/5 (갤럭시 생태계, 제한적)
전환 비용: 4/5 (B2B 고객 기술 의존성, 장기 공급계약)
규제/허가: 3/5 (일반 산업재, 특허는 많으나 독점 아님)
---
총점: 20/25 → 해자강도 4
```

**Re-verification** (해자강도 ≥ 4):
```
검증용desc:
메모리 반도체 시장 점유율 1위(40%, SK하이닉스 2위 30%).
파운드리 점유율 2위(18%, TSMC 1위 60%).
CAPEX 50조원/년으로 진입장벽 극도로 높음 (경쟁사: 30-40조).
10nm 이하 공정 기술력 검증됨 (증권보고서 2024 확인).
→ 해자강도 4 유지 (5로 상향 검토했으나, 파운드리 점유율 고려시 4 적정)
```

---

#### Example 2: 네오위즈 (095660) - 중소형 게임사

**Research Sources**:
- DART 사업보고서 2024
- KIND 기업개요
- 네오위즈 IR

**Core Business**:
```
core_sector_top: 게임
core_sector_sub: 모바일 게임/PC게임
core_desc: 모바일 게임(브라운더스트2, 클로저스), PC게임(블레소, DJ맥스) 개발/퍼블리싱.
           매출 구성: 모바일 60%, PC 30%, 기타 10%.
```

**Moat Analysis**:
```
브랜드 파워: 2/5 (일부 게임 IP 보유하나 인지도 제한적)
원가 우위: 1/5 (외주 개발 의존, 자체 엔진 없음)
네트워크 효과: 3/5 (온라인 게임 유저 커뮤니티, 제한적)
전환 비용: 1/5 (게임 이탈 쉬움, 유저 충성도 낮음)
규제/허가: 2/5 (게임물등급심의만 필요, 진입장벽 낮음)
---
총점: 9/25 → 해자강도 2
```

**No Re-verification** (해자강도 < 4)

---

## 6. Data Sources & API Integration

### 6.1 DART API (금융감독원 전자공시시스템)

**Base URL**: `https://opendart.fss.or.kr`

**API Key**: Required (환경변수 `DART_API_KEY`)

**Key Endpoints**:

1. **Company Info** (`/api/company.json`)
   ```
   GET /api/company.json?crtfc_key={api_key}&corp_code={corp_code}

   Response:
   {
     "corp_name": "삼성전자",
     "corp_code": "00126380",
     "stock_code": "005930",
     "ceo_nm": "한종희",
     "corp_cls": "Y",
     "jurir_no": "1301110006246",
     "bizr_no": "1248100998",
     "adres": "경기도 수원시 영통구 삼성로 129",
     "hm_url": "www.samsung.com",
     "ir_url": "https://www.samsung.com/sec/ir/",
     "phn_no": "031-200-1114",
     "fax_no": "031-200-7538",
     "induty_code": "264",
     "est_dt": "19690113"
   }
   ```

2. **Business Report** (`/api/fnlttSinglAcntAll.json`)
   ```
   GET /api/fnlttSinglAcntAll.json?crtfc_key={api_key}&corp_code={corp_code}&bsns_year=2024&reprt_code=11011

   Response: Financial statements + 사업의 내용 section
   ```

**Usage in Agent**:
```python
def fetch_dart_business_description(corp_code: str) -> str:
    """Fetch 사업의 내용 from DART"""
    url = f"https://opendart.fss.or.kr/api/company.json"
    params = {
        "crtfc_key": os.getenv("DART_API_KEY"),
        "corp_code": corp_code
    }
    response = requests.get(url, params=params)
    data = response.json()

    # Extract business description
    business_desc = data.get('business_summary', '')
    return business_desc
```

### 6.2 KIND API (한국거래소 기업정보)

**Base URL**: `http://kind.krx.co.kr`

**No API Key Required** (public data)

**Web Scraping Endpoints**:

1. **Company Overview**:
   ```
   URL: http://kind.krx.co.kr/corpgeneral/corpList.do?method=loadInitPage

   Search: ticker or name
   Extract: 업종, 주요제품, 사업내용
   ```

**Usage in Agent**:
```python
def fetch_kind_company_info(ticker: str) -> dict:
    """Scrape KIND for company info"""
    url = "http://kind.krx.co.kr/corpgeneral/corpList.do"
    params = {"method": "loadInitPage"}

    # Use BeautifulSoup to parse HTML
    response = requests.get(url, params=params)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract fields
    industry = soup.find('td', text='업종').find_next('td').text
    products = soup.find('td', text='주요제품').find_next('td').text

    return {
        'industry': industry,
        'products': products
    }
```

### 6.3 Company IR Pages

**Strategy**: Use WebFetch tool to fetch IR pages

**Common Patterns**:
- Samsung: `https://www.samsung.com/sec/ir/`
- Naver: `https://ir.navercorp.com/`
- Kakao: `https://ir.kakaocorp.com/`

**Usage**:
```python
# In agent workflow
ir_url = company_data.get('ir_url')
if ir_url:
    content = WebFetch(ir_url, "Extract business description and key products")
```

---

## 7. Progress Tracking & Checkpointing

### 7.1 Status File Structure

**File**: `.stock-moat-status.json`

```json
{
  "version": "1.0.0",
  "last_updated": "2026-02-09T14:30:00Z",
  "total_stocks": 208,
  "completed_stocks": 45,
  "failed_stocks": 2,
  "in_progress_stocks": 10,
  "batches": {
    "total": 20,
    "current": 5,
    "completed": 4
  },
  "high_moat_stocks": [
    "005930",
    "000660",
    "035720"
  ],
  "verification_queue": [
    {
      "ticker": "005930",
      "moat_strength": 4,
      "verified": true,
      "verified_at": "2026-02-09T13:00:00Z"
    }
  ],
  "failed_stocks_log": [
    {
      "ticker": "123456",
      "error": "DART API timeout",
      "retry_count": 3,
      "last_attempt": "2026-02-09T12:00:00Z"
    }
  ],
  "metrics": {
    "avg_tokens_per_stock": 8500,
    "avg_time_per_stock": "4.2 min",
    "total_api_calls": 450,
    "cache_hit_rate": 0.35
  }
}
```

### 7.2 Checkpointing Logic

```python
def checkpoint_progress(batch_idx: int, results: list):
    """Save progress after each batch"""
    status = load_status('.stock-moat-status.json')

    # Update completed stocks
    for result in results:
        if result['success']:
            status['completed_stocks'] += 1
        else:
            status['failed_stocks'] += 1
            status['failed_stocks_log'].append(result['error_info'])

    # Update batch progress
    status['batches']['current'] = batch_idx + 1
    status['batches']['completed'] = batch_idx

    # Update high moat queue
    for result in results:
        if result.get('moat_strength', 0) >= 4:
            status['high_moat_stocks'].append(result['ticker'])
            status['verification_queue'].append({
                'ticker': result['ticker'],
                'moat_strength': result['moat_strength'],
                'verified': False
            })

    # Save status
    save_status('.stock-moat-status.json', status)
```

---

## 8. Error Handling & Retry Strategy

### 8.1 Error Categories

| Error Type | Severity | Retry Strategy | Fallback |
|------------|----------|----------------|----------|
| DART API timeout | Medium | 3x exponential backoff | Try KIND |
| KIND scraping failure | Medium | 2x retry | Try Naver Finance |
| Excel write failure | High | 5x retry + backup | Alert user |
| Sector mapping failure | Low | Manual review | Use "기타" category |
| Rate limit (429) | Low | Wait 60s, retry | Continue next batch |

### 8.2 Retry Implementation

```python
def fetch_with_retry(
    fetch_func,
    max_retries=3,
    backoff_factor=2
):
    """Exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            return fetch_func()
        except (Timeout, ConnectionError) as e:
            if attempt == max_retries - 1:
                raise
            wait_time = backoff_factor ** attempt
            time.sleep(wait_time)
            continue
```

### 8.3 Fallback Chain

```
DART API → KIND Scraping → Naver Finance → Manual Review
```

---

## 9. Implementation Files Structure

### 9.1 Directory Layout

```
.agent/
├── agents/
│   └── stock-moat-estimator/
│       ├── agent.json                  # Agent definition
│       ├── system_prompt.md            # System prompt
│       └── config.yml                  # Agent config
├── memory/
│   └── stock-moat-estimator/
│       ├── KNOWLEDGE.md                # Core knowledge
│       ├── sector_patterns.md          # Industry patterns
│       ├── moat_examples.md            # Reference analyses
│       ├── error_corrections.md        # Quality log
│       ├── research_sources.md         # Data sources
│       └── taxonomy_mapping.json       # 229 sector mapping
├── skills/
│   └── stock-moat/
│       ├── skill.json                  # Skill definition
│       ├── commands/
│       │   ├── analyze.py              # /stock-moat analyze
│       │   ├── batch.py                # /stock-moat batch
│       │   ├── verify.py               # /stock-moat verify
│       │   ├── report.py               # /stock-moat report
│       │   └── status.py               # /stock-moat status
│       └── utils/
│           ├── excel_io.py             # Excel read/write
│           ├── dart_api.py             # DART integration
│           ├── kind_scraper.py         # KIND scraping
│           └── moat_scoring.py         # Moat framework
└── workflows/
    └── stock-moat-estimator/
        ├── single_stock_workflow.yml   # Single stock analysis
        └── batch_workflow.yml          # Batch processing

scripts/
└── stock_moat/
    ├── analyze_stock.py                # CLI entry point
    ├── batch_processor.py              # Batch executor
    └── verification_queue.py           # Moat ≥4 re-verification

data/
└── stock_moat/
    ├── .stock-moat-status.json         # Progress tracking
    └── manual_review.json              # Failed stocks log
```

### 9.2 Key Implementation Files

#### `.agent/agents/stock-moat-estimator/agent.json`
```json
{
  "name": "stock-moat-estimator",
  "version": "1.0.0",
  "model": "claude-sonnet-4-5",
  "fallback_model": "claude-haiku-4-5",
  "max_tokens": 10000,
  "temperature": 0.3,
  "system_prompt_file": "system_prompt.md"
}
```

#### `.agent/skills/stock-moat/commands/analyze.py`
```python
"""
/stock-moat analyze {ticker} implementation
"""

def analyze_stock(ticker: str) -> dict:
    """
    Analyze single stock and fill missing fields

    Returns:
        {
            'ticker': '005930',
            'core_sector_top': '반도체',
            'core_sector_sub': '메모리/시스템반도체',
            'core_desc': '...',
            '해자강도': 4,
            '해자DESC': '...',
            '검증용desc': '...'
        }
    """
    # 1. Load stock data
    stock = load_stock(ticker)

    # 2. Research workflow
    dart_data = fetch_dart(stock['corp_code'])
    kind_data = fetch_kind(ticker)

    # 3. Identify core business
    core_desc = identify_core_business(dart_data, kind_data)

    # 4. Classify sector
    sector_top, sector_sub = classify_sector(core_desc)

    # 5. Evaluate moat
    moat_result = evaluate_moat(dart_data, kind_data, sector_top)

    # 6. Re-verify if moat ≥ 4
    if moat_result['해자강도'] >= 4:
        verification = deep_verify(ticker, moat_result)
        moat_result['검증용desc'] = verification

    # 7. Write to Excel
    update_excel(ticker, {
        'core_sector_top': sector_top,
        'core_sector_sub': sector_sub,
        'core_desc': core_desc,
        **moat_result
    })

    return moat_result
```

---

## 10. Testing & Validation Strategy

### 10.1 Unit Testing

**Test Cases**:
1. Excel I/O: Read/write operations
2. DART API: Mock responses
3. Sector mapping: 229 categories validation
4. Moat scoring: Calculation logic
5. Error handling: Retry logic, fallbacks

**Test File**: `tests/test_stock_moat.py`

```python
def test_moat_calculation():
    scores = {
        'brand': 4,
        'cost': 3,
        'network': 2,
        'switching': 4,
        'regulatory': 5
    }
    result = calculate_moat_strength(scores)
    assert result == 4  # (18/5 = 3.6 → round to 4)

def test_sector_mapping():
    business_desc = "반도체 메모리 제조"
    sector = map_to_sector(business_desc, taxonomy)
    assert sector == "반도체"
```

### 10.2 Integration Testing

**Test Workflow**:
1. Test 5 representative stocks manually
2. Validate all fields filled correctly
3. Check moat scoring consistency
4. Verify re-verification for high moat stocks

**Test Stocks**:
- 삼성전자 (005930) - Large cap, high moat
- 네오위즈 (095660) - Mid cap, low moat
- 알톤 (123750) - Small cap, unclear business
- 현대차 (005380) - Manufacturing
- 카카오 (035720) - Platform

### 10.3 Quality Assurance

**Manual Review** (20% sample):
- Random sample of 40 stocks (20% of 196)
- Expert review of moat scores
- Verify source citations
- Check sector classification accuracy

**Acceptance Criteria**:
- Sector classification accuracy: ≥ 95%
- Moat score consistency: ≥ 90% agreement with expert
- Source citation: 100% of stocks
- Re-verification: 100% for moat ≥ 4

---

## 11. Performance & Optimization

### 11.1 Speed Optimization

**Current Estimate**: 196 stocks × 5 min = 980 min (16.3 hours)

**Optimization Tactics**:

1. **Parallel Processing** (10 concurrent)
   - Reduce to: 20 batches × 5 min = 100 min (1.7 hours)

2. **Model Selection**:
   - Haiku for simple stocks (moat < 4): 2 min/stock
   - Sonnet for complex stocks: 5 min/stock
   - Expected mix: 70% Haiku, 30% Sonnet
   - New estimate: 196 × (0.7 × 2 + 0.3 × 5) = 196 × 2.9 = 568 min (9.5 hours)
   - With parallelization (÷10): **~60 min (1 hour)** ⚡

3. **Caching**:
   - Cache DART responses (same corp_code)
   - Cache sector mappings (common keywords)
   - Expected cache hit rate: 35%
   - Time savings: 35% × 60 min = 21 min saved

**Final Estimate**: **40-50 minutes** for all 196 stocks (with re-verification: +2 hours)

**Total Time**: **2.5-3 hours** ⚡

### 11.2 Token Optimization

**Current Estimate**: 10,000 tokens/stock × 196 = 1,960,000 tokens

**Optimization**:
- Use Haiku (cheaper) for 70% of stocks
- Cache common responses (sector taxonomy)
- Structured prompts (reduce redundancy)

**Token Budget**:
- Haiku: 137 stocks × 5,000 tokens = 685,000 tokens
- Sonnet: 59 stocks × 10,000 tokens = 590,000 tokens
- **Total**: ~1,275,000 tokens (35% savings)

---

## 12. Next Steps (Implementation Phase)

### Phase 1: Setup (2-3 hours)
1. Create agent directory structure
2. Write agent.json and system_prompt.md
3. Create skill.json and command stubs
4. Set up agent memory files

### Phase 2: Core Implementation (4-6 hours)
1. Implement Excel I/O (excel_io.py)
2. DART API integration (dart_api.py)
3. KIND scraping (kind_scraper.py)
4. Moat scoring logic (moat_scoring.py)
5. Single stock workflow (analyze.py)

### Phase 3: Batch Processing (2-3 hours)
1. Implement batch_processor.py
2. Checkpointing logic
3. Error handling & retry
4. Progress tracking

### Phase 4: Testing (2-3 hours)
1. Unit tests (5 stocks)
2. Integration test (batch of 10)
3. Quality validation

### Phase 5: Execution (3-4 hours)
1. Run batch processing (all 196 stocks)
2. Re-verification queue (moat ≥ 4)
3. Generate final report

**Total Development Time**: 10-15 hours (1.5-2 days)
**Total Execution Time**: 3-4 hours

---

## 13. Success Metrics (Design Phase)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Completion Rate** | 100% (208/208) | Excel row count |
| **Moat Accuracy** | ≥ 90% | Expert review (40-stock sample) |
| **Sector Classification** | ≥ 95% | Taxonomy compliance check |
| **Re-verification** | 100% for moat ≥4 | 검증용desc filled |
| **Source Citations** | 100% | All stocks cite DART/KIND/IR |
| **Execution Time** | < 4 hours | Batch processing logs |
| **Token Usage** | < 1.5M tokens | API monitoring |
| **Error Rate** | < 5% | Failed stocks / total stocks |

---

## 14. Risks & Mitigation (Design Phase)

| Risk | Impact | Mitigation Strategy |
|------|--------|---------------------|
| DART API rate limiting | High | Exponential backoff, cache responses, use KIND fallback |
| Insufficient disclosure data | Medium | Use IR pages, Naver Finance; mark for manual review if needed |
| Sector taxonomy ambiguity | Medium | Fuzzy matching, manual review of edge cases (5%) |
| Moat scoring inconsistency | High | Detailed rubric, agent memory learning, expert review sample |
| Excel file corruption | Critical | Atomic writes with backup, test on copy first |
| Token budget overrun | Medium | Use Haiku for 70% of stocks, cache aggressively |

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 2026-02-09 | Claude Sonnet 4.5 | Initial design document created |
| 2026-02-09 | Claude Sonnet 4.5 | Added detailed agent spec, skill API, moat framework, implementation files |
| 2026-02-09 | Claude Sonnet 4.5 | Optimized timeline to 1.5-2 days (parallel processing) |
