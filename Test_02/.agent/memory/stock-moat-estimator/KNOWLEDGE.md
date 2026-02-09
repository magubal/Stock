# Stock Moat Estimator - Knowledge Base

## Data Sources (Priority Order)

### 1. DART (금융감독원 전자공시시스템)
- **URL**: https://dart.fss.or.kr/
- **API**: https://opendart.fss.or.kr/
- **Key Data**: 사업보고서, 분기보고서, 공시자료
- **Best For**: Core business description, revenue breakdown

### 2. KIND (한국거래소 기업정보)
- **URL**: http://kind.krx.co.kr/
- **Key Data**: 기업개요, 업종 분류, 재무정보
- **Best For**: Sector classification, company overview

### 3. Company IR Pages
- **Access**: Company websites (/ir/, /investor/)
- **Key Data**: 투자자 정보, 사업 소개
- **Best For**: Recent updates, strategic direction

### 4. 증권보고서
- **Access**: DART, securities firms
- **Key Data**: 상세 재무/사업 분석
- **Best For**: Deep competitive analysis

---

## Moat Framework (5 Categories)

### 브랜드 파워 (Brand Power)
**Indicators**:
- 브랜드 가치 평가 (Interbrand, Brand Finance)
- 소비자 인지도 (Top-of-Mind awareness)
- 프리미엄 가격 능력 (Price premium vs competitors)
- 시장 점유율 (Market share in brand-sensitive segments)

**Examples**:
- Score 5: 삼성전자 (글로벌 브랜드 인지도)
- Score 3: 중견 브랜드 (일부 인지도)
- Score 1: 2차전지 소재 (브랜드 무관)

---

### 원가 우위 (Cost Advantage)
**Indicators**:
- COGS / Revenue ratio (vs industry average)
- Gross margin (vs competitors)
- CAPEX 규모 (진입장벽)
- 생산능력 순위 (Capacity ranking)

**Examples**:
- Score 5: 삼성전자 파운드리 (CAPEX 50조/년)
- Score 3: 중견 제조업 (중규모 시설)
- Score 1: 유통업 (외주 의존)

---

### 네트워크 효과 (Network Effects)
**Indicators**:
- MAU (Monthly Active Users) growth
- Network density (사용자당 연결 수)
- Multi-homing cost (타 플랫폼 병행 사용 비용)
- Platform dynamics (양면시장 여부)

**Examples**:
- Score 5: 카카오톡 (사용자↑ = 가치↑)
- Score 3: 온라인 커뮤니티 (일부 효과)
- Score 1: 제조업 (효과 없음)

---

### 전환 비용 (Switching Costs)
**Indicators**:
- 평균 계약 기간 (B2B contracts)
- Churn rate (이탈률)
- Integration complexity (시스템 연동)
- Data migration cost

**Examples**:
- Score 5: ERP 솔루션 (시스템 의존)
- Score 3: 보험, 통신 (중간 전환 비용)
- Score 1: 소비재 (전환 쉬움)

---

### 규제/허가 (Regulatory Moat)
**Indicators**:
- 허가/라이선스 취득 기간
- 규제 기관 수
- 신규 진입자 수 (최근 3년)
- 독점 여부

**Examples**:
- Score 5: 의약품, 카지노 (독점 라이선스)
- Score 3: 건설, 에너지 (일부 규제)
- Score 1: IT 서비스 (장벽 없음)

---

## Sector Taxonomy Rules

### Critical Rules
1. **ONLY use Korean names** from the approved 229 categories
2. **NO English names** in `core_sector_top`
3. Format: `core_sector_sub` = "category/subcategory"

### Common Mappings
| Business Description | core_sector_top | core_sector_sub |
|---------------------|-----------------|-----------------|
| 메모리 반도체 제조 | 반도체 | 메모리/시스템반도체 |
| 모바일 게임 개발 | 게임 | 모바일 게임/PC게임 |
| 승용차 제조 | 자동차완성품 | 승용차/SUV |
| 온라인 플랫폼 | 플랫폼 | 전자상거래/포털 |

### 229 Sector Categories (Loaded from Excel)
Refer to `분류유형(참고)` sheet in Excel file for full list.

---

## Moat Scoring Examples

### Example 1: 삼성전자 (High Moat)
```
브랜드 파워: 5/5 (글로벌 톱티어 브랜드)
원가 우위: 5/5 (초대규모 fab, 수직계열화)
네트워크 효과: 3/5 (갤럭시 생태계, 제한적)
전환 비용: 4/5 (B2B 기술 의존성)
규제/허가: 3/5 (일반 산업재)
---
총점: 20/25 → 해자강도 4
```

### Example 2: 중소형 게임사 (Low Moat)
```
브랜드 파워: 2/5 (일부 IP 보유)
원가 우위: 1/5 (외주 개발)
네트워크 효과: 3/5 (유저 커뮤니티)
전환 비용: 1/5 (이탈 쉬움)
규제/허가: 2/5 (등급심의만 필요)
---
총점: 9/25 → 해자강도 2
```

---

## Quality Checklist

Before finalizing analysis:
- [ ] Source cited (DART/KIND/IR)
- [ ] Sector matches 229 taxonomy (Korean only)
- [ ] Moat scores justified with evidence
- [ ] If moat ≥ 4: Re-verification completed
- [ ] Output format correct (해자DESC structure)

---

## Learning Log

Record insights as you analyze stocks:
- Industry-specific patterns → `sector_patterns.md`
- Exemplary analyses → `moat_examples.md`
- Errors and corrections → `error_corrections.md`
