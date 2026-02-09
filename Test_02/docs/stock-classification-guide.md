# 주식 분류 체계 가이드

## 📋 목적

투자 분석을 위한 정확한 종목 분류 체계 정립

---

## 🎯 핵심 원칙

### 1. KSIC vs GICS 구분

| 분류 체계 | 목적 | 사용자 | 적합성 |
|-----------|------|--------|--------|
| **KSIC** (한국표준산업분류) | 정부 통계, 사업자등록 | 통계청, 세무서 | ❌ 투자 부적합 |
| **GICS** (글로벌산업분류) | 투자 분석, 포트폴리오 | KRX, 기관투자자 | ✅ 투자 최적화 |

### 2. 왜 KSIC는 투자에 부적합한가?

**사례: 나노켐텍**
- KSIC 2229: "기타 플라스틱 제품 제조업"
  - 산업 관점: 플라스틱을 "만드는" 회사 (제조업)
  - 투자 관점: 화학 소재를 "판매하는" 회사 (화학)

- **문제**: 제조업으로 분류하면
  - 해자 분석이 잘못됨 (일반 제조업 vs 특수화학)
  - 경쟁사 비교 불가 (LG화학, 금호석유화학과 비교해야 함)
  - 섹터 로테이션 전략 오류

- **해결**: GICS Materials - Specialty Chemicals
  - 화학 소재 업종으로 정확히 분류
  - 해자 동인: 전환 비용, 고객 인증, 기술 특화
  - 경쟁사: 동일 GICS 내 특수화학 기업과 비교

---

## 🌍 GICS 구조

### 4단계 계층 구조

```
Level 1: Sector (11개)
  └─ Level 2: Industry Group (25개)
      └─ Level 3: Industry (74개)
          └─ Level 4: Sub-Industry (163개)
```

### 11개 주요 섹터

1. **Communication Services** (통신서비스)
   - Media, Entertainment, Gaming, Advertising

2. **Consumer Discretionary** (경기소비재)
   - Automobiles, Retail, Leisure, Travel

3. **Consumer Staples** (필수소비재)
   - Food, Beverages, Household Products

4. **Energy** (에너지)
   - Oil & Gas, Energy Equipment

5. **Financials** (금융)
   - Banks, Insurance, Asset Management

6. **Health Care** (헬스케어)
   - Pharmaceuticals, Biotechnology, Medical Devices

7. **Industrials** (산업재)
   - Capital Goods, Transportation, Commercial Services

8. **Information Technology** (정보기술)
   - Software, Semiconductors, IT Services

9. **Materials** (소재)
   - Chemicals, Metals, Paper & Forest Products

10. **Real Estate** (부동산)
    - REITs, Real Estate Management

11. **Utilities** (유틸리티)
    - Electric, Gas, Water Utilities

---

## 🇰🇷 한국 시장 적용

### KRX + WICS 통합 방식

1. **GICS 기본 틀** (글로벌 표준)
   - 11개 섹터 유지
   - 4단계 계층 유지

2. **WICS 한국 조정** (시장 특성 반영)
   - 한국 고유 산업 추가 (2차전지, 수소, K-뷰티)
   - 재벌 구조 반영 (지주회사, 계열사)
   - 한국어 명칭 표준화

### 우리 프로젝트의 229개 카테고리

**평가**:
- GICS Level 2.5~3 수준 (Industry Group + Industry)
- 한국 시장에 적합한 세분화
- 해자 분석에 충분한 깊이

**권장**:
- 현재 229개 카테고리 **유지** ✅
- KSIC → GICS 매핑 로직 추가 ✅
- GICS 표준과 연결 (선택사항)

---

## 🔄 분류 결정 규칙

### Rule 1: 단일 사업부 (Single Segment)

```
IF 한 사업부가 전체 매출의 ≥ 70%:
  → 해당 사업부로 분류 (straightforward)

Example: 삼성SDI
  - 2차전지: 85% 매출
  → GICS: Information Technology - Electronic Components
  → 한국어: 전자 / 2차전지
```

### Rule 2: 양분 사업부 (Dual Segment)

```
IF 두 사업부가 각각 40-60% 매출:
  1. 더 큰 매출 사업부로 분류
  2. core_desc에 부사업부 명시
  3. 해자 강도 -0.5 할인 적용

Example: LG화학
  - 기초소재: 45% 매출
  - 2차전지: 42% 매출
  → Primary: 기초소재 (Materials - Chemicals)
  → Secondary: 2차전지 (명시)
  → Moat discount: -0.5 (복합 사업 리스크)
```

### Rule 3: 다각화 기업 (Conglomerate)

```
IF 세 개 이상 사업부, 최대 사업부 < 51% 매출:
  1. Option A: 지주회사 카테고리 (Holding Company)
  2. Option B: 최대 매출 사업부 + 명시적 할인
  3. 해자 강도 -1.0 할인 적용

Example: 삼성전자
  - 반도체: 65% 매출 → Primary로 분류 가능
  - 가전: 25% 매출
  - 디스플레이: 10% 매출
  → Primary: Semiconductors (단일 분류)
  → Moat discount: -0.5 (다각화 리스크)
```

### Rule 4: 재벌 지주회사 (Korean Chaebol)

```
IF 순수 지주회사 (영업 활동 없음):
  → Financials - Financial Holding Companies
  → Moat: 2-3 (규제 허가 장벽만 있음)

IF 사업 지주회사 (영업 + 지배 구조):
  → 최대 매출 사업부로 분류
  → 거버넌스 리스크 할인 -0.5

Example: SK (주)
  - 순수 지주회사
  → Financials - Holding Company
  → Moat: 2 (지배 구조 복잡성)
```

---

## 🛡️ GICS별 해자 특성

### Information Technology

**Semiconductors** (반도체)
- 주요 해자: 원가 우위
- 동인: CAPEX 장벽, 규모의 경제, 첨단 공정
- 일반 강도: 5/5 (세계 최고 수준)
- 예시: 삼성전자, SK하이닉스

**Software** (소프트웨어)
- 주요 해자: 전환 비용
- 동인: API 통합, 학습곡선, 데이터 종속성
- 일반 강도: 4/5
- 예시: 더존비즈온, 한글과컴퓨터

### Communication Services

**Gaming** (게임)
- 주요 해자: 네트워크 효과
- 동인: 유저 커뮤니티, IP 가치, 플랫폼 효과
- 일반 강도: 4/5 (단, life cycle 짧음)
- 예시: 넥슨, 네오위즈, 펄어비스

**Advertising** (광고)
- 주요 해자: 브랜드 파워
- 동인: 고객 관계, 크리에이티브 역량
- 일반 강도: 2-3/5 (경쟁 치열)

### Materials

**Specialty Chemicals** (특수화학)
- 주요 해자: 전환 비용
- 동인: 고객 인증, 기술 특화, 품질 일관성
- 일반 강도: 4/5
- 예시: 나노켐텍, LG화학 특수소재

**Basic Chemicals** (기초화학)
- 주요 해자: 원가 우위
- 동인: 규모의 경제, 원재료 접근성
- 일반 강도: 3/5 (commodity 성격)

### Health Care

**Pharmaceuticals** (의약품)
- 주요 해자: 규제/허가
- 동인: 임상 승인, 특허, 식약처 인허가
- 일반 강도: 5/5 (진입장벽 최고)
- 예시: 한미약품, 유한양행

**Biotechnology** (바이오)
- 주요 해자: 규제/허가 + 기술
- 동인: 특허, 파이프라인, R&D
- 일반 강도: 4-5/5 (리스크 높음)

### Consumer Discretionary

**Retailing** (소매)
- 주요 해자: 브랜드 파워 or 입지
- 동인: 고객 충성도, 유통망, 상품 차별화
- 일반 강도: 2-3/5 (경쟁 심화)
- 예시: 신세계, 롯데쇼핑

**Automobiles** (자동차)
- 주요 해자: 브랜드 + 원가
- 동인: 브랜드 이미지, 생산 규모, 기술력
- 일반 강도: 3-4/5
- 예시: 현대차, 기아

### Financials

**Banks** (은행)
- 주요 해자: 규제/허가
- 동인: 금융 라이선스, 자본 요건
- 일반 강도: 4/5
- 예시: KB금융, 신한금융

---

## 📊 실무 적용 가이드

### DART 데이터 → GICS 변환 프로세스

```python
# 1. DART API에서 KSIC 코드 추출
dart_result = dart_client.get_company_info(stock_code)
ksic_code = dart_result['industry_code']  # e.g., "2229"

# 2. KSIC → GICS 매핑
gics_mapper = KSICtoGICSMapper()
gics_result = gics_mapper.map_to_gics(ksic_code, company_name)

# 3. 결과
{
  'gics_sector': 'Materials',
  'gics_industry': 'Specialty Chemicals',
  'korean_sector_top': '화학',
  'korean_sector_sub': '특수플라스틱',
  'confidence': 0.95
}

# 4. 해자 특성 조회
moat_info = gics_mapper.get_moat_drivers_by_gics(
  gics_sector='Materials',
  gics_industry='Specialty Chemicals'
)
# → primary_moat: '전환 비용', typical_strength: 4
```

### 분류 신뢰도 기준

| 신뢰도 | 매칭 수준 | 조치 |
|--------|-----------|------|
| ≥ 90% | Exact KSIC match | 자동 승인 |
| 70-89% | Prefix match (4-5자리) | 검토 권장 |
| 50-69% | Prefix match (3자리) | 수동 검토 필수 |
| < 50% | Fallback 추정 | 사업보고서 직접 분석 |

### 예외 처리

**Case 1: DART 업종코드 없음** (해외 상장사)
```
IF dart_industry_code is None:
  → 229 카테고리에서 수동 분류
  → 글로벌 GICS 참조 (Bloomberg, Reuters)
```

**Case 2: 신규 산업** (2차전지, 수소, AI 반도체)
```
IF 기존 KSIC 코드로 부적합:
  → WICS 한국 특화 코드 참조
  → 229 카테고리에 신규 추가
  → GICS 매핑 테이블 업데이트
```

**Case 3: M&A로 사업 변경**
```
IF 최근 M&A로 주력 사업 변경:
  → 최신 분기 보고서 매출 구성 확인
  → 재분류 (1년 유예 없이 즉시 반영)
```

---

## ✅ 체크리스트

### 분류 작업 시 확인 사항

- [ ] DART KSIC 코드 확인
- [ ] KSIC → GICS 매핑 적용
- [ ] 한국어 섹터명 확인 (229 카테고리와 정합성)
- [ ] 다각화 기업인 경우 매출 구성 확인
- [ ] 해자 동인이 GICS 섹터 특성과 일치하는지 확인
- [ ] 신뢰도 < 70%인 경우 수동 검토
- [ ] 경쟁사와 동일 GICS 분류인지 교차 검증

### 해자 평가 시 확인 사항

- [ ] GICS 섹터별 일반적 해자 강도 참조
- [ ] 다각화 할인 적용 여부 (매출 구성 기준)
- [ ] 한국 특수성 (재벌 구조, 정부 지원) 반영
- [ ] 글로벌 경쟁사 대비 상대적 강도 평가

---

## 📚 참고 자료

- [GICS Methodology (MSCI)](https://www.msci.com/gics)
- [KRX GICS 도입 (2017)](https://www.krx.co.kr)
- [WICS (WISEfn)](https://www.wisefn.com)
- [DART 전자공시](https://dart.fss.or.kr)

---

## 🔄 업데이트 이력

- 2026-02-09: 초안 작성 (GICS 기반 분류 체계 정립)
