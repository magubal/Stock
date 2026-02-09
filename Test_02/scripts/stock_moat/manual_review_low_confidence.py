"""
Manual Review for Low-Confidence Stocks
Uses actual business report content to suggest classifications
"""

import sys
import os
import json

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root
project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
sys.path.insert(0, f"{project_root}/.agent/skills/stock-moat/utils")
sys.path.insert(0, f"{project_root}/scripts/stock_moat")

from excel_io import ExcelIO
from dart_client import DARTClient
from industry_mapper import IndustryMapper
import pandas as pd


class ManualReviewer:
    """Interactive manual review with business report analysis"""

    def __init__(self, dart_api_key: str):
        self.dart = DARTClient(dart_api_key)
        self.mapper = IndustryMapper()
        self.excel_path = f"{project_root}/data/ask/stock_core_master_v2_korean_taxonomy_2026-01-30_요청용_011.xlsx"
        self.excel_io = ExcelIO(self.excel_path)

    def get_low_confidence_stocks(self) -> pd.DataFrame:
        """Get stocks with confidence < 50%"""
        df = self.excel_io.load_stock_data()

        # Find stocks with "기타" classification
        low_conf = df[
            (df['해자강도'].notna()) &
            (df['core_sector_top'] == '기타')
        ].copy()

        return low_conf

    def analyze_business_content(self, ticker: str, name: str, industry_code: str) -> dict:
        """
        Analyze business report content and suggest classification

        Returns:
            {
                'industry_code': str,
                'company_name': str,
                'business_summary': str,
                'suggested_sector': str,
                'suggested_sub': str,
                'confidence': float,
                'reasoning': str
            }
        """
        print(f"\n{'='*60}")
        print(f"📋 {name} ({ticker}) 사업보고서 분석")
        print(f"{'='*60}\n")

        # Get DART data
        dart_result = self.dart.analyze_stock(ticker)

        if not dart_result:
            return {
                'industry_code': 'Unknown',
                'company_name': name,
                'business_summary': 'DART 데이터 없음',
                'suggested_sector': '기타',
                'suggested_sub': '미분류',
                'confidence': 0.2,
                'reasoning': 'DART 조회 실패'
            }

        industry_code = dart_result.get('industry_code', '')
        company_name = dart_result.get('corp_name', name)

        # Analyze industry code patterns
        suggestions = self._analyze_industry_code_pattern(industry_code, company_name)

        return {
            'industry_code': industry_code,
            'company_name': company_name,
            'business_summary': dart_result.get('business_desc', ''),
            'suggested_sector': suggestions['sector'],
            'suggested_sub': suggestions['sub'],
            'confidence': suggestions['confidence'],
            'reasoning': suggestions['reasoning']
        }

    def _analyze_industry_code_pattern(self, code: str, company: str) -> dict:
        """
        Analyze industry code patterns to suggest classification

        KSIC 업종코드 패턴:
        - 17x: 제지/펄프
        - 20x: 화학
        - 21x: 의약품
        - 22x: 고무/플라스틱
        - 26x: 전자/반도체
        - 29x: 기계
        - 46x: 도소매
        - 47x: 소매
        - 58x: 출판/소프트웨어
        - 59x: 영상/음반
        - 62x: IT서비스
        - 63x: 정보서비스
        - 75x: 여행/관광
        """
        patterns = {
            # 제지/펄프
            '17': ('제조업', '제지/펄프', '제지 및 종이제품 제조업'),

            # 고무/플라스틱
            '22': ('제조업', '기타', '고무 및 플라스틱 제품 제조업'),
            '222': ('제조업', '기타', '플라스틱 제품 제조업'),
            '231': ('제조업', '기타', '유리 제품 제조업'),

            # 전기/전자
            '27': ('전자', '디스플레이/전자부품', '전기장비 제조업'),
            '281': ('제조업', '기타', '일반목적용 기계 제조업'),

            # 도소매
            '464': ('유통', '도소매', '가정용품 도매업'),
            '465': ('유통', '도소매', '기계장비 도매업'),
            '466': ('유통', '도소매', '상품중개업'),
            '468': ('유통', '도소매', '기타 전문 도소매업'),
            '471': ('유통', '소매', '종합소매업'),
            '479': ('유통', '소매', '기타 소매업'),

            # IT서비스
            '582': ('IT', '소프트웨어/게임', '소프트웨어 개발 및 공급업'),
            '620': ('IT', '기타', 'IT서비스업'),
            '639': ('IT', '기타', '기타 정보서비스업'),

            # 전문서비스
            '713': ('기타', '전문서비스', '광고업'),
            '739': ('기타', '전문서비스', '기타 전문과학기술서비스업'),
            '752': ('여행', '여행/관광', '여행사 및 기타 여행보조 서비스업'),
        }

        # Try exact match
        for code_prefix, (sector, sub, desc) in patterns.items():
            if code.startswith(code_prefix):
                return {
                    'sector': sector,
                    'sub': sub,
                    'confidence': 0.7,
                    'reasoning': f'{desc} (KSIC {code})'
                }

        # Default
        return {
            'sector': '기타',
            'sub': '미분류',
            'confidence': 0.3,
            'reasoning': f'KSIC {code} - 미등록 업종코드'
        }

    def interactive_review(self):
        """Interactive review process"""
        low_conf_stocks = self.get_low_confidence_stocks()
        total = len(low_conf_stocks)

        print(f"\n{'='*60}")
        print(f"🔍 저신뢰도 종목 수동 검토")
        print(f"{'='*60}")
        print(f"총 {total}개 종목\n")

        updates = []

        for idx, (row_idx, stock) in enumerate(low_conf_stocks.iterrows(), start=1):
            ticker = stock['ticker']
            name = stock['name']
            current_sector = stock.get('core_sector_top', '기타')
            current_sub = stock.get('core_sector_sub', '미분류')

            print(f"\n{'─'*60}")
            print(f"[{idx}/{total}] {name} ({ticker})")
            print(f"{'─'*60}")
            print(f"현재 분류: {current_sector} / {current_sub}\n")

            # Analyze
            analysis = self.analyze_business_content(
                ticker,
                name,
                stock.get('core_desc', '')
            )

            print(f"DART 업종코드: {analysis['industry_code']}")
            print(f"사업 요약: {analysis['business_summary']}\n")

            print(f"💡 AI 제안:")
            print(f"  분류: {analysis['suggested_sector']} / {analysis['suggested_sub']}")
            print(f"  신뢰도: {analysis['confidence']:.1%}")
            print(f"  근거: {analysis['reasoning']}\n")

            # User choice
            print("선택:")
            print(f"  1) AI 제안 수용 ({analysis['suggested_sector']})")
            print(f"  2) 현재 유지 ({current_sector})")
            print(f"  3) 직접 입력")
            print(f"  4) 건너뛰기")

            choice = input("\n선택 (1-4, Enter=1): ").strip() or "1"

            if choice == "1":
                # Accept AI suggestion
                update_data = {
                    'core_sector_top': analysis['suggested_sector'],
                    'core_sector_sub': analysis['suggested_sub'],
                    'core_desc': f"{name} - {analysis['reasoning']}"
                }
                updates.append({'ticker': ticker, 'data': update_data})
                print(f"✅ {analysis['suggested_sector']}로 업데이트")

            elif choice == "2":
                # Keep current
                print(f"✅ {current_sector} 유지")
                continue

            elif choice == "3":
                # Manual input
                sector = input("  core_sector_top: ").strip()
                sub = input("  core_sector_sub: ").strip()

                if sector and sub:
                    update_data = {
                        'core_sector_top': sector,
                        'core_sector_sub': sub,
                        'core_desc': f"{name} - 수동 분류 (DART {analysis['industry_code']})"
                    }
                    updates.append({'ticker': ticker, 'data': update_data})
                    print(f"✅ {sector}로 업데이트")

            elif choice == "4":
                # Skip
                print("⏭️  건너뜀")
                continue

            # Progress save every 10 stocks
            if len(updates) > 0 and len(updates) % 10 == 0:
                print(f"\n💾 중간 저장 중... ({len(updates)}개)")
                self._save_batch(updates)
                updates = []

        # Final save
        if len(updates) > 0:
            print(f"\n💾 최종 저장 중... ({len(updates)}개)")
            self._save_batch(updates)

        print(f"\n{'='*60}")
        print(f"✅ 수동 검토 완료!")
        print(f"{'='*60}\n")

    def _save_batch(self, updates):
        """Save batch updates to Excel"""
        if len(updates) == 0:
            return

        results = self.excel_io.batch_update_stocks(updates, mode='efficient')
        print(f"  ✅ 저장 완료: {results['success']}개")


# Main
if __name__ == "__main__":
    dart_api_key = os.getenv("DART_API_KEY")
    if not dart_api_key:
        print("⚠️  DART_API_KEY not set in environment variables")
        print("Please set DART_API_KEY in .env file")
        exit(1)
    reviewer = ManualReviewer(dart_api_key)
    reviewer.interactive_review()
