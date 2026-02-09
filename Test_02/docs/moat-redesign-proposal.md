# 해자 평가 시스템 재설계안 - 증거 기반 접근

> **작성일**: 2026-02-10
> **기반**: 전문가 MGB-MOAT 방법론
> **핵심**: 증거 없으면 평가 안 함 (특히 3점 이상)

---

## 1. 전문가 방법론 vs 현재 시스템

### 1.1 핵심 차이

| 단계 | 전문가 방법론 | 현재 시스템 | Gap |
|------|--------------|------------|-----|
| **Step B: 사실 수집** | 공시/IR 우선 분석 | KSIC 코드만 조회 | ❌ 99% 누락 |
| **Step C: BM 분해** | 6요소 기계적 분해 | 완전 생략 | ❌ 100% 누락 |
| **Step D: 해자 평가** | 증거 문장 → 점수 | 섹터 평균값 적용 | ❌ 증거 0% |
| **Step E: 지속가능성** | 산업구조 + 트렌드 | 완전 생략 | ❌ 100% 누락 |

### 1.2 전문가 방법론 상세

#### Step B. 1차 사실 수집 (공시/IR 우선)

**확인 항목**:
```
✓ 사업부문/매출 구성
✓ 주요 고객/채널
✓ CAPEX (설비 투자)
✓ 생산거점
✓ 라이선스/특허
✓ 최근 실적/가이던스/리스크 공시
✓ 경쟁사/대체재/산업 밸류체인
```

**원칙**:
> "해자 3점 이상은 공시/IR 등 신뢰자료 기반 문장 없으면 기록하지 않음 (특히 4+ 금지)"

#### Step C. BM(사업모델) "기계적으로 분해"

**6요소 고정 프레임워크**:
```
1. 고객은 누구인가
2. 무엇으로 돈을 버는가 (단가 × 물량 × 반복성)
3. 왜 이 회사인가 (차별 포인트)
4. 비용 구조/레버리지 (고정비/변동비)
5. 성장이 되는 조건 (수요/공급/규제/전환비용)
6. 망하는 조건 (가격경쟁/기술변화/수요 붕괴)
```

→ 각 요소를 **확인/추정 라벨**과 함께 기록

#### Step D. 해자 평가 (MGB-MOAT Index) - "증거 기반"

**프로세스**:
```
증거 문장 추출
  ↓
해자 유형 판단
  ↓
점수 부여 (증거 강도 기반)
```

**해자 유형 (예시)**:
- 전환비용
- 네트워크 효과
- 규모의 경제
- 브랜드
- 규제/허가
- 데이터/학습
- 특허/공정
- 공급망/설치기반
- 락인/표준
- 원가우위

**점수 규칙 (핵심)**:
```
1-2점: 해자 없음 or 약함 (증거 불필요)
3점: 공시/IR/신뢰자료로 "왜 해자인지" 문장 확인 필수
4+점: 추가 검증 (반증 체크 포함) + 검증용 desc 필수
```

#### Step E. "산업구조 + 트렌드"로 지속가능성 검증

**3가지 체크**:
```
1. 구조적 성장인지 (중장기 수요 ↑)
2. 경쟁의 축이 바뀌는지 (기술/규제/원가/표준)
3. 해자 유지비용이 과도한지 (도입 느림, 노동집약 모니터링)
```

---

## 2. 재설계안: 3단계 접근

### Phase 1: 기초 인프라 (2-3주)

**목표**: DART 데이터 완전 활용 + 증거 문장 추출

#### 1.1 DART 데이터 확장

**현재**:
```python
DART → induty_code (KSIC) only
```

**개선**:
```python
DART API 확장:
  1. 사업의 내용 (사업보고서 본문)
  2. 재무제표 (매출/영업이익/자산/부채)
  3. 사업부문별 매출 구성
  4. 주요 고객 (매출 집중도)
  5. 주요 원재료 및 생산설비
  6. 연구개발 활동 / 특허
  7. 산업 특성 / 경쟁 현황
```

**구현**:
```python
# dart_client.py 확장
def get_business_report_sections(self, corp_code: str, year: str = "2023"):
    """사업보고서 주요 섹션 추출"""
    return {
        'business_content': "...",      # 사업의 내용
        'revenue_breakdown': {...},      # 사업부문별 매출
        'major_customers': [...],        # 주요 고객
        'facilities': "...",             # 생산설비
        'rnd_patents': "...",            # 연구개발/특허
        'industry_competition': "...",   # 산업/경쟁
        'financials': {                  # 재무제표
            'revenue': ...,
            'operating_income': ...,
            'assets': ...,
            'liabilities': ...,
            'roe': ...,
            'operating_margin': ...
        }
    }
```

#### 1.2 증거 문장 추출 엔진

**목적**: 공시 본문에서 해자 관련 증거 추출

**구현 방식 A: Rule-based (빠르지만 제한적)**
```python
# evidence_extractor.py
class EvidenceExtractor:
    def __init__(self):
        self.patterns = {
            '전환비용': [
                r'고객사.*통합',
                r'전환.*비용',
                r'장기.*계약',
                r'인증.*요구'
            ],
            '네트워크 효과': [
                r'사용자.*증가',
                r'플랫폼.*효과',
                r'커뮤니티'
            ],
            '규모의 경제': [
                r'생산량.*증가',
                r'고정비.*분산',
                r'CAPEX.*규모'
            ],
            # ... 각 해자 유형별 패턴
        }

    def extract_evidence(self, text: str) -> List[Dict]:
        """
        Returns: [
            {
                'moat_type': '전환비용',
                'evidence': "고객사와의 시스템 통합...",
                'confidence': 0.8,
                'source': 'section_name'
            }
        ]
        """
```

**구현 방식 B: LLM-based (느리지만 정확)**
```python
# llm_evidence_extractor.py
def extract_evidence_with_llm(business_report: str, company_name: str):
    """
    LLM Prompt:
    "다음 사업보고서에서 {company_name}의 경쟁우위(해자)를 나타내는
    구체적인 증거 문장을 추출하세요.

    해자 유형: 전환비용, 네트워크 효과, 규모의 경제, 브랜드, 규제/허가...

    각 증거는 반드시:
    1. 구체적 수치 or 사실 포함
    2. 경쟁우위 논리 명확
    3. 지속 가능성 언급

    Output JSON:
    {
        'moat_type': '...',
        'evidence': '원문 그대로 인용',
        'reasoning': '왜 이것이 해자인지 설명',
        'score_suggestion': 1-5
    }
    """
```

**추천**: **Phase 1에서는 A (Rule-based)**, Phase 2에서 B 추가

#### 1.3 BM 분해 자동화

**6요소 질문 → DART 데이터 매핑**

```python
# bm_analyzer.py
class BusinessModelAnalyzer:
    def analyze(self, dart_data: Dict) -> Dict:
        """
        Returns:
        {
            'customer': {
                'answer': "...",
                'confidence': 'confirmed' | 'estimated',
                'source': '사업보고서 p.X'
            },
            'revenue_model': {
                'answer': "...",
                'unit_price': ...,
                'volume': ...,
                'recurring': True/False
            },
            'differentiation': {...},
            'cost_structure': {...},
            'growth_condition': {...},
            'failure_condition': {...}
        }
        """

        # 1. 고객은 누구인가
        customer = self._extract_customer(
            dart_data['business_content'],
            dart_data['major_customers']
        )

        # 2. 무엇으로 돈을 버는가
        revenue_model = self._extract_revenue_model(
            dart_data['revenue_breakdown'],
            dart_data['financials']
        )

        # ... 6요소 모두 분석

        return bm_analysis
```

### Phase 2: 증거 기반 평가 (2-3주)

**목표**: 3점 이상 = 증거 필수 규칙 구현

#### 2.1 새로운 평가 로직

```python
# moat_evaluator_v2.py
class MoatEvaluatorV2:
    def evaluate_moat(
        self,
        company_name: str,
        dart_data: Dict,
        bm_analysis: Dict,
        evidence_list: List[Dict]
    ) -> Dict:
        """
        증거 기반 해자 평가
        """

        moat_scores = {
            '전환비용': 0,
            '네트워크 효과': 0,
            '규모의 경제': 0,
            '브랜드': 0,
            '규제/허가': 0
        }

        evidence_by_type = {}

        for moat_type in moat_scores.keys():
            # 1. 해당 유형의 증거 수집
            evidences = [e for e in evidence_list if e['moat_type'] == moat_type]

            if not evidences:
                # 증거 없음 → 기본값 1-2
                moat_scores[moat_type] = self._get_baseline_score(
                    moat_type,
                    bm_analysis
                )
                evidence_by_type[moat_type] = "증거 없음 (기본값)"
            else:
                # 증거 있음 → 증거 강도 기반 점수
                score, reasoning = self._score_with_evidence(
                    moat_type,
                    evidences,
                    dart_data
                )
                moat_scores[moat_type] = score
                evidence_by_type[moat_type] = reasoning

        # 2. 최종 해자강도 (평균)
        total = sum(moat_scores.values())
        moat_strength = round(total / 5)

        # 3. 증거 검증 (3점 이상)
        if moat_strength >= 3:
            validation = self._validate_high_score(
                moat_strength,
                evidence_by_type,
                dart_data
            )
            if not validation['passed']:
                # 증거 불충분 → 하향 조정
                moat_strength = 2
                evidence_by_type['_validation_note'] = validation['reason']

        return {
            'moat_strength': moat_strength,
            'scores_by_type': moat_scores,
            'evidence_by_type': evidence_by_type,
            'total': total
        }

    def _score_with_evidence(
        self,
        moat_type: str,
        evidences: List[Dict],
        dart_data: Dict
    ) -> Tuple[int, str]:
        """
        증거 강도에 따른 점수 부여

        1점: 증거 없음 (기본값)
        2점: 약한 증거 (추정/일반적 진술)
        3점: 강한 증거 (구체적 수치/사실, 공시 확인)
        4점: 매우 강한 증거 (3점 + 경쟁사 대비 우위 명확)
        5점: 구조적 해자 (4점 + 지속가능성 검증)
        """

        # 증거 품질 평가
        quality_score = 0
        reasoning_parts = []

        for evidence in evidences:
            # 구체성 체크
            has_numbers = bool(re.search(r'\d+%|\d+억|\d+명', evidence['evidence']))
            has_facts = len(evidence['evidence']) > 50  # 충분한 설명

            if has_numbers and has_facts:
                quality_score += 1.5
                reasoning_parts.append(f"✓ {evidence['evidence'][:100]}...")
            elif has_facts:
                quality_score += 1.0
                reasoning_parts.append(f"△ {evidence['evidence'][:100]}...")
            else:
                quality_score += 0.5

        # 점수 변환
        if quality_score >= 3.0:
            score = 4  # 매우 강한 증거
        elif quality_score >= 2.0:
            score = 3  # 강한 증거
        elif quality_score >= 1.0:
            score = 2  # 약한 증거
        else:
            score = 1  # 증거 불충분

        reasoning = f"{moat_type} ({score}점):\n" + "\n".join(reasoning_parts)

        return score, reasoning
```

#### 2.2 검증용 DESC 생성

```python
def generate_verification_desc(
    self,
    company_name: str,
    moat_strength: int,
    evidence_by_type: Dict,
    dart_data: Dict
) -> str:
    """
    4점 이상일 때 필수 검증용 설명
    """

    if moat_strength < 4:
        return ""

    desc = f"""
[검증용 DESC - {company_name} 해자강도 {moat_strength}]

1. 주요 증거:
{self._format_evidence(evidence_by_type)}

2. 경쟁사 대비 우위:
{self._compare_with_competitors(dart_data)}

3. 지속가능성:
{self._assess_sustainability(dart_data)}

4. 반증 체크:
{self._check_counterevidence(dart_data)}

[검증 필요 항목]
□ 전문가 리뷰 완료
□ 경쟁사 비교 완료
□ 산업 트렌드 체크 완료
"""

    return desc
```

### Phase 3: 지속가능성 검증 (1-2주)

**목표**: Step E 구현 (산업구조 + 트렌드)

#### 3.1 산업 분석 데이터 소스

**옵션 A: DART 산업 분석 섹션**
- 사업보고서 "산업의 특성" 섹션
- "경쟁 현황" 섹션
- 자동 추출 가능

**옵션 B: 외부 데이터**
- 한국은행 산업 통계
- 통계청 산업 동향
- 업종별 협회 자료

**옵션 C: LLM 분석**
- GPT-4o 등으로 산업 보고서 분석
- 트렌드 요약

#### 3.2 지속가능성 체크리스트

```python
# sustainability_checker.py
class SustainabilityChecker:
    def check(self, company_name: str, dart_data: Dict, moat_strength: int):
        """
        3가지 체크:
        1. 구조적 성장인지
        2. 경쟁의 축이 바뀌는지
        3. 해자 유지비용이 과도한지
        """

        checks = {
            'structural_growth': self._check_demand_growth(dart_data),
            'competition_shift': self._check_competition_change(dart_data),
            'maintenance_cost': self._check_moat_maintenance(dart_data)
        }

        # 경고 발생 조건
        warnings = []
        if not checks['structural_growth']['positive']:
            warnings.append(f"⚠️ 수요 성장 둔화: {checks['structural_growth']['reason']}")

        if checks['competition_shift']['risk'] == 'high':
            warnings.append(f"⚠️ 경쟁 축 변화: {checks['competition_shift']['reason']}")

        # 해자강도 조정
        adjusted_strength = moat_strength
        if len(warnings) >= 2:
            adjusted_strength = max(moat_strength - 1, 1)
            warnings.append(f"→ 해자강도 {moat_strength} → {adjusted_strength} 하향")

        return {
            'original_strength': moat_strength,
            'adjusted_strength': adjusted_strength,
            'checks': checks,
            'warnings': warnings
        }
```

---

## 3. 구현 우선순위

### 즉시 (1-2일): 치명적 버그 수정

```
✓ KSIC 매핑 수정 (건설업 추가)
✓ Fallback '4' 수정: IT → Industrials
✓ 강제 조정 로직 제거
✓ IT Services moat pattern 추가
```

→ **목표**: 오분류 제거, 현재 시스템 최소 동작

### Phase 1 (2-3주): DART 데이터 완전 활용

```
✓ dart_client.py 확장 (사업보고서 섹션 추출)
✓ 재무 데이터 통합
✓ evidence_extractor.py (Rule-based)
✓ bm_analyzer.py (6요소 분해)
✓ core_desc에 실제 사업 설명 추가
```

→ **목표**: 증거 문장 수집 자동화

### Phase 2 (2-3주): 증거 기반 평가

```
✓ moat_evaluator_v2.py (증거 기반 점수)
✓ 3점 이상 = 증거 필수 로직
✓ 4점 이상 = 검증용 desc 생성
✓ 회사별 차별화 반영
```

→ **목표**: "증거 없으면 평가 안 함" 구현

### Phase 3 (1-2주): 지속가능성 검증

```
✓ sustainability_checker.py
✓ 산업 분석 데이터 통합
✓ 경고 시스템
✓ 해자강도 조정 로직
```

→ **목표**: Step E 완성

---

## 4. 남광토건 재평가 (Phase 1-2 적용 후)

### Step B: 사실 수집 (DART)

```
사업부문: 건축공사 60%, 토목공사 30%, 기타 10%
주요 고객: 공공기관 40%, 민간 60%
CAPEX: 낮음 (건설업은 자산 경량)
생산거점: N/A (건설은 프로젝트별)
특허: 없음
최근 실적: 매출 1,200억, 영업이익률 3%
경쟁사: 중견 건설사 100개 이상
```

### Step C: BM 분해

```
1. 고객: 공공기관 + 민간 발주처
2. 돈 버는 방법: 프로젝트별 계약 (단가×물량, 반복성 낮음)
3. 왜 이 회사: 특별한 차별점 없음 (가격 경쟁)
4. 비용 구조: 변동비 높음 (자재, 인건비)
5. 성장 조건: 건설 경기 회복, 수주 증가
6. 망하는 조건: 부실 시공, 자금 유동성 악화
```

### Step D: 해자 평가 (증거 기반)

```
전환비용: 1점 (증거 없음, 발주처가 자유롭게 업체 선택)
네트워크 효과: 1점 (건설은 네트워크 효과 없음)
규모의 경제: 2점 (중견사, 일부 원가 우위 가능)
브랜드: 1점 (중소 건설사, 브랜드 파워 약함)
규제/허가: 2점 (건설업 면허 있으나 진입장벽 낮음)

총점: 7/25 → 해자강도 1-2
```

### Step E: 지속가능성

```
구조적 성장: △ (건설 경기 순환적)
경쟁 축 변화: ✓ (큰 변화 없음)
유지비용: ✓ (과도하지 않음)

최종: 해자강도 1-2 유지
```

---

## 5. 예상 산출물

### 5.1 개선된 core_desc

**현재**:
```
남광토건 - GICS: Information Technology - IT Services (KSIC 41221, 대분류 추정)
```

**Phase 1 후**:
```
남광토건 (001260) - 건설업

[사업 내용]
주택, 상업시설 및 토목 건설을 영위하는 중견 건설사.
주요 사업: 건축공사 60% (아파트, 오피스텔), 토목공사 30%, 기타 10%

[재무 현황]
매출: 1,200억원 (2023년)
영업이익률: 3.2%
자산: 800억원

[경쟁 환경]
중견 건설사 100개 이상 경쟁, 가격 경쟁 치열
특별한 차별화 요인 없음

[출처: DART 사업보고서 2023]
```

### 5.2 개선된 해자DESC

**현재**:
```
브랜드 파워: 2/5
원가 우위: 2/5
네트워크 효과: 1/5
전환 비용: 2/5
규제/허가: 2/5
---
총점: 9/25 → 해자강도 5 (???)
[출처: GICS_fallback]
```

**Phase 2 후**:
```
해자강도: 2/5 (약한 해자)

[증거 기반 평가]

전환비용 (1점):
❌ 증거 없음
발주처가 프로젝트별로 자유롭게 업체 선택 가능.
장기 계약이나 시스템 통합 등 전환비용 요인 없음.

네트워크 효과 (1점):
❌ 증거 없음
건설업은 네트워크 효과가 발생하지 않는 산업.

규모의 경제 (2점):
△ 약한 증거
중견 건설사 규모로 일부 원가 우위 가능하나,
대형사 대비 경쟁력 제한적.

브랜드 (1점):
❌ 증거 없음
중소 규모, 브랜드 인지도 낮음.

규제/허가 (2점):
✓ 기본 증거
건설업 면허 보유하나 진입장벽 낮음.
중견 건설사 100개 이상 유사 면허 보유.

---
총점: 7/25 → 해자강도 1.4 → 2/5

[지속가능성]
⚠️ 건설 경기 순환적, 구조적 성장 제한
✓ 경쟁 축 큰 변화 없음
✓ 해자 유지비용 과도하지 않음

[출처: DART 사업보고서 2023, 증거 기반 평가]
```

---

## 6. 구현 로드맵

### Week 1-2: 즉시 수정 + Phase 1 시작

```
Day 1-2:  KSIC 매핑 수정, 버그 수정
Day 3-7:  dart_client.py 확장 (사업보고서 API)
Day 8-10: evidence_extractor.py (Rule-based)
Day 11-14: bm_analyzer.py (6요소 분해)
```

**Milestone 1**: 남광토건 재평가 → 올바른 분류 + 사업 설명

### Week 3-4: Phase 2 (증거 기반 평가)

```
Day 15-18: moat_evaluator_v2.py 구현
Day 19-21: 3점 이상 증거 검증 로직
Day 22-24: 검증용 desc 생성
Day 25-28: 208개 샘플 재평가 + 검증
```

**Milestone 2**: 208개 종목 증거 기반 재평가

### Week 5-6: Phase 3 (지속가능성) + 전체 재분석

```
Day 29-32: sustainability_checker.py
Day 33-35: 산업 분석 통합
Day 36-40: 1561개 종목 전체 재분석
Day 41-42: 전문가 리뷰 (샘플 20개)
```

**Milestone 3**: 전체 시스템 완성 + 검증

---

## 7. 성공 기준

### 정량 지표

| 지표 | 현재 | 목표 (Phase 1) | 목표 (Phase 2) | 목표 (Phase 3) |
|------|------|---------------|---------------|---------------|
| **분류 정확도** | 94.9% | 98%+ | 98%+ | 98%+ |
| **사업 설명 있음** | 0% | 90%+ | 95%+ | 95%+ |
| **증거 기반 평가 (3점+)** | 0% | N/A | 80%+ | 90%+ |
| **해자강도 = 섹터 평균** | 90%+ | 70% | 30% | 10% |
| **전문가 리뷰 일치율** | ??? | 60%+ | 75%+ | 85%+ |

### 정성 평가

**Phase 1 후**:
- ✓ "이 회사가 무엇을 하는지" 알 수 있음
- ✓ 재무 상태 파악 가능
- ✓ 분류 오류 90% 이상 해결

**Phase 2 후**:
- ✓ "왜 이 해자 점수인지" 설명 가능
- ✓ 증거 문장으로 뒷받침
- ✓ 회사별 차별화 반영

**Phase 3 후**:
- ✓ 지속가능성 경고 시스템
- ✓ 전문가 리뷰 80%+ 일치
- ✓ 투자 의사결정 보조 가능

---

## 8. 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|------|------|
| **DART API 제한** | 사업보고서 전문 조회 시 느림 | 캐싱 + 점진적 수집 |
| **증거 추출 정확도 낮음** | 잘못된 증거 → 잘못된 점수 | 사람 검증 루프 추가 |
| **LLM 비용** | GPT-4o 사용 시 고비용 | Rule-based 우선, LLM은 선택적 |
| **개발 기간 지연** | 6주 → 8주+ | Phase별 독립 배포 |
| **전문가 리뷰 리소스** | 1561개 전체 검증 불가 | 샘플링 (10%) + 이슈 중심 |

---

## 9. 결론

### 핵심 변화

**Before (현재)**:
```
KSIC 코드 → 섹터 평균값 → 끝
```

**After (Phase 1-3)**:
```
DART 공시 → BM 분해 → 증거 추출 → 증거 기반 점수 → 지속가능성 검증 → 최종 평가
```

### 투자 대비 효과

| 투자 | 효과 |
|------|------|
| **6주 개발** | 증거 기반 해자 평가 시스템 |
| **전문가 리뷰 (샘플)** | 85%+ 일치율 목표 |
| **자동화율** | 90%+ (사람은 검증만) |

### 다음 단계

1. ✅ **승인**: 이 재설계안 승인
2. ✅ **리소스 확보**: 개발 시간, 전문가 리뷰
3. ✅ **Phase 1 착수**: 즉시 수정 + DART 확장

**의사결정 필요**: 이 방향으로 진행할까요?
