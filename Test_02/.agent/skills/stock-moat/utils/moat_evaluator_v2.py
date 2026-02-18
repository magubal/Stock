"""
Moat Evaluator v2 - Step D of MGB-MOAT methodology
Evidence-based moat scoring with strict quality thresholds.

Key Rules:
- Score 1-2: No evidence required
- Score 3+: Must have confirmed evidence from disclosures
- Score 4+: Counter-evidence check + verification DESC required
- Score 5: Sustainability verification required (Step E)
- Fail-safe: Always downgrade on insufficient evidence, never upgrade
"""

import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from evidence_extractor import Evidence, EvidenceCollection
from bm_analyzer import BMAnalysis


@dataclass
class MoatScore:
    """Score for a single moat type"""
    moat_type: str
    score: int  # 1-5
    evidence_count: int
    quality_total: float
    reasoning: str
    downgraded: bool = False
    downgrade_reason: str = ""


@dataclass
class MoatEvaluation:
    """Complete moat evaluation result"""
    company: str
    ticker: str
    moat_strength: int  # Final 1-5
    scores: Dict[str, MoatScore] = field(default_factory=dict)
    total_score: int = 0  # Sum of all type scores (/50)
    evidence_based: bool = False
    verification_desc: Optional[str] = None
    sustainability: Optional[Dict] = None
    classification: Dict = field(default_factory=dict)
    bm_summary: str = ""
    core_desc: str = ""
    moat_desc: str = ""


# Korean labels for moat types
MOAT_TYPE_KR = {
    '전환비용': '전환비용',
    '네트워크효과': '네트워크 효과',
    '규모경제': '규모의 경제',
    '브랜드': '브랜드',
    '규제허가': '규제/허가',
    '데이터학습': '데이터/학습',
    '특허공정': '특허/공정',
    '공급망': '공급망/설치기반',
    '락인표준': '락인/표준',
    '원가우위': '원가 우위',
}

ALL_MOAT_TYPES = list(MOAT_TYPE_KR.keys())

# Score thresholds based on quality_score sum
SCORE_RULES = {
    5: {'min_quality': 5.0, 'description': '구조적 해자 (증거+지속가능성)'},
    4: {'min_quality': 3.5, 'description': '강한 해자 (증거+반증체크)'},
    3: {'min_quality': 2.0, 'description': '보통 해자 (공시 증거)'},
    2: {'min_quality': 0.5, 'description': '약한 해자 (추정)'},
    1: {'min_quality': 0.0, 'description': '해자 없음'},
}


class MoatEvaluatorV2:
    """Evidence-based moat evaluation (Step D)"""

    def evaluate(
        self,
        company_name: str,
        ticker: str,
        evidence_collection: EvidenceCollection,
        bm_analysis: BMAnalysis,
        classification: Dict,
        financials: Dict = None,
        multi_year_financials: Dict = None
    ) -> MoatEvaluation:
        """
        Execute evidence-based moat evaluation.

        Core logic:
        1. Score each moat type based on evidence quality
        2. Validate 3+ scores require disclosure evidence
        3. Validate 4+ scores require counter-evidence check
        4. Validate size requirements (Network Effect etc.)
        5. Calculate final strength from top-5 types
        """
        scores = {}
        if financials is None:
            financials = {}

        # 1. Financial Gatekeeper (1차 관문)
        # 펀더멘털이 약한 기업은 증거 분석 전에 점수 상한선을 설정함
        # 1. Financial Gatekeeper (1차 관문)
        # 펀더멘털이 약한 기업은 증거 분석 전에 점수 상한선을 설정함
        gatekeeper_result = self._apply_financial_gatekeeper(financials, multi_year_financials)
        max_score = gatekeeper_result['max_score']
        gatekeeper_reasons = gatekeeper_result['reasons']

        for moat_type in ALL_MOAT_TYPES:
            evidences = evidence_collection.get_by_type(moat_type)
            score_obj = self._score_single_type(moat_type, evidences)
            
            # Apply Gatekeeper Limit
            if score_obj.score > max_score:
                score_obj.score = max_score
                score_obj.downgraded = True
                reason = " | ".join(gatekeeper_reasons)
                if score_obj.downgrade_reason:
                    score_obj.downgrade_reason = f"펀더멘털 제한({reason}) | " + score_obj.downgrade_reason
                else:
                    score_obj.downgrade_reason = f"펀더멘털 제한({reason})"

            # Apply size-based validation (Revenue < 1000억) (2차 관문)
            new_score, size_reason = self._validate_moat_size(
                moat_type, score_obj.score, financials
            )
            
            if new_score < score_obj.score:
                score_obj.score = new_score
                score_obj.downgraded = True
                if score_obj.downgrade_reason:
                    score_obj.downgrade_reason += f" | {size_reason}"
                else:
                    score_obj.downgrade_reason = size_reason
            
            scores[moat_type] = score_obj

        # Calculate final strength
        moat_strength = self._calculate_final_strength(scores)

        # Generate verification desc if 4+
        # Note: sustainability not yet available here, will be updated by pipeline
        verification_desc = None
        if moat_strength >= 4:
            verification_desc = self._generate_verification_desc(
                company_name, moat_strength, scores, bm_analysis,
                evidence_collection=evidence_collection
            )

        total_score = sum(s.score for s in scores.values())
        evidence_based = any(s.evidence_count > 0 for s in scores.values())

        evaluation = MoatEvaluation(
            company=company_name,
            ticker=ticker,
            moat_strength=moat_strength,
            scores=scores,
            total_score=total_score,
            evidence_based=evidence_based,
            verification_desc=verification_desc,
            classification=classification,
        )

        # Generate descriptions
        evaluation.moat_desc = self.generate_moat_desc(evaluation)

        return evaluation



    def _apply_financial_gatekeeper(self, financials: Dict, multi_year_financials: Dict = None) -> Dict:
        """
        Check financial fundamentals using the LATEST available data.
        Returns max_score and reasons.
        
        Rules:
        - Deficit or OPM < 5%: Max 2.0
        - ROE < 5%: Max 2.5
        
        Exception (Mega Cap / Cyclical):
        - If Revenue > 10 Trillion KRW (Mega Cap), we assume cyclical downturn rather than structural flaw.
        - Cap relaxed to 4.0 (allow evidence to prove moat) even if margins are low.
        """
        max_score = 5
        reasons = []

        # Determine which financials to use (Latest > Current Year)
        target_fin = financials
        target_year = "Current"
        
        if multi_year_financials:
            # Sort years and pick the latest
            years = sorted(multi_year_financials.keys())
            if years:
                latest_year = years[-1]
                latest_fin = multi_year_financials[latest_year]
                
                # Use latest if it has valid data (Revenue check)
                if latest_fin.get('revenue', 0) > 0:
                    target_fin = latest_fin
                    target_year = str(latest_year)

        if not target_fin:
            return {'max_score': 5, 'reasons': []}

        # Check Revenue Size (Mega Cap Exception)
        revenue = target_fin.get('revenue', 0)
        is_mega_cap = revenue >= 10_000_000_000_000  # 10 Trillion KRW
        
        # Check Operating Margin
        opm = target_fin.get('operating_margin')
        
        if opm is not None:
            if opm < 0:
                # Deficit
                if is_mega_cap:
                    max_score = min(max_score, 3) # Mega Cap Deficit: Cap at 3 (Hold)
                    reasons.append(f"적자지속({target_year}, {opm:.1%}) But 초대형주(방어)")
                else:
                    max_score = min(max_score, 2)
                    reasons.append(f"적자지속({target_year}, {opm:.1%})")
            elif opm < 0.05:
                # Low Margin
                if is_mega_cap:
                    # Mega Cap Low Margin: Do NOT cap strictly. Allow evidence to speak.
                    max_score = min(max_score, 4)
                    reasons.append(f"이익률저조({target_year}, {opm:.1%}) But 초대형주(경기민감)")
                else:
                    max_score = min(max_score, 2)
                    reasons.append(f"이익률저조({target_year}, {opm:.1%})")
        
        # Check ROE
        roe = target_fin.get('roe')
        if roe is not None and roe < 0.05:
             if is_mega_cap:
                 # Mega Cap low ROE: Ignore or slight penalty
                 pass
             else:
                 prev_max = max_score
                 max_score = min(max_score, 2)  # Strict
                 if max_score < prev_max:
                     reasons.append(f"ROE저조({target_year}, {roe:.1%})")
        
        return {'max_score': max_score, 'reasons': reasons}

    def _score_single_type(
        self,
        moat_type: str,
        evidences: List[Evidence]
    ) -> MoatScore:
        """Score a single moat type based on evidence"""
        quality_total = sum(e.quality_score for e in evidences)
        evidence_count = len(evidences)

        # Determine raw score from quality
        raw_score = 1
        for score_val in [5, 4, 3, 2]:
            if quality_total >= SCORE_RULES[score_val]['min_quality']:
                raw_score = score_val
                break

        # Validate and potentially downgrade
        final_score, downgrade_reason = self._validate_score(
            raw_score, evidences, quality_total
        )

        # Build reasoning
        kr_name = MOAT_TYPE_KR.get(moat_type, moat_type)
        if evidence_count > 0:
            top_evidence = max(evidences, key=lambda e: e.quality_score)
            reasoning = f"{kr_name}: quality {quality_total:.1f}, 증거 {evidence_count}건"
            if top_evidence.evidence_text:
                reasoning += f" | \"{top_evidence.evidence_text[:80]}...\""
        else:
            reasoning = f"{kr_name}: 증거 없음"

        return MoatScore(
            moat_type=moat_type,
            score=final_score,
            evidence_count=evidence_count,
            quality_total=quality_total,
            reasoning=reasoning,
            downgraded=final_score < raw_score,
            downgrade_reason=downgrade_reason
        )

    def _validate_score(
        self,
        raw_score: int,
        evidences: List[Evidence],
        quality_total: float
    ) -> Tuple[int, str]:
        """
        Validate and potentially downgrade a score.

        Rules (Fail-Safe Downgrade):
        - 3점: At least 1 confirmed evidence required
        - 4점: At least 2 confirmed + 1 with numbers
        - 5점: 4점 conditions + will need sustainability check
        """
        if raw_score <= 2:
            return raw_score, ""

        confirmed = [e for e in evidences if e.confidence == "confirmed"]
        with_numbers = [e for e in evidences if e.has_numbers]

        # 3점 validation
        if raw_score >= 3 and len(confirmed) < 1:
            return 2, f"3점→2점: 공시 확인 증거 없음 (추정만 {len(evidences)}건)"

        # 4점 validation
        if raw_score >= 4:
            if len(confirmed) < 2:
                return 3, f"4점→3점: 확인 증거 부족 ({len(confirmed)}건, 2건 필요)"
            if len(with_numbers) < 1:
                return 3, f"4점→3점: 수치 포함 증거 없음"

        # 5점: keep as candidate, Step E will validate
        return raw_score, ""

    def _validate_moat_size(
        self,
        moat_type: str,
        current_score: int,
        financials: Dict
    ) -> Tuple[int, str]:
        """
        Downgrade moat score if company size is too small for specific moats.
        
        Network Effect / Data Moat / Platform usually require scale.
        If Revenue < 1000억 (Small Cap), hard to claim strong network effect (4+).
        """
        if current_score < 3:
            return current_score, ""
            
        revenue = financials.get('revenue', 0)
        # Threshold: 100 Billion KRW (approx $75M)
        THRESHOLD = 100_000_000_000 
        
        target_moats = ['네트워크효과', '데이터학습', '플랫폼', '규모경제']
        
        if revenue > 0 and revenue < THRESHOLD and moat_type in target_moats:
            return 2, f"{current_score}점→2점: 매출 규모({revenue/100_000_000:.0f}억) 작음 - {moat_type} 약함"
            
        return current_score, ""

    def _calculate_final_strength(self, scores: Dict[str, MoatScore]) -> int:
        """
        Calculate final moat strength.

        Method: Average of top-5 type scores, rounded.
        Reason: Not all types need to be strong; strong core moats matter.
        """
        sorted_scores = sorted(
            scores.values(), key=lambda s: s.score, reverse=True
        )
        top5 = sorted_scores[:5]
        avg = sum(s.score for s in top5) / len(top5) if top5 else 1

        result = round(avg)
        return max(1, min(5, result))

    def _generate_verification_desc(
        self,
        company_name: str,
        moat_strength: int,
        scores: Dict[str, MoatScore],
        bm_analysis: BMAnalysis,
        evidence_collection: EvidenceCollection = None,
        sustainability: Dict = None
    ) -> str:
        """
        Generate verification DESC for 4+ scores.

        Design spec format:
        [검증용 DESC - {회사명} 해자강도 {N}]
        1. 사업 해자 설명: (이 회사의 해자가 무엇인지)
        2. 주요 증거: (출처 포함 원문 인용)
        3. 경쟁사 대비 우위: (BM 차별점)
        4. 반증 체크: (잠재 위협 분석)
        5. 지속가능성: (Step E 연동)
        [검증 필요 항목]
        """
        lines = [
            f"[검증용 DESC - {company_name} 해자강도 {moat_strength}]",
            "",
        ]

        # ── 1. 사업 해자 설명 ───────────────
        lines.append("1. 사업 해자 설명:")
        top_types = sorted(
            [s for s in scores.values() if s.score >= 3],
            key=lambda s: -s.score
        )
        if top_types:
            moat_names = []
            for s in top_types[:3]:
                kr_name = MOAT_TYPE_KR.get(s.moat_type, s.moat_type)
                moat_names.append(f"{kr_name}({s.score}점)")
            lines.append(f"   핵심 해자 유형: {', '.join(moat_names)}")

            # Describe what this moat means for the business
            primary = top_types[0]
            kr_primary = MOAT_TYPE_KR.get(primary.moat_type, primary.moat_type)
            lines.append(f"   주요 해자: {kr_primary} - {primary.reasoning}")
        else:
            lines.append("   3점 이상 해자 유형 없음")

        # ── 2. 주요 증거 (출처 포함 원문 인용) ──
        lines.append("")
        lines.append("2. 주요 증거 (출처 포함):")
        evidence_cited = 0
        if evidence_collection and evidence_collection.evidences:
            # Sort by quality, show top evidences
            sorted_evidences = sorted(
                evidence_collection.evidences,
                key=lambda e: -e.quality_score
            )
            for ev in sorted_evidences[:5]:
                label = "[확인]" if ev.confidence == "confirmed" else "[추정]"
                numbers_tag = " [수치포함]" if ev.has_numbers else ""
                lines.append(f"   {label}{numbers_tag} [{ev.moat_type}] q={ev.quality_score:.1f}")
                # Quote the actual evidence text
                text = ev.evidence_text[:200] if ev.evidence_text else "(텍스트 없음)"
                lines.append(f"      \"{text}\"")
                lines.append(f"      출처: {ev.source}")
                evidence_cited += 1
        if evidence_cited == 0:
            lines.append("   증거 없음 (주의: 4점+ 기준 미달)")

        # ── 3. 경쟁사 대비 우위 (BM 차별점) ──
        lines.append("")
        lines.append("3. 경쟁사 대비 우위:")
        if bm_analysis:
            if bm_analysis.differentiation:
                diff_label = "[확인]" if bm_analysis.differentiation.label == "confirmed" else "[추정]"
                lines.append(f"   차별점 {diff_label}: {bm_analysis.differentiation.answer[:250]}")
            if bm_analysis.revenue_model:
                rev_label = "[확인]" if bm_analysis.revenue_model.label == "confirmed" else "[추정]"
                lines.append(f"   수익모델 {rev_label}: {bm_analysis.revenue_model.answer[:200]}")
            if bm_analysis.failure_condition:
                fail_label = "[확인]" if bm_analysis.failure_condition.label == "confirmed" else "[추정]"
                lines.append(f"   실패조건 {fail_label}: {bm_analysis.failure_condition.answer[:200]}")
        else:
            lines.append("   BM 분석 데이터 없음")

        # ── 4. 반증 체크 (잠재 위협 분석) ──
        lines.append("")
        lines.append("4. 반증 체크:")
        downgraded = [s for s in scores.values() if s.downgraded]
        if downgraded:
            for s in downgraded:
                kr_name = MOAT_TYPE_KR.get(s.moat_type, s.moat_type)
                lines.append(f"   [하향] {kr_name}: {s.downgrade_reason}")
        else:
            lines.append("   하향 조정 없음 (모든 유형 기준 충족)")

        # Check for estimated-only evidence
        anti_evidence_count = 0
        if evidence_collection:
            for ev in evidence_collection.evidences:
                if ev.confidence == "estimated":
                    anti_evidence_count += 1
        if anti_evidence_count > 0:
            lines.append(f"   [주의] 추정 증거 {anti_evidence_count}건 - 확인 증거로 대체 필요")

        # Potential threats from BM failure conditions
        if bm_analysis and bm_analysis.failure_condition:
            lines.append(f"   [위협] {bm_analysis.failure_condition.answer[:200]}")

        # ── 5. 지속가능성 (Step E 연동) ──
        lines.append("")
        lines.append("5. 지속가능성 (Step E):")
        if sustainability:
            adj = sustainability.get('adjusted_strength', moat_strength)
            if adj != moat_strength:
                lines.append(f"   조정: {moat_strength} → {adj}")
            warnings = sustainability.get('warnings', [])
            if warnings:
                for w in warnings:
                    lines.append(f"   [경고] {w}")
            else:
                lines.append("   경고 없음 - 지속가능성 양호")

            # Detail checks if available
            sg = sustainability.get('structural_growth', {})
            if sg:
                status = "양호" if sg.get('positive') else "부정적"
                lines.append(f"   구조적 성장: {status} - {sg.get('reason', '')[:100]}")
            cs = sustainability.get('competition_shift', {})
            if cs:
                lines.append(f"   경쟁 축 변화: 위험도 {cs.get('risk', 'N/A')} - {cs.get('reason', '')[:100]}")
            mc = sustainability.get('maintenance_cost', {})
            if mc:
                status = "과도" if mc.get('excessive') else "적정"
                lines.append(f"   해자 유지비용: {status} - {mc.get('reason', '')[:100]}")
        else:
            lines.append("   (Step E 미실행)")

        # ── 검증 필요 항목 ──
        lines.append("")
        lines.append("[검증 필요 항목]")
        lines.append("- 최신 경쟁 동향 확인 (공시 외 뉴스/리포트)")
        lines.append("- 실제 고객 이탈률/전환 데이터")
        lines.append("- 산업 전문가 의견 교차 검증")
        if sustainability and sustainability.get('warnings'):
            lines.append("- 지속가능성 경고 항목 심층 분석 필요")

        return '\n'.join(lines)

    def generate_moat_desc(self, evaluation: MoatEvaluation) -> str:
        """Generate moat DESC for Excel storage (v2 format)"""
        lines = []

        # Header
        strength_desc = SCORE_RULES.get(evaluation.moat_strength, {}).get('description', '')
        lines.append(f"해자강도: {evaluation.moat_strength}/5 ({strength_desc})")
        lines.append("")

        # Evidence-based scores
        lines.append("[증거 기반 평가]")
        for moat_type in ALL_MOAT_TYPES:
            score = evaluation.scores.get(moat_type)
            if not score:
                continue
            kr_name = MOAT_TYPE_KR.get(moat_type, moat_type)

            if score.score >= 4:
                icon = "●"
            elif score.score >= 3:
                icon = "◐"
            elif score.score >= 2:
                icon = "○"
            else:
                icon = "."

            downgrade = f" ↓{score.downgrade_reason}" if score.downgraded else ""
            lines.append(f"{icon} {kr_name}: {score.score}점 (증거 {score.evidence_count}건, q={score.quality_total:.1f}){downgrade}")

        lines.append("")
        lines.append(f"총점: {evaluation.total_score}/50")
        lines.append(f"증거 기반: {'Yes' if evaluation.evidence_based else 'No'}")

        if evaluation.verification_desc:
            lines.append("")
            lines.append(evaluation.verification_desc)

        lines.append("")
        lines.append("[출처: DART 사업보고서, 증거 기반 평가 v2]")

        return '\r\n'.join(lines)
