# 해자(Moat) 평가 시스템 - 현황 분석 및 근본적 재검토

> **작성일**: 2026-02-10
> **목적**: 개발 중단 후 해자 평가 기준의 근본적 재정의
> **문제 발견**: 남광토건 사례 (건설업 → IT 오분류, 해자 2 → 5 오평가)

---

## 1. 현재 시스템 작동 방식

### 1.1 전체 프로세스 (analyze_stock)

```
입력: ticker, name
  ↓
① DART API → KSIC 업종코드 조회
  ↓
② KSIC → GICS 매핑 (ksic_to_gics_mapper.py)
  ↓
③ 회사명 기반 특성 추출
   - has_strong_brand: ['삼성', '현대', '네이버', '카카오', 'LG', 'SK'] 포함 여부
   - company_size: 'large' if has_strong_brand else 'medium'
  ↓
④ 해자 평가 (evaluate_moat)
   - 5가지 차원 점수 계산
   - GICS typical_strength와 비교 조정
  ↓
⑤ 출력: core_sector, 해자강도, 해자DESC
```

### 1.2 해자 평가 5가지 차원

**Morningstar Economic Moat 프레임워크 기반**:

1. **브랜드 파워** (Brand Power)
   - 소비자 인지도, 충성도, 프리미엄 가격 책정력

2. **원가 우위** (Cost Advantage)
   - 규모의 경제, 독점적 자원, 생산 효율성

3. **네트워크 효과** (Network Effect)
   - 사용자 증가 → 가치 증가 (플랫폼, SNS)

4. **전환 비용** (Switching Costs)
   - 고객이 다른 제품으로 바꾸기 어려운 정도

5. **규제/허가** (Regulatory/Licenses)
   - 진입 장벽, 정부 인허가, 특허

---

## 2. 현재 평가 로직 상세

### 2.1 Sector별 기본 패턴 (industry_patterns)

```python
self.industry_patterns = {
    '게임': {
        'typical_moat': 2,
        'brand': (2, 3),        # 범위: 최소~최대
        'cost': (1, 2),
        'network': (2, 3),
        'switching': (1, 2),
        'regulatory': (2, 2)
    },
    '반도체': {
        'typical_moat': 4,
        'brand': (3, 5),
        'cost': (4, 5),
        'network': (2, 3),
        'switching': (3, 4),
        'regulatory': (3, 4)
    },
    '플랫폼': {
        'typical_moat': 4,
        'brand': (4, 5),
        'cost': (2, 3),
        'network': (4, 5),
        'switching': (3, 4),
        'regulatory': (2, 3)
    },
    '바이오': {
        'typical_moat': 3,
        'brand': (2, 3),
        'cost': (2, 3),
        'network': (1, 2),
        'switching': (3, 4),
        'regulatory': (4, 5)
    },
    '제조업': {
        'typical_moat': 2,
        'brand': (2, 3),
        'cost': (2, 3),
        'network': (1, 1),
        'switching': (2, 3),
        'regulatory': (2, 3)
    }
}
```

**문제점**:
- ❌ 단 5개 섹터만 정의 (게임, 반도체, 플랫폼, 바이오, 제조업)
- ❌ 건설, 금융, 화학, IT서비스 등 주요 섹터 누락
- ❌ 범위만 정의, 실제 판단 기준 없음

### 2.2 점수 계산 로직 (evaluate_moat)

```python
# Step 1: 범위에서 값 선택
brand = brand_range[1] if has_strong_brand else brand_range[0]

if company_size == 'large':
    cost = cost_range[1]
elif company_size == 'small':
    cost = cost_range[0]
else:
    cost = sum(cost_range) // 2

# Step 2: GICS primary_moat에 따라 조정
if primary_moat == '네트워크 효과':
    network = network_range[1]
else:
    network = network_range[0]

# Step 3: 총점 계산
total = brand + cost + network + switching + regulatory
moat_strength = round(total / 5)

# Step 4: GICS typical_strength와 비교 조정
if abs(moat_strength - base_strength) > 2:
    moat_strength = base_strength  # 강제 변경!
```

**문제점**:
- ❌ **has_strong_brand**: 회사명에 6개 키워드('삼성', '현대', ...) 포함 여부만 판단
  - 남광토건: 키워드 없음 → has_strong_brand = False
  - 실제 브랜드 파워는 전혀 고려 안 됨

- ❌ **company_size**: has_strong_brand와 동일 (6개 키워드 기반)
  - 매출, 자산, 시가총액 등 실제 규모 데이터 미사용

- ❌ **has_patents**: 항상 False (특허 정보 조회 안 함)

- ❌ **primary_moat 조정**: GICS에서 가져온 primary_moat만 반영
  - 회사별 실제 경쟁우위 분석 없음

- ❌ **Step 4 강제 조정**: 계산된 값과 GICS typical이 2 이상 차이나면 GICS 값으로 덮어씀
  - 남광토건: 9/25 → 2 계산 → IT Semiconductors typical=5 → **5로 강제 변경**

### 2.3 DART 데이터 활용 현황

**가져오는 데이터** (dart_client.py):
```python
def analyze_stock(stock_code):
    corp_code = get_corp_code(stock_code)  # corpCode.xml에서 조회
    company_info = get_company_info(corp_code)

    return {
        'corp_code': corp_code,
        'corp_name': company_info['corp_name'],
        'industry_code': company_info['induty_code'],  # KSIC 코드만!
        'business_desc': f"업종: {industry_code} | 설립: {est_dt} | {homepage}",
        'homepage': company_info['hm_url']
    }
```

**문제점**:
- ❌ **사업보고서 본문 미사용**: DART API는 사업보고서 전문 조회 가능하지만 사용 안 함
- ❌ **업종코드만 사용**: KSIC 코드 1개만 가져옴
- ❌ **회사 설명 없음**: "남광토건 - GICS: Information Technology..." ← 업종 분류만 표시
- ❌ **재무 데이터 없음**: 매출, 자산, 영업이익률 등 미사용

**DART API로 가능하지만 안 하는 것들**:
1. 사업의 내용 (사업보고서 본문)
2. 주요 제품 및 서비스
3. 경쟁 상황
4. 재무제표 (매출, 자산, 부채 등)
5. 주요 고객 및 공급업체

---

## 3. 남광토건 사례 상세 분석

### 3.1 실제 회사 정보

- **회사명**: 남광토건 (001260)
- **업종**: 건물건설업 (KSIC 41221)
- **사업**: 주택, 상업시설, 토목 건설
- **규모**: 중소형 건설사
- **경쟁력**: 낮음 (건설업은 진입장벽 낮고 경쟁 치열)

### 3.2 시스템 평가 결과

```
섹터: IT / IT서비스 ❌
해자강도: 5/5 ❌

해자 상세:
- 브랜드 파워: 2/5
- 원가 우위: 2/5
- 네트워크 효과: 1/5
- 전환 비용: 2/5
- 규제/허가: 2/5
총점: 9/25 → 평균 1.8 → 반올림 2 → 강제 조정 5
```

### 3.3 오류 발생 과정

```
① KSIC 41221 (건물건설업)
   ↓
② ksic_to_gics 매핑 테이블에 없음
   ↓
③ Fallback: '4'로 시작 → IT/IT서비스 ❌
   (실제: KSIC 4 = 건설/전기/가스/수도, NOT IT!)
   ↓
④ IT sector → Semiconductors moat pattern 적용
   (IT Services pattern 없어서 sector-level fallback)
   ↓
⑤ typical_strength = 5 (반도체급!)
   ↓
⑥ 계산: 9/25 → 2
   abs(2-5) = 3 > 2 → moat = 5로 강제 변경 ❌
```

### 3.4 올바른 평가는?

```
섹터: 제조업 / 건설 ✅
해자강도: 1-2/5 ✅

이유:
- 브랜드: 1 (중소 건설사, 브랜드 파워 약함)
- 원가: 2 (규모의 경제 제한적)
- 네트워크: 1 (네트워크 효과 없음)
- 전환비용: 1 (발주처가 쉽게 타사 선택 가능)
- 규제: 2 (건설업 면허 있으나 진입장벽 낮음)
총점: 7/25 → 해자강도 1-2
```

---

## 4. 근본적 문제점 정리

### 4.1 설계 문제

| 문제 | 현재 상태 | 영향 |
|------|-----------|------|
| **KSIC 매핑 부실** | 139개 중 건설업(41xxx) 없음 | 건설 → IT 오분류 |
| **Fallback '4' 오류** | KSIC 4 → IT (실제: 건설) | 체계적 오분류 |
| **Sector 패턴 부족** | 5개만 정의 (게임, 반도체, 플랫폼, 바이오, 제조업) | 나머지는 '제조업' fallback |
| **강제 조정 로직** | 계산값과 GICS typical 차이 > 2 → 덮어쓰기 | 실제 계산 무시 |

### 4.2 데이터 활용 문제

| 데이터 | 가능 여부 | 현재 사용 | 문제점 |
|--------|-----------|-----------|--------|
| **사업보고서 본문** | ✅ DART API 가능 | ❌ 미사용 | 사업 내용 설명 없음 |
| **재무 데이터** | ✅ DART API 가능 | ❌ 미사용 | 회사 규모 판단 불가 |
| **특허 정보** | ✅ KIPRIS API 가능 | ❌ 미사용 | has_patents 항상 False |
| **브랜드 파워** | ⚠️ 정성 평가 필요 | ❌ 6개 키워드만 | 실제 브랜드 가치 무시 |
| **경쟁 우위** | ⚠️ 정성 평가 필요 | ❌ 완전 누락 | 회사별 차별화 요인 없음 |

### 4.3 평가 기준 문제

**현재: 입력 데이터 거의 없음**
```python
입력:
- ticker (종목코드)
- name (회사명)
- KSIC 코드 (DART에서 조회)

판단:
- has_strong_brand: name에 6개 키워드 포함 여부
- company_size: has_strong_brand와 동일
- has_patents: False (조회 안 함)
- primary_moat: GICS sector의 일반적 특성
```

**결과: 모든 회사가 섹터 평균값으로 수렴**
- 삼성전자 = 다른 반도체 회사와 동일 해자
- 남광토건 = 다른 건설 회사와 동일 해자
- 회사별 차별화 요인 전혀 반영 안 됨

---

## 5. 해자 평가란 무엇이어야 하는가?

### 5.1 Morningstar의 정의

> "Economic Moat는 회사가 경쟁자로부터 자신의 시장 점유율과 수익성을 보호할 수 있는 **구조적 경쟁우위**"

**핵심**:
- ✅ **구조적**: 단기적 실적이 아닌 지속 가능한 우위
- ✅ **경쟁우위**: 동종 업계 대비 차별화 요인
- ✅ **보호력**: 경쟁자가 쉽게 모방/진입 불가

### 5.2 올바른 평가 프로세스

```
① 사업 이해
   - 무엇을 하는 회사인가?
   - 주요 제품/서비스는?
   - 고객은 누구인가?
   ↓
② 산업 분석
   - 산업 경쟁 강도는?
   - 진입장벽은?
   - 대체재 위협은?
   ↓
③ 경쟁우위 식별
   - 이 회사만의 강점은?
   - 왜 고객이 이 회사를 선택하나?
   - 경쟁사가 모방하기 어려운 이유는?
   ↓
④ 해자 유형 판단
   - 5가지 차원 중 어디에 강점?
   - 지속 가능한가?
   - 정량적 증거는? (시장점유율, 마진, 고객유지율 등)
   ↓
⑤ 해자 강도 평가
   - Wide Moat (5): 구조적이고 지속 가능한 강력한 우위
   - Narrow Moat (3-4): 일부 경쟁우위 존재하나 취약
   - No Moat (1-2): 경쟁우위 없음, commoditized
```

**현재 시스템**: ① 사업 이해 스킵, ② 산업 평균 적용, ③-④ 생략, ⑤ 섹터 기본값 사용

---

## 6. 재설계 방향 제안

### 6.1 즉시 수정 (Quick Wins)

1. **KSIC 매핑 수정** (1시간)
   - 건설업 41xxx 추가
   - Fallback '4' 수정: IT → Industrials/Construction
   - 주요 누락 산업 추가 (금융, 화학, 유통 등)

2. **강제 조정 로직 제거** (30분)
   - Line 191-192 삭제 또는 조건 완화
   - 계산된 값 존중

3. **IT Services moat pattern 추가** (30분)
   - ('Information Technology', 'IT Services'): typical_strength = 3

### 6.2 중기 개선 (1-2주)

1. **재무 데이터 통합**
   - DART 재무제표 API 연동
   - 매출, 자산, 영업이익률 → company_size 판단

2. **사업보고서 본문 활용**
   - "사업의 내용" 섹션 추출
   - core_desc에 실제 사업 설명 추가

3. **특허 데이터 통합**
   - KIPRIS API 연동 또는 DART 특허 정보 활용
   - has_patents 실제 판단

4. **섹터별 패턴 확장**
   - 금융, 화학, 유통, 소재 등 주요 섹터 추가
   - 각 섹터 전문가 리뷰

### 6.3 장기 재설계 (1-2개월)

**Option A: Rule-Based Expert System (현재 방향 강화)**
- 각 섹터별 상세 평가 기준 수립
- 재무 지표 기반 정량 평가 (ROE, 마진, 시장점유율)
- 전문가 규칙 추가 (if-then 로직)

**Option B: ML-Based Scoring**
- 역사적 데이터 학습 (상장사 해자 vs 주가 성과)
- 재무 지표 + 정성 지표 입력
- 예측 모델 (Random Forest, XGBoost)

**Option C: Hybrid (추천)**
- Rule-based로 sectoral 특성 반영
- ML로 회사별 차별화 요인 학습
- 사람 전문가 최종 검증 (confidence < 70%)

---

## 7. 결론 및 권고사항

### 7.1 현재 시스템의 한계

❌ **사업 이해 없음**: 회사가 무엇을 하는지 모름
❌ **경쟁우위 분석 없음**: 섹터 평균값만 사용
❌ **데이터 미활용**: DART 사업보고서, 재무제표 안 씀
❌ **회사별 차별화 없음**: 모든 회사가 섹터 기본값

### 7.2 권고사항

**개발 중단 옵션**:
1. ✅ **즉시 수정만 적용** → 분류 정확도 개선 → 배포 중단
2. ✅ **중기 개선 완료** → 실사용 가능 수준 → 제한적 배포
3. ✅ **장기 재설계** → 신뢰할 수 있는 해자 평가 → 정식 배포

**현재 추천**: **Option 2 (중기 개선)**
- 즉시 수정으로 치명적 버그 제거
- 재무 데이터 + 사업 설명 추가
- 섹터 패턴 확장
- 전문가 리뷰 프로세스 추가
- **예상 기간**: 2주

### 7.3 Next Steps

1. ❓ **사용자 의사결정**: 어떤 옵션을 선택할 것인가?
2. ❓ **해자 평가 목적 명확화**: 투자 의사결정? 포트폴리오 스크리닝? 교육용?
3. ❓ **정확도 목표**: 전문가 대비 몇 %까지 허용?
4. ❓ **리소스**: 도메인 전문가 투입 가능? 외부 데이터 구매 가능?

---

## 8. 부록: 관련 파일

- `scripts/stock_moat/moat_analyzer.py` - 해자 평가 로직
- `.agent/skills/stock-moat/utils/ksic_to_gics_mapper.py` - KSIC 매핑
- `.agent/skills/stock-moat/utils/dart_client.py` - DART API
- `docs/stock-classification-guide.md` - 분류 가이드

**작성자**: Claude Sonnet 4.5
**검토 필요**: 투자 전문가, 도메인 전문가
