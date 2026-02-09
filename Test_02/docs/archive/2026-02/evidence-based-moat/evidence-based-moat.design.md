# Evidence-Based Moat (증거 기반 해자 평가) Design Document

> **Summary**: MGB-MOAT 방법론 기반 DART 공시 증거 중심 해자 평가 시스템 상세 설계
>
> **Project**: Stock Research ONE
> **Version**: 2.0
> **Author**: Claude Sonnet 4.5
> **Date**: 2026-02-10
> **Status**: Draft
> **Planning Doc**: [evidence-based-moat.plan.md](../01-plan/features/evidence-based-moat.plan.md)

---

## 1. Overview

### 1.1 Design Goals

1. **증거 우선**: 해자 3점+ = 공시/IR 증거 문장 필수, 4점+ = 반증 체크 필수
2. **DART 데이터 최대 활용**: 현재 2개 → 10개 API 활용 (DS001~DS003)
3. **BM 기계적 분해**: 6요소 고정 프레임워크로 사업모델 자동 분석
4. **회사별 차별화**: 섹터 평균이 아닌 개별 회사 증거 기반 점수
5. **기존 호환**: Excel 출력 구조 유지, 기존 컬럼 + 신규 컬럼 확장

### 1.2 Design Principles

- **Evidence-First**: 증거 없으면 2점 이하 (절대로 3점+ 부여 금지)
- **Fail-Safe Downgrade**: 증거 부족 시 항상 하향 조정 (상향 금지)
- **Cache-Heavy**: DART API 결과 로컬 캐싱 (반복 호출 방지)
- **Labeled Data**: 모든 분석 결과에 `[확인]`/`[추정]` 라벨 부착
- **Backward Compatible**: 기존 Excel 컬럼 유지, 신규 컬럼 추가만

---

## 2. Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Pipeline Orchestrator                      │
│               (analyze_with_evidence.py)                     │
└───────┬──────────┬──────────┬──────────┬──────────┬─────────┘
        │          │          │          │          │
        ▼          ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  DART    │ │  BM      │ │ Evidence │ │  Moat    │ │ Sustain- │
│  Client  │ │ Analyzer │ │ Extrac-  │ │ Evalua-  │ │ ability  │
│ (확장)   │ │ (신규)   │ │ tor(신규)│ │ tor v2   │ │ Checker  │
│          │ │          │ │          │ │ (신규)   │ │ (신규)   │
│ DS001    │ │ 6요소    │ │ 해자유형 │ │ 증거기반 │ │ 3-체크   │
│ DS002    │ │ 분해     │ │ 패턴매칭 │ │ 점수부여 │ │ 검증     │
│ DS003    │ │          │ │          │ │          │ │          │
└──────┬───┘ └─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬───┘
       │           │            │             │            │
       ▼           ▼            ▼             ▼            ▼
┌─────────────────────────────────────────────────────────────┐
│                    DART Cache (JSON Files)                    │
│    data/dart_cache/{corp_code}/                               │
│      ├── company_info.json                                   │
│      ├── financial_statements.json                           │
│      ├── business_report_sections.json                       │
│      └── segment_revenue.json                                │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│               Excel I/O (확장)                                │
│    기존 컬럼 + 신규 컬럼 (evidence_summary, bm_summary 등)   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow (전체 파이프라인)

```
입력: ticker, name
  │
  ▼
[1] DART Client (확장)
  ├── corpCode.xml → corp_code
  ├── company.json → 기업개황 (KSIC)
  ├── fnltt_singl_acnt → 재무제표 (매출/영업이익/자산/부채)
  ├── segmnt_revenue → 사업부문별 매출
  └── document.xml → 사업보고서 원본 (ZIP → XML/HTML 파싱)
  │
  ▼
[2] KSIC → GICS 매핑 (수정)
  ├── 건설(41xxx), 금융(64-66xxx) 등 누락 섹터 추가
  └── Fallback '4' → Industrials로 수정
  │
  ▼
[3] BM Analyzer (Step C)
  ├── 고객 ← 주요 고객 + 매출 구성
  ├── 수익모델 ← 사업부문별 매출 + 재무제표
  ├── 차별점 ← 경쟁현황 + 연구개발
  ├── 비용구조 ← 재무제표 (매출원가율, 판관비율)
  ├── 성장조건 ← 산업 특성 + 매출 추이
  └── 실패조건 ← 리스크 요인 + 부채비율
  │
  ▼
[4] Evidence Extractor (Step B→D)
  ├── 해자 유형별 패턴 매칭 (10가지)
  ├── 사업보고서 텍스트에서 증거 문장 추출
  └── 각 증거에 quality_score 부여
  │
  ▼
[5] Moat Evaluator v2 (Step D)
  ├── 증거 문장 → 해자 유형별 점수
  ├── 3점+ = 공시 증거 필수 (없으면 2점 하향)
  ├── 4점+ = 반증 체크 + 검증용desc 필수
  └── 최종 해자강도 = 유형별 가중 평균
  │
  ▼
[6] Sustainability Checker (Step E)
  ├── 구조적 성장 체크 (매출 CAGR)
  ├── 경쟁 축 변화 체크 (경쟁현황 분석)
  └── 해자 유지비용 체크 (CAPEX/매출)
  │
  ▼
[7] Excel Output (확장)
  ├── 기존: core_sector_top, core_sector_sub, core_desc, 해자강도, 해자DESC, 검증용desc
  └── 신규: evidence_summary, bm_summary, sustainability_notes
```

### 2.3 Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| BM Analyzer | DART Client | 사업보고서 + 재무데이터 필요 |
| Evidence Extractor | DART Client | 사업보고서 텍스트 필요 |
| Moat Evaluator v2 | BM Analyzer, Evidence Extractor | BM 분해 + 증거 모두 필요 |
| Sustainability Checker | DART Client, Moat Evaluator v2 | 재무 추이 + 해자 점수 필요 |
| Excel I/O | All components | 최종 결과 저장 |

---

## 3. Data Model

### 3.1 DART 캐시 데이터 (파일시스템 JSON)

```
data/dart_cache/
├── corp_codes.json             # 전체 기업 고유번호 (corpCode.xml 캐시)
└── {corp_code}/
    ├── company_info.json       # 기업개황
    ├── financials.json         # 재무제표 (3년치)
    ├── segments.json           # 사업부문별 매출
    └── report_sections.json    # 사업보고서 주요 섹션 텍스트
```

#### company_info.json

```python
{
    "corp_code": "00126380",
    "corp_name": "삼성전자",
    "stock_code": "005930",
    "induty_code": "26110",       # KSIC
    "est_dt": "19690113",
    "hm_url": "https://www.samsung.com",
    "fetched_at": "2026-02-10T12:00:00"
}
```

#### financials.json

```python
{
    "corp_code": "00126380",
    "years": {
        "2023": {
            "revenue": 258935000000000,           # 매출
            "operating_income": 6566700000000,     # 영업이익
            "net_income": 15487100000000,          # 당기순이익
            "total_assets": 455905500000000,       # 자산총계
            "total_liabilities": 92228200000000,   # 부채총계
            "total_equity": 363677300000000,       # 자본총계
            "operating_margin": 0.0254,            # 영업이익률
            "roe": 0.0426,                         # ROE
            "debt_ratio": 0.2535                   # 부채비율
        },
        "2022": { ... },
        "2021": { ... }
    },
    "fetched_at": "2026-02-10T12:00:00"
}
```

#### segments.json

```python
{
    "corp_code": "00126380",
    "year": "2023",
    "segments": [
        {
            "name": "DS (반도체)",
            "revenue": 66720000000000,
            "ratio": 0.258,
            "operating_income": -14880000000000
        },
        {
            "name": "MX (모바일)",
            "revenue": 107700000000000,
            "ratio": 0.416,
            "operating_income": 13290000000000
        }
    ],
    "fetched_at": "2026-02-10T12:00:00"
}
```

#### report_sections.json

```python
{
    "corp_code": "00126380",
    "year": "2023",
    "rcept_no": "20240315000123",
    "sections": {
        "business_overview": "당사는 반도체, 디스플레이, ...",
        "major_products": "메모리반도체: DRAM, NAND Flash ...",
        "competition": "메모리 시장은 삼성전자, SK하이닉스, 마이크론 ...",
        "rnd": "연구개발비: 24.9조원 (매출 대비 9.6%) ...",
        "risk_factors": "반도체 업황 사이클 ...",
        "facilities": "평택, 화성, 시안 등 글로벌 생산거점 ..."
    },
    "parse_quality": {
        "total_sections_found": 6,
        "total_text_length": 45000,
        "parsed_successfully": true
    },
    "fetched_at": "2026-02-10T12:00:00"
}
```

### 3.2 BM Analysis 결과

```python
@dataclass
class BMElement:
    """BM 6요소 중 하나"""
    question: str           # "고객은 누구인가"
    answer: str             # "글로벌 IT 기업, 통신사, 소비자"
    label: str              # "confirmed" | "estimated"
    source: str             # "사업보고서 2023 - 주요 고객"
    details: Dict           # 요소별 추가 정보

@dataclass
class BMAnalysis:
    """BM 6요소 분해 결과"""
    company: str
    ticker: str
    customer: BMElement              # 1. 고객은 누구인가
    revenue_model: BMElement         # 2. 무엇으로 돈을 버는가
    differentiation: BMElement       # 3. 왜 이 회사인가
    cost_structure: BMElement        # 4. 비용 구조/레버리지
    growth_condition: BMElement      # 5. 성장이 되는 조건
    failure_condition: BMElement     # 6. 망하는 조건
    completeness: float              # 0.0~1.0 (확인 비율)
```

### 3.3 Evidence 데이터

```python
@dataclass
class Evidence:
    """단일 증거 문장"""
    moat_type: str              # "전환비용", "네트워크 효과" 등
    evidence_text: str          # 원문 인용 또는 요약
    source: str                 # "사업보고서 2023 - 사업의 내용"
    confidence: str             # "confirmed" | "estimated"
    has_numbers: bool           # 구체적 수치 포함 여부
    quality_score: float        # 0.5 ~ 2.0

@dataclass
class EvidenceCollection:
    """회사별 증거 모음"""
    company: str
    ticker: str
    evidences: List[Evidence]
    total_quality: float        # 전체 quality_score 합계
    coverage: Dict[str, int]    # 해자 유형별 증거 개수
```

### 3.4 Moat Evaluation 결과

```python
@dataclass
class MoatScore:
    """해자 유형별 점수"""
    moat_type: str              # "전환비용"
    score: int                  # 1-5
    evidence_count: int         # 증거 개수
    reasoning: str              # "공시 증거: ... (quality 1.5)"
    downgraded: bool            # 증거 부족으로 하향 여부
    downgrade_reason: str       # "3점→2점: 공시 증거 없음"

@dataclass
class MoatEvaluation:
    """최종 해자 평가 결과"""
    company: str
    ticker: str
    moat_strength: int                  # 최종 해자강도 1-5
    scores: Dict[str, MoatScore]        # 유형별 점수
    total_score: int                    # 총점 (/50)
    evidence_based: bool                # 증거 기반 여부
    verification_desc: Optional[str]    # 4점+ 검증용 DESC
    sustainability: Optional[Dict]      # Step E 결과
    classification: Dict                # GICS 분류
    bm_analysis: BMAnalysis             # BM 분해 결과
    core_desc: str                      # 사업 설명
    moat_desc: str                      # 해자 DESC
```

---

## 4. Module Specifications

### 4.1 DART Client 확장 (`dart_client.py`)

#### 신규 메서드

```python
class DARTClient:
    # 기존 메서드 유지
    def get_corp_code(self, stock_code: str) -> Optional[str]: ...
    def get_company_info(self, corp_code: str) -> Optional[Dict]: ...

    # 신규: 재무제표 (DS003)
    def get_financial_statements(
        self,
        corp_code: str,
        bsns_year: str = "2023",
        reprt_code: str = "11011"   # 사업보고서
    ) -> Optional[Dict]:
        """
        DART API: fnltt_singl_acnt (단일회사 주요계정)

        Returns: {
            'revenue': int, 'operating_income': int,
            'net_income': int, 'total_assets': int,
            'total_liabilities': int, 'total_equity': int
        }
        """

    # 신규: 사업부문별 매출 (DS002)
    def get_segment_revenue(
        self,
        corp_code: str,
        bsns_year: str = "2023",
        reprt_code: str = "11011"
    ) -> Optional[List[Dict]]:
        """
        DART API: segmnt_revenue 또는 주요제품매출

        Returns: [
            {'name': 'DS(반도체)', 'revenue': int, 'ratio': float}
        ]
        """

    # 신규: 사업보고서 원본 다운로드 (DS001)
    def download_business_report(
        self,
        corp_code: str,
        bsns_year: str = "2023"
    ) -> Optional[str]:
        """
        DART API: 공시서류원본파일

        Process:
        1. list.json → 사업보고서 접수번호(rcept_no) 조회
        2. document.xml → 문서 목록
        3. 원본파일 다운로드 (ZIP)
        4. XML/HTML 파싱 → 텍스트 추출

        Returns: 사업보고서 원본 텍스트 (전체)
        """

    # 신규: 캐시 관리
    def _get_cache_path(self, corp_code: str, data_type: str) -> str:
        """캐시 파일 경로 반환"""

    def _load_cache(self, corp_code: str, data_type: str) -> Optional[Dict]:
        """캐시 로드 (만료 체크 포함)"""

    def _save_cache(self, corp_code: str, data_type: str, data: Dict):
        """캐시 저장"""
```

#### DART API 엔드포인트 상세

| API | URL | 주요 파라미터 | 응답 |
|-----|-----|-------------|------|
| 기업개황 | `/company.json` | corp_code | JSON (induty_code, est_dt, hm_url) |
| 재무제표 | `/fnltt_singl_acnt.json` | corp_code, bsns_year, reprt_code, fs_div | JSON (account_nm, thstrm_amount) |
| 공시 목록 | `/list.json` | corp_code, bgn_de, end_de, pblntf_ty | JSON (rcept_no, report_nm) |
| 원본파일 | `/document.xml` | rcept_no | XML (dcm_no, file info) |
| 원본 다운 | 별도 URL | dcm_no | ZIP (HTML/XML files) |

#### 캐시 전략

```python
CACHE_CONFIG = {
    'company_info': {'ttl_days': 30},       # 자주 안 변함
    'financials': {'ttl_days': 90},          # 분기별 업데이트
    'segments': {'ttl_days': 90},
    'report_sections': {'ttl_days': 365},    # 연간 보고서
    'corp_codes': {'ttl_days': 7}            # 신규 상장 반영
}
```

### 4.2 사업보고서 파서 (`dart_report_parser.py`)

```python
class DARTReportParser:
    """DART 사업보고서 원본파일 파싱"""

    # 추출 대상 섹션
    TARGET_SECTIONS = {
        'business_overview': [
            '사업의 내용', 'II. 사업의 내용', '1. 사업의 개요'
        ],
        'major_products': [
            '주요 제품', '주요 제품 및 서비스', '주요제품등의 현황'
        ],
        'competition': [
            '경쟁 상황', '시장 현황', '산업의 특성',
            '경쟁요소', '시장점유율'
        ],
        'rnd': [
            '연구개발', '연구 및 개발', '연구개발활동',
            '특허', '지식재산'
        ],
        'risk_factors': [
            '위험 요인', '리스크', '사업의 위험'
        ],
        'facilities': [
            '생산설비', '주요 설비', '생산능력'
        ],
        'major_customers': [
            '주요 고객', '매출처', '거래처'
        ]
    }

    def parse_report(self, html_content: str) -> Dict[str, str]:
        """
        사업보고서 HTML/XML → 섹션별 텍스트

        Args:
            html_content: 원본파일 내용

        Returns:
            {'business_overview': "...", 'major_products': "...", ...}
        """

    def _extract_section(
        self, soup: BeautifulSoup, section_titles: List[str]
    ) -> Optional[str]:
        """
        제목 패턴으로 섹션 찾기

        전략:
        1. <h2>, <h3>, <strong> 태그에서 제목 검색
        2. 제목 발견 후 다음 제목 전까지 텍스트 추출
        3. 테이블 데이터 포함 (매출 구성 등)
        """

    def _clean_text(self, text: str) -> str:
        """
        텍스트 정제
        - HTML 태그 제거
        - 과도한 공백 제거
        - 최대 길이 제한 (섹션당 5000자)
        """
```

### 4.3 BM Analyzer (`bm_analyzer.py`)

```python
class BMAnalyzer:
    """BM 6요소 기계적 분해 (Step C)"""

    def analyze(
        self,
        company_name: str,
        report_sections: Dict[str, str],
        financials: Dict,
        segments: List[Dict]
    ) -> BMAnalysis:
        """
        6요소 분해 실행

        각 요소별 데이터 매핑:
        1. 고객 ← major_customers + segments
        2. 수익모델 ← segments + financials
        3. 차별점 ← competition + rnd
        4. 비용구조 ← financials (매출원가율, 판관비율)
        5. 성장조건 ← business_overview + revenue trend
        6. 실패조건 ← risk_factors + debt_ratio
        """

    def _extract_customer(
        self,
        report_sections: Dict[str, str],
        segments: List[Dict]
    ) -> BMElement:
        """
        1. 고객은 누구인가

        데이터 소스 우선순위:
        1) 사업보고서 '주요 고객' 섹션 → [확인]
        2) 사업부문별 매출에서 B2B/B2C 추정 → [추정]
        3) 산업 일반론 → [추정]
        """

    def _extract_revenue_model(
        self,
        segments: List[Dict],
        financials: Dict
    ) -> BMElement:
        """
        2. 무엇으로 돈을 버는가 (단가 × 물량 × 반복성)

        데이터 소스:
        1) 사업부문별 매출 → 매출 구성비 [확인]
        2) 영업이익률 → 수익성 [확인]
        3) 반복성 = 매출 변동성(3년) → [확인]
        """

    def _extract_differentiation(
        self,
        report_sections: Dict[str, str]
    ) -> BMElement:
        """
        3. 왜 이 회사인가 (차별 포인트)

        데이터 소스:
        1) 사업보고서 '경쟁 상황' → 경쟁우위 언급 [확인]
        2) '연구개발' → 기술적 차별화 [확인]
        3) 매출 집중도 → 특화 정도 [확인]
        """

    def _extract_cost_structure(
        self,
        financials: Dict
    ) -> BMElement:
        """
        4. 비용 구조/레버리지

        계산:
        - 매출원가율 = 매출원가 / 매출
        - 판관비율 = 판관비 / 매출
        - 고정비 비중 추정 (산업별 기본값)
        - 영업레버리지 = 매출 변화율 / 영업이익 변화율
        """

    def _extract_growth_condition(
        self,
        report_sections: Dict[str, str],
        financials: Dict
    ) -> BMElement:
        """
        5. 성장이 되는 조건

        분석:
        1) 매출 CAGR (3년) → 성장 추세 [확인]
        2) 사업보고서 '산업 특성' → 시장 성장 [확인/추정]
        3) 수요/공급/규제/전환비용 키워드 검색
        """

    def _extract_failure_condition(
        self,
        report_sections: Dict[str, str],
        financials: Dict
    ) -> BMElement:
        """
        6. 망하는 조건

        분석:
        1) 사업보고서 '위험 요인' → 리스크 [확인]
        2) 부채비율 → 재무 위험 [확인]
        3) 경쟁 심화, 기술 변화 키워드
        """

    def generate_bm_summary(self, bm: BMAnalysis) -> str:
        """BM 분해 요약 텍스트 생성 (Excel 저장용)"""
```

### 4.4 Evidence Extractor (`evidence_extractor.py`)

```python
class EvidenceExtractor:
    """증거 문장 추출 엔진 (Rule-based)"""

    # 해자 유형별 증거 패턴
    MOAT_PATTERNS = {
        '전환비용': {
            'keywords': [
                r'고객사.*통합', r'장기.*계약', r'인증.*요구',
                r'전환.*비용', r'커스터마이징', r'독점.*공급',
                r'시스템.*연동', r'교체.*어렵', r'호환.*불가'
            ],
            'anti_patterns': [       # 이 패턴이 있으면 전환비용 아님
                r'고객.*자유.*선택', r'경쟁.*입찰'
            ]
        },
        '네트워크 효과': {
            'keywords': [
                r'사용자.*증가.*가치', r'플랫폼.*효과',
                r'양면.*시장', r'커뮤니티', r'회원.*수.*만명',
                r'MAU.*만', r'DAU'
            ],
            'anti_patterns': [
                r'네트워크.*효과.*없'
            ]
        },
        '규모의 경제': {
            'keywords': [
                r'시장.*점유율.*\d+%', r'매출.*\d+조',
                r'생산.*규모', r'고정비.*분산', r'원가.*절감',
                r'CAPEX.*\d+', r'설비.*투자', r'생산능력.*증가'
            ],
            'anti_patterns': []
        },
        '브랜드': {
            'keywords': [
                r'브랜드.*인지도', r'브랜드.*가치',
                r'고객.*충성', r'프리미엄.*가격',
                r'1위', r'No\.\s*1', r'리딩.*기업'
            ],
            'anti_patterns': [
                r'브랜드.*약', r'인지도.*낮'
            ]
        },
        '규제/허가': {
            'keywords': [
                r'인허가', r'라이선스', r'면허',
                r'규제.*승인', r'식약처', r'진입장벽',
                r'독점.*지위', r'정부.*인가'
            ],
            'anti_patterns': [
                r'진입장벽.*낮', r'규제.*완화'
            ]
        },
        '데이터/학습': {
            'keywords': [
                r'데이터.*축적', r'AI.*학습', r'빅데이터',
                r'알고리즘.*개선', r'자동화.*시스템'
            ],
            'anti_patterns': []
        },
        '특허/공정': {
            'keywords': [
                r'특허.*\d+건', r'특허.*등록', r'고유.*기술',
                r'독자.*공정', r'핵심.*기술', r'연구.*개발.*\d+억'
            ],
            'anti_patterns': []
        },
        '공급망/설치기반': {
            'keywords': [
                r'공급망.*구축', r'설치.*기반', r'유통.*네트워크',
                r'물류.*인프라', r'거래처.*\d+개'
            ],
            'anti_patterns': []
        },
        '락인/표준': {
            'keywords': [
                r'표준.*채택', r'생태계', r'API.*통합',
                r'종속.*효과', r'호환성'
            ],
            'anti_patterns': []
        },
        '원가우위': {
            'keywords': [
                r'원가.*우위', r'저비용', r'원가.*경쟁력',
                r'생산.*효율', r'수직.*계열화',
                r'영업이익률.*\d+%'  # 높은 마진 증거
            ],
            'anti_patterns': [
                r'원가.*부담', r'비용.*증가'
            ]
        }
    }

    def extract_evidences(
        self,
        report_sections: Dict[str, str],
        financials: Dict = None
    ) -> EvidenceCollection:
        """
        사업보고서에서 해자 증거 추출

        Process:
        1. 각 해자 유형별 keyword 패턴 매칭
        2. 매칭된 문장 추출 (전후 문맥 포함)
        3. anti_pattern 체크 (해당되면 제외)
        4. quality_score 부여
        5. 재무 데이터 기반 추가 증거 생성
        """

    def _extract_text_evidence(
        self,
        text: str,
        moat_type: str,
        source: str
    ) -> List[Evidence]:
        """
        텍스트에서 특정 해자 유형 증거 추출

        quality_score 기준:
        - 0.5: 일반적 언급 (키워드만 존재)
        - 1.0: 구체적 설명 (50자 이상)
        - 1.5: 수치 포함 (%, 억, 조 등)
        - 2.0: 수치 + 비교 (경쟁사 대비, 시장 점유율 등)
        """

    def _extract_financial_evidence(
        self,
        financials: Dict
    ) -> List[Evidence]:
        """
        재무 데이터 기반 자동 증거 생성

        규칙:
        - 영업이익률 > 15% → '원가우위' 증거 (quality 1.5)
        - 매출 CAGR > 15% → '성장' 증거 (quality 1.0)
        - R&D/매출 > 5% → '특허/공정' 증거 (quality 1.0)
        - 시장점유율 언급 + 1위 → '규모의 경제' 증거 (quality 2.0)
        """
```

### 4.5 Moat Evaluator v2 (`moat_evaluator_v2.py`)

```python
class MoatEvaluatorV2:
    """증거 기반 해자 평가 (Step D)"""

    # 해자 유형 10가지
    MOAT_TYPES = [
        'switching_costs',      # 전환비용
        'network_effect',       # 네트워크 효과
        'economies_of_scale',   # 규모의 경제
        'brand',                # 브랜드
        'regulatory',           # 규제/허가
        'data_learning',        # 데이터/학습
        'patents',              # 특허/공정
        'supply_chain',         # 공급망/설치기반
        'lock_in',              # 락인/표준
        'cost_leadership'       # 원가우위
    ]

    # 증거 기반 점수 규칙
    SCORE_RULES = {
        1: {'min_quality': 0,    'evidence_required': False, 'description': '해자 없음'},
        2: {'min_quality': 0,    'evidence_required': False, 'description': '약한 해자 (추정)'},
        3: {'min_quality': 2.0,  'evidence_required': True,  'description': '보통 해자 (공시 증거)'},
        4: {'min_quality': 3.5,  'evidence_required': True,  'description': '강한 해자 (증거+반증체크)'},
        5: {'min_quality': 5.0,  'evidence_required': True,  'description': '구조적 해자 (증거+지속가능성)'}
    }

    def evaluate(
        self,
        company_name: str,
        ticker: str,
        evidence_collection: EvidenceCollection,
        bm_analysis: BMAnalysis,
        classification: Dict
    ) -> MoatEvaluation:
        """
        증거 기반 해자 평가 실행

        핵심 로직:
        1. 해자 유형별 증거 quality_score 합산
        2. quality_score → 점수 변환 (SCORE_RULES 기반)
        3. 3점+ 검증: 공시 증거 있는지 확인
        4. 4점+ 검증: 반증 체크, 검증용desc 생성
        5. 최종 해자강도 = 상위 5개 유형 평균 (반올림)
        """

    def _score_single_moat_type(
        self,
        moat_type: str,
        evidences: List[Evidence],
        bm_analysis: BMAnalysis
    ) -> MoatScore:
        """
        단일 해자 유형 점수 부여

        Process:
        1. 해당 유형 증거 수집
        2. quality_score 합산
        3. 점수 결정:
           - quality >= 5.0 → 5점 (후보, Step E 검증 후 확정)
           - quality >= 3.5 → 4점 (후보, 반증 체크 후 확정)
           - quality >= 2.0 → 3점 (공시 증거 있음)
           - quality >= 0.5 → 2점 (약한 증거)
           - quality < 0.5  → 1점 (증거 없음)
        4. 증거 부족 시 하향 조정
        """

    def _validate_high_score(
        self,
        score: int,
        evidences: List[Evidence]
    ) -> Tuple[int, str]:
        """
        3점+ 검증 로직

        Rules:
        - 3점: confirmed evidence가 1개 이상 있어야 함
        - 4점: confirmed evidence 2개+ AND has_numbers=True 1개+
        - 5점: 4점 조건 + sustainability check 통과 필요

        위반 시 하향 조정 + 사유 기록
        """

    def _generate_verification_desc(
        self,
        company_name: str,
        moat_strength: int,
        scores: Dict[str, MoatScore],
        bm_analysis: BMAnalysis
    ) -> str:
        """
        4점+ 검증용 DESC 생성

        포맷:
        [검증용 DESC - {회사명} 해자강도 {N}]
        1. 주요 증거: (출처 포함)
        2. 경쟁사 대비 우위: (BM 차별점)
        3. 반증 체크: (잠재 위협)
        4. 지속가능성: (Step E 연동)
        [검증 필요 항목]
        """

    def _calculate_final_strength(
        self,
        scores: Dict[str, MoatScore]
    ) -> int:
        """
        최종 해자강도 계산

        방법:
        1. 10가지 유형 점수 중 상위 5개 선택
        2. 평균 계산 후 반올림
        3. 범위: 1~5

        이유: 모든 유형에서 높을 필요 없음,
        핵심 해자 유형이 강하면 전체 해자 강함
        """

    def generate_moat_desc(
        self,
        evaluation: MoatEvaluation
    ) -> str:
        """
        해자DESC 생성 (Excel 저장용)

        포맷 (v2):
        해자강도: {N}/5 ({description})

        [증거 기반 평가]
        전환비용 ({score}점):
        {✓/△/❌} {reasoning}
        ...

        [BM 요약]
        고객: {customer} [{label}]
        수익: {revenue_model} [{label}]

        [지속가능성]
        {sustainability notes}

        [출처: DART 사업보고서 {year}, 증거 기반 평가]
        """
```

### 4.6 Sustainability Checker (`sustainability_checker.py`)

```python
class SustainabilityChecker:
    """지속가능성 검증 (Step E)"""

    def check(
        self,
        company_name: str,
        financials: Dict,
        report_sections: Dict[str, str],
        moat_strength: int
    ) -> Dict:
        """
        3가지 지속가능성 체크

        Returns: {
            'structural_growth': {
                'positive': bool,
                'reason': str,
                'data': {'revenue_cagr': float, 'industry_growth': str}
            },
            'competition_shift': {
                'risk': 'low' | 'medium' | 'high',
                'reason': str,
                'triggers': [str]    # 발견된 변화 요인
            },
            'maintenance_cost': {
                'excessive': bool,
                'reason': str,
                'data': {'capex_ratio': float, 'rnd_ratio': float}
            },
            'adjusted_strength': int,
            'warnings': [str]
        }
        """

    def _check_structural_growth(
        self,
        financials: Dict,
        report_sections: Dict[str, str]
    ) -> Dict:
        """
        1. 구조적 성장인지

        판단 기준:
        - 매출 CAGR (3년) >= 5% → positive
        - 사업보고서 '산업 특성'에서 '성장', '확대' 키워드
        - '축소', '감소', '쇠퇴' 키워드 → negative
        """

    def _check_competition_shift(
        self,
        report_sections: Dict[str, str]
    ) -> Dict:
        """
        2. 경쟁의 축이 바뀌는지

        판단 기준:
        - '기술 변화', '규제 변경', '원가 구조 변화' 키워드
        - '신규 진입', '대체재', '해외 경쟁' 키워드 → risk
        - 변화 요인 2개 이상 → high risk
        """

    def _check_maintenance_cost(
        self,
        financials: Dict
    ) -> Dict:
        """
        3. 해자 유지비용이 과도한지

        판단 기준:
        - CAPEX/매출 > 30% → 경고 (설비 집약)
        - R&D/매출 > 15% → 경고 (기술 유지 고비용)
        - 두 항목 합계 > 40% → 심각 경고
        """

    def _adjust_strength(
        self,
        moat_strength: int,
        checks: Dict
    ) -> Tuple[int, List[str]]:
        """
        해자강도 조정

        규칙:
        - 경고 0개: 유지
        - 경고 1개: 유지 (경고만 표시)
        - 경고 2개+: 1점 하향
        - 구조적 성장 negative + competition high: 2점 하향 가능
        """
```

### 4.7 KSIC Mapper 수정 (`ksic_to_gics_mapper.py`)

#### 추가할 KSIC 코드

```python
# 건설업 (현재 누락 - 남광토건 사례)
'41': ('Industrials', 'Capital Goods', 'Construction & Engineering', '건설', '종합건설'),
'411': ('Industrials', 'Capital Goods', 'Building Construction', '건설', '건축'),
'41210': ('Industrials', 'Capital Goods', 'Residential Construction', '건설', '주거건설'),
'41221': ('Industrials', 'Capital Goods', 'Commercial Construction', '건설', '건물건설업'),
'42': ('Industrials', 'Capital Goods', 'Civil Engineering', '건설', '토목'),
'421': ('Industrials', 'Capital Goods', 'Road & Rail', '건설', '도로/철도'),
'422': ('Industrials', 'Capital Goods', 'Utility Construction', '건설', '배관/전기'),

# 금융 (일부 누락)
'651': ('Financials', 'Insurance', 'Life Insurance', '보험', '생명보험'),
'652': ('Financials', 'Insurance', 'Property Insurance', '보험', '손해보험'),
'66': ('Financials', 'Diversified Financials', 'Financial Services', '금융', '금융보조'),
'661': ('Financials', 'Diversified Financials', 'Securities', '증권', '증권사'),

# 전기/가스/수도 (KSIC 35xxx)
'351': ('Utilities', 'Utilities', 'Electric Utilities', '유틸리티', '전력'),
'352': ('Utilities', 'Utilities', 'Gas Utilities', '유틸리티', '가스'),
'36': ('Utilities', 'Utilities', 'Water Utilities', '유틸리티', '수도'),

# 운수/창고 (KSIC 49-52)
'49': ('Industrials', 'Transportation', 'Ground Transportation', '운수', '육상운수'),
'50': ('Industrials', 'Transportation', 'Marine Transportation', '운수', '해운'),
'51': ('Industrials', 'Transportation', 'Air Transportation', '운수', '항공'),
'52': ('Industrials', 'Transportation', 'Logistics', '운수', '물류'),

# 통신 (KSIC 61)
'61': ('Communication Services', 'Telecommunication', 'Telecom Services', '통신', '통신'),

# 음식료 (KSIC 10-12)
'10': ('Consumer Staples', 'Food Products', 'Food Products', '식품', '식품'),
'101': ('Consumer Staples', 'Food Products', 'Meat Processing', '식품', '육가공'),
'107': ('Consumer Staples', 'Food Products', 'Bakery & Confectionery', '식품', '제과'),
'11': ('Consumer Staples', 'Beverages', 'Beverages', '식품', '음료'),
'12': ('Consumer Staples', 'Tobacco', 'Tobacco', '식품', '담배'),
```

#### Fallback 패턴 수정

```python
# 수정 전 (버그):
'4': ('Information Technology', ..., 'IT', 'IT서비스'),

# 수정 후:
'4': ('Industrials', 'Capital Goods', 'Construction & Engineering', '건설', '건설/전기'),
```

### 4.8 Excel I/O 확장 (`excel_io.py`)

#### 신규 컬럼

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `evidence_summary` | text | 주요 증거 요약 (최대 500자) |
| `bm_summary` | text | BM 6요소 요약 (최대 300자) |
| `sustainability_notes` | text | 지속가능성 경고 사항 |
| `evidence_count` | int | 증거 개수 |
| `evidence_based` | bool | 증거 기반 평가 여부 |

기존 컬럼은 모두 유지. `해자DESC` 포맷만 v2로 변경.

---

## 5. Error Handling

### 5.1 DART API 에러

| 상황 | 처리 | Fallback |
|------|------|----------|
| API 키 만료 (Status 901) | 에러 로그 + 즉시 중단 | 캐시 데이터 사용 |
| Rate Limit (Status 020) | 5초 대기 후 재시도 (최대 3회) | 해당 종목 스킵 |
| 종목 없음 (Status 013) | 경고 로그 | DART 미등록 → 기본값 |
| 사업보고서 미제출 | 경고 로그 | 재무제표만으로 분석 |
| 네트워크 오류 | 10초 대기 후 재시도 | 캐시 사용 또는 스킵 |

### 5.2 파싱 에러

| 상황 | 처리 |
|------|------|
| HTML 구조 변경 | 다중 패턴 시도 후 raw text fallback |
| 섹션 못 찾음 | 해당 섹션 빈 값, parse_quality에 기록 |
| 인코딩 오류 | UTF-8 → EUC-KR → CP949 순서로 시도 |

### 5.3 평가 에러 (Fail-Safe)

```python
# 핵심 원칙: 에러 발생 시 항상 보수적 평가
try:
    score = evaluate_moat_type(moat_type, evidences)
except Exception:
    score = MoatScore(
        moat_type=moat_type,
        score=1,                        # 최저점
        evidence_count=0,
        reasoning="평가 실패 - 기본값 적용",
        downgraded=True,
        downgrade_reason="평가 오류로 최저점 적용"
    )
```

---

## 6. Security Considerations

- [x] API 키 환경변수 관리 (config.py, 기존 구현)
- [x] .env 파일 .gitignore 포함 (기존)
- [ ] 캐시 디렉토리 .gitignore 추가 (`data/dart_cache/`)
- [ ] 사업보고서 원본파일 로컬 저장 시 민감정보 주의
- [x] Excel 파일 backup/restore 원자적 연산 (기존)

---

## 7. Test Plan

### 7.1 Test Scope

| Type | Target | Tool |
|------|--------|------|
| 단위 테스트 | 개별 모듈 함수 | pytest |
| 통합 테스트 | DART API → 평가 파이프라인 | pytest + mock |
| 검증 테스트 | 특정 종목 재평가 | 수동 비교 |

### 7.2 Test Cases (Key)

**남광토건 테스트 (필수)**:
- [ ] KSIC 41221 → Industrials/Construction 매핑 확인
- [ ] 해자강도 ≤ 2 (기존 5에서 수정)
- [ ] core_desc에 "건설" 포함
- [ ] evidence_count = 0~2 (건설업은 해자 약함)

**삼성전자 테스트 (필수)**:
- [ ] GICS: Information Technology / Semiconductors 유지
- [ ] 해자강도 4-5 (증거 기반)
- [ ] 증거 문장 3개 이상 (시장 점유율, CAPEX, 기술 등)
- [ ] BM 6요소 모두 [확인] 라벨

**증거 없는 소형주 테스트**:
- [ ] 사업보고서 미제출 종목 → 해자강도 ≤ 2
- [ ] 3점+ 시도 → 증거 없으면 자동 하향

**경계값 테스트**:
- [ ] quality_score 정확히 2.0 → 3점 부여
- [ ] quality_score 1.9 → 2점 유지
- [ ] 4점 후보 + 반증 미체크 → 3점 하향

---

## 8. Implementation Guide

### 8.1 File Structure

```
.agent/skills/stock-moat/utils/
├── config.py                    # (기존) 환경변수
├── dart_client.py               # (확장) Phase 1
├── dart_report_parser.py        # (신규) Phase 1
├── ksic_to_gics_mapper.py       # (수정) Phase 0
├── bm_analyzer.py               # (신규) Phase 2
├── evidence_extractor.py        # (신규) Phase 3
├── moat_evaluator_v2.py         # (신규) Phase 3
├── sustainability_checker.py    # (신규) Phase 5
└── excel_io.py                  # (확장) Phase 6

scripts/stock_moat/
├── moat_analyzer.py             # (폐기 → v2 대체)
├── analyze_new_stocks.py        # (수정) v2 호출
├── analyze_with_evidence.py     # (신규) v2 파이프라인 오케스트레이터
└── validate_moat_quality.py     # (신규) 품질 검증

data/
└── dart_cache/                  # (신규) DART 캐시 디렉토리
    ├── corp_codes.json
    └── {corp_code}/
        ├── company_info.json
        ├── financials.json
        ├── segments.json
        └── report_sections.json
```

### 8.2 Implementation Order

```
Phase 0 (Day 1): 치명적 버그 수정
  ├── [0-1] ksic_to_gics_mapper.py: 건설/금융/유틸리티 KSIC 추가
  ├── [0-2] ksic_to_gics_mapper.py: Fallback '4' → Industrials 수정
  ├── [0-3] moat_analyzer.py: 강제 조정 로직(line 191-192) 제거
  └── [0-4] 남광토건 테스트 → 건설/1-2 확인

Phase 1 (Day 2-5): DART 데이터 확장
  ├── [1-1] dart_client.py: 캐시 인프라 (_get_cache_path, _load_cache, _save_cache)
  ├── [1-2] dart_client.py: get_financial_statements() (DS003)
  ├── [1-3] dart_client.py: get_segment_revenue() (DS002)
  ├── [1-4] dart_client.py: download_business_report() (DS001)
  ├── [1-5] dart_report_parser.py: HTML/XML 파싱 (7개 섹션)
  └── [1-6] 삼성전자 테스트 → 재무 + 사업보고서 파싱 확인

Phase 2 (Day 6-8): BM 분해
  ├── [2-1] bm_analyzer.py: BMElement, BMAnalysis 데이터 클래스
  ├── [2-2] bm_analyzer.py: 6요소 추출 메서드
  ├── [2-3] bm_analyzer.py: generate_bm_summary()
  └── [2-4] 삼성전자 + 남광토건 BM 분해 테스트

Phase 3 (Day 9-13): 증거 기반 평가
  ├── [3-1] evidence_extractor.py: MOAT_PATTERNS (10가지 해자 유형)
  ├── [3-2] evidence_extractor.py: extract_evidences()
  ├── [3-3] moat_evaluator_v2.py: SCORE_RULES + evaluate()
  ├── [3-4] moat_evaluator_v2.py: _validate_high_score()
  ├── [3-5] moat_evaluator_v2.py: generate_moat_desc() (v2 포맷)
  └── [3-6] 삼성전자 (4-5점) + 남광토건 (1-2점) 검증

Phase 4 (Day 14-16): 검증용 DESC
  ├── [4-1] moat_evaluator_v2.py: _generate_verification_desc()
  ├── [4-2] moat_evaluator_v2.py: 반증 체크 로직
  └── [4-3] 4점+ 종목 검증용 DESC 테스트

Phase 5 (Day 17-19): 지속가능성
  ├── [5-1] sustainability_checker.py: 3-체크 구현
  ├── [5-2] sustainability_checker.py: 해자강도 조정 로직
  └── [5-3] 5점 후보 종목 지속가능성 검증 테스트

Phase 6 (Day 20-24): 전체 재분석
  ├── [6-1] analyze_with_evidence.py: 파이프라인 오케스트레이터
  ├── [6-2] excel_io.py: 신규 컬럼 추가
  ├── [6-3] 208개 샘플 재분석
  ├── [6-4] 전문가 리뷰 20개 (수동)
  └── [6-5] 전체 1561개 재분석
```

---

## 9. Coding Convention

### 9.1 Python Conventions

| Target | Rule | Example |
|--------|------|---------|
| 클래스 | PascalCase | `MoatEvaluatorV2`, `BMAnalyzer` |
| 함수 | snake_case | `extract_evidences()`, `check_sustainability()` |
| 상수 | UPPER_SNAKE_CASE | `MOAT_PATTERNS`, `SCORE_RULES` |
| 파일 | snake_case.py | `moat_evaluator_v2.py` |
| dataclass | PascalCase | `Evidence`, `BMElement` |
| 로깅 | logging 모듈 | `logger = logging.getLogger(__name__)` |

### 9.2 데이터 라벨 규칙

| 라벨 | 의미 | 사용 조건 |
|------|------|----------|
| `[확인]` / `confirmed` | 공시 데이터에서 직접 추출 | DART API 응답에서 파싱 |
| `[추정]` / `estimated` | 간접 추론 또는 산업 일반론 | 직접 데이터 없을 때 |
| `[재무]` / `financial` | 재무제표 수치 기반 | 매출, 이익률 등 정량 데이터 |

### 9.3 해자 점수 규칙 (불변)

```
1점: 증거 불필요. 해당 해자 유형 없음.
2점: 증거 불필요. 약한 추정 가능.
3점: 공시/IR 증거 문장 필수. quality >= 2.0.
4점: 공시 증거 + 반증 체크 + 검증용desc. quality >= 3.5.
5점: 4점 + 지속가능성 검증 통과. quality >= 5.0.

위반 시: 항상 하향 조정. 절대 상향 금지.
```

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-10 | Initial design based on Plan document and codebase analysis | Claude Sonnet 4.5 |
