"""
BM (Business Model) Analyzer - Step C of MGB-MOAT methodology
Mechanically decomposes a company's business model into 6 fixed elements.

6 Elements:
1. Customer (고객은 누구인가)
2. Revenue Model (무엇으로 돈을 버는가)
3. Differentiation (왜 이 회사인가)
4. Cost Structure (비용 구조/레버리지)
5. Growth Condition (성장이 되는 조건)
6. Failure Condition (망하는 조건)

Each element is labeled as [확인] (confirmed from data) or [추정] (estimated).
"""

import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class BMElement:
    """Single BM element analysis result"""
    question: str
    answer: str
    label: str  # "confirmed" | "estimated"
    source: str
    details: Dict = field(default_factory=dict)


@dataclass
class BMAnalysis:
    """Complete BM 6-element decomposition result"""
    company: str
    ticker: str
    customer: Optional[BMElement] = None
    revenue_model: Optional[BMElement] = None
    differentiation: Optional[BMElement] = None
    cost_structure: Optional[BMElement] = None
    growth_condition: Optional[BMElement] = None
    failure_condition: Optional[BMElement] = None

    @property
    def completeness(self) -> float:
        """Ratio of confirmed (vs estimated) elements"""
        elements = [
            self.customer, self.revenue_model, self.differentiation,
            self.cost_structure, self.growth_condition, self.failure_condition
        ]
        confirmed = sum(1 for e in elements if e and e.label == "confirmed")
        total = sum(1 for e in elements if e is not None)
        return confirmed / total if total > 0 else 0.0

    @property
    def elements_list(self) -> List[Optional[BMElement]]:
        return [
            self.customer, self.revenue_model, self.differentiation,
            self.cost_structure, self.growth_condition, self.failure_condition
        ]


class BMAnalyzer:
    """BM 6-element mechanical decomposition (Step C)"""

    def analyze(
        self,
        company_name: str,
        ticker: str,
        report_sections: Dict[str, str],
        financials: Dict,
        segments: Optional[List[Dict]] = None,
        gics_sector: str = '',
        gics_industry: str = ''
    ) -> BMAnalysis:
        """
        Execute 6-element BM decomposition.

        Args:
            company_name: Company name
            ticker: Stock ticker
            report_sections: Parsed report sections from DARTReportParser
            financials: Financial data from DARTClient
            segments: Segment revenue data (optional)
            gics_sector: GICS sector classification
            gics_industry: GICS industry classification

        Returns:
            BMAnalysis with all 6 elements
        """
        bm = BMAnalysis(company=company_name, ticker=ticker)

        bm.customer = self._extract_customer(report_sections, segments)
        bm.revenue_model = self._extract_revenue_model(segments, financials)
        bm.differentiation = self._extract_differentiation(report_sections)
        bm.cost_structure = self._extract_cost_structure(financials)
        bm.growth_condition = self._extract_growth_condition(report_sections, financials)
        bm.failure_condition = self._extract_failure_condition(report_sections, financials)

        return bm

    def _extract_customer(
        self,
        report_sections: Dict[str, str],
        segments: Optional[List[Dict]]
    ) -> BMElement:
        """
        1. Who is the customer?

        Data source priority:
        1) Report 'major_customers' section → [확인]
        2) Segment revenue → B2B/B2C estimation → [추정]
        3) Industry general → [추정]
        """
        # Try major_customers section (explicitly extracted)
        customers_text = report_sections.get('major_customers', '')
        if customers_text and len(customers_text) > 20:
            return BMElement(
                question="고객은 누구인가",
                answer=customers_text[:500],
                label="confirmed",
                source="사업보고서 - 주요 고객",
                details={'raw_length': len(customers_text)}
            )

        # Try to infer from business overview using keywords
        overview = report_sections.get('business_all', '') or report_sections.get('business_summary', '')
        if overview:
            # Look for customer-related keywords
            customer_keywords = [
                # "Supplies to X", "Major customers are X"
                r'(?:주요\s*)?고객[은는이가]?\s*((?:(?!사항|목적).){0,10}.{10,60})',
                r'(?:납품|공급|판매)[하한]다\.\s*((?:(?!사항|목적).){0,10}.{10,60})',
                r'B2[BC]\s*(.{10,40})',
                r'소비자[에게를]?\s*(.{10,40})',
                r'기업[에게를]?\s*(.{10,40})',
                r'수요[처자는은]?\s*(.{10,40})',
            ]
            for pattern in customer_keywords:
                match = re.search(pattern, overview)
                if match:
                    extracted_text = match.group(0).strip()
                    # Filter out noise (SPAC, standard disclaimers)
                    if "기업인수목적" in extracted_text or "기재사항" in extracted_text:
                        continue
                        
                    return BMElement(
                        question="고객은 누구인가",
                        answer=extracted_text[:300],
                        label="confirmed",
                        source="사업보고서 - 사업의 내용",
                        details={'extraction': 'keyword_match'}
                    )

        # Fallback: estimate from segments
        if segments:
            seg_names = [s.get('name', '') for s in segments]
            return BMElement(
                question="고객은 누구인가",
                answer=f"사업부문 기반 추정: {', '.join(seg_names)}",
                label="estimated",
                source="사업부문별 매출",
                details={'segments': seg_names}
            )

        return BMElement(
            question="고객은 누구인가",
            answer="데이터 부족으로 고객 특정 불가",
            label="estimated",
            source="추정",
            details={}
        )

    def _extract_revenue_model(
        self,
        segments: Optional[List[Dict]],
        financials: Dict
    ) -> BMElement:
        """
        2. How does the company make money? (Price x Volume x Recurrence)

        Data sources:
        1) Segment revenue → revenue composition [확인]
        2) Operating margin → profitability [확인]
        3) Revenue volatility (3yr) → recurrence [확인]
        """
        parts = []
        label = "estimated"
        source_parts = []

        # Segment breakdown
        if segments:
            seg_desc = []
            for seg in sorted(segments, key=lambda x: x.get('revenue', 0), reverse=True):
                name = seg.get('name', '?')
                ratio = seg.get('ratio', 0)
                seg_desc.append(f"{name} ({ratio:.0%})")
            parts.append(f"매출 구성: {', '.join(seg_desc)}")
            label = "confirmed"
            source_parts.append("사업부문별 매출")

        # Profitability
        revenue = financials.get('revenue', 0)
        op_margin = financials.get('operating_margin')
        if revenue > 0 and op_margin is not None:
            parts.append(f"영업이익률: {op_margin:.1%}")
            if label == "estimated":
                label = "confirmed" # At least we have financials
            source_parts.append("재무제표")

        # Revenue scale description
        if revenue > 0:
            if revenue >= 1_000_000_000_000:  # 1 trillion+
                parts.append(f"매출 규모: {revenue/1_000_000_000_000:.1f}조원")
            elif revenue >= 100_000_000:  # 100 million+
                parts.append(f"매출 규모: {revenue/100_000_000:.0f}억원")

        answer = '; '.join(parts) if parts else "매출 구조 데이터 부족"
        source = ', '.join(list(set(source_parts))) if source_parts else "추정"

        return BMElement(
            question="무엇으로 돈을 버는가",
            answer=answer,
            label=label,
            source=source,
            details={
                'revenue': revenue,
                'operating_margin': op_margin,
                'segment_count': len(segments) if segments else 0
            }
        )

    def _extract_differentiation(
        self,
        report_sections: Dict[str, str]
    ) -> BMElement:
        """
        3. Why this company? (Competitive advantages)

        Data sources:
        1) Report 'competition' → competitive advantage mentions [확인]
        2) Report 'rnd' → technical differentiation [확인]
        3) Revenue concentration → specialization [확인]
        """
        parts = []
        label = "estimated"
        source_parts = []

        # Competition section
        competition = report_sections.get('competition', '') or report_sections.get('business_all', '')
        if competition:
            # Look for competitive advantage keywords
            advantage_patterns = [
                r'(?:시장\s*)?점유율\s*(?:약?\s*)?(\d+[.%])', # Capture percentage
                r'(?:1위|선두|No\.?\s*1|리딩)',
                r'(?:독점|과점|진입\s*장벽)',
                r'(?:특허|기술\s*우위|기술\s*리더)',
                r'(?:차별\s*[화점]|경쟁\s*우위|경쟁\s*력)',
            ]
            found = []
            
            # Use findall on a reasonable chunk to avoid massive processing
            search_text = competition[:10000] 
            
            for pattern in advantage_patterns:
                matches = re.finditer(pattern, search_text)
                for m in matches:
                    # Provide some context
                    start = max(0, m.start() - 10)
                    end = min(len(search_text), m.end() + 20)
                    context = search_text[start:end].strip().replace('\n', ' ')
                    found.append(context) 

            if found:
                # Deduplicate and limit
                unique_found = list(set(found))[:3]
                parts.append(f"경쟁우위: {', '.join(unique_found)}")
                label = "confirmed"
                source_parts.append("사업보고서")

        # R&D section (if we can identify it, often part of business overview)
        # We search the whole business section for R&D keywords
        business_all = report_sections.get('business_all', '')
        if business_all:
            rnd_patterns = [
                r'연구개발비[:\s]*[\d,.]+[조억만]?\s*원?',
                r'특허[:\s]*[\d,]+\s*건',
                r'매출\s*대비\s*[\d.]+%',
            ]
            found_rnd = []
            for pattern in rnd_patterns:
                matches = re.findall(pattern, business_all[:50000])
                found_rnd.extend(matches)

            if found_rnd:
                unique_rnd = list(set(found_rnd))[:2]
                parts.append(f"R&D: {', '.join(unique_rnd)}")
                label = "confirmed" # Upgrades certainty
                source_parts.append("연구개발")

        answer = '; '.join(parts) if parts else "차별화 요인 데이터 부족"
        source = ', '.join(list(set(source_parts))) if source_parts else "추정"

        return BMElement(
            question="왜 이 회사인가 (차별 포인트)",
            answer=answer,
            label=label,
            source=source,
            details={'has_competition_section': 'competition' in report_sections}
        )

    def _extract_cost_structure(
        self,
        financials: Dict
    ) -> BMElement:
        """
        4. Cost structure and leverage

        Calculations:
        - Cost ratio = COGS / Revenue
        - SGA ratio = SGA / Revenue
        - Fixed cost ratio estimation (industry default)
        """
        revenue = financials.get('revenue', 0)
        cost_ratio = financials.get('cost_ratio')
        sga_ratio = financials.get('sga_ratio')
        op_margin = financials.get('operating_margin')
        debt_ratio = financials.get('debt_ratio')

        parts = []
        if revenue > 0:
            if cost_ratio is not None:
                parts.append(f"매출원가율: {cost_ratio:.1%}")
            if sga_ratio is not None:
                parts.append(f"판관비율: {sga_ratio:.1%}")
            if op_margin is not None:
                parts.append(f"영업이익률: {op_margin:.1%}")
            if debt_ratio is not None:
                parts.append(f"부채비율: {debt_ratio:.0%}")

        if not parts:
            return BMElement(
                question="비용 구조/레버리지",
                answer="재무 데이터 부족",
                label="estimated",
                source="추정",
                details={}
            )

        return BMElement(
            question="비용 구조/레버리지",
            answer='; '.join(parts),
            label="confirmed",
            source="재무제표",
            details={
                'cost_ratio': cost_ratio,
                'sga_ratio': sga_ratio,
                'operating_margin': op_margin,
                'debt_ratio': debt_ratio
            }
        )

    def _extract_growth_condition(
        self,
        report_sections: Dict[str, str],
        financials: Dict
    ) -> BMElement:
        """
        5. What conditions enable growth?

        Analysis:
        1) Revenue CAGR (3yr) → growth trend [확인]
        2) Report 'business_overview' → market growth [확인/추정]
        3) Demand/supply/regulation keywords
        """
        parts = []
        label = "estimated"
        source_parts = []

        # Revenue trend from financials (if we had multi-year, currently single year snapshot passed generally)
        # Note: financials dict usually just has single year 'revenue'. 
        revenue = financials.get('revenue', 0)
        if revenue > 0:
            # Placeholder for trend analysis if we pass multi-year data later
            pass

        # Growth keywords from business overview
        overview = report_sections.get('business_all', '') or report_sections.get('business_summary', '')
        if overview:
            growth_patterns = [
                r'(?:성장|증가|확대)\s*(?:세|추세|전망)',
                r'(?:시장\s*규모)\s*(?:확대|성장)',
                r'(?:수요\s*증가|수요\s*확대)',
                r'CAGR\s*[\d.]+%',
                r'(?:신규\s*시장|신성장)',
            ]
            found = []
            for pattern in growth_patterns:
                matches = re.finditer(pattern, overview[:20000]) # Check first 20k chars
                for m in matches:
                    start = max(0, m.start() - 10)
                    end = min(len(overview), m.end() + 20)
                    found.append(overview[start:end].strip().replace('\n', ' '))
            
            if found:
                unique_found = list(set(found))[:3]
                parts.append(f"성장 키워드: {', '.join(unique_found)}")
                label = "confirmed"
                source_parts.append("사업보고서")

        answer = '; '.join(parts) if parts else "성장 조건 데이터 부족"
        source = ', '.join(list(set(source_parts))) if source_parts else "추정"

        return BMElement(
            question="성장이 되는 조건",
            answer=answer,
            label=label,
            source=source,
            details={}
        )

    def _extract_failure_condition(
        self,
        report_sections: Dict[str, str],
        financials: Dict
    ) -> BMElement:
        """
        6. What conditions lead to failure?

        Analysis:
        1) Report 'risk_factors' → risks [확인]
        2) Debt ratio → financial risk [확인]
        3) Competition intensity keywords
        """
        parts = []
        label = "estimated"
        source_parts = []

        # Financial risk
        debt_ratio = financials.get('debt_ratio')
        if debt_ratio is not None:
            risk_level = "높음" if debt_ratio > 2.0 else "보통" if debt_ratio > 1.0 else "낮음"
            parts.append(f"부채비율 {debt_ratio:.0%} ({risk_level})")
            if debt_ratio > 1.5:
                 parts.append("높은 부채비율 리스크")
            source_parts.append("재무제표")
            label = "confirmed"

        op_margin = financials.get('operating_margin')
        if op_margin is not None and op_margin < 0:
            parts.append(f"영업적자 지속 (영업이익률 {op_margin:.1%})")
            label = "confirmed"

        # Risk factors from report (if we had a specific risk section parser, currently general search)
        overview = report_sections.get('business_all', '')
        if overview:
             # Look for risk keywords
            risk_patterns = [
                 r'(?:위험|리스크|불확실성)',
                 r'(?:경쟁\s*심화|치열)',
                 r'(?:규제\s*강화|제재)',
                 r'(?:환율\s*변동)',
            ]
            found = []
            for pattern in risk_patterns:
                 matches = re.finditer(pattern, overview[:20000])
                 for m in matches:
                     start = max(0, m.start() - 10)
                     end = min(len(overview), m.end() + 20)
                     found.append(overview[start:end].strip().replace('\n', ' '))
            
            if found:
                unique_found = list(set(found))[:3]
                parts.append(f"언급된 리스크: {', '.join(unique_found)}")
                source_parts.append("사업보고서")
                # Don't necessarily upgrade label to confirmed just for keywords unless very specific
        
        answer = '; '.join(parts) if parts else "리스크 데이터 부족"
        source = ', '.join(list(set(source_parts))) if source_parts else "추정"

        return BMElement(
            question="망하는 조건",
            answer=answer,
            label=label,
            source=source,
            details={'debt_ratio': debt_ratio, 'operating_margin': op_margin}
        )

    def generate_bm_summary(self, bm: BMAnalysis) -> str:
        """Generate BM decomposition summary text for Excel storage"""
        lines = []
        labels = {
            'customer': '1.고객',
            'revenue_model': '2.수익모델',
            'differentiation': '3.차별점',
            'cost_structure': '4.비용구조',
            'growth_condition': '5.성장조건',
            'failure_condition': '6.실패조건'
        }

        for attr, name in labels.items():
            elem = getattr(bm, attr, None)
            if elem:
                tag = "[확인]" if elem.label == "confirmed" else "[추정]"
                answer_short = elem.answer[:100]
                lines.append(f"{name} {tag}: {answer_short}")
            else:
                lines.append(f"{name} [미분석]")

        lines.append(f"---")
        lines.append(f"완성도: {bm.completeness:.0%} ({sum(1 for e in bm.elements_list if e and e.label == 'confirmed')}/6 확인)")

        return '\n'.join(lines)


# Test
if __name__ == "__main__":
    analyzer = BMAnalyzer()

    # Sample data (simulating Samsung Electronics)
    report_sections = {
        'business_all': '...... (생략) ...... 당사는 메모리반도체와 시스템반도체를 설계, 제조, 판매하고 있습니다. 주요 고객은 글로벌 IT 기업 및 모바일 제조사입니다. 메모리 시장 점유율은 약 40%로 1위를 유지하고 있습니다. 글로벌 데이터센터 투자 확대로 서버용 수요 증가가 예상됩니다. 다만 미중 무역분쟁 및 환율 변동 리스크가 존재합니다. ......',
        'business_summary': '사업의 개요...',
        'competition': '메모리 반도체 시장은 진입장벽이 높은 과점 시장입니다.',
    }

    financials = {
        'revenue': 258935000000000,
        'operating_income': 6566700000000,
        'operating_margin': 0.0254,
        'cost_of_revenue': 198000000000000,
        'cost_ratio': 0.7647,
        'sga_expenses': 54000000000000,
        'sga_ratio': 0.2085,
        'total_equity': 363677300000000,
        'total_liabilities': 92228200000000,
        'debt_ratio': 0.2535,
        'roe': 0.0426,
        'net_income': 15487100000000,
    }
    
    segments = [
        {'name': 'DX(세트)', 'revenue': 169000000000000, 'ratio': 0.65},
        {'name': 'DS(반도체)', 'revenue': 66000000000000, 'ratio': 0.25},
        {'name': 'SDC(디스플레이)', 'revenue': 30000000000000, 'ratio': 0.11}, # Approx
    ]

    bm = analyzer.analyze("삼성전자", "005930", report_sections, financials, segments)

    print("=" * 60)
    print("BM Analyzer Test - 삼성전자 [Simulation]")
    print("=" * 60)
    print(analyzer.generate_bm_summary(bm))
