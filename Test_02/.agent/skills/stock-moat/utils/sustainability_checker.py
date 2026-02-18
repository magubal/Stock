"""
Sustainability Checker - Step E of MGB-MOAT methodology
Validates whether a company's moat is sustainable through 3 checks:

1. Structural Growth Check: Is growth structural or cyclical?
2. Competition Shift Check: Is the competitive axis changing?
3. Maintenance Cost Check: Is moat maintenance cost excessive?

Also includes Financial Reality Checks:
- Operating margin < -50% -> cap at 2
- Operating margin < 0% -> cap at 3
- Revenue < 100억 + moat 4+ -> cap at 3
- Revenue CAGR < -15% -> cap at 2
"""

import re
import sys
from typing import Dict, List, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class SustainabilityChecker:
    """Moat sustainability verification (Step E)"""

    def check(
        self,
        company_name: str,
        financials: Dict,
        multi_year_financials: Dict = None,
        report_sections: Dict[str, str] = None,
        moat_strength: int = 3
    ) -> Dict:
        """
        Execute 3 sustainability checks + financial reality checks.

        Returns: {
            'structural_growth': {...},
            'competition_shift': {...},
            'maintenance_cost': {...},
            'adjusted_strength': int,
            'warnings': [str]
        }
        """
        if report_sections is None:
            report_sections = {}

        result = {
            'structural_growth': self._check_structural_growth(
                financials, multi_year_financials, report_sections
            ),
            'competition_shift': self._check_competition_shift(report_sections),
            'maintenance_cost': self._check_maintenance_cost(financials),
            'adjusted_strength': moat_strength,
            'warnings': []
        }

        # ── Financial Reality Check ──
        warnings = []
        adjusted = moat_strength

        op_margin = financials.get('operating_margin')
        revenue = financials.get('revenue', 0)
        cagr = result['structural_growth'].get('data', {}).get('revenue_cagr')

        # Critical: Deeply negative margin = moat is NOT working
        if op_margin is not None and op_margin < -0.5:
            cap = 2
            warnings.append(f"영업이익률 {op_margin:.1%}: 해자가 수익을 보호하지 못함 -> 최대 {cap}점")
            adjusted = min(adjusted, cap)
        elif op_margin is not None and op_margin < 0:
            cap = 2
            warnings.append(f"영업이익률 {op_margin:.1%}: 적자 지속 -> 최대 {cap}점")
            adjusted = min(adjusted, cap)
            
        # Check latest year in multi-year data (catch recent deficits)
        if multi_year_financials:
            years = sorted(multi_year_financials.keys())
            if years:
                latest_year = years[-1]
                latest_fin = multi_year_financials[latest_year]
                latest_op = latest_fin.get('operating_margin')
                
                if latest_op is not None and latest_op < 0:
                    # If base year was positive but latest is negative
                    if op_margin is None or op_margin >= 0:
                        cap = 2
                        warnings.append(f"최근({latest_year}) 영업이익률 {latest_op:.1%}: 적자 전환 -> 최대 {cap}점")
                        adjusted = min(adjusted, cap)

        # Revenue too small for strong moat claim (< 100억원)
        if revenue > 0 and revenue < 10_000_000_000 and moat_strength >= 4:
            warnings.append(f"매출 {revenue/100_000_000:.0f}억원: 규모가 작아 강한 해자 주장 어려움")
            adjusted = min(adjusted, 3)

        # ── Step E: 3 Sustainability Checks ──
        growth_negative = not result['structural_growth']['positive']
        competition_high = result['competition_shift']['risk'] == 'high'
        cost_excessive = result['maintenance_cost']['excessive']

        if growth_negative and adjusted >= 4:
            warnings.append("구조적 성장 미확인: 해자 지속가능성 의문")

        if competition_high and adjusted >= 3:
            warnings.append("경쟁 축 변화 위험 높음: 기존 해자 약화 가능")

        if cost_excessive and adjusted >= 4:
            warnings.append("해자 유지비용 과다: 수익성 저하 위험")

        # Downgrade rules:
        # - structural negative + competition high: up to -2
        # - 2+ warnings from Step E checks: -1
        step_e_warnings = sum([growth_negative, competition_high, cost_excessive])

        if growth_negative and competition_high:
            adjusted = min(adjusted, moat_strength - 2)
            if adjusted < 1:
                adjusted = 1
        elif step_e_warnings >= 2:
            adjusted = min(adjusted, moat_strength - 1)
            if adjusted < 1:
                adjusted = 1

        # Severe revenue decline (CAGR < -15%) = additional cap
        if cagr is not None and cagr < -0.15 and adjusted >= 3:
            warnings.append(f"매출 급감 (CAGR {cagr:.1%}): 해자 유효성 의문")
            adjusted = min(adjusted, 2)

        result['adjusted_strength'] = adjusted
        result['warnings'] = warnings

        return result

    def _check_structural_growth(
        self,
        financials: Dict,
        multi_year_financials: Dict = None,
        report_sections: Dict[str, str] = None
    ) -> Dict:
        """Check 1: Is growth structural?"""
        result = {
            'positive': False,
            'reason': '',
            'data': {}
        }

        # Multi-year revenue trend
        if multi_year_financials and len(multi_year_financials) >= 2:
            years = sorted(multi_year_financials.keys())
            first_rev = multi_year_financials[years[0]].get('revenue', 0)
            last_rev = multi_year_financials[years[-1]].get('revenue', 0)

            if first_rev > 0 and last_rev > 0:
                n_years = len(years) - 1
                if n_years > 0:
                    cagr = (last_rev / first_rev) ** (1 / n_years) - 1
                    result['data']['revenue_cagr'] = round(cagr, 4)

                    if cagr >= 0.05:
                        result['positive'] = True
                        result['reason'] = f"매출 CAGR {cagr:.1%} (구조적 성장)"
                    elif cagr >= 0:
                        result['reason'] = f"매출 CAGR {cagr:.1%} (완만한 성장)"
                    else:
                        result['reason'] = f"매출 CAGR {cagr:.1%} (역성장)"

        # Keyword check from report
        overview = (report_sections or {}).get('business_overview', '')
        if overview:
            growth_kw = re.findall(r'(?:성장|확대|증가|호황)', overview)
            decline_kw = re.findall(r'(?:축소|감소|쇠퇴|역성장|불황)', overview)

            if growth_kw and not decline_kw:
                if not result['reason']:
                    result['positive'] = True
                    result['reason'] = f"사업보고서 성장 키워드 발견: {', '.join(growth_kw[:3])}"
                result['data']['growth_keywords'] = growth_kw[:3]
            elif decline_kw:
                result['data']['decline_keywords'] = decline_kw[:3]
                if not result['reason']:
                    result['reason'] = f"사업보고서 역성장 키워드: {', '.join(decline_kw[:3])}"

        if not result['reason']:
            result['reason'] = "성장 추세 데이터 부족"

        return result

    def _check_competition_shift(
        self,
        report_sections: Dict[str, str]
    ) -> Dict:
        """Check 2: Is the competitive axis shifting?"""
        result = {
            'risk': 'low',
            'reason': '',
            'triggers': []
        }

        competition = report_sections.get('competition', '')
        risk_section = report_sections.get('risk_factors', '')
        text = f"{competition} {risk_section}"

        if not text.strip():
            result['reason'] = "경쟁 데이터 부족"
            return result

        triggers = {
            '기술변화': r'(?:기술\s*변화|기술\s*발전|디지털\s*전환|AI\s*도입)',
            '규제변경': r'(?:규제\s*변[경화]|제도\s*변화|법[률규]\s*개정)',
            '신규진입': r'(?:신규\s*진입|후발\s*업체|경쟁\s*심화|신규\s*경쟁)',
            '대체재': r'(?:대체[재품]|대안\s*기술|대체\s*가능)',
            '해외경쟁': r'(?:해외\s*경쟁|중국.*경쟁|글로벌\s*경쟁)',
            '원가변동': r'(?:원[가재]료\s*가격|비용\s*[증상]가|원가\s*구조\s*변)',
        }

        found_triggers = []
        for trigger_name, pattern in triggers.items():
            if re.search(pattern, text, re.IGNORECASE):
                found_triggers.append(trigger_name)

        result['triggers'] = found_triggers

        if len(found_triggers) >= 3:
            result['risk'] = 'high'
            result['reason'] = f"경쟁 변화 요인 {len(found_triggers)}개 발견 (고위험)"
        elif len(found_triggers) >= 1:
            result['risk'] = 'medium'
            result['reason'] = f"경쟁 변화 요인 {len(found_triggers)}개: {', '.join(found_triggers)}"
        else:
            result['reason'] = "경쟁 축 변화 요인 미발견 (안정적)"

        return result

    def _check_maintenance_cost(self, financials: Dict) -> Dict:
        """Check 3: Is moat maintenance cost excessive?"""
        result = {
            'excessive': False,
            'reason': '',
            'data': {}
        }

        revenue = financials.get('revenue', 0)
        if revenue <= 0:
            result['reason'] = "매출 데이터 없음"
            return result

        rnd = financials.get('rnd_expenses', 0)
        rnd_ratio = rnd / revenue if rnd > 0 else 0
        result['data']['rnd_ratio'] = round(rnd_ratio, 4)

        sga = financials.get('sga_expenses', 0)
        sga_ratio = sga / revenue if sga > 0 else 0
        result['data']['sga_ratio'] = round(sga_ratio, 4)

        maintenance_ratio = rnd_ratio + sga_ratio
        result['data']['maintenance_ratio'] = round(maintenance_ratio, 4)

        if maintenance_ratio > 0.40:
            result['excessive'] = True
            result['reason'] = f"유지비용 과다: R&D {rnd_ratio:.1%} + 판관비 {sga_ratio:.1%} = {maintenance_ratio:.1%}"
        elif maintenance_ratio > 0.25:
            result['reason'] = f"유지비용 보통: R&D {rnd_ratio:.1%} + 판관비 {sga_ratio:.1%} = {maintenance_ratio:.1%}"
        else:
            result['reason'] = f"유지비용 낮음: {maintenance_ratio:.1%}"

        return result

    def generate_sustainability_notes(self, check_result: Dict) -> str:
        """Generate summary text for Excel storage"""
        lines = ["[지속가능성 검증 (Step E)]"]

        sg = check_result['structural_growth']
        icon = "●" if sg['positive'] else "○"
        lines.append(f"{icon} 구조적 성장: {sg['reason']}")

        cs = check_result['competition_shift']
        risk_icon = {'low': '●', 'medium': '◐', 'high': '○'}
        lines.append(f"{risk_icon.get(cs['risk'], '?')} 경쟁 축 변화: {cs['reason']}")

        mc = check_result['maintenance_cost']
        icon = "○" if mc['excessive'] else "●"
        lines.append(f"{icon} 유지비용: {mc['reason']}")

        if check_result.get('warnings'):
            lines.append("")
            lines.append("[경고]")
            for w in check_result['warnings']:
                lines.append(f"* {w}")

        lines.append(f"\n조정 해자강도: {check_result['adjusted_strength']}")

        return '\n'.join(lines)
