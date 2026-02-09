# [Plan] Stock Moat Estimator

> **Feature**: stock-moat-estimator
> **Phase**: Plan
> **Created**: 2026-02-09
> **Status**: Draft

---

## 1. Background & Motivation

### Current State

Stock Research ONE currently has a database of **208 Korean stocks** with incomplete fundamental analysis data. The Excel file `stock_core_master_v2_korean_taxonomy_2026-01-30_요청용_011.xlsx` contains:

- **Total stocks**: 208 종목
- **Incomplete records**: 196 stocks (94.2%) with missing core business and moat analysis
- **Missing fields**:
  - `core_sector_top`: 업종 분류 (상위) - 94.2% empty
  - `core_sector_sub`: 업종 분류 (하위) - 94.2% empty
  - `core_desc`: 본업 설명 - 94.2% empty
  - `해자강도` (Moat Strength): 5점 만점 평가 - 94.2% empty
  - `해자DESC`: 해자 항목별 점수 - 94.2% empty
  - `검증용desc`: 해자강도 4+ 재검증 - 98.1% empty

- **Available sector taxonomy**: 229 개 섹터 분류 (한글 정규명)

### Problem Statement

**Manual stock analysis does not scale**. Currently:

1. **Labor-Intensive Research**: Manually researching 196 stocks for core business identification and moat analysis would take weeks
2. **Inconsistent Quality**: Human analysis varies in depth and accuracy across different stocks
3. **No Automation**: Repetitive task without a reusable agent/skill/tool means wasted effort
4. **Token Inefficiency**: Ad-hoc analysis consumes excessive tokens without learning/memory
5. **Verification Burden**: Moat strength 4+ requires re-analysis for accuracy (double work)

### Why This Matters

- **Investment Accuracy**: Moat analysis is critical for identifying durable competitive advantages
- **Scalability**: Need to process 196 stocks efficiently and handle future additions
- **Repeatability**: This task will recur as new stocks are added to the research universe
- **Cost Efficiency**: Agent + skill + MCP architecture reduces token usage and improves reliability

---

## 2. Objectives

### Primary Goals

1. **Automate Stock Moat Analysis**
   - Create `stock-moat-estimator` agent with expertise in Korean corporate disclosures
   - Analyze 196 incomplete stocks systematically
   - Fill all missing fields with high-quality, researched data
   - Target: 100% completion of stock_core_master sheet

2. **Ensure Research Quality**
   - Use DART (공시), KIND, IR materials, 증권보고서 as primary sources
   - Apply 5-point moat strength scoring (해자강도: 1-5)
   - Provide detailed moat breakdown by category (해자DESC)
   - **Critical**: Re-verify stocks with moat strength ≥ 4 for accuracy

3. **Build Reusable Infrastructure**
   - Create skill: `/stock-moat` for invoking analysis workflow
   - (Optional) MCP server for structured data access to Excel/DB
   - Agent memory: Learn from completed analyses to improve future quality
   - Documentation: Clear schema and examples for future analysts

### Secondary Goals

- Export results back to Excel with proper formatting
- Generate analysis report showing moat strength distribution
- Build knowledge base of Korean industry sector patterns
- Create templates for moat analysis documentation

---

## 3. Scope

### In Scope

#### Phase 1: Agent & Infrastructure Setup
- Create `stock-moat-estimator` agent specification
- Define agent capabilities and knowledge domains
- Set up agent memory for learning across analyses
- Create `/stock-moat` skill for easy invocation

#### Phase 2: Data Schema & Taxonomy
- Document Excel schema structure (ticker, name, sectors, moat fields)
- Map 229 sector categories to Korean business classifications
- Define moat strength scoring rubric (1-5 scale)
- Create moat category framework (e.g., brand, cost, network effects, regulation, switching costs)

#### Phase 3: Research Workflow Design
- Define step-by-step moat analysis process
- Identify data sources: DART, KIND, IR pages, 증권보고서
- Create verification workflow for moat strength ≥ 4
- Design batch processing logic (handle 196 stocks efficiently)

#### Phase 4: Core Analysis Implementation
- Implement per-stock research pipeline:
  1. Fetch company disclosure data
  2. Identify core business (본업) and sector classification
  3. Analyze competitive moat strength
  4. Generate moat description by category
  5. Verify high-moat stocks (≥4) with deeper analysis
- Handle edge cases (unlisted stocks, insufficient data)

#### Phase 5: Data Export & Validation
- Write results back to Excel file
- Validate data completeness (all 196 stocks filled)
- Generate analysis report with statistics
- Gap analysis: compare filled data quality

#### Phase 6: (Optional) MCP Server
- If beneficial, create MCP server for:
  - Structured Excel read/write
  - Database integration
  - Token-efficient data access
- Evaluate ROI before implementation

### Out of Scope

- Real-time market data integration (price, volume)
- Financial ratio analysis (P/E, ROE, etc.)
- Stock screening or ranking features
- Portfolio optimization algorithms
- Web UI for moat analysis results
- English language support (Korean only)

---

## 4. Success Criteria

### Quantitative Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Completion Rate | 12/208 (5.8%) | 208/208 (100%) | Excel row count |
| Moat Analysis Quality | N/A | ≥ 90% accuracy | Expert review sample (20 stocks) |
| Research Time per Stock | Manual: ~30 min | Agent: < 5 min | Execution logs |
| Token Usage per Stock | Unknown | < 10,000 tokens | API monitoring |
| Re-verification Rate | 0% | 100% for moat ≥ 4 | Workflow logs |

### Qualitative Metrics

- [ ] All 229 sector categories correctly mapped
- [ ] Moat strength scoring is consistent across similar companies
- [ ] Moat descriptions provide actionable investment insights
- [ ] High-moat stocks (≥4) have detailed verification notes
- [ ] Agent memory improves quality over time (learns patterns)
- [ ] Skill invocation is simple: `/stock-moat analyze {ticker}`
- [ ] Documentation enables future analysts to extend the system

### Data Quality Validation

**Schema Compliance**:
- `core_sector_top` uses only 229 approved Korean names (no English)
- `core_sector_sub` follows format: "테스트 프로브/소켓" (category/subcategory)
- `해자강도` is integer 1-5
- `해자DESC` follows existing format (multi-item scoring)

**Research Standards**:
- Sources cited: DART, KIND, IR, 증권보고서
- Moat ≥4 stocks have `검증용desc` with re-verification details
- No speculation; only facts from reliable disclosures

---

## 5. Technical Approach

### Architecture Overview

```
┌───────────────────────────────────────────────────────────────┐
│                    User Invocation                            │
│  /stock-moat analyze {ticker}                                 │
│  /stock-moat batch --all                                      │
│  /stock-moat verify {ticker}  (for moat ≥ 4 re-check)        │
└───────────────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────────────────────────────────────────────┐
│              stock-moat-estimator Agent                       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Knowledge Domains                                       │ │
│  │  - Korean corporate disclosure systems (DART, KIND)     │ │
│  │  - 229 sector taxonomy                                  │ │
│  │  - Moat analysis framework (5 categories)              │ │
│  │  - Investment philosophy (docs/investment-philosophy)   │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Capabilities                                            │ │
│  │  - Web research (DART, KIND, IR pages)                 │ │
│  │  - Text analysis (Korean NLP, business description)    │ │
│  │  - Sector classification (229-category mapping)        │ │
│  │  - Moat strength scoring (1-5 rubric)                  │ │
│  │  - Quality verification (moat ≥4 re-check)            │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Memory & Learning                                       │ │
│  │  - .agent/memory/stock-moat-estimator/                 │ │
│  │    - sector_patterns.md (industry insights)            │ │
│  │    - moat_examples.md (reference analyses)             │ │
│  │    - error_corrections.md (quality improvements)       │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────────────────────────────────────────────┐
│                  Data Layer (Optional MCP)                    │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Excel I/O                                               │ │
│  │  - Read: stock_core_master sheet (208 rows)            │ │
│  │  - Read: schema, 분류유형(참고) sheets                    │ │
│  │  - Write: Update fields (atomic operations)            │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ External APIs (Future)                                  │ │
│  │  - DART OpenAPI (공시 검색)                             │ │
│  │  - KIND API (기업정보)                                  │ │
│  │  - Web scraping (IR pages, 증권보고서)                  │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────────────────────────────────────────────┐
│                    Output & Reporting                         │
│  - Updated Excel file (all 208 stocks complete)               │
│  - Analysis report (moat distribution, sector insights)       │
│  - Quality metrics (completion rate, accuracy scores)         │
└───────────────────────────────────────────────────────────────┘
```

### Moat Analysis Framework

**5-Point Moat Strength Scale**:
1. **점수 1** (매우 약함): 경쟁우위 없음, commoditized business
2. **점수 2** (약함): 일시적 우위만 존재, 쉽게 모방 가능
3. **점수 3** (보통): 일부 경쟁우위 존재하나 지속성 불확실
4. **점수 4** (강함): 명확한 해자, 지속 가능한 경쟁우위 ⚠️ **재검증 필수**
5. **점수 5** (매우 강함): 독점적 지위, 구조적 해자 ⚠️ **재검증 필수**

**Moat Categories** (해자DESC 항목):
- **브랜드 파워** (Brand): 소비자 인지도, 브랜드 충성도
- **원가 우위** (Cost Advantage): 규모의 경제, 독점적 자원 접근
- **네트워크 효과** (Network Effects): 사용자 증가 → 가치 증가
- **전환 비용** (Switching Costs): 고객 이탈 장벽
- **규제/허가** (Regulatory): 진입장벽, 라이선스

**Scoring Format** (해자DESC):
```
브랜드 파워: 4/5 (국내 1위 브랜드 인지도)
원가 우위: 3/5 (중규모 생산시설)
네트워크 효과: 2/5 (제한적)
전환 비용: 4/5 (기업 고객 장기 계약)
규제/허가: 5/5 (의료기기 허가 보유)
---
총점: 18/25 → 해자강도 4
```

### Technology Stack

**Agent Implementation**:
- **Framework**: bkit Agent framework (v1.5.2)
- **Model**: Claude Sonnet 4.5 (balanced speed/quality)
- **Memory**: Project-scoped agent memory (persistent learning)
- **Tools**: WebFetch, Grep, Read, Write, Bash

**Skill Implementation** (`/stock-moat`):
- **Type**: User-invocable skill
- **Commands**:
  - `analyze {ticker}` - Single stock analysis
  - `batch --all` - Process all incomplete stocks
  - `batch --range {start}-{end}` - Process range (e.g., rows 1-50)
  - `verify {ticker}` - Re-verify moat ≥4 stock
  - `report` - Generate completion report

**Data Processing**:
- **Language**: Python 3.11+
- **Libraries**: pandas, openpyxl (Excel I/O)
- **Optional MCP**: If Excel operations become token-heavy

### Research Workflow (Per Stock)

```
1. Load Stock Data
   ↓
2. Identify Core Business (본업)
   - Fetch DART 사업보고서 (business description)
   - Extract main revenue sources
   - Map to core_sector_top (229 categories)
   - Determine core_sector_sub (subcategory)
   ↓
3. Analyze Moat Strength
   - Evaluate 5 moat categories
   - Score each category (1-5)
   - Calculate total moat strength
   - Generate 해자DESC (breakdown)
   ↓
4. Verification (if moat ≥ 4)
   - Re-research with deeper sources
   - Cross-validate competitive position
   - Document in 검증용desc
   ↓
5. Write Results to Excel
   - Update row atomically
   - Log completion status
```

### Batch Processing Strategy

**Priority Tiers** (process in order):
1. **Tier 1**: Stocks with ticker + name only (196 stocks)
2. **Tier 2**: Stocks with partial data (verification needed)
3. **Tier 3**: High-moat stocks (≥4) requiring re-verification

**Parallel Processing**:
- Process 5 stocks concurrently (balance speed/quality)
- Implement retry logic for API failures
- Checkpoint progress every 10 stocks

---

## 6. Risks & Mitigation

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| DART/KIND API rate limits | High | Medium | Implement exponential backoff, cache responses |
| Insufficient disclosure data | Medium | High | Fallback to IR pages, news articles, expert judgment |
| Incorrect sector classification | High | Medium | Human review of sample (20 stocks), feedback loop |
| Token usage exceeds budget | Medium | Medium | Use Haiku for simple tasks, cache common queries |
| Excel file corruption during writes | High | Low | Atomic writes, backup file before processing |

### Data Quality Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Inconsistent moat scoring | High | Medium | Detailed rubric, agent memory with examples |
| Moat ≥4 stocks over-estimated | High | Medium | Mandatory re-verification workflow |
| Sector taxonomy mismatch | Medium | Low | Strict validation against 229 approved names |
| Subjective analysis variation | Medium | High | Use structured prompts, cite sources |

### Process Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Batch processing interrupted | Medium | Medium | Checkpoint every 10 stocks, resume capability |
| Agent hallucination (fabricated data) | High | Low | Require source citations, human spot-check |
| Scope creep (adding features) | Low | High | Strict PDCA adherence, defer extras to future |

---

## 7. Dependencies

### Internal Dependencies

- ✅ Excel file with stock list (stock_core_master_v2_korean_taxonomy_2026-01-30_요청용_011.xlsx)
- ✅ Sector taxonomy (분류유형(참고) sheet, 229 categories)
- ✅ Schema documentation (schema sheet)
- [ ] bkit Agent framework setup (agent definition)
- [ ] `/stock-moat` skill implementation
- [ ] Agent memory directory structure

### External Dependencies

- **Data Sources**:
  - DART OpenAPI (금융감독원 전자공시시스템)
  - KIND (한국거래소 기업정보)
  - Company IR pages (investor relations)
  - Naver Finance, 증권보고서

- **Libraries** (Python):
  - `pandas` ✅ (already installed)
  - `openpyxl` ✅ (already installed)
  - `requests` ✅ (HTTP requests)

### Team Dependencies

- **None** (fully automated agent-driven process)
- Human review recommended for quality assurance (20-stock sample)

---

## 8. Timeline & Milestones

### Overall Timeline: 3-5 days (development) + 2-3 days (batch execution)

| Phase | Duration | Start Date | Target Completion |
|-------|----------|------------|-------------------|
| Phase 1: Agent & Skill Setup | 1 day | 2026-02-09 | 2026-02-09 |
| Phase 2: Schema & Taxonomy | 0.5 day | 2026-02-09 | 2026-02-09 |
| Phase 3: Workflow Design | 0.5 day | 2026-02-09 | 2026-02-10 |
| Phase 4: Core Implementation | 2 days | 2026-02-10 | 2026-02-12 |
| Phase 5: Export & Validation | 0.5 day | 2026-02-12 | 2026-02-12 |
| Phase 6: MCP Evaluation | 0.5 day | 2026-02-12 | 2026-02-13 (optional) |
| **Batch Execution** | 2-3 days | 2026-02-13 | 2026-02-16 |

### Key Milestones

- **M1**: Agent definition complete, skill registered (2026-02-09)
- **M2**: Moat analysis framework documented, rubric finalized (2026-02-10)
- **M3**: Single-stock analysis workflow validated (2026-02-11)
- **M4**: Batch processing tested (10 stocks) (2026-02-12)
- **M5**: All 196 stocks analyzed, Excel updated (2026-02-16)
- **M6**: Quality review passed (90% accuracy), PDCA report generated (2026-02-17)

---

## 9. Stakeholders

### Primary Stakeholders

- **Product Owner**: Stock Research ONE project lead
- **Investment Analyst**: Uses moat data for stock selection decisions
- **Data Manager**: Maintains stock_core_master database

### Secondary Stakeholders

- **Future Analysts**: Will use `/stock-moat` skill for new stocks
- **System Architect**: May integrate moat scores into investment algorithms

---

## 10. Next Steps

### Immediate Actions (After Plan Approval)

1. **Approve This Plan**
   - Review objectives, scope, success criteria
   - Confirm moat analysis framework is appropriate
   - Verify timeline is acceptable

2. **Create Design Document**
   ```bash
   /pdca design stock-moat-estimator
   ```

3. **Set Up Agent Infrastructure**
   - Create `.agent/agents/stock-moat-estimator/` directory
   - Define agent specification (capabilities, knowledge, model)
   - Set up agent memory structure

4. **Prepare Development Environment**
   - Verify Excel file location and permissions
   - Test pandas/openpyxl read/write operations
   - Prepare sample stock data (5-10 stocks) for testing

### Decision Points

- [ ] Approve plan document
- [ ] Confirm moat scoring rubric (1-5 scale with 5 categories)
- [ ] MCP server: Build now or defer? (Recommend: defer unless Excel I/O is slow)
- [ ] Batch size: Process all 196 at once or in batches? (Recommend: batches of 50)
- [ ] Human review: Spot-check 10%, 20%, or 100% of results? (Recommend: 20%)

---

## 11. References

### Project Documentation

- **Excel File**: `F:\PSJ\AntigravityWorkPlace\Stock\Test_02\data\ask\stock_core_master_v2_korean_taxonomy_2026-01-30_요청용_011.xlsx`
  - Sheet: `TODO` (requirements)
  - Sheet: `stock_core_master` (208 stocks)
  - Sheet: `schema` (field definitions)
  - Sheet: `분류유형(참고)` (229 sector categories)

- **Project Files**:
  - `CLAUDE.md` - Project guidance
  - `docs/investment-philosophy.md` - Investment strategy (7-step flywheel)
  - `AGENTS.md` - Agent management policy

### External References

- **DART (전자공시시스템)**: https://dart.fss.or.kr/
- **KIND (한국거래소 기업정보)**: http://kind.krx.co.kr/
- **Moat Analysis Framework**:
  - Morningstar Economic Moat Rating methodology
  - Warren Buffett's moat concept (competitive advantages)

### bkit Documentation

- **Agent Framework**: `.agent/` directory structure
- **Skill System**: User-invocable skills (`/stock-moat`)
- **PDCA Workflow**: Plan → Design → Do → Check → Act
- **Agent Memory**: Persistent learning across sessions

---

## 12. Appendix

### A. Moat Scoring Examples

**Example 1: 삼성전자 (Samsung Electronics)**
```
해자강도: 5
해자DESC:
브랜드 파워: 5/5 (글로벌 톱티어 브랜드)
원가 우위: 5/5 (초대규모 반도체 fab, 수직계열화)
네트워크 효과: 3/5 (갤럭시 생태계)
전환 비용: 4/5 (B2B 고객 기술 의존성)
규제/허가: 3/5 (일반 산업재)
---
총점: 20/25 → 해자강도 5
검증용desc: 반도체 파운드리 시장 점유율 2위(18%), 메모리 1위(40%).
CAPEX 50조원/년으로 진입장벽 극도로 높음. 증권보고서(2025) 확인.
```

**Example 2: 중소형 게임사 (Small Game Company)**
```
해자강도: 2
해자DESC:
브랜드 파워: 2/5 (일부 게임 IP 보유하나 인지도 제한적)
원가 우위: 1/5 (외주 개발 의존)
네트워크 효과: 3/5 (온라인 게임 유저 커뮤니티)
전환 비용: 1/5 (게임 이탈 쉬움)
규제/허가: 2/5 (등급심의만 필요)
---
총점: 9/25 → 해자강도 2
```

### B. Sector Classification Examples

| Stock | core_sector_top | core_sector_sub |
|-------|----------------|----------------|
| 알톤 | 게임 | 모바일 게임/PC게임 |
| 티쓰리 | 게임 | 모바일 RPG |
| 네오위즈 | 게임 | 온라인 게임/퍼블리싱 |
| 삼성전자 | 반도체 | 메모리/시스템반도체 |
| 현대자동차 | 자동차완성품 | 승용차/SUV |

### C. Agent Memory Structure

```
.agent/memory/stock-moat-estimator/
├── sector_patterns.md          # Industry-specific moat patterns
├── moat_examples.md            # Reference analyses for learning
├── error_corrections.md        # Quality improvements over time
└── research_sources.md         # Reliable data sources catalog
```

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 2026-02-09 | Claude Sonnet 4.5 | Initial plan document created |
| 2026-02-09 | Claude Sonnet 4.5 | Added moat framework, batch strategy, examples |

