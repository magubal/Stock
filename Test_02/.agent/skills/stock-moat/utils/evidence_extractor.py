"""
Evidence Extractor - Step B->D of MGB-MOAT methodology
Extracts moat evidence from business report text using pattern matching.

10 Moat Types:
전환비용, 네트워크효과, 규모경제, 브랜드, 규제허가,
데이터학습, 특허공정, 공급망, 락인표준, 원가우위

Quality Score:
0.5: Generic mention (keyword only)
1.0: Specific description (30+ Korean chars, 80+ total)
1.5: Includes numbers (%, 억, 조)
2.0: Numbers + comparison (vs competitors, market share)
"""

import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class Evidence:
    """Single evidence item"""
    moat_type: str
    evidence_text: str
    source: str
    confidence: str = "estimated"  # "confirmed" | "estimated"
    has_numbers: bool = False
    quality_score: float = 0.0


@dataclass
class EvidenceCollection:
    """All evidence for a company"""
    company: str
    ticker: str
    evidences: List[Evidence] = field(default_factory=list)

    def add(self, evidence: Evidence):
        self.evidences.append(evidence)

    @property
    def total_quality(self) -> float:
        return sum(e.quality_score for e in self.evidences)

    @property
    def coverage(self) -> Dict[str, int]:
        cov = {}
        for e in self.evidences:
            cov[e.moat_type] = cov.get(e.moat_type, 0) + 1
        return cov

    def get_by_type(self, moat_type: str) -> List[Evidence]:
        return [e for e in self.evidences if e.moat_type == moat_type]

    def quality_by_type(self, moat_type: str) -> float:
        return sum(e.quality_score for e in self.get_by_type(moat_type))


class EvidenceExtractor:
    """Rule-based evidence extraction engine"""

    # Noise text patterns - skip evidence from these contexts
    NOISE_PATTERNS = [
        r'정관\s*[변일]', r'일부\s*개정', r'정관의\s*변경',
        r'주주총회\s*결의', r'배당\s*기산일', r'배당기산일',
        r'연혁', r'임원\s*현황', r'직원\s*현황',
        r'주식\s*매수선택권', r'스톡옵션',
        r'이사회\s*결의', r'감사\s*보고',
        r'전환사채\s*발행', r'신주인수권부사채',
    ]

    MOAT_PATTERNS = {
        '전환비용': {
            'keywords': [
                r'고객사.*통합', r'장기.*계약', r'인증.*요구',
                r'전환\s*비용이?\s*(?:높|크|발생|존재)',
                r'커스터마이징', r'독점.*공급',
                r'시스템.*연동', r'교체.*어렵', r'호환.*불가',
                r'고객.*이탈.*어렵', r'계약.*기간.*\d+년',
            ],
            'anti_patterns': [
                r'고객.*자유.*선택', r'경쟁.*입찰',
                r'전환사채', r'전환권', r'전환가[액격]', r'전환청구',
                r'전환\s*비율', r'전환\s*가격', r'주식\s*전환',
                r'CB\s*전환', r'BW\s*전환', r'사채.*전환',
            ]
        },
        '네트워크효과': {
            'keywords': [
                r'사용자.*증가.*가치', r'플랫폼.*효과',
                r'양면.*시장', r'회원.*수.*\d+만',
                r'MAU.*\d+만', r'DAU.*\d+', r'네트워크\s*효과',
                r'이용자.*\d+만', r'가입자.*\d+만',
            ],
            'anti_patterns': [
                r'네트워크.*효과.*없',
                r'네트워크\s*장비', r'통신\s*네트워크',
            ]
        },
        '규모경제': {
            'keywords': [
                r'시장\s*점유율\s*\d+', r'매출\s*\d+조',
                r'고정비.*분산', r'원가\s*절감.*\d+',
                r'규모의?\s*경제', r'대량\s*생산.*\d+',
            ],
            'anti_patterns': [
                r'규모가?\s*작', r'소규모',
            ]
        },
        '브랜드': {
            'keywords': [
                r'브랜드\s*인지도', r'브랜드\s*가치.*\d+',
                r'고객\s*충성', r'프리미엄\s*가격',
                r'시장\s*(?:점유율|1위).*\d+%', r'No\.?\s*1',
                r'대표\s*브랜드', r'브랜드\s*파워',
            ],
            'anti_patterns': [
                r'브랜드.*약', r'인지도.*낮',
                r'제1위', r'제1호',
                r'1위\s*의결권', r'1위.*주주',
            ]
        },
        '규제허가': {
            'keywords': [
                r'인허가', r'라이선스\s*(?:취득|보유)',
                r'면허\s*(?:취득|보유)',
                r'(?:FDA|식약처|CE)\s*(?:승인|허가|인증)',
                r'진입\s*장벽.*높',
                r'독점\s*지위', r'정부\s*인가',
                r'허가\s*취득', r'GMP\s*인증',
            ],
            'anti_patterns': [
                r'진입장벽.*낮', r'규제.*완화',
                r'규제\s*준수\s*비용',
            ]
        },
        '데이터학습': {
            'keywords': [
                r'데이터\s*축적.*\d+', r'AI\s*학습',
                r'빅데이터.*분석', r'알고리즘\s*개선',
                r'데이터\s*플랫폼', r'머신러닝.*모델',
            ],
            'anti_patterns': [
                r'데이터\s*보호', r'개인정보',
            ]
        },
        '특허공정': {
            'keywords': [
                r'특허.*\d+건', r'특허\s*등록\s*\d+',
                r'고유\s*기술.*보유', r'독자\s*공정',
                r'핵심\s*기술\s*(?:보유|개발)',
                r'R&D.*매출.*\d+%',
            ],
            'anti_patterns': [
                r'특허\s*만료', r'특허\s*분쟁',
            ]
        },
        '공급망': {
            'keywords': [
                r'공급망\s*구축', r'설치\s*기반.*\d+',
                r'유통\s*네트워크.*\d+', r'물류\s*인프라',
                r'거래처\s*\d+', r'납품\s*실적.*\d+',
            ],
            'anti_patterns': [
                r'공급\s*과잉', r'공급\s*불안',
            ]
        },
        '락인표준': {
            'keywords': [
                r'표준\s*채택', r'생태계\s*(?:구축|확장)',
                r'API\s*통합', r'종속\s*효과',
                r'업계\s*표준', r'사실상\s*표준',
            ],
            'anti_patterns': [
                r'호환성\s*(?:문제|이슈)',
            ]
        },
        '원가우위': {
            'keywords': [
                r'원가\s*우위', r'원가\s*경쟁력.*(?:보유|확보)',
                r'생산\s*효율.*\d+', r'수직\s*계열화',
                r'영업이익률\s*\d+%',
            ],
            'anti_patterns': [
                r'원가.*부담', r'비용.*증가',
                r'영업이익률\s*-', r'영업\s*손실',
            ]
        },
    }

    def extract_evidences(
        self,
        company: str,
        ticker: str,
        report_sections: Dict[str, str],
        financials: Dict = None
    ) -> EvidenceCollection:
        """
        Extract moat evidences from business report sections.

        Process:
        1. Pattern match for each moat type in each section
        2. Check anti-patterns (exclude false positives)
        3. Calculate quality_score for each evidence
        4. Generate financial-data-based evidence
        """
        collection = EvidenceCollection(company=company, ticker=ticker)

        section_source_map = {
            'business_overview': '사업보고서 - 사업의 내용',
            'major_products': '사업보고서 - 주요 제품',
            'competition': '사업보고서 - 경쟁 상황',
            'rnd': '사업보고서 - 연구개발',
            'risk_factors': '사업보고서 - 위험 요인',
            'facilities': '사업보고서 - 생산설비',
            'major_customers': '사업보고서 - 주요 고객',
        }

        for section_name, text in report_sections.items():
            if not text or len(text) < 10:
                continue
            source = section_source_map.get(section_name, f'사업보고서 - {section_name}')
            for moat_type in self.MOAT_PATTERNS:
                evidences = self._extract_text_evidence(text, moat_type, source)
                collection.evidences.extend(evidences)

        if financials:
            fin_evidences = self._extract_financial_evidence(financials)
            collection.evidences.extend(fin_evidences)

        return collection

    def _is_noise_context(self, context: str) -> bool:
        """Check if the context is from a noise section"""
        for noise_pat in self.NOISE_PATTERNS:
            if re.search(noise_pat, context, re.IGNORECASE):
                return True
        return False

    def _extract_text_evidence(
        self,
        text: str,
        moat_type: str,
        source: str
    ) -> List[Evidence]:
        """Extract evidence for a specific moat type from text"""
        patterns = self.MOAT_PATTERNS.get(moat_type, {})
        keywords = patterns.get('keywords', [])
        anti_patterns = patterns.get('anti_patterns', [])

        evidences = []

        for keyword_pattern in keywords:
            matches = list(re.finditer(keyword_pattern, text, re.IGNORECASE))
            for match in matches:
                start = max(0, match.start() - 80)
                end = min(len(text), match.end() + 120)
                context = text[start:end].strip()

                # Check anti-patterns
                blocked = False
                for anti in anti_patterns:
                    if re.search(anti, context, re.IGNORECASE):
                        blocked = True
                        break
                if blocked:
                    continue

                # Check noise context
                if self._is_noise_context(context):
                    continue

                quality = self._calculate_quality(context, match.group())

                has_numbers = bool(re.search(r'\d+[%조억만건개사]', context))
                if has_numbers or quality >= 1.5:
                    confidence = "confirmed"
                else:
                    confidence = "estimated"

                evidences.append(Evidence(
                    moat_type=moat_type,
                    evidence_text=context,
                    source=source,
                    confidence=confidence,
                    has_numbers=has_numbers,
                    quality_score=quality
                ))

        # Deduplicate: keep highest quality per unique context
        seen = set()
        unique = []
        for ev in sorted(evidences, key=lambda x: -x.quality_score):
            key = ev.evidence_text[:60]
            if key not in seen:
                seen.add(key)
                unique.append(ev)

        return unique[:2]  # Max 2 per moat type per section

    def _calculate_quality(self, context: str, match_text: str) -> float:
        """Calculate quality score for an evidence (stricter v2)"""
        score = 0.5

        korean_chars = len(re.findall(r'[가-힣]', context))
        has_numbers = bool(re.search(r'\d+[%조억만건개사]', context))

        if korean_chars > 30 and len(context) > 80:
            score = 1.0

        if has_numbers and korean_chars > 20:
            score = 1.5

        if has_numbers and re.search(
            r'(?:점유율|선두|No\.?\s*1|최[대고]|유일|독점|과점|경쟁.*우위|업계.*1위)',
            context
        ):
            score = 2.0

        return score

    def _extract_financial_evidence(self, financials: Dict) -> List[Evidence]:
        """Generate evidence from financial data"""
        evidences = []

        op_margin = financials.get('operating_margin')
        revenue = financials.get('revenue', 0)
        rnd_expenses = financials.get('rnd_expenses', 0)

        # High operating margin -> cost leadership
        if op_margin is not None and op_margin > 0.15:
            evidences.append(Evidence(
                moat_type='원가우위',
                evidence_text=f"영업이익률 {op_margin:.1%} (업종 평균 대비 높음)",
                source="재무제표",
                confidence="confirmed",
                has_numbers=True,
                quality_score=1.5
            ))

        # Large revenue -> economies of scale
        if revenue >= 10_000_000_000_000:  # 10조+
            evidences.append(Evidence(
                moat_type='규모경제',
                evidence_text=f"매출 {revenue/1_000_000_000_000:.1f}조원 (대형 기업)",
                source="재무제표",
                confidence="confirmed",
                has_numbers=True,
                quality_score=1.5
            ))
        elif revenue >= 1_000_000_000_000:  # 1조+
            evidences.append(Evidence(
                moat_type='규모경제',
                evidence_text=f"매출 {revenue/1_000_000_000_000:.1f}조원 (중형 기업)",
                source="재무제표",
                confidence="estimated",
                has_numbers=True,
                quality_score=0.5
            ))

        # High R&D -> patents/process
        if rnd_expenses > 0 and revenue > 0:
            rnd_pct = rnd_expenses / revenue
            if rnd_pct > 0.05:
                evidences.append(Evidence(
                    moat_type='특허공정',
                    evidence_text=f"R&D 투자 매출 대비 {rnd_pct:.1%} ({rnd_expenses/100_000_000:.0f}억원)",
                    source="재무제표",
                    confidence="confirmed",
                    has_numbers=True,
                    quality_score=1.0
                ))

        return evidences
