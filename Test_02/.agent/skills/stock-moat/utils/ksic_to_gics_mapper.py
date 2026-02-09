"""
KSIC to GICS/WICS Mapper
Maps Korean industrial codes to investment-focused sector classifications

GICS Structure (used globally):
- Level 1: 11 Sectors (e.g., Materials, Information Technology)
- Level 2: 25 Industry Groups (e.g., Chemicals, Software & Services)
- Level 3: 74 Industries (e.g., Specialty Chemicals, Application Software)
- Level 4: 163 Sub-Industries (most specific)

WICS: Korean adaptation of GICS with local market adjustments
"""

from typing import Dict, Optional


class KSICtoGICSMapper:
    """Maps KSIC industrial codes to GICS investment sectors"""

    def __init__(self):
        # KSIC -> (GICS Sector, Industry Group, Industry, Korean Category)
        self.ksic_to_gics = {
            # 화학 (Materials - Chemicals)
            '201': ('Materials', 'Chemicals', 'Basic Chemicals', '화학', '기초화학'),
            '20111': ('Materials', 'Chemicals', 'Basic Chemicals', '화학', '석유화학'),
            '20112': ('Materials', 'Chemicals', 'Basic Chemicals', '화학', '정밀화학'),
            '202': ('Materials', 'Chemicals', 'Fertilizers & Agricultural Chemicals', '화학', '비료/농약'),
            '204': ('Materials', 'Chemicals', 'Specialty Chemicals', '화학', '기타화학'),
            '20422': ('Consumer Staples', 'Personal Products', 'Cosmetics', '화학', '화장품'),
            '20423': ('Consumer Staples', 'Household Products', 'Detergents', '화학', '세제'),

            # 의약품 (Health Care - Pharmaceuticals)
            '211': ('Health Care', 'Pharmaceuticals', 'Pharmaceuticals', '바이오', '의약품'),
            '21101': ('Health Care', 'Pharmaceuticals', 'Drug Manufacturing', '바이오', '완제의약품'),
            '21102': ('Health Care', 'Biotechnology', 'Biotechnology', '바이오', '바이오의약품'),

            # 플라스틱/고무 (Materials - Chemicals)
            '221': ('Materials', 'Chemicals', 'Rubber Products', '제조업', '고무제품'),
            '222': ('Materials', 'Chemicals', 'Plastic Products', '제조업', '플라스틱'),
            '2229': ('Materials', 'Chemicals', 'Specialty Plastics', '화학', '특수플라스틱'),  # ← 나노켐텍 여기
            '22232': ('Materials', 'Packaging', 'Plastic Packaging', '제조업', '플라스틱포장'),

            # 유리/세라믹 (Materials - Construction Materials)
            '231': ('Materials', 'Construction Materials', 'Glass Products', '제조업', '유리'),
            '23192': ('Materials', 'Construction Materials', 'Ceramics', '제조업', '세라믹'),

            # 금속 (Materials - Metals & Mining)
            '241': ('Materials', 'Metals & Mining', 'Steel', '소재', '철강'),
            '242': ('Materials', 'Metals & Mining', 'Non-Ferrous Metals', '소재', '비철금속'),
            '259': ('Materials', 'Metals & Mining', 'Metal Fabrication', '제조업', '금속가공'),
            '25923': ('Industrials', 'Capital Goods', 'Metal Products', '제조업', '금속제품'),

            # 전자부품/반도체 (Information Technology - Semiconductors)
            '261': ('Information Technology', 'Semiconductors', 'Semiconductors', '반도체', '반도체'),
            '264': ('Information Technology', 'Semiconductors', 'Semiconductors', '반도체', '반도체'),  # 전자부품 제조업
            '26110': ('Information Technology', 'Semiconductors', 'Memory Chips', '반도체', '메모리반도체'),
            '26121': ('Information Technology', 'Semiconductors', 'Non-Memory Chips', '반도체', '시스템반도체'),
            '26122': ('Information Technology', 'Electronic Components', 'Display Panels', '전자', '디스플레이'),

            # 전기장비 (Industrials - Electrical Equipment)
            '271': ('Industrials', 'Capital Goods', 'Electrical Equipment', '전자', '전기장비'),
            '27199': ('Industrials', 'Capital Goods', 'Electrical Components', '전자', '전기부품'),
            '27212': ('Industrials', 'Capital Goods', 'Batteries', '전자', '축전지'),
            '27216': ('Industrials', 'Capital Goods', 'Cables & Wires', '전자', '전선'),

            # 기계 (Industrials - Machinery)
            '281': ('Industrials', 'Capital Goods', 'Industrial Machinery', '제조업', '기계'),
            '28111': ('Industrials', 'Capital Goods', 'Engines', '제조업', '엔진'),
            '29221': ('Industrials', 'Capital Goods', 'Construction Equipment', '제조업', '건설기계'),
            '29271': ('Industrials', 'Capital Goods', 'Specialized Machinery', '제조업', '전문기계'),
            '29272': ('Industrials', 'Capital Goods', 'Industrial Equipment', '제조업', '산업기계'),
            '29229': ('Industrials', 'Capital Goods', 'General Machinery', '제조업', '일반기계'),

            # 자동차 (Consumer Discretionary - Automobiles)
            '291': ('Consumer Discretionary', 'Automobiles', 'Automobile Manufacturers', '자동차', '완성차'),
            '292': ('Consumer Discretionary', 'Auto Components', 'Auto Parts', '자동차', '자동차부품'),
            '30321': ('Consumer Discretionary', 'Automobiles', 'Electric Vehicles', '자동차', '전기차'),

            # 제지/펄프 (Materials - Paper & Forest Products)
            '171': ('Materials', 'Paper & Forest Products', 'Pulp & Paper', '제조업', '제지/펄프'),
            '172': ('Materials', 'Containers & Packaging', 'Paper Packaging', '제조업', '종이포장'),
            '179': ('Materials', 'Paper & Forest Products', 'Paper Products', '제조업', '종이제품'),

            # 인쇄 (Industrials - Commercial Services)
            '182': ('Industrials', 'Commercial Services', 'Printing Services', '제조업', '인쇄'),

            # 의류 (Consumer Discretionary - Textiles)
            '141': ('Consumer Discretionary', 'Textiles & Apparel', 'Apparel Manufacturing', '제조업', '의류'),

            # 가구 (Consumer Discretionary - Household Durables)
            '311': ('Consumer Discretionary', 'Household Durables', 'Furniture', '제조업', '가구'),

            # 금융 (Financials)
            '641': ('Financials', 'Banks', 'Banks', '은행', '은행'),
            '64111': ('Financials', 'Banks', 'Commercial Banks', '은행', '시중은행'),
            '64191': ('Financials', 'Banks', 'Internet Banks', '은행', '인터넷전문은행'),
            '642': ('Financials', 'Diversified Financials', 'Financial Services', '금융', '금융서비스'),
            '649': ('Financials', 'Diversified Financials', 'Other Financial Services', '금융', '기타금융'),
            '64992': ('Financials', 'Diversified Financials', 'Financial Holding Companies', '금융', '지주회사'),

            # IT 서비스/소프트웨어 (Information Technology)
            '424': ('Information Technology', 'Software & Services', 'Internet Services', 'IT', '인터넷'),
            '581': ('Information Technology', 'Software & Services', 'Software', 'IT', '소프트웨어'),
            '58221': ('Information Technology', 'Software & Services', 'Game Software', '게임', '게임소프트웨어'),
            '5821': ('Communication Services', 'Media & Entertainment', 'Gaming', '게임', '모바일게임/PC게임'),
            '620': ('Information Technology', 'Software & Services', 'IT Consulting', 'IT', 'IT서비스'),
            '631': ('Communication Services', 'Media & Entertainment', 'Internet Platforms', 'IT', '플랫폼'),
            '63120': ('Communication Services', 'Media & Entertainment', 'Internet Platforms', 'IT', '플랫폼'),  # 카카오
            '639': ('Information Technology', 'Software & Services', 'Data Services', 'IT', '정보서비스'),

            # 유통/도소매 (Consumer Discretionary - Retailing)
            '4610': ('Consumer Discretionary', 'Retailing', 'General Trading', '유통', '종합상사'),
            '463': ('Consumer Staples', 'Food & Drug Retailing', 'Food Wholesale', '유통', '식품도매'),
            '464': ('Consumer Discretionary', 'Retailing', 'Household Goods Wholesale', '유통', '가정용품도매'),
            '465': ('Industrials', 'Capital Goods', 'Machinery Wholesale', '유통', '기계도매'),
            '46510': ('Information Technology', 'Technology Hardware', 'IT Equipment Wholesale', '유통', 'IT도매'),
            '46522': ('Information Technology', 'Electronic Components', 'Electronics Wholesale', '유통', '전자부품도매'),
            '468': ('Consumer Discretionary', 'Retailing', 'Specialty Wholesale', '유통', '전문도매'),
            '471': ('Consumer Discretionary', 'Retailing', 'General Merchandise', '유통', '종합소매'),
            '47111': ('Consumer Discretionary', 'Retailing', 'Department Stores', '유통', '백화점'),
            '479': ('Consumer Discretionary', 'Retailing', 'Specialty Retail', '유통', '전문소매'),

            # 광고/마케팅 (Communication Services)
            '713': ('Communication Services', 'Media & Entertainment', 'Advertising', '광고', '광고/마케팅'),

            # 전문서비스 (Industrials - Professional Services)
            '739': ('Industrials', 'Professional Services', 'Consulting & Business Services', '기타', '전문서비스'),

            # 여행/레저 (Consumer Discretionary)
            '752': ('Consumer Discretionary', 'Hotels & Leisure', 'Travel Services', '여행', '여행/관광'),
            '75210': ('Consumer Discretionary', 'Hotels & Leisure', 'Travel Agencies', '여행', '여행사'),
            '319': ('Consumer Discretionary', 'Hotels & Leisure', 'Sports & Recreation', '레저', '스포츠/레저'),
            '31991': ('Consumer Discretionary', 'Specialty Retail', 'Sporting Goods Stores', '레저', '스포츠용품'),
            '91249': ('Consumer Discretionary', 'Hotels & Leisure', 'Casinos & Gaming', '레저', '카지노'),
            '9124': ('Consumer Discretionary', 'Hotels & Leisure', 'Casinos & Gaming', '레저', '카지노'),
            '912': ('Consumer Discretionary', 'Hotels & Leisure', 'Leisure & Recreation', '레저', '레저시설'),
            '90199': ('Consumer Discretionary', 'Hotels & Leisure', 'Personal Services', '레저', '개인서비스'),
            '901': ('Consumer Discretionary', 'Hotels & Leisure', 'Leisure Services', '레저', '레저서비스'),

            # 건설 (Industrials - Construction)
            '411': ('Industrials', 'Capital Goods', 'Construction & Engineering', '건설', '건물건설'),
            '41101': ('Industrials', 'Capital Goods', 'Residential Construction', '건설', '주거용건설'),
            '41102': ('Industrials', 'Capital Goods', 'Commercial Construction', '건설', '비주거용건설'),
            '412': ('Industrials', 'Capital Goods', 'Civil Engineering', '건설', '토목건설'),
            '42110': ('Industrials', 'Capital Goods', 'Road Construction', '건설', '도로건설'),
            '42201': ('Industrials', 'Capital Goods', 'Utility Construction', '건설', '전기통신건설'),
            '42202': ('Industrials', 'Capital Goods', 'Pipeline Construction', '건설', '배관건설'),
            '421': ('Industrials', 'Capital Goods', 'Infrastructure Construction', '건설', '기반시설건설'),
            '422': ('Industrials', 'Capital Goods', 'Utility & Pipeline', '건설', '설비건설'),
            '429': ('Industrials', 'Capital Goods', 'Specialty Construction', '건설', '전문건설'),

            # 전기/가스/수도 (Utilities - 35xxx)
            '351': ('Utilities', 'Utilities', 'Electric Utilities', '유틸리티', '전기'),
            '35111': ('Utilities', 'Utilities', 'Electric Power Generation', '유틸리티', '발전'),
            '35120': ('Utilities', 'Utilities', 'Electric Power Transmission', '유틸리티', '송배전'),
            '352': ('Utilities', 'Utilities', 'Gas Utilities', '유틸리티', '가스'),
            '353': ('Utilities', 'Utilities', 'Steam & Air Conditioning', '유틸리티', '증기/냉난방'),
            '360': ('Utilities', 'Utilities', 'Water Utilities', '유틸리티', '수도'),
            '370': ('Utilities', 'Utilities', 'Waste Management', '유틸리티', '폐기물처리'),

            # 금융 추가 (Financials - 보험/증권/65-66xxx)
            '651': ('Financials', 'Insurance', 'Life Insurance', '금융', '생명보험'),
            '652': ('Financials', 'Insurance', 'Non-Life Insurance', '금융', '손해보험'),
            '661': ('Financials', 'Diversified Financials', 'Securities', '금융', '증권'),
            '662': ('Financials', 'Diversified Financials', 'Asset Management', '금융', '자산운용'),
            '663': ('Financials', 'Diversified Financials', 'Trust Services', '금융', '신탁'),

            # 운수/물류 (Industrials - Transportation)
            '491': ('Industrials', 'Transportation', 'Rail Transportation', '운수', '철도운송'),
            '492': ('Industrials', 'Transportation', 'Land Transportation', '운수', '육상운송'),
            '501': ('Industrials', 'Transportation', 'Ocean Transportation', '운수', '해운'),
            '511': ('Industrials', 'Transportation', 'Air Transportation', '운수', '항공운송'),
            '521': ('Industrials', 'Transportation', 'Warehousing', '운수', '창고/물류'),

            # 통신 (Communication Services)
            '612': ('Communication Services', 'Telecommunication Services', 'Wireless Telecom', '통신', '무선통신'),
            '611': ('Communication Services', 'Telecommunication Services', 'Wired Telecom', '통신', '유선통신'),

            # 부동산 (Real Estate)
            '681': ('Real Estate', 'Real Estate', 'Real Estate Development', '부동산', '부동산개발'),
            '682': ('Real Estate', 'Real Estate', 'Real Estate Services', '부동산', '부동산서비스'),

            # 식품 (Consumer Staples - Food)
            '101': ('Consumer Staples', 'Food & Beverage', 'Meat Processing', '식품', '도축/육가공'),
            '102': ('Consumer Staples', 'Food & Beverage', 'Seafood Processing', '식품', '수산가공'),
            '103': ('Consumer Staples', 'Food & Beverage', 'Fruit & Vegetable Processing', '식품', '과실/채소가공'),
            '104': ('Consumer Staples', 'Food & Beverage', 'Oils & Fats', '식품', '유지/유지가공'),
            '105': ('Consumer Staples', 'Food & Beverage', 'Dairy Products', '식품', '낙농'),
            '106': ('Consumer Staples', 'Food & Beverage', 'Grain Milling', '식품', '곡물가공'),
            '107': ('Consumer Staples', 'Food & Beverage', 'Other Food Products', '식품', '기타식품'),
            '108': ('Consumer Staples', 'Food & Beverage', 'Animal Feed', '식품', '동물사료'),
            '110': ('Consumer Staples', 'Food & Beverage', 'Beverages', '식품', '음료'),
            '120': ('Consumer Staples', 'Food & Beverage', 'Tobacco', '식품', '담배'),
        }

    def map_to_gics(self, ksic_code: str, company_name: str = '') -> Dict:
        """
        Map KSIC code to GICS classification

        Returns:
            {
                'gics_sector': str,
                'gics_industry_group': str,
                'gics_industry': str,
                'korean_sector_top': str,
                'korean_sector_sub': str,
                'confidence': float,
                'reasoning': str
            }
        """

        # Try exact match
        if ksic_code in self.ksic_to_gics:
            gics_sector, ind_group, industry, kr_top, kr_sub = self.ksic_to_gics[ksic_code]
            return {
                'gics_sector': gics_sector,
                'gics_industry_group': ind_group,
                'gics_industry': industry,
                'korean_sector_top': kr_top,
                'korean_sector_sub': kr_sub,
                'confidence': 0.95,
                'reasoning': f'GICS: {gics_sector} - {industry} (KSIC {ksic_code})',
                'source': 'GICS_exact'
            }

        # Try prefix match (5 digits -> 4 -> 3 -> 2)
        for length in [5, 4, 3, 2]:
            prefix = ksic_code[:length]
            for code, (gics_sector, ind_group, industry, kr_top, kr_sub) in self.ksic_to_gics.items():
                if code == prefix:
                    confidence = 0.9 - (0.1 * (5 - length))  # 0.9, 0.8, 0.7, 0.6
                    return {
                        'gics_sector': gics_sector,
                        'gics_industry_group': ind_group,
                        'gics_industry': industry,
                        'korean_sector_top': kr_top,
                        'korean_sector_sub': kr_sub,
                        'confidence': confidence,
                        'reasoning': f'GICS: {gics_sector} - {industry} (KSIC {ksic_code}, {length}자리 매칭)',
                        'source': f'GICS_prefix_{length}'
                    }

        # Fallback: Use broad industry code patterns
        first_digit = ksic_code[0] if ksic_code else '0'

        fallback_patterns = {
            '1': ('Consumer Staples', 'Food & Agriculture', 'Food Products', '식품', '식품'),
            '2': ('Materials', 'Chemicals', 'Chemicals', '화학', '화학'),
            '3': ('Industrials', 'Capital Goods', 'Industrial Goods', '제조업', '일반제조'),
            '4': ('Industrials', 'Capital Goods', 'Construction & Engineering', '건설', '건설'),  # 건설업 41xxx
            '5': ('Industrials', 'Transportation', 'Transportation', '운수', '운수/물류'),
            '6': ('Financials', 'Diversified Financials', 'Financial Services', '금융', '금융'),
            '7': ('Industrials', 'Commercial Services', 'Professional Services', '기타', '전문서비스'),
            '8': ('Industrials', 'Commercial Services', 'Education Services', '기타', '교육'),
            '9': ('Consumer Discretionary', 'Hotels & Leisure', 'Leisure Services', '레저', '서비스'),
        }

        if first_digit in fallback_patterns:
            gics_sector, ind_group, industry, kr_top, kr_sub = fallback_patterns[first_digit]
            return {
                'gics_sector': gics_sector,
                'gics_industry_group': ind_group,
                'gics_industry': industry,
                'korean_sector_top': kr_top,
                'korean_sector_sub': kr_sub,
                'confidence': 0.4,
                'reasoning': f'GICS: {gics_sector} - {industry} (KSIC {ksic_code}, 대분류 추정)',
                'source': 'GICS_fallback'
            }

        # Unknown
        return {
            'gics_sector': 'Unclassified',
            'gics_industry_group': 'Other',
            'gics_industry': 'Other',
            'korean_sector_top': '기타',
            'korean_sector_sub': '미분류',
            'confidence': 0.2,
            'reasoning': f'KSIC {ksic_code} - 미등록 업종코드',
            'source': 'unknown'
        }

    def get_moat_drivers_by_gics(self, gics_sector: str, gics_industry: str) -> Dict:
        """
        Get typical moat drivers for GICS sector/industry

        Returns investment-relevant moat characteristics
        """

        moat_patterns = {
            # Materials
            ('Materials', 'Chemicals'): {
                'primary_moat': '원가 우위',
                'drivers': ['규모의 경제', 'CAPEX 장벽', '원재료 접근성'],
                'typical_strength': 3,
                'notes': '화학: 생산규모가 원가에 직접 영향, 대형 설비투자 필요'
            },
            ('Materials', 'Specialty Chemicals'): {
                'primary_moat': '전환 비용',
                'drivers': ['고객 인증', '기술 특화', '품질 일관성'],
                'typical_strength': 4,
                'notes': '특수화학: 고객 switching cost 높음, 인증 장벽'
            },

            # Information Technology
            ('Information Technology', 'Semiconductors'): {
                'primary_moat': '원가 우위',
                'drivers': ['막대한 CAPEX', '첨단 공정', '규모의 경제'],
                'typical_strength': 5,
                'notes': '반도체: 세계 최고 수준의 CAPEX 장벽, 기술 리더십'
            },
            ('Information Technology', 'Software'): {
                'primary_moat': '전환 비용',
                'drivers': ['API 통합', '학습곡선', '데이터 종속성'],
                'typical_strength': 3,
                'notes': '소프트웨어: 고객 switching cost, 네트워크 효과 가능. 경쟁 치열 고려 하향(4->3)'
            },
            ('Information Technology', 'IT Consulting'): {
                'primary_moat': '전환 비용',
                'drivers': ['B2B 락인', '시스템 운영 노하우', '유지보수'],
                'typical_strength': 2,
                'notes': 'IT서비스/컨설팅: 인력 중심 사업, 진입장벽 낮고 수주 경쟁 치열'
            },
            ('Communication Services', 'Interactive Media & Services'): {
                'primary_moat': '네트워크 효과',
                'drivers': ['사용자 규모', '데이터 선점', '플랫폼 락인'],
                'typical_strength': 4,
                'notes': '인터넷 플랫폼: 승자독식 구조, 네트워크 효과 강력'
            },

            # Communication Services
            ('Communication Services', 'Gaming'): {
                'primary_moat': '네트워크 효과',
                'drivers': ['유저 커뮤니티', 'IP 가치', '플랫폼 효과'],
                'typical_strength': 4,
                'notes': '게임: 네트워크 효과 + IP, 단 life cycle 짧음'
            },

            # Health Care
            ('Health Care', 'Pharmaceuticals'): {
                'primary_moat': '규제/허가',
                'drivers': ['임상 승인', '특허', '식약처 인허가'],
                'typical_strength': 5,
                'notes': '의약품: 규제 진입장벽 매우 높음, 특허 보호'
            },

            # Consumer Discretionary
            ('Consumer Discretionary', 'Retailing'): {
                'primary_moat': '브랜드 파워',
                'drivers': ['고객 충성도', '입지', '상품 차별화'],
                'typical_strength': 3,
                'notes': '소매: 브랜드 또는 입지 우위, 경쟁 치열'
            },
            ('Consumer Discretionary', 'Casinos & Gaming'): {
                'primary_moat': '규제/허가',
                'drivers': ['카지노 인허가', '독점적 입지', '정부 규제'],
                'typical_strength': 4,
                'notes': '카지노: 인허가 장벽 높음, 제한된 지역 독점'
            },

            # Financials
            ('Financials', 'Banks'): {
                'primary_moat': '규제/허가',
                'drivers': ['금융 라이선스', '자본 요건', '규제 보호'],
                'typical_strength': 4,
                'notes': '은행: 금융 인허가 장벽, 자본 규제'
            },
            ('Financials', 'Insurance'): {
                'primary_moat': '규제/허가',
                'drivers': ['보험 인허가', '자본 요건', '계리적 노하우'],
                'typical_strength': 3,
                'notes': '보험: 인허가 장벽, 규모 기반 리스크 분산'
            },
            ('Financials', 'Diversified Financials'): {
                'primary_moat': '규제/허가',
                'drivers': ['금융 라이선스', '고객 기반', '시스템 구축'],
                'typical_strength': 3,
                'notes': '증권/자산운용: 라이선스 + 고객 기반'
            },

            # Industrials - Construction
            ('Industrials', 'Construction & Engineering'): {
                'primary_moat': '원가 우위',
                'drivers': ['시공 실적', '인력/장비', '수주 경쟁'],
                'typical_strength': 2,
                'notes': '건설: 진입장벽 낮음, 수주 경쟁 치열, 해자 약함'
            },

            # Utilities
            ('Utilities', 'Utilities'): {
                'primary_moat': '규제/허가',
                'drivers': ['정부 인허가', '자연독점', '대규모 인프라'],
                'typical_strength': 4,
                'notes': '유틸리티: 자연독점 + 규제 보호, 안정적 해자'
            },

            # Industrials - Transportation
            ('Industrials', 'Transportation'): {
                'primary_moat': '규모의 경제',
                'drivers': ['네트워크 규모', '인프라 투자', '규제'],
                'typical_strength': 3,
                'notes': '운수/물류: 규모 + 인프라 장벽'
            },

            # Communication Services - Telecom
            ('Communication Services', 'Telecommunication Services'): {
                'primary_moat': '규모의 경제',
                'drivers': ['주파수 라이선스', '네트워크 인프라', '고객 기반'],
                'typical_strength': 4,
                'notes': '통신: 인프라 CAPEX + 주파수 라이선스'
            },

            # Real Estate
            ('Real Estate', 'Real Estate'): {
                'primary_moat': '원가 우위',
                'drivers': ['입지', '자산 규모', '개발 노하우'],
                'typical_strength': 2,
                'notes': '부동산: 입지 외 해자 약함, 경기 민감'
            },

            # Consumer Staples - Food
            ('Consumer Staples', 'Food & Beverage'): {
                'primary_moat': '브랜드 파워',
                'drivers': ['브랜드 인지도', '유통망', '원재료 확보'],
                'typical_strength': 3,
                'notes': '식품: 브랜드 + 유통망, 규모에 따라 차이'
            },
        }

        # Try exact match
        key = (gics_sector, gics_industry)
        if key in moat_patterns:
            return moat_patterns[key]

        # Try sector-level match
        for (sector, industry), pattern in moat_patterns.items():
            if sector == gics_sector:
                return {**pattern, 'notes': f'{pattern["notes"]} (산업군 추정)'}

        # Default
        return {
            'primary_moat': '미분류',
            'drivers': [],
            'typical_strength': 3,
            'notes': '해당 GICS 분류에 대한 moat 패턴 미등록'
        }
