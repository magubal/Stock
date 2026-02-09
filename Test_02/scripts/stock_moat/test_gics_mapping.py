"""
Test GICS Mapping vs Old KSIC Mapping
Shows the improvement in classification accuracy
"""

import sys
import os

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root
project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
sys.path.insert(0, f"{project_root}/.agent/skills/stock-moat/utils")

from ksic_to_gics_mapper import KSICtoGICSMapper
from dart_client import DARTClient


def test_problematic_stocks():
    """Test stocks that were misclassified with old approach"""

    dart_api_key = os.getenv("DART_API_KEY")
    if not dart_api_key:
        print("⚠️  DART_API_KEY not set in environment variables")
        print("Please set DART_API_KEY in .env file")
        return

    mapper = KSICtoGICSMapper()
    dart = DARTClient(dart_api_key)

    test_cases = [
        {
            'name': '나노켐텍',
            'ticker': '091970',
            'expected_sector': '화학',
            'expected_sub': '특수플라스틱 or 기타화학',
            'old_classification': '제조업/미분류'
        },
        {
            'name': '네오위즈',
            'ticker': '095660',
            'expected_sector': '게임',
            'expected_sub': '모바일게임/PC게임',
            'old_classification': 'IT/소프트웨어'
        },
        {
            'name': '삼성전자',
            'ticker': '005930',
            'expected_sector': '반도체',
            'expected_sub': '메모리반도체',
            'old_classification': '전자/반도체 (correct)'
        },
        {
            'name': '하나투어',
            'ticker': '039130',
            'expected_sector': '여행',
            'expected_sub': '여행사',
            'old_classification': '기타/미분류'
        },
    ]

    print(f"\n{'='*80}")
    print(f"🧪 GICS 매핑 테스트 - 문제 종목 재분류")
    print(f"{'='*80}\n")

    for idx, case in enumerate(test_cases, start=1):
        print(f"\n[{idx}] {case['name']} ({case['ticker']})")
        print(f"{'─'*80}")

        # Get DART data
        dart_result = dart.analyze_stock(case['ticker'])

        if not dart_result:
            print(f"  ❌ DART 데이터 없음\n")
            continue

        ksic_code = dart_result.get('industry_code', '')
        print(f"  DART 업종코드: {ksic_code}")

        # Old classification
        print(f"\n  📌 기존 분류 (문제): {case['old_classification']}")

        # New GICS classification
        gics_result = mapper.map_to_gics(ksic_code, case['name'])

        print(f"\n  ✨ GICS 기반 분류 (개선):")
        print(f"     GICS Sector: {gics_result['gics_sector']}")
        print(f"     GICS Industry: {gics_result['gics_industry']}")
        print(f"     한국어 분류: {gics_result['korean_sector_top']} / {gics_result['korean_sector_sub']}")
        print(f"     신뢰도: {gics_result['confidence']:.0%}")
        print(f"     근거: {gics_result['reasoning']}")

        # Moat characteristics
        moat_info = mapper.get_moat_drivers_by_gics(
            gics_result['gics_sector'],
            gics_result['gics_industry']
        )

        print(f"\n  🛡️  해자 특성:")
        print(f"     주요 해자: {moat_info['primary_moat']}")
        print(f"     해자 동인: {', '.join(moat_info['drivers'])}")
        print(f"     일반 강도: {moat_info['typical_strength']}/5")
        print(f"     분석 메모: {moat_info['notes']}")

        # Evaluation
        is_correct = (
            gics_result['korean_sector_top'] == case['expected_sector'] or
            case['expected_sector'] in gics_result['korean_sector_top']
        )

        if is_correct:
            print(f"\n  ✅ 분류 정확: 예상 섹터와 일치")
        else:
            print(f"\n  ⚠️  검토 필요: 예상 '{case['expected_sector']}', 실제 '{gics_result['korean_sector_top']}'")

        print(f"\n{'─'*80}")

    print(f"\n{'='*80}")
    print(f"✅ 테스트 완료")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    test_problematic_stocks()
