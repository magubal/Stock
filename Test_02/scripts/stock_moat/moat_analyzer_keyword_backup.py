"""
Stock Moat Analyzer - Automated Analysis Engine
Uses pattern matching + AI reasoning for moat evaluation
"""

import sys
import os
import json
from typing import Dict, Optional, List

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root
project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
sys.path.insert(0, f"{project_root}/.agent/skills/stock-moat/utils")

from excel_io import ExcelIO


class MoatAnalyzer:
    """Automated moat analysis with industry patterns"""

    def __init__(self):
        self.knowledge_path = f"{project_root}/.agent/memory/stock-moat-estimator"
        self.sector_taxonomy = self._load_sector_taxonomy()
        self.industry_patterns = self._load_industry_patterns()

    def _load_sector_taxonomy(self) -> List[str]:
        """Load 229 approved sector categories"""
        excel_path = f"{project_root}/data/ask/stock_core_master_v2_korean_taxonomy_2026-01-30_요청용_011.xlsx"
        excel_io = ExcelIO(excel_path)
        return excel_io.load_sector_taxonomy()

    def _load_industry_patterns(self) -> Dict:
        """Load industry-specific moat patterns from agent memory"""
        patterns_file = f"{self.knowledge_path}/sector_patterns.md"

        # Default patterns (will be updated from memory)
        return {
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

    def classify_sector(self, company_name: str, business_keywords: List[str] = None) -> Dict:
        """
        Classify company into sector based on name and keywords

        Args:
            company_name: Company name
            business_keywords: Optional keywords from business description

        Returns:
            {
                'core_sector_top': '게임',
                'core_sector_sub': '모바일 게임/PC게임',
                'confidence': 0.8
            }
        """
        # Keyword mapping for common sectors (대폭 확장)
        sector_keywords = {
            '게임': ['게임', '엔터', '넥슨', '위메이드', '엔씨', '넷마블', '컴투스',
                    'NHN', '펄어비스', '엠게임', '넷게임즈', '게임빌', '크래프톤',
                    '카카오게임즈', '액토즈', '조이시티', '선데이토즈',
                    # 추가 게임사 (사용자 피드백 반영)
                    '데브시스터즈', '한빛소프트', '플레이위드', '썸에이지', '넥써쓰',
                    '드래곤플라이', '플래스크', '스마일게이트', '조이맥스', '위즈맥스',
                    '네오플', '씨엔에이엔터', '플라즈마', '블루포션게임즈', '어썸피아',
                    '소프트', '플레이', '엔터', '스튜디오', '인터랙티브', '미디어'],
            '반도체': ['반도체', '칩', '메모리', '삼성전자', 'SK하이닉스', '파운드리',
                     'DB하이텍', '키파운드리', '실리콘웍스', '아나패스'],
            '플랫폼': ['플랫폼', '카카오', '네이버', '쿠팡', '배달', '마켓컬리',
                     '토스', '뱅크샐러드', '직방', '당근마켓'],
            '바이오': ['바이오', '제약', '의약', '신약', '셀트리온', '유한양행',
                     '종근당', '대웅제약', '한미약품', '녹십자'],
            '엔터': ['엔터', 'SM', 'JYP', 'YG', 'HYBE', '케이팝',
                    'FNC', '큐브', '스타쉽', '플레디스'],
            '전자': ['전자', '디스플레이', 'LG', 'OLED', 'LCD',
                   'LG디스플레이', '삼성디스플레이'],
            '자동차': ['자동차', '현대차', '기아', '쌍용', '한국GM',
                     '현대모비스', '만도', '한온시스템'],
            '은행': ['은행', '금융', '증권', '보험', 'KB', '신한', '하나',
                   '우리은행', 'NH농협', '미래에셋', '삼성증권'],
            '통신': ['통신', 'SK텔레콤', 'KT', 'LG유플러스', 'SKT', 'LGU+'],
            '반도체장비': ['테스트', '프로브', '장비', 'ATE'],
            'IT': ['소프트웨어', '클라우드', 'SaaS', 'AI'],
        }

        # Match company name to sector
        for sector, keywords in sector_keywords.items():
            for keyword in keywords:
                if keyword in company_name:
                    return {
                        'core_sector_top': sector,
                        'core_sector_sub': self._guess_subsector(sector, company_name),
                        'confidence': 0.7
                    }

        # Default: return most common sector
        return {
            'core_sector_top': '기타',
            'core_sector_sub': '미분류',
            'confidence': 0.3
        }

    def _guess_subsector(self, sector: str, company_name: str) -> str:
        """Guess subsector based on sector and company name"""
        subsector_map = {
            '게임': '모바일 게임/PC게임',
            '반도체': '메모리/시스템반도체',
            '플랫폼': '전자상거래/포털',
            '바이오': '의약품/바이오시밀러',
            '엔터': '음반/공연',
            '전자': '디스플레이/전자부품',
            '자동차': '완성차/부품',
            '은행': '은행/증권',
            '통신': '이동통신/인터넷'
        }
        return subsector_map.get(sector, '기타')

    def evaluate_moat(
        self,
        sector: str,
        company_size: str = 'medium',
        has_strong_brand: bool = False,
        has_patents: bool = False
    ) -> Dict:
        """
        Evaluate moat strength based on sector and characteristics

        Args:
            sector: Industry sector
            company_size: 'large', 'medium', 'small'
            has_strong_brand: Whether company has strong brand
            has_patents: Whether company has significant patents

        Returns:
            {
                'brand': 3,
                'cost': 2,
                'network': 3,
                'switching': 2,
                'regulatory': 2,
                'total': 12,
                'moat_strength': 2
            }
        """
        # Get industry pattern
        pattern = self.industry_patterns.get(sector, self.industry_patterns['제조업'])

        # Base scores from pattern
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

        network = network_range[1] if sector in ['플랫폼', '게임'] else network_range[0]
        switching = switching_range[1] if has_patents else switching_range[0]
        regulatory = regulatory_range[1] if sector in ['바이오', '금융'] else regulatory_range[0]

        total = brand + cost + network + switching + regulatory
        moat_strength = round(total / 5)

        return {
            'brand': brand,
            'cost': cost,
            'network': network,
            'switching': switching,
            'regulatory': regulatory,
            'total': total,
            'moat_strength': moat_strength
        }

    def generate_moat_desc(self, sector: str, scores: Dict, company_name: str = "") -> str:
        """Generate structured 해자DESC text"""
        reasons = self._get_moat_reasons(sector, scores, company_name)

        desc = f"""브랜드 파워: {scores['brand']}/5 ({reasons['brand']})
원가 우위: {scores['cost']}/5 ({reasons['cost']})
네트워크 효과: {scores['network']}/5 ({reasons['network']})
전환 비용: {scores['switching']}/5 ({reasons['switching']})
규제/허가: {scores['regulatory']}/5 ({reasons['regulatory']})
---
총점: {scores['total']}/25 → 해자강도 {scores['moat_strength']}"""

        return desc

    def _get_moat_reasons(self, sector: str, scores: Dict, company_name: str) -> Dict:
        """Generate brief reasons for each moat category"""
        # Sector-specific reason templates
        reason_templates = {
            '게임': {
                'brand': '게임 IP 보유' if scores['brand'] >= 3 else 'IP 제한적',
                'cost': '자체 개발' if scores['cost'] >= 3 else '외주 의존',
                'network': '유저 커뮤니티' if scores['network'] >= 3 else '커뮤니티 약함',
                'switching': '일부 충성도' if scores['switching'] >= 3 else '이탈 쉬움',
                'regulatory': '등급심의'
            },
            '반도체': {
                'brand': '글로벌 브랜드' if scores['brand'] >= 4 else '중견 브랜드',
                'cost': '대규모 fab' if scores['cost'] >= 4 else '중소규모',
                'network': '제한적',
                'switching': 'B2B 계약' if scores['switching'] >= 3 else '일부 계약',
                'regulatory': '일부 특허'
            },
            '플랫폼': {
                'brand': '높은 인지도' if scores['brand'] >= 4 else '중간 인지도',
                'cost': '중간 수준',
                'network': '강력한 네트워크' if scores['network'] >= 4 else '일부 효과',
                'switching': '생태계 의존' if scores['switching'] >= 4 else '중간 의존',
                'regulatory': '일부 규제'
            }
        }

        # Get reasons for sector
        reasons = reason_templates.get(sector, {
            'brand': '일반적',
            'cost': '일반적',
            'network': '일반적',
            'switching': '일반적',
            'regulatory': '일반적'
        })

        return reasons

    def analyze_stock(
        self,
        ticker: str,
        name: str,
        sector_hint: str = None,
        auto_save: bool = False,
        interactive: bool = False
    ) -> Dict:
        """
        Analyze single stock automatically

        Args:
            ticker: Stock code
            name: Company name
            sector_hint: Optional sector hint
            auto_save: Whether to save to Excel

        Returns:
            Analysis result dict
        """
        print(f"\n{'='*60}")
        print(f"🔍 Analyzing: {name} ({ticker})")
        print(f"{'='*60}\n")

        # Step 1: Classify sector
        if sector_hint:
            sector_result = {
                'core_sector_top': sector_hint,
                'core_sector_sub': self._guess_subsector(sector_hint, name),
                'confidence': 0.9
            }
        else:
            sector_result = self.classify_sector(name)

        print(f"📂 Sector: {sector_result['core_sector_top']} / {sector_result['core_sector_sub']}")
        print(f"   Confidence: {sector_result['confidence']:.1%}")

        # Interactive mode: Ask user if confidence is low
        if interactive and sector_result['confidence'] < 0.5:
            print(f"\n❓ {name} ({ticker})의 업종을 확인해주세요:")
            print("   1) 게임")
            print("   2) 반도체")
            print("   3) 플랫폼")
            print("   4) 바이오")
            print("   5) 기타")
            print("   또는 직접 입력 (예: 엔터, IT)")
            user_input = input("   선택 (Enter=자동): ").strip()

            if user_input:
                sector_map = {
                    '1': '게임',
                    '2': '반도체',
                    '3': '플랫폼',
                    '4': '바이오',
                    '5': '기타'
                }
                selected_sector = sector_map.get(user_input, user_input)
                sector_result = {
                    'core_sector_top': selected_sector,
                    'core_sector_sub': self._guess_subsector(selected_sector, name),
                    'confidence': 1.0
                }
                print(f"   ✅ {selected_sector}로 설정됨\n")
        else:
            print()  # Empty line

        # Step 2: Evaluate moat
        # Heuristics based on company name
        has_strong_brand = any(keyword in name for keyword in ['삼성', '현대', '네이버', '카카오', 'LG', 'SK'])
        company_size = 'large' if has_strong_brand else 'medium'

        moat_scores = self.evaluate_moat(
            sector=sector_result['core_sector_top'],
            company_size=company_size,
            has_strong_brand=has_strong_brand
        )

        print(f"🛡️  Moat Strength: {moat_scores['moat_strength']}/5")
        print(f"   Total: {moat_scores['total']}/25\n")

        # Step 3: Generate descriptions
        core_desc = f"{sector_result['core_sector_top']} 관련 사업 (자동 분석)"
        moat_desc = self.generate_moat_desc(
            sector_result['core_sector_top'],
            moat_scores,
            name
        )

        # Step 4: Compile result
        result = {
            'ticker': ticker,
            'name': name,
            'core_sector_top': sector_result['core_sector_top'],
            'core_sector_sub': sector_result['core_sector_sub'],
            'core_desc': core_desc,
            '해자강도': moat_scores['moat_strength'],
            '해자DESC': moat_desc,
            'confidence': sector_result['confidence']
        }

        # Step 5: Auto-save if requested
        if auto_save:
            excel_path = f"{project_root}/data/ask/stock_core_master_v2_korean_taxonomy_2026-01-30_요청용_011.xlsx"
            excel_io = ExcelIO(excel_path)

            save_data = {k: v for k, v in result.items() if k not in ['confidence', 'ticker', 'name']}
            success = excel_io.update_stock_row(ticker, save_data, create_backup=True)

            if success:
                print(f"✅ Saved to Excel\n")
            else:
                print(f"❌ Save failed\n")

        return result


# Test function
if __name__ == "__main__":
    analyzer = MoatAnalyzer()

    # Test: Analyze 네오위즈
    result = analyzer.analyze_stock(
        ticker='095660',
        name='네오위즈',
        sector_hint='게임',
        auto_save=False
    )

    print("Result:")
    for key, value in result.items():
        if key == '해자DESC':
            print(f"{key}:")
            print(value)
        else:
            print(f"{key}: {value}")
