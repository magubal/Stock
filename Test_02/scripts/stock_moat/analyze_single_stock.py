"""
Single Stock Analyzer - MVP Version
Analyzes one stock at a time with user guidance
"""

import sys
import os

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
sys.path.insert(0, project_root)

# Import Excel I/O
sys.path.insert(0, f"{project_root}/.agent/skills/stock-moat/utils")
from excel_io import ExcelIO


def analyze_stock_interactive(ticker: str):
    """
    Interactive stock analysis with user input
    This MVP version guides the user through the analysis process
    """

    excel_path = f"{project_root}/data/ask/stock_core_master_v2_korean_taxonomy_2026-01-30_요청용_011.xlsx"
    excel_io = ExcelIO(excel_path)

    # Load stock data
    stock = excel_io.get_stock_by_ticker(ticker)

    if not stock:
        print(f"❌ Stock {ticker} not found in Excel")
        return

    print(f"\n{'='*60}")
    print(f"📊 Stock Analysis: {stock['name']} ({ticker})")
    print(f"{'='*60}\n")

    # Check if already complete
    if not pd.isna(stock.get('해자강도')):
        print(f"✅ Stock already analyzed (해자강도: {stock['해자강도']})")
        print(f"\n현재 데이터:")
        print(f"  core_sector_top: {stock.get('core_sector_top')}")
        print(f"  core_sector_sub: {stock.get('core_sector_sub')}")
        print(f"  해자강도: {stock.get('해자강도')}")
        return

    print("🔍 이 종목은 아직 분석되지 않았습니다.")
    print("\n다음 정보를 입력해주세요:\n")

    # Interactive prompts
    print("=" * 60)
    core_sector_top = input("📂 core_sector_top (예: 반도체): ")
    core_sector_sub = input("📂 core_sector_sub (예: 메모리/시스템반도체): ")

    print("\n" + "=" * 60)
    core_desc = input("📝 core_desc (본업 설명 1-3줄):\n")

    print("\n" + "=" * 60)
    print("\n해자 강도 평가 (각 항목 1-5점):\n")

    brand = int(input("  브랜드 파워 (1-5): "))
    cost = int(input("  원가 우위 (1-5): "))
    network = int(input("  네트워크 효과 (1-5): "))
    switching = int(input("  전환 비용 (1-5): "))
    regulatory = int(input("  규제/허가 (1-5): "))

    # Calculate moat strength
    total = brand + cost + network + switching + regulatory
    moat_strength = round(total / 5)

    print(f"\n총점: {total}/25 → 해자강도: {moat_strength}")

    # Build 해자DESC
    moat_desc = f"""브랜드 파워: {brand}/5
원가 우위: {cost}/5
네트워크 효과: {network}/5
전환 비용: {switching}/5
규제/허가: {regulatory}/5
---
총점: {total}/25 → 해자강도 {moat_strength}"""

    # Re-verification for moat >= 4
    verification_desc = ""
    if moat_strength >= 4:
        print("\n" + "=" * 60)
        print("⚠️  해자강도 ≥ 4: 재검증 필요")
        verification_desc = input("검증용desc (재검증 내용):\n")

    # Prepare update data
    update_data = {
        'core_sector_top': core_sector_top,
        'core_sector_sub': core_sector_sub,
        'core_desc': core_desc,
        '해자강도': moat_strength,
        '해자DESC': moat_desc,
    }

    if verification_desc:
        update_data['검증용desc'] = verification_desc

    # Confirm before write
    print("\n" + "=" * 60)
    print("📝 입력 내용 확인:\n")
    for key, value in update_data.items():
        print(f"{key}: {value}\n")

    confirm = input("Excel에 저장하시겠습니까? (y/n): ")

    if confirm.lower() == 'y':
        success = excel_io.update_stock_row(ticker, update_data)
        if success:
            print(f"\n✅ {stock['name']} ({ticker}) 분석 완료!")
        else:
            print(f"\n❌ 저장 실패")
    else:
        print("\n취소됨")


if __name__ == "__main__":
    import pandas as pd

    if len(sys.argv) < 2:
        print("Usage: python analyze_single_stock.py {ticker}")
        print("Example: python analyze_single_stock.py 123750")

        # Load incomplete stocks
        excel_path = f"{project_root}/data/ask/stock_core_master_v2_korean_taxonomy_2026-01-30_요청용_011.xlsx"
        excel_io = ExcelIO(excel_path)
        df = excel_io.load_stock_data()
        incomplete = excel_io.get_incomplete_stocks(df)

        print(f"\n미완료 종목 ({len(incomplete)}개):")
        for idx, row in incomplete.head(10).iterrows():
            print(f"  {row['ticker']}: {row['name']}")

        sys.exit(1)

    ticker = sys.argv[1]
    analyze_stock_interactive(ticker)
