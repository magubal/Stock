# Evidence-Based Moat (증거 기반 해자 평가) Planning Document

> **Summary**: DART 공시 데이터 기반 증거 중심 해자 평가 시스템 재설계
>
> **Project**: Stock Research ONE
> **Version**: 2.0 (기존 stock-moat-estimator 완전 재설계)
> **Author**: Claude Sonnet 4.5
> **Date**: 2026-02-10
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

기존 해자 평가 시스템(stock-moat-estimator v1)의 근본적 한계를 해결하고,
전문가 MGB-MOAT 방법론(Steps B-E)에 기반한 **증거 중심 해자 평가 시스템**을 구축한다.

**핵심 원칙**: "증거 없으면 평가 안 함" (특히 해자강도 3점 이상)

### 1.2 Background

#### 기존 시스템의 근본적 문제 (v1)

남광토건 사례에서 드러난 4가지 설계 결함:

| 문제 | 현상 | 원인 |
|------|------|------|
| **분류 오류** | 건설업 → IT/IT서비스 | KSIC 매핑 테이블 누락 + Fallback '4' 오류 |
| **해자 과대평가** | 해자강도 2 → 5 강제 변경 | `abs(계산-typical)>2 → typical` 강제 조정 |
| **증거 부재** | 사업 설명 0%, 재무 데이터 0% | DART API 1개만 사용 (기업개황) |
| **차별화 없음** | 모든 회사 = 섹터 평균값 | 회사별 경쟁우위 분석 로직 없음 |

**정량적 문제**:
- 사업 설명(core_desc)에 실제 사업 내용: **0%** (업종코드만 표시)
- 해자강도 = 섹터 평균값: **90%+** (회사별 차별화 없음)
- 증거 기반 평가 (3점 이상): **0%** (모두 패턴 매칭)
- DART API 활용률: **2/35개** (corpCode.xml + 기업개황)

#### 전문가 MGB-MOAT 방법론

사용자가 제공한 전문가 방법론의 핵심 프로세스:

```
Step B: 1차 사실 수집 (공시/IR 우선)
  → "해자 3점 이상은 공시/IR 등 신뢰자료 기반 문장 없으면 기록하지 않음"
  ↓
Step C: BM 6요소 기계적 분해
  → 고객 / 수익모델 / 차별점 / 비용구조 / 성장조건 / 실패조건
  ↓
Step D: 해자 평가 (MGB-MOAT Index)
  → 증거 문장 먼저 → 점수. 3점+ 공시 확인 필수, 4+ 반증 체크+검증용desc
  ↓
Step E: 산업구조+트렌드로 해자 지속가능성 검증
  → 구조적 성장? 경쟁 축 변화? 해자 유지비용 과도?
```

#### 투자 철학 정합성

프로젝트의 핵심 철학인 "마구티어 플라이휠"과의 정합:

| 투자 철학 요소 | 해자 평가 연결 |
|--------------|--------------|
| **고객가치제안** = 경쟁사 대비 확실한 차별적 혜택 | Step C의 "왜 이 회사인가 (차별 포인트)" |
| **빅트렌드 부합** | Step E의 "구조적 성장인지" |
| **해자요인** = 과점/독점적 요인 | Step D의 "해자 유형별 증거" |
| **경쟁력 증거** | Step B의 "공시/IR 기반 사실 수집" |

### 1.3 Related Documents

- 기존 시스템 분석: `docs/moat-evaluation-critique.md`
- 재설계 제안서: `docs/moat-redesign-proposal.md`
- 기존 PDCA Report: `docs/04-report/features/stock-moat-estimator.report.md`
- 투자 철학: `docs/investment-philosophy.md`
- 기존 코드: `.agent/skills/stock-moat/utils/` (dart_client, moat_analyzer, ksic_to_gics_mapper 등)

---

## 2. Scope

### 2.1 In Scope

- [x] **Phase 0**: 기존 시스템 치명적 버그 수정 (KSIC 매핑, Fallback, 강제 조정)
- [ ] **Phase 1**: DART 데이터 확장 (DS001~DS003 활용) + 사업보고서 파싱
- [ ] **Phase 2**: BM 6요소 기계적 분해 자동화 (Step C)
- [ ] **Phase 3**: 증거 기반 해자 평가 로직 (Step D) - 3점+ 증거 필수
- [ ] **Phase 4**: 검증용 DESC 생성 (4점+ 반증 체크)
- [ ] **Phase 5**: 지속가능성 검증 (Step E) - 산업구조 + 트렌드
- [ ] **Phase 6**: 전체 재분석 (1561 종목) + 품질 검증

### 2.2 Out of Scope

- LLM 기반 증거 추출 (Phase 2에서 향후 고려, 현재는 Rule-based)
- 외부 유료 데이터 소스 연동 (Bloomberg, FactSet 등)
- 실시간 해자 업데이트 (배치 처리만)
- 해외 주식 평가
- UI/Dashboard 변경 (백엔드 로직만)

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | DART 사업보고서 원본 다운로드 및 파싱 (DS001 공시서류원본파일) | High | Pending |
| FR-02 | DART 재무제표 API 연동 (DS003 단일회사 주요계정) | High | Pending |
| FR-03 | DART 사업부문별 매출 조회 (DS002 사업부문별 매출) | High | Pending |
| FR-04 | BM 6요소 분해 자동화 (고객/수익모델/차별점/비용구조/성장조건/실패조건) | High | Pending |
| FR-05 | 증거 문장 추출 엔진 (Rule-based, 해자 유형별 패턴 매칭) | High | Pending |
| FR-06 | 증거 기반 해자 점수 부여 (1-2점: 증거 불필요, 3점+: 공시 증거 필수) | Critical | Pending |
| FR-07 | 4점+ 반증 체크 및 검증용 DESC 자동 생성 | High | Pending |
| FR-08 | 지속가능성 3-체크 (구조적 성장/경쟁 축 변화/해자 유지비용) | Medium | Pending |
| FR-09 | 해자 유형 확장 (10가지: 전환비용/네트워크효과/규모경제/브랜드/규제허가/데이터학습/특허공정/공급망/락인표준/원가우위) | High | Pending |
| FR-10 | KSIC 매핑 테이블 보완 (건설41xxx, 금융64-66xxx 등 누락 섹터) | Critical | Pending |
| FR-11 | 강제 조정 로직(abs>2→typical) 제거 및 증거 기반 로직 대체 | Critical | Pending |
| FR-12 | Excel 출력 확장 (증거 문장, BM 분해, 지속가능성 체크 결과) | Medium | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| **정확도** | 전문가 리뷰 대비 해자강도 ±1 이내 일치율 ≥80% | 20개 샘플 전문가 비교 |
| **증거 커버리지** | 해자 3점+ 종목 중 공시 증거 보유율 ≥95% | 자동 검증 |
| **사업 설명 커버리지** | core_desc에 실제 사업 내용 보유율 ≥90% | 빈 값 비율 체크 |
| **처리 성능** | 1종목 분석 ≤30초 (DART API 포함) | 배치 실행 시간 측정 |
| **DART API 안정성** | API 성공률 ≥95% | 에러 로그 분석 |
| **보안** | API 키 환경변수 관리, 하드코딩 금지 | 코드 스캔 |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] DART 사업보고서 파싱 및 주요 섹션 추출 동작
- [ ] BM 6요소 분해 결과 생성 (확인/추정 라벨 포함)
- [ ] 증거 기반 해자 점수 부여 (3점+ = 공시 증거 필수 규칙 적용)
- [ ] 4점+ 종목의 검증용 DESC 자동 생성
- [ ] 지속가능성 3-체크 경고 시스템 동작
- [ ] 남광토건 재평가: 건설업/해자강도 1-2로 올바르게 분류
- [ ] 삼성전자 재평가: 반도체/해자강도 4-5 (증거 문장 포함)
- [ ] 208개 샘플 재분석 완료 + 전문가 리뷰 일치율 확인

### 4.2 Quality Criteria

#### 정량 지표

| 지표 | 기존 (v1) | 목표 (v2) | 검증 방법 |
|------|-----------|-----------|-----------|
| **분류 정확도** | 94.9% | ≥98% | 수동 검토 50개 |
| **사업 설명 보유** | 0% | ≥90% | core_desc 비어있지 않은 비율 |
| **증거 기반 평가** | 0% | ≥80% (3점+ 중) | 증거 문장 있는 비율 |
| **해자 = 섹터 평균** | 90%+ | ≤30% | 동일 섹터 내 해자 분산 |
| **전문가 리뷰 일치** | 미측정 | ≥80% (±1) | 20개 샘플 |

#### 정성 기준 (남광토건 테스트)

```
Before (v1):
  섹터: IT/IT서비스 ❌   해자강도: 5/5 ❌
  core_desc: "GICS: Information Technology - IT Services" ❌
  해자DESC: "브랜드 2, 원가 2, 네트워크 1, 전환 2, 규제 2 → 5" ❌

After (v2 목표):
  섹터: Industrials/건설 ✅   해자강도: 1-2/5 ✅
  core_desc: "주택/상업시설/토목 건설. 건축공사 60%, 토목공사 30%..." ✅
  해자DESC: "전환비용 1(증거없음), 네트워크 1(건설업 해당없음),
             규모경제 2(△ 중견 규모), 브랜드 1(증거없음),
             규제 2(✓ 면허 보유, 진입장벽 낮음)" ✅
```

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **DART 사업보고서 파싱 실패** | High - 증거 추출 불가 | Medium | DS002 정형 데이터로 대체, 다중 파싱 전략 |
| **DART API Rate Limit** | Medium - 배치 속도 저하 | High | 2초 딜레이, 캐싱, 점진적 수집 |
| **DART API 키 재만료** | High - 전체 중단 | Low | 만료 모니터링, 대체 키 준비 |
| **증거 추출 정확도 낮음** | High - 잘못된 증거 → 잘못된 점수 | Medium | 사람 검증 루프, confidence 임계값 |
| **BM 분해 자동화 한계** | Medium - 6요소 불완전 | High | "추정" 라벨 부착, 누락 요소 경고 |
| **사업보고서 미제출 종목** | Low - 일부 종목 분석 불가 | Medium | 대체 데이터소스 (네이버금융 등) |
| **개발 기간 초과** | Medium - Phase별 독립 불가 | Low | Phase별 독립 배포, Milestone 관리 |
| **기존 데이터 호환성** | Medium - 엑셀 구조 변경 | Low | 점진적 마이그레이션, 기존 컬럼 유지 |

---

## 6. Architecture Considerations

### 6.1 Project Level Selection

| Level | Characteristics | Recommended For | Selected |
|-------|-----------------|-----------------|:--------:|
| **Starter** | Simple structure | Static sites | |
| **Dynamic** | Feature-based modules, BaaS | Web apps with backend | **X** |
| **Enterprise** | Strict layer separation | High-traffic systems | |

**선택 근거**: 기존 프로젝트가 Dynamic 레벨 (React + FastAPI). 해자 평가는 백엔드 Python 모듈.

### 6.2 Key Architectural Decisions

| Decision | Options | Selected | Rationale |
|----------|---------|----------|-----------|
| **DART 접근** | requests 직접 / dart-fss 라이브러리 | requests 직접 | 의존성 최소화, 기존 코드 활용 |
| **사업보고서 파싱** | XML 직접 파싱 / BeautifulSoup / lxml | lxml + BeautifulSoup | DART 원본파일은 XML/HTML 혼재 |
| **증거 추출** | Rule-based / LLM / Hybrid | Rule-based (Phase 1) | 비용 0, 빠른 구현, LLM은 향후 추가 |
| **데이터 캐싱** | 없음 / 파일시스템 / SQLite | 파일시스템 JSON | 단순, 기존 구조 활용 |
| **BM 분해** | 수동 템플릿 / 패턴 추출 | DART 데이터 기반 패턴 추출 | 자동화 가능 범위 내 |
| **출력 포맷** | Excel 기존 / Excel 확장 / DB | Excel 확장 | 기존 워크플로우 유지 |

### 6.3 DART API 활용 계획

```
현재 사용 (2/35 API):
┌──────────────────────────────────────────┐
│ DS001: corpCode.xml (기업 고유번호)       │
│ DS001: company.json (기업개황 - KSIC코드) │
└──────────────────────────────────────────┘

추가 활용 예정 (8개 API):
┌──────────────────────────────────────────┐
│ DS001: 공시서류원본파일 (사업보고서 본문)   │  ← 핵심 (Step B)
│ DS002: 사업부문별 매출                     │  ← BM 분해 (Step C)
│ DS002: 주요 제품/서비스 매출               │  ← BM 분해 (Step C)
│ DS002: 주요주주 현황                      │  ← 지배구조
│ DS002: 임원 현황                          │  ← 경영진
│ DS003: 단일회사 주요계정 (재무제표)         │  ← 정량 분석
│ DS003: 단일회사 전체 재무제표              │  ← 상세 재무
│ DS003: 재무지표                          │  ← ROE, 영업이익률
└──────────────────────────────────────────┘
```

### 6.4 모듈 구조

```
.agent/skills/stock-moat/utils/
├── config.py                  # (기존) 환경변수 관리
├── dart_client.py             # (확장) DART API - DS001~DS003
├── dart_report_parser.py      # (신규) 사업보고서 XML/HTML 파싱
├── ksic_to_gics_mapper.py     # (수정) KSIC 매핑 보완
├── bm_analyzer.py             # (신규) BM 6요소 분해 (Step C)
├── evidence_extractor.py      # (신규) 증거 문장 추출 (Step B→D)
├── moat_evaluator_v2.py       # (신규) 증거 기반 해자 평가 (Step D)
├── sustainability_checker.py  # (신규) 지속가능성 검증 (Step E)
├── moat_analyzer.py           # (폐기) 기존 섹터 평균 기반 로직
└── excel_io.py                # (확장) 출력 컬럼 추가

scripts/stock_moat/
├── analyze_new_stocks.py      # (수정) v2 평가 로직 호출
├── reanalyze_with_evidence.py # (신규) 증거 기반 재분석
└── validate_moat_quality.py   # (신규) 품질 검증 스크립트
```

---

## 7. Convention Prerequisites

### 7.1 Existing Project Conventions

- [x] `CLAUDE.md` has coding conventions section
- [x] `.env` + `config.py` 환경변수 관리
- [x] Python 모듈 구조 (`utils/`, `scripts/`)
- [ ] Unit tests (없음 - 추가 필요)
- [x] Type hints (기존 코드에 적용됨)

### 7.2 Conventions to Define/Verify

| Category | Current State | To Define | Priority |
|----------|---------------|-----------|:--------:|
| **증거 데이터 포맷** | 없음 | Evidence JSON Schema | High |
| **BM 분해 포맷** | 없음 | BM Analysis JSON Schema | High |
| **해자 점수 규칙** | 섹터 평균 | 증거 기반 점수 규칙 | Critical |
| **DART 캐시 구조** | 없음 | 캐시 파일 경로/형식 | Medium |
| **로깅** | print() | logging 모듈 전환 | Medium |

### 7.3 Environment Variables Needed

| Variable | Purpose | Scope | To Be Created |
|----------|---------|-------|:-------------:|
| `DART_API_KEY` | DART API 접근 | Server | 기존 |
| `DART_CACHE_DIR` | DART 캐시 디렉토리 | Server | 신규 |
| `MOAT_MIN_EVIDENCE_SCORE` | 3점+ 증거 필수 임계값 | Config | 신규 |
| `DART_RATE_LIMIT` | API 호출 간격 (초) | Config | 신규 |

---

## 8. Detailed Phase Plan

### Phase 0: 치명적 버그 수정 (1일)

**목표**: 기존 시스템의 즉시 위험 제거

| Task | 파일 | 변경 내용 |
|------|------|----------|
| KSIC 매핑 보완 | `ksic_to_gics_mapper.py` | 건설(41xxx), 금융(64-66xxx), 전기가스(35xxx) 추가 |
| Fallback '4' 수정 | `ksic_to_gics_mapper.py` | '4' → IT 를 '4' → Industrials/Construction 으로 변경 |
| 강제 조정 제거 | `moat_analyzer.py` | `abs(moat-base)>2 → base` 로직 삭제 |
| IT Services 패턴 | `moat_analyzer.py` | IT Services sector에 적절한 typical_strength 추가 |

### Phase 1: DART 데이터 확장 (3-5일)

**목표**: 사업보고서 + 재무제표 수집 자동화

| Task | 상세 |
|------|------|
| **dart_client.py 확장** | DS001 공시서류원본 다운로드, DS002 사업부문별 매출, DS003 재무제표 API 추가 |
| **dart_report_parser.py** | 사업보고서 XML/HTML 파싱. "사업의 내용", "주요 제품", "경쟁 현황" 섹션 추출 |
| **DART 캐싱** | 다운로드된 사업보고서 로컬 캐싱 (재실행 시 API 호출 최소화) |
| **재무 데이터 수집** | `fnltt_singl_acnt` API로 매출/영업이익/자산/부채/ROE 수집 |

**DART API 호출 흐름**:
```
1. corpCode.xml → corp_code 조회
2. company.json → 기업개황 (KSIC, 홈페이지, 설립일)
3. document.xml → 사업보고서 원본 다운로드 (ZIP)
   → 파싱: 사업의 내용, 주요 제품, 경쟁현황, 연구개발
4. fnltt_singl_acnt → 주요계정 (매출, 영업이익, 자산, 부채)
5. srmny → 사업부문별 매출
```

### Phase 2: BM 6요소 분해 (2-3일)

**목표**: Step C 자동화 - 사업모델 기계적 분해

```python
BM 6요소:
1. 고객은 누구인가          → 사업보고서 "주요 고객" + 매출 구성
2. 무엇으로 돈을 버는가      → 사업부문별 매출 + 제품/서비스
3. 왜 이 회사인가 (차별점)   → 경쟁현황 + 연구개발
4. 비용 구조/레버리지        → 재무제표 (고정비/변동비 추정)
5. 성장이 되는 조건          → 산업 특성 + 시장 동향
6. 망하는 조건              → 리스크 요인 + 경쟁 위협
```

**라벨 규칙**: 각 요소에 `[확인]` 또는 `[추정]` 라벨 부착
- `[확인]`: 공시 데이터에서 직접 추출 가능한 항목
- `[추정]`: 공시 데이터 부재 시 산업 일반론으로 추정

### Phase 3: 증거 기반 해자 평가 (3-5일)

**목표**: Step D - "증거 문장 먼저 → 점수"

**해자 유형 10가지**:
1. 전환비용 (Switching Costs)
2. 네트워크 효과 (Network Effect)
3. 규모의 경제 (Economies of Scale)
4. 브랜드 (Brand/Intangible Assets)
5. 규제/허가 (Regulatory/Licenses)
6. 데이터/학습 (Data/Learning Advantage)
7. 특허/공정 (Patents/Process)
8. 공급망/설치기반 (Supply Chain/Installed Base)
9. 락인/표준 (Lock-in/Standard)
10. 원가우위 (Cost Leadership)

**점수 규칙 (MGB-MOAT Index)**:

| 점수 | 정의 | 증거 요구사항 |
|------|------|-------------|
| **1점** | 해자 없음 | 증거 불필요 |
| **2점** | 약한 해자 | 증거 불필요 (일반적 추정 가능) |
| **3점** | 보통 해자 | **공시/IR 기반 증거 문장 필수** |
| **4점** | 강한 해자 | 공시 증거 + **반증 체크** + **검증용desc** 필수 |
| **5점** | 구조적 해자 | 4점 요건 + **지속가능성 검증** (Step E) 통과 |

**핵심 로직**:
```
IF 해자강도 계산값 >= 3:
    IF 공시 증거 문장 없음:
        → 해자강도 = 2 (하향 조정)
        → note = "증거 불충분으로 하향"
    ELIF 해자강도 >= 4:
        IF 반증 체크 미수행:
            → 해자강도 = 3 (하향 조정)
        ELIF 검증용desc 미생성:
            → 해자강도 = 3 (하향 조정)
```

### Phase 4: 검증용 DESC + 반증 체크 (2-3일)

**목표**: 4점+ 종목의 엄격한 검증

**검증용 DESC 구조**:
```
[검증용 DESC - {회사명} 해자강도 {N}]

1. 주요 증거:
   - [공시] {증거 문장 1} (출처: 사업보고서 2023)
   - [공시] {증거 문장 2} (출처: 재무제표)

2. 경쟁사 대비 우위:
   - {경쟁사 대비 차별점}

3. 반증 체크:
   ✓ {반증 1}: {반박 근거}
   ⚠️ {반증 2}: {해소 필요}

4. 지속가능성:
   - 구조적 성장: {판단}
   - 경쟁 축 변화: {판단}

[검증 필요 항목]
□ 전문가 리뷰
□ 경쟁사 비교
```

### Phase 5: 지속가능성 검증 (2-3일)

**목표**: Step E - 산업구조+트렌드로 해자 검증

**3가지 체크**:

| 체크 항목 | 데이터 소스 | 판단 기준 |
|----------|-----------|----------|
| 구조적 성장인지 | 재무 3년 추이 + 산업 특성 | 매출 CAGR ≥ 5%, 산업 성장 언급 |
| 경쟁의 축 변화 | 사업보고서 경쟁현황 + 리스크 | 기술/규제/원가/표준 변화 언급 |
| 해자 유지비용 과도 | CAPEX/매출 비율 + R&D 비용 | CAPEX/매출 > 30% → 경고 |

### Phase 6: 전체 재분석 + 검증 (3-5일)

**목표**: 1561 종목 증거 기반 재분석

| Task | 상세 |
|------|------|
| 208개 우선 재분석 | 기존 데이터와 비교 → 품질 확인 |
| 전문가 리뷰 20개 | 무작위 샘플 → 전문가 대비 일치율 측정 |
| 전체 1561개 재분석 | Phase 1-5 파이프라인 일괄 실행 |
| Excel 업데이트 | 확장된 컬럼 포함 최종 저장 |

---

## 9. Implementation Priority & Dependencies

```
Phase 0 (치명적 버그) ─────────────────────────────┐
  │                                                │
  ▼                                                │
Phase 1 (DART 데이터 확장)                          │
  │                                                │
  ├──────────────┐                                 │
  ▼              ▼                                 │
Phase 2        Phase 3                             │
(BM 분해)      (증거 평가) ←── Phase 2 결과 참조    │
  │              │                                 │
  └──────┬───────┘                                 │
         ▼                                         │
       Phase 4 (검증용 DESC)                        │
         │                                         │
         ▼                                         │
       Phase 5 (지속가능성)                         │
         │                                         │
         ▼                                         │
       Phase 6 (전체 재분석) ◀─────────────────────┘
```

**Critical Path**: Phase 0 → Phase 1 → Phase 3 → Phase 6

---

## 10. Data Schema (증거 데이터 구조)

### 10.1 증거 문장 (Evidence)

```json
{
  "company": "삼성전자",
  "ticker": "005930",
  "evidences": [
    {
      "moat_type": "규모의 경제",
      "evidence_text": "세계 반도체 시장 점유율 1위 (메모리 42%, 파운드리 18%)",
      "source": "사업보고서 2023 - 사업의 내용",
      "confidence": "confirmed",
      "has_numbers": true,
      "quality_score": 1.5
    }
  ]
}
```

### 10.2 BM 분해 (Business Model)

```json
{
  "company": "삼성전자",
  "bm_analysis": {
    "customer": {
      "answer": "글로벌 IT 기업, 통신사, 일반 소비자",
      "label": "confirmed",
      "source": "사업보고서 - 주요 고객"
    },
    "revenue_model": {
      "answer": "반도체 매출 42%, 스마트폰 35%, 디스플레이 15%",
      "unit_economics": "B2B 대량 공급 + B2C 프리미엄 가격",
      "recurring": false,
      "label": "confirmed"
    },
    "differentiation": { "...": "..." },
    "cost_structure": { "...": "..." },
    "growth_condition": { "...": "..." },
    "failure_condition": { "...": "..." }
  }
}
```

### 10.3 해자 평가 결과 (Moat Evaluation)

```json
{
  "company": "남광토건",
  "ticker": "001260",
  "moat_strength": 2,
  "scores_by_type": {
    "switching_costs": 1,
    "network_effect": 1,
    "economies_of_scale": 2,
    "brand": 1,
    "regulatory": 2,
    "data_learning": 1,
    "patents": 1,
    "supply_chain": 1,
    "lock_in": 1,
    "cost_leadership": 2
  },
  "evidence_summary": {
    "total_evidences": 2,
    "confirmed_evidences": 1,
    "estimated_evidences": 1,
    "max_evidence_score": 2
  },
  "sustainability": {
    "structural_growth": "neutral",
    "competition_shift": "stable",
    "maintenance_cost": "low",
    "warnings": ["건설 경기 순환적, 구조적 성장 제한"]
  },
  "verification_desc": null,
  "classification": {
    "gics_sector": "Industrials",
    "gics_industry": "Construction & Engineering",
    "core_sector_top": "건설",
    "core_sector_sub": "건물건설업"
  }
}
```

---

## 11. Next Steps

1. [ ] **사용자 승인**: 이 Plan 문서 검토 및 승인
2. [ ] **Design 문서 작성**: `/pdca design evidence-based-moat`
3. [ ] **Phase 0 즉시 시작**: 치명적 버그 수정 (승인 후 즉시)
4. [ ] **Phase 1 구현**: DART 데이터 확장

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-10 | Initial draft based on MGB-MOAT methodology | Claude Sonnet 4.5 |
