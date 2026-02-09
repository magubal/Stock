"""
Update Casino Stocks with New GICS Mapping
Re-analyze only the 4 casino stocks with newly added mappings
"""

import sys
import os

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root
project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
sys.path.insert(0, f"{project_root}/.agent/skills/stock-moat/utils")
sys.path.insert(0, f"{project_root}/scripts/stock_moat")

from excel_io import ExcelIO
from moat_analyzer import MoatAnalyzer


def update_casino_stocks():
    """Update the 4 casino stocks with new GICS classification"""

    # Casino stocks to update
    casino_stocks = [
        ('034230', '파라다이스'),
        ('035250', '강원랜드'),
        ('114090', 'GKL'),
        ('473980', '노브메르스')
    ]

    print(f"\n{'='*60}")
    print(f"🎰 카지노 업종 재분류")
    print(f"{'='*60}\n")

    excel_path = f"{project_root}/data/ask/stock_core_master_v2_korean_taxonomy_2026-01-30_요청용_011.xlsx"
    excel_io = ExcelIO(excel_path)
    analyzer = MoatAnalyzer()

    batch_updates = []

    for idx, (ticker, name) in enumerate(casino_stocks, start=1):
        print(f"[{idx}/4] {name} ({ticker})")

        try:
            # Analyze with new casino mapping
            result = analyzer.analyze_stock(ticker, name, auto_save=False)

            print(f"  ✅ {result['core_sector_top']} / {result['core_sector_sub']}")
            print(f"  신뢰도: {result['confidence']:.0%}")
            print(f"  해자강도: {result['해자강도']}/5\n")

            # Prepare update
            update_data = {
                'core_sector_top': result['core_sector_top'],
                'core_sector_sub': result['core_sector_sub'],
                'core_desc': result['core_desc'],
                '해자강도': result['해자강도'],
                '해자DESC': result['해자DESC']
            }

            batch_updates.append({
                'ticker': ticker,
                'data': update_data
            })

        except Exception as e:
            print(f"  ❌ Error: {e}\n")

    # Batch update Excel
    if len(batch_updates) > 0:
        print(f"\n{'='*60}")
        print(f"💾 Excel 업데이트 중...")
        print(f"{'='*60}\n")

        results = excel_io.batch_update_stocks(batch_updates, mode='efficient')
        print(f"✅ 업데이트 완료: {results['success']}개\n")

    # Verify final state
    df_after = excel_io.load_stock_data()
    completed = df_after[df_after['해자강도'].notna()]
    low_conf = df_after[(df_after['해자강도'].notna()) & (df_after['core_sector_top'] == '기타')]

    print(f"{'='*60}")
    print(f"📊 최종 결과")
    print(f"{'='*60}")
    print(f"완료: {len(completed)}/{len(df_after)}")
    print(f"'기타' 분류: {len(low_conf)}개 ({len(low_conf)/len(completed)*100:.1f}%)")

    if len(low_conf) > 0:
        print(f"\n남은 '기타' 종목:")
        for _, stock in low_conf.iterrows():
            print(f"  - {stock['name']} ({stock['ticker']})")

    print(f"{'='*60}\n")


if __name__ == "__main__":
    update_casino_stocks()
