"""
Stock Moat Analyzer - DART Business Report Edition
Uses official DART disclosures for accurate sector classification
"""

import sys
import os
from typing import Dict, Optional

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root
project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
sys.path.insert(0, f"{project_root}/.agent/skills/stock-moat/utils")

from dart_client import DARTClient
from ksic_to_gics_mapper import KSICtoGICSMapper
from config import get_dart_api_key


class MoatAnalyzer:
    """GICS-based moat analyzer with DART business reports"""

    def __init__(self, dart_api_key: str = None):
        if dart_api_key is None:
            dart_api_key = get_dart_api_key()
        self.dart = DARTClient(dart_api_key)
        self.gics_mapper = KSICtoGICSMapper()
        self.knowledge_path = f"{project_root}/.agent/memory/stock-moat-estimator"

        # Moat patterns by sector (same as before)
        self.industry_patterns = {
            '게임': {
                'typical_moat': 2,
                'brand': (2, 3),
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

    def classify_sector_dart(self, ticker: str, name: str) -> Dict:
        """
        Classify sector using DART official data

        Args:
            ticker: Stock code
            name: Company name

        Returns:
            {
                'core_sector_top': str,
                'core_sector_sub': str,
                'core_desc': str,
                'confidence': float,
                'source': str
            }
        """
        # Fetch DART data
        dart_result = self.dart.analyze_stock(ticker)

        if not dart_result:
            # Fallback to name-based classification
            print(f"    ⚠️  DART data unavailable, using fallback")
            return {
                'core_sector_top': '기타',
                'core_sector_sub': '미분류',
                'core_desc': f'{name} - DART 데이터 없음',
                'confidence': 0.2,
                'source': 'DART 조회 실패'
            }

        # Map KSIC code to GICS investment classification
        industry_code = dart_result['industry_code']
        company_name = dart_result['corp_name']

        gics_result = self.gics_mapper.map_to_gics(industry_code, company_name)

        # Build core_desc with GICS evidence
        core_desc = f"{name} - {gics_result['reasoning']}"
        if dart_result.get('homepage'):
            core_desc += f" | {dart_result['homepage']}"

        return {
            'core_sector_top': gics_result['korean_sector_top'],
            'core_sector_sub': gics_result['korean_sector_sub'],
            'core_desc': core_desc,
            'confidence': gics_result['confidence'],
            'source': gics_result['source'],
            'gics_sector': gics_result['gics_sector'],
            'gics_industry': gics_result['gics_industry']
        }

    def evaluate_moat(
        self,
        sector: str,
        gics_sector: str = '',
        gics_industry: str = '',
        company_size: str = 'medium',
        has_strong_brand: bool = False,
        has_patents: bool = False
    ) -> Dict:
        """
        Evaluate moat strength based on GICS sector characteristics
        Uses investment-focused moat patterns from GICS mapper
        """
        # Get GICS-based moat pattern
        moat_info = self.gics_mapper.get_moat_drivers_by_gics(gics_sector, gics_industry)

        # Get legacy pattern for fallback
        pattern = self.industry_patterns.get(sector, self.industry_patterns['제조업'])

        # Start with typical strength from GICS
        base_strength = moat_info.get('typical_strength', 3)

        # Use legacy pattern ranges for detailed scoring
        brand_range = pattern['brand']
        cost_range = pattern['cost']
        network_range = pattern['network']
        switching_range = pattern['switching']
        regulatory_range = pattern['regulatory']

        # Adjust based on company characteristics
        brand = brand_range[1] if has_strong_brand else brand_range[0]

        if company_size == 'large':
            cost = cost_range[1]
        elif company_size == 'small':
            cost = cost_range[0]
        else:
            cost = sum(cost_range) // 2

        # GICS-aware adjustments
        primary_moat = moat_info.get('primary_moat', '')

        # Boost primary moat type
        if primary_moat == '네트워크 효과':
            network = network_range[1]
        else:
            network = network_range[0]

        if primary_moat == '전환 비용' or has_patents:
            switching = switching_range[1]
        else:
            switching = switching_range[0]

        if primary_moat == '규제/허가':
            regulatory = regulatory_range[1]
        else:
            regulatory = regulatory_range[0]

        total = brand + cost + network + switching + regulatory
        moat_strength = round(total / 5)

        # Clamp to valid range 1-5
        moat_strength = max(1, min(5, moat_strength))

        return {
            'brand': brand,
            'cost': cost,
            'network': network,
            'switching': switching,
            'regulatory': regulatory,
            'total': total,
            'moat_strength': moat_strength,
            'primary_moat': primary_moat,
            'gics_typical': base_strength
        }

    def generate_moat_desc(self, sector: str, scores: Dict, source: str = "") -> str:
        """Generate structured 해자DESC with source citation"""
        desc = f"""브랜드 파워: {scores['brand']}/5
원가 우위: {scores['cost']}/5
네트워크 효과: {scores['network']}/5
전환 비용: {scores['switching']}/5
규제/허가: {scores['regulatory']}/5
---
총점: {scores['total']}/25 → 해자강도 {scores['moat_strength']}
[출처: {source}]"""

        return desc

    def analyze_stock(
        self,
        ticker: str,
        name: str,
        auto_save: bool = False
    ) -> Dict:
        """
        Analyze single stock with DART data

        Args:
            ticker: Stock code
            name: Company name
            auto_save: Whether to save to Excel

        Returns:
            Analysis result dict
        """
        print(f"\n{'='*60}")
        print(f"🔍 Analyzing: {name} ({ticker})")
        print(f"{'='*60}\n")

        # Step 1: Classify sector using DART
        sector_result = self.classify_sector_dart(ticker, name)

        print(f"📂 Sector: {sector_result['core_sector_top']} / {sector_result['core_sector_sub']}")
        print(f"   Confidence: {sector_result['confidence']:.1%}")
        print(f"   Source: {sector_result['source']}")
        print()

        # Step 2: Evaluate moat
        has_strong_brand = any(keyword in name for keyword in ['삼성', '현대', '네이버', '카카오', 'LG', 'SK'])
        company_size = 'large' if has_strong_brand else 'medium'

        moat_scores = self.evaluate_moat(
            sector=sector_result['core_sector_top'],
            gics_sector=sector_result.get('gics_sector', ''),
            gics_industry=sector_result.get('gics_industry', ''),
            company_size=company_size,
            has_strong_brand=has_strong_brand
        )

        print(f"🛡️  Moat Strength: {moat_scores['moat_strength']}/5")
        print(f"   Total: {moat_scores['total']}/25\n")

        # Step 3: Generate descriptions
        moat_desc = self.generate_moat_desc(
            sector_result['core_sector_top'],
            moat_scores,
            sector_result['source']
        )

        # Step 4: Compile result
        result = {
            'ticker': ticker,
            'name': name,
            'core_sector_top': sector_result['core_sector_top'],
            'core_sector_sub': sector_result['core_sector_sub'],
            'core_desc': sector_result['core_desc'],
            '해자강도': moat_scores['moat_strength'],
            '해자DESC': moat_desc,
            'confidence': sector_result['confidence']
        }

        return result


# Test function
if __name__ == "__main__":
    analyzer = MoatAnalyzer()

    # Test cases
    test_stocks = [
        ('005930', '삼성전자'),
        ('000660', 'SK하이닉스'),
        ('035720', '카카오'),
        ('095660', '네오위즈')
    ]

    print(f"\n{'='*60}")
    print("DART 기반 분석 테스트")
    print(f"{'='*60}")

    for ticker, name in test_stocks:
        result = analyzer.analyze_stock(ticker, name)

        print(f"\n결과:")
        print(f"  Sector: {result['core_sector_top']} / {result['core_sector_sub']}")
        print(f"  Confidence: {result['confidence']:.1%}")
        print(f"  해자강도: {result['해자강도']}/5")
        print(f"  core_desc: {result['core_desc']}")
