"""
Re-analyze Completed Stocks with Improved Keywords
Fixes "기타/미분류" classifications
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
import pandas as pd


def reanalyze_completed():
    """Re-analyze completed stocks with improved keyword matching"""

    excel_path = f"{project_root}/data/ask/stock_core_master_v2_korean_taxonomy_2026-01-30_요청용_011.xlsx"
    excel_io = ExcelIO(excel_path)
    analyzer = MoatAnalyzer()

    print(f"\n{'='*60}")
    print(f"🔄 Re-analyzing Completed Stocks")
    print(f"{'='*60}\n")

    # Load all stock data
    df = excel_io.load_stock_data()

    # Find completed stocks (has 해자강도 but may have 기타/미분류)
    completed = df[df['해자강도'].notna()].copy()

    print(f"Found {len(completed)} completed stocks\n")

    # Focus on stocks with "기타" or "미분류"
    needs_reanalysis = completed[
        (completed['core_sector_top'] == '기타') |
        (completed['core_sector_sub'] == '미분류')
    ]

    print(f"Stocks needing re-classification: {len(needs_reanalysis)}\n")

    if len(needs_reanalysis) == 0:
        print("✅ No stocks need re-classification!")
        return

    # Show what needs fixing
    print("Stocks to re-analyze:")
    for idx, stock in needs_reanalysis.iterrows():
        print(f"  {stock['ticker']}: {stock['name']} → {stock['core_sector_top']}/{stock['core_sector_sub']}")

    print(f"\n{'='*60}\n")
    print("✅ Proceeding with automatic re-analysis...\n")

    # Re-analyze each stock
    batch_updates = []

    for idx, (row_idx, stock) in enumerate(needs_reanalysis.iterrows(), start=1):
        ticker = stock['ticker']
        name = stock['name']

        print(f"\n[{idx}/{len(needs_reanalysis)}] Re-analyzing: {name} ({ticker})")

        # Re-classify sector only (keep existing moat scores)
        sector_result = analyzer.classify_sector(name)

        print(f"  Old: {stock['core_sector_top']} / {stock['core_sector_sub']}")
        print(f"  New: {sector_result['core_sector_top']} / {sector_result['core_sector_sub']}")
        print(f"  Confidence: {sector_result['confidence']:.1%}")

        # Only update if confidence improved
        if sector_result['confidence'] >= 0.5:
            update_data = {
                'core_sector_top': sector_result['core_sector_top'],
                'core_sector_sub': sector_result['core_sector_sub']
            }

            batch_updates.append({
                'ticker': ticker,
                'data': update_data
            })
            print("  ✅ Will update")
        else:
            print("  ⏭️  Skipped (low confidence)")

    # Batch update Excel
    if len(batch_updates) > 0:
        print(f"\n{'='*60}")
        print(f"💾 Updating {len(batch_updates)} stocks in Excel...")
        print(f"{'='*60}\n")

        batch_results = excel_io.batch_update_stocks(
            batch_updates,
            mode='efficient'
        )

        print(f"✅ Updated: {batch_results['success']} stocks")
        if batch_results['failed'] > 0:
            print(f"❌ Failed: {batch_results['failed']} stocks")

    # Show final statistics
    print(f"\n{'='*60}")
    print(f"📊 Re-analysis Complete")
    print(f"{'='*60}")

    # Reload to check results
    df_after = excel_io.load_stock_data()
    completed_after = df_after[df_after['해자강도'].notna()]

    기타_count = len(completed_after[completed_after['core_sector_top'] == '기타'])
    미분류_count = len(completed_after[completed_after['core_sector_sub'] == '미분류'])

    print(f"Remaining '기타': {기타_count}")
    print(f"Remaining '미분류': {미분류_count}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    reanalyze_completed()
