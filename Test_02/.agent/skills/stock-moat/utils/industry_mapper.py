"""
DART Industry Code to Sector Mapper
Maps Korean Standard Industry Classification (KSIC) to our 229 sectors
"""

import sys

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class IndustryMapper:
    """Maps DART industry codes to sector categories"""

    def __init__(self):
        # DART industry code mappings (KSIC 코드)
        # Format: industry_code_prefix -> (core_sector_top, core_sector_sub, keywords)
        self.mappings = {
            # IT/전자
            '261': ('반도체', '메모리/시스템반도체', ['반도체', '메모리', '칩']),
            '262': ('반도체', '메모리/시스템반도체', ['반도체', '메모리']),
            '263': ('전자', '디스플레이/전자부품', ['디스플레이', 'OLED', 'LCD']),
            '264': ('전자', '디스플레이/전자부품', ['전자제품', '가전']),
            '265': ('전자', '디스플레이/전자부품', ['전자부품']),

            # 통신
            '612': ('통신', '이동통신/인터넷', ['이동통신', '무선통신']),
            '613': ('통신', '이동통신/인터넷', ['통신', '인터넷']),

            # 소프트웨어/게임
            '581': ('IT', '기타', ['소프트웨어', '패키지']),
            '582': ('게임', '모바일 게임/PC게임', ['게임', '온라인게임']),
            '5821': ('게임', '모바일 게임/PC게임', ['온라인게임', '모바일게임']),
            '5822': ('게임', '모바일 게임/PC게임', ['게임소프트웨어']),
            '620': ('IT', '기타', ['정보서비스', '데이터처리']),

            # 플랫폼/인터넷
            '631': ('플랫폼', '전자상거래/포털', ['포털', '플랫폼']),
            '632': ('플랫폼', '전자상거래/포털', ['전자상거래', '온라인쇼핑']),

            # 바이오/제약
            '211': ('바이오', '의약품/바이오시밀러', ['의약품', '제약']),
            '212': ('바이오', '의약품/바이오시밀러', ['바이오', '의약']),
            '213': ('바이오', '의약품/바이오시밀러', ['의료용품', '의약외품']),

            # 자동차
            '301': ('자동차', '완성차/부품', ['자동차', '완성차']),
            '303': ('자동차', '완성차/부품', ['자동차부품']),

            # 화학
            '201': ('화학', '기타', ['화학', '석유화학']),
            '202': ('화학', '기타', ['화학제품']),

            # 금속/철강
            '241': ('제조업', '기타', ['철강', '금속']),
            '242': ('제조업', '기타', ['금속제품']),

            # 기계
            '291': ('제조업', '기타', ['일반기계', '기계']),
            '292': ('제조업', '기타', ['특수목적기계']),

            # 엔터테인먼트
            '591': ('엔터', '음반/공연', ['영화', '비디오']),
            '592': ('엔터', '음반/공연', ['음악', '음반']),
            '900': ('엔터', '음반/공연', ['예술', '창작']),

            # 금융/은행
            '641': ('은행', '은행/증권', ['은행', '금융']),
            '651': ('은행', '은행/증권', ['보험', '재보험']),
            '661': ('은행', '은행/증권', ['금융투자', '증권']),

            # 유통/도소매
            '471': ('기타', '미분류', ['소매', '유통']),
            '472': ('기타', '미분류', ['소매업']),

            # 건설
            '411': ('기타', '미분류', ['건설', '건축']),
            '412': ('기타', '미분류', ['토목', '건설']),

            # 운수/여행
            '491': ('기타', '미분류', ['철도', '운송']),
            '501': ('기타', '미분류', ['해운', '운송']),
            '511': ('기타', '미분류', ['항공', '운수']),
            '751': ('기타', '미분류', ['여행', '관광']),

            # 숙박/음식
            '551': ('기타', '미분류', ['숙박', '호텔']),
            '561': ('기타', '미분류', ['음식', '외식']),

            # 제지/펄프
            '171': ('제조업', '기타', ['펄프', '제지']),
            '172': ('제조업', '기타', ['종이제품', '제지']),
        }

    def map_industry_code(self, industry_code: str, company_name: str = "") -> dict:
        """
        Map DART industry code to sector

        Args:
            industry_code: DART KSIC code (e.g., "264")
            company_name: Company name for additional context

        Returns:
            {
                'core_sector_top': str,
                'core_sector_sub': str,
                'confidence': float,
                'source': str
            }
        """
        # Try exact match first
        if industry_code in self.mappings:
            sector_top, sector_sub, keywords = self.mappings[industry_code]
            return {
                'core_sector_top': sector_top,
                'core_sector_sub': sector_sub,
                'confidence': 0.9,  # High confidence for direct mapping
                'source': f'DART 업종코드 {industry_code}'
            }

        # Try prefix match (e.g., "264" matches "26" category)
        for code_prefix, (sector_top, sector_sub, keywords) in self.mappings.items():
            if industry_code.startswith(code_prefix[:2]):
                return {
                    'core_sector_top': sector_top,
                    'core_sector_sub': sector_sub,
                    'confidence': 0.7,  # Medium confidence for prefix match
                    'source': f'DART 업종코드 {industry_code} (추정)'
                }

        # Fallback: Check company name for keywords
        if company_name:
            name_lower = company_name.lower()
            for code_prefix, (sector_top, sector_sub, keywords) in self.mappings.items():
                for keyword in keywords:
                    if keyword in name_lower:
                        return {
                            'core_sector_top': sector_top,
                            'core_sector_sub': sector_sub,
                            'confidence': 0.5,  # Low confidence for name-based guess
                            'source': f'회사명 키워드 ({keyword})'
                        }

        # No match
        return {
            'core_sector_top': '기타',
            'core_sector_sub': '미분류',
            'confidence': 0.3,
            'source': f'DART 업종코드 {industry_code} (미등록)'
        }


# Test
if __name__ == "__main__":
    mapper = IndustryMapper()

    test_cases = [
        ('264', '삼성전자'),      # 전자
        ('261', 'SK하이닉스'),    # 반도체
        ('582', '넥슨'),          # 게임
        ('211', '셀트리온'),      # 바이오
        ('751', '하나투어'),      # 여행
        ('999', '알수없음')       # 미등록
    ]

    print(f"\n{'='*60}")
    print("업종코드 매핑 테스트")
    print(f"{'='*60}\n")

    for code, company in test_cases:
        result = mapper.map_industry_code(code, company)
        print(f"{code} ({company}):")
        print(f"  → {result['core_sector_top']} / {result['core_sector_sub']}")
        print(f"  Confidence: {result['confidence']:.1%}")
        print(f"  Source: {result['source']}\n")
